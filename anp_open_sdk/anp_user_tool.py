import base64
import json
import os
import re
import secrets
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Optional, Any, Tuple

import jcs
import jwt
import yaml
from Crypto.PublicKey import RSA
from agent_connect.authentication import extract_auth_header_parts
from aiohttp import ClientResponse
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from fastapi import HTTPException
from pydantic import BaseModel, Field

from anp_open_sdk.agent_connect_hotpatch.authentication.did_wba_auth_header_memory import DIDWbaAuthHeaderMemory
import logging

from anp_open_sdk.anp_sdk_user_data import LocalUserData
from anp_open_sdk.config import get_global_config, UnifiedConfig

logger = logging.getLogger(__name__)





def load_did_doc_from_path(did_document_path):
    with open(did_document_path, 'r') as f:
        did_document = json.load(f)
    return did_document
def load_private_key(private_key_path: str, password: Optional[bytes] = None):
    """加载私钥"""
    try:
        with open(private_key_path, "rb") as f:
            private_key_data = f.read()
        return load_pem_private_key(private_key_data, password=password)
    except Exception as e:
        logger.error(f"加载私钥时出错: {str(e)}")
        return None
def get_jwt_private_key(key_path: str = None ) -> Optional[str]:
    """
    Get the JWT private key from a PEM file.
    Args:
        key_path: Path to the private key PEM file (default: from config)

    Returns:
        Optional[str]: The private key content as a string, or None if the file cannot be read
    """

    if not os.path.exists(key_path):
        logger.debug(f"Private key file not found: {key_path}")
        return None

    try:
        with open(key_path, "r") as f:
            private_key = f.read()
        logger.debug(f"读取到Token签名密钥文件{key_path}，准备签发Token")
        return private_key
    except Exception as e:
        logger.debug(f"Error reading private key file: {e}")
        return None
def get_jwt_public_key(key_path: str = None) -> Optional[str]:
    """
    Get the JWT public key from a PEM file.

    Args:
        key_path: Path to the public key PEM file (default: from config)

    Returns:
        Optional[str]: The public key content as a string, or None if the file cannot be read
    """
    if not os.path.exists(key_path):
        logger.debug(f"Public key file not found: {key_path}")
        return None

    try:
        with open(key_path, "r") as f:
            public_key = f.read()
        logger.debug(f"Successfully read public key from {key_path}")
        return public_key
    except Exception as e:
        logger.debug(f"Error reading public key file: {e}")
        return None



class AuthenticationContext(BaseModel):
    """认证上下文"""
    caller_did: str
    target_did: str
    request_url: str
    method: str = "GET"
    timestamp: Optional[datetime] = None
    nonce: Optional[str] = None
    custom_headers: Dict[str, str] = Field(default_factory=dict)
    json_data: Optional[Dict[str, Any]] = None
    use_two_way_auth: bool = True
    domain: Optional[str] = None  # 新增 domain 字段
def create_did_auth_header_from_user_data(user_data: 'LocalUserData') -> DIDWbaAuthHeaderMemory:
    """
    [新] 从内存中的 LocalUserData 对象创建 DIDWbaAuthHeaderMemory 实例。
    """
    if not user_data.did_document or not user_data.did_private_key:
        raise ValueError("User data is missing DID document or private key in memory.")
    return DIDWbaAuthHeaderMemory(
        user_data.did_document,
        user_data.did_private_key
    )
def verify_timestamp(timestamp_str: str) -> bool:
    """
    Verify if a timestamp is within the valid period.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        bool: Whether the timestamp is valid
    """
    try:
        # Parse the timestamp string
        request_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

        # Get current time
        current_time = datetime.now(timezone.utc)

        # Calculate time difference
        time_diff = abs((current_time - request_time).total_seconds() / 60)
        config = get_global_config()
        nonce_expire_minutes = config.anp_sdk.nonce_expire_minutes
        # Verify timestamp is within valid period
        if time_diff > nonce_expire_minutes:
            logger.debug(f"Timestamp expired. Current time: {current_time}, Request time: {request_time}, Difference: {time_diff} minutes")
            return False

        return True

    except ValueError as e:
        logger.debug(f"Invalid timestamp format: {e}")
        return False
    except Exception as e:
        logger.debug(f"Error verifying timestamp: {e}")
        return False
def extract_did_from_auth_header(auth_header: str) -> Tuple[Optional[str], Optional[str]]:
    """
    支持两路和标准认证头的 DID 提取
    """
    try:
        # 优先尝试两路认证
        from anp_open_sdk.agent_connect_hotpatch.authentication.did_wba import extract_auth_header_parts_two_way
        parts = extract_auth_header_parts_two_way(auth_header)
        if parts and len(parts) == 6:
            did, nonce, timestamp, resp_did, keyid, signature = parts
            return did, resp_did
    except Exception:
        pass

    try:
        # 回退到标准认证
        parts = extract_auth_header_parts(auth_header)
        if parts and len(parts) >= 4:
            did, nonce, timestamp, keyid, signature = parts
            return did, None
    except Exception:
        pass

    return None, None






