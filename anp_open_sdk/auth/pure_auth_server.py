"""
Pure Authentication Server Implementation

This implementation uses the layered architecture:
- Protocol layer: Pure DID authentication logic (no I/O)
- Framework layer: I/O operations (network, file, storage)

All I/O operations are delegated to the framework layer adapters.
"""

import json
import logging
from datetime import timezone, datetime
from typing import Optional, Callable, Any, Dict, Tuple
import fnmatch

import jwt
from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse

from anp_open_sdk.auth.schemas import AuthenticationContext, DIDDocument, DIDKeyPair, DIDCredentials
from anp_open_sdk.protocol.did_methods.wba import create_wba_authenticator
from anp_open_sdk_framework.adapters.did_auth_adapter import FrameworkDIDAuthAdapter
from anp_open_sdk.config import get_global_config
from anp_open_sdk.anp_sdk_agent import LocalAgent
from anp_open_sdk.auth.token_nonce_auth import get_jwt_public_key, create_access_token

logger = logging.getLogger(__name__)


EXEMPT_PATHS = [
    "/docs", "/anp-nlp/", "/ws/", "/publisher/agents", "/agent/group/*",
    "/redoc", "/openapi.json", "/wba/hostuser/*", "/wba/user/*", "/", "/favicon.ico",
    "/agents/example/ad.json"
]


def is_exempt(path):
    return any(fnmatch.fnmatch(path, pattern) for pattern in EXEMPT_PATHS)


class PureAgentAuthServer:
    """
    Pure authentication server using layered architecture.
    
    - Uses protocol layer for pure authentication logic
    - Uses framework layer for all I/O operations
    """
    
    def __init__(self, auth_method: str = "wba"):
        self.config = get_global_config()
        self.auth_method = auth_method
        
        # Create pure authenticator (no I/O)
        self.authenticator = create_wba_authenticator()
        
        # Create framework adapter for I/O operations
        self.framework_adapter = FrameworkDIDAuthAdapter()

    async def verify_request(self, request: Request) -> Tuple[bool, Any, Optional[Dict[str, Any]]]:
        """Verify authentication request using layered architecture"""
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(status_code=401, detail="Missing Authorization header")

        # Handle Bearer token authentication (I/O via framework)
        if auth_header.startswith("Bearer "):
            req_did = request.headers.get("req_did")
            target_did = request.headers.get("resp_did")
            token = auth_header[len("Bearer "):]
            try:
                result = await self.handle_bearer_auth(token, req_did, target_did)
                return True, "Bearer token verified", result
            except Exception as e:
                logger.debug(f"Bearer authentication failed: {e}")
                return False, str(e), {}

        # Handle DID-based authentication
        req_did, target_did = self.authenticator.extract_dids_from_header(auth_header)
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
            # Use framework adapter for verification (pure logic + I/O)
            success, msg = await self.framework_adapter.verify_request_with_io(
                self.authenticator, auth_header, context
            )
            
            if success:
                response_data = await self.generate_auth_response(req_did, context.use_two_way_auth, target_did, context)
                return True, response_data, None
            else:
                return False, msg, {}
        except Exception as e:
            logger.debug(f"Server authentication verification failed: {e}", exc_info=True)
            return False, str(e), {}

    async def handle_bearer_auth(self, token: str, req_did, resp_did) -> Dict:
        """Handle Bearer token authentication - uses framework layer for I/O"""
        try:
            if token.startswith("Bearer "):
                token_body = token[7:]
            else:
                token_body = token

            # Check cached token (I/O operation via framework)
            token_info = await self.framework_adapter.token_storage.get_token(req_did, resp_did)
            
            if token_info:
                # Token found in cache and is valid
                if token_body == token_info["token"]:
                    logger.debug(f"Token for {req_did} found in cache and is valid")
                    return {
                        "access_token": token,
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

    async def generate_auth_response(self, did: str, is_two_way_auth: bool, resp_did: str, context: AuthenticationContext = None):
        """Generate authentication response - uses file I/O for credentials"""
        resp_did_agent = LocalAgent.from_did(resp_did)
        config = get_global_config()

        # Create access token (file I/O for private key)
        expiration_time = config.anp_sdk.token_expire_time
        access_token = create_access_token(
            resp_did_agent.jwt_private_key_path,
            data={"req_did": did, "resp_did": resp_did},
            expires_delta=expiration_time
        )
        
        # Store token (I/O operation via framework)
        await self.framework_adapter.token_storage.store_token(
            did, resp_did, {
                "token": access_token,
                "expires_delta": expiration_time
            }
        )

        resp_did_auth_header = None
        if is_two_way_auth:
            try:
                # Load credentials (file I/O)
                credentials = DIDCredentials.from_user_data(resp_did_agent)
                
                # Use pure authenticator to build auth header
                request_url = context.request_url if context else "http://virtual.WBAback:9999"
                response_context = AuthenticationContext(
                    caller_did=resp_did,
                    target_did=did,
                    request_url=request_url,
                    use_two_way_auth=True
                )

                resp_did_auth_header = self.authenticator.build_auth_header(response_context, credentials)
            except Exception as e:
                logger.error(f"Error generating two-way auth header for {resp_did}: {e}", exc_info=True)

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


# Cache for auth servers
_auth_server_cache: Dict[str, PureAgentAuthServer] = {}


def get_auth_server(auth_method: str = "wba") -> PureAgentAuthServer:
    """Get cached auth server instance"""
    if auth_method not in _auth_server_cache:
        _auth_server_cache[auth_method] = PureAgentAuthServer(auth_method)
    return _auth_server_cache[auth_method]


async def authenticate_request(request: Request, auth_server: PureAgentAuthServer) -> Optional[dict]:
    """Authenticate request using pure auth server"""
    if request.url.path == "/wba/adapter_auth":
        logger.debug(f"Security middleware intercepted /wba/auth for authentication")
        success, msg, _ = await auth_server.verify_request(request)
        if not success:
            raise HTTPException(status_code=401, detail=f"Authentication failed: {msg}")
        return msg
    else:
        for exempt_path in EXEMPT_PATHS:
            if exempt_path == "/" and request.url.path == "/":
                return None
            elif request.url.path == exempt_path or (exempt_path != '/' and exempt_path.endswith('/') and request.url.path.startswith(exempt_path)):
                return None
            elif is_exempt(request.url.path):
                return None
    
    logger.debug(f"Security middleware checking URL: {request.url}")
    success, msg, _ = await auth_server.verify_request(request)
    if not success:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {msg}")
    return msg


async def auth_middleware(request: Request, call_next: Callable, auth_method: str = "wba") -> Response:
    """Authentication middleware using pure auth server"""
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
        logger.debug(f"Unexpected error in auth middleware: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )