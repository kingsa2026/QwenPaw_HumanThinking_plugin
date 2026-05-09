# -*- coding: utf-8 -*-
"""
文件级记忆存储：MEMORY.md + memory/*.md

借鉴 ReMe 文件存储设计，实现：
1. 人类可读的记忆文件
2. 结构化 MEMORY.md 主文件
3. 按日期分割的记忆文件
4. 支持 Agent 直接读写
"""

from __future__ import annotations

import datetime
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .database import MemoryRecord

logger = logging.getLogger(__name__)


class FileMemoryStore:
    """文件级记忆存储"""

    def __init__(
        self,
        memory_dir: str = ".memory",
        timezone: str = None,
        auto_save: bool = True
    ):
        """
        初始化文件记忆存储
        
        Args:
            memory_dir: 记忆存储目录
            timezone: 时区
            auto_save: 是否自动保存
        """
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建子目录
        self.memory_records_dir = self.memory_dir / "memory"
        self.memory_records_dir.mkdir(exist_ok=True)
        
        self.timezone = timezone
        self.auto_save = auto_save
        self._pending_changes = False

    async def persist_summary(
        self,
        summary: str,
        memories: Optional[List[MemoryRecord]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        持久化总结到 MEMORY.md
        
        Args:
            summary: 总结内容
            memories: 原始记忆列表（可选）
            metadata: 元数据（可选）
        
        Returns:
            MEMORY.md 文件路径
        """
        memory_md_path = self.memory_dir / "MEMORY.md"
        
        # 构建 MEMORY.md 内容
        content = self._build_memory_md_content(summary, memories, metadata)
        
        # 写入文件
        with open(memory_md_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Saved MEMORY.md: {memory_md_path}")
        return str(memory_md_path)

    def _build_memory_md_content(
        self,
        summary: str,
        memories: Optional[List[MemoryRecord]],
        metadata: Optional[Dict[str, Any]]
    ) -> str:
        """构建 MEMORY.md 内容"""
        now = datetime.datetime.now()
        if self.timezone:
            now = now.astimezone()
        
        lines = [
            "# 记忆总结 (MEMORY.md)",
            "",
            f"**更新时间**: {now.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**时区**: {self.timezone or 'UTC'}",
            ""
        ]
        
        # 添加元数据
        if metadata:
            lines.append("## 元数据")
            lines.append("")
            for key, value in metadata.items():
                lines.append(f"- **{key}**: {value}")
            lines.append("")
        
        # 添加总结
        lines.append("## 摘要")
        lines.append("")
        lines.append(summary)
        lines.append("")
        
        # 添加原始记忆（如果有）
        if memories:
            lines.append("## 原始记忆")
            lines.append("")
            lines.append(f"共 {len(memories)} 条记忆")
            lines.append("")
            
            for i, memory in enumerate(memories, 1):
                role = memory.role.upper()
                content = memory.content
                lines.append(f"### [{i}] {role}")
                lines.append("")
                lines.append(content)
                lines.append("")
                
                if memory.metadata:
                    lines.append(f"**元数据**: {memory.metadata}")
                    lines.append("")
        
        return "\n".join(lines)

    async def save_daily_memory(
        self,
        memories: List[MemoryRecord],
        date: Optional[str] = None
    ) -> str:
        """
        保存每日记忆到 memory/YYYY-MM-DD.md
        
        Args:
            memories: 记忆列表
            date: 日期（YYYY-MM-DD 格式），默认今天
        
        Returns:
            文件路径
        """
        if not date:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # 验证日期格式
        try:
            datetime.datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {date}, expected YYYY-MM-DD")
        
        # 构建文件路径
        file_path = self.memory_records_dir / f"{date}.md"
        
        # 构建内容
        content = self._build_daily_memory_content(memories, date)
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        logger.info(f"Saved daily memory: {file_path}")
        return str(file_path)

    def _build_daily_memory_content(
        self,
        memories: List[MemoryRecord],
        date: str
    ) -> str:
        """构建每日记忆文件内容"""
        lines = [
            f"# 记忆记录 - {date}",
            "",
            f"共 {len(memories)} 条记忆",
            ""
        ]
        
        # 按角色分类
        user_memories = [m for m in memories if m.role == "user"]
        assistant_memories = [m for m in memories if m.role == "assistant"]
        system_memories = [m for m in memories if m.role == "system"]
        
        # 用户记忆
        if user_memories:
            lines.append("## 用户消息")
            lines.append("")
            for i, memory in enumerate(user_memories, 1):
                lines.append(f"### [{i}] {memory.created_at}")
                lines.append("")
                lines.append(memory.content)
                lines.append("")
        
        # 助手记忆
        if assistant_memories:
            lines.append("## 助手回复")
            lines.append("")
            for i, memory in enumerate(assistant_memories, 1):
                lines.append(f"### [{i}] {memory.created_at}")
                lines.append("")
                lines.append(memory.content)
                lines.append("")
        
        # 系统记忆
        if system_memories:
            lines.append("## 系统信息")
            lines.append("")
            for i, memory in enumerate(system_memories, 1):
                lines.append(f"### [{i}]")
                lines.append("")
                lines.append(memory.content)
                lines.append("")
        
        return "\n".join(lines)

    async def load_memory_md(self) -> Optional[str]:
        """加载 MEMORY.md 内容"""
        memory_md_path = self.memory_dir / "MEMORY.md"
        
        if not memory_md_path.exists():
            return None
        
        with open(memory_md_path, "r", encoding="utf-8") as f:
            return f.read()

    async def load_daily_memory(self, date: str) -> Optional[str]:
        """加载指定日期的记忆文件"""
        file_path = self.memory_records_dir / f"{date}.md"
        
        if not file_path.exists():
            return None
        
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    async def search_files(
        self,
        query: str,
        date_range: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索文件中的记忆（关键词搜索）
        
        Args:
            query: 搜索关键词
            date_range: 日期范围 (start_date, end_date)
        
        Returns:
            搜索结果列表
        """
        results = []
        
        # 搜索 MEMORY.md
        memory_md_content = await self.load_memory_md()
        if memory_md_content and query.lower() in memory_md_content.lower():
            results.append({
                "file": "MEMORY.md",
                "matched": True,
                "content_preview": self._extract_preview(memory_md_content, query)
            })
        
        # 搜索每日记忆文件
        date_files = sorted(self.memory_records_dir.glob("*.md"))
        
        if date_range:
            start_date = datetime.datetime.strptime(date_range[0], "%Y-%m-%d")
            end_date = datetime.datetime.strptime(date_range[1], "%Y-%m-%d")
            date_files = [
                f for f in date_files
                if start_date <= datetime.datetime.strptime(f.stem, "%Y-%m-%d") <= end_date
            ]
        
        for file_path in date_files:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if query.lower() in content.lower():
                results.append({
                    "file": file_path.name,
                    "matched": True,
                    "date": file_path.stem,
                    "content_preview": self._extract_preview(content, query)
                })
        
        return results

    def _extract_preview(self, content: str, query: str, max_length: int = 200) -> str:
        """提取匹配内容的预览"""
        # 找到查询位置
        idx = content.lower().find(query.lower())
        if idx == -1:
            return content[:max_length] + "..."
        
        # 提取上下文
        start = max(0, idx - 50)
        end = min(len(content), idx + len(query) + 150)
        
        preview = content[start:end]
        if start > 0:
            preview = "..." + preview
        if end < len(content):
            preview = preview + "..."
        
        return preview

    def get_stats(self) -> Dict[str, Any]:
        """获取文件存储统计信息"""
        memory_md_exists = (self.memory_dir / "MEMORY.md").exists()
        
        daily_files = list(self.memory_records_dir.glob("*.md"))
        total_size = sum(f.stat().st_size for f in daily_files)
        
        if memory_md_exists:
            total_size += (self.memory_dir / "MEMORY.md").stat().st_size
        
        return {
            "memory_md_exists": memory_md_exists,
            "daily_files_count": len(daily_files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "memory_dir": str(self.memory_dir)
        }
