ANP SDK 代码重构完整方案
基于前面的讨论，我制定了一个完整的重构方案，将复杂的架构简化为更清晰的分层结构。

1. 整体架构重新设计
1.1 新的目录结构


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
│       │   ├── /agent_manager          # Agent管理
│       │   └── enhanced_sdk.py         # 增强SDK
│       └── pyproject.toml
│
├── /examples                           # 示例项目
└── /configs                           # 配置文件
2. 核心SDK重构
2.1 更新 packages/core/anp_open_sdk/anp_sdk.py


```python
"""
核心SDK - 只保留基础DID服务和Agent路由能力
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
    """核心SDK - 最小可用的DID服务"""
    
    def __init__(self, storage=None, agents: List[LocalAgent] = None):
        self.storage = storage or LocalFileStorage()
        self.agents = {agent.id: agent for agent in (agents or [])}
        self.route_manager = RouteManager()
        self.did_manager = DIDFormatManager()
        self.app = self._create_app()
        self.server_running = False
        
        logger.info(f"🚀 ANP SDK initialized with {len(self.agents)} agents")
    
    def _create_app(self) -> FastAPI:
        """创建FastAPI应用"""
        config = get_global_config()
        
        app = FastAPI(
            title="ANP DID Service",
            description="ANP SDK Core DID Service",
            version="0.1.0",
            docs_url="/docs" if config.anp_sdk.debug_mode else None
        )
        
        # 注册核心路由
        app.include_router(router_did.router, prefix="")
        app.include_router(router_auth.router, prefix="")
        
        # 注册Agent API路由
        self._register_agent_routes(app)
        
        # 根路径
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
        """注册Agent API路由"""
        
        @app.get(self.route_manager.get_route("agent", "api"))
        @app.post(self.route_manager.get_route("agent", "api"))
        async def agent_api_handler(did: str, subpath: str, request: Request):
            """Agent API处理器"""
            try:
                # 标准化DID
                request_context = {
                    "host": request.url.hostname,
                    "port": request.url.port or 80,
                    "path": str(request.url.path)
                }
                normalized_did = self.did_manager.normalize_did(did, request_context)
                
                # 查找Agent
                if normalized_did not in self.agents:
                    return {"error": f"Agent not found: {normalized_did}", "status": 404}
                
                agent = self.agents[normalized_did]
                
                # 构造请求数据
                if request.method == "GET":
                    request_data = dict(request.query_params)
                else:
                    request_data = await request.json()
                
                request_data.update({
                    "type": "api_call",
                    "path": f"/{subpath}",
                    "method": request.method
                })
                
                # 调用Agent处理器
                result = await agent.handle_request("system", request_data, request)
                return result
                
            except Exception as e:
                logger.error(f"Agent API error: {e}")
                return {"error": str(e), "status": 500}
    
    def register_agent(self, agent: LocalAgent):
        """注册Agent"""
        self.agents[agent.id] = agent
        logger.info(f"✅ Registered agent: {agent.name} ({agent.id})")
    
    def get_agent(self, did: str) -> LocalAgent:
        """获取Agent"""
        return self.agents.get(did)
    
    def start_server(self, host: str = None, port: int = None):
        """启动服务器"""
        config = get_global_config()
        host = host or config.anp_sdk.host
        port = port or config.anp_sdk.port
        
        if config.anp_sdk.debug_mode:
            # Debug模式：阻塞运行
            uvicorn.run(self.app, host=host, port=port, reload=True)
        else:
            # 生产模式：后台线程
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
        """停止服务器"""
        if hasattr(self, 'uvicorn_server'):
            self.uvicorn_server.should_exit = True
        if hasattr(self, 'server_thread'):
            self.server_thread.join(timeout=5)
        self.server_running = False
        logger.info("🛑 Server stopped")

```

2.2 实现路由管理器


```python
# packages/core/anp_open_sdk/service/router/route_manager.py

from typing import Dict
from anp_open_sdk.config import get_global_config
import logging

logger = logging.getLogger(__name__)

class RouteManager:
    """统一路由管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        config = get_global_config()
        self.routes_config = config.anp_sdk.routes
        self._route_cache = {}
        self._initialized = True
        logger.info("📋 Route manager initialized")
    
    def get_route(self, category: str, name: str) -> str:
        """获取配置的路由路径"""
        cache_key = f"{category}.{name}"
        
        if cache_key in self._route_cache:
            return self._route_cache[cache_key]
        
        try:
            category_routes = getattr(self.routes_config, category)
            route = getattr(category_routes, name)
            self._route_cache[cache_key] = route
            return route
        except AttributeError:
            logger.error(f"Route not found: {cache_key}")
            raise ValueError(f"Route configuration not found: {cache_key}")
    
    def get_all_routes(self, category: str = None) -> Dict[str, str]:
        """获取所有路由"""
        if category:
            try:
                category_routes = getattr(self.routes_config, category)
                return {
                    name: getattr(category_routes, name)
                    for name in dir(category_routes)
                    if not name.startswith('_')
                }
            except AttributeError:
                return {}
        
        all_routes = {}
        for cat in ['wba', 'publisher', 'agent', 'api', 'websocket']:
            all_routes[cat] = self.get_all_routes(cat)
        return all_routes

```

2.3 实现DID格式管理器


