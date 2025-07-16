# ANP SDK 完整重构方案 - 设计思路详解

## 1. 整体架构重新设计

### 1.1 新的目录结构

```
anp-open-sdk-monorepo/
├── /packages
│   ├── /core                           # 核心SDK - 最小DID服务
│   │   ├── /anp_open_sdk
│   │   │   ├── /protocols              # DID/Auth协议实现
│   │   │   ├── /agents                 # Agent核心抽象
│   │   │   │   ├── local_agent.py
│   │   │   │   └── remote_agent.py
│   │   │   ├── /contact                # 联系人管理
│   │   │   ├── /storage                # 存储接口和基础实现
│   │   │   ├── /service                # 最小HTTP服务
│   │   │   │   └── /router
│   │   │   │       ├── route_manager.py      # 路由管理器
│   │   │   │       ├── did_format_manager.py # DID格式管理器
│   │   │   │       ├── router_did.py         # DID路由
│   │   │   │       └── router_auth.py        # 认证路由
│   │   │   ├── /config                 # 配置管理
│   │   │   └── anp_sdk.py             # 核心SDK类
│   │   └── pyproject.toml
│   │
│   └── /framework                      # 智能体框架
│       ├── /anp_open_sdk_framework
│       │   ├── /decorators             # 装饰器系统
│       │   │   ├── capability.py      # 能力装饰器
│       │   │   ├── mcp_integration.py # MCP集成装饰器
│       │   │   └── route_decorators.py # 路由装饰器
│       │   ├── /mcp_tools              # MCP工具集成
│       │   │   ├── mcp_client.py      # 简化MCP客户端
│       │   │   ├── crawler_tool.py    # Crawler MCP工具
│       │   │   └── tool_registry.py   # 工具注册表
│       │   ├── /capability_manager    # 能力管理
│       │   │   ├── discovery.py       # 自动发现
│       │   │   └── publisher.py       # 能力发布
│       │   ├── /llm_integration        # LLM集成
│       │   │   ├── tool_manager.py    # LLM工具管理器
│       │   │   └── llm_agent.py       # LLM智能体
│       │   ├── /agent_manager          # Agent管理
│       │   └── enhanced_sdk.py         # 增强SDK
│       └── pyproject.toml
│
├── /examples                           # 示例项目
└── /configs                           # 配置文件
```

**设计思路：**
- **分层架构**：将复杂的功能分为Core（基础）和Framework（高级）两层，实现关注点分离
- **Monorepo结构**：便于版本管理和依赖控制，Core可以独立使用，Framework依赖Core
- **模块化设计**：每个功能模块职责单一，便于测试和维护

### 1.2 架构设计原则

- **分层清晰**：Core层提供基础DID服务，Framework层提供高级功能
- **装饰器驱动**：使用装饰器简化开发体验
- **MCP集成**：统一的工具生态系统
- **LLM友好**：原生支持LLM工具调用
- **配置统一**：统一的配置管理系统

## 2. 核心SDK重构

### 2.1 核心SDK类 (packages/core/anp_open_sdk/anp_sdk.py)

**设计思路：**
- **最小化原则**：只保留DID服务和Agent路由的核心功能，移除复杂的业务逻辑
- **单一职责**：专注于HTTP服务、路由管理和Agent注册
- **配置驱动**：所有行为通过配置文件控制，提高灵活性
- **线程安全**：支持生产环境的后台运行模式

**功能安排：**
1. **Agent管理**：注册、查找、路由Agent请求
2. **HTTP服务**：基于FastAPI的轻量级服务器
3. **路由处理**：统一的API路由和DID路由
4. **配置集成**：与统一配置系统集成

