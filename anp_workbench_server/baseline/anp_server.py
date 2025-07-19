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

# 在模块顶部获取 logger，这是标准做法
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from anp_foundation.config import get_global_config
from anp_workbench_server.baseline.middleware.anp_auth_middleware import auth_middleware
from anp_workbench_server.baseline.router import router_did, router_host
from anp_workbench_server.baseline.router import router_publisher, router_auth,router_agent

logger = logging.getLogger(__name__)

class ANP_Server:
    """ANP SDK主类，支持多种运行模式"""
    
    instance = None
    _instances = {}

    @classmethod
    def get_instance(cls, port):
        if port not in cls._instances:
            cls._instances[port] = cls(port=port)
        return cls._instances[port]
    
    def __new__(cls, *args, **kwargs):
        if cls.instance is None:
            cls.instance = super().__new__(cls)
        return cls.instance
    
    def __init__(self, host="0.0.0.0", port=9527, **kwargs):
        if hasattr(self, 'initialized'):
            return
        self.port = port
        self.server_running = False


        self.logger = logger
        self.initialized = True
        config = get_global_config()
        self.debug_mode = config.anp_sdk.debug_mode


        if self.debug_mode:
            self.app = FastAPI(
                title="ANP DID Server in DebugMode",
                description="ANP DID Server in DebugMode",
                version="0.1.0",
                reload=False,
                docs_url="/docs",
                redoc_url="/redoc"
                    )
        else:
            self.app = FastAPI(
                title="ANP DID Server",
                description="ANP DID Server",
                version="0.1.0",
                reload=True,
                docs_url=None,
                redoc_url=None
                    )

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

        self._register_default_routes()


    def _register_default_routes(self):
        self.app.include_router(router_auth.router)
        self.app.include_router(router_did.router)
        self.app.include_router(router_publisher.router)
        self.app.include_router(router_host.router)
        self.app.include_router(router_agent.router)

        @self.app.get("/", tags=["status"])
        async def root():
            return {
                "status": "running",
                "anp_service": "ANP SDK Server",
                "version": "0.1.0",
                "mode": "Server and client",
                "documentation": "/docs"
            }

    def start_server(self):
        if self.server_running:
            self.logger.warning("服务器已经在运行")
            return True
        if os.name == 'posix' and 'darwin' in os.uname().sysname.lower():
            self.logger.debug("检测到Mac环境，使用特殊启动方式")
        import uvicorn
        import threading
        from anp_foundation.config import get_global_config

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
        if hasattr(self, 'uvicorn_server'):
            self.uvicorn_server.should_exit = True
            self.logger.debug("已发送服务器关闭信号")
        self.server_running = False
        self.logger.debug("服务器已停止")
        return True




