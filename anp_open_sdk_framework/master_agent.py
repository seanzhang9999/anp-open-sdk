# Copyright 2024 ANP Open SDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from .unified_crawler import UnifiedCrawler
from .unified_caller import UnifiedCaller

logger = logging.getLogger(__name__)


class MasterAgent:
    """主智能体 - 接受用户任务，统一调度资源"""
    
    def __init__(self, sdk, name: str = "MasterAgent"):
        self.sdk = sdk
        self.name = name
        self.crawler = UnifiedCrawler(sdk)
        self.caller = UnifiedCaller(sdk)
        self.task_history = []
    
    async def initialize(self):
        """初始化主智能体"""
        logger.info(f"🚀 初始化主智能体: {self.name}")
        await self.crawler.discover_all_resources()
        logger.info("✅ 主智能体初始化完成")
    
    async def execute_task(self, task: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """执行用户任务"""
        logger.info(f"📋 接收任务: {task}")
        
        task_id = len(self.task_history) + 1
        task_record = {
            "id": task_id,
            "task": task,
            "context": context or {},
            "status": "processing",
            "result": None,
            "error": None
        }
        
        self.task_history.append(task_record)
        
        try:
            # 分析任务并执行
            result = await self._analyze_and_execute(task, context)
            task_record["status"] = "completed"
            task_record["result"] = result
            
            logger.info(f"✅ 任务完成: {task}")
            return {
                "task_id": task_id,
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            task_record["status"] = "failed"
            task_record["error"] = str(e)
            
            logger.error(f"❌ 任务失败: {task}, 错误: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }
    
    async def _analyze_and_execute(self, task: str, context: Optional[Dict] = None) -> Any:
        """分析任务并执行"""
        # 简单的任务分析逻辑
        task_lower = task.lower()
        
        # 如果是查询资源
        if any(keyword in task_lower for keyword in ["list", "show", "查看", "显示", "资源"]):
            return await self._handle_resource_query(task)
        
        # 如果是搜索任务
        if any(keyword in task_lower for keyword in ["search", "find", "搜索", "查找"]):
            return await self._handle_search_task(task)
        
        # 如果是调用任务
        if any(keyword in task_lower for keyword in ["call", "run", "execute", "调用", "执行"]):
            return await self._handle_call_task(task, context)
        
        # 默认使用智能调用
        return await self.crawler.intelligent_call(task, **(context or {}))
    
    async def _handle_resource_query(self, task: str) -> Dict[str, Any]:
        """处理资源查询任务"""
        summary = self.crawler.get_resource_summary()
        if "message" in summary:
            await self.crawler.discover_all_resources()
            summary = self.crawler.get_resource_summary()
        
        return {
            "type": "resource_summary",
            "data": summary
        }
    
    async def _handle_search_task(self, task: str) -> Dict[str, Any]:
        """处理搜索任务"""
        # 提取搜索关键词（简单实现）
        keywords = ["search", "find", "搜索", "查找"]
        keyword = task
        for kw in keywords:
            if kw in task.lower():
                keyword = task.lower().replace(kw, "").strip()
                break
        
        results = await self.crawler.search_resources(keyword)
        
        return {
            "type": "search_results",
            "keyword": keyword,
            "results": results
        }
    
    async def _handle_call_task(self, task: str, context: Optional[Dict] = None) -> Any:
        """处理调用任务"""
        # 简单的调用解析（实际应该更复杂）
        if context and "method_name" in context:
            return await self.crawler.call_by_name(
                context["method_name"], 
                **context.get("args", {})
            )
        
        # 使用智能调用
        return await self.crawler.intelligent_call(task, **(context or {}))
    
    def get_task_history(self) -> List[Dict]:
        """获取任务历史"""
        return self.task_history
    
    async def get_capabilities(self) -> Dict[str, Any]:
        """获取能力描述"""
        resources = await self.crawler.discover_all_resources()
        
        capabilities = {
            "name": self.name,
            "description": "主智能体 - 统一任务调度和资源管理",
            "features": [
                "统一资源发现和管理",
                "智能任务分析和执行",
                "本地方法和远程Agent调用",
                "任务历史记录和追踪"
            ],
            "available_resources": self.crawler.get_resource_summary(),
            "supported_task_types": [
                "资源查询 (list, show, 查看, 显示)",
                "资源搜索 (search, find, 搜索, 查找)",
                "方法调用 (call, run, execute, 调用, 执行)",
                "智能任务执行 (自然语言描述)"
            ]
        }
        
        return capabilities
