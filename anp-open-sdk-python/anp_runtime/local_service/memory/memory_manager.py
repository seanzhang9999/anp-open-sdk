"""
记忆管理器

统一的记忆管理接口，协调存储、会话、收集、推荐等各个组件
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable, Union, Tuple
import logging

from .memory_models import MemoryEntry, ContextSession, MemoryType, MethodCallMemory
from .memory_storage import MemoryStorageInterface, create_storage
from .context_session import ContextSessionManager, get_session_manager
from .memory_config import MemoryConfig, get_memory_config

logger = logging.getLogger(__name__)


class MemoryEventType:
    """记忆事件类型"""
    MEMORY_CREATED = "memory_created"
    MEMORY_UPDATED = "memory_updated"  
    MEMORY_DELETED = "memory_deleted"
    MEMORY_ACCESSED = "memory_accessed"
    CLEANUP_STARTED = "cleanup_started"
    CLEANUP_COMPLETED = "cleanup_completed"


class MemoryLifecycleManager:
    """记忆生命周期管理器"""
    
    def __init__(self, storage: MemoryStorageInterface, config: MemoryConfig):
        self.storage = storage
        self.config = config
        
        # 事件监听器
        self._event_listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
        
        # 清理任务
        self._cleanup_task = None
        if config.cleanup.enable_auto_cleanup:
            self._start_cleanup_task()
    
    def add_event_listener(self, event_type: str, listener: Callable):
        """添加事件监听器"""
        with self._lock:
            if event_type not in self._event_listeners:
                self._event_listeners[event_type] = []
            self._event_listeners[event_type].append(listener)
    
    def remove_event_listener(self, event_type: str, listener: Callable):
        """移除事件监听器"""
        with self._lock:
            if event_type in self._event_listeners and listener in self._event_listeners[event_type]:
                self._event_listeners[event_type].remove(listener)
    
    def _notify_listeners(self, event_type: str, memory: Optional[MemoryEntry], **kwargs):
        """通知事件监听器"""
        with self._lock:
            listeners = self._event_listeners.get(event_type, [])
        
        for listener in listeners:
            try:
                listener(memory, **kwargs)
            except Exception as e:
                logger.error(f"记忆事件监听器错误: {e}")
    
    def _start_cleanup_task(self):
        """启动自动清理任务"""
        async def cleanup_loop():
            while self.config.cleanup.enable_auto_cleanup:
                try:
                    await asyncio.sleep(self.config.cleanup.cleanup_interval)
                    await self._perform_cleanup()
                except Exception as e:
                    logger.error(f"记忆清理任务错误: {e}")
        
        # 尝试在后台运行清理任务
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._cleanup_task = loop.create_task(cleanup_loop())
        except:
            # 如果没有事件循环，跳过自动清理
            pass
    
    async def _perform_cleanup(self):
        """执行清理操作"""
        self._notify_listeners(MemoryEventType.CLEANUP_STARTED, None)
        
        # 清理过期记忆
        expired_count = await self.storage.cleanup_expired_memories()
        
        # 根据策略清理记忆
        cleaned_count = await self._cleanup_by_strategy()
        
        total_cleaned = expired_count + cleaned_count
        if total_cleaned > 0:
            logger.info(f"记忆清理完成: 过期 {expired_count}, 策略清理 {cleaned_count}")
        
        self._notify_listeners(MemoryEventType.CLEANUP_COMPLETED, None, 
                             expired_count=expired_count, cleaned_count=cleaned_count)
    
    async def _cleanup_by_strategy(self) -> int:
        """根据策略清理记忆"""
        strategy = self.config.cleanup.cleanup_strategy
        max_entries = self.config.cleanup.max_memory_entries
        
        # 获取当前记忆数量
        stats = await self.storage.get_storage_stats()
        current_count = stats.get('total_memories', 0)
        
        if current_count <= max_entries:
            return 0
        
        # 需要清理的数量
        cleanup_count = current_count - max_entries
        
        if strategy == 'lru':
            return await self._cleanup_lru(cleanup_count)
        elif strategy == 'lfu':  
            return await self._cleanup_lfu(cleanup_count)
        elif strategy == 'time_based':
            return await self._cleanup_time_based(cleanup_count)
        elif strategy == 'smart':
            return await self._cleanup_smart(cleanup_count)
        else:
            logger.warning(f"未知的清理策略: {strategy}")
            return 0
    
    async def _cleanup_lru(self, count: int) -> int:
        """LRU清理策略"""
        # 简化实现：清理最久未访问的记忆
        memories = await self.storage.search_memories(limit=count * 2)
        
        # 按最后访问时间排序
        memories.sort(key=lambda m: m.metadata.last_accessed or m.created_at)
        
        cleaned = 0
        for memory in memories[:count]:
            if await self.storage.delete_memory(memory.id):
                cleaned += 1
        
        return cleaned
    
    async def _cleanup_lfu(self, count: int) -> int:
        """LFU清理策略"""
        # 简化实现：清理访问次数最少的记忆
        memories = await self.storage.search_memories(limit=count * 2)
        
        # 按访问次数排序
        memories.sort(key=lambda m: m.metadata.access_count)
        
        cleaned = 0
        for memory in memories[:count]:
            if await self.storage.delete_memory(memory.id):
                cleaned += 1
        
        return cleaned
    
    async def _cleanup_time_based(self, count: int) -> int:
        """基于时间的清理策略"""
        # 清理超过保留期的记忆
        cutoff_date = datetime.now() - timedelta(days=self.config.cleanup.retention_days)
        
        memories = await self.storage.search_memories(limit=count * 2)
        
        cleaned = 0
        for memory in memories:
            if memory.created_at < cutoff_date:
                if await self.storage.delete_memory(memory.id):
                    cleaned += 1
                    if cleaned >= count:
                        break
        
        return cleaned
    
    async def _cleanup_smart(self, count: int) -> int:
        """智能清理策略"""
        # 综合考虑访问频次、时间、重要性等因素
        memories = await self.storage.search_memories(limit=count * 2)
        
        # 计算清理优先级（越低越容易被清理）
        scored_memories = []
        now = datetime.now()
        
        for memory in memories:
            score = 0.0
            
            # 访问频次分数 (0-1)
            access_score = min(memory.metadata.access_count / 10.0, 1.0)
            score += access_score * 0.3
            
            # 时间分数 (越新分数越高, 0-1)
            age_days = (now - memory.created_at).days
            time_score = max(0, 1 - age_days / 365.0)  # 1年内的记忆有较高分数
            score += time_score * 0.3
            
            # 相关度分数
            score += memory.metadata.relevance_score * 0.2
            
            # 类型重要性分数
            type_importance = {
                MemoryType.ERROR: 0.1,        # 错误记忆重要性较低
                MemoryType.METHOD_CALL: 0.5,  # 方法调用记忆中等重要
                MemoryType.USER_PREFERENCE: 0.8,  # 用户偏好重要性较高
                MemoryType.CONTEXT: 0.7,      # 上下文记忆重要性较高
                MemoryType.PATTERN: 0.9       # 模式记忆重要性很高
            }
            score += type_importance.get(memory.memory_type, 0.5) * 0.2
            
            scored_memories.append((memory, score))
        
        # 按分数排序，分数低的优先清理
        scored_memories.sort(key=lambda x: x[1])
        
        cleaned = 0
        for memory, score in scored_memories[:count]:
            # 如果分数太高，不清理
            if score > 0.7:
                continue
                
            if await self.storage.delete_memory(memory.id):
                cleaned += 1
        
        return cleaned
    
    async def close(self):
        """关闭生命周期管理器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class MemorySearchEngine:
    """记忆搜索引擎"""
    
    def __init__(self, storage: MemoryStorageInterface, config: MemoryConfig):
        self.storage = storage
        self.config = config
        
        # 搜索缓存
        self._search_cache: Dict[str, Tuple[List[MemoryEntry], datetime]] = {}
        self._cache_lock = threading.RLock()
    
    async def search(
        self,
        query: str = "",
        memory_type: Optional[MemoryType] = None,
        agent_did: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        limit: int = 100,
        offset: int = 0,
        use_cache: bool = True
    ) -> List[MemoryEntry]:
        """智能搜索记忆条目"""
        
        # 生成缓存键
        cache_key = self._generate_cache_key(
            query, memory_type, agent_did, session_id, tags, keywords, 
            time_range, limit, offset
        )
        
        # 检查缓存
        if use_cache and self.config.performance.enable_search_cache:
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                return cached_result
        
        # 执行搜索
        results = await self.storage.search_memories(
            query=query,
            memory_type=memory_type,
            agent_did=agent_did,
            session_id=session_id,
            tags=tags,
            keywords=keywords,
            limit=limit,
            offset=offset
        )
        
        # 应用时间范围过滤
        if time_range:
            start_time, end_time = time_range
            results = [
                m for m in results 
                if start_time <= m.created_at <= end_time
            ]
        
        # 缓存结果
        if use_cache and self.config.performance.enable_search_cache:
            self._cache_result(cache_key, results)
        
        return results
    
    def _generate_cache_key(self, *args) -> str:
        """生成缓存键"""
        return str(hash(str(args)))
    
    def _get_cached_result(self, cache_key: str) -> Optional[List[MemoryEntry]]:
        """获取缓存结果"""
        with self._cache_lock:
            if cache_key in self._search_cache:
                results, cached_time = self._search_cache[cache_key]
                # 检查缓存是否过期（5分钟）
                if datetime.now() - cached_time < timedelta(minutes=5):
                    return results
                else:
                    del self._search_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, results: List[MemoryEntry]):
        """缓存搜索结果"""
        with self._cache_lock:
            # 限制缓存大小
            if len(self._search_cache) >= self.config.performance.search_cache_size:
                # 移除最旧的缓存
                oldest_key = min(self._search_cache.keys(), 
                               key=lambda k: self._search_cache[k][1])
                del self._search_cache[oldest_key]
            
            self._search_cache[cache_key] = (results, datetime.now())
    
    async def search_similar_memories(
        self, 
        reference_memory: MemoryEntry, 
        similarity_threshold: float = 0.5,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """搜索相似的记忆条目"""
        
        # 基于标签和关键词搜索相似记忆
        similar_memories = []
        
        # 搜索具有相同标签的记忆
        if reference_memory.metadata.tags:
            tag_results = await self.search(
                tags=reference_memory.metadata.tags,
                limit=limit * 2
            )
            similar_memories.extend(tag_results)
        
        # 搜索具有相同关键词的记忆
        if reference_memory.metadata.keywords:
            keyword_results = await self.search(
                keywords=reference_memory.metadata.keywords,
                limit=limit * 2
            )
            similar_memories.extend(keyword_results)
        
        # 去重并计算相似度
        unique_memories = {}
        for memory in similar_memories:
            if memory.id != reference_memory.id:
                unique_memories[memory.id] = memory
        
        # 计算相似度并排序
        scored_memories = []
        for memory in unique_memories.values():
            similarity = self._calculate_memory_similarity(reference_memory, memory)
            if similarity >= similarity_threshold:
                scored_memories.append((memory, similarity))
        
        # 按相似度排序
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        
        return [memory for memory, _ in scored_memories[:limit]]
    
    def _calculate_memory_similarity(
        self, 
        memory1: MemoryEntry, 
        memory2: MemoryEntry
    ) -> float:
        """计算两个记忆条目的相似度"""
        similarity = 0.0
        
        # 类型相似度 (权重: 0.2)
        if memory1.memory_type == memory2.memory_type:
            similarity += 0.2
        
        # 标签相似度 (权重: 0.3)
        tags1 = set(memory1.metadata.tags)
        tags2 = set(memory2.metadata.tags)
        if tags1 or tags2:
            tag_similarity = len(tags1 & tags2) / len(tags1 | tags2)
            similarity += tag_similarity * 0.3
        
        # 关键词相似度 (权重: 0.3)
        keywords1 = set(memory1.metadata.keywords)
        keywords2 = set(memory2.metadata.keywords)
        if keywords1 or keywords2:
            keyword_similarity = len(keywords1 & keywords2) / len(keywords1 | keywords2)
            similarity += keyword_similarity * 0.3
        
        # Agent相似度 (权重: 0.1)
        if memory1.metadata.source_agent_did == memory2.metadata.source_agent_did:
            similarity += 0.1
        
        # 时间相近度 (权重: 0.1)
        time_diff = abs((memory1.created_at - memory2.created_at).total_seconds())
        max_time_diff = 7 * 24 * 3600  # 7天
        time_similarity = max(0, 1 - time_diff / max_time_diff)
        similarity += time_similarity * 0.1
        
        return similarity


class MemoryManager:
    """统一记忆管理器"""
    
    def __init__(
        self, 
        storage: Optional[MemoryStorageInterface] = None,
        session_manager: Optional[ContextSessionManager] = None,
        config: Optional[MemoryConfig] = None
    ):
        self.config = config or get_memory_config()
        self.storage = storage or create_storage(self.config)
        self.session_manager = session_manager or get_session_manager()
        
        # 子组件
        self.lifecycle_manager = MemoryLifecycleManager(self.storage, self.config)
        self.search_engine = MemorySearchEngine(self.storage, self.config)
        
        # 记忆收集器和推荐器将在后续实现时注入
        self.memory_collector = None
        self.memory_recommender = None
        
        # 统计信息
        self._stats = {
            'memories_created': 0,
            'memories_updated': 0,
            'memories_deleted': 0,
            'memories_accessed': 0,
            'searches_performed': 0,
            'recommendations_generated': 0
        }
        self._stats_lock = threading.RLock()
    
    # ============ 基本记忆操作 ============
    
    async def create_memory(
        self,
        memory_type: MemoryType,
        title: str,
        content: Dict[str, Any],
        source_agent_did: str,
        source_agent_name: str,
        target_agent_did: Optional[str] = None,
        target_agent_name: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        expiry_time: Optional[datetime] = None
    ) -> MemoryEntry:
        """创建记忆条目"""
        
        from .memory_models import MemoryMetadata
        
        metadata = MemoryMetadata(
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            target_agent_did=target_agent_did,
            target_agent_name=target_agent_name,
            session_id=session_id,
            tags=tags or [],
            keywords=keywords or [],
            expiry_time=expiry_time
        )
        
        memory = MemoryEntry(
            memory_type=memory_type,
            title=title,
            content=content,
            metadata=metadata
        )
        
        # 保存到存储
        success = await self.storage.save_memory(memory)
        if not success:
            raise RuntimeError(f"创建记忆失败: {memory.id}")
        
        # 如果有会话ID，关联到会话
        if session_id:
            await self.session_manager.add_memory_to_session(session_id, memory.id)
        
        # 更新统计
        with self._stats_lock:
            self._stats['memories_created'] += 1
        
        # 通知监听器
        self.lifecycle_manager._notify_listeners(MemoryEventType.MEMORY_CREATED, memory)
        
        logger.debug(f"创建记忆: {memory.title} ({memory.id})")
        return memory
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """获取记忆条目"""
        memory = await self.storage.get_memory(memory_id)
        
        if memory:
            # 更新统计
            with self._stats_lock:
                self._stats['memories_accessed'] += 1
            
            # 通知监听器
            self.lifecycle_manager._notify_listeners(MemoryEventType.MEMORY_ACCESSED, memory)
        
        return memory
    
    async def update_memory(self, memory: MemoryEntry) -> bool:
        """更新记忆条目"""
        success = await self.storage.update_memory(memory)
        
        if success:
            # 更新统计
            with self._stats_lock:
                self._stats['memories_updated'] += 1
            
            # 通知监听器
            self.lifecycle_manager._notify_listeners(MemoryEventType.MEMORY_UPDATED, memory)
        
        return success
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆条目"""
        # 先获取记忆以便通知
        memory = await self.storage.get_memory(memory_id)
        
        success = await self.storage.delete_memory(memory_id)
        
        if success and memory:
            # 从所有相关会话中移除
            if memory.metadata.session_id:
                await self.session_manager.remove_memory_from_session(
                    memory.metadata.session_id, memory_id
                )
            
            # 更新统计
            with self._stats_lock:
                self._stats['memories_deleted'] += 1
            
            # 通知监听器
            self.lifecycle_manager._notify_listeners(MemoryEventType.MEMORY_DELETED, memory)
        
        return success
    
    # ============ 搜索功能 ============
    
    async def search_memories(self, **kwargs) -> List[MemoryEntry]:
        """搜索记忆条目"""
        results = await self.search_engine.search(**kwargs)
        
        # 更新统计
        with self._stats_lock:
            self._stats['searches_performed'] += 1
        
        return results
    
    async def search_similar_memories(
        self, 
        reference_memory: MemoryEntry, 
        **kwargs
    ) -> List[MemoryEntry]:
        """搜索相似记忆"""
        return await self.search_engine.search_similar_memories(reference_memory, **kwargs)
    
    # ============ 批量操作 ============
    
    async def create_memories_batch(self, memory_specs: List[Dict[str, Any]]) -> List[MemoryEntry]:
        """批量创建记忆条目"""
        memories = []
        
        for spec in memory_specs:
            try:
                memory = await self.create_memory(**spec)
                memories.append(memory)
            except Exception as e:
                logger.error(f"批量创建记忆失败: {e}")
        
        return memories
    
    async def delete_memories_batch(self, memory_ids: List[str]) -> int:
        """批量删除记忆条目"""
        deleted_count = 0
        
        for memory_id in memory_ids:
            try:
                if await self.delete_memory(memory_id):
                    deleted_count += 1
            except Exception as e:
                logger.error(f"批量删除记忆失败: {e}")
        
        return deleted_count
    
    # ============ 便捷方法 ============
    
    async def create_method_call_memory(
        self,
        method_name: str,
        method_key: str,
        input_args: List[Any],
        input_kwargs: Dict[str, Any],
        output: Any,
        execution_time: float,
        source_agent_did: str,
        source_agent_name: str,
        **kwargs
    ) -> MemoryEntry:
        """创建方法调用记忆"""
        memory = MethodCallMemory.create(
            method_name=method_name,
            method_key=method_key,
            input_args=input_args,
            input_kwargs=input_kwargs,
            output=output,
            execution_time=execution_time,
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            **kwargs
        )
        
        # 保存记忆
        success = await self.storage.save_memory(memory)
        if not success:
            raise RuntimeError(f"创建方法调用记忆失败: {memory.id}")
        
        return memory
    
    async def create_error_memory(
        self,
        method_name: str,
        method_key: str,
        input_args: List[Any],
        input_kwargs: Dict[str, Any],
        error: Exception,
        execution_time: float,
        source_agent_did: str,
        source_agent_name: str,
        **kwargs
    ) -> MemoryEntry:
        """创建错误记忆"""
        memory = MethodCallMemory.create_error(
            method_name=method_name,
            method_key=method_key,
            input_args=input_args,
            input_kwargs=input_kwargs,
            error=error,
            execution_time=execution_time,
            source_agent_did=source_agent_did,
            source_agent_name=source_agent_name,
            **kwargs
        )
        
        # 保存记忆
        success = await self.storage.save_memory(memory)
        if not success:
            raise RuntimeError(f"创建错误记忆失败: {memory.id}")
        
        return memory
    
    # ============ 统计和监控 ============
    
    async def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        storage_stats = await self.storage.get_storage_stats()
        session_stats = await self.session_manager.get_session_statistics()
        
        with self._stats_lock:
            operation_stats = self._stats.copy()
        
        return {
            'storage': storage_stats,
            'sessions': session_stats,
            'operations': operation_stats,
            'config': {
                'enabled': self.config.enabled,
                'storage_type': self.config.storage.storage_type,
                'max_memory_entries': self.config.cleanup.max_memory_entries,
                'auto_cleanup': self.config.cleanup.enable_auto_cleanup
            }
        }
    
    # ============ 事件管理 ============
    
    def add_event_listener(self, event_type: str, listener: Callable):
        """添加事件监听器"""
        self.lifecycle_manager.add_event_listener(event_type, listener)
    
    def remove_event_listener(self, event_type: str, listener: Callable):
        """移除事件监听器"""
        self.lifecycle_manager.remove_event_listener(event_type, listener)
    
    # ============ 生命周期管理 ============
    
    async def cleanup_memories(self) -> Dict[str, int]:
        """手动触发记忆清理"""
        await self.lifecycle_manager._perform_cleanup()
        return {
            'expired_cleaned': 0,  # 实际数值会在清理完成事件中提供
            'strategy_cleaned': 0
        }
    
    async def close(self):
        """关闭记忆管理器"""
        await self.lifecycle_manager.close()
        await self.session_manager.close()
        
        # 检查存储是否有close方法（如SQLiteMemoryStorage）
        if hasattr(self.storage, 'close') and callable(getattr(self.storage, 'close')):
            close_method = getattr(self.storage, 'close')
            close_method()


# 全局记忆管理器实例
_global_memory_manager: Optional[MemoryManager] = None


def get_memory_manager() -> MemoryManager:
    """获取全局记忆管理器实例"""
    global _global_memory_manager
    if _global_memory_manager is None:
        _global_memory_manager = MemoryManager()
    return _global_memory_manager


def set_memory_manager(manager: MemoryManager):
    """设置全局记忆管理器实例"""
    global _global_memory_manager
    _global_memory_manager = manager