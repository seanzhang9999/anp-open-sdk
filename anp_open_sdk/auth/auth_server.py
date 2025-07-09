# Copyright 2024 ANP Open SDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Authentication middleware module.
"""


import fnmatch
import json
import logging
from datetime import timezone
from pathlib import Path
from typing import Optional, Callable, Any, Tuple

import jwt
from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse


from anp_open_sdk.config import get_global_config
from .auth_client import _resolve_did_document_insecurely
from ..did_tool import AuthenticationContext, create_did_auth_header_from_path, get_jwt_public_key, \
    extract_did_from_auth_header, create_access_token

logger = logging.getLogger(__name__)

from datetime import datetime
from typing import Dict

VALID_SERVER_NONCES: Dict[str, datetime] = {}

# ... rest of code ...
from ..anp_user import ANPUser


EXEMPT_PATHS = [
    "/docs", "/anp-nlp/", "/ws/", "/publisher/agents", "/agent/group/*",
    "/redoc", "/openapi.json", "/wba/hostuser/*", "/wba/user/*", "/", "/favicon.ico",
    "/agents/example/ad.json"
]
async def auth_middleware(request: Request, call_next: Callable, auth_method: str = "wba" ) -> Response:
    try:
        response_auth = await _authenticate_request(request)

        headers = dict(request.headers)
        request.state.headers = headers

        if response_auth is not None:
            response = await call_next(request)
            response.headers['authorization'] = json.dumps(response_auth) if response_auth else ""
            return response
        else:
            return await call_next(request)

    except HTTPException as exc:
        logger.debug(f"Authentication error: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    except Exception as e:
        logger.debug(f"Unexpected error in auth middleware: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
def is_exempt(path):
    return any(fnmatch.fnmatch(path, pattern) for pattern in EXEMPT_PATHS)
async def _authenticate_request(request: Request) -> Optional[dict]:
    if request.url.path == "/wba/auth":
        logger.debug(f"安全中间件拦截/wba/auth进行认证")
        success, msg = await _verify_auth_header(request)
        if not success:
            raise HTTPException(status_code=401, detail=f"认证失败: {msg}")
        return msg
    else:
        for exempt_path in EXEMPT_PATHS:
            if exempt_path == "/" and request.url.path == "/":
                return None
            elif request.url.path == exempt_path or (exempt_path != '/' and exempt_path.endswith('/') and request.url.path.startswith(exempt_path)):
                return None
            elif is_exempt(request.url.path):
                return None
    logger.debug(f"安全中间件拦截检查url:\n{request.url}")
    success, msg = await _verify_auth_header(request)
    if not success:
        raise HTTPException(status_code=401, detail=f"认证失败: {msg}")
    return msg
async def _verify_auth_header(request: Request) -> (bool, str, Dict[str, Any]):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if auth_header and auth_header.startswith("Bearer "):
        req_did =  request.headers.get("req_did")
        target_did =request.headers.get("resp_did")
        token = auth_header[len("Bearer "):]
        try:
            result = await _verify_bearer_token(token, req_did, target_did)
            return True, "Bearer token verified", result
        except Exception as e:
            logger.debug(f"Bearer认证失败: {e}")
            return False, str(e), {}
    req_did, target_did = extract_did_from_auth_header(auth_header)
    context = AuthenticationContext(
        caller_did=req_did,
        target_did=target_did,
        request_url=str(request.url),
        method=request.method,
        custom_headers=dict(request.headers),
        json_data=None,
        use_two_way_auth=True,
        domain = request.url.hostname)
    try:
        success, msg = await _verify_wba_header(auth_header, context)
        return success, msg
    except Exception as e:
            logger.debug(f"服务端认证验证失败: {e}")
            return False, str(e), {}
async def _verify_wba_header(auth_header: str, context: AuthenticationContext) -> Tuple[bool, str]:
    """验证WBA响应（借鉴 handle_did_auth 主要认证逻辑）"""
    try:
        from anp_open_sdk.agent_connect_hotpatch.authentication.did_wba import (
            extract_auth_header_parts_two_way, verify_auth_header_signature_two_way, resolve_did_wba_document
        )

        # 1. 尝试解析为两路认证
        try:
            header_parts = extract_auth_header_parts_two_way(auth_header)
            if not header_parts:
                return False, "Invalid authorization header format"
            did, nonce, timestamp, resp_did, keyid, signature = header_parts
            is_two_way_auth = True
        except (ValueError, TypeError) as e:
            # 回退到标准认证
            try:
                from agent_connect.authentication.did_wba import extract_auth_header_parts
                header_parts = extract_auth_header_parts(auth_header)
                if not header_parts or len(header_parts) < 4:
                    return False, "Invalid standard authorization header"
                did, nonce, timestamp, keyid, signature = header_parts
                resp_did = None
                is_two_way_auth = False
            except Exception as fallback_error:
                return False, f"Authentication parsing failed: {fallback_error}"

        # 2. 验证时间戳
        config = get_global_config()
        nonce_expire_minutes = config.anp_sdk.nonce_expire_minutes
        from datetime import datetime, timezone
        try:
            request_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            current_time = datetime.now(timezone.utc)
            time_diff = abs((current_time - request_time).total_seconds() / 60)
            if time_diff > nonce_expire_minutes:
                return False, f"Timestamp expired. Current time: {current_time}, Request time: {request_time}, Difference: {time_diff} minutes"
        except Exception as e:
            return False, f"Invalid timestamp: {e}"

        # Verify nonce validity
        if not is_valid_server_nonce(nonce):
            logger.debug(f"Invalid or expired nonce: {nonce}")
            return False, f"Invalid nonce: {e}"
        else:
            logger.debug(f"nonce通过防重放验证{nonce}")

        # 3. 解析DID文档
        did_document = await _resolve_did_document_insecurely(did)
        if not did_document:
            try:
                did_document = await resolve_did_wba_document(did)
            except Exception as e:
                return False, f"Failed to resolve DID document: {e}"
        if not did_document:
            return False, "Failed to resolve DID document"

        # 4. 验证签名
        try:
            if is_two_way_auth:
                is_valid, message = verify_auth_header_signature_two_way(
                    auth_header=auth_header,
                    did_document=did_document,
                    service_domain=context.domain if hasattr(context, 'domain') else None
                )
            else:
                from agent_connect.authentication.did_wba import verify_auth_header_signature
                is_valid, message = verify_auth_header_signature(
                    auth_header=auth_header,
                    did_document=did_document,
                    service_domain=context.domain if hasattr(context, 'domain') else None
                )
            if not is_valid:
                return False, f"Invalid signature: {message}"
        except Exception as e:
            return False, f"Error verifying signature: {e}"
        from ..auth.auth_server import _generate_wba_auth_response

        header_parts = await _generate_wba_auth_response	(did, is_two_way_auth, resp_did)
        return True, header_parts
    except Exception as e:
        return False, f"Exception in verify_response: {e}"
async def _verify_bearer_token(token: str, req_did, resp_did) -> Dict:
    """
    Handle Bearer token authentication.

    Args:
        token: JWT token string
        req_did: 请求方DID
        resp_did: 响应方DID

    Returns:
        Dict: Token payload with DID information

    Raises:
        HTTPException: When token is invalid
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token_body = token[7:]
        else:
            token_body = token

        resp_did_agent = ANPUser.from_did(resp_did)
        token_info = resp_did_agent.contact_manager.get_token_to_remote(req_did)

        # 检查LocalAgent中是否存储了该req_did的token信息

        if token_info:
            # Convert expires_at string to datetime object and ensure it's timezone-aware
            try:
                if isinstance(token_info["expires_at"], str):
                    expires_at_dt = datetime.fromisoformat(token_info["expires_at"])
                else:
                    expires_at_dt = token_info["expires_at"]  # Assuming it's already a datetime object from
                # Ensure the datetime is timezone-aware (assume UTC if naive)
                if expires_at_dt.tzinfo is None:
                    logger.warning(f"Stored expires_at for {req_did} is timezone-naive. Assuming UTC.")
                    expires_at_dt = expires_at_dt.replace(tzinfo=timezone.utc)
                token_info["expires_at"] = expires_at_dt
            except ValueError as e:
                logger.debug(f"Failed to parse expires_at string '{token_info['expires_at']}': {e}")
                raise HTTPException(status_code=401, detail="Invalid token expiration format")

            # 检查token是否被撤销
            if token_info["is_revoked"]:
                logger.debug(f"Token for {req_did} has been revoked")
                raise HTTPException(status_code=401, detail="Token has been revoked")

            # 检查token是否过期（使用存储的过期时间，而不是token中的时间）
            if datetime.now(timezone.utc) > token_info["expires_at"]:
                logger.debug(f"Token for {req_did} has expired")
                raise HTTPException(status_code=401, detail="Token has expired")

            # 验证token是否匹配
            if token_body != token_info["token"]:
                logger.debug(f"Token mismatch for {req_did}")
                raise HTTPException(status_code=401, detail="Invalid token")

            logger.debug(f" {req_did}提交的token在LocalAgent存储中未过期,快速通过!")
        else:
            # 如果LocalAgent中没有存储token信息，则使用公钥验证

            public_key = get_jwt_public_key(resp_did_agent.jwt_public_key_path)
            if not public_key:
                logger.debug("Failed to load JWT public key")
                raise HTTPException(status_code=500, detail="Internal server error during token verification")

            config = get_global_config()
            jwt_algorithm = config.anp_sdk.jwt_algorithm

            # Decode and verify the token using the public key
            payload = jwt.decode(
                token_body,
                public_key,
                algorithms=[jwt_algorithm]
            )

            # Check if token contains required fields and values
            required_fields = ["req_did", "resp_did", "exp"]
            for field in required_fields:
                if field not in payload:
                    raise HTTPException(status_code=401, detail=f"Token missing required field: {field}")

            # 可选：进一步校验 req_did、resp_did 的值
            if payload["req_did"] != req_did:
                raise HTTPException(status_code=401, detail="req_did mismatch")
            if payload["resp_did"] != resp_did:
                raise HTTPException(status_code=401, detail="resp_did mismatch")

            # 校验 exp 是否过期
            now = datetime.now(timezone.utc).timestamp()
            if payload["exp"] < now:
                raise HTTPException(status_code=401, detail="Token expired")

            logger.debug(f"LocalAgent存储中未找到{req_did}提交的token,公钥验证通过")
        return {
            "access_token": token,
            "token_type": "bearer",
            "req_did": req_did,
            "resp_did": resp_did,
        }

    except jwt.PyJWTError as e:
        logger.debug(f"JWT verification error: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        logger.debug(f"Token verification error: {e}")
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")
def is_valid_server_nonce(nonce: str) -> bool:
    """
    Check if a nonce is valid and not expired.
    Each nonce can only be used once (proper nonce behavior).
    Args:
        nonce: The nonce to check
    Returns:
        bool: Whether the nonce is valid
    """
    from datetime import datetime, timezone, timedelta
    try:
        config = get_global_config()
        nonce_expire_minutes = config.anp_sdk.nonce_expire_minutes
    except Exception:
        nonce_expire_minutes = 5

    current_time = datetime.now(timezone.utc)
    # Clean up expired nonces first
    expired_nonces = [
        n for n, t in VALID_SERVER_NONCES.items()
        if current_time - t > timedelta(minutes=nonce_expire_minutes)
    ]
    for n in expired_nonces:
        del VALID_SERVER_NONCES[n]
    # If nonce was already used, reject it
    if nonce in VALID_SERVER_NONCES:
        logger.warning(f"Nonce already used: {nonce}")
        return False
    # Mark nonce as used
    VALID_SERVER_NONCES[nonce] = current_time
    logger.debug(f"Nonce accepted and marked as used: {nonce}")
    return True
async def _generate_wba_auth_response	(did, is_two_way_auth, resp_did):

    resp_did_agent = ANPUser.from_did(resp_did)

    # 生成访问令牌

    config = get_global_config()
    expiration_time = config.anp_sdk.token_expire_time
    access_token = create_access_token(
        resp_did_agent.jwt_private_key_path,
        data={"req_did": did, "resp_did": resp_did, "comments": "open for req_did"},
        expires_delta=expiration_time
    )
    resp_did_agent.contact_manager.store_token_to_remote(did, access_token, expiration_time)
    # logger.debug(f"认证成功，已生成访问令牌")
    # 如果resp_did存在，加载resp_did的DID文档并组装DID认证头
    resp_did_auth_header = None
    if resp_did and resp_did != "没收到":
        try:
            # 获取resp_did用户目录
            did_document_path = resp_did_agent.did_document_path
            private_key_path = resp_did_agent.private_key_path
              # 检查文件是否存在
            if Path(did_document_path).exists() and Path(private_key_path).exists():
                # 创建DID认证客户端
                resp_auth_header = create_did_auth_header_from_path(did_document_path, private_key_path)
                # 获取认证头（用于返回给req_did进行验证,此时 req是现在的did）
                target_url = "http://virtual.WBAback:9999"  # 使用当前请求的域名
                resp_did_auth_header = resp_auth_header.get_auth_header_two_way(target_url, did)
                # 打印认证头
            # logger.debug(f"Generated resp_did_auth_header: {resp_did_auth_header}")

            # logger.debug(f"成功加载resp_did的DID文档并生成认证头")
            else:
                logger.warning(f"resp_did的DID文档或私钥不存在: {did_document_path} or {private_key_path}")
        except Exception as e:
            logger.debug(f"加载resp_did的DID文档时出错: {e}")
            resp_did_auth_header = None
    if is_two_way_auth:
        return [
            {
                "access_token": access_token,
                "token_type": "bearer",
                "req_did": did,
                "resp_did": resp_did,
                "resp_did_auth_header": resp_did_auth_header
            }
        ]
    else:
        return f"bearer {access_token}"
