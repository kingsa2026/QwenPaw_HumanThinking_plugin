# -*- coding: utf-8 -*-
"""
跨Session搜索引擎：整合多Session的记忆检索

支持：
- 跨Session全局搜索
- 按 target_id 过滤
- 按时间范围过滤
- 温度加权排序
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any

from .vector import TFIDFSearchEngine
from ..core.memory_temperature import MemoryTemperature

logger = logging.getLogger(__name__)


class CrossSessionSearcher:
    """跨Session搜索引擎"""

    def __init__(self):
        # 向量索引
        self._vector_engine = TFIDFSearchEngine()
        # 记忆元数据缓存
        self._metadata_cache: Dict[str, Dict[str, Any]] = {}

    def index_memory(
        self,
        memory_id: str,
        content: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        索引记忆
        
        Args:
            memory_id: 记忆ID
            content: 记忆内容
            metadata: 元数据（agent_id, target_id, session_id, created_at, etc.）
        """
        self._vector_engine.add_document(memory_id, content)
        self._metadata_cache[memory_id] = metadata

    def remove_memory(self, memory_id: str) -> None:
        """移除记忆索引"""
        self._vector_engine.remove_document(memory_id)
        self._metadata_cache.pop(memory_id, None)

    async def search(
        self,
        query: str,
        agent_id: Optional[str] = None,
        target_id: Optional[str] = None,
        session_id: Optional[str] = None,
        time_range: Optional[Dict[str, str]] = None,
        min_temperature: float = 0.0,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索记忆（支持跨Session）
        
        Args:
            query: 查询文本
            agent_id: Agent ID 过滤
            target_id: 对话对象 ID 过滤
            session_id: Session ID 过滤（可选，用于限制范围）
            time_range: 时间范围 {"start": "ISO", "end": "ISO"}
            min_temperature: 最低温度阈值
            max_results: 最大结果数
        
        Returns:
            搜索结果列表
        """
        # 1. 向量搜索
        raw_results = self._vector_engine.search(query, max_results=max_results * 2)
        
        # 2. 过滤和排序
        filtered_results = []
        for memory_id, vector_score in raw_results:
            meta = self._metadata_cache.get(memory_id)
            if not meta:
                continue
            
            # 过滤条件
            if agent_id and meta.get("agent_id") != agent_id:
                continue
            if target_id and meta.get("target_id") != target_id:
                continue
            if session_id and meta.get("session_id") != session_id:
                continue
            
            # 时间范围过滤
            if time_range:
                created_at = meta.get("created_at", "")
                if time_range.get("start") and created_at < time_range["start"]:
                    continue
                if time_range.get("end") and created_at > time_range["end"]:
                    continue
            
            # 温度过滤
            temp_score = MemoryTemperature.calculate(
                access_count=meta.get("access_count", 0),
                search_count=meta.get("search_count", 0),
                importance=meta.get("importance", 3),
                created_at=meta.get("created_at"),
                last_accessed_at=meta.get("last_accessed_at"),
            ).score
            
            if temp_score < min_temperature:
                continue
            
            # 混合分数：向量分数 × 0.6 + 温度分数 × 0.4
            final_score = vector_score * 0.6 + temp_score * 0.4
            
            filtered_results.append({
                "memory_id": memory_id,
                "content": meta.get("content", ""),
                "score": round(final_score, 4),
                "vector_score": round(vector_score, 4),
                "temperature": round(temp_score, 4),
                **meta
            })
        
        # 3. 按最终分数排序
        filtered_results.sort(key=lambda x: x["score"], reverse=True)
        return filtered_results[:max_results]

    def get_stats(self) -> Dict[str, Any]:
        """获取搜索索引统计"""
        return {
            "indexed_documents": self._vector_engine.get_document_count(),
            "cache_size": len(self._metadata_cache)
        }

    def clear(self) -> None:
        """清空索引"""
        self._vector_engine.clear()
        self._metadata_cache.clear()
