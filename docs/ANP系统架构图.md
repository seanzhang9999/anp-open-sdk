# ANP系统架构图

## 🏗️ 整体架构

```mermaid
graph TB
    subgraph "Application Layer"
        A1[Your Agents]
        A2[Agent配置文件]
        A3[业务逻辑处理器]
    end
    
    subgraph "anp_transformer"
        T1[AgentManager<br/>Agent管理器]
        T2[Agent装饰器<br/> '@'agent_class]
        T3[全局路由器<br/>GlobalRouter]
        T4[消息管理器<br/>GlobalMessageManager]
    end
    
    subgraph "anp_servicepoint"
        S1[核心服务处理器<br/>core_service_handler]
        S2[扩展服务处理器<br/>extend_service_handler]
        S3[DID托管实现<br/>did_host]
    end
    
    subgraph "anp_workbench_server"
        W1[ANP_Server<br/>基线服务器]
        W2[路由器<br/>router_*]
        W3[中间件<br/>middleware]
    end
    
    subgraph "anp_foundation"
        F1[ANPUser<br/>用户管理]
        F2[DID工具<br/>did_tool]
        F3[配置管理<br/>UnifiedConfig]
        F4[认证授权<br/>auth]
    end
    
    subgraph "data_user"
        D1[用户DID数据<br/>anp_users/]
        D2[Agent配置<br/>agents_config/]
        D3[托管DID数据<br/>anp_users_hosted/]
    end
    
    A1 --> T1
    A2 --> T1
    A3 --> T2
    T1 --> T3
    T1 --> T4
    T3 --> S1
    T4 --> S1
    S1 --> S2
    S2 --> S3
    S1 --> W1
    W1 --> W2
    W1 --> W3
    W2 --> F1
    W3 --> F4
    F1 --> F2
    F1 --> F3
    F1 --> D1
    T1 --> D2
    S3 --> D3
```

## 🔄 Agent生命周期

```mermaid
sequenceDiagram
    participant Dev as 开发者
    participant AM as AgentManager
    participant AU as ANPUser
    participant AS as ANP_Server
    participant Router as GlobalRouter
    
    Dev->>AM: 创建Agent (@agent_class)
    AM->>AU: 获取/创建ANPUser
    AU->>AU: 加载DID和密钥
    AM->>AM: 注册Agent实例
    AM->>Router: 注册API路由
    AM->>AS: 启动服务器
    AS->>AS: 监听HTTP请求
    
    Note over Dev,Router: Agent创建完成，开始服务
    
    AS->>Router: 接收API请求
    Router->>AM: 路由到目标Agent
    AM->>AU: 执行业务逻辑
    AU->>Router: 返回处理结果
    Router->>AS: 响应客户端
```

## 🌐 Agent间通信架构

```mermaid
graph LR
    subgraph "Agent A"
        A1[业务逻辑]
        A2[API调用客户端]
        A3[消息发送器]
    end
    
    subgraph "通信层"
        C1[agent_api_call_post]
        C2[agent_msg_post]
        C3[HTTP/WebSocket]
    end
    
    subgraph "Agent B"
        B1[API处理器]
        B2[消息处理器]
        B3[业务逻辑]
    end
    
    A1 --> A2
    A1 --> A3
    A2 --> C1
    A3 --> C2
    C1 --> C3
    C2 --> C3
    C3 --> B1
    C3 --> B2
    B1 --> B3
    B2 --> B3
```

## 🔐 DID身份架构

```mermaid
graph TB
    subgraph "DID标识符"
        D1[did:wba:localhost%3A9527:wba:user:27c0b1d11180f973]
        D2[协议标识: did]
        D3[方法名: wba]
        D4[主机端口: localhost%3A9527]
        D5[路径: wba:user]
        D6[唯一ID: 27c0b1d11180f973]
    end
    
    subgraph "DID文档"
        DD1[did_document.json]
        DD2[验证方法<br/>verificationMethod]
        DD3[服务端点<br/>service]
        DD4[公钥信息<br/>publicKey]
    end
    
    subgraph "密钥对"
        K1[DID私钥<br/>key-1_private.pem]
        K2[DID公钥<br/>key-1_public.pem]
        K3[JWT私钥<br/>private_key.pem]
        K4[JWT公钥<br/>public_key.pem]
    end
    
    D1 --> DD1
    DD1 --> DD2
    DD1 --> DD3
    DD1 --> DD4
    DD2 --> K1
    DD2 --> K2
    DD4 --> K3
    DD4 --> K4
```

