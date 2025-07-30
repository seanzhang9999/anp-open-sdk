import inspect
import json
import asyncio
import functools
import time
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path

# 导入记忆相关模块
MEMORY_AVAILABLE = False
try:
    from .memory.memory_options import MemoryOptions, normalize_memory_config
    MEMORY_AVAILABLE = True
except ImportError:
    # 记忆模块不可用时的占位符
    MemoryOptions = None
    normalize_memory_config = None

# 全局注册表，存储所有本地方法信息
LOCAL_METHODS_REGISTRY: Dict[str, Dict] = {}

def local_method(
    description: str = "",
    tags: Optional[List[str]] = None,
    memory = None,
    # 为了向后兼容保留的参数
    enable_memory: Optional[bool] = None,
    memory_tags: Optional[List[str]] = None,
    memory_keywords: Optional[List[str]] = None,
    collect_input: Optional[bool] = None,
    collect_output: Optional[bool] = None,
    collect_errors: Optional[bool] = None
):
    """
    本地方法装饰器（集成记忆功能）

    Args:
        description: 方法描述
        tags: 方法标签
        memory: 记忆配置，支持多种格式：
            - bool: True启用默认记忆，False禁用记忆
            - MemoryOptions: 完整的记忆配置对象
            - dict: 记忆配置字典
            - None: 使用默认配置
        
        # 向后兼容参数（已废弃，建议使用memory参数）
        enable_memory: 是否启用记忆收集
        memory_tags: 记忆标签
        memory_keywords: 记忆关键词
        collect_input: 是否收集输入参数
        collect_output: 是否收集输出结果
        collect_errors: 是否收集错误信息
    
    Examples:
        # 简单启用记忆
        @local_method("计算加法", memory=True)
        def add(a, b):
            return a + b
        
        # 使用完整配置
        @local_method("复杂计算", memory=MemoryOptions(
            enabled=True,
            tags=["math", "calculation"],
            keywords=["addition"],
            collect_input=True,
            collect_output=True
        ))
        def complex_calc(x, y):
            return x * y + 10
        
        # 使用字典配置
        @local_method("数据处理", memory={
            "enabled": True,
            "tags": ["data"],
            "collect_errors": True
        })
        def process_data(data):
            return len(data)
    """
    def decorator(func):
        # 获取函数签名信息
        sig = inspect.signature(func)

        # 处理记忆配置（支持新旧参数格式）
        memory_config = _resolve_memory_config(
            memory, enable_memory, memory_tags, memory_keywords,
            collect_input, collect_output, collect_errors
        )

        # 存储方法信息到全局注册表
        method_info = {
            "name": func.__name__,
            "description": description or func.__doc__ or "",
            "tags": tags or [],
            "signature": str(sig),
            "parameters": {},
            "agent_did": None,  # 稍后注册时填入
            "agent_name": None,
            "module": func.__module__,
            "is_async": inspect.iscoroutinefunction(func),
            # 记忆配置（标准化后的）
            "memory_config": memory_config.to_dict() if (memory_config and hasattr(memory_config, 'to_dict')) else None
        }

        # 解析参数信息
        for param_name, param in sig.parameters.items():
            method_info["parameters"][param_name] = {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                "required": param.default == inspect.Parameter.empty
            }

        # 创建支持记忆的包装函数
        wrapped_func = _create_memory_aware_wrapper(func, method_info)

        # 标记函数并存储信息
        setattr(wrapped_func, '_is_local_method', True)
        setattr(wrapped_func, '_method_info', method_info)
        setattr(wrapped_func, '_original_func', func)
        setattr(wrapped_func, '_memory_config', memory_config)

        return wrapped_func
    return decorator


def _resolve_memory_config(
    memory,
    enable_memory: Optional[bool],
    memory_tags: Optional[List[str]],
    memory_keywords: Optional[List[str]],
    collect_input: Optional[bool],
    collect_output: Optional[bool],
    collect_errors: Optional[bool]
):
    """解析记忆配置，支持新旧参数格式"""
    
    # 如果记忆模块不可用，返回None
    if not MEMORY_AVAILABLE or not normalize_memory_config:
        return None
    
    # 如果有新的memory参数，优先使用
    if memory is not None:
        return normalize_memory_config(memory)
    
    # 处理旧的参数格式（向后兼容）
    if enable_memory is not None or any(v is not None for v in [
        memory_tags, memory_keywords, collect_input, collect_output, collect_errors
    ]):
        # 构建配置字典
        config_dict = {}
        
        if enable_memory is not None:
            config_dict['enabled'] = enable_memory
        
        if memory_tags is not None:
            config_dict['tags'] = memory_tags
            
        if memory_keywords is not None:
            config_dict['keywords'] = memory_keywords
            
        if collect_input is not None:
            config_dict['collect_input'] = collect_input
            
        if collect_output is not None:
            config_dict['collect_output'] = collect_output
            
        if collect_errors is not None:
            config_dict['collect_errors'] = collect_errors
        
        return normalize_memory_config(config_dict)
    
    # 默认使用默认配置
    return normalize_memory_config(None)

