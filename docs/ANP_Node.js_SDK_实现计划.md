# ANP Node.js SDK 完整实现计划

## 📋 项目概述

基于ANP应用开发指南中的分层架构，完善Node.js版本的ANP SDK，实现与Python版本功能对等的完整DID认证和Agent管理系统。

## 🏗️ 架构对比分析

### 当前架构状态对比

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

| 层级 | Python版本状态 | Node.js版本状态 | 完成度 | 关键缺失 |
|------|---------------|----------------|--------|----------|
| **应用层 (Agent)** | ✅ 完整 | ✅ 基本完整 | 85% | 生命周期管理、配置模式 |
| **anp_runtime** | ✅ 完整 | ⚠️ 部分实现 | 45% | **Agent间通信、本地方法调用、群组管理、消息路由** |
| **anp_servicepoint** | ✅ 完整 | ⚠️ 部分实现 | 60% | 认证中间件、服务处理器 |
| **anp_server** | ✅ 完整 | ⚠️ 部分实现 | 65% | **标准路由、中间件集成、多域名支持** |
| **anp_foundation** | ✅ 完整 | ❌ 严重缺失 | 25% | **本地数据管理、域名管理、联系人管理** |
| **data_user** | ✅ 完整 | ❌ 完全缺失 | 0% | **用户数据存储和管理** |

## 🎯 实施计划

### 阶段一：Foundation层完善 (优先级：🔥🔥🔥)

#### 1.1 本地用户数据管理器实现
**目标**: 实现类似Python版本的`LocalUserDataManager`

**当前状态**: Node.js版本只有基础的`ANPUser`类，完全缺少用户数据管理器

**文件**: `src/foundation/user/local-user-data-manager.ts` (完全缺失)

**缺失的核心功能**:
- [ ] **用户数据扫描和索引**: 扫描`data_user`目录，建立DID和名称索引
- [ ] **多域名用户管理**: 按域名端口分组管理用户，检测用户名冲突
- [ ] **密钥文件管理**: 自动加载密钥文件到内存，支持DID和JWT密钥
- [ ] **托管DID支持**: 创建和管理托管DID用户
- [ ] **动态用户加载**: 支持运行时扫描和加载新用户
- [ ] **用户冲突检测**: 检测和解决用户名冲突

**Python版本参考**:
```python
class LocalUserDataManager:
    def load_all_users(self)  # 扫描并加载所有用户
    def get_user_data(self, did: str) -> Optional[LocalUserData]  # 通过DID获取用户
    def create_hosted_user(self, parent_user_data, host, port, did_document)  # 创建托管用户
    def scan_and_load_new_users(self)  # 扫描新用户
    def is_username_taken(self, name: str, host: str, port: int) -> bool  # 检查用户名冲突
```

**Node.js实现结构**:
```typescript
export class LocalUserDataManager {
  private static instance: LocalUserDataManager;
  private usersByDid: Map<string, LocalUserData> = new Map();
  private usersByName: Map<string, LocalUserData> = new Map();
  private usersByHostPort: Map<string, Map<string, LocalUserData>> = new Map();
  private conflictingUsers: ConflictInfo[] = [];
  
  public async loadAllUsers(): Promise<void>
  public getUserData(did: string): LocalUserData | undefined
  public async createDidUser(userInput: CreateUserInput): Promise<DIDDocument | null>
  public async createHostedUser(parentUser: LocalUserData, host: string, port: string): Promise<LocalUserData | null>
  public async scanAndLoadNewUsers(): Promise<void>
  public isUsernameTaken(name: string, host: string, port: number): boolean
  public resolveUsernameConflict(did: string, newName: string): boolean
}
```

#### 1.2 本地用户数据类实现
**目标**: 实现完整的`LocalUserData`类

**当前状态**: 基础`ANPUser`存在，但缺少大量功能

**文件**: `src/foundation/user/local-user-data.ts` (需要重构)

**已有功能**:
- ✅ 基础用户数据结构
- ✅ DID和名称属性
- ✅ 文件路径管理

**缺失的核心功能**:
- [ ] **密钥内存缓存**: 自动加载密钥文件到内存对象
- [ ] **联系人管理**: 联系人添加、获取、列表功能
- [ ] **Token管理**: 远程Token的存储和管理
- [ ] **托管DID信息**: 托管DID的特殊属性和方法
- [ ] **密钥文件操作**: 密钥文件的加载和验证

