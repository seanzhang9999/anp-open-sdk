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

# 导入新的Agent系统
from anp_server_framework.agent_manager import AgentManager, LocalAgentManager
from anp_server_framework.global_router import GlobalRouter
from anp_server_framework.global_message_manager import GlobalMessageManager

from anp_server_framework.local_service.local_methods_doc import LocalMethodsDocGenerator

app_config = UnifiedConfig(config_file='unified_config_framework_demo.yaml')
set_global_config(app_config)
setup_logging()
logger = logging.getLogger(__name__)


async def create_agents_with_new_system():
    """使用新的Agent系统创建Agent"""
    logger.info("🔧 使用新Agent系统创建Agent...")
    
    # 清理之前的状态
    AgentManager.clear_all_agents()
    GlobalRouter.clear_routes()
    GlobalMessageManager.clear_handlers()
    
    created_agents = []
    
    # 1. 加载现有的Agent配置文件
    agent_files = glob.glob("data_user/localhost_9527/agents_config/*/agent_mappings.yaml")
    if not agent_files:
        logger.warning("未找到Agent配置文件，将创建代码生成的Agent")
    
    # 2. 使用现有配置创建Agent
    for agent_file in agent_files:
        try:
            agent, handler_module, share_did_config = await LocalAgentManager.load_agent_from_module(agent_file)
            if agent:
                # 使用新的Agent系统重新创建
                if share_did_config:
                    # 共享DID模式 - 检查是否应该是主Agent
                    # 只有第一个共享DID的Agent才设为主Agent
                    is_primary = not any(
                        info.get('shared') and info.get('primary_agent') 
                        for agents_dict in AgentManager._did_usage_registry.values()
                        for info in agents_dict.values()
                        if agents_dict
                    )
                    
                    new_agent = AgentManager.create_agent(
                        agent, 
                        agent.name, 
                        shared=True, 
                        prefix=share_did_config.get('path_prefix', ''),
                        primary_agent=is_primary  # 智能判断是否为主Agent
                    )
                else:
                    # 独占DID模式
                    new_agent = AgentManager.create_agent(
                        agent, 
                        agent.name, 
                        shared=False
                    )
                
                # 注册现有的API和消息处理器 - 使用list()避免字典在迭代时被修改
                for path, handler in list(agent.api_routes.items()):
                    new_agent.api(path)(handler)
                
                for msg_type, handler in list(agent.message_handlers.items()):
                    new_agent.message_handler(msg_type)(handler)
                
                created_agents.append(new_agent)
                logger.info(f"✅ 已转换Agent: {agent.name}")
                
        except Exception as e:
            logger.error(f"❌ 转换Agent失败 {agent_file}: {e}")
    
    # 3. 创建代码生成的Agent
    code_generated_agents = await create_code_generated_agents()
    created_agents.extend(code_generated_agents)
    
    return created_agents


