# 双向Token体系设计

## 1. 概述

### 1.1 当前认证体系的问题

当前的ANP认证体系存在以下问题：
- Token传输过程中缺乏额外的安全保护
- 缺乏对称密钥交换机制
- 双向认证中的密钥管理不够完善
- **存在重放攻击风险**
- **后续请求认证计算开销大**
- **缺乏点对点DID绑定验证**

### 1.2 双向Token体系的优势

新的双向Token体系将提供：
- **安全的密钥交换**: 使用公钥加密传输对称密钥
- **防重放攻击**: 基于对称密钥的时间戳和随机数机制
- **高效认证**: 避免每次请求都使用非对称加密
- **点对点DID绑定**: 确保req_did和resp_did的严格绑定验证
- **增强的通信安全**: 为后续通信提供对称加密基础
- **向后兼容**: 不影响现有的单向认证流程
- **密钥管理**: 完整的密钥生命周期管理

### 1.3 设计目标

- 在现有DID认证基础上增加对称密钥交换
- 确保密钥传输的安全性
- 实现严格的DID对绑定验证
- 提供完整的密钥管理机制
- 保持系统的向后兼容性

## 2. 技术架构

### 2.1 整体流程

```
客户端(req_did) ←→ 服务端(resp_did)
         ↓
发送DID认证请求
         ↓
服务端验证并生成对称密钥
         ↓
使用req_did公钥加密对称密钥
         ↓
返回token + 加密的对称密钥
         ↓
客户端使用私钥解密对称密钥
         ↓
存储对称密钥供后续使用（绑定DID对）
```

### 2.2 密钥生成机制

- **对称密钥**: 使用`secrets.token_hex(32)`生成256位密钥
- **加密算法**: RSA-OAEP with SHA-256
- **存储格式**: Base64编码的加密密钥
- **DID绑定**: 每个对称密钥严格绑定到特定的req_did和resp_did对

### 2.3 数据结构

#### Token数据结构（扩展）
```json
{
  "req_did": "did:wba:...",
  "resp_did": "did:wba:...",
  "comments": "open for req_did",
  "resp_did_token_key": "生成的对称密钥",
  "exp": "过期时间"
}
```

#### 响应数据结构（扩展）
```json
{
  "access_token": "JWT token",
  "token_type": "bearer",
  "req_did": "did:wba:...",
  "resp_did": "did:wba:...",
  "resp_did_auth_header": {...},
  "resp_did_token_key": "加密后的对称密钥"
}
```
## 3. 防重放认证机制设计

### 3.1 认证令牌结构

```json
{
  "req_did": "did:wba:client:123",
  "resp_did": "did:wba:anp_server:456", 
  "token": "原始JWT token",
  "timestamp": 1703123456789,
  "nonce": "random_32_bytes_hex",
  "request_hash": "可选的请求数据哈希",
  "signature": "HMAC-SHA256签名"
}
```

### 3.2 签名数据结构

签名计算包含的字段（按字典序）：

```json
{
  "nonce": "random_32_bytes_hex",
  "req_did": "did:wba:client:123",
  "request_hash": "optional_request_hash", 
  "resp_did": "did:wba:anp_server:456",
  "timestamp": 1703123456789,
  "token": "原始JWT token"
}
```

### 3.3 认证流程

```
客户端请求 → 服务端验证
     ↓
1. 生成时间戳和随机数
     ↓
2. 构造认证载荷（包含req_did和resp_did）
     ↓
3. 使用对称密钥HMAC签名
     ↓
4. 发送请求 + 认证头
     ↓
5. 服务端验证DID对、时间戳、随机数、签名
     ↓
6. 防重放检查通过 → 处理请求
```
## 4. 实现方案

### 4.1 服务端改进 - _generate_wba_auth_response()

#### 4.1.1 生成对称密钥

```python
async def _generate_wba_auth_response(did, is_two_way_auth, resp_did):
    resp_did_agent = ANPUser.from_did(resp_did)
    
    # 生成256位对称密钥
    import secrets
    resp_did_token_key = secrets.token_hex(32)
    
    # 将对称密钥加入token数据
    config = get_global_config()
    expiration_time = config.anp_sdk.token_expire_time
    access_token = create_access_token(
        resp_did_agent.jwt_private_key_path,
        data={
            "req_did": did, 
            "resp_did": resp_did, 
            "comments": "open for req_did",
            "resp_did_token_key": resp_did_token_key  # 新增对称密钥
        },
        expires_delta=expiration_time
    )
    resp_did_agent.contact_manager.store_token_to_remote(did, access_token, expiration_time)
```

