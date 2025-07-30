# 记忆功能集成指南

本指南介绍如何使用重构后的 `@local_method` 装饰器，该装饰器现已完全集成记忆功能。

## 概述

经过重构，原有的 `@local_method` 装饰器现在直接支持记忆功能，无需使用额外的装饰器。这种设计简化了API，提供了更好的用户体验。

## 基本用法

### 1. 不启用记忆（默认行为）

```python
from anp_runtime.local_service.local_methods_decorators import local_method

@local_method("简单计算函数")
def add(a, b):
    """计算两个数的和"""
    return a + b
```

这与之前的用法完全相同，向后兼容。

### 2. 简单启用记忆

```python
@local_method("启用记忆的计算函数", memory=True)
def multiply(x, y):
    """计算两个数的乘积，并记录执行过程"""
    return x * y
```

使用 `memory=True` 启用默认记忆设置。

### 3. 使用完整的记忆配置

```python
from anp_runtime.local_service.memory import MemoryOptions

@local_method("复杂计算", memory=MemoryOptions(
    enabled=True,
    tags=["math", "calculation"],
    keywords=["division", "arithmetic"],
    collect_input=True,
    collect_output=True,
    collect_errors=True,
    session_id="calc_session_001"
))
def divide(a, b):
    """执行除法运算，完整记录过程"""
    if b == 0:
        raise ValueError("除数不能为零")
    return a / b
```

### 4. 使用字典配置

```python
@local_method("文本处理", memory={
    "enabled": True,
    "tags": ["text", "processing"],
    "keywords": ["string", "transform"],
    "collect_input": True,
    "collect_output": False,  # 不记录输出结果
    "collect_errors": True
})
def process_text(text):
    """处理文本，记录输入和错误但不记录输出"""
    return text.upper().strip()
```

### 5. 异步方法

```python
import asyncio

@local_method("异步数据处理", memory=True)
async def async_process_data(data_list):
    """异步处理数据列表"""
    await asyncio.sleep(0.1)  # 模拟异步操作
    return [item * 2 for item in data_list]
```

## 向后兼容性

重构后的装饰器完全支持旧的参数格式：

```python
# 旧的参数格式仍然有效
@local_method(
    description="兼容性测试",
    tags=["legacy"],
    enable_memory=True,
    memory_tags=["old_style"],
    memory_keywords=["legacy"],
    collect_input=True,
    collect_output=True,
    collect_errors=False
)
def legacy_method(data):
    """使用旧参数格式的方法"""
    return len(data)
```

## 记忆配置选项

### MemoryOptions 参数说明

- `enabled` (bool): 是否启用记忆收集，默认 True
- `tags` (List[str]): 记忆标签，用于分类，默认 []
- `keywords` (List[str]): 记忆关键词，用于搜索，默认 []
- `collect_input` (bool): 是否收集输入参数，默认 True
- `collect_output` (bool): 是否收集输出结果，默认 True
- `collect_errors` (bool): 是否收集错误信息，默认 True
- `session_id` (str, optional): 会话ID，用于关联相关操作
- `extra` (Dict[str, Any]): 扩展配置，默认 {}

### 便捷配置函数

```python
from anp_runtime.local_service.memory import memory_enabled, memory_disabled

# 启用记忆并设置标签和关键词
@local_method("数据分析", memory=memory_enabled(
    tags=["analytics", "data"],
    keywords=["statistics", "analysis"],
    collect_errors=False
))
def analyze_data(dataset):
    """分析数据集"""
    return {"mean": sum(dataset) / len(dataset)}

# 明确禁用记忆
@local_method("简单操作", memory=memory_disabled())
def simple_operation(x):
    """不需要记忆的简单操作"""
    return x + 1
```

## 配置优先级

装饰器的记忆配置优先级（从高到低）：

1. `memory` 参数（新格式）
2. 旧格式参数（`enable_memory`, `memory_tags` 等）
3. 全局记忆配置

```python
# 新参数优先于旧参数
@local_method(
    "优先级测试",
    memory=True,  # 这个会被使用
    enable_memory=False  # 这个会被忽略
)
def priority_test():
    pass
```

## 运行时管理

### 查询方法的记忆配置

```python
from anp_runtime.local_service.local_methods_decorators import get_method_memory_config

# 获取方法的记忆配置
method_key = "my_module::my_method"
config = get_method_memory_config(method_key)
if config:
    print(f"记忆已启用: {config.get('enabled')}")
    print(f"标签: {config.get('tags')}")
```

### 列出启用记忆的方法

```python
from anp_runtime.local_service.local_methods_decorators import list_memory_enabled_methods

# 获取所有启用记忆的方法
enabled_methods = list_memory_enabled_methods()
for method_key in enabled_methods:
    print(f"启用记忆的方法: {method_key}")
```

### 动态更新记忆配置

```python
from anp_runtime.local_service.local_methods_decorators import update_method_memory_config

# 动态更新方法的记忆配置
method_key = "my_module::my_method"
success = update_method_memory_config(method_key, {
    "enabled": False,
    "tags": ["updated", "disabled"]
})
print(f"配置更新{'成功' if success else '失败'}")
```

## 错误处理

装饰器设计为优雅地处理各种错误情况：

```python
# 即使记忆模块不可用，方法仍然正常工作
@local_method("容错测试", memory=True)
def fault_tolerant_method(x):
    """即使记忆功能失败，此方法仍能正常执行"""
    return x * 2

# 无效的记忆配置会被忽略，方法照常工作
@local_method("无效配置", memory="invalid_config")
def invalid_config_method():
    """无效配置不会影响方法执行"""
    return "正常工作"
```

## 最佳实践

1. **选择合适的配置方式**：
   - 简单场景使用 `memory=True`
   - 复杂需求使用 `MemoryOptions`
   - 批量配置使用字典格式

2. **合理设置收集选项**：
   - 对于包含敏感数据的方法，考虑设置 `collect_input=False`
   - 对于返回大量数据的方法，考虑设置 `collect_output=False`
   - 总是记录错误信息以便调试

3. **使用标签和关键词**：
   - 为相关方法使用一致的标签
   - 选择有意义的关键词便于后续搜索

4. **会话管理**：
   - 为相关操作使用相同的 `session_id`
   - 会话ID有助于追踪完整的操作流程

## 迁移指南

### 从旧装饰器迁移

如果你之前使用 `@local_method_with_memory`：

```python
# 旧方式
@local_method_with_memory(
    description="计算函数",
    memory_tags=["math"],
    collect_input=True
)
def old_way(x, y):
    return x + y

# 新方式（推荐）
@local_method("计算函数", memory=MemoryOptions(
    enabled=True,
    tags=["math"],
    collect_input=True
))
def new_way(x, y):
    return x + y

# 或者使用更简洁的方式
@local_method("计算函数", memory={
    "enabled": True,
    "tags": ["math"],
    "collect_input": True
})
def newer_way(x, y):
    return x + y
```

### 批量迁移

对于大量现有代码，可以逐步迁移：

1. 现有的 `@local_method` 装饰器继续正常工作
2. 新功能使用新的 `memory` 参数
3. 逐步将旧的记忆相关装饰器替换为新格式

## 总结

重构后的 `@local_method` 装饰器提供了：

- **统一的API**：一个装饰器处理所有需求
- **向后兼容**：现有代码无需修改
- **灵活配置**：支持多种配置方式
- **类型安全**：完整的类型提示支持
- **错误容忍**：优雅处理各种异常情况

这种设计简化了记忆功能的使用，提高了开发效率，同时保持了强大的功能性。