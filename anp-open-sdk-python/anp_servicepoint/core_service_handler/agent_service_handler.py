# agent_core_handlers.py
"""
Agent 核心处理函数 - 与 Web 框架无关的业务逻辑
"""
import logging
import aiohttp
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 导入必要的依赖
from anp_foundation.config import get_global_config
from anp_runtime.global_router_agent_message import GlobalMessageManager, GlobalGroupManager


async def process_group_request(did: str, group_id: str, action: str, request_data: Dict[str, Any],
                                original_request: Optional[Any] = None) -> Dict[str, Any]:
    """
    处理群组相关请求的核心逻辑

    Args:
        did: 目标DID
        group_id: 群组ID
        action: 操作类型 (join/leave/message/connect/members)
        request_data: 请求数据
        original_request: 原始请求对象(可选)

    Returns:
        Dict[str, Any]: 处理结果
    """
    # 获取配置
    config = get_global_config()
    use_transformer_server = getattr(config.anp_sdk, "use_transformer_server", False)
    transformer_server_url = getattr(config.anp_sdk, "transformer_server_url", "http://localhost:9528")

    # 根据配置决定处理方式
    if use_transformer_server:
        # 转发到transformer_server
        try:
            logger.debug(f"🔄 转发群组{action}请求到transformer_server: {did}/{group_id}")

            # 构建请求参数
            params = {}
            if original_request and hasattr(original_request, "query_params"):
                params = dict(original_request.query_params)
            elif "req_did" in request_data:
                params = {"req_did": request_data["req_did"]}

            # 发送请求
            async with aiohttp.ClientSession() as session:
                target_url = f"{transformer_server_url}/agent/group/{did}/{group_id}/{action}"

                # 移除请求数据中的元数据
                payload = {k: v for k, v in request_data.items()
                           if k not in ["req_did", "group_id"]}

                async with session.post(
                        target_url,
                        json=payload,
                        params=params
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ Framework server返回错误: {response.status} - {error_text}")
                        if not getattr(config.anp_sdk, "fallback_to_local", True):
                            return {"status": "error", "message": f"Framework server错误: {response.status}"}
        except Exception as e:
            logger.error(f"❌ 转发到Framework server失败: {e}")
            if not getattr(config.anp_sdk, "fallback_to_local", True):
                return {"status": "error", "message": f"Framework server连接失败: {str(e)}"}

    # 本地处理
    try:
        result = await GlobalMessageManager.route_group_request(
            did, group_id, action, request_data, original_request
        )
        return result
    except Exception as e:
        logger.error(f"❌ 本地处理群组{action}失败: {e}")
        return {"status": "error", "message": f"处理群组{action}失败: {str(e)}"}


async def process_agent_api_request(did: str, subpath: str, request_data: Dict[str, Any],
                                    original_request: Optional[Any] = None) -> Dict[str, Any]:
    """
    处理Agent API调用的核心逻辑

    Args:
        did: 目标DID
        subpath: API路径
        request_data: 请求数据
        original_request: 原始请求对象(可选)

    Returns:
        Dict[str, Any]: 处理结果
    """
    # 获取配置
    config = get_global_config()
    use_transformer_server = getattr(config.anp_sdk, "use_transformer_server", False)
    transformer_server_url = getattr(config.anp_sdk, "transformer_server_url", "http://localhost:9528")

    # 构造请求数据
    processed_data = {
        **request_data,
        "type": "message" if subpath == "message/post" else "api_call",
        "path": f"/{subpath}"
    }

    # 确保req_did存在
    if "req_did" not in processed_data:
        if original_request and hasattr(original_request, "query_params"):
            processed_data["req_did"] = original_request.query_params.get("req_did", "transformer_caller")
        else:
            processed_data["req_did"] = "transformer_caller"

    # 根据配置决定处理方式
    if use_transformer_server:
        # 转发到transformer_server
        try:
            logger.debug(f"🔄 转发请求到transformer_server: {did}/{subpath}")

            # 构建请求参数
            params = {}
            if original_request and hasattr(original_request, "query_params"):
                params = dict(original_request.query_params)
            elif "req_did" in processed_data:
                params = {"req_did": processed_data["req_did"]}

            # 发送请求
            async with aiohttp.ClientSession() as session:
                target_url = f"{transformer_server_url}/agent/api/{did}/{subpath}"

                # 移除请求数据中的元数据
                payload = {k: v for k, v in request_data.items()
                           if k not in ["type", "path", "req_did"]}

                async with session.post(
                        target_url,
                        json=payload,
                        params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ transformer server返回错误: {response.status} - {error_text}")
                        # 失败时回退到本地处理
                        if not getattr(config.anp_sdk, "fallback_to_local", True):
                            return {"status": "error", "message": f"transformer server错误: {response.status}",
                                    "details": error_text}
        except Exception as e:
            logger.error(f"❌ transformer server失败: {e}")
            # 失败时回退到本地处理
            if not getattr(config.anp_sdk, "fallback_to_local", True):
                return {"status": "error", "message": f"transformer server连接失败: {str(e)}"}
            logger.debug("⚠️ 回退到本地处理")

    # 本地处理（或回退处理）
    try:
        # 获取router_agent实例
        from anp_runtime.agent_manager import AgentManager
        router_agent = AgentManager.get_router_agent()

        # 添加错误处理：
        if router_agent is None:
            logger.error("❌ AgentRouter 未初始化")
            return {"status": "error", "message": "AgentRouter 未初始化"}

        # 路由请求
        result = await router_agent.route_request(
            processed_data["req_did"],
            did,
            processed_data,
            original_request
        )

        return result
    except Exception as e:
        logger.error(f"❌ 本地处理请求失败: {e}")
        return {"status": "error", "message": f"处理请求失败: {str(e)}"}


async def process_agent_message(did: str, request_data: Dict[str, Any],
                                original_request: Optional[Any] = None) -> Dict[str, Any]:
    """
    处理Agent消息的核心逻辑

    Args:
        did: 目标DID
        request_data: 请求数据
        original_request: 原始请求对象(可选)

    Returns:
        Dict[str, Any]: 处理结果
    """
    # 获取配置
    config = get_global_config()
    use_transformer_server = getattr(config.anp_sdk, "use_transformer_server", False)
    transformer_server_url = getattr(config.anp_sdk, "transformer_server_url", "http://localhost:9528")

    # 构造请求数据
    processed_data = {
        **request_data,
        "type": "message"
    }

    # 确保req_did存在
    if "req_did" not in processed_data:
        if original_request and hasattr(original_request, "query_params"):
            processed_data["req_did"] = original_request.query_params.get("req_did", "transformer_caller")
        else:
            processed_data["req_did"] = "transformer_caller"

    # 根据配置决定处理方式
    if use_transformer_server:
        # 转发到transformer_server
        try:
            logger.debug(f"🔄 转发消息到transformer_server: {did}")

            # 构建请求参数
            params = {}
            if original_request and hasattr(original_request, "query_params"):
                params = dict(original_request.query_params)
            elif "req_did" in processed_data:
                params = {"req_did": processed_data["req_did"]}

            # 发送请求
            async with aiohttp.ClientSession() as session:
                target_url = f"{transformer_server_url}/agent/message/{did}/post"

                # 移除请求数据中的元数据
                payload = {k: v for k, v in request_data.items()
                           if k not in ["type", "req_did"]}

                async with session.post(
                        target_url,
                        json=payload,
                        params=params
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        logger.error(f"❌ transformer server返回错误: {response.status} - {error_text}")
                        # 失败时回退到本地处理
                        if not getattr(config.anp_sdk, "fallback_to_local", True):
                            return {"anp_result": {"status": "error",
                                                   "message": f"transformer server错误: {response.status}"}}
        except Exception as e:
            logger.error(f"❌ transformer server失败: {e}")
            # 失败时回退到本地处理
            if not getattr(config.anp_sdk, "fallback_to_local", True):
                return {"anp_result": {"status": "error", "message": f"transformer server连接失败: {str(e)}"}}
            logger.debug("⚠️ 回退到本地处理")

    # 本地处理（或回退处理）
    try:
        from anp_runtime.agent_manager import AgentManager
        router_agent = AgentManager.get_router_agent()

        # 添加错误处理：
        if router_agent is None:
            logger.error("❌ AgentRouter 未初始化")
            return {"status": "error", "message": "AgentRouter 未初始化"}

        # 路由请求
        result = await router_agent.route_request(
            processed_data["req_did"],
            did,
            processed_data,
            original_request
        )

        return result
    except Exception as e:
        logger.error(f"❌ 本地处理消息失败: {e}")
        return {"anp_result": {"status": "error", "message": f"处理消息失败: {str(e)}"}}


def get_all_groups() -> Dict[str, Any]:
    """
    获取所有群组信息

    Returns:
        Dict[str, Any]: 群组信息和统计数据
    """
    try:
        groups = GlobalGroupManager.list_groups()
        stats = GlobalGroupManager.get_group_stats()
        return {
            "status": "success",
            "groups": groups,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"❌ 列出群组失败: {e}")
        return {"status": "error", "message": f"列出群组失败: {str(e)}"}