```python

# packages/core/anp_open_sdk/service/router/did_format_manager.py

import re
import urllib.parse
import secrets
from typing import Dict, Optional, Tuple
from anp_open_sdk.config import get_global_config
import logging

logger = logging.getLogger(__name__)

class DIDFormatManager:
    """DID格式管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        config = get_global_config()
        self.did_config = config.anp_sdk.did_format
        self._initialized = True
        logger.info("🔧 DID format manager initialized")
    
    def create_did(self, host: str, port: int, user_type: str = "user",
                   dir: str = None, unique_id: str = None) -> str:
        """创建标准格式的DID"""
        dir = dir or self.did_config.default_dir
        unique_id = unique_id or secrets.token_hex(8)
        
        if user_type not in self.did_config.user_types:
            raise ValueError(f"Invalid user type: {user_type}")
        
        # 处理端口编码
        if port not in self.did_config.default_ports:
            host_port = f"{host}{self.did_config.port_encoding}{port}"
        else:
            host_port = host
        
        segments = [
            "did",
            self.did_config.method,
            host_port,
            urllib.parse.quote(dir, safe=''),
            user_type,
            unique_id
        ]
        
        return ':'.join(segments)
    
    def parse_did(self, did_or_id: str) -> Dict[str, Optional[str]]:
        """解析DID或unique_id"""
        did_or_id = urllib.parse.unquote(did_or_id)
        
        # 检查是否是16位unique_id
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
            pattern = rf"did:{self.did_config.method}:([^:]+?)(?:%3A|:)?(\d*)?:([^:]+):([^:]+):([a-f0-9]{{16}})"
            match = re.match(pattern, did_or_id)
            
            if match:
                host = match.group(1)
                port = match.group(2) or "80"
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
        """标准化DID格式"""
        parsed = self.parse_did(did_or_id)
        
        if parsed["format"] == "full_did":
            return parsed["full_did"]
        
        if parsed["format"] == "unique_id" and request_context:
            host = request_context.get("host", "localhost")
            port = request_context.get("port", 80)
            
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
        
        return did_or_id
    
    def create_method_identifier(self, did: str, method_name: str) -> str:
        """创建本地方法标识符"""
        return f"{did}::{method_name}"
    
    def parse_method_identifier(self, method_id: str) -> Tuple[Optional[str], Optional[str]]:
        """解析方法标识符"""
        if "::" not in method_id:
            return None, None
        parts = method_id.split("::", 1)
        return parts[0], parts[1]

```

3. Framework层重构
3.1 装饰器系统


```python
# packages/framework/anp_open_sdk_framework/decorators/capability.py

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
    """
    def decorator(func: Callable):
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

3.2 MCP集成装饰器


```python

# packages/framework/anp_open_sdk_framework/decorators/mcp_integration.py

from typing import Dict, Any, List, Optional, Callable
from functools import wraps
from .capability import capability
import logging

logger = logging.getLogger(__name__)

def mcp_tool(tool_name: str, 
             server_name: str = "default",
             description: str = None,
             tags: List[str] = None,
             publish_as: str = "local_method"):
    """
    MCP工具装饰器 - 自动调用MCP工具
    """
    def decorator(func: Callable):
        auto_description = description or f"MCP工具: {tool_name} (来自 {server_name})"
        auto_tags = (tags or []) + ["mcp", server_name, "tool"]
        
        # 添加MCP元数据
        func._mcp_meta = {
            'tool_name': tool_name,
            'server_name': server_name,
            'is_mcp_tool': True
        }
        
        # 创建MCP调用包装器
        async def mcp_wrapper(**kwargs):
            try:
                # 获取MCP客户端（从全局注册表或Agent实例）
                mcp_client = _get_mcp_client(server_name)
                if not mcp_client:
                    raise Exception(f"MCP server {server_name} not connected")
                
                # 调用MCP工具
                result = await mcp_client.call_tool(tool_name, kwargs)
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
    """
    def decorator(cls):
        cls._mcp_servers = servers
        return cls
    return decorator

# 全局MCP客户端注册表
_mcp_clients = {}

def _get_mcp_client(server_name: str):
    """获取MCP客户端"""
    return _mcp_clients.get(server_name)

def _register_mcp_client(server_name: str, client):
    """注册MCP客户端"""
    _mcp_clients[server_name] = client

```

3.3 简化的MCP客户端


```python

# packages/framework/anp_open_sdk_framework/mcp_tools/mcp_client.py

import asyncio
import json
import subprocess
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class SimpleMCPClient:
    """简化的MCP客户端"""
    
    def __init__(self, server_name: str):
        self.server_name = server_name
        self.process = None
        self.tools = {}
        self.connected = False
    
    async def connect(self, command: List[str], env: Dict[str, str] = None):
        """连接MCP服务器"""
        try:
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
        """调用MCP工具"""
        if not self.connected:
            raise Exception(f"MCP server {self.server_name} not connected")
        
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
        """初始化MCP连接"""
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
        """发现可用工具"""
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
        """发送请求并接收响应"""
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json.encode())
        await self.process.stdin.drain()
        
        response_line = await self.process.stdout.readline()
        return json.loads(response_line.decode())
    
    async def close(self):
        """关闭连接"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
        self.connected = False
        logger.info(f"🔌 Disconnected MCP server: {self.server_name}")

```

3.4 Crawler作为MCP工具


```python

# packages/framework/anp_open_sdk_framework/mcp_tools/crawler_tool.py

import asyncio
import json
from typing import Dict, Any
from anp_open_sdk.service.interaction.anp_tool import ANPToolCrawler
import logging

logger = logging.getLogger(__name__)

