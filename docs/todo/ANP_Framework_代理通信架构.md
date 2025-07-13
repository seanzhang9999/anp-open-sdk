# ANP SDK HostDID代理通信架构设计方案

## 1. 应用场景与设计目标

### 1.1 核心应用场景
本方案主要解决**内网/移动网络中的服务通过稳定的公网代理安全对外提供服务**的问题：

- **服务方C**：位于内网、移动网络或动态IP环境，无法直接被外部访问
- **代理方B**：具有稳定公网IP的托管服务器，提供代理转发服务  
- **请求方A**：需要访问C提供的服务，但无法直接连接到C

### 1.2 设计目标
- **端到端安全**：基于DID的端到端加密，代理方B无法看到明文数据
- **透明代理**：对C端服务完全透明，无需修改现有业务逻辑
- **网络适应**：解决NAT穿透、防火墙限制等网络连接问题
- **性能优化**：针对不同场景提供最优的通信方式

### 1.3 核心创新
- **HostDID机制**：基于hosted_did的代理身份标识
- **双阶段认证**：密钥协商 + 加密通信的安全机制
- **混合通信**：标准代理 + 反向直连的灵活方案

## 2. 核心架构设计

### 2.1 角色定义
- **请求方A**：`did-a`，发起API调用的客户端
- **Host方B**：托管服务器，提供hostdid代理服务
- **服务方C**：拥有`hostdid-c`，通过WebSocket连接B并注册为处理端口H

### 2.2 整体架构图
```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────────────────┐
│   请求方 A      │         │    Host方 B     │         │        服务方 C            │
│                 │         │                 │         │                             │
│ DID: did-a      │         │ 托管服务器      │         │  ┌─────────────────────┐    │
│ 公钥: pub-a     │         │                 │         │  │  C的WebSocket客户端 │    │
│ 私钥: priv-a    │         │                 │         │  │                     │    │
└─────────────────┘         └─────────────────┘         │  │ 拥有hostdid-c私钥   │    │
         │                           │                   │  └─────────────────────┘    │
         │                           │                   │            │                │
    HTTP请求                    WebSocket                │            │ HTTP请求       │
         │                      代理转发                 │            ▼                │
         │                           │                   │  ┌─────────────────────┐    │
         └───────────────────────────┼───────────────────┼─→│  C的FastAPI服务     │    │
                                     │                   │  │                     │    │
                              处理端口 H                  │  │ /agent/api/         │    │
                                                         │  │ {hostdid-c}/{api}   │    │
                                                         │  └─────────────────────┘    │
                                                         └─────────────────────────────┘
```

### 2.3 通信模式
#### 基础代理模式
```
A → [加密Context] → B → [WebSocket转发] → C → [本地HTTP调用] → 结果返回
```

#### 反向直连模式（用于复杂场景）
```
A ← [反向连接] ← C （处理大文件、流式、实时通信）
```

## 3. 详细技术流程

### 3.1 服务注册阶段
```
服务方 C                    Host方 B
    │                          │
    │ ①WebSocket连接            │
    │─────────────────────────→│
    │                          │
    │ ②注册hostdid-c           │
    │ {                        │
    │   type: "register_hostdid"│
    │   hostdid: "hostdid-c"   │
    │   signature: sign(       │
    │     "register_hostdid-c",│
    │     priv-c               │
    │   )                      │
    │ }                        │
    │─────────────────────────→│
    │                          │
    │ ③注册确认                │
    │←─────────────────────────│
    │                          │
    │ 现在C成为hostdid-c的     │
    │ 处理端口H                │
```

