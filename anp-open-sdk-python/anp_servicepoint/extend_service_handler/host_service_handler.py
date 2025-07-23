# host_core_handlers.py
"""
托管 DID 处理的核心函数 - 与 Web 框架无关的业务逻辑
"""
import json
import logging
import time
import uuid
from typing import Dict, Any, Optional, Tuple, Union

from anp_foundation.domain import get_domain_manager

logger = logging.getLogger(__name__)


class BaseHostedDIDRequest:
    """托管DID申请请求"""

    def __init__(self, did_document: Dict[str, Any], requester_did: str,
                 callback_info: Optional[Dict[str, Any]] = None):
        self.did_document = did_document
        self.requester_did = requester_did
        self.callback_info = callback_info or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "did_document": self.did_document,
            "requester_did": self.requester_did,
            "callback_info": self.callback_info
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseHostedDIDRequest':
        """从字典创建实例"""
        return cls(
            did_document=data.get("did_document", {}),
            requester_did=data.get("requester_did", ""),
            callback_info=data.get("callback_info", {})
        )


async def get_hosted_did_document(user_id: str, host: str, port: int) -> Tuple[bool, Union[Dict[str, Any], str]]:
    """
    获取托管DID文档

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
    did_path = paths['user_hosted_path'] / f"user_{user_id}" / "did_document.json"

    logger.debug(f"查找托管DID文档: {did_path} (域名: {host}:{port})")

    if not did_path.exists():
        return False, f"Hosted DID document not found for user {user_id} in domain {host}:{port}"

    try:
        with open(did_path, 'r', encoding='utf-8') as f:
            did_document = json.load(f)
        logger.debug(f"成功加载托管DID文档: {user_id} from {host}:{port}")
        return True, did_document
    except Exception as e:
        logger.error(f"Error loading hosted DID document: {e}")
        return False, f"Error loading hosted DID document: {str(e)}"


async def submit_hosted_did_request(hosted_request: BaseHostedDIDRequest, host: str, port: int) -> Tuple[
    bool, Dict[str, Any]]:
    """
    提交托管DID申请

    Args:
        hosted_request: 托管DID申请请求
        host: 主机名
        port: 端口号

    Returns:
        Tuple[bool, Dict[str, Any]]: (成功标志, 响应数据)
    """
    try:
        # 获取域名管理器
        domain_manager = get_domain_manager()

        # 验证域名访问权限
        is_valid, error_msg = domain_manager.validate_domain_access(host, port)
        if not is_valid:
            logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
            return False, {"error": error_msg}

        # 确保域名目录存在
        domain_manager.ensure_domain_directories(host, port)

        # 基本验证
        if not hosted_request.did_document or not hosted_request.requester_did:
            return False, {"error": "DID文档和申请者DID不能为空"}

        if not hosted_request.requester_did.startswith('did:wba:'):
            return False, {"error": "申请者DID格式不正确"}

        # 生成申请ID
        request_id = str(uuid.uuid4())

        # 使用队列管理器处理申请
        from anp_servicepoint.extend_service_implementation.did_host.hosted_did_queue_manager import HostedDIDQueueManager
        queue_manager = HostedDIDQueueManager.create_for_domain(host, port)
        success = await queue_manager.add_request(request_id, hosted_request)

        if success:
            logger.info(f"收到托管DID申请: {request_id}, 申请者: {hosted_request.requester_did}")
            return True, {
                "success": True,
                "request_id": request_id,
                "message": "申请已提交，请使用request_id查询处理结果",
                "estimated_processing_time": 300  # 预估5分钟处理时间
            }
        else:
            return False, {"error": "申请提交失败"}

    except Exception as e:
        logger.error(f"处理托管DID申请失败: {e}")
        return False, {"error": str(e)}


async def check_hosted_did_status(request_id: str, host: str, port: int) -> Tuple[bool, Dict[str, Any]]:
    """
    查询托管DID申请状态

    Args:
        request_id: 申请ID
        host: 主机名
        port: 端口号

    Returns:
        Tuple[bool, Dict[str, Any]]: (成功标志, 状态信息)
    """
    try:
        # 获取域名管理器
        domain_manager = get_domain_manager()

        from anp_servicepoint.extend_service_implementation.did_host.hosted_did_queue_manager import HostedDIDQueueManager
        queue_manager = HostedDIDQueueManager.create_for_domain(host, port)
        status_info = await queue_manager.get_request_status(request_id)

        if not status_info:
            return False, {"error": "申请ID不存在"}

        return True, status_info

    except Exception as e:
        logger.error(f"查询申请状态失败: {e}")
        return False, {"error": str(e)}


async def check_hosted_did_result(requester_did_id: str, host: str, port: int) -> Tuple[bool, Dict[str, Any]]:
    """
    检查托管DID处理结果

    Args:
        requester_did_id: 申请者DID
        host: 主机名
        port: 端口号

    Returns:
        Tuple[bool, Dict[str, Any]]: (成功标志, 结果信息)
    """
    try:
        # 获取域名管理器
        domain_manager = get_domain_manager()

        from anp_servicepoint.extend_service_implementation.did_host.hosted_did_result_manager import HostedDIDResultManager
        result_manager = HostedDIDResultManager.create_for_domain(host, port)
        results = await result_manager.get_results_for_requester(requester_did_id)

        return True, {
            "success": True,
            "results": results,
            "total": len(results),
            "check_time": time.time(),
            "host": host,
            "port": port
        }

    except Exception as e:
        logger.error(f"检查托管DID结果失败: {e}")
        return False, {"error": str(e)}


async def acknowledge_hosted_did_result(result_id: str, host: str, port: int) -> Tuple[bool, Dict[str, Any]]:
    """
    确认已收到托管DID结果

    Args:
        result_id: 结果ID
        host: 主机名
        port: 端口号

    Returns:
        Tuple[bool, Dict[str, Any]]: (成功标志, 响应信息)
    """
    try:
        # 获取域名管理器
        domain_manager = get_domain_manager()

        from anp_servicepoint.extend_service_implementation.did_host.hosted_did_result_manager import HostedDIDResultManager
        result_manager = HostedDIDResultManager.create_for_domain(host, port)
        success = await result_manager.acknowledge_result(result_id)

        if success:
            return True, {"success": True, "message": "结果确认成功"}
        else:
            return False, {"error": "结果ID不存在"}

    except Exception as e:
        logger.error(f"确认托管DID结果失败: {e}")
        return False, {"error": str(e)}


async def list_hosted_dids(host: str, port: int) -> Tuple[bool, Dict[str, Any]]:
    """
    列出当前域名下的所有托管DID

    Args:
        host: 主机名
        port: 端口号

    Returns:
        Tuple[bool, Dict[str, Any]]: (成功标志, 托管DID列表)
    """
    try:
        # 获取域名管理器
        domain_manager = get_domain_manager()

        # 验证域名访问权限
        is_valid, error_msg = domain_manager.validate_domain_access(host, port)
        if not is_valid:
            return False, {"error": error_msg}

        # 使用现有的路径获取逻辑
        paths = domain_manager.get_all_data_paths(host, port)
        hosted_dir = paths['user_hosted_path']

        hosted_dids = []

        # 遍历托管DID目录
        for user_dir in hosted_dir.glob('user_*/'):
            try:
                did_doc_path = user_dir / 'did_document.json'
                request_path = user_dir / 'did_document_request.json'

                if did_doc_path.exists():
                    with open(did_doc_path, 'r', encoding='utf-8') as f:
                        did_doc = json.load(f)

                    hosted_info = {
                        'user_id': user_dir.name.replace('user_', ''),
                        'hosted_did_id': did_doc.get('id'),
                        'created_at': user_dir.stat().st_ctime
                    }

                    # 如果有原始请求信息
                    if request_path.exists():
                        with open(request_path, 'r', encoding='utf-8') as f:
                            request_info = json.load(f)
                        hosted_info['original_did'] = request_info.get('id')

                    hosted_dids.append(hosted_info)

            except Exception as e:
                logger.warning(f"读取托管DID信息失败 {user_dir}: {e}")

        return True, {
            "hosted_dids": sorted(hosted_dids, key=lambda x: x.get('created_at', 0), reverse=True),
            "total": len(hosted_dids),
            "host": host,
            "port": port
        }

    except Exception as e:
        logger.error(f"列出托管DID失败: {e}")
        return False, {"error": str(e)}