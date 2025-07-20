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
from typing import Dict, Any, Callable, List, Optional
from datetime import datetime, time

from starlette.responses import StreamingResponse

logger = logging.getLogger(__name__)


class GroupAgent:
    """群组成员Agent信息"""

    def __init__(self, id: str, name: str, port: int = 0, metadata: Dict[str, Any] = None):
        self.id = id
        self.name = name
        self.port = port
        self.metadata = metadata or {}
        self.joined_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "port": self.port,
            "metadata": self.metadata,
            "joined_at": self.joined_at.isoformat()
        }


class Message:
    """群组消息"""

    def __init__(self, type: str, content: Any, sender_id: str, group_id: str,
                 timestamp: float, metadata: Dict[str, Any] = None):
        self.type = type
        self.content = content
        self.sender_id = sender_id
        self.group_id = group_id
        self.timestamp = timestamp
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "sender_id": self.sender_id,
            "group_id": self.group_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class GroupRunner:
    """群组运行器基类"""

    def __init__(self, group_id: str):
        self.group_id = group_id
        self.agents: Dict[str, GroupAgent] = {}
        self.listeners: Dict[str, asyncio.Queue] = {}
        self.created_at = datetime.now()

    async def on_agent_join(self, agent: GroupAgent) -> bool:
        """Agent加入群组时的处理，返回是否允许加入"""
        return True

    async def on_agent_leave(self, agent: GroupAgent):
        """Agent离开群组时的处理"""
        pass

    async def on_message(self, message: Message) -> Optional[Message]:
        """处理群组消息，返回响应消息（可选）"""
        return None

    def is_member(self, agent_id: str) -> bool:
        """检查是否为群组成员"""
        return agent_id in self.agents

    def get_members(self) -> List[GroupAgent]:
        """获取所有成员"""
        return list(self.agents.values())

    async def remove_member(self, agent_id: str) -> bool:
        """移除成员"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            await self.on_agent_leave(agent)
            del self.agents[agent_id]
            return True
        return False

    def register_listener(self, agent_id: str, queue: asyncio.Queue):
        """注册事件监听器"""
        self.listeners[agent_id] = queue

    def unregister_listener(self, agent_id: str):
        """注销事件监听器"""
        if agent_id in self.listeners:
            del self.listeners[agent_id]

    async def broadcast_message(self, message: Dict[str, Any]):
        """广播消息给所有监听器"""
        for queue in self.listeners.values():
            try:
                await queue.put(message)
            except Exception as e:
                logger.error(f"广播消息失败: {e}")


class GlobalGroupManager:
    """全局群组管理器"""

    # 类级别的群组注册表
    _groups: Dict[str, GroupRunner] = {}  # {group_id: GroupRunner}
    _group_patterns: Dict[str, type] = {}  # {url_pattern: GroupRunner类}
    _group_stats: Dict[str, Any] = {}  # 群组统计信息

    @classmethod
    def register_runner(cls, group_id: str, runner_class: type, url_pattern: Optional[str] = None):
        """注册群组运行器"""
        if group_id in cls._groups:
            logger.warning(f"群组 {group_id} 已存在，将被覆盖")

        # 创建运行器实例
        runner = runner_class(group_id)
        cls._groups[group_id] = runner

        # 注册URL模式（如果提供）
        if url_pattern:
            cls._group_patterns[url_pattern] = runner_class

        # 初始化统计信息
        cls._group_stats[group_id] = {
            "created_at": datetime.now().isoformat(),
            "member_count": 0,
            "message_count": 0,
            "last_activity": None
        }

        logger.debug(f"✅ 群组运行器注册成功: {group_id}")

    @classmethod
    def unregister_runner(cls, group_id: str):
        """注销群组运行器"""
        if group_id in cls._groups:
            del cls._groups[group_id]
            if group_id in cls._group_stats:
                del cls._group_stats[group_id]
            logger.debug(f"🗑️ 群组运行器已注销: {group_id}")

    @classmethod
    def get_runner(cls, group_id: str) -> Optional[GroupRunner]:
        """获取群组运行器"""
        return cls._groups.get(group_id)

    @classmethod
    def list_groups(cls) -> List[str]:
        """列出所有群组ID"""
        return list(cls._groups.keys())

    @classmethod
    def get_group_stats(cls, group_id: str = None) -> Dict[str, Any]:
        """获取群组统计信息"""
        if group_id:
            return cls._group_stats.get(group_id, {})
        return cls._group_stats.copy()

    @classmethod
    def update_group_activity(cls, group_id: str, activity_type: str = "message"):
        """更新群组活动统计"""
        if group_id in cls._group_stats:
            cls._group_stats[group_id]["last_activity"] = datetime.now().isoformat()
            if activity_type == "message":
                cls._group_stats[group_id]["message_count"] += 1

    @classmethod
    def clear_groups(cls):
        """清除所有群组（主要用于测试）"""
        cls._groups.clear()
        cls._group_patterns.clear()
        cls._group_stats.clear()
        logger.debug("清除所有群组")

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
    def route_group_request(cls, did: str, group_id: str, request_type: str,
                            request_data: Dict[str, Any], request) -> Any:
        """路由群组请求"""
        # 获取群组运行器
        runner = GlobalGroupManager.get_runner(group_id)
        if not runner:
            return {"status": "error", "message": f"群组不存在: {group_id}"}

        # 更新活动统计
        GlobalGroupManager.update_group_activity(group_id, request_type)

        # 根据请求类型处理
        if request_type == "join":
            return cls._handle_group_join(runner, request_data)
        elif request_type == "leave":
            return cls._handle_group_leave(runner, request_data)
        elif request_type == "message":
            return cls._handle_group_message(runner, request_data)
        elif request_type == "connect":
            return cls._handle_group_connect(runner, request_data)
        elif request_type == "members":
            return cls._handle_group_members(runner, request_data)
        else:
            return {"status": "error", "message": f"未知的群组请求类型: {request_type}"}

    @classmethod
    async def _handle_group_join(cls, runner: GroupRunner, request_data: Dict[str, Any]):
        """处理加入群组请求"""
        req_did = request_data.get("req_did")
        group_agent = GroupAgent(
            id=req_did,
            name=request_data.get("name", req_did),
            port=request_data.get("port", 0),
            metadata=request_data.get("metadata", {})
        )

        allowed = await runner.on_agent_join(group_agent)
        if allowed:
            runner.agents[req_did] = group_agent
            return {"status": "success", "message": "Joined group", "group_id": runner.group_id}
        else:
            return {"status": "error", "message": "Join request rejected"}

    @classmethod
    async def _handle_group_leave(cls, runner: GroupRunner, request_data: Dict[str, Any]):
        """处理离开群组请求"""
        req_did = request_data.get("req_did")
        if req_did in runner.agents:
            group_agent = runner.agents[req_did]
            await runner.on_agent_leave(group_agent)
            del runner.agents[req_did]
            return {"status": "success", "message": "Left group"}
        else:
            return {"status": "error", "message": "Not a member of this group"}

    @classmethod
    async def _handle_group_message(cls, runner: GroupRunner, request_data: Dict[str, Any]):
        """处理群组消息"""
        req_did = request_data.get("req_did")
        if not runner.is_member(req_did):
            return {"status": "error", "message": "Not a member of this group"}

        message = Message(
            type="TEXT",
            content=request_data.get("content"),
            sender_id=req_did,
            group_id=runner.group_id,
            timestamp=time.time(),
            metadata=request_data.get("metadata", {})
        )

        response = await runner.on_message(message)
        if response:
            return {"status": "success", "response": response.to_dict()}
        return {"status": "success"}

    @classmethod
    def _handle_group_connect(cls, runner: GroupRunner, request_data: Dict[str, Any]):
        """处理群组连接请求（SSE）"""
        req_did = request_data.get("req_did")
        if not runner.is_member(req_did):
            return {"status": "error", "message": "Not a member of this group"}

        async def event_generator():
            queue = asyncio.Queue()
            runner.register_listener(req_did, queue)
            try:
                while True:
                    message = await queue.get()
                    import json
                    yield f"data: {json.dumps(message)}\n\n"
            except asyncio.CancelledError:
                runner.unregister_listener(req_did)
                raise

        return StreamingResponse(event_generator(), media_type="text/event-stream")

    @classmethod
    async def _handle_group_members(cls, runner: GroupRunner, request_data: Dict[str, Any]):
        """处理群组成员管理"""
        action = request_data.get("action", "list")

        if action == "list":
            members = [agent.to_dict() for agent in runner.get_members()]
            return {"status": "success", "members": members}
        elif action == "add":
            agent_id = request_data.get("agent_id")
            group_agent = GroupAgent(
                id=agent_id,
                name=request_data.get("name", agent_id),
                port=request_data.get("port", 0),
                metadata=request_data.get("metadata", {})
            )
            allowed = await runner.on_agent_join(group_agent)
            if allowed:
                runner.agents[agent_id] = group_agent
                return {"status": "success", "message": "Member added"}
            return {"status": "error", "message": "Add member rejected"}
        elif action == "remove":
            agent_id = request_data.get("agent_id")
            success = await runner.remove_member(agent_id)
            if success:
                return {"status": "success", "message": "Member removed"}
            return {"status": "error", "message": "Member not found"}
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
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
        

        logger.debug(f"💬 全局消息处理器注册: {did}:{msg_type} <- {agent_name}")
        return True
    

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
