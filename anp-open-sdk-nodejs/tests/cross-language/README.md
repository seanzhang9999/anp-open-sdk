# ANP Node.js SDK 跨语言兼容性测试

## 概述

本测试套件验证ANP Node.js SDK与Python服务器的跨语言兼容性，确保Node.js客户端能够成功调用Python服务器的API，并验证认证、数据格式、错误处理等关键功能的互操作性。

## 测试目标

- ✅ **基础连接测试**: 验证Node.js客户端能够连接到Python服务器
- ✅ **API调用兼容性**: 测试Node.js SDK通过[`agent-api-caller.ts`](../../src/runtime/services/agent-api-caller.ts)调用Python服务器API
- ✅ **认证兼容性**: 验证Node.js生成的认证头能被Python服务器正确验证
- ✅ **时间戳格式兼容性**: 确保Node.js毫秒精度时间戳与Python秒精度时间戳的互操作
- ✅ **数据格式兼容性**: 测试JSON序列化/反序列化、不同数据类型、特殊字符处理
- ✅ **错误处理**: 验证各种错误场景的优雅处理
- ✅ **性能验证**: 确保跨语言调用的响应时间和并发处理能力

## 测试环境要求

### Python flow_anp_agent服务器

测试需要Python flow_anp_agent服务器在localhost:9527端口运行。启动命令：

```bash
PYTHONPATH=$PYTHONPATH:/Users/seanzhang/seanrework/anp-open-sdk/anp-open-sdk-python python examples/flow_anp_agent/flow_anp_agent.py
```

### 用户数据

测试使用以下预配置的用户DID：

- **调用者DID**: `did:wba:localhost%3A9527:wba:user:e0959abab6fc3c3d`
- **目标DID**: `did:wba:localhost%3A9527:wba:user:27c0b1d11180f973`

用户数据位于：`data_user/localhost_9527/anp_users/`

## 运行测试

### 完整测试（需要Python服务器）

```bash
# 1. 启动Python flow_anp_agent服务器
PYTHONPATH=$PYTHONPATH:/Users/seanzhang/seanrework/anp-open-sdk/anp-open-sdk-python python examples/flow_anp_agent/flow_anp_agent.py

# 2. 在另一个终端运行测试
cd anp-open-sdk-nodejs
npm test tests/cross-language/python-server-compatibility.test.ts
```

### 离线测试（Python服务器未运行）

如果Python服务器未运行，测试会自动跳过所有需要服务器的测试用例，并显示启动指导：

```
⚠️  Python flow_anp_agent服务器未运行在localhost:9527

请先启动Python服务器：
PYTHONPATH=$PYTHONPATH:/Users/seanzhang/seanrework/anp-open-sdk/anp-open-sdk-python python examples/flow_anp_agent/flow_anp_agent.py

跳过跨语言兼容性测试...
```

## 测试用例详解

### 1. 服务器连接测试

```typescript
describe('服务器连接测试', () => {
  test('should connect to Python lite server', async () => {
    // 测试基本HTTP连接
  });
  
  test('should verify test user data exists', async () => {
    // 验证测试用户DID和私钥可用
  });
});
```

### 2. 基础API调用测试

```typescript
describe('基础API调用测试', () => {
  test('should call Python server API successfully', async () => {
    // 测试基本的/add API调用
    const result = await agentApiCallPost({
      callerAgent: TEST_CALLER_DID,
      targetAgent: TEST_TARGET_DID,
      apiPath: "/add",
      params: { a: 15, b: 25 }
    });
    expect(result.success).toBe(true);
    expect(result.data.result).toBe(40);
  });
  
  test('should handle multiple test cases', async () => {
    // 测试多种数值组合
  });
});
```

### 3. 认证兼容性测试

```typescript
describe('认证兼容性测试', () => {
  test('should authenticate with Python server using Node.js generated headers', async () => {
    // 验证Node.js生成的认证头被Python服务器接受
  });
  
  test('should handle timestamp format compatibility', async () => {
    // 验证时间戳格式兼容性
    // Node.js: 2025-01-01T00:00:00.000Z
    // Python: 2025-01-01T00:00:00Z
  });
  
  test('should handle DID bidirectional authentication', async () => {
    // 测试DID双向认证的跨语言互操作
  });
});
```

### 4. 数据格式兼容性测试

