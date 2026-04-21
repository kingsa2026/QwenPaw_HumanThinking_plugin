# -*- coding: utf-8 -*-
"""
工具结果压缩器：管理大型工具输出

借鉴 ReMe ToolResultCompactor 设计，实现：
1. 截断大型工具输出
2. 完整内容存储到文件
3. 自动清理过期文件
4. 分级策略：recent vs old 不同阈值
"""

from __future__ import annotations

import datetime
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ToolResultCompactor:
    """工具结果压缩器"""

    def __init__(
        self,
        tool_result_dir: str = ".tool_results",
        old_max_bytes: int = 3000,
        recent_max_bytes: int = 100 * 1024,
        retention_days: int = 3,
        recent_n: int = 1
    ):
        """
        初始化工具结果压缩器
        
        Args:
            tool_result_dir: 工具结果存储目录
            old_max_bytes: 旧工具结果截断阈值（字节）
            recent_max_bytes: 最近工具结果截断阈值（字节）
            retention_days: 文件保留天数
            recent_n: 最近 N 条工具结果不压缩
        """
        self.tool_result_dir = Path(tool_result_dir)
        self.tool_result_dir.mkdir(parents=True, exist_ok=True)
        
        self.old_max_bytes = old_max_bytes
        self.recent_max_bytes = recent_max_bytes
        self.retention_days = retention_days
        self.recent_n = recent_n

    async def compact(
        self,
        tool_results: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        压缩工具结果
        
        Args:
            tool_results: 工具结果列表，每项包含：
                - content: 工具输出内容
                - timestamp: 时间戳
                - tool_name: 工具名称
                - metadata: 元数据
            metadata: 额外元数据
        
        Returns:
            压缩后的工具结果列表
        """
        if not tool_results:
            return []
        
        results = []
        total = len(tool_results)
        
        for idx, result in enumerate(tool_results):
            # 判断是否是最近的结果
            is_recent = idx >= (total - self.recent_n)
            max_bytes = self.recent_max_bytes if is_recent else self.old_max_bytes
            
            content = result.get("content", "")
            content_bytes = len(content.encode("utf-8"))
            
            if content_bytes <= max_bytes:
                # 未超过阈值，保留原样
                results.append(result)
            else:
                # 超过阈值，截断并存储到文件
                truncated_content = content[:max_bytes]
                file_path = await self._save_to_file(
                    content,
                    result.get("tool_name", "unknown"),
                    result.get("timestamp", datetime.datetime.now().isoformat()),
                    metadata
                )
                
                # 替换为截断内容 + 文件引用
                truncated_result = {
                    **result,
                    "content": (
                        f"{truncated_content}\n\n"
                        f"[内容已截断，完整内容保存到文件: {file_path}]\n"
                        f"[原始大小: {content_bytes} 字节, 阈值: {max_bytes} 字节]"
                    ),
                    "truncated": True,
                    "original_size": content_bytes,
                    "file_path": str(file_path)
                }
                results.append(truncated_result)
                
                logger.info(
                    f"Truncated tool result: {result.get('tool_name', 'unknown')}, "
                    f"{content_bytes} -> {max_bytes} bytes, saved to {file_path}"
                )
        
        return results

    async def _save_to_file(
        self,
        content: str,
        tool_name: str,
        timestamp: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        保存完整内容到文件
        
        Args:
            content: 完整内容
            tool_name: 工具名称
            timestamp: 时间戳
            metadata: 元数据
        
        Returns:
            文件路径
        """
        # 生成文件名：tool_name_YYYYMMDD_HHMMSS.json
        dt = datetime.datetime.fromisoformat(timestamp)
        filename = f"{tool_name}_{dt.strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = self.tool_result_dir / filename
        
        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# Tool Result: {tool_name}\n")
            f.write(f"# Timestamp: {timestamp}\n")
            if metadata:
                f.write(f"# Metadata: {metadata}\n")
            f.write("-" * 80 + "\n\n")
            f.write(content)
        
        logger.debug(f"Saved tool result to file: {file_path}")
        return file_path

    def cleanup_expired_files(self) -> int:
        """
        清理过期文件
        
        Returns:
            删除的文件数量
        """
        if not self.tool_result_dir.exists():
            return 0
        
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.retention_days)
        deleted_count = 0
        
        for file_path in self.tool_result_dir.iterdir():
            if file_path.is_file():
                # 检查文件修改时间
                file_mtime = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                        logger.debug(f"Deleted expired file: {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to delete file {file_path}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired tool result files")
        
        return deleted_count

    def get_stats(self) -> Dict[str, Any]:
        """
        获取工具结果统计信息
        
        Returns:
            统计信息
        """
        if not self.tool_result_dir.exists():
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "oldest_file": None,
                "newest_file": None
            }
        
        files = list(self.tool_result_dir.glob("*.txt"))
        if not files:
            return {
                "total_files": 0,
                "total_size_bytes": 0,
                "oldest_file": None,
                "newest_file": None
            }
        
        total_size = sum(f.stat().st_size for f in files)
        oldest = min(files, key=lambda f: f.stat().st_mtime)
        newest = max(files, key=lambda f: f.stat().st_mtime)
        
        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "oldest_file": str(oldest.name),
            "newest_file": str(newest.name),
            "retention_days": self.retention_days
        }