### 3.2 密钥协商阶段（第一阶段认证）
```
请求方 A              Host方 B              服务方 C
    │                     │                     │
    │ ①获取加密密钥请求    │                     │
    │ POST /hostagent/    │                     │
    │      auth/hostdid-c │                     │
    │ {                   │                     │
    │   requester_did:    │                     │
    │   "did-a"           │                     │
    │ }                   │                     │
    │────────────────────→│                     │
    │                     │ ②转发到处理端口H   │
    │                     │ {                   │
    │                     │   type: "auth_req"  │
    │                     │   requester_did:    │
    │                     │   "did-a"           │
    │                     │ }                   │
    │                     │────────────────────→│
    │                     │                     │
    │                     │                     │ ③C生成随机密钥X
    │                     │                     │ ④用did-a公钥加密X
    │                     │                     │ ⑤组装双向认证头
    │                     │                     │
    │                     │ ⑥返回加密密钥       │
    │                     │ {                   │
    │                     │   encrypted_key:    │
    │                     │   encrypt(X, pub-a) │
    │                     │   auth_header: ...  │
    │                     │ }                   │
    │                     │←────────────────────│
    │ ⑦返回加密密钥       │                     │
    │←────────────────────│                     │
    │                     │                     │
    │ A用priv-a解密得到X  │                     │
```

### 3.3 加密通信阶段（第二阶段认证）
```
请求方 A              Host方 B              服务方 C
    │                     │                     │
    │ ①组装context        │                     │
    │ context = {          │                     │
    │   caller_did: "did-a"│                     │
    │   target_did:        │                     │
    │   "hostdid-c"        │                     │
    │   request_url:       │                     │
    │   "api/hostdid-c/xxx"│                     │
    │   method: "POST"     │                     │
    │   json_data: {...}   │                     │
    │   signature: sign(   │                     │
    │     context, priv-a  │                     │
    │   )                  │                     │
    │ }                    │                     │
    │                      │                     │
    │ ②用密钥X加密context  │                     │
    │ encrypted_context =  │                     │
    │ encrypt(context, X)  │                     │
    │                      │                     │
    │ ③发送加密调用请求    │                     │
    │ POST /hostagent/     │                     │
    │      call/hostdid-c  │                     │
    │ {                    │                     │
    │   encrypted_context  │                     │
    │ }                    │                     │
    │─────────────────────→│                     │
    │                      │ ④转发到处理端口H   │
    │                      │ {                   │
    │                      │   type:             │
    │                      │   "encrypted_call"  │
    │                      │   encrypted_context │
    │                      │ }                   │
    │                      │────────────────────→│
    │                      │                     │
    │                      │                     │ ⑤C用密钥X解密context
    │                      │                     │ ⑥验证did-a签名
    │                      │                     │ ⑦组装HTTP请求
    │                      │                     │ POST /agent/api/
    │                      │                     │      hostdid-c/xxx
    │                      │                     │ ⑧C本地服务器处理
    │                      │                     │
    │                      │ ⑨返回处理结果       │
    │                      │←────────────────────│
    │ ⑩返回最终结果       │                     │
    │←─────────────────────│                     │
```

## 4. 代码实现方案

### 4.1 A端实现（auth_client.py）
**位置**：`anp_open_sdk/auth/auth_client.py`

**核心功能**：
- hostdid请求检测和路由
- 双阶段认证流程实现
- context组装和加密

