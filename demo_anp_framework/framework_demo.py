import glob
import json
import os
import sys
import asyncio
import threading

# 添加路径以便导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anp_server_framework.anp_service.agent_api_call import agent_api_call_post
from anp_server_framework.anp_service.agent_message_p2p import agent_msg_post
from anp_server.server_mode import ServerMode

from anp_sdk.config import UnifiedConfig, set_global_config, get_global_config
from anp_sdk.utils.log_base import setup_logging
from anp_server.anp_server import ANP_Server

import logging

from anp_server_framework.agent_manager import LocalAgentManager

from anp_server_framework.local_service.local_methods_doc import LocalMethodsDocGenerator

app_config = UnifiedConfig(config_file='unified_config_framework_demo.yaml')
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

    prepared_agents_info = [await LocalAgentManager.load_agent_from_module(f) for f in agent_files]

    # 过滤掉加载失败的
    valid_agents_info = [info for info in prepared_agents_info if info and info[0]]

    all_agents = [info[0] for info in valid_agents_info]
    # 修复：对于共享DID的Agent，使用Agent名称作为键，而不是agent.id
    lifecycle_modules = {info[0].name: info[1] for info in valid_agents_info}
    shared_did_configs = {}
    for info in valid_agents_info:
        if info[2]:  # 如果有共享DID配置
            agent, _, share_config = info
            # 使用Agent名称作为唯一标识
            shared_did_configs[agent.name] = share_config

    if not all_agents:
        logger.info("No agents were loaded successfully. Exiting.")
        return

    # --- 启动SDK ---
    logger.info("\n✅ All agents pre-loaded. Creating SDK instance...")
    svr = ANP_Server(mode=ServerMode.MULTI_AGENT_ROUTER, agents=all_agents)
    
    # --- 注册共享DID配置 ---
    if shared_did_configs:
        logger.info("\n🔗 注册共享DID配置...")
        for agent_name, share_config in shared_did_configs.items():
            if share_config:
                shared_did = share_config['shared_did']
                path_prefix = share_config['path_prefix']
                api_paths = share_config['api_paths']
                
                # 找到对应的Agent实例，使用其ID（即共享DID）
                target_agent = None
                for agent in all_agents:
                    if agent.name == agent_name:
                        target_agent = agent
                        break
                
                if target_agent:
                    # 修复：使用Agent名称而不是Agent ID进行共享DID注册
                    svr.router.register_shared_did(shared_did, agent_name, path_prefix, api_paths)
                    logger.info(f"  ✅ 已注册共享DID: {shared_did} -> {agent_name} (Agent ID: {target_agent.id}, 前缀: {path_prefix})")
                else:
                    logger.warning(f"  ❌ 未找到Agent: {agent_name}")
        
        logger.info(f"📊 共享DID统计: {len(shared_did_configs)} 个Agent使用共享DID")
        for shared_did in svr.router.list_shared_dids():
            info = svr.router.get_shared_did_info(shared_did)
            logger.info(f"  🔗 {shared_did}: {len(info.get('path_mappings', {}))} 个路径映射")

    # --- 新增：后期初始化循环 ---
    logger.info("\n🔄 Running post-initialization for agents...")
    for agent in all_agents:
        module = lifecycle_modules.get(agent.name)
        if module and hasattr(module, "initialize_agent"):
            logger.info(f"  - Calling initialize_agent for {agent.name}...")
            await module.initialize_agent(agent, svr)  # 传入 agent 和 sdk 实例

    for agent in all_agents:
        await LocalAgentManager.generate_and_save_agent_interfaces(agent, svr)


    # 用线程启动 anp_server
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
        #result = await discovery_agent.run_calculator_add_demo()

        # 添加消息发送测试
        from anp_server_framework.anp_service.agent_message_p2p import agent_msg_post
        
        # 找到 Calculator Agent
        calculator_agent = None
        for agent in all_agents:
            if "Calculator" in agent.name or "calculator" in agent.name.lower():
                calculator_agent = agent
                break
        
        if calculator_agent and discovery_agent:
            logger.info(f"\n🔔 开始测试消息发送功能...")
            # 发送消息给 Calculator Agent
            resp = await agent_msg_post(discovery_agent.id, calculator_agent.id, f"你好，我是{discovery_agent.name}，请问你能帮我计算吗？")
            logger.info(f"[{discovery_agent.name}] 已发送消息给 {calculator_agent.name}, 响应: {resp}")
        else:
            logger.warning("未找到 Calculator Agent 或 Discovery Agent，跳过消息测试")

        # === 新增：共享DID功能测试 ===
        logger.info(f"\n🧪 开始共享DID功能测试...")
        
        # 测试1: Calculator共享DID API调用
        logger.info(f"\n🔧 测试Calculator共享DID API调用...")
        calc_api_success = await test_shared_did_api()
        
        # 测试2: LLM共享DID API调用
        logger.info(f"\n🤖 测试LLM共享DID API调用...")
        llm_api_success = await test_llm_shared_did_api()
        
        # 测试3: 共享DID消息发送
        logger.info(f"\n📨 测试共享DID消息发送...")
        msg_success = await test_message_sending()
        
        # 测试结果总结
        logger.info(f"\n📊 共享DID测试结果总结:")
        logger.info(f"  🔧 Calculator共享DID API: {'✅ 成功' if calc_api_success else '❌ 失败'}")
        logger.info(f"  🤖 LLM共享DID API: {'✅ 成功' if llm_api_success else '❌ 失败'}")
        logger.info(f"  📨 共享DID消息发送: {'✅ 成功' if msg_success else '❌ 失败'}")
        
        success_count = sum([calc_api_success, llm_api_success, msg_success])
        total_count = 3
        
        if success_count == total_count:
            logger.info(f"\n🎉 所有共享DID测试通过! ({success_count}/{total_count}) 架构重构验证成功!")
        else:
            logger.info(f"\n⚠️  部分共享DID测试失败 ({success_count}/{total_count})，需要进一步调试。")

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

    #input("按任意键停止服务")

    # --- 清理 ---
    logger.debug("\n🛑 Shutdown signal received. Cleaning up...")

    # 停止服务器
    # 注意：start_server() 是在单独线程中调用的，sdk.stop_server() 只有在 ANPSDK 实现了对应的停止机制时才有效
    if 'sdk' in locals():
        logger.debug("  - Stopping anp_server...")
        if hasattr(svr, "stop_server"):
            svr.stop_server()
            logger.debug("  - Server stopped.")
        else:
            logger.debug("  - sdk 实例没有 stop_server 方法，无法主动停止服务。")

    # 清理 Agent
    cleanup_tasks = []
    for agent in all_agents:
        module = lifecycle_modules.get(agent.name)
        if module and hasattr(module, "cleanup_agent"):
            logger.debug(f"  - Scheduling cleanup for module of agent: {agent.name}...")
            cleanup_tasks.append(module.cleanup_agent())

    if cleanup_tasks:
        await asyncio.gather(*cleanup_tasks)
    logger.debug("✅ All agents cleaned up. Exiting.")








