"""
记忆配置管理测试

测试 MemoryConfig、各种子配置类以及配置加载、保存、验证等功能
"""

import pytest
import json
import yaml
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from typing import Any, Dict

from anp_runtime.local_service.memory.memory_config import (
    StorageConfig,
    RecommendationConfig,
    CleanupConfig,
    PerformanceConfig,
    CollectionConfig,
    SecurityConfig,
    MemoryConfig,
    get_memory_config,
    set_memory_config,
    reload_memory_config
)


class TestStorageConfig:
    """测试存储配置"""
    
    def test_storage_config_defaults(self):
        """测试存储配置默认值"""
        config = StorageConfig()
        
        assert config.storage_type == "sqlite"
        assert config.database_path == "./data/memory.db"
        assert config.cache_size == 1000
        assert config.enable_persistence == True
        assert config.batch_write_size == 100
        assert config.enable_compression == False
    
    def test_storage_config_custom_values(self):
        """测试存储配置自定义值"""
        config = StorageConfig(
            storage_type="memory",
            database_path="/custom/path/db.sqlite",
            cache_size=2000,
            enable_persistence=False,
            batch_write_size=50,
            enable_compression=True
        )
        
        assert config.storage_type == "memory"
        assert config.database_path == "/custom/path/db.sqlite"
        assert config.cache_size == 2000
        assert config.enable_persistence == False
        assert config.batch_write_size == 50
        assert config.enable_compression == True


class TestRecommendationConfig:
    """测试推荐配置"""
    
    def test_recommendation_config_defaults(self):
        """测试推荐配置默认值"""
        config = RecommendationConfig()
        
        assert config.algorithm == "hybrid"
        assert config.max_recommendations == 10
        assert config.similarity_threshold == 0.5
        assert config.keyword_weight == 0.4
        assert config.tag_weight == 0.3
        assert config.time_weight == 0.2
        assert config.access_weight == 0.1
        assert config.enable_smart_recommendation == True
        
        # 验证权重总和为1.0
        total_weight = (config.keyword_weight + config.tag_weight + 
                       config.time_weight + config.access_weight)
        assert abs(total_weight - 1.0) < 0.001
    
    def test_recommendation_config_custom_values(self):
        """测试推荐配置自定义值"""
        config = RecommendationConfig(
            algorithm="keyword",
            max_recommendations=20,
            similarity_threshold=0.7,
            keyword_weight=0.5,
            tag_weight=0.25,
            time_weight=0.15,
            access_weight=0.1,
            enable_smart_recommendation=False
        )
        
        assert config.algorithm == "keyword"
        assert config.max_recommendations == 20
        assert config.similarity_threshold == 0.7
        assert config.keyword_weight == 0.5
        assert config.tag_weight == 0.25
        assert config.time_weight == 0.15
        assert config.access_weight == 0.1
        assert config.enable_smart_recommendation == False


class TestCleanupConfig:
    """测试清理配置"""
    
    def test_cleanup_config_defaults(self):
        """测试清理配置默认值"""
        config = CleanupConfig()
        
        assert config.enable_auto_cleanup == True
        assert config.cleanup_interval == 3600
        assert config.max_memory_entries == 10000
        assert config.default_expiry_time is None
        assert config.cleanup_strategy == "smart"
        assert config.low_access_threshold == 2
        assert config.retention_days == 30
    
    def test_cleanup_config_custom_values(self):
        """测试清理配置自定义值"""
        config = CleanupConfig(
            enable_auto_cleanup=False,
            cleanup_interval=7200,
            max_memory_entries=5000,
            default_expiry_time=86400,
            cleanup_strategy="lru",
            low_access_threshold=5,
            retention_days=60
        )
        
        assert config.enable_auto_cleanup == False
        assert config.cleanup_interval == 7200
        assert config.max_memory_entries == 5000
        assert config.default_expiry_time == 86400
        assert config.cleanup_strategy == "lru"
        assert config.low_access_threshold == 5
        assert config.retention_days == 60