**关键增强**：
```python
async def send_authenticated_request(
    caller_agent: str, target_agent: str, request_url: str,
    method: str = "GET", json_data: Optional[Dict] = None,
    custom_headers: Optional[Dict[str, str]] = None,
    use_two_way_auth: bool = True,
) -> Tuple[int, str, str, bool]:
    """通用认证函数，支持hostdid代理和直连两种模式"""
    
    # 检测是否为hostdid代理请求
    if _is_hostdid_proxy_request(request_url) or _is_hostdid_proxy_request(target_agent):
        return await _execute_hostdid_proxy_flow(
            caller_agent, target_agent, request_url,
            method, json_data, custom_headers, use_two_way_auth
        )
    else:
        # 现有的直连流程
        return await _execute_wba_auth_flow(
            caller_agent, target_agent, request_url,
            method, json_data, custom_headers, use_two_way_auth
        )

async def _execute_hostdid_proxy_flow(
    caller_did: str, hostdid: str, request_url: str,
    method: str = "GET", json_data: Optional[Dict] = None,
    custom_headers: Dict[str, str] = None,
    use_two_way_auth: bool = True
) -> Tuple[int, str, str, bool]:
    """执行hostdid代理认证流程"""
    
    # 1. 解析hostdid和host服务器地址
    host_server = _parse_host_server_from_hostdid(hostdid)
    
    # 2. 第一阶段：向host服务器请求加密密钥
    auth_url = f"{host_server}/hostagent/auth/{hostdid}"
    encryption_key = await _request_encryption_key(auth_url, caller_did)
    
    # 3. 组装完整的AuthenticationContext
    context = AuthenticationContext(
        caller_did=caller_did,
        target_did=hostdid,
        request_url=f"api/{hostdid}/{_extract_api_path(request_url)}",
        method=method,
        json_data=json_data,
        custom_headers=custom_headers,
        use_two_way_auth=use_two_way_auth
    )
    
    # 4. 用密钥X加密整个context
    encrypted_context = _encrypt_context_with_key(context, encryption_key)
    
    # 5. 第二阶段：发送加密调用请求
    call_url = f"{host_server}/hostagent/call/{hostdid}"
    return await _send_encrypted_call(call_url, encrypted_context)
```

### 4.2 B端实现（router_host.py）
**位置**：`anp_open_sdk_framework/server/router/router_host.py`

**核心功能**：
- hostdid WebSocket连接管理
- 请求路由和转发
- 异步响应处理

