# ANP SDK URL 配置和 DID 路由系统重构方案

## 目标

1. 将所有硬编码的 URL 路径移到配置文件中，实现集中管理
2. 统一 DID 格式规范，确保本机 DID 创建格式与路由匹配
3. 集成 local methods 的身份标识体系
4. 支持多个 agent 共用一个 DID 对外服务的路由机制

## 实施计划

### 第一阶段：扩展配置文件结构

#### 1.1 更新 `unified_config.default.yaml`

在配置文件中添加路由和 DID 格式配置：

```yaml
# 在 anp_sdk 配置节下添加
anp_sdk:
  # ... 现有配置保持不变 ...
  
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
  
  # DID 路由配置（多 Agent 共享）
  did_routing:
    enabled: false  # 默认关闭，需要时启用
    shared_dids: {}  # 共享 DID 配置
```

### 第二阶段：更新类型定义

#### 2.1 更新 `anp_open_sdk/config/config_types.py`

添加新的配置协议：

```python
# 在文件末尾添加

class DIDFormatConfig(Protocol):
    """DID 格式配置协议"""
    method: str
    port_encoding: str
    default_ports: List[int]
    user_types: List[str]
    default_dir: str

class RoutePathsConfig(Protocol):
    """路由路径配置协议"""
    wba: str
    agent: str
    publisher: str
    api: str
    ws: str

class WBARoutesConfig(Protocol):
    """WBA 路由配置协议"""
    auth: str
    user_did: str
    user_ad: str
    user_yaml: str
    user_json: str
    hostuser_did: str
    hostuser_ad: str

class PublisherRoutesConfig(Protocol):
    """发布者路由配置协议"""
    agents: str

class AgentRoutesConfig(Protocol):
    """Agent 路由配置协议"""
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

class APIRoutesConfig(Protocol):
    """API 路由配置协议"""
    root: str
    message: str

class WebSocketRoutesConfig(Protocol):
    """WebSocket 路由配置协议"""
    message: str
    agent: str

class RoutesConfig(Protocol):
    """路由配置协议"""
    base_paths: RoutePathsConfig
    wba: WBARoutesConfig
    publisher: PublisherRoutesConfig
    agent: AgentRoutesConfig
    api: APIRoutesConfig
    websocket: WebSocketRoutesConfig

class DIDRoutingConfig(Protocol):
    """DID 路由配置协议"""
    enabled: bool
    shared_dids: Dict[str, Any]

# 更新 AnpSdkConfig
class AnpSdkConfig(Protocol):
    """ANP SDK 配置协议"""
    # ... 现有字段保持不变 ...
    did_format: DIDFormatConfig
    routes: RoutesConfig
    did_routing: DIDRoutingConfig
```

### 第三阶段：创建核心管理器

#### 3.1 创建 `anp_open_sdk/service/router/route_manager.py`

```python
from typing import Dict, Optional
from anp_open_sdk.config import get_global_config
import logging

logger = logging.getLogger(__name__)

class RouteManager:
    """统一的路由管理器"""
    
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
    
    def get_route(self, category: str, name: str) -> str:
        """获取配置的路由路径
        
        Args:
            category: 路由类别 (wba, publisher, agent, api, websocket)
            name: 路由名称
            
        Returns:
            str: 路由路径
        """
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
        """获取所有路由或指定类别的路由"""
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
        
        # 返回所有路由
        all_routes = {}
        for cat in ['wba', 'publisher', 'agent', 'api', 'websocket']:
            all_routes[cat] = self.get_all_routes(cat)
        return all_routes

# 全局实例
route_manager = RouteManager()
```

#### 3.2 创建 `anp_open_sdk/service/router/did_format_manager.py`

