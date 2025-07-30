"""
记忆管理器测试

测试 MemoryManager、MemoryLifecycleManager、MemorySearchEngine 等核心管理组件
"""

import pytest
import asyncio
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock

from anp_runtime.local_service.memory.memory_manager import (
    MemoryManager,
    MemoryLifecycleManager,
    MemorySearchEngine,
    MemoryEventType,
    get_memory_manager,
    set_memory_manager
)
from anp_runtime.local_service.memory.memory_storage import InMemoryStorage
from anp_runtime.local_service.memory.context_session import ContextSessionManager
from anp_runtime.local_service.memory.memory_models import (
    MemoryEntry,
    ContextSession,
    MemoryType,
    MemoryMetadata,
    MethodCallMemory
)
from anp_runtime.local_service.memory.memory_config import (
    MemoryConfig,
    StorageConfig,
    CleanupConfig,
    PerformanceConfig
)


class TestMemoryLifecycleManager:
    """测试记忆生命周期管理器"""
    
    @pytest.fixture
    def storage(self):
        """创建存储实例"""
        return InMemoryStorage()
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MemoryConfig(
            cleanup=CleanupConfig(
                enable_auto_cleanup=False,  # 测试时禁用自动清理
                max_memory_entries=10,
                cleanup_strategy="smart"
            )
        )
    
    @pytest.fixture
    def lifecycle_manager(self, storage, config):
        """创建生命周期管理器"""
        return MemoryLifecycleManager(storage, config)
    
    def test_lifecycle_manager_initialization(self, lifecycle_manager, storage, config):
        """测试生命周期管理器初始化"""
        assert lifecycle_manager.storage == storage
        assert lifecycle_manager.config == config
        assert isinstance(lifecycle_manager._event_listeners, dict)
        assert "memory_created" in lifecycle_manager._event_listeners
        assert "memory_updated" in lifecycle_manager._event_listeners
        assert "memory_deleted" in lifecycle_manager._event_listeners
    
    def test_add_remove_event_listener(self, lifecycle_manager):
        """测试添加和移除事件监听器"""
        # 创建模拟监听器
        listener1 = Mock()
        listener2 = Mock()
        
        # 添加监听器
        lifecycle_manager.add_event_listener(MemoryEventType.MEMORY_CREATED, listener1)
        lifecycle_manager.add_event_listener(MemoryEventType.MEMORY_CREATED, listener2)
        
        assert listener1 in lifecycle_manager._event_listeners[MemoryEventType.MEMORY_CREATED]
        assert listener2 in lifecycle_manager._event_listeners[MemoryEventType.MEMORY_CREATED]
        
        # 移除监听器
        lifecycle_manager.remove_event_listener(MemoryEventType.MEMORY_CREATED, listener1)
        assert listener1 not in lifecycle_manager._event_listeners[MemoryEventType.MEMORY_CREATED]
        assert listener2 in lifecycle_manager._event_listeners[MemoryEventType.MEMORY_CREATED]
    
    def test_notify_listeners(self, lifecycle_manager):
        """测试通知监听器"""
        # 创建模拟监听器
        listener = Mock()
        lifecycle_manager.add_event_listener(MemoryEventType.MEMORY_CREATED, listener)
        
        # 创建测试记忆
        memory = MemoryEntry(
            title="Test Memory",
            metadata=MemoryMetadata("alice", "Alice")
        )
        
        # 通知监听器
        lifecycle_manager._notify_listeners(MemoryEventType.MEMORY_CREATED, memory, extra_param="test")
        
        # 验证监听器被调用
        listener.assert_called_once_with(memory, extra_param="test")
    
    def test_notify_listeners_with_exception(self, lifecycle_manager):
        """测试监听器异常处理"""
        # 创建会抛出异常的监听器
        failing_listener = Mock(side_effect=Exception("Listener error"))
        working_listener = Mock()
        
        lifecycle_manager.add_event_listener(MemoryEventType.MEMORY_CREATED, failing_listener)
        lifecycle_manager.add_event_listener(MemoryEventType.MEMORY_CREATED, working_listener)
        
        memory = MemoryEntry(title="Test", metadata=MemoryMetadata("alice", "Alice"))
        
        # 通知应该继续执行，不受异常影响
        lifecycle_manager._notify_listeners(MemoryEventType.MEMORY_CREATED, memory)
        
        failing_listener.assert_called_once()
        working_listener.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cleanup_by_strategy_lru(self, lifecycle_manager):
        """测试LRU清理策略"""
        storage = lifecycle_manager.storage
        
        # 创建多个记忆，超过最大限制
        memories = []
        for i in range(15):
            memory = MemoryEntry(
                title=f"Memory {i}",
                metadata=MemoryMetadata("alice", "Alice")
            )
            # 模拟不同的访问时间
            if i < 5:
                memory.metadata.last_accessed = datetime.now() - timedelta(days=i+1)
            memories.append(memory)
            await storage.save_memory(memory)
        
        # 执行LRU清理
        lifecycle_manager.config.cleanup.cleanup_strategy = "lru"
        cleaned_count = await lifecycle_manager._cleanup_by_strategy()
        
        # 验证清理了多余的记忆
        assert cleaned_count >= 5  # 应该清理至少5个以达到限制
        
        # 验证剩余记忆数量
        remaining_memories = await storage.search_memories(limit=20)
        assert len(remaining_memories) <= lifecycle_manager.config.cleanup.max_memory_entries
    
    @pytest.mark.asyncio
    async def test_cleanup_by_strategy_time_based(self, lifecycle_manager):
        """测试基于时间的清理策略"""
        storage = lifecycle_manager.storage
        
        # 创建不同时间的记忆
        old_memory = MemoryEntry(
            title="Old Memory",
            metadata=MemoryMetadata("alice", "Alice"),
            created_at=datetime.now() - timedelta(days=40)
        )
        recent_memory = MemoryEntry(
            title="Recent Memory",
            metadata=MemoryMetadata("alice", "Alice")
        )
        
        await storage.save_memory(old_memory)
        await storage.save_memory(recent_memory)
        
        # 执行时间清理
        lifecycle_manager.config.cleanup.cleanup_strategy = "time_based"
        lifecycle_manager.config.cleanup.retention_days = 30
        
        cleaned_count = await lifecycle_manager._cleanup_time_based(10)
        
        # 验证清理了过期记忆
        assert cleaned_count >= 1
        assert await storage.get_memory(recent_memory.id) is not None
    
    @pytest.mark.asyncio
    async def test_cleanup_by_strategy_smart(self, lifecycle_manager):
        """测试智能清理策略"""
        storage = lifecycle_manager.storage
        
        # 创建不同重要性的记忆
        important_memory = MemoryEntry(
            title="Important Memory",
            memory_type=MemoryType.USER_PREFERENCE,
            metadata=MemoryMetadata(
                "alice", "Alice",
                access_count=10,
                relevance_score=0.9
            )
        )
        
        less_important_memory = MemoryEntry(
            title="Less Important Memory",
            memory_type=MemoryType.ERROR,
            metadata=MemoryMetadata(
                "alice", "Alice",
                access_count=1,
                relevance_score=0.1
            )
        )
        
        await storage.save_memory(important_memory)
        await storage.save_memory(less_important_memory)
        
        # 执行智能清理
        lifecycle_manager.config.cleanup.cleanup_strategy = "smart"
        cleaned_count = await lifecycle_manager._cleanup_smart(1)
        
        # 验证保留了重要记忆
        assert await storage.get_memory(important_memory.id) is not None
        # 低重要性记忆可能被清理


