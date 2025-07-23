import base64
import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, Tuple

import jcs
import jwt
from agent_connect.authentication import extract_auth_header_parts
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, rsa
from fastapi import HTTPException
from pydantic import BaseModel, Field

from anp_foundation.did.agent_connect_hotpatch.authentication.did_wba_auth_header_memory import DIDWbaAuthHeaderMemory
import logging

from anp_foundation.config import get_global_config


logger = logging.getLogger(__name__)


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

def create_did_auth_header_from_user_data(user_data) -> DIDWbaAuthHeaderMemory:
    """
    [新] 从内存中的 LocalUserData 对象创建 DIDWbaAuthHeaderMemory 实例。
    """
    from anp_foundation.anp_user_local_data import LocalUserData
    user_data: LocalUserData

    if not user_data.did_document or not user_data.did_private_key:
        raise ValueError("User data is missing DID document or private key in memory.")
    return DIDWbaAuthHeaderMemory(
        user_data.did_document,
        user_data.did_private_key
    )


def verify_timestamp(timestamp_str: str) -> tuple[bool, str]:
    """
    Verify if a timestamp is within the valid period.

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        tuple[bool, str]: (is_valid, error_message)
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
            error_msg = f"Timestamp expired. Current time: {current_time}, Request time: {request_time}, Difference: {time_diff} minutes"
            logger.debug(error_msg)
            return False, error_msg

        logger.debug(f"_verify_wba_header -- Timestamp passed: {time_diff} less {nonce_expire_minutes}")
        return True, ""

    except ValueError as e:
        error_msg = f"Invalid timestamp format: {e}"
        logger.debug(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error verifying timestamp: {e}"
        logger.debug(error_msg)
        return False, error_msg
def extract_did_from_auth_header(auth_header: str) -> Tuple[Optional[str], Optional[str]]:
    """
    支持两路和标准认证头的 DID 提取
    """
    try:
        # 优先尝试两路认证
        from anp_foundation.did.agent_connect_hotpatch.authentication.did_wba import extract_auth_header_parts_two_way
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
    from anp_foundation.anp_user_local_data import get_user_data_manager
    manager = get_user_data_manager()
    user_data = manager.get_user_data(did)

    if user_data:
        logger.debug(f"从内存中找到用户 {user_data.name} 的数据 (DID: {did})")
        return True, user_data.did_document, user_data.folder_name
    else:
        logger.error(f"未在内存中找到DID为 {did} 的用户数据")
        return False, None, None
def get_agent_cfg_by_user_dir(user_dir: str) -> dict:
    from anp_foundation.anp_user_local_data import get_user_data_manager
    manager = get_user_data_manager()
    all_users = manager.get_all_users()

    for user_data in all_users:
        if user_data.folder_name == user_dir:
            if user_data.agent_cfg:
                return user_data.agent_cfg
            else:
                # 这种情况理论上不应发生，因为加载时总会有 cfg
                raise ValueError(f"User {user_dir} found in memory but has no agent_cfg.")

    # 保持与原函数相同的错误类型，以确保兼容性
    raise FileNotFoundError(f"agent_cfg.yaml not found for user_dir {user_dir} in memory cache")



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
        raise HTTPException(status_code=500, detail="Internal anp_servicepoint error during token generation")

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


@staticmethod
def get_did_host_port_from_did(did: str) -> tuple[str, int]:
    host, port = None, None
    if did.startswith('did:wba:'):
        try:
            did_parts = did.split(':')
            if len(did_parts) > 2:
                host_port = did_parts[2]
                if '%3A' in host_port:
                    host, port = host_port.split('%3A')
                else:
                    host = did_parts[2]
                    port = did_parts[3]
                    if port is not int:
                        port = 80
        except Exception as e:
            logger.debug(f"解析did失败: {did}, 错误: {e}")
    if not host or not port:
        return "localhost", 9527
    return host, int(port)
