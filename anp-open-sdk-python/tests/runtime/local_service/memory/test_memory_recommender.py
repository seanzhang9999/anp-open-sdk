"""
记忆推荐器测试

测试 MemoryRecommender、RecommendationContext、推荐算法等记忆推荐组件
"""

import pytest
import asyncio
import time
import math
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from typing import Any, Dict, List, Optional, Tuple

from anp_runtime.local_service.memory.memory_recommender import (
    MemoryRecommender,
    RecommendationContext,
    ScoringFunction,
    KeywordScoringFunction,
    TagScoringFunction,
    TimeScoringFunction,
    AccessFrequencyScoringFunction,
    AgentAffinityScoringFunction,
    SessionAffinityScoringFunction,
    MethodSimilarityScoringFunction,
    RecommendationAlgorithm,
    HybridRecommendationAlgorithm,
    KeywordRecommendationAlgorithm,
    get_memory_recommender,
    set_memory_recommender
)
from anp_runtime.local_service.memory.memory_manager import MemoryManager
from anp_runtime.local_service.memory.memory_models import (
    MemoryEntry,
    MemoryType,
    MemoryMetadata
)
from anp_runtime.local_service.memory.memory_config import (
    MemoryConfig,
    RecommendationConfig,
    PerformanceConfig
)
from anp_runtime.local_service.memory.context_session import ContextSessionManager


class TestRecommendationContext:
    """测试推荐上下文"""
    
    def test_context_initialization_basic(self):
        """测试基本初始化"""
        context = RecommendationContext()
        
        assert context.query_keywords == []
        assert context.query_tags == []
        assert context.current_agent_did is None
        assert context.current_session_id is None
        assert context.current_method_name is None
        assert context.context_data == {}
        assert context.time_range is None
        assert context.memory_types == []
        assert context.max_recommendations == 10
        assert context.similarity_threshold == 0.3
        assert context.include_similar_methods == True
        assert context.include_error_memories == False
        assert context.boost_recent_memories == True
    
    def test_context_initialization_with_params(self):
        """测试带参数的初始化"""
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        
        context = RecommendationContext(
            query_keywords=["search", "user"],
            query_tags=["important", "frequent"],
            current_agent_did="alice",
            current_session_id="session-123",
            current_method_name="search_users",
            context_data={"operation": "search", "filters": {"active": True}},
            time_range=(start_time, end_time),
            memory_types=[MemoryType.METHOD_CALL, MemoryType.USER_PREFERENCE]
        )
        
        assert context.query_keywords == ["search", "user"]
        assert context.query_tags == ["important", "frequent"]
        assert context.current_agent_did == "alice"
        assert context.current_session_id == "session-123"
        assert context.current_method_name == "search_users"
        assert context.context_data == {"operation": "search", "filters": {"active": True}}
        assert context.time_range == (start_time, end_time)
        assert context.memory_types == [MemoryType.METHOD_CALL, MemoryType.USER_PREFERENCE]
    
    def test_context_parameters_modification(self):
        """测试上下文参数修改"""
        context = RecommendationContext()
        
        # 修改推荐参数
        context.max_recommendations = 20
        context.similarity_threshold = 0.5
        context.include_similar_methods = False
        context.include_error_memories = True
        context.boost_recent_memories = False
        
        assert context.max_recommendations == 20
        assert context.similarity_threshold == 0.5
        assert context.include_similar_methods == False
        assert context.include_error_memories == True
        assert context.boost_recent_memories == False


