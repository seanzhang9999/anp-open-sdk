#!/usr/bin/env python3
"""完整的共享DID功能测试 - 包含服务器启动和测试"""

import asyncio
import json
import os
import sys
import threading
import time
import socket

from anp_server_framework.anp_service.agent_api_call import agent_api_call_post
from anp_server_framework.anp_service import agent_msg_post
from demo_anp_framework.framework_demo import test_shared_did_api, test_message_sending, \
    test_llm_shared_did_api

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 初始化全局配置
from anp_sdk.config import set_global_config, UnifiedConfig
from anp_sdk.utils.log_base import setup_logging
config = UnifiedConfig("unified_config_framework_demo.yaml")
set_global_config(config)
setup_logging()

# 初始化用户数据管理器
from anp_sdk.anp_user_local_data import get_user_data_manager
user_data_manager = get_user_data_manager()


def wait_for_port(host, port, timeout=15.0):
    """等待端口可用"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.2)
    raise RuntimeError(f"Server on {host}:{port} did not start within {timeout} seconds")

async def start_server():
    """启动服务器"""
    print("🚀 启动ANP SDK服务器...")
    
    import glob
    from anp_server import ServerMode
    from anp_server.anp_server import ANP_Server
    from anp_server_framework.agent_manager import LocalAgentManager
    
    # 加载所有Agent
    agent_files = glob.glob("data_user/localhost_9527/agents_config/*/agent_mappings.yaml")
    if not agent_files:
        print("❌ 未找到Agent配置文件")
        return None
    
    prepared_agents_info = [await LocalAgentManager.load_agent_from_module(f) for f in agent_files]
    valid_agents_info = [info for info in prepared_agents_info if info and info[0]]
    all_agents = [info[0] for info in valid_agents_info]
    
    if not all_agents:
        print("❌ 未成功加载任何Agent")
        return None
    
    print(f"✅ 成功加载 {len(all_agents)} 个Agent")
    for agent in all_agents:
        if agent:
            print(f"  - {agent.name} ({agent.id})")
    
    # 创建服务器
    svr = ANP_Server(mode=ServerMode.MULTI_AGENT_ROUTER, anp_users=all_agents)
    
    # 注册共享DID配置
    shared_did_configs = {}
    for info in valid_agents_info:
        if info[2]:  # 如果有共享DID配置
            agent, _, share_config = info
            if agent:
                shared_did_configs[agent.name] = share_config
    
    if shared_did_configs:
        print(f"🔗 注册 {len(shared_did_configs)} 个共享DID配置...")
        for agent_name, share_config in shared_did_configs.items():
            if share_config:
                shared_did = share_config['shared_did']
                path_prefix = share_config['path_prefix']
                api_paths = share_config['api_paths']
                
                # 找到对应的Agent实例
                target_agent = None
                for agent in all_agents:
                    if agent and agent.name == agent_name:
                        target_agent = agent
                        break
                
                if target_agent:
                    # 使用Agent名称而不是Agent ID进行注册
                    svr.router_agent.register_shared_did(shared_did, agent_name, path_prefix, api_paths)
                    print(f"  ✅ {shared_did} -> {agent_name} (前缀: {path_prefix})")
    
    # 启动服务器
    def run_server():
        svr.start_server()
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # 等待服务器启动
    from anp_sdk.config import get_global_config
    global_config = get_global_config()
    host = global_config.anp_sdk.host
    port = global_config.anp_sdk.port
    print(f"⏳ 等待服务器启动 {host}:{port}...")
    wait_for_port(host, port, timeout=15)
    print("✅ 服务器启动成功!")
    
    return svr


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


async def main():
    """主测试函数"""
    print("🚀 ANP SDK 完整共享DID功能测试")
    print("=" * 60)
    
    # 启动服务器
    svr = await start_server()
    if not svr:
        print("❌ 服务器启动失败，退出测试")
        return
    
    # 等待一下让服务器完全就绪
    await asyncio.sleep(0.1)
    
    # 运行测试
    print("\n" + "=" * 60)
    print("🧪 开始功能测试...")
    
    # 测试Calculator API调用
    calc_api_success = await test_shared_did_api()
    
    # 测试LLM API调用
    llm_api_success = await test_llm_shared_did_api()
    
    # 测试消息发送
    msg_success = await test_message_sending()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"  🔧 Calculator共享DID API: {'✅ 成功' if calc_api_success else '❌ 失败'}")
    print(f"  🤖 LLM共享DID API: {'✅ 成功' if llm_api_success else '❌ 失败'}")
    print(f"  📨 消息发送功能: {'✅ 成功' if msg_success else '❌ 失败'}")
    
    success_count = sum([calc_api_success, llm_api_success, msg_success])
    total_count = 3
    
    if success_count == total_count:
        print(f"\n🎉 所有测试通过! ({success_count}/{total_count}) 共享DID路由重构成功!")
    else:
        print(f"\n⚠️  部分测试失败 ({success_count}/{total_count})，需要进一步调试。")
    
    print("\n按 Ctrl+C 退出...")
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 测试结束")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 测试被中断")
