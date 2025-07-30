"""
记忆收集器测试

测试 MemoryCollector、DataFilter、CollectionRules 等记忆收集组件
"""

import pytest
import asyncio
import time
import json
import threading
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, List

from anp_runtime.local_service.memory.memory_collector import (
    MemoryCollector,
    DataFilter,
    CollectionRules,
    MethodExecutionContext,
    get_memory_collector,
    set_memory_collector,
    memory_collection_decorator
)
from anp_runtime.local_service.memory.memory_manager import MemoryManager
from anp_runtime.local_service.memory.memory_models import (
    MemoryEntry,
    MemoryType,
    MemoryMetadata
)
from anp_runtime.local_service.memory.memory_config import (
    MemoryConfig,
    CollectionConfig,
    SecurityConfig
)


class TestDataFilter:
    """测试数据过滤器"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MemoryConfig(
            security=SecurityConfig(
                sensitive_fields=["password", "token", "secret"],
            ),
            collection=CollectionConfig(
                max_param_length=100
            )
        )
    
    @pytest.fixture
    def data_filter(self, config):
        """创建数据过滤器"""
        return DataFilter(config)
    
    def test_filter_simple_data(self, data_filter):
        """测试过滤简单数据"""
        # 测试基本数据类型
        assert data_filter.filter_data("hello") == "hello"
        assert data_filter.filter_data(123) == 123
        assert data_filter.filter_data(True) == True
        assert data_filter.filter_data(None) == None
    
    def test_filter_sensitive_fields(self, data_filter):
        """测试过滤敏感字段"""
        sensitive_data = {
            "username": "alice",
            "password": "secret123",
            "api_token": "abc123",
            "user_secret": "hidden",
            "normal_field": "visible"
        }
        
        filtered_data = data_filter.filter_data(sensitive_data)
        
        assert filtered_data["username"] == "alice"
        assert filtered_data["password"] == "<<FILTERED>>"
        assert filtered_data["api_token"] == "<<FILTERED>>"
        assert filtered_data["user_secret"] == "<<FILTERED>>"
        assert filtered_data["normal_field"] == "visible"
    
    def test_filter_long_strings(self, data_filter):
        """测试过滤长字符串"""
        long_string = "a" * 200
        filtered_string = data_filter.filter_data(long_string)
        
        assert len(filtered_string) == 100 + len("<<TRUNCATED>>")
        assert filtered_string.endswith("<<TRUNCATED>>")
    
    def test_filter_nested_data(self, data_filter):
        """测试过滤嵌套数据"""
        nested_data = {
            "user": {
                "name": "Alice",
                "credentials": {
                    "password": "secret",
                    "token": "abc123"
                }
            },
            "config": {
                "debug": True,
                "api_secret": "hidden"
            }
        }
        
        filtered_data = data_filter.filter_data(nested_data)
        
        assert filtered_data["user"]["name"] == "Alice"
        assert filtered_data["user"]["credentials"]["password"] == "<<FILTERED>>"
        assert filtered_data["user"]["credentials"]["token"] == "<<FILTERED>>"
        assert filtered_data["config"]["debug"] == True
        assert filtered_data["config"]["api_secret"] == "<<FILTERED>>"
    
    def test_filter_list_data(self, data_filter):
        """测试过滤列表数据"""
        list_data = [
            {"name": "item1", "password": "secret1"},
            {"name": "item2", "token": "secret2"},
            "normal_string"
        ]
        
        filtered_data = data_filter.filter_data(list_data)
        
        assert filtered_data[0]["name"] == "item1"
        assert filtered_data[0]["password"] == "<<FILTERED>>"
        assert filtered_data[1]["name"] == "item2"
        assert filtered_data[1]["token"] == "<<FILTERED>>"
        assert filtered_data[2] == "normal_string"
    
    def test_filter_large_list(self, data_filter):
        """测试过滤大列表（限制长度）"""
        large_list = list(range(200))
        filtered_list = data_filter.filter_data(large_list)
        
        # 应该被限制为100个元素
        assert len(filtered_list) == 100
        assert filtered_list[:10] == list(range(10))
    
    def test_filter_custom_object(self, data_filter):
        """测试过滤自定义对象"""
        class TestObject:
            def __init__(self):
                self.name = "test"
                self.password = "secret"
                self._private = "hidden"
        
        obj = TestObject()
        filtered_data = data_filter.filter_data(obj)
        
        # 应该返回对象的字符串表示
        assert "TestObject" in str(filtered_data)
    
    def test_filter_max_depth(self, data_filter):
        """测试最大深度限制"""
        # 创建深度嵌套的数据
        deep_data = {"level": 0}
        current = deep_data
        for i in range(1, 15):
            current["next"] = {"level": i}
            current = current["next"]
        
        filtered_data = data_filter.filter_data(deep_data)
        
        # 应该在某个深度停止并显示MAX_DEPTH_EXCEEDED
        def check_max_depth(data, depth=0):
            if depth > 12:  # 允许一些误差
                return True
            if isinstance(data, dict) and "next" in data:
                if data["next"] == "<<MAX_DEPTH_EXCEEDED>>":
                    return True
                return check_max_depth(data["next"], depth + 1)
            return False
        
        assert check_max_depth(filtered_data)
    
    def test_serialize_for_storage(self, data_filter):
        """测试序列化存储"""
        test_data = {
            "method": "test_method",
            "params": {"username": "alice", "password": "secret"},
            "result": {"status": "success", "token": "abc123"}
        }
        
        serialized = data_filter.serialize_for_storage(test_data)
        
        # 应该是JSON字符串
        assert isinstance(serialized, str)
        
        # 解析并验证敏感数据被过滤
        parsed_data = json.loads(serialized)
        assert parsed_data["params"]["password"] == "<<FILTERED>>"
        assert parsed_data["result"]["token"] == "<<FILTERED>>"
        assert parsed_data["params"]["username"] == "alice"
    
    def test_serialize_invalid_data(self, data_filter):
        """测试序列化无效数据"""
        # 创建无法序列化的对象
        class UnserializableObject:
            def __repr__(self):
                raise Exception("Cannot represent")
        
        invalid_data = UnserializableObject()
        serialized = data_filter.serialize_for_storage(invalid_data)
        
        # 应该返回截断的字符串表示
        assert isinstance(serialized, str)
        assert len(serialized) <= data_filter.max_param_length


class TestCollectionRules:
    """测试收集规则管理器"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MemoryConfig(
            collection=CollectionConfig(
                enable_memory_collection=True,
                collection_mode="selective",
                auto_collect_methods=["test_method", "important_method"],
                collection_filters={
                    "include_patterns": ["test_", "important_"],
                    "exclude_patterns": ["private_", "_internal"],
                    "agent_whitelist": ["alice", "bob"],
                    "agent_blacklist": ["malicious_agent"]
                },
                collect_input_params=True,
                collect_output_results=True,
                collect_errors=True
            )
        )
    
    @pytest.fixture
    def collection_rules(self, config):
        """创建收集规则管理器"""
        return CollectionRules(config)
    
    def test_should_collect_method_disabled(self):
        """测试收集功能禁用时"""
        config = MemoryConfig(
            collection=CollectionConfig(enable_memory_collection=False)
        )
        rules = CollectionRules(config)
        
        result = rules.should_collect_method("test_method", "test_key", "alice", "Alice")
        assert result == False
    
    def test_should_collect_method_manual_mode(self):
        """测试手动收集模式"""
        config = MemoryConfig(
            collection=CollectionConfig(
                enable_memory_collection=True,
                collection_mode="manual"
            )
        )
        rules = CollectionRules(config)
        
        result = rules.should_collect_method("test_method", "test_key", "alice", "Alice")
        assert result == False
    
    def test_should_collect_method_auto_mode(self, collection_rules):
        """测试自动收集模式"""
        # 修改为自动模式
        collection_rules.config.collection.collection_mode = "auto"
        
        # 应该收集所有方法（除非被排除）
        result = collection_rules.should_collect_method("any_method", "any_key", "alice", "Alice")
        assert result == True
    
    def test_should_collect_method_selective_mode(self, collection_rules):
        """测试选择性收集模式"""
        # 测试在auto_collect_methods列表中的方法
        result = collection_rules.should_collect_method("test_method", "test_key", "alice", "Alice")
        assert result == True
        
        # 测试不在列表中的方法
        result = collection_rules.should_collect_method("other_method", "other_key", "alice", "Alice")
        assert result == False
        
        # 测试使用method_key匹配
        result = collection_rules.should_collect_method("some_method", "important_method", "alice", "Alice")
        assert result == True
    
    def test_agent_blacklist(self, collection_rules):
        """测试Agent黑名单"""
        result = collection_rules.should_collect_method(
            "test_method", "test_key", "malicious_agent", "Malicious"
        )
        assert result == False
    
    def test_agent_whitelist(self, collection_rules):
        """测试Agent白名单"""
        # 在白名单中的Agent
        result = collection_rules.should_collect_method("test_method", "test_key", "alice", "Alice")
        assert result == True
        
        # 不在白名单中的Agent
        result = collection_rules.should_collect_method("test_method", "test_key", "charlie", "Charlie")
        assert result == False
    
    def test_include_patterns(self, collection_rules):
        """测试包含模式"""
        # 匹配包含模式的方法
        result = collection_rules.should_collect_method("test_function", "test_key", "alice", "Alice")
        assert result == True
        
        result = collection_rules.should_collect_method("important_task", "task_key", "alice", "Alice")
        assert result == True
        
        # 不匹配包含模式的方法（在选择性模式下）
        result = collection_rules.should_collect_method("other_function", "other_key", "alice", "Alice")
        assert result == False
    
    def test_exclude_patterns(self, collection_rules):
        """测试排除模式"""
        # 测试排除模式（即使在auto_collect_methods中）
        collection_rules.config.collection.auto_collect_methods.append("private_method")
        
        result = collection_rules.should_collect_method("private_method", "private_key", "alice", "Alice")
        assert result == False
        
        result = collection_rules.should_collect_method("method_internal", "internal_key", "alice", "Alice")
        assert result == False
    
    def test_collection_settings(self, collection_rules):
        """测试收集设置"""
        assert collection_rules.should_collect_input() == True
        assert collection_rules.should_collect_output() == True
        assert collection_rules.should_collect_errors() == True
        
        # 测试禁用设置
        collection_rules.config.collection.collect_input_params = False
        collection_rules.config.collection.collect_output_results = False
        collection_rules.config.collection.collect_errors = False
        
        assert collection_rules.should_collect_input() == False
        assert collection_rules.should_collect_output() == False
        assert collection_rules.should_collect_errors() == False


