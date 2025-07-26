# ANP Node.js SDK 测试指南

## 🚀 快速开始

### 基本测试命令

```bash
# 运行所有测试（使用改进的报告格式）
npm test

# 运行详细测试（显示每个测试的详细信息）
npm run test:verbose

# 只运行失败的测试
npm run test:failed

# 运行跨语言兼容性测试
npm run test:cross-lang

# 运行基础功能测试
npm run test:foundation

# 简洁模式（只显示统计信息）
npm run test:summary
```

### 针对特定测试的命令

```bash
# 运行特定测试文件
npm test tests/foundation/local-user-data.test.ts

# 运行包含特定模式的测试
npm test -- --testNamePattern="should create user"

# 运行特定测试套件
npm test -- --testPathPattern="python-server-compatibility"

# 监视模式（文件变化时自动重新运行）
npm run test:watch
```

## 📊 改进的测试报告

### 新的报告格式特性

1. **清晰的统计信息**
   - 总测试数、通过数、失败数
   - 成功率百分比
   - 执行时间统计

2. **按测试套件分组**
   - 每个测试文件的通过/失败状态
   - 失败测试的具体名称和错误信息

3. **详细的错误信息**
   - 清理后的错误消息
   - 文件位置和行号
   - 具体的失败原因

4. **性能统计**
   - 总执行时间
   - 慢速测试识别（>1秒）
   - 性能建议

5. **智能建议**
   - 基于测试结果的修复建议
   - 调试命令提示

### 示例输出

```
═══════════════════════════════════════════════════════════════════════════════
🧪 ANP Node.js SDK 测试结果详细报告
═══════════════════════════════════════════════════════════════════════════════

📊 测试统计:
   • 总测试数: 239
   • 通过: 205 ✅
   • 失败: 34 ❌
   • 成功率: 85.8%

📋 测试套件详情:

✅ local-user-data.test (15/15)
❌ python-server-compatibility.test (12/16)
   失败的测试:
   ❌ should handle authentication failures
      💥 Expected: false, Received: true

🔍 失败测试详细信息:
────────────────────────────────────────────────────────────────

❌ 认证兼容性测试 > should handle authentication failures
   文件: ./tests/cross-language/python-server-compatibility.test.ts
   错误 1:
   Expected: false
   Received: true
   
   at Object.<anonymous> (tests/cross-language/python-server-compatibility.test.ts:475:32)

⚡ 性能统计:
   • 总执行时间: 8.97秒
   • 慢速测试 (>1秒):
     - should handle concurrent requests: 2340ms

🎯 测试总结:
   ⚠️  发现 34 个失败测试，需要修复。
   💡 建议:
      1. 检查上述失败测试的错误信息
      2. 确认测试环境和依赖是否正确
      3. 运行单个测试进行调试: npm test -- --testNamePattern="测试名称"
```

## 🔧 调试失败的测试

### 步骤1: 识别失败的测试
运行 `npm run test:verbose` 查看详细的失败信息。

### 步骤2: 运行单个测试
```bash
# 运行特定的失败测试
npm test -- --testNamePattern="should handle authentication failures"

# 或运行整个测试文件
npm test tests/cross-language/python-server-compatibility.test.ts
```

### 步骤3: 启用调试模式
```bash
# 启用详细日志
DEBUG=* npm test -- --testNamePattern="测试名称"

# 或使用Node.js调试器
node --inspect-brk node_modules/.bin/jest --runInBand --testNamePattern="测试名称"
```

## 📈 测试最佳实践

### 1. 运行测试前的检查清单
- [ ] 确保Python服务器运行（跨语言测试需要）
- [ ] 检查测试数据是否存在
- [ ] 确认环境变量配置正确

### 2. 解读测试结果
- ✅ **绿色通过**: 功能正常工作
- ❌ **红色失败**: 需要修复的问题
- ⏭️ **跳过测试**: 通常因为依赖条件不满足

### 3. 常见失败原因
1. **Python服务器未运行**: 跨语言测试会失败
2. **用户数据缺失**: 检查 `data_user/` 目录
3. **网络问题**: 检查localhost连接
4. **环境配置**: 确认Node.js版本和依赖

## 🎯 特定测试场景

### 跨语言兼容性测试
```bash
# 1. 启动Python服务器
PYTHONPATH=$PYTHONPATH:/path/to/anp-open-sdk-python python examples/flow_anp_agent/flow_anp_agent.py

# 2. 运行跨语言测试
npm run test:cross-lang
```

### 基础功能测试
```bash
# 运行基础功能测试（不需要Python服务器）
npm run test:foundation
```

### 持续集成测试
```bash
# CI环境中的测试命令
npm run test:summary
```

## 🔍 故障排除

### 常见问题和解决方案

1. **所有测试都被跳过**
   - 检查Python服务器是否运行
   - 确认端口9527是否可用

2. **认证相关测试失败**
   - 检查用户DID数据是否存在
   - 确认私钥文件是否正确

3. **性能测试超时**
   - 检查网络连接
   - 考虑增加测试超时时间

4. **报告器错误**
   - 确认 `tests/custom-reporter.js` 文件存在
   - 检查Jest配置是否正确

## 📚 相关文档

- [Jest官方文档](https://jestjs.io/docs/getting-started)
- [跨语言兼容性测试详情](./cross-language/README.md)
- [ANP Node.js SDK文档](../README.md)

## 🤝 贡献指南

如果您发现测试问题或想要改进测试报告，请：

1. 创建Issue描述问题
2. 提交Pull Request with改进
3. 确保新测试遵循现有模式
4. 更新相关文档

---

**提示**: 使用 `npm run test:verbose` 获得最详细的测试信息，这是调试问题的最佳起点。