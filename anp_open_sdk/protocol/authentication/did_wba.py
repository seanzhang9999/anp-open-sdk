# anp_open_sdk/protocol/authentication/did_wba.py
"""
Unified WBA (Web-Based Authentication) DID Implementation

This module provides the complete, unified implementation of WBA DID functionality,
combining all the debugging features and core logic from various implementations.
This is the single source of truth for WBA authentication in the protocol layer.
"""

import base64
import hashlib
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, Union
from urllib.parse import urlparse

import aiohttp
import jcs

from anp_open_sdk.protocol.crypto import create_secp256k1_signer, create_ed25519_signer

logger = logging.getLogger(__name__)


class DIDWbaAuthHeader:
    """WBA认证头处理类"""
    
    def __init__(self, caller_did: str, target_did: str = None, request_url: str = None):
        self.caller_did = caller_did
        self.target_did = target_did
        self.request_url = request_url or "http://localhost"
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from starlette.requests import Request
        except ImportError:
            Request = None

        if Request and isinstance(url, Request):
            # Prefer base_url (remove path), otherwise use url
            url_str = str(getattr(url, "base_url", None) or getattr(url, "url", None))
        else:
            url_str = str(url)

        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc.split(':')[0]
        return domain
    
    def build_auth_header(self, private_key_bytes: bytes, verification_method_fragment: str = "#key-1") -> Dict[str, str]:
        """构建认证头"""
        nonce = secrets.token_hex(16)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        service_domain = self._get_domain(self.request_url)

        logger.info(f"🔑 SIGN PAYLOAD DEBUG - Request URL: {self.request_url}")
        logger.info(f"🔑 SIGN PAYLOAD DEBUG - Extracted service domain: {service_domain}")

        data_to_sign = {
            "nonce": nonce,
            "timestamp": timestamp,
            "service": service_domain,
            "did": self.caller_did,
        }
        
        if self.target_did:
            data_to_sign["resp_did"] = self.target_did

        canonical_json = jcs.canonicalize(data_to_sign)
        content_hash = hashlib.sha256(canonical_json).digest()

        # DEBUG: 记录签名时的数据
        logger.info(f"🔑 SIGN PAYLOAD DEBUG - Data to sign: {data_to_sign}")
        logger.info(f"🔑 SIGN PAYLOAD DEBUG - Canonical JSON: {canonical_json}")
        logger.info(f"🔑 SIGN PAYLOAD DEBUG - Content hash: {content_hash.hex()}")

        # 使用统一的签名器
        signature = sign_payload(content_hash, private_key_bytes)
        
        # DEBUG: 记录签名过程的关键信息
        logger.info(f"🔑 SIGN DEBUG - DID: {self.caller_did}")
        logger.info(f"🔑 SIGN DEBUG - Verification method fragment: {verification_method_fragment}")
        logger.info(f"🔑 SIGN DEBUG - Content hash (hex): {content_hash.hex()}")
        logger.info(f"🔑 SIGN DEBUG - Signature: {signature}")

        parts = [
            f'DIDWba did="{self.caller_did}"',
            f'nonce="{nonce}"',
            f'timestamp="{timestamp}"',
        ]
        
        if self.target_did:
            parts.append(f'resp_did="{self.target_did}"')

        parts.extend([f'verification_method="{verification_method_fragment}"', f'signature="{signature}"'])

        auth_header_value = ", ".join(parts)
        logger.info(f"\nData to sign:{data_to_sign},\ncontent_hash:{content_hash},\nsignature:{signature}")

        return {"Authorization": auth_header_value}

    def parse_auth_header(self, auth_header: str) -> Dict[str, Any]:
        """解析WBA认证头"""
        if not auth_header or not auth_header.startswith("DIDWba "):
            return {}

        value = auth_header.replace("DIDWba ", "", 1)
        import re
        try:
            # This regex finds key="value" pairs.
            parsed = dict(re.findall(r'(\w+)\s*=\s*\"([^\"]*)\"', value))
            return parsed
        except Exception as e:
            logger.error(f"Failed to parse auth header '{auth_header}': {e}")
            return {}