```python
"""
核心SDK - 只保留基础DID服务和Agent路由能力

设计理念：
1. 最小化核心：只包含必要的DID服务功能
2. 配置驱动：所有行为通过配置控制
3. 扩展友好：为Framework层提供清晰的扩展点
4. 生产就绪：支持调试和生产两种运行模式
"""
from fastapi import FastAPI, Request
from typing import List, Dict, Any
import uvicorn
import threading
import logging

from .agents.local_agent import LocalAgent
from .service.router.route_manager import RouteManager
from .service.router.did_format_manager import DIDFormatManager
from .service.router import router_did, router_auth
from .storage.local_file import LocalFileStorage
from .config import get_global_config

logger = logging.getLogger(__name__)

class ANPSDK:
    """
    核心SDK - 最小可用的DID服务
    
    职责：
    - Agent生命周期管理
    - HTTP服务器管理
    - 路由配置和处理
    - DID标准化处理
    """
    
    def __init__(self, storage=None, agents: List[LocalAgent] = None):
        # 存储层：可插拔的存储实现
        self.storage = storage or LocalFileStorage()
        
        # Agent注册表：DID -> Agent映射
        self.agents = {agent.id: agent for agent in (agents or [])}
        
        # 路由管理器：统一的路由配置管理
        self.route_manager = RouteManager()
        
        # DID管理器：DID格式化和解析
        self.did_manager = DIDFormatManager()
        
        # FastAPI应用：HTTP服务核心
        self.app = self._create_app()
        
        # 服务器状态
        self.server_running = False
        
        logger.info(f"🚀 ANP SDK initialized with {len(self.agents)} agents")
    
    def _create_app(self) -> FastAPI:
        """
        创建FastAPI应用
        
        设计考虑：
        - 条件性文档：生产环境禁用API文档
        - 模块化路由：通过include_router组织路由
        - 统一错误处理：集中的异常处理机制
        """
        config = get_global_config()
        
        app = FastAPI(
            title="ANP DID Service",
            description="ANP SDK Core DID Service",
            version="0.1.0",
            docs_url="/docs" if config.anp_sdk.debug_mode else None
        )
        
        # 注册核心路由：DID和认证相关
        app.include_router(router_did.router, prefix="")
        app.include_router(router_auth.router, prefix="")
        
        # 注册Agent API路由：动态Agent处理
        self._register_agent_routes(app)
        
        # 根路径：服务状态和信息
        @app.get(self.route_manager.get_route("api", "root"))
        async def root():
            return {
                "service": "ANP DID Service",
                "version": "0.1.0",
                "agents": len(self.agents),
                "routes": "configured"
            }
        
        return app
    
    def _register_agent_routes(self, app: FastAPI):
        """
        注册Agent API路由
        
        设计思路：
        - 统一入口：所有Agent请求通过统一处理器
        - DID标准化：自动处理各种DID格式
        - 错误处理：统一的错误响应格式
        - 上下文传递：保留完整的请求上下文
        """
        
        @app.get(self.route_manager.get_route("agent", "api"))
        @app.post(self.route_manager.get_route("agent", "api"))
        async def agent_api_handler(did: str, subpath: str, request: Request):
            """
            Agent API处理器
            
            功能：
            1. DID标准化和验证
            2. Agent查找和路由
            3. 请求数据构造
            4. 统一错误处理
            """
            try:
                # 构建请求上下文：用于DID解析
                request_context = {
                    "host": request.url.hostname,
                    "port": request.url.port or 80,
                    "path": str(request.url.path)
                }
                
                # DID标准化：支持多种DID格式
                normalized_did = self.did_manager.normalize_did(did, request_context)
                
                # Agent查找：基于标准化DID
                if normalized_did not in self.agents:
                    return {"error": f"Agent not found: {normalized_did}", "status": 404}
                
                agent = self.agents[normalized_did]
                
                # 请求数据构造：统一的数据格式
                if request.method == "GET":
                    request_data = dict(request.query_params)
                else:
                    request_data = await request.json()
                
                request_data.update({
                    "type": "api_call",
                    "path": f"/{subpath}",
                    "method": request.method
                })
                
                # Agent处理：委托给具体Agent
                result = await agent.handle_request("system", request_data, request)
                return result
                
            except Exception as e:
                logger.error(f"Agent API error: {e}")
                return {"error": str(e), "status": 500}
    
    def register_agent(self, agent: LocalAgent):
        """
        注册Agent
        
        设计考虑：
        - 幂等性：重复注册不会出错
        - 日志记录：便于调试和监控
        - 扩展点：Framework层可以重写此方法
        """
        self.agents[agent.id] = agent
        logger.info(f"✅ Registered agent: {agent.name} ({agent.id})")
    
    def get_agent(self, did: str) -> LocalAgent:
        """获取Agent：简单的字典查找"""
        return self.agents.get(did)
    
    def start_server(self, host: str = None, port: int = None):
        """
        启动服务器
        
        设计思路：
        - 模式切换：调试模式阻塞运行，生产模式后台运行
        - 配置优先级：参数 > 配置文件 > 默认值
        - 线程安全：生产模式使用独立线程
        """
        config = get_global_config()
        host = host or config.anp_sdk.host
        port = port or config.anp_sdk.port
        
        if config.anp_sdk.debug_mode:
            # Debug模式：阻塞运行，支持热重载
            uvicorn.run(self.app, host=host, port=port, reload=True)
        else:
            # 生产模式：后台线程运行
            uvicorn_config = uvicorn.Config(self.app, host=host, port=port)
            self.uvicorn_server = uvicorn.Server(uvicorn_config)
            
            def run_server():
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.uvicorn_server.serve())
            
            self.server_thread = threading.Thread(target=run_server, daemon=True)
            self.server_thread.start()
        
        self.server_running = True
        logger.info(f"🔥 Server started on {host}:{port}")
    
    def stop_server(self):
        """
        停止服务器
        
        设计考虑：
        - 优雅关闭：给服务器时间完成当前请求
        - 资源清理：确保线程和连接正确关闭
        """
        if hasattr(self, 'uvicorn_server'):
            self.uvicorn_server.should_exit = True
        if hasattr(self, 'server_thread'):
            self.server_thread.join(timeout=5)
        self.server_running = False
        logger.info("🛑 Server stopped")
```

### 2.2 路由管理器 (packages/core/anp_open_sdk/service/router/route_manager.py)

**设计思路：**
- **单例模式**：全局唯一的路由配置管理器
- **缓存机制**：避免重复的配置查找
- **配置驱动**：所有路由通过配置文件定义
- **错误处理**：清晰的错误信息和异常处理

**功能安排：**
1. **路由查找**：根据分类和名称查找路由
2. **缓存管理**：提高路由查找性能
3. **配置集成**：与统一配置系统集成
4. **批量操作**：支持获取所有路由

```python
"""
统一路由管理器

设计理念：
1. 单例模式：确保全局路由配置一致性
2. 缓存优化：避免重复的配置文件解析
3. 类型安全：通过配置类型确保路由正确性
4. 扩展友好：支持动态路由注册和查询
"""
from typing import Dict
from anp_open_sdk.config import get_global_config
import logging

logger = logging.getLogger(__name__)

class RouteManager:
    """
    统一路由管理器
    
    职责：
    - 路由配置的集中管理
    - 路由查找的性能优化
    - 路由配置的验证和错误处理
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式：确保全局唯一实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化路由管理器
        
        设计考虑：
        - 防重复初始化：通过_initialized标志
        - 配置加载：从全局配置加载路由设置
        - 缓存初始化：准备路由缓存字典
        """
        if hasattr(self, '_initialized'):
            return
        
        config = get_global_config()
        self.routes_config = config.anp_sdk.routes
        self._route_cache = {}  # 路由缓存：category.name -> route
        self._initialized = True
        logger.info("📋 Route manager initialized")
    
    def get_route(self, category: str, name: str) -> str:
        """
        获取配置的路由路径
        
        设计思路：
        - 缓存优先：先检查缓存，避免重复查找
        - 配置查找：通过反射机制查找配置
        - 错误处理：提供清晰的错误信息
        
        参数：
        - category: 路由分类（如 'agent', 'api'）
        - name: 路由名称（如 'api', 'root'）
        
        返回：路由路径字符串
        """
        cache_key = f"{category}.{name}"
        
        # 缓存命中：直接返回
        if cache_key in self._route_cache:
            return self._route_cache[cache_key]
        
        try:
            # 配置查找：category.name -> route
            category_routes = getattr(self.routes_config, category)
            route = getattr(category_routes, name)
            
            # 缓存存储：提高后续查找性能
            self._route_cache[cache_key] = route
            return route
        except AttributeError:
            logger.error(f"Route not found: {cache_key}")
            raise ValueError(f"Route configuration not found: {cache_key}")
    
    def get_all_routes(self, category: str = None) -> Dict[str, str]:
        """
        获取所有路由
        
        功能：
        - 分类查询：获取特定分类的所有路由
        - 全量查询：获取所有分类的路由
        - 动态发现：通过反射发现配置中的路由
        """
        if category:
            # 单分类查询
            try:
                category_routes = getattr(self.routes_config, category)
                return {
                    name: getattr(category_routes, name)
                    for name in dir(category_routes)
                    if not name.startswith('_')  # 排除私有属性
                }
            except AttributeError:
                return {}
        
        # 全量查询：所有已知分类
        all_routes = {}
        for cat in ['wba', 'publisher', 'agent', 'api', 'websocket']:
            all_routes[cat] = self.get_all_routes(cat)
        return all_routes
```

