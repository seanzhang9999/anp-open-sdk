import asyncio
import glob
import logging
import threading
import time
import socket
from typing import Dict, List, Optional, Any
from pathlib import Path

from anp_open_sdk.anp_sdk import ANPSDK
from anp_open_sdk.sdk_mode import SdkMode
from anp_open_sdk.config import UnifiedConfig, set_global_config, get_global_config
from anp_open_sdk.utils.log_base import setup_logging
from anp_open_sdk_framework.agent_manager import LocalAgentManager
from anp_open_sdk_framework.local_methods.local_methods_doc import LocalMethodsDocGenerator

logger = logging.getLogger(__name__)

class AgentServiceManager:
    """智能体服务管理器，负责加载和管理智能体实例"""
    
    def __init__(self):
        self.sdk: Optional[ANPSDK] = None
        self.agents: List[Any] = []
        self.lifecycle_modules: Dict[str, Any] = {}
        self.server_thread: Optional[threading.Thread] = None
        self.is_initialized = False
        self.config_file = 'unified_config_anp_open_sdk_framework_demo_agent_9528.yaml'
        
    async def initialize_agents(self, config_file: Optional[str] = None) -> bool:
        """初始化智能体服务"""
        try:
            if self.is_initialized:
                logger.info("Agent service already initialized")
                return True
                
            # 使用指定的配置文件或默认配置
            config_path = config_file or self.config_file
            if not Path(config_path).exists():
                logger.error(f"Configuration file not found: {config_path}")
                return False
                
            # 加载配置
            app_config = UnifiedConfig(config_file=config_path)
            set_global_config(app_config)
            setup_logging()
            
            logger.info("🚀 Starting Agent Service Manager...")
            
            config = get_global_config()
            agent_config_path = config.multi_agent_mode.agents_cfg_path
            agent_files = glob.glob(f"{agent_config_path}/*/agent_mappings.yaml")
            
            if not agent_files:
                logger.warning("No agent configurations found")
                return False
                
            # 加载智能体
            prepared_agents_info = [LocalAgentManager.load_agent_from_module(f) for f in agent_files]
            valid_agents_info = [info for info in prepared_agents_info if info and info[0]]
            self.agents = [info[0] for info in valid_agents_info]
            self.lifecycle_modules = {info[0].id: info[1] for info in valid_agents_info}
            
            if not self.agents:
                logger.warning("No agents were loaded successfully")
                return False
                
            logger.info(f"✅ Loaded {len(self.agents)} agents successfully")
            
            # 创建SDK实例
            self.sdk = ANPSDK(mode=SdkMode.MULTI_AGENT_ROUTER, agents=self.agents)
            
            # 执行后初始化
            logger.info("🔄 Running post-initialization for agents...")
            for agent in self.agents:
                module = self.lifecycle_modules.get(agent.id)
                if module and hasattr(module, "initialize_agent"):
                    logger.info(f"  - Calling initialize_agent for {agent.name}...")
                    await module.initialize_agent(agent, self.sdk)
                    
            # 生成接口文档
            for agent in self.agents:
                await LocalAgentManager.generate_and_save_agent_interfaces(agent, self.sdk)
                
            # 启动服务器
            await self._start_server()
            
            # 生成本地方法文档
            script_dir = Path(__file__).parent.parent.parent
            doc_path = script_dir / f"{config.anp_sdk.host}_{config.anp_sdk.port}_local_methods_doc.json"
            LocalMethodsDocGenerator.generate_methods_doc(str(doc_path))
            
            self.is_initialized = True
            logger.info("✅ Agent service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent service: {e}")
            return False
            
    async def _start_server(self):
        """启动SDK服务器"""
        def run_server():
            self.sdk.start_server()
            
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # 等待服务器启动
        config = get_global_config()
        host = config.anp_sdk.host
        port = config.anp_sdk.port
        
        logger.info(f"Waiting for server to start on {host}:{port}...")
        await self._wait_for_port(host, port, timeout=15)
        logger.info("✅ Agent server is ready")
        
    async def _wait_for_port(self, host: str, port: int, timeout: float = 10.0):
        """等待端口可用"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except (OSError, ConnectionRefusedError):
                await asyncio.sleep(0.2)
        raise RuntimeError(f"Server on {host}:{port} did not start within {timeout} seconds")
        
    async def call_orchestrator_method(self, method_name: str, *args, **kwargs) -> Any:
        """调用orchestrator_agent的方法"""
        if not self.is_initialized:
            raise RuntimeError("Agent service not initialized")
            
        # 查找orchestrator agent
        orchestrator_agent = None
        for agent in self.agents:
            if hasattr(agent, method_name):
                orchestrator_agent = agent
                break
                
        if not orchestrator_agent:
            raise ValueError(f"Method {method_name} not found in any agent")
            
        # 调用方法
        method = getattr(orchestrator_agent, method_name)
        if asyncio.iscoroutinefunction(method):
            if method_name in ['run_agent_002_demo']:
                return await method(self.sdk, *args, **kwargs)
            else:
                return await method(*args, **kwargs)
        else:
            return method(*args, **kwargs)
            
    async def get_available_methods(self) -> List[Dict[str, Any]]:
        """获取可用的方法列表"""
        if not self.is_initialized:
            return []
            
        methods = []
        for agent in self.agents:
            agent_methods = []
            for attr_name in dir(agent):
                if not attr_name.startswith('_'):
                    attr = getattr(agent, attr_name)
                    if callable(attr):
                        agent_methods.append({
                            'name': attr_name,
                            'agent_name': agent.name,
                            'agent_id': agent.id,
                            'is_async': asyncio.iscoroutinefunction(attr)
                        })
            methods.extend(agent_methods)
            
        return methods
        
    async def discover_agents(self, publisher_url: str = "http://localhost:9527/publisher/agents") -> Any:
        """发现智能体"""
        return await self.call_orchestrator_method('discover_and_describe_agents', publisher_url)
        
    async def run_calculator_demo(self) -> Any:
        """运行计算器演示"""
        return await self.call_orchestrator_method('run_calculator_add_demo')
        
    async def run_hello_demo(self) -> Any:
        """运行Hello演示"""
        return await self.call_orchestrator_method('run_hello_demo')
        
    async def run_ai_crawler_demo(self) -> Any:
        """运行AI爬虫演示"""
        return await self.call_orchestrator_method('run_ai_crawler_demo')
        
    async def run_ai_root_crawler_demo(self) -> Any:
        """运行AI根爬虫演示"""
        return await self.call_orchestrator_method('run_ai_root_crawler_demo')
        
    async def run_agent_002_demo(self) -> Any:
        """运行Agent 002演示"""
        return await self.call_orchestrator_method('run_agent_002_demo', self.sdk)
        
    async def run_agent_002_demo_new(self) -> Any:
        """运行Agent 002新演示"""
        return await self.call_orchestrator_method('run_agent_002_demo_new')
        
    async def cleanup(self):
        """清理资源"""
        if not self.is_initialized:
            return
            
        logger.info("🛑 Cleaning up agent service...")
        
        # 执行清理任务
        cleanup_tasks = []
        for agent in self.agents:
            module = self.lifecycle_modules.get(agent.id)
            if module and hasattr(module, "cleanup_agent"):
                logger.debug(f"  - Scheduling cleanup for agent: {agent.name}")
                cleanup_tasks.append(module.cleanup_agent())
                
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks)
            
        # 停止服务器
        if self.sdk and hasattr(self.sdk, "stop_server"):
            self.sdk.stop_server()
            
        self.is_initialized = False
        logger.info("✅ Agent service cleaned up")

# 全局智能体服务管理器实例
agent_service_manager = AgentServiceManager()