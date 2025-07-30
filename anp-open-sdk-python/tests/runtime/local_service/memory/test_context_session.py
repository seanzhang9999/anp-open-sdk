"""
上下文会话管理器测试

测试 ContextSessionManager、SessionLifecycleManager、SessionAnalyzer 等会话管理组件
"""

import pytest
import asyncio
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, List, Optional

from anp_runtime.local_service.memory.context_session import (
    ContextSessionManager,
    SessionLifecycleManager,
    SessionAnalyzer,
    get_session_manager,
    set_session_manager
)
from anp_runtime.local_service.memory.memory_models import (
    ContextSession,
    MemoryEntry,
    MemoryType,
    MemoryMetadata
)
from anp_runtime.local_service.memory.memory_storage import MemoryStorageInterface
from anp_runtime.local_service.memory.memory_config import MemoryConfig


class TestSessionLifecycleManager:
    """测试会话生命周期管理器"""
    
    @pytest.fixture
    def mock_storage(self):
        """创建模拟存储"""
        storage = Mock(spec=MemoryStorageInterface)
        storage.save_session = AsyncMock(return_value=True)
        storage.get_session = AsyncMock(return_value=None)
        storage.update_session = AsyncMock(return_value=True)
        storage.delete_session = AsyncMock(return_value=True)
        storage.get_memories_by_session = AsyncMock(return_value=[])
        return storage
    
    @pytest.fixture
    def lifecycle_manager(self, mock_storage):
        """创建会话生命周期管理器"""
        return SessionLifecycleManager(mock_storage)
    
    @pytest.mark.asyncio
    async def test_create_session_basic(self, lifecycle_manager, mock_storage):
        """测试基本会话创建"""
        session = await lifecycle_manager.create_session(
            name="Test Session",
            description="A test session",
            participants=["alice", "bob"],
            context_data={"purpose": "testing"}
        )
        
        # 验证会话属性
        assert session.name == "Test Session"
        assert session.description == "A test session"
        assert session.participants == ["alice", "bob"]
        assert session.context_data == {"purpose": "testing"}
        assert session.is_active == True
        assert isinstance(session.id, str)
        assert isinstance(session.created_at, datetime)
        
        # 验证存储被调用
        mock_storage.save_session.assert_called_once_with(session)
        
        # 验证会话被添加到活跃缓存
        assert session.id in lifecycle_manager._active_sessions
    
    @pytest.mark.asyncio
    async def test_create_session_with_defaults(self, lifecycle_manager, mock_storage):
        """测试使用默认参数创建会话"""
        session = await lifecycle_manager.create_session()
        
        # 验证默认值
        assert session.name.startswith("session_")
        assert session.description == ""
        assert session.participants == []
        assert session.context_data == {}
        assert session.is_active == True
        
        # 验证存储被调用
        mock_storage.save_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session_storage_failure(self, lifecycle_manager, mock_storage):
        """测试会话创建存储失败"""
        mock_storage.save_session.return_value = False
        
        with pytest.raises(RuntimeError, match="创建会话失败"):
            await lifecycle_manager.create_session(name="Failing Session")
    
    @pytest.mark.asyncio
    async def test_get_session_from_cache(self, lifecycle_manager):
        """测试从缓存获取会话"""
        # 创建会话并添加到缓存
        session = ContextSession(name="Cached Session")
        lifecycle_manager._active_sessions[session.id] = session
        
        # 获取会话
        retrieved_session = await lifecycle_manager.get_session(session.id)
        
        assert retrieved_session == session
        assert retrieved_session.name == "Cached Session"
    
    @pytest.mark.asyncio
    async def test_get_session_from_storage(self, lifecycle_manager, mock_storage):
        """测试从存储获取会话"""
        # 创建会话
        session = ContextSession(name="Stored Session")
        mock_storage.get_session.return_value = session
        
        # 获取会话
        retrieved_session = await lifecycle_manager.get_session(session.id)
        
        assert retrieved_session == session
        mock_storage.get_session.assert_called_once_with(session.id)
        
        # 验证会话被添加到缓存
        assert session.id in lifecycle_manager._active_sessions
    
    @pytest.mark.asyncio
    async def test_get_session_inactive_not_cached(self, lifecycle_manager, mock_storage):
        """测试获取非活跃会话不会被缓存"""
        # 创建非活跃会话
        session = ContextSession(name="Inactive Session")
        session.close()
        mock_storage.get_session.return_value = session
        
        # 获取会话
        retrieved_session = await lifecycle_manager.get_session(session.id)
        
        assert retrieved_session == session
        # 验证非活跃会话不被缓存
        assert session.id not in lifecycle_manager._active_sessions
    
    @pytest.mark.asyncio
    async def test_get_session_not_found(self, lifecycle_manager, mock_storage):
        """测试获取不存在的会话"""
        mock_storage.get_session.return_value = None
        
        session = await lifecycle_manager.get_session("non-existent-id")
        
        assert session is None
    
    @pytest.mark.asyncio
    async def test_update_session(self, lifecycle_manager, mock_storage):
        """测试更新会话"""
        # 创建会话
        session = ContextSession(name="Original Name")
        original_time = session.updated_at
        
        # 等待确保时间差异
        await asyncio.sleep(0.01)
        
        # 更新会话
        session.name = "Updated Name"
        success = await lifecycle_manager.update_session(session)
        
        assert success == True
        assert session.updated_at > original_time
        mock_storage.update_session.assert_called_once_with(session)
        
        # 验证缓存更新
        assert lifecycle_manager._active_sessions[session.id] == session
    
    @pytest.mark.asyncio
    async def test_update_session_inactive_removes_from_cache(self, lifecycle_manager, mock_storage):
        """测试更新非活跃会话从缓存中移除"""
        # 创建并缓存会话
        session = ContextSession(name="To Be Inactive")
        lifecycle_manager._active_sessions[session.id] = session
        
        # 关闭会话并更新
        session.close()
        success = await lifecycle_manager.update_session(session)
        
        assert success == True
        # 验证从缓存中移除
        assert session.id not in lifecycle_manager._active_sessions
    
    @pytest.mark.asyncio
    async def test_close_session(self, lifecycle_manager, mock_storage):
        """测试关闭会话"""
        # 创建并缓存会话
        session = ContextSession(name="To Be Closed")
        lifecycle_manager._active_sessions[session.id] = session
        mock_storage.get_session.return_value = session
        
        # 关闭会话
        success = await lifecycle_manager.close_session(session.id)
        
        assert success == True
        assert session.is_active == False
        mock_storage.update_session.assert_called_once()
        
        # 验证从活跃缓存中移除
        assert session.id not in lifecycle_manager._active_sessions
    
    @pytest.mark.asyncio
    async def test_close_session_not_found(self, lifecycle_manager, mock_storage):
        """测试关闭不存在的会话"""
        mock_storage.get_session.return_value = None
        
        success = await lifecycle_manager.close_session("non-existent-id")
        
        assert success == False
        mock_storage.update_session.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_session(self, lifecycle_manager, mock_storage):
        """测试删除会话"""
        # 创建并缓存会话
        session = ContextSession(name="To Be Deleted")
        lifecycle_manager._active_sessions[session.id] = session
        mock_storage.get_session.return_value = session
        
        # 删除会话
        success = await lifecycle_manager.delete_session(session.id)
        
        assert success == True
        mock_storage.delete_session.assert_called_once_with(session.id)
        
        # 验证从缓存中彻底移除
        assert session.id not in lifecycle_manager._active_sessions
    
    @pytest.mark.asyncio
    async def test_add_participant(self, lifecycle_manager, mock_storage):
        """测试添加参与者"""
        # 创建会话
        session = ContextSession(name="Test Session", participants=["alice"])
        mock_storage.get_session.return_value = session
        
        # 添加参与者
        success = await lifecycle_manager.add_participant(session.id, "bob")
        
        assert success == True
        assert "bob" in session.participants
        mock_storage.update_session.assert_called_once_with(session)
    
    @pytest.mark.asyncio
    async def test_add_participant_session_not_found(self, lifecycle_manager, mock_storage):
        """测试向不存在的会话添加参与者"""
        mock_storage.get_session.return_value = None
        
        success = await lifecycle_manager.add_participant("non-existent", "alice")
        
        assert success == False
        mock_storage.update_session.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_remove_participant(self, lifecycle_manager, mock_storage):
        """测试移除参与者"""
        # 创建有多个参与者的会话
        session = ContextSession(name="Test Session", participants=["alice", "bob"])
        mock_storage.get_session.return_value = session
        
        # 移除参与者
        success = await lifecycle_manager.remove_participant(session.id, "alice")
        
        assert success == True
        assert "alice" not in session.participants
        assert "bob" in session.participants
        mock_storage.update_session.assert_called_once_with(session)
    
    @pytest.mark.asyncio
    async def test_add_memory_to_session(self, lifecycle_manager, mock_storage):
        """测试向会话添加记忆"""
        # 创建会话
        session = ContextSession(name="Test Session")
        mock_storage.get_session.return_value = session
        
        # 添加记忆
        success = await lifecycle_manager.add_memory_to_session(session.id, "memory-123")
        
        assert success == True
        assert "memory-123" in session.memory_entries
        mock_storage.update_session.assert_called_once_with(session)
    
    @pytest.mark.asyncio
    async def test_remove_memory_from_session(self, lifecycle_manager, mock_storage):
        """测试从会话移除记忆"""
        # 创建有记忆的会话
        session = ContextSession(name="Test Session", memory_entries=["memory-123", "memory-456"])
        mock_storage.get_session.return_value = session
        
        # 移除记忆
        success = await lifecycle_manager.remove_memory_from_session(session.id, "memory-123")
        
        assert success == True
        assert "memory-123" not in session.memory_entries
        assert "memory-456" in session.memory_entries
        mock_storage.update_session.assert_called_once_with(session)
    
    @pytest.mark.asyncio
    async def test_update_context_data(self, lifecycle_manager, mock_storage):
        """测试更新上下文数据"""
        # 创建会话
        session = ContextSession(name="Test Session")
        mock_storage.get_session.return_value = session
        
        # 更新上下文数据
        success = await lifecycle_manager.update_context_data(session.id, "key1", "value1")
        
        assert success == True
        assert session.context_data["key1"] == "value1"
        mock_storage.update_session.assert_called_once_with(session)
    
    @pytest.mark.asyncio
    async def test_get_context_data(self, lifecycle_manager, mock_storage):
        """测试获取上下文数据"""
        # 创建有上下文数据的会话
        session = ContextSession(
            name="Test Session",
            context_data={"key1": "value1", "key2": "value2"}
        )
        mock_storage.get_session.return_value = session
        
        # 获取存在的键
        value = await lifecycle_manager.get_context_data(session.id, "key1")
        assert value == "value1"
        
        # 获取不存在的键（使用默认值）
        value = await lifecycle_manager.get_context_data(session.id, "key3", "default")
        assert value == "default"
        
        # 获取不存在的键（无默认值）
        value = await lifecycle_manager.get_context_data(session.id, "key3")
        assert value is None
    
    @pytest.mark.asyncio
    async def test_get_context_data_session_not_found(self, lifecycle_manager, mock_storage):
        """测试从不存在的会话获取上下文数据"""
        mock_storage.get_session.return_value = None
        
        value = await lifecycle_manager.get_context_data("non-existent", "key1", "default")
        
        assert value == "default"
    
    @pytest.mark.asyncio
    async def test_get_active_sessions(self, lifecycle_manager):
        """测试获取活跃会话"""
        # 添加多个会话到缓存
        session1 = ContextSession(name="Session 1")
        session2 = ContextSession(name="Session 2")
        session3 = ContextSession(name="Session 3")
        
        lifecycle_manager._active_sessions[session1.id] = session1
        lifecycle_manager._active_sessions[session2.id] = session2
        lifecycle_manager._active_sessions[session3.id] = session3
        
        # 获取活跃会话
        active_sessions = await lifecycle_manager.get_active_sessions()
        
        assert len(active_sessions) == 3
        assert session1 in active_sessions
        assert session2 in active_sessions
        assert session3 in active_sessions
    
    @pytest.mark.asyncio
    async def test_get_sessions_by_participant(self, lifecycle_manager):
        """测试按参与者获取会话"""
        # 创建不同参与者的会话
        session1 = ContextSession(name="Session 1", participants=["alice", "bob"])
        session2 = ContextSession(name="Session 2", participants=["alice", "charlie"])
        session3 = ContextSession(name="Session 3", participants=["bob", "charlie"])
        
        lifecycle_manager._active_sessions[session1.id] = session1
        lifecycle_manager._active_sessions[session2.id] = session2
        lifecycle_manager._active_sessions[session3.id] = session3
        
        # 获取Alice参与的会话
        alice_sessions = await lifecycle_manager.get_sessions_by_participant("alice")
        
        assert len(alice_sessions) == 2
        assert session1 in alice_sessions
        assert session2 in alice_sessions
        assert session3 not in alice_sessions
        
        # 获取Bob参与的会话
        bob_sessions = await lifecycle_manager.get_sessions_by_participant("bob")
        
        assert len(bob_sessions) == 2
        assert session1 in bob_sessions
        assert session3 in bob_sessions
        assert session2 not in bob_sessions
    
    @pytest.mark.asyncio
    async def test_cleanup_inactive_sessions(self, lifecycle_manager, mock_storage):
        """测试清理非活跃会话"""
        now = datetime.now()
        
        # 创建不同时间的会话
        old_session = ContextSession(name="Old Session")
        old_session.updated_at = now - timedelta(hours=25)  # 超过24小时
        
        recent_session = ContextSession(name="Recent Session")
        recent_session.updated_at = now - timedelta(hours=1)  # 1小时内
        
        lifecycle_manager._active_sessions[old_session.id] = old_session
        lifecycle_manager._active_sessions[recent_session.id] = recent_session
        
        # 模拟get_session调用
        def mock_get_session(session_id):
            if session_id == old_session.id:
                return old_session
            elif session_id == recent_session.id:
                return recent_session
            return None
        
        mock_storage.get_session.side_effect = mock_get_session
        
        # 清理非活跃会话
        closed_count = await lifecycle_manager.cleanup_inactive_sessions(max_age_hours=24)
        
        assert closed_count == 1
        assert old_session.is_active == False
        assert recent_session.is_active == True
    
    def test_event_listeners(self, lifecycle_manager):
        """测试事件监听器"""
        # 创建监听器
        session_created_calls = []
        session_updated_calls = []
        
        def on_session_created(session, **kwargs):
            session_created_calls.append((session, kwargs))
        
        def on_session_updated(session, **kwargs):
            session_updated_calls.append((session, kwargs))
        
        # 添加监听器
        lifecycle_manager.add_listener('session_created', on_session_created)
        lifecycle_manager.add_listener('session_updated', on_session_updated)
        
        # 验证监听器被添加
        assert on_session_created in lifecycle_manager._session_listeners['session_created']
        assert on_session_updated in lifecycle_manager._session_listeners['session_updated']
        
        # 触发事件
        test_session = ContextSession(name="Test Session")
        lifecycle_manager._notify_listeners('session_created', test_session, extra_data="test")
        lifecycle_manager._notify_listeners('session_updated', test_session)
        
        # 验证监听器被调用
        assert len(session_created_calls) == 1
        assert session_created_calls[0][0] == test_session
        assert session_created_calls[0][1]['extra_data'] == "test"
        
        assert len(session_updated_calls) == 1
        assert session_updated_calls[0][0] == test_session
        
        # 移除监听器
        lifecycle_manager.remove_listener('session_created', on_session_created)
        
        # 验证监听器被移除
        assert on_session_created not in lifecycle_manager._session_listeners['session_created']
    
    def test_event_listener_exception_handling(self, lifecycle_manager):
        """测试事件监听器异常处理"""
        # 创建会抛出异常的监听器
        def failing_listener(session, **kwargs):
            raise Exception("Listener error")
        
        lifecycle_manager.add_listener('session_created', failing_listener)
        
        # 触发事件不应该抛出异常
        test_session = ContextSession(name="Test Session")
        lifecycle_manager._notify_listeners('session_created', test_session)
        
        # 测试通过（没有异常抛出）


