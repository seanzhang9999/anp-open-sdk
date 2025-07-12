import json
import time
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional

from anp_open_sdk.domain import get_domain_manager
from anp_open_sdk.utils.log_base import logging as logger


class HostedDIDResultManager:
    """托管DID结果管理器"""
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.domain_manager = get_domain_manager()
        
        # 获取结果存储路径
        paths = self.domain_manager.get_all_data_paths(host, port)
        self.results_dir = paths['base_path'] / "hosted_did_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # 子目录
        (self.results_dir / "pending").mkdir(exist_ok=True)      # 待客户端获取
        (self.results_dir / "acknowledged").mkdir(exist_ok=True) # 已确认收到
    
    @classmethod
    def create_for_domain(cls, host: str, port: int) -> 'HostedDIDResultManager':
        """为指定域名创建结果管理器"""
        return cls(host, port)
    
    async def publish_result(self, request_id: str, requester_did: str, 
                           hosted_did_document: Dict[str, Any], success: bool = True, 
                           error_message: str = "") -> bool:
        """发布处理结果"""
        try:
            # 从requester_did中提取用户ID
            did_parts = requester_did.split(':')
            requester_id = did_parts[-1] if did_parts else str(uuid.uuid4())
            
            result_id = f"{requester_id}_{int(time.time())}_{request_id[:8]}"
            
            result_data = {
                "result_id": result_id,
                "request_id": request_id,
                "requester_did": requester_did,
                "requester_id": requester_id,
                "success": success,
                "created_time": time.time(),
                "host": self.host,
                "port": self.port
            }
            
            if success:
                result_data["hosted_did_document"] = hosted_did_document
            else:
                result_data["error_message"] = error_message
            
            # 保存到pending目录
            result_file = self.results_dir / "pending" / f"{result_id}.json"
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"处理结果已发布: {result_id} for {requester_did}")
            return True
            
        except Exception as e:
            logger.error(f"发布处理结果失败: {e}")
            return False
    
    async def get_results_for_requester(self, requester_did_id: str) -> List[Dict[str, Any]]:
        """获取指定申请者的处理结果"""
        try:
            results = []
            pending_dir = self.results_dir / "pending"
            
            for result_file in pending_dir.glob("*.json"):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                    
                    # 检查是否匹配申请者ID
                    if result_data.get("requester_id") == requester_did_id:
                        results.append(result_data)
                        
                except Exception as e:
                    logger.warning(f"读取结果文件失败 {result_file}: {e}")
            
            # 按创建时间排序
            return sorted(results, key=lambda x: x.get("created_time", 0), reverse=True)
            
        except Exception as e:
            logger.error(f"获取申请者结果失败: {e}")
            return []
    
    async def acknowledge_result(self, result_id: str) -> bool:
        """确认结果已收到"""
        try:
            pending_file = self.results_dir / "pending" / f"{result_id}.json"
            acknowledged_file = self.results_dir / "acknowledged" / f"{result_id}.json"
            
            if not pending_file.exists():
                logger.warning(f"结果文件不存在: {pending_file}")
                return False
            
            # 读取结果数据
            with open(pending_file, 'r', encoding='utf-8') as f:
                result_data = json.load(f)
            
            # 添加确认时间
            result_data["acknowledged_time"] = time.time()
            
            # 移动到已确认目录
            with open(acknowledged_file, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)
            
            # 删除原文件
            pending_file.unlink()
            
            logger.info(f"结果已确认: {result_id}")
            return True
            
        except Exception as e:
            logger.error(f"确认结果失败: {e}")
            return False
    
    async def cleanup_old_results(self, max_age_days: int = 7) -> int:
        """清理过期结果"""
        try:
            cleanup_count = 0
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 3600
            
            # 清理已确认的结果
            acknowledged_dir = self.results_dir / "acknowledged"
            for result_file in acknowledged_dir.glob("*.json"):
                try:
                    with open(result_file, 'r', encoding='utf-8') as f:
                        result_data = json.load(f)
                    
                    acknowledged_time = result_data.get("acknowledged_time", 0)
                    if current_time - acknowledged_time > max_age_seconds:
                        result_file.unlink()
                        cleanup_count += 1
                        logger.debug(f"清理过期结果: {result_file.name}")
                        
                except Exception as e:
                    logger.warning(f"清理结果文件失败 {result_file}: {e}")
            
            logger.info(f"清理了 {cleanup_count} 个过期结果")
            return cleanup_count
            
        except Exception as e:
            logger.error(f"清理过期结果失败: {e}")
            return 0
    
    async def get_result_statistics(self) -> Dict[str, Any]:
        """获取结果统计信息"""
        try:
            stats = {
                "pending_count": 0,
                "acknowledged_count": 0,
                "total_count": 0
            }
            
            # 统计待处理结果
            pending_dir = self.results_dir / "pending"
            stats["pending_count"] = len(list(pending_dir.glob("*.json")))
            
            # 统计已确认结果
            acknowledged_dir = self.results_dir / "acknowledged"
            stats["acknowledged_count"] = len(list(acknowledged_dir.glob("*.json")))
            
            stats["total_count"] = stats["pending_count"] + stats["acknowledged_count"]
            
            return stats
            
        except Exception as e:
            logger.error(f"获取结果统计失败: {e}")
            return {"error": str(e)}