#### 4.1.2 加密对称密钥

```python
    # 使用req_did的公钥加密对称密钥
    encrypted_token_key = None
    if is_two_way_auth:
        try:
            # 获取req_did的用户数据
            from ..anp_sdk_user_data import LocalUserDataManager
            user_data_manager = LocalUserDataManager()
            req_user_data = user_data_manager.get_user_data(did)
            
            if req_user_data:
                # 读取req_did的公钥
                from cryptography.hazmat.primitives import serialization
                with open(req_user_data.did_public_key_file_path, "rb") as f:
                    public_key_pem = f.read()
                public_key = serialization.load_pem_public_key(public_key_pem)
                
                # 使用RSA-OAEP加密对称密钥
                from cryptography.hazmat.primitives.asymmetric import padding
                from cryptography.hazmat.primitives import hashes
                import base64
                
                encrypted_key_bytes = public_key.encrypt(
                    resp_did_token_key.encode('utf-8'),
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                encrypted_token_key = base64.b64encode(encrypted_key_bytes).decode('utf-8')
                
                # 存储对称密钥（绑定到特定的req_did）
                resp_did_agent.contact_manager.store_symmetric_key_for_caller(did, resp_did_token_key)
                
                logger.debug(f"成功加密对称密钥给 {did}")
            else:
                logger.warning(f"未找到req_did {did} 的用户数据，无法加密对称密钥")
        except Exception as e:
            logger.error(f"加密对称密钥失败: {e}")
#### 4.1.3 返回扩展响应

```python
    # 生成resp_did的认证头（原有逻辑）
    resp_did_auth_header = None
    if resp_did and resp_did != "没收到":
        # ... 原有的认证头生成逻辑 ...
    
    # 返回扩展的响应数据
    if is_two_way_auth:
        return [
            {
                "access_token": access_token,
                "token_type": "bearer",
                "req_did": did,
                "resp_did": resp_did,
                "resp_did_auth_header": resp_did_auth_header,
                "resp_did_token_key": encrypted_token_key  # 新增加密的对称密钥
            }
        ]
    else:
        return f"bearer {access_token}"
```
### 4.2 客户端改进 - _execute_wba_auth_flow()

#### 4.2.1 解析加密的对称密钥

```python
# 在双向认证成功的处理逻辑中添加
if auth_value != "单向认证":
    response_auth_header = json.loads(response_auth_header.get("Authorization"))
    response_data_obj = response_auth_header[0]
    
    # 获取加密的对称密钥
    encrypted_token_key = response_data_obj.get("resp_did_token_key")
    
    # 解密对称密钥
    decrypted_token_key = None
    if encrypted_token_key:
        try:
            decrypted_token_key = await _decrypt_token_key(encrypted_token_key, context.caller_did)
            if decrypted_token_key:
                logger.debug(f"成功解密对称密钥")
                # 存储对称密钥供后续使用（绑定到特定的resp_did）
                caller_agent.contact_manager.store_symmetric_key(context.target_did, decrypted_token_key)
            else:
                logger.warning("对称密钥解密失败")
        except Exception as e:
            logger.error(f"处理对称密钥时出错: {e}")
    
    # 继续原有的认证头验证逻辑
    response_auth_header = response_data_obj.get("resp_did_auth_header")
    response_auth_header = response_auth_header.get("Authorization")
    if not await _verify_response_auth_header(response_auth_header):
        message = f"接收方DID认证头验证失败! 状态: {status_code}\n响应: {response_data}"
        return status_code, response_data, message, False
    
    caller_agent.contact_manager.store_token_from_remote(context.target_did, token)
    message = f"DID双向认证成功! 已保存 {context.target_did} 颁发的token和对称密钥"
    return status_code, response_data, message, True
#### 4.2.2 对称密钥解密函数

