import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any

from anp_open_sdk.utils.log_base import logging as logger
from .hosted_did_queue_manager import HostedDIDQueueManager, RequestStatus
from .hosted_did_result_manager import HostedDIDResultManager
from ..anp_server_hoster import DIDHostManager


class HostedDIDProcessor:
    """托管DID后台处理器"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.queue_manager = HostedDIDQueueManager.create_for_domain(host, port)
        self.result_manager = HostedDIDResultManager.create_for_domain(host, port)
        self.did_manager = DIDHostManager.create_for_domain(host, port)
        self.running = False
    
    @classmethod
    def create_for_domain(cls, host: str, port: int) -> 'HostedDIDProcessor':
        """为指定域名创建处理器"""
        return cls(host, port)
    
    async def start_processing(self):
        """启动后台处理"""
        self.running = True
        logger.info(f"托管DID处理器启动: {self.host}:{self.port}")
        
        while self.running:
            try:
                await self.process_pending_requests()
                await asyncio.sleep(10)  # 每10秒检查一次
            except Exception as e:
                logger.error(f"处理循环出错: {e}")
                await asyncio.sleep(30)  # 出错后等待30秒
    
    def stop_processing(self):
        """停止后台处理"""
        self.running = False
        logger.info(f"托管DID处理器停止: {self.host}:{self.port}")
    
    async def process_pending_requests(self):
        """处理待处理的申请"""
        try:
            pending_requests = await self.queue_manager.get_pending_requests()
            
            for request_data in pending_requests:
                try:
                    request_id = request_data["request_id"]
                    
                    # 移动到处理中状态
                    await self.queue_manager.move_request_status(
                        request_id, RequestStatus.PENDING, RequestStatus.PROCESSING,
                        "开始处理申请"
                    )
                    
                    # 执行业务逻辑
                    success, result_data, error_msg = await self.perform_business_logic(request_data)
                    
                    if success:
                        # 处理成功，移动到完成状态
                        await self.queue_manager.move_request_status(
                            request_id, RequestStatus.PROCESSING, RequestStatus.COMPLETED,
                            "处理完成"
                        )
                        
                        # 发布结果
                        await self.result_manager.publish_result(
                            request_id=request_id,
                            requester_did=request_data["requester_did"],
                            hosted_did_document=result_data,
                            success=True
                        )
                        
                        logger.info(f"申请处理成功: {request_id}")
                    else:
                        # 处理失败，移动到失败状态
                        await self.queue_manager.move_request_status(
                            request_id, RequestStatus.PROCESSING, RequestStatus.FAILED,
                            f"处理失败: {error_msg}"
                        )
                        
                        # 发布错误结果
                        await self.result_manager.publish_result(
                            request_id=request_id,
                            requester_did=request_data["requester_did"],
                            hosted_did_document={},
                            success=False,
                            error_message=error_msg
                        )
                        
                        logger.error(f"申请处理失败: {request_id} - {error_msg}")
                        
                except Exception as e:
                    logger.error(f"处理申请时出错 {request_data.get('request_id', 'unknown')}: {e}")
                    
                    # 尝试移动到失败状态
                    try:
                        await self.queue_manager.move_request_status(
                            request_data["request_id"], RequestStatus.PROCESSING, RequestStatus.FAILED,
                            f"处理异常: {str(e)}"
                        )
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"处理待处理申请失败: {e}")
    
    async def perform_business_logic(self, request_data: Dict[str, Any]):
        """
        执行实际的业务逻辑
        
        这里可以添加：
        - 身份验证
        - 审批流程
        - 外部系统调用
        - 合规检查
        等等
        """
        try:

            # 获取申请数据
            did_document = request_data["did_document"]
            requester_did = request_data["requester_did"]
            
            logger.debug(f"执行业务逻辑: {request_data['request_id']}")
            
            # 1. 基本验证
            if not did_document or not requester_did:
                return False, {}, "DID文档或申请者DID不能为空"
            
            if not requester_did.startswith('did:wba:'):
                return False, {}, "申请者DID格式不正确"
            
            # 2. 检查重复申请
            if self.did_manager.is_duplicate_did(did_document):
                return False, {}, "重复的DID申请"
            
            # 3. 可选的身份验证逻辑
            if not await self._verify_requester_identity(requester_did):
                logger.warning(f"申请者身份验证失败: {requester_did}")
                # 注意：这里可以选择是否严格验证，目前只记录警告
            
            # 4. 可选的审批流程
            if not await self._check_approval_workflow(request_data):
                return False, {}, "审批流程未通过"
            
            # 5. 执行DID文档存储（使用现有逻辑）
            success, new_did_doc, error = self.did_manager.store_did_document(did_document)
            
            if success:
                logger.info(f"DID文档存储成功: {new_did_doc.get('id')}")
                return True, new_did_doc, ""
            else:
                return False, {}, error
                
        except Exception as e:
            error_msg = f"业务逻辑执行失败: {e}"
            logger.error(error_msg)
            return False, {}, error_msg
    
    async def _verify_requester_identity(self, requester_did: str) -> bool:
        """验证申请者身份"""
        try:
            # 这里可以添加实际的身份验证逻辑
            # 例如：检查申请者是否在白名单中，验证数字签名等
            
            # 目前简单验证DID格式
            if not requester_did or not requester_did.startswith('did:wba:'):
                return False
            
            # 可以添加更多验证逻辑
            # - 检查申请者的信誉度
            # - 验证申请者的数字签名
            # - 检查申请者是否在黑名单中
            
            return True
            
        except Exception as e:
            logger.error(f"身份验证失败: {e}")
            return False
    
    async def _check_approval_workflow(self, request_data: Dict[str, Any]) -> bool:
        """检查审批流程"""
        try:
            # 这里可以实现复杂的审批流程
            # 例如：
            # - 自动审批已知客户端
            # - 需要人工审批的情况
            # - 基于规则的自动审批
            
            # 目前简单的自动审批逻辑
            requester_did = request_data.get("requester_did", "")
            
            # 检查是否为已知的可信客户端
            trusted_clients = [
                "did:wba:localhost:9527:wba:user:",
                "did:wba:user.localhost:9527:wba:user:",
                # 可以添加更多可信客户端
            ]
            
            for trusted_prefix in trusted_clients:
                if requester_did.startswith(trusted_prefix):
                    logger.debug(f"自动审批可信客户端: {requester_did}")
                    return True
            
            # 对于其他客户端，也可以选择自动审批或需要人工审批
            # 目前选择自动审批
            logger.debug(f"自动审批申请: {requester_did}")
            return True
            
        except Exception as e:
            logger.error(f"审批流程检查失败: {e}")
            return False
    
    async def get_processing_statistics(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        try:
            queue_stats = {
                "pending": len(list((self.queue_manager.queue_dir / "pending").glob("*.json"))),
                "processing": len(list((self.queue_manager.queue_dir / "processing").glob("*.json"))),
                "completed": len(list((self.queue_manager.queue_dir / "completed").glob("*.json"))),
                "failed": len(list((self.queue_manager.queue_dir / "failed").glob("*.json")))
            }
            
            result_stats = await self.result_manager.get_result_statistics()
            
            return {
                "processor_status": "running" if self.running else "stopped",
                "host": self.host,
                "port": self.port,
                "queue_statistics": queue_stats,
                "result_statistics": result_stats,
                "last_check": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取处理统计失败: {e}")
            return {"error": str(e)}
