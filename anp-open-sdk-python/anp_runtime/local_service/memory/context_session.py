"""
上下文会话管理器

负责管理跨Agent的上下文会话，包括会话生命周期、记忆条目关联等
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
import logging

from .memory_models import ContextSession, MemoryEntry, MemoryType
from .memory_storage import MemoryStorageInterface, create_storage
from .memory_config import get_memory_config

logger = logging.getLogger(__name__)


class SessionLifecycleManager:
    """会话生命周期管理器"""
    
    def __init__(self, storage: MemoryStorageInterface):
        self.storage = storage
        self.config = get_memory_config()
        
        # 活跃会话缓存
        self._active_sessions: Dict[str, ContextSession] = {}
        self._lock = threading.RLock()
        
        # 会话监听器
        self._session_listeners: Dict[str, List[Callable]] = {
            'session_created': [],
            'session_updated': [],
            'session_closed': [],
            'memory_added': [],
            'memory_removed': []
        }
    
    def add_listener(self, event_type: str, listener: Callable):
        """添加会话事件监听器"""
        if event_type in self._session_listeners:
            self._session_listeners[event_type].append(listener)
    
    def remove_listener(self, event_type: str, listener: Callable):
        """移除会话事件监听器"""
        if event_type in self._session_listeners and listener in self._session_listeners[event_type]:
            self._session_listeners[event_type].remove(listener)
    
    def _notify_listeners(self, event_type: str, session: ContextSession, **kwargs):
        """通知监听器"""
        for listener in self._session_listeners.get(event_type, []):
            try:
                listener(session, **kwargs)
            except Exception as e:
                logger.error(f"会话监听器错误: {e}")
    
    async def create_session(
        self, 
        name: str = "", 
        description: str = "",
        participants: Optional[List[str]] = None,
        context_data: Optional[Dict[str, Any]] = None
    ) -> ContextSession:
        """创建新的上下文会话"""
        session = ContextSession(
            name=name,
            description=description,
            participants=participants or [],
            context_data=context_data or {}
        )
        
        # 保存到存储
        success = await self.storage.save_session(session)
        if not success:
            raise RuntimeError(f"创建会话失败: {session.id}")
        
        # 添加到活跃会话缓存
        with self._lock:
            self._active_sessions[session.id] = session
        
        # 通知监听器
        self._notify_listeners('session_created', session)
        
        logger.info(f"创建会话: {session.name} ({session.id})")
        return session
    
    async def get_session(self, session_id: str) -> Optional[ContextSession]:
        """获取会话"""
        # 先检查缓存
        with self._lock:
            if session_id in self._active_sessions:
                return self._active_sessions[session_id]
        
        # 从存储获取
        session = await self.storage.get_session(session_id)
        if session and session.is_active:
            with self._lock:
                self._active_sessions[session_id] = session
        
        return session
    
    async def update_session(self, session: ContextSession) -> bool:
        """更新会话"""
        session.updated_at = datetime.now()
        success = await self.storage.update_session(session)
        
        if success:
            # 更新缓存
            with self._lock:
                if session.is_active:
                    self._active_sessions[session.id] = session
                else:
                    self._active_sessions.pop(session.id, None)
            
            # 通知监听器
            self._notify_listeners('session_updated', session)
        
        return success
    
    async def close_session(self, session_id: str) -> bool:
        """关闭会话"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.close()
        success = await self.update_session(session)
        
        if success:
            # 从活跃缓存中移除
            with self._lock:
                self._active_sessions.pop(session_id, None)
            
            # 通知监听器
            self._notify_listeners('session_closed', session)
            logger.info(f"关闭会话: {session.name} ({session.id})")
        
        return success
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话（谨慎使用）"""
        # 先关闭会话
        await self.close_session(session_id)
        
        # 删除存储
        success = await self.storage.delete_session(session_id)
        
        if success:
            # 确保从缓存中移除
            with self._lock:
                self._active_sessions.pop(session_id, None)
            
            logger.info(f"删除会话: {session_id}")
        
        return success
    
    async def add_participant(self, session_id: str, agent_did: str) -> bool:
        """添加会话参与者"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.add_participant(agent_did)
        return await self.update_session(session)
    
    async def remove_participant(self, session_id: str, agent_did: str) -> bool:
        """移除会话参与者"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.remove_participant(agent_did)
        return await self.update_session(session)
    
    async def add_memory_to_session(self, session_id: str, memory_id: str) -> bool:
        """向会话添加记忆条目"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.add_memory(memory_id)
        success = await self.update_session(session)
        
        if success:
            # 通知监听器
            self._notify_listeners('memory_added', session, memory_id=memory_id)
        
        return success
    
    async def remove_memory_from_session(self, session_id: str, memory_id: str) -> bool:
        """从会话移除记忆条目"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.remove_memory(memory_id)
        success = await self.update_session(session)
        
        if success:
            # 通知监听器
            self._notify_listeners('memory_removed', session, memory_id=memory_id)
        
        return success
    
    async def update_context_data(self, session_id: str, key: str, value: Any) -> bool:
        """更新会话上下文数据"""
        session = await self.get_session(session_id)
        if not session:
            return False
        
        session.update_context(key, value)
        return await self.update_session(session)
    
    async def get_context_data(self, session_id: str, key: str, default: Any = None) -> Any:
        """获取会话上下文数据"""
        session = await self.get_session(session_id)
        if not session:
            return default
        
        return session.get_context(key, default)
    
    async def get_active_sessions(self) -> List[ContextSession]:
        """获取所有活跃会话"""
        with self._lock:
            return list(self._active_sessions.values())
    
    async def get_sessions_by_participant(self, agent_did: str) -> List[ContextSession]:
        """获取指定参与者的会话"""
        active_sessions = await self.get_active_sessions()
        return [s for s in active_sessions if agent_did in s.participants]
    
    async def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """清理非活跃会话"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        active_sessions = await self.get_active_sessions()
        closed_count = 0
        
        for session in active_sessions:
            if session.updated_at < cutoff_time:
                await self.close_session(session.id)
                closed_count += 1
        
        if closed_count > 0:
            logger.info(f"清理了 {closed_count} 个非活跃会话")
        
        return closed_count