```python
import re
import urllib.parse
import secrets
from typing import Dict, Optional, Tuple, List
from anp_open_sdk.config import get_global_config
import logging

logger = logging.getLogger(__name__)

class DIDFormatManager:
    """DID 格式管理器，统一处理 DID 的创建、解析和路由匹配"""
    
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
    
    def create_did(self, host: str, port: int, user_type: str = "user",
                   dir: str = None, unique_id: str = None) -> str:
        """创建标准格式的 DID
        
        Args:
            host: 主机名
            port: 端口号
            user_type: 用户类型 (user, hostuser, service, agent)
            dir: 目录段，默认为配置中的 default_dir
            unique_id: 16位唯一标识符，默认自动生成
            
        Returns:
            str: 格式化的 DID
        """
        # 使用默认值
        dir = dir or self.did_config.default_dir
        unique_id = unique_id or secrets.token_hex(8)
        
        # 验证用户类型
        if user_type not in self.did_config.user_types:
            raise ValueError(f"Invalid user type: {user_type}. Must be one of {self.did_config.user_types}")
        
        # 处理端口编码
        if port not in self.did_config.default_ports:
            host_port = f"{host}{self.did_config.port_encoding}{port}"
        else:
            host_port = host
        
        # 构建 DID 段
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
        """解析 DID 或 unique_id
        
        Args:
            did_or_id: 完整 DID 或 16位 unique_id
            
        Returns:
            dict: 包含解析结果的字典
        """
        # 处理 URL 编码
        did_or_id = urllib.parse.unquote(did_or_id)
        
        # 检查是否是 16 位 unique_id
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
        
        # 解析完整 DID
        if did_or_id.startswith(f"did:{self.did_config.method}:"):
            # 匹配模式：did:wba:host[%3A|:]port:dir:type:unique_id
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
        """标准化 DID 格式
        
        Args:
            did_or_id: DID 或 unique_id
            request_context: 请求上下文，包含 host、port 等信息
            
        Returns:
            str: 标准化的完整 DID
        """
        parsed = self.parse_did(did_or_id)
        
        if parsed["format"] == "full_did":
            return parsed["full_did"]
        
        if parsed["format"] == "unique_id" and request_context:
            # 从请求上下文构建完整 DID
            host = request_context.get("host", "localhost")
            port = request_context.get("port", 80)
            
            # 从 URL 路径推断用户类型
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
        """创建本地方法的标识符"""
        return f"{did}::{method_name}"
    
    def parse_method_identifier(self, method_id: str) -> Tuple[Optional[str], Optional[str]]:
        """解析方法标识符"""
        if "::" not in method_id:
            return None, None
        
        parts = method_id.split("::", 1)
        return parts[0], parts[1]

# 全局实例
did_format_manager = DIDFormatManager()
```

#### 3.3 创建 `anp_open_sdk/service/router/did_router.py`

```python
import random
from typing import Dict, List, Optional, Any
from anp_open_sdk.config import get_global_config
import logging

logger = logging.getLogger(__name__)

class LoadBalancer:
    """负载均衡器"""
    
    def __init__(self, strategy: str, agents: List[Dict[str, Any]]):
        self.strategy = strategy
        self.agents = agents
        self.current_index = 0
        self.total_weight = sum(a.get("weight", 1) for a in agents)
    
    def get_next_agent(self) -> str:
        """根据策略获取下一个 Agent DID"""
        if not self.agents:
            return None
        
        if self.strategy == "round_robin":
            agent = self.agents[self.current_index]["did"]
            self.current_index = (self.current_index + 1) % len(self.agents)
            return agent
        
        elif self.strategy == "random":
            return random.choice(self.agents)["did"]
        
        elif self.strategy == "weighted":
            rand_weight = random.uniform(0, self.total_weight)
            cumulative_weight = 0
            
            for agent in self.agents:
                cumulative_weight += agent.get("weight", 1)
                if rand_weight <= cumulative_weight:
                    return agent["did"]
            
            return self.agents[-1]["did"]
        
        else:
            return self.agents[0]["did"]

class DIDRouter:
    """DID 路由器，支持多 Agent 共享 DID"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
            
        config = get_global_config()
        self.enabled = config.anp_sdk.did_routing.enabled
        self.shared_dids = config.anp_sdk.did_routing.shared_dids or {}
        self.load_balancers = {}
        
        if self.enabled:
            self._init_load_balancers()
        
        self._initialized = True
    
    def _init_load_balancers(self):
        """初始化负载均衡器"""
        for did, config in self.shared_dids.items():
            if "load_balancing" in config:
                lb_config = config["load_balancing"]
                self.load_balancers[did] = LoadBalancer(
                    strategy=lb_config.get("strategy", "round_robin"),
                    agents=lb_config.get("agents", [])
                )
    
    def route_request(self, target_did: str, path: str) -> str:
        """路由请求到实际的 Agent DID"""
        if not self.enabled:
            return target_did
        
        if target_did not in self.shared_dids:
            return target_did
        
        config = self.shared_dids[target_did]
        
        # 检查路径匹配规则
        for rule in config.get("routing_rules", []):
            if path.startswith(rule["path_prefix"]):
                return rule["target_agent"]
        
        # 检查负载均衡
        if target_did in self.load_balancers:
            next_agent = self.load_balancers[target_did].get_next_agent()
            if next_agent:
                return next_agent
        
        # 使用默认 agent
        return config.get("default_agent", target_did)
    
    def register_shared_did(self, shared_did: str, config: Dict[str, Any]):
        """动态注册共享 DID"""
        self.shared_dids[shared_did] = config
        
        if "load_balancing" in config:
            lb_config = config["load_balancing"]
            self.load_balancers[shared_did] = LoadBalancer(
                strategy=lb_config.get("strategy", "round_robin"),
                agents=lb_config.get("agents", [])
            )
        
        logger.info(f"Registered shared DID: {shared_did}")
    
    def unregister_shared_did(self, shared_did: str):
        """注销共享 DID"""
        if shared_did in self.shared_dids:
            del self.shared_dids[shared_did]
        
        if shared_did in self.load_balancers:
            del self.load_balancers[shared_did]
        
        logger.info(f"Unregistered shared DID: {shared_did}")

# 全局实例
did_router = DIDRouter()
```

