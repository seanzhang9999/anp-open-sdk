# ANP SDK 统一配置系统使用教程

## 概述

ANP SDK 提供了一个强大的统一配置系统，支持 YAML 配置文件、环境变量映射、路径占位符解析和完整的 IDE 代码提示功能。

## 1. 基础使用

### 1.1 初始化配置

```python
from anp_sdk.config import UnifiedConfig, set_global_config, get_global_config

# 方式1：使用默认配置文件名和路径
app_config = UnifiedConfig()  # 默认使用 {APP_ROOT}/unified_config.yaml

# 方式2：指定配置文件名（相对于当前工作目录）
app_config = UnifiedConfig(config_file='my_config.yaml')

# 方式3：指定完整配置文件路径
app_config = UnifiedConfig(config_file='/path/to/config.yaml')

# 方式4：同时指定 app_root 和配置文件
app_config = UnifiedConfig(
    config_file='config/app_config.yaml',
    app_root='/custom/app/root'
)

# 设置为全局配置（重要：必须在应用入口处调用）
set_global_config(app_config)
```

### 1.2 在其他模块中使用配置

```python
from anp_sdk.config import get_global_config


def some_function():
    config = get_global_config()

    # 访问配置项（享受完整的 IDE 代码提示）
    host = config.anp_sdk.host
    port = config.anp_sdk.port
    debug_mode = config.anp_sdk.debug_mode

    # 访问 LLM 配置
    api_url = config.llm.api_url
    model = config.llm.default_model

    # 访问环境变量
    openai_key = config.env.openai_api_key

    # 访问敏感信息
    db_url = config.secrets.database_url
```

## 2. APP_ROOT 详解

### 2.1 APP_ROOT 的定义

`APP_ROOT` 是应用程序的根目录，用作所有相对路径的基准点。

```python
# APP_ROOT 的确定优先级：
# 1. 构造函数中明确指定的 app_root 参数
app_config = UnifiedConfig(app_root='/custom/root')

# 2. 如果未指定，则使用当前工作目录
app_config = UnifiedConfig()  # APP_ROOT = os.getcwd()
```

### 2.2 APP_ROOT 在配置文件中的使用

```yaml
anp_sdk:
  # {APP_ROOT} 占位符会自动替换为实际的应用根目录
  user_did_path: "{APP_ROOT}/data_user/{host}_{port}/anp_users"
  user_hosted_path: "{APP_ROOT}/data_user/{host}_{port}/anp_users_hosted"

mail:
  local_backend_path: "{APP_ROOT}/anp_sdk/testuse/mail_local_backend"
```

### 2.3 路径解析方法

```python
from anp_sdk.config import UnifiedConfig

# 类方法：解析包含 {APP_ROOT} 的路径
resolved_path = UnifiedConfig.resolve_path("{APP_ROOT}/data/config.json")

# 获取应用根目录
app_root = UnifiedConfig.get_app_root()

# 实例方法：获取路径信息
config = get_global_config()
path_info = config.get_path_info()
print(path_info)
```

## 3. 配置文件管理

### 3.1 配置文件的查找规则

```python
# 配置文件路径解析规则：
# 1. 如果 config_file 是绝对路径，直接使用
UnifiedConfig(config_file='/absolute/path/to/config.yaml')

# 2. 如果是相对路径，相对于当前工作目录解析
UnifiedConfig(config_file='config/app.yaml')

# 3. 如果未指定，使用默认路径
UnifiedConfig()  # 使用 {APP_ROOT}/unified_config.yaml
```

### 3.2 配置文件的创建和管理

```python
config = UnifiedConfig()

# 重新加载配置
config.reload()

# 保存配置
config.save()

# 获取配置字典
config_dict = config.to_dict()
```

### 3.3 默认配置文件

如果指定的配置文件不存在，系统会：
1. 查找 `{APP_ROOT}/unified_config.default.yaml`
2. 如果存在，复制为新的配置文件
3. 如果不存在，创建空配置文件

