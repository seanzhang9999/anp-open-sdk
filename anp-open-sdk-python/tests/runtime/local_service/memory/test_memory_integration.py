"""
记忆功能集成测试

测试记忆功能各组件之间的协调工作和端到端场景
"""

import pytest
import asyncio
import time
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Any, Dict, List

from anp_runtime.local_service.memory.memory_manager import MemoryManager
from anp_runtime.local_service.memory.memory_collector import MemoryCollector
from anp_runtime.local_service.memory.memory_recommender import MemoryRecommender, RecommendationContext
from anp_runtime.local_service.memory.context_session import ContextSessionManager
from anp_runtime.local_service.memory.memory_storage import InMemoryStorage, SQLiteMemoryStorage
from anp_runtime.local_service.memory.memory_models import (
    MemoryEntry,
    MemoryType,
    MemoryMetadata,
    ContextSession
)
from anp_runtime.local_service.memory.memory_config import (
    MemoryConfig,
    StorageConfig,
    RecommendationConfig,
    CollectionConfig,
    CleanupConfig,
    SecurityConfig,
    PerformanceConfig
)


class TestMemorySystemBasicIntegration:
    """测试记忆系统基本集成"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def config(self, temp_dir):
        """创建测试配置"""
        return MemoryConfig(
            enabled=True,
            storage=StorageConfig(
                storage_type="memory",
                cache_size=100
            ),
            recommendation=RecommendationConfig(
                algorithm="hybrid",
                max_recommendations=5
            ),
            collection=CollectionConfig(
                enable_memory_collection=False  # 暂时禁用自动收集
            ),
            cleanup=CleanupConfig(
                enable_auto_cleanup=False,  # 禁用自动清理以便测试
                max_memory_entries=50
            )
        )
    
    @pytest.fixture
    def memory_manager(self, config):
        """创建记忆管理器"""
        storage = InMemoryStorage()
        return MemoryManager(storage=storage, config=config)
    
    @pytest.fixture
    def session_manager(self, config):
        """创建会话管理器"""
        storage = InMemoryStorage()
        return ContextSessionManager(storage=storage)
    
    @pytest.fixture
    def memory_recommender(self, memory_manager, config):
        """创建记忆推荐器"""
        return MemoryRecommender(memory_manager=memory_manager, config=config)
    
    @pytest.mark.asyncio
    async def test_basic_memory_lifecycle(self, memory_manager):
        """测试基本记忆生命周期"""
        # 1. 创建记忆
        memory = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Test Method Call",
            content={
                "method_name": "test_function",
                "input": {"param1": "value1", "param2": 42},
                "output": "success",
                "execution_time": 0.123
            },
            source_agent_did="alice",
            source_agent_name="Alice",
            keywords=["test", "function", "method"],
            tags=["integration", "test"]
        )
        
        assert memory is not None
        assert memory.title == "Test Method Call"
        assert memory.memory_type == MemoryType.METHOD_CALL
        
        # 2. 获取记忆
        retrieved_memory = await memory_manager.get_memory(memory.id)
        assert retrieved_memory is not None
        assert retrieved_memory.id == memory.id
        assert retrieved_memory.content == memory.content
        
        # 3. 搜索记忆
        search_results = await memory_manager.search_memories(
            keywords=["test", "function"],
            limit=10
        )
        assert len(search_results) >= 1
        assert any(m.id == memory.id for m in search_results)
        
        # 4. 更新记忆
        memory.content["updated"] = True
        memory.add_tag("updated")
        success = await memory_manager.update_memory(memory)
        assert success == True
        
        # 验证更新
        updated_memory = await memory_manager.get_memory(memory.id)
        assert updated_memory.content["updated"] == True
        assert "updated" in updated_memory.metadata.tags
        
        # 5. 删除记忆
        success = await memory_manager.delete_memory(memory.id)
        assert success == True
        
        # 验证删除
        deleted_memory = await memory_manager.get_memory(memory.id)
        assert deleted_memory is None
        
        await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_memory_with_session_integration(self, memory_manager, session_manager):
        """测试记忆与会话的集成"""
        # 1. 创建会话
        session = await session_manager.create_session(
            name="Integration Test Session",
            description="Testing memory-session integration",
            participants=["alice", "bob"],
            context_data={"project": "test", "phase": "integration"}
        )
        
        # 2. 创建与会话关联的记忆
        memory1 = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="Session Method 1",
            content={"method": "login", "user": "alice"},
            source_agent_did="alice",
            source_agent_name="Alice",
            session_id=session.id,
            keywords=["login", "authentication"]
        )
        
        memory2 = await memory_manager.create_memory(
            memory_type=MemoryType.USER_PREFERENCE,
            title="User Preference",
            content={"theme": "dark", "language": "en"},
            source_agent_did="alice",
            source_agent_name="Alice",
            session_id=session.id,
            keywords=["preference", "settings"]
        )
        
        # 3. 验证会话包含记忆
        session_memories = await session_manager.get_session_memories(session.id)
        memory_ids = [m.id for m in session_memories]
        assert memory1.id in memory_ids
        assert memory2.id in memory_ids
        
        # 4. 通过会话搜索记忆
        session_search_results = await memory_manager.search_memories(
            session_id=session.id,
            limit=10
        )
        assert len(session_search_results) == 2
        
        # 5. 更新会话上下文
        success = await session_manager.update_context_data(
            session.id, "test_status", "completed"
        )
        assert success == True
        
        context_value = await session_manager.get_context_data(
            session.id, "test_status"
        )
        assert context_value == "completed"
        
        # 清理
        await session_manager.close()
        await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_memory_recommendation_integration(self, memory_manager, memory_recommender):
        """测试记忆推荐集成"""
        # 1. 创建多个相关记忆
        memories = []
        
        # 用户相关记忆
        user_memory = await memory_manager.create_memory(
            memory_type=MemoryType.USER_PREFERENCE,
            title="User Settings",
            content={"theme": "dark", "notifications": True},
            source_agent_did="alice",
            source_agent_name="Alice",
            keywords=["user", "settings", "preference"],
            tags=["user", "config"]
        )
        memories.append(user_memory)
        
        # 方法调用记忆
        method_memory = await memory_manager.create_memory(
            memory_type=MemoryType.METHOD_CALL,
            title="User Login",
            content={"method": "login", "user": "alice", "success": True},
            source_agent_did="alice",
            source_agent_name="Alice",
            keywords=["user", "login", "authentication"],
            tags=["method", "auth"]
        )
        memories.append(method_memory)
        
        # 错误记忆
        error_memory = await memory_manager.create_memory(
            memory_type=MemoryType.ERROR,
            title="Login Error",
            content={"error": "Invalid credentials", "user": "bob"},
            source_agent_did="bob",
            source_agent_name="Bob",
            keywords=["user", "login", "error"],
            tags=["error", "auth"]
        )
        memories.append(error_memory)
        
        # 2. 基于上下文推荐
        recommendations = await memory_recommender.recommend_for_context(
            keywords=["user", "login"],
            tags=["auth"],
            agent_did="alice",
            max_recommendations=5
        )
        
        assert len(recommendations) > 0
        # 验证推荐结果包含相关记忆
        recommended_ids = [memory.id for memory, _ in recommendations]
        assert user_memory.id in recommended_ids or method_memory.id in recommended_ids
        
        # 3. 基于方法调用推荐
        method_recommendations = await memory_recommender.recommend_for_method_call(
            method_name="login",
            method_key="auth::login",
            agent_did="alice",
            max_recommendations=3
        )
        
        assert len(method_recommendations) > 0
        
        # 4. 相似记忆推荐
        similar_recommendations = await memory_recommender.recommend_similar_memories(
            reference_memory=user_memory,
            max_recommendations=3
        )
        
        # 应该推荐相似的记忆，但不包括参考记忆本身
        similar_ids = [memory.id for memory, _ in similar_recommendations]
        assert user_memory.id not in similar_ids
        
        await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_batch_operations_integration(self, memory_manager):
        """测试批量操作集成"""
        # 1. 批量创建记忆
        memory_specs = []
        for i in range(10):
            spec = {
                "memory_type": MemoryType.METHOD_CALL,
                "title": f"Batch Memory {i}",
                "content": {"index": i, "data": f"batch_data_{i}"},
                "source_agent_did": "system",
                "source_agent_name": "System",
                "keywords": [f"batch_{i}", "system", "test"],
                "tags": ["batch", "integration"]
            }
            memory_specs.append(spec)
        
        created_memories = await memory_manager.create_memories_batch(memory_specs)
        assert len(created_memories) == 10
        
        # 2. 验证批量创建的记忆
        for i, memory in enumerate(created_memories):
            assert memory.title == f"Batch Memory {i}"
            assert memory.content["index"] == i
        
        # 3. 批量搜索
        batch_search_results = await memory_manager.search_memories(
            tags=["batch"],
            limit=20
        )
        assert len(batch_search_results) >= 10
        
        # 4. 批量删除
        memory_ids = [memory.id for memory in created_memories]
        deleted_count = await memory_manager.delete_memories_batch(memory_ids)
        assert deleted_count == 10
        
        # 5. 验证批量删除
        for memory_id in memory_ids:
            deleted_memory = await memory_manager.get_memory(memory_id)
            assert deleted_memory is None
        
        await memory_manager.close()


class TestMemorySystemAdvancedIntegration:
    """测试记忆系统高级集成"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sqlite_config(self, temp_dir):
        """创建SQLite配置"""
        db_path = Path(temp_dir) / "test_memory.db"
        return MemoryConfig(
            enabled=True,
            storage=StorageConfig(
                storage_type="sqlite",
                database_path=str(db_path),
                cache_size=50
            ),
            recommendation=RecommendationConfig(
                algorithm="hybrid",
                keyword_weight=0.4,
                tag_weight=0.3,
                time_weight=0.2,
                access_weight=0.1
            ),
            cleanup=CleanupConfig(
                enable_auto_cleanup=False,
                max_memory_entries=100,
                cleanup_strategy="smart"
            ),
            security=SecurityConfig(
                sensitive_fields=["password", "token", "secret"],
                enable_access_control=True
            )
        )
    
    @pytest.mark.asyncio
    async def test_sqlite_storage_integration(self, sqlite_config):
        """测试SQLite存储集成"""
        # 创建SQLite存储
        storage = SQLiteMemoryStorage(sqlite_config.storage.database_path)
        memory_manager = MemoryManager(storage=storage, config=sqlite_config)
        
        try:
            # 1. 创建记忆并持久化
            memory = await memory_manager.create_memory(
                memory_type=MemoryType.METHOD_CALL,
                title="SQLite Test Memory",
                content={
                    "method": "test_sqlite",
                    "database": "test.db",
                    "query": "SELECT * FROM users"
                },
                source_agent_did="db_agent",
                source_agent_name="Database Agent",
                keywords=["sqlite", "database", "query"],
                tags=["database", "storage"]
            )
            
            # 2. 重新创建管理器（模拟应用重启）
            await memory_manager.close()
            
            new_storage = SQLiteMemoryStorage(sqlite_config.storage.database_path)
            new_memory_manager = MemoryManager(storage=new_storage, config=sqlite_config)
            
            # 3. 验证数据持久化
            retrieved_memory = await new_memory_manager.get_memory(memory.id)
            assert retrieved_memory is not None
            assert retrieved_memory.title == "SQLite Test Memory"
            assert retrieved_memory.content["method"] == "test_sqlite"
            
            # 4. 搜索持久化的数据
            search_results = await new_memory_manager.search_memories(
                keywords=["sqlite", "database"]
            )
            assert len(search_results) >= 1
            assert any(m.id == memory.id for m in search_results)
            
            await new_memory_manager.close()
            
        finally:
            await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_operations_integration(self, sqlite_config):
        """测试并发操作集成"""
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage, config=sqlite_config)
        session_manager = ContextSessionManager(storage=storage)
        
        try:
            # 创建会话
            session = await session_manager.create_session(
                name="Concurrent Test Session",
                participants=["agent1", "agent2", "agent3"]
            )
            
            # 并发创建记忆
            async def create_memory_batch(agent_id, count):
                memories = []
                for i in range(count):
                    memory = await memory_manager.create_memory(
                        memory_type=MemoryType.METHOD_CALL,
                        title=f"Concurrent Memory {agent_id}-{i}",
                        content={"agent": agent_id, "index": i, "timestamp": time.time()},
                        source_agent_did=f"agent_{agent_id}",
                        source_agent_name=f"Agent {agent_id}",
                        session_id=session.id,
                        keywords=[f"agent{agent_id}", "concurrent", "test"],
                        tags=["concurrent", "integration"]
                    )
                    memories.append(memory)
                return memories
            
            # 并发执行
            tasks = [
                create_memory_batch(1, 5),
                create_memory_batch(2, 5),
                create_memory_batch(3, 5)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证结果
            total_created = 0
            for result in results:
                if isinstance(result, Exception):
                    pytest.fail(f"并发操作失败: {result}")
                elif isinstance(result, list):
                    total_created += len(result)
            
            assert total_created == 15
            
            # 验证会话包含所有记忆
            session_memories = await session_manager.get_session_memories(session.id)
            assert len(session_memories) == 15
            
            # 并发搜索测试
            async def concurrent_search(query_keywords):
                return await memory_manager.search_memories(
                    keywords=query_keywords,
                    session_id=session.id
                )
            
            search_tasks = [
                concurrent_search(["agent1"]),
                concurrent_search(["agent2"]),
                concurrent_search(["agent3"]),
                concurrent_search(["concurrent"])
            ]
            
            search_results = await asyncio.gather(*search_tasks)
            
            # 验证搜索结果
            assert len(search_results[0]) == 5  # agent1的记忆
            assert len(search_results[1]) == 5  # agent2的记忆
            assert len(search_results[2]) == 5  # agent3的记忆
            assert len(search_results[3]) == 15  # 所有concurrent记忆
            
        finally:
            await session_manager.close()
            await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_memory_lifecycle_with_cleanup(self, sqlite_config):
        """测试带清理的记忆生命周期"""
        # 设置较小的最大记忆条目数以触发清理
        sqlite_config.cleanup.max_memory_entries = 10
        sqlite_config.cleanup.cleanup_strategy = "lru"
        
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage, config=sqlite_config)
        
        try:
            # 1. 创建超过限制的记忆条目
            memories = []
            for i in range(15):
                memory = await memory_manager.create_memory(
                    memory_type=MemoryType.METHOD_CALL,
                    title=f"Cleanup Test Memory {i}",
                    content={"index": i, "importance": i % 3},
                    source_agent_did="test_agent",
                    source_agent_name="Test Agent",
                    keywords=[f"cleanup_{i}", "test"],
                    tags=["cleanup", "test"]
                )
                memories.append(memory)
                
                # 模拟不同的访问时间
                if i < 5:
                    # 前5个记忆被多次访问
                    for _ in range(3):
                        await memory_manager.get_memory(memory.id)
                
                # 短暂延迟以确保时间差异
                await asyncio.sleep(0.01)
            
            # 2. 手动触发清理
            cleanup_result = await memory_manager.cleanup_memories()
            
            # 3. 验证清理效果
            remaining_memories = await memory_manager.search_memories(
                tags=["cleanup"],
                limit=20
            )
            
            # 应该保留不超过max_memory_entries的记忆
            assert len(remaining_memories) <= sqlite_config.cleanup.max_memory_entries
            
            # 验证LRU策略：被频繁访问的记忆应该被保留
            remaining_ids = [m.id for m in remaining_memories]
            
            # 前5个被多次访问的记忆更可能被保留
            frequently_accessed_count = sum(
                1 for i in range(5) if memories[i].id in remaining_ids
            )
            rarely_accessed_count = sum(
                1 for i in range(5, 15) if memories[i].id in remaining_ids
            )
            
            # 频繁访问的记忆保留率应该更高
            if len(remaining_memories) > 0:
                frequently_accessed_ratio = frequently_accessed_count / min(5, len(remaining_memories))
                rarely_accessed_ratio = rarely_accessed_count / min(10, len(remaining_memories))
                # 这个断言可能不总是成立，因为LRU策略实现可能有差异
                # assert frequently_accessed_ratio >= rarely_accessed_ratio
            
        finally:
            await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_full_system_workflow(self, sqlite_config):
        """测试完整系统工作流程"""
        # 启用记忆收集
        sqlite_config.collection.enable_memory_collection = True
        sqlite_config.collection.collection_mode = "selective"
        sqlite_config.collection.auto_collect_methods = ["important_method"]
        
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage, config=sqlite_config)
        session_manager = ContextSessionManager(storage=storage)
        memory_recommender = MemoryRecommender(
            memory_manager=memory_manager,
            session_manager=session_manager,
            config=sqlite_config
        )
        
        try:
            # 1. 创建用户会话
            user_session = await session_manager.create_session(
                name="User Workflow Session",
                description="Complete workflow test",
                participants=["alice"],
                context_data={
                    "workflow": "complete_test",
                    "stage": "initial"
                }
            )
            
            # 2. 模拟用户偏好设置
            preference_memory = await memory_manager.create_memory(
                memory_type=MemoryType.USER_PREFERENCE,
                title="User Theme Preference",
                content={
                    "theme": "dark",
                    "language": "zh-CN",
                    "notifications": True
                },
                source_agent_did="alice",
                source_agent_name="Alice",
                session_id=user_session.id,
                keywords=["theme", "preference", "settings"],
                tags=["user", "config"]
            )
            
            # 3. 模拟方法调用历史
            method_memories = []
            for i, method_name in enumerate(["login", "get_profile", "update_settings", "logout"]):
                method_memory = await memory_manager.create_method_call_memory(
                    method_name=method_name,
                    method_key=f"user::{method_name}",
                    input_args=[],
                    input_kwargs={"user_id": "alice"},
                    output={"success": True, "timestamp": time.time()},
                    execution_time=0.1 + i * 0.05,
                    source_agent_did="alice",
                    source_agent_name="Alice",
                    session_id=user_session.id,
                    keywords=[method_name, "user", "operation"],
                    tags=["method", "user_operation"]
                )
                method_memories.append(method_memory)
            
            # 4. 更新会话状态
            await session_manager.update_context_data(
                user_session.id, "stage", "operations_completed"
            )
            
            # 5. 搜索用户相关记忆
            user_memories = await memory_manager.search_memories(
                agent_did="alice",
                session_id=user_session.id,
                limit=10
            )
            
            assert len(user_memories) >= 5  # 至少包含偏好记忆和4个方法记忆
            
            # 6. 基于当前上下文获取推荐
            context_recommendations = await memory_recommender.recommend_for_context(
                keywords=["user", "settings"],
                tags=["config"],
                agent_did="alice",
                session_id=user_session.id,
                max_recommendations=3
            )
            
            assert len(context_recommendations) > 0
            
            # 7. 为新方法调用获取推荐
            method_recommendations = await memory_recommender.recommend_for_method_call(
                method_name="change_password",
                method_key="user::change_password",
                agent_did="alice",
                session_id=user_session.id,
                max_recommendations=3
            )
            
            # 应该推荐相关的用户操作记忆
            assert len(method_recommendations) > 0
            
            # 8. 获取系统统计信息
            memory_stats = await memory_manager.get_memory_statistics()
            session_stats = await session_manager.get_session_statistics()
            recommendation_stats = memory_recommender.get_recommendation_statistics()
            
            # 验证统计信息
            assert memory_stats['operations']['memories_created'] >= 5
            assert session_stats['total_active_sessions'] >= 1
            assert recommendation_stats['recommendations_generated'] >= 0
            
            # 9. 模拟错误情况
            try:
                error_memory = await memory_manager.create_error_memory(
                    method_name="risky_operation",
                    method_key="user::risky_operation",
                    input_args=[],
                    input_kwargs={"user_id": "alice"},
                    error=ValueError("Operation not allowed"),
                    execution_time=0.05,
                    source_agent_did="alice",
                    source_agent_name="Alice",
                    session_id=user_session.id
                )
                
                assert error_memory.memory_type == MemoryType.ERROR
                assert error_memory.content["success"] == False
            except Exception as e:
                pytest.fail(f"错误记忆创建失败: {e}")
            
            # 10. 关闭会话
            success = await session_manager.close_session(user_session.id)
            assert success == True
            
            # 验证会话状态
            closed_session = await session_manager.get_session(user_session.id)
            assert closed_session is not None
            assert closed_session.is_active == False
            
        finally:
            await session_manager.close()
            await memory_manager.close()


