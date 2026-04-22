# -*- coding: utf-8 -*-
"""
HumanThinking 睡眠管理器

功能：
- 监控 Agent 会话空闲时间
- 空闲超过阈值自动进入睡眠
- 有新会话自动唤醒
- 睡眠时自动整理记忆
- 生成洞察与梦境日记
"""

import asyncio
import logging
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class SleepConfig:
    """睡眠配置"""
    def __init__(
        self,
        enable_agent_sleep: bool = True,
        sleep_idle_hours: int = 2,
        auto_consolidate: bool = True,
        consolidate_days: int = 7,
        enable_insight: bool = True,
        enable_dream_log: bool = True,
    ):
        self.enable_agent_sleep = enable_agent_sleep
        self.sleep_idle_seconds = sleep_idle_hours * 3600
        self.auto_consolidate = auto_consolidate
        self.consolidate_days = consolidate_days
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
    """睡眠管理器"""
    
    def __init__(self, config: SleepConfig = None):
        self.config = config or SleepConfig()
        self._agent_states: Dict[str, AgentSleepState] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"SleepManager initialized: {self.config.__dict__}")
    
    def update_config(self, config: SleepConfig):
        """更新配置"""
        self.config = config
        logger.info(f"SleepManager config updated: {config.__dict__}")
    
    def start(self):
        """启动睡眠管理器"""
        if self._running:
            return
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("SleepManager started")
    
    def stop(self):
        """停止睡眠管理器"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
        logger.info("SleepManager stopped")
    
    def record_activity(self, agent_id: str):
        """记录 Agent 活动（唤醒）"""
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id=agent_id)
        
        state = self._agent_states[agent_id]
        
        if state.is_sleeping:
            logger.info(f"Agent {agent_id} woke up from sleep")
        
        state.last_active_time = time.time()
        state.is_sleeping = False
        state.sleep_start_time = None
    
    def is_sleeping(self, agent_id: str) -> bool:
        """检查 Agent 是否在睡眠"""
        return self._agent_states.get(agent_id, AgentSleepState(agent_id=agent_id)).is_sleeping
    
    def get_sleeping_agents(self) -> List[str]:
        """获取所有睡眠中的 Agent"""
        return [
            agent_id for agent_id, state in self._agent_states.items()
            if state.is_sleeping
        ]
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                await asyncio.sleep(60)
                
                if not self.config.enable_agent_sleep:
                    continue
                
                current_time = time.time()
                
                for agent_id, state in list(self._agent_states.items()):
                    if state.is_sleeping:
                        if self.config.auto_consolidate:
                            await self._maybe_consolidate(agent_id, state, current_time)
                    else:
                        idle_time = current_time - state.last_active_time
                        if idle_time >= self.config.sleep_idle_seconds:
                            await self._enter_sleep(agent_id, state, current_time)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sleep monitor loop: {e}", exc_info=True)
    
    async def _enter_sleep(self, agent_id: str, state: AgentSleepState, current_time: float):
        """进入睡眠"""
        state.is_sleeping = True
        state.sleep_start_time = current_time
        
        logger.info(f"Agent {agent_id} entering sleep mode (idle: {current_time - state.last_active_time:.0f}s)")
        
        if self.config.enable_dream_log:
            await self._log_dream_action(agent_id, "ENTER_SLEEP", f"进入睡眠模式，空闲时间 {current_time - state.last_active_time:.0f} 秒")
    
    async def _maybe_consolidate(self, agent_id: str, state: AgentSleepState, current_time: float):
        """检查是否需要整理记忆"""
        if not self.config.auto_consolidate:
            return
        
        if state.last_consolidate_time is None:
            need_consolidate = True
        else:
            elapsed = current_time - state.last_consolidate_time
            consolidate_interval = self.config.consolidate_days * 86400
            need_consolidate = elapsed >= consolidate_interval
        
        if need_consolidate:
            logger.info(f"Agent {agent_id} consolidating memories during sleep...")
            await self._consolidate_memories(agent_id)
            state.last_consolidate_time = current_time
    
    async def _consolidate_memories(self, agent_id: str):
        """整理 Agent 记忆
        
        睡眠时执行：
        1. 扫描近期记忆
        2. 按四种类型分类存储
        3. 归档过期/低优先级记忆
        4. 生成洞察
        5. 记录梦境日记
        """
        from .database import HumanThinkingDB
        
        db = HumanThinkingDB(agent_id)
        await db.initialize()
        
        try:
            memories_scanned = 0
            memories_consolidated = 0
            memories_archived = 0
            
            if self.config.enable_dream_log:
                await db.add_dream_log(agent_id, "CONSOLIDATE_START", "开始整理记忆", 0, 0, 0, 0)
            
            # 1. 获取近期记忆
            memories = await db.get_memories_for_consolidation(agent_id, self.config.consolidate_days)
            memories_scanned = len(memories)
            
            logger.info(f"Scanning {memories_scanned} memories for consolidation")
            
            # 2. 分析并分类记忆
            for memory in memories:
                memory_id = memory.get("id")
                content = memory.get("content", "")
                current_type = memory.get("memory_type", "general")
                
                # 简单的记忆分类逻辑（实际可用 LLM 分析）
                new_type = self._classify_memory(content, current_type)
                
                if new_type != current_type:
                    await db.update_memory_type(memory_id, new_type)
                    memories_consolidated += 1
                
                # 3. 遗忘曲线 - 归档低优先级记忆
                importance = memory.get("importance", 3)
                created_at = memory.get("created_at", "")
                
                if importance <= 1 and created_at:
                    await db.archive_memory(memory_id)
                    memories_archived += 1
            
            # 4. 生成洞察
            if self.config.enable_insight and memories_scanned > 0:
                insights = self._generate_insights(memories)
                for insight in insights:
                    await db.add_insight(
                        agent_id=agent_id,
                        title=insight["title"],
                        content=insight["content"],
                        memory_count=memories_scanned,
                        insight_type=insight.get("type", "pattern")
                    )
            
            # 5. 记录梦境日记
            if self.config.enable_dream_log:
                await db.add_dream_log(
                    agent_id=agent_id,
                    action="CONSOLIDATE_COMPLETE",
                    details=f"扫描{memories_scanned}条记忆，分类{memories_consolidated}条，归档{memories_archived}条",
                    memories_scanned=memories_scanned,
                    memories_consolidated=memories_consolidated,
                    memories_archived=memories_archived,
                    tokens_saved=memories_archived * 100
                )
            
            logger.info(f"Consolidation complete: scanned={memories_scanned}, consolidated={memories_consolidated}, archived={memories_archived}")
            
        finally:
            await db.close()
    
    def _classify_memory(self, content: str, current_type: str) -> str:
        """根据内容分类记忆
        
        四种类型：
        - fact: 事实性记忆
        - preference: 偏好记忆
        - emotion: 情感记忆
        - general: 一般记忆
        """
        content_lower = content.lower()
        
        # 情感关键词
        emotion_keywords = ["喜欢", "讨厌", "开心", "生气", "难过", "满意", "不满意", "感谢", "抱歉", "emotion", "feel", "happy", "angry"]
        if any(kw in content_lower for kw in emotion_keywords):
            return "emotion"
        
        # 偏好关键词
        preference_keywords = ["偏好", "喜欢", "想要", "希望", "不要", "preference", "like", "want", "prefer"]
        if any(kw in content_lower for kw in preference_keywords):
            return "preference"
        
        # 事实关键词
        fact_keywords = ["订单", "手机", "地址", "姓名", "账号", "订单号", "金额", "时间", "fact", "order", "phone", "address"]
        if any(kw in content_lower for kw in fact_keywords):
            return "fact"
        
        return "general"
    
    def _generate_insights(self, memories: List[Dict]) -> List[Dict]:
        """生成洞察
        
        基于记忆分析，发现隐藏模式，输出1-3个建议
        """
        insights = []
        
        if not memories:
            return insights
        
        # 简单的模式分析
        memory_types = {}
        importance_sum = 0
        
        for m in memories:
            mtype = m.get("memory_type", "general")
            memory_types[mtype] = memory_types.get(mtype, 0) + 1
            importance_sum += m.get("importance", 3)
        
        # 洞察1：主要记忆类型
        if memory_types:
            dominant_type = max(memory_types.items(), key=lambda x: x[1])
            type_names = {"fact": "事实", "preference": "偏好", "emotion": "情感", "general": "一般"}
            insights.append({
                "title": f"记忆类型分布",
                "content": f"近期{dominant_type[1]}条记忆主要为【{type_names.get(dominant_type[0], dominant_type[0])}】类型，建议重点关注这类信息的积累。",
                "type": "pattern"
            })
        
        # 洞察2：平均重要性
        avg_importance = importance_sum / len(memories) if memories else 0
        if avg_importance < 2.5:
            insights.append({
                "title": "记忆质量建议",
                "content": "近期记忆平均重要性偏低，建议增加高价值互动的记录频率。",
                "type": "suggestion"
            })
        
        # 洞察3：情感趋势
        emotion_count = memory_types.get("emotion", 0)
        if emotion_count > len(memories) * 0.2:
            insights.append({
                "title": "情感交互频繁",
                "content": f"情感类记忆占比{emotion_count/len(memories)*100:.0f}%，用户情感波动较大，注意情感连续性维护。",
                "type": "warning"
            })
        
        return insights[:3]
    
    async def _log_dream_action(self, agent_id: str, action: str, details: str):
        """记录梦境日记"""
        from .database import HumanThinkingDB
        
        db = HumanThinkingDB(agent_id)
        await db.initialize()
        try:
            await db.add_dream_log(agent_id, action, details)
        finally:
            await db.close()
    
    def get_status(self, agent_id: str) -> dict:
        """获取 Agent 睡眠状态"""
        state = self._agent_states.get(agent_id)
        if not state:
            return {"agent_id": agent_id, "is_sleeping": False, "last_active": None}
        
        current_time = time.time()
        return {
            "agent_id": agent_id,
            "is_sleeping": state.is_sleeping,
            "last_active": datetime.fromtimestamp(state.last_active_time).isoformat(),
            "sleep_duration": current_time - state.sleep_start_time if state.sleep_start_time else 0,
            "last_consolidate": datetime.fromtimestamp(state.last_consolidate_time).isoformat() if state.last_consolidate_time else None
        }


_global_sleep_manager: Optional[SleepManager] = None


def get_sleep_manager() -> Optional[SleepManager]:
    return _global_sleep_manager


def init_sleep_manager(config: SleepConfig = None) -> SleepManager:
    global _global_sleep_manager
    if _global_sleep_manager:
        _global_sleep_manager.stop()
    _global_sleep_manager = SleepManager(config or SleepConfig())
    _global_sleep_manager.start()
    return _global_sleep_manager


def record_agent_activity(agent_id: str):
    if _global_sleep_manager:
        _global_sleep_manager.record_activity(agent_id)


def is_agent_sleeping(agent_id: str) -> bool:
    if _global_sleep_manager:
        return _global_sleep_manager.is_sleeping(agent_id)
    return False