```typescript
describe('数据格式兼容性测试', () => {
  test('should handle JSON serialization/deserialization compatibility', async () => {
    // 测试复杂数据结构的序列化
  });
  
  test('should handle different data types', async () => {
    // 测试不同数据类型：整数、浮点数、负数、大数
  });
  
  test('should handle special characters and Unicode', async () => {
    // 测试特殊字符和中文字符处理
  });
});
```

### 5. 错误处理测试

```typescript
describe('错误处理测试', () => {
  test('should handle invalid parameters gracefully', async () => {
    // 测试无效参数的处理
  });
  
  test('should handle authentication failures', async () => {
    // 测试认证失败场景
  });
  
  test('should handle non-existent endpoints', async () => {
    // 测试不存在的API端点
  });
  
  test('should handle network timeouts gracefully', async () => {
    // 测试网络超时处理
  });
});
```

### 6. 性能验证测试

```typescript
describe('性能验证测试', () => {
  test('should have reasonable response time', async () => {
    // 验证响应时间在5秒内
  });
  
  test('should handle concurrent requests', async () => {
    // 测试并发请求处理
  });
});
```

## 核心功能

### agentApiCallPost 函数

便捷的API调用函数，模拟Python版本的`agent_api_call_post`：

```typescript
export async function agentApiCallPost(options: {
  callerAgent: string;
  targetAgent: string;
  apiPath: string;
  params: any;
}): Promise<{
  success: boolean;
  data?: any;
  error?: string;
  statusCode?: number;
}>
```

**特性**：
- 自动加载用户私钥
- 处理KeyObject到PEM格式转换
- 使用AuthInitiator进行认证
- 统一的错误处理

### Python服务器连接检查

```typescript
async function checkPythonServer(): Promise<boolean> {
  try {
    const response = await axios.get('http://localhost:9527/health', { 
      timeout: 5000,
      validateStatus: () => true // 接受所有状态码
    });
    return response.status === 200 || response.status === 404;
  } catch (error) {
    return false;
  }
}
```

## 验证点

### ✅ 功能验证
- API调用成功返回结果
- 数学计算结果正确
- 认证流程完整

### ✅ 兼容性验证
- 时间戳格式被Python服务器正确解析
- JSON数据格式兼容
- 认证头格式标准化
- DID双向认证跨语言互操作

### ✅ 性能验证
- 响应时间合理（<5秒）
- 内存使用正常
- 错误处理优雅
- 并发请求支持

## 测试数据

测试使用以下数学运算测试用例：

```typescript
const testCases = [
  { a: 15, b: 25, expected: 40 },
  { a: 0, b: 0, expected: 0 },
  { a: -5, b: 10, expected: 5 },
  { a: 1.5, b: 2.5, expected: 4.0 }
];
```

## 故障排除

### 常见问题

1. **Python服务器未启动**
   - 症状：所有测试被跳过，显示服务器连接失败
   - 解决：按照提示启动Python服务器

2. **用户数据缺失**
   - 症状：`无法加载调用者用户数据`错误
   - 解决：确保`data_user/localhost_9527/anp_users/`目录存在且包含用户数据

3. **私钥加载失败**
   - 症状：`无法获取调用者私钥`错误
   - 解决：检查用户目录中的私钥文件是否存在

4. **认证失败**
   - 症状：API调用返回401/403状态码
   - 解决：检查DID格式和认证配置

### 调试模式

启用详细日志：

```bash
DEBUG=* npm test tests/cross-language/python-server-compatibility.test.ts
```

## 贡献指南

### 添加新测试用例

1. 在相应的`describe`块中添加新的`test`
2. 使用`agentApiCallPost`函数进行API调用
3. 添加适当的断言验证
4. 确保包含服务器状态检查

### 扩展测试覆盖

可以考虑添加以下测试场景：
- 更多API端点测试
- 不同认证模式测试
- 大数据量传输测试
- 长连接测试
- 错误恢复测试

## 相关文档

- [ANP Node.js SDK 文档](../../README.md)
- [Agent API Caller 实现](../../src/runtime/services/agent-api-caller.ts)
- [认证机制文档](../../src/foundation/auth/README.md)
- [用户数据管理](../../src/foundation/user/README.md)

## 许可证

Copyright 2024 ANP Open SDK Authors

Licensed under the Apache License, Version 2.0