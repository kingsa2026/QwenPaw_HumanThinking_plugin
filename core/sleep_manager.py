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
        frozen_days: int = 7,
        archive_days: int = 30,
        enable_insight: bool = True,
        enable_dream_log: bool = True,
    ):
        self.enable_agent_sleep = enable_agent_sleep
        self.sleep_idle_seconds = sleep_idle_hours * 3600
        self.auto_consolidate = auto_consolidate
        self.consolidate_days = consolidate_days
        self.frozen_days = min(frozen_days, 90)  # 最高90天
        self.archive_days = min(max(archive_days, frozen_days + 1), 180)  # 最高180天，至少比冷藏多1天
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
        """检查是否需要整理记忆和应用遗忘曲线"""
        # 1. 应用遗忘曲线（每次睡眠都执行）
        db = None
        try:
            from .database import HumanThinkingDB
            db = HumanThinkingDB(agent_id)
            await db.initialize()
            
            forgetting_result = await db.apply_forgetting_curve(
                agent_id,
                frozen_days=self.config.frozen_days,
                archive_days=self.config.archive_days
            )
            logger.info(f"Agent {agent_id} forgetting curve applied: {forgetting_result}")
        except Exception as e:
            logger.error(f"Error applying forgetting curve: {e}")
        finally:
            if db:
                await db.close()
        
        # 2. 检查是否需要整理记忆（按间隔）
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
        2. 分类记忆到层级和类别 (sensory/working/short_term/long_term, episodic/semantic/procedural)
        3. 按四种类型分类 (fact/preference/emotion/general)
        4. 应用遗忘曲线
        5. 归档低优先级记忆
        6. 生成洞察
        7. 记录梦境日记
        """
        from .database import HumanThinkingDB
        
        db = HumanThinkingDB(agent_id)
        await db.initialize()
        
        try:
            memories_scanned = 0
            memories_consolidated = 0
            memories_archived = 0
            tier_changed = 0
            
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
                current_category = memory.get("memory_category", "episodic")
                access_count = memory.get("access_count", 0)
                
                # 2a. 分类到四种类型 (fact/preference/emotion/general)
                new_type = self._classify_memory(content, current_type)
                if new_type != current_type:
                    await db.update_memory_type(memory_id, new_type)
                    memories_consolidated += 1
                
                # 2b. 分类到层级 (sensory/working/short_term/long_term/archived)
                new_tier = self._classify_tier(access_count, memory)
                if new_tier != memory.get("memory_tier", "short_term"):
                    await db.set_memory_tier(memory_id, new_tier)
                    tier_changed += 1
                
                # 2c. 分类到类别 (episodic/semantic/procedural)
                new_category = self._classify_category(content, current_category)
                if new_category != current_category:
                    await db.set_memory_category(memory_id, new_category)
                
                # 3. 遗忘曲线 - 更新衰减分数
                await db.update_decay(memory_id, self._calculate_decay(memory))
            
            # 4. 应用遗忘曲线，查找低价值记忆
            low_value_memories = await db.get_low_value_memories(agent_id, threshold=0.3, limit=50)
            for low_mem in low_value_memories:
                await db.archive_memory(low_mem["id"])
                memories_archived += 1
            
            # 5. 统计各层级和分类
            tier_stats = await db.get_tier_stats(agent_id)
            category_stats = await db.get_category_stats(agent_id)
            
            # 6. 生成洞察
            if self.config.enable_insight and memories_scanned > 0:
                insights = self._generate_insights(memories, tier_stats, category_stats)
                for insight in insights:
                    await db.add_insight(
                        agent_id=agent_id,
                        title=insight["title"],
                        content=insight["content"],
                        memory_count=memories_scanned,
                        insight_type=insight.get("type", "pattern")
                    )
            
            # 7. 记录梦境日记
            if self.config.enable_dream_log:
                await db.add_dream_log(
                    agent_id=agent_id,
                    action="CONSOLIDATE_COMPLETE",
                    details=f"扫描{memories_scanned}条，分类{memories_consolidated}条，层级调整{tier_changed}条，归档{memories_archived}条",
                    memories_scanned=memories_scanned,
                    memories_consolidated=memories_consolidated,
                    memories_archived=memories_archived,
                    tokens_saved=memories_archived * 100
                )
            
            logger.info(f"Consolidation complete: scanned={memories_scanned}, consolidated={memories_consolidated}, tier_changed={tier_changed}, archived={memories_archived}")
            logger.info(f"Tier stats: {tier_stats}, Category stats: {category_stats}")
            
        finally:
            await db.close()
    
    def _classify_tier(self, access_count: int, memory: Dict) -> str:
        """根据访问次数和记忆特征分类到层级
        
        层级：
        - sensory: 毫秒级，仅缓存
        - working: 会话级，短期
        - short_term: 最近N轮，快速检索
        - long_term: 长期持久化
        - archived: 已归档
        """
        created_at = memory.get("created_at", "")
        importance = memory.get("importance", 3)
        
        # 高重要性 + 高访问 = 长时记忆
        if access_count >= 10 and importance >= 4:
            return "long_term"
        
        # 低访问 + 低重要性 = 可能归档
        if access_count <= 1 and importance <= 2:
            return "archived"
        
        # 中等访问 = 短时记忆
        return "short_term"
    
    def _classify_category(self, content: str, current: str) -> str:
        """根据内容分类到类别
        
        类别：
        - episodic: 情景记忆（会话历史）
        - semantic: 语义记忆（事实/偏好/规则）
        - procedural: 程序性记忆（技能/习惯）
        """
        content_lower = content.lower()
        
        # 程序性记忆关键词
        procedural_keywords = ["步骤", "流程", "方法", "技巧", "skill", "procedure", "method", "how to"]
        if any(kw in content_lower for kw in procedural_keywords):
            return "procedural"
        
        # 语义记忆关键词
        semantic_keywords = ["事实", "规则", "偏好", "喜欢", "知道", "fact", "rule", "prefer", "always"]
        if any(kw in content_lower for kw in semantic_keywords):
            return "semantic"
        
        return "episodic"
    
    def _calculate_decay(self, memory: Dict) -> float:
        """计算遗忘分数
        
        公式：decay = base_decay * importance_factor * access_factor
        """
        base_decay = 0.95
        importance = memory.get("importance", 3)
        access_count = memory.get("access_count", 0)
        
        # 重要性越高，衰减越慢
        importance_factor = 1.0 + (importance - 3) * 0.1
        
        # 访问次数越多，衰减越慢
        access_factor = 1.0 + min(access_count * 0.05, 0.5)
        
        decay = base_decay * importance_factor * access_factor
        return min(decay, 1.0)
    
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
    
    def _generate_insights(self, memories: List[Dict], tier_stats: Dict = None, category_stats: Dict = None) -> List[Dict]:
        """生成洞察
        
        基于记忆分析，发现隐藏模式，输出1-3个建议
        """
        insights = []
        
        if not memories:
            return insights
        
        # 统计
        memory_types = {}
        importance_sum = 0
        
        for m in memories:
            mtype = m.get("memory_type", "general")
            memory_types[mtype] = memory_types.get(mtype, 0) + 1
            importance_sum += m.get("importance", 3)
        
        # 洞察1：记忆层级分布
        if tier_stats:
            long_term = tier_stats.get("long_term", 0)
            short_term = tier_stats.get("short_term", 0)
            archived = tier_stats.get("archived", 0)
            total = long_term + short_term + archived
            if total > 0 and long_term / total < 0.2:
                insights.append({
                    "title": "记忆转化建议",
                    "content": f"长期记忆占比{long_term/total*100:.0f}%偏低，建议增加重要信息的访问频率，促进短时记忆向长时记忆转化。",
                    "type": "suggestion"
                })
        
        # 洞察2：记忆类别分布
        if category_stats:
            semantic = category_stats.get("semantic", 0)
            episodic = category_stats.get("episodic", 0)
            procedural = category_stats.get("procedural", 0)
            if procedural < episodic * 0.1:
                insights.append({
                    "title": "程序性记忆建议",
                    "content": f"程序性记忆(技能)偏少，建议多记录操作流程和技巧类信息。",
                    "type": "suggestion"
                })
        
        # 洞察3：主要记忆类型
        if memory_types:
            dominant_type = max(memory_types.items(), key=lambda x: x[1])
            type_names = {"fact": "事实", "preference": "偏好", "emotion": "情感", "general": "一般"}
            insights.append({
                "title": f"记忆类型分布",
                "content": f"近期{dominant_type[1]}条记忆主要为【{type_names.get(dominant_type[0], dominant_type[0])}】类型，建议重点关注这类信息的积累。",
                "type": "pattern"
            })
        
        # 洞察4：平均重要性
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
    """记录活动并唤醒"""
    if _global_sleep_manager:
        _global_sleep_manager.record_activity(agent_id)


def pulse_agent(agent_id: str):
    """心跳 - 唤醒睡眠中的Agent"""
    if _global_sleep_manager:
        _global_sleep_manager.record_activity(agent_id)


def notify_task_start(agent_id: str):
    """定时任务开始 - 唤醒睡眠中的Agent"""
    if _global_sleep_manager:
        _global_sleep_manager.record_activity(agent_id)
        logger.info(f"Agent {agent_id} woken up by scheduled task")


def is_agent_sleeping(agent_id: str) -> bool:
    if _global_sleep_manager:
        return _global_sleep_manager.is_sleeping(agent_id)
    return False
