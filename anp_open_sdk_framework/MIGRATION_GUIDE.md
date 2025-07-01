# ANP Open SDK Framework 重构迁移指南

## 概述
本次重构将原有的分散调用体系统一为更清晰、更易用的架构：
1. **统一调用器** (UnifiedCaller) - 合并本地方法和远程API调用
2. **统一爬虫** (UnifiedCrawler) - 整合资源发现和智能调用，支持LLM增强
3. **主智能体** (MasterAgent) - 提供任务级别的统一调度和自然语言理解
4. **基于API的服务架构** - 将service功能抽象为API调用
5. **LLM增强匹配** - 可选的大语言模型支持，提供更智能的语义理解

## 重构前后对比

### 调用方式对比

#### 重构前
```python
# 本地方法调用
caller = LocalMethodsCaller(sdk)
result = await caller.call_method_by_search("demo_method", arg1, arg2)

# 远程API调用
result = await agent_api_call(caller_did, target_did, "/api/path", params)

# 智能爬虫调用（旧版）
result = await run_intelligent_local_method_crawler(sdk, "demo_method", method_args)
```

#### 重构后
```python
# 统一调用接口
caller = UnifiedCaller(sdk)
result = await caller.call(target, method_or_path, *args, **kwargs)

# 统一爬虫 - 智能调用
crawler = UnifiedCrawler(sdk)
result = await crawler.intelligent_call("执行demo方法", arg1=value1, arg2=value2)

# 主智能体 - 自然语言任务
master = MasterAgent(sdk)
result = await master.execute_task("调用加法方法计算10+20")
```

### 资源发现对比

#### 重构前
```python
# 分别处理本地方法和远程agent
doc_generator = LocalMethodsDocGenerator()
methods = doc_generator.search_methods("keyword")

# 手动实现智能匹配逻辑
def intelligent_method_matching(methods_info, target_method_name):
    # 复杂的匹配算法...
```

#### 重构后
```python
# 统一资源发现
crawler = UnifiedCrawler(sdk)
resources = await crawler.discover_all_resources()

# 智能搜索（支持同义词和模糊匹配）
results = await crawler.search_resources("计算功能")

# LLM增强搜索（可选）
crawler_with_llm = UnifiedCrawler(sdk, llm_config=llm_config)
results = await crawler_with_llm.intelligent_call("找到所有数学计算相关的方法")
```

## 迁移步骤

### 1. 更新导入语句
```python
# 旧的导入
from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller
from anp_open_sdk.service.interaction.agent_api_call import agent_api_call
from anp_open_sdk_framework_demo.crawlers.agent_002_local_caller_crawler import run_intelligent_local_method_crawler

# 新的导入
from anp_open_sdk_framework import UnifiedCaller, UnifiedCrawler, MasterAgent
```

### 2. 替换调用代码

#### 本地方法调用迁移
```python
# 旧代码
caller = LocalMethodsCaller(sdk)
result = await caller.call_method_by_search("demo_method", arg1, arg2)

# 新代码 - 方式1：统一调用器
caller = UnifiedCaller(sdk)
result = await caller.search_and_call("demo_method", arg1, arg2)

# 新代码 - 方式2：统一爬虫
crawler = UnifiedCrawler(sdk)
result = await crawler.call_by_name("demo_method", arg1=arg1, arg2=arg2)

# 新代码 - 方式3：智能调用
result = await crawler.intelligent_call("调用demo方法", arg1=arg1, arg2=arg2)
```

#### 智能爬虫迁移
```python
# 旧代码
result = await run_intelligent_local_method_crawler(
    sdk=sdk,
    target_method_name="calculate_sum",
    method_args={"args": [10, 20]}
)

# 新代码 - 统一爬虫
crawler = UnifiedCrawler(sdk)
result = await crawler.intelligent_call("计算", a=10, b=20)

# 新代码 - 主智能体（推荐）
master = MasterAgent(sdk)
await master.initialize()
result = await master.execute_task("计算10和20的和")
```

#### 远程API调用迁移
```python
# 旧代码
result = await agent_api_call(caller_did, target_did, "/api/path", params)

# 新代码
caller = UnifiedCaller(sdk)
result = await caller.call(target_did, "/api/path", **params)
```

### 3. 使用主智能体模式（推荐）
```python
# 创建主智能体
master = MasterAgent(sdk)
await master.initialize()

# 自然语言任务执行
result = await master.execute_task("调用demo方法")
result = await master.execute_task("计算两个数的和", {"a": 15, "b": 25})
result = await master.execute_task("查找所有可用的计算方法")

# 支持LLM增强（可选）
master_with_llm = MasterAgent(sdk, llm_config={
    'type': 'openai',
    'api_key': 'your-api-key'
})
await master_with_llm.initialize()
result = await master_with_llm.execute_task("帮我找到最适合计算两个数乘积的方法")
```

