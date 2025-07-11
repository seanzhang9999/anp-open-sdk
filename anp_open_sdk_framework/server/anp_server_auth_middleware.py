import fnmatch
import json
from typing import Callable, Optional

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from anp_open_sdk.did.did_tool import extract_did_from_auth_header, AuthenticationContext
from anp_open_sdk.auth.auth_server import _verify_bearer_token, _verify_wba_header

import logging
logger = logging.getLogger(__name__)

EXEMPT_PATHS = [
    "/docs", "/anp-nlp/", "/ws/", "/publisher/agents", "/agent/group/*",
    "/redoc", "/openapi.json", "/wba/hostuser/*", "/wba/user/*", "/", "/favicon.ico",
    "/agents/example/ad.json","/wba/auth"
]


async def auth_middleware(request: Request, call_next: Callable, auth_method: str = "wba" ) -> Response:
    try:
        logger.debug(f"auth_middleware -- get: {request.url}")

        auth_passed,msg,response_auth = await _authenticate_request(request)

        headers = dict(request.headers)
        request.state.headers = headers

        if auth_passed == True:
            if response_auth is not None:
                response = await call_next(request)
                response.headers['authorization'] = json.dumps(response_auth) if response_auth else ""
                return response
            else:
                return await call_next(request)
        elif auth_passed == "NotSupport":
            return JSONResponse(
                status_code=202,
                content={"detail": f"{msg}"}
            )
        else:
            return JSONResponse(
                status_code=401,
                content={"detail": f"{msg}"}
            )


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
    for exempt_path in EXEMPT_PATHS:
        if exempt_path == "/" and request.url.path == "/":
            return True, "exempt url", {}
        elif request.url.path == exempt_path or (exempt_path != '/' and exempt_path.endswith('/') and request.url.path.startswith(exempt_path)):
            return True, "exempt url", {}
        elif is_exempt(request.url.path):
            return True, "exempt url", {}
    logger.debug(f"安全中间件拦截检查url:\n{request.url}")

    # 提取所有需要的信息
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
            return False, f"exception {e}", {}


    req_did, target_did = extract_did_from_auth_header(auth_header)
    use_two_way_auth = True
    if target_did is None:
        use_two_way_auth = False
        # 现在的token生成需要依赖resp_did的jwt私钥，因此必须获取
        # 除了query_params，还可以由服务器开发者根据上下文指定resp_did
        target_did = request.query_params.get("resp_did","")

    if target_did == "":
        msg = "error: Cannot accept request that do not mention resp_did"
        return "NotSupport", msg, {}

    if ":hostuser:" in target_did:
        # 托管DID，未来要做转发，没有转发时候直接拒绝
        msg = "error: Cannot accept request to hosted DID"
        return "NotSupport", msg, {}

    context = AuthenticationContext(
        caller_did=req_did,
        target_did=target_did,
        request_url=str(request.url),
        method=request.method,
        custom_headers=dict(request.headers),
        json_data=None,
        use_two_way_auth=use_two_way_auth,
        domain = request.url.hostname)
    try:
        success, result = await _verify_wba_header(auth_header, context)
        if success :
            return True, "auth passed", result
        else:
            return False, "auth failed", result


    except Exception as e:
            logger.debug(f"wba验证失败: {e}")
            return False, str(e), {}
