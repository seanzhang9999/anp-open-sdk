import importlib
import glob
import os
import sys
import asyncio
import threading

from anp_open_sdk.anp_sdk_user_data import save_interface_files, LocalUserDataManager
from anp_open_sdk.sdk_mode import SdkMode
from anp_open_sdk.service.router.router_agent import wrap_business_handler

from anp_open_sdk.config import UnifiedConfig, set_global_config
from anp_open_sdk.utils.log_base import setup_logging
from anp_open_sdk.anp_sdk import ANPSDK

import logging

from anp_open_sdk_framework.agent_manager import LocalAgentManager

from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller
from anp_open_sdk_framework.local_methods.local_methods_doc import LocalMethodsDocGenerator

app_config = UnifiedConfig(config_file='anp_open_sdk_framework_demo_agent_unified_config.yaml')
set_global_config(app_config)
setup_logging() # Assumption setup_logging Internal changes have also been implemented. get_global_config()
logger = logging.getLogger(__name__)

import inspect



async def main():
    logger.debug("🚀 Starting Agent Host Application...")
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())

    # --- Load and initialize allAgentModule ---

    agent_files = glob.glob("data_user/localhost_9527/agents_config/*/agent_mappings.yaml")
    if not agent_files:
        logger.info("No agent configurations found. Exiting.")
        return

    prepared_agents_info = [LocalAgentManager.load_agent_from_module(f) for f in agent_files]


    # Filter out the failed loads.
    valid_agents_info = [info for info in prepared_agents_info if info and info[0]]

    all_agents = [info[0] for info in valid_agents_info]
    lifecycle_modules = {info[0].id: info[1] for info in valid_agents_info}

    if not all_agents:
        logger.info("No agents were loaded successfully. Exiting.")
        return

    # --- InitiateSDK ---
    logger.info("\n✅ All agents pre-loaded. Creating SDK instance...")
    sdk = ANPSDK(mode=SdkMode.MULTI_AGENT_ROUTER, agents=all_agents)

    # --- Added：Post-initialization loop ---
    logger.info("\n🔄 Running post-initialization for agents...")
    for agent in all_agents:
        module = lifecycle_modules.get(agent.id)
        if module and hasattr(module, "initialize_agent"):
            logger.info(f"  - Calling initialize_agent for {agent.name}...")
            await module.initialize_agent(agent, sdk)  # Input agent And sdk Example

    for agent in all_agents:
        await LocalAgentManager.generate_and_save_agent_interfaces(agent, sdk)


    # Start with threads. server
    def run_server():
        sdk.start_server()
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    logger.info("\n🔥 Server is running. Press Ctrl+C to stop.")


    # Generate local method documentation for review.，If it is just a call，Not necessary.
    # Generate the document in the directory where the current program script is located.
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
        # Direct invocation agent Methods on the instance
        publisher_url = "http://localhost:9527/publisher/agents"
        # agentAutomatic capture function in the middle，Automatically search all from the main address.did/ad/yamlDocument
        result = await discovery_agent.discover_and_describe_agents(publisher_url)
        # agentFunction for network calls in the middle，Invoke the calculator.
        result = await discovery_agent.run_calculator_add_demo()
        # agentFunction for network calls in the middle，Equivalent to sending a message
        result = await discovery_agent.run_hello_demo()
        # agentIn the middle ofAINetwork crawling function，From onedidStarting to crawl the address
        result = await discovery_agent.run_ai_crawler_demo()
        # agentIn the middle ofAINetwork crawling function，From multipledidThe collection of addresses has begun crawling.
        result = await discovery_agent.run_ai_root_crawler_demo()
        # agentLocal in the middleapiCall another one.agentLocalapi
        result = await discovery_agent.run_agent_002_demo(sdk)
        print(result)
        # agentLocal in the middleapiSearch locally.apiRegistry calls anotheragentLocalapi
        result = await discovery_agent.run_agent_002_demo_new()
        print(result)

    else:
        logger.debug("⚠️ No agent with discovery capabilities was found.")

    input("Press any key to stop the service.")

    # --- Clean up ---
    logger.debug("\n🛑 Shutdown signal received. Cleaning up...")

    # Stop the server.
    # Attention：start_server() It is called in a separate thread.，sdk.stop_server() only when ANPSDK Effective only when the corresponding stop mechanism is implemented.
    if 'sdk' in locals():
        logger.debug("  - Stopping server...")
        if hasattr(sdk, "stop_server"):
            sdk.stop_server()
            logger.debug("  - Server stopped.")
        else:
            logger.debug("  - sdk No instances available. stop_server Method，Unable to proactively stop the service.。")

    # Clean up Agent
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