**Python版本参考**:
```python
class LocalUserData:
    def _load_keys_to_memory(self)  # 加载密钥到内存
    def get_token_to_remote(self, remote_did: str)  # 获取发送给远程的Token
    def store_token_to_remote(self, remote_did: str, token: str, expires_delta: int)  # 存储Token
    def add_contact(self, contact: Dict[str, Any])  # 添加联系人
    def get_contact(self, remote_did: str)  # 获取联系人
    def list_contacts(self)  # 列出所有联系人
```

#### 1.3 域名管理器实现
**目标**: 实现多域名环境支持

**当前状态**: 完全缺失

**文件**: `src/foundation/domain/domain-manager.ts` (完全缺失)

**缺失的核心功能**:
- [ ] **域名解析**: 从HTTP请求中解析域名和端口
- [ ] **域名验证**: 验证域名访问权限
- [ ] **数据路径管理**: 为不同域名分配数据路径
- [ ] **目录结构管理**: 确保域名对应的目录结构存在
- [ ] **配置管理**: 支持的域名配置和管理

**Python版本参考**:
```python
class DomainManager:
    def parse_host_header(self, host_header: str) -> Tuple[str, int]  # 解析Host头
    def get_all_data_paths(self, domain: str, port: int) -> Dict[str, Path]  # 获取数据路径
    def ensure_domain_directories(self, domain: str, port: int) -> bool  # 确保目录存在
    def validate_domain_access(self, domain: str, port: int) -> Tuple[bool, str]  # 验证访问权限
    def get_host_port_from_request(self, request) -> Tuple[str, int]  # 从请求获取域名端口
```

#### 1.4 联系人管理器实现
**目标**: 实现联系人管理功能

**当前状态**: 完全缺失

**文件**: `src/foundation/user/contact-manager.ts` (完全缺失)

**缺失的核心功能**:
- [ ] **联系人存储**: 联系人信息的持久化存储
- [ ] **联系人搜索**: 按DID、名称搜索联系人
- [ ] **联系人分组**: 联系人的分组管理
- [ ] **联系人同步**: 联系人信息的同步和更新

#### 1.5 用户数据目录结构创建
**目标**: 建立标准的用户数据存储结构

**当前状态**: 目录结构不存在

**任务**:
- [ ] **创建`data_user`目录结构**: 建立标准的多域名目录结构
- [ ] **实现用户目录扫描逻辑**: 扫描和识别用户目录
- [ ] **建立文件命名规范**: 统一的文件命名和组织规范
- [ ] **实现数据持久化机制**: 用户数据的保存和加载

**目录结构**:
```
data_user/
├── localhost_9527/
│   ├── anp_users/
│   │   └── user_[unique_id]/
│   │       ├── did_document.json
│   │       ├── agent_cfg.yaml
│   │       ├── key-1_private.pem
│   │       ├── key-1_public.pem
│   │       ├── private_key.pem
│   │       ├── public_key.pem
│   │       ├── ad.json
│   │       ├── api_interface.yaml
│   │       └── api_interface.json
│   ├── anp_users_hosted/
│   ├── agents_config/
│   ├── hosted_did_queue/
│   └── hosted_did_results/
└── user_localhost_9527/
    ├── anp_users/
    └── anp_users_hosted/
```

#### 1.6 DID创建和管理工具
**目标**: 实现用户DID创建工具

**当前状态**: 基础DID工具存在，但缺少用户创建功能

**文件**: `src/foundation/user/did-user-creator.ts` (缺失)

**缺失的核心功能**:
- [ ] **DID文档生成**: 标准DID文档的生成
- [ ] **密钥对生成和存储**: ECDSA和RSA密钥对的生成
- [ ] **用户配置文件创建**: agent_cfg.yaml的生成
- [ ] **唯一性检查**: DID和用户名的唯一性验证
- [ ] **目录结构创建**: 用户目录和文件的创建

**Python版本参考**:
```python
def create_did_user(user_input: dict, *, did_hex: bool = True, did_check_unique: bool = True):
    # 生成唯一ID和DID
    # 创建DID文档和密钥对
    # 保存用户配置文件
    # 加载到用户管理器
```

