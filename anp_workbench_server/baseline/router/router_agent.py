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
import logging

logger = logging.getLogger(__name__)


from fastapi import Request, APIRouter

import sys
import os

# 导入或定义核心处理函数
from anp_servicepoint.core_service_handler.agent_service_handler import (
    process_group_request,
    process_agent_api_request,
    process_agent_message,
    get_all_groups
)


router = APIRouter(prefix="/agent", tags=["agent"])


# 添加群组相关路由
@router.post("/api/{did}/group/{group_id}/join")
async def handle_group_join(did: str, group_id: str, request: Request):
    """处理加入群组请求"""
    # 获取请求数据
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    req_did = request.query_params.get("req_did", "demo_caller")

    # 构造请求数据
    request_data = {
        **data,
        "req_did": req_did,
        "group_id": group_id
    }

    # 调用核心处理函数
    return await process_group_request(did, group_id, "join", request_data, request)


@router.post("/api/{did}/group/{group_id}/leave")
async def handle_group_leave(did: str, group_id: str, request: Request):
    """处理离开群组请求"""
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    req_did = request.query_params.get("req_did", "demo_caller")

    request_data = {
        **data,
        "req_did": req_did,
        "group_id": group_id
    }

    # 调用核心处理函数
    return await process_group_request(did, group_id, "leave", request_data, request)


@router.post("/api/{did}/group/{group_id}/message")
async def handle_group_message(did: str, group_id: str, request: Request):
    """处理群组消息"""
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    req_did = request.query_params.get("req_did", "demo_caller")

    request_data = {
        **data,
        "req_did": req_did,
        "group_id": group_id
    }

    # 调用核心处理函数
    return await process_group_request(did, group_id, "message", request_data, request)


@router.get("/api/{did}/group/{group_id}/connect")
async def handle_group_connect(did: str, group_id: str, request: Request):
    """处理群组连接请求（SSE）"""
    req_did = request.query_params.get("req_did", "demo_caller")

    request_data = {
        "req_did": req_did,
        "group_id": group_id
    }

    # 调用核心处理函数
    return await process_group_request(did, group_id, "connect", request_data, request)


@router.post("/api/{did}/group/{group_id}/members")
@router.get("/api/{did}/group/{group_id}/members")
async def handle_group_members(did: str, group_id: str, request: Request):
    """处理群组成员管理"""
    if request.method == "POST":
        data = await request.json() if request.headers.get("content-type") == "application/json" else {}
    else:
        data = {"action": "list"}

    req_did = request.query_params.get("req_did", "demo_caller")

    request_data = {
        **data,
        "req_did": req_did,
        "group_id": group_id
    }

    # 调用核心处理函数
    return await process_group_request(did, group_id, "members", request_data, request)


@router.get("/api/groups")
async def list_all_groups(request: Request):
    """列出所有群组"""
    # 调用核心处理函数
    return get_all_groups()


@router.post("/api/{did}/{subpath:path}")
async def handle_agent_api(did: str, subpath: str, request: Request):
    """处理Agent API调用 - 根据配置决定本地处理或转发"""
    # 获取请求数据
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}

    # 调用核心处理函数
    return await process_agent_api_request(did, subpath, data, request)


# 同样为消息处理添加路由
@router.post("/api/{did}/message/post")
async def handle_agent_message(did: str, request: Request):
    """处理Agent消息 - 根据配置决定本地处理或转发"""
    # 获取请求数据
    data = await request.json() if request.headers.get("content-type") == "application/json" else {}

    # 调用核心处理函数
    return await process_agent_message(did, data, request)


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))