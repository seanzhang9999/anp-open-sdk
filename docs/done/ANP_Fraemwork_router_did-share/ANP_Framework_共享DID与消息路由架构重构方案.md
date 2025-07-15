# ANP Framework 共享DID与消息路由架构重构方案

## 1. 概述

### 1.1 当前架构问题分析

**传统架构问题**：
- Agent与DID严格1:1绑定，缺乏灵活性
- API路由直接绑定在ANPUser上，职责不清
- 消息处理与API处理混合在同一层次
- 缺乏DID使用冲突检测机制

**重构驱动因素**：
- 需要支持多个Agent共享同一个DID身份
- 需要清晰的职责分离：身份管理 vs 功能实现
- 需要灵活的路由机制支持复杂的业务场景
- 需要可扩展的消息处理架构

### 1.2 重构目标和原则

**目标**：
1. 实现Agent与DID的N:1映射关系
2. 建立清晰的架构分层：SDK层(协议) + Framework层(应用)
3. 提供灵活的路由机制支持混合部署
4. 保持向后兼容性

**原则**：
1. **职责分离**：身份管理与功能实现分离
2. **冲突检测**：DID使用冲突自动检测和预防
3. **自主路由**：共享DID内部路由完全自主设计
4. **向后兼容**：支持现有的独立DID Agent

## 2. 核心架构变化

### 2.1 Agent与DID关系重新定义

**之前**：
```
1 Agent = 1 DID = 1 User
每个Agent都有独立的DID身份
```

**现在**：
```
N Agents = 1 Shared DID = 1 User
多个Agent可以共享同一个DID身份
```

**概念重新定义**：
- **Agent**：功能实体，专注于特定业务逻辑
- **DID/ANPUser**：身份容器，提供认证和协议支持
- **Router**：路由到具体的Agent实例，而不是DID

### 2.2 路由机制演进

**API路由流程**：
```
传统: Request -> DID -> ANPUser -> handle_request()
新架构: Request -> Shared DID -> Path Resolution -> Specific Agent -> handle_request()
```

**消息路由流程**：
```
Request -> DID -> ANPUser -> Message Handler -> [内部路由] -> Sub Agents
```

### 2.3 消息处理分层设计

**三层架构**：
1. **Framework层**：DID路由和冲突检测
2. **SDK层**：消息处理器统一接口
3. **应用层**：具体消息处理逻辑和内部路由

## 3. DID管理机制

### 3.1 DID类型定义

**独立DID**：
- 一个DID对应一个Agent
- Agent直接使用DID作为标识
- 传统的1:1映射关系

**共享DID**：
- 一个DID对应多个Agent
- Agent使用名称作为标识
- 通过路径前缀区分不同Agent

### 3.2 DID冲突检测机制

**检测规则**：
1. 同一个DID不能既作为独立DID又作为共享DID
2. 独立DID注册时检查是否已被共享DID使用
3. 共享DID注册时检查是否已被独立DID使用

**实现方案**：

```python
class AgentRouter:
    def __init__(self):
        self.did_usage_registry = {}  # did -> {"type": "independent|shared", "agents": [...]}

    def register_agent_with_domain(self, agent, ...):
        agent_did = str(agent.anp_user_id)

        # 检查DID使用冲突
        if agent_did in self.did_usage_registry:
            existing_type = self.did_usage_registry[agent_did]["type"]
            if existing_type == "shared":
                raise ValueError(f"❌ DID {agent_did} 已被用作共享DID，不能注册为独立Agent")

        # 注册为独立DID
        self.did_usage_registry[agent_did] = {
            "type": "independent",
            "agents": [agent.name]
        }
```

### 3.3 注册流程设计

**独立DID Agent注册**：
1. 检查DID冲突
2. 使用DID作为注册键
3. 注册到domain_agents和global_agents
4. 更新did_usage_registry

**共享DID Agent注册**：
1. 检查DID冲突
2. 使用Agent名称作为注册键
3. 注册共享DID路径映射
4. 更新did_usage_registry

## 4. 消息处理架构

### 4.1 消息路由层次结构

```
HTTP Request (Message)
    ↓
Framework Router (按DID路由)
    ↓
ANPUser.handle_request() (统一消息接口)
    ↓
Message Handler (注册的处理器)
    ↓
[可选] 内部路由 (共享DID自主设计)
    ↓
具体处理逻辑
```

### 4.2 共享DID消息处理器管理

