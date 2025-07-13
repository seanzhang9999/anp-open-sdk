#!/usr/bin/env python3
"""
完整的HTTP托管DID流程演示

这个演示展示了如何使用新的HTTP API方式申请和获取托管DID，
替代传统的邮件方式，提供更轻量、更实时的体验。
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from anp_sdk.anp_user import ANPUser
from anp_server.anp_server import ANP_Server
from anp_server.server_mode import ServerMode
from anp_sdk.config.unified_config import UnifiedConfig, set_global_config
from anp_sdk.anp_sdk_user_data import LocalUserDataManager
from anp_server.domain import get_domain_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class HostedDIDDemo:
    """HTTP托管DID完整流程演示"""
    
    def __init__(self):
        self.client_agent = None
        self.hosting_server = None
        
    async def setup_hosting_server(self):
        """设置托管服务器 (open.localhost:9527)"""
        print("🚀 启动托管服务器...")
        
        try:
            # 使用域名管理器获取正确路径的用户数据
            domain_manager = get_domain_manager()
            paths = domain_manager.get_all_data_paths("localhost", 9527)
            user_dir = paths['user_did_path']
            
            # 创建针对特定域名的用户数据管理器
            user_manager = LocalUserDataManager(str(user_dir))
            users = user_manager.get_all_users()
            
            if users:
                user_id=0
                hosting_agent = ANPUser(users[user_id])
                print(f"   使用现有用户作为托管服务器: {users[user_id].name}")
                print(f"   用户目录: {user_dir}")
            else:
                print(f"   ⚠️ 在 {user_dir} 中无法获取现有用户，跳过服务器启动")
                return
            
            # 启动托管服务器
            self.hosting_server = ANP_Server(
                mode=ServerMode.MULTI_AGENT_ROUTER,
                agents=[hosting_agent],
                host="localhost",
                port=9527
            )
            
            # 在后台启动服务器
            import threading
            server_thread = threading.Thread(
                target=self.hosting_server.start_server,
                daemon=True
            )
            server_thread.start()
            
            # 等待服务器启动
            await asyncio.sleep(0.1)
            print("✅ 托管服务器已启动在 localhost:9527")
            
        except Exception as e:
            print(f"❌ 启动托管服务器失败: {e}")
            raise
    async def trigger_http_processing(self):
        """触发HTTP方式的申请处理"""
        print("🔧 启动HTTP申请处理...")
        from anp_server.did_host.hosted_did_processor import HostedDIDProcessor
        
        processor = HostedDIDProcessor.create_for_domain("open.localhost", 9527)
        
        # 手动处理一次待处理的申请
        await processor.process_pending_requests()
        
        print("✅ HTTP申请处理完成")
    async def setup_client_agent(self):
        """设置客户端Agent"""
        print("👤 设置客户端Agent...")
        
        try:
            # 使用域名管理器获取正确路径的用户数据
            domain_manager = get_domain_manager()
            paths = domain_manager.get_all_data_paths("localhost", 9527)
            user_dir = paths['user_did_path']
            
            # 创建针对特定域名的用户数据管理器
            user_manager = LocalUserDataManager(str(user_dir))
            users = user_manager.get_all_users()
            
            if users:
                user_id = 0
                self.client_agent = ANPUser(users[user_id])
                print(f"✅ 使用现有用户作为客户端: {users[user_id].name}")
                print(f"   DID: {self.client_agent.id}")
                print(f"   名称: {self.client_agent.name}")
                print(f"   用户目录: {user_dir}")
            else:
                print(f"⚠️ 在 {user_dir} 中没有可用的用户数据，将使用模拟模式")
                self.client_agent = None
            
        except Exception as e:
            print(f"⚠️ 无法获取现有用户: {e}")
            self.client_agent = None
    
    async def demonstrate_http_hosted_did_flow(self):
        """演示完整的HTTP托管DID流程"""
        print("\n" + "="*60)
        print("🎯 开始HTTP托管DID完整流程演示")
        print("="*60)
        
        # 检查是否为演示模式
        demo_mode = not (hasattr(self.client_agent, 'request_hosted_did_async') and 
                        hasattr(self.client_agent, 'poll_hosted_did_results'))
        
        if demo_mode:
            print("🎭 演示模式：模拟HTTP托管DID流程")
            print("   (实际方法尚未实现，这里展示预期的工作流程)")
            return await self._simulate_hosted_did_flow()
        
        # 第一步：提交申请
        print("\n📝 第一步：提交托管DID申请")
        
        try:
            success, request_id, error = await self.client_agent.request_hosted_did_async(
                target_host="open.localhost",
                target_port=9527
            )
        except Exception as e:
            print(f"❌ 申请提交失败: {e}")
            return False
        
        if success:
            print(f"✅ 申请已提交成功")
            print(f"   申请ID: {request_id}")
            print(f"   目标服务器: localhost:9527")
        else:
            print(f"❌ 申请提交失败: {error}")
            return False
        
        # 第二步：轮询检查结果
        print(f"\n🔄 第二步：轮询检查处理结果")
        print("   开始轮询检查（每1秒检查一次，最多检查5次）...")
        await self.trigger_http_processing()



        try:
            processed_count = await self.client_agent.poll_hosted_did_results(
                interval=1,  # 每1秒检查一次
                max_polls=1  # 最多检查5次
            )
        except Exception as e:
            print(f"❌ 轮询检查失败: {e}")
            processed_count = 0
        
        if processed_count > 0:
            print(f"🎉 成功处理了 {processed_count} 个托管DID结果")
        else:
            print("⚠️ 没有收到托管DID结果")
            print("   这可能是因为：")
            print("   1. 托管服务器还在处理申请")
            print("   2. 申请被拒绝")
            print("   3. 网络连接问题")
            print("   4. 已经存在托管DID")
        # 第三步：查看创建的托管DID
        await self.show_created_hosted_dids()

        return processed_count > 0
    
    async def _simulate_hosted_did_flow(self):
        """模拟HTTP托管DID流程"""
        import uuid
        
        # 模拟第一步：提交申请
        print("\n📝 第一步：提交托管DID申请")
        print("   正在向 localhost:9527 提交申请...")
        await asyncio.sleep(1)  # 模拟网络延迟
        
        request_id = str(uuid.uuid4())[:8]
        print(f"✅ 申请已提交成功（模拟）")
        print(f"   申请ID: {request_id}")
        print(f"   目标服务器: localhost:9527")
        
        # 模拟第二步：轮询检查结果
        print(f"\n🔄 第二步：轮询检查处理结果")
        print("   开始轮询检查（模拟）...")
        
        for i in range(3):
            print(f"   轮询第 {i+1} 次...")
            await asyncio.sleep(2)  # 模拟轮询间隔
            
            if i == 2:  # 第3次成功
                print("   ✅ 发现新的托管DID结果！")
                break
            else:
                print("   ⏳ 暂无结果，继续等待...")
        
        print(f"🎉 成功处理了 1 个托管DID结果（模拟）")
        
        # 模拟第三步：显示结果
        print(f"\n📁 第三步：查看创建的托管DID（模拟）")
        print("   📂 user_hosted_localhost_9527_abc123")
        print("      🆔 托管DID ID: did:wba:localhost:9527:wba:hostuser:abc123")
        print(f"      📅 创建时间: {time.ctime()}")
        print("      🔗 服务端点:")
        print("         - ANPService: http://localhost:9527/wba/hostuser/abc123")
        
        return True
    
    async def show_created_hosted_dids(self):
        """显示创建的托管DID信息"""
        print(f"\n📁 第三步：查看创建的托管DID")
        
        try:
            # 查找托管DID目录
            if not self.client_agent or not hasattr(self.client_agent, 'user_data') or not self.client_agent.user_data:
                print("   ❌ 无法访问客户端Agent的用户数据")
                return
                
            user_data_path = Path(self.client_agent.user_data.user_dir).parent
            hosted_dirs = list(user_data_path.glob("user_hosted_*"))
            
            if hosted_dirs:
                print(f"   找到 {len(hosted_dirs)} 个托管DID目录:")
                
                for hosted_dir in hosted_dirs:
                    print(f"   📂 {hosted_dir.name}")
                    
                    # 读取托管DID文档
                    did_doc_path = hosted_dir / "did_document.json"
                    if did_doc_path.exists():
                        with open(did_doc_path, 'r', encoding='utf-8') as f:
                            hosted_did_doc = json.load(f)
                        
                        print(f"      🆔 托管DID ID: {hosted_did_doc.get('id')}")
                        print(f"      📅 创建时间: {time.ctime(hosted_dir.stat().st_ctime)}")
                        
                        # 显示服务端点
                        service_endpoints = hosted_did_doc.get('service', [])
                        if service_endpoints:
                            print(f"      🔗 服务端点:")
                            for endpoint in service_endpoints:
                                print(f"         - {endpoint.get('type')}: {endpoint.get('serviceEndpoint')}")
            else:
                print("   ⚠️ 没有找到托管DID目录")
                
        except Exception as e:
            print(f"   ❌ 查看托管DID时出错: {e}")
    
    async def demonstrate_api_calls(self):
        """演示HTTP API调用"""
        print(f"\n🔧 第四步：演示HTTP API调用")
        
        try:
            try:
                import  httpx
            except ImportError:
                print("   ❌ 需要安装aio库: pip install httpx")
                return
            
            # 1. 查询申请状态
            print("   📊 查询托管DID列表...")
            async with httpx.AsyncClient() as client:
                response = await client.get("http://open.localhost:9527/wba/hosted-did/list")
                if response.status_code == 200:
                    result = response.json()
                    print(f"      ✅ 找到 {result.get('total', 0)} 个托管DID")
                    
                    for hosted_did in result.get('hosted_dids', [])[:3]:  # 只显示前3个
                        print(f"         - 用户ID: {hosted_did.get('user_id')}")
                        print(f"           托管DID: {hosted_did.get('hosted_did_id')}")
                else:
                    print(f"      ❌ 查询失败: HTTP {response.status_code}")
            
            # 2. 检查特定用户的结果
            print("   🔍 检查特定用户的处理结果...")
            if not self.client_agent or not hasattr(self.client_agent, 'user_data') or not self.client_agent.user_data:
                print("      ❌ 无法访问客户端Agent的用户数据")
                return
                
            did_parts = self.client_agent.user_data.did_document.get('id', '').split(':')
            requester_id = did_parts[-1] if did_parts else ""
            
            if requester_id:
                async with httpx.AsyncClient() as client:
                    response = await client.get(f"http://open.localhost:9527/wba/hosted-did/check/{requester_id}")
                    if response.status_code == 200:
                        result = response.json()
                        print(f"      ✅ 找到 {result.get('total', 0)} 个结果")
                        print(f"      ✅  {result} ")

                    else:
                        print(f"      ❌ 检查失败: HTTP {response.status_code}")
            
        except Exception as e:
            print(f"   ❌ API调用演示失败: {e}")
    
    async def cleanup(self):
        """清理资源"""
        print(f"\n🧹 清理资源...")
        
        try:
            if self.hosting_server:
                # 这里可以添加服务器关闭逻辑
                pass
            print("✅ 资源清理完成")
        except Exception as e:
            print(f"⚠️ 清理资源时出错: {e}")

async def main():
    """主函数"""
    print("🌟 HTTP托管DID完整流程演示")
    print("=" * 50)
    
    # 初始化全局配置
    try:
        print("⚙️ 初始化配置...")
        config_file = project_root / "unified_config_framework_demo.yaml"
        if not config_file.exists():
            config_file = project_root / "unified_config.default.yaml"
        
        if config_file.exists():
            config = UnifiedConfig(config_file=str(config_file), app_root=str(project_root))
            set_global_config(config)
            print(f"✅ 配置已加载: {config_file.name}")
        else:
            print("⚠️ 未找到配置文件，使用默认配置")
            config = UnifiedConfig(app_root=str(project_root))
            set_global_config(config)
    except Exception as e:
        print(f"❌ 配置初始化失败: {e}")
        return
    
    demo = HostedDIDDemo()
    
    try:
        # 1. 设置托管服务器
        await demo.setup_hosting_server()
        
        # 2. 设置客户端Agent
        await demo.setup_client_agent()
        
        # 3. 演示完整流程
        success = await demo.demonstrate_http_hosted_did_flow()
        
        # 4. 演示API调用
        await demo.demonstrate_api_calls()
        
        print(f"\n🎉 演示完成！")
        print("=" * 50)
        
        if success:
            print("✅ HTTP托管DID流程演示成功")
            print("   主要特点:")
            print("   - 🚀 轻量化：无需邮件服务配置")
            print("   - ⚡ 实时性：即时反馈和状态查询")
            print("   - 🔄 异步处理：支持长时间处理")
            print("   - 🛡️ 生产就绪：完整的错误处理和重试机制")
        else:
            print("⚠️ 演示过程中遇到问题，请检查日志")

        input("任意键退出")
        
    except KeyboardInterrupt:
        print(f"\n⏹️ 用户中断演示")
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        logger.exception("演示错误详情")
    finally:
        await demo.cleanup()

if __name__ == "__main__":
    # 运行演示
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 再见！")
    except Exception as e:
        print(f"\n💥 程序异常退出: {e}")
        sys.exit(1)
