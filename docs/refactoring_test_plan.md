# ANP Open SDK 重构测试计划

## 测试策略总览

### 测试工具和环境准备

```bash
# 1. 运行现有测试套件，建立基线
python -m pytest test/test_anpsdk_all.py -v

# 2. 检查测试覆盖率（如果已安装 pytest-cov）
python -m pytest test/ --cov=anp_open_sdk --cov-report=html

# 3. 运行 demo 验证功能
cd demo_anp_open_sdk
python anp_demo_main.py
```

## 各阶段具体测试方法

### Phase 1: 基础准备和抽象层建立

#### Step 1.1: 创建核心目录结构
```bash
# 测试方法
1. 导入测试：
   python -c "import anp_open_sdk.core; print('Core module imported successfully')"

2. 确保不影响现有导入：
   python -c "import anp_open_sdk; print('Main module still works')"

3. 运行现有测试确保没有破坏：
   python -m pytest test/test_anpsdk_all.py
```

#### Step 1.2-1.6: 创建抽象基类
```python
# 为每个抽象类创建简单的测试文件
# test/test_core_abstractions.py

import pytest
from anp_open_sdk.core.base_user_data import BaseUserData, BaseUserDataManager
from anp_open_sdk.core.base_storage import BaseStorageProvider
from anp_open_sdk.core.base_transport import RequestContext, ResponseContext

def test_base_user_data_is_abstract():
    """确保 BaseUserData 是抽象类"""
    with pytest.raises(TypeError):
        BaseUserData()

def test_request_context_creation():
    """测试数据类可以正确创建"""
    ctx = RequestContext(
        method="GET",
        url="http://test.com",
        headers={"test": "header"}
    )
    assert ctx.method == "GET"
    assert ctx.url == "http://test.com"

# 运行测试
python -m pytest test/test_core_abstractions.py -v
```

### Phase 2: 现有代码适配抽象层

#### Step 2.1: 重构 BaseUserData 继承
```python
# 测试继承关系
# test/test_inheritance.py

from anp_open_sdk.base_user_data import BaseUserData as OldBase
from anp_open_sdk.core.base_user_data import BaseUserData as NewBase

def test_inheritance_chain():
    """确保旧的 BaseUserData 继承自新的抽象类"""
    assert issubclass(OldBase, NewBase)

# 回归测试 - 确保现有功能不受影响
python -m pytest test/test_anpsdk_all.py::test_user_data -v
```

#### Step 2.2: 创建内存化的用户数据实现
```python
# test/test_memory_user_data.py

from anp_open_sdk.core.memory_user_data import MemoryUserData, MemoryUserDataManager

def test_memory_user_data_creation():
    """测试内存用户数据创建"""
    credentials_data = {
        "did": "did:wba:localhost:9527:test",
        "private_key_bytes": {"key-1": b"private_key"},
        "public_key_bytes": {"key-1": b"public_key"},
        "did_document": {"id": "did:wba:localhost:9527:test"},
        "agent_config": {"name": "test_agent"}
    }
    
    user_data = MemoryUserData(credentials_data)
    assert user_data.get_did() == "did:wba:localhost:9527:test"
    assert user_data.get_private_key_bytes("key-1") == b"private_key"

def test_memory_manager():
    """测试内存管理器"""
    manager = MemoryUserDataManager()
    # 测试添加和获取用户
    test_user = create_test_user()
    manager.add_user(test_user)
    
    retrieved = manager.get_user_data(test_user.get_did())
    assert retrieved is not None
    assert retrieved.get_did() == test_user.get_did()
```

### Phase 3: Framework 层建立

