# anp_open_sdk/auth_methods/wba/implementation.py
import base64
import hashlib
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse

import aiohttp
import jcs

from anp_open_sdk.auth.did_auth_base import BaseDIDAuthenticator, BaseDIDResolver, BaseDIDSigner, BaseAuthHeaderBuilder, \
    BaseAuth
from anp_open_sdk.auth.schemas import AuthenticationContext, DIDCredentials, DIDDocument
from anp_open_sdk.auth.utils import generate_nonce, is_valid_server_nonce
from anp_open_sdk.auth.token_nonce_auth import verify_timestamp

logger = logging.getLogger(__name__)


# --- 纯粹的WBA认证逻辑实现 ---

class PureWBADIDSigner(BaseDIDSigner):
    """纯净的WBA DID签名器，完全遵循原版 EcdsaSecp256k1VerificationKey2019 的逻辑。"""

    def encode_signature(self, signature_bytes: bytes) -> str:
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

    def sign_payload(self, payload, private_key_bytes: bytes) -> str:
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
            
            # 直接使用 secp256k1 处理（因为我们的密钥都是 secp256k1）
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
            
        except Exception as e:
            logger.error(f"签名失败: {e}")
            raise

    def verify_signature(self, payload, signature: str, public_key_bytes: bytes) -> bool:
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
                from cryptography.hazmat.primitives.asymmetric import ed25519
                public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
                public_key_obj.verify(signature_bytes, payload_bytes)
                return True
            elif len(public_key_bytes) == 65 and public_key_bytes[0] == 0x04:
                # secp256k1 非压缩公钥 (65 bytes, 以0x04开头)
                return self._verify_secp256k1_signature(signature_bytes, payload_bytes, public_key_bytes)
            elif len(public_key_bytes) == 33:
                # secp256k1 压缩公钥 (33 bytes)
                return self._verify_secp256k1_signature(signature_bytes, payload_bytes, public_key_bytes, compressed=True)
            else:
                logger.error(f"不支持的公钥长度: {len(public_key_bytes)} bytes")
                return False

        except Exception as e:
            logger.error(f"签名验证失败: {e}")
            return False

    def _verify_secp256k1_signature(self, signature_bytes: bytes, payload_bytes: bytes, public_key_bytes: bytes, compressed: bool = False) -> bool:
        """
        验证 secp256k1 签名，正确处理 R|S 到 DER 的转换。
        """
        try:
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.hazmat.primitives import hashes
            from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

            # 创建公钥对象
            if compressed:
                public_key_obj = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), public_key_bytes)
            else:
                # 从非压缩格式创建公钥对象
                x = int.from_bytes(public_key_bytes[1:33], byteorder='big')
                y = int.from_bytes(public_key_bytes[33:65], byteorder='big')
                public_numbers = ec.EllipticCurvePublicNumbers(x, y, ec.SECP256K1())
                public_key_obj = public_numbers.public_key()

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
            
            # 验证 R 和 S 的有效性
            if r == 0 or s == 0:
                logger.error("Invalid signature: R or S is zero")
                return False
            
            # 转换为 DER 格式
            signature_der = encode_dss_signature(r, s)
            
            # 验证签名
            public_key_obj.verify(signature_der, payload_bytes, ec.ECDSA(hashes.SHA256()))
            return True

        except Exception as e:
            logger.error(f"secp256k1 签名验证失败: {e}")
            return False

