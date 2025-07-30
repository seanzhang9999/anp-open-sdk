"""
记忆存储管理测试

测试 SQLiteMemoryStorage、InMemoryStorage 等存储实现
"""

import pytest
import asyncio
import tempfile
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from anp_runtime.local_service.memory.memory_storage import (
    MemoryStorageInterface,
    SQLiteMemoryStorage,
    InMemoryStorage,
    create_storage
)
from anp_runtime.local_service.memory.memory_models import (
    MemoryEntry,
    ContextSession,
    MemoryType,
    MemoryMetadata
)
from anp_runtime.local_service.memory.memory_config import (
    MemoryConfig,
    StorageConfig,
    PerformanceConfig
)


class TestMemoryStorageInterface:
    """测试记忆存储接口"""
    
    def test_interface_abstract_methods(self):
        """测试接口是抽象的"""
        # 不能直接实例化抽象接口
        with pytest.raises(TypeError):
            MemoryStorageInterface()


class TestInMemoryStorage:
    """测试内存存储实现"""
    
    @pytest.fixture
    def storage(self):
        """创建内存存储实例"""
        return InMemoryStorage()
    
    @pytest.fixture
    def sample_memory(self):
        """创建示例记忆条目"""
        metadata = MemoryMetadata(
            source_agent_did="did:example:alice",
            source_agent_name="Alice Agent",
            session_id="session-123",
            tags=["test", "sample"],
            keywords=["memory", "test"]
        )
        return MemoryEntry(
            memory_type=MemoryType.METHOD_CALL,
            title="Test Memory",
            content={"method": "test_method", "result": "success"},
            metadata=metadata
        )
    
    @pytest.fixture
    def sample_session(self):
        """创建示例会话"""
        return ContextSession(
            name="Test Session",
            description="A test session",
            participants=["did:example:alice", "did:example:bob"]
        )
    
    @pytest.mark.asyncio
    async def test_save_and_get_memory(self, storage, sample_memory):
        """测试保存和获取记忆"""
        # 保存记忆
        success = await storage.save_memory(sample_memory)
        assert success
        
        # 获取记忆
        retrieved_memory = await storage.get_memory(sample_memory.id)
        assert retrieved_memory is not None
        assert retrieved_memory.id == sample_memory.id
        assert retrieved_memory.title == sample_memory.title
        assert retrieved_memory.content == sample_memory.content
        
        # 测试访问计数更新
        original_count = sample_memory.metadata.access_count
        assert retrieved_memory.metadata.access_count == original_count + 1
        assert retrieved_memory.metadata.last_accessed is not None
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_memory(self, storage):
        """测试获取不存在的记忆"""
        memory = await storage.get_memory("nonexistent-id")
        assert memory is None
    
    @pytest.mark.asyncio
    async def test_update_memory(self, storage, sample_memory):
        """测试更新记忆"""
        # 先保存
        await storage.save_memory(sample_memory)
        
        # 修改内容
        sample_memory.title = "Updated Title"
        sample_memory.content["status"] = "updated"
        
        # 更新
        success = await storage.update_memory(sample_memory)
        assert success
        
        # 验证更新
        retrieved_memory = await storage.get_memory(sample_memory.id)
        assert retrieved_memory.title == "Updated Title"
        assert retrieved_memory.content["status"] == "updated"
    
    @pytest.mark.asyncio
    async def test_delete_memory(self, storage, sample_memory):
        """测试删除记忆"""
        # 先保存
        await storage.save_memory(sample_memory)
        
        # 确认存在
        memory = await storage.get_memory(sample_memory.id)
        assert memory is not None
        
        # 删除
        success = await storage.delete_memory(sample_memory.id)
        assert success
        
        # 确认已删除
        memory = await storage.get_memory(sample_memory.id)
        assert memory is None
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_memory(self, storage):
        """测试删除不存在的记忆"""
        success = await storage.delete_memory("nonexistent-id")
        assert not success
    
    @pytest.mark.asyncio
    async def test_search_memories_by_type(self, storage):
        """测试按类型搜索记忆"""
        # 创建不同类型的记忆
        method_memory = MemoryEntry(
            memory_type=MemoryType.METHOD_CALL,
            title="Method Call",
            metadata=MemoryMetadata("alice", "Alice")
        )
        error_memory = MemoryEntry(
            memory_type=MemoryType.ERROR,
            title="Error Memory",
            metadata=MemoryMetadata("alice", "Alice")
        )
        
        await storage.save_memory(method_memory)
        await storage.save_memory(error_memory)
        
        # 搜索方法调用记忆
        method_results = await storage.search_memories(
            memory_type=MemoryType.METHOD_CALL
        )
        assert len(method_results) == 1
        assert method_results[0].memory_type == MemoryType.METHOD_CALL
        
        # 搜索错误记忆
        error_results = await storage.search_memories(
            memory_type=MemoryType.ERROR
        )
        assert len(error_results) == 1
        assert error_results[0].memory_type == MemoryType.ERROR
    
    @pytest.mark.asyncio
    async def test_search_memories_by_query(self, storage):
        """测试按查询内容搜索记忆"""
        # 创建包含不同内容的记忆
        memory1 = MemoryEntry(
            title="Database Operations",
            content={"operation": "insert", "table": "users"},
            metadata=MemoryMetadata("alice", "Alice")
        )
        memory2 = MemoryEntry(
            title="File Processing",
            content={"operation": "read", "file": "data.txt"},
            metadata=MemoryMetadata("alice", "Alice")
        )
        
        await storage.save_memory(memory1)
        await storage.save_memory(memory2)
        
        # 搜索包含"Database"的记忆
        results = await storage.search_memories(query="Database")
        assert len(results) == 1
        assert "Database" in results[0].title
        
        # 搜索包含"operation"的记忆
        results = await storage.search_memories(query="operation")
        assert len(results) == 2  # 两个记忆的content中都包含"operation"
    
    @pytest.mark.asyncio
    async def test_search_memories_by_agent(self, storage):
        """测试按Agent搜索记忆"""
        # 创建不同Agent的记忆
        alice_memory = MemoryEntry(
            title="Alice Memory",
            metadata=MemoryMetadata("did:example:alice", "Alice")
        )
        bob_memory = MemoryEntry(
            title="Bob Memory",
            metadata=MemoryMetadata("did:example:bob", "Bob")
        )
        
        await storage.save_memory(alice_memory)
        await storage.save_memory(bob_memory)
        
        # 搜索Alice的记忆
        alice_results = await storage.search_memories(agent_did="did:example:alice")
        assert len(alice_results) == 1
        assert alice_results[0].metadata.source_agent_did == "did:example:alice"
        
        # 搜索Bob的记忆
        bob_results = await storage.search_memories(agent_did="did:example:bob")
        assert len(bob_results) == 1
        assert bob_results[0].metadata.source_agent_did == "did:example:bob"
    
    @pytest.mark.asyncio
    async def test_search_memories_by_session(self, storage):
        """测试按会话搜索记忆"""
        # 创建不同会话的记忆
        session1_memory = MemoryEntry(
            title="Session 1 Memory",
            metadata=MemoryMetadata("alice", "Alice", session_id="session-1")
        )
        session2_memory = MemoryEntry(
            title="Session 2 Memory", 
            metadata=MemoryMetadata("alice", "Alice", session_id="session-2")
        )
        
        await storage.save_memory(session1_memory)
        await storage.save_memory(session2_memory)
        
        # 搜索session-1的记忆
        results = await storage.search_memories(session_id="session-1")
        assert len(results) == 1
        assert results[0].metadata.session_id == "session-1"
    
    @pytest.mark.asyncio
    async def test_search_memories_by_tags(self, storage):
        """测试按标签搜索记忆"""
        memory1 = MemoryEntry(
            title="Tagged Memory 1",
            metadata=MemoryMetadata("alice", "Alice", tags=["important", "test"])
        )
        memory2 = MemoryEntry(
            title="Tagged Memory 2",
            metadata=MemoryMetadata("alice", "Alice", tags=["test", "debug"])
        )
        memory3 = MemoryEntry(
            title="Untagged Memory",
            metadata=MemoryMetadata("alice", "Alice", tags=["other"])
        )
        
        await storage.save_memory(memory1)
        await storage.save_memory(memory2)
        await storage.save_memory(memory3)
        
        # 搜索包含"test"标签的记忆
        results = await storage.search_memories(tags=["test"])
        assert len(results) == 2
        
        # 搜索包含"important"标签的记忆
        results = await storage.search_memories(tags=["important"])
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_search_memories_by_keywords(self, storage):
        """测试按关键词搜索记忆"""
        memory1 = MemoryEntry(
            title="Keyword Memory 1",
            metadata=MemoryMetadata("alice", "Alice", keywords=["database", "query"])
        )
        memory2 = MemoryEntry(
            title="Keyword Memory 2",
            metadata=MemoryMetadata("alice", "Alice", keywords=["query", "optimization"])
        )
        
        await storage.save_memory(memory1)
        await storage.save_memory(memory2)
        
        # 搜索包含"query"关键词的记忆
        results = await storage.search_memories(keywords=["query"])
        assert len(results) == 2
        
        # 搜索包含"database"关键词的记忆
        results = await storage.search_memories(keywords=["database"])
        assert len(results) == 1
    
    @pytest.mark.asyncio
    async def test_search_memories_with_limit_offset(self, storage):
        """测试搜索记忆的分页功能"""
        # 创建多个记忆
        for i in range(10):
            memory = MemoryEntry(
                title=f"Memory {i}",
                metadata=MemoryMetadata("alice", "Alice")
            )
            await storage.save_memory(memory)
        
        # 测试限制数量
        results = await storage.search_memories(limit=5)
        assert len(results) == 5
        
        # 测试偏移
        results = await storage.search_memories(limit=3, offset=5)
        assert len(results) == 3
        
        # 测试超出范围的偏移
        results = await storage.search_memories(limit=5, offset=15)
        assert len(results) == 0
    
    @pytest.mark.asyncio
    async def test_get_memories_by_session(self, storage):
        """测试根据会话ID获取记忆"""
        session_id = "test-session-123"
        
        # 创建属于该会话的记忆
        for i in range(3):
            memory = MemoryEntry(
                title=f"Session Memory {i}",
                metadata=MemoryMetadata("alice", "Alice", session_id=session_id)
            )
            await storage.save_memory(memory)
        
        # 创建不属于该会话的记忆
        other_memory = MemoryEntry(
            title="Other Memory",
            metadata=MemoryMetadata("alice", "Alice", session_id="other-session")
        )
        await storage.save_memory(other_memory)
        
        # 获取会话记忆
        session_memories = await storage.get_memories_by_session(session_id)
        assert len(session_memories) == 3
        for memory in session_memories:
            assert memory.metadata.session_id == session_id
    
    @pytest.mark.asyncio
    async def test_save_and_get_session(self, storage, sample_session):
        """测试保存和获取会话"""
        # 保存会话
        success = await storage.save_session(sample_session)
        assert success
        
        # 获取会话
        retrieved_session = await storage.get_session(sample_session.id)
        assert retrieved_session is not None
        assert retrieved_session.id == sample_session.id
        assert retrieved_session.name == sample_session.name
        assert retrieved_session.participants == sample_session.participants
    
    @pytest.mark.asyncio
    async def test_update_session(self, storage, sample_session):
        """测试更新会话"""
        # 先保存
        await storage.save_session(sample_session)
        
        # 修改会话
        sample_session.name = "Updated Session"
        sample_session.add_participant("did:example:charlie")
        
        # 更新
        success = await storage.update_session(sample_session)
        assert success
        
        # 验证更新
        retrieved_session = await storage.get_session(sample_session.id)
        assert retrieved_session.name == "Updated Session"
        assert "did:example:charlie" in retrieved_session.participants
    
    @pytest.mark.asyncio
    async def test_delete_session(self, storage, sample_session):
        """测试删除会话"""
        # 先保存
        await storage.save_session(sample_session)
        
        # 确认存在
        session = await storage.get_session(sample_session.id)
        assert session is not None
        
        # 删除
        success = await storage.delete_session(sample_session.id)
        assert success
        
        # 确认已删除
        session = await storage.get_session(sample_session.id)
        assert session is None
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_memories(self, storage):
        """测试清理过期记忆"""
        # 创建已过期的记忆
        expired_memory = MemoryEntry(
            title="Expired Memory",
            metadata=MemoryMetadata(
                "alice", "Alice",
                expiry_time=datetime.now() - timedelta(hours=1)
            )
        )
        
        # 创建未过期的记忆
        valid_memory = MemoryEntry(
            title="Valid Memory",
            metadata=MemoryMetadata(
                "alice", "Alice",
                expiry_time=datetime.now() + timedelta(hours=1)
            )
        )
        
        # 创建无过期时间的记忆
        permanent_memory = MemoryEntry(
            title="Permanent Memory",
            metadata=MemoryMetadata("alice", "Alice")
        )
        
        await storage.save_memory(expired_memory)
        await storage.save_memory(valid_memory)
        await storage.save_memory(permanent_memory)
        
        # 执行清理
        cleaned_count = await storage.cleanup_expired_memories()
        assert cleaned_count == 1
        
        # 验证只有过期的记忆被删除
        assert await storage.get_memory(expired_memory.id) is None
        assert await storage.get_memory(valid_memory.id) is not None
        assert await storage.get_memory(permanent_memory.id) is not None
    
    @pytest.mark.asyncio
    async def test_get_storage_stats(self, storage):
        """测试获取存储统计信息"""
        # 创建一些测试数据
        for i in range(5):
            memory = MemoryEntry(
                memory_type=MemoryType.METHOD_CALL if i % 2 == 0 else MemoryType.ERROR,
                title=f"Memory {i}",
                metadata=MemoryMetadata("alice", "Alice")
            )
            await storage.save_memory(memory)
        
        for i in range(3):
            session = ContextSession(
                name=f"Session {i}",
                is_active=i < 2
            )
            await storage.save_session(session)
        
        # 获取统计信息
        stats = await storage.get_storage_stats()
        
        assert stats["storage_type"] == "memory"
        assert stats["total_memories"] == 5
        assert stats["total_sessions"] == 3
        assert stats["active_sessions"] == 2
        assert "memory_types" in stats
        assert stats["memory_types"]["method_call"] == 3
        assert stats["memory_types"]["error"] == 2


