# -*- coding: utf-8 -*-
"""
LLM 驱动压缩器：使用大语言模型进行智能记忆压缩

借鉴 ReMe Compactor 设计，实现：
1. 渐进式压缩（支持 previous_summary）
2. 可定制压缩策略
3. 额外指令引导压缩重点
4. 多语言支持
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from .database import MemoryRecord

logger = logging.getLogger(__name__)


class LLMCompactor:
    """LLM 驱动压缩器"""

    def __init__(
        self,
        llm_generate_func: Callable,
        language: str = "zh",
        max_input_length: int = 8000,
        compact_ratio: float = 0.3,
        default_extra_instruction: str = ""
    ):
        """
        初始化 LLM 压缩器
        
        Args:
            llm_generate_func: LLM 生成函数，接收 prompt 返回文本
            language: 输出语言（zh/en/jp 等）
            max_input_length: 最大输入长度（字符数）
            compact_ratio: 压缩目标比例（0.1-0.5）
            default_extra_instruction: 默认额外指令
        """
        self.llm_generate_func = llm_generate_func
        self.language = language
        self.max_input_length = max_input_length
        self.compact_ratio = compact_ratio
        self.default_extra_instruction = default_extra_instruction

    async def compact(
        self,
        memories: List[MemoryRecord],
        previous_summary: str = "",
        extra_instruction: str = "",
        preserve_details: bool = False
    ) -> str:
        """
        使用 LLM 压缩记忆
        
        Args:
            memories: 待压缩的记忆列表
            previous_summary: 之前的摘要（用于渐进式压缩）
            extra_instruction: 额外指令，引导压缩重点
            preserve_details: 是否保留关键细节（降低压缩率）
        
        Returns:
            压缩后的摘要
        """
        if not memories:
            return ""
        
        # 构建输入内容
        content = self._build_memories_content(memories)
        
        # 截断过长的内容
        if len(content) > self.max_input_length:
            content = content[:self.max_input_length]
            logger.warning(f"Content truncated to {self.max_input_length} chars")
        
        # 构建压缩提示词
        prompt = self._build_compaction_prompt(
            content=content,
            previous_summary=previous_summary,
            extra_instruction=extra_instruction or self.default_extra_instruction,
            preserve_details=preserve_details
        )
        
        # 调用 LLM 生成压缩摘要
        try:
            summary = await self.llm_generate_func(prompt)
            logger.info(
                f"Compacted {len(memories)} memories: "
                f"{len(content)} chars -> {len(summary)} chars"
            )
            return summary
        except Exception as e:
            logger.error(f"LLM compaction failed: {e}")
            # 降级为简单压缩
            return self._fallback_compaction(memories)

    def _build_memories_content(self, memories: List[MemoryRecord]) -> str:
        """构建记忆内容字符串"""
        lines = []
        for i, memory in enumerate(memories, 1):
            role = memory.role.upper()
            content = memory.content
            lines.append(f"[{role}] {content}")
            
            # 如果有 metadata，添加关键信息
            if memory.metadata:
                if "tool_name" in memory.metadata:
                    lines.append(f"  → Tool: {memory.metadata['tool_name']}")
                if "importance" in memory.metadata:
                    lines.append(f"  → Importance: {memory.metadata['importance']}")
        
        return "\n".join(lines)

    def _build_compaction_prompt(
        self,
        content: str,
        previous_summary: str,
        extra_instruction: str,
        preserve_details: bool
    ) -> str:
        """构建压缩提示词"""
        # 根据语言选择语言代码
        lang_map = {
            "zh": "中文",
            "en": "English",
            "jp": "日本語"
        }
        language_name = lang_map.get(self.language, "中文")
        
        # 计算目标长度
        target_length = int(len(content) * self.compact_ratio)
        if preserve_details:
            target_length = int(len(content) * 0.5)  # 保留细节时使用更高的压缩率
        
        prompt = f"""# 记忆压缩任务

请将以下对话记录压缩为简洁的摘要，保留关键信息和重要细节。

## 要求

1. **语言**：使用 {language_name}
2. **目标长度**：约 {target_length} 字符（原始长度：{len(content)} 字符）
3. **保留要点**：保留所有关键决策、重要结论、用户偏好
4. **去除冗余**：删除重复内容、寒暄、无关细节
5. **结构化**：按主题或时间线组织，便于后续检索

## 压缩策略

- **用户偏好**：明确记录用户的偏好、习惯、决策
- **关键事实**：保留重要事实、数据、配置信息
- **任务进度**：记录任务状态、完成情况、待办事项
- **情感线索**：保留用户的情感倾向、满意度指标

"""
        
        # 如果有之前的摘要，添加渐进式压缩说明
        if previous_summary:
            prompt += f"""## 历史摘要

以下是之前生成的摘要，请将新内容与历史摘要合并，保持连续性：

{previous_summary}

"""
        
        # 添加额外指令
        if extra_instruction:
            prompt += f"""## 额外指令

{extra_instruction}

"""
        
        # 添加待压缩内容
        prompt += f"""## 待压缩内容

{content}

---

请输出压缩后的摘要：
"""
        
        return prompt

    def _fallback_compaction(self, memories: List[MemoryRecord]) -> str:
        """
        降级压缩：当 LLM 不可用时使用
        
        策略：提取每条记忆的关键信息（前 50 字符）
        """
        lines = []
        for memory in memories:
            content = memory.content
            if len(content) > 50:
                lines.append(f"- {content[:50]}...")
            else:
                lines.append(f"- {content}")
        
        return "\n".join(lines)

    async def incremental_compact(
        self,
        new_memories: List[MemoryRecord],
        existing_summary: str,
        extra_instruction: str = ""
    ) -> str:
        """
        增量压缩：将新记忆合并到现有摘要
        
        Args:
            new_memories: 新记忆列表
            existing_summary: 现有摘要
            extra_instruction: 额外指令
        
        Returns:
            更新后的摘要
        """
        if not new_memories:
            return existing_summary
        
        # 将现有摘要作为 previous_summary 传入
        return await self.compact(
            memories=new_memories,
            previous_summary=existing_summary,
            extra_instruction=extra_instruction
        )

    def get_compact_stats(
        self,
        original_length: int,
        compressed_length: int
    ) -> Dict[str, Any]:
        """
        获取压缩统计信息
        
        Args:
            original_length: 原始长度
            compressed_length: 压缩后长度
        
        Returns:
            压缩统计
        """
        if original_length == 0:
            return {
                "original_length": 0,
                "compressed_length": 0,
                "compression_ratio": 0.0,
                "saved_chars": 0,
                "saved_percentage": 0.0
            }
        
        ratio = compressed_length / original_length
        saved = original_length - compressed_length
        saved_pct = saved / original_length * 100
        
        return {
            "original_length": original_length,
            "compressed_length": compressed_length,
            "compression_ratio": round(ratio, 3),
            "saved_chars": saved,
            "saved_percentage": round(saved_pct, 2)
        }
