# ANP Open SDK DID Authentication Test Suite

专门的测试套件，包含完整的DID认证端到端测试解决方案。

## 📁 目录结构

```
test_suite/
├── tests/                          # 测试文件
│   ├── simple_test_runner.py       # 简单独立测试
│   ├── test_simplified_did_auth.py # 简化端到端测试
│   ├── test_real_integration.py    # 真实数据集成测试
│   └── test_e2e_did_auth.py       # 完整端到端测试
├── data/                           # 测试数据
│   └── data_user/                  # Agent数据目录
│       └── localhost_9527/
│           └── anp_users/         # 测试Agent
│               ├── test_agent_001/
│               └── test_agent_002/
├── config/                         # 配置文件
│   ├── test_config.yaml           # 主要测试配置
│   └── pytest.ini                 # pytest配置
├── docs/                           # 文档
│   ├── TEST_SUITE_README.md       # 详细说明
│   └── TEST_COMPARISON.md         # 测试类型对比
└── run_tests.py                   # 主入口点
```

## 🚀 快速开始

### 运行所有测试
```bash
cd test_suite
python run_tests.py
```

### 运行特定类型的测试
```bash
# 简单测试（最快）
python run_tests.py --type simple

# 简化端到端测试
python run_tests.py --type simplified_e2e  

# 集成测试
python run_tests.py --type integration
```

### 直接运行单个测试
```bash
# 简单测试（无依赖）
python tests/simple_test_runner.py

# pytest测试
python -m pytest tests/test_simplified_did_auth.py -v
```

## 🧪 测试类型

| 测试类型 | 文件 | 特点 | 用途 |
|---------|------|------|------|
| **简单测试** | `simple_test_runner.py` | 无外部依赖 | 快速验证 |
| **简化端到端** | `test_simplified_did_auth.py` | pytest框架 | 组件测试 |  
| **集成测试** | `test_real_integration.py` | 真实数据 | 兼容性验证 |
| **完整端到端** | `test_e2e_did_auth.py` | 完整流程 | 发布前验证 |

## ⚙️ 配置

### 主要配置文件：`config/test_config.yaml`
```yaml
anp_sdk:
  host: "localhost"
  port: 9527
  user_did_path: "test_suite/data/data_user"  # 指向测试套件数据

test_suite:
  test_data_root: "test_suite/data/data_user"
  temp_dir: "test_suite/temp"
  output_dir: "test_suite/output"
```

### pytest配置：`config/pytest.ini`
```ini
[tool:pytest]
asyncio_mode = auto
filterwarnings = ignore::DeprecationWarning:pydantic.*
```

## 📊 测试数据

测试套件包含预配置的测试Agent：

```
data/data_user/localhost_9527/anp_users/
├── test_agent_001/
│   ├── did_document.json  # DID文档
│   └── private_key.txt    # 私钥
└── test_agent_002/
    ├── did_document.json
    └── private_key.txt
```

每个Agent都有完整的DID文档，包含：
- ✅ 标准DID格式
- ✅ 验证方法 (EcdsaSecp256k1VerificationKey2019)
- ✅ 认证方法
- ✅ 服务端点

## 🔧 开发工作流

### 1. 开发时 - 快速验证
```bash
python tests/simple_test_runner.py
```

### 2. 提交前 - 组件验证  
```bash
python run_tests.py --type simplified_e2e
```

### 3. 集成时 - 兼容性验证
```bash
python run_tests.py --type integration
```

### 4. 发布前 - 完整验证
```bash
python run_tests.py
```

## 📝 测试覆盖

- ✅ DID文档创建和加载
- ✅ 认证组件初始化
- ✅ 签名创建和验证
- ✅ 认证上下文管理
- ✅ 文件系统交互
- ✅ Agent发现和配置
- ✅ 错误处理和边界情况

## 🛠️ 故障排除

### 常见问题

1. **找不到测试数据**
   ```
   ⚠️  Test data directory not found
   ```
   确保运行测试时在项目根目录中。

2. **配置文件未找到**
   ```
   FileNotFoundError: test_config.yaml
   ```
   使用测试套件入口点：`python test_suite/run_tests.py`

3. **pytest未安装**
   ```
   ModuleNotFoundError: No module named 'pytest'
   ```
   安装依赖：`pip install pytest pytest-asyncio`

### 调试模式
```bash
# 详细输出
python run_tests.py --verbose

# 单独调试
python tests/simple_test_runner.py
```

## 📚 相关文档

- `docs/TEST_SUITE_README.md` - 详细技术文档
- `docs/TEST_COMPARISON.md` - 测试类型对比分析
- 项目根目录的 `CLAUDE.md` - 项目总体说明

## 🎯 测试目标

这个测试套件确保：
- 🔐 DID认证流程的正确性
- 🔗 组件间的兼容性
- 📁 文件系统操作的可靠性
- 🌐 网络通信的稳定性
- 🔧 配置管理的灵活性