class CrawlerMCPTool:
    """将Crawler封装为MCP工具"""
    
    def __init__(self):
        self.crawler = ANPToolCrawler()
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
        """处理MCP工具请求"""
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
        """执行智能体爬取"""
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
        """执行通用网页爬取"""
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
    """启动Crawler MCP服务器"""
    import sys
    
    crawler_tool = CrawlerMCPTool()
    
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request = json.loads(line.strip())
            
            try:
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
            
            print(json.dumps(response))
            sys.stdout.flush()
            
        except Exception as e:
            logger.error(f"MCP server error: {e}")
            break

if __name__ == "__main__":
    asyncio.run(start_crawler_mcp_server())

```

3.5 能力自动发现和发布


```python
# packages/framework/anp_open_sdk_framework/capability_manager/discovery.py

import importlib
import inspect
from typing import List, Dict, Any
from anp_open_sdk.service.router.did_format_manager import DIDFormatManager
from ..mcp_tools.mcp_client import SimpleMCPClient
from ..decorators.mcp_integration import _register_mcp_client
import logging

logger = logging.getLogger(__name__)

class CapabilityDiscovery:
    """能力自动发现和注册"""
    
    def __init__(self, agent):
        self.agent = agent
        self.did_manager = DIDFormatManager()
        self.mcp_clients = {}
    
    async def discover_and_register_from_module(self, module_name: str):
        """从模块发现并注册所有能力"""
        try:
            module = importlib.import_module(module_name)
            
            # 检查是否有MCP服务器配置
            if hasattr(module, '_mcp_servers') or hasattr(self.agent.__class__, '_mcp_servers'):
                await self._setup_mcp_servers(getattr(module, '_mcp_servers', None) or 
                                            getattr(self.agent.__class__, '_mcp_servers', {}))
            
            # 发现能力
            capabilities = []
            api_endpoints = []
            
            for name, obj in inspect.getmembers(module):
                if hasattr(obj, '_capability_meta'):
                    capabilities.append(obj)
                elif hasattr(obj, '_api_meta'):
                    api_endpoints.append(obj)
            
            # 注册能力
            for func in capabilities:
                await self._register_capability(func)
            
            # 注册API端点
            for func in api_endpoints:
                self._register_api_endpoint(func)
            
            logger.info(f"🎯 Discovered {len(capabilities)} capabilities and {len(api_endpoints)} API endpoints from {module_name}")
            
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {e}")
    
    async def _setup_mcp_servers(self, servers_config: Dict[str, Dict[str, Any]]):
        """设置MCP服务器"""
        for server_name, config in servers_config.items():
            try:
                client = SimpleMCPClient(server_name)
                success = await client.connect(
                    command=config['command'],
                    env=config.get('env', {})
                )
                
                if success:
                    self.mcp_clients[server_name] = client
                    _register_mcp_client(server_name, client)
                    logger.info(f"✅ MCP server connected: {server_name}")
                
            except Exception as e:
                logger.error(f"❌ Failed to connect MCP server {server_name}: {e}")
    
    async def _register_capability(self, func):
        """注册能力函数"""
        meta = func._capability_meta
        
        # 注册为本地方法
        if meta['publish_as'] in ['local_method', 'both']:
            self._register_as_local_method(meta['name'], func, meta)
        
        # 注册为对外API
        if meta['publish_as'] in ['expose_api', 'both']:
            self._register_as_api(meta['name'], func, meta)
    
    def _register_as_local_method(self, name: str, func, meta: Dict):
        """注册为本地方法"""
        if not hasattr(self.agent, '_local_methods'):
            self.agent._local_methods = {}
        
        method_key = self.did_manager.create_method_identifier(self.agent.id, name)
        
        self.agent._local_methods[method_key] = {
            'name': name,
            'description': meta['description'],
            'tags': meta['tags'],
            'input_schema': meta['input_schema'],
            'output_schema': meta['output_schema'],
            'func': func,
            'agent_did': self.agent.id,
            'agent_name': self.agent.name
        }
        
        setattr(self.agent, name, func)
        logger.debug(f"  📋 Registered local method: {name}")
    
    def _register_as_api(self, name: str, func, meta: Dict):
        """注册为对外API"""
        api_path = f"/{name}"
        self.agent.expose_api(api_path, func, methods=["POST"])
        logger.debug(f"  🌐 Registered API endpoint: {api_path}")
    
    def _register_api_endpoint(self, func):
        """注册API端点"""
        api_meta = func._api_meta
        self.agent.expose_api(api_meta['path'], func, methods=api_meta['methods'])
        logger.debug(f"  🌐 Registered API endpoint: {api_meta['path']}")
    
    async def cleanup(self):
        """清理MCP连接"""
        for client in self.mcp_clients.values():
            await client.close()

```

3.6 增强SDK


```python

# packages/framework/anp_open_sdk_framework/enhanced_sdk.py

from anp_open_sdk import ANPSDK
from anp_open_sdk.agents.local_agent import LocalAgent
from .capability_manager.discovery import CapabilityDiscovery
from typing import List
import logging

logger = logging.getLogger(__name__)

