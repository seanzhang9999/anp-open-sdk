# 自定义Memory管理系统设计方案

## 概述

基于ANP Open SDK Python版本现有的memory管理系统，设计并实现一套完整的自定义memory CRUD接口，允许开发者通过代码手动管理自定义memory，并提供MCP Tool接口封装指导。

## 1. 现有Memory系统分析

### 1.1 核心组件

现有memory系统包含以下核心组件：

- **MemoryEntry**: 基础记忆条目数据模型
- **MemoryType**: 记忆类型枚举（METHOD_CALL, INPUT_OUTPUT, USER_PREFERENCE等）
- **MemoryMetadata**: 记忆元数据（来源Agent、标签、关键词等）
- **MemoryManager**: 统一记忆管理器
- **MemoryStorage**: 存储接口（SQLite、内存存储）
- **ContextSession**: 上下文会话管理

### 1.2 现有功能

- 自动记忆收集（方法调用、输入输出、错误）
- 记忆搜索和检索
- 生命周期管理（过期清理、LRU/LFU策略）
- 会话上下文管理

## 2. 自定义Memory数据模型设计

### 2.1 自定义记忆类型枚举

```python
# custom_memory_models.py

class CustomMemoryType(Enum):
    """自定义记忆类型枚举"""
    CUSTOM_DATA = "custom_data"           # 自定义数据记忆
    CUSTOM_EVENT = "custom_event"         # 自定义事件记忆
    CUSTOM_KNOWLEDGE = "custom_knowledge" # 自定义知识记忆
    CUSTOM_TASK = "custom_task"           # 自定义任务记忆
    CUSTOM_RELATIONSHIP = "custom_relationship" # 自定义关系记忆
    CUSTOM_WORKFLOW = "custom_workflow"   # 自定义工作流记忆
    CUSTOM_CONFIG = "custom_config"       # 自定义配置记忆
    CUSTOM_LOG = "custom_log"             # 自定义日志记忆
```

### 2.2 自定义记忆模式定义

```python
@dataclass
class CustomMemorySchema:
    """自定义记忆模式定义"""
    name: str                             # 模式名称
    version: str = "1.0"                  # 模式版本
    description: str = ""                 # 模式描述
    fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # 字段定义
    required_fields: List[str] = field(default_factory=list)  # 必需字段
    validation_rules: Dict[str, Any] = field(default_factory=dict)  # 验证规则
    
    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """验证数据是否符合模式"""
        errors = []
        
        # 检查必需字段
        for field_name in self.required_fields:
            if field_name not in data:
                errors.append(f"缺少必需字段: {field_name}")
        
        # 检查字段类型
        for field_name, field_config in self.fields.items():
            if field_name in data:
                expected_type = field_config.get('type')
                if expected_type and not isinstance(data[field_name], expected_type):
                    errors.append(f"字段 {field_name} 类型错误，期望 {expected_type.__name__}")
        
        return len(errors) == 0, errors
```

### 2.3 自定义记忆模板

```python
@dataclass
class CustomMemoryTemplate:
    """自定义记忆模板"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    schema: CustomMemorySchema = field(default_factory=lambda: CustomMemorySchema(""))
    default_tags: List[str] = field(default_factory=list)
    default_keywords: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def create_memory(
        self,
        content: Dict[str, Any],
        source_agent_did: str,
        source_agent_name: str,
        title: Optional[str] = None,
        **kwargs
    ) -> MemoryEntry:
        """根据模板创建记忆条目"""
        
        # 验证内容
        is_valid, errors = self.schema.validate_data(content)
        if not is_valid:
            raise ValueError(f"数据验证失败: {', '.join(errors)}")
        
        # 创建元数据
        metadata = MemoryMetadata(
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            tags=self.default_tags + kwargs.get('tags', []),
            keywords=self.default_keywords + kwargs.get('keywords', []),
            **{k: v for k, v in kwargs.items() if k not in ['tags', 'keywords']}
        )
        
        # 创建记忆条目
        return MemoryEntry(
            memory_type=MemoryType.PATTERN,  # 使用PATTERN类型或扩展新的CUSTOM类型
            title=title or f"{self.name}_{uuid.uuid4().hex[:8]}",
            content={
                'template_id': self.id,
                'template_name': self.name,
                'schema_name': self.schema.name,
                'schema_version': self.schema.version,
                'custom_data': content
            },
            metadata=metadata
        )
```