### 第四阶段：更新现有路由文件

#### 4.1 更新 `anp_open_sdk/service/router/router_auth.py`

```python
# 在文件开头添加导入
from anp_open_sdk.service.router.route_manager import route_manager

# 修改路由装饰器
@router.get(route_manager.get_route("wba", "adapter_auth"), summary="DID WBA authentication endpoint")
async def test_endpoint(request: Request) -> Dict:
    # ... 现有实现保持不变 ...
```

#### 4.2 更新 `anp_open_sdk/service/router/router_did.py`

```python
# 在文件开头添加导入
from anp_open_sdk.service.router.route_manager import route_manager
from anp_open_sdk.service.router.did_format_manager import did_format_manager

# 修改 url_did_format 函数
def url_did_format(user_id: str, request: Request) -> str:
    """使用 DID 格式管理器标准化 DID"""
    request_context = {
        "host": request.url.hostname,
        "port": request.url.port or 80,
        "path": str(request.url.path)
    }
    return did_format_manager.normalize_did(user_id, request_context)

# 修改路由装饰器
@router.get(route_manager.get_route("wba", "user_did"), summary="Get DID document")
async def get_did_document(user_id: str, request: Request) -> Dict:
    # ... 使用新的 url_did_format ...
    
@router.get(route_manager.get_route("wba", "user_ad"), summary="Get agent description")
async def get_agent_description(user_id: str, request: Request) -> Dict:
    # ... 使用新的 url_did_format ...

# ... 其他路由类似更新 ...
```

#### 4.3 更新 `anp_open_sdk/service/router/router_publisher.py`

```python
# 在文件开头添加导入
from anp_open_sdk.service.router.route_manager import route_manager

# 修改路由装饰器
@router.get(route_manager.get_route("wba", "hostuser_did"), summary="Get Hosted DID document")
async def get_hosted_did_document(user_id: str) -> Dict:
    # ... 现有实现保持不变 ...

@router.get(route_manager.get_route("publisher", "agents"), summary="Get published agent list")
async def get_agent_publishers(request: Request) -> Dict:
    # ... 现有实现保持不变 ...
```

#### 4.4 更新 `anp_open_sdk/anp_sdk.py`

```python
# 在文件开头添加导入
from anp_open_sdk.service.router.route_manager import route_manager
from anp_open_sdk.service.router.did_router import did_router

# 在 _register_default_routes 方法中使用配置的路由
def _register_default_routes(self):
    # ... 现有代码 ...
    
    # 使用路由管理器获取路由
    @self.app.get(route_manager.get_route("api", "root"), tags=["status"])
    async def root():
        # ... 现有实现 ...
    
    @self.app.get(route_manager.get_route("agent", "api"))
    async def api_entry_get(did: str, subpath: str, request: Request):
        # ... 现有实现 ...
    
    # ... 其他路由类似更新 ...
```

#### 4.5 更新 `anp_open_sdk/service/router/router_agent.py`

