#!/usr/bin/env python3
"""测试共享DID API调用功能"""

import asyncio
import json
import os
import sys

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

from anp_server_framework.anp_service.agent_api_call import agent_api_call_post

async def test_shared_did_api():
    """测试共享DID的API调用"""
    print("🧪 开始测试共享DID API调用...")
    
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
    print("\n📨 开始测试消息发送...")
    
    from anp_server_framework.anp_service import agent_msg_post
    
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

async def main():
    """主测试函数"""
    print("🚀 ANP SDK 共享DID功能测试")
    print("=" * 50)
    
    # 等待服务器启动
    print("⏳ 等待服务器启动...")
    await asyncio.sleep(2)
    
    # 测试API调用
    api_success = await test_shared_did_api()
    
    # 测试消息发送
    msg_success = await test_message_sending()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"  🔧 共享DID API调用: {'✅ 成功' if api_success else '❌ 失败'}")
    print(f"  📨 消息发送功能: {'✅ 成功' if msg_success else '❌ 失败'}")
    
    if api_success and msg_success:
        print("\n🎉 所有测试通过! 共享DID路由重构成功!")
    else:
        print("\n⚠️  部分测试失败，需要进一步调试。")

if __name__ == "__main__":
    asyncio.run(main())
