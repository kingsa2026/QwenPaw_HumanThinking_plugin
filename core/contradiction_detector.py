# -*- coding: utf-8 -*-
"""
记忆矛盾检测器

基于多层级策略检测记忆之间的矛盾：
1. 规则引擎：否定词、反义词、情感极性反转
2. 语义分析：向量相似度 + 情感分析
3. 时序分析：时间戳比较、有效区间判断
4. 置信度评估：来源可靠性、出现频率

矛盾处理策略：
- keep_latest: 保留时间戳最新的记忆
- keep_frequent: 保留出现频率最高的记忆
- keep_high_confidence: 保留置信度最高的记忆
- mark_for_review: 标记为待人工确认
- keep_both: 保留双方，标记矛盾关系
"""

import logging
import re
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class ConflictResolutionStrategy(Enum):
    """矛盾解决策略"""
    KEEP_LATEST = "keep_latest"           # 保留最新的
    KEEP_FREQUENT = "keep_frequent"       # 保留频率最高的
    KEEP_HIGH_CONFIDENCE = "keep_high_confidence"  # 保留置信度最高的
    MARK_FOR_REVIEW = "mark_for_review"   # 标记待确认
    KEEP_BOTH = "keep_both"               # 保留双方，标记矛盾


class ContradictionType(Enum):
    """矛盾类型"""
    NEGATION = "negation"                 # 否定矛盾（喜欢 vs 不喜欢）
    ANTONYM = "antonym"                   # 反义词矛盾（好 vs 坏）
    TEMPORAL = "temporal"                 # 时序矛盾（曾经 vs 现在不）
    SEMANTIC = "semantic"                 # 语义矛盾（向量相似但情感相反）
    FACTUAL = "factual"                   # 事实矛盾（数值/属性冲突）


@dataclass
class ContradictionResult:
    """矛盾检测结果"""
    is_contradiction: bool
    contradiction_type: Optional[ContradictionType]
    confidence: float                     # 矛盾检测置信度 (0-1)
    explanation: str                      # 矛盾解释
    suggested_winner: Optional[Dict]      # 建议保留的记忆
    suggested_loser: Optional[Dict]       # 建议废弃的记忆
    needs_human_review: bool              # 是否需要人工确认


