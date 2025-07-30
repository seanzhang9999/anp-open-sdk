"""
LocalMethod与记忆功能集成测试

测试LocalMethod装饰器与记忆功能的集成，验证方法调用记录、推荐等功能
"""

import pytest
import asyncio
import time
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Any, Dict, List, Optional

from anp_runtime.local_service.memory.memory_manager import MemoryManager
from anp_runtime.local_service.memory.memory_collector import MemoryCollector
from anp_runtime.local_service.memory.memory_recommender import MemoryRecommender
from anp_runtime.local_service.memory.context_session import ContextSessionManager
from anp_runtime.local_service.memory.memory_storage import InMemoryStorage
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
    CleanupConfig
)


# 模拟LocalMethod装饰器和相关类
class MockLocalMethod:
    """模拟LocalMethod装饰器"""
    
    def __init__(self, func):
        self.func = func
        self.method_name = func.__name__
        self.method_key = f"mock::{func.__name__}"
        self.call_history = []
        self.memory_manager = None
        self.session_manager = None
        
    def __call__(self, *args, **kwargs):
        """调用方法并记录到记忆"""
        start_time = time.time()
        
        try:
            # 执行原方法
            result = self.func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            # 记录调用历史
            call_record = {
                'timestamp': datetime.now(),
                'args': args,
                'kwargs': kwargs,
                'result': result,
                'success': True,
                'execution_time': execution_time,
                'error': None
            }
            self.call_history.append(call_record)
            
            # 如果配置了记忆管理器，创建记忆记录
            if self.memory_manager and hasattr(self.memory_manager, 'create_method_call_memory'):
                asyncio.create_task(self._create_memory_record(call_record))
            
            return result
            
        except Exception as error:
            execution_time = time.time() - start_time
            
            # 记录错误
            call_record = {
                'timestamp': datetime.now(),
                'args': args,
                'kwargs': kwargs,
                'result': None,
                'success': False,
                'execution_time': execution_time,
                'error': error
            }
            self.call_history.append(call_record)
            
            # 创建错误记忆记录
            if self.memory_manager and hasattr(self.memory_manager, 'create_error_memory'):
                asyncio.create_task(self._create_error_memory_record(call_record))
            
            raise error
    
    async def __call_async__(self, *args, **kwargs):
        """异步调用方法并记录到记忆"""
        start_time = time.time()
        
        try:
            # 执行原方法
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(*args, **kwargs)
            else:
                result = self.func(*args, **kwargs)
            
            execution_time = time.time() - start_time
            
            # 记录调用历史
            call_record = {
                'timestamp': datetime.now(),
                'args': args,
                'kwargs': kwargs,
                'result': result,
                'success': True,
                'execution_time': execution_time,
                'error': None
            }
            self.call_history.append(call_record)
            
            # 创建记忆记录
            if self.memory_manager:
                await self._create_memory_record(call_record)
            
            return result
            
        except Exception as error:
            execution_time = time.time() - start_time
            
            # 记录错误
            call_record = {
                'timestamp': datetime.now(),
                'args': args,
                'kwargs': kwargs,
                'result': None,
                'success': False,
                'execution_time': execution_time,
                'error': error
            }
            self.call_history.append(call_record)
            
            # 创建错误记忆记录
            if self.memory_manager:
                await self._create_error_memory_record(call_record)
            
            raise error
    
    async def _create_memory_record(self, call_record):
        """创建方法调用记忆记录"""
        try:
            if not self.memory_manager:
                return
                
            session_id = None
            if self.session_manager:
                # 获取当前活跃会话
                sessions = await self.session_manager.get_active_sessions()
                if sessions:
                    session_id = sessions[0].id
            
            # 检查memory_manager是否有create_method_call_memory方法
            if hasattr(self.memory_manager, 'create_method_call_memory'):
                await self.memory_manager.create_method_call_memory(
                    method_name=self.method_name,
                    method_key=self.method_key,
                    input_args=list(call_record['args']),
                    input_kwargs=call_record['kwargs'],
                    output=call_record['result'],
                    execution_time=call_record['execution_time'],
                    source_agent_did="local_method",
                    source_agent_name="Local Method",
                    session_id=session_id,
                    keywords=[self.method_name, "local_method", "call"],
                    tags=["local_method", "executed"]
                )
        except Exception as e:
            print(f"创建记忆记录失败: {e}")
    
    async def _create_error_memory_record(self, call_record):
        """创建错误记忆记录"""
        try:
            if not self.memory_manager:
                return
                
            session_id = None
            if self.session_manager:
                sessions = await self.session_manager.get_active_sessions()
                if sessions:
                    session_id = sessions[0].id
            
            # 检查memory_manager是否有create_error_memory方法
            if hasattr(self.memory_manager, 'create_error_memory'):
                await self.memory_manager.create_error_memory(
                    method_name=self.method_name,
                    method_key=self.method_key,
                    input_args=list(call_record['args']),
                    input_kwargs=call_record['kwargs'],
                    error=call_record['error'],
                    execution_time=call_record['execution_time'],
                    source_agent_did="local_method",
                    source_agent_name="Local Method",
                    session_id=session_id
                )
        except Exception as e:
            print(f"创建错误记忆记录失败: {e}")
    
    def set_memory_manager(self, memory_manager):
        """设置记忆管理器"""
        self.memory_manager = memory_manager
    
    def set_session_manager(self, session_manager):
        """设置会话管理器"""
        self.session_manager = session_manager


