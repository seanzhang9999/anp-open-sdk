# ANP Open SDK 重构设计方案

## 核心思想

本次重构的核心是将**"做什么 (What)"与"怎么做 (How)"**彻底分离，实现以下目标：

1. **anp_open_sdk (Core SDK)**: 定义"做什么"。提供抽象基类和接口，只处理内存中的数据和逻辑，不关心数据从哪里来（文件、数据库等）
2. **anp_open_sdk_framework (Framework)**: 定义"怎么做"。继承Core SDK的基类，并提供具体的实现，负责从文件系统加载配置、运行服务器等与环境相关的任务
3. **PyPI 包化**: 使 anp_open_sdk 成为一个纯净的、可独立安装的 PyPI 包

## 1. 文件迁移：哪些文件应移至 anp_open_sdk_framework

### 1.1 高优先级迁移文件

#### A. 用户数据管理相关
```
anp_open_sdk/anp_sdk_user_data.py → anp_open_sdk_framework/user_data/local_user_data.py
```
**原因**: 包含大量文件操作逻辑（`os.listdir`, `os.path.join`, `yaml.safe_load`, `json.load`），以及创建用户目录和密钥文件的功能

#### B. 服务器运行相关
```
anp_open_sdk/anp_sdk.py → 拆分重构
- FastAPI相关代码 → anp_open_sdk_framework/server/fastapi_server.py
- 路由注册逻辑 → anp_open_sdk_framework/server/route_manager.py
- 核心网络管理 → anp_open_sdk/core/network_manager.py (重构后)
```

#### C. HTTP路由相关
```
anp_open_sdk/service/router/ → anp_open_sdk_framework/http_routes/
├── router_agent.py → agent_routes.py
├── router_auth.py → auth_routes.py
├── router_did.py → did_routes.py
└── router_publisher.py → publisher_routes.py
```

#### D. 发布者服务相关
```
anp_open_sdk/service/publisher/ → anp_open_sdk_framework/publisher/
├── anp_sdk_publisher.py → did_publisher.py
├── anp_sdk_publisher_mail_backend.py → mail_backend.py
└── anp_sdk_publisher_mail_mgr.py → mail_manager.py
```

#### E. 交互服务相关
```
anp_open_sdk/service/interaction/ → anp_open_sdk_framework/interaction/
├── agent_api_call.py → api_caller.py
├── agent_message_p2p.py → p2p_messenger.py
├── anp_sdk_group_member.py → group_member.py
├── anp_sdk_group_runner.py → group_runner.py
└── anp_tool.py → tool_manager.py
```

### 1.2 中优先级迁移文件

#### F. 配置管理相关
```
anp_open_sdk/config/ → 部分迁移
- unified_config.py → 保留在 core，但文件读取逻辑迁移到 framework
- config_types.py → 保留在 core
```

#### G. 认证客户端相关
```
anp_open_sdk/auth/auth_client.py → 部分重构
- HTTP请求逻辑 → anp_open_sdk_framework/transport/http_transport.py
- 认证逻辑 → 保留在 core，但解耦传输层
```

## 2. 基类重构：哪些代码应修改为"基类 + 基础实现"

### 2.1 用户数据抽象层

#### 当前状态
- `LocalUserData` 和 `LocalUserDataManager` 直接处理文件路径
- 文件操作与业务逻辑混合

#### 重构方案