#### 1.7 认证增强
**目标**: 增强现有的认证功能

**当前状态**: 基础认证功能存在，但缺少与用户数据的集成

**文件**: `src/foundation/auth/auth.ts` (需要增强)

**需要增强的功能**:
- [ ] **与LocalUserDataManager集成**: 认证时查询本地用户数据
- [ ] **密钥缓存利用**: 利用内存中的密钥进行验证
- [ ] **托管DID认证**: 支持托管DID的认证逻辑
- [ ] **多域名认证**: 支持多域名环境下的认证

#### 1.8 配置系统增强
**目标**: 增强配置管理功能

**当前状态**: 基础配置系统存在

**文件**: `src/foundation/config/manager.ts` (需要增强)

**需要增强的功能**:
- [ ] **路径解析**: 支持`{APP_ROOT}`等路径变量
- [ ] **多域名配置**: 支持多域名的配置管理
- [ ] **动态配置**: 支持运行时配置更新

### 阶段二：ServicePoint层完善 (优先级：🔥🔥)

#### 2.1 认证中间件完善
**目标**: 实现完整的DID认证中间件

**当前状态**: 基础实现存在，但缺少与Foundation层的集成

**文件**: `src/servicepoint/middleware/auth-middleware.ts` (需要增强)

**已有功能**:
- ✅ 基础认证中间件框架
- ✅ 认证豁免路径处理
- ✅ CORS和日志中间件

**缺失的核心功能**:
- [ ] **与LocalUserDataManager集成**: 验证DID时查询本地用户数据
- [ ] **DID文档验证**: 验证DID文档的有效性
- [ ] **签名验证增强**: 更完整的签名验证逻辑
- [ ] **多域名支持**: 支持多域名环境下的认证

#### 2.2 核心服务处理器实现
**目标**: 实现完整的DID和Agent服务处理器

**当前状态**: 基础Agent服务处理器存在，但缺少DID服务处理器

**文件**: 
- `src/servicepoint/handlers/did-service-handler.ts` (缺失)
- `src/servicepoint/handlers/agent-service-handler.ts` (需要增强)
- `src/servicepoint/handlers/publisher-service-handler.ts` (缺失)

**缺失的核心功能**:
- [ ] **DID文档服务**: 获取和验证DID文档
- [ ] **Agent描述服务**: 获取Agent的ad.json描述文件
- [ ] **OpenAPI文档服务**: 获取Agent的YAML/JSON接口文档
- [ ] **多域名路径解析**: 支持多域名环境下的路径解析
- [ ] **发布者服务**: Agent信息发布和发现

**Python版本参考**:
```python
# DID服务处理器
def get_did_document(user_id: str, host: str, port: int) -> Tuple[bool, Union[Dict, str]]
def get_agent_description(user_id: str, host: str, port: int) -> Tuple[bool, Union[Dict, str]]
def get_agent_yaml_file(resp_did: str, yaml_file_name: str, host: str, port: int)
```

#### 2.3 扩展服务处理器实现
**目标**: 实现托管DID和认证服务处理器

**当前状态**: 完全缺失

**文件**: 
- `src/servicepoint/handlers/host-service-handler.ts` (缺失)
- `src/servicepoint/handlers/auth-service-handler.ts` (缺失)

**缺失的核心功能**:
- [ ] **托管DID申请**: 处理托管DID申请请求
- [ ] **托管DID状态查询**: 查询申请状态和结果
- [ ] **托管DID管理**: 列出和管理托管DID
- [ ] **认证服务**: 提供认证相关的服务端点

**Python版本参考**:
```python
# 托管DID服务
async def submit_hosted_did_request(hosted_request: BaseHostedDIDRequest, host: str, port: int)
async def check_hosted_did_status(request_id: str, host: str, port: int)
async def list_hosted_dids(host: str, port: int)
```

#### 2.4 服务实现层
**目标**: 实现托管DID的具体实现逻辑

**当前状态**: 完全缺失

**文件**: 
- `src/servicepoint/implementations/did-host/` (整个目录缺失)
  - `did-host-manager.ts`
  - `hosted-did-processor.ts`
  - `hosted-did-queue-manager.ts`
  - `hosted-did-result-manager.ts`