class EnhancedANPSDK(ANPSDK):
    """增强SDK - 包含Framework功能"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.capability_managers = {}  # agent_id -> CapabilityDiscovery
        logger.info("🚀 Enhanced ANP SDK initialized")
    
    def register_agent(self, agent: LocalAgent):
        """注册Agent并设置能力发现"""
        super().register_agent(agent)
        
        # 为每个Agent创建能力发现管理器
        discovery = CapabilityDiscovery(agent)
        self.capability_managers[agent.id] = discovery
    
    async def auto_discover_capabilities(self, agent_id: str, module_name: str):
        """自动发现Agent的能力"""
        if agent_id in self.capability_managers:
            await self.capability_managers[agent_id].discover_and_register_from_module(module_name)
    
    async def cleanup_agents(self):
        """清理所有Agent"""
        for discovery in self.capability_managers.values():
            await discovery.cleanup()

```

4. 配置文件更新
4.1 更新 
unified_config.default.yaml


```python
# ANP SDK 统一配置文件
anp_sdk:
  debug_mode: true
  host: localhost
  port: 9527
  
  # DID 格式配置
  did_format:
    method: "wba"
    port_encoding: "%3A"
    default_ports: [80, 443]
    user_types: ["user", "hostuser", "service", "agent"]
    default_dir: "wba"
  
  # 路由配置
  routes:
    # 基础路径
    base_paths:
      wba: "/wba"
      agent: "/agent"
      publisher: "/publisher"
      api: "/api"
      ws: "/ws"
    
    # WBA 路由
    wba:
      auth: "/wba/adapter_auth"
      user_did: "/wba/user/{user_id}/did.json"
      user_ad: "/wba/user/{user_id}/ad.json"
      user_yaml: "/wba/user/{resp_did}/{file_name}.yaml"
      user_json: "/wba/user/{resp_did}/{file_name}.json"
      hostuser_did: "/wba/hostuser/{user_id}/did.json"
      hostuser_ad: "/wba/hostuser/{user_id}/ad.json"
    
    # 发布者路由
    publisher:
      agents: "/publisher/agents"
    
    # Agent API 路由
    agent:
      api: "/agent/api/{did}/{subpath:path}"
      message_post: "/agent/message/{did}/post"
      group_join: "/agent/group/{did}/{group_id}/join"
      group_leave: "/agent/group/{did}/{group_id}/leave"
      group_message: "/agent/group/{did}/{group_id}/message"
      group_connect: "/agent/group/{did}/{group_id}/connect"
      group_members: "/agent/group/{did}/{group_id}/members"
      groups: "/agent/groups"
      # Local methods 路由
      method_call: "/agent/method/{agent_id}/{method_name}"
      method_doc: "/agent/method/{agent_id}/_doc"
      methods_list: "/agent/methods"
      methods_search: "/agent/methods/search"
    
    # 通用 API 路由
    api:
      root: "/"
      message: "/api/message"
    
    # WebSocket 路由
    websocket:
      message: "/ws/message"
      agent: "/ws/agent"

```

4.2 更新配置类型


```python
# packages/core/anp_open_sdk/config/config_types.py

from typing import Protocol, List, Dict, Any

class DIDFormatConfig(Protocol):
    method: str
    port_encoding: str
    default_ports: List[int]
    user_types: List[str]
    default_dir: str

class RoutePathsConfig(Protocol):
    wba: str
    agent: str
    publisher: str
    api: str
    ws: str

class WBARoutesConfig(Protocol):
    auth: str
    user_did: str
    user_ad: str
    user_yaml: str
    user_json: str
    hostuser_did: str
    hostuser_ad: str

class AgentRoutesConfig(Protocol):
    api: str
    message_post: str
    group_join: str
    group_leave: str
    group_message: str
    group_connect: str
    group_members: str
    groups: str
    method_call: str
    method_doc: str
    methods_list: str
    methods_search: str

class RoutesConfig(Protocol):
    base_paths: RoutePathsConfig
    wba: WBARoutesConfig
    agent: AgentRoutesConfig
    # ... 其他路由配置

class AnpSdkConfig(Protocol):
    debug_mode: bool
    host: str
    port: int
    did_format: DIDFormatConfig
    routes: RoutesConfig
    # ... 其他现有配置


```


5. 使用示例
5.1 Agent实现示例


```python
# examples/my_agent/agent_functions.py

from anp_open_sdk_framework.decorators import capability, mcp_tool, expose_api, mcp_server_config
import httpx
import sqlite3

# 配置MCP服务器
@mcp_server_config({
    "filesystem": {
        "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        "env": {}
    },
    "brave_search": {
        "command": ["npx", "-y", "@modelcontextprotocol/server-brave-search"],
        "env": {"BRAVE_API_KEY": "your-api-key"}
    },
    "crawler": {
        "command": ["python", "-m", "anp_open_sdk_framework.mcp_tools.crawler_tool"],
        "env": {}
    }
})
class MyAgentFunctions:
    pass

# 普通能力 - 同时发布为本地方法和API
@capability(
    name="get_weather",
    description="获取指定城市的天气信息",
    input_schema={
        "type": "object",
        "properties": {
            "city": {"type": "string"},
            "units": {"type": "string", "enum": ["celsius", "fahrenheit"]}
        },
        "required": ["city"]
    },
    tags=["weather", "api", "external"],
    publish_as="both"
)
async def get_weather(city: str, units: str = "celsius"):
    """获取天气信息"""
    # 实际实现
    async with httpx.AsyncClient() as client:
        # ... API调用逻辑
        return {"temperature": 25, "description": "晴天"}

# 数据库查询 - 只作为本地方法
@capability(
    name="query_database",
    description="查询本地数据库",
    tags=["database", "internal"],
    publish_as="local_method"
)
async def query_database(sql: str, params: list = None):
    """数据库查询"""
    # 实际实现
    return {"rows": [], "count": 0}

# MCP工具集成 - 文件操作
@mcp_tool("read_file", "filesystem", "读取文件内容")
async def read_file_mcp(file_path: str):
    """通过MCP读取文件"""
    pass  # 实现在装饰器中

# MCP工具集成 - 网络搜索
@mcp_tool("search_web", "brave_search", "网络搜索")
async def search_web_mcp(query: str, count: int = 10):
    """通过MCP进行网络搜索"""
    pass

# MCP工具集成 - 智能体爬取
@mcp_tool("crawl_agent", "crawler", "爬取智能体信息")
async def crawl_agent_mcp(req_did: str, resp_did: str, task_input: str, initial_url: str):
    """通过MCP进行智能体爬取"""
    pass

# 直接API暴露
@expose_api("/custom/endpoint", ["GET", "POST"])
async def custom_endpoint(request_data, request):
    """自定义API端点"""
    return {"message": "Custom endpoint response"}

# 组合能力 - 复杂业务逻辑
@capability(
    name="weather_report",
    description="生成天气报告并发送",
    publish_as="expose_api"
)
async def weather_report(city: str, email: str):
    """生成天气报告"""
    # 1. 获取天气
    weather = await get_weather(city)
    
    # 2. 生成报告
    report = f"城市: {city}, 天气: {weather['description']}, 温度: {weather['temperature']}°C"
    
    # 3. 保存到文件 (使用MCP)
    await read_file_mcp(f"/tmp/weather_report_{city}.txt")
    
    return {"report": report, "status": "sent"}

```

5.2 Agent初始化


```python

# examples/my_agent/agent_handlers.py

from anp_open_sdk_framework.enhanced_sdk import EnhancedANPSDK
from anp_open_sdk_framework.capability_manager.discovery import CapabilityDiscovery

async def initialize_agent(agent, sdk):
    """初始化Agent"""
    
    # 创建能力发现管理器
    discovery = CapabilityDiscovery(agent)
    
    # 自动发现并注册能力
    await discovery.discover_and_register_from_module(
        f"{__name__.replace('.agent_handlers', '')}.agent_functions"
    )
    
    logger.info(f"🎯 Agent {agent.name} initialized with auto-discovered capabilities")

async def cleanup_agent():
    """清理Agent"""
    # 清理逻辑
    pass

```


5.3 完整使用示例


```python
# examples/demo_usage.py

import asyncio
from anp_open_sdk_framework.enhanced_sdk import EnhancedANPSDK
from anp_open_sdk.agents.local_agent import LocalAgent

async def main():
    # 创建增强SDK
    sdk = EnhancedANPSDK()
    
    # 创建Agent
    agent = LocalAgent.from_did("did:wba:localhost%3A9527:wba:user:1234567890abcdef")
    agent.name = "MyAgent"
    
    # 注册Agent
    sdk.register_agent(agent)
    
    # 自动发现能力
    await sdk.auto_discover_capabilities(
        agent.id, 
        "examples.my_agent.agent_functions"
    )
    
    # 启动服务器
    sdk.start_server()
    
    print("🔥 Server running with enhanced capabilities!")
    print("📋 Available capabilities:")
    
    # 列出所有本地方法
    if hasattr(agent, '_local_methods'):
        for method_key, method_info in agent._local_methods.items():
            print(f"  - {method_info['name']}: {method_info['description']}")
    
    # 保持运行
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Shutting down...")
        await sdk.cleanup_agents()
        sdk.stop_server()

if __name__ == "__main__":
    asyncio.run(main())

```

6. 总结
这个重构方案实现了：

✅ 简化的架构
去掉了复杂的资源适配器层
使用装饰器直接标记函数功能
保持了核心SDK的精简
✅ 完整的路由配置
实现了 @did_format_route_cfg.md 中的所有要求
统一的DID格式管理
可配置的路由系统
✅ 灵活的能力发布
支持本地方法、对外API、同时发布三种模式
自动发现和注册机制
统一的身份标识体系
✅ MCP集成
简化的MCP客户端
装饰器式的MCP工具集成
Crawler封装为MCP工具
✅ 保持简单
开发者只需要用装饰器标记函数
自动处理注册、路由、身份标识
清晰的分层和职责划分
这个方案既满足了功能完整性，又保持了使用的简洁性，是一个平衡的重构方案。






mcp_client做什么用

@mcp_tool("crawl_agent", "crawler", "爬取智能体信息") 这个装饰器做什么用

好问题！让我详细解释这两个概念的作用和关系。

1. MCP Client 的作用
什么是 MCP Client？
MCP Client 是连接和调用 MCP 服务器的客户端。它的作用是：



```python

# MCP Client 的核心功能
class SimpleMCPClient:
    """MCP客户端 - 连接外部MCP服务器"""
    
    async def connect(self, command, env):
        """启动并连接到MCP服务器进程"""
        # 启动外部MCP服务器进程
        self.process = await asyncio.create_subprocess_exec(*command)
        
    async def call_tool(self, tool_name, arguments):
        """调用MCP服务器上的工具"""
        # 发送JSON-RPC请求到MCP服务器
        request = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }
        # 返回MCP服务器的响应

```

MCP Client 的具体用途
连接外部工具服务器


```python

# 例如连接文件系统MCP服务器
npx -y @modelcontextprotocol/server-filesystem /tmp

# 或连接搜索MCP服务器  
npx -y @modelcontextprotocol/server-brave-search

```

调用远程工具



```python
# 通过MCP Client调用文件系统工具
result = await mcp_client.call_tool("read_file", {"path": "/tmp/test.txt"})

# 通过MCP Client调用搜索工具
result = await mcp_client.call_tool("search_web", {"query": "ANP protocol"})

```

管理工具生命周期



```python
# 发现可用工具
tools = await mcp_client.discover_tools()

# 关闭连接
await mcp_client.close()

```


2. @mcp_tool 装饰器的作用
装饰器的核心功能
@mcp_tool 装饰器是一个自动化包装器，它的作用是：



```python
@mcp_tool("crawl_agent", "crawler", "爬取智能体信息")
async def crawl_agent_mcp(req_did: str, resp_did: str, task_input: str, initial_url: str):
    """通过MCP进行智能体爬取"""
    pass  # 这里不需要写实现代码！

```


装饰器自动做了什么？
自动连接MCP服务器



```python

# 装饰器内部会：
# 1. 查找名为 "crawler" 的MCP服务器
# 2. 如果没连接，自动连接
mcp_client = _get_mcp_client("crawler")

```

自动调用MCP工具



```python

# 装饰器内部会：
async def mcp_wrapper(**kwargs):
    # 自动调用MCP工具 "crawl_agent"
    result = await mcp_client.call_tool("crawl_agent", kwargs)
    return result

```

自动注册为Agent能力



```python

# 装饰器还会：
# 1. 将函数注册为Agent的本地方法
# 2. 生成标准的能力元数据
# 3. 支持通过Agent的本地方法系统调用
3. 完整的工作流程示例
步骤1：启动MCP服务器

Apply
# 在Agent初始化时，自动启动MCP服务器
mcp_servers = {
    "crawler": {
        "command": ["python", "-m", "anp_open_sdk_framework.mcp_tools.crawler_tool"],
        "env": {}
    },
    "filesystem": {
        "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
        "env": {}
    }
}

# MCP Client 会启动这些外部进程


```

步骤2：装饰器自动包装


```python

# 开发者只需要写这个
@mcp_tool("crawl_agent", "crawler", "爬取智能体信息")
async def crawl_agent_mcp(req_did: str, resp_did: str, task_input: str, initial_url: str):
    pass

# 装饰器自动生成这个实现：
async def crawl_agent_mcp(req_did: str, resp_did: str, task_input: str, initial_url: str):
    mcp_client = _get_mcp_client("crawler")  # 获取crawler服务器的客户端
    result = await mcp_client.call_tool("crawl_agent", {
        "req_did": req_did,
        "resp_did": resp_did, 
        "task_input": task_input,
        "initial_url": initial_url
    })
    return result
```

步骤3：实际调用流程


```python

# 用户调用
result = await agent.crawl_agent_mcp(
    req_did="did:wba:localhost:user:123",
    resp_did="did:wba:localhost:user:456", 
    task_input="计算两个数的和",
    initial_url="http://localhost:9527/agent/api/did:wba:localhost:user:456/ad.json"
)

# 实际执行流程：
# 1. 调用装饰器包装的函数
# 2. 装饰器获取 "crawler" MCP客户端
# 3. MCP客户端发送JSON-RPC请求到crawler服务器进程
# 4. crawler服务器执行实际的爬取逻辑
# 5. 返回结果给装饰器
# 6. 装饰器返回结果给用户

```

4. 为什么要这样设计？
优势1：解耦和模块化


```python

# 不用MCP的方式（紧耦合）
async def crawl_agent_direct(req_did, resp_did, task_input, initial_url):
    # 直接在这里写爬取逻辑
    crawler = ANPToolCrawler()
    return await crawler.run_crawler_demo(...)

# 用MCP的方式（松耦合）
@mcp_tool("crawl_agent", "crawler")
async def crawl_agent_mcp(req_did, resp_did, task_input, initial_url):
    pass  # 爬取逻辑在独立的MCP服务器中

```

优势2：工具复用


```python
# 同一个MCP工具可以被多个Agent使用
@mcp_tool("crawl_agent", "crawler")  # Agent A 使用
async def agent_a_crawl(...): pass

@mcp_tool("crawl_agent", "crawler")  # Agent B 也使用同一个工具
async def agent_b_crawl(...): pass

```

优势3：语言无关


```python
# MCP服务器可以用任何语言实现
# Python Agent 可以调用 Node.js 实现的MCP工具
@mcp_tool("search_web", "brave_search")  # Node.js实现的搜索工具
async def search_web_mcp(query: str): pass

```


优势4：标准化接口


```python

# 所有MCP工具都遵循相同的调用模式
@mcp_tool("tool_name", "server_name", "description")
async def any_tool(...): pass

# 自动获得：
# - 统一的错误处理
# - 标准的参数验证  
# - 一致的日志记录
# - 自动的能力注册

```

5. 实际使用对比
传统方式（复杂）


```python

# 需要手动管理连接、调用、错误处理
class MyAgent:
    def __init__(self):
        self.crawler = ANPToolCrawler()
        self.mcp_client = MCPClient()
    
    async def initialize(self):
        await self.mcp_client.connect("crawler", ["python", "crawler_server.py"])
    
    async def crawl_agent(self, req_did, resp_did, task_input, initial_url):
        try:
            result = await self.mcp_client.call_tool("crawl_agent", {
                "req_did": req_did,
                "resp_did": resp_did,
                "task_input": task_input, 
                "initial_url": initial_url
            })
            return result
        except Exception as e:
            # 手动错误处理
            return {"error": str(e)}

```

MCP装饰器方式（简单）


```python
# 一个装饰器搞定一切
@mcp_tool("crawl_agent", "crawler", "爬取智能体信息")
async def crawl_agent_mcp(req_did: str, resp_did: str, task_input: str, initial_url: str):
    pass  # 就这么简单！

# 自动获得：
# - MCP连接管理
# - 工具调用
# - 错误处理
# - 能力注册
# - 文档生成

```

总结
MCP Client：负责与外部MCP服务器通信的底层客户端
@mcp_tool装饰器：自动化包装器，让开发者无需关心MCP的复杂性
核心价值：将复杂的工具集成简化为一个装饰器，实现工具的标准化、模块化和复用
这样设计让开发者可以专注于业务逻辑，而不用担心工具集成的技术细节。






但是mcp_tool还可以暴露给llm用啊 现在的设计 怎么实现这个呢

非常好的观点！你说得对，MCP工具的一个重要价值就是可以暴露给LLM使用。现在的设计确实需要扩展来支持这个功能。

当前设计的局限性
现在的 @mcp_tool 装饰器只是将MCP工具包装为Agent的本地方法，但没有考虑：

LLM工具调用接口 - LLM需要标准的工具描述格式
工具发现机制 - LLM需要能发现可用的工具
权限控制 - 不是所有工具都应该暴露给LLM
调用上下文 - LLM调用和Agent调用的上下文不同
扩展设计方案
1. 增强的MCP工具装饰器


```python
# packages/framework/anp_open_sdk_framework/decorators/mcp_integration.py

def mcp_tool(tool_name: str, 
             server_name: str = "default",
             description: str = None,
             tags: List[str] = None,
             publish_as: str = "local_method",
             expose_to_llm: bool = False,  # 新增：是否暴露给LLM
             llm_tool_name: str = None,    # 新增：LLM中的工具名
             require_approval: bool = False): # 新增：是否需要人工批准
    """
    增强的MCP工具装饰器 - 支持LLM工具调用
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