```python
# 在文件开头添加导入
from anp_open_sdk.service.router.did_router import did_router
from anp_open_sdk.service.router.did_format_manager import did_format_manager

# 修改 AgentRouter 类
class AgentRouter:
    def __init__(self):
        self.local_agents = {}
        self.logger = logger
        self.did_router = did_router  # 添加 DID 路由器
    
    async def route_request(self, req_did: str, resp_did: str, 
                          request_data: Dict, request: Request) -> Any:
        """增强的路由请求，支持 DID 路由"""
        # 标准化 DID
        request_context = {
            "host": request.url.hostname,
            "port": request.url.port or 80,
            "path": str(request.url.path)
        }
        resp_did = did_format_manager.normalize_did(resp_did, request_context)
        
        # 获取请求路径
        path = request_data.get("path", "")
        
        # 通过 DID 路由器获取实际的目标 Agent
        actual_did = self.did_router.route_request(resp_did, path)
        
        # 如果路由后的 DID 不同，记录日志
        if actual_did != resp_did:
            request_data["original_did"] = resp_did
            request_data["routed_did"] = actual_did
            logger.info(f"DID routing: {resp_did} -> {actual_did} for path: {path}")
        
        # 查找实际的 Agent
        if actual_did in self.local_agents:
            agent = self.local_agents[actual_did]
            request.state.agent = agent
            logger.info(f"成功路由到{agent.id}的处理函数, 请求数据为{request_data}")
            return await agent.handle_request(req_did, request_data, request)
        else:
            # 如果是共享 DID 但没有找到目标 agent，返回详细错误
            if resp_did in self.did_router.shared_dids:
                self.logger.error(f"共享 DID {resp_did} 的目标 Agent {actual_did} 未注册")
                raise ValueError(f"共享 DID {resp_did} 的目标 Agent {actual_did} 未注册")
            else:
                self.logger.error(f"智能体路由器未找到本地智能体: {resp_did}")
                raise ValueError(f"未找到本地智能体: {resp_did}")
```

### 第五阶段：集成 Local Methods

#### 5.1 创建 `anp_open_sdk/service/router/local_methods_router.py`

```python
from fastapi import Request, APIRouter
from typing import Dict, Any
from anp_open_sdk.service.router.route_manager import route_manager
from anp_open_sdk.service.router.did_format_manager import did_format_manager
from anp_open_sdk_framework.local_methods.local_methods_caller import LocalMethodsCaller
from anp_open_sdk_framework.local_methods.local_methods_decorators import LOCAL_METHODS_REGISTRY
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["local_methods"])

@router.post(route_manager.get_route("agent", "method_call"))
async def call_local_method(agent_id: str, method_name: str, request: Request) -> Dict[str, Any]:
    """调用本地方法"""
    try:
        # 获取请求数据
        data = await request.json()
        
        # 标准化 agent_id 为完整 DID
        request_context = {
            "host": request.url.hostname,
            "port": request.url.port or 80,
            "path": str(request.url.path)
        }
        agent_did = did_format_manager.normalize_did(agent_id, request_context)
        
        # 构建方法标识符
        method_key = did_format_manager.create_method_identifier(agent_did, method_name)
        
        # 调用方法
        sdk = request.app.state.sdk
        caller = LocalMethodsCaller(sdk)
        result = await caller.call_method_by_key(method_key, **data)
        
        return {
            "status": "success",
            "result": result,
            "method": method_key
        }
    except Exception as e:
        logger.error(f"Error calling local method: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get(route_manager.get_route("agent", "method_doc"))
async def get_method_doc(agent_id: str, request: Request) -> Dict[str, Any]:
    """获取 Agent 的方法文档"""
    try:
        # 标准化 agent_id
        request_context = {
            "host": request.url.hostname,
            "port": request.url.port or 80,
            "path": str(request.url.path)
        }
        agent_did = did_format_manager.normalize_did(agent_id, request_context)
        
        # 获取该 agent 的所有方法
        agent_methods = {
            key: info for key, info in LOCAL_METHODS_REGISTRY.items()
            if info["agent_did"] == agent_did
        }
        
        return {
            "status": "success",
            "agent_did": agent_did,
            "methods": agent_methods
        }
    except Exception as e:
        logger.error(f"Error getting method doc: {e}")
        return {
            "status": "error",
            "error": str(e)
        }

@router.get(route_manager.get_route("agent", "methods_list"))
async def list_all_methods(request: Request) -> Dict[str, Any]:
    """列出所有可用的本地方法"""
    return {
        "status": "success",
        "total": len(LOCAL_METHODS_REGISTRY),
        "methods": LOCAL_METHODS_REGISTRY
    }

@router.post(route_manager.get_route("agent", "methods_search"))
async def search_methods(request: Request) -> Dict[str, Any]:
    """搜索本地方法"""
    try:
        data = await request.json()
        keyword = data.get("keyword", "")
        agent_name = data.get("agent_name", "")
        tags = data.get("tags", [])
        
        from anp_open_sdk_framework.local_methods.local_methods_doc import LocalMethodsDocGenerator
        doc_generator = LocalMethodsDocGenerator()
        results = doc_generator.search_methods(
            keyword=keyword,
            agent_name=agent_name,
            tags=tags
        )
        
        return {
            "status": "success",
            "count": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error searching methods: {e}")
        return {
            "status": "error",
            "error": str(e)
        }
```

#### 5.2 更新 `anp_open_sdk/anp_sdk.py` 以包含 local methods 路由

在 `_register_default_routes` 方法中添加：

