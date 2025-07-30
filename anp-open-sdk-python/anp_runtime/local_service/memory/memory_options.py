"""
记忆选项配置类

提供结构化的记忆配置选项，用于 @local_method 装饰器
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Union
from .memory_config import MemoryConfig, get_memory_config


@dataclass
class MemoryOptions:
    """
    记忆选项配置类
    
    用于配置本地方法的记忆收集行为
    """
    
    # 是否启用记忆收集
    enabled: bool = True
    
    # 记忆标签
    tags: List[str] = field(default_factory=list)
    
    # 记忆关键词
    keywords: List[str] = field(default_factory=list)
    
    # 收集选项
    collect_input: bool = True
    collect_output: bool = True  
    collect_errors: bool = True
    
    # 会话ID（可选）
    session_id: Optional[str] = None
    
    # 扩展配置
    extra: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def default(cls) -> 'MemoryOptions':
        """创建默认配置"""
        return cls()
    
    @classmethod
    def disabled(cls) -> 'MemoryOptions':
        """创建禁用记忆的配置"""
        return cls(enabled=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryOptions':
        """从字典创建配置"""
        return cls(
            enabled=data.get('enabled', True),
            tags=data.get('tags', []),
            keywords=data.get('keywords', []),
            collect_input=data.get('collect_input', True),
            collect_output=data.get('collect_output', True),
            collect_errors=data.get('collect_errors', True),
            session_id=data.get('session_id'),
            extra=data.get('extra', {})
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'enabled': self.enabled,
            'tags': self.tags,
            'keywords': self.keywords,
            'collect_input': self.collect_input,
            'collect_output': self.collect_output,
            'collect_errors': self.collect_errors,
            'session_id': self.session_id,
            'extra': self.extra
        }
    
    def merge_with_global_config(self, global_config: Optional[MemoryConfig] = None) -> 'MemoryOptions':
        """与全局配置合并，返回新的配置实例"""
        if global_config is None:
            try:
                global_config = get_memory_config()
            except:
                global_config = None
        
        # 如果全局配置禁用了记忆功能，则禁用
        if global_config and not global_config.enabled:
            return MemoryOptions.disabled()
        
        # 如果全局配置禁用了记忆收集，则禁用
        if global_config and not global_config.collection.enable_memory_collection:
            return MemoryOptions.disabled()
        
        # 复制当前配置
        merged = MemoryOptions(
            enabled=self.enabled,
            tags=self.tags.copy(),
            keywords=self.keywords.copy(),
            collect_input=self.collect_input,
            collect_output=self.collect_output,
            collect_errors=self.collect_errors,
            session_id=self.session_id,
            extra=self.extra.copy()
        )
        
        # 如果有全局配置，合并相关设置
        if global_config:
            # 如果本地没有明确设置收集选项，使用全局设置
            if not hasattr(self, '_collect_input_set'):
                merged.collect_input = global_config.collection.collect_input_params
            if not hasattr(self, '_collect_output_set'):
                merged.collect_output = global_config.collection.collect_output_results
            if not hasattr(self, '_collect_errors_set'):
                merged.collect_errors = global_config.collection.collect_errors
        
        return merged
    
    def update(self, **kwargs) -> 'MemoryOptions':
        """更新配置，返回新的配置实例"""
        new_config = MemoryOptions(
            enabled=kwargs.get('enabled', self.enabled),
            tags=kwargs.get('tags', self.tags.copy()),
            keywords=kwargs.get('keywords', self.keywords.copy()),
            collect_input=kwargs.get('collect_input', self.collect_input),
            collect_output=kwargs.get('collect_output', self.collect_output),
            collect_errors=kwargs.get('collect_errors', self.collect_errors),
            session_id=kwargs.get('session_id', self.session_id),
            extra=kwargs.get('extra', self.extra.copy())
        )
        return new_config
    
    def is_collection_enabled(self) -> bool:
        """检查是否启用了记忆收集"""
        if not self.enabled:
            return False
        
        try:
            global_config = get_memory_config()
            return (global_config.enabled and 
                    global_config.collection.enable_memory_collection)
        except:
            return False
    
    def should_collect_input(self) -> bool:
        """是否应该收集输入"""
        return self.enabled and self.collect_input
    
    def should_collect_output(self) -> bool:
        """是否应该收集输出"""
        return self.enabled and self.collect_output
    
    def should_collect_errors(self) -> bool:
        """是否应该收集错误"""
        return self.enabled and self.collect_errors


# 便捷函数
def memory_enabled(
    tags: Optional[List[str]] = None,
    keywords: Optional[List[str]] = None,
    collect_input: bool = True,
    collect_output: bool = True,
    collect_errors: bool = True,
    session_id: Optional[str] = None,
    **extra
) -> MemoryOptions:
    """创建启用记忆的配置"""
    return MemoryOptions(
        enabled=True,
        tags=tags or [],
        keywords=keywords or [],
        collect_input=collect_input,
        collect_output=collect_output,
        collect_errors=collect_errors,
        session_id=session_id,
        extra=extra
    )


def memory_disabled() -> MemoryOptions:
    """创建禁用记忆的配置"""
    return MemoryOptions.disabled()


# 类型别名，支持多种配置方式
MemoryConfigType = Union[bool, MemoryOptions, Dict[str, Any], None]


def normalize_memory_config(config: MemoryConfigType) -> MemoryOptions:
    """
    标准化记忆配置
    
    Args:
        config: 记忆配置，可以是：
            - bool: True启用默认配置，False禁用
            - MemoryOptions: 直接使用
            - dict: 从字典创建配置
            - None: 使用默认配置
    
    Returns:
        标准化的MemoryOptions配置
    """
    if config is None:
        return MemoryOptions.default()
    elif isinstance(config, bool):
        return MemoryOptions.default() if config else MemoryOptions.disabled()
    elif isinstance(config, MemoryOptions):
        return config
    elif isinstance(config, dict):
        return MemoryOptions.from_dict(config)
    else:
        raise ValueError(f"不支持的记忆配置类型: {type(config)}")