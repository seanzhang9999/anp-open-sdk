import inspect
import json
from typing import Dict, Any, List
from pathlib import Path

# 全局注册表，存储所有本地方法信息
LOCAL_METHODS_REGISTRY: Dict[str, Dict] = {}

def local_method(description: str = "", tags: List[str] = None):
    """
    本地方法装饰器

    Args:
        description: 方法描述
        tags: 方法标签
    """
    def decorator(func):
        # 获取函数签名信息
        sig = inspect.signature(func)

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
            "is_async": inspect.iscoroutinefunction(func)
        }

        # 解析参数信息
        for param_name, param in sig.parameters.items():
            method_info["parameters"][param_name] = {
                "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any",
                "default": str(param.default) if param.default != inspect.Parameter.empty else None,
                "required": param.default == inspect.Parameter.empty
            }

        # 标记函数并存储信息
        func._is_local_method = True
        func._method_info = method_info

        return func
    return decorator

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
            method_info = obj._method_info.copy()
            method_info["agent_did"] = agent.anp_user_id
            method_info["agent_name"] = agent.name

            # 🔧 修改：使用module作为唯一标识，避免共享DID冲突
            method_key = f"{method_info['module']}::{name}"
            # 检测冲突（虽然module应该是唯一的，但还是检查一下）
            if method_key in LOCAL_METHODS_REGISTRY:
                existing_info = LOCAL_METHODS_REGISTRY[method_key]
                print(f"⚠️  方法键冲突检测: {method_key}")
                print(f"   现有: {existing_info['agent_name']} ({existing_info['agent_did']})")
                print(f"   新的: {agent.name} ({agent.anp_user_id})")
                print(f"   🔧 覆盖现有方法")

            LOCAL_METHODS_REGISTRY[method_key] = method_info

            registered_count += 1
            print(f"✅ 已注册本地方法: {agent.name}.{name}")

    print(f"📝 共注册了 {registered_count} 个本地方法到 {agent.name}")
    return registered_count