**Core SDK 基类**:
```python
# anp_open_sdk/core/base_user_data.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

class BaseUserData(ABC):
    """用户数据抽象基类 - 纯内存操作"""
    
    @abstractmethod
    def get_did(self) -> str:
        """获取用户DID"""
        pass
    
    @abstractmethod
    def get_private_key_bytes(self, key_id: str = "key-1") -> Optional[bytes]:
        """获取私钥字节数据"""
        pass
    
    @abstractmethod
    def get_public_key_bytes(self, key_id: str = "key-1") -> Optional[bytes]:
        """获取公钥字节数据"""
        pass
    
    @abstractmethod
    def get_did_document_dict(self) -> Dict[str, Any]:
        """获取DID文档字典"""
        pass
    
    @abstractmethod
    def get_agent_config(self) -> Dict[str, Any]:
        """获取智能体配置"""
        pass

class BaseUserDataManager(ABC):
    """用户数据管理器抽象基类"""
    
    @abstractmethod
    def get_user_data(self, did: str) -> Optional[BaseUserData]:
        """根据DID获取用户数据"""
        pass
    
    @abstractmethod
    def get_all_users(self) -> List[BaseUserData]:
        """获取所有用户数据"""
        pass
    
    @abstractmethod
    def create_user(self, user_params: Dict[str, Any]) -> Optional[BaseUserData]:
        """创建新用户"""
        pass
```

**Framework 实现**:
```python
# anp_open_sdk_framework/adapter_user_data/local_user_data.py
from anp_open_sdk.core.base_user_data import BaseUserData, BaseUserDataManager
from anp_open_sdk_framework.storage.base_storage import BaseStorageProvider

class LocalUserData(BaseUserData):
    """基于文件系统的用户数据实现"""
    
    def __init__(self, credentials_data: Dict[str, Any]):
        # 所有数据都在内存中，不直接访问文件
        self._did = credentials_data["did"]
        self._private_key_bytes = credentials_data["private_key_bytes"]
        self._public_key_bytes = credentials_data["public_key_bytes"]
        self._did_document = credentials_data["did_document"]
        self._agent_config = credentials_data["agent_config"]
    
    def get_private_key_bytes(self, key_id: str = "key-1") -> Optional[bytes]:
        return self._private_key_bytes.get(key_id)

class LocalUserDataManager(BaseUserDataManager):
    """基于文件系统的用户数据管理器"""
    
    def __init__(self, storage: BaseStorageProvider, root_path: str):
        self.storage = storage
        self.root_path = root_path
        self._users_cache = {}
    
    async def load_user_from_storage(self, user_dir: str) -> Optional[BaseUserData]:
        """从存储加载用户数据到内存"""
        # 使用 storage 接口读取文件，构建内存数据
        pass
```

### 2.2 智能体抽象层

#### 当前状态
- `LocalAgent` 的初始化依赖于 user_data 对象，该对象包含文件路径
- 智能体逻辑与文件系统耦合

#### 重构方案

**Core SDK 基类**:
```python
# anp_open_sdk/core/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseAgent(ABC):
    """智能体抽象基类 - 纯内存操作"""
    
    def __init__(self, credentials: BaseUserData):
        self.credentials = credentials
        self.id = self.credentials.get_did()
        self._api_registry = {}
        self._message_handlers = {}
    
    @abstractmethod
    async def handle_request(self, req_did: str, request_data: Dict[str, Any], context: Any) -> Any:
        """处理请求的核心逻辑"""
        pass
    
    @abstractmethod
    def register_api(self, path: str, handler: callable, methods: List[str] = None):
        """注册API处理器"""
        pass
    
    @abstractmethod
    def register_message_handler(self, message_type: str, handler: callable):
        """注册消息处理器"""
        pass

class BaseAgentManager(ABC):
    """智能体管理器抽象基类"""
    
    @abstractmethod
    def register_agent(self, agent: BaseAgent) -> bool:
        """注册智能体"""
        pass
    
    @abstractmethod
    def get_agent(self, did: str) -> Optional[BaseAgent]:
        """获取智能体"""
        pass
    
    @abstractmethod
    def unregister_agent(self, did: str) -> bool:
        """注销智能体"""
        pass
```

**Framework 实现**:

