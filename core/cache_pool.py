# -*- coding: utf-8 -*-
"""HumanThinking Memory Manager - Agent Cache Pool Module

Agent级缓存池，读写分离设计：
- 写缓存：存储当前对话轮次新增的记忆（Write Queue + Session Buffers）
- 读缓存：存储最近已持久化的记忆，供快速检索，避免频繁查询DB
"""

import asyncio
import logging
import time
from collections import deque
from typing import Dict, List, Optional

from .session_buffer import SessionBuffer, MemoryItem, SessionStatus

logger = logging.getLogger(__name__)


class QueueDrainingError(Exception):
    """队列正在刷新中"""
    pass


class AtomicWriteQueue:
    """线程安全的原子写队列（写缓存核心）"""
    
    def __init__(self):
        self._queue: List[MemoryItem] = []
        self._lock = asyncio.Lock()
        self._draining = False
        self._checkpoint: Optional[Dict] = None
        self._last_push_time: float = 0
    
    async def push(self, memory: MemoryItem):
        """原子写入"""
        async with self._lock:
            if self._draining:
                raise QueueDrainingError("Queue is currently draining")
            self._queue.append(memory)
            self._last_push_time = time.time()
    
    async def drain(self) -> List[MemoryItem]:
        """原子批量获取"""
        async with self._lock:
            if self._draining:
                return []
            
            self._draining = True
            
            self._checkpoint = {
                'timestamp': time.time(),
                'queue_snapshot': self._queue.copy(),
                'queue_size': len(self._queue)
            }
            
            result = self._queue.copy()
            self._queue.clear()
            
            return result
    
    async def release(self):
        """释放刷新锁"""
        async with self._lock:
            self._draining = False
    
    async def extend(self, items: List[MemoryItem]):
        """扩展队列（回滚用）"""
        async with self._lock:
            self._queue.extend(items)
    
    def size(self) -> int:
        return len(self._queue)
    
    def total_chars(self) -> int:
        return sum(m.char_count for m in self._queue)
    
    def get_last_push_time(self) -> float:
        """获取最后一次 push 的时间戳"""
        return self._last_push_time
    
    def get_checkpoint(self) -> Optional[Dict]:
        """获取当前队列的创建时间戳（用于判断是否老化）"""
        if self._checkpoint:
            return self._checkpoint
        # 如果没有 checkpoint，使用最后一次 push 时间
        if self._last_push_time > 0:
            return {"timestamp": self._last_push_time}
        return None


