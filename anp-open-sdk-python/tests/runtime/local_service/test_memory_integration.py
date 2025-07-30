"""
测试记忆功能与本地方法装饰器的集成

验证重构后的 @local_method 装饰器能否正确处理记忆功能
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

# 导入被测试的模块
from anp_runtime.local_service.local_methods_decorators import (
    local_method,
    LOCAL_METHODS_REGISTRY,
    get_method_memory_config,
    list_memory_enabled_methods
)

try:
    from anp_runtime.local_service.memory import MemoryOptions, memory_enabled, memory_disabled
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    MemoryOptions = None


class TestMemoryIntegration:
    """测试记忆功能集成"""
    
    def setup_method(self):
        """每个测试前的设置"""
        # 清空注册表
        LOCAL_METHODS_REGISTRY.clear()
    
    def test_local_method_without_memory(self):
        """测试不启用记忆的本地方法"""
        
        @local_method("简单计算")
        def add(a, b):
            return a + b
        
        # 验证装饰器正常工作
        assert add(2, 3) == 5
        assert hasattr(add, '_is_local_method')
        assert add._is_local_method is True
        
        # 验证方法信息
        method_info = add._method_info
        assert method_info['name'] == 'add'
        assert method_info['description'] == '简单计算'
        assert method_info['is_async'] is False
    
    def test_local_method_with_simple_memory_config(self):
        """测试使用简单记忆配置的本地方法"""
        
        @local_method("计算乘法", memory=True)
        def multiply(x, y):
            return x * y
        
        # 验证装饰器正常工作
        assert multiply(3, 4) == 12
        
        # 验证记忆配置
        method_info = multiply._method_info
        memory_config = method_info.get('memory_config')
        
        if MEMORY_AVAILABLE:
            assert memory_config is not None
            assert memory_config.get('enabled') is True
        else:
            # 如果记忆模块不可用，配置应为None
            assert memory_config is None
    
    @pytest.mark.skipif(not MEMORY_AVAILABLE, reason="Memory module not available")
    def test_local_method_with_memory_options(self):
        """测试使用完整MemoryOptions的本地方法"""
        
        memory_opts = MemoryOptions(
            enabled=True,
            tags=["math", "calculation"],
            keywords=["division"],
            collect_input=True,
            collect_output=True,
            collect_errors=False
        )
        
        @local_method("计算除法", memory=memory_opts)
        def divide(a, b):
            if b == 0:
                raise ValueError("Division by zero")
            return a / b
        
        # 验证装饰器正常工作
        assert divide(10, 2) == 5.0
        
        # 验证记忆配置
        method_info = divide._method_info
        memory_config = method_info.get('memory_config')
        
        assert memory_config is not None
        assert memory_config.get('enabled') is True
        assert memory_config.get('tags') == ["math", "calculation"]
        assert memory_config.get('keywords') == ["division"]
        assert memory_config.get('collect_input') is True
        assert memory_config.get('collect_output') is True
        assert memory_config.get('collect_errors') is False
    
    def test_local_method_with_dict_memory_config(self):
        """测试使用字典配置记忆的本地方法"""
        
        @local_method("字符串处理", memory={
            "enabled": True,
            "tags": ["text", "processing"],
            "collect_input": True,
            "collect_output": False
        })
        def process_text(text):
            return text.upper()
        
        # 验证装饰器正常工作
        assert process_text("hello") == "HELLO"
        
        # 验证记忆配置
        method_info = process_text._method_info
        memory_config = method_info.get('memory_config')
        
        if MEMORY_AVAILABLE:
            assert memory_config is not None
            assert memory_config.get('enabled') is True
            assert memory_config.get('tags') == ["text", "processing"]
            assert memory_config.get('collect_input') is True
            assert memory_config.get('collect_output') is False
    
    def test_backward_compatibility(self):
        """测试向后兼容性 - 使用旧的参数格式"""
        
        @local_method(
            "旧式配置",
            enable_memory=True,
            memory_tags=["legacy"],
            memory_keywords=["old"],
            collect_input=True,
            collect_output=True,
            collect_errors=False
        )
        def old_style_method(data):
            return len(data)
        
        # 验证装饰器正常工作
        assert old_style_method([1, 2, 3]) == 3
        
        # 验证记忆配置被正确转换
        method_info = old_style_method._method_info
        memory_config = method_info.get('memory_config')
        
        if MEMORY_AVAILABLE:
            assert memory_config is not None
            assert memory_config.get('enabled') is True
            assert memory_config.get('tags') == ["legacy"]
            assert memory_config.get('keywords') == ["old"]
            assert memory_config.get('collect_input') is True
            assert memory_config.get('collect_output') is True
            assert memory_config.get('collect_errors') is False
    
    def test_async_method_with_memory(self):
        """测试异步方法的记忆功能"""
        
        @local_method("异步计算", memory=True)
        async def async_compute(n):
            await asyncio.sleep(0.01)  # 模拟异步操作
            return n * 2
        
        # 验证装饰器正常工作
        result = asyncio.run(async_compute(5))
        assert result == 10
        
        # 验证方法信息
        method_info = async_compute._method_info
        assert method_info['is_async'] is True
        
        # 验证记忆配置
        memory_config = method_info.get('memory_config')
        if MEMORY_AVAILABLE:
            assert memory_config is not None
            assert memory_config.get('enabled') is True
    
    def test_memory_disabled(self):
        """测试禁用记忆的方法"""
        
        @local_method("禁用记忆", memory=False)
        def no_memory_method(x):
            return x + 1
        
        # 验证装饰器正常工作
        assert no_memory_method(5) == 6
        
        # 验证记忆配置
        method_info = no_memory_method._method_info
        memory_config = method_info.get('memory_config')
        
        if MEMORY_AVAILABLE:
            assert memory_config is not None
            assert memory_config.get('enabled') is False
        else:
            assert memory_config is None
    
    def test_method_registry_integration(self):
        """测试方法注册表集成"""
        
        @local_method("注册测试", memory=True)
        def registry_test(value):
            return value
        
        # 模拟Agent注册过程
        mock_agent = Mock()
        mock_agent.anp_user_did = "test-agent-did"
        mock_agent.name = "TestAgent"
        
        from anp_runtime.local_service.local_methods_decorators import register_local_methods_to_agent
        
        # 注册方法到Agent
        module_dict = {'registry_test': registry_test}
        count = register_local_methods_to_agent(mock_agent, module_dict)
        
        assert count == 1
        
        # 验证注册表中的信息
        method_key = f"{registry_test._method_info['module']}::registry_test"
        assert method_key in LOCAL_METHODS_REGISTRY
        
        registered_info = LOCAL_METHODS_REGISTRY[method_key]
        assert registered_info['agent_did'] == "test-agent-did"
        assert registered_info['agent_name'] == "TestAgent"
        assert registered_info['name'] == 'registry_test'
    
    def test_utility_functions(self):
        """测试工具函数"""
        
        @local_method("工具测试", memory=True)
        def utility_test():
            return "test"
        
        # 模拟注册
        mock_agent = Mock()
        mock_agent.anp_user_did = "util-agent"
        mock_agent.name = "UtilAgent"
        
        from anp_runtime.local_service.local_methods_decorators import register_local_methods_to_agent
        register_local_methods_to_agent(mock_agent, {'utility_test': utility_test})
        
        method_key = f"{utility_test._method_info['module']}::utility_test"
        
        # 测试 get_method_memory_config
        config = get_method_memory_config(method_key)
        if MEMORY_AVAILABLE:
            assert config is not None
            assert config.get('enabled') is True
        
        # 测试 list_memory_enabled_methods
        enabled_methods = list_memory_enabled_methods()
        if MEMORY_AVAILABLE:
            assert method_key in enabled_methods
        else:
            assert len(enabled_methods) == 0


class TestErrorHandling:
    """测试错误处理"""
    
    def test_invalid_memory_config(self):
        """测试无效的记忆配置"""
        
        # 这不应该引发异常，而应该优雅地处理
        @local_method("无效配置", memory="invalid")
        def invalid_config_method():
            return "test"
        
        # 方法应该仍然可以正常工作
        assert invalid_config_method() == "test"
    
    def test_missing_memory_module(self):
        """测试记忆模块缺失的情况"""
        
        # 即使记忆模块不可用，装饰器也应该正常工作
        @local_method("缺失模块测试", memory=True)
        def missing_module_test():
            return "works"
        
        assert missing_module_test() == "works"
        assert hasattr(missing_module_test, '_is_local_method')


if __name__ == "__main__":
    pytest.main([__file__, '-v'])