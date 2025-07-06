import argparse
import glob
import os
import sys
import asyncio
import threading
import json

from anp_open_sdk.sdk_mode import SdkMode

from anp_open_sdk.config import UnifiedConfig, set_global_config
from anp_open_sdk.utils.log_base import setup_logging
from anp_open_sdk.anp_sdk import ANPSDK

import logging

from anp_open_sdk_framework.agent_manager import LocalAgentManager
from anp_open_sdk_framework.master_agent import MasterAgent
from anp_open_sdk_framework.unified_crawler import UnifiedCrawler
from anp_open_sdk_framework.unified_caller import UnifiedCaller


from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import  LocalUserDataManager
from anp_open_sdk_framework.adapter_transport.http_transport import HttpTransport
from anp_open_sdk_framework.adapter_auth.framework_auth import FrameworkAuthManager
from anp_open_sdk_framework.auth.auth_client import AuthClient


from anp_open_sdk_framework.local_methods.local_methods_doc import LocalMethodsDocGenerator
from anp_open_sdk.config import get_global_config

logger = logging.getLogger(__name__)


def show_usage_examples():
    print("""
🎯 ANP Open SDK Framework 使用示例

═══════════════════════════════════════════════════════════════════════════════

📋 1. 主智能体模式 (推荐用于复杂任务和自然语言交互)
───────────────────────────────────────────────────────────────────────────────

  🤖 交互模式 - 支持自然语言任务描述:
     python framework_demo.py --master-mode
     
  📝 单任务执行:
     python framework_demo.py --master-mode --task "调用demo方法"
     python framework_demo.py --master-mode --task "查找所有可用的计算方法"
     python framework_demo.py --master-mode --task "调用加法方法计算10+20"
     
  🔧 带参数的任务:
     python framework_demo.py --master-mode --task "计算两个数的和" --method-args '{"a": 15, "b": 25}'

═══════════════════════════════════════════════════════════════════════════════

🔧 2. 统一模式 (推荐用于明确的方法调用)
───────────────────────────────────────────────────────────────────────────────

  🎯 直接调用指定方法:
     python framework_demo.py --unified-mode --target-method "demo_method"
     
  🤖 智能调用 - 自动匹配最佳方法:
     python framework_demo.py --unified-mode --intelligent --target-method "计算"
     python framework_demo.py --unified-mode --intelligent --target-method "demo"
     
  📋 带参数调用:
     python framework_demo.py --unified-mode --target-method "calculate_sum" --method-args '{"args": [10, 20]}'
     python framework_demo.py --unified-mode --target-method "demo_method" --method-args '{"kwargs": {"message": "Hello"}}'

═══════════════════════════════════════════════════════════════════════════════

🔍 3. 默认发现模式 (不指定任何模式时)
───────────────────────────────────────────────────────────────────────────────

  📊 自动发现和演示所有可用功能:
     python framework_demo.py

═══════════════════════════════════════════════════════════════════════════════

💡 选择建议
───────────────────────────────────────────────────────────────────────────────

  🎯 明确知道要调用的方法     → 使用 --unified-mode
  🤖 需要智能匹配和推理       → 使用 --unified-mode --intelligent  
  📋 复杂任务或自然语言描述   → 使用 --master-mode
  🔍 探索可用功能            → 直接运行 (默认发现模式)

═══════════════════════════════════════════════════════════════════════════════

📚 更多信息请参考: MIGRATION_GUIDE.md
    """)

def parse_interactive_input(user_input):
    import shlex
    import json
    try:
        parts = shlex.split(user_input)
        if len(parts) == 1:
            return parts[0], {}
        task_parts = []
        method_args = {}
        i = 0
        while i < len(parts):
            if parts[i] == '--method-args' and i + 1 < len(parts):
                try:
                    method_args = json.loads(parts[i + 1])
                    i += 2
                except json.JSONDecodeError as e:
                    task_parts.append(parts[i])
                    i += 1
            else:
                task_parts.append(parts[i])
                i += 1
        task = ' '.join(task_parts)
        return task, method_args
    except Exception as e:
        return user_input, {}