```python
# 在导入部分添加
from anp_open_sdk.service.router import local_methods_router

# 在 _register_default_routes 方法中添加
def _register_default_routes(self):
    # ... 现有路由注册代码 ...
    
    # 注册 local methods 路由
    self.app.include_router(local_methods_router.router)
    
    # ... 其余代码 ...
```

### 第六阶段：更新 DID 创建逻辑

#### 6.1 更新 `anp_open_sdk/anp_sdk_user_data.py`

修改 `did_create_user` 函数以使用新的 DID 格式管理器：

```python
# 在文件开头添加导入
from anp_open_sdk.service.router.did_format_manager import did_format_manager

# 修改 did_create_user 函数
def did_create_user(user_input: dict, *, did_hex: bool = True, did_check_unique: bool = True):
    """使用 DID 格式管理器创建用户"""
    from agent_connect.authentication.did_wba import create_did_wba_document
    import json
    import os
    from datetime import datetime
    import re
    import yaml
    
    required_fields = ['name', 'host', 'port', 'dir', 'type']
    if not all(field in user_input for field in required_fields):
        logger.error("缺少必需的参数字段")
        return None
    
    config = get_global_config()
    userdid_filepath = config.anp_sdk.user_did_path
    userdid_filepath = UnifiedConfig.resolve_path(userdid_filepath)
    
    # ... 现有的用户名检查逻辑 ...
    
    # 使用 DID 格式管理器创建 DID
    unique_id = secrets.token_hex(8) if did_hex else None
    
    # 确定用户类型
    user_type = user_input.get('type', 'user')
    if user_type not in did_format_manager.did_config.user_types:
        logger.warning(f"Unknown user type: {user_type}, using 'user'")
        user_type = 'user'
    
    # 创建 DID
    did_id = did_format_manager.create_did(
        host=user_input['host'],
        port=int(user_input['port']),
        user_type=user_type,
        dir=user_input.get('dir', 'wba'),
        unique_id=unique_id
    )
    
    # 检查 DID 唯一性
    if not did_hex and did_check_unique:
        for d in os.listdir(userdid_filepath):
            did_path = os.path.join(userdid_filepath, d, 'did_document.json')
            if os.path.exists(did_path):
                with open(did_path, 'r', encoding='utf-8') as f:
                    did_dict = json.load(f)
                    if did_dict.get('id') == did_id:
                        logger.error(f"DID已存在: {did_id}")
                        return None
    
    # 创建用户目录
    user_dir_name = f"user_{unique_id}" if did_hex else f"user_{user_input['name']}"
    if user_type == "hostuser":
        user_dir_name = f"user_hosted_{unique_id}"
    
    userdid_filepath = os.path.join(userdid_filepath, user_dir_name)
    
    # ... 其余的 DID 文档创建逻辑保持不变 ...
    
    # 更新 did_document 的 id
    did_document['id'] = did_id
    
    # ... 保存文件的逻辑保持不变 ...
    
    return did_document
```

### 第七阶段：创建迁移工具

#### 7.1 创建 `anp_open_sdk/tools/migrate_routes.py`