class ReadCache:
    """读缓存 - LRU 淘汰 + 会话冷却清理
    
    存储最近已持久化到数据库的记忆，供快速检索。
    目的：避免每次搜索都查询数据库，扩充有效上下文大小。
    
    清理策略：
    1. LRU 淘汰：超出容量时淘汰最旧数据
    2. 会话冷却：清理长时间不活跃会话的缓存（默认 10 分钟）
    
    默认 500 条 / 512KB，覆盖约 25-40 轮对话记忆。
    """
    
    def __init__(
        self,
        max_items: int = 500,
        max_chars: int = 512 * 1024,
        session_idle_timeout: int = 600
    ):
        """
        Args:
            max_items: 最大记忆数量（默认 500 条）
            max_chars: 最大字符数（默认 512KB，约 256K tokens）
            session_idle_timeout: 会话空闲超时秒数（默认 600s = 10 分钟）
        """
        self._cache: deque = deque()
        self._lock = asyncio.Lock()
        self._max_items = max_items
        self._max_chars = max_chars
        self._total_chars = 0
        
        # 会话跟踪：{session_id: 最后访问时间戳}
        self._session_last_access: Dict[str, float] = {}
        self._session_idle_timeout = session_idle_timeout
    
    async def add_batch(self, memories: List[MemoryItem]):
        """批量添加已持久化的记忆到读缓存"""
        async with self._lock:
            for m in memories:
                self._cache.append(m)
                self._total_chars += m.char_count
                # 更新会话最后访问时间
                self._session_last_access[m.session_id] = time.time()
            
            self._evict_if_needed()
    
    def _evict_if_needed(self):
        """淘汰旧数据，保持缓存大小在限制内"""
        while (
            len(self._cache) > self._max_items or
            self._total_chars > self._max_chars
        ) and self._cache:
            old = self._cache.popleft()
            self._total_chars -= old.char_count
        
        # 清理无对应缓存项的会话记录
        active_sessions = set(m.session_id for m in self._cache)
        for sid in list(self._session_last_access.keys()):
            if sid not in active_sessions:
                del self._session_last_access[sid]
    
    async def search(self, query: str, session_id: Optional[str] = None) -> List[MemoryItem]:
        """在读缓存中搜索，更新访问时间"""
        results = []
        query_lower = query.lower()
        
        for m in self._cache:
            if session_id and m.session_id != session_id:
                continue
            if query_lower in m.content.lower():
                results.append(m)
        
        # 更新访问时间
        if results:
            now = time.time()
            for m in results:
                self._session_last_access[m.session_id] = now
        
        return results
    
    async def evict_inactive_sessions(self) -> int:
        """
        清理不活跃会话的缓存
        
        当会话超过 idle_timeout 没有新操作时，清除其对应的读缓存。
        由 post_memory_operation hook 在对话结束时调用。
        
        Returns:
            清理的记忆数量
        """
        async with self._lock:
            now = time.time()
            inactive_sessions = set()
            
            for sid, last_access in self._session_last_access.items():
                if now - last_access > self._session_idle_timeout:
                    inactive_sessions.add(sid)
            
            if not inactive_sessions:
                return 0
            
            # 从缓存中移除不活跃会话的记忆
            initial_size = len(self._cache)
            new_cache = deque()
            new_total_chars = 0
            
            for m in self._cache:
                if m.session_id in inactive_sessions:
                    continue
                new_cache.append(m)
                new_total_chars += m.char_count
            
            removed_count = initial_size - len(new_cache)
            self._cache = new_cache
            self._total_chars = new_total_chars
            
            # 清理会话记录
            for sid in inactive_sessions:
                self._session_last_access.pop(sid, None)
            
            if removed_count > 0:
                logger.debug(
                    f"ReadCache evicted {removed_count} memories "
                    f"from {len(inactive_sessions)} inactive sessions"
                )
            
            return removed_count
    
    async def clear(self):
        """清空读缓存"""
        async with self._lock:
            self._cache.clear()
            self._total_chars = 0
            self._session_last_access.clear()
    
    def size(self) -> int:
        return len(self._cache)
    
    def total_chars(self) -> int:
        return self._total_chars


