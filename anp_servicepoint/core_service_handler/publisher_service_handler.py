# publisher_core_handlers.py
"""
发布者 API 的核心处理函数 - 与 Web 框架无关的业务逻辑
"""
import logging
from typing import Dict, Any, Tuple, List

from anp_foundation.domain.domain_manager import get_domain_manager

logger = logging.getLogger(__name__)


async def get_published_agents(host: str, port: int) -> Tuple[bool, Dict[str, Any]]:
    """
    获取已发布的智能体列表

    Args:
        host: 主机名
        port: 端口号

    Returns:
        Tuple[bool, Dict[str, Any]]: (成功标志, 智能体列表数据)
    """
    try:
        # 获取域名管理器
        domain_manager = get_domain_manager()

        # 验证域名访问权限
        is_valid, error_msg = domain_manager.validate_domain_access(host, port)
        if not is_valid:
            logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
            return False, {"error": error_msg}

        # 获取所有智能体实例
        from anp_transformer.agent_manager import AgentManager
        all_agents = AgentManager.get_all_agent_instances()

        # 处理智能体信息
        public_agents = []
        seen_dids = set()  # 用于跟踪已经添加的did

        for agent in all_agents:
            # 尝试获取agent的did
            did = "unknown"
            if hasattr(agent, "anp_user_id"):
                did = agent.anp_user_id
            elif hasattr(agent, "anp_user") and hasattr(agent.anp_user, "id"):
                did = agent.anp_user.id
            elif hasattr(agent, "id"):
                did = agent.id

            # 如果did已经添加过，则跳过
            if did in seen_dids:
                continue

            # 添加did到集合
            seen_dids.add(did)

            agent_info = {
                "did": did,
                "name": getattr(agent, "name", "unknown"),
                "domain": f"{host}:{port}",
                "is_hosted": getattr(agent, "is_hosted_did", False)
            }
            public_agents.append(agent_info)

        # 添加域名统计信息
        domain_stats = domain_manager.get_domain_stats()

        # 构建结果
        result = {
            "agents": public_agents,
            "count": len(public_agents),
            "domain": f"{host}:{port}",
            "domain_stats": domain_stats,
            "supported_domains": list(domain_manager.supported_domains.keys()) if hasattr(
                domain_manager.supported_domains, 'keys') else []
        }

        return True, result

    except Exception as e:
        logger.error(f"获取智能体列表失败: {e}")
        return False, {"error": f"获取智能体列表失败: {str(e)}"}