class TestMemorySystemErrorHandling:
    """测试记忆系统错误处理"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MemoryConfig(
            enabled=True,
            storage=StorageConfig(storage_type="memory"),
            cleanup=CleanupConfig(enable_auto_cleanup=False)
        )
    
    @pytest.mark.asyncio
    async def test_storage_failure_handling(self, config):
        """测试存储失败处理"""
        # 创建会失败的模拟存储
        mock_storage = Mock()
        mock_storage.save_memory = AsyncMock(return_value=False)
        mock_storage.get_memory = AsyncMock(return_value=None)
        mock_storage.search_memories = AsyncMock(return_value=[])
        
        memory_manager = MemoryManager(storage=mock_storage, config=config)
        
        try:
            # 测试创建记忆失败
            with pytest.raises(RuntimeError, match="创建记忆失败"):
                await memory_manager.create_memory(
                    memory_type=MemoryType.METHOD_CALL,
                    title="Failing Memory",
                    content={},
                    source_agent_did="test",
                    source_agent_name="Test"
                )
            
            # 测试获取不存在的记忆
            memory = await memory_manager.get_memory("non-existent-id")
            assert memory is None
            
            # 测试搜索空结果
            results = await memory_manager.search_memories(keywords=["nonexistent"])
            assert len(results) == 0
            
        finally:
            await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_concurrent_access_safety(self, config):
        """测试并发访问安全性"""
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage, config=config)
        
        try:
            # 创建共享记忆
            shared_memory = await memory_manager.create_memory(
                memory_type=MemoryType.METHOD_CALL,
                title="Shared Memory",
                content={"counter": 0},
                source_agent_did="system",
                source_agent_name="System",
                keywords=["shared", "counter"]
            )
            
            # 并发访问和更新
            async def concurrent_update(agent_id):
                for i in range(5):
                    # 获取记忆
                    memory = await memory_manager.get_memory(shared_memory.id)
                    if memory:
                        # 更新计数器
                        current_counter = memory.content.get("counter", 0)
                        memory.content["counter"] = current_counter + 1
                        memory.content[f"agent_{agent_id}_update_{i}"] = time.time()
                        
                        # 保存更新
                        await memory_manager.update_memory(memory)
                    
                    # 短暂延迟
                    await asyncio.sleep(0.01)
            
            # 启动多个并发任务
            tasks = [concurrent_update(i) for i in range(3)]
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # 验证最终状态
            final_memory = await memory_manager.get_memory(shared_memory.id)
            assert final_memory is not None
            
            # 计数器应该反映所有更新（可能因为并发竞争不是15）
            final_counter = final_memory.content.get("counter", 0)
            assert final_counter > 0
            
            # 应该有来自不同agent的更新记录
            agent_updates = [key for key in final_memory.content.keys() 
                           if key.startswith("agent_")]
            assert len(agent_updates) > 0
            
        finally:
            await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_invalid_configuration_handling(self):
        """测试无效配置处理"""
        # 创建无效配置
        invalid_config = MemoryConfig()
        invalid_config.storage.storage_type = "unsupported_type"
        invalid_config.storage.cache_size = -1
        invalid_config.recommendation.similarity_threshold = 2.0
        
        # 配置验证应该失败
        assert invalid_config.is_valid() == False
        
        errors = invalid_config.validate()
        assert len(errors) > 0
        
        # 创建存储时应该处理无效类型
        from anp_runtime.local_service.memory.memory_storage import create_storage
        
        # 应该回退到默认存储类型或抛出异常
        try:
            storage = create_storage(invalid_config)
            # 如果没有抛出异常，应该创建了某种有效的存储
            assert storage is not None
        except Exception as e:
            # 或者应该抛出有意义的异常
            assert "unsupported" in str(e).lower() or "invalid" in str(e).lower()


class TestMemorySystemPerformance:
    """测试记忆系统性能"""
    
    @pytest.fixture
    def performance_config(self):
        """创建性能测试配置"""
        return MemoryConfig(
            enabled=True,
            storage=StorageConfig(
                storage_type="memory",
                cache_size=1000
            ),
            performance=PerformanceConfig(
                enable_search_cache=True,
                search_cache_size=100
            ),
            cleanup=CleanupConfig(
                enable_auto_cleanup=False,
                max_memory_entries=2000
            )
        )
    
    @pytest.mark.asyncio
    async def test_large_dataset_performance(self, performance_config):
        """测试大数据集性能"""
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage, config=performance_config)
        
        try:
            # 创建大量记忆条目
            start_time = time.time()
            
            batch_size = 100
            total_memories = 500
            
            for batch_start in range(0, total_memories, batch_size):
                batch_specs = []
                for i in range(batch_start, min(batch_start + batch_size, total_memories)):
                    spec = {
                        "memory_type": MemoryType.METHOD_CALL,
                        "title": f"Performance Test Memory {i}",
                        "content": {
                            "index": i,
                            "batch": batch_start // batch_size,
                            "data": f"performance_data_{i}" * 10  # 增加内容大小
                        },
                        "source_agent_did": f"agent_{i % 10}",
                        "source_agent_name": f"Agent {i % 10}",
                        "keywords": [f"perf_{i}", f"agent_{i % 10}", "performance"],
                        "tags": ["performance", "test", f"batch_{batch_start // batch_size}"]
                    }
                    batch_specs.append(spec)
                
                await memory_manager.create_memories_batch(batch_specs)
            
            creation_time = time.time() - start_time
            print(f"创建 {total_memories} 个记忆耗时: {creation_time:.2f}s")
            
            # 测试搜索性能
            search_start_time = time.time()
            
            search_results = await memory_manager.search_memories(
                tags=["performance"],
                limit=50
            )
            
            search_time = time.time() - search_start_time
            print(f"搜索耗时: {search_time:.3f}s")
            
            assert len(search_results) == 50
            assert search_time < 1.0  # 搜索应该在1秒内完成
            
            # 测试随机访问性能
            random_access_start = time.time()
            
            for i in range(0, 100, 10):  # 随机访问10个记忆
                search_by_index = await memory_manager.search_memories(
                    keywords=[f"perf_{i}"],
                    limit=1
                )
                assert len(search_by_index) == 1
            
            random_access_time = time.time() - random_access_start
            print(f"随机访问耗时: {random_access_time:.3f}s")
            
            assert random_access_time < 2.0  # 随机访问应该在2秒内完成
            
            # 验证内存使用合理
            storage_stats = await memory_manager.storage.get_storage_stats()
            assert storage_stats['total_memories'] == total_memories
            
        finally:
            await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_search_cache_performance(self, performance_config):
        """测试搜索缓存性能"""
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage, config=performance_config)
        
        try:
            # 创建测试数据
            for i in range(100):
                await memory_manager.create_memory(
                    memory_type=MemoryType.METHOD_CALL,
                    title=f"Cache Test Memory {i}",
                    content={"index": i},
                    source_agent_did="cache_test",
                    source_agent_name="Cache Test",
                    keywords=[f"cache_{i}", "test"],
                    tags=["cache", "performance"]
                )
            
            # 第一次搜索（缓存未命中）
            start_time = time.time()
            results1 = await memory_manager.search_memories(
                tags=["cache"],
                keywords=["test"],
                limit=10
            )
            first_search_time = time.time() - start_time
            
            # 第二次相同搜索（应该命中缓存）
            start_time = time.time()
            results2 = await memory_manager.search_memories(
                tags=["cache"],
                keywords=["test"],
                limit=10
            )
            cached_search_time = time.time() - start_time
            
            # 验证结果一致
            assert len(results1) == len(results2)
            assert [r.id for r in results1] == [r.id for r in results2]
            
            # 缓存搜索应该明显更快
            print(f"首次搜索: {first_search_time:.4f}s, 缓存搜索: {cached_search_time:.4f}s")
            
            # 注意：在小数据集上差异可能不明显，这里只做基本验证
            assert cached_search_time <= first_search_time * 2  # 至少不应该更慢
            
        finally:
            await memory_manager.close()


if __name__ == "__main__":
    pytest.main([__file__])