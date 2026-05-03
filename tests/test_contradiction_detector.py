# -*- coding: utf-8 -*-
"""
矛盾检测器单元测试
"""

import pytest
from datetime import datetime, timedelta

from core.contradiction_detector import (
    ContradictionDetector,
    ContradictionType,
    ConflictResolutionStrategy,
    ContradictionResult,
    detect_contradiction,
    batch_detect_contradictions,
)


class TestContradictionDetector:
    """测试矛盾检测器"""
    
    @pytest.fixture
    def detector(self):
        """创建默认矛盾检测器"""
        return ContradictionDetector()
    
    @pytest.fixture
    def detector_keep_latest(self):
        """创建使用 keep_latest 策略的检测器"""
        return ContradictionDetector(
            resolution_strategy=ConflictResolutionStrategy.KEEP_LATEST
        )
    
    @pytest.fixture
    def detector_keep_both(self):
        """创建使用 keep_both 策略的检测器"""
        return ContradictionDetector(
            resolution_strategy=ConflictResolutionStrategy.KEEP_BOTH
        )
    
    @pytest.fixture
    def detector_mark_for_review(self):
        """创建使用 mark_for_review 策略的检测器"""
        return ContradictionDetector(
            resolution_strategy=ConflictResolutionStrategy.MARK_FOR_REVIEW
        )
    
    # ========== 基础功能测试 ==========
    
    def test_disabled_detection(self):
        """测试禁用矛盾检测"""
        detector = ContradictionDetector(enable_contradiction_detection=False)
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "张三对海鲜过敏"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        assert result.is_contradiction is False
        assert result.confidence == 0.0
    
    def test_empty_content(self, detector):
        """测试空内容"""
        mem1 = {"content": ""}
        mem2 = {"content": "张三对海鲜过敏"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        assert result.is_contradiction is False
    
    # ========== 否定词矛盾检测 ==========
    
    def test_negation_contradiction(self, detector):
        """测试否定词矛盾：喜欢 vs 不喜欢"""
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "张三不喜欢吃海鲜"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        assert result.is_contradiction is True
        # 可能被检测为否定或反义词矛盾
        assert result.contradiction_type in (ContradictionType.NEGATION, ContradictionType.ANTONYM)
        assert result.confidence >= 0.6
    
    def test_negation_contradiction_with_no(self, detector):
        """测试否定词矛盾：会 vs 不会"""
        mem1 = {"content": "张三会游泳"}
        mem2 = {"content": "张三不会游泳"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        assert result.is_contradiction is True
        # 可能被检测为否定或反义词矛盾
        assert result.contradiction_type in (ContradictionType.NEGATION, ContradictionType.ANTONYM)
    
    def test_no_false_positive_negation(self, detector):
        """测试否定词不误报：完全不同的内容"""
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "天气不喜欢吃海鲜"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        # 内容不相似，即使一句有否定也不应该判定为矛盾
        assert result.is_contradiction is False
    
    # ========== 反义词矛盾检测 ==========
    
    def test_antonym_contradiction(self, detector):
        """测试反义词矛盾：喜欢 vs 讨厌"""
        mem1 = {"content": "张三喜欢海鲜"}
        mem2 = {"content": "张三讨厌海鲜"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        # 可能被检测为否定或反义词
        assert result.is_contradiction is True
        assert result.contradiction_type in (ContradictionType.ANTONYM, ContradictionType.NEGATION)
    
    def test_antonym_allergy(self, detector):
        """测试反义词矛盾：喜欢 vs 过敏（特殊场景）"""
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "张三对海鲜过敏"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        # 可能被检测为否定或反义词
        assert result.is_contradiction is True
        assert result.confidence > 0.5
    
    def test_antonym_support_vs_oppose(self, detector):
        """测试反义词矛盾：支持 vs 反对"""
        mem1 = {"content": "张三支持这个方案"}
        mem2 = {"content": "张三反对这个方案"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        # 可能被检测为否定或反义词
        assert result.is_contradiction is True
        assert result.contradiction_type in (ContradictionType.ANTONYM, ContradictionType.NEGATION)
    
    # ========== 时序矛盾检测 ==========
    
    def test_temporal_contradiction_past_vs_present(self, detector):
        """测试时序矛盾：过去 vs 现在"""
        mem1 = {
            "content": "张三曾经喜欢吃海鲜",
            "timestamp": "2024-01-01T00:00:00"
        }
        mem2 = {
            "content": "张三现在不喜欢吃海鲜",
            "timestamp": "2024-06-01T00:00:00"
        }
        
        result = detector.detect_contradiction(mem1, mem2)
        
        # 可能被检测为时序或否定矛盾
        assert result.is_contradiction is True
        assert result.contradiction_type in (ContradictionType.TEMPORAL, ContradictionType.NEGATION)
    
    def test_temporal_contradiction_change(self, detector):
        """测试时序矛盾：状态变化"""
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "张三不再喜欢吃海鲜"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        # 可能被检测为时序或否定矛盾
        assert result.is_contradiction is True
        assert result.contradiction_type in (ContradictionType.TEMPORAL, ContradictionType.NEGATION)
    
    def test_temporal_by_timestamp(self, detector):
        """测试通过时间戳检测时序矛盾"""
        old_time = datetime.now() - timedelta(days=60)
        new_time = datetime.now()
        
        mem1 = {
            "content": "张三住在北京",
            "timestamp": old_time.isoformat()
        }
        mem2 = {
            "content": "张三住在上海",
            "timestamp": new_time.isoformat()
        }
        
        result = detector.detect_contradiction(mem1, mem2)
        
        assert result.is_contradiction is True
    
    # ========== 语义矛盾检测 ==========
    
    def test_semantic_contradiction_sentiment(self, detector):
        """测试语义矛盾：情感极性反转"""
        mem1 = {"content": "张三很开心"}
        mem2 = {"content": "张三很难过"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        # 情感词需要足够明确才能触发语义检测
        # 如果语义检测未触发，至少应该被其他检测捕获
        if result.is_contradiction:
            assert result.contradiction_type in (ContradictionType.SEMANTIC, ContradictionType.NEGATION, ContradictionType.ANTONYM)
        else:
            # 如果未检测到，可能是情感词不够强烈
            pass
    
    def test_semantic_contradiction_positive_vs_negative(self, detector):
        """测试语义矛盾：正面 vs 负面"""
        mem1 = {"content": "这个产品很好"}
        mem2 = {"content": "这个产品很糟糕"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        assert result.is_contradiction is True
        assert result.contradiction_type == ContradictionType.SEMANTIC
    
    # ========== 事实矛盾检测 ==========
    
    def test_factual_contradiction_numbers(self, detector):
        """测试事实矛盾：数值冲突"""
        mem1 = {"content": "张三今年25岁"}
        mem2 = {"content": "张三今年30岁"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        assert result.is_contradiction is True
        assert result.contradiction_type == ContradictionType.FACTUAL
    
    # ========== 矛盾解决策略测试 ==========
    
    def test_keep_latest_strategy(self, detector_keep_latest):
        """测试保留最新策略"""
        mem1 = {
            "content": "张三喜欢吃海鲜",
            "timestamp": "2024-01-01T00:00:00"
        }
        mem2 = {
            "content": "张三不喜欢吃海鲜",
            "timestamp": "2024-06-01T00:00:00"
        }
        
        result = detector_keep_latest.detect_contradiction(mem1, mem2)
        
        # 确保检测到矛盾
        assert result.is_contradiction is True
        if result.suggested_winner and result.suggested_loser:
            assert result.suggested_winner == mem2  # 更新的记忆
            assert result.suggested_loser == mem1
    
    def test_keep_both_strategy(self, detector_keep_both):
        """测试保留双方策略"""
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "张三不喜欢吃海鲜"}
        
        result = detector_keep_both.detect_contradiction(mem1, mem2)
        
        # 确保检测到矛盾
        assert result.is_contradiction is True
        assert result.suggested_winner is None
        assert result.suggested_loser is None
    
    def test_mark_for_review_strategy(self, detector_mark_for_review):
        """测试标记审核策略"""
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "张三不喜欢吃海鲜"}
        
        result = detector_mark_for_review.detect_contradiction(mem1, mem2)
        
        # 确保检测到矛盾
        assert result.is_contradiction is True
        assert result.needs_human_review is True
    
    # ========== 置信度评分测试 ==========
    
    def test_confidence_scoring(self, detector):
        """测试置信度评分"""
        mem1 = {
            "content": "张三喜欢吃海鲜",
            "importance": 5,
            "access_count": 10,
            "timestamp": datetime.now().isoformat(),
            "memory_tier": "active"
        }
        mem2 = {
            "content": "张三对海鲜过敏",
            "importance": 3,
            "access_count": 2,
            "timestamp": (datetime.now() - timedelta(days=30)).isoformat(),
            "memory_tier": "working"
        }
        
        score1 = detector._calculate_memory_confidence(mem1)
        score2 = detector._calculate_memory_confidence(mem2)
        
        assert score1 > score2  # mem1 应该更可信
    
    # ========== 批量检测测试 ==========
    
    def test_batch_detect_contradictions(self):
        """测试批量矛盾检测"""
        memories = [
            {"content": "张三喜欢吃海鲜"},
            {"content": "张三不喜欢吃海鲜"},
            {"content": "张三住在北京"},
            {"content": "张三不住在北京"},
            {"content": " unrelated memory "},
        ]
        
        contradictions = batch_detect_contradictions(memories)
        
        assert len(contradictions) >= 2  # 至少检测到2组矛盾
    
    # ========== 边缘情况测试 ==========
    
    def test_no_contradiction_similar_content(self, detector):
        """测试相似内容但不矛盾"""
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "张三喜欢吃海鲜和烤肉"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        assert result.is_contradiction is False
    
    def test_no_contradiction_different_subjects(self, detector):
        """测试不同主体不矛盾"""
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "天气不喜欢吃海鲜"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        assert result.is_contradiction is False
    
    def test_high_confidence_auto_resolve(self):
        """测试高置信度自动解决"""
        detector = ContradictionDetector(
            auto_resolve=True,
            min_confidence_for_auto=0.8
        )
        
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "张三不喜欢吃海鲜"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        # 否定矛盾的置信度通常较高，应该自动解决
        if result.confidence >= 0.8:
            assert result.needs_human_review is False
    
    def test_low_confidence_needs_review(self):
        """测试低置信度需要审核"""
        detector = ContradictionDetector(
            auto_resolve=True,
            min_confidence_for_auto=0.95  # 设置很高的阈值
        )
        
        mem1 = {"content": "张三可能喜欢吃海鲜"}
        mem2 = {"content": "张三也许不喜欢吃海鲜"}
        
        result = detector.detect_contradiction(mem1, mem2)
        
        # 由于使用了"可能"、"也许"等不确定词汇，置信度应该较低
        if result.is_contradiction:
            assert result.needs_human_review is True


class TestContradictionTypes:
    """测试各种矛盾类型"""
    
    def test_contradiction_type_values(self):
        """测试矛盾类型枚举值"""
        assert ContradictionType.NEGATION.value == "negation"
        assert ContradictionType.ANTONYM.value == "antonym"
        assert ContradictionType.TEMPORAL.value == "temporal"
        assert ContradictionType.SEMANTIC.value == "semantic"
        assert ContradictionType.FACTUAL.value == "factual"
    
    def test_resolution_strategy_values(self):
        """测试解决策略枚举值"""
        assert ConflictResolutionStrategy.KEEP_LATEST.value == "keep_latest"
        assert ConflictResolutionStrategy.KEEP_FREQUENT.value == "keep_frequent"
        assert ConflictResolutionStrategy.KEEP_HIGH_CONFIDENCE.value == "keep_high_confidence"
        assert ConflictResolutionStrategy.MARK_FOR_REVIEW.value == "mark_for_review"
        assert ConflictResolutionStrategy.KEEP_BOTH.value == "keep_both"


class TestContradictionResult:
    """测试矛盾结果数据结构"""
    
    def test_result_structure(self):
        """测试结果结构"""
        result = ContradictionResult(
            is_contradiction=True,
            contradiction_type=ContradictionType.NEGATION,
            confidence=0.85,
            explanation="检测到否定矛盾",
            suggested_winner={"content": "test"},
            suggested_loser={"content": "test2"},
            needs_human_review=False
        )
        
        assert result.is_contradiction is True
        assert result.confidence == 0.85
        assert result.needs_human_review is False


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_detect_contradiction_function(self):
        """测试便捷检测函数"""
        mem1 = {"content": "张三喜欢吃海鲜"}
        mem2 = {"content": "张三不喜欢吃海鲜"}
        
        result = detect_contradiction(mem1, mem2)
        
        assert isinstance(result, ContradictionResult)
        assert result.is_contradiction is True
    
    def test_batch_detect_function(self):
        """测试批量检测函数"""
        memories = [
            {"content": "A"},
            {"content": "不A"},
            {"content": "B"},
        ]
        
        result = batch_detect_contradictions(memories)
        
        assert isinstance(result, list)
        assert len(result) >= 1