class ContextSessionManager:
    """上下文会话管理器主类"""
    
    def __init__(self, storage: Optional[MemoryStorageInterface] = None):
        self.storage = storage or create_storage()
        self.lifecycle_manager = SessionLifecycleManager(self.storage)
        self.config = get_memory_config()
        
        # 会话相关性分析器
        self._session_analyzer = SessionAnalyzer(self.storage)
        
        # 自动清理任务
        self._cleanup_task = None
        if self.config.cleanup.enable_auto_cleanup:
            self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """启动自动清理任务"""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.config.cleanup.cleanup_interval)
                    await self.lifecycle_manager.cleanup_inactive_sessions()
                except Exception as e:
                    logger.error(f"会话清理任务错误: {e}")
        
        # 在后台运行清理任务
        loop = None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                self._cleanup_task = loop.create_task(cleanup_loop())
        except:
            # 如果没有事件循环，跳过自动清理
            pass
    
    # 代理生命周期管理器的方法
    async def create_session(self, **kwargs) -> ContextSession:
        return await self.lifecycle_manager.create_session(**kwargs)
    
    async def get_session(self, session_id: str) -> Optional[ContextSession]:
        return await self.lifecycle_manager.get_session(session_id)
    
    async def update_session(self, session: ContextSession) -> bool:
        return await self.lifecycle_manager.update_session(session)
    
    async def close_session(self, session_id: str) -> bool:
        return await self.lifecycle_manager.close_session(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        return await self.lifecycle_manager.delete_session(session_id)
    
    async def add_participant(self, session_id: str, agent_did: str) -> bool:
        return await self.lifecycle_manager.add_participant(session_id, agent_did)
    
    async def remove_participant(self, session_id: str, agent_did: str) -> bool:
        return await self.lifecycle_manager.remove_participant(session_id, agent_did)
    
    async def add_memory_to_session(self, session_id: str, memory_id: str) -> bool:
        return await self.lifecycle_manager.add_memory_to_session(session_id, memory_id)
    
    async def remove_memory_from_session(self, session_id: str, memory_id: str) -> bool:
        return await self.lifecycle_manager.remove_memory_from_session(session_id, memory_id)
    
    async def update_context_data(self, session_id: str, key: str, value: Any) -> bool:
        return await self.lifecycle_manager.update_context_data(session_id, key, value)
    
    async def get_context_data(self, session_id: str, key: str, default: Any = None) -> Any:
        return await self.lifecycle_manager.get_context_data(session_id, key, default)
    
    async def get_active_sessions(self) -> List[ContextSession]:
        return await self.lifecycle_manager.get_active_sessions()
    
    async def get_sessions_by_participant(self, agent_did: str) -> List[ContextSession]:
        return await self.lifecycle_manager.get_sessions_by_participant(agent_did)
    
    # 会话分析功能
    async def find_related_sessions(
        self, 
        session_id: str, 
        similarity_threshold: float = 0.5
    ) -> List[ContextSession]:
        """查找相关会话"""
        return await self._session_analyzer.find_related_sessions(session_id, similarity_threshold)
    
    async def get_session_memories(self, session_id: str) -> List[MemoryEntry]:
        """获取会话相关的记忆条目"""
        return await self.storage.get_memories_by_session(session_id)
    
    async def merge_sessions(self, source_session_id: str, target_session_id: str) -> bool:
        """合并会话"""
        source_session = await self.get_session(source_session_id)
        target_session = await self.get_session(target_session_id)
        
        if not source_session or not target_session:
            return False
        
        # 合并参与者
        for participant in source_session.participants:
            if participant not in target_session.participants:
                target_session.add_participant(participant)
        
        # 合并记忆条目
        for memory_id in source_session.memory_entries:
            if memory_id not in target_session.memory_entries:
                target_session.add_memory(memory_id)
        
        # 合并上下文数据
        for key, value in source_session.context_data.items():
            if key not in target_session.context_data:
                target_session.update_context(key, value)
        
        # 更新目标会话描述
        if source_session.description and target_session.description:
            target_session.description += f"; 合并自: {source_session.description}"
        elif source_session.description:
            target_session.description = source_session.description
        
        # 保存更新并删除源会话
        success = await self.update_session(target_session)
        if success:
            await self.delete_session(source_session_id)
            logger.info(f"会话合并成功: {source_session_id} -> {target_session_id}")
        
        return success
    
    async def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        active_sessions = await self.get_active_sessions()
        
        # 基本统计
        stats = {
            'total_active_sessions': len(active_sessions),
            'participants_distribution': {},
            'memory_distribution': {},
            'context_keys': set()
        }
        
        # 分析每个会话
        for session in active_sessions:
            # 参与者分布
            participant_count = len(session.participants)
            stats['participants_distribution'][participant_count] = \
                stats['participants_distribution'].get(participant_count, 0) + 1
            
            # 记忆条目分布
            memory_count = len(session.memory_entries)
            stats['memory_distribution'][memory_count] = \
                stats['memory_distribution'].get(memory_count, 0) + 1
            
            # 上下文键收集
            stats['context_keys'].update(session.context_data.keys())
        
        # 转换集合为列表以便序列化
        stats['context_keys'] = list(stats['context_keys'])
        
        return stats
    
    def add_session_listener(self, event_type: str, listener: Callable):
        """添加会话事件监听器"""
        self.lifecycle_manager.add_listener(event_type, listener)
    
    def remove_session_listener(self, event_type: str, listener: Callable):
        """移除会话事件监听器"""
        self.lifecycle_manager.remove_listener(event_type, listener)
    
    async def close(self):
        """关闭会话管理器"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass


class SessionAnalyzer:
    """会话相关性分析器"""
    
    def __init__(self, storage: MemoryStorageInterface):
        self.storage = storage
    
    async def find_related_sessions(
        self, 
        session_id: str, 
        similarity_threshold: float = 0.5
    ) -> List[ContextSession]:
        """查找与指定会话相关的其他会话"""
        target_session = await self.storage.get_session(session_id)
        if not target_session:
            return []
        
        # 获取所有活跃会话
        all_sessions = []
        # 这里需要实现获取所有会话的方法，暂时简化
        # 在实际实现中应该从存储中获取所有活跃会话
        
        related_sessions = []
        for session in all_sessions:
            if session.id == session_id or not session.is_active:
                continue
            
            similarity = self._calculate_session_similarity(target_session, session)
            if similarity >= similarity_threshold:
                related_sessions.append((session, similarity))
        
        # 按相似度排序
        related_sessions.sort(key=lambda x: x[1], reverse=True)
        return [session for session, _ in related_sessions]
    
    def _calculate_session_similarity(
        self, 
        session1: ContextSession, 
        session2: ContextSession
    ) -> float:
        """计算两个会话的相似度"""
        similarity_score = 0.0
        
        # 参与者重叠度 (权重: 0.4)
        participants1 = set(session1.participants)
        participants2 = set(session2.participants)
        if participants1 or participants2:
            participant_overlap = len(participants1 & participants2) / len(participants1 | participants2)
            similarity_score += participant_overlap * 0.4
        
        # 记忆条目重叠度 (权重: 0.3)
        memories1 = set(session1.memory_entries)
        memories2 = set(session2.memory_entries)
        if memories1 or memories2:
            memory_overlap = len(memories1 & memories2) / len(memories1 | memories2)
            similarity_score += memory_overlap * 0.3
        
        # 上下文键重叠度 (权重: 0.2)
        context_keys1 = set(session1.context_data.keys())
        context_keys2 = set(session2.context_data.keys())
        if context_keys1 or context_keys2:
            context_overlap = len(context_keys1 & context_keys2) / len(context_keys1 | context_keys2)
            similarity_score += context_overlap * 0.2
        
        # 时间相近度 (权重: 0.1)
        time_diff = abs((session1.created_at - session2.created_at).total_seconds())
        max_time_diff = 7 * 24 * 3600  # 7天
        time_similarity = max(0, 1 - time_diff / max_time_diff)
        similarity_score += time_similarity * 0.1
        
        return similarity_score


# 全局会话管理器实例
_global_session_manager: Optional[ContextSessionManager] = None


def get_session_manager() -> ContextSessionManager:
    """获取全局会话管理器实例"""
    global _global_session_manager
    if _global_session_manager is None:
        _global_session_manager = ContextSessionManager()
    return _global_session_manager


def set_session_manager(manager: ContextSessionManager):
    """设置全局会话管理器实例"""
    global _global_session_manager
    _global_session_manager = manager