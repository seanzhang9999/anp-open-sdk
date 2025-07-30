"""
记忆收集器

负责自动收集方法执行记忆，包括输入输出、错误信息等
"""

import asyncio
import inspect
import time
import json
import threading
from datetime import datetime
from functools import wraps
from typing import Dict, List, Optional, Any, Callable, Set, Union
import logging

from .memory_models import MemoryEntry, MemoryType, MethodCallMemory
from .memory_manager import MemoryManager, get_memory_manager
from .memory_config import MemoryConfig, get_memory_config

logger = logging.getLogger(__name__)


class DataFilter:
    """数据过滤器，用于过滤敏感信息"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.sensitive_fields = set(config.security.sensitive_fields)
        self.max_param_length = config.collection.max_param_length
    
    def filter_data(self, data: Any) -> Any:
        """过滤数据中的敏感信息"""
        return self._filter_recursive(data, depth=0, max_depth=10)
    
    def _filter_recursive(self, data: Any, depth: int, max_depth: int) -> Any:
        """递归过滤数据"""
        if depth > max_depth:
            return "<<MAX_DEPTH_EXCEEDED>>"
        
        if isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                if isinstance(key, str) and any(sensitive in key.lower() for sensitive in self.sensitive_fields):
                    filtered[key] = "<<FILTERED>>"
                else:
                    filtered[key] = self._filter_recursive(value, depth + 1, max_depth)
            return filtered
        
        elif isinstance(data, list):
            return [self._filter_recursive(item, depth + 1, max_depth) for item in data[:100]]  # 限制列表长度
        
        elif isinstance(data, tuple):
            return tuple(self._filter_recursive(item, depth + 1, max_depth) for item in data[:100])
        
        elif isinstance(data, str):
            if len(data) > self.max_param_length:
                return data[:self.max_param_length] + "<<TRUNCATED>>"
            return data
        
        elif hasattr(data, '__dict__'):
            # 处理自定义对象
            try:
                obj_dict = {}
                for attr_name in dir(data):
                    if not attr_name.startswith('_'):
                        try:
                            attr_value = getattr(data, attr_name)
                            if not callable(attr_value):
                                obj_dict[attr_name] = self._filter_recursive(attr_value, depth + 1, max_depth)
                        except:
                            obj_dict[attr_name] = "<<INACCESSIBLE>>"
                return f"{type(data).__name__}({obj_dict})"
            except:
                return f"<<{type(data).__name__}_OBJECT>>"
        
        else:
            return data
    
    def serialize_for_storage(self, data: Any) -> str:
        """将数据序列化为存储格式"""
        try:
            filtered_data = self.filter_data(data)
            return json.dumps(filtered_data, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"数据序列化失败: {e}")
            return str(data)[:self.max_param_length]


class CollectionRules:
    """收集规则管理器"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.auto_collect_methods = set(config.collection.auto_collect_methods)
        self.collection_filters = config.collection.collection_filters
        
        # 解析过滤器
        self.include_patterns = self.collection_filters.get('include_patterns', [])
        self.exclude_patterns = self.collection_filters.get('exclude_patterns', [])
        self.agent_whitelist = set(self.collection_filters.get('agent_whitelist', []))
        self.agent_blacklist = set(self.collection_filters.get('agent_blacklist', []))
    
    def should_collect_method(
        self, 
        method_name: str, 
        method_key: str,
        agent_did: str,
        agent_name: str
    ) -> bool:
        """判断是否应该收集该方法的记忆"""
        
        # 检查收集模式
        if not self.config.collection.enable_memory_collection:
            return False
        
        collection_mode = self.config.collection.collection_mode
        
        if collection_mode == 'manual':
            return False  # 手动模式不自动收集
        
        elif collection_mode == 'auto':
            # 自动模式：收集所有（除非被排除）
            pass
        
        elif collection_mode == 'selective':
            # 选择性模式：只收集配置中指定的方法
            if method_name not in self.auto_collect_methods and method_key not in self.auto_collect_methods:
                return False
        
        # 检查Agent黑白名单
        if self.agent_blacklist and agent_did in self.agent_blacklist:
            return False
        
        if self.agent_whitelist and agent_did not in self.agent_whitelist:
            return False
        
        # 检查包含模式
        if self.include_patterns:
            if not any(pattern in method_name or pattern in method_key for pattern in self.include_patterns):
                return False
        
        # 检查排除模式
        if self.exclude_patterns:
            if any(pattern in method_name or pattern in method_key for pattern in self.exclude_patterns):
                return False
        
        return True
    
    def should_collect_input(self) -> bool:
        """是否应该收集输入参数"""
        return self.config.collection.collect_input_params
    
    def should_collect_output(self) -> bool:
        """是否应该收集输出结果"""
        return self.config.collection.collect_output_results
    
    def should_collect_errors(self) -> bool:
        """是否应该收集错误信息"""
        return self.config.collection.collect_errors


