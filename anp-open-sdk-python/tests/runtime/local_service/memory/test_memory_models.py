"""
记忆数据模型测试

测试 MemoryEntry、ContextSession、MemoryMetadata 等核心数据结构
"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from anp_runtime.local_service.memory.memory_models import (
    MemoryEntry,
    ContextSession,
    MemoryMetadata,
    MemoryType,
    MethodCallMemory
)


class TestMemoryType:
    """测试记忆类型枚举"""
    
    def test_memory_type_values(self):
        """测试记忆类型的值"""
        assert MemoryType.METHOD_CALL.value == "method_call"
        assert MemoryType.INPUT_OUTPUT.value == "input_output"
        assert MemoryType.USER_PREFERENCE.value == "user_preference"
        assert MemoryType.CONTEXT.value == "context"
        assert MemoryType.ERROR.value == "error"
        assert MemoryType.PATTERN.value == "pattern"
    
    def test_memory_type_enum_behavior(self):
        """测试枚举行为"""
        # 测试比较
        assert MemoryType.METHOD_CALL == MemoryType.METHOD_CALL
        assert MemoryType.METHOD_CALL != MemoryType.ERROR
        
        # 测试in操作
        all_types = list(MemoryType)
        assert MemoryType.METHOD_CALL in all_types
        assert len(all_types) == 6


class TestMemoryMetadata:
    """测试记忆元数据"""
    
    def test_metadata_creation(self):
        """测试元数据创建"""
        metadata = MemoryMetadata(
            source_agent_did="did:example:alice",
            source_agent_name="Alice Agent"
        )
        
        assert metadata.source_agent_did == "did:example:alice"
        assert metadata.source_agent_name == "Alice Agent"
        assert metadata.target_agent_did is None
        assert metadata.target_agent_name is None
        assert metadata.session_id is None
        assert metadata.tags == []
        assert metadata.keywords == []
        assert metadata.relevance_score == 1.0
        assert metadata.access_count == 0
        assert metadata.last_accessed is None
        assert metadata.expiry_time is None
    
    def test_metadata_with_all_fields(self):
        """测试包含所有字段的元数据"""
        now = datetime.now()
        expiry = now + timedelta(hours=24)
        
        metadata = MemoryMetadata(
            source_agent_did="did:example:alice",
            source_agent_name="Alice Agent",
            target_agent_did="did:example:bob",
            target_agent_name="Bob Agent",
            session_id="session-123",
            tags=["tag1", "tag2"],
            keywords=["keyword1", "keyword2"],
            relevance_score=0.8,
            access_count=5,
            last_accessed=now,
            expiry_time=expiry
        )
        
        assert metadata.source_agent_did == "did:example:alice"
        assert metadata.source_agent_name == "Alice Agent"
        assert metadata.target_agent_did == "did:example:bob"
        assert metadata.target_agent_name == "Bob Agent"
        assert metadata.session_id == "session-123"
        assert metadata.tags == ["tag1", "tag2"]
        assert metadata.keywords == ["keyword1", "keyword2"]
        assert metadata.relevance_score == 0.8
        assert metadata.access_count == 5
        assert metadata.last_accessed == now
        assert metadata.expiry_time == expiry


class TestMemoryEntry:
    """测试记忆条目"""
    
    def test_memory_entry_creation(self):
        """测试记忆条目创建"""
        metadata = MemoryMetadata("did:example:alice", "Alice Agent")
        
        memory = MemoryEntry(
            memory_type=MemoryType.METHOD_CALL,
            title="Test Memory",
            content={"test": "data"},
            metadata=metadata
        )
        
        assert memory.memory_type == MemoryType.METHOD_CALL
        assert memory.title == "Test Memory"
        assert memory.content == {"test": "data"}
        assert memory.metadata == metadata
        assert isinstance(memory.id, str)
        assert len(memory.id) == 36  # UUID长度
        assert isinstance(memory.created_at, datetime)
        assert isinstance(memory.updated_at, datetime)
    
    def test_memory_entry_default_values(self):
        """测试记忆条目默认值"""
        memory = MemoryEntry()
        
        assert memory.memory_type == MemoryType.METHOD_CALL
        assert memory.title.startswith("method_call_")
        assert memory.content == {}
        assert isinstance(memory.metadata, MemoryMetadata)
        assert memory.metadata.source_agent_did == ""
        assert memory.metadata.source_agent_name == ""
    
    def test_memory_entry_post_init(self):
        """测试初始化后处理"""
        memory = MemoryEntry(memory_type=MemoryType.ERROR)
        
        # 测试默认标题生成
        assert memory.title.startswith("error_")
        assert memory.id[:8] in memory.title
    
    def test_memory_entry_to_dict(self):
        """测试记忆条目序列化"""
        now = datetime.now()
        metadata = MemoryMetadata(
            source_agent_did="did:example:alice",
            source_agent_name="Alice Agent",
            tags=["tag1"],
            keywords=["keyword1"],
            access_count=3,
            last_accessed=now
        )
        
        memory = MemoryEntry(
            id="test-id",
            memory_type=MemoryType.METHOD_CALL,
            title="Test Memory",
            content={"method": "test_method", "result": "success"},
            metadata=metadata,
            created_at=now,
            updated_at=now
        )
        
        data = memory.to_dict()
        
        assert data["id"] == "test-id"
        assert data["memory_type"] == "method_call"
        assert data["title"] == "Test Memory"
        assert data["content"] == {"method": "test_method", "result": "success"}
        assert data["created_at"] == now.isoformat()
        assert data["updated_at"] == now.isoformat()
        
        # 测试元数据序列化
        metadata_data = data["metadata"]
        assert metadata_data["source_agent_did"] == "did:example:alice"
        assert metadata_data["source_agent_name"] == "Alice Agent"
        assert metadata_data["tags"] == ["tag1"]
        assert metadata_data["keywords"] == ["keyword1"]
        assert metadata_data["access_count"] == 3
        assert metadata_data["last_accessed"] == now.isoformat()
    
    def test_memory_entry_from_dict(self):
        """测试记忆条目反序列化"""
        now = datetime.now()
        data = {
            "id": "test-id",
            "memory_type": "method_call",
            "title": "Test Memory",
            "content": {"method": "test_method"},
            "metadata": {
                "source_agent_did": "did:example:alice",
                "source_agent_name": "Alice Agent",
                "target_agent_did": "did:example:bob",
                "target_agent_name": "Bob Agent",
                "session_id": "session-123",
                "tags": ["tag1", "tag2"],
                "keywords": ["keyword1"],
                "relevance_score": 0.9,
                "access_count": 2,
                "last_accessed": now.isoformat(),
                "expiry_time": (now + timedelta(hours=1)).isoformat()
            },
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        memory = MemoryEntry.from_dict(data)
        
        assert memory.id == "test-id"
        assert memory.memory_type == MemoryType.METHOD_CALL
        assert memory.title == "Test Memory"
        assert memory.content == {"method": "test_method"}
        assert memory.created_at == now
        assert memory.updated_at == now
        
        # 测试元数据反序列化
        metadata = memory.metadata
        assert metadata.source_agent_did == "did:example:alice"
        assert metadata.source_agent_name == "Alice Agent"
        assert metadata.target_agent_did == "did:example:bob"
        assert metadata.target_agent_name == "Bob Agent"
        assert metadata.session_id == "session-123"
        assert metadata.tags == ["tag1", "tag2"]
        assert metadata.keywords == ["keyword1"]
        assert metadata.relevance_score == 0.9
        assert metadata.access_count == 2
        assert metadata.last_accessed == now
        assert metadata.expiry_time == now + timedelta(hours=1)
    
    def test_memory_entry_from_dict_with_defaults(self):
        """测试使用默认值的反序列化"""
        data = {
            "memory_type": "error",
            "title": "Error Memory"
        }
        
        memory = MemoryEntry.from_dict(data)
        
        assert memory.memory_type == MemoryType.ERROR
        assert memory.title == "Error Memory"
        assert isinstance(memory.id, str)
        assert memory.content == {}
        assert isinstance(memory.metadata, MemoryMetadata)
        assert isinstance(memory.created_at, datetime)
        assert isinstance(memory.updated_at, datetime)
    
    def test_memory_entry_update_access(self):
        """测试更新访问信息"""
        memory = MemoryEntry()
        initial_access_count = memory.metadata.access_count
        initial_updated_at = memory.updated_at
        
        # 稍微等待以确保时间差异
        import time
        time.sleep(0.01)
        
        memory.update_access()
        
        assert memory.metadata.access_count == initial_access_count + 1
        assert memory.metadata.last_accessed is not None
        assert memory.updated_at > initial_updated_at
    
    def test_memory_entry_is_expired(self):
        """测试过期检查"""
        # 测试未设置过期时间
        memory = MemoryEntry()
        assert not memory.is_expired()
        
        # 测试未过期
        memory.metadata.expiry_time = datetime.now() + timedelta(hours=1)
        assert not memory.is_expired()
        
        # 测试已过期
        memory.metadata.expiry_time = datetime.now() - timedelta(hours=1)
        assert memory.is_expired()
    
    def test_memory_entry_add_tag(self):
        """测试添加标签"""
        memory = MemoryEntry()
        initial_updated_at = memory.updated_at
        
        import time
        time.sleep(0.01)
        
        memory.add_tag("new_tag")
        
        assert "new_tag" in memory.metadata.tags
        assert memory.updated_at > initial_updated_at
        
        # 测试重复添加
        memory.add_tag("new_tag")
        assert memory.metadata.tags.count("new_tag") == 1
    
    def test_memory_entry_add_keyword(self):
        """测试添加关键词"""
        memory = MemoryEntry()
        initial_updated_at = memory.updated_at
        
        import time
        time.sleep(0.01)
        
        memory.add_keyword("new_keyword")
        
        assert "new_keyword" in memory.metadata.keywords
        assert memory.updated_at > initial_updated_at
        
        # 测试重复添加
        memory.add_keyword("new_keyword")
        assert memory.metadata.keywords.count("new_keyword") == 1


class TestContextSession:
    """测试上下文会话"""
    
    def test_context_session_creation(self):
        """测试会话创建"""
        session = ContextSession(
            name="Test Session",
            description="A test session",
            participants=["alice", "bob"],
            context_data={"key": "value"}
        )
        
        assert session.name == "Test Session"
        assert session.description == "A test session"
        assert session.participants == ["alice", "bob"]
        assert session.memory_entries == []
        assert session.context_data == {"key": "value"}
        assert isinstance(session.id, str)
        assert len(session.id) == 36  # UUID长度
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
        assert session.is_active
    
    def test_context_session_default_values(self):
        """测试会话默认值"""
        session = ContextSession()
        
        assert session.name.startswith("session_")
        assert session.description == ""
        assert session.participants == []
        assert session.memory_entries == []
        assert session.context_data == {}
        assert session.is_active
    
    def test_context_session_post_init(self):
        """测试初始化后处理"""
        session = ContextSession()
        
        # 测试默认名称生成
        assert session.name.startswith("session_")
        assert session.id[:8] in session.name
    
    def test_add_participant(self):
        """测试添加参与者"""
        session = ContextSession()
        initial_updated_at = session.updated_at
        
        import time
        time.sleep(0.01)
        
        session.add_participant("alice")
        
        assert "alice" in session.participants
        assert session.updated_at > initial_updated_at
        
        # 测试重复添加
        session.add_participant("alice")
        assert session.participants.count("alice") == 1
    
    def test_remove_participant(self):
        """测试移除参与者"""
        session = ContextSession(participants=["alice", "bob"])
        initial_updated_at = session.updated_at
        
        import time
        time.sleep(0.01)
        
        session.remove_participant("alice")
        
        assert "alice" not in session.participants
        assert "bob" in session.participants
        assert session.updated_at > initial_updated_at
    
    def test_add_memory(self):
        """测试添加记忆条目"""
        session = ContextSession()
        initial_updated_at = session.updated_at
        
        import time
        time.sleep(0.01)
        
        memory_id = "memory-123"
        session.add_memory(memory_id)
        
        assert memory_id in session.memory_entries
        assert session.updated_at > initial_updated_at
        
        # 测试重复添加
        session.add_memory(memory_id)
        assert session.memory_entries.count(memory_id) == 1
    
    def test_remove_memory(self):
        """测试移除记忆条目"""
        memory_id1 = "memory-123"
        memory_id2 = "memory-456"
        session = ContextSession(memory_entries=[memory_id1, memory_id2])
        initial_updated_at = session.updated_at
        
        import time
        time.sleep(0.01)
        
        session.remove_memory(memory_id1)
        
        assert memory_id1 not in session.memory_entries
        assert memory_id2 in session.memory_entries
        assert session.updated_at > initial_updated_at
    
    def test_update_context(self):
        """测试更新上下文数据"""
        session = ContextSession()
        initial_updated_at = session.updated_at
        
        import time
        time.sleep(0.01)
        
        session.update_context("key1", "value1")
        
        assert session.context_data["key1"] == "value1"
        assert session.updated_at > initial_updated_at
    
    def test_get_context(self):
        """测试获取上下文数据"""
        session = ContextSession(context_data={"key1": "value1"})
        
        assert session.get_context("key1") == "value1"
        assert session.get_context("nonexistent") is None
        assert session.get_context("nonexistent", "default") == "default"
    
    def test_close_session(self):
        """测试关闭会话"""
        session = ContextSession()
        initial_updated_at = session.updated_at
        
        import time
        time.sleep(0.01)
        
        session.close()
        
        assert not session.is_active
        assert session.updated_at > initial_updated_at
    
    def test_context_session_to_dict(self):
        """测试会话序列化"""
        now = datetime.now()
        session = ContextSession(
            id="session-123",
            name="Test Session",
            description="Test Description",
            participants=["alice", "bob"],
            memory_entries=["mem1", "mem2"],
            context_data={"key": "value"},
            created_at=now,
            updated_at=now,
            is_active=False
        )
        
        data = session.to_dict()
        
        assert data["id"] == "session-123"
        assert data["name"] == "Test Session"
        assert data["description"] == "Test Description"
        assert data["participants"] == ["alice", "bob"]
        assert data["memory_entries"] == ["mem1", "mem2"]
        assert data["context_data"] == {"key": "value"}
        assert data["created_at"] == now.isoformat()
        assert data["updated_at"] == now.isoformat()
        assert data["is_active"] == False
    
    def test_context_session_from_dict(self):
        """测试会话反序列化"""
        now = datetime.now()
        data = {
            "id": "session-123",
            "name": "Test Session",
            "description": "Test Description",
            "participants": ["alice", "bob"],
            "memory_entries": ["mem1", "mem2"],
            "context_data": {"key": "value"},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "is_active": False
        }
        
        session = ContextSession.from_dict(data)
        
        assert session.id == "session-123"
        assert session.name == "Test Session"
        assert session.description == "Test Description"
        assert session.participants == ["alice", "bob"]
        assert session.memory_entries == ["mem1", "mem2"]
        assert session.context_data == {"key": "value"}
        assert session.created_at == now
        assert session.updated_at == now
        assert session.is_active == False
    
    def test_context_session_from_dict_with_defaults(self):
        """测试使用默认值的会话反序列化"""
        data = {
            "name": "Simple Session"
        }
        
        session = ContextSession.from_dict(data)
        
        assert session.name == "Simple Session"
        assert isinstance(session.id, str)
        assert session.description == ""
        assert session.participants == []
        assert session.memory_entries == []
        assert session.context_data == {}
        assert isinstance(session.created_at, datetime)
        assert isinstance(session.updated_at, datetime)
        assert session.is_active == True


class TestMethodCallMemory:
    """测试方法调用记忆便捷创建类"""
    
    def test_create_method_call_memory(self):
        """测试创建方法调用记忆"""
        memory = MethodCallMemory.create(
            method_name="test_method",
            method_key="module::test_method",
            input_args=[1, 2, 3],
            input_kwargs={"param": "value"},
            output={"result": "success"},
            execution_time=0.5,
            source_agent_did="did:example:alice",
            source_agent_name="Alice Agent",
            target_agent_did="did:example:bob",
            target_agent_name="Bob Agent",
            session_id="session-123",
            tags=["custom_tag"],
            keywords=["custom_keyword"]
        )
        
        assert memory.memory_type == MemoryType.METHOD_CALL
        assert memory.title == "调用test_method"
        
        # 测试内容
        content = memory.content
        assert content["method_name"] == "test_method"
        assert content["method_key"] == "module::test_method"
        assert content["input"]["args"] == [1, 2, 3]
        assert content["input"]["kwargs"] == {"param": "value"}
        assert content["output"] == {"result": "success"}
        assert content["execution_time"] == 0.5
        assert content["success"] == True
        
        # 测试元数据
        metadata = memory.metadata
        assert metadata.source_agent_did == "did:example:alice"
        assert metadata.source_agent_name == "Alice Agent"
        assert metadata.target_agent_did == "did:example:bob"
        assert metadata.target_agent_name == "Bob Agent"
        assert metadata.session_id == "session-123"
        assert "method_call" in metadata.tags
        assert "custom_tag" in metadata.tags
        assert "test_method" in metadata.keywords
        assert "module::test_method" in metadata.keywords
        assert "custom_keyword" in metadata.keywords
    
    def test_create_error_memory(self):
        """测试创建错误记忆"""
        error = ValueError("Test error message")
        
        memory = MethodCallMemory.create_error(
            method_name="failing_method",
            method_key="module::failing_method",
            input_args=[1, 2],
            input_kwargs={"param": "bad_value"},
            error=error,
            execution_time=0.1,
            source_agent_did="did:example:alice",
            source_agent_name="Alice Agent",
            session_id="session-456"
        )
        
        assert memory.memory_type == MemoryType.ERROR
        assert memory.title == "调用failing_method失败"
        
        # 测试内容
        content = memory.content
        assert content["method_name"] == "failing_method"
        assert content["method_key"] == "module::failing_method"
        assert content["input"]["args"] == [1, 2]
        assert content["input"]["kwargs"] == {"param": "bad_value"}
        assert content["error"]["type"] == "ValueError"
        assert content["error"]["message"] == "Test error message"
        assert content["error"]["traceback"] is None  # 默认不包含traceback
        assert content["execution_time"] == 0.1
        assert content["success"] == False
        
        # 测试元数据
        metadata = memory.metadata
        assert metadata.source_agent_did == "did:example:alice"
        assert metadata.source_agent_name == "Alice Agent"
        assert metadata.session_id == "session-456"
        assert "method_call" in metadata.tags
        assert "error" in metadata.tags
        assert "failing_method" in metadata.keywords
        assert "module::failing_method" in metadata.keywords
        assert "error" in metadata.keywords
        assert "ValueError" in metadata.keywords
    
    def test_create_with_minimal_parameters(self):
        """测试使用最少参数创建记忆"""
        memory = MethodCallMemory.create(
            method_name="simple_method",
            method_key="simple_method",
            input_args=[],
            input_kwargs={},
            output=None,
            execution_time=0.01,
            source_agent_did="did:example:agent",
            source_agent_name="Agent"
        )
        
        assert memory.memory_type == MemoryType.METHOD_CALL
        assert memory.title == "调用simple_method"
        assert memory.metadata.target_agent_did is None
        assert memory.metadata.target_agent_name is None
        assert memory.metadata.session_id is None
        assert "method_call" in memory.metadata.tags
        assert "simple_method" in memory.metadata.keywords


class TestMemoryModelsIntegration:
    """测试记忆模型集成场景"""
    
    def test_memory_entry_roundtrip_serialization(self):
        """测试记忆条目完整序列化往返"""
        # 创建复杂的记忆条目
        now = datetime.now()
        expiry = now + timedelta(hours=24)
        
        metadata = MemoryMetadata(
            source_agent_did="did:example:alice",
            source_agent_name="Alice Agent",
            target_agent_did="did:example:bob",
            target_agent_name="Bob Agent",
            session_id="session-123",
            tags=["important", "test"],
            keywords=["method", "call", "test"],
            relevance_score=0.85,
            access_count=10,
            last_accessed=now,
            expiry_time=expiry
        )
        
        original_memory = MemoryEntry(
            memory_type=MemoryType.METHOD_CALL,
            title="Complex Memory Test",
            content={
                "method_name": "complex_method",
                "input": {"args": [1, 2, 3], "kwargs": {"param": "value"}},
                "output": {"result": "success", "data": [1, 2, 3]},
                "execution_time": 1.23
            },
            metadata=metadata
        )
        
        # 序列化
        data = original_memory.to_dict()
        
        # 反序列化
        restored_memory = MemoryEntry.from_dict(data)
        
        # 验证数据一致性
        assert restored_memory.id == original_memory.id
        assert restored_memory.memory_type == original_memory.memory_type
        assert restored_memory.title == original_memory.title
        assert restored_memory.content == original_memory.content
        assert restored_memory.created_at == original_memory.created_at
        assert restored_memory.updated_at == original_memory.updated_at
        
        # 验证元数据一致性
        restored_metadata = restored_memory.metadata
        original_metadata = original_memory.metadata
        assert restored_metadata.source_agent_did == original_metadata.source_agent_did
        assert restored_metadata.source_agent_name == original_metadata.source_agent_name
        assert restored_metadata.target_agent_did == original_metadata.target_agent_did
        assert restored_metadata.target_agent_name == original_metadata.target_agent_name
        assert restored_metadata.session_id == original_metadata.session_id
        assert restored_metadata.tags == original_metadata.tags
        assert restored_metadata.keywords == original_metadata.keywords
        assert restored_metadata.relevance_score == original_metadata.relevance_score
        assert restored_metadata.access_count == original_metadata.access_count
        assert restored_metadata.last_accessed == original_metadata.last_accessed
        assert restored_metadata.expiry_time == original_metadata.expiry_time
    
    def test_context_session_roundtrip_serialization(self):
        """测试上下文会话完整序列化往返"""
        now = datetime.now()
        
        original_session = ContextSession(
            name="Integration Test Session",
            description="A session for integration testing",
            participants=["alice", "bob", "charlie"],
            memory_entries=["mem1", "mem2", "mem3"],
            context_data={
                "project": "ANP SDK",
                "version": "1.0.0",
                "settings": {"debug": True, "timeout": 30}
            },
            created_at=now,
            updated_at=now,
            is_active=True
        )
        
        # 序列化
        data = original_session.to_dict()
        
        # 反序列化
        restored_session = ContextSession.from_dict(data)
        
        # 验证数据一致性
        assert restored_session.id == original_session.id
        assert restored_session.name == original_session.name
        assert restored_session.description == original_session.description
        assert restored_session.participants == original_session.participants
        assert restored_session.memory_entries == original_session.memory_entries
        assert restored_session.context_data == original_session.context_data
        assert restored_session.created_at == original_session.created_at
        assert restored_session.updated_at == original_session.updated_at
        assert restored_session.is_active == original_session.is_active
    
    def test_method_call_memory_creation_with_session(self):
        """测试在会话上下文中创建方法调用记忆"""
        # 首先创建一个会话
        session = ContextSession(
            name="Method Testing Session",
            participants=["did:example:alice"]
        )
        
        # 创建方法调用记忆，关联到会话
        memory = MethodCallMemory.create(
            method_name="test_in_session",
            method_key="session_test::test_in_session",
            input_args=["arg1"],
            input_kwargs={"session_id": session.id},
            output={"status": "completed"},
            execution_time=0.75,
            source_agent_did="did:example:alice",
            source_agent_name="Alice Agent",
            session_id=session.id,
            tags=["session_test"],
            keywords=["session", "test"]
        )
        
        # 验证记忆与会话的关联
        assert memory.metadata.session_id == session.id
        assert "session_test" in memory.metadata.tags
        assert "session" in memory.metadata.keywords
        
        # 模拟将记忆添加到会话
        session.add_memory(memory.id)
        assert memory.id in session.memory_entries


if __name__ == "__main__":
    pytest.main([__file__])