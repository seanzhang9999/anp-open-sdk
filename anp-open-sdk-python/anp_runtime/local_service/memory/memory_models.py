"""
记忆功能数据模型

定义记忆条目、会话上下文等核心数据结构
"""

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import json


class MemoryType(Enum):
    """记忆类型枚举"""
    METHOD_CALL = "method_call"         # 方法调用记忆
    INPUT_OUTPUT = "input_output"       # 输入输出记忆  
    USER_PREFERENCE = "user_preference" # 用户偏好记忆
    CONTEXT = "context"                 # 上下文记忆
    ERROR = "error"                     # 错误记忆
    PATTERN = "pattern"                 # 模式记忆


@dataclass
class MemoryMetadata:
    """记忆元数据"""
    source_agent_did: str                    # 来源Agent DID
    source_agent_name: str                   # 来源Agent名称
    target_agent_did: Optional[str] = None   # 目标Agent DID（如果有）
    target_agent_name: Optional[str] = None  # 目标Agent名称（如果有）
    session_id: Optional[str] = None         # 会话ID
    tags: List[str] = field(default_factory=list)  # 标签
    keywords: List[str] = field(default_factory=list)  # 关键词
    relevance_score: float = 1.0             # 相关度分数
    access_count: int = 0                    # 访问次数
    last_accessed: Optional[datetime] = None # 最后访问时间
    expiry_time: Optional[datetime] = None   # 过期时间