```python
async def _decrypt_token_key(encrypted_token_key: str, caller_did: str) -> Optional[str]:
    """解密对称密钥
    
    Args:
        encrypted_token_key: Base64编码的加密对称密钥
        caller_did: 调用方DID
        
    Returns:
        解密后的对称密钥，失败时返回None
    """
    try:
        from ..anp_sdk_user_data import LocalUserDataManager
        user_data_manager = LocalUserDataManager()
        user_data = user_data_manager.get_user_data(caller_did)
        
        if not user_data:
            logger.error(f"未找到caller_did {caller_did} 的用户数据")
            return None
        
        # 读取私钥
        from cryptography.hazmat.primitives import serialization
        with open(user_data.did_private_key_file_path, "rb") as f:
            private_key_pem = f.read()
        private_key = serialization.load_pem_private_key(private_key_pem, password=None)
        
        # 解密对称密钥
        from cryptography.hazmat.primitives.asymmetric import padding
        from cryptography.hazmat.primitives import hashes
        import base64
        
        encrypted_key_bytes = base64.b64decode(encrypted_token_key)
        decrypted_key_bytes = private_key.decrypt(
            encrypted_key_bytes,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted_key_bytes.decode('utf-8')
        
    except Exception as e:
        logger.error(f"解密对称密钥失败: {e}")
        return None
```

### 4.3 客户端认证头生成

```python
class AuthenticatedRequestClient:
    def __init__(self, caller_did: str):
        self.caller_did = caller_did
        self.caller_agent = ANPUser.from_did(caller_did)
    
    async def create_auth_header(self, target_did: str, request_data: dict = None) -> dict:
        """创建防重放认证头
        
        Args:
            target_did: 目标DID (resp_did)
            request_data: 请求数据（可选，用于请求完整性保护）
            
        Returns:
            认证头字典
        """
        # 获取存储的token和对称密钥
        token = self.caller_agent.contact_manager.get_token_from_remote(target_did)
        symmetric_key = self.caller_agent.contact_manager.get_symmetric_key(target_did)
        
        if not token or not symmetric_key:
            raise ValueError(f"未找到 {target_did} 的token或对称密钥，请先进行认证")
        
        # 生成时间戳和随机数
        import time
        import secrets
        timestamp = int(time.time() * 1000)  # 毫秒级时间戳
        nonce = secrets.token_hex(16)  # 32字节随机数
        
        # 构造认证载荷（包含req_did和resp_did）
        auth_payload = {
            "req_did": self.caller_did,      # 请求方DID
            "resp_did": target_did,          # 响应方DID  
            "token": token,
            "timestamp": timestamp,
            "nonce": nonce
        }
        
        # 如果有请求数据，加入完整性保护
        if request_data:
            import json
            import hashlib
            request_hash = hashlib.sha256(
                json.dumps(request_data, sort_keys=True).encode()
            ).hexdigest()
            auth_payload["request_hash"] = request_hash
        
        # 使用对称密钥生成HMAC签名（包含req_did和resp_did）
        signature = self._generate_hmac_signature(auth_payload, symmetric_key)
        auth_payload["signature"] = signature
        
        return auth_payload
    
    def _generate_hmac_signature(self, payload: dict, symmetric_key: str) -> str:
        """生成HMAC签名
        
        签名数据包含req_did和resp_did，确保点对点验证安全性
        """
        import hmac
        import hashlib
        import json
        
        # 排除signature字段，对其他字段按字典序排序后生成签名
        sign_data = {k: v for k, v in payload.items() if k != "signature"}
        
        # 确保字段按字典序排列，保证签名一致性
        sign_string = json.dumps(sign_data, sort_keys=True, separators=(',', ':'))
        
        # 使用HMAC-SHA256生成签名
        signature = hmac.new(
            symmetric_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"生成签名 - req_did: {sign_data.get('req_did')}, "
                    f"resp_did: {sign_data.get('resp_did')}, "
                    f"签名数据: {sign_string[:100]}...")
        
        return signature
    
    async def send_authenticated_request(self, target_url: str, target_did: str, 
                                       method: str = "GET", data: dict = None) -> tuple:
        """发送带认证的请求
        
        Args:
            target_url: 目标URL
            target_did: 目标DID
            method: HTTP方法
            data: 请求数据
            
        Returns:
            (status_code, response_data, success)
        """
        try:
            # 创建认证头
            auth_header = await self.create_auth_header(target_did, data)
            
            # 构造请求头
            headers = {
                "Authorization": f"ANP-Auth {json.dumps(auth_header)}",
                "Content-Type": "application/json"
            }
            
            # 发送请求
            import httpx
            async with httpx.AsyncClient() as client:
                if method.upper() == "GET":
                    response = await client.get(target_url, headers=headers)
                elif method.upper() == "POST":
                    response = await client.post(target_url, headers=headers, json=data)
                else:
                    response = await client.request(method, target_url, headers=headers, json=data)
                
                return response.status_code, response.json(), response.status_code == 200
                
        except Exception as e:
            logger.error(f"发送认证请求失败: {e}")
            return 500, {"error": str(e)}, False
```
### 4.4 服务端认证验证

