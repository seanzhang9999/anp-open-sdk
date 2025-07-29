# ANP Open SDK Node.js 目录结构

本文档提供了ANP Open SDK Node.js版本的完整目录结构概览，包括所有主要目录及其文件列表。这有助于开发者快速了解项目的组织结构和各个组件的位置。

## 目录

- [ANP Open SDK Node.js 目录结构](#anp-open-sdk-nodejs-目录结构)
  - [目录](#目录)
  - [简介](#简介)
  - [Examples 目录](#examples-目录)
  - [Docs 目录](#docs-目录)
  - [Scripts 目录](#scripts-目录)
  - [Src 目录](#src-目录)
    - [Foundation 子目录](#foundation-子目录)
    - [Runtime 子目录](#runtime-子目录)
    - [Server 子目录](#server-子目录)
    - [ServicePoint 子目录](#servicepoint-子目录)
  - [Tests 目录](#tests-目录)
    - [基础组件测试](#基础组件测试)
    - [跨语言兼容性测试](#跨语言兼容性测试)
    - [测试配置和工具](#测试配置和工具)

## 简介

ANP Open SDK Node.js是一个用于开发ANP（Agent Network Protocol）应用的TypeScript/JavaScript SDK。该SDK提供了一系列工具和接口，用于创建、管理和与ANP网络交互的代理（Agent）。项目结构清晰地分为几个主要部分，包括示例代码、文档、脚本、源代码和测试文件。

## Examples 目录

Examples目录包含了SDK使用的示例代码，展示了不同的实现方法和模式。

```
examples/
├── README.md
├── flow-anp-agent.ts
├── functional-approach-example.ts
├── simple-decorators-example.ts
├── type-safe-decorators-example.ts
└── working-type-safe-decorators-example.ts
```

这个目录提供了多种使用SDK的示例，包括流式ANP代理、函数式方法以及不同类型的装饰器实现方式。这些示例对于新用户理解SDK的使用方法非常有价值。

## Docs 目录

Docs目录包含项目的技术文档，提供了SDK的设计理念、实现细节和使用指南。

```
docs/
├── project-completion-summary.md
├── runtime-implementation-summary.md
├── testing-guide.md
└── typescript-decorators-analysis.md
```

这些文档涵盖了项目完成摘要、运行时实现摘要、测试指南以及TypeScript装饰器分析等内容，为开发者提供了深入了解SDK的资源。

## Scripts 目录

Scripts目录包含用于项目开发、测试和部署的脚本文件。

```
scripts/
└── test-demo.sh
```

目前只有一个测试演示脚本，用于展示和测试SDK的功能。

## Src 目录

Src目录是SDK的核心，包含所有源代码文件。它被组织成几个主要的子目录，每个子目录负责不同的功能领域。

```
src/
├── debug-test.ts
├── example.ts
├── index.ts
├── test-api-url.ts
├── foundation/
├── runtime/
├── server/
└── servicepoint/
```

顶层文件包括主入口点（index.ts）、示例和测试文件。

### Foundation 子目录

Foundation子目录包含SDK的基础组件，提供核心功能和数据结构。

```
foundation/
├── index.ts
├── auth/
│   ├── auth-initiator.ts
│   ├── auth-verifier.ts
│   ├── auth.ts
│   └── index.ts
├── config/
│   ├── index.ts
│   ├── manager.ts
│   ├── types.ts
│   └── unified-config.ts
├── contact/
│   ├── contact-manager.ts
│   └── index.ts
├── did/
│   ├── did-tool.ts
│   ├── did-url-formatter.ts
│   ├── did-wba-auth-client.ts
│   ├── did-wba.ts
│   ├── index.ts
│   ├── types.ts
│   └── verification-methods.ts
├── domain/
│   ├── domain-manager.ts
│   └── index.ts
├── test-utils/
│   └── index.ts
├── types/
│   └── index.ts
├── user/
│   ├── anp-user.ts
│   ├── create-did-user.ts
│   ├── index.ts
│   ├── local-user-data-manager.ts
│   └── local-user-data.ts
└── utils/
    └── index.ts
```

Foundation包含了认证（auth）、配置（config）、联系人管理（contact）、DID（分布式标识符）、域管理（domain）、用户管理（user）等核心功能模块。这些模块为SDK的其他部分提供了基础设施。

### Runtime 子目录

Runtime子目录包含与代理运行时相关的代码，负责代理的生命周期管理和执行。

```
runtime/
├── index.ts
├── core/
│   ├── agent-manager.ts
│   ├── agent.ts
│   ├── global-message-manager.ts
│   └── index.ts
├── decorators/
│   ├── agent-decorators.ts
│   ├── fix-api-routes.ts
│   ├── functional-approach.ts
│   ├── index.ts
│   ├── simple-decorators.ts
│   └── type-safe-decorators.ts
└── services/
    ├── agent-api-caller.ts
    ├── agent-message-caller.ts
    └── index.ts
```

Runtime包含代理核心（core）、装饰器（decorators）和服务（services）等模块，负责代理的创建、管理和通信。

### Server 子目录

Server子目录包含服务器相关的代码，用于创建和管理ANP服务器。

```
server/
├── index.ts
├── express/
│   ├── anp-server.ts
│   └── index.ts
└── routers/
    ├── anp-routers.ts
    └── index.ts
```

Server包含基于Express的服务器实现和路由定义，用于处理ANP协议的HTTP请求。

### ServicePoint 子目录

ServicePoint子目录包含服务点相关的代码，用于定义和管理不同类型的服务。

```
servicepoint/
├── example.ts
├── index.ts
├── service-point-manager.ts
├── service-point-router.ts
├── handlers/
│   ├── agent-service-handler.ts
│   ├── auth-exempt-handler.ts
│   ├── auth-service-handler.ts
│   ├── did-service-handler.ts
│   ├── host-service-handler.ts
│   ├── index.ts
│   └── publisher-service-handler.ts
└── middleware/
    ├── auth-middleware.ts
    └── index.ts
```

ServicePoint包含服务点管理器、路由器以及各种服务处理程序和中间件，用于处理不同类型的服务请求，如代理服务、认证服务、DID服务等。

## Tests 目录

Tests目录包含了用于测试SDK各个组件功能的测试文件。这些测试确保SDK的各个模块按预期工作，并帮助开发者在修改代码后验证功能完整性。测试采用Jest框架，涵盖了基础组件（foundation）和跨语言兼容性（cross-language）等多个方面。

```
tests/
├── README.md                              # 测试文档说明
├── custom-reporter.js                     # 自定义测试报告生成器
├── setup.ts                               # 测试环境设置脚本
├── cross-language/                        # 跨语言兼容性测试
│   ├── README.md                          # 跨语言测试说明文档
│   ├── python-server-compatibility.test.ts # Python服务器兼容性测试
│   └── test-reporter.ts                   # 测试报告工具
└── foundation/                            # 基础组件测试
    ├── auth-initiator.test.ts             # 认证发起器测试
    ├── contact-manager.test.ts            # 联系人管理器测试
    ├── create-did-user.test.ts            # DID用户创建测试
    ├── did-wba-two-way-auth.test.ts       # DID WBA双向认证测试
    ├── domain-manager.test.ts             # 域管理器测试
    ├── local-user-data-manager.test.ts    # 本地用户数据管理器测试
    ├── local-user-data.test.ts            # 本地用户数据测试
    ├── test-data.test.ts                  # 测试数据工具测试
    └── unified-config.test.ts             # 统一配置测试
```

### 基础组件测试

foundation目录包含了SDK核心基础组件的测试文件，主要测试以下功能：

- **认证系统**：测试认证发起和验证流程（auth-initiator.test.ts）
- **用户管理**：测试用户数据的创建、存储和管理（local-user-data.test.ts, local-user-data-manager.test.ts）
- **DID系统**：测试分布式身份标识相关功能，包括用户创建和双向认证（create-did-user.test.ts, did-wba-two-way-auth.test.ts）
- **配置管理**：测试统一配置系统（unified-config.test.ts）
- **域管理**：测试域名解析和管理功能（domain-manager.test.ts）
- **联系人管理**：测试联系人相关功能（contact-manager.test.ts）
- **测试数据**：提供测试所需的模拟数据和工具（test-data.test.ts）

### 跨语言兼容性测试

cross-language目录包含了确保Node.js SDK与其他语言实现（如Python）兼容性的测试：

- **Python服务器兼容性**：测试Node.js SDK与Python实现的服务器之间的互操作性（python-server-compatibility.test.ts）
- **测试报告工具**：用于生成跨语言测试的报告（test-reporter.ts）

### 测试配置和工具

根目录下的文件提供了测试环境的配置和工具支持：

- **测试环境设置**：setup.ts文件配置Jest测试环境，包括全局设置和模拟对象
- **自定义报告生成**：custom-reporter.js提供了定制化的测试结果报告功能
- **测试文档**：README.md提供了如何运行和扩展测试的说明