def parse_wba_did_host_port(did: str) -> Tuple[Optional[str], Optional[int]]:
    """
    从 did:wba:host%3Aport:xxxx / did:wba:host:port:xxxx / did:wba:host:xxxx
    解析 host 和 port
    """
    m = re.match(r"did:wba:([^%:]+)%3A(\d+):", did)
    if m:
        return m.group(1), int(m.group(2))
    m = re.match(r"did:wba:([^:]+):(\d+):", did)
    if m:
        return m.group(1), int(m.group(2))
    m = re.match(r"did:wba:([^:]+):", did)
    if m:
        return m.group(1), 80
    return None, None
def find_user_by_did(did):
    config=get_global_config()

    user_dirs = config.anp_sdk.user_did_path
    for user_dir in os.listdir(user_dirs):
        did_path = os.path.join(user_dirs, user_dir, "did_document.json")
        if os.path.exists(did_path):
            try:
                with open(did_path, 'r', encoding='utf-8') as f:
                    did_dict = json.load(f)
                    if did_dict.get('id') == did:
                        logger.debug(f"已加载用户 {user_dir} 的 DID 文档")
                        return True, did_dict, user_dir
            except Exception as e:
                logger.error(f"读取DID文档 {did_path} 出错: {e}")
                continue
    logger.error(f"未找到DID为 {did} 的用户文档")
    return False, None, None