```python
#!/usr/bin/env python3
"""
路由迁移工具，用于将硬编码的路由迁移到配置文件
"""

import os
import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

class RouteMigrationTool:
    """路由迁移工具"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.route_patterns = []
        self.found_routes = {}
    
    def scan_routes(self) -> Dict[str, List[Tuple[str, str]]]:
        """扫描项目中的所有路由定义"""
        
        # 定义要扫描的文件模式
        patterns = [
            (r'@router.(get|post|put|delete)\s*(\s*["\']([^"\']+)["\']', 'decorator'),
            (r'@app.(get|post|put|delete)\s*(\s*["\']([^"\']+)["\']', 'decorator'),
            (r'add_api_route\s*(\s*["\']([^"\']+)["\']', 'function'),
        ]
        
        # 扫描指定目录
        scan_dirs = [
            self.project_root / "anp_open_sdk" / "service" / "router",
            self.project_root / "anp_open_sdk"
        ]
        
        for scan_dir in scan_dirs:
            for py_file in scan_dir.rglob("*.py"):
                if py_file.name.startswith("__"):
                    continue
                
                try:
                    content = py_file.read_text(encoding='utf-8')
                    file_routes = []
                    
                    for pattern, pattern_type in patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if pattern_type == 'decorator':
                                method, route = match
                                file_routes.append((route, method.upper()))
                            else:
                                file_routes.append((match, 'UNKNOWN'))
                    
                    if file_routes:
                        relative_path = py_file.relative_to(self.project_root)
                        self.found_routes[str(relative_path)] = file_routes
                
                except Exception as e:
                    print(f"Error scanning {py_file}: {e}")
        
        return self.found_routes
    
    def categorize_routes(self) -> Dict[str, Dict[str, str]]:
        """将找到的路由分类"""
        categorized = {
            "wba": {},
            "publisher": {},
            "agent": {},
            "api": {},
            "websocket": {}
        }
        
        for file_path, routes in self.found_routes.items():
            for route, method in routes:
                # 根据路由路径分类
                if route.startswith("/wba/"):
                    if "adapter_auth" in route:
                        categorized["wba"]["adapter_auth"] = route
                    elif "hostuser" in route and "did.json" in route:
                        categorized["wba"]["hostuser_did"] = route
                    elif "user" in route and "did.json" in route:
                        categorized["wba"]["user_did"] = route
                    elif "user" in route and "ad.json" in route:
                        categorized["wba"]["user_ad"] = route
                    elif ".yaml" in route:
                        categorized["wba"]["user_yaml"] = route
                    elif ".json" in route:
                        categorized["wba"]["user_json"] = route
                
                elif route.startswith("/publisher/"):
                    if "agents" in route:
                        categorized["publisher"]["agents"] = route
                
                elif route.startswith("/agent/"):
                    if "/api/" in route:
                        categorized["agent"]["api"] = route
                    elif "/message/" in route:
                        categorized["agent"]["message_post"] = route
                    elif "/group/" in route:
                        if "join" in route:
                            categorized["agent"]["group_join"] = route
                        elif "leave" in route:
                            categorized["agent"]["group_leave"] = route
                        elif "message" in route:
                            categorized["agent"]["group_message"] = route
                        elif "connect" in route:
                            categorized["agent"]["group_connect"] = route
                        elif "members" in route:
                            categorized["agent"]["group_members"] = route
                    elif route == "/agent/groups":
                        categorized["agent"]["groups"] = route
                
                elif route.startswith("/ws/"):
                    if "message" in route:
                        categorized["websocket"]["message"] = route
                    elif "agent" in route:
                        categorized["websocket"]["agent"] = route
                
                elif route == "/":
                    categorized["api"]["root"] = route
                elif route == "/api/message":
                    categorized["api"]["message"] = route
        
        return categorized
    
    def generate_report(self, output_file: str = "route_migration_report.txt"):
        """生成迁移报告"""
        routes = self.scan_routes()
        categorized = self.categorize_routes()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== 路由迁移报告 ===\n\n")
            
            f.write("1. 扫描到的路由文件:\n")
            for file_path in routes.keys():
                f.write(f"   - {file_path}\n")
            
            f.write(f"\n2. 总共找到 {sum(len(r) for r in routes.values())} 个路由定义\n\n")
            
            f.write("3. 路由分类结果:\n")
            for category, route_dict in categorized.items():
                f.write(f"\n   {category.upper()}:\n")
                for name, path in route_dict.items():
                    f.write(f"      {name}: {path}\n")
            
            f.write("\n4. 建议的配置结构已生成在 suggested_routes_config.yaml\n")
        
        # 生成建议的配置
        suggested_config = {
            "routes": categorized
        }
        
        with open("suggested_routes_config.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(suggested_config, f, default_flow_style=False, allow_unicode=True)
        
        print(f"迁移报告已生成: {output_file}")
        print("建议的路由配置已生成: suggested_routes_config.yaml")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ANP SDK 路由迁移工具")
    parser.add_argument("--project-root", default=".", help="项目根目录")
    parser.add_argument("--output", default="route_migration_report.txt", help="输出报告文件")
    
    args = parser.parse_args()
    
    tool = RouteMigrationTool(args.project_root)
    tool.generate_report(args.output)

if __name__ == "__main__":
    main()
```

### 第八阶段：创建测试和验证

#### 8.1 创建 `test/test_route_config.py`