### 2.3 DID格式管理器 (packages/core/anp_open_sdk/service/router/did_format_manager.py)

**设计思路：**
- **标准化处理**：统一处理各种DID格式
- **上下文感知**：根据请求上下文推断DID信息
- **配置驱动**：DID格式规则通过配置定义
- **向后兼容**：支持简化的unique_id格式

**功能安排：**
1. **DID创建**：根据参数生成标准DID
2. **DID解析**：解析各种格式的DID
3. **DID标准化**：将简化格式转换为完整DID
4. **方法标识符**：管理本地方法的标识符

```python
"""
DID格式管理器

设计理念：
1. 标准化：统一处理各种DID格式变体
2. 上下文感知：根据请求上下文智能推断DID信息
3. 向后兼容：支持简化的unique_id格式
4. 配置驱动：所有格式规则通过配置定义
"""
import re
import urllib.parse
import secrets
from typing import Dict, Optional, Tuple
from anp_open_sdk.config import get_global_config
import logging

logger = logging.getLogger(__name__)

class DIDFormatManager:
    """
    DID格式管理器
    
    职责：
    - DID的创建、解析和标准化
    - 支持多种DID格式变体
    - 本地方法标识符管理
    - 配置驱动的格式规则
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式：确保DID格式规则全局一致"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化DID格式管理器
        
        设计考虑：
        - 防重复初始化
        - 配置加载：从全局配置加载DID格式规则
        """
        if hasattr(self, '_initialized'):
            return
            
        config = get_global_config()
        self.did_config = config.anp_sdk.did_format
        self._initialized = True
        logger.info("🔧 DID format manager initialized")
    
    def create_did(self, host: str, port: int, user_type: str = "user",
                   dir: str = None, unique_id: str = None) -> str:
        """
        创建标准格式的DID
        
        设计思路：
        - 参数验证：确保用户类型有效
        - 端口处理：标准端口省略，非标准端口编码
        - 唯一性：自动生成或使用提供的unique_id
        - URL编码：处理特殊字符
        
        DID格式：did:method:host[:port]:dir:user_type:unique_id
        """
        dir = dir or self.did_config.default_dir
        unique_id = unique_id or secrets.token_hex(8)  # 16位十六进制
        
        # 用户类型验证
        if user_type not in self.did_config.user_types:
            raise ValueError(f"Invalid user type: {user_type}")
        
        # 端口处理：标准端口省略，非标准端口编码
        if port not in self.did_config.default_ports:
            host_port = f"{host}{self.did_config.port_encoding}{port}"
        else:
            host_port = host
        
        # DID组装
        segments = [
            "did",
            self.did_config.method,
            host_port,
            urllib.parse.quote(dir, safe=''),  # URL编码目录
            user_type,
            unique_id
        ]
        
        return ':'.join(segments)
    
    def parse_did(self, did_or_id: str) -> Dict[str, Optional[str]]:
        """
        解析DID或unique_id
        
        设计思路：
        - 格式检测：自动识别DID格式类型
        - 向后兼容：支持简化的unique_id格式
        - 正则解析：使用正则表达式解析完整DID
        - 统一返回：标准化的解析结果格式
        
        支持格式：
        1. 完整DID：did:wba:host:dir:user_type:unique_id
        2. 简化ID：16位十六进制字符串
        """
        did_or_id = urllib.parse.unquote(did_or_id)
        
        # 检查是否是16位unique_id（向后兼容）
        if len(did_or_id) == 16 and did_or_id.isalnum():
            return {
                "format": "unique_id",
                "unique_id": did_or_id,
                "host": None,
                "port": None,
                "dir": None,
                "user_type": None,
                "full_did": None
            }
        
        # 解析完整DID
        if did_or_id.startswith(f"did:{self.did_config.method}:"):
            # 正则模式：支持端口编码和可选端口
            pattern = rf"did:{self.did_config.method}:([^:]+?)(?:%3A|:)?(\d*)?:([^:]+):([^:]+):([a-f0-9]{{16}})"
            match = re.match(pattern, did_or_id)
            
            if match:
                host = match.group(1)
                port = match.group(2) or "80"  # 默认端口
                dir = urllib.parse.unquote(match.group(3))
                user_type = match.group(4)
                unique_id = match.group(5)
                
                return {
                    "format": "full_did",
                    "host": host,
                    "port": port,
                    "dir": dir,
                    "user_type": user_type,
                    "unique_id": unique_id,
                    "full_did": did_or_id
                }
        
        # 未知格式
        return {
            "format": "unknown",
            "value": did_or_id,
            "host": None,
            "port": None,
            "dir": None,
            "user_type": None,
            "unique_id": None,
            "full_did": None
        }
    
    def normalize_did(self, did_or_id: str, request_context: Dict = None) -> str:
        """
        标准化DID格式
        
        设计思路：
        - 格式统一：将各种格式转换为完整DID
        - 上下文推断：从请求上下文推断缺失信息
        - 智能判断：根据路径判断用户类型
        
        功能：
        1. 完整DID直接返回
        2. unique_id + 上下文 -> 完整DID
        3. 未知格式原样返回
        """
        parsed = self.parse_did(did_or_id)
        
        # 完整DID：直接返回
        if parsed["format"] == "full_did":
            return parsed["full_did"]
        
        # unique_id + 上下文：构造完整DID
        if parsed["format"] == "unique_id" and request_context:
            host = request_context.get("host", "localhost")
            port = request_context.get("port", 80)
            
            # 从路径推断用户类型
            path = request_context.get("path", "")
            if "hostuser" in path:
                user_type = "hostuser"
            else:
                user_type = "user"
            
            return self.create_did(
                host=host,
                port=port,
                user_type=user_type,
                unique_id=parsed["unique_id"]
            )
        
        # 其他情况：原样返回
        return did_or_id
    
    def create_method_identifier(self, did: str, method_name: str) -> str:
        """
        创建本地方法标识符
        
        格式：did::method_name
        用途：在本地方法注册表中唯一标识方法
        """
        return f"{did}::{method_name}"
    
    def parse_method_identifier(self, method_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        解析方法标识符
        
        返回：(did, method_name) 或 (None, None)
        """
        if "::" not in method_id:
            return None, None
        parts = method_id.split("::", 1)
        return parts[0], parts[1]
```