class TestPerformanceConfig:
    """测试性能配置"""
    
    def test_performance_config_defaults(self):
        """测试性能配置默认值"""
        config = PerformanceConfig()
        
        assert config.enable_async_operations == True
        assert config.thread_pool_size == 4
        assert config.search_index_type == "simple"
        assert config.enable_search_cache == True
        assert config.search_cache_size == 100
        assert config.operation_timeout == 30
    
    def test_performance_config_custom_values(self):
        """测试性能配置自定义值"""
        config = PerformanceConfig(
            enable_async_operations=False,
            thread_pool_size=8,
            search_index_type="advanced",
            enable_search_cache=False,
            search_cache_size=200,
            operation_timeout=60
        )
        
        assert config.enable_async_operations == False
        assert config.thread_pool_size == 8
        assert config.search_index_type == "advanced"
        assert config.enable_search_cache == False
        assert config.search_cache_size == 200
        assert config.operation_timeout == 60


class TestCollectionConfig:
    """测试收集配置"""
    
    def test_collection_config_defaults(self):
        """测试收集配置默认值"""
        config = CollectionConfig()
        
        assert config.enable_memory_collection == False
        assert config.collection_mode == "selective"
        assert config.auto_collect_methods == []
        assert config.collection_filters == {}
        assert config.collect_input_params == True
        assert config.collect_output_results == True
        assert config.collect_errors == True
        assert config.max_param_length == 1000
    
    def test_collection_config_custom_values(self):
        """测试收集配置自定义值"""
        config = CollectionConfig(
            enable_memory_collection=True,
            collection_mode="auto",
            auto_collect_methods=["method1", "method2"],
            collection_filters={"include": ["pattern1"], "exclude": ["pattern2"]},
            collect_input_params=False,
            collect_output_results=False,
            collect_errors=False,
            max_param_length=500
        )
        
        assert config.enable_memory_collection == True
        assert config.collection_mode == "auto"
        assert config.auto_collect_methods == ["method1", "method2"]
        assert config.collection_filters == {"include": ["pattern1"], "exclude": ["pattern2"]}
        assert config.collect_input_params == False
        assert config.collect_output_results == False
        assert config.collect_errors == False
        assert config.max_param_length == 500


class TestSecurityConfig:
    """测试安全配置"""
    
    def test_security_config_defaults(self):
        """测试安全配置默认值"""
        config = SecurityConfig()
        
        assert config.enable_encryption == False
        assert config.encryption_key is None
        assert config.sensitive_fields == ["password", "token", "secret"]
        assert config.enable_access_control == True
        assert config.allowed_agents == []
    
    def test_security_config_custom_values(self):
        """测试安全配置自定义值"""
        config = SecurityConfig(
            enable_encryption=True,
            encryption_key="test-key-123",
            sensitive_fields=["password", "api_key", "private_key"],
            enable_access_control=False,
            allowed_agents=["agent1", "agent2"]
        )
        
        assert config.enable_encryption == True
        assert config.encryption_key == "test-key-123"
        assert config.sensitive_fields == ["password", "api_key", "private_key"]
        assert config.enable_access_control == False
        assert config.allowed_agents == ["agent1", "agent2"]


