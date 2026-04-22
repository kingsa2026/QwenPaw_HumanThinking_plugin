# -*- coding: utf-8 -*-
"""
HumanThinking 睡眠管理器

设计：
- 事件驱动：每次会话触发时检查空闲时间
- 无需后台轮询，节省资源
- 睡眠触发后才执行整理和遗忘曲线
"""

import logging
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SleepConfig:
    """睡眠配置"""
    def __init__(
        self,
        enable_agent_sleep: bool = True,
        sleep_idle_hours: float = 2,
        auto_consolidate: bool = True,
        consolidate_days: int = 7,
        frozen_days: int = 7,
        archive_days: int = 30,
        enable_insight: bool = True,
        enable_dream_log: bool = True,
    ):
        self.enable_agent_sleep = enable_agent_sleep
        self.sleep_idle_seconds = int(sleep_idle_hours * 3600)
        self.auto_consolidate = auto_consolidate
        self.consolidate_days = consolidate_days
        self.frozen_days = min(max(frozen_days, 1), 90)
        self.archive_days = min(max(archive_days, frozen_days + 1), 180)
        self.enable_insight = enable_insight
        self.enable_dream_log = enable_dream_log


@dataclass
class AgentSleepState:
    """Agent 睡眠状态"""
    agent_id: str
    is_sleeping: bool = False
    last_active_time: float = field(default_factory=time.time)
    sleep_start_time: Optional[float] = None
    last_consolidate_time: Optional[float] = None


