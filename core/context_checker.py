# -*- coding: utf-8 -*-
"""
上下文检查器：检查记忆上下文大小，决定是否需要压缩

借鉴 ReMe ContextChecker 设计，确保记忆检索不会导致上下文溢出。

核心功能：
1. 检查记忆列表的 token 数量
2. 智能分割：保留最近记忆，压缩历史记忆
3. 确保记忆完整性（不拆分相关记忆组）
"""

from __future__ import annotations

import logging
from typing import List, Optional, Tuple, Dict, Any

from .database import MemoryRecord

logger = logging.getLogger(__name__)


class ContextChecker:
    """上下文检查器"""

    def __init__(
        self,
        max_tokens: int = 8000,
        reserve_tokens: int = 2000,
        compact_ratio: float = 0.7,
        token_counter: Optional[callable] = None
    ):
        """
        初始化上下文检查器
        
        Args:
            max_tokens: 最大上下文 token 数
            reserve_tokens: 预留 token 数（为新生成回复预留空间）
            compact_ratio: 压缩比例（0.0-1.0）
            token_counter: 自定义 token 计数函数，默认按字符估算
        """
        self.max_tokens = max_tokens
        self.reserve_tokens = reserve_tokens
        self.compact_ratio = compact_ratio
        self.token_counter = token_counter or self._default_token_counter

    @staticmethod
    def _default_token_counter(text: str) -> int:
        """
        默认 token 计数器（粗略估算）
        
        中文：1 字符 ≈ 1.5 token
        英文：1 词 ≈ 1.3 token
        """
        if not text:
            return 0
        
        # 简单估算：中文字符数 * 1.5 + 英文字符数 / 4 * 1.3
        chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
        english_words = len(text.split())
        
        return int(chinese_chars * 1.5 + english_words * 1.3)

    def calculate_threshold(self) -> int:
        """
        计算压缩阈值
        
        公式：(max_tokens - reserve_tokens) × compact_ratio × 0.95
        """
        available_tokens = self.max_tokens - self.reserve_tokens
        return int(available_tokens * self.compact_ratio * 0.95)

    async def check_context(
        self,
        memories: List[MemoryRecord],
        system_prompt: str = "",
        current_query: str = ""
    ) -> Tuple[List[MemoryRecord], List[MemoryRecord], bool]:
        """
        检查记忆上下文大小，决定是否需要压缩
        
        Args:
            memories: 待检查的记忆列表
            system_prompt: 系统提示词（占用上下文空间）
            current_query: 当前查询（占用上下文空间）
        
        Returns:
            (to_compact, to_keep, is_valid)
            - to_compact: 需要压缩的记忆列表
            - to_keep: 保留在上下文中的记忆列表
            - is_valid: 分割是否有效（True 表示不会破坏记忆完整性）
        """
        threshold = self.calculate_threshold()
        
        # 计算固定开销（系统提示词 + 当前查询）
        fixed_overhead = (
            self.token_counter(system_prompt) +
            self.token_counter(current_query)
        )
        
        # 有效阈值
        effective_threshold = threshold - fixed_overhead
        
        # 如果总 token 数未超过阈值，无需压缩
        total_tokens = sum(
            self.token_counter(m.content) for m in memories
        )
        
        if total_tokens <= effective_threshold:
            return [], memories, True
        
        # 需要压缩：从旧到新遍历，分割记忆
        to_compact = []
        to_keep = []
        current_tokens = 0
        
        # 从新到旧遍历（保留最新记忆）
        for memory in reversed(memories):
            memory_tokens = self.token_counter(memory.content)
            
            if current_tokens + memory_tokens <= effective_threshold:
                to_keep.insert(0, memory)
                current_tokens += memory_tokens
            else:
                to_compact.insert(0, memory)
        
        # 验证分割有效性
        is_valid = self._validate_split(to_compact, to_keep)
        
        logger.info(
            f"Context check: total={total_tokens} tokens, "
            f"threshold={effective_threshold} tokens, "
            f"to_compact={len(to_compact)}, to_keep={len(to_keep)}, "
            f"is_valid={is_valid}"
        )
        
        return to_compact, to_keep, is_valid

    def _validate_split(
        self,
        to_compact: List[MemoryRecord],
        to_keep: List[MemoryRecord]
    ) -> bool:
        """
        验证分割是否有效
        
        检查点：
        1. 是否所有记忆都有有效内容
        2. 是否保留了至少一条记忆
        3. 是否压缩了至少一条记忆（如果需要压缩）
        """
        # 必须保留至少一条记忆
        if not to_keep:
            logger.warning("No memories to keep after split")
            return False
        
        # 如果需要压缩但没有记忆被标记为压缩
        if not to_compact and to_keep:
            return True  # 无需压缩，有效
        
        # 所有记忆必须有有效内容
        for memory in to_compact + to_keep:
            if not memory.content or len(memory.content.strip()) == 0:
                logger.warning(f"Empty memory content: id={memory.id}")
                return False
        
        return True

    async def check_and_compact(
        self,
        memories: List[MemoryRecord],
        compact_func: callable,
        system_prompt: str = "",
        current_query: str = ""
    ) -> Tuple[List[MemoryRecord], str]:
        """
        检查上下文并执行压缩
        
        Args:
            memories: 待检查的记忆列表
            compact_func: 压缩函数，接收记忆列表，返回压缩后的摘要
            system_prompt: 系统提示词
            current_query: 当前查询
        
        Returns:
            (processed_memories, compressed_summary)
            - processed_memories: 处理后的记忆列表
            - compressed_summary: 压缩后的摘要（如果有）
        """
        to_compact, to_keep, is_valid = await self.check_context(
            memories, system_prompt, current_query
        )
        
        if not to_compact or not is_valid:
            return memories, ""
        
        # 执行压缩
        try:
            compressed_summary = await compact_func(to_compact)
            logger.info(f"Compacted {len(to_compact)} memories into summary")
            
            # 返回保留的记忆 + 压缩摘要作为一条新记忆
            from .database import MemoryRecord
            import datetime
            
            summary_memory = MemoryRecord(
                id=-1,  # 临时 ID
                agent_id=to_keep[0].agent_id if to_keep else "",
                session_id=to_keep[0].session_id if to_keep else "",
                user_id=to_keep[0].user_id if to_keep else "",
                target_id=to_keep[0].target_id if to_keep else "",
                role="system",
                content=f"[压缩摘要]\n{compressed_summary}",
                importance=4,
                memory_type="summary",
                metadata={"compressed_from": len(to_compact)},
                created_at=datetime.datetime.now().isoformat()
            )
            
            return [summary_memory] + to_keep, compressed_summary
            
        except Exception as e:
            logger.error(f"Error compacting memories: {e}")
            return memories, ""

    def get_context_stats(
        self,
        memories: List[MemoryRecord],
        system_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        获取上下文统计信息
        
        Args:
            memories: 记忆列表
            system_prompt: 系统提示词
        
        Returns:
            上下文统计信息
        """
        threshold = self.calculate_threshold()
        fixed_overhead = self.token_counter(system_prompt)
        effective_threshold = threshold - fixed_overhead
        
        total_tokens = sum(
            self.token_counter(m.content) for m in memories
        )
        
        return {
            "max_tokens": self.max_tokens,
            "reserve_tokens": self.reserve_tokens,
            "threshold": threshold,
            "fixed_overhead": fixed_overhead,
            "effective_threshold": effective_threshold,
            "total_tokens": total_tokens,
            "used_percentage": round(total_tokens / self.max_tokens * 100, 2),
            "needs_compaction": total_tokens > effective_threshold,
            "memory_count": len(memories)
        }