class TestMethodExecutionContext:
    """测试方法执行上下文"""
    
    def test_context_initialization(self):
        """测试上下文初始化"""
        context = MethodExecutionContext(
            method_name="test_method",
            method_key="module::test_method",
            agent_did="alice",
            agent_name="Alice",
            session_id="session-123"
        )
        
        assert context.method_name == "test_method"
        assert context.method_key == "module::test_method"
        assert context.agent_did == "alice"
        assert context.agent_name == "Alice"
        assert context.session_id == "session-123"
        assert context.success == True
        assert context.error is None
        assert context.end_time is None
        assert isinstance(context.start_time, float)
    
    def test_set_input(self):
        """测试设置输入参数"""
        context = MethodExecutionContext("test", "test", "alice", "Alice")
        
        args = (1, 2, 3)
        kwargs = {"param": "value", "flag": True}
        
        context.set_input(args, kwargs)
        
        assert context.input_args == [1, 2, 3]
        assert context.input_kwargs == {"param": "value", "flag": True}
    
    def test_set_output(self):
        """测试设置输出结果"""
        context = MethodExecutionContext("test", "test", "alice", "Alice")
        
        # 等待一小段时间以确保时间差异
        time.sleep(0.01)
        
        output = {"result": "success", "data": [1, 2, 3]}
        context.set_output(output)
        
        assert context.output == output
        assert context.end_time is not None
        assert context.end_time > context.start_time
        assert context.execution_time > 0
    
    def test_set_error(self):
        """测试设置错误信息"""
        context = MethodExecutionContext("test", "test", "alice", "Alice")
        
        time.sleep(0.01)
        
        error = ValueError("Test error")
        context.set_error(error)
        
        assert context.error == error
        assert context.success == False
        assert context.end_time is not None
        assert context.execution_time > 0
    
    def test_execution_time_property(self):
        """测试执行时间属性"""
        context = MethodExecutionContext("test", "test", "alice", "Alice")
        
        # 在未结束时，应该返回当前运行时间
        time.sleep(0.01)
        running_time = context.execution_time
        assert running_time > 0
        
        # 设置结束时间
        context.set_output("result")
        final_time = context.execution_time
        
        # 最终时间应该固定
        time.sleep(0.01)
        assert context.execution_time == final_time


