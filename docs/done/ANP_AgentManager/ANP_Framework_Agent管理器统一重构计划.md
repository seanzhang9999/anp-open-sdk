# ANP Framework Agent管理器统一重构计划

## 项目背景

当前ANP Framework存在两套Agent创建方式导致的冲突问题：
1. **配置加载方式**：通过 `LocalAgentManager.load_agent_from_module()` 加载
2. **代码创建方式**：通过 `ANPUser.from_did()` 直接创建

当多个Agent指向同一个DID时，会产生API路由冲突、消息处理冲突、状态不一致等问题。

## 重构目标

### 核心目标
1. **统一Agent创建接口**：所有Agent都通过 `AgentManager` 统一创建和管理
2. **明确DID使用规则**：通过独占/共享模式明确DID使用权限
3. **简化冲突处理**：将冲突检测前置到Agent创建阶段
4. **保持开发体验**：提供简洁的装饰器API

### 设计原则
- **ANPUser**：纯粹的DID身份容器（did、私钥、token等）
- **Agent**：功能载体，通过装饰器发布API和消息处理功能
- **AgentManager**：统一的创建、注册和冲突管理中心

## 核心设计方案

### 1. DID使用模式

#### 独占DID模式
- **规则**：一个DID只能被一个Agent使用
- **消息处理**：该Agent自动获得所有消息处理权限
- **适用场景**：单一功能的Agent

#### 共享DID模式
- **规则**：多个Agent可以共享一个DID，但需要指定prefix避免API冲突
- **消息处理**：必须指定唯一的主Agent（primary_agent）处理消息
- **适用场景**：功能模块化的复合Agent

### 2. Agent创建接口

```python
class AgentManager:
    @classmethod
    def create_agent(cls, anp_user: ANPUser, name: str, 
                    shared: bool = False, 
                    prefix: str = None,
                    primary_agent: bool = False):
        """统一的Agent创建接口"""
        pass
```

#### 参数说明
- `anp_user`: ANPUser实例（必选）
- `name`: Agent名称（必选）
- `shared`: 是否共享DID（默认False）
- `prefix`: 共享模式下的API前缀（共享模式必选）
- `primary_agent`: 是否为主Agent，拥有消息处理权限（共享模式可选）

### 3. 冲突检测规则

#### 独占模式冲突检测
```python
if not shared:
    if did in cls._did_usage_registry:
        raise ValueError("DID独占冲突: 已被其他Agent使用")
```

#### 共享模式冲突检测
```python
if shared:
    if not prefix:
        raise ValueError("共享模式必须提供prefix参数")
    
    # 检查prefix冲突
    for existing_agent in existing_agents:
        if existing_agent.prefix == prefix:
            raise ValueError("Prefix冲突")
    
    # 检查主Agent冲突
    if primary_agent:
        for existing_agent in existing_agents:
            if existing_agent.primary_agent:
                raise ValueError("主Agent冲突: 已存在主Agent")
```

### 4. Agent装饰器系统

```python
class Agent:
    def api(self, path: str, methods=None):
        """API装饰器"""

        def decorator(func):
            full_path = f"{self.prefix}{path}" if self.prefix else path
            # 注册到全局路由
            GlobalRouter.register_api(self.anp_user_id, full_path, func, self.name)
            return func

        return decorator

    def message_handler(self, msg_type: str):
        """消息处理器装饰器"""

        def decorator(func):
            if not self._can_handle_message():
                raise PermissionError("无消息处理权限")
            # 注册消息处理器
            GlobalMessageManager.register_handler(self.anp_user_id, msg_type, func, self.name)
            return func

        return decorator
```

## 实施计划

### 阶段1：核心架构实现（优先级：高）

#### 1.1 创建统一的AgentManager类
**文件位置**: `anp_server_framework/agent_manager.py`

**主要功能**:
- 实现 `create_agent()` 方法
- DID使用注册表管理
- 冲突检测逻辑
- Agent实例创建和配置

**预计工期**: 2天

#### 1.2 重构Agent类
**文件位置**: `anp_server_framework/agent.py` (新建)