```python
# anp_open_sdk_framework/agents/local_agent.py
from anp_open_sdk.core.base_agent import BaseAgent
from anp_open_sdk_framework.adapter_user_data.local_user_data import LocalUserDataManager


class LocalAgent(BaseAgent):
    """基于本地文件系统的智能体实现"""

    @classmethod
    async def from_did(cls, did: str, user_data_manager: LocalUserDataManager):
        """从DID创建智能体实例"""
        user_data = await user_data_manager.get_user_data(did)
        if not user_data:
            raise ValueError(f"未找到DID对应的用户数据: {did}")
        return cls(user_data)

    @classmethod
    async def from_name(cls, name: str, user_data_manager: LocalUserDataManager):
        """从名称创建智能体实例"""
        user_data = await user_data_manager.get_user_data_by_name(name)
        if not user_data:
            raise ValueError(f"未找到名称对应的用户数据: {name}")
        return cls(user_data)
```

### 2.3 网络管理抽象层

#### 重构方案

**Core SDK 基类**:
```python
# anp_open_sdk/core/base_network.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseNetworkManager(ABC):
    """网络管理器抽象基类"""
    
    def __init__(self):
        self.agents = {}
        self.message_handlers = {}
    
    @abstractmethod
    async def route_request(self, req_did: str, resp_did: str, request_data: Dict[str, Any], context: Any) -> Any:
        """路由请求到对应智能体"""
        pass
    
    @abstractmethod
    def register_agent(self, agent: BaseAgent) -> bool:
        """注册智能体到网络"""
        pass
    
    @abstractmethod
    def get_agent(self, did: str) -> Optional[BaseAgent]:
        """获取网络中的智能体"""
        pass

class BaseServerManager(ABC):
    """服务器管理器抽象基类"""
    
    @abstractmethod
    async def start_server(self) -> bool:
        """启动服务器"""
        pass
    
    @abstractmethod
    async def stop_server(self) -> bool:
        """停止服务器"""
        pass
    
    @abstractmethod
    def register_route(self, path: str, handler: callable, methods: List[str]):
        """注册路由"""
        pass
```

## 3. 文件操作隔离与内存化

### 3.1 存储抽象层设计

**Core SDK 存储接口**:
```python
# anp_open_sdk/core/base_storage.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class BaseStorageProvider(ABC):
    """存储提供者抽象基类"""
    
    @abstractmethod
    async def read_file(self, path: str) -> bytes:
        """读取文件内容"""
        pass
    
    @abstractmethod
    async def write_file(self, path: str, data: bytes) -> bool:
        """写入文件内容"""
        pass
    
    @abstractmethod
    async def list_directories(self, path: str) -> List[str]:
        """列出目录"""
        pass
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """检查路径是否存在"""
        pass
    
    @abstractmethod
    async def create_directory(self, path: str) -> bool:
        """创建目录"""
        pass

class BaseConfigProvider(ABC):
    """配置提供者抽象基类"""
    
    @abstractmethod
    async def load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置"""
        pass
    
    @abstractmethod
    async def save_config(self, config_path: str, config_data: Dict[str, Any]) -> bool:
        """保存配置"""
        pass
```

**Framework 存储实现**:
```python
# anp_open_sdk_framework/storage/file_system_provider.py
import os
import aiofiles
from anp_open_sdk.core.base_storage import BaseStorageProvider

class FileSystemStorageProvider(BaseStorageProvider):
    """基于文件系统的存储实现"""
    
    async def read_file(self, path: str) -> bytes:
        async with aiofiles.open(path, 'rb') as f:
            return await f.read()
    
    async def write_file(self, path: str, data: bytes) -> bool:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            async with aiofiles.open(path, 'wb') as f:
                await f.write(data)
            return True
        except Exception:
            return False
    
    async def list_directories(self, path: str) -> List[str]:
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]

# anp_open_sdk_framework/config/yaml_config_provider.py
import yaml
from anp_open_sdk.core.base_storage import BaseConfigProvider

class YamlConfigProvider(BaseConfigProvider):
    """基于YAML的配置实现"""
    
    def __init__(self, storage: BaseStorageProvider):
        self.storage = storage
    
    async def load_config(self, config_path: str) -> Dict[str, Any]:
        data = await self.storage.read_file(config_path)
        return yaml.safe_load(data.decode('utf-8'))
```