async def test_shared_did_api():
    """测试共享DID的API调用"""
    print("\n🧪 测试共享DID API调用...")

    # 测试参数
    caller_agent = "did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d"  # Orchestrator Agent
    target_agent = "did:wba:localhost%3A9527:wba:user:28cddee0fade0258"  # 共享DID
    api_path = "/calculator/add"  # 共享DID路径
    params = {"a": 10, "b": 20}

    try:
        print(f"📞 调用API: {target_agent}{api_path}")
        print(f"📊 参数: {params}")

        # 调用API
        result = await agent_api_call_post(
            caller_agent=caller_agent,
            target_agent=target_agent,
            api_path=api_path,
            params=params
        )

        print(f"✅ API调用成功!")
        print(f"📋 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        # 验证结果
        if isinstance(result, dict) and "result" in result:
            expected_result = 30  # 10 + 20
            actual_result = result["result"]
            if actual_result == expected_result:
                print(f"🎉 计算结果正确: {actual_result}")
                return True
            else:
                print(f"❌ 计算结果错误: 期望 {expected_result}, 实际 {actual_result}")
                return False
        else:
            print(f"❌ 响应格式不正确: {result}")
            return False

    except Exception as e:
        print(f"❌ API调用失败: {e}")
        return False


async def test_message_sending():
    """测试消息发送功能"""
    print("\n📨 测试消息发送...")

    caller_agent = "did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d"  # Orchestrator Agent
    target_agent = "did:wba:localhost%3A9527:wba:user:28cddee0fade0258"  # 共享DID (Calculator Agent)
    message = "测试消息：请问你能帮我计算 5 + 3 吗？"

    try:
        print(f"📞 发送消息到: {target_agent}")
        print(f"💬 消息内容: {message}")

        # 发送消息
        result = await agent_msg_post(
            caller_agent=caller_agent,
            target_agent=target_agent,
            content=message,
            message_type="text"
        )

        print(f"✅ 消息发送成功!")
        print(f"📋 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        # 验证响应
        if isinstance(result, dict) and "anp_result" in result:
            anp_result = result["anp_result"]
            if isinstance(anp_result, dict) and "reply" in anp_result:
                print(f"💬 Calculator Agent 回复: {anp_result['reply']}")
                return True

        print(f"❌ 消息响应格式不正确: {result}")
        return False

    except Exception as e:
        print(f"❌ 消息发送失败: {e}")
        return False


async def test_llm_shared_did_api():
    """测试LLM Agent的共享DID API调用"""
    print("\n🤖 测试LLM Agent共享DID API调用...")

    # 测试参数
    caller_agent = "did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d"  # Orchestrator Agent
    target_agent = "did:wba:localhost%3A9527:wba:user:28cddee0fade0258"  # 共享DID
    api_path = "/llm/chat"  # LLM共享DID路径
    params = {"message": "你好，请介绍一下你自己"}

    try:
        print(f"📞 调用LLM API: {target_agent}{api_path}")
        print(f"📊 参数: {params}")

        # 调用API
        result = await agent_api_call_post(
            caller_agent=caller_agent,
            target_agent=target_agent,
            api_path=api_path,
            params=params
        )

        print(f"✅ LLM API调用成功!")
        print(f"📋 响应: {json.dumps(result, ensure_ascii=False, indent=2)}")

        # 验证结果
        if isinstance(result, dict) and ("response" in result or "reply" in result or "content" in result):
            print(f"🎉 LLM响应成功!")
            return True
        else:
            print(f"❌ LLM响应格式不正确: {result}")
            return False

    except Exception as e:
        print(f"❌ LLM API调用失败: {e}")
        return False




if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