**注册策略**：
- 允许多个Agent注册消息处理器
- 发现冲突时报警并使用第一个注册的
- 后续注册的处理器被忽略

**实现方案**：
```python
class ANPUser:
    def register_message_handler(self, msg_type: str, handler, agent_name: str = None):
        # 检查是否已有消息处理器
        if msg_type in self.message_handlers:
            existing_handler = self.message_handlers[msg_type]
            logger.warning(f"⚠️  DID {self.id} 的消息类型 '{msg_type}' 已有处理器")
            logger.warning(f"   现有处理器: {getattr(existing_handler, '__name__', 'unknown')}")
            logger.warning(f"   新处理器: {getattr(handler, '__name__', 'unknown')} (来自 {agent_name})")
            logger.warning(f"   🔧 使用第一个注册的处理器，忽略后续注册")
            return  # 使用第一个，忽略后续的
        
        self.message_handlers[msg_type] = handler
        logger.info(f"✅ 注册消息处理器: DID {self.id}, 类型 '{msg_type}', 来自 {agent_name}")
```

### 4.3 内部路由自主设计

**Framework职责边界**：
- Framework只负责将消息路由到正确的DID
- 不关心DID内部如何分发和处理消息

**共享DID内部路由示例**：
```python
class SharedDIDMessageRouter:
    def __init__(self):
        self.sub_agents = {}  # 内部Agent注册表
        self.routing_rules = {}  # 自定义路由规则
    
    async def handle_message(self, request_data):
        """这是注册给ANPUser的统一消息处理器"""
        message_type = request_data.get("message_type")
        content = request_data.get("content", "")
        
        # 内部路由逻辑（完全自主设计）
        if message_type == "command":
            return await self._route_command(content)
        elif message_type == "query":
            return await self._route_query(content)
        else:
            return await self._default_handler(request_data)
```

## 5. API路由重构

### 5.1 共享DID路径映射

**映射机制**：
```python
# 共享DID配置
shared_did: "did:wba:localhost:9527:wba:user:shared001"
path_mappings:
  "/calculator/add" -> ("CalculatorAgent", "/add")
  "/calculator/subtract" -> ("CalculatorAgent", "/subtract")
  "/weather/query" -> ("WeatherAgent", "/query")
```

**路由解析**：
```python
def _resolve_shared_did(self, shared_did: str, api_path: str):
    """解析共享DID，返回(target_agent_name, original_path)"""
    config = self.shared_did_registry[shared_did]
    path_mappings = config.get('path_mappings', {})
    
    # 精确匹配
    if api_path in path_mappings:
        agent_name, original_path = path_mappings[api_path]
        return agent_name, original_path
    
    return None, None
```

### 5.2 混合模式支持

**支持的部署模式**：
1. **纯独立DID模式**：所有Agent都有独立DID
2. **纯共享DID模式**：所有Agent共享同一个DID
3. **混合模式**：独立DID Agent + 共享DID Agent共存

**混合部署示例**：
```
同一系统中：
- MainAgent (独立DID: did:main001)
- CalculatorAgent (共享DID: did:shared001, 路径: /calculator/*)
- WeatherAgent (共享DID: did:shared001, 路径: /weather/*)
```

### 5.3 路由优先级策略

**API路由优先级**：
1. 检查是否为消息请求 -> 直接DID路由
2. 检查是否为共享DID API -> 路径解析路由
3. 常规DID路由

**Agent查找优先级**：
1. 当前域名:端口下的Agent
2. 当前域名下其他端口的Agent
3. 全局Agent（向后兼容）

## 6. 实现方案

### 6.1 代码修改清单

**需要修改的文件**：
1. `anp_open_sdk_framework/server/router/router_agent.py`
   - 添加DID冲突检测
   - 完善共享DID路由逻辑

2. `anp_open_sdk_framework/adapter/agent_manager.py`
   - 添加消息处理器注册逻辑
   - 支持共享DID配置

3. `anp_open_sdk/anp_user.py`
   - 增强消息处理器注册方法
   - 添加冲突检测和警告

### 6.2 关键类和方法设计

**AgentRouter增强**：
```python
class AgentRouter:
    def __init__(self):
        self.did_usage_registry = {}  # DID使用注册表
        # ... 现有属性
    
    def register_agent_with_domain(self, agent, ...):
        # 添加DID冲突检测
        pass
    
    def register_shared_did(self, shared_did, agent_name, ...):
        # 添加DID冲突检测
        pass
    
    def _check_did_conflict(self, did, new_type):
        # DID冲突检测逻辑
        pass
```