class TestSQLiteMemoryStorage:
    """测试SQLite存储实现"""
    
    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库文件路径"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        yield temp_path
        # 清理
        Path(temp_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def storage_config(self, temp_db_path):
        """创建存储配置"""
        return MemoryConfig(
            storage=StorageConfig(
                storage_type="sqlite",
                database_path=temp_db_path,
                cache_size=10
            ),
            performance=PerformanceConfig(
                enable_async_operations=False  # 简化测试
            )
        )
    
    @pytest.fixture
    def storage(self, storage_config):
        """创建SQLite存储实例"""
        storage = SQLiteMemoryStorage(storage_config)
        yield storage
        storage.close()
    
    @pytest.fixture
    def sample_memory(self):
        """创建示例记忆条目"""
        metadata = MemoryMetadata(
            source_agent_did="did:example:alice",
            source_agent_name="Alice Agent",
            session_id="session-123",
            tags=["test", "sample"],
            keywords=["memory", "test"],
            relevance_score=0.8,
            access_count=5
        )
        return MemoryEntry(
            memory_type=MemoryType.METHOD_CALL,
            title="SQLite Test Memory",
            content={"method": "sqlite_test", "params": {"id": 123}},
            metadata=metadata
        )
    
    def test_database_initialization(self, storage, temp_db_path):
        """测试数据库初始化"""
        # 验证数据库文件已创建
        assert Path(temp_db_path).exists()
        
        # 验证表结构
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        
        # 检查memory_entries表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='memory_entries'")
        assert cursor.fetchone() is not None
        
        # 检查context_sessions表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='context_sessions'")
        assert cursor.fetchone() is not None
        
        # 检查索引
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = [row[0] for row in cursor.fetchall()]
        assert any("idx_memory_type" in idx for idx in indices)
        assert any("idx_source_agent" in idx for idx in indices)
        
        conn.close()
    
    @pytest.mark.asyncio
    async def test_save_and_get_memory_sqlite(self, storage, sample_memory):
        """测试SQLite保存和获取记忆"""
        # 保存记忆
        success = await storage.save_memory(sample_memory)
        assert success
        
        # 获取记忆
        retrieved_memory = await storage.get_memory(sample_memory.id)
        assert retrieved_memory is not None
        assert retrieved_memory.id == sample_memory.id
        assert retrieved_memory.title == sample_memory.title
        assert retrieved_memory.content == sample_memory.content
        assert retrieved_memory.metadata.source_agent_did == sample_memory.metadata.source_agent_did
        assert retrieved_memory.metadata.tags == sample_memory.metadata.tags
        assert retrieved_memory.metadata.keywords == sample_memory.metadata.keywords
    
    @pytest.mark.asyncio
    async def test_sqlite_search_performance(self, storage):
        """测试SQLite搜索性能"""
        # 创建大量记忆条目
        start_time = time.time()
        
        memories = []
        for i in range(100):
            memory = MemoryEntry(
                title=f"Performance Test {i}",
                content={"index": i, "data": f"test_data_{i}"},
                metadata=MemoryMetadata(
                    source_agent_did=f"did:example:agent_{i % 10}",
                    source_agent_name=f"Agent {i % 10}",
                    tags=[f"tag_{i % 5}", "performance"],
                    keywords=[f"keyword_{i % 3}", "test"]
                )
            )
            memories.append(memory)
            await storage.save_memory(memory)
        
        creation_time = time.time() - start_time
        assert creation_time < 10.0  # 创建100个记忆应该在10秒内完成
        
        # 测试搜索性能
        start_time = time.time()
        results = await storage.search_memories(tags=["performance"])
        search_time = time.time() - start_time
        
        assert len(results) == 100
        assert search_time < 1.0  # 搜索应该很快
    
    @pytest.mark.asyncio
    async def test_sqlite_concurrent_access(self, storage):
        """测试SQLite并发访问"""
        async def create_memories(start_index, count):
            memories = []
            for i in range(start_index, start_index + count):
                memory = MemoryEntry(
                    title=f"Concurrent Memory {i}",
                    metadata=MemoryMetadata(f"agent_{i}", f"Agent {i}")
                )
                await storage.save_memory(memory)
                memories.append(memory)
            return memories
        
        # 并发创建记忆
        tasks = [
            create_memories(0, 10),
            create_memories(10, 10),
            create_memories(20, 10)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 验证所有记忆都被正确保存
        total_memories = sum(len(batch) for batch in results)
        assert total_memories == 30
        
        # 验证可以检索所有记忆
        all_memories = await storage.search_memories(limit=50)
        assert len(all_memories) == 30
    
    @pytest.mark.asyncio
    async def test_sqlite_cache_mechanism(self, storage):
        """测试SQLite缓存机制"""
        memory = MemoryEntry(
            title="Cache Test Memory",
            metadata=MemoryMetadata("alice", "Alice")
        )
        
        # 保存记忆
        await storage.save_memory(memory)
        
        # 第一次获取（从数据库）
        retrieved1 = await storage.get_memory(memory.id)
        assert retrieved1 is not None
        
        # 第二次获取（应该从缓存）
        retrieved2 = await storage.get_memory(memory.id)
        assert retrieved2 is not None
        
        # 验证缓存工作（通过检查访问次数）
        assert retrieved2.metadata.access_count > retrieved1.metadata.access_count
    
    @pytest.mark.asyncio
    async def test_sqlite_error_handling(self, storage):
        """测试SQLite错误处理"""
        # 测试保存无效数据
        invalid_memory = MemoryEntry()
        invalid_memory.id = None  # 无效ID
        
        # 应该优雅地处理错误
        success = await storage.save_memory(invalid_memory)
        # 根据实现，这可能成功（生成新ID）或失败
        
        # 测试获取使用无效ID
        result = await storage.get_memory("")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_sqlite_data_persistence(self, storage_config, temp_db_path):
        """测试SQLite数据持久化"""
        # 创建第一个存储实例并保存数据
        storage1 = SQLiteMemoryStorage(storage_config)
        
        memory = MemoryEntry(
            title="Persistence Test",
            metadata=MemoryMetadata("alice", "Alice")
        )
        
        await storage1.save_memory(memory)
        storage1.close()
        
        # 创建第二个存储实例
        storage2 = SQLiteMemoryStorage(storage_config)
        
        # 验证数据仍然存在
        retrieved_memory = await storage2.get_memory(memory.id)
        assert retrieved_memory is not None
        assert retrieved_memory.title == "Persistence Test"
        
        storage2.close()
    
    @pytest.mark.asyncio
    async def test_sqlite_complex_queries(self, storage):
        """测试SQLite复杂查询"""
        # 创建复杂的测试数据
        memories = []
        for i in range(20):
            memory_type = MemoryType.METHOD_CALL if i % 2 == 0 else MemoryType.ERROR
            agent_did = f"did:example:agent_{i % 3}"
            session_id = f"session_{i % 4}" if i % 5 != 0 else None
            
            memory = MemoryEntry(
                title=f"Complex Query Test {i}",
                memory_type=memory_type,
                content={"index": i, "category": f"cat_{i % 3}"},
                metadata=MemoryMetadata(
                    source_agent_did=agent_did,
                    source_agent_name=f"Agent {i % 3}",
                    session_id=session_id,
                    tags=[f"tag_{i % 4}", "complex"],
                    keywords=[f"kw_{i % 5}", "query"]
                )
            )
            await storage.save_memory(memory)
            memories.append(memory)
        
        # 测试复合条件查询
        results = await storage.search_memories(
            memory_type=MemoryType.METHOD_CALL,
            agent_did="did:example:agent_0",
            tags=["complex"],
            limit=10
        )
        
        # 验证结果符合所有条件
        for result in results:
            assert result.memory_type == MemoryType.METHOD_CALL
            assert result.metadata.source_agent_did == "did:example:agent_0"
            assert "complex" in result.metadata.tags
        
        # 测试关键词搜索
        keyword_results = await storage.search_memories(
            keywords=["query"],
            limit=25
        )
        assert len(keyword_results) == 20  # 所有记忆都有"query"关键词


class TestStorageFactory:
    """测试存储工厂函数"""
    
    def test_create_memory_storage(self):
        """测试创建内存存储"""
        config = MemoryConfig(
            storage=StorageConfig(storage_type="memory")
        )
        
        storage = create_storage(config)
        assert isinstance(storage, InMemoryStorage)
    
    def test_create_sqlite_storage(self):
        """测试创建SQLite存储"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        
        try:
            config = MemoryConfig(
                storage=StorageConfig(
                    storage_type="sqlite",
                    database_path=temp_path
                )
            )
            
            storage = create_storage(config)
            assert isinstance(storage, SQLiteMemoryStorage)
            
            storage.close()
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_create_storage_invalid_type(self):
        """测试创建无效类型的存储"""
        config = MemoryConfig(
            storage=StorageConfig(storage_type="invalid_type")
        )
        
        with pytest.raises(ValueError, match="不支持的存储类型"):
            create_storage(config)
    
    def test_create_storage_with_none_config(self):
        """测试使用None配置创建存储"""
        with patch('anp_runtime.local_service.memory.memory_storage.get_memory_config') as mock_get_config:
            mock_config = MemoryConfig(
                storage=StorageConfig(storage_type="memory")
            )
            mock_get_config.return_value = mock_config
            
            storage = create_storage(None)
            assert isinstance(storage, InMemoryStorage)
            mock_get_config.assert_called_once()


class TestStorageIntegration:
    """测试存储集成场景"""
    
    @pytest.mark.asyncio
    async def test_memory_and_session_integration(self):
        """测试记忆和会话的集成"""
        storage = InMemoryStorage()
        
        # 创建会话
        session = ContextSession(
            name="Integration Test Session",
            participants=["alice", "bob"]
        )
        await storage.save_session(session)
        
        # 创建属于该会话的记忆
        memory = MemoryEntry(
            title="Session Memory",
            metadata=MemoryMetadata(
                source_agent_did="alice",
                source_agent_name="Alice",
                session_id=session.id
            )
        )
        await storage.save_memory(memory)
        
        # 更新会话的记忆列表
        session.add_memory(memory.id)
        await storage.update_session(session)
        
        # 验证集成
        retrieved_session = await storage.get_session(session.id)
        assert memory.id in retrieved_session.memory_entries
        
        session_memories = await storage.get_memories_by_session(session.id)
        assert len(session_memories) == 1
        assert session_memories[0].id == memory.id
    
    @pytest.mark.asyncio
    async def test_cross_storage_type_compatibility(self):
        """测试不同存储类型间的数据兼容性"""
        # 创建记忆条目
        memory = MemoryEntry(
            title="Cross Storage Test",
            content={"test": "data", "number": 42},
            metadata=MemoryMetadata(
                source_agent_did="did:example:test",
                source_agent_name="Test Agent",
                tags=["cross", "storage"],
                keywords=["test", "compatibility"]
            )
        )
        
        # 在内存存储中保存
        memory_storage = InMemoryStorage()
        await memory_storage.save_memory(memory)
        
        # 序列化数据
        memory_data = memory.to_dict()
        
        # 在另一个内存存储中恢复
        memory_storage2 = InMemoryStorage()
        restored_memory = MemoryEntry.from_dict(memory_data)
        await memory_storage2.save_memory(restored_memory)
        
        # 验证数据一致性
        retrieved_memory = await memory_storage2.get_memory(restored_memory.id)
        assert retrieved_memory.title == memory.title
        assert retrieved_memory.content == memory.content
        assert retrieved_memory.metadata.source_agent_did == memory.metadata.source_agent_did
        assert retrieved_memory.metadata.tags == memory.metadata.tags
        assert retrieved_memory.metadata.keywords == memory.metadata.keywords


if __name__ == "__main__":
    pytest.main([__file__])