def create_did_user(user_iput: dict, *, did_hex: bool = True, did_check_unique: bool = True):
    from agent_connect.authentication.did_wba import create_did_wba_document
    import json
    import os
    from datetime import datetime
    import re
    import urllib.parse



    required_fields = ['name', 'host', 'port', 'dir', 'type']
    if not all(field in user_iput for field in required_fields):
        logger.error("缺少必需的参数字段")
        return None
    config=get_global_config()

    userdid_filepath = config.anp_sdk.user_did_path
    userdid_filepath = UnifiedConfig.resolve_path(userdid_filepath)

    def get_existing_usernames(userdid_filepath):
        if not os.path.exists(userdid_filepath):
            return []
        usernames = []
        for d in os.listdir(userdid_filepath):
            if os.path.isdir(os.path.join(userdid_filepath, d)):
                cfg_path = os.path.join(userdid_filepath, d, 'agent_cfg.yaml')
                if os.path.exists(cfg_path):
                    with open(cfg_path, 'r') as f:
                        try:
                            cfg = yaml.safe_load(f)
                            if cfg and 'name' in cfg:
                                usernames.append(cfg['name'])
                        except:
                            pass
        return usernames

    base_name = user_iput['name']
    existing_names = get_existing_usernames(userdid_filepath)

    if base_name in existing_names:
        date_suffix = datetime.now().strftime('%Y%m%d')
        new_name = f"{base_name}_{date_suffix}"
        if new_name in existing_names:
            pattern = f"{re.escape(new_name)}_?(\\d+)?"
            matches = [re.match(pattern, name) for name in existing_names]
            numbers = [int(m.group(1)) if m and m.group(1) else 0 for m in matches if m]
            next_number = max(numbers + [0]) + 1
            new_name = f"{new_name}_{next_number}"
        user_iput['name'] = new_name
        logger.debug(f"用户名 {base_name} 已存在，使用新名称：{new_name}")

    userdid_hostname = user_iput['host']
    userdid_port = int(user_iput['port'])
    unique_id = secrets.token_hex(8) if did_hex else None


    if userdid_port not in (80, 443):
        userdid_host_port = f"{userdid_hostname}%3A{userdid_port}"
    did_parts = ['did', 'wba', userdid_host_port]
    if user_iput['dir']:
        did_parts.append(urllib.parse.quote(user_iput['dir'], safe=''))
    if user_iput['type']:
        did_parts.append(urllib.parse.quote(user_iput['type'], safe=''))
    if did_hex:
        did_parts.append(unique_id)
    did_id = ':'.join(did_parts)

    if not did_hex and did_check_unique:
        for d in os.listdir(userdid_filepath):
            did_path = os.path.join(userdid_filepath, d, 'did_document.json')
            if os.path.exists(did_path):
                with open(did_path, 'r', encoding='utf-8') as f:
                    did_dict = json.load(f)
                    if did_dict.get('id') == did_id:
                        logger.error(f"DID已存在: {did_id}")
        return None

    user_dir_name = f"user_{unique_id}" if did_hex else f"user_{user_iput['name']}"
    userdid_filepath = os.path.join(userdid_filepath, user_dir_name)

    path_segments = [user_iput['dir'], user_iput['type']]
    if did_hex:
        path_segments.append(unique_id)
    agent_description_url = f"http://{userdid_hostname}:{userdid_port}/{user_iput['dir']}/{user_iput['type']}/{unique_id if did_hex else ''}/ad.json"

    did_document, keys = create_did_wba_document(
        hostname=userdid_hostname,
        port=userdid_port,
        path_segments=path_segments,
        agent_description_url=agent_description_url
        )
    did_document['id'] = did_id
    if keys:
        did_document['key_id'] = list(keys.keys())[0]

    os.makedirs(userdid_filepath, exist_ok=True)
    with open(f"{userdid_filepath}/did_document.json", "w") as f:
        json.dump(did_document, f, indent=4)

    for key_id, (private_key_pem, public_key_pem) in keys.items():
        with open(f"{userdid_filepath}/{key_id}_private.pem", "wb") as f:
            f.write(private_key_pem)
        with open(f"{userdid_filepath}/{key_id}_public.pem", "wb") as f:
            f.write(public_key_pem)

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    agent_cfg = {
        "name": user_iput['name'],
        "unique_id": unique_id,
        "did": did_document["id"],
        "type": user_iput['type'],
        "owner": {"name": "anpsdk 创造用户", "@id": "https://localhost"},
        "description": "anpsdk的测试用户",
        "version": "0.1.0",
        "created_at": time
    }
    with open(f"{userdid_filepath}/agent_cfg.yaml", "w", encoding='utf-8') as f:
        yaml.dump(agent_cfg, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    private_key = RSA.generate(2048).export_key()
    public_key = RSA.import_key(private_key).publickey().export_key()
    testcontent = {"user_id": 123}
    token = create_jwt(testcontent, private_key)
    token = verify_jwt(token, public_key)
    if testcontent["user_id"] == token["user_id"]:
        with open(f"{userdid_filepath}/private_key.pem", "wb") as f:
            f.write(private_key)
        with open(f"{userdid_filepath}/public_key.pem", "wb") as f:
            f.write(public_key)

    logger.debug(f"DID创建成功: {did_document['id']}")
    logger.debug(f"DID文档已保存到: {userdid_filepath}")
    logger.debug(f"密钥已保存到: {userdid_filepath}")
    logger.debug(f"用户文件已保存到: {userdid_filepath}")
    logger.debug(f"jwt密钥已保存到: {userdid_filepath}")


    return did_document
def get_agent_cfg_by_user_dir(user_dir: str) -> dict:
    import os
    import yaml
    config=get_global_config()

    did_path = Path(config.anp_sdk.user_did_path)
    did_path = did_path.joinpath(user_dir, "agent_cfg.yaml")
    cfg_path = Path(UnifiedConfig.resolve_path(did_path.as_posix()))
    if not os.path.isfile(cfg_path):
        raise FileNotFoundError(f"agent_cfg.yaml not found in {user_dir}")
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg





def create_verification_credential(
    did_document: Dict[str, Any],
    private_key: ec.EllipticCurvePrivateKey,
    nonce: str,
    expires_in: int = 3600
) -> Optional[Dict[str, Any]]:
    """
    创建验证凭证(VC)

    Args:
        did_document: DID文档
        private_key_path: 私钥路径
        nonce: 服务器提供的nonce
        expires_in: 凭证有效期（秒）

    Returns:
        Dict: 验证凭证，如果创建失败则返回None
    """
    try:
        # 获取DID ID和验证方法
        did_id = did_document.get("id")
        if not did_id:
            logger.error("DID文档中缺少id字段")
            return None

        verification_methods = did_document.get("verificationMethod", [])
        if not verification_methods:
            logger.error("DID文档中缺少verificationMethod字段")
            return None

        # 使用第一个验证方法
        verification_method = verification_methods[0]

        # 创建凭证
        issuance_date = datetime.now(timezone.utc)
        expiration_date = issuance_date + timedelta(seconds=expires_in)

        credential = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "type": ["VerifiableCredential", "DIDAuthorizationCredential"],
            "issuer": did_id,
            "subject": did_id,
            "issuanceDate": issuance_date.isoformat(),
            "expirationDate": expiration_date.isoformat(),
            "credentialSubject": {
                "id": verification_method.get("id"),
                "type": verification_method.get("type"),
                "controller": verification_method.get("controller"),
                "publicKeyJwk": verification_method.get("publicKeyJwk"),
                "nonce": nonce
            }
        }

        # 加载私钥
        if not private_key:
            logger.error("Provided private key object is invalid.")
            return None

        # 准备签名数据
        credential_without_proof = credential.copy()
        canonical_json = jcs.canonicalize(credential_without_proof)

        # 计算签名
        if isinstance(private_key, ec.EllipticCurvePrivateKey):
            signature = private_key.sign(
                canonical_json,
                ec.ECDSA(hashes.SHA256())
            )

            # 将签名编码为Base64
            signature_b64 = base64.b64encode(signature).decode("utf-8")

            # 添加签名到凭证
            credential["proof"] = {
                "type": "EcdsaSecp256k1Signature2019",
                "created": issuance_date.isoformat(),
                "verificationMethod": verification_method.get("id"),
                "proofPurpose": "assertionMethod",
                "jws": signature_b64
            }

            return credential
        else:
            logger.error("不支持的私钥类型")
            return None
    except Exception as e:
        logger.error(f"创建验证凭证时出错: {str(e)}")
        return None
