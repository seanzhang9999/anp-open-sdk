#!/usr/bin/env python3
"""
认证中间件与URL分析器集成测试

测试URL分析器在认证中间件中的自动DID推断功能
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 初始化配置
from anp_open_sdk.config.unified_config import UnifiedConfig, set_global_config

# 设置应用根目录为项目根目录
app_root = str(Path(__file__).parent.parent)
config = UnifiedConfig(app_root=app_root)
set_global_config(config)

from anp_open_sdk_framework.server.anp_server_auth_middleware import _authenticate_request

class TestAuthMiddlewareUrlAnalyzerIntegration(unittest.TestCase):
    """认证中间件与URL分析器集成测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建模拟请求对象
        self.mock_request = Mock()
        self.mock_request.url = Mock()
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.port = 9527
        self.mock_request.method = "GET"
        self.mock_request.headers = Mock()
        self.mock_request.query_params = Mock()
        
        # 设置默认的headers行为
        def headers_get(key, default=None):
            if key == "Authorization":
                return "DID-WBA did=did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1, nonce=test123, timestamp=2024-01-01T00:00:00Z, keyid=key-1, signature=testsig"
            return default
        
        self.mock_request.headers.get = Mock(side_effect=headers_get)
        
        # 设置query_params行为
        def query_params_get(key, default=""):
            return default
        
        self.mock_request.query_params.get = Mock(side_effect=query_params_get)
    
    @patch('anp_open_sdk_framework.server.anp_server_auth_middleware._verify_wba_header')
    @patch('anp_open_sdk.did.did_tool.extract_did_from_auth_header')
    async def test_url_analyzer_infers_target_did_from_user_id_path(self, mock_extract_did, mock_verify_wba):
        """测试URL分析器从用户ID路径推断目标DID"""
        # 设置模拟
        mock_extract_did.return_value = ("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1", None)
        mock_verify_wba.return_value = (True, {"access_token": "test_token"})
        
        # 设置请求路径
        self.mock_request.url.path = "/wba/user/3ea884878ea5fbb1/did.json"
        
        # 执行认证
        result = await _authenticate_request(self.mock_request)
        
        # 验证结果
        self.assertEqual(result[0], True)  # auth_passed
        self.assertEqual(result[1], "auth passed")  # message
        self.assertIsInstance(result[2], dict)  # response_auth
        
        # 验证_verify_wba_header被调用，并且context包含推断的target_did
        mock_verify_wba.assert_called_once()
        call_args = mock_verify_wba.call_args
        context = call_args[0][1]  # 第二个参数是context
        
        # 验证推断的DID
        expected_did = "did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1"
        self.assertEqual(context.target_did, expected_did)
    
    @patch('anp_open_sdk_framework.server.anp_server_auth_middleware._verify_wba_header')
    @patch('anp_open_sdk.did.did_tool.extract_did_from_auth_header')
    async def test_url_analyzer_infers_target_did_from_encoded_did_path(self, mock_extract_did, mock_verify_wba):
        """测试URL分析器从编码DID路径推断目标DID"""
        # 设置模拟
        mock_extract_did.return_value = ("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1", None)
        mock_verify_wba.return_value = (True, {"access_token": "test_token"})
        
        # 设置请求路径（编码DID）
        encoded_did = "did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1"
        self.mock_request.url.path = f"/wba/user/{encoded_did}/ad.json"
        
        # 执行认证
        result = await _authenticate_request(self.mock_request)
        
        # 验证结果
        self.assertEqual(result[0], True)
        self.assertEqual(result[1], "auth passed")
        
        # 验证推断的DID
        mock_verify_wba.assert_called_once()
        call_args = mock_verify_wba.call_args
        context = call_args[0][1]
        
        expected_did = "did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1"
        self.assertEqual(context.target_did, expected_did)
    
    @patch('anp_open_sdk_framework.server.anp_server_auth_middleware._verify_wba_header')
    @patch('anp_open_sdk.did.did_tool.extract_did_from_auth_header')
    async def test_url_analyzer_infers_target_did_from_hostuser_path(self, mock_extract_did, mock_verify_wba):
        """测试URL分析器从托管用户路径推断目标DID"""
        # 设置模拟
        mock_extract_did.return_value = ("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1", None)
        
        # 设置请求路径（托管用户）
        self.mock_request.url.path = "/wba/hostuser/abc123def456789a/did.json"
        
        # 执行认证
        result = await _authenticate_request(self.mock_request)
        
        # 验证结果 - 托管用户应该被拒绝
        self.assertEqual(result[0], "NotSupport")
        self.assertIn("hosted DID", result[1])
    
    @patch('anp_open_sdk_framework.server.anp_server_auth_middleware._verify_wba_header')
    @patch('anp_open_sdk.did.did_tool.extract_did_from_auth_header')
    async def test_url_analyzer_infers_target_did_from_test_path(self, mock_extract_did, mock_verify_wba):
        """测试URL分析器从测试路径推断目标DID"""
        # 设置模拟
        mock_extract_did.return_value = ("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1", None)
        mock_verify_wba.return_value = (True, {"access_token": "test_token"})
        
        # 设置请求路径（测试用户）
        self.mock_request.url.path = "/wba/test/test_agent_001/ad.json"
        
        # 执行认证
        result = await _authenticate_request(self.mock_request)
        
        # 验证结果
        self.assertEqual(result[0], True)
        self.assertEqual(result[1], "auth passed")
        
        # 验证推断的DID
        mock_verify_wba.assert_called_once()
        call_args = mock_verify_wba.call_args
        context = call_args[0][1]
        
        expected_did = "did:wba:localhost%3A9527:wba:test:test_agent_001"
        self.assertEqual(context.target_did, expected_did)
    
    @patch('anp_open_sdk.did.did_tool.extract_did_from_auth_header')
    async def test_url_analyzer_fallback_when_cannot_infer(self, mock_extract_did):
        """测试URL分析器无法推断时的回退行为"""
        # 设置模拟
        mock_extract_did.return_value = ("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1", None)
        
        # 设置无法识别的请求路径
        self.mock_request.url.path = "/invalid/path/that/cannot/be/analyzed"
        
        # 执行认证
        result = await _authenticate_request(self.mock_request)
        
        # 验证结果 - 应该返回NotSupport
        self.assertEqual(result[0], "NotSupport")
        self.assertIn("cannot infer from URL", result[1])
    
    @patch('anp_open_sdk_framework.server.anp_server_auth_middleware._verify_wba_header')
    @patch('anp_open_sdk.did.did_tool.extract_did_from_auth_header')
    async def test_query_param_takes_precedence_over_url_analyzer(self, mock_extract_did, mock_verify_wba):
        """测试查询参数优先于URL分析器"""
        # 设置模拟
        mock_extract_did.return_value = ("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1", None)
        mock_verify_wba.return_value = (True, {"access_token": "test_token"})
        
        # 设置查询参数中的resp_did
        def query_params_get_with_resp_did(key, default=""):
            if key == "resp_did":
                return "did:wba:localhost%3A9527:wba:user:query_param_did"
            return default
        
        self.mock_request.query_params.get = Mock(side_effect=query_params_get_with_resp_did)
        
        # 设置请求路径（这个路径本来可以推断出不同的DID）
        self.mock_request.url.path = "/wba/user/3ea884878ea5fbb1/did.json"
        
        # 执行认证
        result = await _authenticate_request(self.mock_request)
        
        # 验证结果
        self.assertEqual(result[0], True)
        
        # 验证使用的是查询参数中的DID，而不是URL推断的DID
        mock_verify_wba.assert_called_once()
        call_args = mock_verify_wba.call_args
        context = call_args[0][1]
        
        self.assertEqual(context.target_did, "did:wba:localhost%3A9527:wba:user:query_param_did")
    
    @patch('anp_open_sdk.did.url_analyzer.get_url_analyzer')
    @patch('anp_open_sdk.did.did_tool.extract_did_from_auth_header')
    async def test_url_analyzer_exception_handling(self, mock_extract_did, mock_get_analyzer):
        """测试URL分析器异常处理"""
        # 设置模拟
        mock_extract_did.return_value = ("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1", None)
        
        # 模拟URL分析器抛出异常
        mock_analyzer = Mock()
        mock_analyzer.infer_resp_did_from_url.side_effect = Exception("URL分析器错误")
        mock_get_analyzer.return_value = mock_analyzer
        
        # 设置请求路径
        self.mock_request.url.path = "/wba/user/3ea884878ea5fbb1/did.json"
        
        # 执行认证
        result = await _authenticate_request(self.mock_request)
        
        # 验证结果 - 应该优雅地处理异常并返回NotSupport
        self.assertEqual(result[0], "NotSupport")
        self.assertIn("cannot infer from URL", result[1])
    
    async def test_exempt_paths_bypass_url_analyzer(self):
        """测试豁免路径绕过URL分析器"""
        # 设置豁免路径
        self.mock_request.url.path = "/docs"
        
        # 执行认证
        result = await _authenticate_request(self.mock_request)
        
        # 验证结果 - 豁免路径应该直接通过
        self.assertEqual(result[0], True)
        self.assertEqual(result[1], "exempt url")
        self.assertEqual(result[2], {})


