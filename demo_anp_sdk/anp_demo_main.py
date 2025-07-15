e#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2024 ANP Open SDK Authors

"""ANP SDK 综合演示程序 - 使用新Agent系统"""
import sys
import os
import argparse
import asyncio
import traceback
import logging
import glob
import threading
import time
import socket
import json

# 添加路径以便导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anp_sdk.utils.log_base import setup_logging
from anp_sdk.config import UnifiedConfig, set_global_config, get_global_config
from anp_server.anp_server import ANP_Server
from anp_server.server_mode import ServerMode
from anp_server_framework.agent_manager import AgentManager, LocalAgentManager
from anp_server_framework.anp_service.agent_api_call import agent_api_call_post
from anp_server_framework.anp_service.agent_message_p2p import agent_msg_post

app_config = UnifiedConfig(config_file='unified_config_framework_demo.yaml')
set_global_config(app_config)

setup_logging()
logger = logging.getLogger(__name__)


class ANPDemoApplication:
    """ANP SDK 演示应用程序主类 - 使用新Agent系统"""

    def __init__(self, args):
        logger.info("🔧 初始化 ANPDemoApplication (新Agent系统)...")
        self.args = args
        self.agents = []
        self.server = None
        self.server_thread = None

    async def initialize_agents(self):
        """初始化所有Agent"""
        logger.info("\n🤖 使用新Agent系统创建Agent...")
        
        # 从配置文件加载Agent
        agent_files = glob.glob("data_user/localhost_9527/agents_config/*/agent_mappings.yaml")
        if not agent_files:
            logger.warning("未找到Agent配置文件")
            return []

        # 使用LocalAgentManager加载Agent
        for agent_file in agent_files:
            try:
                # 使用正确的方法名
                agent_info = await LocalAgentManager.load_agent_from_module(agent_file)
                if agent_info and agent_info[0]:
                    anp_user = agent_info[0]  # 这里返回的是ANPUser，不是Agent
                    
                    # 需要将ANPUser转换为Agent
                    # 检查是否有共享DID配置
                    share_config = agent_info[2] if len(agent_info) > 2 else None
                    
                    if share_config:
                        # 共享DID模式
                        agent = AgentManager.create_agent(
                            anp_user=anp_user,
                            name=anp_user.name,
                            shared=True,
                            prefix=share_config.get('path_prefix', ''),
                            primary_agent=share_config.get('primary_agent', True)  # 从配置中读取
                        )
                    else:
                        # 独占DID模式
                        agent = AgentManager.create_agent(
                            anp_user=anp_user,
                            name=anp_user.name,
                            shared=False
                        )
                    
                    self.agents.append(agent)
                    logger.info(f"✅ 已加载Agent: {agent.name}")
            except Exception as e:
                logger.error(f"❌ 加载Agent失败 {agent_file}: {e}")

        if not self.agents:
            logger.error("没有成功加载任何Agent")
            return []

        logger.info(f"📊 总共加载了 {len(self.agents)} 个Agent")
        return self.agents

    def start_server(self):
        """启动服务器"""
        logger.info("\n🚀 启动ANP服务器...")
        
        # 创建服务器实例 - 需要传入Agent列表而不是Agent对象
        agent_list = []
        for agent in self.agents:
            agent_list.append(agent.anp_user)  # ANP_Server需要ANPUser对象
        
        self.server = ANP_Server(mode=ServerMode.MULTI_AGENT_ROUTER, anp_users=agent_list)
        
        # 手动注册所有Agent到SDK路由器（包括共享DID的Agent）
        logger.info("🔧 手动注册所有Agent到SDK路由器...")
        for agent in self.agents:
            try:
                # 确保Agent名称被正确设置
                if not hasattr(agent.anp_user, 'name') or not agent.anp_user.name:
                    agent.anp_user.name = agent.name
                
                # 手动调用注册方法
                self.server.register_anp_user(agent.anp_user)
                
                # 手动注册Agent名称索引（确保所有Agent都被正确索引）
                agent_key = f"{agent.anp_user_id}#{agent.name}"
                if hasattr(self.server, 'router'):
                    # 直接操作router的全局索引，确保Agent名称被正确注册
                    self.server.router_agent.global_agents[agent_key] = agent.anp_user
                    logger.info(f"✅ 手动注册Agent名称索引: {agent_key}")
                
                logger.info(f"✅ 手动注册Agent: {agent.name} -> {agent.anp_user_id}")
            except Exception as e:
                logger.error(f"❌ 手动注册Agent失败 {agent.name}: {e}")
        
        # 注册共享DID配置
        shared_did_configs = {}
        for agent in self.agents:
            if agent.shared and agent.prefix:
                # 构建共享DID配置
                shared_did = agent.anp_user_id
                path_prefix = agent.prefix
                # 从Agent的API路由中提取API路径
                api_paths = list(agent.anp_user.api_routes.keys()) if hasattr(agent.anp_user, 'api_routes') else ['/chat']
                
                shared_did_configs[agent.name] = {
                    'shared_did': shared_did,
                    'path_prefix': path_prefix,
                    'api_paths': api_paths
                }
        
        if shared_did_configs:
            logger.info("🔗 注册共享DID配置...")
            for agent_name, share_config in shared_did_configs.items():
                shared_did = share_config['shared_did']
                path_prefix = share_config['path_prefix']
                api_paths = share_config['api_paths']
                
                # 找到对应的Agent实例
                target_agent = None
                for agent in self.agents:
                    if agent.name == agent_name:
                        target_agent = agent
                        break
                
                if target_agent and hasattr(self.server, 'router'):
                    # 使用Agent的注册键（DID#Agent名称）进行共享DID注册
                    agent_registration_key = f"{target_agent.anp_user_id}#{target_agent.name}"
                    self.server.router_agent.register_shared_did(shared_did, agent_registration_key, path_prefix, api_paths)
                    logger.info(f"  ✅ 已注册共享DID: {shared_did} -> {agent_name} (前缀: {path_prefix})")
                    logger.info(f"    注册键: {agent_registration_key}")
                    logger.info(f"    API路径: {api_paths}")
                    
                    # 调试：检查注册后的共享DID注册表状态
                    shared_did_info = self.server.router_agent.get_shared_did_info(shared_did)
                    logger.info(f"    共享DID注册表状态: {shared_did_info}")
                else:
                    logger.warning(f"  ❌ 未找到Agent或路由器: {agent_name}")
            
            logger.info(f"📊 共享DID统计: {len(shared_did_configs)} 个Agent使用共享DID")
        
        # 确保所有Agent都被正确注册到全局索引中
        if hasattr(self.server, 'ensure_all_agents_registered'):
            self.server.ensure_all_anp_user_registered()
            logger.info("🔧 已确保所有Agent都注册到全局索引")
        
        # 在单独线程中启动服务器
        def run_server():
            if hasattr(self.server, 'start_server'):
                self.server.start_server()
            else:
                logger.error("ANP_Server没有start_server方法")
        
        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        
        # 等待服务器启动
        config = get_global_config()
        host = config.anp_sdk.host
        port = config.anp_sdk.port
        
        logger.info(f"⏳ 等待服务器启动 {host}:{port} ...")
        self.wait_for_port(host, port, timeout=15)
        logger.info("✅ 服务器就绪")

    def wait_for_port(self, host, port, timeout=10.0):
        """等待端口可用"""
        start = time.time()
        while time.time() - start < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except (OSError, ConnectionRefusedError):
                time.sleep(0.2)
        raise RuntimeError(f"服务器 {host}:{port} 在 {timeout} 秒内未启动")

    async def run_demo_tests(self):
        """运行演示测试"""
        logger.info("\n🧪 开始运行演示测试...")
        
        # 找到测试用的Agent
        orchestrator_agent = None
        calculator_agent = None
        llm_agent = None
        
        for agent in self.agents:
            if "orchestrator" in agent.name.lower():
                orchestrator_agent = agent
            elif "calculator" in agent.name.lower():
                calculator_agent = agent
            elif "llm" in agent.name.lower() or "language" in agent.name.lower():
                llm_agent = agent
        
        if not orchestrator_agent:
            logger.warning("未找到Orchestrator Agent，跳过测试")
            return
        
        # 测试1: API调用测试
        if calculator_agent:
            await self.test_api_call(orchestrator_agent, calculator_agent)
        
        # 测试2: 消息发送测试
        if llm_agent:
            await self.test_message_sending(orchestrator_agent, llm_agent)
        
        # 测试3: 共享DID测试
        await self.test_shared_did_functionality(orchestrator_agent)

    async def test_api_call(self, caller_agent, target_agent):
        """测试API调用"""
        logger.info(f"\n🔧 测试API调用: {caller_agent.name} -> {target_agent.name}")
        
        try:
            # 调用计算器API
            result = await agent_api_call_post(
                caller_agent=caller_agent.anp_user_id,
                target_agent=target_agent.anp_user_id,
                api_path="/add",
                params={"a": 15, "b": 25}
            )
            
            logger.info(f"✅ API调用成功: {json.dumps(result, ensure_ascii=False)}")
            
            # 验证结果
            if isinstance(result, dict) and result.get("result") == 40:
                logger.info("🎉 计算结果正确!")
            else:
                logger.warning(f"⚠️ 计算结果异常: {result}")
                
        except Exception as e:
            logger.error(f"❌ API调用失败: {e}")

    async def test_message_sending(self, caller_agent, target_agent):
        """测试消息发送"""
        logger.info(f"\n📨 测试消息发送: {caller_agent.name} -> {target_agent.name}")
        
        try:
            # 发送消息
            result = await agent_msg_post(
                caller_agent=caller_agent.anp_user_id,
                target_agent=target_agent.anp_user_id,
                content="你好，这是一条测试消息",
                message_type="text"
            )
            
            logger.info(f"✅ 消息发送成功: {json.dumps(result, ensure_ascii=False)}")
            
        except Exception as e:
            logger.error(f"❌ 消息发送失败: {e}")

    async def test_shared_did_functionality(self, caller_agent):
        """测试共享DID功能"""
        logger.info(f"\n🔗 测试共享DID功能...")
        
        # 查找共享DID的Agent
        shared_did_agents = [agent for agent in self.agents if agent.shared]
        
        if not shared_did_agents:
            logger.info("未找到共享DID的Agent，跳过测试")
            return
        
        for shared_agent in shared_did_agents:
            logger.info(f"🧪 测试共享DID Agent: {shared_agent.name}")
            
            # 测试共享DID的API调用
            if shared_agent.prefix:
                test_path = f"{shared_agent.prefix}/chat"
                try:
                    result = await agent_api_call_post(
                        caller_agent=caller_agent.anp_user_id,
                        target_agent=shared_agent.anp_user_id,
                        api_path=test_path,
                        params={"message": "测试共享DID"}
                    )
                    logger.info(f"✅ 共享DID API调用成功: {json.dumps(result, ensure_ascii=False)}")
                except Exception as e:
                    logger.error(f"❌ 共享DID API调用失败: {e}")

    def show_agent_summary(self):
        """显示Agent摘要信息"""
        logger.info("\n📊 Agent系统摘要:")
        logger.info(f"总Agent数量: {len(self.agents)}")
        
        for i, agent in enumerate(self.agents, 1):
            logger.info(f"  {i}. {agent.name}")
            logger.info(f"     DID: {agent.anp_user_id}")
            logger.info(f"     模式: {'共享DID' if agent.shared else '独占DID'}")
            if agent.prefix:
                logger.info(f"     前缀: {agent.prefix}")
            logger.info(f"     API数量: {len(agent.api_routes)}")
            logger.info(f"     消息处理器数量: {len(agent.message_handlers)}")

    async def run(self):
        """主运行方法"""
        try:
            logger.info("🚀 启动 ANP Demo (使用新Agent系统)...")
            
            # 初始化Agent
            await self.initialize_agents()
            
            if not self.agents:
                logger.error("没有可用的Agent，退出程序")
                return
            
            # 显示Agent摘要
            self.show_agent_summary()
            
            # 启动服务器
            self.start_server()
            
            # 运行演示测试
            if not self.args.no_test:
                await self.run_demo_tests()
            
            # 保持运行
            if self.args.keep_running:
                logger.info("\n🔥 服务器运行中，按 Ctrl+C 停止...")
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("收到停止信号")
            else:
                logger.info("\n✅ 演示完成")
                
        except Exception as e:
            logger.error(f"程序运行错误: {e}")
            traceback.print_exc()
        finally:
            self.cleanup()

    def cleanup(self):
        """清理资源"""
        logger.info("🛑 清理资源...")
        try:
            if self.server and hasattr(self.server, "stop_server"):
                self.server.stop_server()
            logger.info("✅ 资源清理完成")
        except Exception as e:
            logger.error(f"清理资源时出错: {e}")


def main():
    try:
        logger.info("解析命令行参数...")
        parser = argparse.ArgumentParser(description='ANP SDK 综合演示程序 (新Agent系统)')
        parser.add_argument('--no-test', action='store_true', help='跳过演示测试')
        parser.add_argument('--keep-running', action='store_true', help='保持服务器运行')
        parser.add_argument('--domain', default='localhost', help='指定测试域名')

        args = parser.parse_args()
        
        logger.info(f"运行参数: 跳过测试={args.no_test}, 保持运行={args.keep_running}")

        demo_app = ANPDemoApplication(args)
        asyncio.run(demo_app.run())

    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
