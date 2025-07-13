# Copyright 2024 ANP Open SDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import json
# 在模块顶部获取 logger，这是标准做法
import logging
import os
import time
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import Request, WebSocket, WebSocketDisconnect, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from anp_sdk.anp_user import ANPUser
from anp_sdk.anp_sdk_user_data import get_user_data_manager
from anp_server.anp_server_auth_middleware import auth_middleware
from anp_sdk.config import get_global_config
from anp_server.server_mode import ServerMode
from anp_server_framework.anp_service.anp_sdk_group_runner import GroupManager, GroupRunner, Message, MessageType, Agent
from anp_server.router import router_did,router_host
from anp_server.router import router_publisher, router_auth

logger = logging.getLogger(__name__)

class ANP_Server:
    """ANP SDK主类，支持多种运行模式"""
    
    instance = None
    _instances = {}

    @classmethod
    def get_instance(cls, port):
        if port not in cls._instances:
            cls._instances[port] = cls(ServerMode.MULTI_AGENT_ROUTER, ws_port=port)
        return cls._instances[port]
    
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance
    
    def __init__(self, mode = ServerMode.MULTI_AGENT_ROUTER, agents=None, ws_host="0.0.0.0", ws_port=9527, **kwargs):
        if hasattr(self, 'initialized'):
            return
        self.mode = mode
        self.agents = agents or []
        self.port = ws_port
        self.server_running = False
        self.api_routes = {}
        self.api_registry = {}
        self.message_handlers = {}
        self.ws_connections = {}
        self.sse_clients = set()
        self.logger = logger
        self.proxy_client = None
        self.proxy_mode = False
        self.proxy_task = None
        self.group_manager = GroupManager(self)
        self.user_data_manager = get_user_data_manager()
        self.agent = None
        self.initialized = True
        config = get_global_config()
        self.debug_mode = config.anp_sdk.debug_mode

        if self.debug_mode:
            self.app = FastAPI(
                title="ANP SDK Server in DebugMode",
                description="ANP SDK Server in DebugMode",
                version="0.1.0",
                reload=False,
                docs_url="/docs",
                redoc_url="/redoc"
                    )
        else:
            self.app = FastAPI(
                title="ANP SDK Server",
                description="ANP SDK Server",
                version="0.1.0",
                reload=True,
                docs_url=None,
                redoc_url=None
                    )
        self.app.state.sdk = self

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @self.app.middleware("http")
        async def auth_middleware_wrapper(request, call_next):
            return await auth_middleware(request, call_next)

        from anp_server.router.router_agent import AgentRouter
        self.router = AgentRouter()
        if mode == ServerMode.MULTI_AGENT_ROUTER:
            for agent in self.agents:
                self.register_agent(agent)
            self._register_default_routes()
        elif mode == ServerMode.DID_REG_PUB_SERVER:
            self._register_default_routes()
        elif mode == ServerMode.SDK_WS_PROXY_SERVER:
            self._register_default_routes()
            self._register_ws_proxy_server(ws_host, ws_port)
        elif mode == ServerMode.AGENT_SELF_SERVICE:
            for agent in self.agents:
                self.register_agent(agent)
            self._register_default_routes()
        # 其他模式由LocalAgent主导




    def _register_ws_proxy_server(self, ws_host, ws_port):
        self.ws_clients = {}

        @self.app.websocket("/ws/agent")
        async def ws_agent_endpoint(websocket: WebSocket):
            await websocket.accept()
            client_id = id(websocket)
            self.ws_clients[client_id] = websocket
            try:
                while True:
                    msg = await websocket.receive_text()
                    data = json.loads(msg)
                    # 处理代理注册、DID发布、API代理等
            except Exception as e:
                    self.logger.error(f"WebSocket客户端断开: {e}")
            finally:
                    self.ws_clients.pop(client_id, None)

    def register_group_runner(self, group_id: str, runner_class: type[GroupRunner],
                             url_pattern: Optional[str] = None):
        self.group_manager.register_runner(group_id, runner_class, url_pattern)

    def unregister_group_runner(self, group_id: str):
        self.group_manager.unregister_runner(group_id)

    def get_group_runner(self, group_id: str) -> Optional[GroupRunner]:
        return self.group_manager.get_runner(group_id)

    def list_groups(self) -> List[str]:
        return self.group_manager.list_groups()


    def register_agent(self, agent: ANPUser):
        # 从agent的DID中解析域名和端口
        domain, port = self.get_did_host_port_from_did(agent.id)

        # 标准化域名
        if domain in ['127.0.0.1', '0.0.0.0']:
            domain = 'localhost'
        # 使用解析出的域名和端口注册
        self.router.register_agent_with_domain(
            agent,
            domain=domain,
            port=port
        )
        self.logger.debug(f"已注册智能体到SDK: {agent.id} @ {domain}:{port}")


    def get_agents(self):
        return self.router.get_all_agents().values()

    def get_agent(self, did: str):
        return self.router.get_agent(did)

    def _register_default_routes(self):
        self.app.include_router(router_auth.router)
        self.app.include_router(router_did.router)
        self.app.include_router(router_publisher.router)
        self.app.include_router(router_host.router)
        @self.app.get("/", tags=["status"])
        async def root():
            return {
                "status": "running",
                "anp_service": "ANP SDK Server",
                "version": "0.1.0",
                "mode": "Server and client",
                "documentation": "/docs"
            }

        # 统一路由入口 - GET请求
        @self.app.get("/agent/api/{did}/{subpath:path}")
        async def unified_api_entry_get(did: str, subpath: str, request: Request):
            # 解析请求类型和参数
            request_type, processed_data = await self._parse_unified_request(
                did, subpath, dict(request.query_params), request, "GET"
            )
            
            # 统一路由处理
            return await self._handle_unified_request(
                request_type, did, processed_data, request
            )

        # 统一路由入口 - POST请求
        @self.app.post("/agent/api/{did}/{subpath:path}")
        async def unified_api_entry_post(did: str, subpath: str, request: Request):
            # 获取请求体
            try:
                data = await request.json()
                if not data:
                    data = {}
            except Exception:
                data = {}
            
            # 解析请求类型和参数
            request_type, processed_data = await self._parse_unified_request(
                did, subpath, data, request, "POST"
            )
            
            # 统一路由处理
            return await self._handle_unified_request(
                request_type, did, processed_data, request
            )

        # 注释掉向后兼容的消息路由，强制使用统一路由
        # @self.app.post("/agent/message/{did}/post")
        # async def message_entry_post_legacy(did: str, request: Request):
        #     # 重定向到统一API路径
        #     return await unified_api_entry_post(did, "message/post", request)

        self.group_queues = {}
        self.group_members = {}
        
        @self.app.post("/agent/group/{did}/{group_id}/join")
        async def join_group(did: str, group_id: str, request: Request):
            data = await request.json()
            req_did = request.query_params.get("req_did", "demo_caller")
            runner = self.group_manager.get_runner(group_id)
            if runner:
                agent = Agent(
                    id=req_did,
                    name=data.get("name", req_did),
                    port=data.get("port", 0),
                    metadata=data.get("metadata", {})
                )
                allowed = await runner.on_agent_join(agent)
                if allowed:
                    runner.agents[req_did] = agent
                    return {"status": "success", "message": "Joined group", "group_id": group_id}
                else:
                    return {"status": "error", "message": "Join request rejected"}
            resp_did = did
            data["type"] = "group_join"
            data["group_id"] = group_id
            data["req_did"] = req_did
            result = await self.router.route_request(req_did, resp_did, data, request)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        @self.app.post("/agent/group/{did}/{group_id}/leave")
        async def leave_group(did: str, group_id: str, request: Request):
            data = await request.json()
            req_did = request.query_params.get("req_did", "demo_caller")
            runner = self.group_manager.get_runner(group_id)
            if runner and req_did in runner.agents:
                agent = runner.agents[req_did]
                await runner.on_agent_leave(agent)
                del runner.agents[req_did]
                return {"status": "success", "message": "Left group"}
            resp_did = did
            data["type"] = "group_leave"
            data["group_id"] = group_id
            data["req_did"] = req_did
            result = await self.router.route_request(req_did, resp_did, data, request)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        @self.app.post("/agent/group/{did}/{group_id}/message")
        async def group_message(did: str, group_id: str, request: Request):
            data = await request.json()
            req_did = request.query_params.get("req_did", "demo_caller")
            runner = self.group_manager.get_runner(group_id)
            if runner:
                message = Message(
                    type=MessageType.TEXT,
                    content=data.get("content"),
                    sender_id=req_did,
                    group_id=group_id,
                    timestamp=time.time(),
                    metadata=data.get("metadata", {})
                )
                if not runner.is_member(req_did):
                    return {"status": "error", "message": "Not a member of this group"}
                response = await runner.on_message(message)
                if response:
                    return {"status": "success", "response": response.to_dict()}
                return {"status": "success"}
            resp_did = did
            data["type"] = "group_message"
            data["group_id"] = group_id
            data["req_did"] = req_did
            result = await self.router.route_request(req_did, resp_did, data, request)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        @self.app.get("/agent/group/{did}/{group_id}/connect")
        async def group_connect(did: str, group_id: str, request: Request):
            req_did = request.query_params.get("req_did", "demo_caller")
            runner = self.group_manager.get_runner(group_id)
            if runner:
                if not runner.is_member(req_did):
                    return {"status": "error", "message": "Not a member of this group"}
                async def event_generator():
                    queue = asyncio.Queue()
                    runner.register_listener(req_did, queue)
                    try:
                        while True:
                            message = await queue.get()
                            yield f"data: {json.dumps(message)}\n\n"
                    except asyncio.CancelledError:
                        runner.unregister_listener(req_did)
                        raise
                return StreamingResponse(event_generator(), media_type="text/event-stream")
            resp_did = did
            data = {"type": "group_connect", "group_id": group_id, "req_did": req_did}
            result = await self.router.route_request(req_did, resp_did, data)
            if result and "event_generator" in result:
                return StreamingResponse(result["event_generator"], media_type="text/event-stream")
            return result

        @self.app.post("/agent/group/{did}/{group_id}/members")
        async def manage_group_members(did: str, group_id: str, request: Request):
            data = await request.json()
            req_did = request.query_params.get("req_did", "demo_caller")
            runner = self.group_manager.get_runner(group_id)
            if runner:
                action = data.get("action", "list")
                if action == "list":
                    members = [agent.to_dict() for agent in runner.get_members()]
                    return {"status": "success", "members": members}
                elif action == "add":
                    agent_id = data.get("agent_id")
                    agent = Agent(
                        id=agent_id,
                        name=data.get("name", agent_id),
                        port=data.get("port", 0),
                        metadata=data.get("metadata", {})
                    )
                    allowed = await runner.on_agent_join(agent)
                    if allowed:
                        runner.agents[agent_id] = agent
                        return {"status": "success", "message": "Member added"}
                    return {"status": "error", "message": "Add member rejected"}
                elif action == "remove":
                    agent_id = data.get("agent_id")
                    success = await runner.remove_member(agent_id)
                    if success:
                        return {"status": "success", "message": "Member removed"}
                    return {"status": "error", "message": "Member not found"}
                else:
                    return {"status": "error", "message": f"Unknown action: {action}"}
            resp_did = did
            data["type"] = "group_members"
            data["group_id"] = group_id
            data["req_did"] = req_did
            result = await self.router.route_request(req_did, resp_did, data, request)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        @self.app.get("/agent/group/{did}/{group_id}/members")
        async def get_group_members(did: str, group_id: str, request: Request):
            req_did = request.query_params.get("req_did", "demo_caller")
            runner = self.group_manager.get_runner(group_id)
            if runner:
                members = [agent.to_dict() for agent in runner.get_members()]
                return {"status": "success", "members": members}
            resp_did = did
            data = {"type": "group_members", "action": "list", "group_id": group_id, "req_did": req_did}
            result = await self.router.route_request(req_did, resp_did, data, request)
            if asyncio.iscoroutine(result):
                result = await result
            return result

        @self.app.get("/agent/groups")
        async def list_groups(request: Request):
            groups = self.list_groups()
            return {"status": "success", "groups": groups}

        @self.app.post("/api/message")
        async def receive_message(request: Request):
            data = await request.json()
            return await self._handle_message(data)

        @self.app.websocket("/ws/message")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            client_id = id(websocket)
            self.ws_connections[client_id] = websocket

            try:
                while True:
                    data = await websocket.receive_json()
                    response = await self._handle_message(data)
                    await websocket.send_json(response)
            except WebSocketDisconnect:
                self.logger.debug(f"WebSocket客户端断开连接: {client_id}")
                if client_id in self.ws_connections:
                    del self.ws_connections[client_id]
            except Exception as e:
                self.logger.error(f"WebSocket处理错误: {e}")
                if client_id in self.ws_connections:
                    del self.ws_connections[client_id]

    async def _parse_unified_request(self, did: str, subpath: str, data: dict, request: Request, method: str):
        """解析统一路由请求，返回请求类型和处理后的数据"""
        
        # 获取req_did
        req_did = request.query_params.get("req_did", "demo_caller")
        
        # 基于路径前缀识别请求类型
        if subpath.startswith("message/"):
            return "message", {
                **data,
                "type": "message",
                "path": f"/{subpath}",
                "req_did": req_did
            }
        elif subpath.startswith("group/"):
            # 解析群组操作类型
            group_type = self._parse_group_operation(subpath)
            return "group", {
                **data,
                "type": group_type,
                "path": f"/{subpath}",
                "req_did": req_did
            }
        else:
            # 默认为API调用
            return "api_call", {
                **data,
                "type": "api_call",
                "path": f"/{subpath}",
                "req_did": req_did
            }
    
    def _parse_group_operation(self, subpath: str) -> str:
        """解析群组操作类型"""
        if "/join" in subpath:
            return "group_join"
        elif "/leave" in subpath:
            return "group_leave"
        elif "/message" in subpath:
            return "group_message"
        elif "/connect" in subpath:
            return "group_connect"
        elif "/members" in subpath:
            return "group_members"
        else:
            return "group_unknown"
    
    async def _handle_unified_request(self, request_type: str, did: str, processed_data: dict, request: Request):
        """统一处理路由请求"""
        
        req_did = processed_data.get("req_did", "demo_caller")
        resp_did = did
        
        # 根据请求类型处理
        if request_type == "api_call":
            # API调用 - 保持原有逻辑
            result = await self.router.route_request(req_did, resp_did, processed_data, request)
            if asyncio.iscoroutine(result):
                result = await result
            return result
            
        elif request_type == "message":
            # 消息发送 - 保持原有逻辑
            result = await self.router.route_request(req_did, resp_did, processed_data, request)
            if asyncio.iscoroutine(result):
                result = await result
            return result
            
        elif request_type == "group":
            # 群组操作 - 保持原有逻辑
            result = await self.router.route_request(req_did, resp_did, processed_data, request)
            if asyncio.iscoroutine(result):
                result = await result
            return result
            
        else:
            return {"status": "error", "message": f"未知的请求类型: {request_type}"}

    async def _handle_message(self, message: Dict[str, Any]):
        logger.debug(f"准备处理接收到的消息内容: {message}")
        if "message" in message:
            message = message["message"]
        message_type = message.get("type", "*")
        handler = self.message_handlers.get(message_type) or self.message_handlers.get("*")
        if handler:
            try:
                result = handler(message)
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except Exception as e:
                self.logger.error(f"消息处理器执行错误: {e}")
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"未找到处理{message_type}类型消息的处理器"}

    def start_server(self):
        if self.server_running:
            self.logger.warning("服务器已经在运行")
            return True
        if os.name == 'posix' and 'darwin' in os.uname().sysname.lower():
            self.logger.debug("检测到Mac环境，使用特殊启动方式")
        for route_path, route_info in self.api_routes.items():
            func = route_info['func']
            methods = route_info['methods']
            self.app.add_api_route(f"/{route_path}", func, methods=methods)
        import uvicorn
        import threading
        from anp_sdk.config import get_global_config

        # 2. 修正配置项的名称
        config = get_global_config()

        port = config.anp_sdk.port
        host = config.anp_sdk.host

        app_instance = self.app

        if not self.debug_mode:
            config = uvicorn.Config(app_instance, host=host, port=port)
            server = uvicorn.Server(config)
            self.uvicorn_server = server

            def run_server():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(server.serve())

            server_thread = threading.Thread(target=run_server)
            server_thread.daemon = True
            server_thread.start()
            self.server_running = True
            return server_thread
        else:
            uvicorn.run(app_instance, host=host, port=port)
            self.server_running = True
        return True


    def stop_server(self):
        if not self.server_running:
            return True
        for ws in self.ws_connections.values():
            asyncio.create_task(ws.close())
        self.ws_connections.clear()
        self.sse_clients.clear()
        if hasattr(self, 'uvicorn_server'):
            self.uvicorn_server.should_exit = True
            self.logger.debug("已发送服务器关闭信号")
        self.server_running = False
        self.logger.debug("服务器已停止")
        return True

    def __del__(self):
        try:
            if self.server_running:
                self.stop_server()
        except Exception as e:
            pass

    def call_api(self, target_did: str, api_path: str, params: Dict[str, Any] = None, method: str = "GET"):
        try:
            if hasattr(self, 'enable_local_acceleration') and self.enable_local_acceleration and hasattr(self, 'accelerator') and self.accelerator.is_local_agent(target_did):
                return self.accelerator.call_api(
                    from_did=self.agent.id if self.agent else "unknown",
                    target_did=target_did,
                    api_path=api_path,
                    method=method,
                    data=params,
                    headers={}
                )

            if not self.agent:
                self.logger.error("智能体未初始化")
                return None

            host, port = self.get_did_host_port_from_did(target_did)
            target_url = f"{host}:{port}"
            url = f"http://{target_url}/{api_path}"

            return self.agent.call_api(url, params, method)

        except Exception as e:
            self.logger.error(f"API调用失败: {e}")
            return {"error": str(e)}

    def expose_api(self, route_path: str, methods: List[str] = None):
        if methods is None:
            methods = ["GET"]
        def decorator(func):
            self.api_routes[route_path] = {'func': func, 'methods': methods}
            if self.server_running:
                self.app.add_api_route(f"/{route_path}", func, methods=methods)
            return func
        return decorator

    def register_message_handler(self, message_type: str = None):
        def decorator(func):
            self.message_handlers[message_type or "*"] = func
            return func
        return decorator

    def send_message(self, target_did: str, message: str, message_type: str = "text") -> bool:
        try:
            if hasattr(self, 'enable_local_acceleration') and self.enable_local_acceleration and hasattr(self, 'accelerator') and self.accelerator.is_local_agent(target_did):
                return self.accelerator.send_message(
                    from_did=self.agent.id if self.agent else "unknown",
                    target_did=target_did,
                    message=message,
                    message_type=message_type
                )
            target_agent = self.router.get_agent(target_did)
            if not target_agent:
                self.logger.error(f"未找到目标智能体: {target_did}")
                return False
            message_data = {
                "from_did": self.agent.id if self.agent else "unknown",
                "to_did": target_did,
                "content": message,
                "type": message_type,
                "timestamp": datetime.now().isoformat()
            }
            success = target_agent.receive_message(message_data)
            if success:
                self.logger.debug(f"消息已发送到 {target_did}: {message[:50]}...")
            else:
                self.logger.error(f"消息发送失败到 {target_did}")
            return success

        except Exception as e:
            self.logger.error(f"发送消息失败: {e}")
            return False

    async def broadcast_message(self, message: Dict[str, Any]):
        for ws in self.ws_connections.values():
            try:
                await ws.send_json(message)
            except Exception as e:
                self.logger.error(f"WebSocket广播失败: {e}")
        self.logger.debug(f"向{len(self.sse_clients)}个SSE客户端广播消息")

    def __enter__(self):
        self.start_server()
        return self

    async def __aenter__(self):
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_server()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.stop_server()

    async def _handle_api_call(self, req_did: str, resp_did: str, api_path: str, method: str, params: Dict[str, Any]):
        if resp_did != self.agent.id:
            return {"status": "error", "message": f"未找到智能体: {resp_did}"}
        api_key = f"{method.lower()}:{api_path}"
        if api_key in self.api_routes:
            handler = self.api_routes[api_key]
            try:
                result = await handler(req_did=req_did, **params)
                return result
            except Exception as e:
                self.logger.error(f"API调用错误: {e}")
                return {"status": "error", "message": str(e)}
        else:
            return {"status": "error", "message": f"未找到API: {api_path} [{method}]"}

    @staticmethod
    def get_did_host_port_from_did(did: str) -> tuple[str, int]:
        host, port = None, None
        if did.startswith('did:wba:'):
            try:
                did_parts = did.split(':')
                if len(did_parts) > 2:
                    host_port = did_parts[2]
                    if '%3A' in host_port:
                        host, port = host_port.split('%3A')
                    else:
                        host = did_parts[2]
                        port = did_parts[3]
                        if port is not int:
                            port = 80
            except Exception as e:
                logger.debug(f"解析did失败: {did}, 错误: {e}")
        if not host or not port:
            return "localhost", 9527
        return host, int(port)

    async def unregister_agent(self, agent_id: str):
        try:
            all_agents = self.router.get_all_agents()
            if agent_id not in all_agents:
                self.logger.warning(f"Agent {agent_id} not found in the router")
                return False

            # 从全局索引中移除
            agent = all_agents.pop(agent_id, None)

            if agent_id in self.api_registry:
                del self.api_registry[agent_id]

            for group_id in self.list_groups():
                runner = self.get_group_runner(group_id)
                if runner and runner.is_member(agent_id):
                    await runner.remove_member(agent_id)

            self.logger.debug(f"Successfully unregistered agent: {agent_id}")

            if not self.router.get_all_agents():
                self.logger.debug(f"No agents remaining in the router")

            return True

        except Exception as e:
            self.logger.error(f"Failed to unregister agent {agent_id}: {e}")
            return False