## 3. Framework层重构

### 3.1 装饰器系统

#### 3.1.1 能力装饰器 (packages/framework/anp_open_sdk_framework/decorators/capability.py)

**设计思路：**
- **声明式编程**：通过装饰器声明Agent能力
- **元数据驱动**：将能力信息存储为函数元数据
- **发布模式**：支持多种能力发布方式
- **错误处理**：统一的错误处理和响应格式

**功能安排：**
1. **能力标记**：将普通函数标记为Agent能力
2. **元数据管理**：存储能力的描述、模式等信息
3. **发布控制**：控制能力的发布方式（本地方法/API/两者）
4. **错误包装**：统一的错误处理和响应格式

```python
"""
能力装饰器系统

设计理念：
1. 声明式：通过装饰器声明Agent能力，简化开发
2. 元数据驱动：将能力信息作为函数元数据存储
3. 发布灵活：支持多种发布模式（本地方法、API、两者）
4. 错误统一：标准化的错误处理和响应格式
"""
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def capability(name: str, 
               description: str,
               input_schema: Dict[str, Any] = None,
               output_schema: Dict[str, Any] = None,
               tags: List[str] = None,
               publish_as: str = "both"):  # "local_method", "expose_api", "both"
    """
    能力装饰器 - 标记函数为Agent能力
    
    设计思路：
    - 元数据存储：将能力信息存储在函数的_capability_meta属性中
    - 包装器模式：保持原函数签名，添加错误处理
    - 发布控制：通过publish_as参数控制发布方式
    - JSON Schema：使用标准的JSON Schema描述输入输出
    
    参数：
    - name: 能力名称，用于注册和调用
    - description: 能力描述，用于文档和LLM理解
    - input_schema: 输入参数的JSON Schema
    - output_schema: 输出结果的JSON Schema
    - tags: 标签列表，用于分类和搜索
    - publish_as: 发布方式（local_method/expose_api/both）
    """
    def decorator(func: Callable):
        # 元数据存储：能力的所有信息
        func._capability_meta = {
            'name': name,
            'description': description,
            'input_schema': input_schema or {},
            'output_schema': output_schema or {},
            'tags': tags or [],
            'publish_as': publish_as,
            'func': func
        }
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            """
            能力包装器
            
            功能：
            - 统一错误处理：捕获异常并标准化响应
            - 成功响应：包含结果和能力标识
            - 日志记录：记录能力执行情况
            """
            try:
                result = await func(*args, **kwargs)
                return {
                    'success': True,
                    'result': result,
                    'capability': name
                }
            except Exception as e:
                logger.error(f"Capability {name} error: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'capability': name
                }
        
        wrapper._capability_meta = func._capability_meta
        return wrapper
    
    return decorator

def expose_api(path: str, methods: List[str] = None):
    """
    API暴露装饰器 - 直接暴露为HTTP端点
    
    设计思路：
    - 路径映射：将函数直接映射到HTTP路径
    - 方法支持：支持多种HTTP方法
    - 简化开发：无需手动注册路由
    """
    def decorator(func: Callable):
        func._api_meta = {
            'path': path,
            'methods': methods or ['POST'],
            'func': func
        }
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        
        wrapper._api_meta = func._api_meta
        return wrapper
    
    return decorator

def local_method(description: str = "", tags: List[str] = None):
    """
    本地方法装饰器 - 只注册为本地方法
    
    设计思路：
    - 便捷装饰器：简化只需本地方法的场景
    - 自动命名：使用函数名作为能力名
    - 文档提取：自动使用docstring作为描述
    """
    def decorator(func: Callable):
        return capability(
            name=func.__name__,
            description=description or func.__doc__ or f"本地方法: {func.__name__}",
            tags=tags or [],
            publish_as="local_method"
        )(func)
    
    return decorator
```

#### 3.1.2 MCP集成装饰器 (packages/framework/anp_open_sdk_framework/decorators/mcp_integration.py)

**设计思路：**
- **MCP标准化**：统一的MCP工具调用接口
- **LLM集成**：原生支持LLM工具调用
- **权限控制**：细粒度的工具调用权限管理
- **上下文感知**：区分LLM调用和普通调用

**功能安排：**
1. **MCP工具包装**：将MCP工具包装为Agent能力
2. **LLM工具暴露**：选择性地暴露工具给LLM
3. **权限管理**：支持工具调用的人工批准
4. **调用记录**：记录LLM工具调用历史