class TestScoringFunctions:
    """测试评分函数"""
    
    @pytest.fixture
    def sample_memory(self):
        """创建示例记忆"""
        metadata = MemoryMetadata(
            source_agent_did="alice",
            source_agent_name="Alice",
            target_agent_did="bob",
            session_id="session-123",
            keywords=["search", "user", "database"],
            tags=["important", "frequent"],
            relevance_score=0.8,
            access_count=15
        )
        
        memory = MemoryEntry(
            id="mem-123",
            memory_type=MemoryType.METHOD_CALL,
            title="User Search",
            content={
                "method_name": "search_users",
                "input": {"query": "alice", "limit": 10},
                "output": {"users": [{"id": 1, "name": "Alice"}]}
            },
            metadata=metadata,
            created_at=datetime.now() - timedelta(days=1)
        )
        return memory
    
    @pytest.fixture
    def sample_context(self):
        """创建示例上下文"""
        return RecommendationContext(
            query_keywords=["search", "user"],
            query_tags=["important"],
            current_agent_did="alice",
            current_session_id="session-123",
            current_method_name="search_users"
        )
    
    def test_scoring_function_base_class(self):
        """测试评分函数基类"""
        scorer = ScoringFunction(weight=2.0)
        assert scorer.weight == 2.0
        
        # 基类的calculate_score应该抛出NotImplementedError
        with pytest.raises(NotImplementedError):
            scorer.calculate_score(Mock(), Mock())
    
    def test_keyword_scoring_function(self, sample_memory, sample_context):
        """测试关键词评分函数"""
        scorer = KeywordScoringFunction(weight=1.0)
        
        # 测试有匹配关键词的情况
        score = scorer.calculate_score(sample_memory, sample_context)
        
        # 计算预期分数：intersection=2(search,user), union=4(search,user,database)
        expected_score = 2 / 4  # Jaccard相似度
        assert abs(score - expected_score) < 0.001
        
        # 测试没有查询关键词的情况
        context_no_keywords = RecommendationContext()
        score = scorer.calculate_score(sample_memory, context_no_keywords)
        assert score == 0.0
        
        # 测试记忆没有关键词的情况
        memory_no_keywords = MemoryEntry(
            id="mem-456",
            memory_type=MemoryType.METHOD_CALL,
            title="Test",
            content={},
            metadata=MemoryMetadata(
                source_agent_did="alice",
                source_agent_name="Alice",
                keywords=[]
            )
        )
        score = scorer.calculate_score(memory_no_keywords, sample_context)
        assert score == 0.0
    
    def test_tag_scoring_function(self, sample_memory, sample_context):
        """测试标签评分函数"""
        scorer = TagScoringFunction(weight=1.0)
        
        # 测试有匹配标签的情况
        score = scorer.calculate_score(sample_memory, sample_context)
        
        # 计算预期分数：intersection=1(important), union=2(important,frequent)
        expected_score = 1 / 2
        assert abs(score - expected_score) < 0.001
        
        # 测试没有查询标签的情况
        context_no_tags = RecommendationContext()
        score = scorer.calculate_score(sample_memory, context_no_tags)
        assert score == 0.0
    
    def test_time_scoring_function(self, sample_memory):
        """测试时间评分函数"""
        scorer = TimeScoringFunction(weight=1.0, decay_days=30)
        context = RecommendationContext()
        
        # 测试1天前的记忆
        score = scorer.calculate_score(sample_memory, context)
        expected_score = math.exp(-1 / 30)  # 1天衰减
        assert abs(score - expected_score) < 0.001
        
        # 测试更老的记忆
        old_memory = MemoryEntry(
            id="mem-old",
            memory_type=MemoryType.METHOD_CALL,
            title="Old Memory",
            content={},
            metadata=MemoryMetadata(
                source_agent_did="alice",
                source_agent_name="Alice"
            ),
            created_at=datetime.now() - timedelta(days=30)
        )
        
        score = scorer.calculate_score(old_memory, context)
        expected_score = math.exp(-30 / 30)  # 30天衰减
        assert abs(score - expected_score) < 0.001
    
    def test_access_frequency_scoring_function(self, sample_memory):
        """测试访问频次评分函数"""
        scorer = AccessFrequencyScoringFunction(weight=1.0)
        context = RecommendationContext()
        
        # 测试有访问次数的记忆
        score = scorer.calculate_score(sample_memory, context)
        expected_score = math.log(15 + 1) / math.log(100)  # log归一化
        assert abs(score - expected_score) < 0.001
        
        # 测试没有访问次数的记忆
        no_access_memory = MemoryEntry(
            id="mem-no-access",
            memory_type=MemoryType.METHOD_CALL,
            title="No Access",
            content={},
            metadata=MemoryMetadata(
                source_agent_did="alice",
                source_agent_name="Alice",
                access_count=0
            )
        )
        
        score = scorer.calculate_score(no_access_memory, context)
        assert score == 0.0
    
    def test_agent_affinity_scoring_function(self, sample_memory, sample_context):
        """测试Agent亲和度评分函数"""
        scorer = AgentAffinityScoringFunction(weight=1.0)
        
        # 测试相同source agent
        score = scorer.calculate_score(sample_memory, sample_context)
        assert score == 1.0
        
        # 测试相同target agent
        context_target = RecommendationContext(current_agent_did="bob")
        score = scorer.calculate_score(sample_memory, context_target)
        assert score == 0.7
        
        # 测试不同agent
        context_different = RecommendationContext(current_agent_did="charlie")
        score = scorer.calculate_score(sample_memory, context_different)
        assert score == 0.0
        
        # 测试没有当前agent
        context_no_agent = RecommendationContext()
        score = scorer.calculate_score(sample_memory, context_no_agent)
        assert score == 0.0
    
    def test_session_affinity_scoring_function(self, sample_memory, sample_context):
        """测试会话亲和度评分函数"""
        scorer = SessionAffinityScoringFunction(weight=1.0)
        
        # 测试相同会话
        score = scorer.calculate_score(sample_memory, sample_context)
        assert score == 1.0
        
        # 测试不同会话
        context_different = RecommendationContext(current_session_id="session-456")
        score = scorer.calculate_score(sample_memory, context_different)
        assert score == 0.0
        
        # 测试没有会话信息
        context_no_session = RecommendationContext()
        score = scorer.calculate_score(sample_memory, context_no_session)
        assert score == 0.0
    
    def test_method_similarity_scoring_function(self, sample_context):
        """测试方法相似度评分函数"""
        scorer = MethodSimilarityScoringFunction(weight=1.0)
        
        # 创建方法调用记忆
        method_memory = MemoryEntry(
            id="mem-method",
            memory_type=MemoryType.METHOD_CALL,
            title="Method Call",
            content={"method_name": "search_users"},
            metadata=MemoryMetadata(
                source_agent_did="alice",
                source_agent_name="Alice"
            )
        )
        
        # 测试完全匹配
        score = scorer.calculate_score(method_memory, sample_context)
        assert score == 1.0
        
        # 测试部分匹配
        partial_memory = MemoryEntry(
            id="mem-partial",
            memory_type=MemoryType.METHOD_CALL,
            title="Partial Match",
            content={"method_name": "search_all_users"},
            metadata=MemoryMetadata(
                source_agent_did="alice",
                source_agent_name="Alice"
            )
        )
        score = scorer.calculate_score(partial_memory, sample_context)
        assert score == 0.7
        
        # 测试不匹配
        different_memory = MemoryEntry(
            id="mem-different",
            memory_type=MemoryType.METHOD_CALL,
            title="Different Method",
            content={"method_name": "create_order"},
            metadata=MemoryMetadata(
                source_agent_did="alice",
                source_agent_name="Alice"
            )
        )
        score = scorer.calculate_score(different_memory, sample_context)
        assert score == 0.0
        
        # 测试非方法调用记忆
        non_method_memory = MemoryEntry(
            id="mem-non-method",
            memory_type=MemoryType.USER_PREFERENCE,
            title="User Preference",
            content={},
            metadata=MemoryMetadata(
                source_agent_did="alice",
                source_agent_name="Alice"
            )
        )
        score = scorer.calculate_score(non_method_memory, sample_context)
        assert score == 0.0


