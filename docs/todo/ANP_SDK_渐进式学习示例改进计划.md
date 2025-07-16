# ANP SDK 渐进式学习示例改进计划

## 📋 概述

基于现有代码分析，设计5个渐进式示例来展示ANP SDK的完整能力谱系，让用户可以渐进式学习ANP的核心概念和功能。

## 🔍 现有代码分析结果

### 在 `framework_demo.py` 中发现的核心功能：
- `run_calculator_add_demo()` - 计算器API调用演示
- `run_hello_demo()` - 简单消息发送演示  
- `run_ai_crawler_demo()` - AI爬虫（单个DID开始）
- `run_ai_root_crawler_demo()` - AI爬虫（从汇总地址开始）
- `discover_and_describe_agents()` - 发现和描述Agent

### 在 `demo_tasks.py` 中发现的核心功能：
- `run_anp_tool_crawler_agent_search_ai_ad_jason()` - 远程网络爬虫
- `anptool_intelligent_crawler()` - 通用智能爬虫核心逻辑
- `run_api_demo()` - API调用演示
- `run_message_demo()` - 消息发送演示

## 🎯 5个渐进式示例设计

### 01_simple_remote_crawler - 简单远程爬虫

**学习目标**: 证明ANP可以安全地访问外部服务
**核心价值**: 远程访问能力

**仿写来源**: `demo_tasks.py` 的 `run_anp_tool_crawler_agent_search_ai_ad_jason()`

```python
# 核心功能：
# - 使用ANPTool直接爬取 https://agent-search.ai/ad.json
# - 不需要本地服务器
# - 纯HTTP请求 + DID认证
# - 调用 anptool_intelligent_crawler() 核心逻辑

# 简化要点：
# 1. 移除复杂的服务器启动逻辑
# 2. 直接使用公共智能体的DID
# 3. 简化任务定义和提示模板
# 4. 专注于远程URL访问演示
```

**配置文件**:
```yaml
# config.yaml
name: "简单远程爬虫示例"
description: "演示ANP如何安全访问外部服务"
target_url: "https://agent-search.ai/ad.json"
task: "获取智能体信息"
```

### 02_local_server_crawler - 本地服务器爬虫

**学习目标**: 证明ANP可以提供本地API服务
**核心价值**: 本地服务能力

**仿写来源**: `framework_demo.py` 的 `run_hello_demo()` + `run_calculator_add_demo()`

```python
# 核心功能：
# - 启动单个Agent的HTTP服务器
# - 用ANPTool爬取本地服务器的 /hello 和 /calculator/add API
# - 演示本地DID认证
# - 简化版的服务器启动逻辑

# 简化要点：
# 1. 只启动一个简单的Agent（如calculator或hello）
# 2. 使用最小化的服务器配置
# 3. 演示基本的GET/POST请求
# 4. 展示本地DID认证流程
```

**配置文件**:
```yaml
# config.yaml
name: "本地服务器爬虫示例"
description: "演示ANP本地服务的基础能力"
server:
  host: "localhost"
  port: 9527
agents:
  - name: "calculator"
    endpoints: ["/add", "/subtract"]
  - name: "hello"
    endpoints: ["/hello", "/info"]
```

### 03_multi_agent_crawler - 多Agent爬虫

**学习目标**: 证明ANP可以管理多个智能Agent
**核心价值**: 多Agent协作

**仿写来源**: `framework_demo.py` 的 `discover_and_describe_agents()`

```python
# 核心功能：
# - 启动多个Agent (calculator, hello, llm)
# - 用ANPTool智能发现和调用不同Agent的API
# - 从 /did_host/agents 开始发现所有Agent
# - 演示Agent间的协作

# 简化要点：
# 1. 使用现有的Agent发现机制
# 2. 展示多个Agent的API调用
# 3. 演示Agent间的消息传递
# 4. 简化Agent注册和管理逻辑
```

**配置文件**:
```yaml
# config.yaml
name: "多Agent爬虫示例"
description: "演示ANP多Agent协作能力"
discovery:
  publisher_url: "http://localhost:9527/publisher/agents"
  auto_discover: true
agents:
  - calculator
  - hello
  - llm
tasks:
  - "调用计算器进行加法运算"
  - "发送问候消息"
  - "请求LLM生成文本"
```

### 04_cross_server_crawler - 跨服务器爬虫