## 4. 添加新的配置项和代码提示

### 4.1 在配置文件中添加新配置

```yaml
# 添加新的配置节点
my_service:
  enabled: true
  timeout: 30
  endpoints:
    - "https://api1.example.com"
    - "https://api2.example.com"
  settings:
    max_retries: 3
    batch_size: 100
```

### 4.2 在类型定义中添加协议

```python
# anp_sdk/config/config_types.py
from typing import Protocol, List

# 1. 定义子配置协议
class MyServiceSettingsConfig(Protocol):
    """我的服务设置配置协议"""
    max_retries: int
    batch_size: int

class MyServiceConfig(Protocol):
    """我的服务配置协议"""
    enabled: bool
    timeout: int
    endpoints: List[str]
    settings: MyServiceSettingsConfig

# 2. 在主配置协议中添加新节点
class BaseUnifiedConfigProtocol(Protocol):
    """统一配置协议"""
    # 现有配置...
    anp_sdk: AnpSdkConfig
    llm: LlmConfig
    mail: MailConfig
    
    # 新增配置
    my_service: MyServiceConfig  # 添加这一行
    
    # 方法定义...
    def resolve_path(self, path: str) -> Path: ...
```

### 4.3 使用新配置（享受完整代码提示）

```python
from anp_sdk.config import get_global_config


def use_my_service():
    config = get_global_config()

    # IDE 会提供完整的代码提示
    if config.my_service.enabled:
        timeout = config.my_service.timeout
        endpoints = config.my_service.endpoints
        max_retries = config.my_service.settings.max_retries

        print(f"Service timeout: {timeout}")
        print(f"Max retries: {max_retries}")
        for endpoint in endpoints:
            print(f"Endpoint: {endpoint}")
```

## 5. 环境变量和敏感信息管理

### 5.1 环境变量映射

```yaml
# 环境变量映射
env_mapping:
  # 应用配置
  debug_mode: ANP_DEBUG
  host: ANP_HOST
  port: ANP_PORT
  
  # 新增环境变量映射
  my_service_timeout: MY_SERVICE_TIMEOUT
  my_service_api_key: MY_SERVICE_API_KEY

# 类型转换
env_types:
  debug_mode: boolean
  port: integer
  my_service_timeout: integer  # 新增类型转换
```

### 5.2 敏感信息配置

```yaml
# 敏感信息列表
secrets:
  - openai_api_key
  - mail_password
  - database_url
  - my_service_api_key  # 新增敏感信息
```

### 5.3 在代码中使用环境变量和敏感信息

```python
config = get_global_config()

# 访问环境变量
debug_mode = config.env.debug_mode
host = config.env.host
my_timeout = config.env.my_service_timeout

# 访问敏感信息（每次从环境变量读取）
api_key = config.secrets.my_service_api_key
db_url = config.secrets.database_url
```

## 6. 高级功能

### 6.1 路径管理

```python
config = get_global_config()

# 添加路径到 PATH 环境变量
config.add_to_path("/new/path/to/add")

# 在 PATH 中查找文件
matches = config.find_in_path("python")
for match in matches:
    print(f"Found: {match}")

# 获取路径信息
path_info = config.get_path_info()
print(f"App root: {path_info['app_root']}")
print(f"Config file: {path_info['config_file']}")
```

### 6.2 配置重载

```python
config = get_global_config()

# 重新加载配置文件
config.reload()

# 重新加载环境变量
config.env.reload()
```

## 7. 完整示例

### 7.1 应用入口文件

