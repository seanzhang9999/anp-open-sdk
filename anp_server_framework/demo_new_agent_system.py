#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
新Agent系统演示
展示如何使用统一的AgentManager创建Agent，以及如何处理冲突
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from anp_sdk.anp_user import ANPUser
from anp_server_framework.agent_manager import AgentManager
from anp_server_framework.global_router import GlobalRouter
from anp_server_framework.global_message_manager import GlobalMessageManager

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化配置
def init_config():
    """初始化配置"""
    from anp_sdk.config import UnifiedConfig, set_global_config
    from anp_sdk.anp_sdk_user_data import get_user_data_manager
    
    # 使用framework demo配置文件
    config_path = "unified_config_framework_demo.yaml"
    if os.path.exists(config_path):
        config = UnifiedConfig(config_path)
        set_global_config(config)
        print(f"✅ 配置已加载: {config_path}")
        
        # 初始化用户数据管理器
        user_data_manager = get_user_data_manager()
        user_data_manager.scan_and_load_new_users()
        print(f"✅ 用户数据已扫描加载")
        
    else:
        print(f"⚠️  配置文件不存在: {config_path}，使用默认配置")
        # 创建最小配置
        config = UnifiedConfig()
        set_global_config(config)


async def demo_exclusive_agents():
    """演示独占模式的Agent"""
    print("\n" + "="*60)
    print("🔥 演示1: 独占模式Agent")
    print("="*60)
    
    try:
        # 创建第一个独占Agent - 使用现有的DID
        anp_user1 = ANPUser.from_did("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1")
        agent1 = AgentManager.create_agent(anp_user1, "独占Agent1", shared=False)
        
        # 注册API
        @agent1.api("/hello")
        def hello_api(request_data, request):
            return {"message": "Hello from 独占Agent1"}
        
        # 注册消息处理器
        @agent1.message_handler("text")
        async def handle_text(msg_data):
            return {"reply": f"独占Agent1收到: {msg_data.get('content')}"}
        
        print(f"✅ 创建成功: {agent1}")
        
        # 尝试创建第二个使用相同DID的独占Agent（应该失败）
        try:
            anp_user2 = ANPUser.from_did("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1")
            agent2 = AgentManager.create_agent(anp_user2, "独占Agent2", shared=False)
            print("❌ 这不应该成功！")
        except ValueError as e:
            print(f"✅ 预期的冲突检测: {e}")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")


async def demo_shared_agents():
    """演示共享模式的Agent"""
    print("\n" + "="*60)
    print("🔥 演示2: 共享模式Agent")
    print("="*60)
    
    try:
        # 创建共享DID的多个Agent - 使用现有的DID
        shared_did = "did:wba:localhost%3A9527:wba:user:5fea49e183c6c211"
        anp_user_shared = ANPUser.from_did(shared_did)
        
        # 创建第一个共享Agent（主Agent）
        agent1 = AgentManager.create_agent(
            anp_user_shared, 
            "计算器Agent", 
            shared=True, 
            prefix="/calculator",
            primary_agent=True
        )
        
        # 注册API
        @agent1.api("/add")
        def add_api(request_data, request):
            a = request_data.get('a', 0)
            b = request_data.get('b', 0)
            return {"result": a + b}
        
        # 主Agent可以注册消息处理器
        @agent1.message_handler("text")
        async def handle_text(msg_data):
            return {"reply": f"计算器Agent收到: {msg_data.get('content')}"}
        
        # 创建第二个共享Agent（非主Agent）
        agent2 = AgentManager.create_agent(
            anp_user_shared, 
            "天气Agent", 
            shared=True, 
            prefix="/weather",
            primary_agent=False
        )
        
        # 注册API
        @agent2.api("/current")
        def weather_api(request_data, request):
            city = request_data.get('city', '北京')
            return {"weather": f"{city}今天晴天"}
        
        # 非主Agent尝试注册消息处理器（应该失败）
        try:
            @agent2.message_handler("weather")
            async def handle_weather(msg_data):
                return {"reply": "天气查询"}
        except PermissionError as e:
            print(f"✅ 预期的权限错误: {e}")
        
        print(f"✅ 共享Agent1: {agent1}")
        print(f"✅ 共享Agent2: {agent2}")
        
        # 尝试创建prefix冲突的Agent（应该失败）
        try:
            agent3 = AgentManager.create_agent(
                anp_user_shared, 
                "冲突Agent", 
                shared=True, 
                prefix="/calculator"  # 与agent1冲突
            )
        except ValueError as e:
            print(f"✅ 预期的prefix冲突: {e}")
        
        # 尝试创建第二个主Agent（应该失败）
        try:
            agent4 = AgentManager.create_agent(
                anp_user_shared, 
                "第二主Agent", 
                shared=True, 
                prefix="/second",
                primary_agent=True  # 与agent1冲突
            )
        except ValueError as e:
            print(f"✅ 预期的主Agent冲突: {e}")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")


