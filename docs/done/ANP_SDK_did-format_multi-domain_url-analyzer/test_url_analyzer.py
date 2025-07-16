#!/usr/bin/env python3
"""
URL分析器测试

测试URL模式匹配和DID推断功能
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 初始化配置
from anp_sdk.config.unified_config import UnifiedConfig, set_global_config

# 设置应用根目录为项目根目录
app_root = str(Path(__file__).parent.parent)
config = UnifiedConfig(app_root=app_root)
set_global_config(config)

from anp_sdk.did.url_analyzer import UrlAnalyzer, get_url_analyzer

class TestUrlAnalyzer(unittest.TestCase):
    """URL分析器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.analyzer = UrlAnalyzer()
        
        # 创建模拟请求对象
        self.mock_request = Mock()
        self.mock_request.url = Mock()
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.port = 9527
        
    def test_parse_wba_user_id_pattern(self):
        """测试解析用户ID模式"""
        path = "/wba/user/3ea884878ea5fbb1/did.json"
        result = self.analyzer.parse_url_pattern(path)
        
        self.assertIsNotNone(result)
        if result:  # 类型检查
            self.assertEqual(result['pattern_type'], 'wba_user_id')
            self.assertEqual(result['user_type'], 'user')
            self.assertEqual(result['user_info'], '3ea884878ea5fbb1')
            self.assertEqual(result['file_part'], 'did.json')
            self.assertEqual(result['info_type'], 'user_id')
    
    def test_parse_wba_user_encoded_did_pattern(self):
        """测试解析编码DID模式"""
        path = "/wba/user/did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1/ad.json"
        result = self.analyzer.parse_url_pattern(path)
        
        self.assertIsNotNone(result)
        if result:  # 类型检查
            self.assertEqual(result['pattern_type'], 'wba_user_encoded_did')
            self.assertEqual(result['user_type'], 'user')
            self.assertEqual(result['info_type'], 'encoded_did')
            self.assertTrue(result['user_info'].startswith('did%3A'))
    
    def test_parse_wba_hostuser_pattern(self):
        """测试解析托管用户模式"""
        path = "/wba/hostuser/abc123def456789a/did.json"
        result = self.analyzer.parse_url_pattern(path)
        
        self.assertIsNotNone(result)
        if result:  # 类型检查
            self.assertEqual(result['pattern_type'], 'wba_hostuser')
            self.assertEqual(result['user_type'], 'hostuser')
            self.assertEqual(result['user_info'], 'abc123def456789a')
            self.assertEqual(result['info_type'], 'user_id')
    
    def test_parse_wba_test_pattern(self):
        """测试解析测试用户模式"""
        path = "/wba/tests/test_agent_001/ad.json"
        result = self.analyzer.parse_url_pattern(path)
        
        self.assertIsNotNone(result)
        if result:  # 类型检查
            self.assertEqual(result['pattern_type'], 'wba_test')
            self.assertEqual(result['user_type'], 'tests')
            self.assertEqual(result['user_info'], 'test_agent_001')
            self.assertEqual(result['info_type'], 'test_name')
    
    def test_parse_agent_api_pattern(self):
        """测试解析Agent API模式"""
        path = "/agent/api/did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1/status"
        result = self.analyzer.parse_url_pattern(path)
        
        self.assertIsNotNone(result)
        if result:  # 类型检查
            self.assertEqual(result['pattern_type'], 'agent_api')
            self.assertEqual(result['info_type'], 'encoded_did')
            self.assertTrue(result['user_info'].startswith('did%3A'))
    
    def test_is_user_id_validation(self):
        """测试用户ID验证"""
        # 有效的16位hex
        self.assertTrue(self.analyzer._is_user_id('3ea884878ea5fbb1'))
        self.assertTrue(self.analyzer._is_user_id('0123456789abcdef'))
        
        # 无效的格式
        self.assertFalse(self.analyzer._is_user_id('3ea884878ea5fbb'))  # 15位
        self.assertFalse(self.analyzer._is_user_id('3ea884878ea5fbb12'))  # 17位
        self.assertFalse(self.analyzer._is_user_id('3ea884878ea5fbbg'))  # 包含非hex字符
        self.assertFalse(self.analyzer._is_user_id(''))  # 空字符串
        # 注意：None类型检查在_is_user_id内部处理
    
    def test_is_encoded_did_validation(self):
        """测试编码DID验证"""
        # 有效的编码DID
        self.assertTrue(self.analyzer._is_encoded_did('did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1'))
        self.assertTrue(self.analyzer._is_encoded_did('did:wba:localhost:9527:wba:user:3ea884878ea5fbb1'))
        
        # 无效的格式
        self.assertFalse(self.analyzer._is_encoded_did('3ea884878ea5fbb1'))
        self.assertFalse(self.analyzer._is_encoded_did(''))
        # 注意：None类型检查在_is_encoded_did内部处理
    
    def test_infer_did_from_user_id_path(self):
        """测试从用户ID路径推断DID"""
        self.mock_request.url.path = "/wba/user/3ea884878ea5fbb1/did.json"
        
        result = self.analyzer.infer_resp_did_from_url(self.mock_request)
        
        self.assertIsNotNone(result)
        if result:  # 类型检查
            self.assertTrue(result.startswith('did:wba:'))
            self.assertIn('3ea884878ea5fbb1', result)
            self.assertIn('localhost', result)
            self.assertIn('9527', result)
    
    def test_infer_did_from_encoded_did_path(self):
        """测试从编码DID路径推断DID"""
        encoded_did = "did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1"
        self.mock_request.url.path = f"/wba/user/{encoded_did}/ad.json"
        
        result = self.analyzer.infer_resp_did_from_url(self.mock_request)
        
        self.assertIsNotNone(result)
        self.assertEqual(result, "did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1")
    
    def test_infer_did_from_hostuser_path(self):
        """测试从托管用户路径推断DID"""
        self.mock_request.url.path = "/wba/hostuser/abc123def456789a/did.json"
        
        result = self.analyzer.infer_resp_did_from_url(self.mock_request)
        
        self.assertIsNotNone(result)
        if result:  # 类型检查
            self.assertTrue(result.startswith('did:wba:'))
            self.assertIn('hostuser', result)
            self.assertIn('abc123def456789a', result)
    
    def test_infer_did_from_test_path(self):
        """测试从测试用户路径推断DID"""
        self.mock_request.url.path = "/wba/tests/test_agent_001/ad.json"
        
        result = self.analyzer.infer_resp_did_from_url(self.mock_request)
        
        self.assertIsNotNone(result)
        if result:  # 类型检查
            self.assertTrue(result.startswith('did:wba:'))
            self.assertIn('tests', result)
            self.assertIn('test_agent_001', result)
    
    def test_multi_domain_inference(self):
        """测试多域名环境下的DID推断"""
        # 测试localhost域名的基本功能
        self.mock_request.url.hostname = "localhost"
        self.mock_request.url.port = 9527
        self.mock_request.url.path = "/wba/user/3ea884878ea5fbb1/did.json"
        
        result = self.analyzer.infer_resp_did_from_url(self.mock_request)
        
        self.assertIsNotNone(result)
        if result:
            # 检查DID是否包含正确的域名信息
            self.assertTrue(result.startswith('did:wba:'))
            self.assertIn('localhost', result)
            self.assertIn('3ea884878ea5fbb1', result)
    
    def test_invalid_url_patterns(self):
        """测试无法识别的URL模式"""
        invalid_paths = [
            "/invalid/path",
            "/wba/user/",  # 缺少用户信息
            "/wba/user/invalid_user_id/did.json",  # 无效用户ID
            "/wba/hostuser/",  # 缺少用户信息
            "",  # 空路径
        ]
        
        for path in invalid_paths:
            with self.subTest(path=path):
                self.mock_request.url.path = path
                result = self.analyzer.infer_resp_did_from_url(self.mock_request)
                self.assertIsNone(result)
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 测试请求对象没有url属性
        mock_request_no_url = Mock()
        del mock_request_no_url.url
        result = self.analyzer.infer_resp_did_from_url(mock_request_no_url)
        self.assertIsNone(result)
        
        # 测试请求对象有path属性但没有url
        mock_request_path_only = Mock()
        mock_request_path_only.path = "/wba/user/3ea884878ea5fbb1/did.json"
        del mock_request_path_only.url
        # 这种情况下应该能够处理，但可能无法获取域名信息
        result = self.analyzer.infer_resp_did_from_url(mock_request_path_only)
        # 结果取决于域名管理器的默认行为
    
    def test_pattern_caching(self):
        """测试模式缓存功能"""
        path = "/wba/user/3ea884878ea5fbb1/did.json"
        
        # 第一次解析
        result1 = self.analyzer.parse_url_pattern(path)
        self.assertIsNotNone(result1)
        
        # 第二次解析应该使用缓存
        result2 = self.analyzer.parse_url_pattern(path)
        self.assertEqual(result1, result2)
        
        # 检查缓存中是否存在
        self.assertIn(path, self.analyzer._pattern_cache)
    
    def test_extract_user_info_from_path(self):
        """测试从路径提取用户信息"""
        test_cases = [
            ("/wba/user/3ea884878ea5fbb1/did.json", "user", "3ea884878ea5fbb1"),
            ("/wba/hostuser/abc123def456789a/did.json", "hostuser", "abc123def456789a"),
            ("/wba/tests/test_agent_001/ad.json", "tests", "test_agent_001"),
            ("/invalid/path", None, None)
        ]
        
        for path, expected_type, expected_info in test_cases:
            with self.subTest(path=path):
                user_type, user_info = self.analyzer.extract_user_info_from_path(path)
                self.assertEqual(user_type, expected_type)
                self.assertEqual(user_info, expected_info)
    
    def test_get_supported_patterns(self):
        """测试获取支持的模式列表"""
        patterns = self.analyzer.get_supported_patterns()
        
        self.assertIsInstance(patterns, dict)
        self.assertIn('wba_user_id', patterns)
        self.assertIn('wba_user_encoded_did', patterns)
        self.assertIn('wba_hostuser', patterns)
        self.assertIn('wba_test', patterns)
        self.assertIn('agent_api', patterns)
    
    def test_get_analysis_stats(self):
        """测试获取分析统计信息"""
        stats = self.analyzer.get_analysis_stats()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('supported_patterns', stats)
        self.assertIn('cache_size', stats)
        self.assertIn('patterns', stats)
        self.assertIsInstance(stats['patterns'], list)
    
    def test_global_analyzer_instance(self):
        """测试全局分析器实例"""
        analyzer1 = get_url_analyzer()
        analyzer2 = get_url_analyzer()
        
        # 应该返回同一个实例
        self.assertIs(analyzer1, analyzer2)
        self.assertIsInstance(analyzer1, UrlAnalyzer)


