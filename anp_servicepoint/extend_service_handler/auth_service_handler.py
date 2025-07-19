# auth_core_handlers.py
"""
认证相关的核心处理函数 - 与 Web 框架无关的业务逻辑
"""
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def parse_auth_str_to_dict(auth_str: str) -> dict:
    """
    将类似于 'key1="value1", key2="value2"' 的字符串解析为字典

    Args:
        auth_str: 认证字符串

    Returns:
        dict: 解析后的字典
    """
    result = {}
    try:
        # 先按逗号分割，再按等号分割
        for kv in auth_str.split(", "):
            if "=" in kv:
                k, v = kv.split("=", 1)
                result[k.strip()] = v.strip('"')
    except Exception as e:
        logger.warning(f"解析认证字符串为字典时出错: {e}")
    return result


def process_authentication(req_did: Optional[str], resp_did: Optional[str],
                           auth_header: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    处理认证请求的核心逻辑

    Args:
        req_did: 请求方DID
        resp_did: 响应方DID
        auth_header: 认证头信息

    Returns:
        Tuple[bool, Dict]: (是否认证成功, 响应数据)
    """
    # 检查必要参数
    if not req_did or not resp_did:
        return False, {
            "status": "error",
            "message": "Missing req_did or resp_did in headers or query parameters",
            "authenticated": False
        }

    # 尝试从认证头中提取用户信息
    user = None
    try:
        if req_did != "":  # token 用户
            user = req_did
        elif auth_header:  # did 用户
            # 检查auth_data是否为字符串
            if isinstance(auth_header, str) and " " in auth_header:
                auth_data = auth_header.split(" ", 1)[1]
                auth_dict = parse_auth_str_to_dict(auth_data)
                user = auth_dict.get("req_did")
    except Exception as e:
        logger.warning(f"解析认证数据时出错: {e}")
        user = None

    # 构建响应
    if not user:
        return True, {
            "status": "warning",
            "message": "No authentication provided, but access allowed",
            "authenticated": False
        }

    return True, {
        "status": "success",
        "message": "Successfully authenticated",
        "RequestUser": user,
        "authenticated": True
    }