class SleepManager:
    """睡眠管理器 - 事件驱动模式"""
    
    def __init__(self, config: SleepConfig = None):
        self.config = config or SleepConfig()
        self._agent_states: Dict[str, AgentSleepState] = {}
        
        logger.info(f"SleepManager initialized (event-driven): {self.config.__dict__}")
    
    def update_config(self, config: SleepConfig):
        """更新配置"""
        self.config = config
        logger.info(f"SleepManager config updated: {config.__dict__}")
    
    def record_activity(self, agent_id: str) -> bool:
        """记录活动并检查是否需要进入睡眠
        
        Returns:
            True 表示触发了睡眠后整理
        """
        if not self.config.enable_agent_sleep:
            return False
        
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id=agent_id)
        
        state = self._agent_states[agent_id]
        current_time = time.time()
        
        # 如果已经在睡眠，记录唤醒
        if state.is_sleeping:
            logger.info(f"Agent {agent_id} woke up")
            state.is_sleeping = False
            state.sleep_start_time = None
            state.last_active_time = current_time
            return False
        
        # 检查是否应该进入睡眠（之前已经在睡眠边缘）
        idle_time = current_time - state.last_active_time
        
        # 如果超过空闲阈值，触发睡眠
        if idle_time >= self.config.sleep_idle_seconds:
            return self._trigger_sleep(agent_id, state, current_time)
        
        # 更新活跃时间
        state.last_active_time = current_time
        return False
    
    def _trigger_sleep(self, agent_id: str, state: AgentSleepState, current_time: float) -> bool:
        """触发睡眠并执行整理
        
        Returns:
            True 表示执行了睡眠整理
        """
        state.is_sleeping = True
        state.sleep_start_time = current_time
        
        logger.info(f"Agent {agent_id} entering sleep mode (idle: {current_time - state.last_active_time:.0f}s)")
        
        # 异步执行遗忘曲线和整理
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._execute_sleep_tasks(agent_id))
            loop.close()
        except Exception as e:
            logger.error(f"Error in sleep tasks: {e}", exc_info=True)
        
        return True
    
    async def _execute_sleep_tasks(self, agent_id: str):
        """执行睡眠时的任务"""
        from .database import HumanThinkingDB
        
        db = HumanThinkingDB(agent_id)
        await db.initialize()
        
        try:
            # 1. 记录梦境日志
            if self.config.enable_dream_log:
                await db.add_dream_log(agent_id, "ENTER_SLEEP", "进入睡眠模式")
            
            # 2. 应用遗忘曲线（冷藏/归档/删除）
            forgetting_result = await db.apply_forgetting_curve(
                agent_id,
                frozen_days=self.config.frozen_days,
                archive_days=self.config.archive_days
            )
            logger.info(f"Forgetting curve applied: {forgetting_result}")
            
            # 3. 检查是否需要整理
            if self.config.auto_consolidate:
                await self._consolidate_memories(agent_id, db)
            
            # 4. 记录完成
            if self.config.enable_dream_log:
                await db.add_dream_log(agent_id, "SLEEP_COMPLETE", "睡眠任务完成")
                
        finally:
            await db.close()
    
    async def _consolidate_memories(self, agent_id: str, db):
        """整理记忆"""
        memories = await db.get_memories_for_consolidation(agent_id, self.config.consolidate_days)
        
        if not memories:
            return
        
        memories_scanned = len(memories)
        memories_consolidated = 0
        
        logger.info(f"Consolidating {memories_scanned} memories")
        
        for memory in memories:
            memory_id = memory.get("id")
            content = memory.get("content", "")
            current_type = memory.get("memory_type", "general")
            
            # 分类到四种类型
            new_type = self._classify_memory(content, current_type)
            if new_type != current_type:
                await db.update_memory_type(memory_id, new_type)
                memories_consolidated += 1
            
            # 分类到层级
            access_count = memory.get("access_count", 0)
            new_tier = self._classify_tier(access_count, memory)
            if new_tier != memory.get("memory_tier", "short_term"):
                await db.set_memory_tier(memory_id, new_tier)
            
            # 更新衰减
            await db.update_decay(memory_id, self._calculate_decay(memory))
        
        # 生成洞察
        if self.config.enable_insight:
            tier_stats = await db.get_tier_stats(agent_id)
            category_stats = await db.get_category_stats(agent_id)
            insights = self._generate_insights(memories, tier_stats, category_stats)
            
            for insight in insights:
                await db.add_insight(
                    agent_id=agent_id,
                    title=insight["title"],
                    content=insight["content"],
                    memory_count=memories_scanned,
                    insight_type=insight.get("type", "pattern")
                )
        
        # 记录梦境
        if self.config.enable_dream_log:
            await db.add_dream_log(
                agent_id=agent_id,
                action="CONSOLIDATE_COMPLETE",
                details=f"扫描{memories_scanned}条，分类{memories_consolidated}条",
                memories_scanned=memories_scanned,
                memories_consolidated=memories_consolidated
            )
        
        logger.info(f"Consolidation complete: scanned={memories_scanned}, consolidated={memories_consolidated}")
    
    def _classify_memory(self, content: str, current_type: str) -> str:
        """根据内容分类记忆"""
        content_lower = content.lower()
        
        emotion_keywords = ["喜欢", "讨厌", "开心", "生气", "难过", "满意", "emotion", "feel", "happy"]
        if any(kw in content_lower for kw in emotion_keywords):
            return "emotion"
        
        preference_keywords = ["偏好", "喜欢", "想要", "希望", "preference", "like", "want"]
        if any(kw in content_lower for kw in preference_keywords):
            return "preference"
        
        fact_keywords = ["订单", "手机", "地址", "账号", "订单号", "fact", "order", "phone"]
        if any(kw in content_lower for kw in fact_keywords):
            return "fact"
        
        return "general"
    
    def _classify_tier(self, access_count: int, memory: Dict) -> str:
        """根据访问次数分类层级"""
        importance = memory.get("importance", 3)
        
        if access_count >= 10 and importance >= 4:
            return "long_term"
        
        if access_count <= 1 and importance <= 2:
            return "archived"
        
        return "short_term"
    
    def _calculate_decay(self, memory: Dict) -> float:
        """计算遗忘分数"""
        base_decay = 0.95
        importance = memory.get("importance", 3)
        access_count = memory.get("access_count", 0)
        
        importance_factor = 1.0 + (importance - 3) * 0.1
        access_factor = 1.0 + min(access_count * 0.05, 0.5)
        
        return min(base_decay * importance_factor * access_factor, 1.0)
    
    def _generate_insights(self, memories: List[Dict], tier_stats: Dict = None, category_stats: Dict = None) -> List[Dict]:
        """生成洞察"""
        insights = []
        
        if not memories:
            return insights
        
        memory_types = {}
        for m in memories:
            mtype = m.get("memory_type", "general")
            memory_types[mtype] = memory_types.get(mtype, 0) + 1
        
        if memory_types:
            dominant = max(memory_types.items(), key=lambda x: x[1])
            type_names = {"fact": "事实", "preference": "偏好", "emotion": "情感", "general": "一般"}
            insights.append({
                "title": f"记忆类型分布",
                "content": f"近期{dominant[1]}条记忆主要为【{type_names.get(dominant[0], dominant[0])}】类型",
                "type": "pattern"
            })
        
        return insights[:3]
    
    def is_sleeping(self, agent_id: str) -> bool:
        """检查 Agent 是否在睡眠"""
        return self._agent_states.get(agent_id, AgentSleepState(agent_id=agent_id)).is_sleeping
    
    def get_sleeping_agents(self) -> List[str]:
        """获取所有睡眠中的 Agent"""
        return [
            agent_id for agent_id, state in self._agent_states.items()
            if state.is_sleeping
        ]
    
    def get_status(self, agent_id: str) -> dict:
        """获取 Agent 睡眠状态"""
        state = self._agent_states.get(agent_id)
        if not state:
            return {"agent_id": agent_id, "is_sleeping": False, "last_active": None}
        
        return {
            "agent_id": agent_id,
            "is_sleeping": state.is_sleeping,
            "last_active": datetime.fromtimestamp(state.last_active_time).isoformat(),
            "sleep_duration": time.time() - state.sleep_start_time if state.sleep_start_time else 0
        }


_global_sleep_manager: Optional[SleepManager] = None


def get_sleep_manager() -> Optional[SleepManager]:
    return _global_sleep_manager


def init_sleep_manager(config: SleepConfig = None) -> SleepManager:
    global _global_sleep_manager
    _global_sleep_manager = SleepManager(config or SleepConfig())
    return _global_sleep_manager


def record_agent_activity(agent_id: str) -> bool:
    """记录活动并检查是否触发睡眠
    
    Returns:
        True 表示触发了睡眠后整理
    """
    if _global_sleep_manager:
        return _global_sleep_manager.record_activity(agent_id)
    return False


def pulse_agent(agent_id: str) -> bool:
    """心跳 - 唤醒/记录活动"""
    return record_agent_activity(agent_id)


def notify_task_start(agent_id: str) -> bool:
    """定时任务 - 记录活动"""
    return record_agent_activity(agent_id)


def is_agent_sleeping(agent_id: str) -> bool:
    if _global_sleep_manager:
        return _global_sleep_manager.is_sleeping(agent_id)
    return False