class TestRecommendationAlgorithms:
    """测试推荐算法"""
    
    @pytest.fixture
    def memory_manager(self):
        """创建模拟记忆管理器"""
        manager = Mock(spec=MemoryManager)
        return manager
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MemoryConfig(
            recommendation=RecommendationConfig(
                keyword_weight=1.0,
                tag_weight=0.8,
                time_weight=0.6,
                access_weight=0.4
            )
        )
    
    @pytest.fixture
    def sample_memories(self):
        """创建示例记忆列表"""
        memories = []
        
        # 记忆1：高相关度
        metadata1 = MemoryMetadata(
            source_agent_did="alice",
            source_agent_name="Alice",
            keywords=["search", "user", "database"],
            tags=["important"],
            relevance_score=0.9,
            access_count=20
        )
        memory1 = MemoryEntry(
            id="mem-1",
            memory_type=MemoryType.METHOD_CALL,
            title="User Search",
            content={"method_name": "search_users"},
            metadata=metadata1,
            created_at=datetime.now() - timedelta(hours=1)
        )
        memories.append(memory1)
        
        # 记忆2：中等相关度
        metadata2 = MemoryMetadata(
            source_agent_did="bob",
            source_agent_name="Bob",
            keywords=["user", "profile"],
            tags=["normal"],
            relevance_score=0.6,
            access_count=5
        )
        memory2 = MemoryEntry(
            id="mem-2",
            memory_type=MemoryType.USER_PREFERENCE,
            title="User Preference",
            content={},
            metadata=metadata2,
            created_at=datetime.now() - timedelta(days=1)
        )
        memories.append(memory2)
        
        # 记忆3：低相关度
        metadata3 = MemoryMetadata(
            source_agent_did="charlie",
            source_agent_name="Charlie",
            keywords=["order", "payment"],
            tags=["system"],
            relevance_score=0.3,
            access_count=1
        )
        memory3 = MemoryEntry(
            id="mem-3",
            memory_type=MemoryType.METHOD_CALL,
            title="Payment Processing",
            content={"method_name": "process_payment"},
            metadata=metadata3,
            created_at=datetime.now() - timedelta(days=7)
        )
        memories.append(memory3)
        
        return memories
    
    def test_recommendation_algorithm_base_class(self, config):
        """测试推荐算法基类"""
        algorithm = RecommendationAlgorithm(config)
        assert algorithm.config == config
        assert algorithm.scoring_functions == []
        
        # 添加评分函数
        scorer = KeywordScoringFunction(weight=2.0)
        algorithm.add_scoring_function(scorer)
        assert len(algorithm.scoring_functions) == 1
        assert algorithm.scoring_functions[0] == scorer
        
        # 基类的recommend方法应该抛出NotImplementedError
        with pytest.raises(NotImplementedError):
            asyncio.run(algorithm.recommend(Mock(), Mock()))
    
    @pytest.mark.asyncio
    async def test_hybrid_recommendation_algorithm(self, memory_manager, config, sample_memories):
        """测试混合推荐算法"""
        algorithm = HybridRecommendationAlgorithm(config)
        
        # 验证评分函数被正确添加
        assert len(algorithm.scoring_functions) > 0
        
        # 设置模拟返回
        memory_manager.search_memories = AsyncMock(return_value=sample_memories)
        
        # 创建推荐上下文
        context = RecommendationContext(
            query_keywords=["search", "user"],
            query_tags=["important"],
            current_agent_did="alice"
        )
        context.max_recommendations = 5
        context.similarity_threshold = 0.1  # 低阈值以包含更多结果
        
        # 执行推荐
        recommendations = await algorithm.recommend(memory_manager, context)
        
        # 验证结果
        assert isinstance(recommendations, list)
        assert len(recommendations) <= context.max_recommendations
        
        # 验证结果格式
        for memory, score in recommendations:
            assert isinstance(memory, MemoryEntry)
            assert isinstance(score, float)
            assert score >= 0.0
        
        # 验证结果按分数降序排列
        scores = [score for _, score in recommendations]
        assert scores == sorted(scores, reverse=True)
        
        # 验证搜索被调用
        memory_manager.search_memories.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_hybrid_algorithm_with_memory_types(self, memory_manager, config, sample_memories):
        """测试指定记忆类型的混合推荐"""
        algorithm = HybridRecommendationAlgorithm(config)
        memory_manager.search_memories = AsyncMock(return_value=sample_memories)
        
        context = RecommendationContext(
            query_keywords=["search"],
            memory_types=[MemoryType.METHOD_CALL, MemoryType.USER_PREFERENCE]
        )
        context.max_recommendations = 10
        
        await algorithm.recommend(memory_manager, context)
        
        # 验证为每种记忆类型都调用了搜索
        assert memory_manager.search_memories.call_count == len(context.memory_types)
    
    @pytest.mark.asyncio
    async def test_hybrid_algorithm_with_time_range(self, memory_manager, config, sample_memories):
        """测试带时间范围的混合推荐"""
        algorithm = HybridRecommendationAlgorithm(config)
        memory_manager.search_memories = AsyncMock(return_value=sample_memories)
        
        # 设置时间范围，只包含最近的记忆
        start_time = datetime.now() - timedelta(hours=2)
        end_time = datetime.now()
        
        context = RecommendationContext(
            query_keywords=["search"],
            time_range=(start_time, end_time)
        )
        context.max_recommendations = 10
        
        recommendations = await algorithm.recommend(memory_manager, context)
        
        # 验证只有符合时间范围的记忆被包含
        for memory, _ in recommendations:
            assert start_time <= memory.created_at <= end_time
    
    @pytest.mark.asyncio
    async def test_hybrid_algorithm_exclude_errors(self, memory_manager, config):
        """测试排除错误记忆"""
        algorithm = HybridRecommendationAlgorithm(config)
        
        # 创建包含错误记忆的列表
        memories_with_error = [
            MemoryEntry(
                id="mem-normal",
                memory_type=MemoryType.METHOD_CALL,
                title="Normal Memory",
                content={},
                metadata=MemoryMetadata(
                    source_agent_did="alice",
                    source_agent_name="Alice",
                    keywords=["test"],
                    relevance_score=0.8
                )
            ),
            MemoryEntry(
                id="mem-error",
                memory_type=MemoryType.ERROR,
                title="Error Memory",
                content={},
                metadata=MemoryMetadata(
                    source_agent_did="alice",
                    source_agent_name="Alice",
                    keywords=["test"],
                    relevance_score=0.8
                )
            )
        ]
        
        memory_manager.search_memories = AsyncMock(return_value=memories_with_error)
        
        context = RecommendationContext(
            query_keywords=["test"]
        )
        context.include_error_memories = False  # 排除错误记忆
        context.similarity_threshold = 0.0
        
        recommendations = await algorithm.recommend(memory_manager, context)
        
        # 验证错误记忆被排除
        for memory, _ in recommendations:
            assert memory.memory_type != MemoryType.ERROR
    
    @pytest.mark.asyncio
    async def test_keyword_recommendation_algorithm(self, memory_manager, config, sample_memories):
        """测试关键词推荐算法"""
        algorithm = KeywordRecommendationAlgorithm(config)
        memory_manager.search_memories = AsyncMock(return_value=sample_memories)
        
        context = RecommendationContext(
            query_keywords=["search", "user"]
        )
        context.max_recommendations = 5
        context.similarity_threshold = 0.1
        
        recommendations = await algorithm.recommend(memory_manager, context)
        
        # 验证结果
        assert isinstance(recommendations, list)
        assert len(recommendations) <= context.max_recommendations
        
        # 验证搜索参数
        memory_manager.search_memories.assert_called_once_with(
            keywords=context.query_keywords,
            limit=context.max_recommendations * 2,
            offset=0
        )
    
    @pytest.mark.asyncio
    async def test_keyword_algorithm_no_keywords(self, memory_manager, config):
        """测试没有关键词的关键词推荐算法"""
        algorithm = KeywordRecommendationAlgorithm(config)
        
        context = RecommendationContext()  # 没有关键词
        
        recommendations = await algorithm.recommend(memory_manager, context)
        
        # 应该返回空列表
        assert recommendations == []
        
        # 不应该调用搜索
        memory_manager.search_memories.assert_not_called()


