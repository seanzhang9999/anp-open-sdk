"""
记忆功能配置管理

提供记忆功能的配置选项和参数管理
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import json
import yaml


@dataclass
class StorageConfig:
    """存储配置"""
    # 存储类型 (sqlite, memory, file)
    storage_type: str = "sqlite"
    
    # 数据库文件路径
    database_path: str = "./data/memory.db"
    
    # 内存缓存大小 (记忆条目数量)
    cache_size: int = 1000
    
    # 是否启用持久化
    enable_persistence: bool = True
    
    # 批量写入大小
    batch_write_size: int = 100
    
    # 数据压缩
    enable_compression: bool = False


@dataclass
class RecommendationConfig:
    """推荐配置"""
    # 推荐算法类型 (keyword, similarity, hybrid)
    algorithm: str = "hybrid"
    
    # 推荐结果数量
    max_recommendations: int = 10
    
    # 相似度阈值
    similarity_threshold: float = 0.5
    
    # 关键词权重
    keyword_weight: float = 0.4
    
    # 标签权重
    tag_weight: float = 0.3
    
    # 时间权重 (越新权重越高)
    time_weight: float = 0.2
    
    # 访问频次权重
    access_weight: float = 0.1
    
    # 是否启用智能推荐
    enable_smart_recommendation: bool = True


@dataclass
class CleanupConfig:
    """清理配置"""
    # 是否启用自动清理
    enable_auto_cleanup: bool = True
    
    # 清理间隔 (秒)
    cleanup_interval: int = 3600  # 1小时
    
    # 最大记忆条目数量
    max_memory_entries: int = 10000
    
    # 记忆过期时间 (秒)，None表示永不过期
    default_expiry_time: Optional[int] = None
    
    # 清理策略 (lru, lfu, time_based, smart)
    cleanup_strategy: str = "smart"
    
    # 低访问频次阈值 (清理时使用)
    low_access_threshold: int = 2
    
    # 保留时间 (天)
    retention_days: int = 30


@dataclass
class PerformanceConfig:
    """性能配置"""
    # 是否启用异步操作
    enable_async_operations: bool = True
    
    # 线程池大小
    thread_pool_size: int = 4
    
    # 搜索索引类型 (simple, advanced)
    search_index_type: str = "simple"
    
    # 是否启用搜索缓存
    enable_search_cache: bool = True
    
    # 搜索缓存大小
    search_cache_size: int = 100
    
    # 操作超时时间 (秒)
    operation_timeout: int = 30


@dataclass
class CollectionConfig:
    """收集配置"""
    # 是否启用记忆收集
    enable_memory_collection: bool = False
    
    # 收集模式 (auto, manual, selective)
    collection_mode: str = "selective"
    
    # 自动收集的方法类型
    auto_collect_methods: List[str] = field(default_factory=list)
    
    # 收集过滤器
    collection_filters: Dict[str, Any] = field(default_factory=dict)
    
    # 是否收集输入参数
    collect_input_params: bool = True
    
    # 是否收集输出结果
    collect_output_results: bool = True
    
    # 是否收集错误信息
    collect_errors: bool = True
    
    # 最大参数长度 (字符数，超过则截断)
    max_param_length: int = 1000


@dataclass
class SecurityConfig:
    """安全配置"""
    # 是否启用数据加密
    enable_encryption: bool = False
    
    # 加密密钥
    encryption_key: Optional[str] = None
    
    # 敏感数据字段
    sensitive_fields: List[str] = field(default_factory=lambda: ["password", "token", "secret"])
    
    # 是否启用访问控制
    enable_access_control: bool = True
    
    # 允许访问的Agent DID列表 (空表示允许所有)
    allowed_agents: List[str] = field(default_factory=list)


@dataclass
class MemoryConfig:
    """记忆功能主配置"""
    # 是否启用记忆功能
    enabled: bool = False
    
    # 配置版本
    version: str = "1.0.0"
    
    # 子配置
    storage: StorageConfig = field(default_factory=StorageConfig)
    recommendation: RecommendationConfig = field(default_factory=RecommendationConfig)
    cleanup: CleanupConfig = field(default_factory=CleanupConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    collection: CollectionConfig = field(default_factory=CollectionConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    
    # 扩展配置
    extensions: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保数据库路径存在
        if self.storage.database_path:
            db_dir = Path(self.storage.database_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def load_from_file(cls, config_path: str) -> 'MemoryConfig':
        """从文件加载配置"""
        config_file = Path(config_path)
        
        if not config_file.exists():
            # 配置文件不存在，返回默认配置
            config = cls()
            config.save_to_file(config_path)  # 保存默认配置
            return config
        
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryConfig':
        """从字典创建配置"""
        storage_data = data.get('storage', {})
        storage = StorageConfig(
            storage_type=storage_data.get('storage_type', 'sqlite'),
            database_path=storage_data.get('database_path', './data/memory.db'),
            cache_size=storage_data.get('cache_size', 1000),
            enable_persistence=storage_data.get('enable_persistence', True),
            batch_write_size=storage_data.get('batch_write_size', 100),
            enable_compression=storage_data.get('enable_compression', False)
        )
        
        recommendation_data = data.get('recommendation', {})
        recommendation = RecommendationConfig(
            algorithm=recommendation_data.get('algorithm', 'hybrid'),
            max_recommendations=recommendation_data.get('max_recommendations', 10),
            similarity_threshold=recommendation_data.get('similarity_threshold', 0.5),
            keyword_weight=recommendation_data.get('keyword_weight', 0.4),
            tag_weight=recommendation_data.get('tag_weight', 0.3),
            time_weight=recommendation_data.get('time_weight', 0.2),
            access_weight=recommendation_data.get('access_weight', 0.1),
            enable_smart_recommendation=recommendation_data.get('enable_smart_recommendation', True)
        )
        
        cleanup_data = data.get('cleanup', {})
        cleanup = CleanupConfig(
            enable_auto_cleanup=cleanup_data.get('enable_auto_cleanup', True),
            cleanup_interval=cleanup_data.get('cleanup_interval', 3600),
            max_memory_entries=cleanup_data.get('max_memory_entries', 10000),
            default_expiry_time=cleanup_data.get('default_expiry_time'),
            cleanup_strategy=cleanup_data.get('cleanup_strategy', 'smart'),
            low_access_threshold=cleanup_data.get('low_access_threshold', 2),
            retention_days=cleanup_data.get('retention_days', 30)
        )
        
        performance_data = data.get('performance', {})
        performance = PerformanceConfig(
            enable_async_operations=performance_data.get('enable_async_operations', True),
            thread_pool_size=performance_data.get('thread_pool_size', 4),
            search_index_type=performance_data.get('search_index_type', 'simple'),
            enable_search_cache=performance_data.get('enable_search_cache', True),
            search_cache_size=performance_data.get('search_cache_size', 100),
            operation_timeout=performance_data.get('operation_timeout', 30)
        )
        
        collection_data = data.get('collection', {})
        collection = CollectionConfig(
            enable_memory_collection=collection_data.get('enable_memory_collection', False),
            collection_mode=collection_data.get('collection_mode', 'selective'),
            auto_collect_methods=collection_data.get('auto_collect_methods', []),
            collection_filters=collection_data.get('collection_filters', {}),
            collect_input_params=collection_data.get('collect_input_params', True),
            collect_output_results=collection_data.get('collect_output_results', True),
            collect_errors=collection_data.get('collect_errors', True),
            max_param_length=collection_data.get('max_param_length', 1000)
        )
        
        security_data = data.get('security', {})
        security = SecurityConfig(
            enable_encryption=security_data.get('enable_encryption', False),
            encryption_key=security_data.get('encryption_key'),
            sensitive_fields=security_data.get('sensitive_fields', ['password', 'token', 'secret']),
            enable_access_control=security_data.get('enable_access_control', True),
            allowed_agents=security_data.get('allowed_agents', [])
        )
        
        return cls(
            enabled=data.get('enabled', False),
            version=data.get('version', '1.0.0'),
            storage=storage,
            recommendation=recommendation,
            cleanup=cleanup,
            performance=performance,
            collection=collection,
            security=security,
            extensions=data.get('extensions', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'enabled': self.enabled,
            'version': self.version,
            'storage': {
                'storage_type': self.storage.storage_type,
                'database_path': self.storage.database_path,
                'cache_size': self.storage.cache_size,
                'enable_persistence': self.storage.enable_persistence,
                'batch_write_size': self.storage.batch_write_size,
                'enable_compression': self.storage.enable_compression
            },
            'recommendation': {
                'algorithm': self.recommendation.algorithm,
                'max_recommendations': self.recommendation.max_recommendations,
                'similarity_threshold': self.recommendation.similarity_threshold,
                'keyword_weight': self.recommendation.keyword_weight,
                'tag_weight': self.recommendation.tag_weight,
                'time_weight': self.recommendation.time_weight,
                'access_weight': self.recommendation.access_weight,
                'enable_smart_recommendation': self.recommendation.enable_smart_recommendation
            },
            'cleanup': {
                'enable_auto_cleanup': self.cleanup.enable_auto_cleanup,
                'cleanup_interval': self.cleanup.cleanup_interval,
                'max_memory_entries': self.cleanup.max_memory_entries,
                'default_expiry_time': self.cleanup.default_expiry_time,
                'cleanup_strategy': self.cleanup.cleanup_strategy,
                'low_access_threshold': self.cleanup.low_access_threshold,
                'retention_days': self.cleanup.retention_days
            },
            'performance': {
                'enable_async_operations': self.performance.enable_async_operations,
                'thread_pool_size': self.performance.thread_pool_size,
                'search_index_type': self.performance.search_index_type,
                'enable_search_cache': self.performance.enable_search_cache,
                'search_cache_size': self.performance.search_cache_size,
                'operation_timeout': self.performance.operation_timeout
            },
            'collection': {
                'enable_memory_collection': self.collection.enable_memory_collection,
                'collection_mode': self.collection.collection_mode,
                'auto_collect_methods': self.collection.auto_collect_methods,
                'collection_filters': self.collection.collection_filters,
                'collect_input_params': self.collection.collect_input_params,
                'collect_output_results': self.collection.collect_output_results,
                'collect_errors': self.collection.collect_errors,
                'max_param_length': self.collection.max_param_length
            },
            'security': {
                'enable_encryption': self.security.enable_encryption,
                'encryption_key': self.security.encryption_key,
                'sensitive_fields': self.security.sensitive_fields,
                'enable_access_control': self.security.enable_access_control,
                'allowed_agents': self.security.allowed_agents
            },
            'extensions': self.extensions
        }
    
    def save_to_file(self, config_path: str, format: str = 'auto'):
        """保存配置到文件"""
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        data = self.to_dict()
        
        # 确定格式
        if format == 'auto':
            format = 'yaml' if config_file.suffix.lower() in ['.yaml', '.yml'] else 'json'
        
        with open(config_file, 'w', encoding='utf-8') as f:
            if format == 'yaml':
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, indent=2)
            else:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def update_from_dict(self, updates: Dict[str, Any]):
        """从字典更新配置（部分更新）"""
        if 'enabled' in updates:
            self.enabled = updates['enabled']
        
        if 'storage' in updates:
            storage_updates = updates['storage']
            for key, value in storage_updates.items():
                if hasattr(self.storage, key):
                    setattr(self.storage, key, value)
        
        if 'recommendation' in updates:
            rec_updates = updates['recommendation']
            for key, value in rec_updates.items():
                if hasattr(self.recommendation, key):
                    setattr(self.recommendation, key, value)
        
        if 'cleanup' in updates:
            cleanup_updates = updates['cleanup']
            for key, value in cleanup_updates.items():
                if hasattr(self.cleanup, key):
                    setattr(self.cleanup, key, value)
        
        if 'performance' in updates:
            perf_updates = updates['performance']
            for key, value in perf_updates.items():
                if hasattr(self.performance, key):
                    setattr(self.performance, key, value)
        
        if 'collection' in updates:
            col_updates = updates['collection']
            for key, value in col_updates.items():
                if hasattr(self.collection, key):
                    setattr(self.collection, key, value)
        
        if 'security' in updates:
            sec_updates = updates['security']
            for key, value in sec_updates.items():
                if hasattr(self.security, key):
                    setattr(self.security, key, value)
        
        if 'extensions' in updates:
            self.extensions.update(updates['extensions'])
    
    def validate(self) -> List[str]:
        """验证配置，返回错误列表"""
        errors = []
        
        # 验证存储配置
        if self.storage.storage_type not in ['sqlite', 'memory', 'file']:
            errors.append(f"不支持的存储类型: {self.storage.storage_type}")
        
        if self.storage.cache_size <= 0:
            errors.append("缓存大小必须大于0")
        
        # 验证推荐配置
        if self.recommendation.algorithm not in ['keyword', 'similarity', 'hybrid']:
            errors.append(f"不支持的推荐算法: {self.recommendation.algorithm}")
        
        if not (0 <= self.recommendation.similarity_threshold <= 1):
            errors.append("相似度阈值必须在0-1之间")
        
        # 验证权重总和
        weight_sum = (self.recommendation.keyword_weight + 
                     self.recommendation.tag_weight + 
                     self.recommendation.time_weight + 
                     self.recommendation.access_weight)
        if abs(weight_sum - 1.0) > 0.01:  # 允许小的浮点误差
            errors.append(f"推荐权重总和应为1.0，当前为: {weight_sum}")
        
        # 验证清理配置
        if self.cleanup.cleanup_strategy not in ['lru', 'lfu', 'time_based', 'smart']:
            errors.append(f"不支持的清理策略: {self.cleanup.cleanup_strategy}")
        
        if self.cleanup.max_memory_entries <= 0:
            errors.append("最大记忆条目数量必须大于0")
        
        # 验证性能配置
        if self.performance.search_index_type not in ['simple', 'advanced']:
            errors.append(f"不支持的搜索索引类型: {self.performance.search_index_type}")
        
        if self.performance.thread_pool_size <= 0:
            errors.append("线程池大小必须大于0")
        
        # 验证收集配置
        if self.collection.collection_mode not in ['auto', 'manual', 'selective']:
            errors.append(f"不支持的收集模式: {self.collection.collection_mode}")
        
        return errors
    
    def is_valid(self) -> bool:
        """检查配置是否有效"""
        return len(self.validate()) == 0


# 全局配置实例
_global_config: Optional[MemoryConfig] = None


def get_memory_config() -> MemoryConfig:
    """获取全局记忆配置"""
    global _global_config
    if _global_config is None:
        # 尝试从环境变量获取配置文件路径
        config_path = os.getenv('ANP_MEMORY_CONFIG_PATH', './data/memory_config.yaml')
        _global_config = MemoryConfig.load_from_file(config_path)
    return _global_config


def set_memory_config(config: MemoryConfig):
    """设置全局记忆配置"""
    global _global_config
    _global_config = config


def reload_memory_config(config_path: Optional[str] = None):
    """重新加载记忆配置"""
    global _global_config
    if config_path is None:
        config_path = os.getenv('ANP_MEMORY_CONFIG_PATH', './data/memory_config.yaml')
    _global_config = MemoryConfig.load_from_file(config_path)
    return _global_config