### 3.2 内存化改造

**重构 LocalUserDataManager**:
```python
# anp_open_sdk_framework/adapter_user_data/local_user_data.py
class LocalUserDataManager(BaseUserDataManager):
    def __init__(self, storage: BaseStorageProvider, config_provider: BaseConfigProvider, root_path: str):
        self.storage = storage
        self.config_provider = config_provider
        self.root_path = root_path
        self._users_cache = {}
    
    async def load_users(self):
        """从存储加载所有用户到内存"""
        user_dirs = await self.storage.list_directories(self.root_path)
        
        for user_dir in user_dirs:
            if user_dir.startswith('user_'):
                try:
                    user_data = await self._load_user_from_directory(user_dir)
                    if user_data:
                        self._users_cache[user_data.get_did()] = user_data
                except Exception as e:
                    logger.error(f"加载用户失败 {user_dir}: {e}")
    
    async def _load_user_from_directory(self, user_dir: str) -> Optional[BaseUserData]:
        """从目录加载单个用户数据到内存"""
        user_path = os.path.join(self.root_path, user_dir)
        
        # 加载配置文件
        config_path = os.path.join(user_path, 'agent_cfg.yaml')
        agent_config = await self.config_provider.load_config(config_path)
        
        # 加载DID文档
        did_doc_path = os.path.join(user_path, 'did_document.json')
        did_doc_data = await self.storage.read_file(did_doc_path)
        did_document = json.loads(did_doc_data.decode('utf-8'))
        
        # 加载密钥文件
        key_id = did_document.get('key_id', 'key-1')
        private_key_path = os.path.join(user_path, f'{key_id}_private.pem')
        public_key_path = os.path.join(user_path, f'{key_id}_public.pem')
        
        private_key_bytes = await self.storage.read_file(private_key_path)
        public_key_bytes = await self.storage.read_file(public_key_path)
        
        # 构建内存数据结构
        credentials_data = {
            "did": did_document["id"],
            "private_key_bytes": {key_id: private_key_bytes},
            "public_key_bytes": {key_id: public_key_bytes},
            "did_document": did_document,
            "agent_config": agent_config
        }
        
        return LocalUserData(credentials_data)
```

## 4. Auth模块与HTTP解耦

### 4.1 传输层抽象设计

**Core SDK 传输接口**:
```python
# anp_open_sdk/core/base_transport.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional

@dataclass
class RequestContext:
    """请求上下文 - 协议无关"""
    method: str
    url: str
    headers: Dict[str, str]
    body: Optional[bytes] = None
    params: Optional[Dict[str, Any]] = None

@dataclass
class ResponseContext:
    """响应上下文 - 协议无关"""
    status_code: int
    headers: Dict[str, str]
    body: Optional[bytes] = None
    data: Optional[Dict[str, Any]] = None

class BaseTransport(ABC):
    """传输层抽象基类"""
    
    @abstractmethod
    async def send_request(self, request: RequestContext) -> ResponseContext:
        """发送请求"""
        pass
    
    @abstractmethod
    async def create_server(self, host: str, port: int) -> 'BaseServer':
        """创建服务器"""
        pass

class BaseServer(ABC):
    """服务器抽象基类"""
    
    @abstractmethod
    async def start(self) -> bool:
        """启动服务器"""
        pass
    
    @abstractmethod
    async def stop(self) -> bool:
        """停止服务器"""
        pass
    
    @abstractmethod
    def add_route(self, path: str, handler: callable, methods: List[str]):
        """添加路由"""
        pass
```