@dataclass
class MemoryEntry:
    """记忆条目"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    memory_type: MemoryType = MemoryType.METHOD_CALL
    title: str = ""
    content: Dict[str, Any] = field(default_factory=dict)
    metadata: MemoryMetadata = field(default_factory=lambda: MemoryMetadata("", ""))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.title:
            self.title = f"{self.memory_type.value}_{self.id[:8]}"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'memory_type': self.memory_type.value,
            'title': self.title,
            'content': self.content,
            'metadata': {
                'source_agent_did': self.metadata.source_agent_did,
                'source_agent_name': self.metadata.source_agent_name,
                'target_agent_did': self.metadata.target_agent_did,
                'target_agent_name': self.metadata.target_agent_name,
                'session_id': self.metadata.session_id,
                'tags': self.metadata.tags,
                'keywords': self.metadata.keywords,
                'relevance_score': self.metadata.relevance_score,
                'access_count': self.metadata.access_count,
                'last_accessed': self.metadata.last_accessed.isoformat() if self.metadata.last_accessed else None,
                'expiry_time': self.metadata.expiry_time.isoformat() if self.metadata.expiry_time else None
            },
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """从字典创建记忆条目"""
        metadata_data = data.get('metadata', {})
        metadata = MemoryMetadata(
            source_agent_did=metadata_data.get('source_agent_did', ''),
            source_agent_name=metadata_data.get('source_agent_name', ''),
            target_agent_did=metadata_data.get('target_agent_did'),
            target_agent_name=metadata_data.get('target_agent_name'),
            session_id=metadata_data.get('session_id'),
            tags=metadata_data.get('tags', []),
            keywords=metadata_data.get('keywords', []),
            relevance_score=metadata_data.get('relevance_score', 1.0),
            access_count=metadata_data.get('access_count', 0),
            last_accessed=datetime.fromisoformat(metadata_data['last_accessed']) if metadata_data.get('last_accessed') else None,
            expiry_time=datetime.fromisoformat(metadata_data['expiry_time']) if metadata_data.get('expiry_time') else None
        )
        
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            memory_type=MemoryType(data.get('memory_type', MemoryType.METHOD_CALL.value)),
            title=data.get('title', ''),
            content=data.get('content', {}),
            metadata=metadata,
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now()
        )
    
    def update_access(self):
        """更新访问信息"""
        self.metadata.access_count += 1
        self.metadata.last_accessed = datetime.now()
        self.updated_at = datetime.now()
    
    def is_expired(self) -> bool:
        """检查记忆是否过期"""
        if self.metadata.expiry_time is None:
            return False
        return datetime.now() > self.metadata.expiry_time
    
    def add_tag(self, tag: str):
        """添加标签"""
        if tag not in self.metadata.tags:
            self.metadata.tags.append(tag)
            self.updated_at = datetime.now()
    
    def add_keyword(self, keyword: str):
        """添加关键词"""
        if keyword not in self.metadata.keywords:
            self.metadata.keywords.append(keyword)
            self.updated_at = datetime.now()


@dataclass
class ContextSession:
    """上下文会话"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    participants: List[str] = field(default_factory=list)  # Agent DID列表
    memory_entries: List[str] = field(default_factory=list)  # 记忆条目ID列表
    context_data: Dict[str, Any] = field(default_factory=dict)  # 会话上下文数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.name:
            self.name = f"session_{self.id[:8]}"
    
    def add_participant(self, agent_did: str):
        """添加参与者"""
        if agent_did not in self.participants:
            self.participants.append(agent_did)
            self.updated_at = datetime.now()
    
    def remove_participant(self, agent_did: str):
        """移除参与者"""
        if agent_did in self.participants:
            self.participants.remove(agent_did)
            self.updated_at = datetime.now()
    
    def add_memory(self, memory_id: str):
        """添加记忆条目"""
        if memory_id not in self.memory_entries:
            self.memory_entries.append(memory_id)
            self.updated_at = datetime.now()
    
    def remove_memory(self, memory_id: str):
        """移除记忆条目"""
        if memory_id in self.memory_entries:
            self.memory_entries.remove(memory_id)
            self.updated_at = datetime.now()
    
    def update_context(self, key: str, value: Any):
        """更新上下文数据"""
        self.context_data[key] = value
        self.updated_at = datetime.now()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文数据"""
        return self.context_data.get(key, default)
    
    def close(self):
        """关闭会话"""
        self.is_active = False
        self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'participants': self.participants,
            'memory_entries': self.memory_entries,
            'context_data': self.context_data,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_active': self.is_active
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ContextSession':
        """从字典创建上下文会话"""
        return cls(
            id=data.get('id', str(uuid.uuid4())),
            name=data.get('name', ''),
            description=data.get('description', ''),
            participants=data.get('participants', []),
            memory_entries=data.get('memory_entries', []),
            context_data=data.get('context_data', {}),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
            is_active=data.get('is_active', True)
        )


class MethodCallMemory:
    """方法调用记忆的便捷创建类"""
    
    @staticmethod
    def create(
        method_name: str,
        method_key: str,
        input_args: List[Any],
        input_kwargs: Dict[str, Any],
        output: Any,
        execution_time: float,
        source_agent_did: str,
        source_agent_name: str,
        target_agent_did: Optional[str] = None,
        target_agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None
    ) -> MemoryEntry:
        """创建方法调用记忆"""
        
        # 提取关键词
        auto_keywords = [method_name, method_key]
        if keywords:
            auto_keywords.extend(keywords)
        
        # 提取标签
        auto_tags = ["method_call"]
        if tags:
            auto_tags.extend(tags)
        
        metadata = MemoryMetadata(
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            target_agent_did=target_agent_did,
            target_agent_name=target_agent_name,
            session_id=session_id,
            tags=auto_tags,
            keywords=auto_keywords
        )
        
        content = {
            'method_name': method_name,
            'method_key': method_key,
            'input': {
                'args': input_args,
                'kwargs': input_kwargs
            },
            'output': output,
            'execution_time': execution_time,
            'success': True
        }
        
        return MemoryEntry(
            memory_type=MemoryType.METHOD_CALL,
            title=f"调用{method_name}",
            content=content,
            metadata=metadata
        )
    
    @staticmethod
    def create_error(
        method_name: str,
        method_key: str,
        input_args: List[Any],
        input_kwargs: Dict[str, Any],
        error: Exception,
        execution_time: float,
        source_agent_did: str,
        source_agent_name: str,
        target_agent_did: Optional[str] = None,
        target_agent_name: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> MemoryEntry:
        """创建方法调用错误记忆"""
        
        metadata = MemoryMetadata(
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            target_agent_did=target_agent_did,
            target_agent_name=target_agent_name,
            session_id=session_id,
            tags=["method_call", "error"],
            keywords=[method_name, method_key, "error", type(error).__name__]
        )
        
        content = {
            'method_name': method_name,
            'method_key': method_key,
            'input': {
                'args': input_args,
                'kwargs': input_kwargs
            },
            'error': {
                'type': type(error).__name__,
                'message': str(error),
                'traceback': None  # 可以根据需要添加traceback
            },
            'execution_time': execution_time,
            'success': False
        }
        
        return MemoryEntry(
            memory_type=MemoryType.ERROR,
            title=f"调用{method_name}失败",
            content=content,
            metadata=metadata
        )