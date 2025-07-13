#!/usr/bin/env python3
"""
标准端口处理测试

测试DID格式化中对标准端口（80, 443）的特殊处理
"""

import sys
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

from anp_sdk.did import get_did_format_manager

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_standard_port_formatting():
    """测试标准端口的DID格式化"""
    logger.info("=== 测试标准端口DID格式化 ===")
    
    did_mgr = get_did_format_manager()
    
    test_cases = [
        # (host, port, expected_host_part)
        ("example.com", 80, "example.com"),           # 标准HTTP端口，不编码
        ("example.com", 443, "example.com"),          # 标准HTTPS端口，不编码
        ("localhost", 80, "localhost"),                # 本地标准端口，不编码
        ("localhost", 443, "localhost"),               # 本地标准端口，不编码
        ("localhost", 9527, "localhost%3A9527"),      # 非标准端口，需要编码
        ("api.example.com", 8080, "api.example.com%3A8080"),  # 非标准端口，需要编码
        ("user.localhost", 3000, "user.localhost%3A3000"),    # 非标准端口，需要编码
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for host, port, expected_host_part in test_cases:
        try:
            # 格式化DID
            did = did_mgr.format_did(host, port, "user", "test123")
            
            # 检查是否包含预期的主机部分
            if expected_host_part in did:
                logger.info(f"✅ {host}:{port} -> {did}")
                success_count += 1
            else:
                logger.error(f"❌ {host}:{port} -> {did} (期望包含: {expected_host_part})")
                
        except Exception as e:
            logger.error(f"❌ {host}:{port} 格式化失败: {e}")
    
    logger.info(f"标准端口格式化测试: {success_count}/{total_count} 通过")
    return success_count == total_count

def test_standard_port_parsing():
    """测试标准端口的DID解析"""
    logger.info("=== 测试标准端口DID解析 ===")
    
    did_mgr = get_did_format_manager()
    
    test_cases = [
        # (did, expected_host, expected_port)
        ("did:wba:example.com:wba:user:test123", "example.com", 80),
        ("did:wba:api.example.com:wba:user:test456", "api.example.com", 80),
        ("did:wba:localhost%3A9527:wba:user:test789", "localhost", 9527),
        ("did:wba:user.localhost%3A3000:wba:user:test000", "user.localhost", 3000),
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for did, expected_host, expected_port in test_cases:
        try:
            # 解析DID
            parsed = did_mgr.parse_did(did)
            
            if parsed:
                actual_host = parsed['host']
                actual_port = int(parsed['port'])
                
                if actual_host == expected_host and actual_port == expected_port:
                    logger.info(f"✅ {did} -> {actual_host}:{actual_port}")
                    success_count += 1
                else:
                    logger.error(f"❌ {did} -> {actual_host}:{actual_port} (期望: {expected_host}:{expected_port})")
            else:
                logger.error(f"❌ {did} 解析失败")
                
        except Exception as e:
            logger.error(f"❌ {did} 解析异常: {e}")
    
    logger.info(f"标准端口解析测试: {success_count}/{total_count} 通过")
    return success_count == total_count

def test_round_trip_conversion():
    """测试往返转换（格式化->解析->格式化）"""
    logger.info("=== 测试往返转换 ===")
    
    did_mgr = get_did_format_manager()
    
    test_cases = [
        ("example.com", 80, "user", "test123"),
        ("example.com", 443, "user", "test456"),
        ("localhost", 9527, "user", "test789"),
        ("api.localhost", 8080, "user", "test000"),
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for host, port, user_type, user_id in test_cases:
        try:
            # 第一次格式化
            did1 = did_mgr.format_did(host, port, user_type, user_id)
            
            # 解析
            parsed = did_mgr.parse_did(did1)
            
            if parsed:
                # 第二次格式化
                did2 = did_mgr.format_did(
                    parsed['host'],
                    int(parsed['port']),
                    parsed['user_type'],
                    parsed['user_id']
                )
                
                if did1 == did2:
                    logger.info(f"✅ {host}:{port} 往返转换成功: {did1}")
                    success_count += 1
                else:
                    logger.error(f"❌ {host}:{port} 往返转换失败: {did1} != {did2}")
            else:
                logger.error(f"❌ {host}:{port} 解析失败")
                
        except Exception as e:
            logger.error(f"❌ {host}:{port} 往返转换异常: {e}")
    
    logger.info(f"往返转换测试: {success_count}/{total_count} 通过")
    return success_count == total_count

def test_normalize_did():
    """测试DID标准化"""
    logger.info("=== 测试DID标准化 ===")
    
    did_mgr = get_did_format_manager()
    
    test_cases = [
        # (input_did, expected_normalized)
        ("did:wba:example.com:wba:user:test123", "did:wba:example.com:wba:user:test123"),
        ("did:wba:localhost%3A9527:wba:user:test456", "did:wba:localhost%3A9527:wba:user:test456"),
    ]
    
    success_count = 0
    total_count = len(test_cases)
    
    for input_did, expected_normalized in test_cases:
        try:
            # 标准化DID
            normalized = did_mgr.normalize_did(input_did)
            
            if normalized == expected_normalized:
                logger.info(f"✅ {input_did} -> {normalized}")
                success_count += 1
            else:
                logger.error(f"❌ {input_did} -> {normalized} (期望: {expected_normalized})")
                
        except Exception as e:
            logger.error(f"❌ {input_did} 标准化异常: {e}")
    
    logger.info(f"DID标准化测试: {success_count}/{total_count} 通过")
    return success_count == total_count

def main():
    """运行所有测试"""
    logger.info("🚀 开始标准端口处理测试")
    logger.info("=" * 50)
    
    tests = [
        ("标准端口格式化", test_standard_port_formatting),
        ("标准端口解析", test_standard_port_parsing),
        ("往返转换", test_round_trip_conversion),
        ("DID标准化", test_normalize_did),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed_tests += 1
                logger.info(f"✅ {test_name}: 通过")
            else:
                logger.error(f"❌ {test_name}: 失败")
        except Exception as e:
            logger.error(f"❌ {test_name}: 异常 - {e}")
    
    logger.info("=" * 50)
    logger.info(f"📊 测试结果: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        logger.info("🎉 所有标准端口处理测试通过！")
        return True
    else:
        logger.error("❌ 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