```


# 专门用于LLM的装饰器

```python

def llm_mcp_tool(tool_name: str, 
                 server_name: str = "default",
                 description: str = None,
                 require_approval: bool = False):
    """
    专门暴露给LLM的MCP工具装饰器
    """
    return mcp_tool(
        tool_name=tool_name,
        server_name=server_name, 
        description=description,
        publish_as="local_method",
        expose_to_llm=True,
        require_approval=require_approval
    )

```

2. LLM工具管理器


```python
# packages/framework/anp_open_sdk_framework/llm_integration/tool_manager.py

from typing import Dict, List, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class LLMToolManager:
    """LLM工具管理器 - 管理暴露给LLM的工具"""
    
    def __init__(self, agent):
        self.agent = agent
        self.llm_tools = {}  # tool_name -> tool_info
        self.approval_callbacks = {}  # tool_name -> approval_callback
    
    def register_llm_tool(self, func):
        """注册LLM工具"""
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
        """获取LLM工具模式（OpenAI格式）"""
        return [tool["function"] for tool in self.llm_tools.values()]
    
    def get_llm_tools_schema_anthropic(self) -> List[Dict[str, Any]]:
        """获取LLM工具模式（Anthropic格式）"""
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
        """调用LLM工具"""
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
        """设置工具批准回调"""
        self.approval_callbacks[tool_name] = callback