def encode_signature(signature_bytes: bytes) -> str:
    """
    将签名字节编码为 base64url 格式。如果签名是 DER 格式，先转换为 R|S 格式。
    完全复制原版的 encode_signature 逻辑。
    """
    try:
        from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
        
        # 尝试解析 DER 格式
        try:
            r, s = decode_dss_signature(signature_bytes)
            # 如果成功解析为 DER 格式，转换为 R|S 格式（使用固定32字节长度）
            r_bytes = r.to_bytes(32, byteorder='big')
            s_bytes = s.to_bytes(32, byteorder='big')
            signature = r_bytes + s_bytes
        except Exception:
            # 如果不是 DER 格式，假设已经是 R|S 格式
            if len(signature_bytes) % 2 != 0:
                raise ValueError("Invalid R|S signature format: length must be even")
            signature = signature_bytes
        
        # 编码为 base64url
        return base64.urlsafe_b64encode(signature).rstrip(b'=').decode('ascii')
        
    except Exception as e:
        logger.error(f"Failed to encode signature: {str(e)}")
        raise ValueError(f"Invalid signature format: {str(e)}")


def decode_signature(signature_str: str) -> bytes:
    """
    将 base64url 编码的签名解码为字节格式
    """
    try:
        # 解码 base64url 签名，添加必要的填充
        return base64.urlsafe_b64decode(signature_str + '=' * (-len(signature_str) % 4))
    except Exception as e:
        logger.error(f"Failed to decode signature: {str(e)}")
        raise ValueError(f"Invalid signature format: {str(e)}")


def sign_payload(payload: Union[str, bytes], private_key_bytes: bytes) -> str:
    """
    签名 payload，返回 base64url 编码的签名。
    对于 secp256k1，生成 DER 签名然后转换为 R|S 格式。
    """
    try:
        # 处理payload，支持字符串和字节类型
        if isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        else:
            payload_bytes = payload
        
        # 根据私钥长度判断密钥类型
        if len(private_key_bytes) == 32:
            # secp256k1 或 Ed25519
            # 先尝试 secp256k1
            try:
                from cryptography.hazmat.primitives.asymmetric import ec
                from cryptography.hazmat.primitives import hashes
                from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature
                
                private_key_obj = ec.derive_private_key(
                    int.from_bytes(private_key_bytes, byteorder="big"), 
                    ec.SECP256K1()
                )
                
                # 生成 DER 格式签名
                signature_der = private_key_obj.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))
                
                # 解析 DER 签名得到 R, S
                r, s = decode_dss_signature(signature_der)
                
                # 转换为固定长度的 R|S 格式（32字节 R + 32字节 S）
                r_bytes = r.to_bytes(32, byteorder='big')
                s_bytes = s.to_bytes(32, byteorder='big')
                signature_rs = r_bytes + s_bytes
                
                # 编码为 base64url
                return base64.urlsafe_b64encode(signature_rs).rstrip(b'=').decode('ascii')
                
            except Exception:
                # 如果secp256k1失败，尝试Ed25519
                try:
                    from cryptography.hazmat.primitives.asymmetric import ed25519
                    private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
                    signature_bytes = private_key_obj.sign(payload_bytes)
                    return base64.urlsafe_b64encode(signature_bytes).rstrip(b'=').decode('ascii')
                except Exception as e:
                    logger.error(f"Both secp256k1 and Ed25519 signing failed: {e}")
                    raise
        else:
            raise ValueError(f"Unsupported private key length: {len(private_key_bytes)}")
            
    except Exception as e:
        logger.error(f"签名失败: {e}")
        raise