## 3. 自定义Memory管理器扩展

### 3.1 CustomMemoryManager类设计

```python
# custom_memory_manager.py

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
        
        return template
    
    async def get_template(self, template_id: str) -> Optional[CustomMemoryTemplate]:
        """获取模板"""
        with self._lock:
            return self._templates.get(template_id)
    
    async def list_templates(self) -> List[CustomMemoryTemplate]:
        """列出所有模板"""
        with self._lock:
            return list(self._templates.values())
    
    async def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        with self._lock:
            template = self._templates.pop(template_id, None)
            if template:
                # 清理相关索引
                if template.name in self._template_index:
                    del self._template_index[template.name]
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
        **kwargs
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
            **kwargs
        )
        
        # 保存到基础管理器
        await self.base_manager.storage.save_memory(memory)
        
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
        if template_id:
            template = await self.get_template(template_id)
            if template and content:
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
        
        # 通用搜索
        else:
            # 使用基础管理器搜索
            all_memories = await self.base_manager.search_memories(**kwargs)
            
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
                memory = await self.create_custom_memory(
                    template_id=template_id,
                    content=content,
                    source_agent_did=source_agent_did,
                    source_agent_name=source_agent_name,
                    title=kwargs.get('title', f"Batch_{i+1}"),
                    **{k: v for k, v in kwargs.items() if k != 'title'}
                )
                memories.append(memory)
            except Exception as e:
                logger.error(f"批量创建自定义记忆失败 (索引 {i}): {e}")
        
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
        
        return deleted_count
    
    # ============ 工具方法 ============
    
    def _is_custom_memory(self, memory: MemoryEntry) -> bool:
        """检查是否为自定义记忆"""
        return (
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
```

## 4. MCP Tool接口封装

### 4.1 MCP Tool接口设计

```python
# custom_memory_mcp_tools.py

class CustomMemoryMCPTools:
    """自定义记忆MCP工具集"""
    
    def __init__(self, custom_manager: CustomMemoryManager):
        self.custom_manager = custom_manager
    
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
                default_tags=default_tags,
                default_keywords=default_keywords
            )
            
            return {
                "success": True,
                "template_id": template.id,
                "message": f"模板 '{name}' 创建成功"
            }
        
        except Exception as e:
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
        session_id: Optional[str] = None
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
                session_id=session_id
            )
            
            return {
                "success": True,
                "memory_id": memory.id,
                "message": f"自定义记忆 '{memory.title}' 创建成功"
            }
        
        except Exception as e:
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
            return {
                "success": False,
                "templates": [],
                "count": 0,
                "message": f"获取模板列表失败: {str(e)}"
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
            return {
                "success": False,
                "statistics": {},
                "message": f"获取统计信息失败: {str(e)}"
            }
```

### 4.2 MCP Server集成示例

