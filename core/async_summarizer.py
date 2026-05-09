# -*- coding: utf-8 -*-
"""
异步总结器：后台生成记忆总结

借鉴 ReMe AsyncSummarizer 设计，实现：
1. 不阻塞主流程的记忆总结
2. 自动管理任务生命周期
3. 任务结果收集和日志记录
4. 支持多种总结策略
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from typing import Any, Callable, Dict, List, Optional, Awaitable

from .database import MemoryRecord

logger = logging.getLogger(__name__)


class AsyncSummarizer:
    """异步总结器"""

    def __init__(
        self,
        summarize_func: Optional[Callable] = None,
        max_concurrent_tasks: int = 3,
        auto_cleanup: bool = True
    ):
        """
        初始化异步总结器
        
        Args:
            summarize_func: 总结函数，接收记忆列表，返回总结文本
            max_concurrent_tasks: 最大并发任务数
            auto_cleanup: 是否自动清理已完成任务
        """
        self.summarize_func = summarize_func
        self.max_concurrent_tasks = max_concurrent_tasks
        self.auto_cleanup = auto_cleanup
        self._summary_tasks: List[asyncio.Task] = []
        self._task_results: List[Dict[str, Any]] = []
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

    def add_summary_task(
        self,
        memories: List[MemoryRecord],
        task_id: Optional[str] = None,
        callback: Optional[Callable] = None,
        **kwargs
    ) -> str:
        """
        添加异步总结任务
        
        Args:
            memories: 待总结的记忆列表
            task_id: 任务ID（可选，自动生成）
            callback: 任务完成后的回调函数
            **kwargs: 传递给总结函数的额外参数
        
        Returns:
            task_id: 任务ID
        """
        if not self.summarize_func:
            raise ValueError("summarize_func is required")
        
        # 清理已完成的任务
        if self.auto_cleanup:
            self._cleanup_done_tasks()
        
        # 检查并发限制
        active_tasks = len([t for t in self._summary_tasks if not t.done()])
        if active_tasks >= self.max_concurrent_tasks:
            logger.warning(
                f"Max concurrent tasks ({self.max_concurrent_tasks}) reached, "
                f"skipping new summary task"
            )
            return ""
        
        # 生成任务ID
        if not task_id:
            task_id = f"summary_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self._summary_tasks)}"
        
        # 创建异步任务
        task = asyncio.create_task(
            self._run_summary_task(task_id, memories, callback, **kwargs)
        )
        self._summary_tasks.append(task)
        
        logger.info(f"Added summary task: {task_id}, memories={len(memories)}")
        return task_id

    async def _run_summary_task(
        self,
        task_id: str,
        memories: List[MemoryRecord],
        callback: Optional[Callable],
        **kwargs
    ) -> Dict[str, Any]:
        """
        运行单个总结任务
        
        Args:
            task_id: 任务ID
            memories: 记忆列表
            callback: 回调函数
            **kwargs: 额外参数
        
        Returns:
            任务结果
        """
        async with self._semaphore:
            try:
                logger.info(f"Starting summary task: {task_id}")
                
                # 执行总结
                summary = await self.summarize_func(memories, **kwargs)
                
                result = {
                    "task_id": task_id,
                    "status": "success",
                    "summary": summary,
                    "memory_count": len(memories),
                    "completed_at": datetime.datetime.now().isoformat(),
                    **kwargs
                }
                
                # 存储结果
                self._task_results.append(result)
                
                # 执行回调
                if callback:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(result)
                        else:
                            callback(result)
                    except Exception as e:
                        logger.error(f"Callback error for task {task_id}: {e}")
                
                logger.info(f"Summary task completed: {task_id}")
                return result
                
            except asyncio.CancelledError:
                result = {
                    "task_id": task_id,
                    "status": "cancelled",
                    "completed_at": datetime.datetime.now().isoformat()
                }
                self._task_results.append(result)
                logger.warning(f"Summary task cancelled: {task_id}")
                return result
                
            except Exception as e:
                result = {
                    "task_id": task_id,
                    "status": "error",
                    "error": str(e),
                    "completed_at": datetime.datetime.now().isoformat()
                }
                self._task_results.append(result)
                logger.error(f"Summary task failed: {task_id}, error={e}")
                return result

    def _cleanup_done_tasks(self):
        """清理已完成的任务"""
        remaining_tasks = []
        for task in self._summary_tasks:
            if task.done():
                if task.cancelled():
                    logger.debug("Summary task was cancelled")
                elif task.exception():
                    logger.debug(f"Summary task failed: {task.exception()}")
                else:
                    logger.debug(f"Summary task completed: {task.result()}")
            else:
                remaining_tasks.append(task)
        
        self._summary_tasks = remaining_tasks

    async def await_all_tasks(self) -> List[Dict[str, Any]]:
        """
        等待所有总结任务完成
        
        Returns:
            所有任务的结果列表
        """
        if not self._summary_tasks:
            return self._task_results
        
        # 等待所有任务完成
        results = await asyncio.gather(*self._summary_tasks, return_exceptions=True)
        
        # 处理结果
        final_results = []
        for i, result in enumerate(results):
            task = self._summary_tasks[i]
            task_id = f"task_{i}"
            
            if isinstance(result, Exception):
                final_results.append({
                    "task_id": task_id,
                    "status": "error",
                    "error": str(result)
                })
            elif isinstance(result, dict):
                final_results.append(result)
            else:
                final_results.append({
                    "task_id": task_id,
                    "status": "success",
                    "result": result
                })
        
        # 清理任务列表
        self._summary_tasks.clear()
        
        logger.info(f"All summary tasks completed: {len(final_results)} tasks")
        return final_results

    def get_task_status(self) -> Dict[str, Any]:
        """
        获取任务状态
        
        Returns:
            任务状态信息
        """
        active_tasks = [t for t in self._summary_tasks if not t.done()]
        done_tasks = [t for t in self._summary_tasks if t.done()]
        
        return {
            "total_tasks": len(self._summary_tasks),
            "active_tasks": len(active_tasks),
            "done_tasks": len(done_tasks),
            "completed_results": len(self._task_results),
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "recent_results": self._task_results[-5:] if self._task_results else []
        }

    def cancel_all_tasks(self) -> int:
        """
        取消所有进行中的任务
        
        Returns:
            取消的任务数量
        """
        cancelled_count = 0
        for task in self._summary_tasks:
            if not task.done():
                task.cancel()
                cancelled_count += 1
        
        logger.info(f"Cancelled {cancelled_count} summary tasks")
        return cancelled_count

    def get_recent_summaries(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近的总结结果
        
        Args:
            limit: 返回数量限制
        
        Returns:
            最近的总结结果列表
        """
        successful_results = [
            r for r in self._task_results
            if r.get("status") == "success"
        ]
        return successful_results[-limit:]