def register_local_methods_to_agent(agent, module_or_dict):
    """
    将标记的本地方法注册到agent，并更新全局注册表
    """
    if hasattr(module_or_dict, '__dict__'):
        items = module_or_dict.__dict__.items()
    else:
        items = module_or_dict.items()

    registered_count = 0
    for name, obj in items:
        if callable(obj) and getattr(obj, '_is_local_method', False):
            # 注册到agent
            setattr(agent, name, obj)

            # 更新全局注册表
            method_info = getattr(obj, '_method_info').copy()
            method_info["agent_did"] = agent.anp_user_did
            method_info["agent_name"] = agent.name

            # 🔧 修改：使用module作为唯一标识，避免共享DID冲突
            method_key = f"{method_info['module']}::{name}"
            # 检测冲突（虽然module应该是唯一的，但还是检查一下）
            if method_key in LOCAL_METHODS_REGISTRY:
                existing_info = LOCAL_METHODS_REGISTRY[method_key]
                print(f"⚠️  方法键冲突检测: {method_key}")
                print(f"   现有: {existing_info['agent_name']} ({existing_info['agent_did']})")
                print(f"   新的: {agent.name} ({agent.anp_user_did})")
                print(f"   🔧 覆盖现有方法")

            LOCAL_METHODS_REGISTRY[method_key] = method_info

            registered_count += 1
            print(f"✅ 已注册本地方法: {agent.name}.{name}")

    print(f"📝 共注册了 {registered_count} 个本地方法到 {agent.name}")
    return registered_count


def _create_memory_aware_wrapper(func: Callable, method_info: Dict[str, Any]) -> Callable:
    """创建支持记忆功能的包装函数"""
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        return _execute_with_memory_collection(
            func, method_info, args, kwargs, is_async=False
        )
    
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        return await _execute_with_memory_collection(
            func, method_info, args, kwargs, is_async=True
        )
    
    # 根据原函数类型返回对应的包装函数
    if inspect.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def _execute_with_memory_collection(
    func: Callable,
    method_info: Dict[str, Any],
    args: tuple,
    kwargs: dict,
    is_async: bool = False
):
    """执行函数并收集记忆"""
    
    # 获取记忆配置
    memory_config = method_info.get("memory_config", {})
    
    # 检查是否需要启用记忆收集
    should_collect_memory = (
        memory_config and 
        memory_config.get("enabled", False) and 
        MEMORY_AVAILABLE
    )
    
    # 如果不需要记忆收集，直接执行原函数（但仍然正确传递参数）
    if not should_collect_memory:
        if is_async:
            return func(*args, **kwargs)
        else:
            return func(*args, **kwargs)
    
    # 记录执行开始时间
    start_time = time.time()
    
    # 获取记忆收集器（延迟导入避免循环依赖）
    try:
        from .memory.memory_collector import get_memory_collector
        memory_collector = get_memory_collector()
    except (ImportError, AttributeError):
        # 如果记忆模块不可用，直接执行原函数
        if is_async:
            return func(*args, **kwargs)  # 直接返回协程对象，不要用 create_task
        else:
            return func(*args, **kwargs)
    
    # 生成方法键
    method_key = f"{method_info['module']}::{method_info['name']}"
    
    if is_async:
        return _execute_async_with_memory(
            func, method_info, method_key, args, kwargs,
            start_time, memory_collector
        )
    else:
        return _execute_sync_with_memory(
            func, method_info, method_key, args, kwargs,
            start_time, memory_collector
        )