class PureWBAAuthHeaderBuilder(BaseAuthHeaderBuilder):
    """纯净的WBA认证头构建器。"""

    def __init__(self, signer: BaseDIDSigner):
        self.signer = signer

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

        from urllib.parse import urlparse
        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc.split(':')[0]
        return domain
    def _select_authentication_method(self, did_document) -> Tuple[Dict, str]:
        """从DID文档中选择第一个认证方法。"""
        # Check if it's a DIDDocument (Pydantic model) or a dict
        if hasattr(did_document, 'authentication'):
            authentication_methods = did_document.authentication
            verification_methods = did_document.verification_methods
        else:
            authentication_methods = did_document.get("authentication")
            verification_methods = did_document.get("verificationMethod", [])
            
        if not authentication_methods or not isinstance(authentication_methods, list):
            raise ValueError("DID document is missing or has an invalid 'authentication' field.")

        first_method_ref = authentication_methods[0]

        if isinstance(first_method_ref, str):
            method_id = first_method_ref
            if hasattr(did_document, 'verification_methods'):
                # For DIDDocument Pydantic model
                method_dict = next((vm.__dict__ for vm in verification_methods if vm.id == method_id), None)
            else:
                # For dict
                method_dict = next((vm for vm in verification_methods if vm.get("id") == method_id), None)
            if not method_dict:
                raise ValueError(f"Verification method '{method_id}' not found in 'verificationMethod' array.")
        elif isinstance(first_method_ref, dict):
            method_dict = first_method_ref
            method_id = method_dict.get("id")
            if not method_id:
                raise ValueError("Embedded authentication method is missing 'id'.")
        else:
            raise ValueError("Invalid format for authentication method reference.")

        fragment = urlparse(method_id).fragment
        if not fragment:
            raise ValueError(f"Could not extract fragment from verification method ID: {method_id}")

        return method_dict, f"#{fragment}"

    def build_auth_header(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        did_document = credentials.did_document
        did = credentials.did

        _method_dict, verification_method_fragment = self._select_authentication_method(did_document)

        nonce = secrets.token_hex(16)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        service_domain = self._get_domain(context.request_url)

        data_to_sign = {
            "nonce": nonce,
            "timestamp": timestamp,
            "service": service_domain,
            "did": did,
        }
        if context.use_two_way_auth:
            data_to_sign["resp_did"] = context.target_did

        canonical_json = jcs.canonicalize(data_to_sign)
        content_hash = hashlib.sha256(canonical_json).digest()

        signature_der = credentials.sign(content_hash, verification_method_fragment)
        
        # 使用 signer 的 encode_signature 方法处理 DER 到 R|S 的转换和编码
        signature = self.signer.encode_signature(signature_der)

        parts = [
            f'DIDWba did="{did}"',
            f'nonce="{nonce}"',
            f'timestamp="{timestamp}"',
        ]
        if context.use_two_way_auth:
            parts.append(f'resp_did="{context.target_did}"')

        parts.extend([f'verification_method="{verification_method_fragment}"', f'signature="{signature}"'])

        auth_header_value = ", ".join(parts)
        logger.info(f"\nData to sign:{data_to_sign},\ncontent_hash:{content_hash},\nsignature:{signature}")

        return {"Authorization": auth_header_value}

    def parse_auth_header(self, auth_header: str) -> Dict[str, Any]:
        """解析纯净的WBA认证头。"""
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
class PureWBAAuth(BaseAuth):
    """纯净的WBA认证头解析器。"""

    def extract_did_from_auth_header(self, auth_header: str) -> Tuple[Optional[str], Optional[str]]:
        if not auth_header or not auth_header.startswith("DIDWba "):
            return None, None

        import re
        try:
            value_str = auth_header.replace("DIDWba ", "", 1)
            parsed = dict(re.findall(r'(\w+)\s*=\s*\"([^\"]*)\"', value_str))
            caller_did = parsed.get('did')
            target_did = parsed.get('resp_did')  # will be None if not present
            return caller_did, target_did
        except Exception:
            return None, None

class PureWBADIDAuthenticator(BaseDIDAuthenticator):
    """
    完全独立的WBA认证器，不依赖agent_connect。
    它依赖于一个外部的DIDResolver来获取公钥。
    """


    def __init__(self, resolver: BaseDIDResolver, signer: BaseDIDSigner, header_builder: BaseAuthHeaderBuilder, base_auth: BaseAuth):
        super().__init__(resolver, signer, header_builder, base_auth)

    async def authenticate_request(self, context: AuthenticationContext, credentials: DIDCredentials) -> Tuple[
        bool, str, Dict[str, Any]]:
        """
        使用纯净组件执行认证请求。
        借鉴 WBADIDAuthenticator 的实现，但使用自身的 pure 组件。
        """
        try:
            # 1. 构建认证头
            auth_headers = self.header_builder.build_auth_header(context, credentials)

            # 2. 准备请求参数
            request_url = context.request_url
            method = getattr(context, 'method', 'GET').upper()
            json_data = getattr(context, 'json_data', None)
            custom_headers = getattr(context, 'custom_headers', {})

            # 合并认证头和自定义头
            merged_headers = {**custom_headers, **auth_headers}

            # 3. 发送带认证头的HTTP请求
            async with aiohttp.ClientSession() as session:
                request_kwargs = {'headers': merged_headers}
                if method in ["POST", "PUT", "PATCH"] and json_data is not None:
                    request_kwargs['json'] = json_data

                async with session.request(method, request_url, **request_kwargs) as response:
                    status = response.status
                    is_success = 200 <= status < 300
                    response_headers = dict(response.headers)

                    try:
                        response_body = await response.json()
                    except (aiohttp.ContentTypeError, json.JSONDecodeError):
                        response_body = {"text": await response.text()}

                    return is_success, json.dumps(response_headers), response_body

        except Exception as e:
            logger.error(f"Pure authenticate_request failed: {e}", exc_info=True)
            return False, "", {"error": str(e)}

    async def verify_response(self, auth_header: str, context: AuthenticationContext) -> Tuple[bool, str]:
        """
        验证来自服务端的响应认证头。
        这是对 BaseDIDAuthenticator 中抽象方法的实现。
        """
        try:
            if not auth_header or not auth_header.startswith("DIDWba "):
                return False, "Invalid or missing 'DIDWba' prefix in auth header."

            parts = auth_header[7:].split(',')
            if len(parts) != 6:
                return False, f"Invalid auth header format. Expected 6 parts, got {len(parts)}."

            did, nonce, timestamp, resp_did, key_id, signature = parts

            # 1. 验证时间戳
            if not verify_timestamp(timestamp):
                return False, "Timestamp verification failed."

            # 2. 验证响应的接收者是否是请求的发起者
            if resp_did != context.caller_did:
                return False, f"Response DID mismatch. Expected {context.caller_did}, got {resp_did}."

            # 3. 解析签名者的DID文档
            did_doc = await self.resolver.resolve_did_document(did)
            if not did_doc:
                return False, f"Failed to resolve DID document for {did}."

            # 4. 从DID文档中获取公钥
            public_key_b58 = None
            for vm in did_doc.verification_methods:
                if vm.get('id') == key_id:
                    public_key_b58 = vm.get('publicKeyMultibase')
                    break

            if not public_key_b58:
                return False, f"Public key with id {key_id} not found in DID document for {did}."

            # Multibase 'z' prefix indicates base58btc
            from anp_open_sdk.auth.utils import multibase_to_bytes
            public_key_bytes = multibase_to_bytes(public_key_b58)

            # 5. 验证签名
            payload_to_verify = ",".join(parts[:-1])
            is_valid = self.signer.verify_signature(payload_to_verify, signature, public_key_bytes)

            if not is_valid:
                return False, "Signature verification failed."

            return True, "Response verification successful."
        except Exception as e:
            logger.error(f"Error during response verification: {e}", exc_info=True)
            return False, f"Exception during verification: {e}"

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

        from urllib.parse import urlparse
        parsed_url = urlparse(url_str)
        domain = parsed_url.netloc.split(':')[0]
        return domain

    async def verify_request_header(self, auth_header: str, context: AuthenticationContext) -> Tuple[bool, str]:
        """
        验证来自客户端的请求认证头 (服务端使用)。
        """
        try:
            parsed_header = self.header_builder.parse_auth_header(auth_header)
            if not parsed_header:
                return False, "Invalid or unparsable auth header."
            # 根据认证类型检查必需字段
            header_keys = set(parsed_header.keys())
            one_way_keys = {"did", "nonce", "timestamp", "verification_method", "signature"}
            two_way_keys = one_way_keys.union({"resp_did"})

            # Check if the header contains exactly the keys for one-way or two-way auth
            if header_keys != one_way_keys and header_keys != two_way_keys:
                return False, "Auth header is missing or contains invalid fields."

            did = parsed_header['did']
            nonce = parsed_header['nonce']
            timestamp = parsed_header['timestamp']
            verification_method_fragment = parsed_header['verification_method']
            signature = parsed_header['signature']
            resp_did_from_header = parsed_header.get('resp_did')

            # 1. 验证时间戳
            if not verify_timestamp(timestamp):
                return False, "Timestamp verification failed."

            # 2. 验证 Nonce
            if not is_valid_server_nonce(nonce):
                return False, "Invalid or reused nonce."

            # 3. 如果是双向认证，验证目标DID
            if resp_did_from_header:
                if resp_did_from_header != context.target_did:
                    return False, f"Response DID mismatch. Header has {resp_did_from_header}, server is {context.target_did}."

            # 4. 解析签名者的DID文档
            did_doc = None
            try:
                from anp_open_sdk.auth.did_auth_wba_custom_did_resolver import resolve_local_did_document
                from agent_connect.authentication.did_wba import resolve_did_wba_document
                from anp_open_sdk.auth.schemas import DIDDocument

                did_doc_dict = await resolve_local_did_document(did)
                if not did_doc_dict:
                    did_doc_dict = await resolve_did_wba_document(did)

                if did_doc_dict:
                    did_doc = DIDDocument(
                        **did_doc_dict,
                        raw_document=did_doc_dict
                    )
            except Exception as e:
                logger.error(f"Failed to resolve DID document for {did}: {e}")
                return False, f"Failed to resolve DID document for {did}."

            if not did_doc:
                return False, f"Failed to resolve DID document for {did}."

            # 5. 获取公钥
            public_key_bytes = did_doc.get_public_key_bytes_by_fragment(verification_method_fragment)
            if not public_key_bytes:
                return False, f"Public key with fragment {verification_method_fragment} not found in DID document for {did}."
            service_domain = self._get_domain(context.request_url)

            # 6. 重构签名内容并验证签名
            data_to_sign = {
                "nonce": nonce,
                "timestamp": timestamp,
                "service": service_domain,
                "did": did,
            }
            if resp_did_from_header:
                data_to_sign["resp_did"] = resp_did_from_header


            canonical_json_bytes = jcs.canonicalize(data_to_sign)

            payload_to_verify = hashlib.sha256(canonical_json_bytes).digest()
            logger.info(
                f"\nData to verify:{data_to_sign},\npayload_to_verify_hash:{payload_to_verify},\npublic_bytes:{public_key_bytes}")

            is_valid = self.signer.verify_signature(payload_to_verify, signature, public_key_bytes)

            if not is_valid:
                return False, "Signature verification failed."

            return True, "Request verification successful."
        except Exception as e:
            logger.error(f"Error during request header verification: {e}", exc_info=True)
            return False, f"Exception during verification: {e}"


    async def verify_response_header(self, auth_header: str, expected_sender_did: str) -> bool:
        """
        验证来自服务端的响应头。
        这是 check_response_DIDAtuhHeader 的纯净替代品。
        """
        if not auth_header or not auth_header.startswith("DIDWba "):
            return False

        parts = auth_header[7:].split(',')
        if len(parts) != 6:  # 响应头必须是双向的
            return False

        did, nonce, timestamp, resp_did, key_id, signature = parts

        if did != expected_sender_did:
            return False

        if not verify_timestamp(timestamp):
            return False

        # 使用注入的解析器获取公钥
        did_doc = await self.resolver.resolve_did_document(did)
        if not did_doc:
            return False

        public_key_bytes = did_doc.get_public_key_bytes(key_id)
        if not public_key_bytes:
            return False

        payload_to_verify = ",".join(parts[:-1])
        return self.signer.verify_signature(payload_to_verify, signature, public_key_bytes)


def create_pure_authenticator(resolver: BaseDIDResolver) -> BaseDIDAuthenticator:
    """工厂函数，创建无依赖的认证器。"""
    signer = PureWBADIDSigner()
    header_builder = PureWBAAuthHeaderBuilder(signer)
    base_auth = PureWBAAuth()
    return PureWBADIDAuthenticator(resolver, signer, header_builder, base_auth)
