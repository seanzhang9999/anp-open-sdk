# Copyright 2024 ANP Open SDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import inspect
import json
from typing import Any, Dict, Optional, List, Union
from urllib.parse import urlencode, quote

from anp_open_sdk.auth.auth_client import agent_auth_request, handle_response
# 延迟导入以避免循环依赖
# from anp_open_sdk.anp_sdk_agent import RemoteAgent, LocalAgent
from anp_open_sdk_framework.local_methods.local_methods_decorators import LOCAL_METHODS_REGISTRY
from anp_open_sdk_framework.local_methods.local_methods_doc import LocalMethodsDocGenerator


class UnifiedCaller:
    """统一调用器 - 支持本地方法和远程Agent API调用"""

    def __init__(self, sdk):
        self.sdk = sdk
        self.doc_generator = LocalMethodsDocGenerator()

    def _get_agent_classes(self):
        """延迟导入 agent 类以避免循环依赖"""
        from anp_open_sdk.anp_sdk_agent import RemoteAgent, LocalAgent
        return RemoteAgent, LocalAgent

    async def call(self, target: str, method_or_path: str, *args, **kwargs) -> Any:
        """
        统一调用接口
        
        Args:
            target: 目标标识符 (DID for remote agent, agent_name for local)
            method_or_path: 方法名或API路径
            *args, **kwargs: 参数
            
        Returns:
            调用结果
        """
        # 判断是本地调用还是远程调用
        if self._is_local_target(target):
            return await self._call_local_method(target, method_or_path, *args, **kwargs)
        else:
            return await self._call_remote_api(target, method_or_path, *args, **kwargs)

    def _is_local_target(self, target: str) -> bool:
        """判断是否为本地目标"""
        # 检查是否为本地agent
        local_agent = self.sdk.get_agent(target)
        if local_agent:
            return True
        
        # 检查是否在本地方法注册表中
        for method_key in LOCAL_METHODS_REGISTRY:
            if target in method_key:
                return True
        
        return False

    async def _call_local_method(self, target: str, method_name: str, *args, **kwargs) -> Any:
        """调用本地方法"""
        # 尝试通过agent直接调用
        agent = self.sdk.get_agent(target)
        if agent and hasattr(agent, method_name):
            method = getattr(agent, method_name)
            return await self._execute_method(method, agent, *args, **kwargs)
        
        # 尝试通过方法注册表调用
        method_key = f"{target}::{method_name}"
        if method_key in LOCAL_METHODS_REGISTRY:
            method_info = LOCAL_METHODS_REGISTRY[method_key]
            target_agent = self.sdk.get_agent(method_info["agent_did"])
            if target_agent:
                method = getattr(target_agent, method_name)
                return await self._execute_method(method, target_agent, *args, **kwargs)
        
        raise ValueError(f"未找到本地方法: {target}.{method_name}")

    async def _call_remote_api(self, target_did: str, api_path: str, *args, params: Optional[Dict] = None, method: str = "GET", **kwargs) -> Dict:
        """调用远程Agent API"""
        # 获取调用者DID
        caller_agent = None
        for agent in getattr(self.sdk, 'agents', []):
            if hasattr(agent, 'id'):
                caller_agent = agent.id
                break
        
        if not caller_agent:
            raise ValueError("未找到可用的调用者Agent")

        # 合并参数
        if params is None:
            params = {}
        if 'args' in kwargs:
            params.update({'args': kwargs.pop('args')})
        if kwargs:
            params.update(kwargs)

        return await self._agent_api_call(caller_agent, target_did, api_path, params, method)

    async def _agent_api_call(self, caller_agent: str, target_agent: str, api_path: str, params: Optional[Dict] = None, method: str = "GET") -> Dict:
        """执行Agent API调用"""
        RemoteAgent, LocalAgent = self._get_agent_classes()
        caller_agent_obj = LocalAgent.from_did(caller_agent)
        target_agent_obj = RemoteAgent(target_agent)
        target_agent_path = quote(target_agent)
        
        if method.upper() == "POST":
            req = {"params": params or {}}
            url_params = {
                "req_did": caller_agent_obj.id,
                "resp_did": target_agent_obj.id
            }
            url_params = urlencode(url_params)
            url = f"http://{target_agent_obj.host}:{target_agent_obj.port}/agent/api/{target_agent_path}{api_path}?{url_params}"
            status, response, info, is_auth_pass = await agent_auth_request(
                caller_agent, target_agent, url, method="POST", json_data=req
            )
        else:
            url_params = {
                "req_did": caller_agent_obj.id,
                "resp_did": target_agent_obj.id,
                "params": json.dumps(params) if params else ""
            }
            url_params = urlencode(url_params)
            url = f"http://{target_agent_obj.host}:{target_agent_obj.port}/agent/api/{target_agent_path}{api_path}?{url_params}"
            status, response, info, is_auth_pass = await agent_auth_request(
                caller_agent, target_agent, url, method="GET")
        
        return await handle_response(response)

    async def _execute_method(self, method, agent, *args, **kwargs) -> Any:
        """执行方法调用"""
        if not callable(method):
            raise TypeError(f"{method} 不是可调用方法")
        
        # 检查是否需要自动注入 agent
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())
        inject_agent = False
        if params and params[0] == "agent":
            if len(args) < 1 and "agent" not in kwargs:
                inject_agent = True

        # 调用方法
        if inspect.iscoroutinefunction(method):
            if inject_agent:
                return await method(agent, *args, **kwargs)
            else:
                return await method(*args, **kwargs)
        else:
            if inject_agent:
                return method(agent, *args, **kwargs)
            else:
                return method(*args, **kwargs)

    async def search_and_call(self, search_keyword: str, *args, **kwargs) -> Any:
        """通过搜索关键词找到方法并调用"""
        results = self.doc_generator.search_methods(keyword=search_keyword)

        if not results:
            raise ValueError(f"未找到包含关键词 '{search_keyword}' 的方法")

        if len(results) > 1:
            method_list = [f"{r['agent_name']}.{r['method_name']}" for r in results]
            raise ValueError(f"找到多个匹配的方法: {method_list}，请使用更具体的关键词")

        method_info = results[0]
        return await self.call(method_info["agent_did"], method_info["name"], *args, **kwargs)

    def list_all_methods(self) -> Dict[str, Dict]:
        """列出所有可用的本地方法"""
        return LOCAL_METHODS_REGISTRY

    async def discover_remote_agents(self) -> List[Dict]:
        """发现远程Agent"""
        # 这里可以实现Agent发现逻辑
        # 暂时返回空列表，具体实现需要根据实际需求
        return []