## 🔀 共享DID架构

```mermaid
graph TB
    subgraph "共享DID: did:wba:localhost%3A9527:wba:user:shared123"
        SD1[DID文档]
        SD2[密钥对]
    end
    
    subgraph "主Agent (Primary)"
        PA1[天气主服务<br/>prefix: /weather]
        PA2[API: /weather/current]
        PA3[消息处理器: text]
    end
    
    subgraph "辅助Agent 1"
        AA1[天气预报服务<br/>prefix: /forecast]
        AA2[API: /forecast/daily]
    end
    
    subgraph "辅助Agent 2"
        AB1[天气历史服务<br/>prefix: /history]
        AB2[API: /history/monthly]
    end
    
    subgraph "路由分发"
        R1[GlobalRouter]
        R2[路径匹配]
        R3[Agent选择]
    end
    
    SD1 --> PA1
    SD1 --> AA1
    SD1 --> AB1
    SD2 --> PA1
    SD2 --> AA1
    SD2 --> AB1
    
    PA1 --> R1
    AA1 --> R1
    AB1 --> R1
    R1 --> R2
    R2 --> R3
    
    R3 --> PA2
    R3 --> AA2
    R3 --> AB2
    R3 --> PA3
```

## 📁 数据存储架构

```mermaid
graph TB
    subgraph "data_user/"
        subgraph "localhost_9527/"
            subgraph "anp_users/ (用户DID数据)"
                U1[user_27c0b1d11180f973/]
                U2[user_28cddee0fade0258/]
                U3[user_e0959abab6fc3c3d/]
            end
            
            subgraph "agents_config/ (Agent配置)"
                AC1[agent_001/]
                AC2[agent_calculator/]
                AC3[agent_llm/]
            end
            
            subgraph "anp_users_hosted/ (托管DID)"
                UH1[user_hosted_*/]
            end
            
            subgraph "队列和结果"
                Q1[hosted_did_queue/]
                Q2[hosted_did_results/]
            end
        end
    end
    
    subgraph "用户数据文件"
        UF1[did_document.json<br/>DID文档]
        UF2[agent_cfg.yaml<br/>Agent配置]
        UF3[*.pem<br/>密钥文件]
        UF4[ad.json<br/>Agent描述]
        UF5[api_interface.*<br/>接口文档]
    end
    
    U1 --> UF1
    U1 --> UF2
    U1 --> UF3
    U1 --> UF4
    U1 --> UF5
    
    subgraph "Agent配置文件"
        AF1[agent_mappings.yaml<br/>Agent映射]
        AF2[agent_handlers.py<br/>处理器实现]
        AF3[agent_register.py<br/>注册逻辑]
    end
    
    AC1 --> AF1
    AC1 --> AF2
    AC1 --> AF3
```

## 🚀 部署架构

```mermaid
graph TB
    subgraph "开发环境"
        DE1[本地开发<br/>localhost:9527]
        DE2[配置文件<br/>unified_config_framework_demo.yaml]
        DE3[Agent代码<br/>Python装饰器]
    end
    
    subgraph "运行时环境"
        RE1[ANP_Server<br/>HTTP服务器]
        RE2[AgentManager<br/>Agent管理]
        RE3[GlobalRouter<br/>请求路由]
        RE4[数据存储<br/>data_user/]
    end
    
    subgraph "网络接口"
        NI1[HTTP API<br/>/agent/api/*]
        NI2[消息接口<br/>/agent/message/*]
        NI3[DID服务<br/>/wba/user/*]
        NI4[发布接口<br/>/publisher/*]
    end
    
    subgraph "外部访问"
        EA1[其他Agent<br/>API调用]
        EA2[Web客户端<br/>HTTP请求]
        EA3[DID网络<br/>分布式通信]
    end
    
    DE1 --> RE1
    DE2 --> RE1
    DE3 --> RE2
    RE1 --> RE2
    RE2 --> RE3
    RE3 --> RE4
    RE1 --> NI1
    RE1 --> NI2
    RE1 --> NI3
    RE1 --> NI4
    NI1 --> EA1
    NI2 --> EA1
    NI3 --> EA3
    NI4 --> EA2
```

