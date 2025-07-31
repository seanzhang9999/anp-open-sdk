"""
自定义记忆数据模型

提供开发者自定义记忆的数据结构和便捷创建方法
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Tuple
import json
import logging

from .memory_models import MemoryEntry, MemoryType, MemoryMetadata

logger = logging.getLogger(__name__)


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


@dataclass
class CustomMemorySchema:
    """自定义记忆模式定义"""
    name: str                             # 模式名称
    version: str = "1.0"                  # 模式版本
    description: str = ""                 # 模式描述
    fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # 字段定义
    required_fields: List[str] = field(default_factory=list)  # 必需字段
    validation_rules: Dict[str, Any] = field(default_factory=dict)  # 验证规则
    
    def validate_data(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
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
                if expected_type:
                    # 转换类型名到实际类型
                    if isinstance(expected_type, str):
                        type_mapping = {
                            'str': str,
                            'int': int,
                            'float': float,
                            'bool': bool,
                            'list': list,
                            'dict': dict
                        }
                        expected_type = type_mapping.get(expected_type, str)
                    
                    if not isinstance(data[field_name], expected_type):
                        errors.append(f"字段 {field_name} 类型错误，期望 {expected_type.__name__}")
                
                # 检查枚举值
                enum_values = field_config.get('enum')
                if enum_values and data[field_name] not in enum_values:
                    errors.append(f"字段 {field_name} 值 '{data[field_name]}' 不在允许的枚举值中: {enum_values}")
                
                # 检查数值范围
                if isinstance(data[field_name], (int, float)):
                    min_val = field_config.get('min')
                    max_val = field_config.get('max')
                    if min_val is not None and data[field_name] < min_val:
                        errors.append(f"字段 {field_name} 值 {data[field_name]} 小于最小值 {min_val}")
                    if max_val is not None and data[field_name] > max_val:
                        errors.append(f"字段 {field_name} 值 {data[field_name]} 大于最大值 {max_val}")
        
        return len(errors) == 0, errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'fields': self.fields,
            'required_fields': self.required_fields,
            'validation_rules': self.validation_rules
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomMemorySchema':
        """从字典创建模式"""
        return cls(
            name=data.get('name', ''),
            version=data.get('version', '1.0'),
            description=data.get('description', ''),
            fields=data.get('fields', {}),
            required_fields=data.get('required_fields', []),
            validation_rules=data.get('validation_rules', {})
        )


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
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.name:
            self.name = f"template_{self.id[:8]}"
    
    def create_memory(
        self,
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
        """根据模板创建记忆条目"""
        
        # 验证内容
        is_valid, errors = self.schema.validate_data(content)
        if not is_valid:
            raise ValueError(f"数据验证失败: {', '.join(errors)}")
        
        # 合并标签和关键词
        merged_tags = self.default_tags.copy()
        if tags:
            merged_tags.extend(tags)
        
        merged_keywords = self.default_keywords.copy()
        if keywords:
            merged_keywords.extend(keywords)
        
        # 创建元数据
        metadata = MemoryMetadata(
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            target_agent_did=target_agent_did,
            target_agent_name=target_agent_name,
            session_id=session_id,
            tags=merged_tags,
            keywords=merged_keywords,
            expiry_time=expiry_time
        )
        
        # 创建记忆条目
        return MemoryEntry(
            memory_type=MemoryType.PATTERN,  # 使用PATTERN类型来存储自定义记忆
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
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'schema': self.schema.to_dict(),
            'default_tags': self.default_tags,
            'default_keywords': self.default_keywords,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CustomMemoryTemplate':
        """从字典创建模板"""
        schema_data = data.get('schema', {})
        schema = CustomMemorySchema.from_dict(schema_data) if schema_data else CustomMemorySchema("")
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            description=data.get('description', ''),
            schema=schema,
            default_tags=data.get('default_tags', []),
            default_keywords=data.get('default_keywords', []),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        )


class CustomMemoryBuilder:
    """自定义记忆构建器 - 提供便捷的创建方法"""
    
    @staticmethod
    def create_user_profile_schema() -> CustomMemorySchema:
        """创建用户档案模式"""
        return CustomMemorySchema(
            name="user_profile",
            version="1.0",
            description="用户档案信息",
            fields={
                "name": {"type": "str", "description": "用户姓名"},
                "email": {"type": "str", "description": "用户邮箱"},
                "age": {"type": "int", "description": "用户年龄", "min": 0, "max": 120},
                "preferences": {"type": "dict", "description": "用户偏好"},
                "last_activity": {"type": "str", "description": "最后活动时间"}
            },
            required_fields=["name", "email"]
        )
    
    @staticmethod
    def create_task_management_schema() -> CustomMemorySchema:
        """创建任务管理模式"""
        return CustomMemorySchema(
            name="task_management",
            version="1.0",
            description="任务管理记忆模式",
            fields={
                "task_name": {"type": "str", "description": "任务名称"},
                "status": {"type": "str", "description": "任务状态", 
                          "enum": ["待处理", "进行中", "已完成", "已取消"]},
                "priority": {"type": "int", "description": "优先级(1-5)", "min": 1, "max": 5},
                "assignee": {"type": "str", "description": "负责人"},
                "due_date": {"type": "str", "description": "截止日期"},
                "progress": {"type": "float", "description": "完成进度(0-1)", "min": 0.0, "max": 1.0},
                "description": {"type": "str", "description": "任务描述"}
            },
            required_fields=["task_name", "status", "priority"]
        )
    
    @staticmethod
    def create_knowledge_base_schema() -> CustomMemorySchema:
        """创建知识库模式"""
        return CustomMemorySchema(
            name="knowledge_base",
            version="1.0",
            description="知识库记忆模式",
            fields={
                "title": {"type": "str", "description": "知识标题"},
                "category": {"type": "str", "description": "知识分类"},
                "content": {"type": "str", "description": "知识内容"},
                "source": {"type": "str", "description": "知识来源"},
                "confidence": {"type": "float", "description": "可信度(0-1)", "min": 0.0, "max": 1.0},
                "references": {"type": "list", "description": "参考链接"},
                "tags": {"type": "list", "description": "知识标签"}
            },
            required_fields=["title", "category", "content"]
        )
    
    @staticmethod
    def create_conversation_schema() -> CustomMemorySchema:
        """创建对话历史模式"""
        return CustomMemorySchema(
            name="conversation_history",
            version="1.0",
            description="对话历史记忆模式",
            fields={
                "session_id": {"type": "str", "description": "会话ID"},
                "participants": {"type": "list", "description": "参与者列表"},
                "messages": {"type": "list", "description": "消息列表"},
                "topic": {"type": "str", "description": "对话主题"},
                "sentiment": {"type": "str", "description": "情感倾向", 
                             "enum": ["positive", "negative", "neutral"]},
                "summary": {"type": "str", "description": "对话摘要"},
                "start_time": {"type": "str", "description": "开始时间"},
                "end_time": {"type": "str", "description": "结束时间"}
            },
            required_fields=["session_id", "participants", "messages"]
        )
    
    @staticmethod
    def create_event_log_schema() -> CustomMemorySchema:
        """创建事件日志模式"""
        return CustomMemorySchema(
            name="event_log",
            version="1.0",
            description="系统事件日志记忆模式",
            fields={
                "event_name": {"type": "str", "description": "事件名称"},
                "event_type": {"type": "str", "description": "事件类型"},
                "timestamp": {"type": "str", "description": "事件时间"},
                "level": {"type": "str", "description": "日志级别", 
                         "enum": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]},
                "data": {"type": "dict", "description": "事件数据"},
                "source": {"type": "str", "description": "事件来源"}
            },
            required_fields=["event_name", "event_type", "timestamp", "level"]
        )


# 预定义的模板工厂
class TemplateFactory:
    """模板工厂 - 快速创建常用模板"""
    
    @staticmethod
    def create_user_profile_template() -> CustomMemoryTemplate:
        """创建用户档案模板"""
        return CustomMemoryTemplate(
            name="user_profile_template",
            description="用户档案记忆模板",
            schema=CustomMemoryBuilder.create_user_profile_schema(),
            default_tags=["user", "profile"],
            default_keywords=["用户信息", "档案"]
        )
    
    @staticmethod
    def create_task_template() -> CustomMemoryTemplate:
        """创建任务管理模板"""
        return CustomMemoryTemplate(
            name="task_template",
            description="任务管理记忆模板",
            schema=CustomMemoryBuilder.create_task_management_schema(),
            default_tags=["task", "project"],
            default_keywords=["任务", "项目管理"]
        )
    
    @staticmethod
    def create_knowledge_template() -> CustomMemoryTemplate:
        """创建知识库模板"""
        return CustomMemoryTemplate(
            name="knowledge_template",
            description="知识库记忆模板",
            schema=CustomMemoryBuilder.create_knowledge_base_schema(),
            default_tags=["knowledge", "reference"],
            default_keywords=["知识", "参考资料"]
        )
    
    @staticmethod
    def create_conversation_template() -> CustomMemoryTemplate:
        """创建对话历史模板"""
        return CustomMemoryTemplate(
            name="conversation_template",
            description="对话历史记忆模板",
            schema=CustomMemoryBuilder.create_conversation_schema(),
            default_tags=["conversation", "history"],
            default_keywords=["对话", "历史记录"]
        )
    
    @staticmethod
    def create_event_log_template() -> CustomMemoryTemplate:
        """创建事件日志模板"""
        return CustomMemoryTemplate(
            name="event_log_template",
            description="系统事件日志记忆模板",
            schema=CustomMemoryBuilder.create_event_log_schema(),
            default_tags=["event", "log", "system"],
            default_keywords=["事件", "日志", "系统"]
        )