class TestMemoryRecommender:
    """测试记忆推荐器主类"""
    
    @pytest.fixture
    def memory_manager(self):
        """创建模拟记忆管理器"""
        manager = Mock(spec=MemoryManager)
        return manager
    
    @pytest.fixture
    def session_manager(self):
        """创建模拟会话管理器"""
        manager = Mock(spec=ContextSessionManager)
        return manager
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return MemoryConfig(
            recommendation=RecommendationConfig(
                keyword_weight=1.0,
                tag_weight=0.8,
                time_weight=0.6,
                access_weight=0.4
            ),
            performance=PerformanceConfig(
                enable_search_cache=True,
                search_cache_size=100
            )
        )
    
    @pytest.fixture
    def memory_recommender(self, memory_manager, session_manager, config):
        """创建记忆推荐器"""
        return MemoryRecommender(memory_manager, session_manager, config)
    
    def test_memory_recommender_initialization(self, memory_recommender, memory_manager, config):
        """测试记忆推荐器初始化"""
        assert memory_recommender.memory_manager == memory_manager
        assert memory_recommender.config == config
        
        # 验证算法被正确初始化
        assert 'hybrid' in memory_recommender.algorithms
        assert 'keyword' in memory_recommender.algorithms
        assert 'similarity' in memory_recommender.algorithms
        
        # 验证统计信息初始化
        assert memory_recommender._stats['recommendations_generated'] == 0
        assert memory_recommender._stats['cache_hits'] == 0
        assert memory_recommender._stats['cache_misses'] == 0
    
    @pytest.mark.asyncio
    async def test_recommend_memories_basic(self, memory_recommender):
        """测试基本推荐功能"""
        # 模拟推荐结果
        mock_memories = [
            (Mock(spec=MemoryEntry), 0.8),
            (Mock(spec=MemoryEntry), 0.6)
        ]
        
        with patch.object(memory_recommender.algorithms['hybrid'], 'recommend', new_callable=AsyncMock) as mock_recommend:
            mock_recommend.return_value = mock_memories
            
            context = RecommendationContext(query_keywords=["test"])
            recommendations = await memory_recommender.recommend_memories(context)
            
            assert recommendations == mock_memories
            mock_recommend.assert_called_once_with(memory_recommender.memory_manager, context)
            
            # 验证统计信息更新
            assert memory_recommender._stats['recommendations_generated'] == 1
    
    @pytest.mark.asyncio
    async def test_recommend_memories_with_cache(self, memory_recommender):
        """测试带缓存的推荐"""
        mock_memories = [(Mock(spec=MemoryEntry), 0.8)]
        
        with patch.object(memory_recommender.algorithms['hybrid'], 'recommend', new_callable=AsyncMock) as mock_recommend:
            mock_recommend.return_value = mock_memories
            
            context = RecommendationContext(query_keywords=["test"])
            
            # 第一次调用
            recommendations1 = await memory_recommender.recommend_memories(context, use_cache=True)
            assert recommendations1 == mock_memories
            assert memory_recommender._stats['cache_misses'] == 1
            
            # 第二次调用应该使用缓存
            recommendations2 = await memory_recommender.recommend_memories(context, use_cache=True)
            assert recommendations2 == mock_memories
            assert memory_recommender._stats['cache_hits'] == 1
            
            # 算法只被调用一次
            mock_recommend.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_recommend_memories_algorithm_fallback(self, memory_recommender):
        """测试算法回退机制"""
        mock_memories = [(Mock(spec=MemoryEntry), 0.7)]
        
        with patch.object(memory_recommender.algorithms['hybrid'], 'recommend', new_callable=AsyncMock) as mock_recommend:
            mock_recommend.return_value = mock_memories
            
            context = RecommendationContext(query_keywords=["test"])
            
            # 使用不存在的算法，应该回退到hybrid
            recommendations = await memory_recommender.recommend_memories(
                context, algorithm='non_existent'
            )
            
            assert recommendations == mock_memories
            mock_recommend.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_recommend_for_method_call(self, memory_recommender):
        """测试为方法调用推荐"""
        mock_memories = [(Mock(spec=MemoryEntry), 0.9)]
        
        with patch.object(memory_recommender, 'recommend_memories', new_callable=AsyncMock) as mock_recommend:
            mock_recommend.return_value = mock_memories
            
            recommendations = await memory_recommender.recommend_for_method_call(
                method_name="search_users",
                method_key="user::search_users",
                agent_did="alice",
                session_id="session-123",
                max_recommendations=5
            )
            
            assert recommendations == mock_memories
            
            # 验证推荐上下文
            mock_recommend.assert_called_once()
            call_args = mock_recommend.call_args[0][0]  # 获取context参数
            assert isinstance(call_args, RecommendationContext)
            assert "search_users" in call_args.query_keywords
            assert call_args.current_agent_did == "alice"
            assert call_args.current_session_id == "session-123"
            assert call_args.current_method_name == "search_users"
            assert call_args.max_recommendations == 5
            assert call_args.include_error_memories == True
            assert MemoryType.METHOD_CALL in call_args.memory_types
    
    @pytest.mark.asyncio
    async def test_recommend_for_context(self, memory_recommender):
        """测试为上下文推荐"""
        mock_memories = [(Mock(spec=MemoryEntry), 0.7)]
        
        with patch.object(memory_recommender, 'recommend_memories', new_callable=AsyncMock) as mock_recommend:
            mock_recommend.return_value = mock_memories
            
            recommendations = await memory_recommender.recommend_for_context(
                keywords=["search", "user"],
                tags=["important"],
                agent_did="alice",
                session_id="session-123",
                max_recommendations=10
            )
            
            assert recommendations == mock_memories
            
            # 验证推荐上下文
            call_args = mock_recommend.call_args[0][0]
            assert call_args.query_keywords == ["search", "user"]
            assert call_args.query_tags == ["important"]
            assert call_args.current_agent_did == "alice"
            assert call_args.current_session_id == "session-123"
            assert call_args.max_recommendations == 10
    
    @pytest.mark.asyncio
    async def test_recommend_similar_memories(self, memory_recommender):
        """测试推荐相似记忆"""
        # 创建参考记忆
        reference_memory = MemoryEntry(
            id="ref-mem",
            memory_type=MemoryType.METHOD_CALL,
            title="Reference",
            content={},
            metadata=MemoryMetadata(
                source_agent_did="alice",
                source_agent_name="Alice",
                session_id="session-123",
                keywords=["search", "user"],
                tags=["important"]
            )
        )
        
        # 模拟推荐结果（包含参考记忆本身）
        mock_memories = [
            (reference_memory, 1.0),  # 参考记忆本身
            (Mock(spec=MemoryEntry), 0.8),
            (Mock(spec=MemoryEntry), 0.6)
        ]
        mock_memories[1][0].id = "similar-1"
        mock_memories[2][0].id = "similar-2"
        
        with patch.object(memory_recommender, 'recommend_memories', new_callable=AsyncMock) as mock_recommend:
            mock_recommend.return_value = mock_memories
            
            recommendations = await memory_recommender.recommend_similar_memories(
                reference_memory, max_recommendations=5
            )
            
            # 验证参考记忆被移除
            assert len(recommendations) == 2
            assert all(memory.id != reference_memory.id for memory, _ in recommendations)
            
            # 验证推荐上下文
            call_args = mock_recommend.call_args[0][0]
            assert call_args.query_keywords == reference_memory.metadata.keywords
            assert call_args.query_tags == reference_memory.metadata.tags
            assert call_args.current_agent_did == reference_memory.metadata.source_agent_did
            assert call_args.current_session_id == reference_memory.metadata.session_id
            assert reference_memory.memory_type in call_args.memory_types
    
    def test_generate_cache_key(self, memory_recommender):
        """测试缓存键生成"""
        context = RecommendationContext(
            query_keywords=["search", "user"],
            query_tags=["important"],
            current_agent_did="alice",
            current_session_id="session-123",
            current_method_name="search_users",
            memory_types=[MemoryType.METHOD_CALL]
        )
        context.max_recommendations = 10
        context.similarity_threshold = 0.3
        
        key1 = memory_recommender._generate_cache_key(context, 'hybrid')
        key2 = memory_recommender._generate_cache_key(context, 'hybrid')
        
        # 相同上下文应该生成相同键
        assert key1 == key2
        
        # 不同算法应该生成不同键
        key3 = memory_recommender._generate_cache_key(context, 'keyword')
        assert key1 != key3
        
        # 不同上下文应该生成不同键
        context2 = RecommendationContext(query_keywords=["different"])
        key4 = memory_recommender._generate_cache_key(context2, 'hybrid')
        assert key1 != key4
    
    def test_cache_operations(self, memory_recommender):
        """测试缓存操作"""
        mock_memories = [(Mock(spec=MemoryEntry), 0.8)]
        cache_key = "test_key"
        
        # 测试缓存存储
        memory_recommender._cache_recommendation(cache_key, mock_memories)
        
        # 测试缓存获取
        cached_result = memory_recommender._get_cached_recommendation(cache_key)
        assert cached_result == mock_memories
        
        # 测试缓存过期
        with patch('anp_runtime.local_service.memory.memory_recommender.datetime') as mock_datetime:
            # 设置当前时间比缓存时间晚15分钟
            mock_datetime.now.return_value = datetime.now() + timedelta(minutes=15)
            
            expired_result = memory_recommender._get_cached_recommendation(cache_key)
            assert expired_result is None
    
    def test_cache_size_limit(self, memory_recommender):
        """测试缓存大小限制"""
        # 设置小的缓存大小
        memory_recommender.config.performance.search_cache_size = 2
        
        mock_memories = [(Mock(spec=MemoryEntry), 0.8)]
        
        # 添加超过限制的缓存项
        memory_recommender._cache_recommendation("key1", mock_memories)
        memory_recommender._cache_recommendation("key2", mock_memories)
        memory_recommender._cache_recommendation("key3", mock_memories)  # 应该触发清理
        
        # 验证缓存大小不超过限制
        assert len(memory_recommender._recommendation_cache) <= 2
    
    def test_get_recommendation_statistics(self, memory_recommender):
        """测试获取推荐统计信息"""
        # 设置一些统计数据
        memory_recommender._stats['recommendations_generated'] = 10
        memory_recommender._stats['cache_hits'] = 3
        memory_recommender._stats['cache_misses'] = 7
        memory_recommender._stats['avg_recommendation_score'] = 0.75
        
        # 添加一些缓存
        memory_recommender._recommendation_cache['test1'] = ([], datetime.now())
        memory_recommender._recommendation_cache['test2'] = ([], datetime.now())
        
        stats = memory_recommender.get_recommendation_statistics()
        
        assert stats['recommendations_generated'] == 10
        assert stats['cache_hits'] == 3
        assert stats['cache_misses'] == 7
        assert stats['avg_recommendation_score'] == 0.75
        assert stats['algorithms_available'] == ['hybrid', 'keyword', 'similarity']
        assert stats['cache_size'] == 2
        assert abs(stats['cache_hit_ratio'] - 0.3) < 0.001  # 3/(3+7)
    
    def test_clear_cache(self, memory_recommender):
        """测试清空缓存"""
        # 添加一些缓存项
        memory_recommender._recommendation_cache['test1'] = ([], datetime.now())
        memory_recommender._recommendation_cache['test2'] = ([], datetime.now())
        
        assert len(memory_recommender._recommendation_cache) == 2
        
        # 清空缓存
        memory_recommender.clear_cache()
        
        assert len(memory_recommender._recommendation_cache) == 0