**Framework 传输实现**:
```python
# anp_open_sdk_framework/transport/http_transport.py
import aiohttp
from anp_open_sdk.core.base_transport import BaseTransport, RequestContext, ResponseContext

class HttpTransport(BaseTransport):
    """HTTP传输实现"""
    
    async def send_request(self, request: RequestContext) -> ResponseContext:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=request.method,
                url=request.url,
                headers=request.headers,
                data=request.body,
                params=request.params
            ) as response:
                response_body = await response.read()
                response_data = None
                
                if response.content_type == 'application/json':
                    response_data = await response.json()
                
                return ResponseContext(
                    status_code=response.status,
                    headers=dict(response.headers),
                    body=response_body,
                    data=response_data
                )

# anp_open_sdk_framework/transport/websocket_transport.py
class WebSocketTransport(BaseTransport):
    """WebSocket传输实现"""
    
    async def send_request(self, request: RequestContext) -> ResponseContext:
        # WebSocket实现
        pass

# anp_open_sdk_framework/transport/sse_transport.py
class SSETransport(BaseTransport):
    """Server-Sent Events传输实现"""
    
    async def send_request(self, request: RequestContext) -> ResponseContext:
        # SSE实现
        pass
```

### 4.2 认证系统解耦

**重构 auth_client.py**:
```python
# anp_open_sdk/core/auth_manager.py
from anp_open_sdk.core.base_transport import BaseTransport, RequestContext
from anp_open_sdk.core.base_user_data import BaseUserData

class AuthManager:
    """认证管理器 - 协议无关"""
    
    def __init__(self, transport: BaseTransport):
        self.transport = transport
    
    async def authenticate_request(
        self,
        caller_credentials: BaseUserData,
        target_did: str,
        request_url: str,
        method: str = "GET",
        data: Optional[Dict] = None
    ) -> ResponseContext:
        """执行认证请求 - 不依赖具体传输协议"""
        
        # 构建认证头
        auth_header = await self._build_auth_header(caller_credentials, target_did)
        
        # 构建请求上下文
        request_context = RequestContext(
            method=method,
            url=request_url,
            headers={"Authorization": auth_header},
            body=json.dumps(data).encode() if data else None
        )
        
        # 通过传输层发送请求
        return await self.transport.send_request(request_context)
```

**重构 auth_server.py**:
```python
# anp_open_sdk/core/auth_validator.py
class AuthValidator:
    """认证验证器 - 协议无关"""
    
    def verify_request(self, request_context: RequestContext) -> bool:
        """验证请求认证信息"""
        auth_header = request_context.headers.get("Authorization")
        if not auth_header:
            return False
        
        # 验证逻辑（不依赖FastAPI Request对象）
        return self._validate_auth_header(auth_header)
```

## 5. 重构后的架构图