**关键增强**：
```python
# 全局WebSocket连接管理
hostdid_connections = {}  # hostdid -> websocket_connection
pending_requests = {}     # request_id -> asyncio.Future

@router.websocket("/ws/hostdid")
async def hostdid_websocket_endpoint(websocket: WebSocket):
    """hostdid WebSocket连接端点"""
    await websocket.accept()
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            await _handle_hostdid_websocket_message(websocket, message)
    except WebSocketDisconnect:
        _cleanup_hostdid_connection(websocket)

@router.post("/hostagent/auth/{hostdid}")
async def hostdid_auth_proxy(hostdid: str, request: Request):
    """hostdid认证代理 - 第一阶段：密钥协商"""
    try:
        if hostdid not in hostdid_connections:
            raise HTTPException(status_code=404, detail=f"hostdid {hostdid} 未注册")
        
        request_data = await request.json()
        request_id = str(uuid.uuid4())
        
        # 转发给C的WebSocket客户端
        ws_message = {
            "type": "auth_request",
            "request_id": request_id,
            "requester_did": request_data.get("requester_did"),
            "hostdid": hostdid
        }
        
        websocket = hostdid_connections[hostdid]
        await websocket.send_text(json.dumps(ws_message))
        
        # 等待C的响应
        response = await _wait_for_auth_response(request_id)
        return response
        
    except Exception as e:
        logger.error(f"hostdid认证代理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hostagent/call/{hostdid}")
async def hostdid_call_proxy(hostdid: str, request: Request):
    """hostdid调用代理 - 第二阶段：加密调用"""
    try:
        if hostdid not in hostdid_connections:
            raise HTTPException(status_code=404, detail=f"hostdid {hostdid} 未注册")
        
        request_data = await request.json()
        request_id = str(uuid.uuid4())
        
        # 转发给C的WebSocket客户端
        ws_message = {
            "type": "encrypted_call",
            "request_id": request_id,
            "encrypted_context": request_data.get("encrypted_context")
        }
        
        websocket = hostdid_connections[hostdid]
        await websocket.send_text(json.dumps(ws_message))
        
        # 等待C的响应
        response = await _wait_for_call_response(request_id)
        return response
        
    except Exception as e:
        logger.error(f"hostdid调用代理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### 4.3 C端实现（anp_user.py）
**位置**：`anp_open_sdk/anp_user.py`

**核心功能**：
- WebSocket客户端连接管理
- hostdid注册和身份验证
- 加密解密和本地API调用

**关键增强**：
```python
class ANPUser:
    def __init__(self, ...):
        # 现有初始化代码...
        
        # 新增：hostdid代理相关属性
        self.hostdid_websocket = None
        self.hostdid_private_key = None  # hostdid的私钥
        self.encryption_keys = {}  # requester_did -> encryption_key
        
    async def start_hostdid_proxy_client(self, host_server_url: str, hostdid: str):
        """启动hostdid代理客户端"""
        self.hostdid = hostdid
        self.hostdid_private_key = self._load_hostdid_private_key(hostdid)
        
        # 连接到host方B的WebSocket
        import websockets
        
        while True:
            try:
                ws_url = f"{host_server_url}/ws/hostdid"
                async with websockets.connect(ws_url) as websocket:
                    self.hostdid_websocket = websocket
                    
                    # 注册hostdid
                    await self._register_hostdid(websocket, hostdid)
                    
                    # 开始消息循环
                    await self._hostdid_websocket_loop(websocket)
                    
            except Exception as e:
                logger.error(f"hostdid代理客户端连接失败: {e}")
                await asyncio.sleep(5)  # 重连间隔

    async def _handle_auth_request(self, data: dict):
        """处理密钥协商请求"""
        request_id = data.get("request_id")
        requester_did = data.get("requester_did")
        
        try:
            # 1. 生成随机传输密钥X
            encryption_key = self._generate_encryption_key()
            
            # 2. 获取requester_did的公钥
            requester_public_key = await self._get_did_public_key(requester_did)
            
            # 3. 用requester_did的公钥加密传输密钥X
            encrypted_key = self._encrypt_with_public_key(encryption_key, requester_public_key)
            
            # 4. 生成双向认证头
            auth_header = self._generate_auth_header(requester_did)
            
            # 5. 存储密钥供后续使用
            self.encryption_keys[requester_did] = encryption_key
            
            # 6. 通过WebSocket返回结果
            response = {
                "type": "auth_response",
                "request_id": request_id,
                "encrypted_key": encrypted_key,
                "auth_header": auth_header
            }
            
            await self.hostdid_websocket.send(json.dumps(response))
            
        except Exception as e:
            error_response = {
                "type": "auth_response",
                "request_id": request_id,
                "error": str(e)
            }
            await self.hostdid_websocket.send(json.dumps(error_response))

    async def _handle_encrypted_call(self, data: dict):
        """处理加密调用请求"""
        request_id = data.get("request_id")
        encrypted_context = data.get("encrypted_context")
        
        try:
            # 1. 解密context
            context = self._decrypt_context(encrypted_context)
            
            # 2. 验证caller_did的签名
            if not self._verify_context_signature(context):
                raise Exception("context签名验证失败")
            
            # 3. 组装HTTP请求到本地FastAPI服务
            api_path = context["request_url"].replace(f"api/{self.hostdid}/", "")
            local_url = f"http://localhost:{self.port}/agent/api/{self.hostdid}/{api_path}"
            
            # 4. 发送HTTP请求到本地FastAPI服务
            async with aiohttp.ClientSession() as session:
                method = context["method"]
                json_data = context["json_data"]
                
                if method.upper() == "GET":
                    async with session.get(local_url) as response:
                        result = await response.json()
                        status_code = response.status
                elif method.upper() == "POST":
                    async with session.post(local_url, json=json_data) as response:
                        result = await response.json()
                        status_code = response.status
            
            # 5. 通过WebSocket返回结果
            response = {
                "type": "call_response",
                "request_id": request_id,
                "status_code": status_code,
                "result": result
            }
            
            await self.hostdid_websocket.send(json.dumps(response))
            
        except Exception as e:
            error_response = {
                "type": "call_response",
                "request_id": request_id,
                "error": str(e)
            }
            await self.hostdid_websocket.send(json.dumps(error_response))
