"""
记忆生命周期管理器 - 管理记忆从创建到删除的完整生命周期

实现记忆的完整生命周期管理：
创建 → 活跃 → 冷藏 → 归档 → 删除

基于记忆温度系统和访问频率自动推进记忆状态。

Author: Qwen3.6-Plus
Version: 1.0.0-beta0.1
"""

import asyncio
import time
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta


class MemoryState(Enum):
    """记忆状态"""
    ACTIVE = "active"           # 活跃 - 新创建或频繁访问
    COOLING = "cooling"         # 冷藏 - 访问减少，温度下降
    ARCHIVED = "archived"       # 归档 - 长期不访问，但保留
    DELETED = "deleted"         # 删除 - 标记删除（软删除）


@dataclass
class LifecycleConfig:
    """生命周期配置"""
    # 活跃 → 冷藏阈值
    active_to_cooling_days: float = 7.0          # 多少天不访问转为冷藏
    active_access_count_threshold: int = 3       # 最少访问次数保持活跃
    
    # 冷藏 → 归档阈值
    cooling_to_archived_days: float = 30.0       # 多少天不访问转为归档
    cooling_access_count_threshold: int = 1      # 最少访问次数保持冷藏
    
    # 归档 → 删除阈值
    archived_to_deleted_days: float = 365.0      # 多少天不访问转为删除
    archived_keep_min_count: int = 1             # 最少保留记忆数量
    
    # 特殊保护
    protected_tags: List[str] = field(default_factory=lambda: ["important", "permanent"])
    protected_max_age_days: float = 180.0        # 保护记忆最大年龄
    
    # 检查间隔
    lifecycle_check_interval_hours: float = 24.0  # 生命周期检查间隔


@dataclass
class MemoryLifecycleRecord:
    """记忆生命周期记录"""
    memory_id: int
    state: MemoryState
    created_at: datetime
    last_accessed_at: datetime
    access_count: int
    state_transitions: List[Tuple[datetime, MemoryState, MemoryState]] = field(default_factory=list)