## 🔧 配置管理架构

```mermaid
graph LR
    subgraph "配置文件"
        CF1[unified_config_framework_demo.yaml]
        CF2[环境变量<br/>.env]
        CF3[默认配置<br/>unified_config.default.yaml]
    end
    
    subgraph "配置管理器"
        CM1[UnifiedConfig]
        CM2[配置解析器]
        CM3[路径解析器]
        CM4[环境变量映射]
    end
    
    subgraph "全局配置"
        GC1[get_global_config]
        GC2[set_global_config]
        GC3[配置对象缓存]
    end
    
    subgraph "组件使用"
        CU1[ANP_Server]
        CU2[AgentManager]
        CU3[ANPUser]
        CU4[日志系统]
    end
    
    CF1 --> CM1
    CF2 --> CM4
    CF3 --> CM1
    CM1 --> CM2
    CM1 --> CM3
    CM1 --> CM4
    CM2 --> GC1
    CM3 --> GC1
    CM4 --> GC1
    GC1 --> GC3
    GC2 --> GC3
    GC3 --> CU1
    GC3 --> CU2
    GC3 --> CU3
    GC3 --> CU4
```

## 🔄 请求处理流程

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant Server as ANP_Server
    participant Router as GlobalRouter
    participant Agent as Target Agent
    participant ANPUser as ANPUser
    
    Client->>Server: HTTP请求
    Server->>Server: 中间件处理
    Server->>Router: 路由请求
    Router->>Router: 解析DID和路径
    Router->>Agent: 查找目标Agent
    Agent->>Agent: 验证权限
    Agent->>ANPUser: 执行业务逻辑
    ANPUser->>ANPUser: 处理数据
    ANPUser->>Agent: 返回结果
    Agent->>Router: 响应数据
    Router->>Server: 格式化响应
    Server->>Client: HTTP响应
```

## 📊 监控和日志架构

```mermaid
graph TB
    subgraph "日志系统"
        L1[setup_logging]
        L2[日志配置<br/>log_settings]
        L3[日志文件<br/>tmp_log/app.log]
        L4[日志级别<br/>Debug/Info/Error]
    end
    
    subgraph "监控指标"
        M1[Agent状态监控]
        M2[API调用统计]
        M3[消息传递统计]
        M4[错误率监控]
    end
    
    subgraph "调试工具"
        D1[Agent健康检查<br/>/health]
        D2[系统状态<br/>/status]
        D3[接口文档<br/>api_interface.*]
        D4[Agent描述<br/>ad.json]
    end
    
    L1 --> L2
    L2 --> L3
    L2 --> L4
    M1 --> L3
    M2 --> L3
    M3 --> L3
    M4 --> L3
    D1 --> M1
    D2 --> M2
    D3 --> D4
```

---

## 🎯 架构特点

### ✅ 优势

1. **模块化设计**: 清晰的分层架构，职责分离
2. **可扩展性**: 支持动态添加Agent和服务
3. **标准化通信**: 基于DID的统一身份和通信协议
4. **灵活配置**: 支持代码和配置文件两种开发模式
5. **完整生态**: 从开发到部署的完整工具链

### 🔧 核心设计原则

1. **单一职责**: 每个组件专注于特定功能
2. **松耦合**: 组件间通过标准接口通信
3. **高内聚**: 相关功能集中在同一模块
4. **可测试**: 支持单元测试和集成测试
5. **可维护**: 清晰的代码结构和文档

### 🚀 扩展点

1. **自定义Agent**: 通过装饰器或配置文件
2. **服务处理器**: 扩展anp_servicepoint功能
3. **中间件**: 添加认证、限流等功能
4. **存储后端**: 支持不同的数据存储方案
5. **通信协议**: 支持WebSocket、gRPC等协议

---

*架构图最后更新: 2024年1月*