class ContradictionDetector:
    """矛盾检测器"""
    
    # 否定词模式（中文 + 英文）
    NEGATION_PATTERNS = {
        "不", "没", "无", "非", "莫", "勿", "未", "否",
        "反对", "拒绝", "禁止", "防止", "避免", "取消",
        "not", "no", "never", "none", "nothing", "nobody",
        "don't", "doesn't", "didn't", "won't", "wouldn't",
        "can't", "cannot", "couldn't", "shouldn't",
    }
    
    # 反义词词典（中文）
    ANTONYM_PAIRS = [
        ("喜欢", "讨厌"), ("喜欢", "厌恶"), ("喜欢", "反感"), ("喜欢", "恨"),
        ("爱", "恨"), ("爱", "讨厌"),
        ("支持", "反对"), ("同意", "反对"),
        ("相信", "怀疑"), ("信任", "怀疑"),
        ("能", "不能"), ("会", "不会"), ("可以", "不可以"),
        ("好", "坏"), ("优", "劣"), ("强", "弱"),
        ("大", "小"), ("多", "少"), ("高", "低"),
        ("快", "慢"), ("早", "晚"), ("新", "旧"),
        ("开心", "难过"), ("快乐", "悲伤"), ("幸福", "痛苦"),
        ("成功", "失败"), ("胜利", "失败"),
        ("有", "没有"), ("是", "不是"),
        ("经常", "从不"), ("总是", "从不"),
        ("过敏", "喜欢"), ("过敏", "爱吃"),  # 特殊场景
    ]
    
    # 时序关键词
    TEMPORAL_PATTERNS = {
        "past": ["曾经", "以前", "过去", "之前", "原来", "以前", "formerly", "used to", "previously"],
        "present": ["现在", "目前", "当前", "如今", "现在", "now", "currently", "presently"],
        "future": ["将来", "以后", "未来", "之后", "将要", "will", "going to", "future"],
        "change": ["不再", "已经", "变了", "改", "变成", "not anymore", "no longer", "changed"],
    }
    
    # 情感极性词（简化版）
    POSITIVE_WORDS = {
        "喜欢", "爱", "开心", "快乐", "幸福", "满意", "享受", "热爱", "欣赏",
        "优秀", "好", "棒", "赞", "完美", "舒服", "轻松", "愉快",
        "支持", "同意", "认可", "接受", "欢迎", "推荐",
        "成功", "胜利", "达成", "实现", "完成",
        "beautiful", "good", "great", "excellent", "amazing", "wonderful",
        "love", "like", "enjoy", "happy", "pleased", "satisfied",
    }
    
    NEGATIVE_WORDS = {
        "讨厌", "恨", "厌恶", "反感", "恶心", "烦", "痛苦", "难过", "悲伤",
        "差", "坏", "糟", "烂", "垃圾", "糟糕", "严重", "危险",
        "反对", "拒绝", "抵制", "排斥", "否认", "抗议",
        "失败", "错误", "失误", "错过", "失去",
        "hate", "dislike", "disgusting", "terrible", "awful", "horrible",
        "bad", "worst", "fail", "wrong", "error", "miss",
        "过敏", "不耐受", "禁止", "不能", "不可",
    }
    
    def __init__(
        self,
        enable_contradiction_detection: bool = True,
        contradiction_threshold: float = 0.7,
        resolution_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.KEEP_LATEST,
        enable_semantic_check: bool = True,
        enable_temporal_check: bool = True,
        enable_confidence_scoring: bool = True,
        auto_resolve: bool = True,         # 是否自动解决（否则标记待确认）
        min_confidence_for_auto: float = 0.85,  # 自动解决的最低置信度
    ):
        self.enable_contradiction_detection = enable_contradiction_detection
        self.contradiction_threshold = contradiction_threshold
        self.resolution_strategy = resolution_strategy
        self.enable_semantic_check = enable_semantic_check
        self.enable_temporal_check = enable_temporal_check
        self.enable_confidence_scoring = enable_confidence_scoring
        self.auto_resolve = auto_resolve
        self.min_confidence_for_auto = min_confidence_for_auto
        
        # 构建反义词快速查找表
        self._antonym_map: Dict[str, Set[str]] = {}
        for w1, w2 in self.ANTONYM_PAIRS:
            self._antonym_map.setdefault(w1, set()).add(w2)
            self._antonym_map.setdefault(w2, set()).add(w1)
    
    def detect_contradiction(self, mem1: Dict, mem2: Dict) -> ContradictionResult:
        """
        检测两条记忆是否矛盾
        
        Args:
            mem1: 记忆1
            mem2: 记忆2
            
        Returns:
            ContradictionResult: 矛盾检测结果
        """
        if not self.enable_contradiction_detection:
            return ContradictionResult(
                is_contradiction=False,
                contradiction_type=None,
                confidence=0.0,
                explanation="矛盾检测已禁用",
                suggested_winner=None,
                suggested_loser=None,
                needs_human_review=False
            )
        
        content1 = mem1.get("content", "").strip()
        content2 = mem2.get("content", "").strip()
        
        if not content1 or not content2:
            return ContradictionResult(
                is_contradiction=False,
                contradiction_type=None,
                confidence=0.0,
                explanation="内容为空",
                suggested_winner=None,
                suggested_loser=None,
                needs_human_review=False
            )
        
        # 多层级检测
        checks = []
        
        # Layer 1: 否定词检测
        neg_result = self._check_negation(content1, content2)
        if neg_result[0]:
            checks.append((ContradictionType.NEGATION, neg_result[1], neg_result[2]))
        
        # Layer 2: 反义词检测
        ant_result = self._check_antonym(content1, content2)
        if ant_result[0]:
            checks.append((ContradictionType.ANTONYM, ant_result[1], ant_result[2]))
        
        # Layer 3: 时序矛盾检测
        if self.enable_temporal_check:
            temp_result = self._check_temporal(content1, content2, mem1, mem2)
            if temp_result[0]:
                checks.append((ContradictionType.TEMPORAL, temp_result[1], temp_result[2]))
        
        # Layer 4: 语义矛盾检测（情感极性反转）
        if self.enable_semantic_check:
            sem_result = self._check_semantic(content1, content2)
            if sem_result[0]:
                checks.append((ContradictionType.SEMANTIC, sem_result[1], sem_result[2]))
        
        # Layer 5: 事实矛盾检测（数值/属性冲突）
        fact_result = self._check_factual(content1, content2)
        if fact_result[0]:
            checks.append((ContradictionType.FACTUAL, fact_result[1], fact_result[2]))
        
        # 综合判断
        if not checks:
            return ContradictionResult(
                is_contradiction=False,
                contradiction_type=None,
                confidence=0.0,
                explanation="未检测到矛盾",
                suggested_winner=None,
                suggested_loser=None,
                needs_human_review=False
            )
        
        # 取最高置信度的矛盾类型
        best_check = max(checks, key=lambda x: x[2])
        contradiction_type, explanation, confidence = best_check
        
        # 如果多个检测都命中，提升置信度
        if len(checks) > 1:
            confidence = min(confidence + 0.1 * (len(checks) - 1), 1.0)
            explanation += f" (多重验证: {len(checks)}种检测命中)"
        
        # 判断是否达到矛盾阈值
        is_contradiction = confidence >= self.contradiction_threshold
        
        # 确定建议的胜者和败者
        suggested_winner, suggested_loser = self._resolve_contradiction(
            mem1, mem2, contradiction_type, confidence
        )
        
        # 判断是否需要人工确认
        needs_human_review = (
            not self.auto_resolve or 
            confidence < self.min_confidence_for_auto or
            self.resolution_strategy == ConflictResolutionStrategy.MARK_FOR_REVIEW
        )
        
        return ContradictionResult(
            is_contradiction=is_contradiction,
            contradiction_type=contradiction_type,
            confidence=confidence,
            explanation=explanation,
            suggested_winner=suggested_winner,
            suggested_loser=suggested_loser,
            needs_human_review=needs_human_review
        )
    
    def _check_negation(self, text1: str, text2: str) -> Tuple[bool, str, float]:
        """检测否定词矛盾"""
        # 检查是否一句有否定词，另一句没有
        has_neg1 = any(p in text1 for p in self.NEGATION_PATTERNS)
        has_neg2 = any(p in text2 for p in self.NEGATION_PATTERNS)
        
        if has_neg1 == has_neg2:
            return False, "", 0.0
        
        # 检查核心内容是否相似（去掉否定词后）
        clean1 = self._remove_negation(text1)
        clean2 = self._remove_negation(text2)
        
        # 提取主语（前2-4个字通常是主语）
        subject1 = self._extract_subject(text1)
        subject2 = self._extract_subject(text2)
        
        # 如果主语不同，可能是不同主体的描述，不一定是矛盾
        if subject1 and subject2 and subject1 != subject2:
            # 主语不同，降低相似度阈值要求
            similarity = self._text_similarity(clean1, clean2)
            if similarity > 0.85:  # 需要更高的相似度才判定为矛盾
                return True, f"检测到否定矛盾(不同主体): '{text1[:30]}...' vs '{text2[:30]}...'", min(similarity, 0.7)
            return False, "", 0.0
        
        # 如果去掉否定词后很相似 → 矛盾
        similarity = self._text_similarity(clean1, clean2)
        
        if similarity > 0.6:
            neg_word = "否定词" if has_neg1 else "肯定"
            pos_word = "肯定" if has_neg1 else "否定词"
            return True, f"检测到否定矛盾: '{text1[:30]}...' 含{neg_word}，'{text2[:30]}...' 为{pos_word}", min(similarity + 0.2, 0.9)
        
        return False, "", 0.0
    
    def _extract_subject(self, text: str) -> Optional[str]:
        """提取句子主语（简化：取前2-4个字符）"""
        if len(text) < 2:
            return None
        # 取前2-4个字符作为主语候选
        return text[:min(4, len(text))]
    
    def _check_antonym(self, text1: str, text2: str) -> Tuple[bool, str, float]:
        """检测反义词矛盾"""
        words1 = set(self._extract_words(text1))
        words2 = set(self._extract_words(text2))
        
        # 检查是否有反义词对
        for word1 in words1:
            if word1 in self._antonym_map:
                antonyms = self._antonym_map[word1]
                for word2 in words2:
                    if word2 in antonyms:
                        # 检查上下文是否相同
                        context_sim = self._context_similarity(text1, text2, word1, word2)
                        if context_sim > 0.5:
                            return True, f"检测到反义词矛盾: '{word1}' vs '{word2}'", min(context_sim + 0.3, 0.95)
        
        return False, "", 0.0
    
    def _check_temporal(self, text1: str, text2: str, mem1: Dict, mem2: Dict) -> Tuple[bool, str, float]:
        """检测时序矛盾"""
        # 检查是否有时间关键词
        has_past1 = any(p in text1 for p in self.TEMPORAL_PATTERNS["past"])
        has_past2 = any(p in text2 for p in self.TEMPORAL_PATTERNS["past"])
        has_present1 = any(p in text1 for p in self.TEMPORAL_PATTERNS["present"])
        has_present2 = any(p in text2 for p in self.TEMPORAL_PATTERNS["present"])
        has_change1 = any(p in text1 for p in self.TEMPORAL_PATTERNS["change"])
        has_change2 = any(p in text2 for p in self.TEMPORAL_PATTERNS["change"])
        
        # 情况1：一句说过去，一句说现在（且内容相似）
        if (has_past1 and has_present2) or (has_present1 and has_past2):
            similarity = self._text_similarity(text1, text2)
            if similarity > 0.5:
                return True, "检测到时序矛盾: 过去 vs 现在", min(similarity + 0.2, 0.85)
        
        # 情况2：一句含"不再/已经"等变化词
        if has_change1 or has_change2:
            similarity = self._text_similarity(text1, text2)
            if similarity > 0.5:
                return True, "检测到时序矛盾: 状态变化", min(similarity + 0.15, 0.8)
        
        # 情况3：时间戳比较（如果一条很旧，一条很新，且内容相似）
        time1 = mem1.get("timestamp") or mem1.get("created_at")
        time2 = mem2.get("timestamp") or mem2.get("created_at")
        
        if time1 and time2:
            try:
                dt1 = self._parse_datetime(time1)
                dt2 = self._parse_datetime(time2)
                if dt1 and dt2:
                    days_diff = abs((dt2 - dt1).days)
                    if days_diff > 30:  # 超过30天
                        similarity = self._text_similarity(text1, text2)
                        if similarity > 0.6:
                            return True, f"检测到时序矛盾: 时间差{days_diff}天", min(similarity + 0.1, 0.75)
            except:
                pass
        
        return False, "", 0.0
    
    def _check_semantic(self, text1: str, text2: str) -> Tuple[bool, str, float]:
        """检测语义矛盾（情感极性反转 + 内容相似）"""
        # 计算情感极性
        sentiment1 = self._calculate_sentiment(text1)
        sentiment2 = self._calculate_sentiment(text2)
        
        # 如果情感极性相反（一正一负）
        if sentiment1 * sentiment2 < 0:  # 异号
            # 检查内容相似度
            similarity = self._text_similarity(text1, text2)
            if similarity > 0.5:
                confidence = min(abs(sentiment1 - sentiment2) * 0.5 + similarity * 0.5, 0.9)
                return True, f"检测到语义矛盾: 情感极性反转 ({sentiment1:.2f} vs {sentiment2:.2f})", confidence
        
        return False, "", 0.0
    
    def _check_factual(self, text1: str, text2: str) -> Tuple[bool, str, float]:
        """检测事实矛盾（数值、属性冲突）"""
        # 提取数值
        numbers1 = re.findall(r'\d+\.?\d*', text1)
        numbers2 = re.findall(r'\d+\.?\d*', text2)
        
        # 如果都有数值且数值不同，但上下文相似
        if numbers1 and numbers2 and text1 != text2:
            # 检查是否有相同的度量单位或属性
            similarity = self._text_similarity(
                re.sub(r'\d+\.?\d*', '', text1),
                re.sub(r'\d+\.?\d*', '', text2)
            )
            if similarity > 0.7:
                return True, f"检测到事实矛盾: 数值/属性冲突", min(similarity + 0.1, 0.8)
        
        return False, "", 0.0
    
    def _resolve_contradiction(
        self,
        mem1: Dict,
        mem2: Dict,
        contradiction_type: ContradictionType,
        confidence: float
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """根据策略决定保留哪条记忆"""
        strategy = self.resolution_strategy
        
        if strategy == ConflictResolutionStrategy.KEEP_BOTH:
            return None, None  # 不决定胜负，保留双方
        
        if strategy == ConflictResolutionStrategy.MARK_FOR_REVIEW:
            return None, None  # 待人工确认
        
        if strategy == ConflictResolutionStrategy.KEEP_LATEST:
            time1 = self._parse_datetime(mem1.get("timestamp") or mem1.get("created_at", ""))
            time2 = self._parse_datetime(mem2.get("timestamp") or mem2.get("created_at", ""))
            if time1 and time2:
                return (mem1, mem2) if time1 >= time2 else (mem2, mem1)
            # 无法比较时间， fallback 到 KEEP_HIGH_CONFIDENCE
            strategy = ConflictResolutionStrategy.KEEP_HIGH_CONFIDENCE
        
        if strategy == ConflictResolutionStrategy.KEEP_FREQUENT:
            freq1 = mem1.get("access_count", 0) + mem1.get("hit_count", 0)
            freq2 = mem2.get("access_count", 0) + mem2.get("hit_count", 0)
            if freq1 != freq2:
                return (mem1, mem2) if freq1 > freq2 else (mem2, mem1)
            strategy = ConflictResolutionStrategy.KEEP_HIGH_CONFIDENCE
        
        if strategy == ConflictResolutionStrategy.KEEP_HIGH_CONFIDENCE:
            score1 = self._calculate_memory_confidence(mem1)
            score2 = self._calculate_memory_confidence(mem2)
            return (mem1, mem2) if score1 >= score2 else (mem2, mem1)
        
        # 默认：保留第一条
        return mem1, mem2
    
    def _calculate_memory_confidence(self, mem: Dict) -> float:
        """计算记忆的综合置信度分数"""
        if not self.enable_confidence_scoring:
            return 0.5
        
        scores = []
        
        # 1. 重要性分数
        importance = mem.get("importance", 3)
        scores.append(importance / 5.0)
        
        # 2. 访问频率（被引用的次数）
        access_count = mem.get("access_count", 0) + mem.get("hit_count", 0)
        scores.append(min(access_count / 10.0, 1.0))
        
        # 3. 时效性（越新的记忆置信度越高）
        created_at = mem.get("created_at") or mem.get("timestamp")
        if created_at:
            try:
                dt = self._parse_datetime(created_at)
                if dt:
                    days_old = (datetime.now() - dt).days
                    scores.append(max(0, 1.0 - days_old / 365.0))
            except:
                scores.append(0.5)
        else:
            scores.append(0.5)
        
        # 4. 记忆层级（active > working > frozen > archived）
        tier_scores = {"active": 1.0, "working": 0.8, "frozen": 0.5, "archived": 0.3}
        tier = mem.get("memory_tier", "working")
        scores.append(tier_scores.get(tier, 0.5))
        
        # 5. 是否有验证标记
        if mem.get("verified"):
            scores.append(1.0)
        
        return sum(scores) / len(scores)
    
    def _calculate_sentiment(self, text: str) -> float:
        """计算文本情感极性 (-1 到 +1)"""
        words = self._extract_words(text)
        
        pos_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
        neg_count = sum(1 for w in words if w in self.NEGATIVE_WORDS)
        total = pos_count + neg_count
        
        if total == 0:
            return 0.0
        
        return (pos_count - neg_count) / total
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """计算两段文本的相似度 (0-1)"""
        import difflib
        return difflib.SequenceMatcher(None, text1, text2).ratio()
    
    def _remove_negation(self, text: str) -> str:
        """移除文本中的否定词"""
        result = text
        for neg in sorted(self.NEGATION_PATTERNS, key=len, reverse=True):
            result = result.replace(neg, "")
        return result.strip()
    
    def _extract_words(self, text: str) -> List[str]:
        """提取中文词汇（简化版）"""
        # 使用正则提取中文字符和英文单词
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        # 提取所有2-4字的中文子串（用于反义词匹配）
        chinese_phrases = []
        # 提取连续中文字符序列
        sequences = re.findall(r'[\u4e00-\u9fff]+', text)
        for seq in sequences:
            # 提取2字、3字、4字的子串
            for length in [2, 3, 4]:
                for i in range(len(seq) - length + 1):
                    chinese_phrases.append(seq[i:i+length])
        return chinese_chars + english_words + chinese_phrases
    
    def _context_similarity(self, text1: str, text2: str, word1: str, word2: str) -> float:
        """计算两个词在各自文本中的上下文相似度"""
        # 简单的实现：去掉关键词后比较剩余部分
        clean1 = text1.replace(word1, "").replace(word2, "")
        clean2 = text2.replace(word1, "").replace(word2, "")
        return self._text_similarity(clean1, clean2)
    
    def _parse_datetime(self, dt_value) -> Optional[datetime]:
        """解析各种日期时间格式"""
        if isinstance(dt_value, datetime):
            return dt_value
        
        if isinstance(dt_value, str):
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%d",
                "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(dt_value.split('+')[0].split('Z')[0], fmt)
                except ValueError:
                    continue
        
        if isinstance(dt_value, (int, float)):
            # 假设是时间戳
            return datetime.fromtimestamp(dt_value)
        
        return None


# 便捷函数
def detect_contradiction(mem1: Dict, mem2: Dict, **config) -> ContradictionResult:
    """便捷函数：检测两条记忆是否矛盾"""
    detector = ContradictionDetector(**config)
    return detector.detect_contradiction(mem1, mem2)


def batch_detect_contradictions(
    memories: List[Dict],
    **config
) -> List[Tuple[int, int, ContradictionResult]]:
    """批量检测记忆列表中的矛盾对"""
    detector = ContradictionDetector(**config)
    contradictions = []
    
    for i in range(len(memories)):
        for j in range(i + 1, len(memories)):
            result = detector.detect_contradiction(memories[i], memories[j])
            if result.is_contradiction:
                contradictions.append((i, j, result))
    
    return contradictions