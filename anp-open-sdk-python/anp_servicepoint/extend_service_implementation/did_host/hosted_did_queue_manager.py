import json
import time
from enum import Enum
from typing import Dict, Any, List, Optional

from anp_foundation.domain import get_domain_manager

import logging
logger = logging.getLogger(__name__)

class RequestStatus(Enum):
    """申请状态枚举"""
    PENDING = "pending"        # 等待处理
    PROCESSING = "processing"  # 正在处理
    COMPLETED = "completed"    # 处理完成
    FAILED = "failed"         # 处理失败


class HostedDIDQueueManager:
    """托管DID申请队列管理器"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.domain_manager = get_domain_manager()
        
        # 获取队列存储路径
        paths = self.domain_manager.get_all_data_paths(host, port)
        self.queue_dir = paths['base_path'] / "hosted_did_queue"
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        
        # 子目录
        (self.queue_dir / "pending").mkdir(exist_ok=True)
        (self.queue_dir / "processing").mkdir(exist_ok=True)
        (self.queue_dir / "completed").mkdir(exist_ok=True)
        (self.queue_dir / "failed").mkdir(exist_ok=True)
    
    @classmethod
    def create_for_domain(cls, host: str, port: int) -> 'HostedDIDQueueManager':
        """为指定域名创建队列管理器"""
        return cls(host, port)
    
    async def add_request(self, request_id: str, hosted_request) -> bool:
        """添加申请到队列"""
        try:
            request_data = {
                "request_id": request_id,
                "requester_did": hosted_request.requester_did,
                "did_document": hosted_request.did_document,
                "callback_info": hosted_request.callback_info,
                "submit_time": time.time(),
                "status": RequestStatus.PENDING.value,
                "host": self.host,
                "port": self.port
            }
            
            # 保存到pending目录
            request_file = self.queue_dir / "pending" / f"{request_id}.json"
            with open(request_file, 'w', encoding='utf-8') as f:
                json.dump(request_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"申请已添加到队列: {request_id}")
            return True
            
        except Exception as e:
            logger.error(f"添加申请到队列失败: {e}")
            return False
    
    async def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """获取申请状态"""
        try:
            # 在各个状态目录中查找
            for status in RequestStatus:
                request_file = self.queue_dir / status.value / f"{request_id}.json"
                if request_file.exists():
                    with open(request_file, 'r', encoding='utf-8') as f:
                        request_data = json.load(f)
                    
                    return {
                        "request_id": request_id,
                        "status": status.value,
                        "submit_time": request_data.get("submit_time"),
                        "process_time": request_data.get("process_time"),
                        "complete_time": request_data.get("complete_time"),
                        "message": request_data.get("message", ""),
                        "requester_did": request_data.get("requester_did")
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"获取申请状态失败: {e}")
            return None
    
    async def get_pending_requests(self) -> List[Dict[str, Any]]:
        """获取待处理的申请"""
        try:
            pending_requests = []
            pending_dir = self.queue_dir / "pending"
            
            for request_file in pending_dir.glob("*.json"):
                try:
                    with open(request_file, 'r', encoding='utf-8') as f:
                        request_data = json.load(f)
                    pending_requests.append(request_data)
                except Exception as e:
                    logger.warning(f"读取申请文件失败 {request_file}: {e}")
            
            # 按提交时间排序
            return sorted(pending_requests, key=lambda x: x.get("submit_time", 0))
            
        except Exception as e:
            logger.error(f"获取待处理申请失败: {e}")
            return []
    
    async def move_request_status(self, request_id: str, from_status: RequestStatus, 
                                 to_status: RequestStatus, message: str = "") -> bool:
        """移动申请状态"""
        try:
            from_file = self.queue_dir / from_status.value / f"{request_id}.json"
            to_file = self.queue_dir / to_status.value / f"{request_id}.json"
            
            if not from_file.exists():
                logger.warning(f"申请文件不存在: {from_file}")
                return False
            
            # 读取并更新数据
            with open(from_file, 'r', encoding='utf-8') as f:
                request_data = json.load(f)
            
            request_data["status"] = to_status.value
            request_data["message"] = message
            
            if to_status == RequestStatus.PROCESSING:
                request_data["process_time"] = time.time()
            elif to_status in [RequestStatus.COMPLETED, RequestStatus.FAILED]:
                request_data["complete_time"] = time.time()
            
            # 保存到新位置
            with open(to_file, 'w', encoding='utf-8') as f:
                json.dump(request_data, f, ensure_ascii=False, indent=2)
            
            # 删除原文件
            from_file.unlink()
            
            logger.info(f"申请状态已更新: {request_id} {from_status.value} -> {to_status.value}")
            return True
            
        except Exception as e:
            logger.error(f"移动申请状态失败: {e}")
            return False
