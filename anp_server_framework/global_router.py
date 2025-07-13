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

import logging
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class APIRoute:
    """API路由信息"""
    
    def __init__(self, did: str, path: str, handler: Callable, agent_name: str, methods: List[str]):
        self.did = did
        self.path = path
        self.handler = handler
        self.agent_name = agent_name
        self.methods = methods
        self.registered_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "did": self.did,
            "path": self.path,
            "agent_name": self.agent_name,
            "methods": self.methods,
            "registered_at": self.registered_at.isoformat(),
            "handler_name": getattr(self.handler, '__name__', 'unknown')
        }


class GlobalRouter:
    """全局API路由管理器"""
    
    # 类级别的路由注册表
    _routes: Dict[str, Dict[str, APIRoute]] = {}  # {did: {path: APIRoute}}
    _route_conflicts: List[Dict[str, Any]] = []  # 冲突记录
    
    @classmethod
    def register_api(cls, did: str, path: str, handler: Callable, 
                    agent_name: str, methods: Optional[List[str]] = None) -> bool:
        """注册API路由
        
        Args:
            did: DID标识
            path: API路径
            handler: 处理函数
            agent_name: Agent名称
            methods: HTTP方法列表
            
        Returns:
            bool: 注册是否成功
        """
        methods = methods or ["GET", "POST"]
        
        # 初始化DID的路由表
        if did not in cls._routes:
            cls._routes[did] = {}
        
        # 检查路径冲突
        if path in cls._routes[did]:
            existing_route = cls._routes[did][path]
            conflict_info = {
                "did": did,
                "path": path,
                "existing_agent": existing_route.agent_name,
                "new_agent": agent_name,
                "conflict_time": datetime.now().isoformat(),
                "action": "ignored"  # 忽略新的注册
            }
            cls._route_conflicts.append(conflict_info)
            
            logger.warning(f"⚠️  API路径冲突: {did}{path}")
            logger.warning(f"   现有Agent: {existing_route.agent_name}")
            logger.warning(f"   新Agent: {agent_name}")
            logger.warning(f"   🔧 使用第一个注册的路由，忽略后续注册")
            return False
        
        # 注册新路由
        route = APIRoute(did, path, handler, agent_name, methods)
        cls._routes[did][path] = route
        
        # 同时注册到ANPUser的api_routes（保持兼容性）
        cls._register_to_anp_user(did, path, handler)
        
        logger.debug(f"🔗 全局路由注册: {did}{path} <- {agent_name}")
        return True
    
    @classmethod
    def _register_to_anp_user(cls, did: str, path: str, handler: Callable):
        """注册到ANPUser的api_routes（保持兼容性）"""
        try:
            from anp_sdk.anp_user import ANPUser
            from anp_sdk.anp_sdk_user_data import get_user_data_manager
            
            user_data_manager = get_user_data_manager()
            user_data = user_data_manager.get_user_data(did)
            
            if user_data:
                # 使用from_did方法确保使用缓存的实例
                anp_user = ANPUser.from_did(did)
                anp_user.api_routes[path] = handler
                
                # 注册到ANP_Server的api_registry
                from anp_server.anp_server import ANP_Server
                if hasattr(ANP_Server, 'instance') and ANP_Server.instance:
                    if did not in ANP_Server.instance.api_registry:
                        ANP_Server.instance.api_registry[did] = []
                    
                    api_info = {
                        "path": f"/agent/api/{did}{path}",
                        "methods": ["GET", "POST"],
                        "summary": handler.__doc__ or f"API接口{path}",
                        "agent_id": did,
                        "agent_name": "unknown"
                    }
                    ANP_Server.instance.api_registry[did].append(api_info)
        except Exception as e:
            logger.warning(f"注册到ANPUser失败: {e}")
    
    @classmethod
    def get_handler(cls, did: str, path: str) -> Optional[Callable]:
        """获取API处理器"""
        if did in cls._routes and path in cls._routes[did]:
            return cls._routes[did][path].handler
        return None
    
    @classmethod
    def list_routes(cls, did: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出路由信息"""
        routes = []
        
        if did:
            # 列出特定DID的路由
            if did in cls._routes:
                for route in cls._routes[did].values():
                    routes.append(route.to_dict())
        else:
            # 列出所有路由
            for did_routes in cls._routes.values():
                for route in did_routes.values():
                    routes.append(route.to_dict())
        
        return routes
    
    @classmethod
    def get_conflicts(cls) -> List[Dict[str, Any]]:
        """获取冲突记录"""
        return cls._route_conflicts.copy()
    
    @classmethod
    def clear_routes(cls, did: Optional[str] = None):
        """清除路由（主要用于测试）"""
        if did:
            if did in cls._routes:
                del cls._routes[did]
                logger.debug(f"清除DID {did} 的所有路由")
        else:
            cls._routes.clear()
            cls._route_conflicts.clear()
            logger.debug("清除所有路由")
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取路由统计信息"""
        total_routes = sum(len(routes) for routes in cls._routes.values())
        did_count = len(cls._routes)
        conflict_count = len(cls._route_conflicts)
        
        return {
            "total_routes": total_routes,
            "did_count": did_count,
            "conflict_count": conflict_count,
            "routes_per_did": {did: len(routes) for did, routes in cls._routes.items()}
        }