```python
# custom_memory_mcp_server.py

from mcp.server import Server
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types
from typing import Any

# 创建MCP服务器
server = Server("custom-memory-manager")

# 初始化自定义记忆管理器
custom_manager = CustomMemoryManager()
mcp_tools = CustomMemoryMCPTools(custom_manager)

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """列出可用的工具"""
    return [
        types.Tool(
            name="create_memory_template",
            description="创建自定义记忆模板",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "模板名称"},
                    "schema_definition": {
                        "type": "object",
                        "description": "模式定义",
                        "properties": {
                            "fields": {"type": "object"},
                            "required_fields": {"type": "array", "items": {"type": "string"}},
                            "validation_rules": {"type": "object"}
                        }
                    },
                    "description": {"type": "string", "description": "模板描述"},
                    "default_tags": {"type": "array", "items": {"type": "string"}},
                    "default_keywords": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["name", "schema_definition"]
            }
        ),
        types.Tool(
            name="create_custom_memory",
            description="创建自定义记忆",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_id": {"type": "string", "description": "模板ID"},
                    "content": {"type": "object", "description": "记忆内容"},
                    "source_agent_did": {"type": "string", "description": "来源Agent DID"},
                    "source_agent_name": {"type": "string", "description": "来源Agent名称"},
                    "title": {"type": "string", "description": "记忆标题"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "session_id": {"type": "string", "description": "会话ID"}
                },
                "required": ["template_id", "content", "source_agent_did", "source_agent_name"]
            }
        ),
        types.Tool(
            name="get_custom_memory",
            description="获取自定义记忆",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string", "description": "记忆ID"}
                },
                "required": ["memory_id"]
            }
        ),
        types.Tool(
            name="update_custom_memory",
            description="更新自定义记忆",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string", "description": "记忆ID"},
                    "content": {"type": "object", "description": "新的记忆内容"},
                    "title": {"type": "string", "description": "新的标题"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "keywords": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["memory_id"]
            }
        ),
        types.Tool(
            name="delete_custom_memory",
            description="删除自定义记忆",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "string", "description": "记忆ID"}
                },
                "required": ["memory_id"]
            }
        ),
        types.Tool(
            name="search_custom_memories",
            description="搜索自定义记忆",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_name": {"type": "string", "description": "模板名称"},
                    "schema_name": {"type": "string", "description": "模式名称"},
                    "content_query": {"type": "object", "description": "内容查询条件"},
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "limit": {"type": "integer", "description": "结果限制", "default": 100}
                }
            }
        ),
        types.Tool(
            name="list_templates",
            description="列出所有模板",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        types.Tool(
            name="get_statistics",
            description="获取自定义记忆统计信息",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[types.TextContent]:
    """处理工具调用"""
    
    if arguments is None:
        arguments = {}
    
    try:
        if name == "create_memory_template":
            result = await mcp_tools.create_memory_template(**arguments)
        elif name == "create_custom_memory":
            result = await mcp_tools.create_custom_memory(**arguments)
        elif name == "get_custom_memory":
            result = await mcp_tools.get_custom_memory(**arguments)
        elif name == "update_custom_memory":
            result = await mcp_tools.update_custom_memory(**arguments)
        elif name == "delete_custom_memory":
            result = await mcp_tools.delete_custom_memory(**arguments)
        elif name == "search_custom_memories":
            result = await mcp_tools.search_custom_memories(**arguments)
        elif name == "list_templates":
            result = await mcp_tools.list_templates()
        elif name == "get_statistics":
            result = await mcp_tools.get_statistics()
        else:
            result = {"success": False, "message": f"未知工具: {name}"}
        
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    
    except Exception as e:
        error_result = {"success": False, "message": f"工具执行失败: {str(e)}"}
        return [types.TextContent(type="text", text=json.dumps(error_result, ensure_ascii=False, indent=2))]

async def main():
    # 使用stdio传输运行服务器
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="custom-memory-manager",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## 5. 使用示例

### 5.1 基础使用示例

```python
# 使用示例
async def example_usage():
    """自定义记忆使用示例"""
    
    # 1. 创建自定义记忆管理器
    custom_manager = CustomMemoryManager()
    
    # 2. 创建用户信息模式
    user_schema = CustomMemorySchema(
        name="user_profile",
        version="1.0",
        description="用户档案信息",
        fields={
            "name": {"type": str, "description": "用户姓名"},
            "age": {"type": int, "description": "用户年龄"},
            "preferences": {"type": dict, "description": "用户偏好"},
            "last_activity": {"type": str, "description": "最后活动时间"}
        },
        required_fields=["name", "age"]
    )
    
    # 3. 创建模板
    user_template = await custom_manager.create_template(
        name="user_profile_template",
        schema=user_schema,
        description="用户档案记忆模板",
        default_tags=["user", "profile"],
        default_keywords=["用户信息", "档案"]
    )
    
    # 4. 创建自定义记忆
    user_memory = await custom_manager.create_custom_memory(
        template_id=user_template.id,
        content={
            "name": "张三",
            "age": 25,
            "preferences": {
                "language": "中文",
                "theme": "dark"
            },
            "last_activity": "2024-01-15T10:30:00"
        },
        source_agent_did="did:anp:agent1",
        source_agent_name="UserAgent",
        title="用户张三的档案信息"
    )
    
    # 5. 查询自定义记忆
    retrieved_memory = await custom_manager.get_custom_memory(user_memory.id)
    print(f"获取到记忆: {retrieved_memory.title}")
    
    # 6. 更新自定义记忆
    await custom_manager.update_custom_memory(
        memory_id=user_memory.id,
        content={
            "name": "张三",
            "age": 26,  # 更新年龄
            "preferences": {
                "language": "中文",
                "theme": "light"  # 更新主题偏好
            },
            "last_activity": "2024-01-16T09:15:00"
        }
    )
    
    # 7. 搜索记忆
    memories = await custom_manager.search_custom_memories(
        template_name="user_profile_template",
        content_query={"age": 26}
    )
    print(f"搜索到 {len(memories)} 条记忆")
    
    # 8. 获取统计信息
    stats = await custom_manager.get_custom_memory_statistics()
    print(f"统计信息: {stats}")