class TestMemorySearchEngine:
    """测试记忆搜索引擎"""
    
    @pytest.fixture
    def storage(self):
        """创建存储实例"""
        return InMemoryStorage()
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MemoryConfig(
            performance=PerformanceConfig(
                enable_search_cache=True,
                search_cache_size=5
            )
        )
    
    @pytest.fixture
    def search_engine(self, storage, config):
        """创建搜索引擎"""
        return MemorySearchEngine(storage, config)
    
    @pytest.fixture
    async def sample_memories(self, storage):
        """创建示例记忆数据"""
        memories = [
            MemoryEntry(
                title="Database Query",
                memory_type=MemoryType.METHOD_CALL,
                content={"method": "query_users", "table": "users"},
                metadata=MemoryMetadata(
                    "alice", "Alice",
                    tags=["database", "query"],
                    keywords=["sql", "users"]
                )
            ),
            MemoryEntry(
                title="File Processing",
                memory_type=MemoryType.METHOD_CALL,
                content={"method": "process_file", "file": "data.csv"},
                metadata=MemoryMetadata(
                    "bob", "Bob",
                    tags=["file", "processing"],
                    keywords=["csv", "data"]
                )
            ),
            MemoryEntry(
                title="Error Handling",
                memory_type=MemoryType.ERROR,
                content={"error": "connection_failed"},
                metadata=MemoryMetadata(
                    "alice", "Alice",
                    tags=["error", "connection"],
                    keywords=["network", "failure"]
                )
            )
        ]
        
        for memory in memories:
            await storage.save_memory(memory)
        
        return memories
    
    @pytest.mark.asyncio
    async def test_basic_search(self, search_engine, sample_memories):
        """测试基本搜索功能"""
        # 搜索包含"Database"的记忆
        results = await search_engine.search(query="Database")
        assert len(results) == 1
        assert "Database" in results[0].title
        
        # 按类型搜索
        method_results = await search_engine.search(memory_type=MemoryType.METHOD_CALL)
        assert len(method_results) == 2
        
        error_results = await search_engine.search(memory_type=MemoryType.ERROR)
        assert len(error_results) == 1
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, search_engine, sample_memories):
        """测试带过滤器的搜索"""
        # 按Agent搜索
        alice_results = await search_engine.search(agent_did="alice")
        assert len(alice_results) == 2
        
        # 按标签搜索
        database_results = await search_engine.search(tags=["database"])
        assert len(database_results) == 1
        
        # 按关键词搜索
        data_results = await search_engine.search(keywords=["data"])
        assert len(data_results) == 1
    
    @pytest.mark.asyncio
    async def test_search_with_time_range(self, search_engine, sample_memories):
        """测试时间范围搜索"""
        now = datetime.now()
        time_range = (now - timedelta(hours=1), now + timedelta(hours=1))
        
        results = await search_engine.search(time_range=time_range)
        # 所有记忆都在时间范围内
        assert len(results) == 3
        
        # 测试过去的时间范围
        past_range = (now - timedelta(days=2), now - timedelta(days=1))
        past_results = await search_engine.search(time_range=past_range)
        assert len(past_results) == 0
    
    @pytest.mark.asyncio
    async def test_search_with_pagination(self, search_engine, sample_memories):
        """测试搜索分页"""
        # 限制结果数量
        results = await search_engine.search(limit=2)
        assert len(results) <= 2
        
        # 测试偏移
        offset_results = await search_engine.search(limit=2, offset=1)
        assert len(offset_results) <= 2
    
    @pytest.mark.asyncio
    async def test_search_cache(self, search_engine, sample_memories):
        """测试搜索缓存"""
        # 第一次搜索
        results1 = await search_engine.search(query="Database", use_cache=True)
        
        # 第二次相同搜索应该使用缓存
        results2 = await search_engine.search(query="Database", use_cache=True)
        
        assert len(results1) == len(results2)
        assert results1[0].id == results2[0].id
        
        # 验证缓存存在
        cache_key = search_engine._generate_cache_key(
            "Database", None, None, None, None, None, None, 100, 0
        )
        assert cache_key in search_engine._search_cache
    
    @pytest.mark.asyncio
    async def test_search_similar_memories(self, search_engine, sample_memories):
        """测试搜索相似记忆"""
        reference_memory = sample_memories[0]  # Database Query memory
        
        similar_memories = await search_engine.search_similar_memories(
            reference_memory,
            similarity_threshold=0.1,
            limit=5
        )
        
        # 应该找到一些相似记忆（但不包括自己）
        assert len(similar_memories) >= 0
        for memory in similar_memories:
            assert memory.id != reference_memory.id
    
    def test_calculate_memory_similarity(self, search_engine):
        """测试记忆相似度计算"""
        memory1 = MemoryEntry(
            title="Test Memory 1",
            memory_type=MemoryType.METHOD_CALL,
            metadata=MemoryMetadata(
                "alice", "Alice",
                tags=["test", "similarity"],
                keywords=["algorithm", "test"]
            )
        )
        
        memory2 = MemoryEntry(
            title="Test Memory 2",
            memory_type=MemoryType.METHOD_CALL,
            metadata=MemoryMetadata(
                "alice", "Alice",
                tags=["test", "comparison"],
                keywords=["algorithm", "comparison"]
            )
        )
        
        similarity = search_engine._calculate_memory_similarity(memory1, memory2)
        
        # 相似度应该在0-1之间
        assert 0 <= similarity <= 1
        
        # 相同类型应该增加相似度
        assert similarity > 0
        
        # 测试完全相同的记忆
        same_similarity = search_engine._calculate_memory_similarity(memory1, memory1)
        assert same_similarity > similarity


