# ANP Open SDK for Node.js

ANP Open SDK 的 Node.js/TypeScript 实现版本，用于构建去中心化智能体网络。

## 🚀 核心目标

**ANP Open SDK 的核心目标是让智能体网络开发者可以快速、高效地搭建基于 `agent_connect` 核心协议的 ANP 智能体网络**，推动由可互操作、智能化、去中心化 Agent 组成的生态繁荣。

## 🏗️ 架构设计

本 SDK 采用模块化的4层架构：

### 1. `foundation` - 基础层
- **用户管理**：DID 用户身份管理
- **认证系统**：JWT + 加密认证
- **配置管理**：统一配置管理
- **工具库**：通用工具函数

### 2. `servicepoint` - 服务层
- **HTTP处理器**：请求响应处理
- **中间件**：认证、日志等中间件
- **API路由**：服务端点管理

### 3. `runtime` - 智能体运行时层
- **Agent核心**：Agent类和管理器
- **装饰器**：API暴露和消息处理装饰器
- **服务调用**：P2P通信和服务调用

### 4. `server` - 服务器层
- **Express集成**：HTTP服务器
- **路由管理**：RESTful API路由

## ⚡ 快速开始

### 安装依赖
```bash
npm install
```

### 开发模式
```bash
npm run dev
```

### 构建项目
```bash
npm run build
```

### 运行测试
```bash
npm test
```

## 📚 技术栈

- **运行时**：Node.js 18+
- **语言**：TypeScript
- **Web框架**：Express.js
- **加密**：jose, crypto
- **HTTP客户端**：axios
- **装饰器**：reflect-metadata

## 📄 许可证

Apache License 2.0