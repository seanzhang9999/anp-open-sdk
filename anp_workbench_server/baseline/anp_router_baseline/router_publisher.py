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
Publisher API anp_router_baseline for hosted DID documents, agent descriptions, and API forwarding with multi-domain support.
"""
import logging
logger = logging.getLogger(__name__)
from typing import Dict
from fastapi import APIRouter, Request, HTTPException
from anp_foundation.domain.domain_manager import get_domain_manager

from anp_servicepoint.core_service_handler.publisher_service_handler import  get_published_agents

router = APIRouter(tags=["did_host"])


@router.get("/publisher/agents", summary="Get published agent list")
async def get_agent_publishers(request: Request) -> Dict:
    """
    获取已发布的智能体列表，支持多域名环境
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    success, result = await get_published_agents(host, port)

    if not success:
        status_code = 403 if "域名访问被拒绝" in result.get("error", "") else 500
        raise HTTPException(status_code=status_code, detail=result.get("error", "Unknown error"))

    return result