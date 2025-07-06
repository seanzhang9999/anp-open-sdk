# ANP Open SDK 重构执行计划

## 总体原则
1. **小步快跑**: 每个步骤控制在2-4小时内完成
2. **持续可用**: 每步完成后，现有功能仍然正常工作
3. **可验证性**: 每步都有明确的验证方法
4. **可回滚性**: 如果出现问题，可以快速回滚到上一个稳定版本

## Phase 1: 基础准备和抽象层建立 (第1-2周)

### Step 1.1: 创建核心目录结构
**任务**: 建立新的目录结构，不影响现有代码
```
- 创建 anp_open_sdk/core/ 目录
- 创建 anp_open_sdk/core/__init__.py
- 创建基础的 README.md 说明文件
```
**验证**: 运行现有测试，确保没有破坏
**提交信息**: "feat: create core directory structure for refactoring"

### Step 1.2: 创建用户数据抽象基类
**任务**: 创建 `base_user_data.py` 抽象类
```python
# anp_open_sdk/core/base_user_data.py
- 定义 BaseUserData 抽象类
- 定义 BaseUserDataManager 抽象类
- 只包含抽象方法，不包含实现
```
**验证**: 导入测试，确保没有语法错误
**提交信息**: "feat: add BaseUserData abstract classes"

### Step 1.3: 创建存储抽象基类
**任务**: 创建 `base_storage.py` 抽象类
```python
# anp_open_sdk/core/base_storage.py
- 定义 BaseStorageProvider 抽象类
- 定义 BaseConfigProvider 抽象类
```
**验证**: 导入测试
**提交信息**: "feat: add storage abstraction layer"

### Step 1.4: 创建传输抽象基类
**任务**: 创建 `base_transport.py` 抽象类
```python
# anp_open_sdk/core/base_transport.py
- 定义 RequestContext 数据类
- 定义 ResponseContext 数据类
- 定义 BaseTransport 抽象类
```
**验证**: 导入测试
**提交信息**: "feat: add transport abstraction layer"

### Step 1.5: 创建智能体抽象基类
**任务**: 创建 `base_agent.py` 抽象类
```python
# anp_open_sdk/core/base_agent.py
- 定义 BaseAgent 抽象类
- 定义 BaseAgentManager 抽象类
```
**验证**: 导入测试
**提交信息**: "feat: add agent abstraction layer"

### Step 1.6: 创建网络管理抽象基类
**任务**: 创建 `base_network.py` 抽象类
```python
# anp_open_sdk/core/base_network.py
- 定义 BaseNetworkManager 抽象类
- 定义 BaseServerManager 抽象类
```
**验证**: 导入测试
**提交信息**: "feat: add network management abstraction"

## Phase 2: 现有代码适配抽象层 (第2-3周)

### Step 2.1: 重构 BaseUserData 继承
**任务**: 修改现有的 `base_user_data.py`
```python
# 让现有的 BaseUserData 继承自 core.BaseUserData
# 保持现有功能不变
```
**验证**: 运行 test_anpsdk_all.py
**提交信息**: "refactor: adapt existing BaseUserData to inherit from core"

### Step 2.2: 创建内存化的用户数据实现
**任务**: 创建新的内存化实现
```python
# anp_open_sdk/core/memory_user_data.py
- 实现纯内存的 MemoryUserData 类
- 实现纯内存的 MemoryUserDataManager 类
```
**验证**: 单元测试新类
**提交信息**: "feat: add memory-based user data implementation"

### Step 2.3: 重构 LocalUserData - 分离文件操作
**任务**: 开始分离文件操作逻辑
```python
# 在 LocalUserData 中标记所有文件操作方法
# 添加 TODO 注释，准备后续迁移
```
**验证**: 运行现有测试
**提交信息**: "refactor: mark file operations in LocalUserData for migration"

### Step 2.4: 创建认证管理器核心类
**任务**: 创建协议无关的认证管理器
```python
# anp_open_sdk/core/auth_manager.py
- 创建 AuthManager 类（不依赖 HTTP）
- 创建 AuthValidator 类
```
**验证**: 单元测试
**提交信息**: "feat: add protocol-agnostic auth manager"

## Phase 3: Framework 层建立 (第3-4周)

### Step 3.1: 创建 Framework 目录结构
**任务**: 建立 framework 的目录结构
```
- 创建 anp_open_sdk_framework/storage/
- 创建 anp_open_sdk_framework/transport/
- 创建 anp_open_sdk_framework/server/
- 创建 anp_open_sdk_framework/user_data/
```
**验证**: 确保不影响现有导入
**提交信息**: "feat: create framework directory structure"

