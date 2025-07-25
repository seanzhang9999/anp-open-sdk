# ANP Node.js SDK 测试指南

## 测试脚本概览

ANP Node.js SDK 提供了完整的测试框架，包括单元测试、集成测试和性能测试。

## 🚀 快速开始

### 运行所有测试
```bash
# 进入项目目录
cd anp-open-sdk-nodejs

# 安装依赖
npm install

# 运行所有测试
npm test
```

### 监视模式运行测试
```bash
# 监视文件变化，自动重新运行测试
npm run test:watch
```

## 📋 可用的测试脚本

### 基本测试命令

| 命令 | 描述 | 用途 |
|------|------|------|
| `npm test` | 运行所有测试 | 完整的测试套件 |
| `npm run test:watch` | 监视模式运行测试 | 开发时持续测试 |

### 高级测试命令

```bash
# 运行特定测试文件
npx jest tests/foundation/local-user-data.test.ts

# 运行特定测试套件
npx jest tests/foundation/

# 运行测试并生成覆盖率报告
npx jest --coverage

# 运行测试并输出详细信息
npx jest --verbose

# 运行测试并更新快照
npx jest --updateSnapshot

# 运行失败的测试
npx jest --onlyFailures

# 运行特定模式的测试
npx jest --testNamePattern="LocalUserData"
```

## 📁 测试文件结构

```
anp-open-sdk-nodejs/
├── tests/
│   ├── setup.ts                           # 测试环境设置
│   └── foundation/                        # Foundation层测试
│       ├── auth-initiator.test.ts         # 认证发起器测试
│       ├── contact-manager.test.ts        # 联系人管理器测试
│       ├── create-did-user.test.ts        # DID用户创建测试
│       ├── did-wba-two-way-auth.test.ts   # 双向认证测试
│       ├── domain-manager.test.ts         # 域名管理器测试
│       ├── local-user-data-manager.test.ts # 用户数据管理器测试
│       ├── local-user-data.test.ts        # 用户数据测试
│       ├── test-data.test.ts              # 测试数据验证
│       └── unified-config.test.ts         # 统一配置测试
├── jest.config.js                         # Jest配置文件
└── package.json                          # 包含测试脚本
```

## 🔧 测试配置

### Jest 配置 (`jest.config.js`)

```javascript
module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'node',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: [
    '**/__tests__/**/*.ts',
    '**/?(*.)+(spec|test).ts'
  ],
  collectCoverageFrom: [
    'src/**/*.ts',
    '!src/**/*.d.ts',
    '!src/index.ts',
    '!src/**/__tests__/**',
    '!src/**/test-utils/**'
  ],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 85,
      lines: 85,
      statements: 85
    }
  },
  setupFilesAfterEnv: ['<rootDir>/tests/setup.ts'],
  testTimeout: 30000
};
```

### 测试环境设置 (`tests/setup.ts`)

测试环境会自动：
- 验证测试数据完整性
- 设置全局测试配置
- 提供自定义Jest匹配器
- 配置错误处理

## 📊 测试覆盖率

### 覆盖率目标
- **分支覆盖率**: 80%
- **函数覆盖率**: 85%
- **行覆盖率**: 85%
- **语句覆盖率**: 85%

### 生成覆盖率报告
```bash
# 生成覆盖率报告
npx jest --coverage

# 查看HTML覆盖率报告
open coverage/lcov-report/index.html
```

## 🧪 测试类型

### 1. Foundation层测试

#### 用户数据管理测试
```bash
# 运行用户数据相关测试
npx jest tests/foundation/local-user-data

# 运行用户数据管理器测试
npx jest tests/foundation/local-user-data-manager
```

#### 认证系统测试
```bash
# 运行认证发起器测试
npx jest tests/foundation/auth-initiator

# 运行双向认证测试
npx jest tests/foundation/did-wba-two-way-auth
```

#### 域名管理测试
```bash
# 运行域名管理器测试
npx jest tests/foundation/domain-manager
```

#### 联系人管理测试
```bash
# 运行联系人管理器测试
npx jest tests/foundation/contact-manager
```

#### 配置管理测试
```bash
# 运行统一配置测试
npx jest tests/foundation/unified-config
```

### 2. 测试数据验证
```bash
# 验证测试数据完整性
npx jest tests/foundation/test-data
```

