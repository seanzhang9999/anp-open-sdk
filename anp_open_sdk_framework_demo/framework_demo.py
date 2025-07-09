import glob
import os
import sys
import asyncio
import threading

from anp_open_sdk_framework.server_mode import ServerMode

from anp_open_sdk.config import UnifiedConfig, set_global_config, get_global_config
from anp_open_sdk.utils.log_base import setup_logging
from anp_open_sdk_framework.anp_server import ANP_Server

import logging

from anp_open_sdk_framework.agent_adaptation.agent_manager import LocalAgentManager

from anp_open_sdk_framework.agent_adaptation.local_service.local_methods_doc import LocalMethodsDocGenerator

app_config = UnifiedConfig(config_file='anp_open_sdk_framework_demo_agent_unified_config.yaml')
set_global_config(app_config)
setup_logging() # 假设 setup_logging 内部也改用 get_global_config()
logger = logging.getLogger(__name__)


async def main():
    logger.debug("🚀 Starting Agent Host Application...")
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())

    config = get_global_config()
    # --- 加载和初始化所有Agent模块 ---

    agent_files = glob.glob("data_user/localhost_9527/agents_config/*/agent_mappings.yaml")
    if not agent_files:
        logger.info("No agent configurations found. Exiting.")
        return

    prepared_agents_info = [LocalAgentManager.load_agent_from_module(f) for f in agent_files]


    # 过滤掉加载失败的
    valid_agents_info = [info for info in prepared_agents_info if info and info[0]]

    all_agents = [info[0] for info in valid_agents_info]
    lifecycle_modules = {info[0].id: info[1] for info in valid_agents_info}

    if not all_agents:
        logger.info("No agents were loaded successfully. Exiting.")
        return

    # --- 启动SDK ---
    logger.info("\n✅ All agents pre-loaded. Creating SDK instance...")
    svr = ANP_Server(mode=ServerMode.MULTI_AGENT_ROUTER, agents=all_agents)

    # --- 新增：后期初始化循环 ---
    logger.info("\n🔄 Running post-initialization for agents...")
    for agent in all_agents:
        module = lifecycle_modules.get(agent.id)
        if module and hasattr(module, "initialize_agent"):
            logger.info(f"  - Calling initialize_agent for {agent.name}...")
            await module.initialize_agent(agent, svr)  # 传入 agent 和 sdk 实例

    for agent in all_agents:
        await LocalAgentManager.generate_and_save_agent_interfaces(agent, svr)


    # 用线程启动 server
    def run_server():
        svr.start_server()
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()


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

    host = config.anp_sdk.host
    port = config.anp_sdk.port
    logger.info(f"⏳ 等待服务器启动 {host}:{port} ...")
    wait_for_port(host, port, timeout=15)
    logger.info("✅ 服务器就绪，开始执行任务。")


    logger.info("\n🔥 Server is running. Press Ctrl+C to stop.")


    # 生成本地方法文档供查看，如果只是调用，不需要
    # 在当前程序脚本所在目录下生成文档
    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(script_dir, "local_methods_doc.json")
    LocalMethodsDocGenerator.generate_methods_doc(doc_path)

    logger.debug("\n🔍 Searching for an agent with discovery capabilities...")
    discovery_agent = None
    for agent in all_agents:
        if hasattr(agent, 'discover_and_describe_agents'):
            discovery_agent = agent
            break
    if discovery_agent:
        logger.info(f"✅ Found discovery agent: '{discovery_agent.name}'. Starting its discovery task...")
        # 直接调用 agent 实例上的方法
        publisher_url = "http://localhost:9527/publisher/agents"
        # agent中的自动抓取函数，自动从主地址搜寻所有did/ad/yaml文档
        #result = await discovery_agent.discover_and_describe_agents(publisher_url)
        # agent中的联网调用函数，调用计算器
        result = await discovery_agent.run_calculator_add_demo()
        # agent中的联网调用函数，相当于发送消息
        #result = await discovery_agent.run_hello_demo()
        # agent中的AI联网爬取函数，从一个did地址开始爬取
        #result = await discovery_agent.run_ai_crawler_demo()
        # agent中的AI联网爬取函数，从多个did汇总地址开始爬取
        #result = await discovery_agent.run_ai_root_crawler_demo()
        # agent中的本地api去调用另一个agent的本地api
        #result = await discovery_agent.run_agent_002_demo(sdk)
        # agent中的本地api通过搜索本地api注册表去调用另一个agent的本地api
        #result = await discovery_agent.run_agent_002_demo_new()

    else:
        logger.debug("⚠️ No agent with discovery capabilities was found.")

    input("按任意键停止服务")

    # --- 清理 ---
    logger.debug("\n🛑 Shutdown signal received. Cleaning up...")

    # 停止服务器
    # 注意：start_server() 是在单独线程中调用的，sdk.stop_server() 只有在 ANPSDK 实现了对应的停止机制时才有效
    if 'sdk' in locals():
        logger.debug("  - Stopping server...")
        if hasattr(svr, "stop_server"):
            svr.stop_server()
            logger.debug("  - Server stopped.")
        else:
            logger.debug("  - sdk 实例没有 stop_server 方法，无法主动停止服务。")

    # 清理 Agent
    cleanup_tasks = []
    for agent in all_agents:
        module = lifecycle_modules.get(agent.id)
        if module and hasattr(module, "cleanup_agent"):
            logger.debug(f"  - Scheduling cleanup for module of agent: {agent.name}...")
            cleanup_tasks.append(module.cleanup_agent())

    if cleanup_tasks:
        await asyncio.gather(*cleanup_tasks)
    logger.debug("✅ All agents cleaned up. Exiting.")







if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass