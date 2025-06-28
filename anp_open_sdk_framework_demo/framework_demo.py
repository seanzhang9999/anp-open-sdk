import argparse
import importlib
import glob
import os
import sys
import asyncio
import threading

from anp_open_sdk.anp_sdk_user_data import save_interface_files, LocalUserDataManager
from anp_open_sdk.sdk_mode import SdkMode
from anp_open_sdk.service.router.router_agent import wrap_business_handler
from anp_open_sdk_framework.local_methods.local_methods_decorators import register_local_methods_to_agent

from anp_open_sdk.config import UnifiedConfig, set_global_config
from anp_open_sdk.utils.log_base import setup_logging
from anp_open_sdk.anp_sdk import ANPSDK

import logging

from anp_open_sdk_framework.agent_manager import LocalAgentManager

from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller
from anp_open_sdk_framework.local_methods.local_methods_doc import LocalMethodsDocGenerator
from anp_open_sdk.config import get_global_config

logger = logging.getLogger(__name__)

import inspect


async def main():
    parser = argparse.ArgumentParser(description="ANP Open SDK Multi-Agent Demo")
    parser.add_argument(
        '--config',
        type=str,
        default='anp_open_sdk_framework_demo_agent_unified_config.yaml',
        help='Path to the unified configuration file.'
    )
    parser.add_argument(
        '--crawler',
        type=str,
        help='Name of the crawler to run (e.g., agent_002_local_caller_crawler).'
    )
    parser.add_argument(
        '--intelligent',
        action='store_true',
        help='Use intelligent crawler mode with LLM analysis.'
    )
    parser.add_argument(
        '--target-method',
        type=str,
        default='demo_method',
        help='Target method name for intelligent crawler (default: demo_method).'
    )
    args = parser.parse_args()

    app_config = UnifiedConfig(config_file=args.config)
    set_global_config(app_config)
    setup_logging()

    logger.debug("🚀 Starting Agent Host Application...")
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())

    config = get_global_config()
    agent_config_path = config.multi_agent_mode.agents_cfg_path
    agent_files = glob.glob(f"{agent_config_path}/*/agent_mappings.yaml")
    if not agent_files:
        logger.info("No agent configurations found. Exiting.")
        return

    prepared_agents_info = [LocalAgentManager.load_agent_from_module(f) for f in agent_files]
    valid_agents_info = [info for info in prepared_agents_info if info and info[0]]
    all_agents = [info[0] for info in valid_agents_info]
    lifecycle_modules = {info[0].id: info[1] for info in valid_agents_info}

    if not all_agents:
        logger.info("No agents were loaded successfully. Exiting.")
        return

    logger.info("\n✅ All agents pre-loaded. Creating SDK instance...")
    sdk = ANPSDK(mode=SdkMode.MULTI_AGENT_ROUTER, agents=all_agents)

    logger.info("\n🔄 Running post-initialization for agents...")
    for agent in all_agents:
        module = lifecycle_modules.get(agent.id)
        if module and hasattr(module, "initialize_agent"):
            logger.info(f"  - Calling initialize_agent for {agent.name}...")
            await module.initialize_agent(agent, sdk)

    for agent in all_agents:
        await LocalAgentManager.generate_and_save_agent_interfaces(agent, sdk)

    def run_server():
        sdk.start_server()
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
    logger.info(f"Waiting for server to start on {host}:{port} ...")
    wait_for_port(host, port, timeout=15)
    logger.info("Server is ready, proceeding with agent tasks.")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(script_dir, f"{config.anp_sdk.host}_{config.anp_sdk.port}_local_methods_doc.json")
    LocalMethodsDocGenerator.generate_methods_doc(doc_path)

    if args.crawler:
        try:
            crawler_module_name = f"anp_open_sdk_framework_demo.crawlers.{args.crawler}"
            crawler_module = importlib.import_module(crawler_module_name)
            
            if args.intelligent:
                # 使用智能爬虫模式
                if hasattr(crawler_module, "run_intelligent_local_method_crawler"):
                    logger.info(f"--- Running intelligent crawler: {args.crawler} with target method: {args.target_method} ---")
                    result = await crawler_module.run_intelligent_local_method_crawler(
                        sdk=sdk,
                        target_method_name=args.target_method
                    )
                    logger.info(f"--- Intelligent crawler result: {result} ---")
                    logger.info(f"--- Intelligent crawler finished: {args.crawler} ---")
                else:
                    logger.error(f"Crawler module {args.crawler} does not have a run_intelligent_local_method_crawler function.")
            else:
                # 使用普通爬虫模式
                if hasattr(crawler_module, "run_local_method_crawler"):
                    logger.info(f"--- Running crawler: {args.crawler} ---")
                    await crawler_module.run_local_method_crawler(sdk)
                    logger.info(f"--- Crawler finished: {args.crawler} ---")
                else:
                    logger.error(f"Crawler module {args.crawler} does not have a run_local_method_crawler function.")
                    
        except ImportError:
            logger.error(f"Could not import crawler: {args.crawler}")
        except Exception as e:
            logger.error(f"An error occurred while running the crawler: {e}")

    else:
        logger.debug("\n🔍 No crawler specified. Running default discovery...")
        discovery_agent = None
        for agent in all_agents:
            if hasattr(agent, 'discover_and_describe_agents'):
                discovery_agent = agent
                break
        if discovery_agent:
            logger.info(f"✅ Found discovery agent: '{discovery_agent.name}'. Starting its discovery task...")
            result = await discovery_agent.run_agent_002_demo(sdk)
            print(result)
            result = await discovery_agent.run_agent_002_demo_new()
            print(result)
        else:
            logger.debug("⚠️ No agent with discovery capabilities was found.")

    input("\n🔥 Server is still running. Press any key to stop.")

    logger.debug("\n🛑 Shutdown signal received. Cleaning up...")

    cleanup_tasks = []
    for agent in all_agents:
        module = lifecycle_modules.get(agent.id)
        if module and hasattr(module, "cleanup_agent"):
            logger.debug(f"  - Scheduling cleanup for module of agent: {agent.name}...")
            cleanup_tasks.append(module.cleanup_agent())

    if cleanup_tasks:
        await asyncio.gather(*cleanup_tasks)
    logger.debug("✅ All agents cleaned up. Exiting.")

    if 'sdk' in locals():
        logger.debug("  - Stopping server...")
        if hasattr(sdk, "stop_server"):
            sdk.stop_server()
            logger.debug("  - Server stopped.")
        else:
            logger.debug("  - sdk 实例没有 stop_server 方法，无法主动停止服务。")

    import signal
    os.kill(os.getpid(), signal.SIGKILL)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
