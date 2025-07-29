## 总体结构说明

ANP Open SDK 是一个多语言的去中心化智能体网络开发工具包，旨在基于 `agent_connect` 核心协议构建可互操作的智能体生态系统。

### 项目架构总览

本项目采用**Python为主SDK**的设计理念：
- **主SDK**: Python语言编写，提供完整的ANP协议实现
- **辅助版本**: 基于Python可用版本，通过AI生成Node.js/TypeScript代码
- **根目录资源**: examples、scripts等文件夹均服务于Python SDK
- **核心模块**: foundation（基础层）、runtime（运行时）、servicepoint（服务点）三大核心
- **服务集成**: server文件夹提供集成servicepoint的ANP服务端点示范样例

### 主要目录结构

#### 🐍 `anp-open-sdk-python/` - Python SDK（主SDK）
采用模块化的4层架构设计，提供完整的ANP协议实现：

**核心模块**：
- **`anp_foundation/`** - 基础层模块（核心）
  - [`auth/`](anp-open-sdk-python/anp_foundation/auth/) - 认证系统
  - [`config/`](anp-open-sdk-python/anp_foundation/config/) - 配置管理
  - [`did/`](anp-open-sdk-python/anp_foundation/did/) - DID身份管理
  - [`domain/`](anp-open-sdk-python/anp_foundation/domain/) - 域名管理
  - [`utils/`](anp-open-sdk-python/anp_foundation/utils/) - 工具库

- **`anp_runtime/`** - 运行时模块（核心）
  - [`local_service/`](anp-open-sdk-python/anp_runtime/local_service/) - 本地服务调用
  - [`anp_service/`](anp-open-sdk-python/anp_runtime/anp_service/) - ANP服务管理

- **`anp_servicepoint/`** - 服务点模块（核心）
  - [`core_service_handler/`](anp-open-sdk-python/anp_servicepoint/core_service_handler/) - 核心服务处理器
  - [`extend_service_handler/`](anp-open-sdk-python/anp_servicepoint/extend_service_handler/) - 扩展服务处理器
  - [`extend_service_implementation/`](anp-open-sdk-python/anp_servicepoint/extend_service_implementation/) - 扩展服务实现

**集成示范**：
- **`anp_server/`** - 服务器集成示范
  - [`baseline/`](anp-open-sdk-python/anp_server/baseline/) - 集成servicepoint形成对外ANP服务端点的示范样例
  - [`anp_middleware_baseline/`](anp-open-sdk-python/anp_server/baseline/anp_middleware_baseline/) - 中间件示范
  - [`anp_router_baseline/`](anp-open-sdk-python/anp_server/baseline/anp_router_baseline/) - 路由示范

#### 📦 `anp-open-sdk-nodejs/` - Node.js/TypeScript SDK（AI生成版本）
基于Python主SDK，通过AI生成的Node.js/TypeScript实现，保持架构一致性：

**核心模块**：
- **`src/foundation/`** - 基础层模块（核心）
  - [`auth/`](anp-open-sdk-nodejs/src/foundation/auth/) - 认证系统（JWT + 加密认证）
  - [`config/`](anp-open-sdk-nodejs/src/foundation/config/) - 统一配置管理
  - [`did/`](anp-open-sdk-nodejs/src/foundation/did/) - DID身份管理
  - [`user/`](anp-open-sdk-nodejs/src/foundation/user/) - 用户管理
  - [`contact/`](anp-open-sdk-nodejs/src/foundation/contact/) - 联系人管理
  - [`domain/`](anp-open-sdk-nodejs/src/foundation/domain/) - 域名管理
  - [`utils/`](anp-open-sdk-nodejs/src/foundation/utils/) - 通用工具函数

- **`src/runtime/`** - 智能体运行时层（核心）
  - [`core/`](anp-open-sdk-nodejs/src/runtime/core/) - Agent核心类和管理器
  - [`decorators/`](anp-open-sdk-nodejs/src/runtime/decorators/) - API暴露和消息处理装饰器
  - [`services/`](anp-open-sdk-nodejs/src/runtime/services/) - P2P通信和服务调用

- **`src/servicepoint/`** - 服务层模块（核心）
  - [`handlers/`](anp-open-sdk-nodejs/src/servicepoint/handlers/) - HTTP请求处理器
  - [`middleware/`](anp-open-sdk-nodejs/src/servicepoint/middleware/) - 认证、日志等中间件

**集成示范**：
- **`src/server/`** - 服务器集成示范
  - [`express/`](anp-open-sdk-nodejs/src/server/express/) - 集成servicepoint的Express.js示范样例
  - [`routers/`](anp-open-sdk-nodejs/src/server/routers/) - RESTful API路由管理示范

**开发支持**：
- **`examples/`** - 示例代码和演示项目
- **`tests/`** - 单元测试和集成测试
- **`dev/`** - 开发工具和测试脚本

#### 📁 其他重要目录（服务于Python主SDK）

- **`data_user/`** - 用户数据存储目录
  - 按服务点组织的用户配置和数据
  - Agent配置文件
  - 用户身份信息和托管数据

- **`docs/`** - 项目文档
  - [`nodejs/`](docs/nodejs/) - Node.js版本文档
  - [`python/`](docs/python/) - Python版本文档

- **`examples/`** - 完整示例项目（主要服务于Python SDK）
  - [`flow_anp_agent/`](examples/flow_anp_agent/) - Agent流程示例
  - [`flow_anp_user_portal/`](examples/flow_anp_user_portal/) - 用户门户示例
  - [`flow_host_did/`](examples/flow_host_did/) - DID托管示例

- **`scripts/`** - 项目脚本和工具（主要服务于Python SDK）

### 架构特点

1. **Python主导**：以Python为主SDK，提供完整的ANP协议实现
2. **AI辅助多语言**：通过AI生成Node.js版本，保持架构一致性
3. **三层核心架构**：foundation（基础层）+ runtime（运行时）+ servicepoint（服务点）
4. **模块化设计**：清晰的分层架构，便于维护和扩展
5. **去中心化**：基于DID的身份管理和P2P通信机制
6. **可互操作**：跨语言、跨平台的Agent通信协议
7. **开发友好**：丰富的装饰器、示例代码和开发工具

## python测试方法
### 1. 配置文件
```bash
cp .env.example .env
```

编辑 `.env` 文件，填写你的 `OPENAI_API_KEY`、`OPENAI_API_MODEL_NAME` 和 `OPENAI_API_BASE_URL`。

### 2. 安装依赖

建议使用 Python 虚拟环境管理依赖：

```bash
python -m venv .venv
source .venv/bin/activate 
poetry install
```

### 3. 运行 SDK 测试和 Demo

运行工具和 Demo，验证核心 SDK 是否安装并能正常工作：

```bash
 PYTHONPATH=$PYTHONPATH:/Users/seanzhang/seanrework/anp-open-sdk/anp-open-sdk-python  python scripts/agent_user_binding.py

 PYTHONPATH=$PYTHONPATH:/Users/seanzhang/seanrework/anp-open-sdk/anp-open-sdk-python  python examples/flow_anp_agent/flow_anp_agent.py

```


## nodejs测试方法

### 运行所有测试
```bash
# 进入项目目录
cd anp-open-sdk-nodejs

# 安装依赖
npm install

# 运行所有测试
npm test

# 运行样例代码
npx ts-node examples/flow-anp-agent.ts
```