**主要功能**:
- Agent装饰器系统（`@agent.api`, `@agent.message_handler`）
- 消息处理权限检查
- API路由注册
- 与ANPUser的关联管理

**预计工期**: 2天

#### 1.3 全局路由和消息管理器
**文件位置**: 
- `anp_server_framework/global_router.py` (新建)
- `anp_server_framework/global_message_manager.py` (新建)

**主要功能**:
- 统一的API路由注册和分发
- 消息处理器注册和分发
- 冲突检测和错误处理

**预计工期**: 1天

### 阶段2：配置系统集成（优先级：高）

#### 2.1 更新配置文件格式
**影响文件**: `data_user/*/agents_config/*/agent_mappings.yaml`

**新增字段**:
```yaml
shared: true/false
prefix: "/calculator"  # 共享模式必需
primary_agent: true/false  # 共享模式可选
```

**预计工期**: 0.5天

#### 2.2 更新LocalAgentManager
**文件位置**: `anp_server_framework/agent_manager.py`

**修改内容**:
- 配置加载逻辑适配新的AgentManager接口
- 支持shared、prefix、primary_agent参数
- 保持向后兼容性

**预计工期**: 1天

### 阶段3：现有代码迁移（优先级：中）

#### 3.1 迁移现有配置Agent
**影响文件**: 
- `data_user/localhost_9527/agents_config/agent_*/`
- 所有现有的agent配置

**迁移策略**:
1. 分析现有Agent的DID使用情况
2. 确定独占/共享模式
3. 为共享模式的Agent分配prefix
4. 更新配置文件

**预计工期**: 1天

#### 3.2 提供ANPUser.from_did()迁移支持
**文件位置**: `anp_sdk/anp_user.py`

**实现方案**:
```python
@classmethod
def from_did(cls, did: str, **kwargs):
    import warnings
    warnings.warn(
        "直接使用 ANPUser.from_did() 已废弃，请使用 AgentManager.create_agent()",
        DeprecationWarning,
        stacklevel=2
    )
    # 可选：自动重定向到新接口或抛出错误
```

**预计工期**: 0.5天

### 阶段4：测试和文档（优先级：中）

#### 4.1 单元测试
**测试文件**: `tests/test_agent_manager.py` (新建)

**测试覆盖**:
- Agent创建的各种场景
- 冲突检测逻辑
- 装饰器功能
- 错误处理

**预计工期**: 1天

#### 4.2 集成测试
**测试场景**:
- 配置加载Agent与代码创建Agent的交互
- 共享DID模式下的API路由
- 消息处理权限验证

**预计工期**: 1天

#### 4.3 更新文档和示例
**文档更新**:
- API使用指南
- 迁移指南
- 最佳实践

**预计工期**: 1天

## 使用示例

### 独占DID模式示例

```python
# 创建独占DID的Agent
anp_user = ANPUser.from_did("did:wba:localhost:9527:user:calculator")
agent = AgentManager.create_agent(
   anp_user=anp_user,
   name="Calculator Agent",
   shared=False  # 独占模式
)


@agent._api("/add")
def add_numbers(a: int, b: int):
   return {"result": a + b}


@agent._message_handler("text")  # ✅ 独占模式自动有消息权限
def handle_text(message):
   return f"Calculator: {message['content']}"
```

### 共享DID模式示例

```python
# 主Agent
anp_user = ANPUser.from_did("did:wba:localhost:9527:user:shared")
main_agent = AgentManager.create_agent(
   anp_user=anp_user,
   name="Main Agent",
   shared=True,
   prefix="/main",
   primary_agent=True  # 主Agent，可处理消息
)


@main_agent._message_handler("text")  # ✅ 主Agent可以处理消息
def handle_text(message):
   return f"Main: {message['content']}"


# 辅助Agent
calc_agent = AgentManager.create_agent(
   anp_user=anp_user,
   name="Calculator Agent",
   shared=True,
   prefix="/calc",
   primary_agent=False  # 辅助Agent，只提供API
)


@calc_agent._api("/add")  # ✅ 辅助Agent可以提供API
def add_numbers(a: int, b: int):
   return {"result": a + b}
```

