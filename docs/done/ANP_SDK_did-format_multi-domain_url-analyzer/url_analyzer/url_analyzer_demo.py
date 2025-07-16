#!/usr/bin/env python3
"""
URL分析器演示脚本

展示URL分析器的各种功能和使用方法
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 初始化配置
from anp_sdk.config.unified_config import UnifiedConfig, set_global_config

# 设置应用根目录为项目根目录
app_root = str(Path(__file__).parent.parent)
config = UnifiedConfig(app_root=app_root)
set_global_config(config)

from anp_sdk.did.url_analyzer import get_url_analyzer

def demo_url_pattern_parsing():
    """演示URL模式解析功能"""
    print("=" * 60)
    print("URL模式解析演示")
    print("=" * 60)
    
    analyzer = get_url_analyzer()
    
    test_paths = [
        "/wba/user/3ea884878ea5fbb1/did.json",
        "/wba/user/did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1/ad.json",
        "/wba/hostuser/abc123def456789a/did.json",
        "/wba/tests/test_agent_001/ad.json",
        "/agent/api/did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1/status",
        "/invalid/path"
    ]
    
    for path in test_paths:
        print(f"\n路径: {path}")
        result = analyzer.parse_url_pattern(path)
        if result:
            print(f"  模式类型: {result['pattern_type']}")
            print(f"  用户类型: {result.get('user_type', 'N/A')}")
            print(f"  用户信息: {result.get('user_info', 'N/A')}")
            print(f"  信息类型: {result.get('info_type', 'N/A')}")
            if 'file_part' in result:
                print(f"  文件部分: {result['file_part']}")
        else:
            print("  ❌ 无法识别的模式")

def demo_did_inference():
    """演示DID推断功能"""
    print("\n" + "=" * 60)
    print("DID推断演示")
    print("=" * 60)
    
    analyzer = get_url_analyzer()
    
    # 创建模拟请求对象
    test_cases = [
        {
            "path": "/wba/user/3ea884878ea5fbb1/did.json",
            "hostname": "localhost",
            "port": 9527,
            "description": "标准用户ID访问"
        },
        {
            "path": "/wba/user/did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1/ad.json",
            "hostname": "localhost", 
            "port": 9527,
            "description": "编码DID访问"
        },
        {
            "path": "/wba/hostuser/abc123def456789a/did.json",
            "hostname": "localhost",
            "port": 9527,
            "description": "托管用户访问"
        },
        {
            "path": "/wba/tests/test_agent_001/ad.json",
            "hostname": "localhost",
            "port": 9527,
            "description": "测试用户访问"
        }
    ]
    
    for case in test_cases:
        print(f"\n{case['description']}:")
        print(f"  请求路径: {case['path']}")
        print(f"  主机名: {case['hostname']}:{case['port']}")
        
        # 创建模拟请求
        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = case['path']
        mock_request.url.hostname = case['hostname']
        mock_request.url.port = case['port']
        
        # 推断DID
        inferred_did = analyzer.infer_resp_did_from_url(mock_request)
        
        if inferred_did:
            print(f"  ✅ 推断的DID: {inferred_did}")
        else:
            print(f"  ❌ 无法推断DID")

def demo_validation_functions():
    """演示验证功能"""
    print("\n" + "=" * 60)
    print("验证功能演示")
    print("=" * 60)
    
    analyzer = get_url_analyzer()
    
    print("\n用户ID验证:")
    user_ids = [
        "3ea884878ea5fbb1",  # 有效
        "0123456789abcdef",  # 有效
        "3ea884878ea5fbb",   # 无效：15位
        "3ea884878ea5fbb12", # 无效：17位
        "3ea884878ea5fbbg",  # 无效：包含非hex字符
        "",                  # 无效：空字符串
    ]
    
    for user_id in user_ids:
        is_valid = analyzer._is_user_id(user_id)
        status = "✅ 有效" if is_valid else "❌ 无效"
        print(f"  {user_id:20} -> {status}")
    
    print("\n编码DID验证:")
    encoded_dids = [
        "did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1",  # 有效
        "did:wba:localhost:9527:wba:user:3ea884878ea5fbb1",              # 有效
        "3ea884878ea5fbb1",                                              # 无效
        "",                                                              # 无效
    ]
    
    for encoded_did in encoded_dids:
        is_valid = analyzer._is_encoded_did(encoded_did)
        status = "✅ 有效" if is_valid else "❌ 无效"
        print(f"  {encoded_did[:50]:50} -> {status}")

def demo_performance_and_caching():
    """演示性能和缓存功能"""
    print("\n" + "=" * 60)
    print("性能和缓存演示")
    print("=" * 60)
    
    import time
    
    analyzer = get_url_analyzer()
    
    test_path = "/wba/user/3ea884878ea5fbb1/did.json"
    iterations = 1000
    
    # 第一次运行（建立缓存）
    start_time = time.time()
    for _ in range(iterations):
        analyzer.parse_url_pattern(test_path)
    first_run_time = time.time() - start_time
    
    # 第二次运行（使用缓存）
    start_time = time.time()
    for _ in range(iterations):
        analyzer.parse_url_pattern(test_path)
    second_run_time = time.time() - start_time
    
    print(f"\n性能测试结果 ({iterations} 次迭代):")
    print(f"  第一次运行时间: {first_run_time:.4f}s")
    print(f"  第二次运行时间: {second_run_time:.4f}s")
    print(f"  性能提升: {first_run_time/second_run_time:.2f}x")
    
    # 显示缓存统计
    stats = analyzer.get_analysis_stats()
    print(f"\n缓存统计:")
    print(f"  缓存大小: {stats['cache_size']}")
    print(f"  支持的模式数量: {stats['supported_patterns']}")

def demo_supported_patterns():
    """演示支持的模式"""
    print("\n" + "=" * 60)
    print("支持的URL模式")
    print("=" * 60)
    
    analyzer = get_url_analyzer()
    patterns = analyzer.get_supported_patterns()
    
    for pattern_name, pattern_regex in patterns.items():
        print(f"\n{pattern_name}:")
        print(f"  正则表达式: {pattern_regex}")
        
        # 根据模式名称提供描述
        descriptions = {
            'wba_user_id': '通过16位十六进制用户ID访问用户资源',
            'wba_user_encoded_did': '通过URL编码的完整DID访问用户资源',
            'wba_hostuser': '访问托管用户资源',
            'wba_test': '访问测试环境中的代理资源',
            'agent_api': '通过API访问代理功能'
        }
        description = descriptions.get(pattern_name, '未知模式')
        print(f"  描述: {description}")

def demo_extract_user_info():
    """演示用户信息提取"""
    print("\n" + "=" * 60)
    print("用户信息提取演示")
    print("=" * 60)
    
    analyzer = get_url_analyzer()
    
    test_paths = [
        "/wba/user/3ea884878ea5fbb1/did.json",
        "/wba/hostuser/abc123def456789a/did.json",
        "/wba/tests/test_agent_001/ad.json",
        "/invalid/path"
    ]
    
    for path in test_paths:
        user_type, user_info = analyzer.extract_user_info_from_path(path)
        print(f"\n路径: {path}")
        print(f"  用户类型: {user_type or 'N/A'}")
        print(f"  用户信息: {user_info or 'N/A'}")

def main():
    """主函数"""
    print("🚀 URL分析器功能演示")
    print("这个演示展示了ANP Open SDK中URL分析器的各种功能")
    
    try:
        demo_url_pattern_parsing()
        demo_did_inference()
        demo_validation_functions()
        demo_extract_user_info()
        demo_supported_patterns()
        demo_performance_and_caching()
        
        print("\n" + "=" * 60)
        print("✅ 演示完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