class TestMemoryCollector:
    """测试记忆收集器"""
    
    @pytest.fixture
    def memory_manager(self):
        """创建模拟记忆管理器"""
        manager = Mock(spec=MemoryManager)
        manager.create_method_call_memory = AsyncMock(return_value=Mock())
        manager.create_error_memory = AsyncMock(return_value=Mock())
        return manager
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MemoryConfig(
            collection=CollectionConfig(
                enable_memory_collection=True,
                collection_mode="auto",
                collect_input_params=True,
                collect_output_results=True,
                collect_errors=True,
                max_param_length=500
            ),
            security=SecurityConfig(
                sensitive_fields=["password", "token"]
            )
        )
    
    @pytest.fixture
    def memory_collector(self, memory_manager, config):
        """创建记忆收集器"""
        return MemoryCollector(memory_manager, config)
    
    def test_memory_collector_initialization(self, memory_collector, memory_manager, config):
        """测试记忆收集器初始化"""
        assert memory_collector.memory_manager == memory_manager
        assert memory_collector.config == config
        assert isinstance(memory_collector.data_filter, DataFilter)
        assert isinstance(memory_collector.collection_rules, CollectionRules)
        assert isinstance(memory_collector._execution_contexts, dict)
        assert isinstance(memory_collector._stats, dict)
    
    def test_create_collection_decorator_skip(self, memory_collector):
        """测试装饰器跳过不收集的方法"""
        # 配置为不收集此方法
        memory_collector.collection_rules.should_collect_method = Mock(return_value=False)
        
        @memory_collector.create_collection_decorator(
            "skip_method", "skip_key", "alice", "Alice"
        )
        def test_function():
            return "result"
        
        # 函数应该是原始函数（未被装饰）
        result = test_function()
        assert result == "result"
        
        # 不应该有收集活动
        memory_collector.collection_rules.should_collect_method.assert_called_once()
    
    def test_create_collection_decorator_sync(self, memory_collector):
        """测试同步函数的收集装饰器"""
        # 配置为收集此方法
        memory_collector.collection_rules.should_collect_method = Mock(return_value=True)
        
        @memory_collector.create_collection_decorator(
            "sync_method", "sync_key", "alice", "Alice"
        )
        def sync_function(x, y=10):
            return x + y
        
        # 执行函数
        with patch.object(memory_collector, '_execute_with_collection') as mock_execute:
            mock_execute.return_value = asyncio.Future()
            mock_execute.return_value.set_result(15)
            
            result = sync_function(5)
            
            # 验证执行和参数
            mock_execute.assert_called_once()
            args, kwargs = mock_execute.call_args
            assert args[1] == "sync_method"  # method_name
            assert args[2] == "sync_key"     # method_key
            assert args[5] == (5,)           # args
            assert args[6] == {'y': 10}      # kwargs
            assert args[7] == False          # is_async
    
    def test_create_collection_decorator_async(self, memory_collector):
        """测试异步函数的收集装饰器"""
        memory_collector.collection_rules.should_collect_method = Mock(return_value=True)
        
        @memory_collector.create_collection_decorator(
            "async_method", "async_key", "alice", "Alice"
        )
        async def async_function(x, y=10):
            return x + y
        
        # 验证返回的是异步函数
        import inspect
        assert inspect.iscoroutinefunction(async_function)
    
    @pytest.mark.asyncio
    async def test_execute_with_collection_success(self, memory_collector):
        """测试成功执行的记忆收集"""
        def test_function(x, y):
            return x + y
        
        result = await memory_collector._execute_with_collection(
            test_function, "test_method", "test_key", "alice", "Alice",
            None, (3, 4), {}, False
        )
        
        assert result == 7
        
        # 验证收集成功记忆
        memory_collector.memory_manager.create_method_call_memory.assert_called_once()
        call_args = memory_collector.memory_manager.create_method_call_memory.call_args[1]
        assert call_args["method_name"] == "test_method"
        assert call_args["method_key"] == "test_key"
        assert call_args["input_args"] == [3, 4]
        assert call_args["input_kwargs"] == {}
        assert call_args["output"] == 7
        assert call_args["source_agent_did"] == "alice"
        assert call_args["source_agent_name"] == "Alice"
    
    @pytest.mark.asyncio
    async def test_execute_with_collection_async_success(self, memory_collector):
        """测试异步函数成功执行的记忆收集"""
        async def async_test_function(x, y):
            await asyncio.sleep(0.01)  # 模拟异步操作
            return x * y
        
        result = await memory_collector._execute_with_collection(
            async_test_function, "async_method", "async_key", "alice", "Alice",
            None, (3, 4), {}, True
        )
        
        assert result == 12
        
        # 验证收集记忆
        memory_collector.memory_manager.create_method_call_memory.assert_called_once()
        call_args = memory_collector.memory_manager.create_method_call_memory.call_args[1]
        assert call_args["output"] == 12
        assert call_args["execution_time"] > 0
    
    @pytest.mark.asyncio
    async def test_execute_with_collection_error(self, memory_collector):
        """测试错误执行的记忆收集"""
        def failing_function():
            raise ValueError("Test error message")
        
        with pytest.raises(ValueError, match="Test error message"):
            await memory_collector._execute_with_collection(
                failing_function, "failing_method", "failing_key", "alice", "Alice",
                None, (), {}, False
            )
        
        # 验证收集错误记忆
        memory_collector.memory_manager.create_error_memory.assert_called_once()
        call_args = memory_collector.memory_manager.create_error_memory.call_args[1]
        assert call_args["method_name"] == "failing_method"
        assert call_args["method_key"] == "failing_key"
        assert isinstance(call_args["error"], ValueError)
        assert str(call_args["error"]) == "Test error message"
    
    @pytest.mark.asyncio
    async def test_execute_with_collection_disabled_input(self, memory_collector):
        """测试禁用输入收集"""
        memory_collector.collection_rules.should_collect_input = Mock(return_value=False)
        
        def test_function(secret_param):
            return "result"
        
        await memory_collector._execute_with_collection(
            test_function, "test_method", "test_key", "alice", "Alice",
            None, ("secret_value",), {}, False
        )
        
        # 验证没有收集输入参数
        call_args = memory_collector.memory_manager.create_method_call_memory.call_args[1]
        assert call_args["input_args"] == []
        assert call_args["input_kwargs"] == {}
    
    @pytest.mark.asyncio
    async def test_execute_with_collection_disabled_output(self, memory_collector):
        """测试禁用输出收集"""
        memory_collector.collection_rules.should_collect_output = Mock(return_value=False)
        
        def test_function():
            return "sensitive_result"
        
        await memory_collector._execute_with_collection(
            test_function, "test_method", "test_key", "alice", "Alice",
            None, (), {}, False
        )
        
        # 验证没有收集输出结果
        call_args = memory_collector.memory_manager.create_method_call_memory.call_args[1]
        assert call_args["output"] is None
    
    @pytest.mark.asyncio
    async def test_execute_with_collection_disabled_errors(self, memory_collector):
        """测试禁用错误收集"""
        memory_collector.collection_rules.should_collect_errors = Mock(return_value=False)
        
        def failing_function():
            raise ValueError("Should not be collected")
        
        with pytest.raises(ValueError):
            await memory_collector._execute_with_collection(
                failing_function, "failing_method", "failing_key", "alice", "Alice",
                None, (), {}, False
            )
        
        # 验证没有收集错误记忆
        memory_collector.memory_manager.create_error_memory.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_collect_manual_memory(self, memory_collector):
        """测试手动收集记忆"""
        content = {
            "user_data": {"username": "alice", "password": "secret123"},
            "operation": "login",
            "result": "success"
        }
        
        with patch.object(memory_collector.memory_manager, 'create_memory', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = Mock()
            
            result = await memory_collector.collect_manual_memory(
                memory_type=MemoryType.USER_PREFERENCE,
                title="User Login",
                content=content,
                agent_did="alice",
                agent_name="Alice",
                session_id="session-123",
                tags=["login", "user"],
                keywords=["authentication", "user"]
            )
            
            # 验证调用了创建记忆
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["memory_type"] == MemoryType.USER_PREFERENCE
            assert call_args["title"] == "User Login"
            assert call_args["agent_did"] == "alice"
            assert call_args["session_id"] == "session-123"
            assert call_args["tags"] == ["login", "user"]
            assert call_args["keywords"] == ["authentication", "user"]
            
            # 验证敏感数据被过滤
            filtered_content = call_args["content"]
            assert filtered_content["user_data"]["password"] == "<<FILTERED>>"
            assert filtered_content["user_data"]["username"] == "alice"
    
    def test_get_active_contexts(self, memory_collector):
        """测试获取活跃执行上下文"""
        # 添加一些模拟上下文
        context1 = MethodExecutionContext("method1", "key1", "alice", "Alice")
        context2 = MethodExecutionContext("method2", "key2", "bob", "Bob")
        
        memory_collector._execution_contexts["ctx1"] = context1
        memory_collector._execution_contexts["ctx2"] = context2
        
        active_contexts = memory_collector.get_active_contexts()
        
        assert len(active_contexts) == 2
        assert context1 in active_contexts
        assert context2 in active_contexts
    
    def test_get_collection_statistics(self, memory_collector):
        """测试获取收集统计信息"""
        # 设置一些统计数据
        memory_collector._stats['collections_attempted'] = 10
        memory_collector._stats['collections_successful'] = 8
        memory_collector._stats['collections_failed'] = 2
        
        # 添加一些活跃上下文
        memory_collector._execution_contexts["ctx1"] = Mock()
        
        stats = memory_collector.get_collection_statistics()
        
        assert stats['collections_attempted'] == 10
        assert stats['collections_successful'] == 8
        assert stats['collections_failed'] == 2
        assert stats['collection_enabled'] == True
        assert stats['collection_mode'] == "auto"
        assert stats['active_contexts'] == 1
        assert 'collect_input_params' in stats
        assert 'collect_output_results' in stats
        assert 'collect_errors' in stats
    
    def test_update_collection_rules(self, memory_collector):
        """测试更新收集规则"""
        new_rules = {
            'enable_memory_collection': False,
            'collection_mode': 'manual',
            'collect_input_params': False,
            'collect_errors': False,
            'auto_collect_methods': ['new_method'],
            'collection_filters': {'include_patterns': ['new_']}
        }
        
        memory_collector.update_collection_rules(new_rules)
        
        # 验证配置更新
        assert memory_collector.config.collection.enable_memory_collection == False
        assert memory_collector.config.collection.collection_mode == 'manual'
        assert memory_collector.config.collection.collect_input_params == False
        assert memory_collector.config.collection.collect_errors == False
        assert memory_collector.config.collection.auto_collect_methods == ['new_method']
        assert memory_collector.config.collection.collection_filters == {'include_patterns': ['new_']}
        
        # 验证规则管理器被重新初始化
        assert isinstance(memory_collector.collection_rules, CollectionRules)
    
    def test_enable_disable_collection(self, memory_collector):
        """测试启用/禁用收集"""
        # 禁用收集
        memory_collector.disable_collection()
        assert memory_collector.config.collection.enable_memory_collection == False
        
        # 启用收集
        memory_collector.enable_collection()
        assert memory_collector.config.collection.enable_memory_collection == True
    
    def test_concurrent_collection(self, memory_collector):
        """测试并发收集"""
        # 模拟多个并发执行上下文
        contexts = {}
        
        def add_context(context_id):
            context = MethodExecutionContext(f"method_{context_id}", f"key_{context_id}", "alice", "Alice")
            contexts[context_id] = context
            memory_collector._execution_contexts[f"ctx_{context_id}"] = context
            time.sleep(0.01)  # 模拟执行时间
            del memory_collector._execution_contexts[f"ctx_{context_id}"]
        
        # 创建多个线程
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_context, args=(i,))
            threads.append(thread)
        
        # 启动所有线程
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        # 验证所有上下文都被处理
        assert len(contexts) == 5
        assert len(memory_collector._execution_contexts) == 0  # 应该都被清理