async def demo_global_router():
    """演示全局路由器功能"""
    print("\n" + "="*60)
    print("🔥 演示3: 全局路由器")
    print("="*60)
    
    # 列出所有路由
    routes = GlobalRouter.list_routes()
    print(f"📋 当前注册的路由数量: {len(routes)}")
    
    for route in routes:
        print(f"  🔗 {route['did']}{route['path']} <- {route['agent_name']}")
    
    # 获取路由统计
    stats = GlobalRouter.get_stats()
    print(f"📊 路由统计: {stats}")
    
    # 获取冲突记录
    conflicts = GlobalRouter.get_conflicts()
    if conflicts:
        print(f"⚠️  路由冲突记录: {len(conflicts)}个")
        for conflict in conflicts:
            print(f"  - {conflict['did']}{conflict['path']}: {conflict['existing_agent']} vs {conflict['new_agent']}")
    else:
        print("✅ 无路由冲突")


async def demo_global_message_manager():
    """演示全局消息管理器功能"""
    print("\n" + "="*60)
    print("🔥 演示4: 全局消息管理器")
    print("="*60)
    
    # 列出所有消息处理器
    handlers = GlobalMessageManager.list_handlers()
    print(f"📋 当前注册的消息处理器数量: {len(handlers)}")
    
    for handler in handlers:
        print(f"  💬 {handler['did']}:{handler['msg_type']} <- {handler['agent_name']}")
    
    # 获取统计
    stats = GlobalMessageManager.get_stats()
    print(f"📊 消息处理器统计: {stats}")
    
    # 获取冲突记录
    conflicts = GlobalMessageManager.get_conflicts()
    if conflicts:
        print(f"⚠️  消息处理器冲突记录: {len(conflicts)}个")
        for conflict in conflicts:
            print(f"  - {conflict['did']}:{conflict['msg_type']}: {conflict['existing_agent']} vs {conflict['new_agent']}")
    else:
        print("✅ 无消息处理器冲突")


async def demo_agent_manager():
    """演示AgentManager功能"""
    print("\n" + "="*60)
    print("🔥 演示5: AgentManager管理功能")
    print("="*60)
    
    # 列出所有Agent
    agents = AgentManager.list_agents()
    print(f"📋 当前管理的Agent:")
    
    for did, agent_dict in agents.items():
        print(f"  DID: {did}")
        for agent_name, agent_info in agent_dict.items():
            mode = "共享" if agent_info['shared'] else "独占"
            primary = " (主)" if agent_info.get('primary_agent') else ""
            prefix = f" prefix:{agent_info['prefix']}" if agent_info['prefix'] else ""
            print(f"    - {agent_name}: {mode}{primary}{prefix}")


async def main():
    """主演示函数"""
    print("🚀 新Agent系统演示开始")
    
    try:
        # 初始化配置
        init_config()
        
        # 清理之前的状态
        AgentManager.clear_all_agents()
        GlobalRouter.clear_routes()
        GlobalMessageManager.clear_handlers()
        
        # 运行各个演示
        await demo_exclusive_agents()
        await demo_shared_agents()
        await demo_global_router()
        await demo_global_message_manager()
        await demo_agent_manager()
        
        print("\n" + "="*60)
        print("🎉 演示完成！新Agent系统工作正常")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
