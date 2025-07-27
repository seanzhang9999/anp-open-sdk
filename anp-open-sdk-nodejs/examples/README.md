# ANP Node.js SDK 示例文档

欢迎使用ANP Node.js SDK示例集合！本文档详细介绍了五个核心示例，帮助您快速理解和使用ANP Agent系统的各种功能。

## 📋 目录

- [ANP Node.js SDK 示例文档](#anp-nodejs-sdk-示例文档)
  - [📋 目录](#-目录)
  - [🚀 环境准备](#-环境准备)
    - [系统要求](#系统要求)
    - [安装依赖](#安装依赖)
    - [环境配置](#环境配置)
  - [📊 示例概览](#-示例概览)
  - [📖 详细示例说明](#-详细示例说明)
    - [1. flow-anp-agent.ts - 主要演示文件](#1-flow-anp-agentts---主要演示文件)
    - [2. functional-approach-example.ts - 函数式方法](#2-functional-approach-examplets---函数式方法)
    - [3. simple-decorators-example.ts - 简化装饰器](#3-simple-decorators-examplets---简化装饰器)
    - [4. type-safe-decorators-example.ts - 类型安全装饰器](#4-type-safe-decorators-examplets---类型安全装饰器)
    - [5. working-type-safe-decorators-example.ts - 完整工作示例](#5-working-type-safe-decorators-examplets---完整工作示例)
  - [🎯 学习路径建议](#-学习路径建议)
    - [初学者路径](#初学者路径)
    - [开发者路径](#开发者路径)
    - [生产环境建议](#生产环境建议)
  - [🔧 故障排除](#-故障排除)
    - [常见问题](#常见问题)
      - [1. 装饰器不工作](#1-装饰器不工作)
      - [2. 模块导入错误](#2-模块导入错误)
      - [3. TypeScript编译错误](#3-typescript编译错误)
      - [4. 运行时错误](#4-运行时错误)
    - [调试技巧](#调试技巧)
      - [1. 启用详细日志](#1-启用详细日志)
      - [2. 检查Agent状态](#2-检查agent状态)
      - [3. 验证API路由](#3-验证api路由)
  - [🏆 最佳实践](#-最佳实践)
    - [1. Agent设计原则](#1-agent设计原则)
    - [2. 代码组织](#2-代码组织)
    - [3. 错误处理](#3-错误处理)
    - [4. 性能优化](#4-性能优化)
    - [5. 安全考虑](#5-安全考虑)
    - [6. 测试策略](#6-测试策略)
  - [📞 获取帮助](#-获取帮助)

## 🚀 环境准备

### 系统要求
- Node.js >= 16.0.0
- TypeScript >= 4.5.0
- npm 或 yarn

### 安装依赖
```bash
# 进入项目目录
cd anp-open-sdk-nodejs

# 安装依赖
npm install

# 确保data_user目录存在
mkdir -p data_user
```

### 环境配置
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件（如需要）
# vim .env
```

## 📊 示例概览

| 示例文件 | 主要特性 | 难度级别 | 推荐用途 |
|---------|---------|---------|---------|
| [`flow-anp-agent.ts`](./flow-anp-agent.ts) | 装饰器Agent创建、完整功能演示 | ⭐⭐⭐ | 学习核心概念 |
| [`functional-approach-example.ts`](./functional-approach-example.ts) | 函数式创建、配置对象方式 | ⭐⭐ | 批量创建Agent |
| [`simple-decorators-example.ts`](./simple-decorators-example.ts) | 简化装饰器、群组事件处理 | ⭐⭐ | 快速原型开发 |
| [`type-safe-decorators-example.ts`](./type-safe-decorators-example.ts) | 类型安全、完整TypeScript支持 | ⭐⭐⭐⭐ | 生产环境开发 |
| [`working-type-safe-decorators-example.ts`](./working-type-safe-decorators-example.ts) | 完整工作示例、最佳实践 | ⭐⭐⭐⭐⭐ | 参考实现 |

## 📖 详细示例说明

### 1. flow-anp-agent.ts - 主要演示文件

**🎯 用途和目标**
- 完全复现Python版本的Agent功能
- 展示装饰器方式创建Agent的完整流程
- 演示Agent管理器和全局消息管理器的使用

**⚡ 核心特性**
- 使用 `@agentClass` 装饰器创建Agent类
- 支持 `@classApi` 和 `@classMessageHandler` 装饰器
- 演示计算器、天气、助手三种不同类型的Agent
- 展示共享DID和独占DID的使用方式
- 完整的Agent状态管理和调试信息

**🔧 技术亮点**
- 装饰器模式的完整实现
- Agent生命周期管理
- API路由自动注册
- 消息处理器自动绑定
- 统计和调试信息展示

**▶️ 运行方法**
```bash
npx ts-node examples/flow-anp-agent.ts
```

**📋 预期输出**
```
[DEBUG] 🚀 Starting Agent System Demo...
[DEBUG] 🧹 已清除之前的Agent注册记录
[DEBUG] 🤖 创建代码生成的Agent...
[DEBUG] ✅ 创建代码生成计算器Agent成功
[DEBUG] ✅ 创建代码生成天气Agent成功
[DEBUG] ✅ 创建代码生成助手Agent成功

[DEBUG] 📊 Agent管理器状态:
[DEBUG]   DID: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973共有1个agent
[DEBUG]     - 代码生成计算器: 独占
[DEBUG]   DID: did:wba:localhost%3A9527:wba:user:5fea49e183c6c211共有2个agent
[DEBUG]     - 代码生成天气: 共享 (主) prefix:/weather
[DEBUG]     - 代码生成助手: 共享 prefix:/assistant

[DEBUG] 💬 全局消息管理器状态:
[DEBUG]   💬 did:wba:localhost%3A9527:wba:user:27c0b1d11180f973:text <- 代码生成计算器
[DEBUG]   💬 did:wba:localhost%3A9527:wba:user:5fea49e183c6c211:text <- 代码生成天气

[DEBUG] 🔍 调试：检查Agent的API路由注册情况...
[DEBUG] Agent: 代码生成计算器
[DEBUG]   DID: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973
[DEBUG]   API路由数量: 2
[DEBUG]     - /add: addApi
[DEBUG]     - /multiply: multiplyApi

[DEBUG] 🎉 Agent系统演示完成!
```

**🎓 适用场景**
- 学习ANP Agent系统的基本概念
- 理解装饰器模式在Agent创建中的应用
- 掌握Agent管理器的使用方法

**📚 学习重点**
- Agent装饰器的使用方法
- API和消息处理器的注册机制
- 共享DID vs 独占DID的区别
- Agent状态管理和调试技巧

---

### 2. functional-approach-example.ts - 函数式方法

**🎯 用途和目标**
- 避免装饰器的复杂性，使用纯函数式API
- 展示配置对象方式创建Agent
- 演示批量创建Agent系统的方法

**⚡ 核心特性**
- 使用 `createAgentWithConfig` 函数创建Agent
- 支持预定义的Agent创建函数（`createCalculatorAgent`, `createWeatherAgent`）
- 批量创建Agent系统（`createAgentSystem`）
- Python兼容的创建方式（`createAgentsWithCode`）
- 全局消息管理器的完整使用

**🔧 技术亮点**
- 配置驱动的Agent创建
- 类型安全的配置接口
- 批量操作支持
- 跨语言兼容性
- 灵活的API和消息处理器配置

**▶️ 运行方法**
```bash
npx ts-node examples/functional-approach-example.ts
```

**📋 预期输出**
```
[DEBUG] 🚀 开始函数式Agent创建示例

[DEBUG] === 预定义Agent示例 ===
[DEBUG] ✅ 创建计算器Agent: 计算器Agent
[DEBUG]    API路由数量: 2
[DEBUG]    消息处理器数量: 1
[DEBUG] ✅ 创建天气Agent: 天气Agent
[DEBUG]    API路由数量: 2
[DEBUG]    消息处理器数量: 1

[DEBUG] === 自定义Agent创建示例 ===
[DEBUG] ✅ 创建智能助手Agent: 智能助手
[DEBUG]    DID: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973
[DEBUG]    API路由: /help, /status
[DEBUG]    消息类型: help, text

[DEBUG] === 批量Agent创建示例 ===
[DEBUG] ✅ 批量创建完成，共创建3个Agent:
[DEBUG]    - 数据分析Agent (API: 1, 消息: 0)
[DEBUG]    - 文件管理Agent (API: 1, 消息: 0)
[DEBUG]    - 通知Agent (API: 0, 消息: 1)

[DEBUG] === Python兼容创建示例 ===
[DEBUG] ✅ Python兼容创建完成，共3个Agent
[DEBUG] DID: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973
[DEBUG]   - 计算器服务: 独占 (主)
[DEBUG]   - 天气服务: 共享 prefix:weather
[DEBUG]   - 翻译服务: 共享 prefix:translate

[DEBUG] ✅ 函数式Agent创建示例完成
```

**🎓 适用场景**
- 需要动态创建大量Agent的场景
- 配置驱动的Agent系统
- 与Python版本保持兼容的项目
- 不希望使用装饰器的开发场景

**📚 学习重点**
- 函数式Agent创建的优势
- 配置对象的结构和使用
- 批量操作的实现方式
- 跨语言兼容性的考虑

---

### 3. simple-decorators-example.ts - 简化装饰器

**🎯 用途和目标**
- 提供简化的装饰器系统
- 结合类装饰器和函数式方法
- 演示群组事件处理功能

**⚡ 核心特性**
- 简化的 `@agentClass`, `@classApi`, `@classMessageHandler` 装饰器
- 支持 `@groupEventMethod` 群组事件装饰器
- 函数式创建方法（`createAgent`, `createSharedAgent`）
- 批量创建系统（`createAgentsWithCode`）
- 全局消息管理器集成

**🔧 技术亮点**
- 装饰器和函数式方法的混合使用
- 群组事件处理机制
- 简化的API设计
- 灵活的Agent配置选项
- 统计和调试功能

**▶️ 运行方法**
```bash
npx ts-node examples/simple-decorators-example.ts
```

**📋 预期输出**
```
[DEBUG] 🚀 开始简化装饰器示例

[DEBUG] === 类装饰器方式 ===
[DEBUG] 计算器Agent: 计算器Agent
[DEBUG] 天气Agent: 天气Agent

[DEBUG] === 函数式Agent创建示例 ===
[DEBUG] ✅ 创建助手Agent: 智能助手
[DEBUG] ✅ 创建共享Agent: 共享服务

[DEBUG] === 批量Agent系统创建示例 ===
[DEBUG] ✅ 批量创建完成，共3个Agent
[DEBUG] Agent系统统计: {
  totalAgents: 3,
  sharedAgents: 2,
  primaryAgents: 1
}

[DEBUG] === 全局消息管理器示例 ===
[DEBUG] 消息处理器统计: [
  { did: "global", msgType: "system", agentName: "GlobalHandler" },
  { did: "global", msgType: "user", agentName: "GlobalHandler" }
]
[DEBUG] 系统消息处理器数量: 1

[DEBUG] === 最终统计 ===
[DEBUG] 总Agent数量: 8
[DEBUG]   - 计算器Agent (DID: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973)
[DEBUG]   - 天气Agent (DID: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973)
[DEBUG]   - 智能助手 (DID: did:wba:localhost%3A9527:wba:user:another_user)

[DEBUG] ✅ 简化装饰器示例完成
```

**🎓 适用场景**
- 快速原型开发
- 需要群组事件处理的应用
- 希望使用简化API的项目
- 混合使用装饰器和函数式方法的场景

**📚 学习重点**
- 简化装饰器的使用方法
- 群组事件处理机制
- 装饰器与函数式方法的结合
- Agent系统的统计和监控

---

### 4. type-safe-decorators-example.ts - 类型安全装饰器

**🎯 用途和目标**
- 提供完整的TypeScript类型支持
- 展示类型安全的装饰器系统
- 演示参数类型定义和验证

**⚡ 核心特性**
- 类型安全的 `@agentClass`, `@classApi`, `@classMessageHandler` 装饰器
- 完整的参数类型定义支持
- 支持 `@groupEventMethod` 群组事件装饰器
- 函数式装饰器（`agentApi`, `agentMessageHandler`）
- 编译时类型检查

**🔧 技术亮点**
- 完整的TypeScript类型系统集成
- 参数类型定义和文档生成
- 编译时错误检查
- IDE智能提示支持
- 类型安全的API设计

**▶️ 运行方法**
```bash
npx ts-node examples/type-safe-decorators-example.ts
```

**📋 预期输出**
```
[DEBUG] 🚀 Starting Type-Safe Decorators Demo...
[DEBUG] 🧹 已清除之前的Agent注册记录
[DEBUG] 🤖 使用类型安全装饰器创建Agent...
[DEBUG] ✅ 创建类型安全计算器Agent成功
[DEBUG] ✅ 创建类型安全天气Agent成功
[DEBUG] ✅ 创建类型安全助手Agent成功

[DEBUG] 📊 Agent管理器状态:
[DEBUG]   DID: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973共有1个agent
[DEBUG]     - 类型安全计算器: 独占
[DEBUG]   DID: did:wba:localhost%3A9527:wba:user:5fea49e183c6c211共有2个agent
[DEBUG]     - 类型安全天气: 共享 (主) prefix:/weather
[DEBUG]     - 类型安全助手: 共享 prefix:/assistant

[DEBUG] 💬 全局消息管理器状态:
[DEBUG]   💬 did:wba:localhost%3A9527:wba:user:27c0b1d11180f973:text <- 类型安全计算器
[DEBUG]   💬 did:wba:localhost%3A9527:wba:user:5fea49e183c6c211:text <- 类型安全天气

[DEBUG] 🎉 类型安全装饰器演示完成!
[DEBUG] 📝 类型安全装饰器的优势:
[DEBUG]   ✅ 编译时类型检查
[DEBUG]   ✅ 完整的IDE智能提示
[DEBUG]   ✅ 避免运行时类型错误
[DEBUG]   ✅ 与Python版本功能完全对等
```

**🎓 适用场景**
- 大型项目开发
- 需要严格类型检查的应用
- 团队协作开发
- 生产环境部署

**📚 学习重点**
- TypeScript类型系统的高级用法
- 类型安全装饰器的实现原理
- 参数类型定义的最佳实践
- 编译时错误检查的优势

---

### 5. working-type-safe-decorators-example.ts - 完整工作示例

**🎯 用途和目标**
- 展示完整的工作示例
- 集成所有功能演示
- 提供最佳实践参考
- 展示统计和调试信息

**⚡ 核心特性**
- 完整的类型安全装饰器系统
- 所有功能的综合演示
- 详细的统计和调试信息
- 最佳实践的完整实现
- 生产就绪的代码结构

**🔧 技术亮点**
- 完整的Agent生命周期管理
- 综合的错误处理机制
- 详细的日志和调试信息
- 性能监控和统计
- 模块化的代码组织

**▶️ 运行方法**
```bash
npx ts-node examples/working-type-safe-decorators-example.ts
```

**📋 预期输出**
```
[DEBUG] 🚀 开始类型安全装饰器示例

[DEBUG] === 类装饰器方式 ===
[DEBUG] 计算器Agent: 计算器Agent
[DEBUG] 天气Agent: 天气Agent

[DEBUG] === 函数式Agent创建示例 ===
[DEBUG] ✅ 创建助手Agent: 智能助手
[DEBUG] ✅ 创建共享Agent: 共享服务

[DEBUG] === 批量Agent系统创建示例 ===
[DEBUG] ✅ 批量创建完成，共3个Agent
[DEBUG] Agent系统统计: {
  totalAgents: 3,
  sharedAgents: 2,
  primaryAgents: 1,
  apiRoutes: 8,
  messageHandlers: 5
}

[DEBUG] === 全局消息管理器示例 ===
[DEBUG] 消息处理器统计: [
  { did: "global", msgType: "system", agentName: "GlobalHandler" },
  { did: "global", msgType: "user", agentName: "GlobalHandler" }
]
[DEBUG] 系统消息处理器数量: 1

[DEBUG] === 最终统计 ===
[DEBUG] Agent管理器统计: {
  totalAgents: 8,
  totalDIDs: 3,
  sharedAgents: 5,
  primaryAgents: 3,
  totalApiRoutes: 15,
  totalMessageHandlers: 8
}
[DEBUG] 总Agent数量: 8
[DEBUG]   - 计算器Agent (DID: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973)
[DEBUG]   - 天气Agent (DID: did:wba:localhost%3A9527:wba:user:27c0b1d11180f973)
[DEBUG]   - 智能助手 (DID: did:wba:localhost%3A9527:wba:user:another_user)

[DEBUG] ✅ 类型安全装饰器示例完成
```

**🎓 适用场景**
- 生产环境部署
- 完整功能演示
- 代码参考和学习
- 性能测试和优化

**📚 学习重点**
- 完整Agent系统的架构设计
- 生产环境的最佳实践
- 性能监控和调试技巧
- 错误处理和异常管理

## 🎯 学习路径建议

### 初学者路径
1. **开始** → [`flow-anp-agent.ts`](./flow-anp-agent.ts)
   - 理解基本概念和装饰器使用
   - 学习Agent的创建和管理

2. **进阶** → [`simple-decorators-example.ts`](./simple-decorators-example.ts)
   - 掌握简化的装饰器系统
   - 学习群组事件处理

3. **深入** → [`functional-approach-example.ts`](./functional-approach-example.ts)
   - 理解函数式创建方法
   - 学习批量操作和配置管理

### 开发者路径
1. **类型安全** → [`type-safe-decorators-example.ts`](./type-safe-decorators-example.ts)
   - 掌握TypeScript类型系统
   - 学习类型安全的API设计

2. **最佳实践** → [`working-type-safe-decorators-example.ts`](./working-type-safe-decorators-example.ts)
   - 学习生产环境的最佳实践
   - 掌握完整的系统架构

### 生产环境建议
- 使用 [`type-safe-decorators-example.ts`](./type-safe-decorators-example.ts) 作为基础
- 参考 [`working-type-safe-decorators-example.ts`](./working-type-safe-decorators-example.ts) 的完整实现
- 根据需要选择函数式或装饰器方法

## 🔧 故障排除

### 常见问题

#### 1. 装饰器不工作
**问题**: 装饰器没有正确注册Agent或API
```bash
Error: Agent not found or API route not registered
```

**解决方案**:
```bash
# 确保启用了装饰器支持
npm install reflect-metadata

# 在代码顶部添加
import 'reflect-metadata';

# 检查tsconfig.json配置
{
  "compilerOptions": {
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true
  }
}
```

#### 2. 模块导入错误
**问题**: 无法导入相关模块
```bash
Error: Cannot find module '../src/runtime'
```

**解决方案**:
```bash
# 确保在正确的目录下运行
cd anp-open-sdk-nodejs

# 重新安装依赖
npm install

# 检查文件路径是否正确
ls -la src/runtime/
```

#### 3. TypeScript编译错误
**问题**: TypeScript类型检查失败
```bash
Error: Type 'any' is not assignable to type 'AgentConfig'
```

**解决方案**:
```bash
# 更新TypeScript版本
npm install -D typescript@latest

# 检查类型定义
npm run type-check

# 使用正确的类型注解
const config: AgentConfig = { ... };
```

#### 4. 运行时错误
**问题**: Agent创建失败或API调用失败
```bash
Error: Failed to create agent or API call failed
```

**解决方案**:
```bash
# 检查data_user目录权限
chmod -R 755 data_user/

# 清理之前的状态
rm -rf data_user/*

# 重新运行示例
npx ts-node examples/flow-anp-agent.ts
```

### 调试技巧

#### 1. 启用详细日志
```typescript
// 在代码中添加详细日志
import { getLogger } from '../src/foundation/utils';
const logger = getLogger('YourComponent');
logger.debug('详细调试信息');
```

#### 2. 检查Agent状态
```typescript
// 检查Agent管理器状态
const agentsInfo = AgentManager.listAgents();
console.log('Agent状态:', JSON.stringify(agentsInfo, null, 2));

// 检查全局消息管理器
const handlers = GlobalMessageManager.listHandlers();
console.log('消息处理器:', handlers);
```

#### 3. 验证API路由
```typescript
// 检查Agent的API路由
for (const agent of allAgents) {
  if (agent.anpUser) {
    console.log(`Agent: ${agent.name}`);
    console.log(`API路由:`, Array.from(agent.anpUser.apiRoutes.keys()));
  }
}
```

## 🏆 最佳实践

### 1. Agent设计原则
- **单一职责**: 每个Agent应该有明确的单一职责
- **松耦合**: Agent之间应该保持松耦合关系
- **可测试**: 设计时考虑单元测试的便利性
- **可扩展**: 预留扩展接口和配置选项

### 2. 代码组织
```typescript
// 推荐的项目结构
src/
├── agents/           # Agent实现
│   ├── calculator/   # 计算器Agent
│   ├── weather/      # 天气Agent
│   └── assistant/    # 助手Agent
├── config/           # 配置文件
├── types/            # 类型定义
└── utils/            # 工具函数
```

### 3. 错误处理
```typescript
// 统一的错误处理
try {
  const result = await agent.processRequest(data);
  return result;
} catch (error) {
  logger.error(`Agent处理失败: ${error.message}`);
  return { error: '处理失败', details: error.message };
}
```

### 4. 性能优化
- 使用连接池管理数据库连接
- 实现请求缓存机制
- 合理设置超时时间
- 监控内存使用情况

### 5. 安全考虑
- 验证输入参数
- 实现访问控制
- 记录审计日志
- 定期更新依赖

### 6. 测试策略
```typescript
// 单元测试示例
describe('CalculatorAgent', () => {
  let agent: CalculatorAgent;
  
  beforeEach(() => {
    agent = new CalculatorAgent();
  });
  
  it('should perform addition correctly', async () => {
    const result = await agent.addApi({ params: { a: 2, b: 3 } }, {});
    expect(result.result).toBe(5);
  });
});
```

## 📞 获取帮助

如果您在使用过程中遇到问题，可以通过以下方式获取帮助：

1. **查看文档**: 阅读项目根目录下的README.md
2. **检查日志**: 查看详细的调试日志信息
3. **参考示例**: 对比工作正常的示例代码
4. **社区支持**: 在项目仓库中提交Issue

---

**🎉 恭喜！您已经掌握了ANP Node.js SDK的核心功能。开始构建您的Agent系统吧！**