```

## 5. 复杂场景解决方案：反向直连

### 5.1 适用场景
对于以下复杂场景，基础代理方案存在限制：
- **大文件传输**：文件大小超过WebSocket消息限制
- **流式响应**：SSE、实时数据流等
- **实时通信**：WebSocket代理、低延迟要求

### 5.2 反向直连机制
**核心思路**：A通过hostdid代理告诉C建立反向连接，后续复杂通信走反向通道

#### 协商流程
```python
# 1. A通过hostdid代理发起反向连接协商
context = {
    "caller_did": "did-a",
    "target_did": "hostdid-c", 
    "request_url": "api/hostdid-c/setup_reverse_connection",
    "method": "POST",
    "json_data": {
        "reverse_endpoint": "https://A的公网地址:端口/reverse_callback",
        "session_id": "unique_session_id",
        "connection_type": "large_file|streaming|realtime",
        "encryption_key": "shared_session_key"
    }
}

# 2. C收到请求后建立反向连接
async def setup_reverse_connection(request_data):
    reverse_endpoint = request_data["reverse_endpoint"]
    session_id = request_data["session_id"]
    
    # C主动连接A
    reverse_connection = await establish_reverse_connection(
        reverse_endpoint, 
        session_id,
        encryption_key=request_data["encryption_key"]
    )
    
    # 保持长连接用于后续通信
    self.reverse_connections[session_id] = reverse_connection

# 3. 后续复杂通信走反向通道
if is_complex_request(request):
    if session_id in active_reverse_connections:
        return await send_via_reverse_connection(session_id, request)
    else:
        await negotiate_reverse_connection(hostdid)
        return await send_via_reverse_connection(session_id, request)
