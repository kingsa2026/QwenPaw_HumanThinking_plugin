# -*- coding: utf-8 -*-
"""
相关性排序器：优化搜索结果的相关性排序

支持：
- BM25 改进排序
- 时间衰减因子
- 重要性加权
- 多维度相关性融合
"""

from __future__ import annotations

import datetime
import logging
import math
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class RelevanceRanker:
    """相关性排序器"""

    def __init__(
        self,
        bm25_k1: float = 1.2,
        bm25_b: float = 0.75,
        time_decay_factor: float = 0.1,
        importance_weight: float = 0.3,
        time_weight: float = 0.2,
        relevance_weight: float = 0.5
    ):
        """
        初始化排序器
        
        Args:
            bm25_k1: BM25 k1 参数（词频饱和点）
            bm25_b: BM25 b 参数（长度归一化）
            time_decay_factor: 时间衰减因子
            importance_weight: 重要性权重
            time_weight: 时间权重
            relevance_weight: 相关性权重
        """
        self.bm25_k1 = bm25_k1
        self.bm25_b = bm25_b
        self.time_decay_factor = time_decay_factor
        self.importance_weight = importance_weight
        self.time_weight = time_weight
        self.relevance_weight = relevance_weight

    def rank(
        self,
        results: List[Dict[str, Any]],
        query: str,
        current_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        对搜索结果进行排序
        
        Args:
            results: 搜索结果列表
            query: 查询文本
            current_time: 当前时间（ISO 格式）
        
        Returns:
            排序后的结果列表
        """
        if not current_time:
            current_time = datetime.datetime.now().isoformat()
        
        ranked_results = []
        for result in results:
            # 计算综合分数
            final_score = self._calculate_final_score(
                result=result,
                query=query,
                current_time=current_time
            )
            
            ranked_results.append({
                **result,
                "final_score": round(final_score, 4),
                "relevance_score": round(result.get("score", 0) * self.relevance_weight, 4),
                "importance_score": round(self._calculate_importance_score(result) * self.importance_weight, 4),
                "time_score": round(self._calculate_time_score(result, current_time) * self.time_weight, 4)
            })
        
        # 按最终分数降序
        ranked_results.sort(key=lambda x: x["final_score"], reverse=True)
        return ranked_results

    def _calculate_final_score(
        self,
        result: Dict[str, Any],
        query: str,
        current_time: str
    ) -> float:
        """计算最终综合分数"""
        # 1. 相关性分数（BM25/TF-IDF）
        relevance_score = result.get("score", 0)
        
        # 2. 重要性分数
        importance_score = self._calculate_importance_score(result)
        
        # 3. 时间分数
        time_score = self._calculate_time_score(result, current_time)
        
        # 加权融合
        final_score = (
            relevance_score * self.relevance_weight +
            importance_score * self.importance_weight +
            time_score * self.time_weight
        )
        
        return final_score

    def _calculate_importance_score(self, result: Dict[str, Any]) -> float:
        """计算重要性分数（0.0 - 1.0）"""
        importance = result.get("importance", 3)
        return importance / 5.0

    def _calculate_time_score(self, result: Dict[str, Any], current_time: str) -> float:
        """
        计算时间分数（基于时间衰减）
        
        使用指数衰减模型：score = e^(-λ * t)
        其中 t 是距离当前的天数，λ 是衰减因子
        """
        created_at = result.get("created_at")
        if not created_at:
            return 0.5  # 默认中间值
        
        try:
            created = datetime.datetime.fromisoformat(created_at)
            current = datetime.datetime.fromisoformat(current_time)
            days_diff = (current - created).total_seconds() / 86400
            
            # 指数衰减
            time_score = math.exp(-self.time_decay_factor * days_diff)
            return max(0.0, min(1.0, time_score))
        except Exception:
            return 0.5
