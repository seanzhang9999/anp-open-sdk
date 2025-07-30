"""
记忆推荐器

基于历史记忆提供智能推荐，支持多种推荐算法
"""

import asyncio
import math
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple, Callable
import logging

from .memory_models import MemoryEntry, MemoryType
from .memory_manager import MemoryManager, get_memory_manager
from .memory_config import MemoryConfig, get_memory_config
from .context_session import ContextSessionManager, get_session_manager

logger = logging.getLogger(__name__)


class RecommendationContext:
    """推荐上下文"""
    
    def __init__(
        self,
        query_keywords: Optional[List[str]] = None,
        query_tags: Optional[List[str]] = None,
        current_agent_did: Optional[str] = None,
        current_session_id: Optional[str] = None,
        current_method_name: Optional[str] = None,
        context_data: Optional[Dict[str, Any]] = None,
        time_range: Optional[Tuple[datetime, datetime]] = None,
        memory_types: Optional[List[MemoryType]] = None
    ):
        self.query_keywords = query_keywords or []
        self.query_tags = query_tags or []
        self.current_agent_did = current_agent_did
        self.current_session_id = current_session_id
        self.current_method_name = current_method_name
        self.context_data = context_data or {}
        self.time_range = time_range
        self.memory_types = memory_types or []
        
        # 推荐参数
        self.max_recommendations = 10
        self.similarity_threshold = 0.3
        self.include_similar_methods = True
        self.include_error_memories = False
        self.boost_recent_memories = True


class ScoringFunction:
    """评分函数基类"""
    
    def __init__(self, weight: float = 1.0):
        self.weight = weight
    
    def calculate_score(
        self, 
        memory: MemoryEntry, 
        context: RecommendationContext
    ) -> float:
        """计算记忆条目的评分"""
        raise NotImplementedError


class KeywordScoringFunction(ScoringFunction):
    """基于关键词的评分函数"""
    
    def calculate_score(
        self, 
        memory: MemoryEntry, 
        context: RecommendationContext
    ) -> float:
        if not context.query_keywords:
            return 0.0
        
        # 计算关键词匹配度
        memory_keywords = set(memory.metadata.keywords)
        query_keywords = set(context.query_keywords)
        
        if not memory_keywords or not query_keywords:
            return 0.0
        
        # Jaccard相似度
        intersection = len(memory_keywords & query_keywords)
        union = len(memory_keywords | query_keywords)
        
        return intersection / union if union > 0 else 0.0


class TagScoringFunction(ScoringFunction):
    """基于标签的评分函数"""
    
    def calculate_score(
        self, 
        memory: MemoryEntry, 
        context: RecommendationContext
    ) -> float:
        if not context.query_tags:
            return 0.0
        
        memory_tags = set(memory.metadata.tags)
        query_tags = set(context.query_tags)
        
        if not memory_tags or not query_tags:
            return 0.0
        
        # Jaccard相似度
        intersection = len(memory_tags & query_tags)
        union = len(memory_tags | query_tags)
        
        return intersection / union if union > 0 else 0.0


class TimeScoringFunction(ScoringFunction):
    """基于时间的评分函数"""
    
    def __init__(self, weight: float = 1.0, decay_days: int = 30):
        super().__init__(weight)
        self.decay_days = decay_days
    
    def calculate_score(
        self, 
        memory: MemoryEntry, 
        context: RecommendationContext
    ) -> float:
        # 时间衰减函数：越新的记忆分数越高
        now = datetime.now()
        age_days = (now - memory.created_at).days
        
        # 使用指数衰减函数
        decay_factor = math.exp(-age_days / self.decay_days)
        
        return decay_factor


class AccessFrequencyScoringFunction(ScoringFunction):
    """基于访问频次的评分函数"""
    
    def calculate_score(
        self, 
        memory: MemoryEntry, 
        context: RecommendationContext
    ) -> float:
        # 访问次数归一化（使用对数函数避免过大的差异）
        access_count = memory.metadata.access_count
        if access_count <= 0:
            return 0.0
        
        # 使用对数归一化
        return math.log(access_count + 1) / math.log(100)  # 假设最大访问次数为100


class AgentAffinityScoringFunction(ScoringFunction):
    """基于Agent亲和度的评分函数"""
    
    def calculate_score(
        self, 
        memory: MemoryEntry, 
        context: RecommendationContext
    ) -> float:
        if not context.current_agent_did:
            return 0.0
        
        # 相同Agent的记忆得分更高
        if memory.metadata.source_agent_did == context.current_agent_did:
            return 1.0
        elif memory.metadata.target_agent_did == context.current_agent_did:
            return 0.7
        else:
            return 0.0


