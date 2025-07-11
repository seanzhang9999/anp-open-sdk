# 双向Token体系设计

## 1. 概述

### 1.1 当前认证体系的问题

当前的ANP认证体系存在以下问题：
- Token传输过程中缺乏额外的安全保护
- 缺乏对称密钥交换机制
- 双向认证中的密钥管理不够完善
- 无法实现更高级的加密通信

### 1.2 双向Token体系的优势

新的双向Token体系将提供：
- **安全的密钥交换**: 使用公钥加密传输对称密钥
- **增强的通信安全**: 为后续通信提供对称加密基础
- **向后兼容**: 不影响现有的单向认证流程
- **密钥管理**: 完整的密钥生命周期管理

### 1.3 设计目标

- 在现有DID认证基础上增加对称密钥交换
- 确保密钥传输的安全性
- 提供完整的密钥管理机制
- 保持系统的向后兼容性

## 2. 技术架构

### 2.1 整体流程

```
客户端(req_did) ←→ 服务端(resp_did)
     ↓
1. 发送DID认证请求
     ↓
2. 服务端验证并生成对称密钥
     ↓
3. 使用req_did公钥加密对称密钥
     ↓
4. 返回token + 加密的对称密钥
     ↓
5. 客户端使用私钥解密对称密钥
     ↓
6. 存储对称密钥供后续使用
```

### 2.2 密钥生成机制

- **对称密钥**: 使用`secrets.token_hex(32)`生成256位密钥
- **加密算法**: RSA-OAEP with SHA-256
- **存储格式**: Base64编码的加密密钥

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

## 3. 实现方案

### 3.1 服务端改进 - `_generate_wba_auth_response()`

#### 3.1.1 生成对称密钥
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

#### 3.1.2 加密对称密钥
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
                logger.debug(f"成功加密对称密钥给 {did}")
            else:
                logger.warning(f"未找到req_did {did} 的用户数据，无法加密对称密钥")
        except Exception as e:
            logger.error(f"加密对称密钥失败: {e}")
```

#### 3.1.3 返回扩展响应
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

### 3.2 客户端改进 - `_execute_wba_auth_flow()`

#### 3.2.1 解析加密的对称密钥
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
                # 存储对称密钥供后续使用
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
```

#### 3.2.2 对称密钥解密函数
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

### 3.3 联系人管理器扩展

#### 3.3.1 对称密钥存储
```python
class ContactManager:
    def store_symmetric_key(self, remote_did: str, symmetric_key: str):
        """存储对称密钥
        
        Args:
            remote_did: 远程DID
            symmetric_key: 对称密钥
        """
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        
        # 确保symmetric_keys属性存在
        if not hasattr(self.user_data, 'symmetric_keys'):
            self.user_data.symmetric_keys = {}
        
        self.user_data.symmetric_keys[remote_did] = {
            "key": symmetric_key,
            "created_at": now.isoformat(),
            "last_used": now.isoformat(),
            "usage_count": 0
        }
        
        # 持久化存储
        self._save_symmetric_keys()
        logger.debug(f"已存储对称密钥给 {remote_did}")

    def get_symmetric_key(self, remote_did: str) -> Optional[str]:
        """获取对称密钥
        
        Args:
            remote_did: 远程DID
            
        Returns:
            对称密钥，不存在时返回None
        """
        symmetric_keys = getattr(self.user_data, 'symmetric_keys', {})
        key_info = symmetric_keys.get(remote_did)
        
        if key_info:
            # 更新最后使用时间
            from datetime import datetime, timezone
            key_info["last_used"] = datetime.now(timezone.utc).isoformat()
            key_info["usage_count"] = key_info.get("usage_count", 0) + 1
            self._save_symmetric_keys()
            return key_info.get("key")
        
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

## 4. 安全考虑

### 4.1 加密算法选择

- **对称密钥生成**: 使用`secrets.token_hex(32)`生成256位密钥
- **非对称加密**: RSA-OAEP with SHA-256
- **填充方案**: OAEP (Optimal Asymmetric Encryption Padding)
- **哈希算法**: SHA-256

### 4.2 密钥管理

#### 4.2.1 密钥轮换策略
- 对称密钥应定期轮换（建议每24小时）
- 提供手动轮换接口
- 自动清理过期密钥

#### 4.2.2 密钥存储安全
- 对称密钥应加密存储在本地
- 使用用户的主密钥加密对称密钥
- 实现密钥的安全删除

### 4.3 错误处理

#### 4.3.1 加密失败处理
- 公钥不存在时的降级策略
- 加密失败时的错误日志
- 不影响原有认证流程

#### 4.3.2 解密失败处理
- 私钥不匹配时的处理
- 密钥格式错误的处理
- 优雅的错误恢复机制

### 4.4 日志安全

- 避免在日志中记录明文密钥
- 只记录密钥的哈希值或ID
- 敏感操作的审计日志

## 5. 实施计划

### 5.1 第一阶段：基础实现
- [ ] 实现对称密钥生成
- [ ] 实现公钥加密功能
- [ ] 扩展服务端响应结构
- [ ] 基础测试用例

### 5.2 第二阶段：客户端集成
- [ ] 实现客户端解密功能
- [ ] 扩展联系人管理器
- [ ] 集成测试
- [ ] 错误处理完善

### 5.3 第三阶段：安全增强
- [ ] 密钥轮换机制
- [ ] 安全存储实现
- [ ] 审计日志系统
- [ ] 性能优化

### 5.4 第四阶段：生产部署
- [ ] 完整的测试覆盖
- [ ] 文档完善
- [ ] 监控和告警
- [ ] 生产环境部署

## 6. 测试策略

### 6.1 单元测试
- 对称密钥生成测试
- 加密/解密功能测试
- 错误处理测试

### 6.2 集成测试
- 端到端认证流程测试
- 多客户端并发测试
- 异常场景测试

### 6.3 安全测试
- 密钥泄露测试
- 中间人攻击测试
- 重放攻击测试

## 7. 配置参数

### 7.1 新增配置项
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

### 7.2 兼容性配置
```yaml
anp_sdk:
  # 向后兼容配置
  compatibility:
    enable_symmetric_key: true  # 是否启用对称密钥
    fallback_on_error: true     # 错误时是否降级
    log_key_operations: false   # 是否记录密钥操作日志
```

## 8. 使用示例

### 8.1 基本使用
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

### 8.2 获取对称密钥
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

## 9. 总结

双向Token体系设计通过在现有DID认证基础上增加对称密钥交换机制，为ANP系统提供了更强的安全保障。该设计具有以下特点：

1. **安全性**: 使用公钥加密确保对称密钥的安全传输
2. **兼容性**: 不影响现有的认证流程
3. **可扩展性**: 为未来的加密通信提供基础
4. **可管理性**: 完整的密钥生命周期管理

通过分阶段实施，可以确保系统的稳定性和安全性，同时为用户提供更好的安全体验。
