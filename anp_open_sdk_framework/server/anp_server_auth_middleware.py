import fnmatch
import json
from typing import Callable

from fastapi import HTTPException
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from anp_open_sdk.auth.auth_server import _authenticate_request

import logging
logger = logging.getLogger(__name__)

EXEMPT_PATHS = [
    "/docs", "/anp-nlp/", "/ws/", "/publisher/agents", "/agent/group/*",
    "/redoc", "/openapi.json", "/wba/hostuser/*", "/wba/user/*", "/", "/favicon.ico",
    "/agents/example/ad.json","/wba/auth", "/wba/hosted-did/*"
]


async def _check_permissions(self, request: Request, auth_info: dict) :
    """
    权限检查扩展点
    可以根据请求路径、方法、认证信息等进行权限判断
    """
    # 这里可以插入具体的权限检查逻辑
    # 比如基于角色的访问控制(RBAC)、基于属性的访问控制(ABAC)等
    return True,"success"



async def auth_middleware(request: Request, call_next: Callable, auth_method: str = "wba" ) -> Response:
    try:
        logger.debug(f"auth_middleware -- get: {request.url}")

        # Check exempt paths first
        for exempt_path in EXEMPT_PATHS:
            if exempt_path == "/" and request.url.path == "/":
                return await call_next(request)
            elif request.url.path == exempt_path or (exempt_path != '/' and exempt_path.endswith('/') and request.url.path.startswith(exempt_path)):
                return await call_next(request)
            elif is_exempt(request.url.path):
                return await call_next(request)
        # Only authenticate if not exempt
        auth_passed,msg,response_auth = await _authenticate_request(request)

        headers = dict(request.headers)
        request.state.headers = headers

        if auth_passed == True:
            if response_auth is not None:
                # 权限控制扩展点
                permission_result, error_message = await _check_permissions(request, response_auth)
                if not permission_result.allowed:
                    return JSONResponse(
                        status_code=403,
                        content={"error": "Permission denied", "message": error_message}
                    )
                response = await call_next(request)
                response.headers['authorization'] = json.dumps(response_auth) if response_auth else ""

                # 可以在这里添加权限相关的响应头
                if permission_result.additional_headers:
                    for key, value in permission_result.additional_headers.items():
                        response.headers[key] = value

                return response
            else:
                msg = "auth passed but there is no authz response,something is wrong"
                return JSONResponse(
                    status_code=500,
                    content={"detail": f"{msg}"}
                )
        elif auth_passed == "NotSupport":
            return JSONResponse(
                status_code=202,
                content={"detail": f"{msg}:{response_auth}"}
            )
        else:
            return JSONResponse(
                status_code=401,
                content={"detail": f"{msg}:{response_auth}"}
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
