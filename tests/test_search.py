# -*- coding: utf-8 -*-
"""
搜索模块单元测试

测试覆盖：
- TF-IDF 搜索引擎
- 跨Session搜索
- 相关性排序
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from HumanThinking.search.vector import TFIDFSearchEngine
from HumanThinking.search.cross_session_searcher import CrossSessionSearcher
from HumanThinking.search.relevance_ranker import RelevanceRanker


class TestTFIDFSearchEngine:
    """TF-IDF 搜索引擎测试"""

    def test_add_and_search(self):
        """添加文档并搜索"""
        engine = TFIDFSearchEngine()
        engine.add_document("doc1", "电商团队的目标是打造高效协作的数字化工作空间")
        engine.add_document("doc2", "今天天气很好，适合出去散步")
        
        results = engine.search("电商")
        assert len(results) > 0
        assert results[0][0] == "doc1"

    def test_search_with_no_results(self):
        """搜索无结果"""
        engine = TFIDFSearchEngine()
        engine.add_document("doc1", "测试文档")
        
        results = engine.search("不存在的内容")
        assert len(results) == 0

    def test_remove_document(self):
        """移除文档"""
        engine = TFIDFSearchEngine()
        engine.add_document("doc1", "测试文档")
        engine.remove_document("doc1")
        
        results = engine.search("测试")
        assert len(results) == 0

    def test_max_results(self):
        """限制结果数量"""
        engine = TFIDFSearchEngine()
        for i in range(20):
            engine.add_document(f"doc{i}", f"测试内容{i}")
        
        results = engine.search("测试", max_results=5)
        assert len(results) == 5

    def test_clear(self):
        """清空索引"""
        engine = TFIDFSearchEngine()
        engine.add_document("doc1", "测试文档")
        engine.clear()
        
        assert engine.get_document_count() == 0

    def test_chinese_tokenization(self):
        """中文分词"""
        engine = TFIDFSearchEngine()
        engine.add_document("doc1", "电商团队目标")
        
        results = engine.search("电商")
        assert len(results) > 0

    def test_english_tokenization(self):
        """英文分词"""
        engine = TFIDFSearchEngine()
        engine.add_document("doc1", "The quick brown fox jumps over the lazy dog")
        
        results = engine.search("quick fox")
        assert len(results) > 0


class TestCrossSessionSearcher:
    """跨Session搜索引擎测试"""

    @pytest.mark.asyncio
    async def test_search_across_sessions(self):
        """跨Session搜索"""
        searcher = CrossSessionSearcher()
        
        # 索引不同Session的记忆
        searcher.index_memory(
            "m1", "电商团队目标讨论",
            {"agent_id": "agent_1", "target_id": "user_1", "session_id": "s1", "created_at": "2026-04-01T00:00:00"}
        )
        searcher.index_memory(
            "m2", "电商架构设计",
            {"agent_id": "agent_1", "target_id": "user_1", "session_id": "s2", "created_at": "2026-04-02T00:00:00"}
        )
        searcher.index_memory(
            "m3", "其他话题",
            {"agent_id": "agent_1", "target_id": "user_2", "session_id": "s3", "created_at": "2026-04-03T00:00:00"}
        )
        
        results = await searcher.search("电商", agent_id="agent_1", target_id="user_1")
        assert len(results) >= 2
        assert all(r["target_id"] == "user_1" for r in results)

    @pytest.mark.asyncio
    async def test_search_with_target_filter(self):
        """按 target_id 过滤"""
        searcher = CrossSessionSearcher()
        searcher.index_memory(
            "m1", "内容A",
            {"agent_id": "agent_1", "target_id": "user_A", "session_id": "s1"}
        )
        searcher.index_memory(
            "m2", "内容B",
            {"agent_id": "agent_1", "target_id": "user_B", "session_id": "s2"}
        )
        
        results = await searcher.search("内容", target_id="user_A")
        assert len(results) == 1
        assert results[0]["target_id"] == "user_A"

    @pytest.mark.asyncio
    async def test_search_stats(self):
        """搜索统计"""
        searcher = CrossSessionSearcher()
        searcher.index_memory("m1", "内容", {})
        
        stats = searcher.get_stats()
        assert stats["indexed_documents"] == 1

    @pytest.mark.asyncio
    async def test_clear(self):
        """清空索引"""
        searcher = CrossSessionSearcher()
        searcher.index_memory("m1", "内容", {})
        searcher.clear()
        
        results = await searcher.search("内容")
        assert len(results) == 0


class TestRelevanceRanker:
    """相关性排序器测试"""

    def test_rank_results(self):
        """排序结果"""
        ranker = RelevanceRanker()
        results = [
            {"score": 0.5, "importance": 3, "created_at": "2026-04-01T00:00:00"},
            {"score": 0.8, "importance": 5, "created_at": "2026-04-10T00:00:00"}
        ]
        
        ranked = ranker.rank(results, query="test")
        assert len(ranked) == 2
        assert ranked[0]["final_score"] >= ranked[1]["final_score"]

    def test_importance_weight(self):
        """重要性加权"""
        ranker = RelevanceRanker(
            relevance_weight=0.3,
            importance_weight=0.6,
            time_weight=0.1
        )
        results = [
            {"score": 0.9, "importance": 1, "created_at": "2026-04-01T00:00:00"},
            {"score": 0.7, "importance": 5, "created_at": "2026-04-10T00:00:00"}
        ]
        
        ranked = ranker.rank(results, query="test")
        # 重要性高的应该排在前面
        assert ranked[0]["importance"] >= ranked[1]["importance"]

    def test_time_decay(self):
        """时间衰减"""
        ranker = RelevanceRanker(time_decay_factor=0.1)
        results = [
            {"score": 0.5, "importance": 3, "created_at": "2026-04-01T00:00:00"},
            {"score": 0.5, "importance": 3, "created_at": "2026-04-10T00:00:00"}
        ]
        
        ranked = ranker.rank(results, query="test", current_time="2026-04-15T00:00:00")
        # 最近的应该排在前面
        assert ranked[0]["created_at"] >= ranked[1]["created_at"]