```

### 5.3 实现要点
- **连接管理**：反向连接的建立、维护和重连
- **会话隔离**：多个A客户端的会话独立管理
- **安全保证**：反向连接仍使用DID加密
- **降级机制**：反向连接失败时自动降级到代理模式

## 6. 安全机制设计

### 6.1 身份验证
- **hostdid私钥签名**：C用hostdid私钥签名注册声明
- **DID文档验证**：B验证hostdid的有效性和签名
- **双向认证**：A和C之间的双向身份确认

### 6.2 端到端加密
- **传输密钥X**：C为每个A生成独立的对称加密密钥
- **公钥加密**：用A的公钥加密传输密钥X
- **对称加密**：用密钥X加密实际的通信内容

### 6.3 防攻击机制
- **重放攻击防护**：时间戳和nonce验证
- **中间人攻击防护**：完整的签名验证链
- **密钥轮换**：定期更新传输密钥

## 7. 风险评估与缓解策略

### 7.1 性能风险
**风险**：
- 双重加密/解密开销
- WebSocket消息序列化开销
- 网络延迟增加

**缓解策略**：
- 使用高效的对称加密算法（AES-GCM）
- 消息压缩（gzip）
- 连接池和长连接复用
- 性能监控和告警

### 7.2 可靠性风险
**风险**：
- WebSocket连接断开导致请求失败
- B服务器单点故障
- 消息丢失或重复

**缓解策略**：
- 自动重连机制
- 请求重试和幂等性保证
- B服务器集群部署
- 消息确认机制

### 7.3 安全风险
**风险**：
- 密钥泄露风险
- 重放攻击
- 时序攻击

**缓解策略**：
- 密钥定期轮换
- 时间戳和nonce防重放
- 请求频率限制
- 审计日志

### 7.4 扩展性风险
**风险**：
- B服务器压力过大
- 大量并发连接管理
- 内存和带宽消耗

**缓解策略**：
- 水平扩展B服务器
- 负载均衡和流量控制
- 连接池优化
- 反向直连分流

## 8. 方案适用性分析

### 8.1 适用场景 ✓
- **标准API调用**：JSON请求/响应，数据量适中
- **安全要求高**：需要端到端加密的场景
- **内网服务暴露**：C在内网/移动网络环境
- **中小规模部署**：并发量和数据量在合理范围内

### 8.2 不适用场景 ✗
- **超大文件传输**：单次传输超过100MB的文件
- **极高并发**：同时处理数千个并发请求
- **超低延迟**：对延迟要求极其苛刻的场景
- **复杂协议代理**：需要代理复杂的二进制协议

### 8.3 配套解决方案
- **大文件传输**：提供专门的文件传输服务或反向直连
- **高并发场景**：B服务器集群和负载均衡
- **低延迟需求**：反向直连或专用通道
- **复杂协议**：协议转换或专用代理

## 9. 实施策略

### 9.1 渐进式实施
1. **第一阶段**：基础hostdid代理功能（支持标准HTTP请求）
2. **第二阶段**：反向直连协商机制
3. **第三阶段**：性能优化和监控
4. **第四阶段**：高可用和扩展性增强

### 9.2 兼容性保证
- 保持现有API完全兼容
- 提供配置开关控制功能启用
- 支持降级到直连模式
- 向后兼容现有的认证机制

### 9.3 监控和运维
#### 关键指标
- 传输数据大小分布
- 加密/解密耗时
- WebSocket连接稳定性
- 端到端响应时间
- 反向连接成功率

#### 告警机制
- 大数据传输告警
- 连接异常告警
- 性能阈值告警
- 安全事件告警

## 10. 讨论细节总结

### 10.1 方案演进过程
我们的讨论经历了以下几个阶段的方案演进：

#### 初始方案：完整Context加密传输
- **核心思路**：A组装完整的AuthenticationContext，用传输密钥X加密，通过B的WebSocket传递给C
- **优点**：实现简单，端到端加密，B完全不知道内容
- **问题**：大数据传输开销大，不支持流式响应，调试复杂

#### 替代方案探索
1. **混合隧道方案**：被否决，B压力太大
2. **智能代理网关方案**：被否决，A和C的秘密对B不透明
3. **基于QUIC的方案**：被否决，ABC都要大改动
4. **Group Runner协作方案**：作为补充方案，适合特定协作场景

#### 最终方案：hostdid代理 + 反向直连
- **基础通信**：保持原有的加密Context传输方案
- **复杂场景**：通过反向直连处理大文件、流式、实时通信
- **优势**：简单实用，性能优化，安全性保持，网络适应性强

### 10.2 关键技术决策
1. **端到端加密不妥协**：始终坚持B无法看到明文数据的原则
2. **原封不动传递**：Context完整加密传输，保持请求语义
3. **双阶段认证**：密钥协商 + 加密通信的安全机制
4. **混合通信模式**：标准代理 + 反向直连的灵活组合

### 10.3 实现细节确认
- **A端**：在`auth_client.py`中实现hostdid检测和双阶段认证
- **B端**：在`router_host.py`中实现hostdid代理路由和WebSocket管理
- **C端**：在`anp_user.py`中实现WebSocket客户端和加密处理
- **反向直连**：通过hostdid代理协商，C主动连接A建立直连通道

### 10.4 风险评估结论
- **性能风险**：可接受，有缓解策略
- **安全风险**：可控，有完整的防护机制
- **可靠性风险**：可管理，有重连和降级机制
- **适用性限制**：明确定义适用和不适用场景

### 10.5 未来扩展方向
- 支持更多的加密算法和安全协议
- 实现智能路由和负载均衡算法
- 集成更完善的监控和运维工具
- 探索更高效的传输优化方案

## 11. 总结

本设计方案通过hostdid代理架构实现了内网服务的安全对外暴露，在保证端到端加密的前提下提供了灵活的通信方式。通过基础代理处理标准API调用，通过反向直连处理复杂场景，形成了一个完整的解决方案。

该方案适合中小规模的分布式智能体系统部署，特别是对安全性要求较高、网络环境复杂的场景。通过渐进式实施和完善的监控机制，可以确保方案的稳定性和可扩展性。

**核心价值**：
- 解决内网服务安全暴露的根本问题
- 提供端到端加密的安全保障
- 支持多种通信场景的灵活处理
- 保持与现有架构的良好兼容性