```python
"""
MCP集成装饰器系统

设计理念：
1. MCP标准化：统一的MCP工具调用接口
2. LLM友好：原生支持LLM工具调用协议
3. 权限控制：细粒度的工具调用权限管理
4. 上下文感知：区分不同调用来源和场景
"""
from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from .capability import capability
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

def mcp_tool(tool_name: str, 
             server_name: str = "default",
             description: str = None,
             tags: List[str] = None,
             publish_as: str = "local_method",
             expose_to_llm: bool = False,  # 是否暴露给LLM
             llm_tool_name: str = None,    # LLM中的工具名
             require_approval: bool = False): # 是否需要人工批准
    """
    增强的MCP工具装饰器 - 支持LLM工具调用
    
    设计思路：
    - 双重身份：既是Agent能力，也可以是LLM工具
    - 权限分层：普通调用和LLM调用可以有不同权限
    - 上下文传递：通过_call_context传递调用信息
    - 自动标签：自动添加MCP相关标签
    
    参数：
    - tool_name: MCP工具名称
    - server_name: MCP服务器名称
    - expose_to_llm: 是否暴露给LLM使用
    - require_approval: LLM调用时是否需要人工批准
    """
    def decorator(func: Callable):
        auto_description = description or f"MCP工具: {tool_name} (来自 {server_name})"
        auto_tags = (tags or []) + ["mcp", server_name, "tool"]
        
        # 添加LLM相关元数据
        func._mcp_meta = {
            'tool_name': tool_name,
            'server_name': server_name,
            'is_mcp_tool': True,
            'expose_to_llm': expose_to_llm,
            'llm_tool_name': llm_tool_name or tool_name,
            'require_approval': require_approval
        }
        
        # 创建MCP调用包装器
        async def mcp_wrapper(**kwargs):
            """
            MCP工具包装器
            
            功能：
            - 调用上下文检查：识别LLM调用
            - 权限验证：LLM调用的批准机制
            - MCP客户端调用：实际的工具执行
            - 调用记录：记录LLM工具调用
            """
            try:
                # 检查调用上下文
                call_context = kwargs.pop('_call_context', {})
                is_llm_call = call_context.get('is_llm_call', False)
                
                # 如果是LLM调用且需要批准
                if is_llm_call and require_approval:
                    approval = await _request_approval(tool_name, kwargs, call_context)
                    if not approval:
                        raise Exception("Tool call not approved by user")
                
                # 获取MCP客户端并调用工具
                mcp_client = _get_mcp_client(server_name)
                if not mcp_client:
                    raise Exception(f"MCP server {server_name} not connected")
                
                result = await mcp_client.call_tool(tool_name, kwargs)
                
                # 记录LLM工具调用
                if is_llm_call:
                    await _log_llm_tool_call(tool_name, kwargs, result, call_context)
                
                return result
                
            except Exception as e:
                logger.error(f"MCP tool {tool_name} error: {e}")
                raise
        
        # 应用capability装饰器
        capability_decorator = capability(
            name=f"mcp_{tool_name.replace('-', '_')}",
            description=auto_description,
            tags=auto_tags,
            publish_as=publish_as
        )
        
        wrapped_func = capability_decorator(mcp_wrapper)
        wrapped_func._mcp_meta = func._mcp_meta
        
        return wrapped_func
    
    return decorator

def mcp_server_config(servers: Dict[str, Dict[str, Any]]):
    """
    MCP服务器配置装饰器 - 用于Agent类
    
    设计思路：
    - 类级配置：在Agent类上声明MCP服务器
    - 自动发现：能力发现时自动连接服务器
    - 配置集中：所有MCP配置在一处管理
    """
    def decorator(cls):
        cls._mcp_servers = servers
        return cls
    return decorator

def llm_mcp_tool(tool_name: str, 
                 server_name: str = "default",
                 description: str = None,
                 require_approval: bool = False):
    """
    专门暴露给LLM的MCP工具装饰器
    
    设计思路：
    - 便捷装饰器：专门用于LLM工具的简化版本
    - 默认配置：自动设置LLM相关的默认参数
    """
    return mcp_tool(
        tool_name=tool_name,
        server_name=server_name, 
        description=description,
        publish_as="local_method",
        expose_to_llm=True,
        require_approval=require_approval
    )

# 全局MCP客户端注册表
_mcp_clients = {}

def _get_mcp_client(server_name: str):
    """获取MCP客户端"""
    return _mcp_clients.get(server_name)

def _register_mcp_client(server_name: str, client):
    """注册MCP客户端"""
    _mcp_clients[server_name] = client

async def _request_approval(tool_name: str, arguments: Dict[str, Any], 
                          call_context: Dict[str, Any]) -> bool:
    """
    请求用户批准工具调用
    
    设计思路：
    - 交互式批准：通过控制台与用户交互
    - 信息透明：显示工具名称、参数和上下文
    - 安全默认：异常情况默认拒绝
    """
    print(f"\n🤖 LLM请求调用工具: {tool_name}")
    print(f"📋 参数: {json.dumps(arguments, indent=2, ensure_ascii=False)}")
    print(f"🔍 上下文: {call_context.get('llm_context', {})}")
    
    try:
        response = input("是否批准此工具调用？(y/n): ").strip().lower()
        return response in ['y', 'yes', '是', '批准']
    except:
        return False

async def _log_llm_tool_call(tool_name: str, arguments: Dict[str, Any], 
                           result: Dict[str, Any], call_context: Dict[str, Any]):
    """
    记录LLM工具调用
    
    设计思路：
    - 完整记录：记录调用的所有相关信息
    - 时间戳：便于审计和分析
    - 结构化：使用JSON格式便于后续处理
    """
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'tool_name': tool_name,
        'arguments': arguments,
        'result': result,
        'context': call_context
    }
    
    logger.info(f"LLM工具调用记录: {json.dumps(log_entry, ensure_ascii=False)}")
```

### 3.2 MCP工具集成

#### 3.2.1 简化的MCP客户端 (packages/framework/anp_open_sdk_framework/mcp_tools/mcp_client.py)

