import json
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple

from .base_user_data import BaseUserData
from .base_transport import RequestContext, ResponseContext
from ..auth.schemas import DIDCredentials, AuthenticationContext, DIDDocument
from ..auth_methods.wba.implementation import create_pure_authenticator

from pydantic import ValidationError

logger = logging.getLogger(__name__)
@dataclass
class AuthResult:
    """封装认证流程的最终结果，供框架层使用。"""
    is_successful: bool
    status_code: int
    body: Any
    token_to_store: Optional[str] = None
    error_message: Optional[str] = None


class AuthFlowManager:
    """
    纯净的、内存中的认证流程管理器。
    严格实现了双向认证、回退、响应验证等核心逻辑。
    """

    def __init__(self, user_data: BaseUserData, resolver):
        self.user_data = user_data
        # 依赖注入一个纯净的解析器
        self.authenticator = create_pure_authenticator(resolver)

    async def prepare_request_context(
            self, target_did: str, url: str, method: str, json_data: Optional[Dict] = None,
            use_two_way_auth: bool = True
    ) -> RequestContext:
        """
        准备认证请求。这是 WBAAuthHeaderBuilder.build_auth_header 逻辑的纯净版。
        """
        # 1. 尝试使用Token (简化逻辑，实际可扩展)
        token = self.user_data.get_token_from_remote(target_did)
        if token:
            headers = {"Authorization": f"Bearer {token}", "req_did": self.user_data.did, "resp_did": target_did}
            return RequestContext(method=method, url=url, headers=headers, json_data=json_data)

        # 2. 如果没有Token，执行DID认证
        try:
            # 使用 DIDCredentials.from_user_data 方法创建凭证
            caller_credentials = DIDCredentials.from_user_data(self.user_data)
        except Exception as e:
            logger.error(f"Failed to create DIDCredentials from user_data: {e}")
            raise ValueError("user_data is incomplete for DID authentication.") from e

        context = AuthenticationContext(
            caller_did=caller_credentials.did_document.id,
            target_did=target_did,
            request_url=url,
            method=method,
            json_data=json_data,
            use_two_way_auth=use_two_way_auth
        )

        auth_headers = self.authenticator.header_builder.build_auth_header(context, caller_credentials)
        return RequestContext(method=method, url=url, headers=auth_headers, json_data=json_data)

    async def process_response(
            self, response: ResponseContext, target_did: str
    ) -> AuthResult:
        """
        处理响应，严格实现了响应头解析、签名验证和Token提取。
        """
        # 1. 处理HTTP级别的错误
        if response.status_code >= 400:
            return AuthResult(
                is_successful=False,
                status_code=response.status_code,
                body=response.json_data or response.text_data,
                error_message=f"HTTP Error {response.status_code}"
            )

        # 2. 解析响应头，提取Token和对方的认证信息
        # 这是 get_response_DIDAuthHeader_Token 的纯净实现
        auth_header_str = response.headers.get("Authorization")
        if not auth_header_str:
            # 可能是公开接口，直接成功
            return AuthResult(is_successful=True, status_code=200, body=response.json_data)

        auth_type, token, peer_auth_header = self._parse_response_header(auth_header_str)

        if not token:
            return AuthResult(is_successful=False, status_code=401, error_message="No token found in response")

        # 3. 如果是双向认证，验证对方的签名
        # 这是 check_response_DIDAtuhHeader 的纯净实现
        if auth_type == "TwoWayAuth":
            # 这里的 authenticator 需要一个纯净的 verify_signature 方法
            # 它依赖于一个 DID 解析器来获取对方的公钥
            is_peer_signature_valid = await self.authenticator.verify_signature_from_header(
                peer_auth_header, expected_sender_did = target_did
            )
            if not is_peer_signature_valid:
                return AuthResult(
                    is_successful=False,
                    status_code=401,
                    error_message="Peer DID signature verification failed."
                )

        # 4. 所有验证通过，返回成功结果
        return AuthResult(
            is_successful=True,
            status_code=response.status_code,
            body=response.json_data,
            token_to_store=token
        )

    def _parse_response_header(self, auth_header_str: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        get_response_DIDAuthHeader_Token 的纯净版本。
        返回 (认证类型, Token, 对方的认证头)
        """
        if auth_header_str.startswith('Bearer '):
            return "OneWayAuth", auth_header_str[7:], None

        try:
            auth_data = json.loads(auth_header_str)
            if isinstance(auth_data, list) and len(auth_data) > 0:
                token = auth_data[0].get("access_token")
                peer_auth_header = auth_data[0].get("resp_did_auth_header", {}).get("Authorization")
                if token and peer_auth_header:
                    return "TwoWayAuth", token, peer_auth_header
                elif token:
                    return "OneWayAuth", token, None
        except json.JSONDecodeError:
            pass  # Fallback to raw string handling if not JSON

        return None, None, None
