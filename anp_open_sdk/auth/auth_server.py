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
Authentication Server - Framework Integration Layer

This module provides FastAPI integration for the authentication system.
It uses the SDK layer (auth_manager) for business logic and the framework layer for I/O.
"""

from datetime import timezone, datetime, timedelta
from pathlib import Path
import random
import string
from typing import Optional, Callable, Any, Dict, Tuple
import fnmatch
import json

import jwt
from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse
from .schemas import AuthenticationContext, DIDDocument, DIDKeyPair, DIDCredentials
from .auth_manager import create_auth_manager, AuthMethod
from .pure_auth_server import get_auth_server
from anp_open_sdk_framework.adapters.did_auth_adapter import FrameworkDIDAuthAdapter
from ..config import get_global_config
from ..anp_sdk_agent import LocalAgent
from .token_nonce_auth import get_jwt_public_key, create_access_token


import logging
logger = logging.getLogger(__name__)



EXEMPT_PATHS = [
    "/docs", "/anp-nlp/", "/ws/", "/publisher/agents", "/agent/group/*",
    "/redoc", "/openapi.json", "/wba/hostuser/*", "/wba/user/*", "/", "/favicon.ico",
    "/agents/example/ad.json"
]

def is_exempt(path):
    return any(fnmatch.fnmatch(path, pattern) for pattern in EXEMPT_PATHS)


class AgentAuthServer:
    """
    Authentication server for FastAPI integration.
    
    Uses SDK layer (auth_manager) for business logic and framework layer for I/O.
    """
    
    def __init__(self):
        self.config = get_global_config()
        # Create framework adapter for I/O operations
        self.framework_adapter = FrameworkDIDAuthAdapter()
        # Create SDK layer authentication manager
        self.auth_manager = create_auth_manager(self.framework_adapter)

    async def verify_request(self, request: Request) -> Tuple[bool, Any, Optional[Dict[str, Any]]]:
        """Verify authentication request using SDK layer auth manager"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")

        # Handle Bearer token authentication
        if auth_header.startswith("Bearer "):
            req_did = request.headers.get("req_did")
            target_did = request.headers.get("resp_did")
            try:
                result = await self.handle_bearer_auth(auth_header, req_did, target_did)
                return True, "Bearer token verified", result
            except Exception as e:
                logger.debug(f"Bearer authentication failed: {e}")
                return False, str(e), {}

        # Extract DIDs for context
        # Try to extract DIDs from different auth methods
        req_did, target_did = None, None
        
        # For DID-WBA headers
        if auth_header.startswith("DIDWba "):
            from ..protocol.did_methods import create_wba_authenticator
            temp_auth = create_wba_authenticator()
            req_did, target_did = temp_auth.extract_dids_from_header(auth_header)

        if not req_did:
            return False, "Failed to extract DID from auth header", {}

        # Create authentication context
        context = AuthenticationContext(
            caller_did=req_did,
            target_did=target_did,
            request_url=str(request.url),
            method=request.method,
            custom_headers=dict(request.headers),
            json_data=None,
            use_two_way_auth=bool(target_did),
            domain=request.url.hostname
        )

        try:
            # Use SDK layer auth manager for verification
            auth_result = await self.auth_manager.verify_request(auth_header, context)
            
            if auth_result.success:
                response_data = await self.generate_auth_response(req_did, context.use_two_way_auth, target_did, context)
                return True, response_data, None
            else:
                return False, auth_result.message, {}
        except Exception as e:
            logger.debug(f"Server authentication verification failed: {e}", exc_info=True)
            return False, str(e), {}

    async def handle_bearer_auth(self, auth_header: str, req_did, resp_did) -> Dict:
        """Handle Bearer token authentication using framework layer"""
        try:
            if auth_header.startswith("Bearer "):
                token_body = auth_header[7:]
            else:
                token_body = auth_header

            # Check cached token using framework adapter
            token_info = await self.framework_adapter.token_storage.get_token(req_did, resp_did)
            
            if token_info:
                # Token found in cache and is valid
                if token_body == token_info["token"]:
                    logger.debug(f"Token for {req_did} found in cache and is valid")
                    return {
                        "access_token": auth_header,
                        "token_type": "bearer", 
                        "req_did": req_did,
                        "resp_did": resp_did,
                    }
                else:
                    logger.debug(f"Token mismatch for {req_did}")
                    raise HTTPException(status_code=401, detail="Invalid token")
            else:
                # Verify JWT token (file I/O for public key)
                resp_did_agent = LocalAgent.from_did(resp_did)
                public_key = get_jwt_public_key(resp_did_agent.jwt_public_key_path)
                if not public_key:
                    logger.debug("Failed to load JWT public key")
                    raise HTTPException(status_code=500, detail="Internal server error during token verification")

                jwt_algorithm = self.config.anp_sdk.jwt_algorithm

                payload = jwt.decode(
                    token_body,
                    public_key,
                    algorithms=[jwt_algorithm]
                )

                # Validate JWT payload
                required_fields = ["req_did", "resp_did", "exp"]
                for field in required_fields:
                    if field not in payload:
                        raise HTTPException(status_code=401, detail=f"Token missing required field: {field}")

                if payload["req_did"] != req_did:
                    raise HTTPException(status_code=401, detail="req_did mismatch")
                if payload["resp_did"] != resp_did:
                    raise HTTPException(status_code=401, detail="resp_did mismatch")

                now = datetime.now(timezone.utc).timestamp()
                if payload["exp"] < now:
                    raise HTTPException(status_code=401, detail="Token expired")

                logger.debug(f"JWT verification successful for {req_did}")
                return {
                    "access_token": auth_header,
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

async def generate_auth_response(did: str, is_two_way_auth: bool, resp_did: str, context: AuthenticationContext = None):
    resp_did_agent = LocalAgent.from_did(resp_did)
    config = get_global_config()

    from anp_open_sdk.auth.token_nonce_auth import create_access_token
    expiration_time = config.anp_sdk.token_expire_time
    access_token = create_access_token(
        resp_did_agent.jwt_private_key_path,
        data={"req_did": did, "resp_did": resp_did},
        expires_delta=expiration_time
    )
    resp_did_agent.contact_manager.store_token_to_remote(did, access_token, expiration_time)

    resp_did_auth_header = None
    if is_two_way_auth:
        try:
            did_doc_path = Path(resp_did_agent.did_document_path)
            pk_path = Path(resp_did_agent.private_key_path)

            if did_doc_path.exists() and pk_path.exists():
                with open(did_doc_path, 'r') as f:
                    did_doc_raw = json.load(f)
                # 从 DID 文档中获取 key_id
                key_id_full = did_doc_raw.get('verificationMethod', [{}])[0].get('id')
                if not key_id_full:
                    raise ValueError("无法从DID文档中找到 verificationMethod ID")

                # key_id 通常是 '#' 后面的部分
                key_id = key_id_full.split('#')[-1]

                # 使用 schemas.py 中提供的工厂方法来创建完整的密钥对
                key_pair = DIDKeyPair.from_file_path(str(pk_path), key_id)

                did_doc = DIDDocument(**did_doc_raw, raw_document=did_doc_raw)

                # 正确地创建 DIDCredentials 实例
                server_credentials = DIDCredentials(
                    did=did_doc.id,
                    did_document=did_doc,
                    key_pairs={key_pair.key_id: key_pair}
                )

                # 使用真实的请求URL，如果context可用的话
                request_url = context.request_url if context else "http://virtual.WBAback:9999"
                
                response_context = AuthenticationContext(
                    caller_did=resp_did,
                    target_did=did,
                    request_url=request_url,
                    use_two_way_auth=True
                )

                signer = PureWBADIDSigner()
                header_builder = PureWBAAuthHeaderBuilder(signer)
                resp_did_auth_header = header_builder.build_auth_header(response_context, server_credentials)
            else:
                logger.warning(f"resp_did的DID文档或私钥不存在: {did_doc_path} or {pk_path}")

        except Exception as e:
            logger.error(f"为 {resp_did} 生成双向认证头时出错: {e}", exc_info=True)

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


async def authenticate_request(request: Request, auth_server: AgentAuthServer) -> Optional[dict]:
    if request.url.path == "/wba/adapter_auth":
        logger.debug(f"安全中间件拦截/wba/auth进行认证")
        success, msg, _ = await auth_server.verify_request(request)
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
    success, msg, _ = await auth_server.verify_request(request)
    if not success:
        raise HTTPException(status_code=401, detail=f"认证失败: {msg}")
    return msg

async def auth_middleware(request: Request, call_next: Callable, auth_method: str = "wba" ) -> Response:
    try:
        auth_server = get_auth_server(auth_method)
        response_auth = await authenticate_request(request, auth_server)
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
        logger.debug(f"Unexpected error in adapter_auth middleware: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
