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


class MessageHandler:
    """消息处理器信息"""
    
    def __init__(self, did: str, msg_type: str, handler: Callable, agent_name: str):
        self.did = did
        self.msg_type = msg_type
        self.handler = handler
        self.agent_name = agent_name
        self.registered_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "did": self.did,
            "msg_type": self.msg_type,
            "agent_name": self.agent_name,
            "registered_at": self.registered_at.isoformat(),
            "handler_name": getattr(self.handler, '__name__', 'unknown')
        }


class GlobalMessageManager:
    """全局消息处理管理器"""
    
    # 类级别的消息处理器注册表
    _handlers: Dict[str, Dict[str, MessageHandler]] = {}  # {did: {msg_type: MessageHandler}}
    _handler_conflicts: List[Dict[str, Any]] = []  # 冲突记录
    
    @classmethod
    def register_handler(cls, did: str, msg_type: str, handler: Callable, agent_name: str) -> bool:
        """注册消息处理器
        
        Args:
            did: DID标识
            msg_type: 消息类型
            handler: 处理函数
            agent_name: Agent名称
            
        Returns:
            bool: 注册是否成功
        """
        # 初始化DID的处理器表
        if did not in cls._handlers:
            cls._handlers[did] = {}
        
        # 检查消息类型冲突
        if msg_type in cls._handlers[did]:
            existing_handler = cls._handlers[did][msg_type]
            conflict_info = {
                "did": did,
                "msg_type": msg_type,
                "existing_agent": existing_handler.agent_name,
                "new_agent": agent_name,
                "conflict_time": datetime.now().isoformat(),
                "action": "ignored"  # 忽略新的注册
            }
            cls._handler_conflicts.append(conflict_info)
            
            logger.warning(f"⚠️  消息处理器冲突: {did}:{msg_type}")
            logger.warning(f"   现有Agent: {existing_handler.agent_name}")
            logger.warning(f"   新Agent: {agent_name}")
            logger.warning(f"   🔧 使用第一个注册的处理器，忽略后续注册")
            return False
        
        # 注册新处理器
        message_handler = MessageHandler(did, msg_type, handler, agent_name)
        cls._handlers[did][msg_type] = message_handler
        
        # 同时注册到ANPUser的message_handlers（保持兼容性）
        cls._register_to_anp_user(did, msg_type, handler, agent_name)
        
        logger.debug(f"💬 全局消息处理器注册: {did}:{msg_type} <- {agent_name}")
        return True
    
    @classmethod
    def _register_to_anp_user(cls, did: str, msg_type: str, handler: Callable, agent_name: str):
        """注册到ANPUser的message_handlers（保持兼容性）"""
        try:
            from anp_sdk.anp_user import ANPUser
            from anp_sdk.anp_sdk_user_data import get_user_data_manager
            
            user_data_manager = get_user_data_manager()
            user_data = user_data_manager.get_user_data(did)
            
            if user_data:
                anp_user = ANPUser(user_data)
                # 使用ANPUser的内部注册方法，包含冲突检测
                anp_user._register_message_handler_internal(msg_type, handler, agent_name)
        except Exception as e:
            logger.warning(f"注册到ANPUser失败: {e}")
    
    @classmethod
    def get_handler(cls, did: str, msg_type: str) -> Optional[Callable]:
        """获取消息处理器"""
        if did in cls._handlers and msg_type in cls._handlers[did]:
            return cls._handlers[did][msg_type].handler
        return None
    
    @classmethod
    def list_handlers(cls, did: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出消息处理器信息"""
        handlers = []
        
        if did:
            # 列出特定DID的处理器
            if did in cls._handlers:
                for handler in cls._handlers[did].values():
                    handlers.append(handler.to_dict())
        else:
            # 列出所有处理器
            for did_handlers in cls._handlers.values():
                for handler in did_handlers.values():
                    handlers.append(handler.to_dict())
        
        return handlers
    
    @classmethod
    def get_conflicts(cls) -> List[Dict[str, Any]]:
        """获取冲突记录"""
        return cls._handler_conflicts.copy()
    
    @classmethod
    def clear_handlers(cls, did: Optional[str] = None):
        """清除消息处理器（主要用于测试）"""
        if did:
            if did in cls._handlers:
                del cls._handlers[did]
                logger.debug(f"清除DID {did} 的所有消息处理器")
        else:
            cls._handlers.clear()
            cls._handler_conflicts.clear()
            logger.debug("清除所有消息处理器")
    
    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """获取消息处理器统计信息"""
        total_handlers = sum(len(handlers) for handlers in cls._handlers.values())
        did_count = len(cls._handlers)
        conflict_count = len(cls._handler_conflicts)
        
        return {
            "total_handlers": total_handlers,
            "did_count": did_count,
            "conflict_count": conflict_count,
            "handlers_per_did": {did: len(handlers) for did, handlers in cls._handlers.items()}
        }