def show_interactive_help():
    print("""
📚 交互模式使用帮助

═══════════════════════════════════════════════════════════════════════════════

🎯 输入格式:
───────────────────────────────────────────────────────────────────────────────

1. 简单任务 (自然语言描述):
   调用demo方法
   查找所有计算功能
   显示可用的方法列表

2. 带参数的任务:
   计算两个数的和 --method-args '{"a": 15, "b": 25}'
   调用demo方法 --method-args '{"message": "Hello World"}'

3. 复杂的自然语言任务:
   调用加法方法计算10和20的和
   找到所有包含"demo"关键词的方法
   执行一个简单的演示功能

═══════════════════════════════════════════════════════════════════════════════

💡 参数格式说明:
───────────────────────────────────────────────────────────────────────────────

--method-args 后面跟 JSON 格式的参数:
• 数字参数: '{"a": 15, "b": 25}'
• 字符串参数: '{"message": "Hello", "name": "World"}'
• 混合参数: '{"count": 5, "text": "test", "enabled": true}'

═══════════════════════════════════════════════════════════════════════════════

🔧 特殊命令:
───────────────────────────────────────────────────────────────────────────────

help     - 显示此帮助信息
quit     - 退出交互模式
exit     - 退出交互模式
退出     - 退出交互模式

═══════════════════════════════════════════════════════════════════════════════
    """)