class AgentCachePool:
    """Agent级缓存池 - 读写分离"""
    
    def __init__(
        self,
        agent_id: str,
        db,
        max_queue_size: int = 10,
        max_chars: int = 64 * 1024,
        session_idle_timeout: int = 180,
        max_session_size: int = 100,
        max_session_chars: int = 512 * 1024,
        max_read_cache_items: int = 500,
        max_read_cache_chars: int = 512 * 1024,
        read_cache_idle_timeout: int = 600,
        flush_interval: int = 60
    ):
        self.agent_id = agent_id
        self.db = db
        self._session_idle_timeout = session_idle_timeout  # 会话空闲超时（秒）
        self._last_flush_time: float = 0
        self._flush_interval = flush_interval  # 后台 flush 间隔兜底（秒）
        
        # 写缓存
        self._sessions: Dict[str, SessionBuffer] = {}
        self._write_queue = AtomicWriteQueue()
        
        # 读缓存（最近已持久化的记忆）
        self._read_cache = ReadCache(
            max_items=max_read_cache_items,
            max_chars=max_read_cache_chars,
            session_idle_timeout=read_cache_idle_timeout
        )
        
        self._flush_lock = asyncio.Lock()
        self._lock = asyncio.Lock()
        
        # 后台兜底刷新任务
        self._auto_flush_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动缓存池"""
        self._auto_flush_task = asyncio.create_task(self._auto_flush_loop())
        logger.info(f"AgentCachePool started for agent {self.agent_id}")
    
    async def close(self):
        """关闭缓存池"""
        if self._auto_flush_task and not self._auto_flush_task.done():
            self._auto_flush_task.cancel()
            try:
                await self._auto_flush_task
            except asyncio.CancelledError:
                pass
        
        for session_id in list(self._sessions.keys()):
            await self.close_session(session_id)
        
        await self.flush()
        logger.info(f"AgentCachePool closed for agent {self.agent_id}")
    
    async def _auto_flush_loop(self):
        """
        后台兜底刷新循环
        
        作用：如果用户长时间不发消息，_idle_check 无法触发，
        此任务确保写缓存不会永远滞留内存。
        
        每 60 秒检查一次，如果写队列有数据且超过 30 秒没更新，则 flush。
        """
        try:
            while True:
                await asyncio.sleep(self._flush_interval)
                
                if self._write_queue.size() == 0:
                    continue
                
                now = time.time()
                checkpoint = self._write_queue.get_checkpoint()
                if checkpoint and (now - checkpoint["timestamp"]) > self._session_idle_timeout:
                    logger.debug(
                        f"Auto-flushing {self._write_queue.size()} stale memories "
                        f"(age={now - checkpoint['timestamp']:.0f}s)"
                    )
                    await self.flush()
                    await self._read_cache.evict_inactive_sessions()
        except asyncio.CancelledError:
            pass
    
    # ====== 写入路径 ======
    
    async def store(self, memory: MemoryItem, session_id: str) -> str:
        """
        存储记忆到写缓存
        
        新对话开始时会先 flush 上一轮的缓存，确保完整对话不会截断。
        
        Args:
            memory: 记忆项
            session_id: Session ID
        
        Returns:
            temp_id: 临时记忆 ID
        """
        if memory.agent_id != self.agent_id:
            raise ValueError(f"Agent ID mismatch: {memory.agent_id} != {self.agent_id}")
        
        # 新消息到达时，如果上一轮缓存已空闲，先 flush
        now = time.time()
        if now - self._last_flush_time > self._session_idle_timeout * 2:
            if self._write_queue.size() > 0:
                await self.flush()
                await self._read_cache.evict_inactive_sessions()
            self._last_flush_time = now
        
        session = await self._get_or_create_session(session_id)
        
        success = await session.add(memory)
        if not success:
            raise Exception(f"Failed to add memory to session {session_id}")
        
        await self._write_queue.push(memory)
        
        logger.debug(
            f"Memory cached: temp_id={memory.temp_id}, session={session_id}, "
            f"queue_size={self._write_queue.size()}"
        )
        return memory.temp_id
    
    async def flush_on_turn_end(self) -> int:
        """
        每轮对话结束时调用，通过 runner.py finally 块的 post_memory_operation 钩子触发。
        
        流程：
        1. 检查写队列是否有数据
        2. 清理不活跃的读缓存
        3. 执行 flush 写入数据库
        """
        if self._write_queue.size() == 0:
            return 0
        
        # 清理过期读缓存
        await self._read_cache.evict_inactive_sessions()
        
        return await self.flush()
    
    async def flush(self) -> int:
        """
        安全的批量刷新
        
        流程：
        1. 从写队列获取数据快照
        2. 写入数据库
        3. 同步到读缓存（供后续快速检索）
        4. 清理写缓存（Session Buffer + 写队列）
        """
        async with self._flush_lock:
            batch = await self._write_queue.drain()
            if not batch:
                return 0
            
            await asyncio.sleep(0.01)
            
            try:
                memories_data = [
                    {
                        "agent_id": m.agent_id,
                        "session_id": m.session_id,
                        "user_id": m.user_id,
                        "role": m.role,
                        "content": m.content,
                        "importance": m.importance,
                        "memory_type": m.memory_type,
                        "metadata": m.metadata,
                        "tags": m.tags
                    }
                    for m in batch
                ]
                
                await self.db.batch_insert(memories_data, sync=True)
                
                # 同步到读缓存
                await self._read_cache.add_batch(batch)
                
                # 清理写缓存
                affected_sessions = set(m.session_id for m in batch)
                for sid in affected_sessions:
                    if sid in self._sessions:
                        await self._sessions[sid].mark_flushed()
                
                logger.info(
                    f"Flushed {len(batch)} memories to DB, "
                    f"read cache now has {self._read_cache.size()} items"
                )
                return len(batch)
                
            except Exception as e:
                await self._write_queue.extend(batch)
                logger.error(f"Flush failed, rolled back: {e}")
                raise
            finally:
                await self._write_queue.release()
    
    # ====== 读取路径 ======
    
    async def search(self, query: str, session_id: Optional[str] = None) -> List[MemoryItem]:
        """
        搜索记忆 - 读写分离
        
        优先级：
        1. 先搜索当前 session
        2. 如果当前 session 无结果，跨 session 搜索
        3. 写缓存（当前轮次新增，尚未持久化）
        4. 读缓存（最近已持久化，快速检索）
        """
        results = []
        seen_ids = set()
        
        # 1. 搜索当前 session 的写缓存
        for sid, session in self._sessions.items():
            if session_id and sid != session_id:
                continue
            
            for memory in session.get_memories():
                if memory.temp_id not in seen_ids and query.lower() in memory.content.lower():
                    results.append(memory)
                    seen_ids.add(memory.temp_id)
        
        # 2. 搜索当前 session 的写队列
        for memory in self._write_queue._queue:
            if memory.temp_id not in seen_ids:
                if session_id and memory.session_id != session_id:
                    continue
                if query.lower() in memory.content.lower():
                    results.append(memory)
                    seen_ids.add(memory.temp_id)
        
        # 3. 搜索当前 session 的读缓存
        if session_id:
            read_results = await self._read_cache.search(query, session_id)
            for memory in read_results:
                if memory.temp_id not in seen_ids:
                    results.append(memory)
                    seen_ids.add(memory.temp_id)
        
        # 4. 如果当前 session 无结果，跨 session 搜索
        if not results and session_id:
            # 跨 session 搜索写缓存
            for sid, session in self._sessions.items():
                if sid == session_id:
                    continue
                for memory in session.get_memories():
                    if memory.temp_id not in seen_ids and query.lower() in memory.content.lower():
                        results.append(memory)
                        seen_ids.add(memory.temp_id)
            
            # 跨 session 搜索写队列
            for memory in self._write_queue._queue:
                if memory.temp_id not in seen_ids and memory.session_id != session_id:
                    if query.lower() in memory.content.lower():
                        results.append(memory)
                        seen_ids.add(memory.temp_id)
            
            # 跨 session 搜索读缓存
            cross_session_read = await self._read_cache.search(query, None)
            for memory in cross_session_read:
                if memory.temp_id not in seen_ids:
                    results.append(memory)
                    seen_ids.add(memory.temp_id)
        
        return results
    
    # ====== Session 管理 ======
    
    async def close_session(self, session_id: str) -> None:
        """关闭 Session"""
        async with self._lock:
            if session_id in self._sessions:
                session = self._sessions[session_id]
                
                memories = await session.close()
                
                if memories:
                    for m in memories:
                        await self._write_queue.push(m)
                    
                    await self.flush()
                
                del self._sessions[session_id]
                logger.info(f"Session {session_id} closed and flushed")
    
    async def get_session(self, agent_id: str, session_id: str) -> Optional[SessionBuffer]:
        """获取 Session Buffer"""
        if agent_id != self.agent_id:
            raise ValueError(f"Agent ID mismatch")
        
        return self._sessions.get(session_id)
    
    async def _get_or_create_session(self, session_id: str) -> SessionBuffer:
        """获取或创建 Session Buffer"""
        async with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = SessionBuffer(
                    session_id=session_id,
                    agent_id=self.agent_id,
                    max_size=100,
                    max_chars=512 * 1024
                )
                logger.info(f"Created new session buffer: {session_id}")
            
            return self._sessions[session_id]
    
    # ====== 统计 ======
    
    def get_stats(self) -> Dict:
        """获取缓存池统计"""
        return {
            "agent_id": self.agent_id,
            "write_cache": {
                "session_count": len(self._sessions),
                "queue_size": self._write_queue.size(),
                "queue_chars": self._write_queue.total_chars(),
                "sessions": {
                    sid: s.get_stats() 
                    for sid, s in self._sessions.items()
                }
            },
            "read_cache": {
                "item_count": self._read_cache.size(),
                "total_chars": self._read_cache.total_chars()
            }
        }
