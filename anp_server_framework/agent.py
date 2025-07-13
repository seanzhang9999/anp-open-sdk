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
from typing import Dict, Any, Callable, Optional
from datetime import datetime

from anp_sdk.anp_user import ANPUser

logger = logging.getLogger(__name__)


class Agent:
    """Agent类 - 功能载体，通过装饰器发布API和消息处理功能"""
    
    def __init__(self, anp_user: ANPUser, name: str, shared: bool = False, 
                 prefix: Optional[str] = None, primary_agent: bool = False):
        """初始化Agent
        
        Args:
            anp_user: ANPUser实例（DID身份容器）
            name: Agent名称
            shared: 是否共享DID模式
            prefix: 共享模式下的API前缀
            primary_agent: 是否为主Agent（拥有消息处理权限）
        """
        self.anp_user = anp_user
        self.name = name
        self.shared = shared
        self.prefix = prefix
        self.primary_agent = primary_agent
        self.created_at = datetime.now()
        
        # 功能注册表
        self.api_routes = {}  # path -> handler
        self.message_handlers = {}  # type -> handler
        
        logger.info(f"✅ Agent创建成功: {name}")
        logger.info(f"   DID: {anp_user.id} ({'共享' if shared else '独占'})")
        if prefix:
            logger.info(f"   Prefix: {prefix}")
        if primary_agent:
            logger.info(f"   主Agent: 是")
    
    def api(self, path: str, methods=None):
        """API装饰器"""
        methods = methods or ["GET", "POST"]
        
        def decorator(func):
            # 计算完整路径
            full_path = f"{self.prefix}{path}" if self.prefix else path
            
            # 注册到Agent的路由表
            self.api_routes[path] = func
            
            # 注册到ANPUser的API路由系统（这是关键！）
            # 对于共享DID，我们需要确保API路由不会被覆盖
            if full_path not in self.anp_user.api_routes:
                self.anp_user.api_routes[full_path] = func
            else:
                # 如果路径已存在，检查是否是同一个Agent注册的
                existing_handler = self.anp_user.api_routes[full_path]
                if existing_handler != func:
                    logger.warning(f"⚠️  API路径冲突: {full_path}")
                    logger.warning(f"   现有处理器: {getattr(existing_handler, '__name__', 'unknown')}")
                    logger.warning(f"   新处理器: {getattr(func, '__name__', 'unknown')} (来自 {self.name})")
                    logger.warning(f"   🔧 覆盖现有处理器")
                self.anp_user.api_routes[full_path] = func
            
            # 注册到全局路由（通过GlobalRouter）
            from anp_server_framework.global_router import GlobalRouter
            GlobalRouter.register_api(
                did=self.anp_user.id,
                path=full_path,
                handler=func,
                agent_name=self.name,
                methods=methods
            )
            
            logger.info(f"🔗 API注册成功: {self.anp_user.id}{full_path} <- {self.name}")
            return func
        
        return decorator
    
    def message_handler(self, msg_type: str):
        """消息处理器装饰器"""
        def decorator(func):
            # 检查消息处理权限
            if not self._can_handle_message():
                error_msg = self._get_message_permission_error()
                logger.error(f"❌ 消息处理器注册失败: {error_msg}")
                raise PermissionError(error_msg)
            
            # 注册到Agent的消息处理器表
            self.message_handlers[msg_type] = func
            
            # 注册到全局消息管理器
            from anp_server_framework.global_message_manager import GlobalMessageManager
            GlobalMessageManager.register_handler(
                did=self.anp_user.id,
                msg_type=msg_type,
                handler=func,
                agent_name=self.name
            )
            
            logger.info(f"💬 消息处理器注册成功: {self.anp_user.id}:{msg_type} <- {self.name}")
            return func
        
        return decorator
    
    def _can_handle_message(self) -> bool:
        """检查是否可以处理消息"""
        if not self.shared:
            # 独占模式：自动有消息处理权限
            return True
        else:
            # 共享模式：只有主Agent可以处理消息
            return self.primary_agent
    
    def _get_message_permission_error(self) -> str:
        """获取消息权限错误信息"""
        if self.shared and not self.primary_agent:
            return (f"Agent '{self.name}' 无消息处理权限\n"
                   f"原因: 共享DID模式下，只有主Agent可以处理消息\n"
                   f"解决方案: 设置 primary_agent=True 或使用独占DID")
        else:
            return "未知的消息权限错误"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "did": self.anp_user.id,
            "shared": self.shared,
            "prefix": self.prefix,
            "primary_agent": self.primary_agent,
            "created_at": self.created_at.isoformat(),
            "api_count": len(self.api_routes),
            "message_handler_count": len(self.message_handlers)
        }
    
    def __repr__(self):
        return f"Agent(name='{self.name}', did='{self.anp_user.id}', shared={self.shared})"
