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
import inspect
import asyncio
from typing import Dict, Any, Callable, Optional, List
from datetime import datetime
from fastapi import Request
from starlette.responses import JSONResponse

try:
    import nest_asyncio
except ImportError:
    nest_asyncio = None

from anp_sdk.anp_user import ANPUser

logger = logging.getLogger(__name__)


class Agent:
    """Agent类 - 功能载体，通过装饰器发布API和消息处理功能
    
    这个类承担了从ANPUser迁移过来的expose handler功能：
    1. API暴露功能 (expose_api -> api装饰器)
    2. 消息处理器注册 (register_message_handler -> message_handler装饰器)
    3. 群组事件处理 (register_group_event_handler -> group_event_handler装饰器)
    4. 请求处理核心逻辑 (handle_request -> handle_request方法)
    """
    
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
        
        # 为了向后兼容性，添加id属性
        self.anp_user_id = anp_user.id
        
        # 功能注册表 - 从ANPUser迁移过来
        self.api_routes = {}  # path -> handler
        self.message_handlers = {}  # type -> handler
        self.group_event_handlers = {}  # (group_id, event_type) -> [handlers]
        self.group_global_handlers = []  # [(event_type, handler)] 全局handler
        
        logger.debug(f"✅ Agent创建成功: {name}")
        logger.debug(f"   DID: {anp_user.id} ({'共享' if shared else '独占'})")
        if prefix:
            logger.debug(f"   Prefix: {prefix}")
        if primary_agent:
            logger.debug(f"   主Agent: 是")
    
    def api(self, path: str, methods=None):
        """API装饰器"""
        methods = methods or ["GET", "POST"]
        
        def decorator(func):
            # 计算完整路径
            full_path = f"{self.prefix}{path}" if self.prefix else path
            
            # 注册到Agent的路由表 - 使用带前缀的路径
            self.api_routes[full_path] = func  # 修改这里
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
            
            logger.debug(f"🔗 API注册成功: {self.anp_user.id}{full_path} <- {self.name}")
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
            
            logger.debug(f"💬 消息处理器注册成功: {self.anp_user.id}:{msg_type} <- {self.name}")
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

    # ========== 从ANPUser迁移的功能 ==========
    
    def expose_api(self, path: str, func: Optional[Callable] = None, methods=None):
        """API暴露功能 - 从ANPUser.expose_api()迁移
        
        支持装饰器和函数式注册API，保持向后兼容性
        """
        methods = methods or ["GET", "POST"]
        if func is None:
            def decorator(f: Callable) -> Callable:
                return self._register_api_internal(path, f, methods)
            return decorator
        else:
            return self._register_api_internal(path, func, methods)
    
    def _register_api_internal(self, path: str, func: Callable, methods: List[str]):
        """内部API注册方法"""
        # 计算完整路径
        full_path = f"{self.prefix}{path}" if self.prefix else path
        
        # 注册到Agent的路由表
        self.api_routes[full_path] = func
        
        # 注册到全局路由器
        from anp_server_framework.global_router import GlobalRouter
        GlobalRouter.register_api(
            did=self.anp_user.id,
            path=full_path,
            handler=func,
            agent_name=self.name,
            methods=methods
        )
        
        # 为了向后兼容，也注册到ANPUser（但这应该逐步废弃）
        self.anp_user.api_routes[full_path] = func
        
        logger.debug(f"🔗 API暴露成功: {self.anp_user.id}{full_path} <- {self.name}")
        return func
    
    def register_message_handler(self, msg_type: str, func: Optional[Callable] = None, agent_name: Optional[str] = None):
        """消息处理器注册 - 从ANPUser.register_message_handler()迁移
        
        支持装饰器和函数式注册，包含冲突检测
        """
        if func is None:
            def decorator(f: Callable) -> Callable:
                self._register_message_handler_internal(msg_type, f, agent_name or self.name)
                return f
            return decorator
        else:
            self._register_message_handler_internal(msg_type, func, agent_name or self.name)
            return func
    
    def _register_message_handler_internal(self, msg_type: str, handler: Callable, agent_name: str):
        """内部消息处理器注册方法，包含冲突检测"""
        # 检查消息处理权限
        if not self._can_handle_message():
            error_msg = self._get_message_permission_error()
            logger.error(f"❌ 消息处理器注册失败: {error_msg}")
            raise PermissionError(error_msg)
        
        # 检查是否已有消息处理器
        if msg_type in self.message_handlers:
            existing_handler = self.message_handlers[msg_type]
            logger.warning(f"⚠️  DID {self.anp_user.id} 的消息类型 '{msg_type}' 已有处理器")
            logger.warning(f"   现有处理器: {getattr(existing_handler, '__name__', 'unknown')}")
            logger.warning(f"   新处理器: {getattr(handler, '__name__', 'unknown')} (来自 {agent_name})")
            logger.warning(f"   🔧 使用第一个注册的处理器，忽略后续注册")
            return  # 使用第一个，忽略后续的
        
        self.message_handlers[msg_type] = handler
        
        # 注册到全局消息管理器
        from anp_server_framework.global_message_manager import GlobalMessageManager
        GlobalMessageManager.register_handler(
            did=self.anp_user.id,
            msg_type=msg_type,
            handler=handler,
            agent_name=agent_name
        )
        
        # 为了向后兼容，也注册到ANPUser（但这应该逐步废弃）
        self.anp_user.message_handlers[msg_type] = handler
        
        logger.debug(f"✅ 注册消息处理器: DID {self.anp_user.id}, 类型 '{msg_type}', 来自 {agent_name}")
    
    def register_group_event_handler(self, handler: Callable, group_id: Optional[str] = None, event_type: Optional[str] = None):
        """群组事件处理器注册 - 从ANPUser.register_group_event_handler()迁移"""
        if group_id is None and event_type is None:
            self.group_global_handlers.append((None, handler))
        elif group_id is None:
            self.group_global_handlers.append((event_type, handler))
        else:
            key = (group_id, event_type)
            self.group_event_handlers.setdefault(key, []).append(handler)
        
        logger.debug(f"✅ 注册群组事件处理器: Agent {self.name}, 群组 {group_id or 'all'}, 事件 {event_type or 'all'}")
    
    def _get_group_event_handlers(self, group_id: str, event_type: str):
        """获取群组事件处理器 - 从ANPUser._get_group_event_handlers()迁移"""
        handlers = []
        for et, h in self.group_global_handlers:
            if et is None or et == event_type:
                handlers.append(h)
        for (gid, et), hs in self.group_event_handlers.items():
            if gid == group_id and (et is None or et == event_type):
                handlers.extend(hs)
        return handlers
    
    async def _dispatch_group_event(self, group_id: str, event_type: str, event_data: dict):
        """分发群组事件 - 从ANPUser._dispatch_group_event()迁移"""
        handlers = self._get_group_event_handlers(group_id, event_type)
        for handler in handlers:
            try:
                ret = handler(group_id, event_type, event_data)
                if inspect.isawaitable(ret):
                    await ret
            except Exception as e:
                logger.error(f"群事件处理器出错: {e}")
    
    async def handle_request(self, req_did: str, request_data: Dict[str, Any], request: Request):
        """请求处理核心逻辑 - 从ANPUser.handle_request()迁移
        
        统一的API调用和消息处理入口
        """
        req_type = request_data.get("type")
        
        # 群组消息处理
        if req_type in ("group_message", "group_connect", "group_members"):
            handler = self.message_handlers.get(req_type)
            if handler:
                try:
                    if nest_asyncio:
                        nest_asyncio.apply()
                    if asyncio.iscoroutinefunction(handler):
                        result = await handler(request_data)
                    else:
                        result = handler(request_data)
                    if isinstance(result, dict) and "anp_result" in result:
                        return result
                    return {"anp_result": result}
                except Exception as e:
                    logger.error(f"Group message handling error: {e}")
                    return {"anp_result": {"status": "error", "message": str(e)}}
            else:
                return {"anp_result": {"status": "error", "message": f"No handler for group type: {req_type}"}}
        
        # API调用处理
        if req_type == "api_call":
            api_path = request_data.get("path")
            
            # 调试信息：显示当前Agent的所有API路由
            logger.debug(f"🔍 Agent {self.name} 查找API路径: {api_path}")
            logger.debug(f"🔍 Agent {self.name} 当前所有API路由:")
            for route_path, route_handler in self.api_routes.items():
                logger.debug(f"   - {route_path}: {getattr(route_handler, '__name__', 'unknown')}")
            
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
                    logger.debug(
                        f"发送到 handler的请求数据{request_data}\n"                        
                        f"完整请求为 url: {request.url} \n"
                        f"body: {await request.body()}")
                    logger.error(f"API调用错误: {e}")
                    return JSONResponse(
                        status_code=500,
                        content={"status": "error", "error_message": str(e)}
                    )
            else:
                return JSONResponse(
                    status_code=404,
                    content={"status": "error", "message": f"未找到API: {api_path}"}
                )
        
        # 消息处理
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
                    logger.error(f"消息处理错误: {e}")
                    return {"anp_result": {"status": "error", "message": str(e)}}
            else:
                return {"anp_result": {"status": "error", "message": f"未找到消息处理器: {msg_type}"}}
        else:
            return {"anp_result": {"status": "error", "message": "未知的请求类型"}}
    
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
            "message_handler_count": len(self.message_handlers),
            "group_event_handler_count": len(self.group_event_handlers) + len(self.group_global_handlers)
        }
    
    def __repr__(self):
        return f"Agent(name='{self.name}', did='{self.anp_user.id}', shared={self.shared})"
