import asyncio
from typing import Any, Dict, Optional, List, Tuple
import logging

from .local_methods_decorators import LOCAL_METHODS_REGISTRY
from .local_methods_doc import LocalMethodsDocGenerator
from ..agent_manager import AgentManager

logger = logging.getLogger(__name__)


class LocalMethodsCaller:
    """本地方法调用器"""

    def __init__(self):
        self.doc_generator = LocalMethodsDocGenerator()
        
        # 记忆推荐器（延迟初始化）
        self._memory_recommender = None
        self._memory_config = None
    
    @property
    def memory_recommender(self):
        """获取记忆推荐器（延迟初始化）"""
        if self._memory_recommender is None:
            try:
                from .memory.memory_recommender import get_memory_recommender
                self._memory_recommender = get_memory_recommender()
            except (ImportError, AttributeError):
                self._memory_recommender = None
        return self._memory_recommender
    
    @property
    def memory_config(self):
        """获取记忆配置（延迟初始化）"""
        if self._memory_config is None:
            try:
                from .memory.memory_config import get_memory_config
                self._memory_config = get_memory_config()
            except (ImportError, AttributeError):
                self._memory_config = None
        return self._memory_config
    
    def is_memory_enabled(self) -> bool:
        """检查记忆功能是否启用"""
        config = self.memory_config
        return config is not None and config.enabled

    async def call_method_by_search(
        self,
        search_keyword: str,
        agent_did: Optional[str] = None,
        session_id: Optional[str] = None,
        use_memory_recommendations: bool = True,
        *args, **kwargs
    ) -> Any:
        """
        通过搜索关键词找到方法并调用

        Args:
            search_keyword: 搜索关键词
            agent_did: 调用者Agent DID
            session_id: 会话ID
            use_memory_recommendations: 是否使用记忆推荐
            *args, **kwargs: 方法参数
        """
        # 首先尝试基于记忆的推荐搜索
        if use_memory_recommendations and self.is_memory_enabled():
            try:
                memory_results = await self._search_methods_with_memory_recommendations(
                    search_keyword, agent_did, session_id
                )
                if memory_results:
                    logger.info(f"基于记忆推荐找到 {len(memory_results)} 个方法")
                    # 使用第一个推荐结果
                    best_match = memory_results[0]
                    return await self.call_method_by_key(
                        best_match["method_key"],
                        *args, **kwargs
                    )
            except Exception as e:
                logger.warning(f"记忆推荐搜索失败: {e}，回退到常规搜索")
        
        # 常规搜索方法
        results = self.doc_generator.search_methods(keyword=search_keyword)

        if not results:
            raise ValueError(f"未找到包含关键词 '{search_keyword}' 的方法")

        if len(results) > 1:
            method_list = [f"{r['agent_name']}.{r['method_name']}" for r in results]
            raise ValueError(f"找到多个匹配的方法: {method_list}，请使用更具体的关键词")

        # 调用找到的方法
        method_info = results[0]
        return await self.call_method_by_key(
            method_info["method_key"],
            *args, **kwargs
        )

    async def call_method_by_key(
        self,
        method_key: str,
        agent_did: Optional[str] = None,
        session_id: Optional[str] = None,
        show_memory_recommendations: bool = False,
        *args, **kwargs
    ) -> Any:
        """
        通过方法键调用方法

        Args:
            method_key: 方法键 (格式: module::method_name)
            agent_did: 调用者Agent DID
            session_id: 会话ID
            show_memory_recommendations: 是否显示记忆推荐
            *args, **kwargs: 方法参数
        """
        # 获取方法信息
        method_info = self.doc_generator.get_method_info(method_key)
        if not method_info:
            # 提供更详细的错误信息
            available_keys = list(LOCAL_METHODS_REGISTRY.keys())
            raise ValueError(
                f"未找到方法: {method_key}\n"
                f"可用的方法键:\n" +
                "\n".join(f"  - {key}" for key in available_keys[:10]) +
                (f"\n  ... 还有 {len(available_keys) - 10} 个" if len(available_keys) > 10 else "")
            )
        
        # 显示记忆推荐（如果启用）
        if show_memory_recommendations and self.is_memory_enabled():
            try:
                recommendations = await self._get_method_memory_recommendations(
                    method_key, agent_did, session_id
                )
                if recommendations:
                    print(f"💡 基于历史记忆的相关推荐:")
                    for i, (memory, score) in enumerate(recommendations[:3], 1):
                        print(f"   {i}. {memory.title} (相似度: {score:.2f})")
                        print(f"      时间: {memory.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                logger.warning(f"获取记忆推荐失败: {e}")

        # 获取目标agent
        target_agent = AgentManager.get_agent(method_info["agent_did"], method_info["agent_name"])
        if not target_agent:
            raise ValueError(f"未找到agent: {method_info['agent_did']}")

        # 获取方法
        method_name = method_info["name"]
        if not hasattr(target_agent, method_name):
            raise AttributeError(f"Agent {method_info['agent_name']} 没有方法 {method_name}")

        method = getattr(target_agent, method_name)
        if not callable(method):
            raise TypeError(f"{method_name} 不是可调用方法")


        # 调用方法
        print(f"🚀 调用方法: {method_info['agent_name']}.{method_name}")
        if method_info["is_async"]:
            if asyncio.iscoroutinefunction(method):
                return await method(*args, **kwargs)
            else:
                # 如果标记为异步但实际不是，直接调用
                return method(*args, **kwargs)
        else:
            return method(*args, **kwargs)

    def list_all_methods(self) -> List[Dict]:
        """列出所有可用的本地方法"""
        return list(LOCAL_METHODS_REGISTRY.values())
    
    async def recommend_methods_by_context(
        self,
        keywords: List[str],
        tags: Optional[List[str]] = None,
        agent_did: Optional[str] = None,
        session_id: Optional[str] = None,
        max_recommendations: int = 5
    ) -> List[Dict[str, Any]]:
        """
        基于上下文推荐方法
        
        Args:
            keywords: 关键词列表
            tags: 标签列表
            agent_did: Agent DID
            session_id: 会话ID
            max_recommendations: 最大推荐数量
        
        Returns:
            推荐的方法列表，包含方法信息和推荐分数
        """
        if not self.is_memory_enabled():
            return []
        
        try:
            from .memory.memory_recommender import RecommendationContext
            
            # 检查记忆推荐器是否可用
            if not self.memory_recommender:
                return []
            
            # 创建推荐上下文
            context = RecommendationContext(
                query_keywords=keywords,
                query_tags=tags or [],
                current_agent_did=agent_did,
                current_session_id=session_id
            )
            context.max_recommendations = max_recommendations
            
            # 获取记忆推荐
            memory_recommendations = await self.memory_recommender.recommend_memories(context)
            
            # 将记忆推荐转换为方法推荐
            method_recommendations = []
            for memory, score in memory_recommendations:
                # 从记忆中提取方法信息
                if memory.memory_type.value == 'method_call':
                    method_name = memory.content.get('method_name')
                    method_key = memory.content.get('method_key')
                    
                    if method_key and method_key in LOCAL_METHODS_REGISTRY:
                        method_info = LOCAL_METHODS_REGISTRY[method_key].copy()
                        method_info['recommendation_score'] = score
                        method_info['recommendation_reason'] = f"基于历史记忆推荐 (相似度: {score:.2f})"
                        method_info['related_memory_id'] = memory.id
                        method_recommendations.append(method_info)
            
            return method_recommendations
            
        except Exception as e:
            logger.error(f"基于上下文推荐方法失败: {e}")
            return []
    
    async def get_method_usage_history(
        self,
        method_key: str,
        agent_did: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取方法的使用历史
        
        Args:
            method_key: 方法键
            agent_did: Agent DID
            limit: 最大返回数量
        
        Returns:
            方法使用历史列表
        """
        if not self.is_memory_enabled():
            return []
        
        try:
            from .memory.memory_models import MemoryType
            
            # 检查记忆推荐器是否可用
            if not self.memory_recommender:
                return []
            
            # 搜索方法调用记忆
            memories = await self.memory_recommender.memory_manager.search_memories(
                memory_type=MemoryType.METHOD_CALL,
                agent_did=agent_did,
                limit=limit
            )
            
            # 过滤指定方法的记忆
            method_memories = []
            for memory in memories:
                if memory.content.get('method_key') == method_key:
                    history_item = {
                        'memory_id': memory.id,
                        'timestamp': memory.created_at,
                        'input_args': memory.content.get('input_args', []),
                        'input_kwargs': memory.content.get('input_kwargs', {}),
                        'output': memory.content.get('output'),
                        'execution_time': memory.content.get('execution_time', 0),
                        'agent_name': memory.metadata.source_agent_name,
                        'session_id': memory.metadata.session_id,
                        'success': memory.memory_type == MemoryType.METHOD_CALL
                    }
                    method_memories.append(history_item)
            
            # 按时间排序（最新的在前）
            method_memories.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return method_memories
            
        except Exception as e:
            logger.error(f"获取方法使用历史失败: {e}")
            return []
    
    async def _search_methods_with_memory_recommendations(
        self,
        search_keyword: str,
        agent_did: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """基于记忆推荐搜索方法"""
        
        # 基于关键词推荐方法
        method_recommendations = await self.recommend_methods_by_context(
            keywords=[search_keyword],
            agent_did=agent_did,
            session_id=session_id,
            max_recommendations=5
        )
        
        # 过滤出高分推荐
        high_score_recommendations = [
            rec for rec in method_recommendations
            if rec.get('recommendation_score', 0) >= 0.3
        ]
        
        return high_score_recommendations
    
    async def _get_method_memory_recommendations(
        self,
        method_key: str,
        agent_did: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> List[Tuple[Any, float]]:
        """获取方法的记忆推荐"""
        
        if not method_key in LOCAL_METHODS_REGISTRY:
            return []
        
        # 检查记忆推荐器是否可用
        recommender = self.memory_recommender
        if not recommender:
            return []
        
        method_info = LOCAL_METHODS_REGISTRY[method_key]
        
        # 推荐相关的方法调用记忆
        recommendations = await recommender.recommend_for_method_call(
            method_name=method_info['name'],
            method_key=method_key,
            agent_did=agent_did or method_info.get('agent_did', ''),
            session_id=session_id,
            max_recommendations=5
        )
        
        return recommendations
    
    def get_memory_statistics(self) -> Dict[str, Any]:
        """获取记忆功能统计信息"""
        if not self.is_memory_enabled():
            return {'memory_enabled': False}
        
        try:
            # 检查记忆推荐器是否可用
            recommender = self.memory_recommender
            if not recommender:
                return {'memory_enabled': True, 'error': 'Memory recommender not available'}
            
            # 获取记忆推荐统计
            rec_stats = recommender.get_recommendation_statistics()
            
            # 获取方法记忆配置统计
            from .local_methods_decorators import list_memory_enabled_methods
            memory_enabled_methods = list_memory_enabled_methods()
            
            return {
                'memory_enabled': True,
                'total_methods': len(LOCAL_METHODS_REGISTRY),
                'memory_enabled_methods': len(memory_enabled_methods),
                'recommendation_statistics': rec_stats,
                'memory_enabled_method_keys': memory_enabled_methods
            }
            
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {'memory_enabled': True, 'error': str(e)}