class TestSessionAnalyzer:
    """测试会话分析器"""
    
    @pytest.fixture
    def mock_storage(self):
        """创建模拟存储"""
        storage = Mock(spec=MemoryStorageInterface)
        return storage
    
    @pytest.fixture
    def session_analyzer(self, mock_storage):
        """创建会话分析器"""
        return SessionAnalyzer(mock_storage)
    
    def test_calculate_session_similarity_high(self, session_analyzer):
        """测试高相似度会话"""
        now = datetime.now()
        
        # 创建相似的会话
        session1 = ContextSession(
            name="Session 1",
            participants=["alice", "bob", "charlie"],
            memory_entries=["mem1", "mem2", "mem3"],
            context_data={"purpose": "meeting", "topic": "project"},
            created_at=now
        )
        
        session2 = ContextSession(
            name="Session 2",
            participants=["alice", "bob"],  # 2/3 重叠
            memory_entries=["mem2", "mem3", "mem4"],  # 2/4 重叠
            context_data={"purpose": "meeting", "location": "office"},  # 1/3 重叠
            created_at=now + timedelta(minutes=30)  # 相近时间
        )
        
        similarity = session_analyzer._calculate_session_similarity(session1, session2)
        
        # 计算预期相似度：
        # 参与者: 2/3 * 0.4 = 0.267
        # 记忆: 2/4 * 0.3 = 0.15
        # 上下文: 1/3 * 0.2 = 0.067
        # 时间: (1 - 1800/604800) * 0.1 ≈ 0.097
        # 总计: ≈ 0.58
        
        assert similarity > 0.5
        assert similarity < 0.7
    
    def test_calculate_session_similarity_low(self, session_analyzer):
        """测试低相似度会话"""
        now = datetime.now()
        
        # 创建不相似的会话
        session1 = ContextSession(
            name="Session 1",
            participants=["alice", "bob"],
            memory_entries=["mem1", "mem2"],
            context_data={"purpose": "meeting"},
            created_at=now
        )
        
        session2 = ContextSession(
            name="Session 2",
            participants=["charlie", "dave"],  # 无重叠
            memory_entries=["mem3", "mem4"],  # 无重叠
            context_data={"topic": "project"},  # 无重叠
            created_at=now - timedelta(days=10)  # 时间较远
        )
        
        similarity = session_analyzer._calculate_session_similarity(session1, session2)
        
        # 只有时间相似度有一点贡献
        assert similarity < 0.3
    
    def test_calculate_session_similarity_empty_sessions(self, session_analyzer):
        """测试空会话的相似度"""
        session1 = ContextSession(name="Empty 1")
        session2 = ContextSession(name="Empty 2")
        
        similarity = session_analyzer._calculate_session_similarity(session1, session2)
        
        # 只有时间相似度（创建时间很接近）
        assert similarity > 0.05
        assert similarity < 0.15
    
    def test_calculate_session_similarity_identical(self, session_analyzer):
        """测试相同会话的相似度"""
        session = ContextSession(
            name="Same Session",
            participants=["alice", "bob"],
            memory_entries=["mem1", "mem2"],
            context_data={"purpose": "meeting"}
        )
        
        similarity = session_analyzer._calculate_session_similarity(session, session)
        
        # 应该接近1.0（完全相似）
        assert similarity > 0.9


