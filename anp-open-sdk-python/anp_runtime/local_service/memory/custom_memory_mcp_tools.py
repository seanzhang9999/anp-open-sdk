"""
自定义记忆MCP工具集

提供标准化的MCP工具接口，用于操作自定义记忆系统
"""

import json
import asyncio
from typing import Dict, List, Optional, Any
import logging

from .custom_memory_manager import CustomMemoryManager, get_custom_memory_manager
from .custom_memory_models import CustomMemorySchema

logger = logging.getLogger(__name__)


class CustomMemoryMCPTools:
    """自定义记忆MCP工具集"""
    
    def __init__(self, custom_manager: Optional[CustomMemoryManager] = None):
        self.custom_manager = custom_manager or get_custom_memory_manager()
    
    async def create_memory_template(
        self,
        name: str,
        schema_definition: Dict[str, Any],
        description: str = "",
        default_tags: Optional[List[str]] = None,
        default_keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        MCP Tool: 创建自定义记忆模板
        
        Args:
            name: 模板名称
            schema_definition: 模式定义
                {
                    "fields": {
                        "field_name": {"type": "str", "description": "字段描述"},
                        ...
                    },
                    "required_fields": ["field1", "field2"],
                    "validation_rules": {...}
                }
            description: 模板描述
            default_tags: 默认标签
            default_keywords: 默认关键词
        
        Returns:
            {
                "success": bool,
                "template_id": str,
                "message": str
            }
        """
        try:
            # 创建模式
            schema = CustomMemorySchema(
                name=f"{name}_schema",
                description=schema_definition.get('description', ''),
                fields=schema_definition.get('fields', {}),
                required_fields=schema_definition.get('required_fields', []),
                validation_rules=schema_definition.get('validation_rules', {})
            )
            
            # 创建模板
            template = await self.custom_manager.create_template(
                name=name,
                schema=schema,
                description=description,
                default_tags=default_tags or [],
                default_keywords=default_keywords or []
            )
            
            return {
                "success": True,
                "template_id": template.id,
                "message": f"模板 '{name}' 创建成功"
            }
        
        except Exception as e:
            logger.error(f"创建模板失败: {e}")
            return {
                "success": False,
                "template_id": None,
                "message": f"创建模板失败: {str(e)}"
            }
    
    async def create_custom_memory(
        self,
        template_id: str,
        content: Dict[str, Any],
        source_agent_did: str,
        source_agent_name: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        session_id: Optional[str] = None,
        target_agent_did: Optional[str] = None,
        target_agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        MCP Tool: 创建自定义记忆
        
        Args:
            template_id: 模板ID
            content: 记忆内容
            source_agent_did: 来源Agent DID
            source_agent_name: 来源Agent名称
            title: 记忆标题
            tags: 标签
            keywords: 关键词
            session_id: 会话ID
            target_agent_did: 目标Agent DID
            target_agent_name: 目标Agent名称
        
        Returns:
            {
                "success": bool,
                "memory_id": str,
                "message": str
            }
        """
        try:
            memory = await self.custom_manager.create_custom_memory(
                template_id=template_id,
                content=content,
                source_agent_did=source_agent_did,
                source_agent_name=source_agent_name,
                title=title,
                tags=tags,
                keywords=keywords,
                session_id=session_id,
                target_agent_did=target_agent_did,
                target_agent_name=target_agent_name
            )
            
            return {
                "success": True,
                "memory_id": memory.id,
                "message": f"自定义记忆 '{memory.title}' 创建成功"
            }
        
        except Exception as e:
            logger.error(f"创建自定义记忆失败: {e}")
            return {
                "success": False,
                "memory_id": None,
                "message": f"创建自定义记忆失败: {str(e)}"
            }
    
    async def get_custom_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        MCP Tool: 获取自定义记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            {
                "success": bool,
                "memory": Dict[str, Any] | None,
                "message": str
            }
        """
        try:
            memory = await self.custom_manager.get_custom_memory(memory_id)
            
            if memory:
                return {
                    "success": True,
                    "memory": memory.to_dict(),
                    "message": "获取自定义记忆成功"
                }
            else:
                return {
                    "success": False,
                    "memory": None,
                    "message": f"未找到记忆: {memory_id}"
                }
        
        except Exception as e:
            logger.error(f"获取自定义记忆失败: {e}")
            return {
                "success": False,
                "memory": None,
                "message": f"获取自定义记忆失败: {str(e)}"
            }
    
    async def update_custom_memory(
        self,
        memory_id: str,
        content: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        MCP Tool: 更新自定义记忆
        
        Args:
            memory_id: 记忆ID
            content: 新的记忆内容
            title: 新的标题
            tags: 新的标签
            keywords: 新的关键词
        
        Returns:
            {
                "success": bool,
                "message": str
            }
        """
        try:
            success = await self.custom_manager.update_custom_memory(
                memory_id=memory_id,
                content=content,
                title=title,
                tags=tags,
                keywords=keywords
            )
            
            if success:
                return {
                    "success": True,
                    "message": f"自定义记忆 {memory_id} 更新成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"更新自定义记忆失败: 记忆不存在或更新失败"
                }
        
        except Exception as e:
            logger.error(f"更新自定义记忆失败: {e}")
            return {
                "success": False,
                "message": f"更新自定义记忆失败: {str(e)}"
            }
    
    async def delete_custom_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        MCP Tool: 删除自定义记忆
        
        Args:
            memory_id: 记忆ID
        
        Returns:
            {
                "success": bool,
                "message": str
            }
        """
        try:
            success = await self.custom_manager.delete_custom_memory(memory_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"自定义记忆 {memory_id} 删除成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"删除自定义记忆失败: 记忆不存在或删除失败"
                }
        
        except Exception as e:
            logger.error(f"删除自定义记忆失败: {e}")
            return {
                "success": False,
                "message": f"删除自定义记忆失败: {str(e)}"
            }
    
    async def search_custom_memories(
        self,
        template_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        content_query: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        MCP Tool: 搜索自定义记忆
        
        Args:
            template_name: 模板名称
            schema_name: 模式名称
            content_query: 内容查询条件
            tags: 标签过滤
            keywords: 关键词过滤
            limit: 结果限制
        
        Returns:
            {
                "success": bool,
                "memories": List[Dict[str, Any]],
                "count": int,
                "message": str
            }
        """
        try:
            memories = await self.custom_manager.search_custom_memories(
                template_name=template_name,
                schema_name=schema_name,
                content_query=content_query,
                tags=tags,
                keywords=keywords,
                limit=limit
            )
            
            return {
                "success": True,
                "memories": [memory.to_dict() for memory in memories],
                "count": len(memories),
                "message": f"搜索完成，找到 {len(memories)} 条自定义记忆"
            }
        
        except Exception as e:
            logger.error(f"搜索自定义记忆失败: {e}")
            return {
                "success": False,
                "memories": [],
                "count": 0,
                "message": f"搜索自定义记忆失败: {str(e)}"
            }
    
    async def list_templates(self) -> Dict[str, Any]:
        """
        MCP Tool: 列出所有模板
        
        Returns:
            {
                "success": bool,
                "templates": List[Dict[str, Any]],
                "count": int,
                "message": str
            }
        """
        try:
            templates = await self.custom_manager.list_templates()
            
            template_data = []
            for template in templates:
                template_data.append({
                    "id": template.id,
                    "name": template.name,
                    "description": template.description,
                    "schema_name": template.schema.name,
                    "schema_version": template.schema.version,
                    "default_tags": template.default_tags,
                    "default_keywords": template.default_keywords,
                    "created_at": template.created_at.isoformat()
                })
            
            return {
                "success": True,
                "templates": template_data,
                "count": len(template_data),
                "message": f"获取模板列表成功，共 {len(template_data)} 个模板"
            }
        
        except Exception as e:
            logger.error(f"获取模板列表失败: {e}")
            return {
                "success": False,
                "templates": [],
                "count": 0,
                "message": f"获取模板列表失败: {str(e)}"
            }
    
    async def get_template_by_name(self, template_name: str) -> Dict[str, Any]:
        """
        MCP Tool: 根据名称获取模板
        
        Args:
            template_name: 模板名称
        
        Returns:
            {
                "success": bool,
                "template": Dict[str, Any] | None,
                "message": str
            }
        """
        try:
            template = await self.custom_manager.get_template_by_name(template_name)
            
            if template:
                return {
                    "success": True,
                    "template": template.to_dict(),
                    "message": f"获取模板 '{template_name}' 成功"
                }
            else:
                return {
                    "success": False,
                    "template": None,
                    "message": f"未找到模板: {template_name}"
                }
        
        except Exception as e:
            logger.error(f"获取模板失败: {e}")
            return {
                "success": False,
                "template": None,
                "message": f"获取模板失败: {str(e)}"
            }
    
    async def delete_template(self, template_id: str) -> Dict[str, Any]:
        """
        MCP Tool: 删除模板
        
        Args:
            template_id: 模板ID
        
        Returns:
            {
                "success": bool,
                "message": str
            }
        """
        try:
            success = await self.custom_manager.delete_template(template_id)
            
            if success:
                return {
                    "success": True,
                    "message": f"模板 {template_id} 删除成功"
                }
            else:
                return {
                    "success": False,
                    "message": f"删除模板失败: 模板不存在或删除失败"
                }
        
        except Exception as e:
            logger.error(f"删除模板失败: {e}")
            return {
                "success": False,
                "message": f"删除模板失败: {str(e)}"
            }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        MCP Tool: 获取自定义记忆统计信息
        
        Returns:
            {
                "success": bool,
                "statistics": Dict[str, Any],
                "message": str
            }
        """
        try:
            stats = await self.custom_manager.get_custom_memory_statistics()
            
            return {
                "success": True,
                "statistics": stats,
                "message": "获取统计信息成功"
            }
        
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "success": False,
                "statistics": {},
                "message": f"获取统计信息失败: {str(e)}"
            }
    
    async def create_user_profile(
        self,
        user_data: Dict[str, Any],
        source_agent_did: str,
        source_agent_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        MCP Tool: 创建用户档案记忆（便捷方法）
        
        Args:
            user_data: 用户数据
            source_agent_did: 来源Agent DID
            source_agent_name: 来源Agent名称
            **kwargs: 其他参数
        
        Returns:
            {
                "success": bool,
                "memory_id": str,
                "message": str
            }
        """
        try:
            memory = await self.custom_manager.create_user_profile(
                user_data=user_data,
                source_agent_did=source_agent_did,
                source_agent_name=source_agent_name,
                **kwargs
            )
            
            return {
                "success": True,
                "memory_id": memory.id,
                "message": f"用户档案 '{user_data.get('name', 'Unknown')}' 创建成功"
            }
        
        except Exception as e:
            logger.error(f"创建用户档案失败: {e}")
            return {
                "success": False,
                "memory_id": None,
                "message": f"创建用户档案失败: {str(e)}"
            }
    
    async def create_task(
        self,
        task_data: Dict[str, Any],
        source_agent_did: str,
        source_agent_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        MCP Tool: 创建任务记忆（便捷方法）
        
        Args:
            task_data: 任务数据
            source_agent_did: 来源Agent DID
            source_agent_name: 来源Agent名称
            **kwargs: 其他参数
        
        Returns:
            {
                "success": bool,
                "memory_id": str,
                "message": str
            }
        """
        try:
            memory = await self.custom_manager.create_task(
                task_data=task_data,
                source_agent_did=source_agent_did,
                source_agent_name=source_agent_name,
                **kwargs
            )
            
            return {
                "success": True,
                "memory_id": memory.id,
                "message": f"任务 '{task_data.get('task_name', 'Unknown')}' 创建成功"
            }
        
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return {
                "success": False,
                "memory_id": None,
                "message": f"创建任务失败: {str(e)}"
            }
    
    async def create_knowledge(
        self,
        knowledge_data: Dict[str, Any],
        source_agent_did: str,
        source_agent_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        MCP Tool: 创建知识记忆（便捷方法）
        
        Args:
            knowledge_data: 知识数据
            source_agent_did: 来源Agent DID
            source_agent_name: 来源Agent名称
            **kwargs: 其他参数
        
        Returns:
            {
                "success": bool,
                "memory_id": str,
                "message": str
            }
        """
        try:
            memory = await self.custom_manager.create_knowledge(
                knowledge_data=knowledge_data,
                source_agent_did=source_agent_did,
                source_agent_name=source_agent_name,
                **kwargs
            )
            
            return {
                "success": True,
                "memory_id": memory.id,
                "message": f"知识 '{knowledge_data.get('title', 'Unknown')}' 创建成功"
            }
        
        except Exception as e:
            logger.error(f"创建知识失败: {e}")
            return {
                "success": False,
                "memory_id": None,
                "message": f"创建知识失败: {str(e)}"
            }
    
    async def batch_create_memories(
        self,
        template_id: str,
        contents: List[Dict[str, Any]],
        source_agent_did: str,
        source_agent_name: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        MCP Tool: 批量创建自定义记忆
        
        Args:
            template_id: 模板ID
            contents: 记忆内容列表
            source_agent_did: 来源Agent DID
            source_agent_name: 来源Agent名称
            **kwargs: 其他参数
        
        Returns:
            {
                "success": bool,
                "created_count": int,
                "memory_ids": List[str],
                "message": str
            }
        """
        try:
            memories = await self.custom_manager.create_custom_memories_batch(
                template_id=template_id,
                contents=contents,
                source_agent_did=source_agent_did,
                source_agent_name=source_agent_name,
                **kwargs
            )
            
            memory_ids = [memory.id for memory in memories]
            
            return {
                "success": True,
                "created_count": len(memories),
                "memory_ids": memory_ids,
                "message": f"批量创建成功，共创建 {len(memories)} 条记忆"
            }
        
        except Exception as e:
            logger.error(f"批量创建记忆失败: {e}")
            return {
                "success": False,
                "created_count": 0,
                "memory_ids": [],
                "message": f"批量创建记忆失败: {str(e)}"
            }
    
    async def batch_delete_memories(self, memory_ids: List[str]) -> Dict[str, Any]:
        """
        MCP Tool: 批量删除自定义记忆
        
        Args:
            memory_ids: 记忆ID列表
        
        Returns:
            {
                "success": bool,
                "deleted_count": int,
                "message": str
            }
        """
        try:
            deleted_count = await self.custom_manager.delete_custom_memories_batch(memory_ids)
            
            return {
                "success": True,
                "deleted_count": deleted_count,
                "message": f"批量删除成功，共删除 {deleted_count} 条记忆"
            }
        
        except Exception as e:
            logger.error(f"批量删除记忆失败: {e}")
            return {
                "success": False,
                "deleted_count": 0,
                "message": f"批量删除记忆失败: {str(e)}"
            }


# 全局MCP工具实例
_global_mcp_tools: Optional[CustomMemoryMCPTools] = None


def get_custom_memory_mcp_tools() -> CustomMemoryMCPTools:
    """获取全局MCP工具实例"""
    global _global_mcp_tools
    if _global_mcp_tools is None:
        _global_mcp_tools = CustomMemoryMCPTools()
    return _global_mcp_tools


def set_custom_memory_mcp_tools(tools: CustomMemoryMCPTools):
    """设置全局MCP工具实例"""
    global _global_mcp_tools
    _global_mcp_tools = tools