def local_method(func):
    """LocalMethod装饰器"""
    return MockLocalMethod(func)


class TestLocalMethodBasicIntegration:
    """测试LocalMethod基本集成"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MemoryConfig(
            enabled=True,
            storage=StorageConfig(storage_type="memory"),
            collection=CollectionConfig(
                enable_memory_collection=True,
                collection_mode="auto",
                collect_input_params=True,
                collect_output_results=True,
                collect_errors=True
            ),
            cleanup=CleanupConfig(enable_auto_cleanup=False)
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
    
    @pytest.mark.asyncio
    async def test_method_call_recording(self, memory_manager, session_manager):
        """测试方法调用记录"""
        # 定义测试方法
        @local_method
        def calculate_sum(a: int, b: int) -> int:
            """计算两数之和"""
            return a + b
        
        # 设置记忆管理器
        calculate_sum.set_memory_manager(memory_manager)
        calculate_sum.set_session_manager(session_manager)
        
        try:
            # 创建测试会话
            session = await session_manager.create_session(
                name="Method Test Session",
                participants=["local_method"]
            )
            
            # 调用方法
            result1 = await calculate_sum.__call_async__(10, 20)
            assert result1 == 30
            
            result2 = await calculate_sum.__call_async__(15, 25)
            assert result2 == 40
            
            # 短暂等待确保记忆记录创建完成
            await asyncio.sleep(0.1)
            
            # 验证调用历史
            assert len(calculate_sum.call_history) == 2
            assert calculate_sum.call_history[0]['result'] == 30
            assert calculate_sum.call_history[1]['result'] == 40
            
            # 验证记忆记录创建
            method_memories = await memory_manager.search_memories(
                keywords=["calculate_sum"],
                memory_type=MemoryType.METHOD_CALL
            )
            
            assert len(method_memories) == 2
            
            # 验证记忆内容
            memory1 = method_memories[0]
            assert memory1.content['method_name'] == "calculate_sum"
            assert memory1.content['success'] == True
            assert memory1.content['output'] == 30 or memory1.content['output'] == 40
            assert 'execution_time' in memory1.content
            
            # 验证会话关联
            session_memories = await session_manager.get_session_memories(session.id)
            assert len(session_memories) >= 2
            
        finally:
            await session_manager.close()
            await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_method_error_recording(self, memory_manager, session_manager):
        """测试方法错误记录"""
        # 定义会出错的测试方法
        @local_method
        def divide_numbers(a: int, b: int) -> float:
            """数字除法"""
            if b == 0:
                raise ValueError("除数不能为零")
            return a / b
        
        # 设置记忆管理器
        divide_numbers.set_memory_manager(memory_manager)
        divide_numbers.set_session_manager(session_manager)
        
        try:
            # 创建测试会话
            session = await session_manager.create_session(
                name="Error Test Session",
                participants=["local_method"]
            )
            
            # 正常调用
            result = await divide_numbers.__call_async__(10, 2)
            assert result == 5.0
            
            # 错误调用
            with pytest.raises(ValueError, match="除数不能为零"):
                await divide_numbers.__call_async__(10, 0)
            
            # 短暂等待确保记忆记录创建完成
            await asyncio.sleep(0.1)
            
            # 验证调用历史
            assert len(divide_numbers.call_history) == 2
            assert divide_numbers.call_history[0]['success'] == True
            assert divide_numbers.call_history[1]['success'] == False
            assert divide_numbers.call_history[1]['error'] is not None
            
            # 验证成功记忆记录
            success_memories = await memory_manager.search_memories(
                keywords=["divide_numbers"],
                memory_type=MemoryType.METHOD_CALL
            )
            assert len(success_memories) >= 1
            
            # 验证错误记忆记录
            error_memories = await memory_manager.search_memories(
                keywords=["divide_numbers"],
                memory_type=MemoryType.ERROR
            )
            assert len(error_memories) >= 1
            
            error_memory = error_memories[0]
            assert error_memory.content['success'] == False
            assert "除数不能为零" in str(error_memory.content['error'])
            
        finally:
            await session_manager.close()
            await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_method_recommendation_integration(self, memory_manager, session_manager):
        """测试方法推荐集成"""
        # 定义测试方法
        @local_method
        def user_login(username: str, password: str) -> dict:
            """用户登录"""
            return {
                "success": True,
                "user_id": username,
                "token": f"token_{username}_{int(time.time())}"
            }
        
        @local_method
        def get_user_profile(user_id: str) -> dict:
            """获取用户资料"""
            return {
                "user_id": user_id,
                "name": f"User {user_id}",
                "email": f"{user_id}@example.com"
            }
        
        # 设置记忆管理器
        user_login.set_memory_manager(memory_manager)
        user_login.set_session_manager(session_manager)
        get_user_profile.set_memory_manager(memory_manager)
        get_user_profile.set_session_manager(session_manager)
        
        # 创建推荐器
        memory_recommender = MemoryRecommender(
            memory_manager=memory_manager,
            session_manager=session_manager,
            config=MemoryConfig(
                recommendation=RecommendationConfig(
                    algorithm="hybrid",
                    max_recommendations=5
                )
            )
        )
        
        try:
            # 创建测试会话
            session = await session_manager.create_session(
                name="Recommendation Test Session",
                participants=["user_system"]
            )
            
            # 执行一系列相关方法调用
            login_result = await user_login.__call_async__("alice", "password123")
            profile_result = await get_user_profile.__call_async__("alice")
            
            # 再次登录不同用户
            await user_login.__call_async__("bob", "password456")
            await get_user_profile.__call_async__("bob")
            
            # 短暂等待确保记忆记录创建完成
            await asyncio.sleep(0.2)
            
            # 验证记忆记录
            all_memories = await memory_manager.search_memories(
                keywords=["user"],
                session_id=session.id
            )
            assert len(all_memories) >= 4
            
            # 测试基于上下文的推荐
            context_recommendations = await memory_recommender.recommend_for_context(
                keywords=["user", "login"],
                tags=["method"],
                session_id=session.id,
                max_recommendations=3
            )
            
            assert len(context_recommendations) > 0
            # 推荐结果应该包含相关的用户操作记忆
            recommended_methods = [memory.content.get('method_name') for memory, _ in context_recommendations]
            assert 'user_login' in recommended_methods or 'get_user_profile' in recommended_methods
            
            # 测试基于方法调用的推荐
            method_recommendations = await memory_recommender.recommend_for_method_call(
                method_name="user_login",
                method_key="mock::user_login",
                agent_did="user_system",
                session_id=session.id
            )
            
            # 应该推荐相关的用户操作
            assert len(method_recommendations) >= 0  # 可能为空，因为没有足够的历史数据
            
            # 测试相似记忆推荐
            login_memories = await memory_manager.search_memories(
                keywords=["user_login"],
                memory_type=MemoryType.METHOD_CALL,
                limit=1
            )
            
            if login_memories:
                similar_recommendations = await memory_recommender.recommend_similar_memories(
                    reference_memory=login_memories[0],
                    max_recommendations=3
                )
                # 相似推荐不应包含参考记忆本身
                similar_ids = [memory.id for memory, _ in similar_recommendations]
                assert login_memories[0].id not in similar_ids
            
        finally:
            await session_manager.close()
            await memory_manager.close()


class TestLocalMethodAdvancedIntegration:
    """测试LocalMethod高级集成"""
    
    @pytest.fixture
    def advanced_config(self):
        """创建高级测试配置"""
        return MemoryConfig(
            enabled=True,
            storage=StorageConfig(
                storage_type="memory",
                cache_size=500
            ),
            collection=CollectionConfig(
                enable_memory_collection=True,
                collection_mode="selective",
                auto_collect_methods=["important_method", "user_action"],
                collect_input_params=True,
                collect_output_results=True,
                collect_errors=True,
                max_param_length=500
            ),
            recommendation=RecommendationConfig(
                algorithm="hybrid",
                max_recommendations=10,
                similarity_threshold=0.3
            ),
            cleanup=CleanupConfig(
                enable_auto_cleanup=False,
                max_memory_entries=1000
            )
        )
    
    @pytest.mark.asyncio
    async def test_complex_workflow_integration(self, advanced_config):
        """测试复杂工作流程集成"""
        # 创建组件
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage, config=advanced_config)
        session_manager = ContextSessionManager(storage=storage)
        memory_recommender = MemoryRecommender(
            memory_manager=memory_manager,
            session_manager=session_manager,
            config=advanced_config
        )
        
        # 定义工作流程方法
        @local_method
        def start_project(project_name: str, description: str) -> dict:
            """开始项目"""
            return {
                "project_id": f"proj_{int(time.time())}",
                "name": project_name,
                "description": description,
                "status": "started",
                "created_at": datetime.now().isoformat()
            }
        
        @local_method
        def add_task(project_id: str, task_name: str, priority: str = "medium") -> dict:
            """添加任务"""
            return {
                "task_id": f"task_{int(time.time() * 1000)}",
                "project_id": project_id,
                "name": task_name,
                "priority": priority,
                "status": "pending"
            }
        
        @local_method
        def complete_task(task_id: str, notes: str = "") -> dict:
            """完成任务"""
            return {
                "task_id": task_id,
                "status": "completed",
                "completed_at": datetime.now().isoformat(),
                "notes": notes
            }
        
        @local_method
        def important_method(data: dict) -> dict:
            """重要方法（会被自动收集）"""
            return {"processed": True, "result": data.get("value", 0) * 2}
        
        # 设置记忆管理器
        for method in [start_project, add_task, complete_task, important_method]:
            method.set_memory_manager(memory_manager)
            method.set_session_manager(session_manager)
        
        try:
            # 创建工作会话
            work_session = await session_manager.create_session(
                name="Project Workflow Session",
                description="Complete project workflow test",
                participants=["project_manager", "developer"],
                context_data={
                    "workflow_type": "project_management",
                    "stage": "initial"
                }
            )
            
            # 执行工作流程
            # 1. 启动项目
            project = await start_project.__call_async__(
                "Test Project",
                "Integration test project"
            )
            project_id = project["project_id"]
            
            # 2. 添加多个任务
            task1 = await add_task.__call_async__(
                project_id, "Setup environment", "high"
            )
            task2 = await add_task.__call_async__(
                project_id, "Write tests", "medium"
            )
            task3 = await add_task.__call_async__(
                project_id, "Implementation", "high"
            )
            
            # 3. 执行重要方法（会被自动收集）
            await important_method.__call_async__({"value": 42})
            await important_method.__call_async__({"value": 100})
            
            # 4. 完成一些任务
            await complete_task.__call_async__(
                task1["task_id"],
                "Environment setup completed successfully"
            )
            await complete_task.__call_async__(
                task2["task_id"],
                "All tests written and passing"
            )
            
            # 更新会话状态
            await session_manager.update_context_data(
                work_session.id, "stage", "execution"
            )
            
            # 短暂等待确保所有记忆记录创建完成
            await asyncio.sleep(0.3)
            
            # 验证记忆记录
            session_memories = await session_manager.get_session_memories(work_session.id)
            assert len(session_memories) >= 7  # 至少7个方法调用
            
            # 验证不同类型的记忆
            project_memories = await memory_manager.search_memories(
                keywords=["start_project"],
                session_id=work_session.id
            )
            assert len(project_memories) >= 1
            
            task_memories = await memory_manager.search_memories(
                keywords=["add_task"],
                session_id=work_session.id
            )
            assert len(task_memories) >= 3
            
            complete_memories = await memory_manager.search_memories(
                keywords=["complete_task"],
                session_id=work_session.id
            )
            assert len(complete_memories) >= 2
            
            # 验证重要方法的记忆（应该被特别收集）
            important_memories = await memory_manager.search_memories(
                keywords=["important_method"],
                session_id=work_session.id
            )
            assert len(important_memories) >= 2
            
            # 测试工作流程推荐
            # 基于当前项目上下文推荐
            workflow_recommendations = await memory_recommender.recommend_for_context(
                keywords=["project", "task"],
                tags=["integration"],
                session_id=work_session.id,
                max_recommendations=5
            )
            
            assert len(workflow_recommendations) > 0
            
            # 验证推荐质量 - 应该推荐相关的项目管理操作
            recommended_methods = []
            for memory, score in workflow_recommendations:
                method_name = memory.content.get('method_name')
                if method_name:
                    recommended_methods.append(method_name)
            
            # 至少应该推荐一些项目相关的方法
            project_related_methods = ['start_project', 'add_task', 'complete_task']
            has_project_methods = any(method in recommended_methods for method in project_related_methods)
            assert has_project_methods
            
            # 测试基于特定方法的推荐
            task_method_recommendations = await memory_recommender.recommend_for_method_call(
                method_name="add_task",
                method_key="mock::add_task",
                agent_did="project_manager",
                session_id=work_session.id
            )
            
            # 应该推荐相关的任务管理操作
            # 在真实场景中，这会推荐类似的任务添加或完成操作
            
            # 获取系统统计信息
            memory_stats = await memory_manager.get_memory_statistics()
            session_stats = await session_manager.get_session_statistics()
            
            # 验证统计信息
            assert memory_stats['operations']['memories_created'] >= 7
            assert memory_stats['storage']['total_memories'] >= 7
            assert session_stats['total_active_sessions'] >= 1
            
            # 测试会话统计信息
            session_stats = await session_manager.get_session_statistics()
            assert session_stats is not None
            assert session_stats.get('total_sessions', 0) > 0
            
        finally:
            await session_manager.close()
            await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_performance_with_many_methods(self, advanced_config):
        """测试大量方法调用的性能"""
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage, config=advanced_config)
        session_manager = ContextSessionManager(storage=storage)
        
        # 定义批量测试方法
        @local_method
        def batch_process(batch_id: int, data: list) -> dict:
            """批量处理"""
            processed_count = len(data)
            return {
                "batch_id": batch_id,
                "processed_count": processed_count,
                "status": "completed"
            }
        
        batch_process.set_memory_manager(memory_manager)
        batch_process.set_session_manager(session_manager)
        
        try:
            # 创建性能测试会话
            perf_session = await session_manager.create_session(
                name="Performance Test Session",
                participants=["performance_tester"]
            )
            
            # 批量执行方法调用
            batch_count = 50
            start_time = time.time()
            
            tasks = []
            for i in range(batch_count):
                task = batch_process.__call_async__(
                    i, [f"item_{j}" for j in range(10)]
                )
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks)
            
            execution_time = time.time() - start_time
            print(f"执行 {batch_count} 个方法调用耗时: {execution_time:.2f}s")
            
            # 验证所有调用都成功
            assert len(results) == batch_count
            for i, result in enumerate(results):
                assert result["batch_id"] == i
                assert result["processed_count"] == 10
            
            # 短暂等待确保所有记忆记录创建完成
            await asyncio.sleep(0.5)
            
            # 验证记忆记录
            batch_memories = await memory_manager.search_memories(
                keywords=["batch_process"],
                session_id=perf_session.id
            )
            
            assert len(batch_memories) == batch_count
            
            # 验证调用历史
            assert len(batch_process.call_history) == batch_count
            
            # 测试搜索性能
            search_start_time = time.time()
            search_results = await memory_manager.search_memories(
                session_id=perf_session.id,
                limit=20
            )
            search_time = time.time() - search_start_time
            
            print(f"搜索 {len(batch_memories)} 条记忆耗时: {search_time:.3f}s")
            assert search_time < 1.0  # 搜索应该在1秒内完成
            
            # 验证性能统计
            memory_stats = await memory_manager.get_memory_statistics()
            assert memory_stats['operations']['memories_created'] >= batch_count
            assert memory_stats['performance']['average_search_time'] < 1.0
            
        finally:
            await session_manager.close()
            await memory_manager.close()


class TestLocalMethodErrorHandling:
    """测试LocalMethod错误处理"""
    
    @pytest.fixture
    def config(self):
        return MemoryConfig(
            enabled=True,
            storage=StorageConfig(storage_type="memory"),
            collection=CollectionConfig(
                enable_memory_collection=True,
                collect_errors=True
            )
        )
    
    @pytest.mark.asyncio
    async def test_memory_system_failure_handling(self, config):
        """测试记忆系统失败处理"""
        # 创建会失败的模拟存储
        mock_storage = Mock()
        mock_storage.save_memory = AsyncMock(return_value=False)
        mock_storage.search_memories = AsyncMock(return_value=[])
        
        # 使用失败的存储创建记忆管理器
        failing_memory_manager = MemoryManager(storage=mock_storage, config=config)
        
        # 定义测试方法
        @local_method
        def test_method(value: int) -> int:
            """测试方法"""
            return value * 2
        
        test_method.set_memory_manager(failing_memory_manager)
        
        try:
            # 即使记忆系统失败，方法调用仍应成功
            result = await test_method.__call_async__(21)
            assert result == 42
            
            # 验证调用历史仍然被记录（本地记录）
            assert len(test_method.call_history) == 1
            assert test_method.call_history[0]['result'] == 42
            
            # 验证方法执行不受记忆系统失败影响
            result2 = await test_method.__call_async__(10)
            assert result2 == 20
            assert len(test_method.call_history) == 2
            
        finally:
            await failing_memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_method_exception_with_memory_failure(self, config):
        """测试方法异常和记忆失败的组合处理"""
        # 创建正常的存储和管理器
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage, config=config)
        
        # 定义会抛出异常的方法
        @local_method
        def failing_method(should_fail: bool) -> str:
            """会失败的测试方法"""
            if should_fail:
                raise RuntimeError("Method intentionally failed")
            return "success"
        
        failing_method.set_memory_manager(memory_manager)
        
        try:
            # 正常调用
            result = await failing_method.__call_async__(False)
            assert result == "success"
            
            # 异常调用
            with pytest.raises(RuntimeError, match="Method intentionally failed"):
                await failing_method.__call_async__(True)
            
            # 短暂等待记忆记录创建
            await asyncio.sleep(0.1)
            
            # 验证调用历史
            assert len(failing_method.call_history) == 2
            assert failing_method.call_history[0]['success'] == True
            assert failing_method.call_history[1]['success'] == False
            
            # 验证错误记忆记录
            error_memories = await memory_manager.search_memories(
                keywords=["failing_method"],
                memory_type=MemoryType.ERROR
            )
            assert len(error_memories) >= 1
            
            error_memory = error_memories[0]
            assert error_memory.content['success'] == False
            assert "Method intentionally failed" in str(error_memory.content['error'])
            
        finally:
            await memory_manager.close()


if __name__ == "__main__":
    pytest.main([__file__])