**学习目标**: 证明ANP分布式网络能力
**核心价值**: 分布式网络

**仿写来源**: `framework_demo.py` 的 `run_ai_root_crawler_demo()`

```python
# 核心功能：
# - 两个ANP服务器实例 (localhost:9527 和 localhost:9528)
# - 服务器A的爬虫访问服务器B的多个Agent
# - 演示跨服务器的DID认证和发现
# - 修改 run_ai_root_crawler_demo 支持不同端口

# 简化要点：
# 1. 启动两个独立的服务器实例
# 2. 配置不同的端口和数据目录
# 3. 演示跨服务器的Agent发现
# 4. 展示分布式DID认证
```

**配置文件**:
```yaml
# config.yaml
name: "跨服务器爬虫示例"
description: "演示ANP分布式网络能力"
servers:
  server_a:
    host: "localhost"
    port: 9527
    data_dir: "data_user/localhost_9527"
  server_b:
    host: "localhost"
    port: 9528
    data_dir: "data_user/localhost_9528"
cross_server_tasks:
  - "服务器A发现服务器B的Agent"
  - "跨服务器API调用"
  - "跨服务器消息传递"
```

### 05_delegated_crawler - 委托爬虫

**学习目标**: 证明ANP复杂协作和委托能力
**核心价值**: 复杂委托

**仿写来源**: `framework_demo.py` 的 `run_ai_crawler_demo()`

```python
# 核心功能：
# - 本地orchestrator_agent调用本地crawler_agent
# - crawler_agent去爬取远程服务器的Agent
# - 演示Agent委托和链式调用
# - 使用现有的Agent间调用机制

# 简化要点：
# 1. 创建orchestrator和crawler两个Agent
# 2. 演示Agent间的委托调用
# 3. 展示链式任务执行
# 4. 简化复杂的协作逻辑
```

**配置文件**:
```yaml
# config.yaml
name: "委托爬虫示例"
description: "演示ANP复杂协作和委托能力"
agents:
  orchestrator:
    role: "任务协调者"
    capabilities: ["task_planning", "agent_delegation"]
  crawler:
    role: "数据爬取者"
    capabilities: ["web_crawling", "data_extraction"]
delegation_chain:
  - "用户 -> Orchestrator: 请求数据"
  - "Orchestrator -> Crawler: 委托爬取任务"
  - "Crawler -> 远程服务器: 执行爬取"
  - "Crawler -> Orchestrator: 返回结果"
  - "Orchestrator -> 用户: 提供最终结果"
```

## 📁 目录结构设计

```
examples/
├── README.md                           # 总体说明文档
├── 01_simple_remote_crawler/
│   ├── main.py                         # 基于 run_anp_tool_crawler_agent_search_ai_ad_jason
│   ├── config.yaml                     # 简化配置
│   ├── README.md                       # 详细说明文档
│   └── requirements.txt                # 依赖列表
├── 02_local_server_crawler/
│   ├── main.py                         # 基于 run_hello_demo + run_calculator_add_demo
│   ├── config.yaml                     # 本地服务器配置
│   ├── README.md                       # 详细说明文档
│   └── requirements.txt                # 依赖列表
├── 03_multi_agent_crawler/
│   ├── main.py                         # 基于 discover_and_describe_agents
│   ├── config.yaml                     # 多Agent配置
│   ├── README.md                       # 详细说明文档
│   └── requirements.txt                # 依赖列表
├── 04_cross_server_crawler/
│   ├── main.py                         # 基于 run_ai_root_crawler_demo
│   ├── config.yaml                     # 跨服务器配置
│   ├── server_a_config.yaml           # 服务器A配置
│   ├── server_b_config.yaml           # 服务器B配置
│   ├── README.md                       # 详细说明文档
│   └── requirements.txt                # 依赖列表
└── 05_delegated_crawler/
    ├── main.py                         # 基于 run_ai_crawler_demo
    ├── config.yaml                     # 委托配置
    ├── orchestrator_config.yaml        # 协调者配置
    ├── crawler_config.yaml             # 爬虫配置
    ├── README.md                       # 详细说明文档
    └── requirements.txt                # 依赖列表
```

## 🔧 代码提取和简化策略

### 1. 通用简化原则