**设计思路：**
- **协议简化**：简化MCP协议的复杂性
- **异步支持**：完全异步的客户端实现
- **错误处理**：健壮的错误处理和重连机制
- **工具发现**：自动发现服务器提供的工具

**功能安排：**
1. **连接管理**：MCP服务器的连接和断开
2. **协议处理**：MCP协议的握手和通信
3. **工具调用**：统一的工具调用接口
4. **工具发现**：自动发现可用工具

```python
"""
简化的MCP客户端

设计理念：
1. 协议简化：隐藏MCP协议的复杂性，提供简单接口
2. 异步优先：完全异步的设计，适合现代Python应用
3. 错误健壮：完善的错误处理和连接管理
4. 自动发现：自动发现和注册服务器提供的工具
"""
import asyncio
import json
import subprocess
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """
    简化的MCP客户端
    
    职责：
    - MCP服务器连接管理
    - MCP协议处理和通信
    - 工具发现和调用
    - 错误处理和日志记录
    """
    
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.process = None  # 子进程对象
        self.tools = {}      # 可用工具字典
        self.connected = False
    
    async def connect(self, command: List[str], env: Dict[str, str] = None):
        """
        连接MCP服务器
        
        设计思路：
        - 子进程启动：通过subprocess启动MCP服务器
        - 协议握手：执行MCP初始化握手
        - 工具发现：自动发现服务器提供的工具
        - 状态管理：维护连接状态
        
        参数：
        - command: 启动MCP服务器的命令
        - env: 环境变量
        """
        try:
            # 启动MCP服务器子进程
            self.process = await asyncio.create_subprocess_exec(
                *command,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            # 初始化握手
            await self._initialize()
            
            # 发现工具
            await self._discover_tools()
            
            self.connected = True
            logger.info(f"✅ Connected to MCP server: {self.server_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect MCP server {self.server_name}: {e}")
            return False
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        调用MCP工具
        
        设计思路：
        - 连接检查：确保服务器已连接
        - 请求构造：按MCP协议构造请求
        - 错误处理：处理工具调用错误
        - 结果提取：从响应中提取结果
        """
        if not self.connected:
            raise Exception(f"MCP server {self.server_name} not connected")
        
        # 构造MCP工具调用请求
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }
        
        response = await self._send_request(request)
        
        if "error" in response:
            raise Exception(f"MCP tool error: {response['error']}")
        
        return response.get("result", {})
    
    async def _initialize(self):
        """
        初始化MCP连接
        
        功能：
        - 发送初始化请求
        - 声明客户端能力
        - 完成协议握手
        """
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "anp-open-sdk",
                    "version": "0.1.0"
                }
            }
        }
        
        await self._send_request(init_request)
    
    async def _discover_tools(self):
        """
        发现可用工具
        
        功能：
        - 请求工具列表
        - 解析工具信息
        - 构建工具注册表
        """
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list"
        }
        
        response = await self._send_request(request)
        
        if "result" in response and "tools" in response["result"]:
            for tool in response["result"]["tools"]:
                self.tools[tool["name"]] = tool
                logger.info(f"  📋 Discovered tool: {tool['name']}")
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送请求并接收响应
        
        设计思路：
        - JSON-RPC协议：使用标准的JSON-RPC格式
        - 异步通信：非阻塞的请求响应
        - 错误处理：处理通信错误
        """
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        response_line = await self.process.stdout.readline()
        return json.loads(response_line.decode())
    
    async def close(self):
        """
        关闭连接
        
        设计思路：
        - 优雅关闭：给进程时间正常退出
        - 资源清理：确保进程和连接正确关闭
        - 状态更新：更新连接状态
        """
        if self.process:
            self.process.terminate()
            await self.process.wait()
        self.connected = False
        logger.info(f"🔌 Disconnected MCP server: {self.server_name}")
```

#### 3.2.2 Crawler作为MCP工具 (packages/framework/anp_open_sdk_framework/mcp_tools/crawler_tool.py)

**设计思路：**
- **现有集成**：将现有的Crawler功能包装为MCP工具
- **工具标准化**：提供标准的MCP工具接口
- **功能扩展**：在原有基础上增加通用爬取功能
- **独立运行**：可以作为独立的MCP服务器运行

**功能安排：**
1. **智能体爬取**：包装现有的Agent爬取功能
2. **通用爬取**：提供通用的网页爬取工具
3. **MCP服务器**：实现完整的MCP服务器协议
4. **错误处理**：统一的错误处理和响应格式