```
anp-open-sdk-monorepo/
├── packages/
│   ├── core/                           # 核心SDK - 最小DID服务
│   │   ├── anp_open_sdk/
│   │   │   ├── core/                   # 核心抽象层
│   │   │   │   ├── base_agent.py       # 智能体基类
│   │   │   │   ├── base_user_data.py   # 用户数据基类
│   │   │   │   ├── base_storage.py     # 存储基类
│   │   │   │   ├── base_transport.py   # 传输基类
│   │   │   │   ├── base_network.py     # 网络管理基类
│   │   │   │   └── auth_manager.py     # 认证管理器
│   │   │   ├── protocols/              # DID/Auth协议实现
│   │   │   │   ├── did_resolver.py     # DID解析器
│   │   │   │   ├── did_signer.py       # DID签名器
│   │   │   │   └── auth_validator.py   # 认证验证器
│   │   │   ├── utils/                  # 工具类
│   │   │   │   ├── crypto_utils.py     # 加密工具
│   │   │   │   └── did_utils.py        # DID工具
│   │   │   └── __init__.py
│   │   └── pyproject.toml
│   │
│   └── framework/                      # 智能体框架
│       ├── anp_open_sdk_framework/
│       │   ├── agents/                 # 智能体实现
│       │   │   ├── local_agent.py      # 本地智能体
│       │   │   └── remote_agent.py     # 远程智能体
│       │   ├── user_data/              # 用户数据实现
│       │   │   └── local_user_data.py  # 本地用户数据
│       │   ├── storage/                # 存储实现
│       │   │   ├── file_system_provider.py  # 文件系统存储
│       │   │   └── memory_provider.py       # 内存存储
│       │   ├── transport/              # 传输实现
│       │   │   ├── http_transport.py   # HTTP传输
│       │   │   ├── websocket_transport.py  # WebSocket传输
│       │   │   └── sse_transport.py    # SSE传输
│       │   ├── server/                 # 服务器实现
│       │   │   ├── fastapi_server.py   # FastAPI服务器
│       │   │   └── route_manager.py    # 路由管理器
│       │   ├── config/                 # 配置实现
│       │   │   └── yaml_config_provider.py  # YAML配置
│       │   ├── decorators/             # 装饰器系统
│       │   │   ├── capability.py       # 能力装饰器
│       │   │   └── route_decorators.py # 路由装饰器
│       │   ├── unified_caller.py       # 统一调用器
│       │   ├── unified_crawler.py      # 统一爬虫
│       │   └── unified_orchestrator.py # 统一编排器
│       └── pyproject.toml
│
├── examples/                           # 示例项目
└── configs/                           # 配置文件
```

## 6. 实施计划

### 阶段1: 核心抽象层建立 (2-3周)
1. 创建 `anp_open_sdk/core/` 目录结构
2. 实现所有基类接口
3. 重构现有代码以使用基类
4. 建立存储和传输抽象层

### 阶段2: 文件迁移和重构 (3-4周)
1. 迁移用户数据管理相关文件
2. 重构 ANPSDK 类，分离服务器逻辑
3. 迁移路由和服务相关文件
4. 实现文件系统存储提供者

### 阶段3: 传输层解耦 (2-3周)
1. 实现传输层抽象
2. 重构认证系统
3. 实现 HTTP、WebSocket、SSE 传输
4. 更新所有网络调用以使用传输层

### 阶段4: Framework层实现 (3-4周)
1. 实现所有Framework层的具体类
2. 创建工厂类和依赖注入
3. 实现配置驱动的组件创建
4. 完善错误处理和日志

### 阶段5: PyPI包化和测试 (2-3周)
1. 配置 Core SDK 的 pyproject.toml
2. 实现包的独立性测试
3. 创建安装和使用文档
4. 发布到 PyPI

### 阶段6: 向后兼容和迁移 (1-2周)
1. 创建兼容性层
2. 更新所有示例和文档
3. 提供迁移指南
4. 性能测试和优化

## 7. 预期效果

### 7.1 Core SDK (anp_open_sdk)
- **纯净性**: 无文件I/O，无HTTP依赖，纯内存操作
- **可测试性**: 所有组件可独立测试，易于mock
- **可扩展性**: 通过接口扩展，支持多种实现
- **PyPI就绪**: 可独立安装和使用

### 7.2 Framework (anp_open_sdk_framework)
- **实用性**: 提供开箱即用的实现
- **灵活性**: 支持多种传输协议和存储方式
- **可配置性**: 通过配置文件控制行为
- **向后兼容**: 保持现有API的兼容性

### 7.3 开发体验
- **清晰的职责分离**: 开发者明确知道在哪一层工作
- **渐进式采用**: 可以只使用Core SDK，也可以使用完整Framework
- **易于扩展**: 新的传输协议和存储方式易于添加
- **测试友好**: 每一层都可以独立测试

这个重构方案将使 ANP Open SDK 成为一个真正模块化、可扩展、可测试的框架，同时为未来的发展奠定坚实的基础。
