import json
from typing import Dict, Any, Optional
import time
import uuid

from fastapi import HTTPException, APIRouter
from starlette.requests import Request
from pydantic import BaseModel

from anp_sdk.domain import get_domain_manager

import logging
logger = logging.getLogger(__name__)

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
async def get_hosted_did_document(user_id: str, request: Request) -> Dict:
    """
    Retrieve a DID document by user ID from anp_users_hosted with multi-domain support.
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
    did_path = paths['user_hosted_path'] / f"user_{user_id}" / "did_document.json"

    logger.debug(f"查找托管DID文档: {did_path} (域名: {host}:{port})")

    if not did_path.exists():
        raise HTTPException(status_code=404, detail=f"Hosted DID document not found for user {user_id} in domain {host}:{port}")

    try:
        with open(did_path, 'r', encoding='utf-8') as f:
            did_document = json.load(f)
        logger.debug(f"成功加载托管DID文档: {user_id} from {host}:{port}")
        return did_document
    except Exception as e:
        logger.error(f"Error loading hosted DID document: {e}")
        raise HTTPException(status_code=500, detail="Error loading hosted DID document")


@router.post("/wba/hosted-did/request", response_model=HostedDIDRequestResponse)
async def submit_hosted_did_request(request: Request, hosted_request: HostedDIDRequest):
    """
    第一步：提交托管DID申请（HTTP方式）
    
    复用现有的域名管理和验证逻辑
    """
    try:
        # 复用现有的域名管理逻辑
        domain_manager = get_domain_manager()
        host, port = domain_manager.get_host_port_from_request(request)

        # 复用现有的域名验证逻辑
        is_valid, error_msg = domain_manager.validate_domain_access(host, port)
        if not is_valid:
            logger.warning(f"域名访问被拒绝: {host}:{port} - {error_msg}")
            raise HTTPException(status_code=403, detail=error_msg)

        # 确保域名目录存在
        domain_manager.ensure_domain_directories(host, port)
        
        # 基本验证
        if not hosted_request.did_document or not hosted_request.requester_did:
            raise HTTPException(status_code=400, detail="DID文档和申请者DID不能为空")
        
        if not hosted_request.requester_did.startswith('did:wba:'):
            raise HTTPException(status_code=400, detail="申请者DID格式不正确")
        
        # 生成申请ID
        request_id = str(uuid.uuid4())
        
        # 使用队列管理器处理申请
        from anp_server.did_host.hosted_did_queue_manager import HostedDIDQueueManager
        queue_manager = HostedDIDQueueManager.create_for_domain(host, port)
        success = await queue_manager.add_request(request_id, hosted_request)
        
        if success:
            logger.info(f"收到托管DID申请: {request_id}, 申请者: {hosted_request.requester_did}")
            return HostedDIDRequestResponse(
                success=True,
                request_id=request_id,
                message="申请已提交，请使用request_id查询处理结果",
                estimated_processing_time=300  # 预估5分钟处理时间
            )
        else:
            raise HTTPException(status_code=500, detail="申请提交失败")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理托管DID申请失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wba/hosted-did/status/{request_id}")
async def check_hosted_did_status(request: Request, request_id: str):
    """查询申请状态（中间状态检查）"""
    try:
        # 复用现有的域名管理逻辑
        domain_manager = get_domain_manager()
        host, port = domain_manager.get_host_port_from_request(request)
        
        from anp_server.did_host.hosted_did_queue_manager import HostedDIDQueueManager
        queue_manager = HostedDIDQueueManager.create_for_domain(host, port)
        status_info = await queue_manager.get_request_status(request_id)
        
        if not status_info:
            raise HTTPException(status_code=404, detail="申请ID不存在")
        
        return status_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询申请状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wba/hosted-did/check/{requester_did_id}")
async def check_hosted_did_result(request: Request, requester_did_id: str):
    """
    第二步：检查托管DID处理结果
    
    客户端使用自己的DID ID来检查是否有新的托管DID结果
    支持轮询调用
    """
    try:
        # 复用现有的域名管理逻辑
        domain_manager = get_domain_manager()
        host, port = domain_manager.get_host_port_from_request(request)
        
        from anp_server.did_host.hosted_did_result_manager import HostedDIDResultManager
        result_manager = HostedDIDResultManager.create_for_domain(host, port)
        results = await result_manager.get_results_for_requester(requester_did_id)
        
        return {
            "success": True,
            "results": results,
            "total": len(results),
            "check_time": time.time(),
            "host": host,
            "port": port
        }
        
    except Exception as e:
        logger.error(f"检查托管DID结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/wba/hosted-did/acknowledge/{result_id}")
async def acknowledge_hosted_did_result(request: Request, result_id: str):
    """确认已收到托管DID结果"""
    try:
        # 复用现有的域名管理逻辑
        domain_manager = get_domain_manager()
        host, port = domain_manager.get_host_port_from_request(request)
        
        from anp_server.did_host.hosted_did_result_manager import HostedDIDResultManager
        result_manager = HostedDIDResultManager.create_for_domain(host, port)
        success = await result_manager.acknowledge_result(result_id)
        
        if success:
            return {"success": True, "message": "结果确认成功"}
        else:
            raise HTTPException(status_code=404, detail="结果ID不存在")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"确认托管DID结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wba/hosted-did/list")
async def list_hosted_dids(request: Request):
    """列出当前域名下的所有托管DID"""
    try:
        # 复用现有的域名管理逻辑
        domain_manager = get_domain_manager()
        host, port = domain_manager.get_host_port_from_request(request)
        
        # 验证域名访问权限
        is_valid, error_msg = domain_manager.validate_domain_access(host, port)
        if not is_valid:
            raise HTTPException(status_code=403, detail=error_msg)
        
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
        
        return {
            "hosted_dids": sorted(hosted_dids, key=lambda x: x.get('created_at', 0), reverse=True),
            "total": len(hosted_dids),
            "host": host,
            "port": port
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"列出托管DID失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
