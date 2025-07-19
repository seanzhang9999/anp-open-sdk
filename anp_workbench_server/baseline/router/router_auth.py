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
Authentication API router.
"""
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import logging
logger = logging.getLogger(__name__)

from typing import Dict
from fastapi import APIRouter, Request, HTTPException

# 导入核心处理函数
from anp_servicepoint.extend_service_handler.auth_service_handler import process_authentication

router = APIRouter(tags=["authentication"])



@router.get("/wba/auth", summary="DID WBA authentication endpoint")
async def test_endpoint(request: Request) -> Dict:
    """
    Test endpoint for DID WBA authentication.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dict: Test result
    """
    # 从请求中提取必要参数
    req_did = request.query_params.get("req_did", "demo_caller")
    resp_did = request.query_params.get("resp_did", "demo_responser")

    # 获取认证头
    auth_header = request.state.headers.get("authorization", "") if hasattr(request.state, "headers") else None

    # 调用核心处理函数
    success, result = process_authentication(req_did, resp_did, auth_header)

    # 处理结果
    if not success:
        raise HTTPException(status_code=401, detail=result.get("message", "Authentication failed"))

    return result
    
    
