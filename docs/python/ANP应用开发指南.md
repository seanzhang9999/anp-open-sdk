# ANP应用开发指南

## 📋 目录

1. [ANP SDK概述](#anp-sdk概述)
2. [快速开始](#快速开始)
3. [核心概念](#核心概念)
4. [开发模式](#开发模式)
5. [Agent间通信](#agent间通信)
6. [共享DID模式](#共享did模式)
7. [配置管理](#配置管理)
8. [数据存储](#数据存储)
9. [部署运行](#部署运行)
10. [最佳实践](#最佳实践)
11. [API参考](#api参考)

---

## ANP SDK概述

ANP (Agent Network Protocol) SDK是一个基于DID (Decentralized Identifier) 的智能体网络协议开发框架。它提供了完整的智能体创建、管理、通信和部署解决方案。

### 🏗️ 核心架构

ANP SDK采用分层架构设计：

```
┌─────────────────────┐    ┌──────────────────┬─────────────────┐    ┌─────────────────────┐
│                     │    │   anp_servicepoint│   anp_runtime   │    │                     │
│                     │    │     (服务处理)     │   (Agent运行时)  │    │   应用层             │
│     anp_server      │    │                  │                 │    │                     │
│     (服务器)         │    │────────────────────────────────────│    │    Agent            │
│                     │    │       anp_foundation               │    │                     │
│                     │    │         (基础设施)                  │    │                     │
└─────────────────────┘    └────────────────────────────────────┘    └─────────────────────┘

```

### 🔧 核心组件

1. **anp_foundation**: DID认证及用户管理基础能力
2. **anp_servicepoint**: 平台无关的ANP DID节点服务能力
3. **anp_server**: 基线样例服务器
4. **anp_runtime**: Agent运行时环境，通过装饰器模式加载开发者代码为Agent
5. **data_user**: 所有用户数据的读写地址

---

## 快速开始

### 🚀 5分钟创建第一个Agent

#### 1. 环境准备

```bash
# 克隆项目
git clone https://github.com/seanzhang9999/anp-open-sdk.git
cd anp-open-sdk

# 安装激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 使用Poetry安装
poetry install && poetry shell

# 配置.env
copy .env.example .env


```

#### 2. 创建简单Agent

```python
# my_first_agent.py
import asyncio
from anp_runtime.agent_decorator import agent_class, class_api


@agent_class(
    name="我的第一个Agent",
    description="一个简单的问候Agent",
    did="did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
    shared=False
)
class HelloAgent:
    @class_api("/hello", auto_wrap=True)
    async def hello_api(self, name: str = "世界"):
        """问候API"""
        return {"message": f"你好, {name}!"}

    @class_api("/info")
    async def info_api(self, request_data, request):
        """信息API"""
        return {
            "agent_name": "我的第一个Agent",
            "version": "1.0.0",
            "status": "运行中"
        }


# 创建并运行Agent
async def main():
    agent = HelloAgent()
    print(f"Agent '{agent.agent.name}' 创建成功!")

    # 启动服务器
    from anp_server.baseline.anp_server_baseline import ANP_Server
    server = ANP_Server()
    server.start_server()


if __name__ == "__main__":
    asyncio.run(main())
```

#### 3. 运行Agent

```bash
python my_first_agent.py
```

#### 4. 测试API

**重要**: ANP系统使用DID认证机制，不支持直接的HTTP调用。所有API调用都必须通过ANP客户端进行：

```python
# 使用ANP客户端测试API
from anp_runtime.anp_service.agent_api_call import agent_api_call_post

# 测试问候API
result = await agent_api_call_post(
    caller_agent="did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1",
    target_agent="did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
    api_path="/hello",
    params={"name": "开发者"}
)
print(result)  # {"message": "你好, 开发者!"}
```

**为什么必须使用ANP客户端？**
- **DID身份验证**: 确保调用方身份合法
- **请求签名和加密**: 保证通信安全
- **正确的消息格式组装**: 符合ANP协议规范

---

## 核心概念

### 🆔 DID (Decentralized Identifier)

DID是ANP系统中每个用户的唯一标识符，格式为：
```
did:wba:localhost%3A9527:wba:user:27c0b1d11180f973
```

- `did`: 协议标识
- `wba`: 方法名
- `localhost%3A9527`: 主机和端口（URL编码）
- `wba`: 路径段
- `user`: 用户类型
- `27c0b1d11180f973`: 唯一ID

### 🤖 Agent

Agent是ANP系统中的基本执行单元，具有以下特征：

- **身份**: 每个Agent都有唯一的DID
- **能力**: 通过API和消息处理器提供服务
- **通信**: 可以与其他Agent进行API调用和消息传递
- **状态**: 维护自己的数据和配置

### 🔗 API调用

Agent间通过HTTP API进行同步通信：

```python
from anp_runtime.anp_service.agent_api_call import agent_api_call_post

result = await agent_api_call_post(
    caller_agent="did:wba:localhost%3A9527:wba:user:caller",
    target_agent="did:wba:localhost%3A9527:wba:user:target",
    api_path="/calculate",
    params={"a": 10, "b": 20}
)
```

### 💬 消息传递

Agent间通过消息进行异步通信：

```python
from anp_runtime.anp_service.agent_message_p2p import agent_msg_post

result = await agent_msg_post(
    caller_agent="did:wba:localhost%3A9527:wba:user:sender",
    target_agent="did:wba:localhost%3A9527:wba:user:receiver",
    content="Hello, Agent!",
    message_type="text"
)
```

---

## 开发模式

ANP SDK支持多种开发模式，适应不同的开发需求：

### 🎨 装饰器模式（推荐）

使用Python装饰器快速创建Agent：

#### 面向对象风格

```python
from anp_runtime.agent_decorator import agent_class, class_api, class_message_handler


@agent_class(
    name="计算器Agent",
    description="提供基本计算功能",
    did="did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
    shared=False
)
class CalculatorAgent:
    @class_api("/add", auto_wrap=True)
    async def add_api(self, a: float, b: float):
        """加法计算"""
        return {"result": a + b, "operation": "add"}

    @class_api("/multiply", auto_wrap=True)
    async def multiply_api(self, a: float, b: float):
        """乘法计算"""
        return {"result": a * b, "operation": "multiply"}

    @class_message_handler("text")
    async def handle_text(self, content: str, sender_id: str = None):
        """处理文本消息"""
        if '+' in content:
            try:
                parts = content.split('+')
                a, b = float(parts[0].strip()), float(parts[1].strip())
                result = a + b
                return {"reply": f"计算结果: {a} + {b} = {result}"}
            except:
                return {"reply": "计算格式错误，请使用 'a + b' 格式"}
        return {"reply": f"收到消息: {content}"}
```

#### 函数式风格

```python
from anp_runtime.agent_decorator import create_agent, agent_api, agent_message_handler

# 创建Agent实例
agent = create_agent(
    "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
    "函数式计算器"
)


@agent_api(agent, "/divide", auto_wrap=True)
async def divide_api(a: float, b: float):
    """除法计算"""
    if b == 0:
        return {"error": "除数不能为零"}
    return {"result": a / b, "operation": "divide"}


@agent_message_handler(agent, "command")
async def handle_command(content: str):
    """处理命令消息"""
    return {"reply": f"执行命令: {content}"}
```

### 📋 配置模式

通过YAML配置文件定义Agent：

#### agent_mappings.yaml

```yaml
name: "配置式计算器"
did: "did:wba:localhost%3A9527:wba:user:28cddee0fade0258"
description: "通过配置文件创建的计算器Agent"
version: "1.0.0"

api:
  - path: "/subtract"
    handler: "subtract_handler"
    description: "减法计算"
  - path: "/power"
    handler: "power_handler"
    description: "幂运算"

message_handlers:
  - type: "text"
    handler: "handle_message"
```

#### agent_handlers.py

```python
async def subtract_handler(request_data, request):
    """减法处理器"""
    params = request_data.get('params', {})
    a = params.get('a', 0)
    b = params.get('b', 0)
    return {"result": a - b, "operation": "subtract"}

async def power_handler(request_data, request):
    """幂运算处理器"""
    params = request_data.get('params', {})
    base = params.get('base', 1)
    exponent = params.get('exponent', 1)
    return {"result": base ** exponent, "operation": "power"}

async def handle_message(msg_data):
    """消息处理器"""
    content = msg_data.get('content', '')
    return {"reply": f"配置式Agent收到: {content}"}
```

### 🔧 自定义注册模式（推荐高级用户）

通过`agent_register.py`文件实现完全自定义的Agent注册逻辑：

#### 目录结构

```
agent_calculator/
├── agent_mappings.yaml    # Agent基本配置
├── agent_handlers.py      # 处理函数实现
└── agent_register.py      # 自定义注册逻辑
```

#### agent_mappings.yaml

```yaml
name: "自定义计算器"
did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973"
description: "通过自定义注册逻辑创建的计算器Agent"
version: "1.0.0"
```

#### agent_handlers.py

```python
import logging
logger = logging.getLogger(__name__)

async def add(request_data, request):
    """计算两个数的和"""
    try:
        params = request_data.get('params', {})
        a = float(params.get('a', 0))
        b = float(params.get('b', 0))
        
        result = a + b
        logger.info(f"Calculator Agent: {a} + {b} = {result}")
        return {"result": result}
    except (ValueError, TypeError) as e:
        logger.error(f"Calculator Agent: 参数错误 - {e}")
        return {
            "error": f"参数错误: {str(e)}",
            "expected_format": {"params": {"a": 2.5, "b": 3.7}}
        }

async def handle_text_message(content):
    """处理文本消息"""
    logger.info(f"Calculator Agent 收到消息: {content}")
    return {"reply": f"Calculator Agent: 收到消息 '{content}'，我可以帮您进行数学计算！"}
```

#### agent_register.py

```python
import logging
from anp_runtime.agent_decorator import agent_api, agent_message_handler

logger = logging.getLogger(__name__)


def register(agent):
    """自定义Agent注册函数
    
    Args:
        agent: 由系统创建的Agent实例
    """
    logger.info(f"开始自定义注册Agent: {agent.name}")

    # 导入处理函数
    from . import agent_handlers

    # 1. 注册API - 使用装饰器方式
    @agent_api(agent, "/add", auto_wrap=True)
    async def add_api_wrapper(request_data, request):
        """加法API包装器"""
        return await agent_handlers.add(request_data, request)

    # 2. 注册更多API
    @agent_api(agent, "/multiply", auto_wrap=True)
    async def multiply_api(request_data, request):
        """乘法API - 直接在register中定义"""
        try:
            params = request_data.get('params', {})
            a = float(params.get('a', 1))
            b = float(params.get('b', 1))
            result = a * b
            logger.info(f"Calculator Agent: {a} × {b} = {result}")
            return {"result": result, "operation": "multiply"}
        except Exception as e:
            return {"error": str(e)}

    # 3. 注册消息处理器
    @agent_message_handler(agent, "text")
    async def text_message_wrapper(msg_data):
        """文本消息处理器包装器"""
        content = msg_data.get('content', '')
        return await agent_handlers.handle_text_message(content)

    # 4. 可以添加更多自定义逻辑
    # 比如初始化数据库连接、设置定时任务等

    logger.info(f"Agent {agent.name} 自定义注册完成")
    logger.info(f"  - 注册API: /add, /multiply")
    logger.info(f"  - 注册消息处理器: text")
```

**自定义注册模式的优势**：

1. **完全控制**: 对Agent注册过程有完全的控制权
2. **动态逻辑**: 可以根据条件动态注册不同的API
3. **复杂初始化**: 支持复杂的初始化逻辑
4. **灵活组合**: 可以组合多种注册方式

**使用场景**：
- 需要根据配置动态注册API
- 需要复杂的初始化逻辑
- 需要与外部系统集成
- 需要高度定制化的Agent行为

### 🔄 生命周期管理模式（推荐进阶用户）

通过`initialize_agent`和`cleanup_agent`函数管理Agent的生命周期：

#### 目录结构

```
agent_llm/
├── agent_mappings.yaml    # Agent配置文件
└── agent_handlers.py      # 包含生命周期函数的处理器
```

#### agent_mappings.yaml

```yaml
name: "LLM智能助手"
did: "did:wba:localhost%3A9527:wba:user:5fea49e183c6c211"
description: "基于大语言模型的智能助手Agent"
version: "1.0.0"
```

#### agent_handlers.py

```python
import logging
from anp_runtime.agent_decorator import agent_api, agent_message_handler

logger = logging.getLogger(__name__)

# 全局变量存储Agent状态
llm_client = None
agent_config = None


async def initialize_agent(agent):
    """Agent初始化函数
    
    Args:
        agent: 由系统创建的Agent实例
    """
    global llm_client, agent_config
    logger.info(f"初始化Agent: {agent.name}")

    try:
        # 1. 初始化LLM客户端
        from openai import AsyncOpenAI
        from anp_foundation.config import get_global_config

        config = get_global_config()
        llm_client = AsyncOpenAI(
            api_key=config.llm.api_key,
            base_url=config.llm.api_url
        )

        # 2. 保存Agent配置
        agent_config = {
            "model": config.llm.default_model,
            "max_tokens": config.llm.max_tokens,
            "system_prompt": config.llm.system_prompt
        }

        # 3. 注册API处理器
        @agent_api(agent, "/chat", auto_wrap=True)
        async def chat_api(message: str, temperature: float = 0.7):
            """聊天API"""
            return await handle_chat_request(message, temperature)

        @agent_api(agent, "/summarize", auto_wrap=True)
        async def summarize_api(text: str, max_length: int = 100):
            """文本摘要API"""
            return await handle_summarize_request(text, max_length)

        # 4. 注册消息处理器
        @agent_message_handler(agent, "text")
        async def text_message_handler(msg_data):
            """处理文本消息"""
            content = msg_data.get('content', '')
            return await handle_chat_request(content)

        logger.info(f"Agent {agent.name} 初始化完成")
        logger.info(f"  - LLM模型: {agent_config['model']}")
        logger.info(f"  - 注册API: /chat, /summarize")

    except Exception as e:
        logger.error(f"Agent初始化失败: {e}")
        raise


async def cleanup_agent():
    """Agent清理函数"""
    global llm_client, agent_config
    logger.info("开始清理Agent资源...")

    try:
        # 清理LLM客户端
        if llm_client:
            await llm_client.close()
            llm_client = None
            logger.info("LLM客户端已关闭")

        # 清理配置
        agent_config = None

        logger.info("Agent资源清理完成")

    except Exception as e:
        logger.error(f"Agent清理失败: {e}")


async def handle_chat_request(message: str, temperature: float = 0.7):
    """处理聊天请求"""
    global llm_client, agent_config

    if not llm_client:
        return {"error": "LLM客户端未初始化"}

    try:
        # 构建消息
        messages = [
            {"role": "system", "content": agent_config["system_prompt"]},
            {"role": "user", "content": message}
        ]

        # 调用LLM API
        response = await llm_client.chat.completions.create(
            model=agent_config["model"],
            messages=messages,
            max_tokens=agent_config["max_tokens"],
            temperature=temperature
        )

        reply = response.choices[0].message.content
        logger.info(f"LLM响应: {reply[:50]}...")

        return {
            "reply": reply,
            "model": agent_config["model"],
            "tokens_used": response.usage.total_tokens if response.usage else 0
        }

    except Exception as e:
        logger.error(f"LLM调用失败: {e}")
        return {"error": f"LLM调用失败: {str(e)}"}


async def handle_summarize_request(text: str, max_length: int = 100):
    """处理文本摘要请求"""
    global llm_client, agent_config

    if not llm_client:
        return {"error": "LLM客户端未初始化"}

    try:
        # 构建摘要提示
        prompt = f"请将以下文本总结为不超过{max_length}字的摘要：\n\n{text}"
        messages = [
            {"role": "system", "content": "你是一个专业的文本摘要助手。"},
            {"role": "user", "content": prompt}
        ]

        # 调用LLM API
        response = await llm_client.chat.completions.create(
            model=agent_config["model"],
            messages=messages,
            max_tokens=max_length * 2,  # 给一些余量
            temperature=0.3  # 摘要任务使用较低温度
        )

        summary = response.choices[0].message.content
        logger.info(f"生成摘要: {summary[:30]}...")

        return {
            "summary": summary,
            "original_length": len(text),
            "summary_length": len(summary),
            "compression_ratio": round(len(summary) / len(text), 2)
        }

    except Exception as e:
        logger.error(f"摘要生成失败: {e}")
        return {"error": f"摘要生成失败: {str(e)}"}
```

**生命周期管理模式的优势**：

1. **资源管理**: 自动管理外部资源的初始化和清理
2. **状态维护**: 维护Agent运行期间的状态信息
3. **错误恢复**: 支持初始化失败时的错误处理
4. **优雅关闭**: 确保资源正确释放

**使用场景**：
- 需要连接数据库或外部服务
- 需要维护复杂的内部状态
- 需要定时任务或后台处理
- 需要资源池管理（如连接池）

**生命周期函数说明**：
- `initialize_agent(agent)`: Agent启动时调用，用于初始化资源
- `cleanup_agent()`: Agent关闭时调用，用于清理资源

---

## Agent间通信

### 🔄 API调用示例

#### 调用方Agent

```python
@agent_class(name="调用方Agent", did="caller_did")
class CallerAgent:
    @class_api("/call_calculator")
    async def call_calculator_api(self, request_data, request):
        # 调用计算器Agent的加法API
        result = await agent_api_call_post(
            caller_agent=self.agent.anp_user_did,
            target_agent="did:wba:localhost%3A9527:wba:user:calculator",
            api_path="/add",
            params={"a": 15, "b": 25}
        )
        return {"calculation_result": result}
```

#### 被调用方Agent

```python
@agent_class(name="计算器Agent", did="calculator_did")
class CalculatorAgent:
    @class_api("/add", auto_wrap=True)
    async def add_api(self, a: float, b: float):
        return {"result": a + b}
```

### 💬 消息传递示例

#### 发送方Agent

```python
@agent_class(name="发送方Agent", did="sender_did")
class SenderAgent:
    @class_api("/send_greeting")
    async def send_greeting_api(self, request_data, request):
        # 发送问候消息
        result = await agent_msg_post(
            caller_agent=self.agent.anp_user_did,
            target_agent="did:wba:localhost%3A9527:wba:user:receiver",
            content="Hello from sender!",
            message_type="text"
        )
        return {"message_sent": True, "response": result}
```

#### 接收方Agent

```python
@agent_class(name="接收方Agent", did="receiver_did")
class ReceiverAgent:
    @class_message_handler("text")
    async def handle_text_message(self, content: str, sender_id: str = None):
        return {"reply": f"收到来自 {sender_id} 的消息: {content}"}
```

---

## 共享DID模式

共享DID模式允许多个Agent共享同一个DID，通过路径前缀区分不同的服务。

### 🔗 配置共享DID

#### 主Agent（处理消息）

```python
@agent_class(
    name="天气主服务",
    description="天气信息主服务",
    did="did:wba:localhost%3A9527:wba:user:5fea49e183c6c211",
    shared=True,
    prefix="/weather",
    primary_agent=True  # 主Agent，可以处理消息
)
class WeatherMainAgent:
    @class_api("/current", auto_wrap=True)
    async def current_weather(self, city: str = "北京"):
        """获取当前天气"""
        return {
            "city": city,
            "temperature": "22°C",
            "condition": "晴天",
            "humidity": "65%"
        }
    
    @class_message_handler("text")
    async def handle_weather_message(self, content: str):
        """处理天气相关消息"""
        return {"reply": f"天气服务收到: {content}"}
```

#### 辅助Agent（仅提供API）

```python
@agent_class(
    name="天气预报服务",
    description="天气预报辅助服务",
    did="did:wba:localhost%3A9527:wba:user:5fea49e183c6c211",  # 相同DID
    shared=True,
    prefix="/forecast",
    primary_agent=False  # 辅助Agent，不处理消息
)
class WeatherForecastAgent:
    @class_api("/daily", auto_wrap=True)
    async def daily_forecast(self, city: str = "北京", days: int = 7):
        """获取每日预报"""
        forecast = []
        for i in range(days):
            forecast.append({
                "date": f"2024-01-{15+i:02d}",
                "high": f"{20+i}°C",
                "low": f"{10+i}°C",
                "condition": "晴天"
            })
        return {"city": city, "forecast": forecast}
```

### 🌐 调用共享DID服务

```python
# 调用天气当前信息
result1 = await agent_api_call_post(
    caller_agent="caller_did",
    target_agent="did:wba:localhost%3A9527:wba:user:5fea49e183c6c211",
    api_path="/weather/current",  # 路径包含prefix
    params={"city": "上海"}
)

# 调用天气预报信息
result2 = await agent_api_call_post(
    caller_agent="caller_did", 
    target_agent="did:wba:localhost%3A9527:wba:user:5fea49e183c6c211",
    api_path="/forecast/daily",   # 路径包含prefix
    params={"city": "深圳", "days": 3}
)
```

---

## 配置管理

### 📄 统一配置文件

ANP SDK使用`unified_config_framework_demo.yaml`作为主配置文件：

```yaml
# ANP SDK 统一配置文件
anp_sdk:
  debug_mode: true
  host: localhost
  port: 9527
  user_did_path: '{APP_ROOT}/data_user/localhost_9527/anp_users'
  user_hosted_path: '{APP_ROOT}/data_user/localhost_9527/anp_users_hosted'
  token_expire_time: 3600
  user_did_key_id: key-1

# DID配置
did_config:
  method: wba
  format_template: did:{method}:{host}%3A{port}:{method}:{user_type}:{user_id}
  hosts:
    localhost: 9527
    user.localhost: 9527
    service.localhost: 9527

# 日志配置
log_settings:
  log_level: Info
  detail:
    file: "{APP_ROOT}/tmp_log/app.log"
    max_size: 100

# LLM配置
llm:
  api_url: https://api.302ai.cn/v1
  default_model: deepseek/deepseek-chat-v3-0324:free
  max_tokens: 512
  system_prompt: 你是一个智能助手，请根据用户的提问进行专业、简洁的回复。
```

### 🔧 配置使用

```python
from anp_foundation.config import get_global_config, set_global_config, UnifiedConfig

# 加载配置
config = UnifiedConfig(config_file='unified_config_framework_demo.yaml')
set_global_config(config)

# 使用配置
config = get_global_config()
host = config.anp_sdk.host
port = config.anp_sdk.port
debug_mode = config.anp_sdk.debug_mode
```

---

## 数据存储

### 📁 目录结构

```
data_user/
└── localhost_9527/
    ├── agents_config/          # Agent配置
    │   ├── agent_001/
    │   │   ├── agent_mappings.yaml
    │   │   └── agent_handlers.py
    │   └── agent_calculator/
    │       ├── agent_mappings.yaml
    │       └── agent_handlers.py
    ├── anp_users/             # 用户DID数据
    │   ├── user_27c0b1d11180f973/
    │   │   ├── did_document.json
    │   │   ├── agent_cfg.yaml
    │   │   ├── key-1_private.pem
    │   │   ├── key-1_public.pem
    │   │   ├── private_key.pem
    │   │   ├── public_key.pem
    │   │   ├── ad.json
    │   │   ├── api_interface.yaml
    │   │   └── api_interface.json
    │   └── user_28cddee0fade0258/
    ├── anp_users_hosted/      # 托管用户数据
    ├── hosted_did_queue/      # 托管DID队列
    └── hosted_did_results/    # 托管DID结果
```

### 📋 用户数据文件

#### did_document.json
```json
{
  "id": "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
  "verificationMethod": [
    {
      "id": "key-1",
      "type": "EcdsaSecp256k1VerificationKey2019",
      "publicKeyPem": "-----BEGIN PUBLIC KEY-----\n..."
    }
  ],
  "service": [
    {
      "id": "agent-service",
      "type": "AgentService",
      "serviceEndpoint": "http://localhost:9527/wba/user/..."
    }
  ]
}
```

#### agent_cfg.yaml
```yaml
name: "计算器Agent"
unique_id: "27c0b1d11180f973"
did: "did:wba:localhost%3A9527:wba:user:27c0b1d11180f973"
type: "user"
description: "提供基本计算功能的Agent"
version: "1.0.0"
created_at: "2024-01-15 10:30:00"
```

---

## 部署运行

### 🚀 完整应用示例

基于`examples/flow_anp_agent/flow_anp_agent.py`的完整应用：

```python
import asyncio
import logging
from anp_foundation.config import UnifiedConfig, set_global_config
from anp_foundation.utils.log_base import setup_logging
from anp_server.baseline.anp_server_baseline import ANP_Server
from anp_runtime.agent_manager import AgentManager, LocalAgentManager
from anp_runtime.agent_decorator import agent_class, class_api, class_message_handler

# 配置初始化
app_config = UnifiedConfig(config_file='unified_config_framework_demo.yaml')
set_global_config(app_config)
setup_logging()
logger = logging.getLogger(__name__)


async def create_agents():
    """创建Agent实例"""
    # 清理之前的状态
    AgentManager.clear_all_agents()

    created_agents = []

    # 1. 从配置文件加载Agent
    agent_files = glob.glob("data_user/localhost_9527/agents_config/*/agent_mappings.yaml")
    for agent_file in agent_files:
        try:
            anp_agent, handler_module, share_did_config = await LocalAgentManager.load_agent_from_module(agent_file)
            if anp_agent:
                created_agents.append(anp_agent)
        except Exception as e:
            logger.error(f"加载Agent失败 {agent_file}: {e}")

    # 2. 代码生成的Agent
    @agent_class(
        name="代码生成计算器",
        description="提供基本的计算功能",
        did="did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
        shared=False
    )
    class CalculatorAgent:
        @class_api("/add", auto_wrap=True)
        async def add_api(self, a: float, b: float):
            """加法计算API"""
            result = a + b
            logger.debug(f"计算: {a} + {b} = {result}")
            return {"result": result, "operation": "add", "inputs": [a, b]}

        @class_message_handler("text")
        async def handle_calc_message(self, content: str):
            """处理计算消息"""
            logger.debug(f"计算器收到消息: {content}")
            if '+' in content:
                try:
                    parts = content.split('+')
                    if len(parts) == 2:
                        a = float(parts[0].strip())
                        b = float(parts[1].strip())
                        result = a + b
                        return {"reply": f"计算结果: {a} + {b} = {result}"}
                except:
                    pass
            return {"reply": f"计算器收到: {content}。支持格式如 '5 + 3'"}

    # 实例化Agent
    calc_agent = CalculatorAgent().agent
    created_agents.append(calc_agent)

    return created_agents


async def main():
    """主函数"""
    logger.info("🚀 启动ANP Agent系统...")

    # 初始化Agent管理器
    AgentManager.initialize_router()

    # 创建Agent
    all_agents = await create_agents()

    if not all_agents:
        logger.error("没有创建任何Agent，退出")
        return

    # 生成接口文档
    processed_dids = set()
    for agent in all_agents:
        if hasattr(agent, 'anp_user'):
            did = agent.anp_user_did
            if did not in processed_dids:
                await LocalAgentManager.generate_and_save_agent_interfaces(agent)
                processed_dids.add(did)
                logger.info(f"✅ 为 DID '{did}' 生成接口文档")

    # 启动服务器
    logger.info("✅ 所有Agent创建完成，启动服务器...")
    svr = ANP_Server()
    config = get_global_config()
    host = config.anp_sdk.host
    port = config.anp_sdk.port

    # 启动服务器
    await launch_anp_server(host, port, svr)
    logger.info(f"✅ 服务器启动成功 {host}:{port}")

    # 显示Agent状态
    logger.info("\n📊 Agent管理器状态:")
    agents_info = AgentManager.list_agents()
    for did, agent_dict in agents_info.items():
        logger.info(f"  DID: {did} 共有 {len(agent_dict)} 个Agent")
        for agent_name, agent_info in agent_dict.items():
            mode = "共享" if agent_info['shared'] else "独占"
            primary = " (主)" if agent_info.get('primary_agent') else ""
            prefix = f" prefix:{agent_info['prefix']}" if agent_info['prefix'] else ""
            logger.info(f"    - {agent_name}: {mode}{primary}{prefix}")

    # 等待用户输入
    input("\n🔥 系统运行中，按任意键停止...")

    # 停止服务器
    if hasattr(svr, 'stop_server'):
        svr.stop_server()
        logger.info("✅ 服务器已停止")


async def launch_anp_server(host, port, svr):
    """启动ANP服务器"""
    import threading
    import time
    import socket

    def run_server():
        svr.start_server()

    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # 等待服务器启动
    def wait_for_port(host, port, timeout=10.0):
        start = time.time()
        while time.time() - start < timeout:
            try:
                with socket.create_connection((host, port), timeout=1):
                    return True
            except (OSError, ConnectionRefusedError):
                time.sleep(0.2)
        raise RuntimeError(f"服务器在 {timeout} 秒内未启动")

    wait_for_port(host, port, timeout=15)


if __name__ == "__main__":
    asyncio.run(main())
```

### 🔧 运行步骤

1. **准备环境**
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装依赖
poetry install
```

2. **配置文件**
确保`unified_config_framework_demo.yaml`配置正确

3. **运行应用**
```bash
python examples/flow_anp_agent/flow_anp_agent.py
```

4. **测试API**

```python
# 使用ANP客户端测试API
from anp_runtime.anp_service.agent_api_call import agent_api_call_post

# 测试计算器API
result = await agent_api_call_post(
    caller_agent="did:wba:localhost%3A9527:wba:user:3ea884878ea5fbb1",
    target_agent="did:wba:localhost%3A9527:wba:user:27c0b1d11180f973",
    api_path="/add",
    params={"a": 10, "b": 20}
)
print(result)  # {"result": 30}
```

**重要**: ANP系统使用DID认证机制，不支持直接的HTTP调用。所有API调用都必须通过ANP客户端进行，这样可以确保：
- DID身份验证
- 请求签名和加密
- 正确的消息格式组装
REPLACE

---

## 最佳实践

### 🎯 Agent设计原则

1. **单一职责**: 每个Agent专注于特定功能
2. **松耦合**: Agent间通过标准API通信
3. **可扩展**: 支持动态添加新功能
4. **容错性**: 处理异常情况和错误恢复

### 🔒 安全考虑

1. **DID验证**: 确保DID格式正确和唯一性
2. **权限控制**: 实现适当的访问控制
3. **数据加密**: 敏感数据加密存储
4. **输入验证**: 验证所有输入参数

### 📈 性能优化

1. **异步处理**: 使用async/await处理并发
2. **连接池**: 复用HTTP连接
3. **缓存策略**: 缓存频繁访问的数据
4. **资源管理**: 及时释放资源

### 🐛 调试技巧

1. **日志记录**: 详细的日志记录
```python
import logging
logger = logging.getLogger(__name__)

@class_api("/debug_api")
async def debug_api(self, request_data, request):
    logger.debug(f"收到请求: {request_data}")
    try:
        result = process_request(request_data)
        logger.info(f"处理成功: {result}")
        return result
    except Exception as e:
        logger.error(f"处理失败: {e}")
        raise
```

2. **状态监控**: 监控Agent状态

```python
@class_api("/health")
async def health_check(self, request_data, request):
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_name": self.agent.name,
        "did": self.agent.anp_user_did
    }
```

### 🔄 错误处理

```python
@class_api("/safe_api", auto_wrap=True)
async def safe_api(self, data: str):
    try:
        # 业务逻辑
        result = process_data(data)
        return {"success": True, "data": result}
    except ValueError as e:
        return {"success": False, "error": "参数错误", "message": str(e)}
    except Exception as e:
        logger.error(f"未预期错误: {e}")
        return {"success": False, "error": "内部错误"}
```

---

## API参考

### 🎨 装饰器API

#### @agent_class
创建Agent类装饰器

```python
@agent_class(
    name: str,                    # Agent名称
    description: str = "",        # Agent描述
    version: str = "1.0.0",      # 版本号
    did: str = None,             # DID标识
    shared: bool = False,        # 是否共享DID
    prefix: str = None,          # API路径前缀
    primary_agent: bool = True   # 是否为主Agent
)
```

#### @class_api
类方法API装饰器

```python
@class_api(
    path: str,                   # API路径
    methods: List[str] = None,   # HTTP方法
    description: str = None,     # API描述
    auto_wrap: bool = True       # 自动参数包装
)
```

#### @class_message_handler
类方法消息处理器装饰器

```python
@class_message_handler(
    msg_type: str,              # 消息类型
    description: str = None,    # 处理器描述
    auto_wrap: bool = True      # 自动参数包装
)
```

### 🔧 工具函数API

#### agent_api_call_post
Agent API调用

```python
async def agent_api_call_post(
    caller_agent: str,          # 调用方DID
    target_agent: str,          # 目标Agent DID
    api_path: str,              # API路径
    params: Dict[str, Any]      # 参数字典
) -> Dict[str, Any]:           # 返回结果
```

#### agent_msg_post
Agent消息发送

```python
async def agent_msg_post(
    caller_agent: str,          # 发送方DID
    target_agent: str,          # 接收方DID
    content: str,               # 消息内容
    message_type: str = "text"  # 消息类型
) -> Dict[str, Any]:           # 返回结果
```

### 🎯 参数自动提取 (auto_wrap=True)

当使用`auto_wrap=True`时，ANP SDK会自动从请求中提取参数并映射到函数参数：

```python
@class_api("/calculate", auto_wrap=True)
async def calculate_api(self, operation: str, a: float, b: float, precision: int = 2):
    """
    自动参数提取示例
    - operation: 运算类型 (必需)
    - a, b: 操作数 (必需)
    - precision: 精度 (可选，默认2)
    """
    if operation == "add":
        result = a + b
    elif operation == "multiply":
        result = a * b
    else:
        return {"error": f"不支持的运算: {operation}"}
    
    return {"result": round(result, precision)}

# 调用示例
result = await agent_api_call_post(
    caller_agent="caller_did",
    target_agent="target_did", 
    api_path="/calculate",
    params={
        "operation": "add",
        "a": 10.5,
        "b": 20.3,
        "precision": 1
    }
)
# 返回: {"result": 30.8}
```

### 🛡️ 错误处理最佳实践

```python
from anp_runtime.anp_service.anp_tool import wrap_business_handler


@class_api("/robust_api", auto_wrap=True)
async def robust_api(self, data: str, validate: bool = True):
    """健壮的API示例"""
    try:
        # 输入验证
        if validate and not data:
            return {
                "success": False,
                "error": "INVALID_INPUT",
                "message": "data参数不能为空"
            }

        # 业务逻辑
        processed_data = process_complex_data(data)

        return {
            "success": True,
            "data": processed_data,
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        return {
            "success": False,
            "error": "VALIDATION_ERROR",
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"API处理异常: {e}", exc_info=True)
        return {
            "success": False,
            "error": "INTERNAL_ERROR",
            "message": "内部处理错误"
        }
```

### 🔄 本地方法调用

ANP SDK支持本地方法调用，无需网络通信：

```python
from anp_runtime.local_service.local_methods_caller import call_local_method


@class_api("/local_call_demo")
async def local_call_demo(self, request_data, request):
    """本地方法调用示例"""
    # 调用本地注册的方法
    result = await call_local_method(
        method_name="calculator.add",
        params={"a": 10, "b": 20}
    )
    return {"local_result": result}


# 注册本地方法
from anp_runtime.local_service.local_methods_decorators import local_method


@local_method("calculator.add")
async def local_add(a: float, b: float):
    """本地加法方法"""
    return {"result": a + b}
```

### 🏗️ 管理器API

#### AgentManager
Agent管理器

```python
class AgentManager:
    @classmethod
    def create_agent(cls, anp_user: ANPUser, name: str, 
                    shared: bool = False, prefix: str = None, 
                    primary_agent: bool = False) -> Agent
    
    @classmethod
    def get_agent_info(cls, did: str, agent_name: str = None) -> Dict
    
    @classmethod
    def list_agents(cls) -> Dict[str, Any]
    
    @classmethod
    def clear_all_agents(cls)
```

#### LocalAgentManager
本地Agent管理器

```python
class LocalAgentManager:
    @staticmethod
    async def load_agent_from_module(yaml_path: str) -> Tuple
    
    @staticmethod
    async def generate_and_save_agent_interfaces(agent: Agent)
```

---

## 🎉 总结

ANP SDK提供了完整的智能体开发框架，支持：

- ✅ **快速开发**: 装饰器模式简化Agent创建
- ✅ **灵活配置**: 支持代码和配置文件两种模式
- ✅ **标准通信**: 基于DID的标准化通信协议
- ✅ **共享资源**: 共享DID模式支持服务组合
- ✅ **完整生态**: 从开发到部署的完整工具链

开始你的ANP应用开发之旅吧！🚀

---

## 📚 更多资源

- [GitHub仓库](https://github.com/seanzhang9999/anp-open-sdk)
- [示例代码](examples/)
- [API文档](docs/api/)
- [常见问题](docs/faq.md)

---

*最后更新: 2024年1月*