#### Step 3.2: 实现文件系统存储提供者
```python
# test/test_storage_provider.py

import pytest
import asyncio
from anp_open_sdk_framework.storage.file_system_provider import FileSystemStorageProvider

@pytest.mark.asyncio
async def test_file_operations():
    """测试文件操作"""
    provider = FileSystemStorageProvider()
    
    # 测试写入
    test_path = "test_data/test_file.txt"
    test_content = b"Hello, World!"
    
    success = await provider.write_file(test_path, test_content)
    assert success
    
    # 测试读取
    content = await provider.read_file(test_path)
    assert content == test_content
    
    # 清理
    import os
    os.remove(test_path)

@pytest.mark.asyncio
async def test_directory_listing():
    """测试目录列表"""
    provider = FileSystemStorageProvider()
    dirs = await provider.list_directories(".")
    assert isinstance(dirs, list)
```

#### Step 3.3: 实现 HTTP 传输层
```python
# test/test_http_transport.py

import pytest
from unittest.mock import patch, AsyncMock
from anp_open_sdk_framework.transport.http_transport import HttpTransport
from anp_open_sdk.core.base_transport import RequestContext

@pytest.mark.asyncio
async def test_http_transport_send():
    """测试 HTTP 传输"""
    transport = HttpTransport()
    
    # Mock aiohttp 响应
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.read = AsyncMock(return_value=b'{"result": "ok"}')
        mock_response.json = AsyncMock(return_value={"result": "ok"})
        mock_response.content_type = "application/json"
        
        mock_session.return_value.__aenter__.return_value.request.return_value.__aenter__.return_value = mock_response
        
        request = RequestContext(
            method="GET",
            url="http://test.com/api",
            headers={"Authorization": "Bearer test"}
        )
        
        response = await transport.send_request(request)
        assert response.status_code == 200
        assert response.data == {"result": "ok"}
```

### Phase 4: 路由和服务迁移

#### Step 4.2: 分离 ANPSDK 类
```python
# 集成测试 - 确保分离后功能正常
# test/test_sdk_separation.py

from anp_open_sdk.core.network_manager import NetworkManager
from anp_open_sdk_framework.server.fastapi_server import FastAPIServer

def test_network_manager_creation():
    """测试网络管理器可以独立创建"""
    manager = NetworkManager()
    assert manager is not None
    assert hasattr(manager, 'agents')

def test_server_creation():
    """测试服务器可以独立创建"""
    server = FastAPIServer()
    assert server is not None
    assert hasattr(server, 'app')

# 端到端测试
def test_compatibility_layer():
    """测试兼容层"""
    from anp_open_sdk.anp_sdk import ANPSDK
    
    # 应该仍然可以像以前一样使用
    sdk = ANPSDK()
    assert sdk is not None
```

## 持续集成测试脚本

创建一个测试脚本来自动化验证：

```bash
#!/bin/bash
# scripts/test_refactoring.sh

echo "=== Running Refactoring Tests ==="

# 1. 基础导入测试
echo "1. Testing imports..."
python -c "import anp_open_sdk.core" || exit 1
python -c "import anp_open_sdk" || exit 1

# 2. 单元测试
echo "2. Running unit tests..."
python -m pytest test/test_core_abstractions.py -v || exit 1

# 3. 回归测试
echo "3. Running regression tests..."
python -m pytest test/test_anpsdk_all.py -v || exit 1

# 4. Demo 测试
echo "4. Testing demos..."
cd demo_anp_open_sdk
timeout 30 python anp_demo_main.py || exit 1
cd ..

# 5. 集成测试
echo "5. Running integration tests..."
python -m pytest test/test_sdk_separation.py -v || exit 1

echo "=== All tests passed! ==="
```

## 测试检查清单

对于每个步骤，使用这个检查清单：

```markdown
## 测试检查清单 - Step X.X

- [ ] 代码语法检查通过 (`python -m py_compile <file>`)
- [ ] 导入测试通过
- [ ] 单元测试通过
- [ ] 现有测试没有失败
- [ ] Demo 仍然可以运行
- [ ] 代码覆盖率没有下降
- [ ] 性能没有明显退化
- [ ] 文档字符串完整
- [ ] 类型提示正确（如果使用 mypy）
```