```

### 5.2 MCP工具使用示例

```python
# MCP工具使用示例
async def mcp_usage_example():
    """MCP工具使用示例"""
    
    # 初始化MCP工具
    custom_manager = CustomMemoryManager()
    mcp_tools = CustomMemoryMCPTools(custom_manager)
    
    # 1. 创建任务模板
    result = await mcp_tools.create_memory_template(
        name="task_template",
        schema_definition={
            "description": "任务记忆模式",
            "fields": {
                "task_name": {"type": "str", "description": "任务名称"},
                "status": {"type": "str", "description": "任务状态"},
                "priority": {"type": "int", "description": "优先级"},
                "assignee": {"type": "str", "description": "负责人"},
                "due_date": {"type": "str", "description": "截止日期"},
                "description": {"type": "str", "description": "任务描述"}
            },
            "required_fields": ["task_name", "status", "priority"],
            "validation_rules": {
                "status": {"enum": ["待处理", "进行中", "已完成", "已取消"]},
                "priority": {"min": 1, "max": 5}
            }
        },
        description="项目任务管理模板",
        default_tags=["task", "project"],
        default_keywords=["任务", "项目管理"]
    )
    
    print(f"创建模板结果: {result}")
    
    if result["success"]:
        template_id = result["template_id"]
        
        # 2. 创建任务记忆
        task_result = await mcp_tools.create_custom_memory(
            template_id=template_id,
            content={
                "task_name": "实现自定义记忆功能",
                "status": "进行中",
                "priority": 3,
                "assignee": "开发团队",
                "due_date": "2024-02-01",
                "description": "为ANP SDK添加自定义记忆管理功能"
            },
            source_agent_did="did:anp:project_manager",
            source_agent_name="ProjectManager",
            title="开发任务-自定义记忆功能"
        )
        
        print(f"创建任务记忆结果: {task_result}")
        
        if task_result["success"]:
            memory_id = task_result["memory_id"]
            
            # 3. 更新任务状态
            update_result = await mcp_tools.update_custom_memory(
                memory_id=memory_id,
                content={
                    "task_name": "实现自定义记忆功能",
                    "status": "已完成",  # 更新状态
                    "priority": 3,
                    "assignee": "开发团队",
                    "due_date": "2024-02-01",
                    "description": "为ANP SDK添加自定义记忆管理功能 - 已完成开发和测试"
                }
            )
            
            print(f"更新任务结果: {update_result}")
            
            # 4. 搜索已完成的任务
            search_result = await mcp_tools.search_custom_memories(
                template_name="task_template",
                content_query={"status": "已完成"}
            )
            
            print(f"搜索结果: {search_result}")