**ANPUser增强**：
```python
class ANPUser:
    def register_message_handler(self, msg_type: str, handler, agent_name: str = None):
        # 添加冲突检测和警告
        pass
```

### 6.3 向后兼容性保证

**兼容性策略**：
1. 保持现有API接口不变
2. 添加新功能时使用可选参数
3. 保持全局索引以支持旧的查找方式
4. 渐进式迁移，不强制使用新功能

## 7. 配置示例

### 7.1 独立DID Agent配置

```yaml
# agent_main.yaml
did: "did:wba:localhost:9527:wba:user:main001"
name: "MainAgent"
api:
  - path: "/status"
    handler: "get_status"
    method: "GET"
  - path: "/process"
    handler: "process_request"
    method: "POST"
```

### 7.2 共享DID Agent配置

```yaml
# agent_calculator.yaml
did: "did:wba:localhost:9527:wba:user:calculator001"  # 这个会被忽略
name: "CalculatorAgent"
share_did:
  enabled: true
  shared_did: "did:wba:localhost:9527:wba:user:shared001"
  path_prefix: "/calculator"
api:
  - path: "/add"
    handler: "add_numbers"
    method: "POST"
  - path: "/subtract"
    handler: "subtract_numbers"
    method: "POST"
```

```yaml
# agent_weather.yaml
did: "did:wba:localhost:9527:wba:user:weather001"  # 这个会被忽略
name: "WeatherAgent"
share_did:
  enabled: true
  shared_did: "did:wba:localhost:9527:wba:user:shared001"
  path_prefix: "/weather"
api:
  - path: "/query"
    handler: "get_weather"
    method: "GET"
```

### 7.3 混合部署示例

**系统中同时存在**：
```
独立DID Agents:
- MainAgent: did:main001
- AdminAgent: did:admin001

共享DID Agents (共享 did:shared001):
- CalculatorAgent: /calculator/*
- WeatherAgent: /weather/*
- NewsAgent: /news/*
```

**访问示例**：
```bash
# 独立DID Agent
POST /agent/api/did:main001/status

# 共享DID Agent
POST /agent/api/did:shared001/calculator/add
POST /agent/api/did:shared001/weather/query

# 消息（都直接路由到DID）
POST /agent/api/did:main001/message/post
POST /agent/api/did:shared001/message/post  # 由第一个注册的Agent处理
```

## 8. 测试策略

### 8.1 冲突检测测试

**测试用例**：
1. 尝试将已用作共享DID的DID注册为独立DID
2. 尝试将已用作独立DID的DID用作共享DID
3. 多个Agent尝试注册相同的消息处理器

**预期结果**：
- 抛出明确的错误信息
- 系统状态保持一致
- 日志记录详细的冲突信息

### 8.2 路由功能测试

**测试场景**：
1. 独立DID Agent的API调用
2. 共享DID Agent的API调用
3. 路径解析的正确性
4. 混合模式下的路由优先级

### 8.3 消息处理测试

**测试场景**：
1. 独立DID的消息处理
2. 共享DID的消息处理
3. 消息处理器冲突的处理
4. 内部路由的自主设计验证

## 9. 实施计划

### 9.1 第一阶段：基础架构
- [ ] 实现DID冲突检测机制
- [ ] 增强AgentRouter的注册逻辑
- [ ] 完善消息处理器注册

### 9.2 第二阶段：路由增强
- [ ] 完善共享DID路由解析
- [ ] 实现混合模式支持
- [ ] 添加详细的日志和错误处理

### 9.3 第三阶段：测试和优化
- [ ] 编写全面的测试用例
- [ ] 性能优化和稳定性测试
- [ ] 文档完善和示例更新

## 10. 总结

这个架构重构方案实现了以下核心目标：

1. **灵活的Agent-DID映射**：支持1:1和N:1两种模式
2. **清晰的职责分离**：Framework、SDK、应用层各司其职
3. **强大的冲突检测**：自动预防DID使用冲突
4. **自主的内部路由**：共享DID内部路由完全可定制
5. **完整的向后兼容**：现有系统无需修改即可运行

通过这个方案，ANP Framework将具备更强的灵活性和扩展性，能够支持更复杂的业务场景和部署模式。
