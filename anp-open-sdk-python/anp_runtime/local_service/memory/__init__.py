"""
LocalMethod公共记忆功能模块

提供跨Agent的记忆管理功能，包括：
- 记忆数据模型
- 存储管理
- 上下文会话管理
- 记忆收集和推荐
"""

from .memory_models import (
    MemoryEntry,
    ContextSession,
    MemoryType,
    MemoryMetadata
)

from .memory_config import MemoryConfig

from .memory_options import MemoryOptions, normalize_memory_config, memory_enabled, memory_disabled

from .memory_manager import MemoryManager

from .memory_collector import MemoryCollector, get_memory_collector

from .memory_recommender import (
    MemoryRecommender,
    RecommendationContext,
    get_memory_recommender,
    set_memory_recommender
)

__all__ = [
    'MemoryEntry',
    'ContextSession',
    'MemoryType',
    'MemoryMetadata',
    'MemoryConfig',
    'MemoryOptions',
    'normalize_memory_config',
    'memory_enabled',
    'memory_disabled',
    'MemoryManager',
    'MemoryCollector',
    'get_memory_collector',
    'MemoryRecommender',
    'RecommendationContext',
    'get_memory_recommender',
    'set_memory_recommender'
]