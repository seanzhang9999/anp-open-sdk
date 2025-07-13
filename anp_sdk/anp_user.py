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
import logging
from typing import Dict, Any, Callable, List, Tuple

import httpx
import nest_asyncio
from fastapi import FastAPI, Request

from anp_sdk.anp_sdk_user_data import get_user_data_manager

logger = logging.getLogger(__name__)
from starlette.responses import JSONResponse


from anp_sdk.config import get_global_config
from anp_sdk.did.did_tool import parse_wba_did_host_port
from anp_sdk.contact_manager import ContactManager
from anp_server.server_mode import ServerMode

class RemoteANPUser:
    def __init__(self, id: str, name: str = None, host: str = None, port: int = None, **kwargs):
        self.id = id
        self.name = name
        self.host = host
        self.port = port
        if self.id and (self.host is None or self.port is None):
            self.host, self.port = parse_wba_did_host_port(self.id)
        self.extra = kwargs

    def to_dict(self):
        return {
            "did": self.id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            **self.extra
        }

class ANPUser:
    """本地智能体，代表当前用户的DID身份"""
    api_config: List[Dict[str, Any]]  # 用于多智能体加载时 从agent_mappings.yaml加载api相关扩展描述

    def __init__(self, user_data, name: str = "未命名", agent_type: str = "personal"):
        """初始化本地智能体
        
        Args:
            user_data: 用户数据对象
            agent_type: 智能体类型，"personal"或"anp_service"
        """
        self.user_data = user_data
        user_dir = self.user_data.user_dir

        if name == "未命名":
            if self.user_data.name  is not None:
                self.name = self.user_data.name
            else:
                self.name = f"未命名智能体{self.user_data.did}"
        self.id = self.user_data.did
        self.name = name
        self.user_dir = user_dir
        self.agent_type = agent_type
        config = get_global_config()
        self.key_id = config.anp_sdk.user_did_key_id

        self.did_document_path = self.user_data.did_doc_path
        self.private_key_path = self.user_data.did_private_key_file_path
        self.jwt_private_key_path = self.user_data.jwt_private_key_file_path
        self.jwt_public_key_path = self.user_data.jwt_public_key_file_path

        self.logger = logger
        self._ws_connections = {}
        self._sse_clients = set()
        # 托管DID标识
        self.is_hosted_did = self.user_data.is_hosted_did
        self.parent_did = self.user_data.parent_did
        self.hosted_info = self.user_data.hosted_info
        import requests
        self.requests = requests
        # 新增: API与消息handler注册表
        self.api_routes = {}  # path -> handler
        self.message_handlers = {}  # type -> handler
        # 新增: 群事件handler注册表
        # {(group_id, event_type): [handlers]}
        self._group_event_handlers = {}
        # [(event_type, handler)] 全局handler
        self._group_global_handlers = []

        # 群组相关属性
        self.group_queues = {}  # 群组消息队列: {group_id: {client_id: Queue}}
        self.group_members = {}  # 群组成员列表: {group_id: set(did)}

        # 新增：联系人管理器
        self.contact_manager = ContactManager(self.user_data)

    @classmethod
    def from_did(cls, did: str, name: str = "未命名", agent_type: str = "personal"):
        user_data_manager = get_user_data_manager()
        user_data = user_data_manager.get_user_data(did)
        if not user_data:
            # 尝试刷新用户数据
            logger.info(f"用户 {did} 不在内存中，尝试刷新用户数据...")
            user_data_manager.scan_and_load_new_users()
            # 再次尝试获取
            user_data = user_data_manager.get_user_data(did)
            if not user_data:
                # 如果还是找不到，抛出异常
                raise ValueError(f"未找到 DID 为 '{did}' 的用户数据。请检查您的用户目录和配置文件。")
        if name == "未命名":
            name = user_data.name
        if not user_data:
            raise ValueError(f"未找到 DID 为 {did} 的用户数据")
        return cls(user_data, name, agent_type)

    @classmethod
    def from_name(cls, name: str, agent_type: str = "personal"):
        user_data_manager = get_user_data_manager()
        user_data = user_data_manager.get_user_data_by_name(name)
        if not user_data:
            # 尝试刷新用户数据
            logger.info(f"用户 {name} 不在内存中，尝试刷新用户数据...")
            user_data_manager.scan_and_load_new_users()

            # 再次尝试获取
            user_data = user_data_manager.get_user_data_by_name(name)
            if not user_data:
                # 如果还是找不到，抛出异常
                logger.error(f"未找到 name 为 {name} 的用户数据")
                raise ValueError(f"未找到 name 为 '{name}' 的用户数据。请检查您的用户目录和配置文件。")
            return cls( None, name, agent_type)
        return cls(user_data, name, agent_type)

    def __del__(self):
        """确保在对象销毁时释放资源"""
        try:
            for ws in self._ws_connections.values():
                self.logger.debug(f"LocalAgent {self.id} 销毁时存在未关闭的WebSocket连接")
            self._ws_connections.clear()
            self._sse_clients.clear()
            self.logger.debug(f"LocalAgent {self.id} 资源已释放")
        except Exception:
            pass
                
    def get_host_dids(self):
        """获取用户目录"""
        return self.user_dir

    # 支持装饰器和函数式注册API
    def expose_api(self, path: str, func: Callable = None, methods=None):
        methods = methods or ["GET", "POST"]
        if func is None:
            def decorator(f):
                self.api_routes[path] = f
                api_info = {
                    "path": f"/agent/api/{self.id}{path}",
                    "methods": methods,
                    "summary": f.__doc__ or f"{self.name}的{path}接口",
                    "agent_id": self.id,
                    "agent_name": self.name
                }
                from anp_server.anp_server import ANP_Server
                if hasattr(ANP_Server, 'instance') and ANP_Server.instance:
                    if self.id not in ANP_Server.instance.api_registry:
                        ANP_Server.instance.api_registry[self.id] = []
                    ANP_Server.instance.api_registry[self.id].append(api_info)
                    logger.debug(f"注册 API: {api_info}")
                return f
            return decorator
        else:
            self.api_routes[path] = func
            api_info = {
                "path": f"/agent/api/{self.id}{path}",
                "methods": methods,
                "summary": func.__doc__ or f"{self.name}的{path}接口",
                "agent_id": self.id,
                "agent_name": self.name
            }
            from anp_server.anp_server import ANP_Server
            if hasattr(ANP_Server, 'instance') and ANP_Server.instance:
                if self.id not in ANP_Server.instance.api_registry:
                    ANP_Server.instance.api_registry[self.id] = []
                ANP_Server.instance.api_registry[self.id].append(api_info)
                logger.debug(f"注册 API: {api_info}")
            return func

    def register_message_handler(self, msg_type: str, func: Callable = None, agent_name: str = None):
        """注册消息处理器，支持冲突检测"""
        if func is None:
            def decorator(f):
                self._register_message_handler_internal(msg_type, f, agent_name)
                return f
            return decorator
        else:
            self._register_message_handler_internal(msg_type, func, agent_name)
            return func
    
    def _register_message_handler_internal(self, msg_type: str, handler: Callable, agent_name: str = None):
        """内部消息处理器注册方法，包含冲突检测"""
        # 检查是否已有消息处理器
        if msg_type in self.message_handlers:
            existing_handler = self.message_handlers[msg_type]
            self.logger.warning(f"⚠️  DID {self.id} 的消息类型 '{msg_type}' 已有处理器")
            self.logger.warning(f"   现有处理器: {getattr(existing_handler, '__name__', 'unknown')}")
            self.logger.warning(f"   新处理器: {getattr(handler, '__name__', 'unknown')} (来自 {agent_name or 'unknown'})")
            self.logger.warning(f"   🔧 使用第一个注册的处理器，忽略后续注册")
            return  # 使用第一个，忽略后续的
        
        self.message_handlers[msg_type] = handler
        self.logger.info(f"✅ 注册消息处理器: DID {self.id}, 类型 '{msg_type}', 来自 {agent_name or 'unknown'}")

    def register_group_event_handler(self, handler: Callable, group_id: str = None, event_type: str = None):
        if group_id is None and event_type is None:
            self._group_global_handlers.append((None, handler))
        elif group_id is None:
            self._group_global_handlers.append((event_type, handler))
        else:
            key = (group_id, event_type)
            self._group_event_handlers.setdefault(key, []).append(handler)

    def _get_group_event_handlers(self, group_id: str, event_type: str):
        handlers = []
        for et, h in self._group_global_handlers:
            if et is None or et == event_type:
                handlers.append(h)
        for (gid, et), hs in self._group_event_handlers.items():
            if gid == group_id and (et is None or et == event_type):
                handlers.extend(hs)
        return handlers

    async def _dispatch_group_event(self, group_id: str, event_type: str, event_data: dict):
        handlers = self._get_group_event_handlers(group_id, event_type)
        for handler in handlers:
            try:
                ret = handler(group_id, event_type, event_data)
                if inspect.isawaitable(ret):
                    await ret
            except Exception as e:
                self.logger.error(f"群事件处理器出错: {e}")

    async def handle_request(self, req_did: str, request_data: Dict[str, Any], request: Request):
        req_type = request_data.get("type")
        if req_type in ("group_message", "group_connect", "group_members"):
            handler = self.message_handlers.get(req_type)
            if handler:
                try:
                    nest_asyncio.apply()
                    if asyncio.iscoroutinefunction(handler):
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            future = asyncio.ensure_future(handler(request_data))
                            return loop.run_until_complete(future)
                        else:
                            return loop.run_until_complete(handler(request_data))
                    else:
                        result = handler(request_data)
                    if isinstance(result, dict) and "anp_result" in result:
                        return result
                    return {"anp_result": result}
                except Exception as e:
                    self.logger.error(f"Group message handling error: {e}")
                    return {"anp_result": {"status": "error", "message": str(e)}}
            else:
                return {"anp_result": {"status": "error", "message": f"No handler for group type: {req_type}"}}
        if req_type == "api_call":
            api_path = request_data.get("path")
            handler = self.api_routes.get(api_path)
            if handler:
                try:
                    result = await handler(request_data, request)
                    if isinstance(result, dict):
                        status_code = result.pop('status_code', 200)
                        return JSONResponse(
                            status_code=status_code,
                            content=result
                        )
                    else:
                        return result
                except Exception as e:
                    self.logger.debug(
                        f"发送到 handler的请求数据{request_data}\n"                        
                        f"完整请求为 url: {request.url} \n"
                        f"body: {await request.body()}")
                    self.logger.error(f"API调用错误: {e}")
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "error_message": str(e)}
                    )
            else:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"未找到API: {api_path}"}
                )
        elif req_type == "message":
            msg_type = request_data.get("message_type", "*")
            handler = self.message_handlers.get(msg_type) or self.message_handlers.get("*")
            if handler:
                try:
                    result = await handler(request_data)
                    if isinstance(result, dict) and "anp_result" in result:
                        return result
                    return {"anp_result": result}
                except Exception as e:
                    self.logger.error(f"消息处理错误: {e}")
                    return {"anp_result": {"status": "error", "message": str(e)}}
            else:
                return {"anp_result": {"status": "error", "message": f"未找到消息处理器: {msg_type}"}}
        else:
            return {"anp_result": {"status": "error", "message": "未知的请求类型"}}


    def get_token_to_remote(self, remote_did, hosted_did=None):
        return self.contact_manager.get_token_to_remote(remote_did)

    def store_token_from_remote(self, remote_did, token, hosted_did=None):
        return self.contact_manager.store_token_from_remote(remote_did, token)

    def get_token_from_remote(self, remote_did, hosted_did=None):
        return self.contact_manager.get_token_from_remote(remote_did)

    def revoke_token_to_remote(self, remote_did, hosted_did=None):
        return self.contact_manager.revoke_token_to_remote(remote_did)

    def add_contact(self, remote_agent):
        contact = remote_agent if isinstance(remote_agent, dict) else remote_agent.to_dict() if hasattr(remote_agent, "to_dict") else {
            "did": remote_agent.id,
            "host": getattr(remote_agent, "host", None),
            "port": getattr(remote_agent, "port", None),
            "name": getattr(remote_agent, "name", None)
        }
        self.contact_manager.add_contact(contact)

    def get_contact(self, remote_did: str):
        return self.contact_manager.get_contact(remote_did)

    def list_contacts(self):
        return self.contact_manager.list_contacts()

    async def request_hosted_did_async(self, target_host: str, target_port: int = 9527) -> Tuple[bool, str, str]:
        """
        异步申请托管DID（第一步：提交申请）
        
        Args:
            target_host: 目标托管服务主机
            target_port: 目标托管服务端口
            
        Returns:
            tuple: (是否成功, 申请ID, 错误信息)
        """
        try:
            if not self.user_data.did_document:
                return False, "", "当前用户没有DID文档"
            
            # 构建申请请求
            request_data = {
                "did_document": self.user_data.did_document,
                "requester_did": self.user_data.did_document.get('id'),
                "callback_info": {
                    "client_host": getattr(self, 'host', 'localhost'),
                    "client_port": getattr(self, 'port', 9527)
                }
            }
            
            # 发送申请请求
            target_url = f"http://{target_host}:{target_port}/wba/hosted-did/request"
            

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    target_url,
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        request_id = result.get('request_id')
                        logger.info(f"托管DID申请已提交: {request_id}")
                        return True, request_id, ""
                    else:
                        error_msg = result.get('message', '申请失败')
                        return False, "", error_msg
                else:
                    error_msg = f"申请请求失败: HTTP {response.status_code}"
                    logger.error(error_msg)
                    return False, "", error_msg
                    
        except Exception as e:
            error_msg = f"申请托管DID失败: {e}"
            logger.error(error_msg)
            return False, "", error_msg

    async def check_hosted_did_results(self) -> Tuple[bool, List[Dict[str, Any]], str]:
        """
        检查托管DID处理结果（第二步：检查结果）
        
        Returns:
            tuple: (是否成功, 结果列表, 错误信息)
        """
        try:
            if not self.user_data.did_document:
                return False, [], "当前用户没有DID文档"
            
            # 从自己的DID中提取ID
            did_parts = self.user_data.did_document.get('id', '').split(':')
            requester_id = did_parts[-1] if did_parts else ""
            
            if not requester_id:
                return False, [], "无法从DID中提取用户ID"
            
            # 检查结果（可以检查多个托管服务）
            all_results = []
            
            # 这里可以配置多个托管服务地址
            target_services = [
                ("localhost", 9527),
                ("open.localhost", 9527),
                # 可以添加更多托管服务
            ]
            
            import httpx
            for target_host, target_port in target_services:
                try:
                    check_url = f"http://{target_host}:{target_port}/wba/hosted-did/check/{requester_id}"
                    
                    async with httpx.AsyncClient() as client:
                        response = await client.get(check_url, timeout=10.0)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('success') and result.get('results'):
                                for res in result['results']:
                                    res['source_host'] = target_host
                                    res['source_port'] = target_port
                                all_results.extend(result['results'])
                        
                except Exception as e:
                    logger.warning(f"检查托管服务 {target_host}:{target_port} 失败: {e}")
            
            return True, all_results, ""
            
        except Exception as e:
            error_msg = f"检查托管DID结果失败: {e}"
            logger.error(error_msg)
            return False, [], error_msg

    async def process_hosted_did_results(self, results: List[Dict[str, Any]]) -> int:
        """
        处理托管DID结果
        
        使用现有的create_hosted_did方法保存到本地
        在anp_users/下创建user_hosted_{host}_{port}_{id}/目录
        """
        processed_count = 0
        
        for result in results:
            try:
                if result.get('success') and result.get('hosted_did_document'):
                    hosted_did_doc = result['hosted_did_document']
                    source_host = result.get('source_host', 'unknown')
                    source_port = result.get('source_port', 9527)
                    
                    # 使用现有的create_hosted_did方法
                    # 这会在anp_users/下创建user_hosted_{host}_{port}_{id}/目录
                    success, hosted_result = self.create_hosted_did(
                        source_host, str(source_port), hosted_did_doc
                    )
                    
                    if success:
                        # 确认收到结果
                        await self._acknowledge_hosted_did_result(
                            result.get('result_id', ''), source_host, source_port
                        )
                        
                        logger.info(f"托管DID已保存: {hosted_result}")
                        logger.info(f"托管DID ID: {hosted_did_doc.get('id')}")
                        processed_count += 1
                    else:
                        logger.error(f"保存托管DID失败: {hosted_result}")
                else:
                    logger.warning(f"托管DID申请失败: {result.get('error_message', '未知错误')}")
                    
            except Exception as e:
                logger.error(f"处理托管DID结果失败: {e}")
        
        return processed_count

    async def _acknowledge_hosted_did_result(self, result_id: str, source_host: str, source_port: int):
        """确认收到托管DID结果"""
        try:
            if not result_id:
                return
                
            ack_url = f"http://{source_host}:{source_port}/wba/hosted-did/acknowledge/{result_id}"
            
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(ack_url, timeout=10.0)
                if response.status_code == 200:
                    logger.debug(f"已确认托管DID结果: {result_id}")
                else:
                    logger.warning(f"确认托管DID结果失败: {response.status_code}")
                    
        except Exception as e:
            logger.warning(f"确认托管DID结果时出错: {e}")

    async def poll_hosted_did_results(self, interval: int = 30, max_polls: int = 20) -> int:
        """
        轮询托管DID结果
        
        Args:
            interval: 轮询间隔（秒）
            max_polls: 最大轮询次数
            
        Returns:
            int: 总共处理的结果数量
        """
        total_processed = 0
        
        for i in range(max_polls):
            try:
                success, results, error = await self.check_hosted_did_results()
                
                if success and results:
                    processed = await self.process_hosted_did_results(results)
                    total_processed += processed
                    
                    if processed > 0:
                        logger.info(f"轮询第{i+1}次: 处理了{processed}个托管DID结果")
                
                if i < max_polls - 1:  # 不是最后一次
                    await asyncio.sleep(interval)
                    
            except Exception as e:
                logger.error(f"轮询托管DID结果失败: {e}")
                await asyncio.sleep(interval)
        
        return total_processed

    def create_hosted_did(self, host: str, port: str, did_document: dict) -> Tuple[bool, Any]:
        """
        [新] 创建一个托管DID。此方法将调用数据管理器来处理持久化和内存加载。
        """
        manager = get_user_data_manager()
        success, new_user_data = manager.create_hosted_user(
            parent_user_data=self.user_data,
            host=host,
            port=port,
            did_document=did_document
        )
        if success:
            # 返回新创建的 ANPUser 实例
            return True, ANPUser(user_data=new_user_data)
        return False, None


    def start(self, mode: ServerMode, ws_proxy_url=None, host="0.0.0.0", port=8000):
        if mode == ServerMode.AGENT_SELF_SERVICE:
            self._start_self_service(host, port)
        elif mode == ServerMode.AGENT_WS_PROXY_CLIENT:
            self._start_self_service(host, port)
            asyncio.create_task(self._start_ws_proxy_client(ws_proxy_url))
        # 其他模式由ANPSDK主导

    def _start_self_service(self, host, port):
        self.app = FastAPI(title=f"{self.name} LocalAgent", description="LocalAgent Self-Service API", version="1.0.0")
        self._register_self_routes()
        import uvicorn
        uvicorn.run(self.app, host=host, port=port)

    def _register_self_routes(self):
        from fastapi import Request

        @self.app.post("/agent/api/{agent_id}/{path:path}")
        async def agent_api(agent_id: str, path: str, request: Request):
            if agent_id != self.id:
                return JSONResponse(status_code=404, content={"status": "error", "message": "Agent ID not found"})
            request_data = await request.json()
            return await self.handle_request(agent_id, request_data, request)

        # 可扩展更多自服务API

    async def _start_ws_proxy_client(self, ws_proxy_url):
        import websockets
        while True:
            try:
                async with websockets.connect(ws_proxy_url) as ws:
                    await self._ws_proxy_loop(ws)
            except Exception as e:
                self.logger.error(f"WebSocket代理连接失败: {e}")
                await asyncio.sleep(5)

    async def _ws_proxy_loop(self, ws):
        await ws.send(json.dumps({"type": "register", "did": self.id}))
        async for msg in ws:
            data = json.loads(msg)
            # 处理来自中心的请求
            # 这里可以根据data内容调用self.handle_request等
            # 例如:
            req_type = data.get("type")
            if req_type == "api_call":
                # 伪造一个Request对象
                class DummyRequest:
                    def __init__(self, json_data):
                        self._json = json_data
                    async def json(self):
                        return self._json
                response = await self.handle_request(self.id, data, DummyRequest(data))
                await ws.send(json.dumps({"type": "response", "data": response}))
            # 可扩展其他消息类型