class SessionAffinityScoringFunction(ScoringFunction):
    """基于会话亲和度的评分函数"""
    
    def calculate_score(
        self, 
        memory: MemoryEntry, 
        context: RecommendationContext
    ) -> float:
        if not context.current_session_id or not memory.metadata.session_id:
            return 0.0
        
        # 相同会话的记忆得分更高
        return 1.0 if memory.metadata.session_id == context.current_session_id else 0.0


class MethodSimilarityScoringFunction(ScoringFunction):
    """基于方法相似度的评分函数"""
    
    def calculate_score(
        self, 
        memory: MemoryEntry, 
        context: RecommendationContext
    ) -> float:
        if not context.current_method_name or memory.memory_type != MemoryType.METHOD_CALL:
            return 0.0
        
        memory_method_name = memory.content.get('method_name', '')
        if not memory_method_name:
            return 0.0
        
        # 简单的字符串相似度
        if memory_method_name == context.current_method_name:
            return 1.0
        elif context.current_method_name in memory_method_name or memory_method_name in context.current_method_name:
            return 0.7
        else:
            return 0.0


class RecommendationAlgorithm:
    """推荐算法基类"""
    
    def __init__(self, config: MemoryConfig):
        self.config = config
        self.scoring_functions: List[ScoringFunction] = []
    
    def add_scoring_function(self, scoring_function: ScoringFunction):
        """添加评分函数"""
        self.scoring_functions.append(scoring_function)
    
    async def recommend(
        self, 
        memory_manager: MemoryManager,
        context: RecommendationContext
    ) -> List[Tuple[MemoryEntry, float]]:
        """生成推荐列表"""
        raise NotImplementedError


class HybridRecommendationAlgorithm(RecommendationAlgorithm):
    """混合推荐算法"""
    
    def __init__(self, config: MemoryConfig):
        super().__init__(config)
        
        # 根据配置初始化评分函数
        self.add_scoring_function(
            KeywordScoringFunction(weight=config.recommendation.keyword_weight)
        )
        self.add_scoring_function(
            TagScoringFunction(weight=config.recommendation.tag_weight)
        )
        self.add_scoring_function(
            TimeScoringFunction(weight=config.recommendation.time_weight)
        )
        self.add_scoring_function(
            AccessFrequencyScoringFunction(weight=config.recommendation.access_weight)
        )
        self.add_scoring_function(
            AgentAffinityScoringFunction(weight=0.1)
        )
        self.add_scoring_function(
            SessionAffinityScoringFunction(weight=0.1)
        )
        self.add_scoring_function(
            MethodSimilarityScoringFunction(weight=0.1)
        )
    
    async def recommend(
        self,
        memory_manager: MemoryManager,
        context: RecommendationContext
    ) -> List[Tuple[MemoryEntry, float]]:
        """生成混合推荐"""
        
        # 构建搜索参数
        limit = context.max_recommendations * 3  # 获取更多候选以便筛选
        
        if context.memory_types:
            # 如果指定了多个类型，需要分别搜索后合并
            all_memories = []
            for memory_type in context.memory_types:
                memories = await memory_manager.search_memories(
                    keywords=context.query_keywords or None,
                    tags=context.query_tags or None,
                    agent_did=context.current_agent_did,
                    session_id=context.current_session_id,
                    memory_type=memory_type,
                    limit=limit,
                    offset=0
                )
                all_memories.extend(memories)
            
            # 去重
            unique_memories = {m.id: m for m in all_memories}.values()
            candidate_memories = list(unique_memories)
        else:
            candidate_memories = await memory_manager.search_memories(
                keywords=context.query_keywords or None,
                tags=context.query_tags or None,
                agent_did=context.current_agent_did,
                session_id=context.current_session_id,
                limit=limit,
                offset=0
            )
        
        # 应用时间范围过滤
        if context.time_range:
            start_time, end_time = context.time_range
            candidate_memories = [
                m for m in candidate_memories
                if start_time <= m.created_at <= end_time
            ]
        
        # 过滤错误记忆（如果配置不包含）
        if not context.include_error_memories:
            candidate_memories = [
                m for m in candidate_memories
                if m.memory_type != MemoryType.ERROR
            ]
        
        # 计算推荐分数
        scored_memories = []
        for memory in candidate_memories:
            total_score = 0.0
            
            for scoring_function in self.scoring_functions:
                score = scoring_function.calculate_score(memory, context)
                total_score += score * scoring_function.weight
            
            # 相关度分数加权
            total_score *= memory.metadata.relevance_score
            
            # 应用相似度阈值
            if total_score >= context.similarity_threshold:
                scored_memories.append((memory, total_score))
        
        # 排序并返回前N个
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return scored_memories[:context.max_recommendations]


