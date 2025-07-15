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
import urllib.parse
from urllib.parse import quote

from fastapi.responses import JSONResponse

from anp_sdk.did.did_tool import find_user_by_did, get_agent_cfg_by_user_dir
from anp_server.domain.domain_manager import get_domain_manager

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
import json
import logging
logger = logging.getLogger(__name__)

from typing import Dict
from fastapi import APIRouter, Request, Response, HTTPException

from anp_sdk.utils.log_base import  logging as logger

router = APIRouter(tags=["did"])


@router.get("/wba/user/{user_id}/did.json", summary="Get DID document")
async def get_did_document(user_id: str, request: Request) -> Dict:
    """
    Retrieve a DID document by user ID from anp_users with multi-domain support.
    """
    # 集成域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)
    
    # 验证域名访问权限
    is_valid, error_msg = domain_manager.validate_domain_access(host, port)
    if not is_valid:
        logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
        raise HTTPException(status_code=403, detail=error_msg)
    
    # 确保域名目录存在
    domain_manager.ensure_domain_directories(host, port)
    
    # 使用动态路径替换硬编码路径
    paths = domain_manager.get_all_data_paths(host, port)
    did_path = paths['user_did_path'] / f"user_{user_id}" / "did_document.json"
    
    logger.debug(f"查找DID文档: {did_path} (域名: {host}:{port})")
    
    if not did_path.exists():
        raise HTTPException(status_code=404, detail=f"DID document not found for user {user_id} in domain {host}:{port}")
    
    try:
        with open(did_path, 'r', encoding='utf-8') as f:
            did_document = json.load(f)
        logger.debug(f"成功加载DID文档: {user_id} from {host}:{port}")
        return did_document
    except Exception as e:
        logger.error(f"Error loading DID document: {e}")
        raise HTTPException(status_code=500, detail="Error loading DID document")


# 注意：托管 DID 文档的功能已移至 router_publisher.py
# 未来对于托管 did-doc/ad.json/yaml 以及消息转发/api转发都将通过 did_host 路由处理

@router.get("/wba/user/{user_id}/ad.json", summary="Get agent description")
async def get_agent_description(user_id: str, request: Request) -> Dict:
    """
    返回符合 schema.org/did/ad 规范的 JSON-LD 格式智能体描述。
    """
    # 集成域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 验证域名访问权限
    is_valid, error_msg = domain_manager.validate_domain_access(host, port)
    if not is_valid:
        logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
        raise HTTPException(status_code=403, detail=error_msg)

    resp_did = url_did_format(user_id, request)

    success, did_doc, user_dir = find_user_by_did(resp_did)
    if not success:
        raise HTTPException(status_code=404, detail=f"DID {resp_did} not found")

    if user_dir is None:
        raise HTTPException(status_code=404, detail=f"User directory not found for DID {resp_did}")

    # 使用动态路径获取用户目录
    paths = domain_manager.get_all_data_paths(host, port)
    user_full_path = paths['user_did_path'] / user_dir

    # 从文件系统读取ad.json
    ad_json_path = user_full_path / "ad.json"

    if ad_json_path.exists():
        try:
            with open(ad_json_path, 'r', encoding='utf-8') as f:
                ad_json = json.load(f)
            return ad_json
        except Exception as e:
            logger.error(f"读取ad.json失败: {e}")
            raise HTTPException(status_code=500, detail=f"读取ad.json失败: {e}")
    else:
        # 如果ad.json不存在，返回错误
        raise HTTPException(status_code=404, detail=f"ad.json not found for DID {resp_did}")


def url_did_format(user_id: str, request: Request) -> str:
    """
    格式化URL中的DID，支持多域名环境
    """
    # 使用域名管理器获取主机和端口
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)
    
    user_id = urllib.parse.unquote(user_id)
    
    if user_id.startswith("did:wba"):
        # 新增处理：如果 user_id 不包含 %3A，按 : 分割，第四个部分是数字，则把第三个 : 换成 %3A
        if "%3A" not in user_id:
            parts = user_id.split(":")
            if len(parts) > 4 and parts[3].isdigit():
                resp_did = ":".join(parts[:3]) + "%3A" + ":".join(parts[3:])
            else:
                resp_did = user_id
        else:
            resp_did = user_id
    elif len(user_id) == 16:  # unique_id
        if port == 80 or port == 443:
            resp_did = f"did:wba:{host}:wba:user:{user_id}"
        else:
            resp_did = f"did:wba:{host}%3A{port}:wba:user:{user_id}"
    else:
        resp_did = "not_did_wba"

    return resp_did


@router.get("/wba/user/{resp_did}/{yaml_file_name}.yaml", summary="Get agent OpenAPI YAML")
async def get_agent_openapi_yaml(resp_did: str, yaml_file_name: str, request: Request):
    """
    获取Agent的OpenAPI YAML文件，支持多域名环境
    """
    # 集成域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)
    
    # 验证域名访问权限
    is_valid, error_msg = domain_manager.validate_domain_access(host, port)
    if not is_valid:
        logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
        raise HTTPException(status_code=403, detail=error_msg)
    
    resp_did = url_did_format(resp_did, request)

    success, did_doc, user_dir = find_user_by_did(resp_did)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    if user_dir is None:
        raise HTTPException(status_code=404, detail=f"User directory not found for DID {resp_did}")



    
    # 使用动态路径
    paths = domain_manager.get_all_data_paths(host, port)
    yaml_path = paths['user_did_path'] / user_dir / f"{yaml_file_name}.yaml"
    
    if not yaml_path.exists():
        raise HTTPException(status_code=404, detail="OpenAPI YAML not found")
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        yaml_content = f.read()
    return Response(content=yaml_content, media_type="application/x-yaml")


@router.get("/wba/user/{resp_did}/{jsonrpc_file_name}.json", summary="Get agent JSON-RPC")
async def get_agent_jsonrpc(resp_did: str, jsonrpc_file_name: str, request: Request):
    """
    获取Agent的JSON-RPC文件，支持多域名环境
    """
    # 集成域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)
    
    # 验证域名访问权限
    is_valid, error_msg = domain_manager.validate_domain_access(host, port)
    if not is_valid:
        logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
        raise HTTPException(status_code=403, detail=error_msg)

    resp_did = url_did_format(resp_did, request)

    success, did_doc, user_dir = find_user_by_did(resp_did)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    if user_dir is None:
        raise HTTPException(status_code=404, detail=f"User directory not found for DID {resp_did}")


    
    # 使用动态路径
    paths = domain_manager.get_all_data_paths(host, port)
    json_path = paths['user_did_path'] / user_dir / f"{jsonrpc_file_name}.json"
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="json rpc not found")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        json_content = json.load(f)
    return JSONResponse(content=json_content, status_code=200)