```python
import pytest
from anp_open_sdk.service.router.route_manager import RouteManager
from anp_open_sdk.service.router.did_format_manager import DIDFormatManager
from anp_open_sdk.service.router.did_router import DIDRouter, LoadBalancer

class TestRouteConfiguration:
    """测试路由配置系统"""
    
    def test_route_manager_singleton(self):
        """测试路由管理器单例"""
        rm1 = RouteManager()
        rm2 = RouteManager()
        assert rm1 is rm2
    
    def test_get_route(self):
        """测试获取路由"""
        rm = RouteManager()
        
        # 测试 WBA 路由
        assert rm.get_route("wba", "adapter_auth") == "/wba/adapter_auth"
        assert rm.get_route("wba", "user_did") == "/wba/user/{user_id}/did.json"
        
        # 测试 Agent 路由
        assert rm.get_route("agent", "api") == "/agent/api/{did}/{subpath:path}"
        
        # 测试错误情况
        with pytest.raises(ValueError):
            rm.get_route("invalid", "route")
    
    def test_did_format_manager(self):
        """测试 DID 格式管理器"""
        dfm = DIDFormatManager()
        
        # 测试创建 DID
        did = dfm.create_did("localhost", 9527, "user", "wba", "1234567890abcdef")
        assert did == "did:wba:localhost%3A9527:wba:user:1234567890abcdef"
        
        # 测试解析 DID
        parsed = dfm.parse_did(did)
        assert parsed["format"] == "full_did"
        assert parsed["host"] == "localhost"
        assert parsed["port"] == "9527"
        assert parsed["user_type"] == "user"
        assert parsed["unique_id"] == "1234567890abcdef"
        
        # 测试解析 unique_id
        parsed = dfm.parse_did("1234567890abcdef")
        assert parsed["format"] == "unique_id"
        assert parsed["unique_id"] == "1234567890abcdef"
    
    def test_load_balancer(self):
        """测试负载均衡器"""
        agents = [
            {"did": "did:wba:localhost:wba:agent:001", "weight": 3},
            {"did": "did:wba:localhost:wba:agent:002", "weight": 2},
            {"did": "did:wba:localhost:wba:agent:003", "weight": 1}
        ]
        
        # 测试轮询
        lb = LoadBalancer("round_robin", agents)
        results = [lb.get_next_agent() for _ in range(6)]
        assert results == [
            "did:wba:localhost:wba:agent:001",
            "did:wba:localhost:wba:agent:002",
            "did:wba:localhost:wba:agent:003",
            "did:wba:localhost:wba:agent:001",
            "did:wba:localhost:wba:agent:002",
            "did:wba:localhost:wba:agent:003"
        ]
        
        # 测试随机（只验证返回值在列表中）
        lb = LoadBalancer("random", agents)
        for _ in range(10):
            result = lb.get_next_agent()
            assert result in [a["did"] for a in agents]
    
    def test_did_router(self):
        """测试 DID 路由器"""
        # 需要模拟配置
        router = DIDRouter()
        
        # 测试注册共享 DID
        shared_config = {
            "routing_rules": [
                {"path_prefix": "/api/llm", "target_agent": "did:wba:localhost:wba:agent:llm"},
                {"path_prefix": "/api/calc", "target_agent": "did:wba:localhost:wba:agent:calc"}
            ],
            "default_agent": "did:wba:localhost:wba:agent:default"
        }
        
        router.register_shared_did("did:wba:localhost:wba:gateway:main", shared_config)
        
        # 测试路由
        assert router.route_request("did:wba:localhost:wba:gateway:main", "/api/llm/chat") == "did:wba:localhost:wba:agent:llm"
        assert router.route_request("did:wba:localhost:wba:gateway:main", "/api/calc/add") == "did:wba:localhost:wba:agent:calc"
        assert router.route_request("did:wba:localhost:wba:gateway:main", "/api/other") == "did:wba:localhost:wba:agent:default"
        
        # 测试非共享 DID
        assert router.route_request("did:wba:localhost:wba:user:123", "/any/path") == "did:wba:localhost:wba:user:123"
```

### 第九阶段：文档和示例

#### 9.1 创建 `docs/route_configuration.md`

````markdown
# ANP SDK 路由配置指南

## 概述

ANP SDK 使用统一的配置系统管理所有 URL 路由和 DID 格式。这提供了更好的灵活性和可维护性。

## 配置结构

### 1. DID 格式配置

```yaml
anp_sdk:
  did_format:
    method: "wba"              # DID 方法
    port_encoding: "%3A"       # 端口编码方式
    default_ports: [80, 443]   # 不需要编码的默认端口
    user_types:                # 支持的用户类型
      - "user"
      - "hostuser"
      - "service"
      - "agent"
    default_dir: "wba"         # 默认目录段
````

### 2. 路由配置

```yaml
anp_sdk:
  routes:
    # 基础路径定义
    base_paths:
      wba: "/wba"
      agent: "/agent"
      publisher: "/publisher"
      api: "/api"
      ws: "/ws"
    
    # 各类路由定义
    wba:
      auth: "/wba/adapter_auth"
      user_did: "/wba/user/{user_id}/did.json"
      # ... 更多路由
