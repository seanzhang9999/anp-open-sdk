"""
ANP Python SDK 测试套件
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 设置测试环境变量
os.environ.setdefault('ANP_TEST_MODE', 'true')
os.environ.setdefault('ANP_MEMORY_CONFIG_PATH', str(PROJECT_ROOT / 'tests' / 'data' / 'test_memory_config.yaml'))