async def _execute_async_with_memory(
    func: Callable,
    method_info: Dict[str, Any],
    method_key: str,
    args: tuple,
    kwargs: dict,
    start_time: float,
    memory_collector
):
    """异步执行函数并收集记忆"""
    
    try:
        # 执行函数
        result = await func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # 收集成功记忆（如果启用了输出收集）
        memory_config = method_info.get('memory_config', {})
        if memory_config.get('collect_output', True):
            # 使用新的记忆管理器API
            asyncio.create_task(memory_collector.memory_manager.create_method_call_memory(
                method_name=method_info['name'],
                method_key=method_key,
                input_args=list(args) if memory_config.get('collect_input', True) else [],
                input_kwargs=kwargs if memory_config.get('collect_input', True) else {},
                output=result,
                execution_time=execution_time,
                source_agent_did=method_info.get('agent_did') or 'unknown',
                source_agent_name=method_info.get('agent_name') or 'unknown',
                session_id=None
            ))
        
        return result
        
    except Exception as error:
        execution_time = time.time() - start_time
        
        # 收集错误记忆（如果启用了错误收集）
        memory_config = method_info.get('memory_config', {})
        if memory_config.get('collect_errors', True):
            asyncio.create_task(memory_collector.memory_manager.create_method_call_memory(
                method_name=method_info['name'],
                method_key=method_key,
                input_args=list(args) if memory_config.get('collect_input', True) else [],
                input_kwargs=kwargs if memory_config.get('collect_input', True) else {},
                output=None,
                execution_time=execution_time,
                source_agent_did=method_info.get('agent_did') or 'unknown',
                source_agent_name=method_info.get('agent_name') or 'unknown',
                session_id=None,
                error=error
            ))
        
        # 重新抛出异常
        raise


def _execute_sync_with_memory(
    func: Callable,
    method_info: Dict[str, Any],
    method_key: str,
    args: tuple,
    kwargs: dict,
    start_time: float,
    memory_collector
):
    """同步执行函数并收集记忆"""
    
    try:
        # 执行函数
        result = func(*args, **kwargs)
        execution_time = time.time() - start_time
        
        # 收集成功记忆（如果启用了输出收集）
        memory_config = method_info.get('memory_config', {})
        if memory_config.get('collect_output', True):
            try:
                asyncio.create_task(memory_collector.memory_manager.create_method_call_memory(
                    method_name=method_info['name'],
                    method_key=method_key,
                    input_args=list(args) if memory_config.get('collect_input', True) else [],
                    input_kwargs=kwargs if memory_config.get('collect_input', True) else {},
                    output=result,
                    execution_time=execution_time,
                    source_agent_did=method_info.get('agent_did') or 'unknown',
                    source_agent_name=method_info.get('agent_name') or 'unknown',
                    session_id=None
                ))
            except RuntimeError:
                # 如果没有事件循环，跳过记忆收集
                pass
        
        return result
        
    except Exception as error:
        execution_time = time.time() - start_time
        
        # 收集错误记忆（如果启用了错误收集）
        memory_config = method_info.get('memory_config', {})
        if memory_config.get('collect_errors', True):
            try:
                asyncio.create_task(memory_collector.memory_manager.create_method_call_memory(
                    method_name=method_info['name'],
                    method_key=method_key,
                    input_args=list(args) if memory_config.get('collect_input', True) else [],
                    input_kwargs=kwargs if memory_config.get('collect_input', True) else {},
                    output=None,
                    execution_time=execution_time,
                    source_agent_did=method_info.get('agent_did') or 'unknown',
                    source_agent_name=method_info.get('agent_name') or 'unknown',
                    session_id=None,
                    error=error
                ))
            except RuntimeError:
                # 如果没有事件循环，跳过记忆收集
                pass
        
        # 重新抛出异常
        raise


def get_method_memory_config(method_key: str) -> Optional[Dict[str, Any]]:
    """获取方法的记忆配置"""
    method_info = LOCAL_METHODS_REGISTRY.get(method_key)
    if method_info:
        return method_info.get('memory_config')
    return None


def update_method_memory_config(method_key: str, config_updates: Dict[str, Any]) -> bool:
    """更新方法的记忆配置"""
    if method_key in LOCAL_METHODS_REGISTRY:
        method_info = LOCAL_METHODS_REGISTRY[method_key]
        memory_config = method_info.setdefault('memory_config', {})
        memory_config.update(config_updates)
        return True
    return False


def list_memory_enabled_methods() -> List[str]:
    """列出启用记忆功能的方法"""
    memory_methods = []
    for method_key, method_info in LOCAL_METHODS_REGISTRY.items():
        memory_config = method_info.get('memory_config', {})
        if memory_config and memory_config.get('enabled'):
            memory_methods.append(method_key)
    return memory_methods
