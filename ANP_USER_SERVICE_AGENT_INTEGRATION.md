# ANP User Service 智能体集成使用说明

## 概述

已成功将 `anp_open_sdk_framework_demo/framework_demo.py` 的智能体服务能力集成到 `anp_user_service` 中，让 Chrome 插件用户登录后可以直接调用 orchestrator_agent 的各种方法。

## 架构变更

### 1. 新增文件
- **`anp_user_service/app/services/agent_service.py`** - 智能体服务管理器
- **`anp_user_service/app/routers/agents.py`** - 智能体API路由处理器

### 2. 修改文件
- **`anp_user_service/main.py`** - 集成智能体服务启动和关闭
- **`anp_user_extension/src/popup.html`** - 添加智能体演示面板
- **`anp_user_extension/src/popup.js`** - 添加智能体调用功能
- **`anp_user_extension/src/style.css`** - 添加智能体演示样式

## 功能特性

### 智能体管理服务 (AgentServiceManager)
- 自动加载和初始化智能体配置
- 管理智能体生命周期
- 提供统一的方法调用接口
- 支持异步清理和资源管理

### API 端点
- `GET /agents/status` - 获取智能体服务状态
- `GET /agents/methods` - 获取可用方法列表
- `POST /agents/call` - 通用智能体方法调用
- `POST /agents/discover` - 发现智能体
- `POST /agents/demo/*` - 各种演示功能

### Chrome 插件增强
- 新增"Agent Demos"模式
- 一键式智能体功能演示
- 实时显示智能体服务状态
- 可视化演示结果展示

## 使用方法

### 1. 启动服务
```bash
# 启动用户服务（会自动初始化智能体服务）
cd anp_user_service
python main.py
```

### 2. 使用Chrome插件
1. 打开Chrome插件
2. 使用现有账户登录（如：anp_user/anp_666）
3. 切换到"Agent Demos"标签
4. 点击任意演示按钮体验功能

### 3. 可用的演示功能
- **发现智能体** - 扫描网络中的智能体
- **计算器演示** - 调用计算器智能体
- **Hello演示** - 简单的问候功能
- **AI爬虫演示** - 智能爬虫功能
- **AI根爬虫演示** - 从根URL开始的智能爬虫
- **Agent 002演示** - 直接调用其他智能体
- **Agent 002新演示** - 通过搜索调用智能体

## 技术细节

### 配置文件
智能体服务使用 `anp_open_sdk_framework_demo_agent_9528_unified_config.yaml` 配置文件，指向 `data_user/localhost_9528/agents_config/` 目录下的智能体配置。

### 认证机制
Chrome插件通过用户名/密码认证访问智能体服务，确保只有登录用户可以调用智能体功能。

### 错误处理
- 智能体服务初始化失败时会显示错误状态
- API调用失败时会在插件中显示具体错误信息
- 网络连接问题会被捕获并友好提示

## 部署注意事项

1. **端口配置**：确保 anp_user_service 运行在 8000 端口
2. **配置文件**：确认智能体配置文件路径正确
3. **依赖检查**：确保所有必要的 Python 包已安装
4. **权限配置**：确保服务有读取配置文件和智能体目录的权限

## 故障排除

### 智能体服务无法启动
- 检查配置文件是否存在
- 验证智能体配置目录路径
- 查看服务日志获取详细错误信息

### Chrome插件连接失败
- 确认 anp_user_service 正在运行
- 检查 CORS 设置是否正确
- 验证插件扩展ID是否在允许列表中

### 演示功能执行失败
- 检查目标智能体是否正在运行
- 验证网络连接和DID认证
- 查看服务端日志获取详细错误信息

## 扩展开发

要添加新的智能体演示功能：

1. 在 `anp_user_service/app/routers/agents.py` 中添加新的路由
2. 在 `anp_user_extension/src/popup.html` 中添加新按钮
3. 在 `anp_user_extension/src/popup.js` 中添加按钮监听器
4. 重新构建Chrome插件

这样就完成了智能体服务在用户服务中的集成，为用户提供了便捷的智能体交互体验。