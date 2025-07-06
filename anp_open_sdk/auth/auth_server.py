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
from .did_auth_base import BaseDIDAuthenticator, BaseDIDResolver
from .schemas import AuthenticationContext, DIDDocument, DIDKeyPair, DIDCredentials
from ..auth_methods.wba.implementation import PureWBADIDAuthenticator, PureWBADIDSigner, PureWBAAuthHeaderBuilder, PureWBAAuth
from ..config import get_global_config
from ..anp_sdk_agent import LocalAgent
from .token_nonce_auth import get_jwt_public_key
from .utils import is_valid_server_nonce, multibase_to_bytes # 从新位置导入


import logging
logger = logging.getLogger(__name__)



EXEMPT_PATHS = [
    "/docs", "/anp-nlp/", "/ws/", "/publisher/agents", "/agent/group/*",
    "/redoc", "/openapi.json", "/wba/hostuser/*", "/wba/user/*", "/", "/favicon.ico",
    "/agents/example/ad.json"
]

class LocalFileDIDResolver(BaseDIDResolver):
    async def resolve_did_document(self, did: str) -> Optional[DIDDocument]:
        try:
            agent = LocalAgent.from_did(did)
            did_doc_path = Path(agent.did_document_path)
            if did_doc_path.exists():
                with open(did_doc_path, 'r') as f:
                    raw_doc = json.load(f)
            return DIDDocument(
                did=raw_doc.get('id', did),
                verification_methods=raw_doc.get('verificationMethod', []),
                authentication=raw_doc.get('authentication', []),
                service_endpoints=raw_doc.get('service', []),
                raw_document=raw_doc
            )
        except Exception as e:
            logger.error(f"使用LocalFileDIDResolver解析DID失败: {did}, 错误: {e}")
            return None

    def supports_did_method(self, did: str) -> bool:
        return did.startswith("did:wba:") or did.startswith("did:key:")



def is_exempt(path):
    return any(fnmatch.fnmatch(path, pattern) for pattern in EXEMPT_PATHS)

def create_authenticator(auth_method: str = "wba") -> BaseDIDAuthenticator:
    if auth_method == "wba":
        resolver = LocalFileDIDResolver()
        signer = PureWBADIDSigner()
        header_builder = PureWBAAuthHeaderBuilder(signer)
        base_auth = PureWBAAuth()
        return PureWBADIDAuthenticator(resolver, signer, header_builder, base_auth)
    else:
        raise ValueError(f"Unsupported authentication method: {auth_method}")

_auth_server_cache: Dict[str, 'AgentAuthServer'] = {}

def get_auth_server(auth_method: str = "wba") -> 'AgentAuthServer':
    if auth_method not in _auth_server_cache:
        _auth_server_cache[auth_method] = AgentAuthServer(create_authenticator(auth_method))
    return _auth_server_cache[auth_method]

class AgentAuthServer:
    def __init__(self, authenticator: BaseDIDAuthenticator):
        self.config = get_global_config()
        self.authenticator = authenticator

    async def verify_request(self, request: Request) -> Tuple[bool, Any, Optional[Dict[str, Any]]]:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")

        if auth_header.startswith("Bearer "):
            req_did = request.headers.get("req_did")
            target_did = request.headers.get("resp_did")
            token = auth_header[len("Bearer "):]
            try:
                result = await self.handle_bearer_auth(token, req_did, target_did)
                return True, "Bearer token verified", result
            except Exception as e:
                logger.debug(f"Bearer认证失败: {e}")
                return False, str(e), {}

        req_did, target_did = self.authenticator.base_auth.extract_did_from_auth_header(auth_header)
        if not req_did:
            return False, "Failed to extract DID from auth header", {}

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
            success, msg = await self.authenticator.verify_request_header(auth_header, context)
            if success:
                response_data = await generate_auth_response(req_did, context.use_two_way_auth, target_did)
                return True, response_data, None
            else:
                return False, msg, {}
        except Exception as e:
            logger.debug(f"服务端认证验证失败: {e}", exc_info=True)
            return False, str(e), {}

    async def handle_bearer_auth(self, token: str, req_did, resp_did) -> Dict:
        try:
            if token.startswith("Bearer "):
                token_body = token[7:]
            else:
                token_body = token

            resp_did_agent = LocalAgent.from_did(resp_did)
            token_info = resp_did_agent.contact_manager.get_token_to_remote(req_did)

            if token_info:
                try:
                    if isinstance(token_info["expires_at"], str):
                        expires_at_dt = datetime.fromisoformat(token_info["expires_at"])
                    else:
                        expires_at_dt = token_info["expires_at"]
                    if expires_at_dt.tzinfo is None:
                        logger.warning(f"Stored expires_at for {req_did} is timezone-naive. Assuming UTC.")
                        expires_at_dt = expires_at_dt.replace(tzinfo=timezone.utc)
                    token_info["expires_at"] = expires_at_dt
                except ValueError as e:
                    logger.debug(f"Failed to parse expires_at string '{token_info['expires_at']}': {e}")
                    raise HTTPException(status_code=401, detail="Invalid token expiration format")

                if token_info["is_revoked"]:
                    logger.debug(f"Token for {req_did} has been revoked")
                    raise HTTPException(status_code=401, detail="Token has been revoked")

                if datetime.now(timezone.utc) > token_info["expires_at"]:
                    logger.debug(f"Token for {req_did} has expired")
                    raise HTTPException(status_code=401, detail="Token has expired")

                if token_body != token_info["token"]:
                    logger.debug(f"Token mismatch for {req_did}")
                    raise HTTPException(status_code=401, detail="Invalid token")

                logger.debug(f" {req_did}提交的token在LocalAgent存储中未过期,快速通过!")
            else:
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

async def generate_auth_response(did: str, is_two_way_auth: bool, resp_did: str):
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
                with open(pk_path, 'r') as f:
                    pk_data = json.load(f)

                key_id = did_doc_raw.get('verificationMethod', [{}])[0].get('id')
                private_key_b58 = pk_data.get('privateKeyMultibase')

                from .utils import multibase_to_bytes
                private_key_bytes = multibase_to_bytes(private_key_b58)

                server_credentials = DIDCredentials(
                    did_document=DIDDocument.parse_obj(did_doc_raw),
                    key_pairs=[DIDKeyPair(key_id=key_id, private_key=private_key_bytes)]
                )

                response_context = AuthenticationContext(
                    caller_did=resp_did,
                    target_did=did,
                    request_url="http://virtual.WBAback:9999",
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