### 4. 更新爬虫代码
```python
# 旧的爬虫模式（已弃用）
async def run_local_method_crawler(sdk):
    caller = LocalMethodsCaller(sdk)
    # ... 复杂的逻辑

async def run_intelligent_local_method_crawler(sdk, target_method_name, method_args):
    # ... 复杂的智能匹配逻辑

# 新的统一爬虫模式
async def run_unified_crawler(sdk):
    crawler = UnifiedCrawler(sdk)

    # 发现所有资源
    resources = await crawler.discover_all_resources()
    print(crawler.get_resource_summary())

    # 智能调用
    result = await crawler.intelligent_call("执行演示功能")

    # 精确调用
    result = await crawler.call_by_name("demo_method", message="Hello")

    # 搜索资源
    search_results = await crawler.search_resources("计算")
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

# 复杂任务理解
result = await master.execute_task("帮我执行一个简单的演示")
result = await master.execute_task("计算15和25的和")
```

### 2. 统一资源管理
```python
crawler = UnifiedCrawler(sdk)

# 发现所有资源
resources = await crawler.discover_all_resources()

# 获取资源摘要
summary = crawler.get_resource_summary()
print(summary)
# 输出：
# 📊 资源摘要:
#   - local_methods: 3 个
#     例如: calculate_sum, demo_method, info_method
#   - remote_agents: 0 个
#   - api_endpoints: 0 个
# 📈 总计: 3 个资源

# 智能搜索（支持同义词）
results = await crawler.search_resources("计算")  # 会找到 calculate_sum
results = await crawler.search_resources("加法")  # 也会找到 calculate_sum
results = await crawler.search_resources("所有")  # 返回所有资源
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

### 4. LLM增强功能（可选）
```python
# 配置LLM
llm_config = {
    'type': 'openai',
    'api_key': 'your-openai-api-key',
    'base_url': None  # 可选，用于自定义端点
}

# 创建LLM增强的爬虫
crawler = UnifiedCrawler(sdk, llm_config=llm_config)

# LLM会理解更复杂的自然语言
result = await crawler.intelligent_call("帮我找到一个可以计算两个数字相加的方法")
result = await crawler.intelligent_call("我需要执行一个演示功能")

# 主智能体也支持LLM
master = MasterAgent(sdk, llm_config=llm_config)
await master.initialize()
result = await master.execute_task("请帮我找到最适合进行数学计算的方法")
```

## 命令行使用

### 主智能体模式（推荐）
```bash
# 交互模式 - 支持自然语言对话
python framework_demo.py --master-mode

# 单任务模式
python framework_demo.py --master-mode --task "调用demo方法"
python framework_demo.py --master-mode --task "计算两个数的和"

# 带参数的任务
python framework_demo.py --master-mode --task "计算" --method-args '{"a": 15, "b": 25}'
```

### 统一模式
```bash
# 直接调用
python framework_demo.py --unified-mode --target-method "demo_method"

# 智能调用 - 支持中文描述
python framework_demo.py --unified-mode --intelligent --target-method "计算方法"
python framework_demo.py --unified-mode --intelligent --target-method "加法"

# 带参数的智能调用
python framework_demo.py --unified-mode --intelligent --target-method "计算" --method-args '{"a": 10, "b": 20}'
```

### 查看帮助和示例
```bash
# 查看详细使用示例
python framework_demo.py --help-examples

# 查看基本帮助
python framework_demo.py --help
```

## 兼容性说明
- ✅ 原有的 `LocalMethodsCaller` 和 `agent_api_call` 仍然可用，但建议迁移到新的统一接口
- ✅ 现有的本地方法装饰器 `@local_method` 无需修改
- ✅ 现有的agent配置和DID认证机制保持不变
- ⚠️ 旧的爬虫模块（如 `agent_002_local_caller_crawler`）已弃用，建议迁移到新架构
- ❌ `--crawler` 命令行参数已移除，请使用 `--unified-mode` 或 `--master-mode`

## 最佳实践

### 1. 选择合适的模式
```python
# 🎯 明确知道要调用的方法 → 使用统一调用器
caller = UnifiedCaller(sdk)
result = await caller.call_by_name("demo_method")

# 🤖 需要智能匹配和推理 → 使用统一爬虫
crawler = UnifiedCrawler(sdk)
result = await crawler.intelligent_call("计算功能")

# 📋 复杂任务或自然语言描述 → 使用主智能体（推荐）
master = MasterAgent(sdk)
result = await master.execute_task("调用加法方法计算10+20")

# 🔍 探索可用功能 → 直接运行默认发现模式
python framework_demo.py
```

### 2. 参数传递最佳实践
```python
# 位置参数
result = await crawler.intelligent_call("计算", args=[10, 20])

# 关键字参数（推荐）
result = await crawler.intelligent_call("计算", a=10, b=20)

# 混合参数
result = await crawler.intelligent_call("方法调用", args=[1, 2], message="test")

# 命令行参数格式
--method-args '{"a": 10, "b": 20}'
--method-args '{"args": [1, 2], "kwargs": {"message": "hello"}}'
```

### 3. 错误处理
```python
try:
    result = await master.execute_task("调用不存在的方法")