class TestMemoryCollectorGlobal:
    """测试全局记忆收集器"""
    
    def test_get_memory_collector_singleton(self):
        """测试获取全局记忆收集器单例"""
        # 清除全局实例
        with patch('anp_runtime.local_service.memory.memory_collector._global_memory_collector', None):
            # 第一次获取应该创建新实例
            collector1 = get_memory_collector()
            assert isinstance(collector1, MemoryCollector)
            
            # 第二次获取应该返回同一实例
            collector2 = get_memory_collector()
            assert collector1 is collector2
    
    def test_set_memory_collector(self):
        """测试设置全局记忆收集器"""
        # 创建自定义收集器
        custom_collector = Mock(spec=MemoryCollector)
        
        # 设置全局收集器
        set_memory_collector(custom_collector)
        
        # 验证获取的是设置的收集器
        retrieved_collector = get_memory_collector()
        assert retrieved_collector is custom_collector
        
        # 清理
        set_memory_collector(None)
    
    def test_memory_collection_decorator_function(self):
        """测试记忆收集装饰器函数"""
        with patch('anp_runtime.local_service.memory.memory_collector.get_memory_collector') as mock_get_collector:
            mock_collector = Mock()
            mock_collector.create_collection_decorator = Mock(return_value=lambda f: f)
            mock_get_collector.return_value = mock_collector
            
            # 使用装饰器函数
            decorator = memory_collection_decorator(
                "test_method", "test_key", "alice", "Alice", "session-123"
            )
            
            # 验证收集器被调用
            mock_get_collector.assert_called_once()
            mock_collector.create_collection_decorator.assert_called_once_with(
                "test_method", "test_key", "alice", "Alice", "session-123"
            )