class TestAuthMiddlewareUrlAnalyzerPerformance(unittest.TestCase):
    """认证中间件URL分析器性能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.mock_request = Mock()
        self.mock_request.url = Mock()
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.port = 9527
        self.mock_request.method = "GET"
        self.mock_request.headers = Mock()
        self.mock_request.query_params = Mock()
        
        # 设置默认的headers行为
        def headers_get(key, default=None):
            if key == "Authorization":
                return "DID-WBA did=did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1, nonce=test123, timestamp=2024-01-01T00:00:00Z, keyid=key-1, signature=testsig"
            return default
        
        self.mock_request.headers.get = Mock(side_effect=headers_get)
        self.mock_request.query_params.get = Mock(return_value="")
    
    @patch('anp_open_sdk_framework.server.anp_server_auth_middleware._verify_wba_header')
    @patch('anp_open_sdk.did.did_tool.extract_did_from_auth_header')
    async def test_url_analyzer_caching_performance(self, mock_extract_did, mock_verify_wba):
        """测试URL分析器缓存性能"""
        import time
        
        # 设置模拟
        mock_extract_did.return_value = ("did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1", None)
        mock_verify_wba.return_value = (True, {"access_token": "test_token"})
        
        # 设置请求路径
        self.mock_request.url.path = "/wba/user/3ea884878ea5fbb1/did.json"
        
        # 第一次运行（建立缓存）
        start_time = time.time()
        for _ in range(10):
            await _authenticate_request(self.mock_request)
        first_run_time = time.time() - start_time
        
        # 第二次运行（使用缓存）
        start_time = time.time()
        for _ in range(10):
            await _authenticate_request(self.mock_request)
        second_run_time = time.time() - start_time
        
        print(f"第一次运行时间: {first_run_time:.4f}s")
        print(f"第二次运行时间: {second_run_time:.4f}s")
        
        # 验证缓存确实在工作（第二次应该不会明显更慢）
        self.assertLessEqual(second_run_time, first_run_time * 2)  # 允许一些误差


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
