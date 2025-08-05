# Memory系统重新架构定位：公共信号量与状态发布点设计

## 🎯 架构重新定位

基于您的深度思考，Memory系统需要从单纯的"记忆存储"重新定位为：

### 核心定位
- **Agent信息助理**：类似网络上下文工程是网络助理
- **公共信号量**：所有Agent的共享状态协调中心
- **状态发布点**：Agent运行状态信息的统一发布平台
- **同等级服务**：与MCP tool、浏览器子智能体等平级

## 📊 本地服务 vs 网络服务技术对比

### 方案A：本地服务架构

#### 技术实现
```python
# 本地Memory服务
class LocalMemoryService:
    def __init__(self, socket_path: str = "/tmp/anp_memory.sock"):
        self.socket_path = socket_path
        self.memory_store = SQLiteVectorMemory("memory.db")
        self.signal_store = {}  # 信号量存储
        self.agent_states = {}  # Agent状态存储
        self.subscriptions = {}  # 订阅关系
        
    def start_service(self):
        """启动Unix Domain Socket服务"""
        import socket
        import threading
        
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.socket_path)
        server.listen(5)
        
        while True:
            client, address = server.accept()
            thread = threading.Thread(target=self._handle_client, args=(client,))
            thread.start()
    
    def _handle_client(self, client_socket):
        """处理客户端请求"""
        while True:
            try:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                request = json.loads(data.decode())
                response = self._process_request(request)
                client_socket.send(json.dumps(response).encode())
                
            except Exception as e:
                break
        
        client_socket.close()

# Agent客户端
class MemoryClient:
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.socket_path = "/tmp/anp_memory.sock"
        self._connect()
    
    def _connect(self):
        import socket
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.connect(self.socket_path)
    
    def publish_state(self, state: dict):
        """发布Agent状态"""
        request = {
            "action": "publish_state",
            "agent_id": self.agent_id,
            "state": state,
            "timestamp": time.time()
        }
        return self._send_request(request)
    
    def get_signal(self, signal_name: str):
        """获取信号量"""
        request = {
            "action": "get_signal",
            "signal_name": signal_name,
            "agent_id": self.agent_id
        }
        return self._send_request(request)
    
    def set_signal(self, signal_name: str, value: any, ttl: int = None):
        """设置信号量"""
        request = {
            "action": "set_signal",
            "signal_name": signal_name,
            "value": value,
            "ttl": ttl,
            "agent_id": self.agent_id
        }
        return self._send_request(request)
```

**本地服务优势：**
- ✅ **极低延迟**：Unix Socket通信，微秒级响应
- ✅ **无网络依赖**：本地通信，不受网络影响
- ✅ **数据安全**：数据不离开本地机器
- ✅ **简单部署**：无需网络配置和端口管理
- ✅ **资源效率**：共享内存，减少序列化开销

**本地服务劣势：**
- ❌ **单机限制**：无法跨机器共享状态
- ❌ **扩展性差**：难以支持分布式Agent
- ❌ **监控困难**：难以远程监控和管理

### 方案B：网络服务架构