```

## 6. 集成指导

### 6.1 集成到现有项目

1. **添加依赖文件**:
   - `custom_memory_models.py` - 自定义记忆数据模型
   - `custom_memory_manager.py` - 自定义记忆管理器
   - `custom_memory_mcp_tools.py` - MCP工具封装

2. **更新__init__.py**:
```python
# memory/__init__.py 中添加
from .custom_memory_models import (
    CustomMemoryType,
    CustomMemorySchema,
    CustomMemoryTemplate
)

from .custom_memory_manager import CustomMemoryManager

from .custom_memory_mcp_tools import (
    CustomMemoryMCPTools
)
```

3. **初始化自定义管理器**:
```python
# 在应用启动时初始化
from anp_runtime.local_service.memory import CustomMemoryManager

# 创建全局自定义记忆管理器
custom_memory_manager = CustomMemoryManager()
```

### 6.2 在装饰器中使用

```python
# 在local_methods_decorators.py中集成
from .memory.custom_memory_manager import CustomMemoryManager

@local_method(memory=memory_enabled(tags=["custom_operation"]))
async def create_user_profile(user_data: dict):
    """创建用户档案并保存为自定义记忆"""
    
    # 获取自定义记忆管理器
    custom_manager = CustomMemoryManager()
    
    # 查找用户档案模板
    templates = await custom_manager.list_templates()
    user_template = None
    for template in templates:
        if template.name == "user_profile_template":
            user_template = template
            break
    
    if user_template:
        # 创建用户档案记忆
        memory = await custom_manager.create_custom_memory(
            template_id=user_template.id,
            content=user_data,
            source_agent_did=get_current_agent_did(),
            source_agent_name=get_current_agent_name(),
            title=f"用户档案-{user_data.get('name', 'Unknown')}"
        )
        
        return {
            "success": True,
            "memory_id": memory.id,
            "message": "用户档案创建成功"
        }
    
    return {"success": False, "message": "未找到用户档案模板"}
```

## 7. 最佳实践

### 7.1 模式设计建议

1. **字段定义清晰**: 为每个字段提供明确的类型和描述
2. **验证规则完善**: 设置适当的验证规则确保数据质量
3. **版本管理**: 使用版本号管理模式演化
4. **标签和关键词**: 合理使用标签和关键词提高检索效率

### 7.2 性能优化

1. **缓存策略**: 合理使用内存缓存减少数据库访问
2. **批量操作**: 大量数据处理时使用批量操作
3. **索引优化**: 针对常用查询字段建立索引
4. **清理策略**: 定期清理过期和无用的自定义记忆

### 7.3 安全考虑

1. **权限控制**: 实现基于Agent DID的权限控制
2. **数据验证**: 严格验证输入数据防止注入攻击
3. **敏感信息**: 对敏感信息进行加密处理
4. **访问日志**: 记录关键操作的访问日志

## 8. 总结

本设计方案提供了一套完整的自定义memory管理系统，包括：

1. **灵活的数据模型**: 支持自定义模式和模板
2. **完整的CRUD接口**: 提供创建、读取、更新、删除操作
3. **强大的搜索功能**: 支持多维度搜索和过滤
4. **MCP工具集成**: 提供标准化的MCP工具接口
5. **批量操作支持**: 支持批量创建和删除操作
6. **统计和监控**: 提供详细的使用统计信息

开发者可以根据这个设计方案实现自定义memory功能，并通过MCP工具接口轻松集成到现有的应用中。