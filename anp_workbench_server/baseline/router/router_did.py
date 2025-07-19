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
DID document API router with multi-domain support.
"""
import os
import sys

from fastapi.responses import JSONResponse

from anp_foundation.domain.domain_manager import get_domain_manager

import logging
logger = logging.getLogger(__name__)

from typing import Dict
from fastapi import APIRouter, Request, Response, HTTPException

# 导入核心处理函数
from anp_servicepoint.core_service_handler.did_service_handler import (
    format_did_from_user_id,
    get_did_document,
    get_agent_description,
    get_agent_yaml_file,
    get_agent_json_file
)
router = APIRouter(tags=["did"])


@router.get("/wba/user/{user_id}/did.json", summary="Get DID document")
async def get_did_document_endpoint(user_id: str, request: Request) -> Dict:
    """
    Retrieve a DID document by user ID from anp_users with multi-domain support.
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    success, result = get_did_document(user_id, host, port)

    if not success:
        raise HTTPException(status_code=404 if "not found" in result else 500, detail=result)

    return result

@router.get("/wba/user/{user_id}/ad.json", summary="Get agent description")
async def get_agent_description_endpoint(user_id: str, request: Request) -> Dict:
    """
    返回符合 schema.org/did/ad 规范的 JSON-LD 格式智能体描述。
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    success, result = get_agent_description(user_id, host, port)

    if not success:
        status_code = 404 if "not found" in result else 500
        raise HTTPException(status_code=status_code, detail=result)

    return result


def url_did_format(user_id: str, request: Request) -> str:
    """
    格式化URL中的DID，支持多域名环境
    """
    # 使用域名管理器获取主机和端口
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    return format_did_from_user_id(user_id, host, port)



@router.get("/wba/user/{resp_did}/{yaml_file_name}.yaml", summary="Get agent OpenAPI YAML")
async def get_agent_openapi_yaml(resp_did: str, yaml_file_name: str, request: Request):
    """
       获取Agent的OpenAPI YAML文件，支持多域名环境
       """
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    success, result = get_agent_yaml_file(resp_did, yaml_file_name, host, port)

    if not success:
        status_code = 404 if "not found" in result else 500
        raise HTTPException(status_code=status_code, detail=result)

    return Response(content=result, media_type="application/x-yaml")


@router.get("/wba/user/{resp_did}/{jsonrpc_file_name}.json", summary="Get agent JSON-RPC")
async def get_agent_jsonrpc(resp_did: str, jsonrpc_file_name: str, request: Request):
    """
    获取Agent的JSON-RPC文件，支持多域名环境
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    success, result = get_agent_json_file(resp_did, jsonrpc_file_name, host, port)

    if not success:
        status_code = 404 if "not found" in result else 500
        raise HTTPException(status_code=status_code, detail=result)

    return JSONResponse(content=result, status_code=200)