async def main():
    parser = argparse.ArgumentParser(
        description="ANP Open SDK Framework - 统一的多智能体调用框架",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
工作模式说明:
  1. 主智能体模式 (--master-mode): 支持自然语言任务描述和复杂任务执行
  2. 统一调用模式 (--unified-mode): 精确的方法调用和智能匹配
  3. 默认发现模式: 自动发现和演示所有可用功能

使用 --help-examples 查看详细示例
        """
    )
    parser.add_argument(
        '--config',
        type=str,
        default='unified_config_anp_open_sdk_framework_demo_agent.yaml',
        help='配置文件路径'
    )
    mode_group = parser.add_argument_group('工作模式')
    mode_group.add_argument(
        '--master-mode',
        action='store_true',
        help='启用主智能体模式 - 支持自然语言任务描述和复杂任务执行'
    )
    mode_group.add_argument(
        '--unified-mode',
        action='store_true',
        help='启用统一调用模式 - 精确的方法调用和智能匹配'
    )
    master_group = parser.add_argument_group('主智能体模式参数')
    master_group.add_argument(
        '--task',
        type=str,
        help='任务描述，支持自然语言 (例: "调用demo方法", "查找计算功能")'
    )
    unified_group = parser.add_argument_group('统一调用模式参数')
    unified_group.add_argument(
        '--intelligent',
        action='store_true',
        help='启用智能匹配 - 自动找到最佳匹配的方法'
    )
    unified_group.add_argument(
        '--target-method',
        type=str,
        default='demo_method',
        help='目标方法名或描述 (默认: demo_method)'
    )
    common_group = parser.add_argument_group('通用参数')
    common_group.add_argument(
        '--method-args',
        type=str,
        help='方法参数 JSON 格式，例: \'{"args": [1, 2], "kwargs": {"name": "test"}}\''
    )
    common_group.add_argument(
        '--help-examples',
        action='store_true',
        help='显示详细的使用示例'
    )
    args = parser.parse_args()
    if args.help_examples:
        show_usage_examples()
        return
    if args.master_mode and args.unified_mode:
        logger.error("❌ 不能同时指定 --master-mode 和 --unified-mode")
        return
    if args.intelligent and not args.unified_mode:
        logger.error("❌ --intelligent 参数只能在 --unified-mode 下使用")
        return
    if args.task and not args.master_mode:
        logger.error("❌ --task 参数只能在 --master-mode 下使用")
        return

    config_file = args.config
    if not os.path.isabs(config_file):
        # 如果是相对路径，在当前脚本目录下查找
        script_dir = os.path.dirname(os.path.abspath(__file__))
        config_file = os.path.join(script_dir, config_file)
        app_config = UnifiedConfig(config_file=config_file, app_root=script_dir)
    else:
        app_config = UnifiedConfig(config_file=config_file)

    set_global_config(app_config)
    setup_logging()

    logger.info("🚀 启动 ANP Open SDK Framework...")
    if os.getcwd() not in sys.path:
        sys.path.append(os.getcwd())

    config = get_global_config()
    agent_config_path = config.multi_agent_mode.agents_cfg_path
    agent_files = glob.glob(f"{agent_config_path}/*/agent_mappings.yaml")
    if not agent_files:
        logger.info("❌ 未找到智能体配置文件，退出。")
        return

    prepared_agents_info = [LocalAgentManager.load_agent_from_module(f) for f in agent_files]
    valid_agents_info = [info for info in prepared_agents_info if info and info[0]]
    all_agents = [info[0] for info in valid_agents_info]
    lifecycle_modules = {info[0].id: info[1] for info in valid_agents_info}

    if not all_agents:
        logger.info("❌ 没有成功加载任何智能体，退出。")
        return

    logger.info(f"✅ 成功加载 {len(all_agents)} 个智能体，创建SDK实例...")
    sdk = ANPSDK(mode=SdkMode.MULTI_AGENT_ROUTER, agents=all_agents)

    # --- 核心改造开始 ---
    # 1. 在顶层创建核心服务实例
    # 这些实例将在整个应用程序的生命周期中作为单例使用
    user_data_manager = LocalUserDataManager()
    sdk.user_data_manager = user_data_manager
    http_transport = HttpTransport()
    # 注意：FrameworkAuthManager现在需要一个DIDResolver
    # 我们将在其构造函数中创建它，或者也可以在这里创建并注入
    framework_auth_manager = FrameworkAuthManager(user_data_manager, http_transport)
    auth_client = AuthClient(framework_auth_manager)

    # 2. 将核心服务注入到每个 agent 实例中
    logger.info("💉 正在向所有智能体注入核心服务...")
    for agent in all_agents:
        agent.auth_client = auth_client
        # 未来可以注入更多服务，如 Orchestrator, Crawler 等
        # agent.orchestrator = ...
    logger.info("✅ 核心服务注入完成。")
    # --- 核心改造结束 ---

    logger.info("🔄 执行智能体后初始化...")
    for agent in all_agents:
        module = lifecycle_modules.get(agent.id)
        if module and hasattr(module, "initialize_agent"):
            logger.info(f"  - 初始化智能体: {agent.name}")
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
    logger.info(f"⏳ 等待服务器启动 {host}:{port} ...")
    wait_for_port(host, port, timeout=15)
    logger.info("✅ 服务器就绪，开始执行任务。")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc_path = os.path.join(script_dir, f"{config.anp_sdk.host}_{config.anp_sdk.port}_local_methods_doc.json")
    LocalMethodsDocGenerator.generate_methods_doc(doc_path)

    if args.master_mode:
        logger.info("🤖 启动主智能体模式...")
        master_agent = MasterAgent(sdk, name="FrameworkMasterAgent")
        await master_agent.initialize()
        if args.task:
            logger.info(f"📋 执行任务: {args.task}")
            task_context = {}
            if args.method_args:
                try:
                    task_context = json.loads(args.method_args)
                    logger.info(f"📋 任务上下文: {task_context}")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ 任务上下文JSON格式错误: {e}")
                    return
            result = await master_agent.execute_task(args.task, task_context)
            logger.info(f"📊 任务执行完成")
            print(f"\n🎯 任务结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            logger.info("🎯 进入交互模式")
            print("\n" + "="*60)
            print("🤖 主智能体交互模式")
            print("💡 支持以下输入格式:")
            print("   1. 简单任务: 调用demo方法")
            print("   2. 带参数任务: 计算两个数的和 --method-args '{\"a\": 15, \"b\": 25}'")
            print("   3. 自然语言: 查找所有计算功能")
            print("   4. 复杂任务: 调用加法方法计算10+20")
            print("📝 输入 'quit', 'exit' 或 '退出' 结束会话")
            print("📝 输入 'help' 查看更多示例")
            print("="*60)
            while True:
                try:
                    user_input = input("\n🎯 请输入任务: ").strip()
                    if user_input.lower() in ['quit', 'exit', '退出', 'q']:
                        print("👋 再见！")
                        break
                    if user_input.lower() == 'help':
                        show_interactive_help()
                        continue
                    if user_input:
                        task, task_context = parse_interactive_input(user_input)
                        print(f"⏳ 执行任务: {task}")
                        if task_context:
                            print(f"📋 任务参数: {task_context}")
                        result = await master_agent.execute_task(task, task_context)
                        print(f"\n📊 结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
                    else:
                        print("⚠️  请输入有效的任务描述")
                except KeyboardInterrupt:
                    print("\n👋 再见！")
                    break
                except Exception as e:
                    logger.error(f"❌ 任务执行错误: {e}")
                    print(f"❌ 执行失败: {e}")
        return

    if args.unified_mode:
        logger.info("🔧 启动统一调用模式...")
        unified_crawler = UnifiedCrawler(sdk)
        unified_caller = UnifiedCaller(sdk)
        logger.info("📊 发现可用资源...")
        resources = await unified_crawler.discover_all_resources()
        resource_summary = unified_crawler.get_resource_summary()
        logger.info(f"✅ 资源发现完成: {resource_summary}")
        if args.target_method:
            method_args = {}
            if args.method_args:
                try:
                    method_args = json.loads(args.method_args)
                    logger.info(f"📋 解析到方法参数: {method_args}")
                except json.JSONDecodeError as e:
                    logger.error(f"❌ 方法参数JSON格式错误: {e}")
                    return
            try:
                if args.intelligent:
                    logger.info(f"🤖 智能调用目标方法: {args.target_method}")
                    result = await unified_crawler.intelligent_call(args.target_method, **method_args)
                else:
                    logger.info(f"🎯 直接调用目标方法: {args.target_method}")
                    result = await unified_crawler.call_by_name(args.target_method, **method_args)
                logger.info("✅ 调用完成")
                print(f"\n🎯 调用结果:\n{json.dumps(result, indent=2, ensure_ascii=False)}")
            except Exception as e:
                logger.error(f"❌ 调用失败: {e}")
        else:
            logger.info("💡 未指定目标方法，显示可用资源摘要")
            print(f"\n📊 可用资源摘要:\n{resource_summary}")
        return

    logger.info("🔍 启动默认发现模式...")
    print("\n" + "="*60)
    print("🔍 默认发现模式 - 演示所有可用功能")
    print("💡 建议使用以下模式获得更好体验:")
    print("   --master-mode     (主智能体模式)")
    print("   --unified-mode    (统一调用模式)")
    print("   --help-examples   (查看详细示例)")
    print("="*60)
    discovery_agent = None
    for agent in all_agents:
        if hasattr(agent, 'discover_and_describe_agents'):
            discovery_agent = agent
            break
    if discovery_agent:
        logger.info(f"✅ 找到发现智能体: '{discovery_agent.name}'，开始演示...")
        try:
            result = await discovery_agent.run_ai_root_crawler_demo()
            print(f"\n🤖 AI根爬虫演示结果:\n{result}")
        except Exception as e:
            logger.error(f"❌ AI根爬虫演示失败: {e}")
        try:
            result = await discovery_agent.run_agent_002_demo(sdk)
            print(f"\n🔧 Agent 002 演示结果:\n{result}")
        except Exception as e:
            logger.error(f"❌ Agent 002 演示失败: {e}")
        try:
            result = await discovery_agent.run_agent_002_demo_new()
            print(f"\n🆕 Agent 002 新演示结果:\n{result}")
        except Exception as e:
            logger.error(f"❌ Agent 002 新演示失败: {e}")
    else:
        logger.warning("⚠️ 未找到具有发现功能的智能体")
        print("\n💡 尝试使用以下命令体验框架功能:")
        print("   python framework_demo.py --master-mode")
        print("   python framework_demo.py --unified-mode --intelligent --target-method demo")

    print(f"\n🔥 服务器仍在运行中...")
    print("💡 你可以:")
    print("   1. 按任意键停止服务器")
    print("   2. 在另一个终端中使用其他模式测试")
    print("   3. 查看生成的文档: localhost_9527_local_methods_doc.json")
    input("\n⏸️  按任意键停止服务器...")

    logger.info("🛑 收到停止信号，开始清理...")

    cleanup_tasks = []
    for agent in all_agents:
        module = lifecycle_modules.get(agent.id)
        if module and hasattr(module, "cleanup_agent"):
            logger.info(f"  - 清理智能体: {agent.name}")
            cleanup_tasks.append(module.cleanup_agent())

    if cleanup_tasks:
        await asyncio.gather(*cleanup_tasks)
    logger.info("✅ 所有智能体已清理完成")

    if 'sdk' in locals():
        logger.info("  - 停止服务器...")
        if hasattr(sdk, "stop_server"):
            sdk.stop_server()
            logger.info("  - 服务器已停止")
        else:
            logger.info("  - SDK实例没有stop_server方法")

    logger.info("👋 程序退出")
    sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
        pass
