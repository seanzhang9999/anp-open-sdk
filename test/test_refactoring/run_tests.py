#!/usr/bin/env python3
"""
Test Runner for ANP SDK Refactoring

This script runs the complete test suite for the layered architecture refactoring.
It provides detailed reporting and can be used for CI/CD validation.
"""

import sys
import subprocess
import argparse
from pathlib import Path
import time


def run_test_suite(test_pattern=None, verbose=False, coverage=False):
    """Run the test suite with optional filtering and coverage"""
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test directory
    test_dir = Path(__file__).parent
    cmd.append(str(test_dir))
    
    # Add verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add coverage if requested
    if coverage:
        cmd.extend([
            "--cov=anp_open_sdk.protocol",
            "--cov=anp_open_sdk.auth", 
            "--cov=anp_open_sdk_framework.adapters",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov"
        ])
    
    # Add test pattern filter
    if test_pattern:
        cmd.extend(["-k", test_pattern])
    
    # Add async support
    cmd.append("--asyncio-mode=auto")
    
    # Run tests
    print(f"Running: {' '.join(cmd)}")
    print("=" * 60)
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=False)
    end_time = time.time()
    
    print("=" * 60)
    print(f"Test run completed in {end_time - start_time:.2f} seconds")
    
    return result.returncode


def run_specific_test_categories():
    """Run tests by category with detailed reporting"""
    
    categories = {
        "Protocol Layer": "test_protocol.py",
        "SDK Layer": "test_sdk.py", 
        "Framework Layer": "test_framework.py",
        "Integration": "test_integration.py",
        "Configuration": "test_config.py"
    }
    
    results = {}
    total_start = time.time()
    
    for category, test_file in categories.items():
        print(f"\n{'=' * 60}")
        print(f"Running {category} Tests")
        print(f"{'=' * 60}")
        
        start_time = time.time()
        cmd = [
            "python", "-m", "pytest",
            str(Path(__file__).parent / test_file),
            "-v",
            "--asyncio-mode=auto"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        end_time = time.time()
        
        results[category] = {
            "returncode": result.returncode,
            "duration": end_time - start_time,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
        # Print summary
        if result.returncode == 0:
            print(f"✅ {category} tests PASSED ({end_time - start_time:.2f}s)")
        else:
            print(f"❌ {category} tests FAILED ({end_time - start_time:.2f}s)")
            print("STDOUT:", result.stdout[-500:] if result.stdout else "None")
            print("STDERR:", result.stderr[-500:] if result.stderr else "None")
    
    total_end = time.time()
    
    # Print overall summary
    print(f"\n{'=' * 60}")
    print("OVERALL TEST SUMMARY")
    print(f"{'=' * 60}")
    
    passed = sum(1 for r in results.values() if r["returncode"] == 0)
    total = len(results)
    
    for category, result in results.items():
        status = "✅ PASS" if result["returncode"] == 0 else "❌ FAIL"
        print(f"{category:20} {status:8} ({result['duration']:.2f}s)")
    
    print(f"\nTotal: {passed}/{total} test categories passed")
    print(f"Total time: {total_end - total_start:.2f} seconds")
    
    return 0 if passed == total else 1


def validate_test_environment():
    """Validate that the test environment is properly set up"""
    
    print("Validating test environment...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        return False
    else:
        print(f"✅ Python {sys.version}")
    
    # Check required packages
    required_packages = [
        "pytest", "pytest-asyncio", "pydantic", "jcs", "cryptography", 
        "aiohttp", "yaml", "fastapi"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    # Check test files exist
    test_dir = Path(__file__).parent
    test_files = [
        "test_base.py",
        "test_protocol.py", 
        "test_sdk.py",
        "test_framework.py",
        "test_integration.py",
        "test_config.py"
    ]
    
    for test_file in test_files:
        if (test_dir / test_file).exists():
            print(f"✅ {test_file}")
        else:
            print(f"❌ {test_file} (missing)")
            return False
    
    print("\n✅ Test environment validation passed")
    return True


def main():
    parser = argparse.ArgumentParser(description="Run ANP SDK refactoring tests")
    parser.add_argument(
        "--pattern", "-k", 
        help="Run only tests matching this pattern"
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--coverage", "-c",
        action="store_true", 
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--by-category",
        action="store_true",
        help="Run tests by category with detailed reporting"
    )
    parser.add_argument(
        "--validate-env",
        action="store_true",
        help="Validate test environment setup"
    )
    
    args = parser.parse_args()
    
    # Validate environment if requested
    if args.validate_env:
        if not validate_test_environment():
            return 1
        return 0
    
    # Validate environment before running tests
    if not validate_test_environment():
        print("\n❌ Environment validation failed. Use --validate-env for details.")
        return 1
    
    # Run tests by category
    if args.by_category:
        return run_specific_test_categories()
    
    # Run all tests
    return run_test_suite(
        test_pattern=args.pattern,
        verbose=args.verbose,
        coverage=args.coverage
    )


if __name__ == "__main__":
    sys.exit(main())