### Step 3.2: 实现文件系统存储提供者
**任务**: 创建具体的存储实现
```python
# anp_open_sdk_framework/storage/file_system_provider.py
- 实现 FileSystemStorageProvider
- 实现异步文件操作
```
**验证**: 单元测试文件操作
**提交信息**: "feat: implement file system storage provider"

### Step 3.3: 实现 HTTP 传输层
**任务**: 创建 HTTP 传输实现
```python
# anp_open_sdk_framework/transport/http_transport.py
- 实现 HttpTransport 类
- 从 auth_client.py 迁移 HTTP 逻辑
```
**验证**: 测试 HTTP 请求功能
**提交信息**: "feat: implement HTTP transport layer"

### Step 3.4: 迁移 LocalUserData 到 Framework
**任务**: 复制并重构 LocalUserData
```python
# anp_open_sdk_framework/adapter_user_data/local_user_data.py
- 复制 LocalUserData 类
- 使用 StorageProvider 替换直接文件操作
```
**验证**: 对比测试新旧实现
**提交信息**: "feat: migrate LocalUserData to framework with storage abstraction"

## Phase 4: 路由和服务迁移 (第4-5周)

### Step 4.1: 迁移路由文件
**任务**: 逐个迁移路由文件
```
- 复制 router_agent.py → framework/http_routes/agent_routes.py
- 复制 router_auth.py → framework/http_routes/auth_routes.py
- 复制 router_did.py → framework/http_routes/did_routes.py
```
**验证**: 确保导入路径正确
**提交信息**: "feat: migrate router files to framework"

### Step 4.2: 分离 ANPSDK 类
**任务**: 拆分 ANPSDK 的职责
```python
# 创建 anp_open_sdk/core/network_manager.py
- 提取网络管理逻辑
# 创建 anp_open_sdk_framework/server/fastapi_server.py
- 提取 FastAPI 相关代码
```
**验证**: 运行 demo 确保功能正常
**提交信息**: "refactor: split ANPSDK into core and framework components"

### Step 4.3: 创建兼容层
**任务**: 保持向后兼容
```python
# 在原 anp_sdk.py 中创建兼容包装
- 使用新的分离组件
- 保持原有 API 不变
```
**验证**: 运行所有现有 demo
**提交信息**: "feat: add compatibility layer for ANPSDK"

## Phase 5: 认证系统解耦 (第5-6周)

### Step 5.1: 重构 auth_client
**任务**: 分离认证逻辑和传输逻辑
```python
# 修改 auth_client.py
- 使用 AuthManager 和 Transport 抽象
- 保持原有函数签名
```
**验证**: 运行认证相关测试
**提交信息**: "refactor: decouple auth_client from HTTP transport"

### Step 5.2: 重构 auth_server
**任务**: 使认证验证协议无关
```python
# 修改 auth_server.py
- 使用 RequestContext 替代 FastAPI Request
- 创建适配器函数
```
**验证**: 测试认证中间件
**提交信息**: "refactor: make auth_server protocol-agnostic"

## Phase 6: 清理和优化 (第6-7周)

### Step 6.1: 删除冗余代码
**任务**: 清理已迁移的代码
```
- 标记废弃的方法
- 添加迁移提示
```
**验证**: 确保没有破坏现有功能
**提交信息**: "chore: mark deprecated code for removal"

### Step 6.2: 更新导入路径
**任务**: 逐步更新导入
```
- 更新 demo 中的导入
- 更新测试中的导入
```
**验证**: 运行所有测试和 demo
**提交信息**: "refactor: update import paths to use new structure"

### Step 6.3: 创建 PyPI 包配置
**任务**: 配置 pyproject.toml
```
- 配置 anp_open_sdk 的依赖
- 设置包元数据
- 创建发布脚本
```
**验证**: 本地安装测试
**提交信息**: "feat: add PyPI package configuration"

## Phase 7: 文档和测试 (第7-8周)

### Step 7.1: 更新文档
**任务**: 创建新的文档
```
- 创建迁移指南
- 更新 README
- 添加架构图
```
**验证**: 文档审查
**提交信息**: "docs: update documentation for new architecture"

### Step 7.2: 添加集成测试
**任务**: 创建新的测试套件
```
- 测试 core 和 framework 集成
- 测试向后兼容性
```
**验证**: 测试覆盖率报告
**提交信息**: "test: add integration tests for refactored architecture"

## 执行建议

1. **每日计划**: 每天完成 2-3 个步骤
2. **测试优先**: 每个步骤都要运行相关测试
3. **及时沟通**: 遇到问题及时讨论
4. **灵活调整**: 根据实际情况调整步骤

## 如何使用AI来执行

对于每个步骤，你可以：
1. 告诉AI当前要执行的步骤编号
2. AI会为你创建/修改相应的文件
3. 你运行测试验证
4. 确认无误后提交
5. 继续下一个步骤