```

# 全局批准请求函数
```python
async def _request_approval(tool_name: str, arguments: Dict[str, Any], 
                          call_context: Dict[str, Any]) -> bool:
    """请求用户批准工具调用"""
    # 这里可以实现各种批准机制：
    # 1. 命令行交互
    # 2. Web界面
    # 3. 消息通知
    # 4. 预设规则
    
    print(f"\n🤖 LLM请求调用工具: {tool_name}")
    print(f"📋 参数: {json.dumps(arguments, indent=2, ensure_ascii=False)}")
    print(f"🔍 上下文: {call_context.get('llm_context', {})}")
    
    # 简单的命令行批准（实际应用中可以更复杂）
    try:
        response = input("是否批准此工具调用？(y/n): ").strip().lower()
        return response in ['y', 'yes', '是', '批准']
    except:
        return False

async def _log_llm_tool_call(tool_name: str, arguments: Dict[str, Any], 
                           result: Dict[str, Any], call_context: Dict[str, Any]):
    """记录LLM工具调用"""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'tool_name': tool_name,
        'arguments': arguments,
        'result': result,
        'context': call_context
    }
    
    # 可以保存到文件、数据库或发送到监控系统
    logger.info(f"LLM工具调用记录: {json.dumps(log_entry, ensure_ascii=False)}")