class TestMemoryConfig:
    """测试主记忆配置"""
    
    def test_memory_config_defaults(self):
        """测试记忆配置默认值"""
        config = MemoryConfig()
        
        assert config.enabled == False
        assert config.version == "1.0.0"
        assert isinstance(config.storage, StorageConfig)
        assert isinstance(config.recommendation, RecommendationConfig)
        assert isinstance(config.cleanup, CleanupConfig)
        assert isinstance(config.performance, PerformanceConfig)
        assert isinstance(config.collection, CollectionConfig)
        assert isinstance(config.security, SecurityConfig)
        assert config.extensions == {}
    
    def test_memory_config_custom_values(self):
        """测试记忆配置自定义值"""
        custom_storage = StorageConfig(storage_type="memory")
        custom_recommendation = RecommendationConfig(algorithm="keyword")
        
        config = MemoryConfig(
            enabled=True,
            version="2.0.0",
            storage=custom_storage,
            recommendation=custom_recommendation,
            extensions={"custom_feature": True}
        )
        
        assert config.enabled == True
        assert config.version == "2.0.0"
        assert config.storage == custom_storage
        assert config.recommendation == custom_recommendation
        assert config.extensions == {"custom_feature": True}
    
    @patch('pathlib.Path.mkdir')
    def test_memory_config_post_init(self, mock_mkdir):
        """测试初始化后处理"""
        config = MemoryConfig()
        config.storage.database_path = "/test/path/db.sqlite"
        config.__post_init__()
        
        # 验证目录创建被调用
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    def test_to_dict(self):
        """测试转换为字典"""
        config = MemoryConfig(
            enabled=True,
            version="1.0.0",
            extensions={"test": "value"}
        )
        
        data = config.to_dict()
        
        # 验证基本字段
        assert data["enabled"] == True
        assert data["version"] == "1.0.0"
        assert data["extensions"] == {"test": "value"}
        
        # 验证子配置存在
        assert "storage" in data
        assert "recommendation" in data
        assert "cleanup" in data
        assert "performance" in data
        assert "collection" in data
        assert "security" in data
        
        # 验证子配置字段
        assert data["storage"]["storage_type"] == "sqlite"
        assert data["recommendation"]["algorithm"] == "hybrid"
        assert data["cleanup"]["cleanup_strategy"] == "smart"
    
    def test_from_dict_basic(self):
        """测试从字典创建配置"""
        data = {
            "enabled": True,
            "version": "2.0.0",
            "storage": {
                "storage_type": "memory",
                "cache_size": 2000
            },
            "recommendation": {
                "algorithm": "keyword",
                "max_recommendations": 20
            },
            "extensions": {"feature1": True}
        }
        
        config = MemoryConfig.from_dict(data)
        
        assert config.enabled == True
        assert config.version == "2.0.0"
        assert config.storage.storage_type == "memory"
        assert config.storage.cache_size == 2000
        assert config.recommendation.algorithm == "keyword"
        assert config.recommendation.max_recommendations == 20
        assert config.extensions == {"feature1": True}
    
    def test_from_dict_partial(self):
        """测试从部分字典创建配置"""
        data = {
            "enabled": True,
            "storage": {
                "storage_type": "memory"
                # 缺少其他存储配置字段
            }
        }
        
        config = MemoryConfig.from_dict(data)
        
        assert config.enabled == True
        assert config.storage.storage_type == "memory"
        # 其他字段应该使用默认值
        assert config.storage.cache_size == 1000
        assert config.version == "1.0.0"
    
    def test_from_dict_empty(self):
        """测试从空字典创建配置"""
        config = MemoryConfig.from_dict({})
        
        # 所有字段都应该使用默认值
        assert config.enabled == False
        assert config.version == "1.0.0"
        assert config.storage.storage_type == "sqlite"
    
    def test_update_from_dict_basic(self):
        """测试从字典更新配置"""
        config = MemoryConfig()
        original_storage_cache = config.storage.cache_size
        
        updates = {
            "enabled": True,
            "storage": {
                "cache_size": 5000
            },
            "recommendation": {
                "algorithm": "keyword"
            },
            "extensions": {"new_feature": True}
        }
        
        config.update_from_dict(updates)
        
        assert config.enabled == True
        assert config.storage.cache_size == 5000
        assert config.storage.storage_type == "sqlite"  # 未更新的字段保持原值
        assert config.recommendation.algorithm == "keyword"
        assert config.extensions == {"new_feature": True}
    
    def test_update_from_dict_partial(self):
        """测试部分字段更新"""
        config = MemoryConfig()
        config.extensions = {"existing": "value"}
        
        updates = {
            "storage": {
                "cache_size": 3000
            },
            "extensions": {"new": "value"}
        }
        
        config.update_from_dict(updates)
        
        assert config.storage.cache_size == 3000
        assert config.storage.storage_type == "sqlite"  # 未更新
        # extensions应该被新值替换，不是合并
        assert config.extensions == {"existing": "value", "new": "value"}
    
    def test_update_from_dict_invalid_attributes(self):
        """测试更新不存在的属性"""
        config = MemoryConfig()
        
        updates = {
            "storage": {
                "invalid_field": "value",
                "cache_size": 2000
            }
        }
        
        config.update_from_dict(updates)
        
        # 有效字段应该更新
        assert config.storage.cache_size == 2000
        # 无效字段应该被忽略
        assert not hasattr(config.storage, "invalid_field")