class KeywordRecommendationAlgorithm(RecommendationAlgorithm):
    """基于关键词的推荐算法"""
    
    async def recommend(
        self,
        memory_manager: MemoryManager,
        context: RecommendationContext
    ) -> List[Tuple[MemoryEntry, float]]:
        """基于关键词的推荐"""
        
        if not context.query_keywords:
            return []
        
        # 搜索包含关键词的记忆
        memories = await memory_manager.search_memories(
            keywords=context.query_keywords,
            limit=context.max_recommendations * 2,
            offset=0
        )
        
        # 计算关键词匹配分数
        keyword_scorer = KeywordScoringFunction()
        scored_memories = []
        
        for memory in memories:
            score = keyword_scorer.calculate_score(memory, context)
            if score >= context.similarity_threshold:
                scored_memories.append((memory, score))
        
        # 排序并返回
        scored_memories.sort(key=lambda x: x[1], reverse=True)
        return scored_memories[:context.max_recommendations]


class MemoryRecommender:
    """记忆推荐器主类"""
    
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        session_manager: Optional[ContextSessionManager] = None,
        config: Optional[MemoryConfig] = None
    ):
        self.config = config or get_memory_config()
        self.memory_manager = memory_manager or get_memory_manager()
        self.session_manager = session_manager or get_session_manager()
        
        # 推荐算法
        self.algorithms = {
            'hybrid': HybridRecommendationAlgorithm(self.config),
            'keyword': KeywordRecommendationAlgorithm(self.config),
            'similarity': HybridRecommendationAlgorithm(self.config)  # 使用混合算法作为相似度算法
        }
        
        # 推荐缓存
        self._recommendation_cache: Dict[str, Tuple[List[Tuple[MemoryEntry, float]], datetime]] = {}
        self._cache_lock = threading.RLock()
        
        # 统计信息
        self._stats = {
            'recommendations_generated': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'avg_recommendation_score': 0.0
        }
        self._stats_lock = threading.RLock()
    
    async def recommend_memories(
        self,
        context: RecommendationContext,
        algorithm: str = 'hybrid',
        use_cache: bool = True
    ) -> List[Tuple[MemoryEntry, float]]:
        """推荐记忆条目"""
        
        # 生成缓存键
        cache_key = self._generate_cache_key(context, algorithm)
        
        # 检查缓存
        if use_cache and self.config.performance.enable_search_cache:
            cached_result = self._get_cached_recommendation(cache_key)
            if cached_result:
                with self._stats_lock:
                    self._stats['cache_hits'] += 1
                return cached_result
        
        # 检查算法是否存在
        if algorithm not in self.algorithms:
            algorithm = 'hybrid'  # 默认使用混合算法
        
        # 生成推荐
        recommendations = await self.algorithms[algorithm].recommend(
            self.memory_manager, context
        )
        
        # 缓存结果
        if use_cache and self.config.performance.enable_search_cache:
            self._cache_recommendation(cache_key, recommendations)
            with self._stats_lock:
                self._stats['cache_misses'] += 1
        
        # 更新统计
        with self._stats_lock:
            self._stats['recommendations_generated'] += 1
            if recommendations:
                avg_score = sum(score for _, score in recommendations) / len(recommendations)
                self._stats['avg_recommendation_score'] = (
                    self._stats['avg_recommendation_score'] * 0.9 + avg_score * 0.1
                )
        
        logger.debug(f"生成了 {len(recommendations)} 个推荐 (算法: {algorithm})")
        return recommendations
    
    async def recommend_for_method_call(
        self,
        method_name: str,
        method_key: str,
        agent_did: str,
        session_id: Optional[str] = None,
        max_recommendations: int = 5
    ) -> List[Tuple[MemoryEntry, float]]:
        """为方法调用推荐相关记忆"""
        
        context = RecommendationContext(
            query_keywords=[method_name, method_key],
            current_agent_did=agent_did,
            current_session_id=session_id,
            current_method_name=method_name,
            memory_types=[MemoryType.METHOD_CALL, MemoryType.PATTERN]
        )
        context.max_recommendations = max_recommendations
        context.include_error_memories = True  # 包含错误记忆以供参考
        
        return await self.recommend_memories(context)
    
    async def recommend_for_context(
        self,
        keywords: List[str],
        tags: List[str],
        agent_did: Optional[str] = None,
        session_id: Optional[str] = None,
        max_recommendations: int = 10
    ) -> List[Tuple[MemoryEntry, float]]:
        """为上下文推荐相关记忆"""
        
        context = RecommendationContext(
            query_keywords=keywords,
            query_tags=tags,
            current_agent_did=agent_did,
            current_session_id=session_id
        )
        context.max_recommendations = max_recommendations
        
        return await self.recommend_memories(context)
    
    async def recommend_similar_memories(
        self,
        reference_memory: MemoryEntry,
        max_recommendations: int = 5
    ) -> List[Tuple[MemoryEntry, float]]:
        """推荐与指定记忆相似的记忆"""
        
        context = RecommendationContext(
            query_keywords=reference_memory.metadata.keywords,
            query_tags=reference_memory.metadata.tags,
            current_agent_did=reference_memory.metadata.source_agent_did,
            current_session_id=reference_memory.metadata.session_id,
            memory_types=[reference_memory.memory_type]
        )
        context.max_recommendations = max_recommendations
        
        recommendations = await self.recommend_memories(context)
        
        # 移除参考记忆本身
        recommendations = [
            (memory, score) for memory, score in recommendations
            if memory.id != reference_memory.id
        ]
        
        return recommendations
    
    def _generate_cache_key(self, context: RecommendationContext, algorithm: str) -> str:
        """生成缓存键"""
        key_data = {
            'algorithm': algorithm,
            'keywords': sorted(context.query_keywords),
            'tags': sorted(context.query_tags),
            'agent_did': context.current_agent_did,
            'session_id': context.current_session_id,
            'method_name': context.current_method_name,
            'memory_types': [mt.value for mt in context.memory_types],
            'max_recommendations': context.max_recommendations,
            'similarity_threshold': context.similarity_threshold
        }
        return str(hash(str(sorted(key_data.items()))))
    
    def _get_cached_recommendation(
        self, 
        cache_key: str
    ) -> Optional[List[Tuple[MemoryEntry, float]]]:
        """获取缓存的推荐结果"""
        with self._cache_lock:
            if cache_key in self._recommendation_cache:
                recommendations, cached_time = self._recommendation_cache[cache_key]
                # 检查缓存是否过期（10分钟）
                if datetime.now() - cached_time < timedelta(minutes=10):
                    return recommendations
                else:
                    del self._recommendation_cache[cache_key]
        return None
    
    def _cache_recommendation(
        self, 
        cache_key: str, 
        recommendations: List[Tuple[MemoryEntry, float]]
    ):
        """缓存推荐结果"""
        with self._cache_lock:
            # 限制缓存大小
            if len(self._recommendation_cache) >= self.config.performance.search_cache_size:
                # 移除最旧的缓存
                oldest_key = min(self._recommendation_cache.keys(), 
                               key=lambda k: self._recommendation_cache[k][1])
                del self._recommendation_cache[oldest_key]
            
            self._recommendation_cache[cache_key] = (recommendations, datetime.now())
    
    def get_recommendation_statistics(self) -> Dict[str, Any]:
        """获取推荐统计信息"""
        with self._stats_lock:
            stats = self._stats.copy()
        
        stats.update({
            'algorithms_available': list(self.algorithms.keys()),
            'cache_size': len(self._recommendation_cache),
            'cache_hit_ratio': (
                stats['cache_hits'] / max(stats['cache_hits'] + stats['cache_misses'], 1)
            )
        })
        
        return stats
    
    def clear_cache(self):
        """清空推荐缓存"""
        with self._cache_lock:
            self._recommendation_cache.clear()
        logger.info("推荐缓存已清空")


# 全局记忆推荐器实例
_global_memory_recommender: Optional[MemoryRecommender] = None


def get_memory_recommender() -> MemoryRecommender:
    """获取全局记忆推荐器实例"""
    global _global_memory_recommender
    if _global_memory_recommender is None:
        _global_memory_recommender = MemoryRecommender()
    return _global_memory_recommender


def set_memory_recommender(recommender: MemoryRecommender):
    """设置全局记忆推荐器实例"""
    global _global_memory_recommender
    _global_memory_recommender = recommender