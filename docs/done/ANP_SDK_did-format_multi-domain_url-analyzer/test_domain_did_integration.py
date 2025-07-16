#!/usr/bin/env python3
"""
域名管理和DID格式管理集成测试

测试新的多域名支持和DID格式管理功能
"""

import sys
import asyncio
import logging
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 初始化配置
from anp_sdk.config.unified_config import UnifiedConfig, set_global_config

# 设置应用根目录为项目根目录
app_root = str(Path(__file__).parent.parent)
config = UnifiedConfig(app_root=app_root)
set_global_config(config)

from anp_sdk.domain import get_domain_manager
from anp_sdk.did import get_did_format_manager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_domain_manager():
    """测试域名管理器功能"""
    logger.info("=== 测试域名管理器 ===")
    
    domain_manager = get_domain_manager()
    
    # 测试支持的域名
    supported_domains = domain_manager.supported_domains
    logger.info(f"✅ 支持的域名: {supported_domains}")
    
    # 测试Host头解析
    test_hosts = [
        "user.localhost:9527",
        "service.localhost:9527", 
        "localhost:9527",
        "[::1]:9527",
        "api.localhost"
    ]
    
    for host_header in test_hosts:
        host, port = domain_manager.parse_host_header(host_header)
        logger.info(f"✅ 解析 '{host_header}' -> {host}:{port}")
    
    # 测试域名验证
    test_domains = [
        ("user.localhost", 9527),
        ("service.localhost", 9527),
        ("unknown.localhost", 9527),
        ("localhost", 8080)
    ]
    
    for domain, port in test_domains:
        is_supported = domain_manager.is_supported_domain(domain, port)
        valid, error = domain_manager.validate_domain_access(domain, port)
        logger.info(f"✅ 域名 {domain}:{port} - 支持: {is_supported}, 有效: {valid}")
        if not valid:
            logger.info(f"   错误: {error}")
    
    # 测试数据路径
    for domain, port in [("user.localhost", 9527), ("service.localhost", 9527)]:
        paths = domain_manager.get_all_data_paths(domain, port)
        logger.info(f"✅ {domain}:{port} 数据路径:")
        for path_name, path in paths.items():
            logger.info(f"   {path_name}: {path}")
    
    # 测试统计信息
    stats = domain_manager.get_domain_stats()
    logger.info(f"✅ 域名统计: {stats}")
    
    return True

def test_did_format_manager():
    """测试DID格式管理器功能"""
    logger.info("=== 测试DID格式管理器 ===")
    
    did_manager = get_did_format_manager()
    
    # 测试DID格式化
    test_cases = [
        ("user.localhost", 9527, "user", "abc123"),
        ("service.localhost", 9527, "user", "def456"),
        ("localhost", 9527, "tests", "test123")
    ]
    
    formatted_dids = []
    for host, port, user_type, user_id in test_cases:
        did = did_manager.format_did(host, port, user_type, user_id)
        formatted_dids.append(did)
        logger.info(f"✅ 格式化DID: {host}:{port}/{user_type}/{user_id} -> {did}")
    
    # 测试DID解析
    for did in formatted_dids:
        parsed = did_manager.parse_did(did)
        if parsed:
            logger.info(f"✅ 解析DID: {did}")
            for key, value in parsed.items():
                logger.info(f"   {key}: {value}")
        else:
            logger.error(f"❌ 解析DID失败: {did}")
    
    # 测试DID标准化
    legacy_dids = [
        "did:wba:localhost:9527:wba:user:abc123",  # 无编码版本
        "did:wba:user.localhost%3A9527:wba:user:def456"  # 已编码版本
    ]
    
    for legacy_did in legacy_dids:
        normalized = did_manager.normalize_did(legacy_did)
        logger.info(f"✅ 标准化DID: {legacy_did} -> {normalized}")
    
    # 测试DID验证
    for did in formatted_dids:
        valid, error = did_manager.validate_did_format(did)
        logger.info(f"✅ 验证DID: {did} - 有效: {valid}")
        if not valid:
            logger.info(f"   错误: {error}")
    
    # 测试用户类型
    supported_types = did_manager.get_supported_user_types()
    creatable_types = did_manager.get_creatable_user_types()
    logger.info(f"✅ 支持的用户类型: {supported_types}")
    logger.info(f"✅ 可创建的用户类型: {creatable_types}")
    
    # 测试统计信息
    stats = did_manager.get_did_stats()
    logger.info(f"✅ DID统计: {stats}")
    
    return True

