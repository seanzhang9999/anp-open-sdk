# anp_open_sdk/auth_methods/wba/implementation.py
import base64
import json
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple

from anp_open_sdk.core.auth.base import BaseDIDAuthenticator, BaseDIDResolver, BaseDIDSigner, BaseAuthHeaderBuilder, \
    BaseAuth
from anp_open_sdk.core.auth.schemas import AuthenticationContext, DIDCredentials, DIDDocument
from anp_open_sdk.core.auth.utils import generate_nonce, verify_timestamp

logger = logging.getLogger(__name__)


# --- 纯粹的WBA认证逻辑实现 ---

class PureWBADIDSigner(BaseDIDSigner):
    """纯净的WBA DID签名器，只处理内存中的字节。"""

    def sign_payload(self, payload: str, private_key_bytes: bytes) -> str:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        private_key_obj = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        signature_bytes = private_key_obj.sign(payload.encode('utf-8'))
        return base64.b64encode(signature_bytes).decode('utf-8')

    def verify_signature(self, payload: str, signature: str, public_key_bytes: bytes) -> bool:
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            public_key_obj = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            signature_bytes = base64.b64decode(signature)
            public_key_obj.verify(signature_bytes, payload.encode('utf-8'))
            return True
        except Exception as e:
            logger.error(f"签名验证失败: {e}")
            return False


class PureWBAAuthHeaderBuilder(BaseAuthHeaderBuilder):
    """纯净的WBA认证头构建器。"""

    def __init__(self, signer: BaseDIDSigner):
        self.signer = signer

    def build_auth_header(self, context: AuthenticationContext, credentials: DIDCredentials) -> Dict[str, str]:
        nonce = generate_nonce()
        timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        key_id = credentials.key_id

        parts = [credentials.did, nonce, timestamp]
        if context.use_two_way_auth and context.target_did:
            parts.append(context.target_did)
        parts.append(key_id)

        payload_to_sign = ",".join(parts)
        signature = self.signer.sign_payload(payload_to_sign, credentials.private_key_bytes)

        header_parts = parts + [signature]
        auth_header_value = ",".join(header_parts)
        return {"Authorization": f"DIDWba {auth_header_value}"}


class PureWBAAuth(BaseAuth):
    """纯净的WBA认证头解析器。"""

    def extract_did_from_auth_header(self, auth_header: str) -> Tuple[Optional[str], Optional[str]]:
        if not auth_header or not auth_header.startswith("DIDWba "):
            return None, None

        parts = auth_header[7:].split(',')
        # 双向: did,nonce,ts,resp_did,keyid,sig (6 parts)
        # 单向: did,nonce,ts,keyid,sig (5 parts)
        if len(parts) == 6:
            return parts[0], parts[3]  # caller_did, target_did
        elif len(parts) == 5:
            return parts[0], None  # caller_did
        return None, None


class PureWBADIDAuthenticator(BaseDIDAuthenticator):
    """
    完全独立的WBA认证器，不依赖agent_connect。
    它依赖于一个外部的DIDResolver来获取公钥。
    """

    def __init__(self, resolver: BaseDIDResolver):
        signer = PureWBADIDSigner()
        header_builder = PureWBAAuthHeaderBuilder(signer)
        base_auth = PureWBAAuth()
        super().__init__(resolver, signer, header_builder, base_auth)

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
    return PureWBADIDAuthenticator(resolver)