class TestContextSessionManager:
    """测试上下文会话管理器主类"""
    
    @pytest.fixture
    def mock_storage(self):
        """创建模拟存储"""
        storage = Mock(spec=MemoryStorageInterface)
        storage.save_session = AsyncMock(return_value=True)
        storage.get_session = AsyncMock(return_value=None)
        storage.update_session = AsyncMock(return_value=True)
        storage.delete_session = AsyncMock(return_value=True)
        storage.get_memories_by_session = AsyncMock(return_value=[])
        return storage
    
    @pytest.fixture
    def session_manager(self, mock_storage):
        """创建会话管理器"""
        with patch('anp_runtime.local_service.memory.context_session.create_storage') as mock_create_storage:
            mock_create_storage.return_value = mock_storage
            manager = ContextSessionManager(storage=mock_storage)
            # 停止自动清理任务以避免测试干扰
            if manager._cleanup_task:
                manager._cleanup_task.cancel()
            return manager
    
    @pytest.mark.asyncio
    async def test_session_manager_delegation(self, session_manager, mock_storage):
        """测试会话管理器方法代理"""
        # 测试创建会话
        session = await session_manager.create_session(name="Test Session")
        assert session.name == "Test Session"
        mock_storage.save_session.assert_called_once()
        
        # 测试获取会话
        mock_storage.get_session.return_value = session
        retrieved_session = await session_manager.get_session(session.id)
        assert retrieved_session == session
        
        # 测试更新会话
        session.description = "Updated"
        success = await session_manager.update_session(session)
        assert success == True
        mock_storage.update_session.assert_called()
        
        # 测试关闭会话
        success = await session_manager.close_session(session.id)
        assert success == True
        
        # 测试删除会话
        success = await session_manager.delete_session(session.id)
        assert success == True
        mock_storage.delete_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_memories(self, session_manager, mock_storage):
        """测试获取会话记忆"""
        # 创建测试记忆
        memories = [
            MemoryEntry(
                id="mem1",
                memory_type=MemoryType.METHOD_CALL,
                title="Memory 1",
                content={},
                metadata=MemoryMetadata(
                    source_agent_did="alice",
                    source_agent_name="Alice"
                )
            ),
            MemoryEntry(
                id="mem2",
                memory_type=MemoryType.USER_PREFERENCE,
                title="Memory 2",
                content={},
                metadata=MemoryMetadata(
                    source_agent_did="bob",
                    source_agent_name="Bob"
                )
            )
        ]
        
        mock_storage.get_memories_by_session.return_value = memories
        
        # 获取会话记忆
        session_memories = await session_manager.get_session_memories("session-123")
        
        assert len(session_memories) == 2
        assert session_memories == memories
        mock_storage.get_memories_by_session.assert_called_once_with("session-123")
    
    @pytest.mark.asyncio
    async def test_merge_sessions(self, session_manager, mock_storage):
        """测试合并会话"""
        # 创建源会话和目标会话
        source_session = ContextSession(
            name="Source Session",
            description="Source description",
            participants=["alice", "bob"],
            memory_entries=["mem1", "mem2"],
            context_data={"key1": "value1", "key2": "value2"}
        )
        
        target_session = ContextSession(
            name="Target Session",
            description="Target description",
            participants=["bob", "charlie"],
            memory_entries=["mem2", "mem3"],
            context_data={"key2": "different_value", "key3": "value3"}
        )
        
        # 模拟存储返回
        def mock_get_session(session_id):
            if session_id == source_session.id:
                return source_session
            elif session_id == target_session.id:
                return target_session
            return None
        
        mock_storage.get_session.side_effect = mock_get_session
        
        # 执行合并
        success = await session_manager.merge_sessions(source_session.id, target_session.id)
        
        assert success == True
        
        # 验证合并结果
        # 参与者合并（去重）
        assert set(target_session.participants) == {"alice", "bob", "charlie"}
        
        # 记忆条目合并（去重）
        assert set(target_session.memory_entries) == {"mem1", "mem2", "mem3"}
        
        # 上下文数据合并（不覆盖已存在的键）
        assert target_session.context_data["key1"] == "value1"  # 新增
        assert target_session.context_data["key2"] == "different_value"  # 保持原值
        assert target_session.context_data["key3"] == "value3"  # 保持原值
        
        # 描述合并
        assert "合并自: Source description" in target_session.description
        
        # 验证存储操作
        mock_storage.update_session.assert_called()
        mock_storage.delete_session.assert_called_once_with(source_session.id)
    
    @pytest.mark.asyncio
    async def test_merge_sessions_source_not_found(self, session_manager, mock_storage):
        """测试合并不存在的源会话"""
        target_session = ContextSession(name="Target Session")
        mock_storage.get_session.side_effect = lambda sid: target_session if sid == target_session.id else None
        
        success = await session_manager.merge_sessions("non-existent", target_session.id)
        
        assert success == False
        mock_storage.update_session.assert_not_called()
        mock_storage.delete_session.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_merge_sessions_target_not_found(self, session_manager, mock_storage):
        """测试合并到不存在的目标会话"""
        source_session = ContextSession(name="Source Session")
        mock_storage.get_session.side_effect = lambda sid: source_session if sid == source_session.id else None
        
        success = await session_manager.merge_sessions(source_session.id, "non-existent")
        
        assert success == False
        mock_storage.update_session.assert_not_called()
        mock_storage.delete_session.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_get_session_statistics(self, session_manager):
        """测试获取会话统计信息"""
        # 创建不同的会话
        session1 = ContextSession(
            name="Session 1",
            participants=["alice"],  # 1个参与者
            memory_entries=["mem1", "mem2"],  # 2个记忆
            context_data={"key1": "value1", "key2": "value2"}
        )
        
        session2 = ContextSession(
            name="Session 2",
            participants=["alice", "bob"],  # 2个参与者
            memory_entries=["mem3"],  # 1个记忆
            context_data={"key2": "value2", "key3": "value3"}
        )
        
        session3 = ContextSession(
            name="Session 3",
            participants=["alice", "bob", "charlie"],  # 3个参与者
            memory_entries=[],  # 0个记忆
            context_data={"key1": "value1"}
        )
        
        # 添加到活跃会话
        session_manager.lifecycle_manager._active_sessions[session1.id] = session1
        session_manager.lifecycle_manager._active_sessions[session2.id] = session2
        session_manager.lifecycle_manager._active_sessions[session3.id] = session3
        
        # 获取统计信息
        stats = await session_manager.get_session_statistics()
        
        # 验证基本统计
        assert stats['total_active_sessions'] == 3
        
        # 验证参与者分布
        assert stats['participants_distribution'][1] == 1  # 1个会话有1个参与者
        assert stats['participants_distribution'][2] == 1  # 1个会话有2个参与者
        assert stats['participants_distribution'][3] == 1  # 1个会话有3个参与者
        
        # 验证记忆分布
        assert stats['memory_distribution'][0] == 1  # 1个会话有0个记忆
        assert stats['memory_distribution'][1] == 1  # 1个会话有1个记忆
        assert stats['memory_distribution'][2] == 1  # 1个会话有2个记忆
        
        # 验证上下文键收集
        assert set(stats['context_keys']) == {"key1", "key2", "key3"}
    
    def test_session_event_listeners(self, session_manager):
        """测试会话事件监听器"""
        # 创建监听器
        listener_calls = []
        
        def test_listener(session, **kwargs):
            listener_calls.append((session.name, kwargs))
        
        # 添加监听器
        session_manager.add_session_listener('session_created', test_listener)
        
        # 验证监听器被添加到生命周期管理器
        assert test_listener in session_manager.lifecycle_manager._session_listeners['session_created']
        
        # 移除监听器
        session_manager.remove_session_listener('session_created', test_listener)
        
        # 验证监听器被移除
        assert test_listener not in session_manager.lifecycle_manager._session_listeners['session_created']
    
    @pytest.mark.asyncio
    async def test_context_session_manager_close(self, session_manager):
        """测试会话管理器关闭"""
        # 模拟有清理任务
        session_manager._cleanup_task = Mock()
        session_manager._cleanup_task.cancel = Mock()
        
        # 关闭管理器
        await session_manager.close()
        
        # 验证清理任务被取消
        session_manager._cleanup_task.cancel.assert_called_once()