**缺失的核心功能**:
- [ ] **托管DID队列管理**: 申请队列的管理和处理
- [ ] **托管DID处理器**: 实际的DID创建和处理逻辑
- [ ] **结果管理**: 处理结果的存储和查询
- [ ] **域名管理集成**: 与域名管理器的集成

#### 2.5 认证豁免处理器
**目标**: 完善认证豁免逻辑

**当前状态**: 基础实现存在，但功能不完整

**文件**: `src/servicepoint/auth-exempt-handler.ts` (需要独立出来)

**需要增强的功能**:
- [ ] **动态豁免规则**: 支持动态添加豁免规则
- [ ] **路径模式匹配**: 更复杂的路径匹配逻辑
- [ ] **条件豁免**: 基于条件的豁免逻辑

### 阶段三：Runtime层增强 (优先级：🔥)

#### 3.1 Agent间通信实现
**目标**: 实现完整的Agent间通信机制

**当前状态**: Node.js版本只有基础的`AgentApiCaller`，缺少标准化的API调用接口

**文件**: 
- `src/runtime/services/agent-api-caller.ts` (需要重构)
- `src/runtime/services/agent-message-service.ts` (缺失)
- `src/runtime/services/agent-api-call.ts` (缺失)

**缺失的核心功能**:
- [ ] **标准化API调用函数**: 类似Python的`agent_api_call_post`、`agent_api_call_get`
- [ ] **消息传递系统**: 类似Python的`agent_msg_post`
- [ ] **响应处理标准化**: 统一的响应格式处理
- [ ] **DID路径编码**: URL编码和路径构建
- [ ] **认证集成**: 与Foundation层的认证系统集成

**Python版本参考**:
```python
# 标准化的API调用接口
async def agent_api_call_post(caller_agent: str, target_agent: str, api_path: str, params: Dict) -> Dict
async def agent_msg_post(caller_agent: str, target_agent: str, content: str, message_type: str = "text")
```

#### 3.2 本地方法调用系统
**目标**: 实现本地方法注册和调用

**当前状态**: 完全缺失

**文件**: 
- `src/runtime/local-service/local-methods-caller.ts` (缺失)
- `src/runtime/local-service/local-methods-decorators.ts` (缺失)
- `src/runtime/local-service/local-methods-doc.ts` (缺失)

**缺失的核心功能**:
- [ ] **本地方法注册表**: 全局方法注册和索引
- [ ] **装饰器支持**: `@local_method`装饰器
- [ ] **方法搜索和调用**: 通过关键词搜索和调用方法
- [ ] **文档生成**: 自动生成方法文档
- [ ] **参数验证**: 方法参数类型检查

**Python版本参考**:
```python
@local_method("calculator.add")
async def local_add(a: float, b: float):
    return {"result": a + b}

# 调用本地方法
result = await call_local_method("calculator.add", {"a": 10, "b": 20})
```

#### 3.3 全局消息路由系统
**目标**: 实现全局消息处理和群组管理

**当前状态**: 完全缺失

**文件**: 
- `src/runtime/core/global-message-manager.ts` (缺失)
- `src/runtime/core/global-group-manager.ts` (缺失)
- `src/runtime/services/group-member-sdk.ts` (缺失)

**缺失的核心功能**:
- [ ] **全局消息路由**: 消息处理器注册和路由
- [ ] **群组管理**: 群组创建、加入、离开
- [ ] **群组消息**: 群组内消息广播和处理
- [ ] **SSE支持**: 服务器发送事件流
- [ ] **冲突检测**: 消息处理器冲突检测和解决

**Python版本参考**:
```python
class GlobalMessageManager:
    def register_handler(cls, did: str, msg_type: str, handler: Callable, agent_name: str)
    def get_handler(cls, did: str, msg_type: str) -> Optional[Callable]

class GlobalGroupManager:
    def register_runner(cls, group_id: str, runner_class: type)
    def get_runner(cls, group_id: str) -> Optional[GroupRunner]
```

#### 3.4 Agent生命周期管理
**目标**: 实现Agent生命周期管理

**当前状态**: 基础Agent类存在，但缺少生命周期钩子

**文件**: `src/runtime/core/agent-lifecycle.ts` (缺失)

