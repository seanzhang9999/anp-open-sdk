"""
自定义记忆管理器

提供完整的自定义记忆CRUD操作接口
"""

import threading
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Callable, Union, Tuple
import logging

from .memory_models import MemoryEntry, MemoryType, MemoryMetadata
from .memory_manager import MemoryManager, get_memory_manager
from .custom_memory_models import (
    CustomMemorySchema, 
    CustomMemoryTemplate, 
    CustomMemoryType,
    TemplateFactory
)

logger = logging.getLogger(__name__)


class CustomMemoryManager:
    """自定义记忆管理器"""
    
    def __init__(self, base_manager: Optional[MemoryManager] = None):
        self.base_manager = base_manager or get_memory_manager()
        
        # 自定义记忆相关缓存
        self._templates: Dict[str, CustomMemoryTemplate] = {}
        self._schemas: Dict[str, CustomMemorySchema] = {}
        self._custom_memory_cache: Dict[str, MemoryEntry] = {}
        
        # 索引
        self._template_index: Dict[str, List[str]] = {}  # template_name -> memory_ids
        self._schema_index: Dict[str, List[str]] = {}    # schema_name -> memory_ids
        
        self._lock = threading.RLock()
        
        # 初始化预定义模板
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """初始化预定义模板"""
        try:
            default_templates = [
                TemplateFactory.create_user_profile_template(),
                TemplateFactory.create_task_template(),
                TemplateFactory.create_knowledge_template(),
                TemplateFactory.create_conversation_template(),
                TemplateFactory.create_event_log_template()
            ]
            
            with self._lock:
                for template in default_templates:
                    self._templates[template.id] = template
                    self._schemas[template.schema.name] = template.schema
                    
            logger.info(f"初始化了 {len(default_templates)} 个预定义模板")
            
        except Exception as e:
            logger.error(f"初始化预定义模板失败: {e}")
    
    # ============ 模板管理 ============
    
    async def create_template(
        self,
        name: str,
        schema: CustomMemorySchema,
        description: str = "",
        default_tags: Optional[List[str]] = None,
        default_keywords: Optional[List[str]] = None
    ) -> CustomMemoryTemplate:
        """创建自定义记忆模板"""
        
        template = CustomMemoryTemplate(
            name=name,
            description=description,
            schema=schema,
            default_tags=default_tags or [],
            default_keywords=default_keywords or []
        )
        
        with self._lock:
            self._templates[template.id] = template
            self._schemas[schema.name] = schema
        
        logger.debug(f"创建模板: {name} ({template.id})")
        return template
    
    async def get_template(self, template_id: str) -> Optional[CustomMemoryTemplate]:
        """获取模板"""
        with self._lock:
            return self._templates.get(template_id)
    
    async def get_template_by_name(self, template_name: str) -> Optional[CustomMemoryTemplate]:
        """根据名称获取模板"""
        with self._lock:
            for template in self._templates.values():
                if template.name == template_name:
                    return template
        return None
    
    async def list_templates(self) -> List[CustomMemoryTemplate]:
        """列出所有模板"""
        with self._lock:
            return list(self._templates.values())
    
    async def update_template(
        self,
        template_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        default_tags: Optional[List[str]] = None,
        default_keywords: Optional[List[str]] = None
    ) -> bool:
        """更新模板"""
        with self._lock:
            template = self._templates.get(template_id)
            if not template:
                return False
            
            if name is not None:
                template.name = name
            if description is not None:
                template.description = description
            if default_tags is not None:
                template.default_tags = default_tags
            if default_keywords is not None:
                template.default_keywords = default_keywords
            
            return True
    
    async def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        with self._lock:
            template = self._templates.pop(template_id, None)
            if template:
                # 清理相关索引
                if template.name in self._template_index:
                    del self._template_index[template.name]
                
                # 清理模式（如果没有其他模板使用）
                schema_in_use = any(
                    t.schema.name == template.schema.name 
                    for t in self._templates.values()
                )
                if not schema_in_use:
                    self._schemas.pop(template.schema.name, None)
                    if template.schema.name in self._schema_index:
                        del self._schema_index[template.schema.name]
                
                logger.debug(f"删除模板: {template.name} ({template_id})")
                return True
            return False
    
    # ============ 自定义记忆CRUD操作 ============
    
    async def create_custom_memory(
        self,
        template_id: str,
        content: Dict[str, Any],
        source_agent_did: str,
        source_agent_name: str,
        title: Optional[str] = None,
        target_agent_did: Optional[str] = None,
        target_agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        expiry_time: Optional[datetime] = None
    ) -> MemoryEntry:
        """创建自定义记忆"""
        
        template = await self.get_template(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        # 使用模板创建记忆
        memory = template.create_memory(
            content=content,
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            title=title,
            target_agent_did=target_agent_did,
            target_agent_name=target_agent_name,
            session_id=session_id,
            tags=tags,
            keywords=keywords,
            expiry_time=expiry_time
        )
        
        # 保存到基础管理器
        success = await self.base_manager.storage.save_memory(memory)
        if not success:
            raise RuntimeError(f"保存自定义记忆失败: {memory.id}")
        
        # 更新缓存和索引
        with self._lock:
            self._custom_memory_cache[memory.id] = memory
            
            # 更新模板索引
            if template.name not in self._template_index:
                self._template_index[template.name] = []
            self._template_index[template.name].append(memory.id)
            
            # 更新模式索引
            if template.schema.name not in self._schema_index:
                self._schema_index[template.schema.name] = []
            self._schema_index[template.schema.name].append(memory.id)
        
        logger.debug(f"创建自定义记忆: {memory.title} ({memory.id})")
        return memory
    
    async def get_custom_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """获取自定义记忆"""
        
        # 先检查缓存
        with self._lock:
            if memory_id in self._custom_memory_cache:
                return self._custom_memory_cache[memory_id]
        
        # 从基础管理器获取
        memory = await self.base_manager.get_memory(memory_id)
        
        # 验证是否为自定义记忆
        if memory and self._is_custom_memory(memory):
            with self._lock:
                self._custom_memory_cache[memory_id] = memory
            return memory
        
        return None
    
    async def update_custom_memory(
        self,
        memory_id: str,
        content: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        **kwargs
    ) -> bool:
        """更新自定义记忆"""
        
        memory = await self.get_custom_memory(memory_id)
        if not memory:
            return False
        
        # 获取模板信息进行验证
        template_id = memory.content.get('template_id')
        if template_id and content is not None:
            template = await self.get_template(template_id)
            if template:
                # 验证新内容
                is_valid, errors = template.schema.validate_data(content)
                if not is_valid:
                    raise ValueError(f"数据验证失败: {', '.join(errors)}")
                
                # 更新自定义数据
                memory.content['custom_data'] = content
        
        # 更新其他字段
        if title:
            memory.title = title
        
        if tags is not None:
            memory.metadata.tags = tags
        
        if keywords is not None:
            memory.metadata.keywords = keywords
        
        # 更新时间戳
        memory.updated_at = datetime.now()
        
        # 保存更新
        success = await self.base_manager.update_memory(memory)
        
        if success:
            # 更新缓存
            with self._lock:
                self._custom_memory_cache[memory_id] = memory
            
            logger.debug(f"更新自定义记忆: {memory.title} ({memory_id})")
        
        return success
    
    async def delete_custom_memory(self, memory_id: str) -> bool:
        """删除自定义记忆"""
        
        memory = await self.get_custom_memory(memory_id)
        if not memory:
            return False
        
        # 从基础管理器删除
        success = await self.base_manager.delete_memory(memory_id)
        
        if success:
            # 清理缓存和索引
            with self._lock:
                self._custom_memory_cache.pop(memory_id, None)
                
                # 清理索引
                template_id = memory.content.get('template_id')
                if template_id:
                    template = self._templates.get(template_id)
                    if template:
                        # 从模板索引中移除
                        if template.name in self._template_index:
                            try:
                                self._template_index[template.name].remove(memory_id)
                            except ValueError:
                                pass
                        
                        # 从模式索引中移除
                        if template.schema.name in self._schema_index:
                            try:
                                self._schema_index[template.schema.name].remove(memory_id)
                            except ValueError:
                                pass
            
            logger.debug(f"删除自定义记忆: {memory.title} ({memory_id})")
        
        return success
    
    # ============ 查询功能 ============
    
    async def search_custom_memories(
        self,
        template_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        content_query: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[MemoryEntry]:
        """搜索自定义记忆"""
        
        results = []
        
        # 基于模板名搜索
        if template_name:
            with self._lock:
                memory_ids = self._template_index.get(template_name, [])
            
            for memory_id in memory_ids:
                memory = await self.get_custom_memory(memory_id)
                if memory:
                    results.append(memory)
        
        # 基于模式名搜索
        elif schema_name:
            with self._lock:
                memory_ids = self._schema_index.get(schema_name, [])
            
            for memory_id in memory_ids:
                memory = await self.get_custom_memory(memory_id)
                if memory:
                    results.append(memory)
        
        # 通用搜索 - 搜索所有PATTERN类型的记忆并过滤出自定义记忆
        else:
            # 使用基础管理器搜索PATTERN类型记忆
            all_memories = await self.base_manager.search_memories(
                memory_type=MemoryType.PATTERN,
                **kwargs
            )
            
            # 过滤出自定义记忆
            for memory in all_memories:
                if self._is_custom_memory(memory):
                    results.append(memory)
        
        # 内容查询过滤
        if content_query and results:
            filtered_results = []
            for memory in results:
                custom_data = memory.content.get('custom_data', {})
                if self._match_content_query(custom_data, content_query):
                    filtered_results.append(memory)
            results = filtered_results
        
        return results
    
    async def list_custom_memories_by_template(self, template_name: str) -> List[MemoryEntry]:
        """列出指定模板的所有记忆"""
        return await self.search_custom_memories(template_name=template_name)
    
    async def list_custom_memories_by_schema(self, schema_name: str) -> List[MemoryEntry]:
        """列出指定模式的所有记忆"""
        return await self.search_custom_memories(schema_name=schema_name)
    
    # ============ 批量操作 ============
    
    async def create_custom_memories_batch(
        self,
        template_id: str,
        contents: List[Dict[str, Any]],
        source_agent_did: str,
        source_agent_name: str,
        **kwargs
    ) -> List[MemoryEntry]:
        """批量创建自定义记忆"""
        
        memories = []
        
        for i, content in enumerate(contents):
            try:
                title = kwargs.get('title')
                if title and isinstance(title, str):
                    title = f"{title}_{i+1}"
                elif not title:
                    title = f"Batch_{i+1}"
                
                memory = await self.create_custom_memory(
                    template_id=template_id,
                    content=content,
                    source_agent_did=source_agent_did,
                    source_agent_name=source_agent_name,
                    title=title,
                    **{k: v for k, v in kwargs.items() if k != 'title'}
                )
                memories.append(memory)
                
            except Exception as e:
                logger.error(f"批量创建自定义记忆失败 (索引 {i}): {e}")
        
        logger.debug(f"批量创建了 {len(memories)} 条自定义记忆")
        return memories
    
    async def delete_custom_memories_batch(self, memory_ids: List[str]) -> int:
        """批量删除自定义记忆"""
        
        deleted_count = 0
        
        for memory_id in memory_ids:
            try:
                if await self.delete_custom_memory(memory_id):
                    deleted_count += 1
            except Exception as e:
                logger.error(f"批量删除自定义记忆失败 ({memory_id}): {e}")
        
        logger.debug(f"批量删除了 {deleted_count} 条自定义记忆")
        return deleted_count
    
    # ============ 工具方法 ============
    
    def _is_custom_memory(self, memory: MemoryEntry) -> bool:
        """检查是否为自定义记忆"""
        return (
            memory.memory_type == MemoryType.PATTERN and
            'template_id' in memory.content and
            'custom_data' in memory.content
        )
    
    def _match_content_query(self, data: Dict[str, Any], query: Dict[str, Any]) -> bool:
        """检查数据是否匹配内容查询"""
        for key, value in query.items():
            if key not in data:
                return False
            
            if isinstance(value, dict) and isinstance(data[key], dict):
                if not self._match_content_query(data[key], value):
                    return False
            elif data[key] != value:
                return False
        
        return True
    
    # ============ 统计功能 ============
    
    async def get_custom_memory_statistics(self) -> Dict[str, Any]:
        """获取自定义记忆统计信息"""
        
        with self._lock:
            template_stats = {
                name: len(memory_ids) 
                for name, memory_ids in self._template_index.items()
            }
            
            schema_stats = {
                name: len(memory_ids) 
                for name, memory_ids in self._schema_index.items()
            }
        
        return {
            'total_templates': len(self._templates),
            'total_schemas': len(self._schemas),
            'total_custom_memories': len(self._custom_memory_cache),
            'template_usage': template_stats,
            'schema_usage': schema_stats
        }
    
    # ============ 便捷方法 ============
    
    async def create_user_profile(
        self,
        user_data: Dict[str, Any],
        source_agent_did: str,
        source_agent_name: str,
        **kwargs
    ) -> MemoryEntry:
        """创建用户档案记忆"""
        template = await self.get_template_by_name("user_profile_template")
        if not template:
            raise ValueError("用户档案模板不存在")
        
        return await self.create_custom_memory(
            template_id=template.id,
            content=user_data,
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            title=f"用户档案-{user_data.get('name', 'Unknown')}",
            **kwargs
        )
    
    async def create_task(
        self,
        task_data: Dict[str, Any],
        source_agent_did: str,
        source_agent_name: str,
        **kwargs
    ) -> MemoryEntry:
        """创建任务记忆"""
        template = await self.get_template_by_name("task_template")
        if not template:
            raise ValueError("任务模板不存在")
        
        return await self.create_custom_memory(
            template_id=template.id,
            content=task_data,
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            title=f"任务-{task_data.get('task_name', 'Unknown')}",
            **kwargs
        )
    
    async def create_knowledge(
        self,
        knowledge_data: Dict[str, Any],
        source_agent_did: str,
        source_agent_name: str,
        **kwargs
    ) -> MemoryEntry:
        """创建知识记忆"""
        template = await self.get_template_by_name("knowledge_template")
        if not template:
            raise ValueError("知识模板不存在")
        
        return await self.create_custom_memory(
            template_id=template.id,
            content=knowledge_data,
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            title=f"知识-{knowledge_data.get('title', 'Unknown')}",
            **kwargs
        )


# 全局自定义记忆管理器实例
_global_custom_memory_manager: Optional[CustomMemoryManager] = None


def get_custom_memory_manager() -> CustomMemoryManager:
    """获取全局自定义记忆管理器实例"""
    global _global_custom_memory_manager
    if _global_custom_memory_manager is None:
        _global_custom_memory_manager = CustomMemoryManager()
    return _global_custom_memory_manager


def set_custom_memory_manager(manager: CustomMemoryManager):
    """设置全局自定义记忆管理器实例"""
    global _global_custom_memory_manager
    _global_custom_memory_manager = manager