class TestMemoryConfigValidation:
    """测试记忆配置验证"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config = MemoryConfig()
        
        errors = config.validate()
        assert len(errors) == 0
        assert config.is_valid() == True
    
    def test_invalid_storage_type(self):
        """测试无效存储类型"""
        config = MemoryConfig()
        config.storage.storage_type = "invalid_type"
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("不支持的存储类型" in error for error in errors)
        assert config.is_valid() == False
    
    def test_invalid_cache_size(self):
        """测试无效缓存大小"""
        config = MemoryConfig()
        config.storage.cache_size = 0
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("缓存大小必须大于0" in error for error in errors)
    
    def test_invalid_recommendation_algorithm(self):
        """测试无效推荐算法"""
        config = MemoryConfig()
        config.recommendation.algorithm = "invalid_algorithm"
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("不支持的推荐算法" in error for error in errors)
    
    def test_invalid_similarity_threshold(self):
        """测试无效相似度阈值"""
        config = MemoryConfig()
        config.recommendation.similarity_threshold = 1.5
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("相似度阈值必须在0-1之间" in error for error in errors)
        
        # 测试负值
        config.recommendation.similarity_threshold = -0.1
        errors = config.validate()
        assert len(errors) > 0
        assert any("相似度阈值必须在0-1之间" in error for error in errors)
    
    def test_invalid_weight_sum(self):
        """测试无效权重总和"""
        config = MemoryConfig()
        config.recommendation.keyword_weight = 0.5
        config.recommendation.tag_weight = 0.5
        config.recommendation.time_weight = 0.3  # 总和超过1.0
        config.recommendation.access_weight = 0.1
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("推荐权重总和应为1.0" in error for error in errors)
    
    def test_invalid_cleanup_strategy(self):
        """测试无效清理策略"""
        config = MemoryConfig()
        config.cleanup.cleanup_strategy = "invalid_strategy"
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("不支持的清理策略" in error for error in errors)
    
    def test_invalid_max_memory_entries(self):
        """测试无效最大记忆条目数"""
        config = MemoryConfig()
        config.cleanup.max_memory_entries = -1
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("最大记忆条目数量必须大于0" in error for error in errors)
    
    def test_invalid_search_index_type(self):
        """测试无效搜索索引类型"""
        config = MemoryConfig()
        config.performance.search_index_type = "invalid_type"
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("不支持的搜索索引类型" in error for error in errors)
    
    def test_invalid_thread_pool_size(self):
        """测试无效线程池大小"""
        config = MemoryConfig()
        config.performance.thread_pool_size = 0
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("线程池大小必须大于0" in error for error in errors)
    
    def test_invalid_collection_mode(self):
        """测试无效收集模式"""
        config = MemoryConfig()
        config.collection.collection_mode = "invalid_mode"
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("不支持的收集模式" in error for error in errors)
    
    def test_multiple_validation_errors(self):
        """测试多个验证错误"""
        config = MemoryConfig()
        config.storage.storage_type = "invalid"
        config.recommendation.algorithm = "invalid"
        config.cleanup.cleanup_strategy = "invalid"
        
        errors = config.validate()
        assert len(errors) >= 3
        assert config.is_valid() == False


class TestMemoryConfigFileOperations:
    """测试配置文件操作"""
    
    def test_save_to_file_json(self):
        """测试保存为JSON文件"""
        config = MemoryConfig(enabled=True, version="2.0.0")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            config.save_to_file(temp_path, format='json')
            
            # 验证文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            assert data["enabled"] == True
            assert data["version"] == "2.0.0"
            assert "storage" in data
            assert "recommendation" in data
        finally:
            os.unlink(temp_path)
    
    def test_save_to_file_yaml(self):
        """测试保存为YAML文件"""
        config = MemoryConfig(enabled=True, version="2.0.0")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            config.save_to_file(temp_path, format='yaml')
            
            # 验证文件内容
            with open(temp_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            assert data["enabled"] == True
            assert data["version"] == "2.0.0"
            assert "storage" in data
            assert "recommendation" in data
        finally:
            os.unlink(temp_path)
    
    def test_save_to_file_auto_format(self):
        """测试自动格式检测保存"""
        config = MemoryConfig(enabled=True)
        
        # 测试YAML扩展名
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            temp_path = f.name
        
        try:
            config.save_to_file(temp_path, format='auto')
            
            with open(temp_path, 'r', encoding='utf-8') as f:
                content = f.read()
                # YAML格式应该包含缩进和冒号
                assert "enabled: true" in content
        finally:
            os.unlink(temp_path)
    
    def test_load_from_file_json(self):
        """测试从JSON文件加载"""
        test_data = {
            "enabled": True,
            "version": "2.0.0",
            "storage": {
                "storage_type": "memory",
                "cache_size": 2000
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name
        
        try:
            config = MemoryConfig.load_from_file(temp_path)
            
            assert config.enabled == True
            assert config.version == "2.0.0"
            assert config.storage.storage_type == "memory"
            assert config.storage.cache_size == 2000
        finally:
            os.unlink(temp_path)
    
    def test_load_from_file_yaml(self):
        """测试从YAML文件加载"""
        test_data = {
            "enabled": True,
            "version": "2.0.0",
            "storage": {
                "storage_type": "memory",
                "cache_size": 2000
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_data, f)
            temp_path = f.name
        
        try:
            config = MemoryConfig.load_from_file(temp_path)
            
            assert config.enabled == True
            assert config.version == "2.0.0"
            assert config.storage.storage_type == "memory"
            assert config.storage.cache_size == 2000
        finally:
            os.unlink(temp_path)
    
    def test_load_from_nonexistent_file(self):
        """测试从不存在的文件加载"""
        temp_path = "/tmp/nonexistent_config.yaml"
        
        # 确保文件不存在
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        
        config = MemoryConfig.load_from_file(temp_path)
        
        # 应该返回默认配置
        assert config.enabled == False
        assert config.version == "1.0.0"
        
        # 应该创建了默认配置文件
        assert os.path.exists(temp_path)
        
        # 清理
        if os.path.exists(temp_path):
            os.unlink(temp_path)
    
    @patch('builtins.open', side_effect=IOError("Permission denied"))
    def test_load_from_file_io_error(self, mock_open):
        """测试文件读取IO错误"""
        with pytest.raises(IOError):
            MemoryConfig.load_from_file("/some/path/config.yaml")
    
    def test_load_from_file_invalid_json(self):
        """测试加载无效JSON文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json")
            temp_path = f.name
        
        try:
            with pytest.raises(json.JSONDecodeError):
                MemoryConfig.load_from_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_load_from_file_invalid_yaml(self):
        """测试加载无效YAML文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name
        
        try:
            with pytest.raises(yaml.YAMLError):
                MemoryConfig.load_from_file(temp_path)
        finally:
            os.unlink(temp_path)


class TestGlobalMemoryConfig:
    """测试全局配置管理"""
    
    def test_get_memory_config_default(self):
        """测试获取默认全局配置"""
        # 清除全局配置
        with patch('anp_runtime.local_service.memory.memory_config._global_config', None):
            with patch.dict(os.environ, {}, clear=True):
                with patch('anp_runtime.local_service.memory.memory_config.MemoryConfig.load_from_file') as mock_load:
                    mock_config = MemoryConfig(enabled=True)
                    mock_load.return_value = mock_config
                    
                    config = get_memory_config()
                    
                    assert config == mock_config
                    mock_load.assert_called_once_with('./data/memory_config.yaml')
    
    def test_get_memory_config_from_env(self):
        """测试从环境变量获取配置"""
        with patch('anp_runtime.local_service.memory.memory_config._global_config', None):
            with patch.dict(os.environ, {'ANP_MEMORY_CONFIG_PATH': '/custom/config.yaml'}):
                with patch('anp_runtime.local_service.memory.memory_config.MemoryConfig.load_from_file') as mock_load:
                    mock_config = MemoryConfig(enabled=True)
                    mock_load.return_value = mock_config
                    
                    config = get_memory_config()
                    
                    assert config == mock_config
                    mock_load.assert_called_once_with('/custom/config.yaml')
    
    def test_get_memory_config_singleton(self):
        """测试全局配置单例模式"""
        # 清除全局配置
        with patch('anp_runtime.local_service.memory.memory_config._global_config', None):
            with patch('anp_runtime.local_service.memory.memory_config.MemoryConfig.load_from_file') as mock_load:
                mock_config = MemoryConfig(enabled=True)
                mock_load.return_value = mock_config
                
                # 第一次调用应该加载配置
                config1 = get_memory_config()
                assert config1 == mock_config
                assert mock_load.call_count == 1
                
                # 第二次调用应该返回缓存的配置
                config2 = get_memory_config()
                assert config2 == mock_config
                assert config1 is config2
                assert mock_load.call_count == 1  # 不应该再次调用
    
    def test_set_memory_config(self):
        """测试设置全局配置"""
        custom_config = MemoryConfig(enabled=True, version="custom")
        
        set_memory_config(custom_config)
        
        # 获取的配置应该是设置的配置
        config = get_memory_config()
        assert config is custom_config
        assert config.enabled == True
        assert config.version == "custom"
    
    def test_reload_memory_config_default_path(self):
        """测试重新加载配置（默认路径）"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('anp_runtime.local_service.memory.memory_config.MemoryConfig.load_from_file') as mock_load:
                mock_config = MemoryConfig(enabled=True, version="reloaded")
                mock_load.return_value = mock_config
                
                config = reload_memory_config()
                
                assert config == mock_config
                mock_load.assert_called_once_with('./data/memory_config.yaml')
    
    def test_reload_memory_config_custom_path(self):
        """测试重新加载配置（自定义路径）"""
        with patch('anp_runtime.local_service.memory.memory_config.MemoryConfig.load_from_file') as mock_load:
            mock_config = MemoryConfig(enabled=True, version="reloaded")
            mock_load.return_value = mock_config
            
            config = reload_memory_config('/custom/config.yaml')
            
            assert config == mock_config
            mock_load.assert_called_once_with('/custom/config.yaml')
    
    def test_reload_memory_config_from_env(self):
        """测试从环境变量重新加载配置"""
        with patch.dict(os.environ, {'ANP_MEMORY_CONFIG_PATH': '/env/config.yaml'}):
            with patch('anp_runtime.local_service.memory.memory_config.MemoryConfig.load_from_file') as mock_load:
                mock_config = MemoryConfig(enabled=True, version="env-reloaded")
                mock_load.return_value = mock_config
                
                config = reload_memory_config()
                
                assert config == mock_config
                mock_load.assert_called_once_with('/env/config.yaml')