**缺失的核心功能**:
- [ ] **初始化钩子**: `initialize_agent`函数支持
- [ ] **清理钩子**: `cleanup_agent`函数支持
- [ ] **资源管理**: 自动资源分配和释放
- [ ] **错误恢复**: 初始化失败时的恢复机制

#### 3.5 工具函数和实用程序
**目标**: 实现运行时工具函数

**当前状态**: 部分缺失

**文件**: 
- `src/runtime/services/anp-tool.ts` (缺失)

**缺失的核心功能**:
- [ ] **业务处理器包装**: `wrap_business_handler`
- [ ] **参数自动提取**: `auto_wrap`功能增强
- [ ] **错误处理标准化**: 统一的错误处理模式
- [ ] **响应格式化**: 标准化的响应格式

### 阶段四：Server层完善 (优先级：🔥)

#### 4.1 标准路由实现
**目标**: 实现符合ANP协议的标准路由

**当前状态**: 基础路由存在，但缺少标准ANP路由结构

**文件**: 
- `src/server/routers/anp-routers.ts` (需要重构)
- `src/server/routers/did-router.ts` (缺失)
- `src/server/routers/agent-router.ts` (缺失)
- `src/server/routers/host-router.ts` (缺失)

**缺失的核心功能**:
- [ ] **标准DID路由**: `/wba/user/{user_id}/did.json`、`/wba/user/{user_id}/ad.json`
- [ ] **Agent API路由**: `/agent/api/{did}/{endpoint}`标准格式
- [ ] **托管DID路由**: 托管DID申请和查询路由
- [ ] **群组路由**: 群组管理和消息路由
- [ ] **发布者路由**: Agent信息发布路由

**Python版本参考**:
```python
# 标准DID路由
@router.get("/wba/user/{user_id}/did.json")
@router.get("/wba/user/{user_id}/ad.json")
@router.get("/wba/user/{resp_did}/{yaml_file_name}.yaml")

# Agent API路由
@router.all("/agent/api/{did}/{endpoint:path}")
```

#### 4.2 中间件集成完善
**目标**: 完善服务器中间件集成

**当前状态**: 基础中间件集成存在，但缺少完整的中间件链

**文件**: `src/server/express/anp-server.ts` (需要增强)

**已有功能**:
- ✅ 基础Express服务器
- ✅ 简单的认证中间件集成
- ✅ 基础路由处理

**缺失的核心功能**:
- [ ] **完整的中间件链**: 请求处理、认证、日志、错误处理
- [ ] **域名管理集成**: 多域名环境支持
- [ ] **请求上下文管理**: 请求上下文的传递和管理
- [ ] **性能监控**: 请求性能监控和统计

#### 4.3 多域名支持
**目标**: 实现多域名环境支持

**当前状态**: 不支持多域名

**文件**: 
- `src/server/middleware/domain-middleware.ts` (缺失)
- `src/server/utils/domain-resolver.ts` (缺失)

**缺失的核心功能**:
- [ ] **域名解析**: 从请求中解析域名和端口
- [ ] **域名验证**: 验证域名访问权限
- [ ] **路径映射**: 基于域名的路径映射
- [ ] **配置管理**: 多域名配置管理

**Python版本参考**:
```python
# 域名管理集成
domain_manager = get_domain_manager()
host, port = domain_manager.get_host_port_from_request(request)
is_valid, error_msg = domain_manager.validate_domain_access(host, port)
```

#### 4.4 错误处理和响应标准化
**目标**: 实现标准化的错误处理和响应格式

**当前状态**: 基础错误处理存在，但不够标准化

**文件**: 
- `src/server/middleware/error-handler.ts` (缺失)
- `src/server/utils/response-formatter.ts` (缺失)

**缺失的核心功能**:
- [ ] **统一错误处理**: 全局错误处理中间件
- [ ] **标准响应格式**: 统一的API响应格式
- [ ] **错误分类**: 不同类型错误的分类处理
- [ ] **错误日志**: 详细的错误日志记录

#### 4.5 服务器生命周期管理
**目标**: 实现服务器生命周期管理

**当前状态**: 基础启动停止功能存在

**文件**: `src/server/express/anp-server.ts` (需要增强)

**需要增强的功能**:
- [ ] **优雅关闭**: 优雅关闭机制
- [ ] **健康检查**: 详细的健康检查端点
- [ ] **服务发现**: 服务注册和发现
- [ ] **监控指标**: 服务器监控指标