async def create_code_generated_agents():
    """创建代码生成的Agent"""
    logger.info("🤖 创建代码生成的Agent...")
    
    from anp_sdk.anp_user import ANPUser
    
    code_agents = []
    
    try:
        # 创建一个代码生成的计算器Agent - 使用不同的DID避免冲突
        calc_user = ANPUser.from_did("did:wba:localhost%3A9527:wba:user:27c0b1d11180f973")
        calc_agent = AgentManager.create_agent(calc_user, "代码生成计算器", shared=False)
        
        # 注册API
        @calc_agent.api("/add")
        async def add_api(request_data, request):
            """加法计算API"""
            # 从params中获取参数
            params = request_data.get('params', {})
            a = params.get('a', 0)
            b = params.get('b', 0)
            result = a + b
            logger.info(f"🔢 计算: {a} + {b} = {result}")
            return {"result": result, "operation": "add", "inputs": [a, b]}
        
        @calc_agent.api("/multiply")
        async def multiply_api(request_data, request):
            """乘法计算API"""
            # 从params中获取参数
            params = request_data.get('params', {})
            a = params.get('a', 1)
            b = params.get('b', 1)
            result = a * b
            logger.info(f"🔢 计算: {a} × {b} = {result}")
            return {"result": result, "operation": "multiply", "inputs": [a, b]}
        
        # 注册消息处理器
        @calc_agent.message_handler("text")
        async def handle_calc_message(msg_data):
            content = msg_data.get('content', '')
            logger.info(f"💬 代码生成计算器收到消息: {content}")
            
            # 简单的计算解析
            if '+' in content:
                try:
                    parts = content.split('+')
                    if len(parts) == 2:
                        a = float(parts[0].strip())
                        b = float(parts[1].strip())
                        result = a + b
                        return {"reply": f"计算结果: {a} + {b} = {result}"}
                except:
                    pass
            
            return {"reply": f"代码生成计算器收到: {content}。支持格式如 '5 + 3'"}
        
        code_agents.append(calc_agent)
        logger.info("✅ 创建代码生成计算器Agent成功")
        
        # 创建一个代码生成的天气Agent（共享DID）
        weather_user = ANPUser.from_did("did:wba:localhost%3A9527:wba:user:5fea49e183c6c211")
        weather_agent = AgentManager.create_agent(
            weather_user, 
            "代码生成天气", 
            shared=True, 
            prefix="/weather",
            primary_agent=True
        )
        
        @weather_agent.api("/current")
        async def weather_current_api(request_data, request):
            """获取当前天气API"""
            # 从params中获取参数
            params = request_data.get('params', {})
            city = params.get('city', '北京')
            # 模拟天气数据
            weather_data = {
                "city": city,
                "temperature": "22°C",
                "condition": "晴天",
                "humidity": "65%",
                "wind": "微风"
            }
            logger.info(f"🌤️ 查询天气: {city} - {weather_data['condition']}")
            return weather_data
        
        @weather_agent.api("/forecast")
        async def weather_forecast_api(request_data, request):
            """获取天气预报API"""
            # 从params中获取参数
            params = request_data.get('params', {})
            city = params.get('city', '北京')
            days = params.get('days', 3)
            
            forecast = []
            conditions = ["晴天", "多云", "小雨"]
            for i in range(days):
                forecast.append({
                    "date": f"2024-01-{15+i:02d}",
                    "condition": conditions[i % len(conditions)],
                    "high": f"{20+i}°C",
                    "low": f"{10+i}°C"
                })
            
            result = {"city": city, "forecast": forecast}
            logger.info(f"🌤️ 查询{days}天预报: {city}")
            return result
        
        @weather_agent.message_handler("text")
        async def handle_weather_message(msg_data):
            content = msg_data.get('content', '')
            logger.info(f"💬 代码生成天气Agent收到消息: {content}")
            
            if '天气' in content:
                return {"reply": f"天气查询服务已收到: {content}。可以查询任何城市的天气信息。"}
            
            return {"reply": f"代码生成天气Agent收到: {content}"}
        
        code_agents.append(weather_agent)
        logger.info("✅ 创建代码生成天气Agent成功")
        
        # 创建一个助手Agent（共享DID，非主Agent）
        assistant_agent = AgentManager.create_agent(
            weather_user,  # 使用相同的DID
            "代码生成助手", 
            shared=True, 
            prefix="/assistant",
            primary_agent=False  # 非主Agent
        )
        
        @assistant_agent.api("/help")
        async def help_api(request_data, request):
            """帮助信息API"""
            # 从params中获取参数
            params = request_data.get('params', {})
            topic = params.get('topic', 'general')
            
            help_info = {
                "general": "我是代码生成助手，可以提供各种帮助信息",
                "weather": "天气相关帮助：使用 /weather/current 查询当前天气",
                "calc": "计算相关帮助：使用 /add 或 /multiply 进行计算"
            }
            
            response = {
                "topic": topic,
                "help": help_info.get(topic, help_info["general"]),
                "available_topics": list(help_info.keys())
            }
            
            logger.info(f"❓ 提供帮助: {topic}")
            return response
        
        code_agents.append(assistant_agent)
        logger.info("✅ 创建代码生成助手Agent成功")
        
    except Exception as e:
        logger.error(f"❌ 创建代码生成Agent失败: {e}")
        import traceback
        traceback.print_exc()
    
    return code_agents


async def main():
    logger.debug("🚀 Starting New Agent System Demo...")
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())

    config = get_global_config()
    
    # 使用新的Agent系统创建Agent
    all_agents = await create_agents_with_new_system()
    
    if not all_agents:
        logger.info("No agents were created. Exiting.")
        return

    # 获取ANPUser实例用于服务器
    anp_users = []
    for agent in all_agents:
        if hasattr(agent, 'anp_user'):
            anp_users.append(agent.anp_user)
    
    # --- 启动SDK ---
    logger.info("\n✅ All agents created with new system. Creating SDK instance...")
    svr = ANP_Server(mode=ServerMode.MULTI_AGENT_ROUTER, agents=anp_users)
    
    # 生成接口文档
    for agent in all_agents:
        if hasattr(agent, 'anp_user'):
            await LocalAgentManager.generate_and_save_agent_interfaces(agent.anp_user, svr)

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

    # 生成本地方法文档
    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(script_dir, "local_methods_doc.json")
    LocalMethodsDocGenerator.generate_methods_doc(doc_path)

    # 显示Agent管理器状态
    logger.info("\n📊 Agent管理器状态:")
    agents_info = AgentManager.list_agents()
    for did, agent_dict in agents_info.items():
        logger.info(f"  DID: {did}")
        for agent_name, agent_info in agent_dict.items():
            mode = "共享" if agent_info['shared'] else "独占"
            primary = " (主)" if agent_info.get('primary_agent') else ""
            prefix = f" prefix:{agent_info['prefix']}" if agent_info['prefix'] else ""
            logger.info(f"    - {agent_name}: {mode}{primary}{prefix}")

    # 显示全局路由器状态
    logger.info("\n🔗 全局路由器状态:")
    routes = GlobalRouter.list_routes()
    for route in routes:
        logger.info(f"  🔗 {route['did']}{route['path']} <- {route['agent_name']}")

    # 显示全局消息管理器状态
    logger.info("\n💬 全局消息管理器状态:")
    handlers = GlobalMessageManager.list_handlers()
    for handler in handlers:
        logger.info(f"  💬 {handler['did']}:{handler['msg_type']} <- {handler['agent_name']}")

    # 调试：检查ANPUser的API路由
    logger.info("\n🔍 调试：检查ANPUser的API路由注册情况...")
    for agent in all_agents:
        if hasattr(agent, 'anp_user'):
            logger.info(f"Agent: {agent.name}")
            logger.info(f"  DID: {agent.anp_user.id}")
            logger.info(f"  API路由数量: {len(agent.anp_user.api_routes)}")
            for path, handler in agent.anp_user.api_routes.items():
                handler_name = handler.__name__ if hasattr(handler, '__name__') else 'unknown'
                logger.info(f"    - {path}: {handler_name}")

    # 测试新Agent系统功能
    await test_new_agent_system(all_agents)

    logger.info("\n🔥 Demo completed. Press Ctrl+C to stop.")


