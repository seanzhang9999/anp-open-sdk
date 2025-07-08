#!/usr/bin/env python3
"""
ANP Open SDK DID Authentication Test Suite

主入口点，用于运行所有测试类型
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def get_test_suite_root():
    """获取测试套件根目录"""
    return Path(__file__).parent

def parse_pytest_output(output):
    """解析pytest输出，提取测试统计信息"""
    import re
    
    # 查找测试结果行，格式如: "12 passed, 7 warnings in 0.63s"
    result_pattern = r'=+ (\d+) passed(?:, (\d+) skipped)?(?:, (\d+) failed)?(?:, (\d+) warnings?)? in [\d.]+s =+'
    match = re.search(result_pattern, output)
    
    if match:
        passed = int(match.group(1)) if match.group(1) else 0
        skipped = int(match.group(2)) if match.group(2) else 0
        failed = int(match.group(3)) if match.group(3) else 0
        warnings = int(match.group(4)) if match.group(4) else 0
        total = passed + skipped + failed
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'warnings': warnings
        }
    
    # 备用解析：查找collected项目数
    collected_pattern = r'collected (\d+) items'
    collected_match = re.search(collected_pattern, output)
    if collected_match:
        total = int(collected_match.group(1))
        # 如果没有失败信息，假设全部通过
        if 'FAILED' not in output and 'ERROR' not in output:
            return {
                'total': total,
                'passed': total,
                'failed': 0,
                'skipped': 0,
                'warnings': output.count('warnings')
            }
    
    # 默认值
    return {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'warnings': 0
    }

def run_simple_tests():
    """运行简单测试"""
    print("🚀 Running Simple Tests...")
    test_file = get_test_suite_root() / "tests" / "simple_test_runner.py"
    result = subprocess.run([sys.executable, str(test_file)], 
                          capture_output=True, text=True, cwd=get_test_suite_root().parent)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # 解析简单测试的结果 - 更精确的解析
    output = result.stdout
    
    # 计算实际测试通过数量：查找"🎉 All tests passed!"行
    if "🎉 All tests passed!" in output and result.returncode == 0:
        # 查找"Passed: X/Y"模式
        import re
        passed_pattern = r'Passed: (\d+)/(\d+)'
        match = re.search(passed_pattern, output)
        if match:
            passed_count = int(match.group(1))
            total_count = int(match.group(2))
        else:
            # 备用：数✅符号，但要更准确
            test_sections = output.split("🧪 Test")
            passed_count = len([section for section in test_sections[1:] if "✅" in section and "passed" in section])
            total_count = passed_count
    else:
        # 失败情况
        passed_count = 0
        total_count = 5  # 简单测试固定5个
    
    warnings_count = 0  # 简单测试没有警告
    
    return {
        'success': result.returncode == 0,
        'total': total_count,
        'passed': passed_count,
        'failed': total_count - passed_count if result.returncode != 0 else 0,
        'skipped': 0,
        'warnings': warnings_count
    }

def run_simplified_e2e_tests():
    """运行简化端到端测试"""
    print("🧪 Running Simplified E2E Tests...")
    test_file = get_test_suite_root() / "tests" / "test_simplified_did_auth.py"
    config_file = get_test_suite_root() / "config" / "pytest.ini"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-c", str(config_file),
        "-v", "--tb=short"
    ]
    
    # 设置正确的工作目录
    result = subprocess.run(cmd, capture_output=True, text=True, 
                          cwd=str(get_test_suite_root().parent))
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # 解析pytest输出
    stats = parse_pytest_output(result.stdout)
    stats['success'] = result.returncode == 0
    return stats

def run_integration_tests():
    """运行集成测试"""
    print("🔗 Running Integration Tests...")
    test_file = get_test_suite_root() / "tests" / "test_real_integration.py"
    config_file = get_test_suite_root() / "config" / "pytest.ini"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-c", str(config_file),
        "-v", "--tb=short"
    ]
    
    # 设置正确的工作目录
    result = subprocess.run(cmd, capture_output=True, text=True,
                          cwd=str(get_test_suite_root().parent))
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # 解析pytest输出
    stats = parse_pytest_output(result.stdout)
    stats['success'] = result.returncode == 0
    return stats

def run_router_flow_tests():
    """运行路由器完整流程测试"""
    print("🔄 Running Router Complete Flow Tests...")
    test_file = get_test_suite_root() / "tests" / "test_router_complete_flow.py"
    config_file = get_test_suite_root() / "config" / "pytest.ini"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-c", str(config_file),
        "-v", "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, 
                          cwd=str(get_test_suite_root().parent))
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # 解析pytest输出
    stats = parse_pytest_output(result.stdout)
    stats['success'] = result.returncode == 0
    return stats

def run_sdk_integration_tests():
    """运行SDK集成测试"""
    print("⚙️ Running SDK Integration Tests...")
    test_file = get_test_suite_root() / "tests" / "test_sdk_integration.py"
    config_file = get_test_suite_root() / "config" / "pytest.ini"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-c", str(config_file),
        "-v", "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, 
                          cwd=str(get_test_suite_root().parent))
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # 解析pytest输出
    stats = parse_pytest_output(result.stdout)
    stats['success'] = result.returncode == 0
    return stats

def run_service_injection_tests():
    """运行服务注入模式测试"""
    print("💉 Running Service Injection Pattern Tests...")
    test_file = get_test_suite_root() / "tests" / "test_service_injection_pattern.py"
    config_file = get_test_suite_root() / "config" / "pytest.ini"
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_file),
        "-c", str(config_file),
        "-v", "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, 
                          cwd=str(get_test_suite_root().parent))
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    # 解析pytest输出
    stats = parse_pytest_output(result.stdout)
    stats['success'] = result.returncode == 0
    return stats

def run_all_tests():
    """运行所有测试"""
    print("🎯 Running All Test Types...")
    print("=" * 80)
    
    results = {}
    
    # 1. 简单测试
    results['simple'] = run_simple_tests()
    print()
    
    # 2. 简化端到端测试
    results['simplified_e2e'] = run_simplified_e2e_tests()
    print()
    
    # 3. 集成测试
    results['integration'] = run_integration_tests()
    print()
    
    # 4. 路由器完整流程测试
    results['router_flow'] = run_router_flow_tests()
    print()
    
    # 5. SDK集成测试
    results['sdk_integration'] = run_sdk_integration_tests()
    print()
    
    # 6. 服务注入模式测试
    results['service_injection'] = run_service_injection_tests()
    print()
    
    # 计算总计
    total_tests = sum(result['total'] for result in results.values())
    total_passed = sum(result['passed'] for result in results.values())
    total_failed = sum(result['failed'] for result in results.values())
    total_skipped = sum(result['skipped'] for result in results.values())
    total_warnings = sum(result['warnings'] for result in results.values())
    
    # 详细结果总结
    print("📊 Test Results Summary")
    print("=" * 96)
    print(f"{'Test Type':<20} {'Status':<10} {'Total':<7} {'Passed':<7} {'Failed':<7} {'Skipped':<8} {'Warnings':<9}")
    print("-" * 96)
    
    for test_type, result in results.items():
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"{test_type:<20} {status:<10} {result['total']:<7} {result['passed']:<7} {result['failed']:<7} {result['skipped']:<8} {result['warnings']:<9}")
    
    print("-" * 96)
    status_all = "✅ PASSED" if all(result['success'] for result in results.values()) else "❌ FAILED"
    print(f"{'TOTAL':<20} {status_all:<10} {total_tests:<7} {total_passed:<7} {total_failed:<7} {total_skipped:<8} {total_warnings:<9}")
    print("=" * 96)
    
    # 总结信息
    all_passed = all(result['success'] for result in results.values())
    if all_passed:
        print(f"\n🎉 All {len(results)} test types passed! ({total_passed}/{total_tests} tests passed")
        if total_skipped > 0:
            print(f"   📋 {total_skipped} tests skipped")
        if total_warnings > 0:
            print(f"   ⚠️  {total_warnings} warnings")
        print(")")
    else:
        failed_types = [name for name, result in results.items() if not result['success']]
        print(f"\n❌ {len(failed_types)}/{len(results)} test type(s) failed: {', '.join(failed_types)}")
        print(f"   📊 Overall: {total_passed}/{total_tests} tests passed, {total_failed} failed, {total_skipped} skipped")
        if total_warnings > 0:
            print(f"   ⚠️  {total_warnings} warnings")
    
    return all_passed

def display_single_test_result(test_type, result):
    """显示单个测试类型的详细结果"""
    print("\n📊 Test Results Summary")
    print("=" * 96)
    print(f"{'Test Type':<20} {'Status':<10} {'Total':<7} {'Passed':<7} {'Failed':<7} {'Skipped':<8} {'Warnings':<9}")
    print("-" * 96)
    
    if isinstance(result, dict):
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"{test_type:<20} {status:<10} {result['total']:<7} {result['passed']:<7} {result['failed']:<7} {result['skipped']:<8} {result['warnings']:<9}")
        
        print("=" * 96)
        
        if result['success']:
            print(f"\n🎉 {test_type} tests passed! ({result['passed']}/{result['total']} tests passed")
            if result['skipped'] > 0:
                print(f"   📋 {result['skipped']} tests skipped")
            if result['warnings'] > 0:
                print(f"   ⚠️  {result['warnings']} warnings")
            print(")")
        else:
            print(f"\n❌ {test_type} tests failed!")
            print(f"   📊 {result['passed']}/{result['total']} tests passed, {result['failed']} failed, {result['skipped']} skipped")
            if result['warnings'] > 0:
                print(f"   ⚠️  {result['warnings']} warnings")
    else:
        # 兼容旧格式 (boolean)
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_type:<20} {status:<10} {'N/A':<7} {'N/A':<7} {'N/A':<7} {'N/A':<8} {'N/A':<9}")
        print("=" * 96)
        if result:
            print(f"\n🎉 {test_type} tests passed!")
        else:
            print(f"\n❌ {test_type} tests failed!")

def main():
    parser = argparse.ArgumentParser(description="ANP Open SDK DID Authentication Test Suite")
    parser.add_argument("--type", choices=["simple", "simplified_e2e", "integration", "router_flow", "sdk_integration", "service_injection", "all"],
                       default="all", help="Test type to run")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("ANP Open SDK DID Authentication Test Suite")
    print("=" * 80)
    print(f"Test Suite Root: {get_test_suite_root()}")
    print(f"Working Directory: {get_test_suite_root().parent}")
    print()
    
    if args.type == "simple":
        result = run_simple_tests()
        display_single_test_result("simple", result)
        success = result['success'] if isinstance(result, dict) else result
    elif args.type == "simplified_e2e":
        result = run_simplified_e2e_tests()
        display_single_test_result("simplified_e2e", result)
        success = result['success'] if isinstance(result, dict) else result
    elif args.type == "integration":
        result = run_integration_tests()
        display_single_test_result("integration", result)
        success = result['success'] if isinstance(result, dict) else result
    elif args.type == "router_flow":
        result = run_router_flow_tests()
        display_single_test_result("router_flow", result)
        success = result['success'] if isinstance(result, dict) else result
    elif args.type == "sdk_integration":
        result = run_sdk_integration_tests()
        display_single_test_result("sdk_integration", result)
        success = result['success'] if isinstance(result, dict) else result
    elif args.type == "service_injection":
        result = run_service_injection_tests()
        display_single_test_result("service_injection", result)
        success = result['success'] if isinstance(result, dict) else result
    else:  # all
        success = run_all_tests()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()