#### 技术实现
```python
# 网络Memory服务
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer
import asyncio
import redis
import websockets

class NetworkMemoryService:
    def __init__(self):
        self.app = FastAPI(title="ANP Memory Service")
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.memory_store = SQLiteVectorMemory("memory.db")
        self.websocket_connections = {}  # Agent WebSocket连接
        self.setup_routes()
        
    def setup_routes(self):
        
        @self.app.post("/api/memory/add")
        async def add_memory(request: AddMemoryRequest, 
                          agent_info = Depends(self.verify_agent)):
            """添加记忆"""
            memory_id = await self.memory_store.add_memory(
                content=request.content,
                embedding=request.embedding,
                agent_id=agent_info.agent_id
            )
            return {"memory_id": memory_id}
        
        @self.app.post("/api/signal/set")
        async def set_signal(request: SetSignalRequest,
                           agent_info = Depends(self.verify_agent)):
            """设置信号量"""
            key = f"signal:{request.signal_name}"
            value = json.dumps({
                "value": request.value,
                "agent_id": agent_info.agent_id,
                "timestamp": time.time(),
                "ttl": request.ttl
            })
            
            if request.ttl:
                self.redis_client.setex(key, request.ttl, value)
            else:
                self.redis_client.set(key, value)
            
            # 通知订阅者
            await self._notify_signal_subscribers(request.signal_name, request.value)
            return {"status": "success"}
        
        @self.app.get("/api/signal/{signal_name}")
        async def get_signal(signal_name: str,
                           agent_info = Depends(self.verify_agent)):
            """获取信号量"""
            key = f"signal:{signal_name}"
            data = self.redis_client.get(key)
            
            if not data:
                raise HTTPException(status_code=404, detail="Signal not found")
            
            return json.loads(data)
        
        @self.app.post("/api/state/publish")
        async def publish_state(request: PublishStateRequest,
                              agent_info = Depends(self.verify_agent)):
            """发布Agent状态"""
            state_key = f"agent_state:{agent_info.agent_id}"
            state_data = {
                "state": request.state,
                "timestamp": time.time(),
                "agent_id": agent_info.agent_id
            }
            
            # 存储到Redis
            self.redis_client.setex(state_key, 300, json.dumps(state_data))  # 5分钟TTL
            
            # 实时推送给监控订阅者
            await self._broadcast_state_update(agent_info.agent_id, state_data)
            return {"status": "published"}
        
        @self.app.websocket("/ws/{agent_id}")
        async def websocket_endpoint(websocket: WebSocket, agent_id: str):
            """WebSocket实时通信"""
            await websocket.accept()
            self.websocket_connections[agent_id] = websocket
            
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self._handle_websocket_message(agent_id, message)
            except:
                pass
            finally:
                if agent_id in self.websocket_connections:
                    del self.websocket_connections[agent_id]

# Agent网络客户端
class NetworkMemoryClient:
    def __init__(self, agent_id: str, base_url: str, api_key: str):
        self.agent_id = agent_id
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.websocket = None
        
    async def connect_websocket(self):
        """建立WebSocket连接"""
        ws_url = f"{self.base_url.replace('http', 'ws')}/ws/{self.agent_id}"
        self.websocket = await websockets.connect(ws_url)
        
        # 启动消息监听
        asyncio.create_task(self._listen_websocket())
    
    async def publish_state(self, state: dict):
        """发布状态"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/state/publish",
                json={"state": state},
                headers=self.headers
            )
            return response.json()
    
    async def set_signal(self, signal_name: str, value: any, ttl: int = None):
        """设置信号量"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/signal/set",
                json={
                    "signal_name": signal_name,
                    "value": value,
                    "ttl": ttl
                },
                headers=self.headers
            )
            return response.json()
```

**网络服务优势：**
- ✅ **分布式支持**：跨机器、跨网络Agent协作
- ✅ **可扩展性**：支持水平扩展和负载均衡
- ✅ **远程监控**：Web界面统一监控所有Agent
- ✅ **标准化**：HTTP/WebSocket标准协议
- ✅ **云原生**：容器化部署，适合云环境

**网络服务劣势：**
- ❌ **网络延迟**：网络通信增加延迟
- ❌ **复杂性高**：需要处理网络故障、重连等
- ❌ **安全考虑**：需要认证、加密、防火墙配置
- ❌ **资源占用**：网络服务和序列化开销

### 方案C：混合架构（推荐）

#### 技术实现
```python
class HybridMemoryService:
    def __init__(self, deployment_mode: str = "auto"):
        self.deployment_mode = deployment_mode
        
        # 本地组件
        self.local_cache = LocalMemoryCache()
        self.local_signals = LocalSignalStore()
        
        # 可选网络组件
        self.network_client = None
        self.is_network_available = False
        
        if deployment_mode in ["network", "auto"]:
            self._try_connect_network()
    
    def _try_connect_network(self):
        """尝试连接网络服务"""
        try:
            self.network_client = NetworkMemoryClient(
                agent_id=self.agent_id,
                base_url=os.getenv("MEMORY_SERVICE_URL"),
                api_key=os.getenv("MEMORY_API_KEY")
            )
            self.is_network_available = True
        except:
            self.is_network_available = False
    
    async def set_signal(self, signal_name: str, value: any, 
                        scope: str = "local", ttl: int = None):
        """智能信号量设置"""
        
        # 本地信号量
        if scope == "local" or not self.is_network_available:
            return self.local_signals.set(signal_name, value, ttl)
        
        # 全局信号量
        elif scope == "global" and self.is_network_available:
            try:
                result = await self.network_client.set_signal(signal_name, value, ttl)
                # 同步到本地缓存
                self.local_cache.cache_signal(signal_name, value, ttl)
                return result
            except:
                # 网络失败，降级到本地
                return self.local_signals.set(signal_name, value, ttl)
        
        # 自动选择
        elif scope == "auto":
            if self._is_cross_agent_signal(signal_name):
                return await self.set_signal(signal_name, value, "global", ttl)
            else:
                return await self.set_signal(signal_name, value, "local", ttl)
    
    def _is_cross_agent_signal(self, signal_name: str) -> bool:
        """判断是否需要跨Agent共享的信号"""
        cross_agent_patterns = [
            "task_coordination_", 
            "resource_lock_",
            "global_state_",
            "shared_data_"
        ]
        return any(signal_name.startswith(pattern) for pattern in cross_agent_patterns)
```

