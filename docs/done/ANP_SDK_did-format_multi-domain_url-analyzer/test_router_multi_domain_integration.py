#!/usr/bin/env python3
"""
路由器多域名集成测试

测试 router_did.py 和 router_publisher.py 的多域名支持功能
"""

import sys
import asyncio
import json
import logging
from pathlib import Path
from unittest.mock import Mock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from anp_sdk.config.unified_config import UnifiedConfig, set_global_config
from anp_sdk.domain import get_domain_manager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TestRouterMultiDomainIntegration:
    """路由器多域名集成测试类"""
    
    def __init__(self):
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """设置测试环境"""
        # 设置应用根目录
        app_root = str(Path(__file__).parent.parent)
        
        # 创建统一配置
        config = UnifiedConfig(app_root=app_root)
        set_global_config(config)
        
        # 域名管理器会自动从配置中读取支持的域名
        # 我们只需要确保配置正确即可
        domain_manager = get_domain_manager()
        
        logger.info("✅ 测试环境设置完成")
        logger.info(f"支持的域名: {domain_manager.supported_domains}")
    
    def create_mock_request(self, host: str, port: int, path: str = "/"):
        """创建模拟请求对象"""
        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.hostname = host
        mock_request.url.port = port
        mock_request.url.scheme = "http"
        mock_request.url.netloc = f"{host}:{port}"
        mock_request.url.path = path
        
        # 正确设置headers属性
        mock_request.headers = Mock()
        mock_request.headers.get = Mock(return_value=f"{host}:{port}")
        
        return mock_request
    
    def create_test_did_document(self, user_id: str, host: str, port: int):
        """创建测试DID文档"""
        if port in [80, 443]:
            did = f"did:wba:{host}:wba:user:{user_id}"
        else:
            did = f"did:wba:{host}%3A{port}:wba:user:{user_id}"
        
        return {
            "id": did,
            "verificationMethod": [
                {
                    "id": f"{did}#key-1",
                    "type": "EcdsaSecp256k1VerificationKey2019",
                    "controller": did,
                    "publicKeyJwk": {
                        "kty": "EC",
                        "crv": "secp256k1",
                        "x": "test_x_value",
                        "y": "test_y_value"
                    }
                }
            ],
            "authentication": [f"{did}#key-1"],
            "service": []
        }
    
    async def test_router_did_multi_domain_access(self):
        """测试 router_did.py 的多域名访问功能"""
        logger.info("=== 测试 router_did.py 多域名访问 ===")
        
        from anp_server.router.router_did import get_did_document
        from anp_sdk.domain import get_domain_manager
        
        domain_manager = get_domain_manager()
        
        # 测试用例数据 - 使用配置中支持的域名
        test_cases = [
            ("localhost", 9527, "12345678"),
            ("user.localhost", 9527, "87654321"),
            ("service.localhost", 9527, "abcdef12")
        ]
        
        for host, port, user_id in test_cases:
            logger.info(f"测试域名: {host}:{port}, 用户ID: {user_id}")
            
            # 确保域名目录存在
            domain_manager.ensure_domain_directories(host, port)
            
            # 创建测试DID文档
            paths = domain_manager.get_all_data_paths(host, port)
            user_dir = paths['user_did_path'] / f"user_{user_id}"
            user_dir.mkdir(parents=True, exist_ok=True)
            
            did_doc = self.create_test_did_document(user_id, host, port)
            did_path = user_dir / "did_document.json"
            
            with open(did_path, 'w', encoding='utf-8') as f:
                json.dump(did_doc, f, indent=2, ensure_ascii=False)
            
            # 创建模拟请求
            mock_request = self.create_mock_request(host, port, f"/wba/user/{user_id}/did.json")
            
            try:
                # 调用路由函数
                result = await get_did_document(user_id, mock_request)
                
                # 验证结果
                assert result['id'] == did_doc['id'], f"DID不匹配: {result['id']} != {did_doc['id']}"
                logger.info(f"✅ {host}:{port} DID文档访问成功")
                
            except Exception as e:
                logger.error(f"❌ {host}:{port} DID文档访问失败: {e}")
                return False
        
        logger.info("✅ router_did.py 多域名访问测试通过")
        return True
    
    async def test_router_did_domain_validation(self):
        """测试 router_did.py 的域名验证功能"""
        logger.info("=== 测试 router_did.py 域名验证 ===")
        
        from anp_server.router.router_did import get_did_document
        from fastapi import HTTPException
        
        # 测试不支持的域名
        unsupported_host = "unsupported.domain"
        unsupported_port = 9999
        
        mock_request = self.create_mock_request(
            unsupported_host, 
            unsupported_port, 
            "/wba/user/test123/did.json"
        )
        
        try:
            await get_did_document("test123", mock_request)
            logger.error("❌ 应该拒绝不支持的域名访问")
            return False
        except HTTPException as e:
            if e.status_code == 403:
                logger.info(f"✅ 正确拒绝不支持的域名: {e.detail}")
                return True
            else:
                logger.error(f"❌ 错误的状态码: {e.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ 意外错误: {e}")
            return False
    
    async def test_router_publisher_multi_domain(self):
        """测试 router_publisher.py 的多域名功能"""
        logger.info("=== 测试 router_publisher.py 多域名功能 ===")
        
        from anp_server import get_agent_publishers
        from anp_server.router.router_host import get_hosted_did_document
        from anp_sdk.domain import get_domain_manager
        
        domain_manager = get_domain_manager()
        
        # 测试托管DID文档 - 使用支持的域名
        host, port = "user.localhost", 9527
        user_id = "hosted123"
        
        # 确保域名目录存在
        domain_manager.ensure_domain_directories(host, port)
        
        # 创建测试托管DID文档
        paths = domain_manager.get_all_data_paths(host, port)
        hosted_user_dir = paths['user_hosted_path'] / f"user_{user_id}"
        hosted_user_dir.mkdir(parents=True, exist_ok=True)
        
        hosted_did_doc = self.create_test_did_document(user_id, host, port)
        hosted_did_path = hosted_user_dir / "did_document.json"
        
        with open(hosted_did_path, 'w', encoding='utf-8') as f:
            json.dump(hosted_did_doc, f, indent=2, ensure_ascii=False)
        
        # 测试托管DID文档访问
        mock_request = self.create_mock_request(host, port, f"/wba/hostuser/{user_id}/did.json")
        
        try:
            result = await get_hosted_did_document(user_id, mock_request)
            assert result['id'] == hosted_did_doc['id']
            logger.info(f"✅ 托管DID文档访问成功: {host}:{port}")
        except Exception as e:
            logger.error(f"❌ 托管DID文档访问失败: {e}")
            return False
        
        # 测试代理列表功能
        mock_request_agents = self.create_mock_request(host, port, "/did_host/agents")
        
        # 模拟SDK和代理
        mock_sdk = Mock()
        mock_agent = Mock()
        mock_agent.id = "did:wba:test1.local%3A8001:wba:user:agent001"
        mock_agent.name = "Test Agent"
        mock_agent.is_hosted_did = False
        
        mock_sdk.get_agents.return_value = [mock_agent]
        mock_request_agents.app = Mock()
        mock_request_agents.app.state = Mock()
        mock_request_agents.app.state.sdk = mock_sdk
        
        try:
            result = await get_agent_publishers(mock_request_agents)
            assert result['count'] == 1
            assert result['domain'] == f"{host}:{port}"
            assert result['agents'][0]['did'] == mock_agent.id
            logger.info(f"✅ 代理列表功能测试成功: {host}:{port}")
        except Exception as e:
            logger.error(f"❌ 代理列表功能测试失败: {e}")
            return False
        
        logger.info("✅ router_publisher.py 多域名功能测试通过")
        return True
    
    async def test_url_did_format_multi_domain(self):
        """测试URL DID格式化的多域名支持"""
        logger.info("=== 测试URL DID格式化多域名支持 ===")
        
        from anp_server.router.router_did import url_did_format
        
        test_cases = [
            # (host, port, user_id, expected_did) - 使用16位用户ID
            ("localhost", 9527, "1234567890abcdef", "did:wba:localhost%3A9527:wba:user:1234567890abcdef"),
            ("user.localhost", 9527, "abcdef1234567890", "did:wba:user.localhost%3A9527:wba:user:abcdef1234567890"),
            ("service.localhost", 9527, "fedcba0987654321", "did:wba:service.localhost%3A9527:wba:user:fedcba0987654321"),
            ("localhost", 80, "1111222233334444", "did:wba:localhost:wba:user:1111222233334444"),
            ("example.com", 9527, "did:wba:example.com%3A9527:wba:user:existing", "did:wba:example.com%3A9527:wba:user:existing")
        ]
        
        for host, port, user_id, expected_did in test_cases:
            mock_request = self.create_mock_request(host, port)
            result_did = url_did_format(user_id, mock_request)
            
            if result_did == expected_did:
                logger.info(f"✅ DID格式化正确: {host}:{port} -> {result_did}")
            else:
                logger.error(f"❌ DID格式化错误: {host}:{port}")
                logger.error(f"   期望: {expected_did}")
                logger.error(f"   实际: {result_did}")
                return False
        
        logger.info("✅ URL DID格式化多域名支持测试通过")
        return True
    
    async def test_domain_data_isolation(self):
        """测试域名数据隔离"""
        logger.info("=== 测试域名数据隔离 ===")
        
        from anp_sdk.domain import get_domain_manager
        
        domain_manager = get_domain_manager()
        
        # 测试不同域名的数据路径隔离
        domains = [
            ("test1.local", 8001),
            ("test2.local", 8002),
            ("localhost", 9527)
        ]
        
        paths_by_domain = {}
        
        for host, port in domains:
            paths = domain_manager.get_all_data_paths(host, port)
            paths_by_domain[f"{host}:{port}"] = paths
            
            # 确保每个域名的路径都不同
            for other_domain, other_paths in paths_by_domain.items():
                if other_domain != f"{host}:{port}":
                    if paths['user_did_path'] == other_paths['user_did_path']:
                        logger.error(f"❌ 域名数据路径冲突: {host}:{port} 和 {other_domain}")
                        return False
        
        logger.info("✅ 域名数据隔离测试通过")
        
        # 验证路径结构
        for domain, paths in paths_by_domain.items():
            logger.info(f"域名 {domain} 的数据路径:")
            for path_type, path_value in paths.items():
                logger.info(f"  {path_type}: {path_value}")
        
        return True
    
    async def run_all_tests(self):
        """运行所有测试"""
        logger.info("🚀 开始路由器多域名集成测试")
        logger.info("=" * 60)
        
        tests = [
            ("域名数据隔离", self.test_domain_data_isolation),
            ("URL DID格式化多域名支持", self.test_url_did_format_multi_domain),
            ("router_did.py 多域名访问", self.test_router_did_multi_domain_access),
            ("router_did.py 域名验证", self.test_router_did_domain_validation),
            ("router_publisher.py 多域名功能", self.test_router_publisher_multi_domain),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\n📋 执行测试: {test_name}")
            try:
                if await test_func():
                    passed += 1
                    logger.info(f"✅ {test_name} - 通过")
                else:
                    logger.error(f"❌ {test_name} - 失败")
            except Exception as e:
                logger.error(f"❌ {test_name} - 异常: {e}")
        
        logger.info("=" * 60)
        logger.info(f"🎯 测试结果: {passed}/{total} 通过")
        
        if passed == total:
            logger.info("🎉 所有路由器多域名集成测试通过！")
            logger.info("✨ 路由器增强成功：支持多域名环境和数据隔离")
            return True
        else:
            logger.error("💥 部分测试失败，需要检查和修复")
            return False

async def main():
    """主函数"""
    test_runner = TestRouterMultiDomainIntegration()
    success = await test_runner.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
