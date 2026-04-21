# -*- coding: utf-8 -*-
"""
Phase 3 组件单元测试（独立运行版）

此脚本可以直接运行，不依赖 pytest 框架。
用于测试 VectorStoreBackend、MemoryLifecycle、AgenticRetriever 三个组件。
"""

import sys
import os
import asyncio
import importlib.util
from pathlib import Path
from datetime import datetime, timedelta

# 动态加载模块
def load_module(name, path):
    """动态加载模块，绕过包初始化"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# 获取 HumanThinking 根目录
script_dir = Path(__file__).parent
ht_dir = script_dir.parent

# 加载 Phase 3 组件
print("Loading Phase 3 components...")
vector_store_module = load_module("vector_store_backend", ht_dir / "search" / "vector_store_backend.py")
VectorStoreBackend = vector_store_module.VectorStoreBackend
VectorBackendType = vector_store_module.VectorBackendType
VectorRecord = vector_store_module.VectorRecord
SearchResult = vector_store_module.SearchResult

lifecycle_module = load_module("memory_lifecycle", ht_dir / "core" / "memory_lifecycle.py")
MemoryLifecycle = lifecycle_module.MemoryLifecycle
MemoryState = lifecycle_module.MemoryState
LifecycleConfig = lifecycle_module.LifecycleConfig
MemoryLifecycleRecord = lifecycle_module.MemoryLifecycleRecord

agentic_module = load_module("agentic_retriever", ht_dir / "search" / "agentic_retriever.py")
AgenticRetriever = agentic_module.AgenticRetriever
RetrievalStrategy = agentic_module.RetrievalStrategy
RetrievalAction = agentic_module.RetrievalAction
RetrievalResult = agentic_module.RetrievalResult

print("All Phase 3 components loaded successfully!")
print()


# 测试计数
test_passed = 0
test_failed = 0
test_errors = 0


def run_test(name, func):
    """运行单个测试"""
    global test_passed, test_failed, test_errors
    try:
        func()
        print(f"  PASS: {name}")
        test_passed += 1
    except AssertionError as e:
        print(f"  FAIL: {name} - {e}")
        test_failed += 1
    except Exception as e:
        print(f"  ERROR: {name} - {type(e).__name__}: {e}")
        test_errors += 1


def run_async_test(name, coro):
    """运行异步测试"""
    global test_passed, test_failed, test_errors
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(coro)
        loop.close()
        print(f"  PASS: {name}")
        test_passed += 1
    except AssertionError as e:
        print(f"  FAIL: {name} - {e}")
        test_failed += 1
    except Exception as e:
        print(f"  ERROR: {name} - {type(e).__name__}: {e}")
        test_errors += 1


# ============================================================
# VectorStoreBackend 测试
# ============================================================

print("=" * 60)
print("Testing VectorStoreBackend")
print("=" * 60)


def test_default_init():
    backend = VectorStoreBackend()
    assert backend.backend_type == VectorBackendType.IN_MEMORY
    assert backend.collection_name == "memory_vectors"
    assert backend.embedding_dim == 1536
    assert backend.hybrid_search is True
    assert backend._initialized is True

run_test("default_init", test_default_init)


def test_custom_init():
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

run_test("custom_init", test_custom_init)


def test_backend_type_enum():
    assert VectorBackendType.IN_MEMORY.value == "in_memory"
    assert VectorBackendType.CHROMA.value == "chroma"
    assert VectorBackendType.QDRANT.value == "qdrant"
    assert VectorBackendType.PGVECTOR.value == "pgvector"

run_test("backend_type_enum", test_backend_type_enum)


async def test_add_single_vector():
    backend = VectorStoreBackend()
    vectors = [VectorRecord(
        id="vec_1",
        vector=[0.1, 0.2, 0.3, 0.4, 0.5],
        metadata={"type": "memory", "agent_id": "agent_1"},
        document="测试记忆内容"
    )]
    count = await backend.add_vectors(vectors)
    assert count == 1

run_async_test("add_single_vector", test_add_single_vector())


async def test_add_multiple_vectors():
    backend = VectorStoreBackend()
    vectors = [
        VectorRecord(id=f"vec_{i}", vector=[0.1 * i, 0.2 * i, 0.3 * i], metadata={"index": i})
        for i in range(10)
    ]
    count = await backend.add_vectors(vectors)
    assert count == 10

run_async_test("add_multiple_vectors", test_add_multiple_vectors())


async def test_add_vectors_overwrite():
    backend = VectorStoreBackend()
    vectors1 = [VectorRecord(id="vec_1", vector=[0.1, 0.2, 0.3], document="原始内容")]
    await backend.add_vectors(vectors1)

    vectors2 = [VectorRecord(id="vec_1", vector=[0.4, 0.5, 0.6], document="更新内容")]
    await backend.add_vectors(vectors2)

    count = await backend.get_vector_count()
    assert count == 1

run_async_test("add_vectors_overwrite", test_add_vectors_overwrite())


async def test_search_basic():
    backend = VectorStoreBackend()
    vectors = [
        VectorRecord(id="vec_1", vector=[1.0, 0.0, 0.0], document="文档1"),
        VectorRecord(id="vec_2", vector=[0.0, 1.0, 0.0], document="文档2"),
        VectorRecord(id="vec_3", vector=[0.0, 0.0, 1.0], document="文档3"),
    ]
    await backend.add_vectors(vectors)

    results = await backend.search(query_vector=[1.0, 0.0, 0.0], top_k=1)
    assert len(results) == 1
    assert results[0].id == "vec_1"

run_async_test("search_basic", test_search_basic())


async def test_search_top_k():
    backend = VectorStoreBackend()
    vectors = [
        VectorRecord(id=f"vec_{i}", vector=[1.0 / (i + 1), 0.0, 0.0])
        for i in range(10)
    ]
    await backend.add_vectors(vectors)

    results = await backend.search(query_vector=[1.0, 0.0, 0.0], top_k=3)
    assert len(results) <= 3

run_async_test("search_top_k", test_search_top_k())


async def test_search_empty_db():
    backend = VectorStoreBackend()
    results = await backend.search(query_vector=[1.0, 0.0, 0.0], top_k=5)
    assert len(results) == 0

run_async_test("search_empty_db", test_search_empty_db())


async def test_delete_vectors():
    backend = VectorStoreBackend()
    vectors = [
        VectorRecord(id="vec_1", vector=[1.0, 0.0, 0.0]),
        VectorRecord(id="vec_2", vector=[0.0, 1.0, 0.0]),
    ]
    await backend.add_vectors(vectors)

    deleted = await backend.delete_vectors(["vec_1"])
    assert deleted == 1

    count = await backend.get_vector_count()
    assert count == 1

run_async_test("delete_vectors", test_delete_vectors())


async def test_delete_nonexistent():
    backend = VectorStoreBackend()
    deleted = await backend.delete_vectors(["nonexistent"])
    assert deleted == 0

run_async_test("delete_nonexistent", test_delete_nonexistent())


async def test_clear_all():
    backend = VectorStoreBackend()
    vectors = [
        VectorRecord(id=f"vec_{i}", vector=[0.1 * i, 0.2 * i, 0.3 * i])
        for i in range(5)
    ]
    await backend.add_vectors(vectors)

    await backend.clear()
    count = await backend.get_vector_count()
    assert count == 0

run_async_test("clear_all", test_clear_all())


async def test_get_vector_count():
    backend = VectorStoreBackend()
    vectors = [VectorRecord(id=f"vec_{i}", vector=[0.1 * i, 0.2 * i, 0.3 * i]) for i in range(5)]
    await backend.add_vectors(vectors)

    count = await backend.get_vector_count()
    assert count == 5

run_async_test("get_vector_count", test_get_vector_count())


def test_get_stats():
    async def run():
        backend = VectorStoreBackend()
        vectors = [VectorRecord(id=f"vec_{i}", vector=[0.1 * i, 0.2 * i, 0.3 * i]) for i in range(3)]
        await backend.add_vectors(vectors)
        stats = backend.get_stats()
        assert stats["backend_type"] == "in_memory"
        assert stats["vector_count"] == 3
        assert stats["initialized"] is True
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run())
    loop.close()

run_test("get_stats", test_get_stats)


def test_vector_record():
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

run_test("vector_record", test_vector_record)


def test_search_result():
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

run_test("search_result", test_search_result)


# ============================================================
# MemoryLifecycle 测试
# ============================================================

print()
print("=" * 60)
print("Testing MemoryLifecycle")
print("=" * 60)


def test_lifecycle_default_init():
    lifecycle = MemoryLifecycle()
    assert lifecycle.config.active_to_cooling_days == 7.0
    assert lifecycle.config.cooling_to_archived_days == 30.0
    assert lifecycle.config.archived_to_deleted_days == 365.0

run_test("lifecycle_default_init", test_lifecycle_default_init)


def test_lifecycle_custom_config():
    config = LifecycleConfig(
        active_to_cooling_days=1.0,
        cooling_to_archived_days=3.0,
        archived_to_deleted_days=30.0
    )
    lifecycle = MemoryLifecycle(config=config)
    assert lifecycle.config.active_to_cooling_days == 1.0

run_test("lifecycle_custom_config", test_lifecycle_custom_config)


def test_register_memory():
    lifecycle = MemoryLifecycle()
    record = lifecycle.register_memory(memory_id=1)
    assert record.memory_id == 1
    assert record.state == MemoryState.ACTIVE
    assert record.access_count == 0

run_test("register_memory", test_register_memory)


def test_register_multiple():
    lifecycle = MemoryLifecycle()
    for i in range(5):
        lifecycle.register_memory(memory_id=i)
    assert len(lifecycle._lifecycle_records) == 5

run_test("register_multiple", test_register_multiple)


def test_record_access():
    lifecycle = MemoryLifecycle()
    lifecycle.register_memory(memory_id=1)
    record = lifecycle.record_access(memory_id=1)
    assert record.access_count == 1

run_test("record_access", test_record_access)


def test_record_access_nonexistent():
    lifecycle = MemoryLifecycle()
    result = lifecycle.record_access(memory_id=999)
    assert result is None

run_test("record_access_nonexistent", test_record_access_nonexistent)


def test_access_restores_from_archived():
    lifecycle = MemoryLifecycle()
    lifecycle.register_memory(memory_id=1)
    lifecycle.manually_transition(memory_id=1, new_state=MemoryState.ARCHIVED)
    record = lifecycle.record_access(memory_id=1)
    assert record.state == MemoryState.ACTIVE

run_test("access_restores_from_archived", test_access_restores_from_archived)


def test_manually_transition():
    lifecycle = MemoryLifecycle()
    lifecycle.register_memory(memory_id=1)
    success = lifecycle.manually_transition(memory_id=1, new_state=MemoryState.COOLING)
    assert success is True
    record = lifecycle.get_memory_lifecycle(memory_id=1)
    assert record.state == MemoryState.COOLING

run_test("manually_transition", test_manually_transition)


def test_manually_transition_nonexistent():
    lifecycle = MemoryLifecycle()
    success = lifecycle.manually_transition(memory_id=999, new_state=MemoryState.COOLING)
    assert success is False

run_test("manually_transition_nonexistent", test_manually_transition_nonexistent)


def test_full_lifecycle():
    lifecycle = MemoryLifecycle()
    lifecycle.register_memory(memory_id=1)
    lifecycle.manually_transition(memory_id=1, new_state=MemoryState.COOLING)
    lifecycle.manually_transition(memory_id=1, new_state=MemoryState.ARCHIVED)
    record = lifecycle.get_memory_lifecycle(memory_id=1)
    assert record.state == MemoryState.ARCHIVED
    assert len(record.state_transitions) == 2

run_test("full_lifecycle", test_full_lifecycle)


async def test_check_and_update_no_transitions():
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

run_async_test("check_and_update_no_transitions", test_check_and_update_no_transitions())


async def test_check_and_update_with_old_memories():
    config = LifecycleConfig(
        active_to_cooling_days=0.001,
        cooling_to_archived_days=0.001,
        archived_to_deleted_days=0.001,
        archived_keep_min_count=0
    )
    lifecycle = MemoryLifecycle(config=config)
    old_time = datetime.now() - timedelta(days=400)
    lifecycle.register_memory(memory_id=1, created_at=old_time)
    stats = await lifecycle.check_and_update_lifecycle()
    total_transitions = stats["active_to_cooling"] + stats["cooling_to_archived"] + stats["archived_to_deleted"]
    assert total_transitions >= 1

run_async_test("check_and_update_with_old_memories", test_check_and_update_with_old_memories())


def test_get_lifecycle_stats():
    lifecycle = MemoryLifecycle()
    for i in range(5):
        lifecycle.register_memory(memory_id=i)
    stats = lifecycle.get_lifecycle_stats()
    assert stats["total_memories"] == 5
    assert stats["by_state"]["active"] == 5

run_test("get_lifecycle_stats", test_get_lifecycle_stats)


def test_get_lifecycle_stats_empty():
    lifecycle = MemoryLifecycle()
    stats = lifecycle.get_lifecycle_stats()
    assert stats["total_memories"] == 0

run_test("get_lifecycle_stats_empty", test_get_lifecycle_stats_empty)


def test_get_memories_by_state():
    lifecycle = MemoryLifecycle()
    lifecycle.register_memory(memory_id=1)
    lifecycle.register_memory(memory_id=2)
    lifecycle.manually_transition(memory_id=2, new_state=MemoryState.COOLING)
    active = lifecycle.get_memories_by_state(MemoryState.ACTIVE)
    assert len(active) == 1
    cooling = lifecycle.get_memories_by_state(MemoryState.COOLING)
    assert len(cooling) == 1

run_test("get_memories_by_state", test_get_memories_by_state)


# ============================================================
# AgenticRetriever 测试
# ============================================================

print()
print("=" * 60)
print("Testing AgenticRetriever")
print("=" * 60)


def test_agentic_default_init():
    retriever = AgenticRetriever()
    assert retriever.max_retries == 2
    assert retriever.enable_multi_hop is True
    assert retriever.max_hops == 3

run_test("agentic_default_init", test_agentic_default_init)


def test_agentic_custom_init():
    retriever = AgenticRetriever(
        max_retries=5,
        enable_multi_hop=False,
        max_hops=2
    )
    assert retriever.max_retries == 5
    assert retriever.enable_multi_hop is False
    assert retriever.max_hops == 2

run_test("agentic_custom_init", test_agentic_custom_init)


async def test_heuristic_personal_intent():
    retriever = AgenticRetriever()
    result = await retriever._analyze_intent("我的偏好是什么")
    assert result["intent"] == "personal"

run_async_test("heuristic_personal_intent", test_heuristic_personal_intent())


async def test_heuristic_task_intent():
    retriever = AgenticRetriever()
    result = await retriever._analyze_intent("任务进度如何")
    assert result["intent"] == "task"

run_async_test("heuristic_task_intent", test_heuristic_task_intent())


async def test_heuristic_tool_intent():
    retriever = AgenticRetriever()
    result = await retriever._analyze_intent("工具使用方法")
    assert result["intent"] == "tool"

run_async_test("heuristic_tool_intent", test_heuristic_tool_intent())


async def test_heuristic_general_intent():
    retriever = AgenticRetriever()
    result = await retriever._analyze_intent("你好")
    assert result["intent"] == "general"

run_async_test("heuristic_general_intent", test_heuristic_general_intent())


def test_select_personal_strategy():
    retriever = AgenticRetriever()
    intent = {"intent": "personal", "entities": [], "time_mentions": [], "memory_types": ["preference"]}
    action = retriever._select_strategy(intent, None, None)
    assert action.strategy == RetrievalStrategy.PERSONAL_MEMORY

run_test("select_personal_strategy", test_select_personal_strategy)


def test_select_task_strategy():
    retriever = AgenticRetriever()
    intent = {"intent": "task", "entities": [], "time_mentions": [], "memory_types": ["task"]}
    action = retriever._select_strategy(intent, None, None)
    assert action.strategy == RetrievalStrategy.TASK_MEMORY

run_test("select_task_strategy", test_select_task_strategy)


def test_select_tool_strategy():
    retriever = AgenticRetriever()
    intent = {"intent": "tool", "entities": [], "time_mentions": [], "memory_types": ["tool_usage"]}
    action = retriever._select_strategy(intent, None, None)
    assert action.strategy == RetrievalStrategy.TOOL_MEMORY

run_test("select_tool_strategy", test_select_tool_strategy)


def test_select_temporal_strategy():
    retriever = AgenticRetriever()
    intent = {"intent": "general", "entities": [], "time_mentions": [], "memory_types": []}
    action = retriever._select_strategy(intent, None, ("2024-01-01", "2024-12-31"))
    assert action.strategy == RetrievalStrategy.TEMPORAL_SEARCH

run_test("select_temporal_strategy", test_select_temporal_strategy)


def test_select_default_strategy():
    retriever = AgenticRetriever()
    intent = {"intent": "general", "entities": [], "time_mentions": [], "memory_types": []}
    action = retriever._select_strategy(intent, None, None)
    assert action.strategy == RetrievalStrategy.HYBRID_SEARCH

run_test("select_default_strategy", test_select_default_strategy)


def test_merge_results_no_overlap():
    retriever = AgenticRetriever()

    class MockMemory:
        def __init__(self, id):
            self.id = id

    primary = [MockMemory(1), MockMemory(2)]
    secondary = [MockMemory(3), MockMemory(4)]
    merged = retriever._merge_results(primary, secondary)
    assert len(merged) == 4

run_test("merge_results_no_overlap", test_merge_results_no_overlap)


def test_merge_results_with_overlap():
    retriever = AgenticRetriever()

    class MockMemory:
        def __init__(self, id):
            self.id = id

    primary = [MockMemory(1), MockMemory(2)]
    secondary = [MockMemory(2), MockMemory(3)]
    merged = retriever._merge_results(primary, secondary)
    assert len(merged) == 3

run_test("merge_results_with_overlap", test_merge_results_with_overlap)


def test_rank_results_basic():
    retriever = AgenticRetriever()

    class MockMemory:
        def __init__(self, id):
            self.id = id

    memories = [MockMemory(i) for i in range(10)]
    ranked = retriever._rank_results("query", memories, top_k=5)
    assert len(ranked) == 5

run_test("rank_results_basic", test_rank_results_basic)


def test_retrieval_strategy_enum():
    assert RetrievalStrategy.VECTOR_SIMILARITY.value == "vector_similarity"
    assert RetrievalStrategy.KEYWORD_MATCH.value == "keyword_match"
    assert RetrievalStrategy.HYBRID_SEARCH.value == "hybrid_search"
    assert RetrievalStrategy.TEMPORAL_SEARCH.value == "temporal_search"

run_test("retrieval_strategy_enum", test_retrieval_strategy_enum)


def test_retrieval_action_dataclass():
    action = RetrievalAction(
        strategy=RetrievalStrategy.HYBRID_SEARCH,
        params={"top_k": 10},
        reasoning="测试原因",
        confidence=0.8
    )
    assert action.strategy == RetrievalStrategy.HYBRID_SEARCH
    assert action.confidence == 0.8

run_test("retrieval_action_dataclass", test_retrieval_action_dataclass)


def test_retrieval_result_dataclass():
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

run_test("retrieval_result_dataclass", test_retrieval_result_dataclass)


async def test_retrieve_with_mock_functions():
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

run_async_test("retrieve_with_mock_functions", test_retrieve_with_mock_functions())


async def test_retrieve_empty_results():
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

run_async_test("retrieve_empty_results", test_retrieve_empty_results())


# ============================================================
# 测试报告
# ============================================================

print()
print("=" * 60)
print("TEST REPORT")
print("=" * 60)
print(f"  Passed:  {test_passed}")
print(f"  Failed:  {test_failed}")
print(f"  Errors:  {test_errors}")
print(f"  Total:   {test_passed + test_failed + test_errors}")
print()

if test_failed == 0 and test_errors == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"WARNING: {test_failed} tests failed, {test_errors} tests with errors")
    sys.exit(1)
