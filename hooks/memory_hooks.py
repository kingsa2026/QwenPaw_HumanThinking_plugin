# -*- coding: utf-8 -*-
"""
记忆钩子：在记忆生命周期中插入自定义逻辑

支持钩子：
- before_store: 存储前处理（去重、重要性计算）
- after_store: 存储后处理（索引、关联）
- before_search: 搜索前处理（查询扩展）
- after_search: 搜索后处理（重排序、过滤）
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Awaitable

logger = logging.getLogger(__name__)


class MemoryHook:
    """记忆钩子基类"""

    async def before_store(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """存储前钩子"""
        return memory_data

    async def after_store(self, memory_id: int, memory_data: Dict[str, Any]) -> None:
        """存储后钩子"""
        pass

    async def before_search(self, query: str, filters: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """搜索前钩子"""
        return query, filters

    async def after_search(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """搜索后钩子"""
        return results


class HookManager:
    """钩子管理器"""

    def __init__(self):
        self._hooks: Dict[str, List[MemoryHook]] = {
            "before_store": [],
            "after_store": [],
            "before_search": [],
            "after_search": [],
        }

    def register(self, hook: MemoryHook) -> None:
        """注册钩子"""
        for hook_type in self._hooks:
            if hasattr(hook, hook_type):
                self._hooks[hook_type].append(hook)
                logger.debug(f"Registered hook: {hook.__class__.__name__} -> {hook_type}")

    async def run_before_store(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """运行存储前钩子"""
        for hook in self._hooks["before_store"]:
            try:
                memory_data = await hook.before_store(memory_data)
            except Exception as e:
                logger.error(f"Error in before_store hook {hook.__class__.__name__}: {e}")
        return memory_data

    async def run_after_store(self, memory_id: int, memory_data: Dict[str, Any]) -> None:
        """运行存储后钩子"""
        for hook in self._hooks["after_store"]:
            try:
                await hook.after_store(memory_id, memory_data)
            except Exception as e:
                logger.error(f"Error in after_store hook {hook.__class__.__name__}: {e}")

    async def run_before_search(
        self,
        query: str,
        filters: Dict[str, Any]
    ) -> tuple[str, Dict[str, Any]]:
        """运行搜索前钩子"""
        for hook in self._hooks["before_search"]:
            try:
                query, filters = await hook.before_search(query, filters)
            except Exception as e:
                logger.error(f"Error in before_search hook {hook.__class__.__name__}: {e}")
        return query, filters

    async def run_after_search(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """运行搜索后钩子"""
        for hook in self._hooks["after_search"]:
            try:
                results = await hook.after_search(results)
            except Exception as e:
                logger.error(f"Error in after_search hook {hook.__class__.__name__}: {e}")
        return results


# 内置钩子实现

class DeduplicationHook(MemoryHook):
    """去重钩子：防止重复存储相同内容"""

    def __init__(self):
        self._content_hashes: set = set()

    async def before_store(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """检查内容是否重复"""
        content = memory_data.get("content", "")
        content_hash = hash(content)
        
        if content_hash in self._content_hashes:
            raise ValueError(f"Duplicate content detected: {content[:50]}...")
        
        self._content_hashes.add(content_hash)
        return memory_data

    async def after_store(self, memory_id: int, memory_data: Dict[str, Any]) -> None:
        """存储后保留哈希"""
        pass


class ImportanceCalculatorHook(MemoryHook):
    """重要性计算钩子：自动计算记忆重要性"""

    async def before_store(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """自动计算重要性"""
        if "importance" not in memory_data:
            content = memory_data.get("content", "")
            memory_data["importance"] = self._calculate_importance(content)
        
        return memory_data

    def _calculate_importance(self, content: str) -> int:
        score = 3
        
        if len(content) > 100:
            score += 1
        elif len(content) > 50:
            score += 1
        
        important_keywords = ["目标", "计划", "决定", "重要", "必须", "关键"]
        for keyword in important_keywords:
            if keyword in content:
                score += 1
                break
        
        return min(5, max(1, score))