class TestContextSessionManagerIntegration:
    """测试会话管理器集成场景"""
    
    @pytest.mark.asyncio
    async def test_full_session_lifecycle(self):
        """测试完整的会话生命周期"""
        from anp_runtime.local_service.memory.memory_storage import InMemoryStorage
        
        # 创建真实的存储和管理器
        storage = InMemoryStorage()
        session_manager = ContextSessionManager(storage=storage)
        
        # 1. 创建会话
        session = await session_manager.create_session(
            name="Integration Test Session",
            description="Testing full lifecycle",
            participants=["alice", "bob"],
            context_data={"purpose": "testing", "priority": "high"}
        )
        
        assert session.is_active == True
        assert len(session.participants) == 2
        
        # 2. 添加更多参与者
        success = await session_manager.add_participant(session.id, "charlie")
        assert success == True
        
        updated_session = await session_manager.get_session(session.id)
        assert updated_session is not None
        assert "charlie" in updated_session.participants
        
        # 3. 添加记忆条目
        success = await session_manager.add_memory_to_session(session.id, "memory-1")
        success = await session_manager.add_memory_to_session(session.id, "memory-2")
        assert success == True
        
        # 4. 更新上下文数据
        success = await session_manager.update_context_data(session.id, "status", "active")
        assert success == True
        
        context_value = await session_manager.get_context_data(session.id, "status")
        assert context_value == "active"
        
        # 5. 获取会话统计
        stats = await session_manager.get_session_statistics()
        assert stats['total_active_sessions'] >= 1
        
        # 6. 按参与者查找会话
        alice_sessions = await session_manager.get_sessions_by_participant("alice")
        assert len(alice_sessions) >= 1
        assert any(s.id == session.id for s in alice_sessions)
        
        # 7. 关闭会话
        success = await session_manager.close_session(session.id)
        assert success == True
        
        closed_session = await session_manager.get_session(session.id)
        assert closed_session is not None
        assert closed_session.is_active == False
        
        # 8. 删除会话
        success = await session_manager.delete_session(session.id)
        assert success == True
        
        deleted_session = await session_manager.get_session(session.id)
        assert deleted_session is None
        
        await session_manager.close()
    
    @pytest.mark.asyncio
    async def test_session_merge_scenario(self):
        """测试会话合并场景"""
        from anp_runtime.local_service.memory.memory_storage import InMemoryStorage
        
        storage = InMemoryStorage()
        session_manager = ContextSessionManager(storage=storage)
        
        # 创建两个相关的会话
        session1 = await session_manager.create_session(
            name="Project Meeting 1",
            description="Initial project discussion",
            participants=["alice", "bob"],
            context_data={"project": "alpha", "phase": "planning"}
        )
        
        session2 = await session_manager.create_session(
            name="Project Meeting 2", 
            description="Follow-up discussion",
            participants=["bob", "charlie"],
            context_data={"project": "alpha", "phase": "execution"}
        )
        
        # 添加记忆到两个会话
        await session_manager.add_memory_to_session(session1.id, "memory-planning-1")
        await session_manager.add_memory_to_session(session1.id, "memory-planning-2")
        await session_manager.add_memory_to_session(session2.id, "memory-execution-1")
        
        # 合并会话
        success = await session_manager.merge_sessions(session1.id, session2.id)
        assert success == True
        
        # 验证合并结果
        merged_session = await session_manager.get_session(session2.id)
        assert merged_session is not None
        
        # 参与者应该合并
        assert set(merged_session.participants) == {"alice", "bob", "charlie"}
        
        # 记忆应该合并
        assert set(merged_session.memory_entries) == {
            "memory-planning-1", "memory-planning-2", "memory-execution-1"
        }
        
        # 上下文数据应该合并
        assert merged_session.context_data["project"] == "alpha"
        assert "phase" in merged_session.context_data  # 保留原有值
        
        # 源会话应该被删除
        deleted_session = await session_manager.get_session(session1.id)
        assert deleted_session is None
        
        await session_manager.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_session_operations(self):
        """测试并发会话操作"""
        from anp_runtime.local_service.memory.memory_storage import InMemoryStorage
        
        storage = InMemoryStorage()
        session_manager = ContextSessionManager(storage=storage)
        
        # 创建基础会话
        session = await session_manager.create_session(
            name="Concurrent Test Session",
            participants=["alice"]
        )
        
        # 并发操作函数
        async def add_participant(agent_id):
            await session_manager.add_participant(session.id, f"agent_{agent_id}")
        
        async def add_memory(memory_id):
            await session_manager.add_memory_to_session(session.id, f"memory_{memory_id}")
        
        async def update_context(key, value):
            await session_manager.update_context_data(session.id, f"key_{key}", f"value_{value}")
        
        # 并发执行多个操作
        tasks = []
        for i in range(5):
            tasks.append(add_participant(i))
            tasks.append(add_memory(i))
            tasks.append(update_context(i, i))
        
        await asyncio.gather(*tasks)
        
        # 验证所有操作都成功
        final_session = await session_manager.get_session(session.id)
        assert final_session is not None
        
        # 应该有原始参与者 + 5个新参与者
        assert len(final_session.participants) == 6
        
        # 应该有5个记忆条目
        assert len(final_session.memory_entries) == 5
        
        # 应该有5个上下文键值对
        assert len(final_session.context_data) == 5
        
        await session_manager.close()


class TestGlobalSessionManager:
    """测试全局会话管理器"""
    
    def test_get_session_manager_singleton(self):
        """测试获取全局会话管理器单例"""
        # 清除全局实例
        with patch('anp_runtime.local_service.memory.context_session._global_session_manager', None):
            # 第一次获取应该创建新实例
            manager1 = get_session_manager()
            assert isinstance(manager1, ContextSessionManager)
            
            # 第二次获取应该返回同一实例
            manager2 = get_session_manager()
            assert manager1 is manager2
    
    def test_set_session_manager(self):
        """测试设置全局会话管理器"""
        # 创建自定义管理器
        custom_manager = Mock(spec=ContextSessionManager)
        
        # 设置全局管理器
        set_session_manager(custom_manager)
        
        # 验证获取的是设置的管理器
        retrieved_manager = get_session_manager()
        assert retrieved_manager is custom_manager


if __name__ == "__main__":
    pytest.main([__file__])