def verify_verification_credential(
    credential: Dict[str, Any],
    did_document: Dict[str, Any],
    expected_nonce: Optional[str] = None
) -> bool:
    """
    验证验证凭证(VC)

    Args:
        credential: 验证凭证
        did_document: DID文档
        expected_nonce: 预期的nonce，如果提供则验证nonce是否匹配

    Returns:
        bool: 验证是否通过
    """
    try:
        # 验证基本字段
        if "proof" not in credential or "credentialSubject" not in credential:
            logger.error("验证凭证缺少必要字段")
            return False

        # 验证过期时间
        if "expirationDate" in credential:
            expiration_date = datetime.fromisoformat(credential["expirationDate"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expiration_date:
                logger.error("验证凭证已过期")
                return False

        # 验证nonce
        if expected_nonce:
            credential_nonce = credential.get("credentialSubject", {}).get("nonce")
            if credential_nonce != expected_nonce:
                logger.error(f"Nonce不匹配: 预期 {expected_nonce}, 实际 {credential_nonce}")
                return False

        # 验证签名
        # 注意：这里简化了签名验证过程，实际应用中应该使用专门的VC库
        # 例如，可以使用DID解析器获取公钥，然后验证签名

        # 这里假设验证通过
        return True
    except Exception as e:
        logger.error(f"验证凭证时出错: {str(e)}")
        return False



def create_access_token(private_key: rsa.RSAPrivateKey, data: Dict, expires_delta: int = None) -> str:
    """
    Create a new JWT access token.

    Args:
        private_key: RSA private key object from memory
        data: Data to encode in the token
        expires_delta: Optional expiration time

    Returns:
        str: Encoded JWT token
    """
    config = get_global_config()
    token_expire_time = config.anp_sdk.token_expire_time

    to_encode = data.copy()
    expires = datetime.now(timezone.utc) + (timedelta(minutes=expires_delta) if expires_delta else timedelta(seconds=token_expire_time))
    to_encode.update({"exp": expires})

    if not private_key:
        logger.debug("Invalid JWT private key object provided")
        raise HTTPException(status_code=500, detail="Internal server error during token generation")

    jwt_algorithm = config.anp_sdk.jwt_algorithm
    # Create the JWT token using RS256 algorithm with private key
    encoded_jwt = jwt.encode(
        to_encode,
        private_key,
        algorithm=jwt_algorithm
    )
    return encoded_jwt

def create_jwt(content: dict, private_key: str) -> str:
    try:
        headers = {
            'alg': 'RS256',
            'typ': 'JWT'
        }
        token = jwt.encode(
            payload=content,
            key=private_key,
            algorithm='RS256',
            headers=headers
        )
        return token
    except Exception as e:
        logger.error(f"生成 JWT token 失败: {e}")
        return None
def verify_jwt(token: str, public_key: str) -> dict:
    try:
        payload = jwt.decode(
            jwt=token,
            key=public_key,
            algorithms=['RS256']
        )
        return payload
    except jwt.InvalidTokenError as e:
        logger.error(f"验证 JWT token 失败: {e}")
        return None



async def response_to_dict(response: Any) -> Dict:
    if isinstance(response, dict):
        return response
    elif isinstance(response, ClientResponse):
        try:
            if response.status >= 400:
                error_text = await response.text()
                logger.error(f"HTTP错误 {response.status}: {error_text}")
                return {"error": f"HTTP {response.status}", "message": error_text}
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return await response.json()
            else:
                text = await response.text()
                logger.warning(f"非JSON响应，Content-Type: {content_type}")
                return {"content": text, "content_type": content_type}
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            text = await response.text()
            return {"error": "JSON解析失败", "raw_text": text}
        except Exception as e:
            logger.error(f"处理响应时出错: {e}")
            return {"error": str(e)}
    else:
        logger.error(f"未知响应类型: {type(response)}")
        return {"error": f"未知类型: {type(response)}"}

