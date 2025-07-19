# did_core_handlers.py
"""
DID 文档处理的核心函数 - 与 Web 框架无关的业务逻辑
"""
import json
import logging
import urllib.parse
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union

from anp_foundation.did.did_tool import find_user_by_did
from anp_foundation.domain.domain_manager import get_domain_manager

logger = logging.getLogger(__name__)


def format_did_from_user_id(user_id: str, host: str, port: int) -> str:
    """
    格式化用户ID为标准DID格式

    Args:
        user_id: 用户ID或DID
        host: 主机名
        port: 端口号

    Returns:
        str: 格式化后的DID
    """
    user_id = urllib.parse.unquote(user_id)

    if user_id.startswith("did:wba"):
        # 处理已经是DID格式的情况
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


def get_did_document(user_id: str, host: str, port: int) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    获取DID文档

    Args:
        user_id: 用户ID
        host: 主机名
        port: 端口号

    Returns:
        Tuple[bool, Union[Dict[str, Any], str]]: (成功标志, DID文档或错误消息)
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()

    # 验证域名访问权限
    is_valid, error_msg = domain_manager.validate_domain_access(host, port)
    if not is_valid:
        logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
        return False, error_msg

    # 确保域名目录存在
    domain_manager.ensure_domain_directories(host, port)

    # 使用动态路径替换硬编码路径
    paths = domain_manager.get_all_data_paths(host, port)
    did_path = paths['user_did_path'] / f"user_{user_id}" / "did_document.json"

    logger.debug(f"查找DID文档: {did_path} (域名: {host}:{port})")

    if not did_path.exists():
        return False, f"DID document not found for user {user_id} in domain {host}:{port}"

    try:
        with open(did_path, 'r', encoding='utf-8') as f:
            did_document = json.load(f)
        logger.debug(f"成功加载DID文档: {user_id} from {host}:{port}")
        return True, did_document
    except Exception as e:
        logger.error(f"Error loading DID document: {e}")
        return False, f"Error loading DID document: {str(e)}"


def get_agent_description(user_id: str, host: str, port: int) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    获取智能体描述文档

    Args:
        user_id: 用户ID
        host: 主机名
        port: 端口号

    Returns:
        Tuple[bool, Union[Dict[str, Any], str]]: (成功标志, 智能体描述或错误消息)
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()

    # 验证域名访问权限
    is_valid, error_msg = domain_manager.validate_domain_access(host, port)
    if not is_valid:
        logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
        return False, error_msg

    # 格式化DID
    resp_did = format_did_from_user_id(user_id, host, port)

    # 查找用户
    success, did_doc, user_dir = find_user_by_did(resp_did)
    if not success:
        return False, f"DID {resp_did} not found"

    if user_dir is None:
        return False, f"User directory not found for DID {resp_did}"

    # 使用动态路径获取用户目录
    paths = domain_manager.get_all_data_paths(host, port)
    user_full_path = paths['user_did_path'] / user_dir

    # 从文件系统读取ad.json
    ad_json_path = user_full_path / "ad.json"

    if ad_json_path.exists():
        try:
            with open(ad_json_path, 'r', encoding='utf-8') as f:
                ad_json = json.load(f)
            return True, ad_json
        except Exception as e:
            logger.error(f"读取ad.json失败: {e}")
            return False, f"读取ad.json失败: {str(e)}"
    else:
        # 如果ad.json不存在，返回错误
        return False, f"ad.json not found for DID {resp_did}"


def get_agent_yaml_file(resp_did: str, yaml_file_name: str, host: str, port: int) -> Tuple[bool, Union[str, bytes]]:
    """
    获取智能体YAML文件

    Args:
        resp_did: 响应方DID
        yaml_file_name: YAML文件名
        host: 主机名
        port: 端口号

    Returns:
        Tuple[bool, Union[str, bytes]]: (成功标志, YAML内容或错误消息)
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()

    # 验证域名访问权限
    is_valid, error_msg = domain_manager.validate_domain_access(host, port)
    if not is_valid:
        logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
        return False, error_msg

    # 格式化DID
    resp_did = format_did_from_user_id(resp_did, host, port)

    # 查找用户
    success, did_doc, user_dir = find_user_by_did(resp_did)
    if not success:
        return False, "User not found"

    if user_dir is None:
        return False, f"User directory not found for DID {resp_did}"

    # 使用动态路径
    paths = domain_manager.get_all_data_paths(host, port)
    yaml_path = paths['user_did_path'] / user_dir / f"{yaml_file_name}.yaml"

    if not yaml_path.exists():
        return False, "OpenAPI YAML not found"

    try:
        with open(yaml_path, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        return True, yaml_content
    except Exception as e:
        logger.error(f"读取YAML文件失败: {e}")
        return False, f"读取YAML文件失败: {str(e)}"


def get_agent_json_file(resp_did: str, json_file_name: str, host: str, port: int) -> Tuple[
    bool, Union[Dict[str, Any], str]]:
    """
    获取智能体JSON文件

    Args:
        resp_did: 响应方DID
        json_file_name: JSON文件名
        host: 主机名
        port: 端口号

    Returns:
        Tuple[bool, Union[Dict[str, Any], str]]: (成功标志, JSON内容或错误消息)
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()

    # 验证域名访问权限
    is_valid, error_msg = domain_manager.validate_domain_access(host, port)
    if not is_valid:
        logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
        return False, error_msg

    # 格式化DID
    resp_did = format_did_from_user_id(resp_did, host, port)

    # 查找用户
    success, did_doc, user_dir = find_user_by_did(resp_did)
    if not success:
        return False, "User not found"

    if user_dir is None:
        return False, f"User directory not found for DID {resp_did}"

    # 使用动态路径
    paths = domain_manager.get_all_data_paths(host, port)
    json_path = paths['user_did_path'] / user_dir / f"{json_file_name}.json"

    if not json_path.exists():
        return False, "JSON file not found"

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_content = json.load(f)
        return True, json_content
    except Exception as e:
        logger.error(f"读取JSON文件失败: {e}")
        return False, f"读取JSON文件失败: {str(e)}"