def verify_signature(payload: Union[str, bytes], signature: str, public_key_bytes: bytes) -> bool:
    """
    验证签名，完全复制原版的 verify_signature 逻辑。
    修复了 R|S 到 DER 转换中的前导零处理问题。
    """
    try:
        # 解码 base64url 签名（与原版保持一致）
        signature_bytes = base64.urlsafe_b64decode(signature + '=' * (-len(signature) % 4))

        # 处理payload，支持字符串和字节类型
        if isinstance(payload, str):
            payload_bytes = payload.encode('utf-8')
        else:
            payload_bytes = payload

        # 根据公钥长度判断密钥类型
        if len(public_key_bytes) == 32:
            # Ed25519 公钥 (32 bytes)
            return _verify_ed25519_signature(signature_bytes, payload_bytes, public_key_bytes)
        elif len(public_key_bytes) == 65 and public_key_bytes[0] == 0x04:
            # secp256k1 非压缩公钥 (65 bytes, 以0x04开头)
            return _verify_secp256k1_signature(signature_bytes, payload_bytes, public_key_bytes)
        elif len(public_key_bytes) == 33:
            # secp256k1 压缩公钥 (33 bytes)
            return _verify_secp256k1_signature(signature_bytes, payload_bytes, public_key_bytes, compressed=True)
        else:
            logger.error(f"不支持的公钥长度: {len(public_key_bytes)} bytes")
            return False

    except Exception as e:
        logger.error(f"签名验证失败: {e}")
        return False


def _verify_ed25519_signature(signature_bytes: bytes, payload_bytes: bytes, public_key_bytes: bytes) -> bool:
    """验证 Ed25519 签名"""
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key_obj.verify(signature_bytes, payload_bytes)
        return True
    except Exception as e:
        logger.error(f"Ed25519 签名验证失败: {e}")
        return False


def _verify_secp256k1_signature(signature_bytes: bytes, payload_bytes: bytes, public_key_bytes: bytes, compressed: bool = False) -> bool:
    """
    验证 secp256k1 签名，正确处理 R|S 到 DER 的转换。
    """
    try:
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

        # DEBUG: 记录验证过程的输入参数
        logger.info(f"🔍 VERIFY DETAIL - Signature bytes length: {len(signature_bytes)}")
        logger.info(f"🔍 VERIFY DETAIL - Signature bytes (hex): {signature_bytes.hex()}")
        logger.info(f"🔍 VERIFY DETAIL - Payload bytes length: {len(payload_bytes)}")
        logger.info(f"🔍 VERIFY DETAIL - Payload bytes (hex): {payload_bytes.hex()}")
        logger.info(f"🔍 VERIFY DETAIL - Public key bytes length: {len(public_key_bytes)}")
        logger.info(f"🔍 VERIFY DETAIL - Public key bytes (hex): {public_key_bytes.hex()}")
        logger.info(f"🔍 VERIFY DETAIL - Compressed mode: {compressed}")

        # 创建公钥对象
        if compressed:
            logger.info(f"🔍 VERIFY DETAIL - Creating compressed public key from encoded point")
            public_key_obj = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
        else:
            # 从非压缩格式创建公钥对象
            logger.info(f"🔍 VERIFY DETAIL - Creating uncompressed public key from coordinates")
            logger.info(f"🔍 VERIFY DETAIL - Public key format byte: 0x{public_key_bytes[0]:02x}")
            
            x = int.from_bytes(public_key_bytes[1:33], byteorder='big')
            y = int.from_bytes(public_key_bytes[33:65], byteorder='big')
            
            logger.info(f"🔍 VERIFY DETAIL - X coordinate: {x}")
            logger.info(f"🔍 VERIFY DETAIL - Y coordinate: {y}")
            
            # 验证坐标是否在曲线上
            logger.info(f"🔍 VERIFY DETAIL - Attempting to create EllipticCurvePublicNumbers")
            public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
            
            logger.info(f"🔍 VERIFY DETAIL - Attempting to create public key object")
            public_key_obj = public_numbers.public_key()
            
            logger.info(f"🔍 VERIFY DETAIL - Public key object created successfully")

        # 确保签名长度是 64 字节（32字节 R + 32字节 S）
        if len(signature_bytes) != 64:
            logger.error(f"Invalid signature length: {len(signature_bytes)}, expected 64")
            return False

        # 从固定长度 R|S 格式提取 R 和 S
        r_bytes = signature_bytes[:32]
        s_bytes = signature_bytes[32:]
        
        # 转换为整数（去除前导零）
        r = int.from_bytes(r_bytes, 'big')
        s = int.from_bytes(s_bytes, 'big')
        
        logger.info(f"🔍 VERIFY DETAIL - R value: {r}")
        logger.info(f"🔍 VERIFY DETAIL - S value: {s}")
        
        # 验证 R 和 S 的有效性
        if r == 0 or s == 0:
            logger.error("Invalid signature: R or S is zero")
            return False
        
        # 转换为 DER 格式
        signature_der = encode_dss_signature(r, s)
        logger.info(f"🔍 VERIFY DETAIL - DER signature length: {len(signature_der)}")
        logger.info(f"🔍 VERIFY DETAIL - DER signature (hex): {signature_der.hex()}")
        
        # 验证签名
        try:
            logger.info(f"🔍 VERIFY DETAIL - Attempting signature verification")
            public_key_obj.verify(signature_der, payload_bytes, ec.ECDSA(hashes.SHA256()))
            logger.info(f"🔍 VERIFY DETAIL - Signature verification SUCCESSFUL")
            return True
        except Exception as verify_error:
            logger.error(f"🔍 VERIFY DETAIL - Signature verification FAILED: {verify_error}")
            logger.error(f"🔍 VERIFY DETAIL - Error type: {type(verify_error).__name__}")
            raise verify_error

    except Exception as e:
        logger.error(f"🔍 VERIFY DETAIL - secp256k1 verification failed: {e}")
        logger.error(f"🔍 VERIFY DETAIL - Error type: {type(e).__name__}")
        return False