```python
"""
Crawler MCP工具

设计理念：
1. 现有集成：将现有Crawler功能包装为标准MCP工具
2. 功能扩展：在原有基础上增加通用爬取能力
3. 标准协议：完全符合MCP协议规范
4. 独立部署：可以作为独立的MCP服务器运行
"""
import asyncio
import json
from typing import Dict, Any
from anp_open_sdk.service.interaction.anp_tool import ANPToolCrawler
import logging

logger = logging.getLogger(__name__)

class CrawlerMCPTool:
    """
    将Crawler封装为MCP工具
    
    职责：
    - 现有功能包装：将ANPToolCrawler包装为MCP工具
    - 工具定义：定义MCP工具的输入输出模式
    - 请求处理：处理MCP协议请求
    - 错误管理：统一的错误处理
    """
    
    def __init__(self):
        self.crawler = ANPToolCrawler()
        
        # 定义可用工具
        self.tools = [
            {
                "name": "crawl_agent",
                "description": "爬取智能体信息并执行任务",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "req_did": {"type": "string", "description": "请求方DID"},
                        "resp_did": {"type": "string", "description": "目标智能体DID"},
                        "task_input": {"type": "string", "description": "任务描述"},
                        "initial_url": {"type": "string", "description": "初始URL"},
                        "use_two_way_auth": {"type": "boolean", "default": True},
                        "task_type": {"type": "string", "enum": ["function_query", "root_query"], "default": "function_query"}
                    },
                    "required": ["req_did", "resp_did", "task_input", "initial_url"]
                }
            },
            {
                "name": "crawl_web",
                "description": "通用网页爬取工具",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string", "description": "目标URL"},
                        "method": {"type": "string", "enum": ["GET", "POST"], "default": "GET"},
                        "headers": {"type": "object", "description": "HTTP头"},
                        "data": {"type": "object", "description": "POST数据"}
                    },
                    "required": ["url"]
                }
            }
        ]
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理MCP工具请求
        
        设计思路：
        - 方法路由：根据MCP方法路由到具体处理器
        - 工具调用：处理tools/call请求
        - 工具列表：处理tools/list请求
        - 错误处理：统一的错误响应
        """
        try:
            if method == "tools/list":
                return {"tools": self.tools}
            
            elif method == "tools/call":
                tool_name = params["name"]
                arguments = params["arguments"]
                
                if tool_name == "crawl_agent":
                    return await self._crawl_agent(arguments)
                elif tool_name == "crawl_web":
                    return await self._crawl_web(arguments)
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")
            
            else:
                raise ValueError(f"Unknown method: {method}")
                
        except Exception as e:
            logger.error(f"Crawler MCP tool error: {e}")
            raise
    
    async def _crawl_agent(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行智能体爬取
        
        功能：
        - 参数提取：从MCP参数中提取爬取参数
        - 爬取执行：调用现有的爬取功能
        - 结果包装：将结果包装为标准格式
        """
        try:
            result = await self.crawler.run_crawler_demo(
                req_did=args["req_did"],
                resp_did=args["resp_did"],
                task_input=args["task_input"],
                initial_url=args["initial_url"],
                use_two_way_auth=args.get("use_two_way_auth", True),
                task_type=args.get("task_type", "function_query")
            )
            
            return {
                "success": True,
                "result": result,
                "tool": "crawl_agent"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": "crawl_agent"
            }
    
    async def _crawl_web(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行通用网页爬取
        
        功能：
        - HTTP请求：使用httpx执行HTTP请求
        - 方法支持：支持GET和POST方法
        - 头部处理：支持自定义HTTP头
        - 数据处理：支持POST数据
        """
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                if args.get("method", "GET") == "GET":
                    response = await client.get(
                        args["url"],
                        headers=args.get("headers", {})
                    )
                else:
                    response = await client.post(
                        args["url"],
                        headers=args.get("headers", {}),
                        json=args.get("data", {})
                    )
                
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "content": response.text,
                    "tool": "crawl_web"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "tool": "crawl_web"
            }

# MCP服务器启动脚本
async def start_crawler_mcp_server():
    """
    启动Crawler MCP服务器
    
    设计思路：
    - 标准输入输出：使用stdin/stdout进行MCP通信
    - 事件循环：持续监听和处理请求
    - 错误恢复：单个请求错误不影响整个服务器
    - 协议兼容：完全符合MCP协议规范
    """
    import sys
    
    crawler_tool = CrawlerMCPTool()
    
    while True:
        try:
            # 从标准输入读取请求
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request = json.loads(line.strip())
            
            try:
                # 处理MCP请求
                if request["method"] in ["tools/list", "tools/call"]:
                    result = await crawler_tool.handle_request(
                        request["method"], 
                        request.get("params", {})
                    )
                    response = {
                        "jsonrpc": "2.0",
                        "id": request["id"],
                        "result": result
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request["id"],
                        "error": {"code": -32601, "message": "Method not found"}
                    }
            
            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "error": {"code": -32603, "message": str(e)}
                }
            
            # 发送响应到标准输出
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"MCP server error: {e}")
            break

if __name__ == "__main__":
    asyncio.run(start_crawler_mcp_server())
```

### 3.3 LLM集成

#### 3.3.1 LLM工具管理器 (packages/framework/anp_open_sdk_framework/llm_integration/tool_manager.py)

**设计思路：**
- **工具注册**：管理暴露给LLM的工具
- **格式转换**：支持不同LLM提供商的工具格式
- **调用管理**：统一的LLM工具调用接口
- **权限控制**：工具调用的权限和批准机制

**功能安排：**
1. **工具注册**：注册和管理LLM可用工具
2. **格式转换**：转换为不同LLM提供商的格式
3. **调用执行**：执行LLM工具调用
4. **权限管理**：工具调用的批准和记录