## 📋 权限控制机制设计

### 基于角色的权限控制(RBAC)
```python
class MemoryPermissionManager:
    def __init__(self):
        self.permissions = {
            # Agent权限定义
            "agent_roles": {
                "coordinator": {  # 协调Agent
                    "signals": ["read", "write", "delete"],
                    "states": ["read", "write", "subscribe"],
                    "memories": ["read", "write", "search"]
                },
                "worker": {  # 工作Agent
                    "signals": ["read", "write"],
                    "states": ["write"],  # 只能发布自己的状态
                    "memories": ["read", "write", "search"]
                },
                "monitor": {  # 监控Agent
                    "signals": ["read"],
                    "states": ["read", "subscribe"],
                    "memories": ["read", "search"]
                }
            },
            
            # 资源权限定义
            "resource_permissions": {
                "signal_patterns": {
                    "task_coordination_*": ["coordinator"],
                    "resource_lock_*": ["coordinator", "worker"],
                    "agent_status_*": ["coordinator", "monitor"],
                    "private_*": []  # 私有信号，只有创建者可访问
                },
                "memory_types": {
                    "public": ["coordinator", "worker", "monitor"],
                    "shared": ["coordinator", "worker"],
                    "private": []  # 只有创建者可访问
                }
            }
        }
    
    def check_permission(self, agent_id: str, resource_type: str, 
                        resource_name: str, action: str) -> bool:
        """检查权限"""
        agent_role = self._get_agent_role(agent_id)
        
        if resource_type == "signal":
            return self._check_signal_permission(agent_role, resource_name, action)
        elif resource_type == "state":
            return self._check_state_permission(agent_role, agent_id, action)
        elif resource_type == "memory":
            return self._check_memory_permission(agent_role, resource_name, action)
        
        return False
    
    def _check_signal_permission(self, role: str, signal_name: str, action: str) -> bool:
        """检查信号量权限"""
        # 检查角色基础权限
        role_perms = self.permissions["agent_roles"].get(role, {})
        if action not in role_perms.get("signals", []):
            return False
        
        # 检查信号模式权限
        for pattern, allowed_roles in self.permissions["resource_permissions"]["signal_patterns"].items():
            if fnmatch.fnmatch(signal_name, pattern):
                return role in allowed_roles
        
        return True  # 默认允许
```

## 🏗️ 工程实现方案

### 部署决策树
```python
class MemoryDeploymentDecision:
    def __init__(self):
        self.factors = {
            "agent_count": 0,
            "cross_machine": False,
            "monitoring_required": False,
            "scalability_required": False,
            "network_reliability": "high",
            "security_level": "medium"
        }
    
    def recommend_deployment(self, factors: dict) -> str:
        """推荐部署方案"""
        self.factors.update(factors)
        
        # 决策逻辑
        if self.factors["agent_count"] == 1 and not self.factors["cross_machine"]:
            return "local_only"
        
        elif self.factors["agent_count"] <= 5 and not self.factors["cross_machine"]:
            if self.factors["monitoring_required"]:
                return "hybrid_local_primary"
            else:
                return "local_only"
        
        elif self.factors["cross_machine"] or self.factors["scalability_required"]:
            return "network_primary"
        
        else:
            return "hybrid_balanced"
```

## 🎯 推荐实施策略

### 阶段化部署
1. **阶段1**：本地服务 + Unix Socket
   - 单机多Agent场景
   - 快速原型验证
   
2. **阶段2**：混合架构
   - 本地 + 可选网络
   - 支持监控和简单分布式
   
3. **阶段3**：完整网络服务
   - 全分布式部署
   - 企业级监控和管理

### 技术选型建议
- **小规模**（1-5个Agent）：本地服务
- **中等规模**（5-20个Agent）：混合架构
- **大规模**（20+个Agent）：网络服务

Memory系统作为公共信号量和状态发布点，需要在性能、复杂度和扩展性之间找到平衡！