```python
# 移除复杂的生命周期管理
# 原代码：
async def main():
    # 复杂的Agent加载逻辑
    agent_files = glob.glob("data_user/localhost_9527/agents_config/*/agent_mappings.yaml")
    prepared_agents_info = [LocalAgentManager.load_agent_from_module(f) for f in agent_files]
    # ... 复杂的初始化逻辑

# 简化后：
async def main():
    # 直接使用预定义的Agent
    agent = create_simple_agent("calculator")
    sdk = ANP_Server(mode=ServerMode.SINGLE_AGENT, agents=[agent])
```

### 2. 配置简化

```python
# 原代码：使用复杂的统一配置
app_config = UnifiedConfig(config_file='unified_config_framework_demo.yaml')

# 简化后：使用简单的字典配置
config = {
    "name": "Simple Example",
    "host": "localhost",
    "port": 9527,
    "agents": ["calculator"]
}
```

### 3. 核心功能提取

```python
# 从 anptool_intelligent_crawler 提取核心逻辑
async def simple_crawler(url: str, task: str):
    """简化版智能爬虫"""
    anp_tool = ANPTool(user_data=get_default_user_data())
    
    # 获取URL内容
    content = await anp_tool.execute(url=url)
    
    # 简单的任务处理
    result = process_content(content, task)
    
    return result
```

## 📚 每个示例的详细设计

### 示例01: 简单远程爬虫

**文件结构**:
```
01_simple_remote_crawler/
├── main.py
├── config.yaml
├── README.md
└── requirements.txt
```

**main.py 核心代码**:

```python
import asyncio
import yaml
from anp_server_framework.anp_service import ANPTool
from anp_sdk.anp_user_data import LocalUserDataManager


async def main():
    """简单远程爬虫示例"""
    print("🚀 启动简单远程爬虫示例")

    # 加载配置
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    # 获取公共智能体数据
    user_data_manager = LocalUserDataManager()
    user_data = user_data_manager.get_user_data_by_name("公共智能体_did:wba:agent-did.com:tests:public")

    # 创建ANPTool
    anp_tool = ANPTool(user_data=user_data)

    # 爬取远程URL
    print(f"📡 正在爬取: {config['target_url']}")
    result = await anp_tool.execute(url=config['target_url'])

    # 显示结果
    print("✅ 爬取完成!")
    print(f"📄 结果: {result}")


if __name__ == "__main__":
    asyncio.run(main())
```

**README.md 内容**:
```markdown
# 简单远程爬虫示例

## 学习目标
- 了解ANP如何安全访问外部服务
- 掌握ANPTool的基本使用方法
- 理解DID认证的基本概念

## 运行步骤
1. 安装依赖: `pip install -r requirements.txt`
2. 运行示例: `python main.py`

## 核心概念
- **ANPTool**: ANP协议的HTTP客户端工具
- **DID认证**: 去中心化身份认证
- **远程访问**: 通过ANP协议访问外部服务
```

### 示例02: 本地服务器爬虫

**main.py 核心代码**:

```python
import asyncio
import threading
from anp_server.anp_server import ANP_Server
from anp_server_framework.anp_service import ANPTool


async def main():
    """本地服务器爬虫示例"""
    print("🚀 启动本地服务器爬虫示例")

    # 1. 创建简单的Agent
    agent = create_calculator_agent()

    # 2. 启动服务器
    sdk = ANP_Server(anp_users=[agent])
    server_thread = threading.Thread(target=sdk.start_server, daemon=True)
    server_thread.start()

    # 3. 等待服务器启动
    await wait_for_server("localhost", 9527)
    print("✅ 服务器启动完成")

    # 4. 使用ANPTool爬取本地API
    anp_tool = ANPTool(user_data=agent.user_data)

    # 测试计算器API
    result = await anp_tool.execute(
        url="http://localhost:9527/agent/api/calculator/add",
        method="POST",
        body={"a": 5, "b": 3}
    )

    print(f"🧮 计算结果: {result}")


def create_calculator_agent():
    """创建简单的计算器Agent"""
    # 简化的Agent创建逻辑
    pass


if __name__ == "__main__":
    asyncio.run(main())
```

### 示例03: 多Agent爬虫