```python
class AuthenticationVerifier:
    def __init__(self):
        self.nonce_cache = {}  # 简单的内存缓存，生产环境应使用Redis
        self.cache_ttl = 300  # 5分钟TTL

    async def verify_auth_header(self, auth_header_str: str,
                                 expected_resp_did: str,  # 新增：期望的响应方DID
                                 request_data: dict = None) -> tuple:
        """验证认证头
        
        Args:
            auth_header_str: 认证头字符串
            expected_resp_did: 期望的响应方DID（当前服务的DID）
            request_data: 请求数据
            
        Returns:
            (is_valid, caller_did, error_message)
        """
        try:
            # 解析认证头
            if not auth_header_str.startswith("ANP-Auth "):
                return False, None, "无效的认证头格式"

            auth_data_str = auth_header_str[9:]  # 移除 "ANP-Auth " 前缀
            auth_data = json.loads(auth_data_str)

            # 提取认证信息
            req_did = auth_data.get("req_did")  # 请求方DID
            resp_did = auth_data.get("resp_did")  # 响应方DID
            token = auth_data.get("token")
            timestamp = auth_data.get("timestamp")
            nonce = auth_data.get("nonce")
            signature = auth_data.get("signature")
            request_hash = auth_data.get("request_hash")

            # 基本字段验证
            if not all([req_did, resp_did, token, timestamp, nonce, signature]):
                return False, None, "认证头字段不完整"

            # **关键验证：确保resp_did匹配当前服务**
            if resp_did != expected_resp_did:
                logger.warning(f"DID不匹配 - 期望: {expected_resp_did}, 实际: {resp_did}")
                return False, None, f"响应方DID不匹配，期望: {expected_resp_did}, 实际: {resp_did}"

            # 时间戳验证（防重放）
            import time
            current_time = int(time.time() * 1000)
            time_diff = abs(current_time - timestamp)

            if time_diff > 300000:  # 5分钟窗口
                return False, None, "请求时间戳过期"

            # 随机数验证（防重放）- 包含DID对绑定
            nonce_key = f"{req_did}:{resp_did}:{nonce}"
            if nonce_key in self.nonce_cache:
                return False, None, "检测到重放攻击"

            # **验证JWT token中的DID绑定**
            if not await self._verify_jwt_token(token, req_did, resp_did):
                return False, None, "JWT token验证失败或DID不匹配"

            # **获取针对特定DID对的对称密钥**
            symmetric_key = await self._get_symmetric_key(req_did, resp_did)
            if not symmetric_key:
                return False, None, f"未找到 {req_did} -> {resp_did} 的对称密钥"

            # **验证HMAC签名（包含DID对验证）**
            expected_signature = self._generate_hmac_signature(
                {k: v for k, v in auth_data.items() if k != "signature"},
                symmetric_key
            )

            if not hmac.compare_digest(signature, expected_signature):
                logger.warning(f"签名验证失败 - req_did: {req_did}, resp_did: {resp_did}")
                return False, None, "签名验证失败"

            # 验证请求完整性（如果提供）
            if request_data and request_hash:
                import hashlib
                actual_hash = hashlib.sha256(
                    json.dumps(request_data, sort_keys=True).encode()
                ).hexdigest()

                if not hmac.compare_digest(request_hash, actual_hash):
                    return False, None, "请求数据完整性验证失败"

            # 缓存随机数（防重放）- 使用DID对+随机数作为key
            self.nonce_cache[nonce_key] = current_time
            self._cleanup_nonce_cache()

            logger.debug(f"认证成功 - req_did: {req_did}, resp_did: {resp_did}")
            return True, req_did, "认证成功"

        except Exception as e:
            logger.error(f"认证验证失败: {e}")
            return False, None, f"认证验证异常: {str(e)}"

    def _generate_hmac_signature(self, payload: dict, symmetric_key: str) -> str:
        """生成HMAC签名（与客户端保持一致）"""
        import hmac
        import hashlib
        import json

        # 确保字段按字典序排列
        sign_string = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        signature = hmac.new(
            symmetric_key.encode('utf-8'),
            sign_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return signature

    async def _verify_jwt_token(self, token: str, req_did: str, resp_did: str) -> bool:
        """验证JWT token中的DID绑定"""
        try:
            from anp_server import verify_token
            payload = verify_token(token)

            # **关键验证：确保token中的DID对匹配**
            token_req_did = payload.get("req_did")
            token_resp_did = payload.get("resp_did")

            if token_req_did != req_did or token_resp_did != resp_did:
                logger.warning(f"Token中DID不匹配 - "
                               f"Token: {token_req_did}->{token_resp_did}, "
                               f"请求: {req_did}->{resp_did}")
                return False

            return True
        except Exception as e:
            logger.error(f"JWT token验证失败: {e}")
            return False

    async def _get_symmetric_key(self, req_did: str, resp_did: str) -> Optional[str]:
        """获取针对特定DID对的对称密钥"""
        try:
            # 从响应方DID的用户数据中获取为请求方DID生成的对称密钥
            resp_agent = ANPUser.from_did(resp_did)
            symmetric_key = resp_agent.contact_manager.get_symmetric_key_for_caller(req_did)

            if symmetric_key:
                logger.debug(f"找到对称密钥 - {req_did} -> {resp_did}")
            else:
                logger.warning(f"未找到对称密钥 - {req_did} -> {resp_did}")

            return symmetric_key
        except Exception as e:
            logger.error(f"获取对称密钥失败: {e}")
            return None

    def _cleanup_nonce_cache(self):
        """清理过期的随机数缓存"""
        import time
        current_time = int(time.time() * 1000)
        expired_keys = [
            key for key, timestamp in self.nonce_cache.items()
            if current_time - timestamp > self.cache_ttl * 1000
        ]
        for key in expired_keys:
            del self.nonce_cache[key]
```