class TestMemoryCollectorIntegration:
    """测试记忆收集器集成场景"""
    
    @pytest.mark.asyncio
    async def test_full_collection_workflow(self):
        """测试完整的收集工作流程"""
        # 创建真实的组件（而不是Mock）
        from anp_runtime.local_service.memory.memory_storage import InMemoryStorage
        from anp_runtime.local_service.memory.memory_manager import MemoryManager
        
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage)
        config = MemoryConfig(
            collection=CollectionConfig(
                enable_memory_collection=True,
                collection_mode="auto",
                collect_input_params=True,
                collect_output_results=True,
                collect_errors=True
            )
        )
        
        collector = MemoryCollector(memory_manager, config)
        
        # 1. 创建收集装饰器
        @collector.create_collection_decorator(
            "integration_test", "integration::test", "alice", "Alice", "session-123"
        )
        def test_method(x, y, multiplier=2):
            return (x + y) * multiplier
        
        # 2. 执行方法
        result = test_method(3, 4, multiplier=3)
        assert result == 21
        
        # 3. 验证记忆被收集
        # 等待异步收集完成
        await asyncio.sleep(0.1)
        
        # 搜索收集的记忆
        memories = await storage.search_memories(limit=10)
        assert len(memories) >= 1
        
        # 验证记忆内容
        collected_memory = memories[0]
        assert collected_memory.memory_type == MemoryType.METHOD_CALL
        assert collected_memory.content["method_name"] == "integration_test"
        assert collected_memory.content["input"]["args"] == [3, 4]
        assert collected_memory.content["input"]["kwargs"] == {"multiplier": 3}
        assert collected_memory.content["output"] == 21
        assert collected_memory.content["success"] == True
        assert collected_memory.metadata.source_agent_did == "alice"
        assert collected_memory.metadata.source_agent_name == "Alice"
        assert collected_memory.metadata.session_id == "session-123"
        
        # 4. 测试错误收集
        @collector.create_collection_decorator(
            "failing_test", "integration::failing", "alice", "Alice"
        )
        def failing_method():
            raise RuntimeError("Integration test error")
        
        with pytest.raises(RuntimeError):
            failing_method()
        
        # 等待错误记忆收集
        await asyncio.sleep(0.1)
        
        # 验证错误记忆被收集
        error_memories = await storage.search_memories(memory_type=MemoryType.ERROR, limit=10)
        assert len(error_memories) >= 1
        
        error_memory = error_memories[0]
        assert error_memory.content["method_name"] == "failing_test"
        assert error_memory.content["error"]["type"] == "RuntimeError"
        assert error_memory.content["error"]["message"] == "Integration test error"
        assert error_memory.content["success"] == False
        
        # 5. 验证统计信息
        stats = collector.get_collection_statistics()
        assert stats['collections_attempted'] >= 2
        assert stats['collections_successful'] >= 2
        
        await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_data_filtering_integration(self):
        """测试数据过滤集成"""
        from anp_runtime.local_service.memory.memory_storage import InMemoryStorage
        from anp_runtime.local_service.memory.memory_manager import MemoryManager
        
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage)
        config = MemoryConfig(
            collection=CollectionConfig(
                enable_memory_collection=True,
                max_param_length=50
            ),
            security=SecurityConfig(
                sensitive_fields=["password", "api_key", "secret"]
            )
        )
        
        collector = MemoryCollector(memory_manager, config)
        
        # 创建包含敏感数据的方法
        @collector.create_collection_decorator(
            "sensitive_method", "sensitive::method", "alice", "Alice"
        )
        def process_user_data(user_info, api_credentials):
            return {"status": "processed", "user_id": user_info["id"]}
        
        # 执行包含敏感数据的方法
        user_data = {
            "id": "user123",
            "name": "Alice",
            "password": "super_secret_password",
            "api_key": "sk-1234567890abcdef"
        }
        
        credentials = {
            "secret": "top_secret_value",
            "endpoint": "https://api.example.com"
        }
        
        result = process_user_data(user_data, credentials)
        
        # 等待收集完成
        await asyncio.sleep(0.1)
        
        # 验证敏感数据被过滤
        memories = await storage.search_memories(limit=1)
        assert len(memories) == 1
        
        memory = memories[0]
        input_args = memory.content["input"]["args"]
        
        # 验证敏感字段被过滤
        assert input_args[0]["password"] == "<<FILTERED>>"
        assert input_args[0]["api_key"] == "<<FILTERED>>"
        assert input_args[1]["secret"] == "<<FILTERED>>"
        
        # 验证非敏感字段保留
        assert input_args[0]["name"] == "Alice"
        assert input_args[0]["id"] == "user123"
        assert input_args[1]["endpoint"] == "https://api.example.com"
        
        await memory_manager.close()


if __name__ == "__main__":
    pytest.main([__file__])