**main.py 核心代码**:
```python
async def main():
    """多Agent爬虫示例"""
    print("🚀 启动多Agent爬虫示例")
    
    # 1. 创建多个Agent
    agents = [
        create_calculator_agent(),
        create_hello_agent(),
        create_llm_agent()
    ]
    
    # 2. 启动服务器
    sdk = ANP_Server(agents=agents)
    await start_server_async(sdk)
    
    # 3. 发现所有Agent
    discovery_url = "http://localhost:9527/publisher/agents"
    discovered_agents = await discover_agents(discovery_url)
    
    print(f"🔍 发现了 {len(discovered_agents)} 个Agent")
    
    # 4. 依次调用每个Agent的API
    for agent_info in discovered_agents:
        await test_agent_apis(agent_info)
    
    print("✅ 多Agent协作演示完成")
```

### 示例04: 跨服务器爬虫

**main.py 核心代码**:
```python
async def main():
    """跨服务器爬虫示例"""
    print("🚀 启动跨服务器爬虫示例")
    
    # 1. 启动两个服务器实例
    server_a = await start_server_a()  # localhost:9527
    server_b = await start_server_b()  # localhost:9528
    
    # 2. 服务器A发现服务器B的Agent
    agents_b = await discover_remote_agents("http://localhost:9528/publisher/agents")
    
    print(f"🌐 在服务器B发现了 {len(agents_b)} 个Agent")
    
    # 3. 跨服务器API调用
    for agent in agents_b:
        result = await cross_server_api_call(server_a, agent)
        print(f"🔗 跨服务器调用结果: {result}")
    
    print("✅ 跨服务器演示完成")
```

### 示例05: 委托爬虫

**main.py 核心代码**:

```python
async def main():
    """委托爬虫示例"""
    print("🚀 启动委托爬虫示例")

    # 1. 创建协调者和爬虫Agent
    orchestrator = create_orchestrator_agent()
    crawler = create_crawler_agent()

    # 2. 启动服务器
    sdk = ANP_Server(agents=[orchestrator, crawler])
    await start_server_async(sdk)

    # 3. 用户向协调者发送任务
    task = "爬取 https://agent-search.ai/ad.json 的数据"

    # 4. 协调者委托给爬虫
    result = await orchestrator.delegate_task(crawler.anp_user_id, task)

    print(f"🎯 委托任务完成: {result}")

    # 5. 展示委托链
    show_delegation_chain(orchestrator, crawler, task, result)

    print("✅ 委托爬虫演示完成")
```

## 🎯 实施计划

### 阶段1: 基础设施准备 (1-2天)
1. **创建examples目录结构**
2. **提取核心代码模块**
3. **设计通用的简化工具函数**

### 阶段2: 示例开发 (3-5天)
1. **开发示例01**: 简单远程爬虫
2. **开发示例02**: 本地服务器爬虫  
3. **开发示例03**: 多Agent爬虫
4. **开发示例04**: 跨服务器爬虫
5. **开发示例05**: 委托爬虫

### 阶段3: 文档和测试 (1-2天)
1. **编写详细的README文档**
2. **创建运行脚本和配置文件**
3. **测试所有示例的可运行性**
4. **优化用户体验**

## 📊 成功标准

### 技术标准
- ✅ 每个示例都能独立运行
- ✅ 代码简洁易懂，注释详细
- ✅ 配置文件清晰明了
- ✅ 错误处理完善

### 教育标准
- ✅ 渐进式学习路径清晰
- ✅ 每个示例都有明确的学习目标
- ✅ 核心概念解释到位
- ✅ 实际运行效果明显

### 用户体验标准
- ✅ 安装和运行步骤简单
- ✅ 输出信息友好易懂
- ✅ 文档完整准确
- ✅ 故障排除指南完善

## 🔄 后续优化

### 短期优化
1. **添加更多配置选项**
2. **增强错误处理和日志**
3. **提供更多使用场景**

### 长期优化
1. **集成到ANP SDK官方文档**
2. **制作视频教程**
3. **社区反馈收集和改进**

## 总结

这个渐进式示例改进计划通过5个精心设计的示例，展示了ANP SDK从简单到复杂的完整能力谱系：

1. **远程访问能力** - 证明ANP可以安全访问外部服务
2. **本地服务能力** - 证明ANP可以提供本地API服务  
3. **多Agent协作** - 证明ANP可以管理多个智能Agent
4. **分布式网络** - 证明ANP可以构建分布式Agent网络
5. **复杂委托** - 证明ANP可以实现复杂的Agent协作模式

通过这种渐进式的学习方式，用户可以逐步掌握ANP SDK的核心概念和高级功能，为实际项目开发打下坚实基础。