### 4.5 中间件集成

```python
# 在 anp_auth_middleware.py 中集成
async def auth_middleware(request: Request, call_next, auth_method: str = "wba"):
    # ... 现有代码 ...

    # 检查是否使用新的ANP-Auth认证
    auth_header = request.headers.get("authorization", "")

    if auth_header.startswith("ANP-Auth "):
        # 使用新的防重放认证机制
        verifier = AuthenticationVerifier()

        # **获取当前服务的DID（响应方DID）**
        current_did = await _get_current_service_did(request)
        if not current_did:
            return JSONResponse(
                status_code=500,
                content={"error": "无法确定当前服务DID"}
            )

        # 获取请求数据用于完整性验证
        request_data = None
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    request_data = json.loads(body)
            except:
                pass

        # **验证认证头（包含DID对验证）**
        is_valid, req_did, error_msg = await verifier.verify_auth_header(
            auth_header, current_did, request_data
        )

        if is_valid:
            # 认证成功，设置请求上下文
            request.state.authenticated = True
            request.state.req_did = req_did
            request.state.resp_did = current_did
            request.state.auth_method = "anp_symmetric"

            logger.debug(f"ANP对称认证成功 - {req_did} -> {current_did}")
            response = await call_next(request)
            return response
        else:
            # 认证失败
            logger.warning(f"ANP对称认证失败: {error_msg}")
            return JSONResponse(
                status_code=401,
                content={"error": "Authentication failed", "message": error_msg}
            )

    # 继续现有的认证逻辑
    # ... 现有代码 ...


async def _get_current_service_did(request: Request) -> Optional[str]:
    """获取当前服务的DID"""
    try:
        # 方法1: 从路径中提取DID
        path = request.url.path
        if "/agent/api/" in path:
            # 路径格式: /agent/api/{did}/...
            parts = path.split("/")
            if len(parts) >= 4:
                return parts[3]

        # 方法2: 从服务器配置中获取默认DID
        from anp_server.anp_server import ANP_Server
        server = ANP_Server.instance
        if server and hasattr(server, 'router') and server.router_agent.local_agents:
            # 返回第一个本地智能体的DID
            return next(iter(server.router_agent.local_agents.keys()))

        # 方法3: 从请求头中获取（如果客户端提供）
        target_did = request.headers.get("X-Target-DID")
        if target_did:
            return target_did

        return None
    except Exception as e:
        logger.error(f"获取当前服务DID失败: {e}")
        return None


### 4.6 联系人管理器扩展

```python


