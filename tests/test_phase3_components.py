# -*- coding: utf-8 -*-
"""
Phase 3 组件单元测试

测试覆盖：
- VectorStoreBackend: 向量存储后端包装器
- MemoryLifecycle: 记忆生命周期管理器
- AgenticRetriever: ReAct 模式智能检索器
"""

import asyncio
import os
import pytest
import tempfile
import sys
import importlib.util
import time
from pathlib import Path
from datetime import datetime, timedelta

# 直接导入模块文件，绕过包初始化
test_dir = Path(__file__).parent.parent

def load_module(name, path):
    """动态加载模块"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# 加载 Phase 3 组件
vector_store_module = load_module("vector_store_backend", test_dir / "search" / "vector_store_backend.py")
VectorStoreBackend = vector_store_module.VectorStoreBackend
VectorBackendType = vector_store_module.VectorBackendType
VectorRecord = vector_store_module.VectorRecord
SearchResult = vector_store_module.SearchResult

lifecycle_module = load_module("memory_lifecycle", test_dir / "core" / "memory_lifecycle.py")
MemoryLifecycle = lifecycle_module.MemoryLifecycle
MemoryState = lifecycle_module.MemoryState
LifecycleConfig = lifecycle_module.LifecycleConfig
MemoryLifecycleRecord = lifecycle_module.MemoryLifecycleRecord

agentic_module = load_module("agentic_retriever", test_dir / "search" / "agentic_retriever.py")
AgenticRetriever = agentic_module.AgenticRetriever
RetrievalStrategy = agentic_module.RetrievalStrategy
RetrievalAction = agentic_module.RetrievalAction
RetrievalResult = agentic_module.RetrievalResult


# ============================================================
# VectorStoreBackend 测试
# ============================================================

class TestVectorStoreBackendInit:
    """测试 VectorStoreBackend 初始化"""

    def test_default_init(self):
        """默认初始化（内存模式）"""
        backend = VectorStoreBackend()
        assert backend.backend_type == VectorBackendType.IN_MEMORY
        assert backend.collection_name == "memory_vectors"
        assert backend.embedding_dim == 1536
        assert backend.hybrid_search is True
        assert backend._initialized is True

    def test_custom_init(self):
        """自定义参数初始化"""
        backend = VectorStoreBackend(
            backend_type=VectorBackendType.IN_MEMORY,
            collection_name="test_collection",
            embedding_dim=768,
            hybrid_search=False,
            keyword_weight=0.4,
            vector_weight=0.6
        )
        assert backend.collection_name == "test_collection"
        assert backend.embedding_dim == 768
        assert backend.hybrid_search is False
        assert backend.keyword_weight == 0.4
        assert backend.vector_weight == 0.6

    def test_backend_type_enum(self):
        """测试后端类型枚举"""
        assert VectorBackendType.IN_MEMORY.value == "in_memory"
        assert VectorBackendType.CHROMA.value == "chroma"
        assert VectorBackendType.QDRANT.value == "qdrant"
        assert VectorBackendType.PGVECTOR.value == "pgvector"


class TestVectorStoreBackendAddVectors:
    """测试向量添加功能"""

    @pytest.fixture
    def backend(self):
        return VectorStoreBackend()

    @pytest.mark.asyncio
    async def test_add_single_vector(self, backend):
        """添加单个向量"""
        vectors = [VectorRecord(
            id="vec_1",
            vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={"type": "memory", "agent_id": "agent_1"},
            document="测试记忆内容"
        )]
        count = await backend.add_vectors(vectors)
        assert count == 1

    @pytest.mark.asyncio
    async def test_add_multiple_vectors(self, backend):
        """批量添加向量"""
        vectors = [
            VectorRecord(id=f"vec_{i}", vector=[0.1 * i, 0.2 * i, 0.3 * i], metadata={"index": i})
            for i in range(10)
        ]
        count = await backend.add_vectors(vectors)
        assert count == 10

    @pytest.mark.asyncio
    async def test_add_vectors_overwrite(self, backend):
        """添加相同 ID 的向量应覆盖"""
        vectors1 = [VectorRecord(id="vec_1", vector=[0.1, 0.2, 0.3], document="原始内容")]
        await backend.add_vectors(vectors1)

        vectors2 = [VectorRecord(id="vec_1", vector=[0.4, 0.5, 0.6], document="更新内容")]
        await backend.add_vectors(vectors2)

        count = await backend.get_vector_count()
        assert count == 1


class TestVectorStoreBackendSearch:
    """测试向量搜索功能"""

    @pytest.fixture
    def backend(self):
        backend = VectorStoreBackend()
        return backend

    @pytest.mark.asyncio
    async def test_search_basic(self, backend):
        """基本向量搜索"""
        vectors = [
            VectorRecord(id="vec_1", vector=[1.0, 0.0, 0.0], document="文档1"),
            VectorRecord(id="vec_2", vector=[0.0, 1.0, 0.0], document="文档2"),
            VectorRecord(id="vec_3", vector=[0.0, 0.0, 1.0], document="文档3"),
        ]
        await backend.add_vectors(vectors)

        results = await backend.search(query_vector=[1.0, 0.0, 0.0], top_k=1)
        assert len(results) == 1
        assert results[0].id == "vec_1"

    @pytest.mark.asyncio
    async def test_search_top_k(self, backend):
        """测试 top_k 限制"""
        vectors = [
            VectorRecord(id=f"vec_{i}", vector=[1.0 / (i + 1), 0.0, 0.0])
            for i in range(10)
        ]
        await backend.add_vectors(vectors)

        results = await backend.search(query_vector=[1.0, 0.0, 0.0], top_k=3)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_with_text(self, backend):
        """测试混合搜索（向量+文本）"""
        vectors = [
            VectorRecord(id="vec_1", vector=[1.0, 0.0, 0.0], document="Python 编程语言"),
            VectorRecord(id="vec_2", vector=[0.9, 0.1, 0.0], document="Java 编程语言"),
        ]
        await backend.add_vectors(vectors)

        results = await backend.search(
            query_vector=[1.0, 0.0, 0.0],
            query_text="Python",
            top_k=2
        )
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_with_metadata_filter(self, backend):
        """测试元数据过滤搜索"""
        vectors = [
            VectorRecord(id="vec_1", vector=[1.0, 0.0, 0.0], metadata={"type": "personal"}),
            VectorRecord(id="vec_2", vector=[0.9, 0.1, 0.0], metadata={"type": "task"}),
        ]
        await backend.add_vectors(vectors)

        results = await backend.search(
            query_vector=[1.0, 0.0, 0.0],
            top_k=5,
            filter_metadata={"type": "personal"}
        )
        assert all(r.metadata.get("type") == "personal" for r in results)

    @pytest.mark.asyncio
    async def test_search_empty_db(self, backend):
        """测试空数据库搜索"""
        results = await backend.search(query_vector=[1.0, 0.0, 0.0], top_k=5)
        assert len(results) == 0


class TestVectorStoreBackendDelete:
    """测试向量删除功能"""

    @pytest.fixture
    def backend(self):
        backend = VectorStoreBackend()
        return backend

    @pytest.mark.asyncio
    async def test_delete_vectors(self, backend):
        """删除向量"""
        vectors = [
            VectorRecord(id="vec_1", vector=[1.0, 0.0, 0.0]),
            VectorRecord(id="vec_2", vector=[0.0, 1.0, 0.0]),
        ]
        await backend.add_vectors(vectors)

        deleted = await backend.delete_vectors(["vec_1"])
        assert deleted == 1

        count = await backend.get_vector_count()
        assert count == 1

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, backend):
        """删除不存在的向量"""
        deleted = await backend.delete_vectors(["nonexistent"])
        assert deleted == 0

    @pytest.mark.asyncio
    async def test_clear_all(self, backend):
        """清空所有向量"""
        vectors = [
            VectorRecord(id=f"vec_{i}", vector=[0.1 * i, 0.2 * i, 0.3 * i])
            for i in range(5)
        ]
        await backend.add_vectors(vectors)

        await backend.clear()
        count = await backend.get_vector_count()
        assert count == 0


class TestVectorStoreBackendStats:
    """测试统计功能"""

    @pytest.fixture
    def backend(self):
        return VectorStoreBackend()

    @pytest.mark.asyncio
    async def test_get_vector_count(self, backend):
        """获取向量数量"""
        vectors = [VectorRecord(id=f"vec_{i}", vector=[0.1 * i, 0.2 * i, 0.3 * i]) for i in range(5)]
        await backend.add_vectors(vectors)

        count = await backend.get_vector_count()
        assert count == 5

    @pytest.mark.asyncio
    async def test_get_stats(self, backend):
        """获取后端统计"""
        vectors = [VectorRecord(id=f"vec_{i}", vector=[0.1 * i, 0.2 * i, 0.3 * i]) for i in range(3)]
        await backend.add_vectors(vectors)

        stats = backend.get_stats()
        assert stats["backend_type"] == "in_memory"
        assert stats["vector_count"] == 3
        assert stats["initialized"] is True


class TestVectorStoreBackendDataStructures:
    """测试数据结构"""

    def test_vector_record(self):
        """测试 VectorRecord 数据结构"""
        record = VectorRecord(
            id="test_id",
            vector=[0.1, 0.2, 0.3],
            metadata={"key": "value"},
            document="test document"
        )
        assert record.id == "test_id"
        assert record.vector == [0.1, 0.2, 0.3]
        assert record.metadata == {"key": "value"}
        assert record.document == "test document"

    def test_search_result(self):
        """测试 SearchResult 数据结构"""
        result = SearchResult(
            id="test_id",
            score=0.95,
            metadata={"key": "value"},
            document="test document"
        )
        assert result.id == "test_id"
        assert result.score == 0.95
        assert result.metadata == {"key": "value"}
        assert result.document == "test document"


# ============================================================
# MemoryLifecycle 测试
# ============================================================

class TestMemoryLifecycleInit:
    """测试 MemoryLifecycle 初始化"""

    def test_default_init(self):
        """默认初始化"""
        lifecycle = MemoryLifecycle()
        assert lifecycle.config.active_to_cooling_days == 7.0
        assert lifecycle.config.cooling_to_archived_days == 30.0
        assert lifecycle.config.archived_to_deleted_days == 365.0

    def test_custom_config(self):
        """自定义配置初始化"""
        config = LifecycleConfig(
            active_to_cooling_days=1.0,
            cooling_to_archived_days=3.0,
            archived_to_deleted_days=30.0
        )
        lifecycle = MemoryLifecycle(config=config)
        assert lifecycle.config.active_to_cooling_days == 1.0


class TestMemoryLifecycleRegister:
    """测试记忆注册"""

    def test_register_memory(self):
        """注册新记忆"""
        lifecycle = MemoryLifecycle()
        record = lifecycle.register_memory(memory_id=1)

        assert record.memory_id == 1
        assert record.state == MemoryState.ACTIVE
        assert record.access_count == 0

    def test_register_multiple(self):
        """注册多个记忆"""
        lifecycle = MemoryLifecycle()
        for i in range(5):
            lifecycle.register_memory(memory_id=i)

        assert len(lifecycle._lifecycle_records) == 5


class TestMemoryLifecycleAccess:
    """测试访问记录"""

    def test_record_access(self):
        """记录记忆访问"""
        lifecycle = MemoryLifecycle()
        lifecycle.register_memory(memory_id=1)

        record = lifecycle.record_access(memory_id=1)
        assert record.access_count == 1

    def test_record_access_nonexistent(self):
        """记录不存在记忆的访问"""
        lifecycle = MemoryLifecycle()
        result = lifecycle.record_access(memory_id=999)
        assert result is None

    def test_access_restores_from_archived(self):
        """访问归档记忆应恢复为活跃"""
        lifecycle = MemoryLifecycle()
        lifecycle.register_memory(memory_id=1)

        # 手动转为归档
        lifecycle.manually_transition(memory_id=1, new_state=MemoryState.ARCHIVED)

        # 访问后应恢复为活跃
        record = lifecycle.record_access(memory_id=1)
        assert record.state == MemoryState.ACTIVE


class TestMemoryLifecycleStateTransitions:
    """测试状态转换"""

    def test_manually_transition(self):
        """手动状态转换"""
        lifecycle = MemoryLifecycle()
        lifecycle.register_memory(memory_id=1)

        # 活跃 → 冷藏
        success = lifecycle.manually_transition(memory_id=1, new_state=MemoryState.COOLING)
        assert success is True

        record = lifecycle.get_memory_lifecycle(memory_id=1)
        assert record.state == MemoryState.COOLING

    def test_manually_transition_nonexistent(self):
        """手动转换不存在的记忆"""
        lifecycle = MemoryLifecycle()
        success = lifecycle.manually_transition(memory_id=999, new_state=MemoryState.COOLING)
        assert success is False

    def test_full_lifecycle(self):
        """完整生命周期转换"""
        lifecycle = MemoryLifecycle()
        lifecycle.register_memory(memory_id=1)

        # 活跃 → 冷藏
        lifecycle.manually_transition(memory_id=1, new_state=MemoryState.COOLING)
        # 冷藏 → 归档
        lifecycle.manually_transition(memory_id=1, new_state=MemoryState.ARCHIVED)

        record = lifecycle.get_memory_lifecycle(memory_id=1)
        assert record.state == MemoryState.ARCHIVED

        # 记录转换历史
        assert len(record.state_transitions) == 2


class TestMemoryLifecycleCheckAndUpdate:
    """测试自动生命周期检查"""

    @pytest.mark.asyncio
    async def test_check_and_update_no_transitions(self):
        """无状态转换的检查"""
        config = LifecycleConfig(
            active_to_cooling_days=365.0,
            cooling_to_archived_days=365.0,
            archived_to_deleted_days=365.0
        )
        lifecycle = MemoryLifecycle(config=config)
        lifecycle.register_memory(memory_id=1)

        stats = await lifecycle.check_and_update_lifecycle()
        assert stats["active_to_cooling"] == 0
        assert stats["cooling_to_archived"] == 0
        assert stats["archived_to_deleted"] == 0

    @pytest.mark.asyncio
    async def test_check_and_update_with_old_memories(self):
        """有旧记忆的生命周期检查"""
        config = LifecycleConfig(
            active_to_cooling_days=0.001,
            cooling_to_archived_days=0.001,
            archived_to_deleted_days=0.001,
            archived_keep_min_count=0
        )
        lifecycle = MemoryLifecycle(config=config)

        # 注册一个旧记忆（创建时间设为过去）
        old_time = datetime.now() - timedelta(days=400)
        lifecycle.register_memory(memory_id=1, created_at=old_time)

        stats = await lifecycle.check_and_update_lifecycle()
        # 应该有多次状态转换
        total_transitions = stats["active_to_cooling"] + stats["cooling_to_archived"] + stats["archived_to_deleted"]
        assert total_transitions >= 1


class TestMemoryLifecycleStats:
    """测试统计功能"""

    def test_get_lifecycle_stats(self):
        """获取生命周期统计"""
        lifecycle = MemoryLifecycle()
        for i in range(5):
            lifecycle.register_memory(memory_id=i)

        stats = lifecycle.get_lifecycle_stats()
        assert stats["total_memories"] == 5
        assert stats["by_state"]["active"] == 5

    def test_get_lifecycle_stats_empty(self):
        """空生命周期统计"""
        lifecycle = MemoryLifecycle()
        stats = lifecycle.get_lifecycle_stats()
        assert stats["total_memories"] == 0

    def test_get_memories_by_state(self):
        """按状态获取记忆"""
        lifecycle = MemoryLifecycle()
        lifecycle.register_memory(memory_id=1)
        lifecycle.register_memory(memory_id=2)

        lifecycle.manually_transition(memory_id=2, new_state=MemoryState.COOLING)

        active = lifecycle.get_memories_by_state(MemoryState.ACTIVE)
        assert len(active) == 1

        cooling = lifecycle.get_memories_by_state(MemoryState.COOLING)
        assert len(cooling) == 1


class TestMemoryLifecycleProtection:
    """测试保护机制"""

    def test_protected_tags(self):
        """受保护标签的记忆"""
        config = LifecycleConfig(
            active_to_cooling_days=0.0,
            protected_tags=["important"]
        )

        lifecycle = MemoryLifecycle(config=config)
        lifecycle.register_memory(memory_id=1)

        # 由于没有数据库支持，保护机制无法验证标签
        # 但至少验证配置正确
        assert "important" in lifecycle.config.protected_tags


# ============================================================
# AgenticRetriever 测试
# ============================================================

class TestAgenticRetrieverInit:
    """测试 AgenticRetriever 初始化"""

    def test_default_init(self):
        """默认初始化"""
        retriever = AgenticRetriever()
        assert retriever.max_retries == 2
        assert retriever.enable_multi_hop is True
        assert retriever.max_hops == 3

    def test_custom_init(self):
        """自定义参数初始化"""
        retriever = AgenticRetriever(
            max_retries=5,
            enable_multi_hop=False,
            max_hops=2
        )
        assert retriever.max_retries == 5
        assert retriever.enable_multi_hop is False
        assert retriever.max_hops == 2


class TestAgenticRetrieverIntentAnalysis:
    """测试意图分析"""

    @pytest.mark.asyncio
    async def test_heuristic_personal_intent(self):
        """启发式个人记忆意图分析"""
        retriever = AgenticRetriever()
        result = await retriever._analyze_intent("我的偏好是什么")
        assert result["intent"] == "personal"

    @pytest.mark.asyncio
    async def test_heuristic_task_intent(self):
        """启发式任务记忆意图分析"""
        retriever = AgenticRetriever()
        result = await retriever._analyze_intent("任务进度如何")
        assert result["intent"] == "task"

    @pytest.mark.asyncio
    async def test_heuristic_tool_intent(self):
        """启发式工具记忆意图分析"""
        retriever = AgenticRetriever()
        result = await retriever._analyze_intent("工具使用方法")
        assert result["intent"] == "tool"

    @pytest.mark.asyncio
    async def test_heuristic_general_intent(self):
        """启发式通用意图分析"""
        retriever = AgenticRetriever()
        result = await retriever._analyze_intent("你好")
        assert result["intent"] == "general"

    @pytest.mark.asyncio
    async def test_entity_extraction(self):
        """实体提取"""
        retriever = AgenticRetriever()
        result = await retriever._analyze_intent('查询关于"机器学习"的内容')
        assert len(result["entities"]) >= 1

    @pytest.mark.asyncio
    async def test_time_mention_detection(self):
        """时间提及检测"""
        retriever = AgenticRetriever()
        result = await retriever._analyze_intent("昨天的任务")
        assert len(result["time_mentions"]) >= 1


class TestAgenticRetrieverStrategySelection:
    """测试策略选择"""

    def test_select_personal_strategy(self):
        """个人记忆策略选择"""
        retriever = AgenticRetriever()
        intent = {"intent": "personal", "entities": [], "time_mentions": [], "memory_types": ["preference"]}
        action = retriever._select_strategy(intent, None, None)
        assert action.strategy == RetrievalStrategy.PERSONAL_MEMORY

    def test_select_task_strategy(self):
        """任务记忆策略选择"""
        retriever = AgenticRetriever()
        intent = {"intent": "task", "entities": [], "time_mentions": [], "memory_types": ["task"]}
        action = retriever._select_strategy(intent, None, None)
        assert action.strategy == RetrievalStrategy.TASK_MEMORY

    def test_select_tool_strategy(self):
        """工具记忆策略选择"""
        retriever = AgenticRetriever()
        intent = {"intent": "tool", "entities": [], "time_mentions": [], "memory_types": ["tool_usage"]}
        action = retriever._select_strategy(intent, None, None)
        assert action.strategy == RetrievalStrategy.TOOL_MEMORY

    def test_select_temporal_strategy(self):
        """时间范围策略选择"""
        retriever = AgenticRetriever()
        intent = {"intent": "general", "entities": [], "time_mentions": [], "memory_types": []}
        action = retriever._select_strategy(intent, None, ("2024-01-01", "2024-12-31"))
        assert action.strategy == RetrievalStrategy.TEMPORAL_SEARCH

    def test_select_default_strategy(self):
        """默认策略选择"""
        retriever = AgenticRetriever()
        intent = {"intent": "general", "entities": [], "time_mentions": [], "memory_types": []}
        action = retriever._select_strategy(intent, None, None)
        assert action.strategy == RetrievalStrategy.HYBRID_SEARCH


class TestAgenticRetrieverResultMerging:
    """测试结果合并"""

    def test_merge_results_no_overlap(self):
        """合并无重叠结果"""
        retriever = AgenticRetriever()

        class MockMemory:
            def __init__(self, id):
                self.id = id

        primary = [MockMemory(1), MockMemory(2)]
        secondary = [MockMemory(3), MockMemory(4)]

        merged = retriever._merge_results(primary, secondary)
        assert len(merged) == 4

    def test_merge_results_with_overlap(self):
        """合并有重叠结果"""
        retriever = AgenticRetriever()

        class MockMemory:
            def __init__(self, id):
                self.id = id

        primary = [MockMemory(1), MockMemory(2)]
        secondary = [MockMemory(2), MockMemory(3)]

        merged = retriever._merge_results(primary, secondary)
        assert len(merged) == 3


class TestAgenticRetrieverRankResults:
    """测试结果排序"""

    def test_rank_results_basic(self):
        """基本结果排序"""
        retriever = AgenticRetriever()

        class MockMemory:
            def __init__(self, id):
                self.id = id

        memories = [MockMemory(i) for i in range(10)]
        ranked = retriever._rank_results("query", memories, top_k=5)
        assert len(ranked) == 5


class TestRetrievalEnums:
    """测试枚举类"""

    def test_retrieval_strategy_enum(self):
        """测试 RetrievalStrategy 枚举"""
        assert RetrievalStrategy.VECTOR_SIMILARITY.value == "vector_similarity"
        assert RetrievalStrategy.KEYWORD_MATCH.value == "keyword_match"
        assert RetrievalStrategy.HYBRID_SEARCH.value == "hybrid_search"
        assert RetrievalStrategy.TEMPORAL_SEARCH.value == "temporal_search"

    def test_retrieval_action_dataclass(self):
        """测试 RetrievalAction 数据类"""
        action = RetrievalAction(
            strategy=RetrievalStrategy.HYBRID_SEARCH,
            params={"top_k": 10},
            reasoning="测试原因",
            confidence=0.8
        )
        assert action.strategy == RetrievalStrategy.HYBRID_SEARCH
        assert action.confidence == 0.8

    def test_retrieval_result_dataclass(self):
        """测试 RetrievalResult 数据类"""
        result = RetrievalResult(
            query="test query",
            strategy_used=RetrievalStrategy.HYBRID_SEARCH,
            memories=[],
            total_candidates=0,
            time_cost_ms=100.0,
            reasoning_trace=["step 1", "step 2"]
        )
        assert result.query == "test query"
        assert len(result.reasoning_trace) == 2


class TestAgenticRetrieverIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_retrieve_with_mock_functions(self):
        """使用模拟函数测试检索"""
        async def mock_retrieve(**kwargs):
            class MockMemory:
                def __init__(self, id):
                    self.id = id
            return [MockMemory(i) for i in range(3)]

        retriever = AgenticRetriever(retrieve_func=mock_retrieve)
        result = await retriever.retrieve(
            query="测试查询",
            agent_id="agent_1",
            user_id="user_1",
            top_k=5
        )
        assert result.query == "测试查询"
        assert result.total_candidates == 3

    @pytest.mark.asyncio
    async def test_retrieve_empty_results(self):
        """测试空结果检索"""
        async def mock_retrieve(**kwargs):
            return []

        retriever = AgenticRetriever(retrieve_func=mock_retrieve)
        result = await retriever.retrieve(
            query="测试查询",
            agent_id="agent_1",
            user_id="user_1",
            top_k=5
        )
        assert result.total_candidates == 0