```
    

3. LLM集成示例


```python
# packages/framework/anp_open_sdk_framework/llm_integration/llm_agent.py

import openai
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class LLMAgent:
    """集成LLM的智能体"""
    
    def __init__(self, agent, llm_client=None):
        self.agent = agent
        self.llm_client = llm_client or openai.AsyncOpenAI()
        self.tool_manager = LLMToolManager(agent)
        self.conversation_history = []
    
    def register_tools_from_agent(self):
        """从Agent注册LLM工具"""
        if hasattr(self.agent, '_local_methods'):
            for method_key, method_info in self.agent._local_methods.items():
                func = method_info.get('func')
                if func and hasattr(func, '_mcp_meta'):
                    self.tool_manager.register_llm_tool(func)
    
    async def chat(self, message: str, system_prompt: str = None) -> str:
        """与LLM对话，支持工具调用"""
        
        # 构建消息
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史对话
        messages.extend(self.conversation_history)
        messages.append({"role": "user", "content": message})
        
        # 获取可用工具
        tools = self.tool_manager.get_llm_tools_schema()
        
        try:
            # 调用LLM
            response = await self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )
            
            assistant_message = response.choices[0].message
            
            # 处理工具调用
            if assistant_message.tool_calls:
                # 添加助手消息到历史
                messages.append(assistant_message)
                
                # 执行工具调用
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    arguments = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"🤖 LLM调用工具: {tool_name}")
                    
                    # 执行工具
                    tool_result = await self.tool_manager.call_llm_tool(
                        tool_name, 
                        arguments,
                        llm_context={
                            'conversation_id': id(self.conversation_history),
                            'user_message': message
                        }
                    )
                    
                    # 添加工具结果到消息
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_result, ensure_ascii=False)
                    })
                
                # 再次调用LLM获取最终回复
                final_response = await self.llm_client.chat.completions.create(
                    model="gpt-4",
                    messages=messages
                )
                
                final_content = final_response.choices[0].message.content
            else:
                final_content = assistant_message.content
            
            # 更新对话历史
            self.conversation_history.append({"role": "user", "content": message})
            self.conversation_history.append({"role": "assistant", "content": final_content})
            
            # 保持历史长度
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]
            
            return final_content
            
        except Exception as e:
            logger.error(f"LLM chat error: {e}")
            return f"抱歉，处理您的请求时出现错误: {str(e)}"

