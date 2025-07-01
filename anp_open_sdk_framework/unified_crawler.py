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
import json
import logging
from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod

from .unified_caller import UnifiedCaller
from .local_methods.local_methods_doc import LocalMethodsDocGenerator

logger = logging.getLogger(__name__)


class ResourceDiscoverer(ABC):
    """资源发现器基类"""
    
    @abstractmethod
    async def discover(self) -> List[Dict]:
        """发现资源"""
        pass


class LocalMethodsDiscoverer(ResourceDiscoverer):
    """本地方法发现器"""
    
    def __init__(self, sdk):
        self.sdk = sdk
        self.doc_generator = LocalMethodsDocGenerator()
    
    async def discover(self) -> List[Dict]:
        """发现本地方法"""
        methods = []
        for method_key, method_info in self.doc_generator.list_all_methods().items():
            methods.append({
                "type": "local_method",
                "key": method_key,
                "name": method_info["name"],
                "agent_name": method_info.get("agent_name", ""),
                "agent_did": method_info.get("agent_did", ""),
                "description": method_info.get("description", ""),
                "tags": method_info.get("tags", []),
                "is_async": method_info.get("is_async", False)
            })
        return methods


class RemoteAgentDiscoverer(ResourceDiscoverer):
    """远程Agent发现器"""
    
    def __init__(self, sdk):
        self.sdk = sdk
        self.caller = UnifiedCaller(sdk)
    
    async def discover(self) -> List[Dict]:
        """发现远程Agent"""
        agents = []
        # 这里可以实现具体的Agent发现逻辑
        # 例如通过DID解析、网络扫描等方式
        return agents


class UnifiedCrawler:
    """统一爬虫 - 整合本地方法和远程Agent资源发现与调用"""
    
    def __init__(self, sdk):
        self.sdk = sdk
        self.caller = UnifiedCaller(sdk)
        self.discoverers = {
            "local_methods": LocalMethodsDiscoverer(sdk),
            "remote_agents": RemoteAgentDiscoverer(sdk)
        }
        self.resource_cache = {}
    
    async def discover_all_resources(self, refresh_cache: bool = False) -> Dict[str, List[Dict]]:
        """发现所有资源"""
        if not refresh_cache and self.resource_cache:
            return self.resource_cache
        
        resources = {}
        for resource_type, discoverer in self.discoverers.items():
            try:
                logger.info(f"🔍 发现 {resource_type} 资源...")
                resources[resource_type] = await discoverer.discover()
                logger.info(f"✅ 发现 {len(resources[resource_type])} 个 {resource_type} 资源")
            except Exception as e:
                logger.error(f"❌ 发现 {resource_type} 资源时出错: {e}")
                resources[resource_type] = []
        
        self.resource_cache = resources
        return resources
    
    async def search_resources(self, keyword: str, resource_types: Optional[List[str]] = None) -> List[Dict]:
        """搜索资源"""
        resources = await self.discover_all_resources()
        results = []
        
        search_types = resource_types or list(resources.keys())
        
        for resource_type in search_types:
            if resource_type not in resources:
                continue
                
            for resource in resources[resource_type]:
                # 简单的关键词匹配
                if (keyword.lower() in resource.get("name", "").lower() or
                    keyword.lower() in resource.get("description", "").lower() or
                    any(keyword.lower() in tag.lower() for tag in resource.get("tags", []))):
                    results.append(resource)
        
        return results
    
    async def intelligent_call(self, task_description: str, **kwargs) -> Any:
        """智能调用 - 根据任务描述自动选择合适的资源并调用"""
        logger.info(f"🤖 智能调用任务: {task_description}")
        
        # 搜索相关资源
        resources = await self.search_resources(task_description)
        
        if not resources:
            raise ValueError(f"未找到与任务 '{task_description}' 相关的资源")
        
        # 选择最佳资源（这里使用简单策略，实际可以更复杂）
        best_resource = resources[0]
        logger.info(f"📋 选择资源: {best_resource['name']} ({best_resource['type']})")
        
        # 执行调用
        if best_resource["type"] == "local_method":
            return await self.caller.call(
                best_resource["agent_did"], 
                best_resource["name"], 
                **kwargs
            )
        elif best_resource["type"] == "remote_agent":
            # 远程Agent调用逻辑
            return await self.caller.call(
                best_resource["did"], 
                kwargs.get("api_path", "/"), 
                **kwargs
            )
        else:
            raise ValueError(f"不支持的资源类型: {best_resource['type']}")
    
    async def call_by_name(self, resource_name: str, *args, **kwargs) -> Any:
        """通过资源名称调用"""
        resources = await self.discover_all_resources()
        
        for resource_type, resource_list in resources.items():
            for resource in resource_list:
                if resource["name"] == resource_name:
                    if resource["type"] == "local_method":
                        return await self.caller.call(
                            resource["agent_did"], 
                            resource["name"], 
                            *args, **kwargs
                        )
                    elif resource["type"] == "remote_agent":
                        return await self.caller.call(
                            resource["did"], 
                            kwargs.get("api_path", "/"), 
                            *args, **kwargs
                        )
        
        raise ValueError(f"未找到资源: {resource_name}")
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """获取资源摘要"""
        if not self.resource_cache:
            return {"message": "请先调用 discover_all_resources() 发现资源"}
        
        summary = {}
        for resource_type, resources in self.resource_cache.items():
            summary[resource_type] = {
                "count": len(resources),
                "names": [r.get("name", "") for r in resources[:10]]  # 只显示前10个
            }
        
        return summary