class ContactManager:
    def store_symmetric_key_for_caller(self, req_did: str, symmetric_key: str):
        """为特定请求方DID存储对称密钥（服务端使用）
        
        Args:
            req_did: 请求方DID
            symmetric_key: 对称密钥
        """
        if not hasattr(self.user_data, 'caller_symmetric_keys'):
            self.user_data.caller_symmetric_keys = {}

        from datetime import datetime, timezone
        self.user_data.caller_symmetric_keys[req_did] = {
            "key": symmetric_key,
            "req_did": req_did,
            "resp_did": self.user_data.did,  # 当前用户的DID作为响应方
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used": datetime.now(timezone.utc).isoformat(),
            "usage_count": 0
        }

        self._save_symmetric_keys()
        logger.debug(f"已为请求方 {req_did} -> 响应方 {self.user_data.did} 存储对称密钥")

    def get_symmetric_key_for_caller(self, req_did: str) -> Optional[str]:
        """获取为特定请求方DID生成的对称密钥（服务端使用）
        
        Args:
            req_did: 请求方DID
            
        Returns:
            对称密钥，不存在时返回None
        """
        caller_keys = getattr(self.user_data, 'caller_symmetric_keys', {})
        key_info = caller_keys.get(req_did)

        if key_info:
            # 验证DID对匹配
            if key_info.get("resp_did") != self.user_data.did:
                logger.warning(f"DID对不匹配 - 存储的resp_did: {key_info.get('resp_did')}, "
                               f"当前DID: {self.user_data.did}")
                return None

            # 更新使用统计
            from datetime import datetime, timezone
            key_info["last_used"] = datetime.now(timezone.utc).isoformat()
            key_info["usage_count"] = key_info.get("usage_count", 0) + 1
            self._save_symmetric_keys()

            logger.debug(f"获取对称密钥成功 - {req_did} -> {self.user_data.did}")
            return key_info.get("key")

        logger.warning(f"未找到对称密钥 - {req_did} -> {self.user_data.did}")
        return None

    def store_symmetric_key(self, resp_did: str, symmetric_key: str):
        """存储对称密钥（客户端使用）
        
        Args:
            resp_did: 响应方DID
            symmetric_key: 对称密钥
        """
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)

        # 确保symmetric_keys属性存在
        if not hasattr(self.user_data, 'symmetric_keys'):
            self.user_data.symmetric_keys = {}

        self.user_data.symmetric_keys[resp_did] = {
            "key": symmetric_key,
            "req_did": self.user_data.did,  # 当前用户的DID作为请求方
            "resp_did": resp_did,
            "created_at": now.isoformat(),
            "last_used": now.isoformat(),
            "usage_count": 0
        }

        # 持久化存储
        self._save_symmetric_keys()
        logger.debug(f"已存储对称密钥 - {self.user_data.did} -> {resp_did}")

    def get_symmetric_key(self, resp_did: str) -> Optional[str]:
        """获取对称密钥（客户端使用）
        
        Args:
            resp_did: 响应方DID
            
        Returns:
            对称密钥，不存在时返回None
        """
        symmetric_keys = getattr(self.user_data, 'symmetric_keys', {})
        key_info = symmetric_keys.get(resp_did)

        if key_info:
            # 验证DID对匹配
            if key_info.get("req_did") != self.user_data.did:
                logger.warning(f"DID对不匹配 - 存储的req_did: {key_info.get('req_did')}, "
                               f"当前DID: {self.user_data.did}")
                return None

            # 更新最后使用时间
            from datetime import datetime, timezone
            key_info["last_used"] = datetime.now(timezone.utc).isoformat()
            key_info["usage_count"] = key_info.get("usage_count", 0) + 1
            self._save_symmetric_keys()

            logger.debug(f"获取对称密钥成功 - {self.user_data.did} -> {resp_did}")
            return key_info.get("key")

        logger.warning(f"未找到对称密钥 - {self.user_data.did} -> {resp_did}")
        return None

    def revoke_symmetric_key(self, remote_did: str):
        """撤销对称密钥
        
        Args:
            remote_did: 远程DID
        """
        symmetric_keys = getattr(self.user_data, 'symmetric_keys', {})
        if remote_did in symmetric_keys:
            del symmetric_keys[remote_did]
            self._save_symmetric_keys()
            logger.debug(f"已撤销对称密钥给 {remote_did}")

    def _save_symmetric_keys(self):
        """持久化对称密钥数据"""
        # 这里可以实现具体的持久化逻辑
        # 例如保存到文件或数据库
        pass