class MethodExecutionContext:
    """方法执行上下文"""
    
    def __init__(
        self,
        method_name: str,
        method_key: str,
        agent_did: str,
        agent_name: str,
        session_id: Optional[str] = None
    ):
        self.method_name = method_name
        self.method_key = method_key
        self.agent_did = agent_did
        self.agent_name = agent_name
        self.session_id = session_id
        
        self.start_time = time.time()
        self.end_time = None
        self.input_args = []
        self.input_kwargs = {}
        self.output = None
        self.error = None
        self.success = True
    
    def set_input(self, args: tuple, kwargs: dict):
        """设置输入参数"""
        self.input_args = list(args)
        self.input_kwargs = dict(kwargs)
    
    def set_output(self, output: Any):
        """设置输出结果"""
        self.output = output
        self.end_time = time.time()
    
    def set_error(self, error: Exception):
        """设置错误信息"""
        self.error = error
        self.success = False
        self.end_time = time.time()
    
    @property
    def execution_time(self) -> float:
        """获取执行时间"""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time


class MemoryCollector:
    """记忆收集器主类"""
    
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        config: Optional[MemoryConfig] = None
    ):
        self.config = config or get_memory_config()
        self.memory_manager = memory_manager or get_memory_manager()
        
        # 组件
        self.data_filter = DataFilter(self.config)
        self.collection_rules = CollectionRules(self.config)
        
        # 执行上下文追踪
        self._execution_contexts: Dict[str, MethodExecutionContext] = {}
        self._context_lock = threading.RLock()
        
        # 统计信息
        self._stats = {
            'collections_attempted': 0,
            'collections_successful': 0,
            'collections_filtered': 0,
            'collections_failed': 0
        }
        self._stats_lock = threading.RLock()
    
    def create_collection_decorator(
        self,
        method_name: str,
        method_key: str,
        agent_did: str,
        agent_name: str,
        session_id: Optional[str] = None
    ) -> Callable:
        """创建记忆收集装饰器"""
        
        def decorator(func: Callable) -> Callable:
            # 检查是否应该收集此方法
            if not self.collection_rules.should_collect_method(
                method_name, method_key, agent_did, agent_name
            ):
                return func  # 不收集，直接返回原函数
            
            if inspect.iscoroutinefunction(func):
                @wraps(func)
                async def async_wrapper(*args, **kwargs):
                    return await self._execute_with_collection(
                        func, method_name, method_key, agent_did, agent_name,
                        session_id, args, kwargs, is_async=True
                    )
                return async_wrapper
            
            else:
                @wraps(func)
                def sync_wrapper(*args, **kwargs):
                    return asyncio.run(self._execute_with_collection(
                        func, method_name, method_key, agent_did, agent_name,
                        session_id, args, kwargs, is_async=False
                    ))
                return sync_wrapper
        
        return decorator
    
    async def _execute_with_collection(
        self,
        func: Callable,
        method_name: str,
        method_key: str,
        agent_did: str,
        agent_name: str,
        session_id: Optional[str],
        args: tuple,
        kwargs: dict,
        is_async: bool
    ) -> Any:
        """在记忆收集的上下文中执行方法"""
        
        # 创建执行上下文
        context_id = f"{method_key}_{time.time()}_{id(args)}"
        context = MethodExecutionContext(
            method_name, method_key, agent_did, agent_name, session_id
        )
        
        # 记录输入
        if self.collection_rules.should_collect_input():
            context.set_input(args, kwargs)
        
        # 注册执行上下文
        with self._context_lock:
            self._execution_contexts[context_id] = context
        
        try:
            # 执行原函数
            if is_async:
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 记录输出
            if self.collection_rules.should_collect_output():
                context.set_output(result)
            
            # 收集成功记忆
            await self._collect_memory(context)
            
            return result
            
        except Exception as e:
            # 记录错误
            if self.collection_rules.should_collect_errors():
                context.set_error(e)
                await self._collect_error_memory(context)
            
            raise e
            
        finally:
            # 清理执行上下文
            with self._context_lock:
                self._execution_contexts.pop(context_id, None)
    
    async def _collect_memory(self, context: MethodExecutionContext):
        """收集成功执行的记忆"""
        with self._stats_lock:
            self._stats['collections_attempted'] += 1
        
        try:
            # 创建记忆条目
            memory = await self.memory_manager.create_method_call_memory(
                method_name=context.method_name,
                method_key=context.method_key,
                input_args=context.input_args,
                input_kwargs=context.input_kwargs,
                output=context.output,
                execution_time=context.execution_time,
                source_agent_did=context.agent_did,
                source_agent_name=context.agent_name,
                session_id=context.session_id
            )
            
            with self._stats_lock:
                self._stats['collections_successful'] += 1
            
            logger.debug(f"收集方法记忆成功: {context.method_name}")
            
        except Exception as e:
            with self._stats_lock:
                self._stats['collections_failed'] += 1
            logger.error(f"收集方法记忆失败: {e}")
    
    async def _collect_error_memory(self, context: MethodExecutionContext):
        """收集错误执行的记忆"""
        with self._stats_lock:
            self._stats['collections_attempted'] += 1
        
        try:
            # 创建错误记忆条目
            memory = await self.memory_manager.create_error_memory(
                method_name=context.method_name,
                method_key=context.method_key,
                input_args=context.input_args,
                input_kwargs=context.input_kwargs,
                error=context.error if context.error is not None else Exception("Unknown error"),
                execution_time=context.execution_time,
                source_agent_did=context.agent_did,
                source_agent_name=context.agent_name,
                session_id=context.session_id
            )
            
            with self._stats_lock:
                self._stats['collections_successful'] += 1
            
            logger.debug(f"收集错误记忆成功: {context.method_name}")
            
        except Exception as e:
            with self._stats_lock:
                self._stats['collections_failed'] += 1
            logger.error(f"收集错误记忆失败: {e}")
    
    async def collect_manual_memory(
        self,
        memory_type: MemoryType,
        title: str,
        content: Dict[str, Any],
        agent_did: str,
        agent_name: str,
        session_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        keywords: Optional[List[str]] = None
    ) -> MemoryEntry:
        """手动收集记忆"""
        
        # 过滤敏感数据
        filtered_content = self.data_filter.filter_data(content)
        
        # 创建记忆
        memory = await self.memory_manager.create_memory(
            memory_type=memory_type,
            title=title,
            content=filtered_content,
            source_agent_did=agent_did,
            source_agent_name=agent_name,
            session_id=session_id,
            tags=tags,
            keywords=keywords
        )
        
        with self._stats_lock:
            self._stats['collections_successful'] += 1
        
        logger.info(f"手动收集记忆成功: {title}")
        return memory
    
    def get_active_contexts(self) -> List[MethodExecutionContext]:
        """获取当前活跃的执行上下文"""
        with self._context_lock:
            return list(self._execution_contexts.values())
    
    def get_collection_statistics(self) -> Dict[str, Any]:
        """获取收集统计信息"""
        with self._stats_lock:
            stats = self._stats.copy()
        
        # 添加配置信息
        additional_stats = {
            'collection_enabled': self.config.collection.enable_memory_collection,
            'collection_mode': self.config.collection.collection_mode,
            'auto_collect_methods_count': len(self.collection_rules.auto_collect_methods),
            'collect_input_params': self.config.collection.collect_input_params,
            'collect_output_results': self.config.collection.collect_output_results,
            'collect_errors': self.config.collection.collect_errors,
            'active_contexts': len(self._execution_contexts)
        }
        stats.update(additional_stats)
        
        return stats
    
    def update_collection_rules(self, new_rules: Dict[str, Any]):
        """更新收集规则"""
        # 手动更新配置
        if 'enable_memory_collection' in new_rules:
            self.config.collection.enable_memory_collection = new_rules['enable_memory_collection']
        if 'collection_mode' in new_rules:
            self.config.collection.collection_mode = new_rules['collection_mode']
        if 'auto_collect_methods' in new_rules:
            self.config.collection.auto_collect_methods = new_rules['auto_collect_methods']
        if 'collection_filters' in new_rules:
            self.config.collection.collection_filters = new_rules['collection_filters']
        if 'collect_input_params' in new_rules:
            self.config.collection.collect_input_params = new_rules['collect_input_params']
        if 'collect_output_results' in new_rules:
            self.config.collection.collect_output_results = new_rules['collect_output_results']
        if 'collect_errors' in new_rules:
            self.config.collection.collect_errors = new_rules['collect_errors']
        
        # 重新初始化规则
        self.collection_rules = CollectionRules(self.config)
        
        logger.info("记忆收集规则已更新")
    
    def enable_collection(self):
        """启用记忆收集"""
        self.config.collection.enable_memory_collection = True
        logger.info("记忆收集已启用")
    
    def disable_collection(self):
        """禁用记忆收集"""
        self.config.collection.enable_memory_collection = False
        logger.info("记忆收集已禁用")


# 全局记忆收集器实例
_global_memory_collector: Optional[MemoryCollector] = None


def get_memory_collector() -> MemoryCollector:
    """获取全局记忆收集器实例"""
    global _global_memory_collector
    if _global_memory_collector is None:
        _global_memory_collector = MemoryCollector()
    return _global_memory_collector


def set_memory_collector(collector: MemoryCollector):
    """设置全局记忆收集器实例"""
    global _global_memory_collector
    _global_memory_collector = collector


def memory_collection_decorator(
    method_name: str,
    method_key: str,
    agent_did: str,
    agent_name: str,
    session_id: Optional[str] = None
) -> Callable:
    """记忆收集装饰器的便捷函数"""
    collector = get_memory_collector()
    return collector.create_collection_decorator(
        method_name, method_key, agent_did, agent_name, session_id
    )