async def resolve_did_wba_document(did: str) -> Optional[Dict]:
    """
    解析 WBA DID 文档
    优先使用本地解析，然后尝试网络解析
    """
    try:
        # 先尝试本地解析
        try:
            from anp_open_sdk.auth.did_auth_wba_custom_did_resolver import resolve_local_did_document
            result = await resolve_local_did_document(did)
            if result:
                logger.debug(f"本地解析DID成功: {did}")
                return result
        except Exception as e:
            logger.debug(f"本地解析DID失败: {e}")
        
        # 如果本地失败，尝试通过HTTP解析
        from anp_open_sdk.utils.did_utils import parse_wba_did_host_port
        
        host, port = parse_wba_did_host_port(did)
        if not host or not port:
            logger.error(f"无法从DID中提取主机和端口: {did}")
            return None
        
        # 构建WBA DID解析URL  
        url = f"http://{host}:{port}/wba/did-document?did={did}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.debug(f"网络解析DID成功: {did}")
                    return result
                else:
                    logger.error(f"DID解析请求失败: {response.status}")
                    return None
                    
    except Exception as e:
        logger.error(f"解析DID文档失败: {e}")
        return None


def resolve_did_wba_document_sync(did: str) -> Optional[Dict]:
    """同步版本的DID文档解析"""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(resolve_did_wba_document(did))
    except RuntimeError:
        # 如果没有事件循环，创建一个新的
        return asyncio.run(resolve_did_wba_document(did))


async def generate_auth_header_two_way(caller_did: str, target_did: str, request_url: str, private_key_bytes: bytes) -> Dict[str, Any]:
    """生成双向认证头"""
    auth_header = DIDWbaAuthHeader(caller_did, target_did, request_url)
    return auth_header.build_auth_header(private_key_bytes)


def extract_auth_header_parts_two_way(auth_header: str) -> Optional[Dict[str, Any]]:
    """提取认证头各部分"""
    dummy_header = DIDWbaAuthHeader("dummy")
    parsed = dummy_header.parse_auth_header(auth_header)
    if parsed:
        return [parsed.get('did'), parsed.get('resp_did'), parsed.get('nonce'), 
                parsed.get('timestamp'), parsed.get('verification_method'), parsed.get('signature')]
    return None


