# -*- coding: utf-8 -*-
"""
专用检索器：针对不同类型记忆优化检索策略

借鉴 ReMe 专用检索器设计，实现：
1. PersonalRetriever: 个人记忆检索（偏好、习惯、关系）
2. TaskRetriever: 任务记忆检索（进度、决策、经验）
3. ToolRetriever: 工具记忆检索（工具使用、结果）
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..core.database import HumanThinkingDB, MemoryRecord
from ..search.vector import TFIDFSearchEngine

logger = logging.getLogger(__name__)


class BaseRetriever:
    """检索器基类"""

    def __init__(
        self,
        db: HumanThinkingDB,
        memory_type: str,
        max_results: int = 5,
        min_score: float = 0.1
    ):
        """
        初始化检索器
        
        Args:
            db: 数据库实例
            memory_type: 记忆类型
            max_results: 最大结果数
            min_score: 最低分数阈值
        """
        self.db = db
        self.memory_type = memory_type
        self.max_results = max_results
        self.min_score = min_score

    async def retrieve(
        self,
        query: str,
        agent_id: str,
        target_id: Optional[str] = None,
        user_id: Optional[str] = None,
        **kwargs
    ) -> List[MemoryRecord]:
        """
        检索记忆
        
        Args:
            query: 查询文本
            agent_id: Agent ID
            target_id: 对话对象 ID
            user_id: 用户 ID
            **kwargs: 其他参数
        
        Returns:
            记忆记录列表
        """
        memories = await self.db.search_memories(
            query=query,
            agent_id=agent_id,
            target_id=target_id,
            user_id=user_id,
            max_results=self.max_results,
            min_score=self.min_score
        )
        
        # 过滤记忆类型
        return [m for m in memories if m.memory_type == self.memory_type]


class PersonalRetriever(BaseRetriever):
    """个人记忆检索器：检索用户偏好、习惯、关系"""

    def __init__(
        self,
        db: HumanThinkingDB,
        max_results: int = 5,
        min_score: float = 0.1
    ):
        super().__init__(
            db=db,
            memory_type="personal",
            max_results=max_results,
            min_score=min_score
        )

    async def retrieve(
        self,
        query: str,
        agent_id: str,
        user_id: str,
        target_id: Optional[str] = None,
        include_preferences: bool = True,
        include_habits: bool = True,
        include_relationships: bool = True
    ) -> List[MemoryRecord]:
        """
        检索个人记忆
        
        Args:
            query: 查询文本
            agent_id: Agent ID
            user_id: 用户 ID
            target_id: 对话对象 ID
            include_preferences: 是否包含偏好
            include_habits: 是否包含习惯
            include_relationships: 是否包含关系
        
        Returns:
            个人记忆列表
        """
        # 调用父类检索
        memories = await super().retrieve(
            query=query,
            agent_id=agent_id,
            target_id=target_id,
            user_id=user_id
        )
        
        # 根据标志过滤
        filtered = []
        for memory in memories:
            metadata = memory.metadata or {}
            subtype = metadata.get("subtype", "")
            
            if include_preferences and subtype == "preference":
                filtered.append(memory)
            elif include_habits and subtype == "habit":
                filtered.append(memory)
            elif include_relationships and subtype == "relationship":
                filtered.append(memory)
            elif not subtype:  # 没有子类型，默认包含
                filtered.append(memory)
        
        return filtered

    async def retrieve_user_preferences(
        self,
        agent_id: str,
        user_id: str,
        max_results: int = 10
    ) -> List[MemoryRecord]:
        """检索用户偏好"""
        return await self.db.search_memories(
            query="",
            agent_id=agent_id,
            user_id=user_id,
            max_results=max_results
        )

    async def retrieve_user_habits(
        self,
        agent_id: str,
        user_id: str,
        max_results: int = 10
    ) -> List[MemoryRecord]:
        """检索用户习惯"""
        memories = await self.db.search_memories(
            query="",
            agent_id=agent_id,
            user_id=user_id,
            max_results=max_results
        )
        return [
            m for m in memories
            if m.metadata and m.metadata.get("subtype") == "habit"
        ]


class TaskRetriever(BaseRetriever):
    """任务记忆检索器：检索任务进度、决策、经验"""

    def __init__(
        self,
        db: HumanThinkingDB,
        max_results: int = 5,
        min_score: float = 0.1
    ):
        super().__init__(
            db=db,
            memory_type="task",
            max_results=max_results,
            min_score=min_score
        )

    async def retrieve(
        self,
        query: str,
        agent_id: str,
        target_id: Optional[str] = None,
        user_id: Optional[str] = None,
        include_progress: bool = True,
        include_decisions: bool = True,
        include_lessons: bool = True
    ) -> List[MemoryRecord]:
        """
        检索任务记忆
        
        Args:
            query: 查询文本
            agent_id: Agent ID
            target_id: 对话对象 ID
            user_id: 用户 ID
            include_progress: 是否包含进度
            include_decisions: 是否包含决策
            include_lessons: 是否包含经验
        
        Returns:
            任务记忆列表
        """
        memories = await super().retrieve(
            query=query,
            agent_id=agent_id,
            target_id=target_id,
            user_id=user_id
        )
        
        # 根据标志过滤
        filtered = []
        for memory in memories:
            metadata = memory.metadata or {}
            subtype = metadata.get("subtype", "")
            
            if include_progress and subtype == "progress":
                filtered.append(memory)
            elif include_decisions and subtype == "decision":
                filtered.append(memory)
            elif include_lessons and subtype == "lesson":
                filtered.append(memory)
            elif not subtype:
                filtered.append(memory)
        
        return filtered

    async def retrieve_task_progress(
        self,
        agent_id: str,
        target_id: str,
        max_results: int = 10
    ) -> List[MemoryRecord]:
        """检索任务进度"""
        memories = await self.db.search_memories(
            query="",
            agent_id=agent_id,
            target_id=target_id,
            max_results=max_results
        )
        return [
            m for m in memories
            if m.metadata and m.metadata.get("subtype") == "progress"
        ]

    async def retrieve_decisions(
        self,
        agent_id: str,
        target_id: str,
        max_results: int = 10
    ) -> List[MemoryRecord]:
        """检索历史决策"""
        memories = await self.db.search_memories(
            query="决策",
            agent_id=agent_id,
            target_id=target_id,
            max_results=max_results
        )
        return [
            m for m in memories
            if m.metadata and m.metadata.get("subtype") == "decision"
        ]


class ToolRetriever(BaseRetriever):
    """工具记忆检索器：检索工具使用经验、结果"""

    def __init__(
        self,
        db: HumanThinkingDB,
        max_results: int = 5,
        min_score: float = 0.1
    ):
        super().__init__(
            db=db,
            memory_type="tool",
            max_results=max_results,
            min_score=min_score
        )

    async def retrieve(
        self,
        query: str,
        agent_id: str,
        target_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tool_name: Optional[str] = None
    ) -> List[MemoryRecord]:
        """
        检索工具记忆
        
        Args:
            query: 查询文本
            agent_id: Agent ID
            target_id: 对话对象 ID
            user_id: 用户 ID
            tool_name: 工具名称过滤
        
        Returns:
            工具记忆列表
        """
        memories = await super().retrieve(
            query=query,
            agent_id=agent_id,
            target_id=target_id,
            user_id=user_id
        )
        
        # 按工具名称过滤
        if tool_name:
            return [
                m for m in memories
                if m.metadata and m.metadata.get("tool_name") == tool_name
            ]
        
        return memories

    async def retrieve_tool_usage(
        self,
        agent_id: str,
        tool_name: str,
        max_results: int = 10
    ) -> List[MemoryRecord]:
        """检索特定工具的使用历史"""
        memories = await self.db.search_memories(
            query=tool_name,
            agent_id=agent_id,
            max_results=max_results
        )
        return [
            m for m in memories
            if m.metadata and m.metadata.get("tool_name") == tool_name
        ]

    async def retrieve_tool_errors(
        self,
        agent_id: str,
        tool_name: Optional[str] = None,
        max_results: int = 10
    ) -> List[MemoryRecord]:
        """检索工具错误记录"""
        query = "错误" if not tool_name else f"{tool_name} 错误"
        memories = await self.db.search_memories(
            query=query,
            agent_id=agent_id,
            max_results=max_results
        )
        return [
            m for m in memories
            if m.metadata and m.metadata.get("status") == "error"
        ]
