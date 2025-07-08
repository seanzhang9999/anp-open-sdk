# Agent Connect 迭代接口需求和规范

## 概述

基于 Protocol Wrapper 集中控制架构的测试验证结果，本文档为 agent_connect 库的未来迭代提供明确的接口需求、行为规范和设计指导。

## 核心设计原则

### 1. 纯净性原则
- **纯算法逻辑**: 加密、签名、验证等核心算法应该是纯函数，无副作用
- **网络隔离**: 网络操作应该与算法逻辑完全分离
- **文件系统隔离**: 文件访问应该通过注入的接口进行，而非直接操作

### 2. 可控性原则
- **依赖注入**: 所有外部依赖（网络、文件、随机数）都应该可以注入
- **状态可观测**: 提供清晰的状态查询接口
- **错误可控**: 标准化的错误处理和报告机制

## 接口需求规范

### 1. 加密操作接口 (Pure Crypto Interface)

#### 1.1 验证方法创建
```python
def create_verification_method(verification_method: Dict[str, Any]) -> VerificationMethodInterface:
    """
    创建验证方法对象
    
    要求:
    - 纯函数，无副作用
    - 支持多种验证方法类型
    - 输入验证和错误处理
    - 可预测的行为
    
    参数:
    - verification_method: DID 验证方法字典
    
    返回:
    - VerificationMethodInterface: 统一的验证方法接口
    
    支持的类型:
    - EcdsaSecp256k1VerificationKey2019
    - Ed25519VerificationKey2020
    - JsonWebKey2020
    """
```

#### 1.2 曲线映射配置
```python
def get_curve_mapping() -> Dict[str, str]:
    """
    获取支持的椭圆曲线映射
    
    要求:
    - 静态配置，运行时不变
    - 标准化的曲线名称
    - 完整的类型支持
    
    返回:
    - Dict: 验证方法类型到曲线名称的映射
    """
```

#### 1.3 签名操作
```python
def sign_data(data: bytes, private_key: bytes, algorithm: str) -> bytes:
    """
    对数据进行数字签名
    
    要求:
    - 确定性输出（相同输入总是产生相同输出）
    - 支持多种签名算法
    - 标准化的签名格式
    - 明确的错误处理
    """

def verify_signature(data: bytes, signature: bytes, public_key: bytes, algorithm: str) -> bool:
    """
    验证数字签名
    
    要求:
    - 严格的验证逻辑
    - 防止时间攻击
    - 标准化的公钥格式支持
    - 清晰的布尔返回值
    """
```

### 2. 网络操作接口 (Network Interface)

#### 2.1 DID 文档解析
```python
async def resolve_did_document(did: str, resolver_config: ResolverConfig = None) -> Optional[Dict[str, Any]]:
    """
    异步解析 DID 文档
    
    要求:
    - 完全的网络隔离（可配置端点）
    - 超时控制
    - 重试机制
    - 缓存策略（可选）
    - 详细的错误信息
    
    参数:
    - did: 要解析的 DID
    - resolver_config: 可选的解析器配置
    
    返回:
    - Optional[Dict]: DID 文档或 None
    """
```

#### 2.2 网络配置接口
```python
@dataclass
class ResolverConfig:
    """DID 解析器配置"""
    timeout: float = 10.0
    max_retries: int = 3
    cache_ttl: Optional[int] = 300
    custom_endpoints: Dict[str, str] = field(default_factory=dict)
    verify_ssl: bool = True
```

### 3. 状态监控接口 (Status Interface)

#### 3.1 健康检查
```python
def get_health_status() -> HealthStatus:
    """
    获取库的健康状态
    
    要求:
    - 快速响应（<100ms）
    - 详细的组件状态
    - 版本信息
    - 依赖状态
    """

@dataclass
class HealthStatus:
    """健康状态数据结构"""
    overall_status: str  # "healthy" | "degraded" | "unhealthy"
    crypto_available: bool
    network_available: bool
    version: str
    components: Dict[str, ComponentStatus]
    timestamp: datetime
```

#### 3.2 错误报告
```python
class AgentConnectException(Exception):
    """标准化的异常基类"""
    def __init__(self, message: str, error_code: str, details: Dict[str, Any] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()

class CryptoException(AgentConnectException):
    """加密操作相关异常"""
    pass

class NetworkException(AgentConnectException):
    """网络操作相关异常"""
    pass
```

## 迭代优先级建议

### 高优先级 (P0)
1. **纯化加密操作**: 移除所有网络和文件依赖
2. **标准化接口**: 实现统一的验证方法接口
3. **错误处理**: 实现标准化的异常体系

### 中优先级 (P1)
1. **网络操作分离**: 将 DID 解析独立为异步接口
2. **配置系统**: 实现可注入的配置系统
3. **状态监控**: 添加健康检查和状态报告

### 低优先级 (P2)
1. **性能优化**: 实现缓存和批处理
2. **扩展性**: 支持更多验证方法类型
3. **监控集成**: 支持 metrics 和 tracing

## 测试要求

### 1. 单元测试覆盖率
- 加密操作: 100% 覆盖率
- 网络操作: 95% 覆盖率（模拟网络）
- 错误处理: 100% 覆盖率

### 2. 集成测试
- Protocol Wrapper 兼容性测试
- 现有 ANP SDK 集成测试
- 性能基准测试

### 3. 安全测试
- 加密算法正确性验证
- 时间攻击防护测试
- 输入验证测试

## 向后兼容性

### 1. 迁移策略
- 保持现有公共 API 3 个版本
- 提供明确的迁移指南
- 自动化迁移工具

### 2. 弃用时间表
- v1.0: 引入新接口，标记旧接口为 deprecated
- v1.1: 发出弃用警告
- v2.0: 移除旧接口

## 实现建议

### 1. 模块结构
```
agent_connect/
├── crypto/           # 纯加密操作
│   ├── signing.py
│   ├── verification.py
│   └── curves.py
├── network/          # 网络操作
│   ├── resolver.py
│   └── transport.py
├── config/           # 配置管理
│   └── settings.py
├── monitoring/       # 状态监控
│   └── health.py
└── exceptions.py     # 异常定义
```

### 2. 依赖管理
- 最小化外部依赖
- 明确的可选依赖标记
- 依赖版本锁定策略

### 3. 文档要求
- API 文档完整覆盖
- 迁移指南详细说明
- 最佳实践示例

## 验收标准

✅ **Protocol Wrapper 测试全部通过**  
✅ **现有 ANP SDK 功能保持不变**  
✅ **性能基准达到或超过当前版本**  
✅ **安全测试全部通过**  
✅ **文档覆盖率 100%**  

通过以上接口需求和规范，agent_connect 的迭代将能够：
1. 提供更清晰、更可控的 API
2. 更好地支持测试和模拟
3. 为 ANP Open SDK 的持续发展提供稳定基础
4. 遵循现代软件工程最佳实践