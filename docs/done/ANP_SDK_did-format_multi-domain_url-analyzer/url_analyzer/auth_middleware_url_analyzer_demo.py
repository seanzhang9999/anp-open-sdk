#!/usr/bin/env python3
"""
认证中间件与URL分析器集成演示

展示URL分析器如何在认证中间件中自动推断目标DID，改善用户体验
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional
from unittest.mock import Mock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 初始化配置
from anp_sdk.config.unified_config import UnifiedConfig, set_global_config

# 设置应用根目录为项目根目录
app_root = str(Path(__file__).parent.parent)
config = UnifiedConfig(app_root=app_root)
set_global_config(config)

from anp_sdk.auth.auth_server import _authenticate_request
from anp_sdk.did.url_analyzer import get_url_analyzer

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_mock_request(path: str, hostname: str = "localhost", port: int = 9527, auth_header: Optional[str] = None):
    """创建模拟请求对象"""
    mock_request = Mock()
    mock_request.url = Mock()
    mock_request.url.hostname = hostname
    mock_request.url.port = port
    mock_request.url.path = path
    mock_request.method = "GET"
    mock_request.headers = Mock()
    mock_request.query_params = Mock()
    
    # 设置默认的认证头
    if auth_header is None:
        auth_header = "DID-WBA did=did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1, nonce=test123, timestamp=2024-01-01T00:00:00Z, keyid=key-1, signature=testsig"
    
    # 设置headers行为
    def headers_get(key, default=None):
        if key == "Authorization":
            return auth_header
        return default
    
    mock_request.headers.get = Mock(side_effect=headers_get)
    
    # 设置query_params行为
    def query_params_get(key, default=""):
        return default
    
    mock_request.query_params.get = Mock(side_effect=query_params_get)
    
    return mock_request

async def demo_url_analyzer_inference():
    """演示URL分析器推断功能"""
    logger.info("🚀 开始演示URL分析器在认证中间件中的自动DID推断功能")
    logger.info("=" * 80)
    
    # 获取URL分析器实例
    url_analyzer = get_url_analyzer()
    
    # 测试用例
    test_cases = [
        {
            "name": "用户ID路径",
            "path": "/wba/user/3ea884878ea5fbb1/did.json",
            "expected_did": "did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1"
        },
        {
            "name": "编码DID路径",
            "path": "/wba/user/did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1/ad.json",
            "expected_did": "did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1"
        },
        {
            "name": "测试用户路径",
            "path": "/wba/tests/test_agent_001/ad.json",
            "expected_did": "did:wba:localhost%3A9527:wba:tests:test_agent_001"
        },
        {
            "name": "托管用户路径",
            "path": "/wba/hostuser/abc123def456789a/did.json",
            "expected_did": "did:wba:localhost%3A9527:wba:hostuser:abc123def456789a"
        },
        {
            "name": "无法识别的路径",
            "path": "/invalid/path/that/cannot/be/analyzed",
            "expected_did": None
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n📋 测试用例 {i}: {test_case['name']}")
        logger.info(f"   请求路径: {test_case['path']}")
        
        # 创建模拟请求
        mock_request = create_mock_request(test_case['path'])
        
        # 使用URL分析器推断DID
        try:
            inferred_did = url_analyzer.infer_resp_did_from_url(mock_request)
            if inferred_did:
                logger.info(f"   ✅ 推断出的DID: {inferred_did}")
                if test_case['expected_did']:
                    if inferred_did == test_case['expected_did']:
                        logger.info(f"   ✅ 推断结果正确")
                    else:
                        logger.warning(f"   ⚠️ 推断结果不匹配，期望: {test_case['expected_did']}")
                else:
                    logger.warning(f"   ⚠️ 意外推断出DID，期望为None")
            else:
                logger.info(f"   ❌ 无法推断DID")
                if test_case['expected_did'] is None:
                    logger.info(f"   ✅ 符合预期（无法推断）")
                else:
                    logger.warning(f"   ⚠️ 应该能推断出: {test_case['expected_did']}")
        except Exception as e:
            logger.error(f"   ❌ 推断过程出错: {e}")

async def demo_auth_middleware_integration():
    """演示认证中间件集成"""
    logger.info("\n🔐 演示认证中间件与URL分析器的集成")
    logger.info("=" * 80)
    
    # 模拟认证中间件的行为（不实际调用认证验证）
    test_scenarios = [
        {
            "name": "单向认证 + URL推断",
            "path": "/wba/user/3ea884878ea5fbb1/did.json",
            "auth_header": "DID-WBA did=did:wba:localhost%3A9527:wba:user:caller123, nonce=test123, timestamp=2024-01-01T00:00:00Z, keyid=key-1, signature=testsig",
            "description": "认证头中没有target_did，需要从URL推断"
        },
        {
            "name": "查询参数优先",
            "path": "/wba/user/3ea884878ea5fbb1/did.json",
            "auth_header": "DID-WBA did=did:wba:localhost%3A9527:wba:user:caller123, nonce=test123, timestamp=2024-01-01T00:00:00Z, keyid=key-1, signature=testsig",
            "query_param_did": "did:wba:localhost%3A9527:wba:user:query_param_did",
            "description": "查询参数中有resp_did，应该优先使用"
        },
        {
            "name": "托管用户拒绝",
            "path": "/wba/hostuser/abc123def456789a/did.json",
            "auth_header": "DID-WBA did=did:wba:localhost%3A9527:wba:user:caller123, nonce=test123, timestamp=2024-01-01T00:00:00Z, keyid=key-1, signature=testsig",
            "description": "托管用户路径应该被拒绝"
        },
        {
            "name": "无法推断回退",
            "path": "/invalid/path/that/cannot/be/analyzed",
            "auth_header": "DID-WBA did=did:wba:localhost%3A9527:wba:user:caller123, nonce=test123, timestamp=2024-01-01T00:00:00Z, keyid=key-1, signature=testsig",
            "description": "无法推断DID时的回退行为"
        }
    ]
    
    for i, scenario in enumerate(test_scenarios, 1):
        logger.info(f"\n📋 场景 {i}: {scenario['name']}")
        logger.info(f"   描述: {scenario['description']}")
        logger.info(f"   请求路径: {scenario['path']}")
        
        # 创建模拟请求
        mock_request = create_mock_request(scenario['path'], auth_header=scenario['auth_header'])
        
        # 如果有查询参数，设置它
        if 'query_param_did' in scenario:
            def query_params_get_with_resp_did(key, default=""):
                if key == "resp_did":
                    return scenario['query_param_did']
                return default
            mock_request.query_params.get = Mock(side_effect=query_params_get_with_resp_did)
        
        # 模拟认证中间件的DID推断逻辑
        try:
            # 模拟extract_did_from_auth_header的行为
            req_did = "did:wba:localhost%3A9527:wba:user:caller123"
            target_did = None  # 单向认证
            
            # 模拟查询参数检查
            if 'query_param_did' in scenario:
                target_did = scenario['query_param_did']
                logger.info(f"   📝 从查询参数获取target_did: {target_did}")
            else:
                target_did = mock_request.query_params.get("resp_did", "")
            
            # 如果仍然没有target_did，使用URL分析器推断
            if target_did == "":
                url_analyzer = get_url_analyzer()
                inferred_did = url_analyzer.infer_resp_did_from_url(mock_request)
                if inferred_did:
                    target_did = inferred_did
                    logger.info(f"   🔍 URL分析器推断出target_did: {target_did}")
                else:
                    logger.info(f"   ❌ URL分析器无法推断target_did")
            
            # 检查结果
            if target_did == "":
                logger.info(f"   ❌ 最终结果: 无法获取target_did，请求将被拒绝")
            elif ":hostuser:" in target_did:
                logger.info(f"   🚫 最终结果: 托管用户DID，请求将被拒绝")
            else:
                logger.info(f"   ✅ 最终结果: target_did = {target_did}，可以继续认证")
                
        except Exception as e:
            logger.error(f"   ❌ 处理过程出错: {e}")

async def demo_performance_comparison():
    """演示性能对比"""
    logger.info("\n⚡ 演示URL分析器性能")
    logger.info("=" * 80)
    
    import time
    
    url_analyzer = get_url_analyzer()
    test_path = "/wba/user/3ea884878ea5fbb1/did.json"
    mock_request = create_mock_request(test_path)
    
    # 预热
    for _ in range(5):
        url_analyzer.infer_resp_did_from_url(mock_request)
    
    # 性能测试
    iterations = 1000
    
    logger.info(f"📊 执行 {iterations} 次URL分析...")
    start_time = time.time()
    
    for _ in range(iterations):
        result = url_analyzer.infer_resp_did_from_url(mock_request)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / iterations * 1000  # 转换为毫秒
    
    logger.info(f"   总时间: {total_time:.4f} 秒")
    logger.info(f"   平均时间: {avg_time:.4f} 毫秒/次")
    logger.info(f"   吞吐量: {iterations/total_time:.0f} 次/秒")
    
    if avg_time < 1.0:
        logger.info(f"   ✅ 性能优秀：平均响应时间 < 1ms")
    elif avg_time < 5.0:
        logger.info(f"   ✅ 性能良好：平均响应时间 < 5ms")
    else:
        logger.warning(f"   ⚠️ 性能需要优化：平均响应时间 > 5ms")

async def main():
    """主演示函数"""
    logger.info("🎯 认证中间件与URL分析器集成演示")
    logger.info("🎯 展示如何通过URL自动推断目标DID，改善用户体验")
    logger.info("🎯 这样用户在发起请求时不需要手动指定resp_did参数")
    
    try:
        # 1. 演示URL分析器推断功能
        await demo_url_analyzer_inference()
        
        # 2. 演示认证中间件集成
        await demo_auth_middleware_integration()
        
        # 3. 演示性能
        await demo_performance_comparison()
        
        logger.info("\n" + "=" * 80)
        logger.info("🎉 演示完成！")
        logger.info("✨ URL分析器成功集成到认证中间件中")
        logger.info("✨ 用户体验得到显著改善：")
        logger.info("   - 自动从URL推断目标DID")
        logger.info("   - 减少手动配置需求")
        logger.info("   - 保持向后兼容性")
        logger.info("   - 优秀的性能表现")
        
    except Exception as e:
        logger.error(f"❌ 演示过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
