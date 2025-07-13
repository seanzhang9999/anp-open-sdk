# URL分析器实现文档

## 概述

URL分析器是ANP Open SDK中的一个核心组件，用于从HTTP请求URL中智能推断目标DID（分布式身份标识符）。这个组件支持多种URL模式，并能够自动识别不同类型的用户和服务。

## 功能特性

### 1. 支持的URL模式

#### WBA用户ID模式
- **模式**: `/wba/user/{user_id}/{file}`
- **示例**: `/wba/user/3ea884878ea5fbb1/did.json`
- **用途**: 通过16位十六进制用户ID访问用户资源

#### WBA编码DID模式
- **模式**: `/wba/user/{encoded_did}/{file}`
- **示例**: `/wba/user/did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1/ad.json`
- **用途**: 通过URL编码的完整DID访问用户资源

#### WBA托管用户模式
- **模式**: `/wba/hostuser/{user_id}/{file}`
- **示例**: `/wba/hostuser/abc123def456789a/did.json`
- **用途**: 访问托管用户资源

#### WBA测试模式
- **模式**: `/wba/test/{test_name}/{file}`
- **示例**: `/wba/test/test_agent_001/ad.json`
- **用途**: 访问测试环境中的代理资源

#### Agent API模式
- **模式**: `/agent/api/{encoded_did}/{endpoint}`
- **示例**: `/agent/api/did%3Awba%3Alocalhost%253A9527%3Awba%3Auser%3A3ea884878ea5fbb1/status`
- **用途**: 通过API访问代理功能

### 2. 核心功能

#### URL模式解析
- 自动识别URL模式类型
- 提取用户信息（用户ID、编码DID、测试名称等）
- 缓存解析结果以提高性能

#### DID推断
- 根据URL模式和请求信息推断目标DID
- 支持多域名环境
- 处理标准端口和非标准端口

#### 验证功能
- 验证用户ID格式（16位十六进制）
- 验证编码DID格式
- 检查URL模式的有效性

## 架构设计

### 类结构

```python
class UrlAnalyzer:
    """URL分析器主类"""
    
    def __init__(self):
        self.domain_manager = get_domain_manager()
        self.did_manager = get_did_format_manager()
        self._pattern_cache = {}
    
    def parse_url_pattern(self, path: str) -> Optional[Dict[str, str]]
    def infer_resp_did_from_url(self, request) -> Optional[str]
    def extract_user_info_from_path(self, path: str) -> Tuple[Optional[str], Optional[str]]
    def _is_user_id(self, text: str) -> bool
    def _is_encoded_did(self, text: str) -> bool
```

### 依赖关系

- **域名管理器**: 处理域名和端口信息
- **DID格式管理器**: 处理DID的创建和解析
- **统一配置系统**: 获取系统配置信息

## 使用方法

### 基本用法

```python
from anp_sdk.did.url_analyzer import get_url_analyzer

# 获取全局分析器实例
analyzer = get_url_analyzer()

# 解析URL模式
pattern_info = analyzer.parse_url_pattern("/wba/user/3ea884878ea5fbb1/did.json")

# 从请求推断DID
target_did = analyzer.infer_resp_did_from_url(request)
```

### 在认证中间件中使用

```python
async def auth_middleware(request: Request, call_next):
    analyzer = get_url_analyzer()
    target_did = analyzer.infer_resp_did_from_url(request)
    
    if target_did:
        # 使用推断的DID进行认证处理
        context.target_did = target_did
    
    return await call_next(request)
```

## 性能优化

### 缓存机制
- URL模式解析结果会被缓存
- 避免重复的正则表达式匹配
- 提高高频访问路径的响应速度

### 单例模式
- 使用全局单例实例
- 减少对象创建开销
- 保持缓存状态

## 测试覆盖

### 单元测试
- URL模式解析测试
- DID推断功能测试
- 验证函数测试
- 边界情况测试

### 集成测试
- 与域名管理器的集成
- 与DID格式管理器的集成
- 真实请求模拟测试

### 性能测试
- 缓存性能验证
- 大量请求处理测试

## 配置选项

URL分析器的行为可以通过统一配置系统进行调整：

```yaml
anp_sdk:
  domain:
    default_domain: "localhost"
    default_port: 9527
  did:
    default_user_type: "user"
```

## 错误处理

### 常见错误情况
1. **无效的URL模式**: 返回None，不抛出异常
2. **无效的用户ID格式**: 验证失败，返回False
3. **缺少请求信息**: 优雅降级，使用默认值

### 日志记录
- 使用标准Python logging模块
- 记录解析失败和异常情况
- 支持调试级别的详细日志

## 扩展性

### 添加新的URL模式
1. 在`URL_PATTERNS`字典中添加新模式
2. 实现对应的解析逻辑
3. 添加相应的测试用例

### 自定义验证规则
- 可以扩展`_is_user_id`和`_is_encoded_did`方法
- 支持自定义验证函数

## 最佳实践

1. **使用全局实例**: 通过`get_url_analyzer()`获取实例
2. **缓存友好**: 相同的URL路径会被缓存
3. **错误处理**: 始终检查返回值是否为None
4. **性能监控**: 监控缓存命中率和解析性能

## 版本历史

- **v1.0.0**: 初始实现，支持基本URL模式解析
- **v1.1.0**: 添加缓存机制和性能优化
- **v1.2.0**: 支持多域名环境和标准端口处理

## 相关文档

- [域名管理器文档](./domain_manager.md)
- [DID格式管理器文档](./did_format_manager.md)
- [统一配置系统文档](./unified_config.md)