## 🔍 调试测试

### 使用VS Code调试

1. 在VS Code中打开项目
2. 设置断点
3. 按F5或使用调试面板
4. 选择"Jest Tests"配置

### 命令行调试
```bash
# 使用Node.js调试器
node --inspect-brk node_modules/.bin/jest --runInBand tests/foundation/local-user-data.test.ts

# 使用VS Code调试
npx jest --runInBand --no-cache tests/foundation/local-user-data.test.ts
```

## 📝 编写新测试

### 测试文件命名规范
- 单元测试: `*.test.ts`
- 集成测试: `*.integration.test.ts`
- 端到端测试: `*.e2e.test.ts`

### 测试模板
```typescript
import { describe, test, expect, beforeEach, afterEach } from '@jest/globals';

describe('YourModule', () => {
  beforeEach(() => {
    // 测试前设置
  });

  afterEach(() => {
    // 测试后清理
  });

  test('should do something', () => {
    // 测试实现
    expect(true).toBe(true);
  });

  test('should handle errors', async () => {
    // 异步测试
    await expect(async () => {
      throw new Error('Test error');
    }).rejects.toThrow('Test error');
  });
});
```

### 自定义匹配器

项目提供了自定义Jest匹配器：

```typescript
// 验证DID格式
expect('did:wba:localhost%3A9527:wba:user:27c0b1d11180f973').toBeValidDID();

// 验证用户目录文件
expect(['did_document.json', 'agent_cfg.yaml']).toHaveRequiredUserFiles();
```

## 🚨 常见问题

### 1. 测试数据不存在
```
❌ data_user目录不存在，请确保项目根目录包含测试数据
```

**解决方案**: 确保项目根目录包含`data_user`目录和测试数据。

### 2. 测试超时
```
Timeout - Async callback was not invoked within the 30000 ms timeout
```

**解决方案**: 
- 检查异步操作是否正确处理
- 增加测试超时时间
- 使用`jest.setTimeout(60000)`

### 3. 模块路径问题
```
Cannot resolve module '@foundation/...'
```

**解决方案**: 检查`jest.config.js`中的`moduleNameMapper`配置。

### 4. TypeScript编译错误
```
TypeScript compilation error
```

**解决方案**: 
- 运行`npm run build`检查TypeScript错误
- 确保`tsconfig.json`配置正确

## 📈 性能测试

### 基准测试
```bash
# 运行性能测试（如果有）
npx jest --testNamePattern="performance|benchmark"
```

### 内存泄漏检测
```bash
# 使用--detectOpenHandles检测资源泄漏
npx jest --detectOpenHandles --forceExit
```

## 🔄 持续集成

### GitHub Actions示例
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm install
      - run: npm test
      - run: npm run build
```

## 📚 最佳实践

### 1. 测试组织
- 按功能模块组织测试文件
- 使用描述性的测试名称
- 保持测试独立性

### 2. 测试数据
- 使用真实但匿名化的测试数据
- 避免硬编码测试数据
- 使用工厂函数创建测试对象

### 3. 异步测试
- 正确处理Promise和async/await
- 使用适当的超时设置
- 避免测试间的竞态条件

### 4. Mock和Stub
- 合理使用Mock避免外部依赖
- 保持Mock的简单性
- 验证Mock的调用

## 🎯 测试策略

### 测试金字塔
1. **单元测试** (70%) - 测试单个函数和类
2. **集成测试** (20%) - 测试模块间交互
3. **端到端测试** (10%) - 测试完整流程

### 测试优先级
1. **核心业务逻辑** - 用户数据管理、认证系统
2. **API接口** - 公共API的正确性
3. **错误处理** - 异常情况的处理
4. **边界条件** - 极端情况的处理

## 📞 获取帮助

如果在运行测试时遇到问题：

1. 检查[常见问题](#-常见问题)部分
2. 查看测试日志输出
3. 运行`npm run build`检查编译错误
4. 确保所有依赖已正确安装

## 总结

ANP Node.js SDK提供了完整的测试框架，支持：
- ✅ 完整的单元测试覆盖
- ✅ 集成测试支持
- ✅ 自动化测试运行
- ✅ 覆盖率报告
- ✅ 调试支持
- ✅ 持续集成就绪

使用`npm test`即可开始运行所有测试，确保代码质量和功能正确性。