except Exception as e:
    print(f"任务执行失败: {e}")

    # 可以尝试搜索相似的方法
    crawler = UnifiedCrawler(sdk)
    similar = await crawler.search_resources("方法")
    print(f"相似的方法: {similar}")
```

### 4. 性能优化
```python
# 预先发现资源，避免重复发现
crawler = UnifiedCrawler(sdk)
await crawler.discover_all_resources()

# 批量调用
tasks = [
    crawler.intelligent_call("计算", a=1, b=2),
    crawler.intelligent_call("演示"),
    crawler.intelligent_call("信息查询")
]
results = await asyncio.gather(*tasks)
```

## 故障排除

### 常见问题

#### 1. 找不到方法
```python
# 问题：未找到名称为 'xxx' 的资源
# 解决方案：
crawler = UnifiedCrawler(sdk)
resources = await crawler.discover_all_resources()
print(crawler.get_resource_summary())  # 查看所有可用资源

# 尝试搜索相似的方法
results = await crawler.search_resources("部分关键词")
```

#### 2. 智能匹配失败
```python
# 问题：智能调用找不到匹配的资源
# 解决方案：
# 1. 使用更具体的描述
result = await crawler.intelligent_call("calculate_sum")  # 而不是 "计算"

# 2. 检查同义词映射
# 3. 考虑配置LLM增强
llm_config = {'type': 'openai', 'api_key': 'your-key'}
crawler_with_llm = UnifiedCrawler(sdk, llm_config=llm_config)
```

#### 3. 参数格式错误
```python
# 问题：方法参数JSON格式错误
# 正确格式：
--method-args '{"a": 15, "b": 25}'  # 关键字参数
--method-args '{"args": [1, 2]}'    # 位置参数
--method-args '{"args": [1], "kwargs": {"name": "test"}}'  # 混合参数
```

### 调试技巧
```python
# 1. 启用详细日志
import logging
logging.getLogger('anp_open_sdk_framework').setLevel(logging.DEBUG)

# 2. 检查可用资源
crawler = UnifiedCrawler(sdk)
resources = await crawler.discover_all_resources()
print(crawler.get_resource_summary())

# 3. 测试搜索功能
results = await crawler.search_resources("你的关键词")
print(f"搜索结果: {results}")

# 4. 检查方法注册
from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller
caller = LocalMethodsCaller(sdk)
methods = caller.list_all_methods()
for key, info in methods.items():
    print(f"{key}: {info['name']} - {info['description']}")
```

### 性能监控
```python
import time

# 监控任务执行时间
start_time = time.time()
result = await master.execute_task("你的任务")
execution_time = time.time() - start_time
print(f"任务执行时间: {execution_time:.2f}秒")

# 监控资源发现时间
start_time = time.time()
resources = await crawler.discover_all_resources()
discovery_time = time.time() - start_time
print(f"资源发现时间: {discovery_time:.2f}秒")
```

## 总结

### 重构成果
这个重构方案成功解决了原有架构的问题：
1. **✅ 统一调用体系** - UnifiedCaller 合并了本地方法和远程API调用
2. **✅ 统一爬虫架构** - UnifiedCrawler 整合了资源发现和调用逻辑
3. **✅ 主智能体设计** - MasterAgent 提供任务级别的统一调度
4. **✅ 基于API的架构** - 所有功能都通过统一的API接口工作
5. **🆕 LLM增强支持** - 可选的大语言模型集成，提供更智能的理解能力

### 主要优势

#### 🎯 开发者友好
- 统一的接口，减少学习成本
- 清晰的命令行参数结构
- 详细的错误提示和调试信息

#### 🚀 功能强大
- 支持自然语言任务描述
- 智能方法匹配和参数推荐
- 多层降级机制，确保调用成功率
- 可选的LLM增强，支持复杂语义理解

#### 🏗️ 架构清晰
- 分层设计，职责明确
- 插件化的资源发现器设计
- 统一的错误处理和日志记录

#### 🔄 向后兼容
- 保持现有代码可用性
- 渐进式迁移支持
- 现有配置和认证机制不变

#### 📈 易于扩展
- 支持新的资源类型（远程智能体、API端点）
- 可插拔的LLM客户端
- 灵活的同义词和匹配规则配置

### 迁移建议

1. **🎯 新项目** - 直接使用主智能体模式，享受最佳的开发体验
2. **🔄 现有项目** - 逐步迁移，先从简单的调用开始
3. **🧪 实验性功能** - 尝试LLM增强功能，体验更智能的交互
4. **📚 学习路径** - 从统一模式开始，逐步过渡到主智能体模式

### 未来发展
- 🔮 更多LLM提供商支持（Claude, Gemini, 本地模型等）
- 🌐 远程智能体发现和调用功能完善
- 📊 任务执行分析和优化建议
- 🎨 图形化界面和可视化工具

---

**需要帮助？**
- 📖 查看详细示例：`python framework_demo.py --help-examples`
- 🐛 遇到问题：启用DEBUG日志查看详细信息
- 💡 功能建议：欢迎提交Issue和Pull Request

**开始你的迁移之旅吧！** 🚀