class TestUrlAnalyzerIntegration(unittest.TestCase):
    """URL分析器集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.analyzer = get_url_analyzer()
    
    def test_real_request_simulation(self):
        """模拟真实请求测试"""
        # 模拟FastAPI Request对象
        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = "/wba/user/3ea884878ea5fbb1/did.json"
        mock_request.url.hostname = "localhost"
        mock_request.url.port = 9527
        
        result = self.analyzer.infer_resp_did_from_url(mock_request)
        
        self.assertIsNotNone(result)
        if result:  # 类型检查
            self.assertTrue(result.startswith('did:wba:'))
            
            # 验证DID格式
            from anp_sdk.did.did_format_manager import get_did_format_manager
            did_manager = get_did_format_manager()
            parsed = did_manager.parse_did(result)
            
            self.assertIsNotNone(parsed)
            if parsed:  # 类型检查
                self.assertEqual(parsed['user_id'], '3ea884878ea5fbb1')
                self.assertEqual(parsed['user_type'], 'user')
    
    def test_performance_with_cache(self):
        """测试缓存性能"""
        import time
        
        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.hostname = "localhost"
        mock_request.url.port = 9527
        
        paths = [
            "/wba/user/3ea884878ea5fbb1/did.json",
            "/wba/user/abc123def456789a/ad.json",
            "/wba/hostuser/fedcba9876543210/did.json"
        ]
        
        # 第一次运行（建立缓存）
        start_time = time.time()
        for path in paths * 10:  # 重复10次
            mock_request.url.path = path
            self.analyzer.infer_resp_did_from_url(mock_request)
        first_run_time = time.time() - start_time
        
        # 第二次运行（使用缓存）
        start_time = time.time()
        for path in paths * 10:  # 重复10次
            mock_request.url.path = path
            self.analyzer.infer_resp_did_from_url(mock_request)
        second_run_time = time.time() - start_time
        
        # 第二次应该更快（由于缓存）
        print(f"第一次运行时间: {first_run_time:.4f}s")
        print(f"第二次运行时间: {second_run_time:.4f}s")
        
        # 验证缓存确实在工作
        self.assertGreater(len(self.analyzer._pattern_cache), 0)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