def test_agent_identity_creation():
    """测试Agent身份创建"""
    logger.info("=== 测试Agent身份创建 ===")
    
    did_manager = get_did_format_manager()
    
    # 测试创建不同域名的Agent身份
    test_agents = [
        {
            "name": "用户服务助手",
            "description": "处理用户相关请求的智能助手",
            "host": "user.localhost",
            "port": 9527
        },
        {
            "name": "服务管理助手", 
            "description": "管理各种服务的智能助手",
            "host": "service.localhost",
            "port": 9527
        },
        {
            "name": "API网关助手",
            "description": "API请求处理助手",
            "host": "localhost",
            "port": 9527
        }
    ]
    
    created_identities = []
    for agent_info in test_agents:
        try:
            identity = did_manager.create_agent_identity(**agent_info)
            created_identities.append(identity)
            logger.info(f"✅ 创建Agent身份成功:")
            for key, value in identity.items():
                logger.info(f"   {key}: {value}")
            logger.info("")
        except Exception as e:
            logger.error(f"❌ 创建Agent身份失败: {e}")
    
    # 验证创建的身份
    for identity in created_identities:
        valid, error = did_manager.validate_agent_identity(identity)
        logger.info(f"✅ 验证身份 {identity['name']}: {valid}")
        if not valid:
            logger.info(f"   错误: {error}")
    
    return len(created_identities) == len(test_agents)

def test_data_path_management():
    """测试数据路径管理"""
    logger.info("=== 测试数据路径管理 ===")
    
    domain_manager = get_domain_manager()
    
    # 测试不同域名的数据路径
    test_domains = [
        ("user.localhost", 9527),
        ("service.localhost", 9527),
        ("localhost", 9527)
    ]
    
    for domain, port in test_domains:
        logger.info(f"✅ 测试域名: {domain}:{port}")
        
        # 获取数据路径
        paths = domain_manager.get_all_data_paths(domain, port)
        for path_name, path in paths.items():
            logger.info(f"   {path_name}: {path}")
        
        # 确保目录存在
        success = domain_manager.ensure_domain_directories(domain, port)
        logger.info(f"   目录创建: {'成功' if success else '失败'}")
        
        # 检查目录是否真的存在
        for path_name, path in paths.items():
            if path_name != 'base_path':
                exists = path.exists()
                logger.info(f"   {path_name} 存在: {exists}")
    
    return True

def test_integration():
    """集成测试"""
    logger.info("=== 集成测试 ===")
    
    domain_manager = get_domain_manager()
    did_manager = get_did_format_manager()
    
    # 模拟HTTP请求
    class MockRequest:
        def __init__(self, host_header):
            self.headers = {"Host": host_header}
    
    test_requests = [
        MockRequest("user.localhost:9527"),
        MockRequest("service.localhost:9527"),
        MockRequest("localhost:9527")
    ]
    
    for request in test_requests:
        # 从请求中提取主机端口
        host, port = did_manager.get_host_port_from_request(request)
        logger.info(f"✅ 请求 {request.headers['Host']} -> {host}:{port}")
        
        # 获取数据路径
        paths = did_manager.get_data_paths(host, port)
        logger.info(f"   数据路径: {paths['base_path']}")
        
        # 创建测试身份
        try:
            identity = did_manager.create_agent_identity(
                name=f"测试助手-{host}",
                description=f"在{host}上运行的测试助手",
                host=host,
                port=port
            )
            logger.info(f"   创建身份: {identity['did']}")
        except Exception as e:
            logger.error(f"   创建身份失败: {e}")
    
    return True

async def run_all_tests():
    """运行所有测试"""
    logger.info("🚀 开始域名管理和DID格式管理集成测试")
    logger.info("=" * 60)
    
    tests = [
        ("域名管理器", test_domain_manager),
        ("DID格式管理器", test_did_format_manager),
        ("Agent身份创建", test_agent_identity_creation),
        ("数据路径管理", test_data_path_management),
        ("集成测试", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
            logger.info(f"✅ {test_name}: {'通过' if result else '失败'}")
        except Exception as e:
            logger.error(f"❌ {test_name}: 异常 - {e}")
            results.append((test_name, False))
    
    logger.info("\n" + "=" * 60)
    logger.info("📊 测试结果汇总:")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        logger.info("🎉 所有测试通过！多域名和DID格式管理功能正常工作")
        return True
    else:
        logger.error("❌ 部分测试失败，请检查相关功能")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