```

## 5. 安全增强特性

### 5.1 DID对绑定验证

```python
def verify_did_pair_binding(req_did: str, resp_did: str, token: str, symmetric_key: str) -> bool:
    """验证DID对绑定的完整性
    
    Args:
        req_did: 请求方DID
        resp_did: 响应方DID  
        token: JWT token
        symmetric_key: 对称密钥
        
    Returns:
        验证是否通过
    """
    try:
        # 1. 验证token中的DID对
        payload = verify_token(token)
        if payload.get("req_did") != req_did or payload.get("resp_did") != resp_did:
            return False
        
        # 2. 验证对称密钥是否为该DID对生成
        # 这里可以加入额外的密钥验证逻辑
        
        # 3. 验证DID的有效性
        if not is_valid_did(req_did) or not is_valid_did(resp_did):
            return False
        
        return True
    except:
        return False
```

### 5.2 签名数据示例

```json
{
  "nonce": "a1b2c3d4e5f6789012345678",
  "req_did": "did:wba:client.example.com:9527:wba:user:alice",
  "request_hash": "sha256_hash_of_request_data",
  "resp_did": "did:wba:anp_server.example.com:8080:wba:service:api",
  "timestamp": 1703123456789,
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**HMAC签名计算**：
```
HMAC-SHA256(symmetric_key, JSON.stringify(sign_data, sort_keys=True))
```
### 5.3 防重放攻击
- **时间戳窗口**: 5分钟有效期
- **随机数缓存**: 防止相同随机数重复使用（包含DID对信息）
- **请求完整性**: 可选的请求数据哈希验证
- **DID对绑定**: 随机数缓存key包含完整的DID对信息

### 5.4 高效认证
- **对称加密**: HMAC-SHA256，比RSA快数百倍
- **缓存机制**: 对称密钥本地缓存，避免重复交换
- **批量验证**: 支持批量请求的高效验证

### 5.5 向后兼容
- **渐进式升级**: 新旧认证机制并存
- **自动降级**: 不支持对称密钥时自动使用原有机制
- **配置开关**: 可配置启用/禁用新认证机制
## 6. 安全考虑

### 6.1 加密算法选择
- **对称密钥生成**: 使用`secrets.token_hex(32)`生成256位密钥
- **非对称加密**: RSA-OAEP with SHA-256
- **填充方案**: OAEP (Optimal Asymmetric Encryption Padding)
- **哈希算法**: SHA-256

### 6.2 密钥管理

#### 6.2.1 密钥轮换策略
- 对称密钥应定期轮换（建议每24小时）
- 提供手动轮换接口
- 自动清理过期密钥

#### 6.2.2 密钥存储安全
- 对称密钥应加密存储在本地
- 使用用户的主密钥加密对称密钥
- 实现密钥的安全删除

### 6.3 错误处理

#### 6.3.1 加密失败处理
- 公钥不存在时的降级策略
- 加密失败时的错误日志
- 不影响原有认证流程

#### 6.3.2 解密失败处理
- 私钥不匹配时的处理
- 密钥格式错误的处理
- 优雅的错误恢复机制

### 6.4 日志安全
- 避免在日志中记录明文密钥
- 只记录密钥的哈希值或ID
- 敏感操作的审计日志
## 7. 性能对比

| 认证方式 | 客户端开销 | 服务端开销 | 网络开销 | 安全性 |
|---------|-----------|-----------|---------|--------|
| 原有JWT | 低 | 中等 | 低 | 中等（有重放风险） |
| 每次RSA签名 | 高 | 高 | 中等 | 高 |
| 对称密钥+HMAC | 低 | 低 | 低 | 高 |

## 8. 使用示例

### 8.1 完整的认证流程

```python
# 1. 双向认证获取对称密钥
req_did = "did:wba:client.example.com:9527:wba:user:alice"
resp_did = "did:wba:anp_server.example.com:8080:wba:service:api"

status, data, message, success = await send_authenticated_request(
    caller_agent=req_did,
    target_agent=resp_did,
    request_url="https://server.example.com/auth",
    use_two_way_auth=True
)

if success:
    print(f"认证成功 - {req_did} <-> {resp_did}")
    
    # 2. 使用对称密钥进行后续请求
    auth_client = AuthenticatedRequestClient(req_did)
    
    # 发送API请求（自动包含DID对验证）
    status, response, success = await auth_client.send_authenticated_request(
        target_url="https://server.example.com/api/secure-data",
        target_did=resp_did,
        method="POST",
        data={"query": "sensitive_data"}
    )
    
    if success:
        print("API调用成功，DID对验证通过")
    else:
        print("API调用失败，可能是DID对不匹配")
### 8.2 基本使用

```python
# 发送认证请求（客户端）
status, data, message, success = await send_authenticated_request(
    caller_agent="did:wba:localhost:9527:wba:user:abc123",
    target_agent="did:wba:example.com:8080:wba:service:def456",
    request_url="https://example.com/api/data",
    use_two_way_auth=True
)

if success:
    print(f"认证成功，已获取对称密钥")
    # 对称密钥已自动存储，可用于后续加密通信
```

### 8.3 获取对称密钥

```python
# 获取存储的对称密钥
caller_agent = ANPUser.from_did("did:wba:localhost:9527:wba:user:abc123")
symmetric_key = caller_agent.contact_manager.get_symmetric_key(
    "did:wba:example.com:8080:wba:service:def456"
)

if symmetric_key:
    print(f"对称密钥: {symmetric_key}")
    # 可用于AES加密等对称加密操作
```

### 8.4 服务端验证日志

```
[DEBUG] 生成签名 - req_did: did:wba:client:alice, resp_did: did:wba:server:api
[DEBUG] 找到对称密钥 - did:wba:client:alice -> did:wba:server:api  
[DEBUG] 认证成功 - req_did: did:wba:client:alice, resp_did: did:wba:server:api
[INFO] ANP对称认证成功 - did:wba:client:alice -> did:wba:server:api
```
## 9. 实施计划

### 9.1 第一阶段：基础实现
- [ ] 实现对称密钥生成
- [ ] 实现公钥加密功能
- [ ] 扩展服务端响应结构
- [ ] 基础测试用例

### 9.2 第二阶段：客户端集成
- [ ] 实现客户端解密功能
- [ ] 扩展联系人管理器
- [ ] 集成测试
- [ ] 错误处理完善

### 9.3 第三阶段：安全增强
- [ ] 密钥轮换机制
- [ ] 安全存储实现
- [ ] 审计日志系统
- [ ] 性能优化

### 9.4 第四阶段：生产部署
- [ ] 完整的测试覆盖
- [ ] 文档完善
- [ ] 监控和告警
- [ ] 生产环境部署
## 10. 测试策略

### 10.1 单元测试
- 对称密钥生成测试
- 加密/解密功能测试
- 错误处理测试

### 10.2 集成测试
- 端到端认证流程测试
- 多客户端并发测试
- 异常场景测试

### 10.3 安全测试
- 密钥泄露测试
- 中间人攻击测试
- 重放攻击测试

## 11. 配置参数

### 11.1 新增配置项

```yaml
anp_sdk:
  # 对称密钥配置
  symmetric_key:
    key_length: 32  # 密钥长度（字节）
    rotation_interval: 86400  # 轮换间隔（秒）
    max_usage_count: 1000  # 最大使用次数
    
  # 加密配置
  encryption:
    algorithm: "RSA-OAEP"
    hash_algorithm: "SHA-256"
    padding: "OAEP"
```

### 11.2 兼容性配置

```yaml
anp_sdk:
  # 向后兼容配置
  compatibility:
    enable_symmetric_key: true  # 是否启用对称密钥
    fallback_on_error: true     # 错误时是否降级
    log_key_operations: false   # 是否记录密钥操作日志
```

## 12. 总结

双向Token体系设计通过在现有DID认证基础上增加对称密钥交换机制，为ANP系统提供了更强的安全保障。该设计具有以下特点：

- **安全性**: 使用公钥加密确保对称密钥的安全传输
- **DID对绑定**: 严格的req_did和resp_did绑定验证
- **防重放**: 时间戳+随机数+HMAC签名三重保护
- **高性能**: HMAC比RSA快几百倍，适合高频请求
- **兼容性**: 不影响现有的认证流程
- **可扩展性**: 为未来的加密通信提供基础
- **可管理性**: 完整的密钥生命周期管理

通过分阶段实施，可以确保系统的稳定性和安全性，同时为用户提供更好的安全体验。关键的DID对绑定验证确保了点对点通信的安全性，防止了密钥混用和身份冒充攻击。