class MemoryLifecycle:
    """
    记忆生命周期管理器
    
    管理记忆的完整生命周期：
    1. 创建：新记忆初始化为 ACTIVE 状态
    2. 活跃：频繁访问的记忆保持 ACTIVE
    3. 冷藏：访问减少的记忆转为 COOLING
    4. 归档：长期不访问的记忆转为 ARCHIVED
    5. 删除：超长不访问的记忆标记 DELETED
    
    支持：
    - 自动状态转换
    - 手动状态转换
    - 特殊保护机制
    - 生命周期统计
    """

    def __init__(
        self,
        config: Optional[LifecycleConfig] = None,
        get_memory_func: Optional[Callable] = None,
        update_memory_func: Optional[Callable] = None,
        delete_memory_func: Optional[Callable] = None
    ):
        """
        初始化生命周期管理器
        
        Args:
            config: 生命周期配置
            get_memory_func: 获取记忆的函数 (memory_id) -> MemoryRecord
            update_memory_func: 更新记忆的函数 (memory_id, **kwargs)
            delete_memory_func: 删除记忆的函数 (memory_id)
        """
        self.config = config or LifecycleConfig()
        self.get_memory_func = get_memory_func
        self.update_memory_func = update_memory_func
        self.delete_memory_func = delete_memory_func
        
        # 生命周期记录缓存
        self._lifecycle_records: Dict[int, MemoryLifecycleRecord] = {}
        
        # 后台任务
        self._lifecycle_task: Optional[asyncio.Task] = None
        self._running = False
    
    def register_memory(
        self,
        memory_id: int,
        created_at: Optional[datetime] = None
    ) -> MemoryLifecycleRecord:
        """
        注册新记忆到生命周期管理
        
        Args:
            memory_id: 记忆 ID
            created_at: 创建时间（默认现在）
            
        Returns:
            生命周期记录
        """
        now = created_at or datetime.now()
        
        record = MemoryLifecycleRecord(
            memory_id=memory_id,
            state=MemoryState.ACTIVE,
            created_at=now,
            last_accessed_at=now,
            access_count=0
        )
        
        self._lifecycle_records[memory_id] = record
        return record
    
    def record_access(
        self,
        memory_id: int,
        access_time: Optional[datetime] = None
    ) -> Optional[MemoryLifecycleRecord]:
        """
        记录记忆访问
        
        Args:
            memory_id: 记忆 ID
            access_time: 访问时间（默认现在）
            
        Returns:
            更新后的生命周期记录，如果记忆不存在返回 None
        """
        if memory_id not in self._lifecycle_records:
            return None
        
        record = self._lifecycle_records[memory_id]
        now = access_time or datetime.now()
        
        record.last_accessed_at = now
        record.access_count += 1
        
        # 如果记忆被归档，访问后恢复为活跃
        if record.state == MemoryState.ARCHIVED:
            old_state = record.state
            record.state = MemoryState.ACTIVE
            record.state_transitions.append((now, old_state, MemoryState.ACTIVE))
            
            # 更新数据库状态
            if self.update_memory_func:
                self.update_memory_func(memory_id, state="active")
        
        # 如果记忆在冷藏，访问后可能恢复为活跃
        elif record.state == MemoryState.COOLING:
            if record.access_count >= self.config.active_access_count_threshold:
                old_state = record.state
                record.state = MemoryState.ACTIVE
                record.state_transitions.append((now, old_state, MemoryState.ACTIVE))
                
                if self.update_memory_func:
                    self.update_memory_func(memory_id, state="active")
        
        return record
    
    async def check_and_update_lifecycle(self) -> Dict[str, int]:
        """
        检查并更新所有记忆的生命周期状态
        
        Returns:
            状态转换统计 {from_state_to_state: count}
        """
        stats = {
            "active_to_cooling": 0,
            "cooling_to_archived": 0,
            "archived_to_deleted": 0,
            "protected": 0,
            "total_checked": 0
        }
        
        now = datetime.now()
        
        for memory_id, record in list(self._lifecycle_records.items()):
            stats["total_checked"] += 1
            
            # 检查是否受保护
            if self._is_protected(record, now):
                stats["protected"] += 1
                continue
            
            # 状态转换
            old_state = record.state
            
            if record.state == MemoryState.ACTIVE:
                if self._should_cool(record, now):
                    record.state = MemoryState.COOLING
                    record.state_transitions.append((now, old_state, MemoryState.COOLING))
                    stats["active_to_cooling"] += 1
                    
                    if self.update_memory_func:
                        self.update_memory_func(memory_id, state="cooling")
            
            elif record.state == MemoryState.COOLING:
                if self._should_archive(record, now):
                    record.state = MemoryState.ARCHIVED
                    record.state_transitions.append((now, old_state, MemoryState.ARCHIVED))
                    stats["cooling_to_archived"] += 1
                    
                    if self.update_memory_func:
                        self.update_memory_func(memory_id, state="archived")
            
            elif record.state == MemoryState.ARCHIVED:
                if self._should_delete(record, now):
                    record.state = MemoryState.DELETED
                    record.state_transitions.append((now, old_state, MemoryState.DELETED))
                    stats["archived_to_deleted"] += 1
                    
                    if self.delete_memory_func:
                        self.delete_memory_func(memory_id)
                    else:
                        # 软删除：从生命周期记录中移除
                        del self._lifecycle_records[memory_id]
        
        return stats
    
    def _should_cool(
        self,
        record: MemoryLifecycleRecord,
        now: datetime
    ) -> bool:
        """检查记忆是否应该转为冷藏"""
        days_since_access = (now - record.last_accessed_at).total_seconds() / 86400.0
        return (
            days_since_access >= self.config.active_to_cooling_days and
            record.access_count < self.config.active_access_count_threshold
        )
    
    def _should_archive(
        self,
        record: MemoryLifecycleRecord,
        now: datetime
    ) -> bool:
        """检查记忆是否应该转为归档"""
        days_since_access = (now - record.last_accessed_at).total_seconds() / 86400.0
        return (
            days_since_access >= self.config.cooling_to_archived_days and
            record.access_count < self.config.cooling_access_count_threshold
        )
    
    def _should_delete(
        self,
        record: MemoryLifecycleRecord,
        now: datetime
    ) -> bool:
        """检查记忆是否应该删除"""
        days_since_access = (now - record.last_accessed_at).total_seconds() / 86400.0
        
        # 检查最小保留数量
        archived_count = sum(
            1 for r in self._lifecycle_records.values()
            if r.state == MemoryState.ARCHIVED
        )
        
        if archived_count <= self.config.archived_keep_min_count:
            return False
        
        return days_since_access >= self.config.archived_to_deleted_days
    
    def _is_protected(
        self,
        record: MemoryLifecycleRecord,
        now: datetime
    ) -> bool:
        """检查记忆是否受保护"""
        # 检查年龄
        age_days = (now - record.created_at).total_seconds() / 86400.0
        if age_days > self.config.protected_max_age_days:
            return False
        
        # 检查标签（需要从数据库获取记忆）
        if self.get_memory_func:
            memory = self.get_memory_func(record.memory_id)
            if memory and hasattr(memory, 'tags'):
                for tag in self.config.protected_tags:
                    if tag in memory.tags:
                        return True
        
        return False
    
    def manually_transition(
        self,
        memory_id: int,
        new_state: MemoryState,
        reason: str = "manual"
    ) -> bool:
        """
        手动转换记忆状态
        
        Args:
            memory_id: 记忆 ID
            new_state: 目标状态
            reason: 转换原因
            
        Returns:
            是否成功转换
        """
        if memory_id not in self._lifecycle_records:
            return False
        
        record = self._lifecycle_records[memory_id]
        old_state = record.state
        
        record.state = new_state
        record.state_transitions.append((datetime.now(), old_state, new_state))
        
        # 更新数据库
        if self.update_memory_func:
            self.update_memory_func(memory_id, state=new_state.value)
        
        return True
    
    def get_lifecycle_stats(self) -> Dict[str, Any]:
        """
        获取生命周期统计信息
        
        Returns:
            统计信息
        """
        stats = {
            "total_memories": len(self._lifecycle_records),
            "by_state": {
                "active": 0,
                "cooling": 0,
                "archived": 0,
                "deleted": 0
            },
            "avg_age_days": 0.0,
            "avg_access_count": 0.0
        }
        
        if not self._lifecycle_records:
            return stats
        
        total_age = 0.0
        total_access = 0
        now = datetime.now()
        
        for record in self._lifecycle_records.values():
            state_name = record.state.value
            stats["by_state"][state_name] = stats["by_state"].get(state_name, 0) + 1
            
            age_days = (now - record.created_at).total_seconds() / 86400.0
            total_age += age_days
            total_access += record.access_count
        
        count = len(self._lifecycle_records)
        stats["avg_age_days"] = total_age / count
        stats["avg_access_count"] = total_access / count
        
        return stats
    
    def get_memories_by_state(
        self,
        state: MemoryState,
        limit: int = 100
    ) -> List[MemoryLifecycleRecord]:
        """
        获取指定状态的记忆
        
        Args:
            state: 目标状态
            limit: 最大返回数量
            
        Returns:
            生命周期记录列表
        """
        return [
            record for record in self._lifecycle_records.values()
            if record.state == state
        ][:limit]
    
    async def start_background_check(self, interval_hours: Optional[float] = None):
        """
        启动后台生命周期检查任务
        
        Args:
            interval_hours: 检查间隔（小时）
        """
        if self._running:
            return
        
        self._running = True
        interval = interval_hours or self.config.lifecycle_check_interval_hours
        interval_seconds = interval * 3600
        
        self._lifecycle_task = asyncio.create_task(
            self._background_lifecycle_check(interval_seconds)
        )
    
    async def _background_lifecycle_check(self, interval_seconds: float):
        """后台生命周期检查循环"""
        while self._running:
            try:
                stats = await self.check_and_update_lifecycle()
                # 可以在这里添加日志记录
            except Exception as e:
                # 记录错误但不中断循环
                pass
            
            await asyncio.sleep(interval_seconds)
    
    async def stop_background_check(self):
        """停止后台生命周期检查任务"""
        self._running = False
        
        if self._lifecycle_task:
            self._lifecycle_task.cancel()
            try:
                await self._lifecycle_task
            except asyncio.CancelledError:
                pass
            
            self._lifecycle_task = None
    
    def remove_memory(self, memory_id: int) -> bool:
        """
        从生命周期管理中移除记忆
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            是否成功移除
        """
        if memory_id in self._lifecycle_records:
            del self._lifecycle_records[memory_id]
            return True
        return False
    
    def get_memory_lifecycle(
        self,
        memory_id: int
    ) -> Optional[MemoryLifecycleRecord]:
        """
        获取记忆的生命周期记录
        
        Args:
            memory_id: 记忆 ID
            
        Returns:
            生命周期记录，如果不存在返回 None
        """
        return self._lifecycle_records.get(memory_id)