```python
"""
LLM工具管理器

设计理念：
1. 工具抽象：将Agent能力抽象为LLM可用工具
2. 格式适配：支持不同LLM提供商的工具格式
3. 权限控制：细粒度的工具调用权限管理
4. 调用追踪：完整的工具调用历史记录
"""
from typing import Dict, List, Any, Optional, Callable
import json
import logging

logger = logging.getLogger(__name__)

class LLMToolManager:
    """
    LLM工具管理器 - 管理暴露给LLM的工具
    
    职责：
    - 工具注册和管理
    - LLM格式转换
    - 工具调用执行
    - 权限控制和审计
    """
    
    def __init__(self, agent):
        self.agent = agent
        self.llm_tools = {}  # tool_name -> tool_info
        self.approval_callbacks = {}  # tool_name -> approval_callback
    
    def register_llm_tool(self, func):
        """
        注册LLM工具
        
        设计思路：
        - 选择性注册：只注册标记为LLM可用的工具
        - 元数据提取：从函数元数据构建LLM工具描述
        - 格式转换：转换为OpenAI Function Calling格式
        - 工具索引：建立工具名称到函数的映射
        """
        if not hasattr(func, '_mcp_meta') or not func._mcp_meta.get('expose_to_llm'):
            return
        
        mcp_meta = func._mcp_meta
        capability_meta = func._capability_meta
        
        # 构建LLM工具描述（OpenAI Function Calling格式）
        tool_info = {
            "type": "function",
            "function": {
                "name": mcp_meta['llm_tool_name'],
                "description": capability_meta['description'],
                "parameters": capability_meta.get('input_schema', {})
            },
            "mcp_meta": mcp_meta,
            "func": func
        }
        
        self.llm_tools[mcp_meta['llm_tool_name']] = tool_info
        logger.info(f"📋 Registered LLM tool: {mcp_meta['llm_tool_name']}")
    
    def get_llm_tools_schema(self) -> List[Dict[str, Any]]:
        """
        获取LLM工具模式（OpenAI格式）
        
        功能：
        - 格式转换：转换为OpenAI Function Calling格式
        - 工具列表：返回所有可用工具的描述
        """
        return [tool["function"] for tool in self.llm_tools.values()]
    
    def get_llm_tools_schema_anthropic(self) -> List[Dict[str, Any]]:
        """
        获取LLM工具模式（Anthropic格式）
        
        功能：
        - 格式适配：转换为Anthropic工具格式
        - 兼容性：支持不同LLM提供商
        """
        anthropic_tools = []
        for tool in self.llm_tools.values():
            anthropic_tools.append({
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"]
            })
        return anthropic_tools
    
    async def call_llm_tool(self, tool_name: str, arguments: Dict[str, Any], 
                           llm_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        调用LLM工具
        
        设计思路：
        - 工具查找：根据名称查找工具
        - 上下文注入：添加LLM调用上下文
        - 错误处理：统一的错误处理和响应
        - 调用记录：记录工具调用历史
        """
        if tool_name not in self.llm_tools:
            raise ValueError(f"LLM tool not found: {tool_name}")
        
        tool_info = self.llm_tools[tool_name]
        func = tool_info["func"]
        
        # 添加LLM调用上下文
        arguments['_call_context'] = {
            'is_llm_call': True,
            'llm_context': llm_context or {},
            'agent_id': self.agent.id,
            'tool_name': tool_name
        }
        
        try:
            result = await func(**arguments)
            return result
        except Exception as e:
            logger.error(f"LLM tool call error: {e}")
            return {
                'success': False,
                'error': str(e),
                'tool': tool_name
            }
    
    def set_approval_callback(self, tool_name: str, callback: Callable):
        """
        设置工具批准回调
        
        功能：
        - 自定义批准：允许自定义批准逻辑
        - 工具级控制：每个工具可以有不同的批准机制
        """
        self.approval_callbacks[tool_name] = callback
```

## 4. 设计思路总结

### 4.1 核心设计理念

**1. 分层架构设计**
- **Core层职责**：提供最基础的DID服务、Agent路由、配置管理
- **Framework层职责**：提供高级功能如装饰器系统、MCP集成、LLM支持
- **分离原则**：Core可以独立使用，Framework依赖Core但提供增强功能

**2. 装饰器驱动开发**
- **声明式编程**：通过装饰器声明Agent能力，简化开发流程
- **元数据管理**：将功能信息存储为函数元数据，便于自动发现和注册
- **发布控制**：通过装饰器参数控制能力的发布方式和权限

**3. MCP生态集成**
- **标准化接口**：统一的MCP工具调用接口，隐藏协议复杂性
- **工具包装**：将现有功能包装为标准MCP工具
- **LLM友好**：原生支持LLM工具调用协议

**4. 配置驱动架构**
- **统一配置**：所有行为通过配置文件控制
- **类型安全**：使用Protocol定义配置类型
- **缓存优化**：配置查找的性能优化

### 4.2 关键技术决策

**1. 单例模式的使用**
- **RouteManager**：确保全局路由配置一致性
- **DIDFormatManager**：确保DID格式规则全局统一
- **设计考虑**：避免配置不一致，提高性能

**2. 异步优先设计**
- **全异步**：所有I/O操作都是异步的
- **性能考虑**：适合高并发场景
- **现代化**：符合现代Python开发最佳实践

**3. 错误处理策略**
- **统一格式**：标准化的错误响应格式
- **分层处理**：不同层次的错误处理机制
- **日志记录**：完整的错误日志和调试信息

**4. 权限控制设计**
- **分级权限**：普通调用和LLM调用的不同权限
- **交互式批准**：LLM工具调用的人工批准机制
- **审计追踪**：完整的工具调用历史记录

### 4.3 扩展性考虑

**1. 插件化架构**
- **存储层**：可插拔的存储实现
- **MCP工具**：标准化的工具接口
- **装饰器系统**：可扩展的装饰器类型

**2. 多LLM支持**
- **格式适配**：支持OpenAI和Anthropic格式
- **统一接口**：LLM无关的工具调用接口
- **扩展性**：易于添加新的LLM提供商支持

**3. 配置扩展**
- **模块化配置**：配置按功能模块组织
- **类型安全**：通过Protocol确保配置正确性
- **向后兼容**：配置格式的向后兼容性

### 4.4 开发体验优化

**1. 极简API设计**
- **装饰器驱动**：只需添加装饰器即可实现复杂功能
- **自动发现**：自动发现和注册Agent能力
- **零配置**：合理的默认配置，减少配置工作

**2. 调试友好**
- **详细日志**：完整的执行日志和错误信息
- **调试模式**：开发环境的特殊支持
- **错误追踪**：清晰的错误堆栈和上下文

**3. 文档和示例**
- **代码即文档**：通过装饰器参数提供文档
- **完整示例**：从简单到复杂的使用示例
- **迁移指南**：从现有代码的迁移路径

### 4.5 性能优化策略

**1. 缓存机制**
- **路由缓存**：避免重复的配置查找
- **工具注册表**：快速的工具查找
- **连接复用**：MCP连接的复用和管理

**2. 异步优化**
- **并发处理**：支持高并发的请求处理
- **非阻塞I/O**：所有I/O操作都是非阻塞的
- **资源管理**：合理的资源分配和回收

**3. 内存优化**
- **懒加载**：按需加载功能模块
- **对象复用**：单例模式减少对象创建
- **垃圾回收**：合理的对象生命周期管理

这个重构方案通过清晰的分层架构、装饰器驱动的开发模式、统一的MCP工具生态和原生的LLM支持，将ANP SDK从复杂的架构简化为开发者友好的框架，同时保持了强大的功能性和扩展性。每个组件都有明确的职责和设计理念，确保了代码的可维护性和可扩展性。
