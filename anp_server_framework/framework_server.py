#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ANP Framework 独立服务器
专门处理Agent相关的所有功能，支持Apache 2.0许可证发布
"""

import asyncio
import logging
import os
import sys
import threading
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 添加路径以便导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anp_sdk.config import UnifiedConfig, set_global_config, get_global_config
from anp_sdk.utils.log_base import setup_logging
from anp_sdk.anp_user import ANPUser

from anp_server_framework.agent_manager import AgentManager, LocalAgentManager
from anp_server_framework.global_router import GlobalRouter
from anp_server_framework.global_message_manager import GlobalMessageManager

logger = logging.getLogger(__name__)


class ANPFrameworkServer:
    """ANP Framework 独立服务器"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9528, config_file: str = None):
        self.host = host
        self.port = port
        self.app = FastAPI(
            title="ANP Framework Server",
            description="Agent Network Protocol Framework - Agent Processing Service",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # 配置CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self.agents = []
        self.server_running = False
        
        # 初始化配置
        if config_file:
            config = UnifiedConfig(config_file)
            set_global_config(config)
        
        setup_logging()
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self):
        """注册Framework服务的路由"""
        
        @self.app.get("/", tags=["status"])
        async def root():
            return {
                "service": "ANP Framework Server",
                "version": "1.0.0",
                "status": "running",
                "license": "Apache 2.0",
                "agents_count": len(self.agents),
                "documentation": "/docs"
            }
        
        @self.app.get("/health", tags=["status"])
        async def health_check():
            """健康检查"""
            return {
                "status": "healthy",
                "agents": len(self.agents),
                "routes": len(GlobalRouter.list_routes()),
                "message_handlers": len(GlobalMessageManager.list_handlers())
            }
        
        # Agent API处理 - 统一入口
        @self.app.post("/agent/api/{did}/{subpath:path}")
        async def handle_agent_api(did: str, subpath: str, request: Request):
            """处理Agent API调用"""
            try:
                # 获取请求数据
                data = await request.json() if request.headers.get("content-type") == "application/json" else {}
                
                # 构造请求数据
                request_data = {
                    **data,
                    "type": "api_call",
                    "path": f"/{subpath}",
                    "req_did": request.query_params.get("req_did", "framework_caller")
                }
                
                # 查找目标Agent
                agent = self._find_agent(did)
                if not agent:
                    return {"status": "error", "message": f"Agent not found: {did}"}
                
                # 处理请求
                result = await agent.handle_request(
                    request_data["req_did"], 
                    request_data, 
                    request
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Agent API处理错误: {e}")
                return {"status": "error", "message": str(e)}
        
        # Agent消息处理
        @self.app.post("/agent/message/{did}/post")
        async def handle_agent_message(did: str, request: Request):
            """处理Agent消息"""
            try:
                data = await request.json()
                
                request_data = {
                    **data,
                    "type": "message",
                    "req_did": request.query_params.get("req_did", "framework_caller")
                }
                
                agent = self._find_agent(did)
                if not agent:
                    return {"anp_result": {"status": "error", "message": f"Agent not found: {did}"}}
                
                result = await agent.handle_request(
                    request_data["req_did"], 
                    request_data, 
                    request
                )
                
                return result
                
            except Exception as e:
                logger.error(f"Agent消息处理错误: {e}")
                return {"anp_result": {"status": "error", "message": str(e)}}
        
        # Agent管理接口
        @self.app.get("/agents", tags=["management"])
        async def list_agents():
            """列出所有Agent"""
            return {
                "agents": [agent.to_dict() for agent in self.agents],
                "total": len(self.agents)
            }
        
        @self.app.get("/agents/{did}", tags=["management"])
        async def get_agent_info(did: str):
            """获取特定Agent信息"""
            agent = self._find_agent(did)
            if not agent:
                return {"status": "error", "message": f"Agent not found: {did}"}
            
            return agent.to_dict()
        
        # 路由管理接口
        @self.app.get("/routes", tags=["management"])
        async def list_routes():
            """列出所有路由"""
            return {
                "routes": GlobalRouter.list_routes(),
                "stats": GlobalRouter.get_stats()
            }
        
        # 消息处理器管理接口
        @self.app.get("/message-handlers", tags=["management"])
        async def list_message_handlers():
            """列出所有消息处理器"""
            return {
                "handlers": GlobalMessageManager.list_handlers(),
                "stats": GlobalMessageManager.get_stats()
            }
    
    def _find_agent(self, did: str):
        """查找Agent"""
        # 首先尝试直接匹配DID
        for agent in self.agents:
            if hasattr(agent, 'anp_user') and agent.anp_user_id == did:
                return agent
            elif hasattr(agent, 'id') and agent.anp_user_id == did:
                return agent
        
        # 然后尝试匹配Agent名称（用于共享DID）
        for agent in self.agents:
            if hasattr(agent, 'name') and agent.name == did:
                return agent
            # 尝试组合键匹配
            if hasattr(agent, 'anp_user') and hasattr(agent, 'name'):
                combined_key = f"{agent.anp_user_id}#{agent.name}"
                if combined_key == did or agent.name == did:
                    return agent
        
        return None
    
    async def load_agents_from_config(self):
        """从配置加载Agent"""
        logger.info("🔧 开始从配置加载Agent...")
        
        # 清理之前的状态
        AgentManager.clear_all_agents()
        GlobalRouter.clear_routes()
        GlobalMessageManager.clear_handlers()
        
        created_agents = []
        
        # 加载配置文件中的Agent
        import glob
        agent_files = glob.glob("data_user/localhost_9527/agents_config/*/agent_mappings.yaml")
        
        for agent_file in agent_files:
            try:
                agent, handler_module, share_did_config = await LocalAgentManager.load_agent_from_module(agent_file)
                if agent:
                    # 使用新的Agent系统重新创建
                    if share_did_config:
                        # 共享DID模式
                        new_agent = AgentManager.create_agent(
                            agent, 
                            agent.name, 
                            shared=True, 
                            prefix=share_did_config.get('path_prefix', ''),
                            primary_agent=share_did_config.get('primary_agent', False)
                        )
                    else:
                        # 独占DID模式
                        new_agent = AgentManager.create_agent(
                            agent, 
                            agent.name, 
                            shared=False
                        )
                    
                    # 注册现有的API和消息处理器
                    for path, handler in list(agent.api_routes.items()):
                        new_agent.api(path)(handler)
                    
                    for msg_type, handler in list(agent.message_handlers.items()):
                        new_agent.message_handler(msg_type)(handler)
                    
                    created_agents.append(new_agent)
                    logger.info(f"✅ 已加载Agent: {agent.name}")
                    
            except Exception as e:
                logger.error(f"❌ 加载Agent失败 {agent_file}: {e}")
        
        self.agents = created_agents
        logger.info(f"✅ 总共加载了 {len(created_agents)} 个Agent")
        
        return created_agents
    
    def start_server(self):
        """启动服务器"""
        if self.server_running:
            logger.warning("服务器已经在运行")
            return
        
        def run_server():
            config = uvicorn.Config(self.app, host=self.host, port=self.port)
            server = uvicorn.Server(config)
            self.uvicorn_server = server
            
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(server.serve())
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        self.server_running = True
        
        logger.info(f"🚀 ANP Framework Server 启动成功: http://{self.host}:{self.port}")
        return server_thread
    
    def stop_server(self):
        """停止服务器"""
        if hasattr(self, 'uvicorn_server'):
            self.uvicorn_server.should_exit = True
        self.server_running = False
        logger.info("🛑 ANP Framework Server 已停止")


async def main():
    """主函数"""
    # 创建Framework服务器
    framework_server = ANPFrameworkServer(
        host="0.0.0.0", 
        port=9528,
        config_file="unified_config_framework_demo.yaml"
    )
    
    # 加载Agent
    await framework_server.load_agents_from_config()
    
    # 启动服务器
    framework_server.start_server()
    
    # 等待服务器启动
    import time
    import socket
    
    def wait_for_port(host, port, timeout=10.0):
        start = time.time()
        while time.time() - start < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except (OSError, ConnectionRefusedError):
                time.sleep(0.2)
        raise RuntimeError(f"Server on {host}:{port} did not start within {timeout} seconds")
    
    wait_for_port("localhost", 9528, timeout=15)
    logger.info("✅ Framework服务器就绪")
    
    # 显示状态
    logger.info(f"\n📊 Framework服务器状态:")
    logger.info(f"  - Agent数量: {len(framework_server.agents)}")
    logger.info(f"  - 路由数量: {len(GlobalRouter.list_routes())}")
    logger.info(f"  - 消息处理器数量: {len(GlobalMessageManager.list_handlers())}")
    
    logger.info(f"\n🔗 服务访问地址:")
    logger.info(f"  - API文档: http://localhost:9528/docs")
    logger.info(f"  - 健康检查: http://localhost:9528/health")
    logger.info(f"  - Agent列表: http://localhost:9528/agents")
    
    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        framework_server.stop_server()
        logger.info("👋 Framework服务器已关闭")


if __name__ == "__main__":
    asyncio.run(main())
