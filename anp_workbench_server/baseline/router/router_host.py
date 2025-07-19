from typing import Dict, Any, Optional

from fastapi import HTTPException, APIRouter
from starlette.requests import Request

from pydantic import BaseModel
from anp_foundation.domain import get_domain_manager

import logging
logger = logging.getLogger(__name__)

# 导入核心处理函数
from anp_servicepoint.extend_service_handler.host_service_handler import (
    get_hosted_did_document,
    submit_hosted_did_request,
    check_hosted_did_status,
    check_hosted_did_result,
    acknowledge_hosted_did_result,
    list_hosted_dids
)



# 添加请求模型
class HostedDIDRequest(BaseModel):
    """托管DID申请请求"""
    did_document: Dict[str, Any]
    requester_did: str
    callback_info: Optional[Dict[str, Any]] = None

class HostedDIDRequestResponse(BaseModel):
    """托管DID申请响应"""
    success: bool
    request_id: Optional[str] = None
    message: Optional[str] = None
    estimated_processing_time: Optional[int] = None

router = APIRouter(tags=["did_host"])

@router.get("/wba/hostuser/{user_id}/did.json", summary="Get Hosted DID document")
async def get_hosted_did_document_endpoint(user_id: str, request: Request) -> Dict:
    """
    Retrieve a DID document by user ID from anp_users_hosted with multi-domain support.
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    success, result = await get_hosted_did_document(user_id, host, port)

    if not success:
        status_code = 404 if "not found" in result else 500
        raise HTTPException(status_code=status_code, detail=result)

    return result

@router.post("/wba/hosted-did/request", response_model=HostedDIDRequestResponse)
async def receive_hosted_did_request_endpoint(request: Request, hosted_request: HostedDIDRequest):
    """
    第一步：提交托管DID申请（HTTP方式）

    复用现有的域名管理和验证逻辑
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 转换请求模型
    core_request = HostedDIDRequest(
        did_document=hosted_request.did_document,
        requester_did=hosted_request.requester_did,
        callback_info=hosted_request.callback_info
    )

    # 调用核心处理函数
    success, result = await submit_hosted_did_request(core_request, host, port)

    if not success:
        raise HTTPException(status_code=400 if "格式" in result.get("error", "") else 500,
                            detail=result.get("error", "Unknown error"))

    return HostedDIDRequestResponse(
        success=result.get("success", False),
        request_id=result.get("request_id"),
        message=result.get("message"),
        estimated_processing_time=result.get("estimated_processing_time")
    )


@router.get("/wba/hosted-did/status/{request_id}")
async def check_hosted_did_status_endpoint(request: Request, request_id: str):
    """查询申请状态（中间状态检查）"""
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    success, result = await check_hosted_did_status(request_id, host, port)

    if not success:
        raise HTTPException(status_code=404, detail=result.get("error", "Unknown error"))

    return result


@router.get("/wba/hosted-did/check/{requester_did_id}")
async def check_hosted_did_result_endpoint(request: Request, requester_did_id: str):
    """
    第二步：检查托管DID处理结果

    客户端使用自己的DID ID来检查是否有新的托管DID结果
    支持轮询调用
    """
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    success, result = await check_hosted_did_result(requester_did_id, host, port)

    if not success:
        raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))

    return result

@router.post("/wba/hosted-did/acknowledge/{result_id}")
async def acknowledge_hosted_did_result_endpoint(request: Request, result_id: str):
    """确认已收到托管DID结果"""
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    success, result = await acknowledge_hosted_did_result(result_id, host, port)

    if not success:
        status_code = 404 if "不存在" in result.get("error", "") else 500
        raise HTTPException(status_code=status_code, detail=result.get("error", "Unknown error"))

    return result


@router.get("/wba/hosted-did/list")
async def list_hosted_dids_endpoint(request: Request):
    """列出当前域名下的所有托管DID"""
    # 获取域名管理器
    domain_manager = get_domain_manager()
    host, port = domain_manager.get_host_port_from_request(request)

    # 调用核心处理函数
    success, result = await list_hosted_dids(host, port)

    if not success:
        status_code = 403 if "访问被拒绝" in result.get("error", "") else 500
        raise HTTPException(status_code=status_code, detail=result.get("error", "Unknown error"))

    return result