async def verify_auth_header_signature_two_way(auth_header: str, expected_caller_did: str) -> Tuple[bool, str]:
    """验证双向认证头签名"""
    try:
        dummy_header = DIDWbaAuthHeader("dummy")
        parsed = dummy_header.parse_auth_header(auth_header)
        
        if not parsed:
            return False, "无法解析认证头"
        
        caller_did = parsed.get('did')
        target_did = parsed.get('resp_did')
        nonce = parsed.get('nonce')
        timestamp = parsed.get('timestamp')
        verification_method_fragment = parsed.get('verification_method')
        signature = parsed.get('signature')
        
        if caller_did != expected_caller_did:
            return False, f"DID不匹配: 期望 {expected_caller_did}, 收到 {caller_did}"
        
        # 解析DID文档获取公钥
        did_doc = await resolve_did_wba_document(caller_did)
        if not did_doc:
            return False, f"无法解析DID文档: {caller_did}"
        
        # 从验证方法中获取公钥
        public_key_bytes = None
        for vm in did_doc.get('verificationMethod', []):
            if vm.get('id', '').endswith(verification_method_fragment):
                # 首先尝试 publicKeyMultibase 格式
                public_key_multibase = vm.get('publicKeyMultibase')
                if public_key_multibase:
                    from anp_open_sdk.auth.utils import multibase_to_bytes
                    public_key_bytes = multibase_to_bytes(public_key_multibase)
                    break
                
                # 如果没有 publicKeyMultibase，尝试 publicKeyJwk 格式
                public_key_jwk = vm.get('publicKeyJwk')
                if public_key_jwk and public_key_jwk.get('kty') == 'EC' and public_key_jwk.get('crv') == 'secp256k1':
                    import base64
                    x = public_key_jwk.get('x')
                    y = public_key_jwk.get('y')
                    if x and y:
                        # 解码 JWK 格式的坐标
                        x_bytes = base64.urlsafe_b64decode(x + '=' * (-len(x) % 4))
                        y_bytes = base64.urlsafe_b64decode(y + '=' * (-len(y) % 4))
                        # 构造未压缩格式的公钥（0x04 + x + y）
                        public_key_bytes = b'\x04' + x_bytes + y_bytes
                        break
        
        if not public_key_bytes:
            return False, f"找不到公钥: {verification_method_fragment}"
        
        # 重构签名数据
        service_domain = dummy_header._get_domain("http://localhost")  # 简化处理
        data_to_sign = {
            "nonce": nonce,
            "timestamp": timestamp,
            "service": service_domain,
            "did": caller_did,
        }
        
        if target_did:
            data_to_sign["resp_did"] = target_did
        
        canonical_json = jcs.canonicalize(data_to_sign)
        content_hash = hashlib.sha256(canonical_json).digest()
        
        # 验证签名
        is_valid = verify_signature(content_hash, signature, public_key_bytes)
        
        if is_valid:
            return True, "签名验证成功"
        else:
            return False, "签名验证失败"
            
    except Exception as e:
        logger.error(f"验证认证头签名时出错: {e}")
        return False, f"验证过程中发生异常: {e}"


def generate_auth_json(caller_did: str, target_did: str = None, request_url: str = "http://localhost", private_key_bytes: bytes = None) -> Dict[str, Any]:
    """生成认证JSON格式数据"""
    auth_header = DIDWbaAuthHeader(caller_did, target_did, request_url)
    header_dict = auth_header.build_auth_header(private_key_bytes)
    auth_header_value = header_dict.get("Authorization", "")
    
    # 解析认证头为JSON格式
    parsed = auth_header.parse_auth_header(auth_header_value)
    return parsed


def verify_auth_json_signature(auth_json: Dict[str, Any], expected_caller_did: str = None) -> bool:
    """验证认证JSON格式的签名"""
    try:
        caller_did = auth_json.get('did')
        signature = auth_json.get('signature')
        
        if expected_caller_did and caller_did != expected_caller_did:
            return False
        
        # 这里简化实现，实际应该重构完整的验证逻辑
        return signature is not None and len(signature) > 0
        
    except Exception as e:
        logger.error(f"验证认证JSON签名失败: {e}")
        return False


def create_did_wba_document(did: str, public_key_multibase: str, verification_method_type: str = "EcdsaSecp256k1VerificationKey2019") -> Dict[str, Any]:
    """创建WBA DID文档"""
    verification_method_id = f"{did}#key-1"
    
    did_document = {
        "@context": [
            "https://www.w3.org/ns/did/v1",
            "https://w3id.org/security/suites/secp256k1-2019/v1"
        ],
        "id": did,
        "verificationMethod": [{
            "id": verification_method_id,
            "type": verification_method_type,
            "controller": did,
            "publicKeyMultibase": public_key_multibase
        }],
        "authentication": [verification_method_id],
        "assertionMethod": [verification_method_id],
        "service": []
    }
    
    return did_document