## 快速验证命令

为了快速验证，可以使用这些一行命令：

```bash
# 快速语法检查
find anp_open_sdk -name "*.py" -exec python -m py_compile {} \;

# 快速导入测试
python -c "import anp_open_sdk; import anp_open_sdk.core; print('✓ Imports OK')"

# 快速运行核心测试
python -m pytest test/test_anpsdk_all.py -k "test_basic" -v

# 检查是否有破坏性改动
git diff --name-only | xargs python -m py_compile
```

## 测试驱动的开发流程

对于每个步骤：

1. **先写测试**：定义期望的行为
2. **运行测试**：确认测试失败（红）
3. **实现功能**：编写最少的代码使测试通过
4. **运行测试**：确认测试通过（绿）
5. **重构**：改进代码质量
6. **运行测试**：确保重构没有破坏功能

## 特定步骤的详细测试方法

### Step 1.1 测试脚本
```bash
#!/bin/bash
# test_step_1_1.sh
echo "Testing Step 1.1: Core directory structure"

# 检查目录是否创建
if [ -d "anp_open_sdk/core" ]; then
    echo "✓ Core directory created"
else
    echo "✗ Core directory not found"
    exit 1
fi

# 检查 __init__.py 是否存在
if [ -f "anp_open_sdk/core/__init__.py" ]; then
    echo "✓ Core __init__.py created"
else
    echo "✗ Core __init__.py not found"
    exit 1
fi

# 导入测试
python -c "import anp_open_sdk.core" && echo "✓ Core module imports successfully" || exit 1

# 确保现有功能不受影响
python -c "import anp_open_sdk" && echo "✓ Main module still works" || exit 1

# 运行现有测试
python -m pytest test/test_anpsdk_all.py -v && echo "✓ Existing tests pass" || exit 1

echo "Step 1.1 tests completed successfully!"
```

### Step 1.2 测试脚本
```bash
#!/bin/bash
# test_step_1_2.sh
echo "Testing Step 1.2: BaseUserData abstract classes"

# 语法检查
python -m py_compile anp_open_sdk/core/base_user_data.py && echo "✓ Syntax check passed" || exit 1

# 导入测试
python -c "from anp_open_sdk.core.base_user_data import BaseUserData, BaseUserDataManager" && echo "✓ Import test passed" || exit 1

# 抽象类测试
python -c "
from anp_open_sdk.core.base_user_data import BaseUserData
try:
    BaseUserData()
    print('✗ BaseUserData should be abstract')
    exit(1)
except TypeError:
    print('✓ BaseUserData is properly abstract')
" || exit 1

echo "Step 1.2 tests completed successfully!"
```

## 性能基准测试

为了确保重构不影响性能，建立性能基准：

```python
# test/test_performance_baseline.py

import time
import pytest
from anp_open_sdk.anp_sdk import ANPSDK


def test_sdk_initialization_time():
    """测试 SDK 初始化时间"""
    start_time = time.time()
    sdk = ANPSDK()
    end_time = time.time()

    initialization_time = end_time - start_time
    # 假设初始化应该在 1 秒内完成
    assert initialization_time < 1.0, f"SDK initialization took {initialization_time:.2f}s"


def test_user_data_loading_time():
    """测试用户数据加载时间"""
    from anp_open_sdk_framework.adapter_user_data.anp_sdk_user_data import LocalUserDataManager

    start_time = time.time()
    manager = LocalUserDataManager()
    end_time = time.time()

    loading_time = end_time - start_time
    # 假设加载应该在 0.5 秒内完成
    assert loading_time < 0.5, f"User data loading took {loading_time:.2f}s"
```

这个测试计划确保了：
- 每个改动都是可验证的
- 不会破坏现有功能
- 可以快速发现问题
- 有信心进行下一步
- 性能不会退化

使用这个测试计划，你可以在每个步骤完成后运行相应的测试，确保重构过程的安全性和可靠性。
