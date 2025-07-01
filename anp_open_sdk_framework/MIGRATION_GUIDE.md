# ANP Open SDK Framework 重构迁移指南

## 概述
本次重构将原有的分散调用体系统一为更清晰、更易用的架构：
1. **统一调用器** (UnifiedCaller) - 合并本地方法和远程API调用
2. **统一爬虫** (UnifiedCrawler) - 整合资源发现和智能调用
3. **主智能体** (MasterAgent) - 提供任务级别的统一调度
4. **基于API的服务架构** - 将service功能抽象为API调用

## 重构前后对比

### 调用方式对比

#### 重构前
```python
# 本地方法调用
caller = LocalMethodsCaller(sdk)
result = await caller.call_method_by_search("demo_method", arg1, arg2)

# 远程API调用
result = await agent_api_call(caller_did, target_did, "/api/path", params)
```

#### 重构后
```python
# 统一调用接口
caller = UnifiedCaller(sdk)
result = await caller.call(target, method_or_path, *args, **kwargs)

# 或者使用统一爬虫
crawler = UnifiedCrawler(sdk)
result = await crawler.intelligent_call("执行demo方法", arg1=value1, arg2=value2)
```

### 资源发现对比

#### 重构前
```python
# 分别处理本地方法和远程agent
doc_generator = LocalMethodsDocGenerator()
methods = doc_generator.search_methods("keyword")

# 远程agent发现需要单独实现
```

#### 重构后
```python
# 统一资源发现
crawler = UnifiedCrawler(sdk)
resources = await crawler.discover_all_resources()
results = await crawler.search_resources("keyword")
```

## 迁移步骤

### 1. 更新导入语句
```python
# 旧的导入
from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller
from anp_open_sdk.service.interaction.agent_api_call import agent_api_call

# 新的导入
from anp_open_sdk_framework import UnifiedCaller, UnifiedCrawler, MasterAgent
```

### 2. 替换调用代码

#### 本地方法调用迁移
```python
# 旧代码
caller = LocalMethodsCaller(sdk)
result = await caller.call_method_by_search("demo_method", arg1, arg2)

# 新代码
caller = UnifiedCaller(sdk)
result = await caller.search_and_call("demo_method", arg1, arg2)
```

#### 远程API调用迁移
```python
# 旧代码
result = await agent_api_call(caller_did, target_did, "/api/path", params)

# 新代码
caller = UnifiedCaller(sdk)
result = await caller.call(target_did, "/api/path", **params)
```

### 3. 使用主智能体模式
```python
# 创建主智能体
master = MasterAgent(sdk)
await master.initialize()

# 执行任务
result = await master.execute_task("调用demo方法计算1+2", {"arg1": 1, "arg2": 2})
```

### 4. 更新爬虫代码
如果你有自定义的爬虫，可以基于新的统一架构重写：

```python
# 旧的爬虫模式
async def run_local_method_crawler(sdk):
    caller = LocalMethodsCaller(sdk)
    # ... 具体逻辑

# 新的统一爬虫模式
async def run_unified_crawler(sdk):
    crawler = UnifiedCrawler(sdk)
    resources = await crawler.discover_all_resources()

    # 智能调用
    result = await crawler.intelligent_call("任务描述")

    # 或者精确调用
    result = await crawler.call_by_name("method_name", **args)
```

## 新功能特性

### 1. 智能任务执行
```python
master = MasterAgent(sdk)
await master.initialize()

# 自然语言任务描述
result = await master.execute_task("查找所有可用的计算方法")
result = await master.execute_task("调用加法方法计算10+20")
result = await master.execute_task("搜索包含'demo'关键词的方法")
```

### 2. 统一资源管理
```python
crawler = UnifiedCrawler(sdk)

# 发现所有资源
resources = await crawler.discover_all_resources()

# 获取资源摘要
summary = crawler.get_resource_summary()

# 搜索资源
results = await crawler.search_resources("计算")
```

### 3. 灵活的调用方式
```python
caller = UnifiedCaller(sdk)

# 通过DID调用远程API
result = await caller.call("did:example:123", "/calculate", a=1, b=2)

# 通过agent名称调用本地方法
result = await caller.call("calculator_agent", "add", 1, 2)

# 搜索并调用
result = await caller.search_and_call("加法", 1, 2)
```

## 命令行使用

### 主智能体模式
```bash
# 交互模式
python framework_demo.py --master-mode

# 单任务模式
python framework_demo.py --master-mode --task "调用demo方法"

# 带参数的任务
python framework_demo.py --master-mode --task "计算" --method-args '{"a": 1, "b": 2}'
```

### 统一模式
```bash
# 统一爬虫模式
python framework_demo.py --unified-mode --target-method "demo_method"

# 智能调用
python framework_demo.py --unified-mode --intelligent --target-method "计算方法"
```

## 兼容性说明
- 原有的 `LocalMethodsCaller` 和 `agent_api_call` 仍然可用，但建议迁移到新的统一接口
- 现有的本地方法装饰器 `@local_method` 无需修改
- 现有的agent配置和DID认证机制保持不变

## 最佳实践
1. **优先使用主智能体模式** - 适合复杂任务和用户交互场景
2. **使用统一调用器** - 适合明确知道调用目标的场景
3. **使用统一爬虫** - 适合需要资源发现和智能匹配的场景
4. **保持向后兼容** - 逐步迁移，避免一次性大规模修改

## 故障排除

### 常见问题
1. **找不到方法** - 确保方法已正确注册并且agent已加载
2. **调用失败** - 检查参数格式和权限设置
3. **资源发现为空** - 确保SDK已正确初始化并且agents已加载

### 调试技巧
```python
# 启用详细日志
import logging
logging.getLogger('anp_open_sdk_framework').setLevel(logging.DEBUG)

# 检查可用资源
crawler = UnifiedCrawler(sdk)
resources = await crawler.discover_all_resources()
print(crawler.get_resource_summary())

# 检查方法注册
caller = UnifiedCaller(sdk)
methods = caller.list_all_methods()
print(methods)
```

## 总结
这个重构方案解决了你提出的所有问题：
1. **统一调用体系** - UnifiedCaller 合并了本地方法和远程API调用
2. **统一爬虫架构** - UnifiedCrawler 整合了资源发现和调用逻辑
3. **主智能体设计** - MasterAgent 提供任务级别的统一调度
4. **基于API的架构** - 所有功能都通过统一的API接口工作

主要优势：
• **开发者友好** - 统一的接口，减少学习成本
• **功能强大** - 支持智能任务执行和自然语言交互
• **架构清晰** - 分层设计，职责明确
• **向后兼容** - 保持现有代码可用性
• **易于扩展** - 插件化的资源发现器设计

你觉得这个重构方案如何？需要我详细解释某个部分或者添加其他功能吗？