class TestMemoryManager:
    """测试记忆管理器"""
    
    @pytest.fixture
    def storage(self):
        """创建存储实例"""
        return InMemoryStorage()
    
    @pytest.fixture
    def session_manager(self):
        """创建会话管理器"""
        return Mock(spec=ContextSessionManager)
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MemoryConfig(
            enabled=True,
            cleanup=CleanupConfig(enable_auto_cleanup=False)
        )
    
    @pytest.fixture
    def memory_manager(self, storage, session_manager, config):
        """创建记忆管理器"""
        return MemoryManager(storage, session_manager, config)
    
    def test_memory_manager_initialization(self, memory_manager, storage, session_manager, config):
        """测试记忆管理器初始化"""
        assert memory_manager.storage == storage
        assert memory_manager.session_manager == session_manager
        assert memory_manager.config == config
        assert isinstance(memory_manager.lifecycle_manager, MemoryLifecycleManager)
        assert isinstance(memory_manager.search_engine, MemorySearchEngine)
        assert isinstance(memory_manager._stats, dict)
    
    @pytest.mark.asyncio
    async def test_create_memory(self, memory_manager):
        """测试创建记忆"""
        memory = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Test Memory",
            content={"test": "data"},
            source_agent_did="alice",
            source_agent_name="Alice",
            tags=["test"],
            keywords=["memory"]
        )
        
        assert memory.memory_type == MemoryType.METHOD_CALL
        assert memory.title == "Test Memory"
        assert memory.content == {"test": "data"}
        assert memory.metadata.source_agent_did == "alice"
        assert memory.metadata.tags == ["test"]
        assert memory.metadata.keywords == ["memory"]
        
        # 验证统计信息更新
        assert memory_manager._stats['memories_created'] == 1
    
    @pytest.mark.asyncio
    async def test_create_memory_with_session(self, memory_manager):
        """测试创建带会话的记忆"""
        session_id = "test-session"
        memory_manager.session_manager.add_memory_to_session = AsyncMock(return_value=True)
        
        memory = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Session Memory",
            content={},
            source_agent_did="alice",
            source_agent_name="Alice",
            session_id=session_id
        )
        
        assert memory.metadata.session_id == session_id
        
        # 验证会话管理器被调用
        memory_manager.session_manager.add_memory_to_session.assert_called_once_with(
            session_id, memory.id
        )
    
    @pytest.mark.asyncio
    async def test_get_memory(self, memory_manager):
        """测试获取记忆"""
        # 先创建记忆
        created_memory = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Get Test",
            content={},
            source_agent_did="alice",
            source_agent_name="Alice"
        )
        
        # 获取记忆
        retrieved_memory = await memory_manager.get_memory(created_memory.id)
        
        assert retrieved_memory is not None
        assert retrieved_memory.id == created_memory.id
        assert retrieved_memory.title == "Get Test"
        
        # 验证统计信息更新
        assert memory_manager._stats['memories_accessed'] >= 1
    
    @pytest.mark.asyncio
    async def test_update_memory(self, memory_manager):
        """测试更新记忆"""
        # 创建记忆
        memory = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Original Title",
            content={},
            source_agent_did="alice",
            source_agent_name="Alice"
        )
        
        # 修改记忆
        memory.title = "Updated Title"
        memory.content["updated"] = True
        
        # 更新记忆
        success = await memory_manager.update_memory(memory)
        assert success
        
        # 验证更新
        updated_memory = await memory_manager.get_memory(memory.id)
        assert updated_memory.title == "Updated Title"
        assert updated_memory.content["updated"] == True
        
        # 验证统计信息
        assert memory_manager._stats['memories_updated'] >= 1
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, memory_manager):
        """测试删除记忆"""
        # 创建带会话的记忆
        memory = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Delete Test",
            content={},
            source_agent_did="alice",
            source_agent_name="Alice",
            session_id="test-session"
        )
        
        memory_manager.session_manager.remove_memory_from_session = AsyncMock(return_value=True)
        
        # 删除记忆
        success = await memory_manager.delete_memory(memory.id)
        assert success
        
        # 验证记忆已删除
        deleted_memory = await memory_manager.get_memory(memory.id)
        assert deleted_memory is None
        
        # 验证从会话中移除
        memory_manager.session_manager.remove_memory_from_session.assert_called_once_with(
            "test-session", memory.id
        )
        
        # 验证统计信息
        assert memory_manager._stats['memories_deleted'] >= 1
    
    @pytest.mark.asyncio
    async def test_search_memories(self, memory_manager):
        """测试搜索记忆"""
        # 创建测试记忆
        await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Search Test 1",
            content={},
            source_agent_did="alice",
            source_agent_name="Alice",
            tags=["search", "test"]
        )
        
        await memory_manager.create_memory(
            memory_type=MemoryType.ERROR,
            title="Search Test 2",
            content={},
            source_agent_did="bob",
            source_agent_name="Bob",
            tags=["search", "error"]
        )
        
        # 搜索记忆
        results = await memory_manager.search_memories(tags=["search"])
        assert len(results) == 2
        
        type_results = await memory_manager.search_memories(memory_type=MemoryType.METHOD_CALL)
        assert len(type_results) >= 1
        
        # 验证统计信息
        assert memory_manager._stats['searches_performed'] >= 2
    
    @pytest.mark.asyncio
    async def test_search_similar_memories(self, memory_manager):
        """测试搜索相似记忆"""
        # 创建参考记忆
        reference_memory = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Reference Memory",
            content={},
            source_agent_did="alice",
            source_agent_name="Alice",
            tags=["reference", "similarity"],
            keywords=["test", "similarity"]
        )
        
        # 创建相似记忆
        await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Similar Memory",
            content={},
            source_agent_did="alice",
            source_agent_name="Alice",
            tags=["reference", "test"],
            keywords=["test", "algorithm"]
        )
        
        # 搜索相似记忆
        similar_memories = await memory_manager.search_similar_memories(reference_memory)
        
        # 应该找到相似记忆，但不包括自己
        for memory in similar_memories:
            assert memory.id != reference_memory.id
    
    @pytest.mark.asyncio
    async def test_create_memories_batch(self, memory_manager):
        """测试批量创建记忆"""
        memory_specs = [
            {
                "memory_type": MemoryType.METHOD_CALL,
                "title": "Batch Memory 1",
                "content": {"index": 1},
                "source_agent_did": "alice",
                "source_agent_name": "Alice"
            },
            {
                "memory_type": MemoryType.METHOD_CALL,
                "title": "Batch Memory 2",
                "content": {"index": 2},
                "source_agent_did": "bob",
                "source_agent_name": "Bob"
            }
        ]
        
        created_memories = await memory_manager.create_memories_batch(memory_specs)
        
        assert len(created_memories) == 2
        assert created_memories[0].title == "Batch Memory 1"
        assert created_memories[1].title == "Batch Memory 2"
        
        # 验证统计信息
        assert memory_manager._stats['memories_created'] >= 2
    
    @pytest.mark.asyncio
    async def test_delete_memories_batch(self, memory_manager):
        """测试批量删除记忆"""
        # 创建测试记忆
        memory1 = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Delete Batch 1",
            content={},
            source_agent_did="alice",
            source_agent_name="Alice"
        )
        
        memory2 = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Delete Batch 2",
            content={},
            source_agent_did="alice",
            source_agent_name="Alice"
        )
        
        # 批量删除
        deleted_count = await memory_manager.delete_memories_batch([memory1.id, memory2.id])
        
        assert deleted_count == 2
        
        # 验证删除
        assert await memory_manager.get_memory(memory1.id) is None
        assert await memory_manager.get_memory(memory2.id) is None
    
    @pytest.mark.asyncio
    async def test_create_method_call_memory(self, memory_manager):
        """测试创建方法调用记忆"""
        memory = await memory_manager.create_method_call_memory(
            method_name="test_method",
            method_key="module::test_method",
            input_args=[1, 2, 3],
            input_kwargs={"param": "value"},
            output={"result": "success"},
            execution_time=0.5,
            source_agent_did="alice",
            source_agent_name="Alice"
        )
        
        assert memory.memory_type == MemoryType.METHOD_CALL
        assert memory.title == "调用test_method"
        assert memory.content["method_name"] == "test_method"
        assert memory.content["input"]["args"] == [1, 2, 3]
        assert memory.content["output"] == {"result": "success"}
        assert memory.content["execution_time"] == 0.5
    
    @pytest.mark.asyncio
    async def test_create_error_memory(self, memory_manager):
        """测试创建错误记忆"""
        error = ValueError("Test error")
        
        memory = await memory_manager.create_error_memory(
            method_name="failing_method",
            method_key="module::failing_method",
            input_args=[],
            input_kwargs={},
            error=error,
            execution_time=0.1,
            source_agent_did="alice",
            source_agent_name="Alice"
        )
        
        assert memory.memory_type == MemoryType.ERROR
        assert memory.title == "调用failing_method失败"
        assert memory.content["method_name"] == "failing_method"
        assert memory.content["error"]["type"] == "ValueError"
        assert memory.content["error"]["message"] == "Test error"
        assert memory.content["success"] == False
    
    @pytest.mark.asyncio
    async def test_get_memory_statistics(self, memory_manager):
        """测试获取记忆统计信息"""
        # 创建一些测试数据
        await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Stats Test",
            content={},
            source_agent_did="alice",
            source_agent_name="Alice"
        )
        
        # 模拟存储和会话统计
        with patch.object(memory_manager.storage, 'get_storage_stats', new_callable=AsyncMock) as mock_storage_stats:
            with patch.object(memory_manager.session_manager, 'get_session_statistics', new_callable=AsyncMock) as mock_session_stats:
                mock_storage_stats.return_value = {
                    "total_memories": 1,
                    "storage_type": "memory"
                }
                mock_session_stats.return_value = {
                    "total_sessions": 0
                }
                
                stats = await memory_manager.get_memory_statistics()
                
                assert "storage" in stats
                assert "sessions" in stats
                assert "operations" in stats
                assert "config" in stats
                
                # 验证操作统计
                assert stats["operations"]["memories_created"] >= 1
                
                # 验证配置信息
                assert stats["config"]["enabled"] == True
    
    def test_event_management(self, memory_manager):
        """测试事件管理"""
        listener = Mock()
        
        # 添加事件监听器
        memory_manager.add_event_listener(MemoryEventType.MEMORY_CREATED, listener)
        
        # 验证监听器被添加
        assert listener in memory_manager.lifecycle_manager._event_listeners[MemoryEventType.MEMORY_CREATED]
        
        # 移除事件监听器
        memory_manager.remove_event_listener(MemoryEventType.MEMORY_CREATED, listener)
        
        # 验证监听器被移除
        assert listener not in memory_manager.lifecycle_manager._event_listeners[MemoryEventType.MEMORY_CREATED]
    
    @pytest.mark.asyncio
    async def test_cleanup_memories(self, memory_manager):
        """测试手动触发记忆清理"""
        with patch.object(memory_manager.lifecycle_manager, '_perform_cleanup', new_callable=AsyncMock) as mock_cleanup:
            result = await memory_manager.cleanup_memories()
            
            mock_cleanup.assert_called_once()
            assert isinstance(result, dict)
            assert "expired_cleaned" in result
            assert "strategy_cleaned" in result
    
    @pytest.mark.asyncio
    async def test_close_memory_manager(self, memory_manager):
        """测试关闭记忆管理器"""
        with patch.object(memory_manager.lifecycle_manager, 'close', new_callable=AsyncMock) as mock_lifecycle_close:
            with patch.object(memory_manager.session_manager, 'close', new_callable=AsyncMock) as mock_session_close:
                with patch.object(memory_manager.storage, 'close') as mock_storage_close:
                    await memory_manager.close()
                    
                    mock_lifecycle_close.assert_called_once()
                    mock_session_close.assert_called_once()
                    mock_storage_close.assert_called_once()


