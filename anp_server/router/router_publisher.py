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
Publisher API router for hosted DID documents, agent descriptions, and API forwarding with multi-domain support.
"""
import logging
logger = logging.getLogger(__name__)
from typing import Dict
from fastapi import APIRouter, Request, HTTPException
from anp_server.domain.domain_manager import get_domain_manager


router = APIRouter(tags=["did_host"])


@router.get("/publisher/agents", summary="Get published agent list")
async def get_agent_publishers(request: Request) -> Dict:
    """
    获取已发布的代理列表，直接从运行中的 SDK 实例获取，支持多域名环境。
    发布设置:
    - open: 公开给所有人
    """
    try:
        # 集成域名管理器
        domain_manager = get_domain_manager()
        host, port = domain_manager.get_host_port_from_request(request)
        
        # 验证域名访问权限
        is_valid, error_msg = domain_manager.validate_domain_access(host, port)
        if not is_valid:
            logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
            raise HTTPException(status_code=403, detail=error_msg)
        
        # 通过 request.app.state 获取在 ANPSDK 初始化时存储的 sdk 实例
        sdk = request.app.state.sdk

        # 从 SDK 实例中获取所有已注册的 agent
        all_agents = sdk.get_agents() # 使用 get_agents() 公共方法

        public_agents = []
        for agent in all_agents:
            agent_info = {
                "did": getattr(agent, "id", "unknown"),
                "name": getattr(agent, "name", "unknown"),
                "domain": f"{host}:{port}",
                "is_hosted": getattr(agent, "is_hosted_did", False)
            }
            public_agents.append(agent_info)

        # 添加域名统计信息
        domain_stats = domain_manager.get_domain_stats()
        
        return {
            "agents": public_agents,
            "count": len(public_agents),
            "domain": f"{host}:{port}",
            "domain_stats": domain_stats,
            "supported_domains": list(domain_manager.supported_domains.keys()) if hasattr(domain_manager.supported_domains, 'keys') else []
        }
    except Exception as e:
        logger.error(f"Error getting agent list from SDK instance: {e}")
        raise HTTPException(status_code=500, detail="Error getting agent list from SDK instance")