### 配置文件示例

```yaml
# agent_mappings.yaml
did: "did:wba:localhost:9527:user:shared"
name: "Main Agent"
shared: true
prefix: "/main"
primary_agent: true

api:
  - path: "/status"
    handler: "get_status"

message_handlers:
  - type: "text"
    handler: "handle_text_message"
```

## 错误处理示例

### DID独占冲突
```python
# Agent1 创建成功
agent1 = AgentManager.create_agent(anp_user, "Agent1", shared=False)  # ✅

# Agent2 尝试使用同一个DID
agent2 = AgentManager.create_agent(anp_user, "Agent2", shared=False)  
# ❌ ValueError: DID独占冲突: did:wba:localhost:9527:user:abc123 已被Agent 'Agent1' 使用
#    解决方案:
#      1. 使用不同的DID
#      2. 设置 shared=True 进入共享模式
```

### Prefix冲突
```python
# Agent1 创建成功
agent1 = AgentManager.create_agent(anp_user, "Agent1", shared=True, prefix="/calc")  # ✅

# Agent2 使用相同prefix
agent2 = AgentManager.create_agent(anp_user, "Agent2", shared=True, prefix="/calc")  
# ❌ ValueError: Prefix冲突: /calc 已被Agent 'Agent1' 使用
#    解决方案:
#      1. 使用不同的prefix
#      2. 修改现有Agent的prefix
#      3. 合并功能到现有Agent
```

### 主Agent冲突
```python
# 主Agent创建成功
main_agent = AgentManager.create_agent(anp_user, "Main", shared=True, prefix="/main", primary_agent=True)  # ✅

# 尝试创建第二个主Agent
another_main = AgentManager.create_agent(anp_user, "Another", shared=True, prefix="/another", primary_agent=True)  
# ❌ ValueError: 主Agent冲突: DID did:wba:localhost:9527:user:abc123 的主Agent已被 'Main' 占用
#    解决方案:
#      1. 设置 primary_agent=False
#      2. 修改现有主Agent配置
```

## 风险评估和缓解措施

### 高风险项
1. **现有代码兼容性**
   - **风险**: 现有使用 `ANPUser.from_did()` 的代码可能中断
   - **缓解**: 提供废弃警告和自动重定向机制

2. **配置文件迁移**
   - **风险**: 大量现有配置文件需要更新
   - **缓解**: 提供自动迁移脚本和向后兼容支持

### 中风险项
1. **性能影响**
   - **风险**: 新的冲突检测可能影响Agent创建性能
   - **缓解**: 优化检测算法，使用缓存机制

2. **学习成本**
   - **风险**: 开发者需要学习新的API
   - **缓解**: 提供详细文档和迁移指南

## 成功标准

### 功能标准
- [ ] 所有Agent都通过AgentManager统一创建
- [ ] DID冲突在创建时被检测和阻止
- [ ] 共享DID模式正常工作，prefix无冲突
- [ ] 消息处理权限按规则正确分配
- [ ] 现有配置Agent正常迁移

### 质量标准
- [ ] 单元测试覆盖率 > 90%
- [ ] 集成测试通过率 100%
- [ ] 性能无明显下降
- [ ] 错误信息清晰易懂

### 文档标准
- [ ] API文档完整
- [ ] 迁移指南清晰
- [ ] 示例代码可运行
- [ ] 最佳实践文档

## 总结

本重构计划通过统一Agent管理接口，明确DID使用规则，将冲突检测前置，从根本上解决了当前多Agent指向同一DID的冲突问题。重构后的系统将具有更好的可维护性、可扩展性和开发体验。

**预计总工期**: 10天
**关键里程碑**: 
- 第3天：核心架构完成
- 第6天：配置系统集成完成  
- 第8天：现有代码迁移完成
- 第10天：测试和文档完成

**建议实施顺序**: 按阶段顺序实施，确保每个阶段完成后进行充分测试再进入下一阶段。
