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
import logging
import json
from typing import Dict, Any, Optional
import httpx
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class FrameworkProxy:
    """Framework服务代理 - 负责将请求转发到Framework服务"""
    
    def __init__(self, framework_host: str = "localhost", framework_port: int = 9528):
        self.framework_base_url = f"http://{framework_host}:{framework_port}"
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def forward_agent_request(self, did: str, subpath: str, request_data: Dict[str, Any], 
                                  request: Request) -> Dict[str, Any]:
        """转发Agent请求到Framework服务"""
        try:
            # 构造Framework服务的URL
            framework_url = f"{self.framework_base_url}/agent/api/{did}/{subpath}"
            
            # 转发查询参数
            params = dict(request.query_params)
            
            # 发送请求到Framework服务
            response = await self.client.post(
                framework_url,
                json=request_data,
                params=params,
                headers={
                    "Content-Type": "application/json",
                    "X-Forwarded-From": "anp-server-gateway"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Framework服务返回错误: {response.status_code} - {response.text}")
                return {
                    "status": "error", 
                    "message": f"Framework服务错误: {response.status_code}",
                    "details": response.text
                }
                
        except httpx.ConnectError:
            logger.error(f"无法连接到Framework服务: {self.framework_base_url}")
            return {
                "status": "error",
                "message": "Framework服务不可用",
                "framework_url": self.framework_base_url
            }
        except Exception as e:
            logger.error(f"转发请求到Framework服务失败: {e}")
            return {
                "status": "error",
                "message": f"代理转发失败: {str(e)}"
            }
    
    async def forward_message_request(self, did: str, request_data: Dict[str, Any], 
                                    request: Request) -> Dict[str, Any]:
        """转发消息请求到Framework服务"""
        try:
            framework_url = f"{self.framework_base_url}/agent/message/{did}/post"
            
            params = dict(request.query_params)
            
            response = await self.client.post(
                framework_url,
                json=request_data,
                params=params,
                headers={
                    "Content-Type": "application/json",
                    "X-Forwarded-From": "anp-server-gateway"
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Framework服务消息处理错误: {response.status_code} - {response.text}")
                return {
                    "anp_result": {
                        "status": "error", 
                        "message": f"Framework服务错误: {response.status_code}"
                    }
                }
                
        except Exception as e:
            logger.error(f"转发消息到Framework服务失败: {e}")
            return {
                "anp_result": {
                    "status": "error",
                    "message": f"消息代理转发失败: {str(e)}"
                }
            }
    
    async def check_framework_health(self) -> bool:
        """检查Framework服务健康状态"""
        try:
            response = await self.client.get(f"{self.framework_base_url}/health")
            return response.status_code == 200
        except:
            return False
    
    async def get_framework_agents(self) -> Dict[str, Any]:
        """获取Framework服务中的Agent列表"""
        try:
            response = await self.client.get(f"{self.framework_base_url}/agents")
            if response.status_code == 200:
                return response.json()
            else:
                return {"agents": [], "total": 0, "error": "无法获取Agent列表"}
        except Exception as e:
            return {"agents": [], "total": 0, "error": str(e)}


class DIDRegistry:
    """DID注册表 - 管理DID到Framework服务的映射"""
    
    def __init__(self):
        # DID -> Framework服务信息的映射
        self.did_mappings: Dict[str, Dict[str, Any]] = {}
        # 默认Framework服务
        self.default_framework = FrameworkProxy()
    
    def register_did(self, did: str, framework_host: str = "localhost", 
                    framework_port: int = 9528, metadata: Dict[str, Any] = None):
        """注册DID到特定的Framework服务"""
        self.did_mappings[did] = {
            "framework_host": framework_host,
            "framework_port": framework_port,
            "framework_proxy": FrameworkProxy(framework_host, framework_port),
            "metadata": metadata or {},
            "registered_at": asyncio.get_event_loop().time()
        }
        logger.info(f"✅ DID注册成功: {did} -> {framework_host}:{framework_port}")
    
    def get_framework_proxy(self, did: str) -> FrameworkProxy:
        """获取DID对应的Framework代理"""
        if did in self.did_mappings:
            return self.did_mappings[did]["framework_proxy"]
        else:
            # 使用默认Framework服务
            logger.debug(f"DID {did} 未注册，使用默认Framework服务")
            return self.default_framework
    
    def list_registered_dids(self) -> Dict[str, Any]:
        """列出所有注册的DID"""
        result = {}
        for did, info in self.did_mappings.items():
            result[did] = {
                "framework_host": info["framework_host"],
                "framework_port": info["framework_port"],
                "metadata": info["metadata"],
                "registered_at": info["registered_at"]
            }
        return result
    
    async def sync_with_framework(self):
        """与Framework服务同步DID信息"""
        logger.info("🔄 开始与Framework服务同步DID信息...")
        
        # 获取默认Framework服务中的Agent列表
        agents_info = await self.default_framework.get_framework_agents()
        
        if "agents" in agents_info:
            for agent_info in agents_info["agents"]:
                did = agent_info.get("did")
                if did and did not in self.did_mappings:
                    # 自动注册发现的DID
                    self.register_did(
                        did, 
                        metadata={
                            "auto_discovered": True,
                            "agent_name": agent_info.get("name"),
                            "shared": agent_info.get("shared", False)
                        }
                    )
                    logger.info(f"🔍 自动发现并注册DID: {did}")
        
        logger.info(f"✅ DID同步完成，当前注册DID数量: {len(self.did_mappings)}")


class GatewayProxy:
    """网关代理 - anp_server的核心代理组件"""
    
    def __init__(self):
        self.did_registry = DIDRegistry()
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "framework_errors": 0
        }
    
    async def initialize(self):
        """初始化网关代理"""
        logger.info("🚀 初始化网关代理...")
        
        # 检查Framework服务健康状态
        is_healthy = await self.did_registry.default_framework.check_framework_health()
        if is_healthy:
            logger.info("✅ Framework服务健康检查通过")
            # 同步DID信息
            await self.did_registry.sync_with_framework()
        else:
            logger.warning("⚠️  Framework服务健康检查失败，将在运行时重试")
    
    async def handle_agent_api_request(self, did: str, subpath: str, 
                                     request_data: Dict[str, Any], request: Request):
        """处理Agent API请求"""
        self.stats["total_requests"] += 1
        
        try:
            # 获取对应的Framework代理
            framework_proxy = self.did_registry.get_framework_proxy(did)
            
            # 转发请求
            result = await framework_proxy.forward_agent_request(did, subpath, request_data, request)
            
            if result.get("status") == "error":
                self.stats["failed_requests"] += 1
                if "Framework服务" in result.get("message", ""):
                    self.stats["framework_errors"] += 1
            else:
                self.stats["successful_requests"] += 1
            
            return result
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"网关代理处理API请求失败: {e}")
            return {
                "status": "error",
                "message": f"网关代理错误: {str(e)}"
            }
    
    async def handle_agent_message_request(self, did: str, request_data: Dict[str, Any], 
                                         request: Request):
        """处理Agent消息请求"""
        self.stats["total_requests"] += 1
        
        try:
            framework_proxy = self.did_registry.get_framework_proxy(did)
            result = await framework_proxy.forward_message_request(did, request_data, request)
            
            if result.get("anp_result", {}).get("status") == "error":
                self.stats["failed_requests"] += 1
            else:
                self.stats["successful_requests"] += 1
            
            return result
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"网关代理处理消息请求失败: {e}")
            return {
                "anp_result": {
                    "status": "error",
                    "message": f"网关代理错误: {str(e)}"
                }
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取网关统计信息"""
        return {
            **self.stats,
            "registered_dids": len(self.did_registry.did_mappings),
            "success_rate": (
                self.stats["successful_requests"] / max(self.stats["total_requests"], 1) * 100
            )
        }
    
    def get_registered_dids(self) -> Dict[str, Any]:
        """获取注册的DID信息"""
        return self.did_registry.list_registered_dids()


# 全局网关代理实例
gateway_proxy = GatewayProxy()