```

4. 使用示例


```python
# examples/llm_agent/agent_functions.py

from anp_open_sdk_framework.decorators import llm_mcp_tool, mcp_tool

# 暴露给LLM的工具（需要批准）
@llm_mcp_tool("read_file", "filesystem", "读取文件内容", require_approval=True)
async def read_file_for_llm(file_path: str):
    """LLM可以调用的文件读取工具"""
    pass

# 暴露给LLM的工具（无需批准）
@llm_mcp_tool("search_web", "brave_search", "网络搜索")
async def search_web_for_llm(query: str, count: int = 5):
    """LLM可以调用的网络搜索工具"""
    pass

# 暴露给LLM的爬虫工具（需要批准）
@llm_mcp_tool("crawl_agent", "crawler", "爬取智能体信息", require_approval=True)
async def crawl_agent_for_llm(req_did: str, resp_did: str, task_input: str, initial_url: str):
    """LLM可以调用的智能体爬取工具"""
    pass

# 只给Agent用的工具（不暴露给LLM）
@mcp_tool("write_file", "filesystem", "写入文件", expose_to_llm=False)
async def write_file_internal(file_path: str, content: str):
    """只有Agent内部可以使用的文件写入工具"""
    pass
    

```

5. Agent初始化和使用


```python
# examples/llm_agent/agent_handlers.py

from anp_open_sdk_framework.llm_integration.llm_agent import LLMAgent
from anp_open_sdk_framework.capability_manager.discovery import CapabilityDiscovery

llm_agent = None

async def initialize_agent(agent, sdk):
    """初始化支持LLM的Agent"""
    global llm_agent
    
    # 常规能力发现
    discovery = CapabilityDiscovery(agent)
    await discovery.discover_and_register_from_module(
        f"{__name__.replace('.agent_handlers', '')}.agent_functions"
    )
    
    # 创建LLM Agent
    llm_agent = LLMAgent(agent)
    llm_agent.register_tools_from_agent()
    
    # 暴露LLM聊天接口
    @agent.expose_api("/chat", ["POST"])
    async def chat_endpoint(request_data, request):
        message = request_data.get('message', '')
        system_prompt = request_data.get('system_prompt', '你是一个有用的AI助手，可以使用各种工具来帮助用户。')
        
        response = await llm_agent.chat(message, system_prompt)
        return {
            'response': response,
            'available_tools': len(llm_agent.tool_manager.llm_tools)
        }
    
    logger.info(f"🤖 LLM Agent initialized with {len(llm_agent.tool_manager.llm_tools)} tools")

```

6. 实际使用场景


```python
# 用户通过HTTP API与LLM对话
POST /agent/api/did:wba:localhost:user:123/chat
{
    "message": "帮我搜索一下ANP协议的相关信息，然后读取/tmp/notes.txt文件的内容"
}

```


# LLM会：
1. 自动调用 search_web_for_llm("ANP协议")
2. 请求用户批准后调用 read_file_for_llm("/tmp/notes.txt")  
3. 综合信息给出回复

总结
通过这个扩展设计：

- ✅ LLM工具调用支持
MCP工具可以选择性暴露给LLM
支持OpenAI和Anthropic的工具调用格式
自动处理工具调用流程
- ✅ 权限和安全控制
可以设置哪些工具需要人工批准
记录所有LLM工具调用
区分LLM调用和Agent内部调用
- ✅ 灵活的配置
同一个MCP工具可以有不同的暴露策略
支持工具重命名和描述定制
可以为不同LLM提供不同的工具集
- ✅ 保持简单
开发者只需要添加装饰器参数
自动处理LLM集成的复杂性
统一的工具管理接口
- 开发者只需要添加装饰器参数
- 自动处理LLM集成的复杂性
- 统一的工具管理接口
- 这样MCP工具就真正成为了一个统一的工具生态系统，既可以被Agent内部使用，也可以被LLM调用，实现了工具的最大化复用和价值。
+ - **开发者体验极简**：只需为函数添加装饰器参数（如 `expose_to_llm=True`），即可选择性暴露MCP工具给LLM，无需手动管理注册、权限或路由。
+ - **LLM集成全自动**：框架会自动处理LLM工具发现、参数校验、调用上下文、权限批准和调用日志，开发者无需关心底层细节。
+ - **统一工具生态**：所有MCP工具通过同一管理接口统一注册和发现，支持被Agent本地方法调用，也支持被LLM（如OpenAI/Anthropic）标准工具调用协议访问。
+ - **最大化复用与安全**：同一工具既能服务于Agent业务逻辑，也能安全地暴露给LLM，支持细粒度权限控制和调用审计，真正实现了跨智能体和LLM的工具生态闭环。
