"""
记忆存储管理器

负责记忆数据的存储、查询、更新、删除等操作
支持SQLite、内存和文件存储
"""

import sqlite3
import json
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from concurrent.futures import ThreadPoolExecutor
import logging

from .memory_models import MemoryEntry, ContextSession, MemoryType
from .memory_config import MemoryConfig, get_memory_config

logger = logging.getLogger(__name__)


class MemoryStorageInterface(ABC):
    """记忆存储接口"""
    
    @abstractmethod
    async def save_memory(self, memory: MemoryEntry) -> bool:
        """保存记忆条目"""
        pass
    
    @abstractmethod
    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """获取记忆条目"""
        pass
    
    @abstractmethod
    async def update_memory(self, memory: MemoryEntry) -> bool:
        """更新记忆条目"""
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆条目"""
        pass
    
    @abstractmethod
    async def search_memories(
        self,
        query: str = "",
        memory_type: Optional[MemoryType] = None,
        agent_did: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MemoryEntry]:
        """搜索记忆条目"""
        pass
    
    @abstractmethod
    async def get_memories_by_session(self, session_id: str) -> List[MemoryEntry]:
        """根据会话ID获取记忆条目"""
        pass
    
    @abstractmethod
    async def save_session(self, session: ContextSession) -> bool:
        """保存上下文会话"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[ContextSession]:
        """获取上下文会话"""
        pass
    
    @abstractmethod
    async def update_session(self, session: ContextSession) -> bool:
        """更新上下文会话"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """删除上下文会话"""
        pass
    
    @abstractmethod
    async def cleanup_expired_memories(self) -> int:
        """清理过期记忆，返回清理数量"""
        pass
    
    @abstractmethod
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        pass


class SQLiteMemoryStorage(MemoryStorageInterface):
    """SQLite记忆存储实现"""
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or get_memory_config()
        self.db_path = Path(self.config.storage.database_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 线程池
        self._executor = ThreadPoolExecutor(
            max_workers=self.config.performance.thread_pool_size
        )
        
        # 内存缓存
        self._memory_cache: Dict[str, MemoryEntry] = {}
        self._session_cache: Dict[str, ContextSession] = {}
        self._cache_lock = threading.RLock()
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path))
            try:
                cursor = conn.cursor()
                
                # 创建记忆条目表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS memory_entries (
                        id TEXT PRIMARY KEY,
                        memory_type TEXT NOT NULL,
                        title TEXT NOT NULL,
                        content TEXT NOT NULL,
                        source_agent_did TEXT NOT NULL,
                        source_agent_name TEXT NOT NULL,
                        target_agent_did TEXT,
                        target_agent_name TEXT,
                        session_id TEXT,
                        tags TEXT,
                        keywords TEXT,
                        relevance_score REAL DEFAULT 1.0,
                        access_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        last_accessed TEXT,
                        expiry_time TEXT
                    )
                ''')
                
                # 创建上下文会话表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS context_sessions (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        participants TEXT,
                        memory_entries TEXT,
                        context_data TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1
                    )
                ''')
                
                # 创建索引
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_memory_type 
                    ON memory_entries(memory_type)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_source_agent 
                    ON memory_entries(source_agent_did)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_session_id 
                    ON memory_entries(session_id)
                ''')
                
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON memory_entries(created_at)
                ''')
                
                conn.commit()
                logger.debug(f"数据库初始化完成: {self.db_path}")
                
            finally:
                conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # 允许按列名访问
        return conn
    
    def _memory_to_row(self, memory: MemoryEntry) -> Tuple:
        """将MemoryEntry转换为数据库行"""
        metadata = memory.metadata
        return (
            memory.id,
            memory.memory_type.value,
            memory.title,
            json.dumps(memory.content, ensure_ascii=False),
            metadata.source_agent_did,
            metadata.source_agent_name,
            metadata.target_agent_did,
            metadata.target_agent_name,
            metadata.session_id,
            json.dumps(metadata.tags, ensure_ascii=False),
            json.dumps(metadata.keywords, ensure_ascii=False),
            metadata.relevance_score,
            metadata.access_count,
            memory.created_at.isoformat(),
            memory.updated_at.isoformat(),
            metadata.last_accessed.isoformat() if metadata.last_accessed else None,
            metadata.expiry_time.isoformat() if metadata.expiry_time else None
        )
    
    def _row_to_memory(self, row: sqlite3.Row) -> MemoryEntry:
        """将数据库行转换为MemoryEntry"""
        from .memory_models import MemoryMetadata
        
        metadata = MemoryMetadata(
            source_agent_did=row['source_agent_did'],
            source_agent_name=row['source_agent_name'],
            target_agent_did=row['target_agent_did'],
            target_agent_name=row['target_agent_name'],
            session_id=row['session_id'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            keywords=json.loads(row['keywords']) if row['keywords'] else [],
            relevance_score=row['relevance_score'],
            access_count=row['access_count'],
            last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
            expiry_time=datetime.fromisoformat(row['expiry_time']) if row['expiry_time'] else None
        )
        
        return MemoryEntry(
            id=row['id'],
            memory_type=MemoryType(row['memory_type']),
            title=row['title'],
            content=json.loads(row['content']),
            metadata=metadata,
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    
    def _session_to_row(self, session: ContextSession) -> Tuple:
        """将ContextSession转换为数据库行"""
        return (
            session.id,
            session.name,
            session.description,
            json.dumps(session.participants, ensure_ascii=False),
            json.dumps(session.memory_entries, ensure_ascii=False),
            json.dumps(session.context_data, ensure_ascii=False),
            session.created_at.isoformat(),
            session.updated_at.isoformat(),
            1 if session.is_active else 0
        )
    
    def _row_to_session(self, row: sqlite3.Row) -> ContextSession:
        """将数据库行转换为ContextSession"""
        return ContextSession(
            id=row['id'],
            name=row['name'],
            description=row['description'] or '',
            participants=json.loads(row['participants']) if row['participants'] else [],
            memory_entries=json.loads(row['memory_entries']) if row['memory_entries'] else [],
            context_data=json.loads(row['context_data']) if row['context_data'] else {},
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at']),
            is_active=bool(row['is_active'])
        )
    
    def _update_cache(self, memory: MemoryEntry):
        """更新内存缓存"""
        with self._cache_lock:
            if len(self._memory_cache) >= self.config.storage.cache_size:
                # 简单的LRU清理：移除最早的条目
                oldest_key = min(self._memory_cache.keys())
                del self._memory_cache[oldest_key]
            self._memory_cache[memory.id] = memory
    
    def _update_session_cache(self, session: ContextSession):
        """更新会话缓存"""
        with self._cache_lock:
            self._session_cache[session.id] = session
    
    async def save_memory(self, memory: MemoryEntry) -> bool:
        """保存记忆条目"""
        try:
            def _save():
                with self._lock:
                    conn = self._get_connection()
                    try:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR REPLACE INTO memory_entries (
                                id, memory_type, title, content,
                                source_agent_did, source_agent_name,
                                target_agent_did, target_agent_name,
                                session_id, tags, keywords,
                                relevance_score, access_count,
                                created_at, updated_at,
                                last_accessed, expiry_time
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', self._memory_to_row(memory))
                        conn.commit()
                        return True
                    finally:
                        conn.close()
            
            if self.config.performance.enable_async_operations:
                loop = None
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                except:
                    pass
                
                if loop:
                    result = await loop.run_in_executor(self._executor, _save)
                else:
                    result = _save()
            else:
                result = _save()
            
            if result:
                self._update_cache(memory)
                logger.debug(f"保存记忆条目成功: {memory.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"保存记忆条目失败: {e}")
            return False
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        """获取记忆条目"""
        # 先检查缓存
        with self._cache_lock:
            if memory_id in self._memory_cache:
                memory = self._memory_cache[memory_id]
                memory.update_access()
                return memory
        
        try:
            def _get():
                with self._lock:
                    conn = self._get_connection()
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            'SELECT * FROM memory_entries WHERE id = ?',
                            (memory_id,)
                        )
                        row = cursor.fetchone()
                        return self._row_to_memory(row) if row else None
                    finally:
                        conn.close()
            
            if self.config.performance.enable_async_operations:
                loop = None
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                except:
                    pass
                
                if loop:
                    memory = await loop.run_in_executor(self._executor, _get)
                else:
                    memory = _get()
            else:
                memory = _get()
            
            if memory:
                memory.update_access()
                self._update_cache(memory)
                # 更新数据库中的访问信息
                await self.update_memory(memory)
            
            return memory
            
        except Exception as e:
            logger.error(f"获取记忆条目失败: {e}")
            return None
    
    async def update_memory(self, memory: MemoryEntry) -> bool:
        """更新记忆条目"""
        memory.updated_at = datetime.now()
        return await self.save_memory(memory)
    
    async def delete_memory(self, memory_id: str) -> bool:
        """删除记忆条目"""
        try:
            def _delete():
                with self._lock:
                    conn = self._get_connection()
                    try:
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM memory_entries WHERE id = ?', (memory_id,))
                        conn.commit()
                        return cursor.rowcount > 0
                    finally:
                        conn.close()
            
            if self.config.performance.enable_async_operations:
                loop = None
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                except:
                    pass
                
                if loop:
                    result = await loop.run_in_executor(self._executor, _delete)
                else:
                    result = _delete()
            else:
                result = _delete()
            
            if result:
                # 从缓存中删除
                with self._cache_lock:
                    self._memory_cache.pop(memory_id, None)
                logger.debug(f"删除记忆条目成功: {memory_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"删除记忆条目失败: {e}")
            return False
    
    async def search_memories(
        self,
        query: str = "",
        memory_type: Optional[MemoryType] = None,
        agent_did: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MemoryEntry]:
        """搜索记忆条目"""
        try:
            def _search():
                with self._lock:
                    conn = self._get_connection()
                    try:
                        cursor = conn.cursor()
                        
                        # 构建查询条件
                        conditions = []
                        params = []
                        
                        if query:
                            conditions.append('(title LIKE ? OR content LIKE ?)')
                            query_pattern = f'%{query}%'
                            params.extend([query_pattern, query_pattern])
                        
                        if memory_type:
                            conditions.append('memory_type = ?')
                            params.append(memory_type.value)
                        
                        if agent_did:
                            conditions.append('(source_agent_did = ? OR target_agent_did = ?)')
                            params.extend([agent_did, agent_did])
                        
                        if session_id:
                            conditions.append('session_id = ?')
                            params.append(session_id)
                        
                        if tags:
                            for tag in tags:
                                conditions.append('tags LIKE ?')
                                params.append(f'%"{tag}"%')
                        
                        if keywords:
                            for keyword in keywords:
                                conditions.append('keywords LIKE ?')
                                params.append(f'%"{keyword}"%')
                        
                        # 构建完整查询
                        sql = 'SELECT * FROM memory_entries'
                        if conditions:
                            sql += ' WHERE ' + ' AND '.join(conditions)
                        sql += ' ORDER BY updated_at DESC LIMIT ? OFFSET ?'
                        params.extend([limit, offset])
                        
                        cursor.execute(sql, params)
                        rows = cursor.fetchall()
                        return [self._row_to_memory(row) for row in rows]
                    
                    finally:
                        conn.close()
            
            if self.config.performance.enable_async_operations:
                loop = None
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                except:
                    pass
                
                if loop:
                    memories = await loop.run_in_executor(self._executor, _search)
                else:
                    memories = _search()
            else:
                memories = _search()
            
            return memories
            
        except Exception as e:
            logger.error(f"搜索记忆条目失败: {e}")
            return []
    
    async def get_memories_by_session(self, session_id: str) -> List[MemoryEntry]:
        """根据会话ID获取记忆条目"""
        return await self.search_memories(query="", session_id=session_id)
    
    async def save_session(self, session: ContextSession) -> bool:
        """保存上下文会话"""
        try:
            def _save():
                with self._lock:
                    conn = self._get_connection()
                    try:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT OR REPLACE INTO context_sessions (
                                id, name, description, participants,
                                memory_entries, context_data,
                                created_at, updated_at, is_active
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', self._session_to_row(session))
                        conn.commit()
                        return True
                    finally:
                        conn.close()
            
            if self.config.performance.enable_async_operations:
                loop = None
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                except:
                    pass
                
                if loop:
                    result = await loop.run_in_executor(self._executor, _save)
                else:
                    result = _save()
            else:
                result = _save()
            
            if result:
                self._update_session_cache(session)
                logger.debug(f"保存会话成功: {session.id}")
            
            return result
            
        except Exception as e:
            logger.error(f"保存会话失败: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[ContextSession]:
        """获取上下文会话"""
        # 先检查缓存
        with self._cache_lock:
            if session_id in self._session_cache:
                return self._session_cache[session_id]
        
        try:
            def _get():
                with self._lock:
                    conn = self._get_connection()
                    try:
                        cursor = conn.cursor()
                        cursor.execute(
                            'SELECT * FROM context_sessions WHERE id = ?',
                            (session_id,)
                        )
                        row = cursor.fetchone()
                        return self._row_to_session(row) if row else None
                    finally:
                        conn.close()
            
            if self.config.performance.enable_async_operations:
                loop = None
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                except:
                    pass
                
                if loop:
                    session = await loop.run_in_executor(self._executor, _get)
                else:
                    session = _get()
            else:
                session = _get()
            
            if session:
                self._update_session_cache(session)
            
            return session
            
        except Exception as e:
            logger.error(f"获取会话失败: {e}")
            return None
    
    async def update_session(self, session: ContextSession) -> bool:
        """更新上下文会话"""
        session.updated_at = datetime.now()
        return await self.save_session(session)
    
    async def delete_session(self, session_id: str) -> bool:
        """删除上下文会话"""
        try:
            def _delete():
                with self._lock:
                    conn = self._get_connection()
                    try:
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM context_sessions WHERE id = ?', (session_id,))
                        conn.commit()
                        return cursor.rowcount > 0
                    finally:
                        conn.close()
            
            if self.config.performance.enable_async_operations:
                loop = None
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                except:
                    pass
                
                if loop:
                    result = await loop.run_in_executor(self._executor, _delete)
                else:
                    result = _delete()
            else:
                result = _delete()
            
            if result:
                # 从缓存中删除
                with self._cache_lock:
                    self._session_cache.pop(session_id, None)
                logger.debug(f"删除会话成功: {session_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"删除会话失败: {e}")
            return False
    
    async def cleanup_expired_memories(self) -> int:
        """清理过期记忆，返回清理数量"""
        try:
            def _cleanup():
                with self._lock:
                    conn = self._get_connection()
                    try:
                        cursor = conn.cursor()
                        now = datetime.now().isoformat()
                        cursor.execute(
                            'DELETE FROM memory_entries WHERE expiry_time IS NOT NULL AND expiry_time < ?',
                            (now,)
                        )
                        conn.commit()
                        return cursor.rowcount
                    finally:
                        conn.close()
            
            if self.config.performance.enable_async_operations:
                loop = None
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                except:
                    pass
                
                if loop:
                    count = await loop.run_in_executor(self._executor, _cleanup)
                else:
                    count = _cleanup()
            else:
                count = _cleanup()
            
            if count > 0:
                logger.info(f"清理了 {count} 个过期记忆条目")
                # 清理缓存中的过期条目
                with self._cache_lock:
                    expired_keys = [
                        k for k, v in self._memory_cache.items() 
                        if v.is_expired()
                    ]
                    for key in expired_keys:
                        del self._memory_cache[key]
            
            return count
            
        except Exception as e:
            logger.error(f"清理过期记忆失败: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            def _get_stats():
                with self._lock:
                    conn = self._get_connection()
                    try:
                        cursor = conn.cursor()
                        
                        # 记忆条目统计
                        cursor.execute('SELECT COUNT(*) FROM memory_entries')
                        total_memories = cursor.fetchone()[0]
                        
                        cursor.execute('SELECT memory_type, COUNT(*) FROM memory_entries GROUP BY memory_type')
                        memory_types = dict(cursor.fetchall())
                        
                        # 会话统计
                        cursor.execute('SELECT COUNT(*) FROM context_sessions')
                        total_sessions = cursor.fetchone()[0]
                        
                        cursor.execute('SELECT COUNT(*) FROM context_sessions WHERE is_active = 1')
                        active_sessions = cursor.fetchone()[0]
                        
                        # 数据库文件大小
                        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                        
                        return {
                            'storage_type': 'sqlite',
                            'database_path': str(self.db_path),
                            'database_size_bytes': db_size,
                            'total_memories': total_memories,
                            'memory_types': memory_types,
                            'total_sessions': total_sessions,
                            'active_sessions': active_sessions,
                            'cache_size': len(self._memory_cache),
                            'session_cache_size': len(self._session_cache)
                        }
                        
                    finally:
                        conn.close()
            
            if self.config.performance.enable_async_operations:
                loop = None
                try:
                    import asyncio
                    loop = asyncio.get_event_loop()
                except:
                    pass
                
                if loop:
                    stats = await loop.run_in_executor(self._executor, _get_stats)
                else:
                    stats = _get_stats()
            else:
                stats = _get_stats()
            
            return stats
            
        except Exception as e:
            logger.error(f"获取存储统计失败: {e}")
            return {}
    
    def close(self):
        """关闭存储"""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=True)


class InMemoryStorage(MemoryStorageInterface):
    """内存存储实现（用于测试和临时存储）"""
    
    def __init__(self):
        self._memories: Dict[str, MemoryEntry] = {}
        self._sessions: Dict[str, ContextSession] = {}
        self._lock = threading.RLock()
    
    async def save_memory(self, memory: MemoryEntry) -> bool:
        with self._lock:
            self._memories[memory.id] = memory
        return True
    
    async def get_memory(self, memory_id: str) -> Optional[MemoryEntry]:
        with self._lock:
            memory = self._memories.get(memory_id)
            if memory:
                memory.update_access()
            return memory
    
    async def update_memory(self, memory: MemoryEntry) -> bool:
        return await self.save_memory(memory)
    
    async def delete_memory(self, memory_id: str) -> bool:
        with self._lock:
            return self._memories.pop(memory_id, None) is not None
    
    async def search_memories(
        self,
        query: str = "",
        memory_type: Optional[MemoryType] = None,
        agent_did: Optional[str] = None,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[MemoryEntry]:
        with self._lock:
            results = []
            for memory in self._memories.values():
                # 简单的过滤逻辑
                if memory_type and memory.memory_type != memory_type:
                    continue
                
                if agent_did and (memory.metadata.source_agent_did != agent_did and
                                 memory.metadata.target_agent_did != agent_did):
                    continue
                
                if session_id and memory.metadata.session_id != session_id:
                    continue
                
                if query and (query.lower() not in memory.title.lower() and
                             query.lower() not in str(memory.content).lower()):
                    continue
                
                if tags and not any(tag in memory.metadata.tags for tag in tags):
                    continue
                
                if keywords and not any(kw in memory.metadata.keywords for kw in keywords):
                    continue
                
                results.append(memory)
            
            # 排序并分页
            results.sort(key=lambda x: x.updated_at, reverse=True)
            return results[offset:offset + limit]
    
    async def get_memories_by_session(self, session_id: str) -> List[MemoryEntry]:
        with self._lock:
            return [m for m in self._memories.values() if m.metadata.session_id == session_id]
    
    async def save_session(self, session: ContextSession) -> bool:
        with self._lock:
            self._sessions[session.id] = session
        return True
    
    async def get_session(self, session_id: str) -> Optional[ContextSession]:
        with self._lock:
            return self._sessions.get(session_id)
    
    async def update_session(self, session: ContextSession) -> bool:
        return await self.save_session(session)
    
    async def delete_session(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None
    
    async def cleanup_expired_memories(self) -> int:
        with self._lock:
            expired_ids = [
                memory_id for memory_id, memory in self._memories.items()
                if memory.is_expired()
            ]
            for memory_id in expired_ids:
                del self._memories[memory_id]
            return len(expired_ids)
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        with self._lock:
            memory_types = {}
            for memory in self._memories.values():
                memory_type = memory.memory_type.value
                memory_types[memory_type] = memory_types.get(memory_type, 0) + 1
            
            return {
                'storage_type': 'memory',
                'total_memories': len(self._memories),
                'memory_types': memory_types,
                'total_sessions': len(self._sessions),
                'active_sessions': sum(1 for s in self._sessions.values() if s.is_active)
            }


def create_storage(config: Optional[MemoryConfig] = None) -> MemoryStorageInterface:
    """创建存储实例"""
    config = config or get_memory_config()
    
    if config.storage.storage_type == 'sqlite':
        return SQLiteMemoryStorage(config)
    elif config.storage.storage_type == 'memory':
        return InMemoryStorage()
    else:
        raise ValueError(f"不支持的存储类型: {config.storage.storage_type}")