### 阶段五：配置和开发模式支持 (优先级：🔥)

#### 5.1 配置模式支持
**目标**: 支持YAML配置文件定义Agent

**文件**: `src/runtime/config/config-agent-loader.ts`

**核心功能**:
- [ ] YAML配置解析
- [ ] 动态Agent创建
- [ ] 处理器绑定
- [ ] 配置验证

#### 5.2 自定义注册模式
**目标**: 支持`agent_register.js`自定义注册

**文件**: `src/runtime/config/custom-register-loader.ts`

**核心功能**:
- [ ] 自定义注册脚本加载
- [ ] 动态方法绑定
- [ ] 错误处理
- [ ] 调试支持

### 阶段五：工具和示例完善 (优先级：⚠️)

#### 5.1 用户管理工具
**目标**: 提供用户管理CLI工具

**文件**: `src/tools/user-manager.ts`

**核心功能**:
- [ ] 创建用户
- [ ] 列出用户
- [ ] 删除用户
- [ ] 用户信息查看

#### 5.2 完整示例应用
**目标**: 提供完整的示例应用

**文件**: `examples/complete-anp-app/`

**核心功能**:
- [ ] 多Agent协作示例
- [ ] 配置文件示例
- [ ] 部署脚本
- [ ] 测试用例

## 📅 实施时间表

### 第1周：Foundation层核心实现
- [ ] Day 1-2: `LocalUserDataManager`基础实现
- [ ] Day 3-4: `LocalUserData`类和密钥管理
- [ ] Day 5-7: 用户创建工具和数据持久化

### 第2周：ServicePoint和Runtime增强
- [ ] Day 1-3: 认证中间件和服务处理器
- [ ] Day 4-5: Agent间通信实现
- [ ] Day 6-7: 本地方法调用系统

### 第3周：配置模式和生命周期
- [ ] Day 1-3: 配置模式支持
- [ ] Day 4-5: 自定义注册模式
- [ ] Day 6-7: Agent生命周期管理

### 第4周：测试和文档
- [ ] Day 1-3: 单元测试和集成测试
- [ ] Day 4-5: 示例应用和文档
- [ ] Day 6-7: 性能优化和bug修复

## 🔧 技术实现细节

### 关键技术决策

1. **TypeScript严格模式**: 确保类型安全
2. **异步优先**: 所有I/O操作使用async/await
3. **错误处理**: 统一的错误处理机制
4. **日志系统**: 结构化日志记录
5. **配置管理**: 统一的配置系统

### 依赖管理

**新增依赖**:
```json
{
  "dependencies": {
    "yaml": "^2.3.4",
    "chokidar": "^3.5.3",
    "joi": "^17.11.0"
  },
  "devDependencies": {
    "@types/yaml": "^1.9.7"
  }
}
```

### 测试策略

1. **单元测试**: 每个模块独立测试
2. **集成测试**: Agent间通信测试
3. **端到端测试**: 完整流程测试
4. **性能测试**: 并发和负载测试

## 🎯 成功标准

### 功能完整性
- [ ] 与Python版本功能对等
- [ ] 所有示例正常运行
- [ ] 完整的DID认证流程
- [ ] Agent间通信正常

### 代码质量
- [ ] TypeScript类型覆盖率 > 95%
- [ ] 单元测试覆盖率 > 80%
- [ ] ESLint无警告
- [ ] 文档完整

### 性能指标
- [ ] Agent创建时间 < 100ms
- [ ] API调用延迟 < 50ms
- [ ] 内存使用稳定
- [ ] 支持100+并发Agent

## 🚀 开始实施

### 立即开始的任务

1. **创建基础目录结构**
2. **实现LocalUserDataManager骨架**
3. **建立测试框架**
4. **设置CI/CD流程**

### 第一个里程碑

**目标**: 实现基本的用户数据管理
**时间**: 1周
**验收标准**: 
- 能够创建和加载用户DID
- 密钥文件正确生成和加载
- 基本的用户数据持久化

---

## 📝 备注

- 优先实现Foundation层，这是整个系统的基础
- 保持与Python版本的API兼容性
- 重视错误处理和日志记录
- 及时编写测试和文档

**让我们开始逐步实施这个计划！** 🚀