class TestMemoryConfigIntegration:
    """测试配置集成场景"""
    
    def test_complete_config_workflow(self):
        """测试完整的配置工作流程"""
        # 1. 创建自定义配置
        config = MemoryConfig(
            enabled=True,
            version="test-1.0",
            storage=StorageConfig(
                storage_type="memory",
                cache_size=5000
            ),
            recommendation=RecommendationConfig(
                algorithm="keyword",
                max_recommendations=20
            ),
            extensions={"test_feature": True}
        )
        
        # 2. 验证配置
        assert config.is_valid() == True
        
        # 3. 转换为字典
        config_dict = config.to_dict()
        assert config_dict["enabled"] == True
        assert config_dict["storage"]["storage_type"] == "memory"
        
        # 4. 从字典重建配置
        restored_config = MemoryConfig.from_dict(config_dict)
        assert restored_config.enabled == True
        assert restored_config.storage.storage_type == "memory"
        assert restored_config.storage.cache_size == 5000
        assert restored_config.recommendation.algorithm == "keyword"
        
        # 5. 部分更新配置
        updates = {
            "storage": {"cache_size": 8000},
            "recommendation": {"max_recommendations": 30}
        }
        restored_config.update_from_dict(updates)
        
        assert restored_config.storage.cache_size == 8000
        assert restored_config.recommendation.max_recommendations == 30
        assert restored_config.storage.storage_type == "memory"  # 未更新的字段保持不变
    
    def test_config_file_roundtrip_json(self):
        """测试JSON配置文件往返"""
        original_config = MemoryConfig(
            enabled=True,
            version="roundtrip-test",
            storage=StorageConfig(storage_type="memory", cache_size=3000),
            collection=CollectionConfig(
                enable_memory_collection=True,
                auto_collect_methods=["test1", "test2"]
            )
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            # 保存配置
            original_config.save_to_file(temp_path)
            
            # 加载配置
            loaded_config = MemoryConfig.load_from_file(temp_path)
            
            # 验证配置完整性
            assert loaded_config.enabled == original_config.enabled
            assert loaded_config.version == original_config.version
            assert loaded_config.storage.storage_type == original_config.storage.storage_type
            assert loaded_config.storage.cache_size == original_config.storage.cache_size
            assert loaded_config.collection.enable_memory_collection == original_config.collection.enable_memory_collection
            assert loaded_config.collection.auto_collect_methods == original_config.collection.auto_collect_methods
        finally:
            os.unlink(temp_path)
    
    def test_config_file_roundtrip_yaml(self):
        """测试YAML配置文件往返"""
        original_config = MemoryConfig(
            enabled=True,
            version="yaml-roundtrip",
            security=SecurityConfig(
                enable_encryption=True,
                sensitive_fields=["custom_field", "password"]
            )
        )
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            # 保存配置
            original_config.save_to_file(temp_path)
            
            # 加载配置
            loaded_config = MemoryConfig.load_from_file(temp_path)
            
            # 验证配置完整性
            assert loaded_config.enabled == original_config.enabled
            assert loaded_config.version == original_config.version
            assert loaded_config.security.enable_encryption == original_config.security.enable_encryption
            assert loaded_config.security.sensitive_fields == original_config.security.sensitive_fields
        finally:
            os.unlink(temp_path)
    
    def test_config_validation_comprehensive(self):
        """测试综合配置验证"""
        # 创建一个有多个问题的配置
        config = MemoryConfig()
        
        # 设置多个无效值
        config.storage.storage_type = "unsupported"
        config.storage.cache_size = -100
        config.recommendation.algorithm = "unknown"
        config.recommendation.similarity_threshold = 2.0
        config.recommendation.keyword_weight = 0.6
        config.recommendation.tag_weight = 0.6  # 权重总和超过1.0
        config.cleanup.cleanup_strategy = "invalid"
        config.cleanup.max_memory_entries = 0
        config.performance.search_index_type = "unknown"
        config.performance.thread_pool_size = -1
        config.collection.collection_mode = "invalid"
        
        # 执行验证
        errors = config.validate()
        
        # 应该有多个错误
        assert len(errors) >= 9  # 至少9种不同的错误类型
        assert config.is_valid() == False
        
        # 验证错误信息包含预期内容
        error_text = " ".join(errors)
        assert "不支持的存储类型" in error_text
        assert "缓存大小必须大于0" in error_text
        assert "不支持的推荐算法" in error_text
        assert "相似度阈值必须在0-1之间" in error_text
        assert "推荐权重总和应为1.0" in error_text
        assert "不支持的清理策略" in error_text
        assert "最大记忆条目数量必须大于0" in error_text
        assert "不支持的搜索索引类型" in error_text
        assert "线程池大小必须大于0" in error_text
        assert "不支持的收集模式" in error_text


if __name__ == "__main__":
    pytest.main([__file__])