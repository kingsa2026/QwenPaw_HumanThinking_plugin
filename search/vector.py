# -*- coding: utf-8 -*-
"""
向量搜索引擎：基于 TF-IDF 的轻量级语义检索

支持：
- TF-IDF 关键词匹配
- 混合检索（关键词 + 规则排序）
- 缓存优化
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TFIDFSearchEngine:
    """TF-IDF 搜索引擎"""

    def __init__(self):
        # 文档库
        self._documents: Dict[str, str] = {}
        # 词频统计：{doc_id: {term: count}}
        self._doc_freq: Dict[str, Counter] = {}
        # 逆文档频率：{term: count}
        self._idf: Counter = Counter()
        # 分词缓存
        self._tokenize_cache: Dict[str, List[str]] = {}

    def add_document(self, doc_id: str, content: str) -> None:
        """
        添加文档到索引
        
        Args:
            doc_id: 文档ID
            content: 文档内容
        """
        if doc_id in self._documents:
            return  # 已存在
        
        self._documents[doc_id] = content
        tokens = self._tokenize(content)
        self._doc_freq[doc_id] = Counter(tokens)
        
        # 更新 IDF
        for term in set(tokens):
            self._idf[term] += 1

    def remove_document(self, doc_id: str) -> None:
        """移除文档"""
        if doc_id not in self._documents:
            return
        
        content = self._documents.pop(doc_id)
        tokens = set(self._tokenize(content))
        del self._doc_freq[doc_id]
        
        # 更新 IDF
        for term in tokens:
            self._idf[term] -= 1
            if self._idf[term] <= 0:
                del self._idf[term]

    def search(
        self,
        query: str,
        max_results: int = 10,
        min_score: float = 0.1
    ) -> List[Tuple[str, float]]:
        """
        搜索文档
        
        Args:
            query: 查询文本
            max_results: 最大结果数
            min_score: 最低分数阈值
        
        Returns:
            [(doc_id, score), ...] 按分数降序
        """
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        scores = []
        for doc_id, doc_content in self._documents.items():
            score = self._calculate_tfidf(query_tokens, doc_id)
            if score >= min_score:
                scores.append((doc_id, score))
        
        # 按分数降序
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:max_results]

    def _calculate_tfidf(self, query_tokens: List[str], doc_id: str) -> float:
        """计算 TF-IDF 分数"""
        if doc_id not in self._doc_freq:
            return 0.0
        
        doc_freq = self._doc_freq[doc_id]
        doc_length = sum(doc_freq.values())
        
        tfidf_score = 0.0
        for term in query_tokens:
            if term not in doc_freq:
                continue
            
            # TF: 词频归一化
            tf = doc_freq[term] / doc_length
            
            # IDF: 逆文档频率
            idf = math.log((len(self._documents) + 1) / (self._idf[term] + 1)) + 1
            
            tfidf_score += tf * idf
        
        # 长度归一化
        if doc_length > 0:
            tfidf_score /= math.sqrt(doc_length)
        
        return tfidf_score

    def _tokenize(self, text: str) -> List[str]:
        """
        简单分词（中文按字符，英文按单词）
        
        TODO: 替换为真正的中文分词库（如 jieba）
        """
        if text in self._tokenize_cache:
            return self._tokenize_cache[text]
        
        # 英文单词
        english_words = re.findall(r'[a-zA-Z]+', text.lower())
        # 中文字符
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        
        tokens = english_words + chinese_chars
        self._tokenize_cache[text] = tokens
        
        return tokens

    def get_document_count(self) -> int:
        """获取文档总数"""
        return len(self._documents)

    def clear(self) -> None:
        """清空索引"""
        self._documents.clear()
        self._doc_freq.clear()
        self._idf.clear()
        self._tokenize_cache.clear()