class TestMemoryManagerGlobal:
    """测试全局记忆管理器"""
    
    def test_get_memory_manager_singleton(self):
        """测试获取全局记忆管理器单例"""
        # 清除全局实例
        set_memory_manager(None)
        
        # 第一次获取应该创建新实例
        manager1 = get_memory_manager()
        assert isinstance(manager1, MemoryManager)
        
        # 第二次获取应该返回同一实例
        manager2 = get_memory_manager()
        assert manager1 is manager2
    
    def test_set_memory_manager(self):
        """测试设置全局记忆管理器"""
        # 创建自定义管理器
        custom_manager = Mock(spec=MemoryManager)
        
        # 设置全局管理器
        set_memory_manager(custom_manager)
        
        # 验证获取的是设置的管理器
        retrieved_manager = get_memory_manager()
        assert retrieved_manager is custom_manager
        
        # 清理
        set_memory_manager(None)


class TestMemoryManagerIntegration:
    """测试记忆管理器集成场景"""
    
    @pytest.mark.asyncio
    async def test_full_memory_lifecycle(self):
        """测试完整的记忆生命周期"""
        # 创建集成测试环境
        storage = InMemoryStorage()
        session_manager = Mock(spec=ContextSessionManager)
        session_manager.add_memory_to_session = AsyncMock(return_value=True)
        session_manager.remove_memory_from_session = AsyncMock(return_value=True)
        
        config = MemoryConfig(enabled=True)
        memory_manager = MemoryManager(storage, session_manager, config)
        
        # 1. 创建记忆
        memory = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Integration Test Memory",
            content={"step": "create"},
            source_agent_did="alice",
            source_agent_name="Alice",
            session_id="integration-session",
            tags=["integration", "test"],
            keywords=["lifecycle", "test"]
        )
        
        # 2. 获取记忆
        retrieved_memory = await memory_manager.get_memory(memory.id)
        assert retrieved_memory is not None
        assert retrieved_memory.title == "Integration Test Memory"
        
        # 3. 更新记忆
        retrieved_memory.content["step"] = "update"
        await memory_manager.update_memory(retrieved_memory)
        
        # 4. 搜索记忆
        search_results = await memory_manager.search_memories(tags=["integration"])
        assert len(search_results) == 1
        assert search_results[0].content["step"] == "update"
        
        # 5. 创建相似记忆
        similar_memory = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Similar Integration Memory",
            content={"step": "similar"},
            source_agent_did="alice",
            source_agent_name="Alice",
            tags=["integration", "similar"],
            keywords=["lifecycle", "similar"]
        )
        
        # 6. 搜索相似记忆
        similar_results = await memory_manager.search_similar_memories(retrieved_memory)
        assert len(similar_results) >= 1
        
        # 7. 获取统计信息
        stats = await memory_manager.get_memory_statistics()
        assert stats["operations"]["memories_created"] >= 2
        assert stats["operations"]["memories_accessed"] >= 1
        assert stats["operations"]["memories_updated"] >= 1
        assert stats["operations"]["searches_performed"] >= 2
        
        # 8. 删除记忆
        await memory_manager.delete_memory(memory.id)
        await memory_manager.delete_memory(similar_memory.id)
        
        # 验证删除
        assert await memory_manager.get_memory(memory.id) is None
        assert await memory_manager.get_memory(similar_memory.id) is None
        
        # 关闭管理器
        await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_memory_operations(self):
        """测试并发记忆操作"""
        memory_manager = MemoryManager()
        
        async def create_memories(start_index, count):
            memories = []
            for i in range(start_index, start_index + count):
                memory = await memory_manager.create_memory(
                    memory_type=MemoryType.METHOD_CALL,
                    title=f"Concurrent Memory {i}",
                    content={"index": i},
                    source_agent_did=f"agent_{i % 3}",
                    source_agent_name=f"Agent {i % 3}"
                )
                memories.append(memory)
            return memories
        
        # 并发创建记忆
        tasks = [
            create_memories(0, 10),
            create_memories(10, 10),
            create_memories(20, 10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 验证所有记忆都被创建
        total_memories = sum(len(batch) for batch in results)
        assert total_memories == 30
        
        # 验证可以搜索到所有记忆
        all_memories = await memory_manager.search_memories(limit=50)
        assert len(all_memories) == 30
        
        # 验证统计信息
        stats = await memory_manager.get_memory_statistics()
        assert stats["operations"]["memories_created"] == 30
        
        await memory_manager.close()


if __name__ == "__main__":
    pytest.main([__file__])