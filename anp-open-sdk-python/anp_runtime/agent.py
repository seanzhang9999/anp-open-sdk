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
import warnings
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from fastapi import Request
from starlette.responses import JSONResponse

try:
    import nest_asyncio
except ImportError:
    nest_asyncio = None

from anp_foundation.anp_user import ANPUser

logger = logging.getLogger(__name__)


class Agent:
    """Agent类 - 功能载体，通过装饰器发布API和消息处理功能
    
    这个类承担了从ANPUser迁移过来的功能：
    1. API暴露功能 (api装饰器)
    2. 消息处理器注册 (message_handler装饰器)
    3. 群组事件处理 (group_event_handler装饰器)
    4. 请求处理核心逻辑 (handle_request方法)
    """
    
    def __init__(self, anp_user_did_str: str, name: str, shared: bool = False,
                 prefix: Optional[str] = None, primary_agent: bool = False):
        """初始化Agent
        
        Args:
            anp_user: ANPUser实例（DID身份容器）
            name: Agent名称
            shared: 是否共享DID模式
            prefix: 共享模式下的API前缀
            primary_agent: 是否为主Agent（拥有消息处理权限）
        """
        #self.anp_user = anp_user
        # 为了向后兼容性，添加id属性
        self.anp_user_did = anp_user_did_str

        self.name = name
        self.shared = shared
        self.prefix = prefix
        self.primary_agent = primary_agent
        self.created_at = datetime.now()
        

        
        # 功能注册表 - 从ANPUser迁移过来
        self.api_routes = {}  # path -> handler
        self.message_handlers = {}  # type -> handler
        self.group_event_handlers = {}  # (group_id, event_type) -> [handlers]
        self.group_global_handlers = []  # [(event_type, handler)] 全局handler
        
        # API配置存储 - 用于保存从YAML配置文件中读取的API参数定义
        self.api_configs = {}  # path -> config_dict，存储API的参数配置信息
        
        logger.debug(f"✅ Agent创建成功: {name}")
        logger.debug(f"   DID: {self.anp_user_did} ({'共享' if shared else '独占'})")
        if prefix:
            logger.debug(f"   Prefix: {prefix}")
        if primary_agent:
            logger.debug(f"   主Agent: 是")

    def set_api_config(self, path: str, config: dict):
        """设置API配置信息
        
        Args:
            path: API路径
            config: API配置字典，包含params、summary等信息
        """
        self.api_configs[path] = config
        logger.debug(f"保存API配置: {path} -> {config}")
    
    def get_api_config(self, path: str) -> dict:
        """获取API配置信息
        
        Args:
            path: API路径
            
        Returns:
            dict: API配置字典，如果不存在则返回空字典
        """
        return self.api_configs.get(path, {})




    def _api(self, path: str, methods=None):
        """API装饰器，用于注册API处理函数
        
        Args:
            path: API路径
            methods: HTTP方法列表，默认为["GET", "POST"]
            
        Returns:
            装饰器函数
        
        Example:
            @agent.api("/hello")
            async def hello_handler(request_data, request):
                return {"message": "Hello, world!"}
        """
        methods = methods or ["GET", "POST"]
        
        def decorator(func):
            # 计算完整路径
            full_path = f"{self.prefix}{path}" if self.prefix else path
            
            # 注册到Agent的路由表 - 使用带前缀的路径
            self.api_routes[full_path] = func  # 修改这里
            logger.info(f"🔗 API注册成功: {self.anp_user_did}{full_path} <- {self.name}")
            return func
        
        return decorator
    
    def _message_handler(self, msg_type: str):
        """消息处理器装饰器，用于注册消息处理函数
        
        Args:
            msg_type: 消息类型，如"text"、"command"等，或"*"表示处理所有类型
            
        Returns:
            装饰器函数
            
        Example:
            @agent.message_handler("text")
            async def handle_text(msg_data):
                return {"reply": f"收到消息: {msg_data.get('content')}"}
        """
        def decorator(func):
            # 检查消息处理权限
            if not self._can_handle_message():
                error_msg = self._get_message_permission_error()
                logger.error(f"❌ 消息处理器注册失败: {error_msg}")
                raise PermissionError(error_msg)
            
            # 注册到Agent的消息处理器表
            self.message_handlers[msg_type] = func
            
            # 注册到全局消息管理器
            from anp_runtime.global_router_agent_message import GlobalMessageManager
            GlobalMessageManager.register_handler(
                did=self.anp_user_did,
                msg_type=msg_type,
                handler=func,
                agent_name=self.name
            )
            
            logger.debug(f"💬 消息处理器注册成功: {self.anp_user_did}:{msg_type} <- {self.name}")
            return func
        
        return decorator
    
    def _group_event_handler(self, group_id: Optional[str] = None, event_type: Optional[str] = None):
        """群组事件处理器装饰器，用于注册群组事件处理函数
        
        Args:
            group_id: 群组ID，如果为None则处理所有群组
            event_type: 事件类型，如果为None则处理所有类型
            
        Returns:
            装饰器函数
            
        Example:
            @agent.group_event_handler(group_id="group1", event_type="join")
            async def handle_join(group_id, event_type, event_data):
                return {"status": "success"}
        """
        def decorator(func):
            if group_id is None and event_type is None:
                self.group_global_handlers.append((None, func))
            elif group_id is None:
                self.group_global_handlers.append((event_type, func))
            else:
                key = (group_id, event_type)
                self.group_event_handlers.setdefault(key, []).append(func)
            
            logger.debug(f"✅ 注册群组事件处理器: Agent {self.name}, 群组 {group_id or 'all'}, 事件 {event_type or 'all'}")
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
            return (

                f"Agent '{self.name}' 无消息处理权限\n"
                f"原因: 共享DID模式下，只有主Agent可以处理消息\n"
                f"当前状态: shared={self.shared}, primary_agent={self.primary_agent}\n"
                f"解决方案: 设置 primary_agent=True 或使用独占DID"
            )
        else:
            return "未知的消息权限错误"

    # ========== 废弃的方法（保留但发出警告） ==========
    
    def expose_api(self, path: str, func: Optional[Callable] = None, methods=None):
        """
        [已废弃] 请使用 api 装饰器代替
        """
        warnings.warn(
            "expose_api 方法已废弃，请使用 api 装饰器代替。例如：@agent.api('/path')",
            DeprecationWarning, 
            stacklevel=2
        )
        methods = methods or ["GET", "POST"]
        if func is None:
            return self._api(path, methods)
        else:
            return self._api(path, methods)(func)
    
    def register_message_handler(self, msg_type: str, func: Optional[Callable] = None, agent_name: Optional[str] = None):
        """
        [已废弃] 请使用 message_handler 装饰器代替
        """
        warnings.warn(
            "register_message_handler 方法已废弃，请使用 message_handler 装饰器代替。例如：@agent.message_handler('text')",
            DeprecationWarning, 
            stacklevel=2
        )
        if func is None:
            return self._message_handler(msg_type)
        else:
            return self._message_handler(msg_type)(func)
    
    def register_group_event_handler(self, handler: Callable, group_id: Optional[str] = None, event_type: Optional[str] = None):
        """
        [已废弃] 请使用 group_event_handler 装饰器代替
        """
        warnings.warn(
            "register_group_event_handler 方法已废弃，请使用 group_event_handler 装饰器代替。例如：@agent.group_event_handler(group_id, event_type)",
            DeprecationWarning, 
            stacklevel=2
        )
        return self._group_event_handler(group_id, event_type)(handler)
    
    def _get_group_event_handlers(self, group_id: str, event_type: str):
        """获取群组事件处理器"""
        handlers = []
        for et, h in self.group_global_handlers:
            if et is None or et == event_type:
                handlers.append(h)
        for (gid, et), hs in self.group_event_handlers.items():
            if gid == group_id and (et is None or et == event_type):
                handlers.extend(hs)
        return handlers
    
    async def _dispatch_group_event(self, group_id: str, event_type: str, event_data: dict):
        """分发群组事件"""
        handlers = self._get_group_event_handlers(group_id, event_type)
        for handler in handlers:
            try:
                ret = handler(group_id, event_type, event_data)
                if inspect.isawaitable(ret):
                    await ret
            except Exception as e:
                logger.error(f"群事件处理器出错: {e}")
    
    async def handle_request(self, req_did: str, request_data: Dict[str, Any], request: Request):
        """请求处理核心逻辑
        
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
            logger.debug(f"🔍 Agent {self.name} API{api_path} 对应处理器 {handler}:")
            if handler:
                try:
                    # 检查是否是类方法
                    is_class_method = getattr(handler, '_is_class_method', False)
                    
                    if is_class_method:
                        # 如果是类方法，不传递self参数
                        result = await handler(request_data, request)
                    else:
                        # 如果不是类方法，正常调用
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
                    # 使用智能参数适配
                    result = await self._call_message_handler(handler, request_data, request)
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

    async def _call_message_handler(self, handler, request_data, request):
        """调用消息处理器，自动适配参数格式"""
        sig = inspect.signature(handler)
        param_names = list(sig.parameters.keys())

        if 'request_data' in param_names and 'request' in param_names:
            # 情况1: 同时需要 request_data 和 request
            return await handler(request_data, request)
        elif 'request_data' in param_names:
            # 情况2: 只需要 request_data
            return await handler(request_data)
        else:
            # 情况3: 传统格式，构造 msg_content
            msg_content = {
                'content': request_data.get('content', ''),
                'message_type': request_data.get('message_type', 'text'),
                'sender': request_data.get('req_did', ''),
                'timestamp': request_data.get('timestamp', ''),
                # 可以根据需要添加更多字段
            }
            # 新增：特殊处理 msg_data 参数名的情况
            if len(param_names) == 1 and param_names[0] == 'msg_data':
                return await handler(msg_content)
            # 检查处理器期望的参数名
            if len(param_names) == 1:
                param_name = param_names[0]
                if param_name == 'msg':
                    return await handler(msg_content)
                elif param_name == 'msg_data':
                    return await handler(msg_content)
                else:
                    # 其他参数名，也传递 msg_content
                    return await handler(msg_content)
            else:
                # 多个参数的情况，传递 msg_content 作为第一个参数
                return await handler(msg_content)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "did": self.anp_user_did,
            "shared": self.shared,
            "prefix": self.prefix,
            "primary_agent": self.primary_agent,
            "created_at": self.created_at.isoformat(),
            "api_count": len(self.api_routes),
            "message_handler_count": len(self.message_handlers),
            "group_event_handler_count": len(self.group_event_handlers) + len(self.group_global_handlers)
        }
    
    def __repr__(self):
        return f"Agent(name='{self.name}', did='{self.anp_user_did}', shared={self.shared})"