class TestMemoryRecommenderGlobal:
    """测试全局记忆推荐器"""
    
    def test_get_memory_recommender_singleton(self):
        """测试获取全局记忆推荐器单例"""
        # 清除全局实例
        with patch('anp_runtime.local_service.memory.memory_recommender._global_memory_recommender', None):
            # 第一次获取应该创建新实例
            recommender1 = get_memory_recommender()
            assert isinstance(recommender1, MemoryRecommender)
            
            # 第二次获取应该返回同一实例
            recommender2 = get_memory_recommender()
            assert recommender1 is recommender2
    
    def test_set_memory_recommender(self):
        """测试设置全局记忆推荐器"""
        # 创建自定义推荐器
        custom_recommender = Mock(spec=MemoryRecommender)
        
        # 设置全局推荐器
        set_memory_recommender(custom_recommender)
        
        # 验证获取的是设置的推荐器
        retrieved_recommender = get_memory_recommender()
        assert retrieved_recommender is custom_recommender


class TestMemoryRecommenderIntegration:
    """测试记忆推荐器集成场景"""
    
    @pytest.mark.asyncio
    async def test_full_recommendation_workflow(self):
        """测试完整的推荐工作流程"""
        from anp_runtime.local_service.memory.memory_storage import InMemoryStorage
        from anp_runtime.local_service.memory.memory_manager import MemoryManager
        
        # 创建真实的组件
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage)
        config = MemoryConfig(
            recommendation=RecommendationConfig(
                keyword_weight=1.0,
                tag_weight=0.8,
                time_weight=0.6,
                access_weight=0.4
            ),
            performance=PerformanceConfig(
                enable_search_cache=True,
                search_cache_size=50
            )
        )
        
        recommender = MemoryRecommender(memory_manager, None, config)
        
        # 1. 创建一些测试记忆
        memories_to_create = [
            {
                "memory_type": MemoryType.METHOD_CALL,
                "title": "Search Users",
                "content": {"method_name": "search_users", "query": "alice"},
                "keywords": ["search", "user", "alice"],
                "tags": ["important", "frequent"],
                "agent_did": "alice",
                "session_id": "session-1"
            },
            {
                "memory_type": MemoryType.USER_PREFERENCE,
                "title": "User Preference",
                "content": {"theme": "dark", "language": "en"},
                "keywords": ["user", "preference", "settings"],
                "tags": ["user", "config"],
                "agent_did": "alice",
                "session_id": "session-1"
            },
            {
                "memory_type": MemoryType.METHOD_CALL,
                "title": "Create Order",
                "content": {"method_name": "create_order", "amount": 100},
                "keywords": ["order", "create", "payment"],
                "tags": ["business", "transaction"],
                "agent_did": "bob",
                "session_id": "session-2"
            }
        ]
        
        created_memories = []
        for mem_data in memories_to_create:
            memory = await memory_manager.create_memory(
                memory_type=mem_data["memory_type"],
                title=mem_data["title"],
                content=mem_data["content"],
                source_agent_did=mem_data["agent_did"],
                source_agent_name=mem_data["agent_did"].capitalize(),
                keywords=mem_data["keywords"],
                tags=mem_data["tags"],
                session_id=mem_data["session_id"]
            )
            created_memories.append(memory)
        
        # 2. 测试基于关键词的推荐
        context = RecommendationContext(
            query_keywords=["search", "user"]
        )
        context.max_recommendations = 5
        context.similarity_threshold = 0.1
        
        recommendations = await recommender.recommend_memories(context)
        
        # 验证推荐结果
        assert len(recommendations) > 0
        assert all(isinstance(memory, MemoryEntry) for memory, _ in recommendations)
        assert all(isinstance(score, float) for _, score in recommendations)
        
        # 验证结果按分数排序
        scores = [score for _, score in recommendations]
        assert scores == sorted(scores, reverse=True)
        
        # 3. 测试方法调用推荐
        method_recommendations = await recommender.recommend_for_method_call(
            method_name="search_users",
            method_key="user::search_users",
            agent_did="alice",
            max_recommendations=3
        )
        
        assert len(method_recommendations) > 0
        
        # 4. 测试相似记忆推荐
        reference_memory = created_memories[0]  # 使用第一个记忆作为参考
        similar_recommendations = await recommender.recommend_similar_memories(
            reference_memory, max_recommendations=3
        )
        
        # 验证参考记忆本身不在结果中
        similar_ids = [memory.id for memory, _ in similar_recommendations]
        assert reference_memory.id not in similar_ids
        
        # 5. 验证缓存功能
        stats_before = recommender.get_recommendation_statistics()
        
        # 重复相同的推荐请求
        cached_recommendations = await recommender.recommend_memories(context)
        
        stats_after = recommender.get_recommendation_statistics()
        
        # 验证缓存命中
        assert stats_after['cache_hits'] > stats_before['cache_hits']
        assert cached_recommendations == recommendations
        
        # 6. 测试统计信息
        final_stats = recommender.get_recommendation_statistics()
        assert final_stats['recommendations_generated'] > 0
        assert final_stats['cache_size'] > 0
        assert 'cache_hit_ratio' in final_stats
        
        await memory_manager.close()
    
    @pytest.mark.asyncio
    async def test_recommendation_performance(self):
        """测试推荐性能"""
        from anp_runtime.local_service.memory.memory_storage import InMemoryStorage
        from anp_runtime.local_service.memory.memory_manager import MemoryManager
        
        storage = InMemoryStorage()
        memory_manager = MemoryManager(storage=storage)
        recommender = MemoryRecommender(memory_manager)
        
        # 创建大量测试记忆
        start_time = time.time()
        
        for i in range(50):
            await memory_manager.create_memory(
                memory_type=MemoryType.METHOD_CALL,
                title=f"Test Memory {i}",
                content={"method_name": f"test_method_{i}", "param": i},
                source_agent_did="test_agent",
                source_agent_name="Test Agent",
                keywords=[f"keyword_{i}", "test", "method"],
                tags=[f"tag_{i}", "test"]
            )
        
        creation_time = time.time() - start_time
        
        # 测试推荐性能
        context = RecommendationContext(
            query_keywords=["test", "method"]
        )
        context.max_recommendations = 10
        context.similarity_threshold = 0.1
        
        recommendation_start = time.time()
        recommendations = await recommender.recommend_memories(context)
        recommendation_time = time.time() - recommendation_start
        
        # 验证性能合理（应该在合理时间内完成）
        assert creation_time < 5.0  # 创建50个记忆应该在5秒内完成
        assert recommendation_time < 1.0  # 推荐应该在1秒内完成
        assert len(recommendations) <= context.max_recommendations
        
        # 测试缓存性能
        cached_start = time.time()
        cached_recommendations = await recommender.recommend_memories(context)
        cached_time = time.time() - cached_start
        
        # 缓存的推荐应该更快
        assert cached_time < recommendation_time
        assert cached_recommendations == recommendations
        
        await memory_manager.close()


if __name__ == "__main__":
    pytest.main([__file__])