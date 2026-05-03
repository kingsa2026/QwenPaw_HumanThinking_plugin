# -*- coding: utf-8 -*-
"""HumanThinking Memory Manager - Session Buffer Module

会话缓冲区，保证会话完整性和线程安全
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """会话状态"""
    ACTIVE = "active"
    DRAINING = "draining"
    CLOSED = "closed"


@dataclass
class MemoryItem:
    """记忆项"""
    content: str
    agent_id: str
    session_id: str
    user_id: Optional[str] = None
    target_id: Optional[str] = None  # 对话对象ID，区分不同Agent/用户
    role: str = "assistant"
    importance: int = 3
    memory_type: str = "general"
    metadata: Dict = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    temp_id: str = ""
    created_at: float = field(default_factory=time.time)
    
    def __post_init__(self):
        if not self.temp_id:
            self.temp_id = f"temp_{int(self.created_at)}_{id(self)}"
    
    @property
    def char_count(self) -> int:
        return len(self.content)


class SessionBuffer:
    """会话缓冲（线程安全）"""
    
    def __init__(
        self,
        session_id: str,
        agent_id: str,
        max_size: int = 100,
        max_chars: int = 512 * 1024  # 512KB
    ):
        self.session_id = session_id
        self.agent_id = agent_id
        self.max_size = max_size
        self.max_chars = max_chars
        
        self._buffer: List[MemoryItem] = []
        self._lock = asyncio.Lock()
        self.status = SessionStatus.ACTIVE
        self.created_at = time.time()
        self.last_activity = time.time()
        self.total_chars = 0
    
    async def add(self, memory: MemoryItem) -> bool:
        """
        线程安全添加记忆
        
        Returns:
            是否成功添加
        """
        async with self._lock:
            if self.status != SessionStatus.ACTIVE:
                logger.warning(f"Session {self.session_id} is not active, status={self.status}")
                return False
            
            # 验证 agent_id 匹配
            if memory.agent_id != self.agent_id:
                raise ValueError(
                    f"Agent ID mismatch: {memory.agent_id} != {self.agent_id}"
                )
            
            # 验证 session_id 匹配
            if memory.session_id != self.session_id:
                raise ValueError(
                    f"Session ID mismatch: {memory.session_id} != {self.session_id}"
                )
            
            # 检查阈值
            if len(self._buffer) >= self.max_size:
                logger.warning(f"Session buffer size limit reached: {self.max_size}")
                return False
            
            if self.total_chars + memory.char_count >= self.max_chars:
                logger.warning(f"Session buffer char limit reached: {self.max_chars}")
                return False
            
            self._buffer.append(memory)
            self.total_chars += memory.char_count
            self.last_activity = time.time()
            
            logger.debug(
                f"Added memory to session {self.session_id}: "
                f"size={len(self._buffer)}, chars={self.total_chars}"
            )
            return True
    
    async def close(self) -> List[MemoryItem]:
        """
        关闭会话并获取所有记忆
        
        Returns:
            所有待写入的记忆
        """
        async with self._lock:
            if self.status == SessionStatus.CLOSED:
                return []
            
            self.status = SessionStatus.CLOSED
            memories = self._buffer.copy()
            self._buffer.clear()
            self.total_chars = 0
            
            logger.info(
                f"Session {self.session_id} closed, "
                f"collected {len(memories)} memories"
            )
            return memories
    
    async def mark_flushed(self) -> bool:
        """
        标记 Session 已刷新，清理已写入数据库的记忆
        
        Returns:
            是否成功清理
        """
        async with self._lock:
            flushed_count = len(self._buffer)
            self._buffer.clear()
            self.total_chars = 0
            self.status = SessionStatus.ACTIVE
            logger.debug(f"Session {self.session_id} flushed, cleared {flushed_count} memories")
            return True
    
    async def remove_by_temp_ids(self, temp_ids: set) -> int:
        """
        按temp_id精确移除已写入DB的记忆，保留未写入的新记忆
        
        Args:
            temp_ids: 已写入DB的记忆temp_id集合
            
        Returns:
            移除的记忆数量
        """
        async with self._lock:
            new_buffer = []
            removed = 0
            new_total_chars = 0
            
            for m in self._buffer:
                if m.temp_id in temp_ids:
                    removed += 1
                else:
                    new_buffer.append(m)
                    new_total_chars += m.char_count
            
            self._buffer = new_buffer
            self.total_chars = new_total_chars
            
            if removed > 0:
                logger.debug(
                    f"Session {self.session_id}: removed {removed} flushed memories, "
                    f"remaining {len(self._buffer)} memories"
                )
            
            return removed
    
    async def mark_draining(self) -> bool:
        """
        标记为等待刷新状态
        
        Returns:
            是否成功标记
        """
        async with self._lock:
            if self.status != SessionStatus.ACTIVE:
                return False
            
            self.status = SessionStatus.DRAINING
            logger.debug(f"Session {self.session_id} marked as draining")
            return True
    
    def is_silent(self, threshold: int = 300) -> bool:
        """
        静默检测
        
        Args:
            threshold: 静默阈值（秒）
        
        Returns:
            是否静默超过阈值
        """
        return (time.time() - self.last_activity) > threshold
    
    def get_buffer_size(self) -> int:
        """获取缓冲区大小"""
        return len(self._buffer)
    
    def get_buffer_chars(self) -> int:
        """获取缓冲区字符数"""
        return self.total_chars
    
    def get_memories(self) -> List[MemoryItem]:
        """获取所有记忆（非线程安全，仅供内部使用）"""
        return self._buffer.copy()
    
    def get_stats(self) -> Dict:
        """获取缓冲统计"""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "status": self.status.value,
            "buffer_size": len(self._buffer),
            "buffer_chars": self.total_chars,
            "max_size": self.max_size,
            "max_chars": self.max_chars,
            "created_at": self.created_at,
            "last_activity": self.last_activity,
            "is_silent_5min": self.is_silent(300)
        }