```python
# main.py
from anp_sdk.config import UnifiedConfig, set_global_config, get_global_config
from anp_sdk.utils.log_base import setup_logging
import logging

# 1. 初始化配置
app_config = UnifiedConfig(config_file='my_app_config.yaml')
set_global_config(app_config)

# 2. 设置日志
setup_logging()
logger = logging.getLogger(__name__)


# 3. 使用配置
async def main():
    config = get_global_config()

    logger.info(f"Starting anp_server on {config.anp_sdk.host}:{config.anp_sdk.port}")

    if config.my_service.enabled:
        logger.info("My service is enabled")
        # 使用服务配置...


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
```

### 7.2 其他模块中使用

```python
# service_module.py
from anp_sdk.config import get_global_config
import logging

logger = logging.getLogger(__name__)


class MyService:
    def __init__(self):
        self.config = get_global_config()

    async def start(self):
        if not self.config.my_service.enabled:
            logger.info("Service is disabled")
            return

        timeout = self.config.my_service.timeout
        endpoints = self.config.my_service.endpoints
        api_key = self.config.secrets.my_service_api_key

        logger.info(f"Starting service with timeout: {timeout}")
        # 服务启动逻辑...
```

## 8. 最佳实践

### 8.1 配置文件组织

```yaml
# 推荐的配置文件结构
# 1. 核心应用配置
anp_sdk:
  # ...

# 2. 外部服务配置
llm:
  # ...

mail:
  # ...

# 3. 自定义服务配置
my_service:
  # ...

# 4. 环境变量映射
env_mapping:
  # ...

# 5. 敏感信息列表
secrets:
  # ...
```

### 8.2 代码组织

```python
# 1. 在应用入口处初始化配置
# main.py 或 app.py
from anp_sdk.config import UnifiedConfig, set_global_config

app_config = UnifiedConfig()
set_global_config(app_config)

# 2. 在其他模块中使用配置
# service.py
from anp_sdk.config import get_global_config


def my_function():
    config = get_global_config()
    # 使用配置...
```

### 8.3 类型安全

```python
# 利用类型提示获得更好的 IDE 支持
from anp_sdk.config import get_global_config
from anp_sdk.config.config_types import BaseUnifiedConfigProtocol


def process_config(config: BaseUnifiedConfigProtocol):
    # IDE 会提供完整的代码提示
    host = config.anp_sdk.host
    port = config.anp_sdk.port
    # ...


# 使用
config = get_global_config()
process_config(config)
```

## 9. 配置系统特性总结

通过这个配置系统，您可以享受到：

- 🎯 **完整的 IDE 代码提示和类型检查** - 基于 Protocol 的类型系统
- 🔧 **灵活的配置文件管理** - 支持多种配置文件路径指定方式
- 🛡️ **安全的敏感信息处理** - 敏感信息从环境变量实时读取
- 📁 **智能的路径解析** - {APP_ROOT} 占位符自动替换
- 🔄 **动态的配置重载** - 运行时重新加载配置
- 🌍 **环境变量集成** - 无缝的环境变量映射和类型转换

## 10. 常见问题

### Q: 如何在不同环境中使用不同的配置文件？

```python
import os

# 根据环境变量选择配置文件
env = os.getenv('APP_ENV', 'development')
config_file = f'config/{env}.yaml'

app_config = UnifiedConfig(config_file=config_file)
set_global_config(app_config)
```

### Q: 如何验证配置项是否存在？

```python
config = get_global_config()

# 使用 hasattr 检查配置项是否存在
if hasattr(config, 'my_service') and hasattr(config.my_service, 'enabled'):
    enabled = config.my_service.enabled
else:
    enabled = False
```

### Q: 如何在配置文件中使用环境变量？

```yaml
# 在配置文件中直接使用环境变量（通过 env_mapping）
my_service:
  api_key: "${MY_SERVICE_API_KEY}"  # 这需要在 env_mapping 中定义

# 或者通过 secrets 配置
secrets:
  - my_service_api_key

env_mapping:
  my_service_api_key: MY_SERVICE_API_KEY
```

然后在代码中：

```python
config = get_global_config()
api_key = config.secrets.my_service_api_key  # 从环境变量读取
```