async def test_new_agent_system(agents):
    """测试新Agent系统的功能"""
    logger.info("\n🧪 开始测试新Agent系统功能...")
    
    # 找到不同类型的Agent
    calc_agent = None
    weather_agent = None
    assistant_agent = None
    
    for agent in agents:
        if "计算器" in agent.name:
            calc_agent = agent
        elif "天气" in agent.name:
            weather_agent = agent
        elif "助手" in agent.name:
            assistant_agent = agent
    
    # 测试1: API调用
    if calc_agent:
        logger.info(f"\n🔧 测试计算器Agent API调用...")
        try:
            # 模拟API调用
            calc_did = calc_agent.anp_user.id if hasattr(calc_agent, 'anp_user') else calc_agent.did
            result = await agent_api_call_post(
                caller_agent="did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d",
                target_agent=calc_did,
                api_path="/add",
                params={"a": 15, "b": 25}
            )
            logger.info(f"✅ 计算器API调用成功: {result}")
        except Exception as e:
            logger.error(f"❌ 计算器API调用失败: {e}")
    
    # 测试2: 消息发送
    if weather_agent:
        logger.info(f"\n📨 测试天气Agent消息发送...")
        try:
            weather_did = weather_agent.anp_user.id if hasattr(weather_agent, 'anp_user') else weather_agent.did
            result = await agent_msg_post(
                caller_agent="did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d",
                target_agent=weather_did,
                content="请问今天北京的天气怎么样？",
                message_type="text"
            )
            logger.info(f"✅ 天气Agent消息发送成功: {result}")
        except Exception as e:
            logger.error(f"❌ 天气Agent消息发送失败: {e}")
    
    # 测试3: 共享DID API调用
    if weather_agent and assistant_agent:
        logger.info(f"\n🔗 测试共享DID API调用...")
        try:
            # 调用天气API
            weather_did = weather_agent.anp_user.id if hasattr(weather_agent, 'anp_user') else weather_agent.did
            weather_result = await agent_api_call_post(
                caller_agent="did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d",
                target_agent=weather_did,
                api_path="/weather/current",
                params={"city": "上海"}
            )
            logger.info(f"✅ 天气API调用成功: {weather_result}")
            
            # 调用助手API
            assistant_did = assistant_agent.anp_user.id if hasattr(assistant_agent, 'anp_user') else assistant_agent.did
            help_result = await agent_api_call_post(
                caller_agent="did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d",
                target_agent=assistant_did,
                api_path="/assistant/help",
                params={"topic": "weather"}
            )
            logger.info(f"✅ 助手API调用成功: {help_result}")
            
        except Exception as e:
            logger.error(f"❌ 共享DID API调用失败: {e}")
    
    # 测试4: 冲突检测
    logger.info(f"\n⚠️  测试冲突检测...")
    try:
        # 尝试创建冲突的Agent
        from anp_sdk.anp_user import ANPUser
        test_user = ANPUser.from_did("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1")
        
        # 这应该失败，因为DID已被独占使用
        conflict_agent = AgentManager.create_agent(test_user, "冲突测试Agent", shared=False)
        logger.error("❌ 冲突检测失败：应该阻止创建冲突Agent")
        
    except ValueError as e:
        logger.info(f"✅ 冲突检测成功: {e}")
    except Exception as e:
        logger.error(f"❌ 冲突检测异常: {e}")
    
    logger.info(f"\n🎉 新Agent系统测试完成!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