```

### 3. DID 路由配置（多 Agent 共享）

```yaml
anp_sdk:
  did_routing:
    enabled: true
    shared_dids:
      "did:wba:api.example.com:wba:gateway:main":
        routing_rules:
          - path_prefix: "/api/llm"
            target_agent: "did:wba:internal:wba:service:llm"
          - path_prefix: "/api/calc"
            target_agent: "did:wba:internal:wba:service:calc"
        load_balancing:
          strategy: "weighted"
          agents:
            - did: "did:wba:internal:wba:worker:001"
              weight: 3
            - did: "did:wba:internal:wba:worker:002"
              weight: 2
```

## 使用示例

### 1. 在路由定义中使用

```python
from anp_open_sdk.service.router.route_manager import route_manager

@router.get(route_manager.get_route("wba", "adapter_auth"))
async def auth_endpoint(request: Request):
    # 实现逻辑
    pass
```

### 2. DID 格式管理

```python
from anp_open_sdk.service.router.did_format_manager import did_format_manager

# 创建 DID
did = did_format_manager.create_did(
    host="localhost",
    port=9527,
    user_type="user",
    unique_id="1234567890abcdef"
)

# 解析 DID
parsed = did_format_manager.parse_did(did)
```

### 3. 配置多 Agent 共享 DID

```python
from anp_open_sdk.service.router.did_router import did_router

# 动态注册共享 DID
did_router.register_shared_did(
    "did:wba:api.example.com:wba:gateway:main",
    {
        "routing_rules": [...],
        "load_balancing": {...}
    }
)
```

## 迁移指南

1. 运行迁移工具扫描现有路由：

   ```bash
   python -m anp_open_sdk.tools.migrate_routes --project-root .
   ```

2. 查看生成的报告和建议配置

3. 将建议的配置合并到 `unified_config.yaml`

4. 逐步更新代码使用新的路由管理器

## 最佳实践

1. __集中管理__：所有路由配置都应该在配置文件中定义
2. __类型安全__：使用类型协议确保配置的正确性
3. __版本控制__：配置文件应该纳入版本控制
4. __环境隔离__：不同环境使用不同的配置文件
5. __文档同步__：更新路由时同步更新文档

```javascript

## 执行步骤总结

当您切换到 Act Mode 后，请按以下顺序执行：

1. **更新配置文件**
   - 修改 `unified_config.default.yaml` 添加路由和 DID 配置
   - 更新 `config_types.py` 添加新的协议定义

2. **创建核心管理器**
   - 创建 `route_manager.py`
   - 创建 `did_format_manager.py`
   - 创建 `did_router.py`
   - 创建 `local_methods_router.py`

3. **更新现有文件**
   - 更新 `router_auth.py`、`router_did.py`、`router_publisher.py`
   - 更新 `anp_sdk.py` 和 `router_agent.py`
   - 更新 `anp_sdk_user_data.py` 中的 DID 创建逻辑

4. **创建工具和测试**
   - 创建迁移工具 `migrate_routes.py`
   - 创建测试文件 `test_route_config.py`

5. **创建文档**
   - 创建 `route_configuration.md` 文档

这个方案实现了所有目标：
- ✅ URL 路径集中配置管理
- ✅ DID 格式统一和标准化
- ✅ Local methods 身份标识集成
- ✅ 多 Agent 共享 DID 的路由支持
```




这个综合方案实现了：

1. __Local Methods 集成__：

   - 使用 DID 作为方法的命名空间
   - 自动生成方法路由
   - 支持方法文档和搜索

2. __多 Agent 共享 DID__：

   - 基于路径的路由规则
   - 负载均衡支持
   - 动态路由配置

3. __统一的身份和路由体系__：

   - DID 格式的一致性
   - 灵活的路由配置
   - 向后兼容性

这样的设计既保持了系统的灵活性，又确保了身份标识和路由的一致性。


1. __统一配置__：所有 URL 和 DID 格式都在一个地方配置
2. __格式一致性__：DID 创建和路由匹配使用相同的格式规则
3. __灵活性__：可以轻松修改路由路径和 DID 格式
4. __类型安全__：通过协议定义确保配置的类型安全
5. __可扩展性__：易于添加新的路由和 DID 格式变体
6. __向后兼容__：可以逐步迁移现有代码


1. __统一的 DID 格式__：所有用户类型（user、hostuser、service、agent）都使用相同的 DID 格式规范
2. __灵活的路由配置__：根据用户类型自动选择正确的路由路径
3. __类型感知__：系统能够从 DID 中识别用户类型并做出相应处理
4. __向后兼容__：支持使用 unique_id 访问，系统会根据上下文推断用户类型

这样的设计确保了整个系统的一致性，无论是普通用户还是托管用户，都遵循相同的 DID 格式和路由规则。
