# -*- coding: utf-8 -*-
"""
HumanThinking 睡眠管理器 - 事件驱动模式

三阶段睡眠设计：
- 阶段一：浅睡眠（Light Sleep）- 扫描7天日志，去重过滤，标记重要信息，暂存
- 阶段二：REM - 提取主题，发现跨对话模式，生成反思摘要，识别持久真理
- 阶段三：深睡眠（Deep Sleep）- 六维评分，高分写入MEMORY.md长期记忆

触发机制（基于数据库查询的惰性计算）：
- 每次查询睡眠状态时，从数据库获取最后活动时间
- 根据空闲时间实时计算当前应处于的睡眠状态
- 状态转换时执行对应的睡眠任务
"""
import logging
import time
import os
import asyncio
from pathlib import Path
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import re

from ..utils.paths import resolve_qwenpaw_dir as _resolve_qwenpaw_dir, resolve_agent_workspace_dir as _resolve_agent_workspace_dir, validate_agent_id, safe_path_join, get_db_path as _get_db_path

logger = logging.getLogger(__name__)

# 模块级别导入 HumanThinkingDB 以便测试 patch
# 使用 try/except 避免循环导入问题
try:
    from .database import HumanThinkingDB
except ImportError:
    HumanThinkingDB = None


def _get_db(agent_id: str):
    if HumanThinkingDB is None:
        from .database import HumanThinkingDB as DBClass
    else:
        DBClass = HumanThinkingDB
    
    db_path = str(_get_db_path(agent_id))
    db_path_obj = Path(db_path)
    db_path_obj.parent.mkdir(parents=True, exist_ok=True)
    db = DBClass(db_path)
    return db, db_path


class SleepConfig:
    """睡眠配置"""
    def __init__(
        self,
        enable_agent_sleep: bool = True,
        light_sleep_minutes: float = 30,
        rem_minutes: float = 60,
        deep_sleep_minutes: float = 120,
        auto_consolidate: bool = True,
        consolidate_days: int = 7,
        frozen_days: int = 30,
        archive_days: int = 90,
        delete_days: int = 180,
        enable_insight: bool = True,
        enable_dream_log: bool = True,
        memory_md_path: str = None,
        enable_merge: bool = True,
        merge_similarity_threshold: float = 0.8,
        merge_max_distance_hours: int = 72,
        # 矛盾检测配置
        enable_contradiction_detection: bool = True,
        contradiction_threshold: float = 0.7,
        contradiction_resolution_strategy: str = "keep_latest",
        enable_semantic_contradiction_check: bool = True,
        enable_temporal_contradiction_check: bool = True,
        enable_confidence_scoring: bool = True,
        auto_resolve_contradiction: bool = True,
        min_confidence_for_auto_resolve: float = 0.85,
    ):
        self.enable_agent_sleep = enable_agent_sleep
        self.light_sleep_seconds = int(light_sleep_minutes * 60)
        self.rem_seconds = int(rem_minutes * 60)
        self.deep_sleep_seconds = int(deep_sleep_minutes * 60)
        self.light_sleep_minutes = light_sleep_minutes
        self.rem_minutes = rem_minutes
        self.deep_sleep_minutes = deep_sleep_minutes
        self.auto_consolidate = auto_consolidate
        self.consolidate_days = consolidate_days
        self.frozen_days = min(max(frozen_days, 1), 90)
        self.archive_days = min(max(archive_days, self.frozen_days + 1), 180)
        self.delete_days = min(max(delete_days, self.archive_days + 1), 365)
        self.enable_insight = enable_insight
        self.enable_dream_log = enable_dream_log
        self.memory_md_path = memory_md_path
        self.enable_merge = enable_merge
        self.merge_similarity_threshold = min(max(merge_similarity_threshold, 0.5), 0.95)
        self.merge_max_distance_hours = min(max(merge_max_distance_hours, 1), 168)
        # 矛盾检测配置
        self.enable_contradiction_detection = enable_contradiction_detection
        self.contradiction_threshold = min(max(contradiction_threshold, 0.3), 0.99)
        self.contradiction_resolution_strategy = contradiction_resolution_strategy
        self.enable_semantic_contradiction_check = enable_semantic_contradiction_check
        self.enable_temporal_contradiction_check = enable_temporal_contradiction_check
        self.enable_confidence_scoring = enable_confidence_scoring
        self.auto_resolve_contradiction = auto_resolve_contradiction
        self.min_confidence_for_auto_resolve = min(max(min_confidence_for_auto_resolve, 0.5), 0.99)


class AgentSleepState:
    """Agent 睡眠状态
    
    状态转换：
    active → light_sleep → rem → deep_sleep → active(唤醒)
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.is_active = True
        self.is_light_sleep = False
        self.is_rem = False
        self.is_deep_sleep = False
        self.last_active_time = 0.0
        self.last_light_sleep_time: Optional[float] = None
        self.last_rem_time: Optional[float] = None
        self.last_deep_sleep_time: Optional[float] = None
        self.last_consolidate_time: Optional[float] = None
        
        self.pending_importance: List[Dict] = []
        self.lasting_truths: List[Dict] = []
        self.theme_summary: Optional[str] = None
        self.contradiction_reports: List[Dict] = []
        
        self._light_sleep_executed = False
        self._rem_executed = False
        self._deep_sleep_executed = False
        
        self.forced_state: Optional[str] = None
        self.actual_status: str = "active"

    def to_dict(self) -> dict:
        """将睡眠状态转换为字典"""
        if self.forced_state:
            status_map = {
                "light_sleep": ("light_sleep", "浅睡（强制）", "🌛", "#faad14"),
                "rem": ("rem", "REM睡眠（强制）", "🌙", "#1890ff"),
                "deep_sleep": ("deep_sleep", "深度睡眠（强制）", "🌑", "#722ed1"),
            }
            if self.forced_state in status_map:
                status, status_text, icon, color = status_map[self.forced_state]
                return {
                    "agent_id": self.agent_id,
                    "status": status,
                    "status_text": status_text,
                    "icon": icon,
                    "color": color,
                    "last_active_time": self.last_active_time,
                    "forced": True,
                }
        
        if self.is_deep_sleep:
            status = "deep_sleep"
            status_text = "深度睡眠"
            icon = "🌑"
            color = "#722ed1"
        elif self.is_rem:
            status = "rem"
            status_text = "REM睡眠"
            icon = "🌙"
            color = "#1890ff"
        elif self.is_light_sleep:
            status = "light_sleep"
            status_text = "浅睡"
            icon = "🌛"
            color = "#faad14"
        else:
            status = "active"
            status_text = "活跃"
            icon = "☀️"
            color = "#52c41a"
        
        return {
            "agent_id": self.agent_id,
            "status": status,
            "status_text": status_text,
            "icon": icon,
            "color": color,
            "last_active_time": self.last_active_time,
        }


class SleepManager:
    """睡眠管理器 - 基于数据库查询的惰性计算模式
    
    支持Agent隔离：每个Agent独立维护自己的睡眠状态和配置
    触发机制：
    1. 查询时触发：每次查询睡眠状态时，从数据库获取最后活动时间，实时计算
    2. 状态转换时执行对应的睡眠任务（每个阶段只执行一次）
    """
    
    def __init__(self, config: SleepConfig = None):
        self._default_config = config or SleepConfig()
        self._agent_configs: Dict[str, SleepConfig] = {}
        self._agent_states: Dict[str, AgentSleepState] = {}
        self._db_cache: Dict[str, Any] = {}
        
        logger.info(f"SleepManager initialized: {self._default_config.__dict__}")
    
    def _get_agent_config(self, agent_id: str) -> SleepConfig:
        """获取Agent的配置（支持Agent隔离）"""
        if agent_id in self._agent_configs:
            return self._agent_configs[agent_id]
        # 尝试从Agent专属文件加载
        try:
            config = _load_config_from_file(agent_id)
            if config is not None:
                self._agent_configs[agent_id] = config
                return config
        except Exception as e:
            logger.warning(f"Failed to load config for agent {agent_id}: {e}")
        # 尝试从全局文件加载
        try:
            config = _load_global_config_from_file()
            if config is not None:
                return config
        except Exception as e:
            logger.warning(f"Failed to load global config: {e}")
        return self._default_config
    
    def update_config(self, config: SleepConfig, agent_id: str = None):
        """更新配置
        
        Args:
            config: 新的睡眠配置
            agent_id: Agent ID（可选，如果提供则只更新该agent的配置）
        """
        if agent_id:
            self._agent_configs[agent_id] = config
            _save_config_to_file(agent_id, config)
            logger.info(f"SleepManager config updated for agent {agent_id}: {config.__dict__}")
        else:
            self._default_config = config
            _save_global_config_to_file(config)
            logger.info(f"SleepManager default config updated: {config.__dict__}")
    
    async def get_sleep_status(self, agent_id: str) -> dict:
        """获取Agent的睡眠状态（基于数据库查询的惰性计算）"""
        config = self._get_agent_config(agent_id)
        if not config.enable_agent_sleep:
            return {
                "agent_id": agent_id,
                "status": "active",
                "status_text": "活跃",
                "icon": "☀️",
                "color": "#52c41a",
                "idle_time": 0,
                "next_sleep_in": -1
            }
        
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        
        state = self._agent_states[agent_id]
        current_time = time.time()
        
        if state.forced_state:
            result = state.to_dict()
            result["idle_time"] = int(current_time - max(state.last_active_time, 0))
            if state.last_light_sleep_time:
                result["light_sleep_elapsed"] = int(current_time - state.last_light_sleep_time)
            if state.last_rem_time:
                result["rem_elapsed"] = int(current_time - state.last_rem_time)
            if state.last_deep_sleep_time:
                result["deep_sleep_elapsed"] = int(current_time - state.last_deep_sleep_time)
            result["actual_status"] = state.actual_status
            idle_time = max(0, current_time - state.last_active_time)
            if state.actual_status == "active":
                result["next_sleep_in"] = max(0, config.light_sleep_seconds - idle_time)
            elif state.actual_status == "light_sleep":
                elapsed_in_stage = current_time - (state.last_light_sleep_time or state.last_active_time)
                result["next_sleep_in"] = max(0, config.rem_seconds - config.light_sleep_seconds - elapsed_in_stage)
            elif state.actual_status == "rem":
                elapsed_in_stage = current_time - (state.last_rem_time or state.last_active_time)
                result["next_sleep_in"] = max(0, config.deep_sleep_seconds - config.rem_seconds - elapsed_in_stage)
            else:
                result["next_sleep_in"] = -1
            return result
        
        last_activity_time = await self._get_last_activity_time(agent_id)
        if last_activity_time and last_activity_time > state.last_active_time:
            state.last_active_time = last_activity_time
        elif state.last_active_time <= 0:
            state.last_active_time = current_time
        
        idle_time = max(0, current_time - state.last_active_time)
        
        await self._update_sleep_state(agent_id, state, idle_time, current_time)
        
        result = state.to_dict()
        result["idle_time"] = int(idle_time)
        
        if state.last_light_sleep_time:
            result["light_sleep_elapsed"] = int(current_time - state.last_light_sleep_time)
        if state.last_rem_time:
            result["rem_elapsed"] = int(current_time - state.last_rem_time)
        if state.last_deep_sleep_time:
            result["deep_sleep_elapsed"] = int(current_time - state.last_deep_sleep_time)
        if state.is_active:
            result["next_sleep_in"] = max(0, config.light_sleep_seconds - idle_time)
        elif state.is_light_sleep:
            elapsed_in_stage = current_time - (state.last_light_sleep_time or state.last_active_time)
            result["next_sleep_in"] = max(0, config.rem_seconds - config.light_sleep_seconds - elapsed_in_stage)
        elif state.is_rem:
            elapsed_in_stage = current_time - (state.last_rem_time or state.last_active_time)
            result["next_sleep_in"] = max(0, config.deep_sleep_seconds - config.rem_seconds - elapsed_in_stage)
        else:
            result["next_sleep_in"] = -1
        
        return result
    
    async def _get_or_create_db(self, agent_id: str):
        """获取或创建缓存的数据库连接"""
        db_path_str = str(_get_db_path(agent_id))
        if db_path_str in self._db_cache:
            return self._db_cache[db_path_str]
        
        if HumanThinkingDB is None:
            from .database import HumanThinkingDB as DBClass
        else:
            DBClass = HumanThinkingDB
        
        db = DBClass(db_path_str)
        await db.initialize()
        self._db_cache[db_path_str] = db
        return db
    
    async def _get_last_activity_time(self, agent_id: str) -> Optional[float]:
        """从数据库获取Agent的最后活动时间"""
        try:
            db = await self._get_or_create_db(agent_id)
            recent = await db.get_recent_memories(agent_id, days=7, limit=1)
            if recent and len(recent) > 0:
                ts = recent[0].get("created_at") or recent[0].get("timestamp")
                if ts:
                    dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                    return dt.timestamp()
            
            return None
        except Exception as e:
            logger.warning(f"Failed to get last activity time for {agent_id}: {e}")
            return None
    
    async def _update_sleep_state(self, agent_id: str, state: AgentSleepState, idle_time: float, current_time: float):
        """根据空闲时间更新睡眠状态并执行对应任务
        
        Args:
            agent_id: Agent ID
            state: Agent睡眠状态
            idle_time: 空闲时间（秒）
            current_time: 当前时间戳
        """
        config = self._get_agent_config(agent_id)
        if not config.enable_agent_sleep:
            return
        
        try:
            # 状态转换逻辑 - 按顺序执行，不跳过中间阶段
            if idle_time >= config.light_sleep_seconds and state.is_active:
                logger.info(f"Agent {agent_id} entering light sleep (idle {idle_time:.0f}s)")
                await self._enter_light_sleep(state, current_time)
            
            if idle_time >= config.rem_seconds and state.is_light_sleep and not state.is_rem and not state.is_deep_sleep:
                logger.info(f"Agent {agent_id} entering REM (idle {idle_time:.0f}s)")
                await self._enter_rem(state, current_time)
            
            if idle_time >= config.deep_sleep_seconds and state.is_rem and not state.is_deep_sleep:
                logger.info(f"Agent {agent_id} entering deep sleep (idle {idle_time:.0f}s)")
                await self._enter_deep_sleep(state, current_time)
            
            # 如果空闲时间超过深睡阈值但跳过了中间阶段，按顺序补执行
            if idle_time >= config.deep_sleep_seconds and not state.is_deep_sleep:
                if state.is_active:
                    logger.info(f"Agent {agent_id} fast-forwarding: active -> light sleep (idle {idle_time:.0f}s)")
                    await self._enter_light_sleep(state, current_time)
                if state.is_light_sleep and not state.is_rem:
                    logger.info(f"Agent {agent_id} fast-forwarding: light sleep -> REM (idle {idle_time:.0f}s)")
                    await self._enter_rem(state, current_time)
                if state.is_rem and not state.is_deep_sleep:
                    logger.info(f"Agent {agent_id} fast-forwarding: REM -> deep sleep (idle {idle_time:.0f}s)")
                    await self._enter_deep_sleep(state, current_time)
            
            # 如果空闲时间超过REM但未到深睡，且跳过了浅睡
            if idle_time >= config.rem_seconds and not state.is_rem and not state.is_deep_sleep:
                if state.is_active:
                    logger.info(f"Agent {agent_id} fast-forwarding: active -> light sleep (idle {idle_time:.0f}s)")
                    await self._enter_light_sleep(state, current_time)
                if state.is_light_sleep and not state.is_rem:
                    logger.info(f"Agent {agent_id} fast-forwarding: light sleep -> REM (idle {idle_time:.0f}s)")
                    await self._enter_rem(state, current_time)
            
            # 如果空闲时间低于浅睡阈值，恢复活跃状态
            if idle_time < config.light_sleep_seconds and not state.is_active:
                logger.info(f"Agent {agent_id} waking up to active")
                self._reset_to_active(state)
        except Exception as e:
            logger.error(f"Error in _update_sleep_state for {agent_id}: {e}", exc_info=True)
    
    async def _enter_light_sleep(self, state: AgentSleepState, current_time: float):
        """进入浅层睡眠"""
        state.is_active = False
        state.is_light_sleep = True
        state.is_rem = False
        state.is_deep_sleep = False
        state.last_light_sleep_time = current_time
        
        if not state._light_sleep_executed:
            state._light_sleep_executed = True
            try:
                await self._execute_light_sleep(state.agent_id, state)
            except Exception as e:
                logger.error(f"Light sleep task failed: {e}", exc_info=True)
    
    async def _enter_rem(self, state: AgentSleepState, current_time: float):
        """进入REM阶段"""
        state.is_active = False
        state.is_light_sleep = False
        state.is_rem = True
        state.is_deep_sleep = False
        state.last_rem_time = current_time
        
        if not state._rem_executed:
            state._rem_executed = True
            try:
                await self._execute_rem(state.agent_id, state)
            except Exception as e:
                logger.error(f"REM task failed: {e}", exc_info=True)
    
    async def _enter_deep_sleep(self, state: AgentSleepState, current_time: float):
        """进入深层睡眠"""
        state.is_active = False
        state.is_light_sleep = False
        state.is_rem = False
        state.is_deep_sleep = True
        state.last_deep_sleep_time = current_time
        
        if not state._deep_sleep_executed:
            state._deep_sleep_executed = True
            try:
                await self._execute_deep_sleep(state.agent_id, state)
            except Exception as e:
                logger.error(f"Deep sleep task failed: {e}", exc_info=True)
    
    def _reset_to_active(self, state: AgentSleepState):
        """重置为活跃状态"""
        state.is_active = True
        state.is_light_sleep = False
        state.is_rem = False
        state.is_deep_sleep = False
        state.last_active_time = time.time()
        
        # 重置执行标记
        state._light_sleep_executed = False
        state._rem_executed = False
        state._deep_sleep_executed = False
    
    async def force_light_sleep(self, agent_id: str) -> dict:
        """强制进入浅睡（跳过睡眠执行任务，仅设置状态）"""
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        state = self._agent_states[agent_id]
        if not state.forced_state:
            if state.is_deep_sleep:
                state.actual_status = "deep_sleep"
            elif state.is_rem:
                state.actual_status = "rem"
            elif state.is_light_sleep:
                state.actual_status = "light_sleep"
            else:
                state.actual_status = "active"
        state.is_active = False
        state.is_light_sleep = True
        state.is_rem = False
        state.is_deep_sleep = False
        state.forced_state = "light_sleep"
        state._light_sleep_executed = True
        return {"success": True, "agent_id": agent_id, "status": "light_sleep"}
    
    async def force_rem(self, agent_id: str) -> dict:
        """强制进入REM（跳过睡眠执行任务，仅设置状态）"""
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        state = self._agent_states[agent_id]
        if not state.forced_state:
            if state.is_deep_sleep:
                state.actual_status = "deep_sleep"
            elif state.is_rem:
                state.actual_status = "rem"
            elif state.is_light_sleep:
                state.actual_status = "light_sleep"
            else:
                state.actual_status = "active"
        state.is_active = False
        state.is_light_sleep = False
        state.is_rem = True
        state.is_deep_sleep = False
        state.forced_state = "rem"
        state._light_sleep_executed = True
        state._rem_executed = True
        return {"success": True, "agent_id": agent_id, "status": "rem"}
    
    async def force_deep_sleep(self, agent_id: str) -> dict:
        """强制进入深睡（跳过睡眠执行任务，仅设置状态）"""
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        state = self._agent_states[agent_id]
        if not state.forced_state:
            if state.is_deep_sleep:
                state.actual_status = "deep_sleep"
            elif state.is_rem:
                state.actual_status = "rem"
            elif state.is_light_sleep:
                state.actual_status = "light_sleep"
            else:
                state.actual_status = "active"
        state.is_active = False
        state.is_light_sleep = False
        state.is_rem = False
        state.is_deep_sleep = True
        state.forced_state = "deep_sleep"
        state._light_sleep_executed = True
        state._rem_executed = True
        state._deep_sleep_executed = True
        return {"success": True, "agent_id": agent_id, "status": "deep_sleep"}
    
    async def wakeup(self, agent_id: str) -> dict:
        """唤醒Agent"""
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        state = self._agent_states[agent_id]
        if state.is_active and not state.forced_state:
            return {"success": True, "agent_id": agent_id, "status": "active"}
        self._reset_to_active(state)
        state.forced_state = None
        state.actual_status = "active"
        logger.info(f"Agent {agent_id} manually woken up, last_active_time={state.last_active_time}")
        return {"success": True, "agent_id": agent_id, "status": "active"}
    
    async def record_activity(self, agent_id: str) -> bool:
        """记录Agent活动（由消息钩子调用）
        
        当Agent响应消息时调用此方法：
        - 如果Agent处于深睡状态，唤醒它
        - 更新最后活动时间
        
        Returns:
            True 表示Agent被唤醒
        """
        config = self._get_agent_config(agent_id)
        if not config.enable_agent_sleep:
            return False
        
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        
        state = self._agent_states[agent_id]
        current_time = time.time()
        
        if not state.is_active:
            if state.forced_state:
                return False
            if state.is_deep_sleep:
                logger.info(f"Agent {agent_id} woke up from deep sleep by new message")
                self._write_memory_md(agent_id, state)
            elif state.is_rem:
                logger.info(f"Agent {agent_id} woke up from REM by new message")
            elif state.is_light_sleep:
                logger.info(f"Agent {agent_id} woke up from light sleep by new message")
            self._reset_to_active(state)
            return True
        
        state.last_active_time = current_time
        return False
    
    async def _execute_light_sleep(self, agent_id: str, state: AgentSleepState):
        """阶段一：浅层睡眠
        
        扫描最近7天内的对话日志
        去重、过滤废话、标记潜在重要信息
        仅暂存，不写入长期记忆
        """
        try:
            db = await self._get_or_create_db(agent_id)
            
            config = self._get_agent_config(agent_id)
            if config.enable_dream_log:
                await db.add_dream_log(agent_id, "LIGHT_SLEEP", "阶段一：浅层睡眠 - 扫描7天日志，去重过滤")
            
            memories = await db.get_recent_memories(agent_id, days=7)
            
            if not memories:
                logger.info(f"No memories to process in light sleep for {agent_id}")
                return
            
            # 去重和过滤
            filtered = self._filter_memories(memories)
            
            # 标记潜在重要信息
            for mem in filtered:
                importance = self._calculate_importance(mem)
                mem["_calculated_importance"] = importance
                mem["importance"] = importance
                if importance >= 6:
                    state.pending_importance.append(mem)
            
            logger.info(f"Light sleep processed {len(memories)} memories, {len(state.pending_importance)} important")
            
        except Exception as e:
            logger.error(f"Error in light sleep: {e}", exc_info=True)
    
    async def _execute_rem(self, agent_id: str, state: AgentSleepState):
        """阶段二：REM
        
        提取主题，发现跨对话模式
        生成反思摘要，识别持久真理
        """
        try:
            db = await self._get_or_create_db(agent_id)
            
            config = self._get_agent_config(agent_id)
            if config.enable_dream_log:
                await db.add_dream_log(agent_id, "REM", "阶段二：REM - 提取主题，发现跨对话模式")
            
            # 提取主题
            themes = self._extract_themes(state.pending_importance)
            
            # 发现持久真理
            truths = self._discover_truths(state.pending_importance)
            state.lasting_truths = truths
            
            # 生成反思摘要
            if config.enable_insight:
                summary = self._generate_reflection_summary(themes, truths)
                state.theme_summary = summary
                
                # 保存洞察到数据库
                await db.add_insight(
                    agent_id, 
                    summary[:100], 
                    summary, 
                    memory_count=len(state.pending_importance),
                    insight_type="reflection"
                )
            
            logger.info(f"REM processed {len(state.pending_importance)} important memories, found {len(truths)} truths")
            
        except Exception as e:
            logger.error(f"Error in REM: {e}", exc_info=True)
    
    async def _execute_deep_sleep(self, agent_id: str, state: AgentSleepState):
        """阶段三：深层睡眠
        
        六维加权评分
        高分记忆写入MEMORY.md长期记忆
        执行遗忘曲线算法
        """
        try:
            db = await self._get_or_create_db(agent_id)
            
            config = self._get_agent_config(agent_id)
            if config.enable_dream_log:
                await db.add_dream_log(agent_id, "DEEP_SLEEP", "阶段三：深层睡眠 - 六维评分，写入长期记忆")
            
            # 六维评分
            scored_memories = []
            for mem in state.lasting_truths:
                score = self._six_dimensional_score(mem)
                scored_memories.append({**mem, "score": score})
            
            # 按分数排序
            scored_memories.sort(key=lambda x: x["score"], reverse=True)
            
            # 写入长期记忆（前20%）
            top_memories = scored_memories[:max(1, len(scored_memories) // 5)]
            
            for mem in top_memories:
                mem_id = mem.get("id")
                if mem_id:
                    await db.update_memory_score(mem_id, mem["score"])
                    await db.set_memory_tier(mem_id, "long_term")
            
            
            await self._apply_memory_temperature(db, agent_id, scored_memories)
            
            await self._archive_and_freeze(db, agent_id)
            
            if config.auto_consolidate:
                await self._consolidate_memories(db, agent_id)
            
            logger.info(f"Deep sleep processed {len(scored_memories)} memories, wrote {len(top_memories)} to long-term")
            
        except Exception as e:
            logger.error(f"Error in deep sleep: {e}", exc_info=True)
    
    def _filter_memories(self, memories: List[Dict]) -> List[Dict]:
        """过滤记忆：去重、过滤废话"""
        seen = set()
        filtered = []
        
        for mem in memories:
            content = mem.get("content", "")
            # 去重
            if content in seen:
                continue
            seen.add(content)
            
            # 过滤过短的内容
            if len(content) < 10:
                continue
            
            filtered.append(mem)
        
        return filtered
    
    def _calculate_importance(self, memory: Dict) -> int:
        """计算记忆重要性（1-10）"""
        score = 5
        
        content = memory.get("content", "")
        
        # 关键词加分
        important_keywords = ["重要", "关键", "必须", "永远", "总是", "喜欢", "讨厌", "目标", "梦想"]
        for keyword in important_keywords:
            if keyword in content:
                score += 1
        
        # 长度加分
        if len(content) > 100:
            score += 1
        
        # 情感加分
        if any(word in content for word in ["爱", "恨", "开心", "难过", "愤怒"]):
            score += 1
        
        return min(score, 10)
    
    def _extract_themes(self, memories: List[Dict]) -> List[str]:
        """提取主题"""
        themes = []
        for mem in memories:
            content = mem.get("content", "")
            # 简单主题提取：查找重复出现的名词
            # 实际实现可以使用NLP
            themes.append(content[:50])  # 简化实现
        return themes
    
    def _discover_truths(self, memories: List[Dict]) -> List[Dict]:
        """发现持久真理"""
        truths = []
        for mem in memories:
            if mem.get("importance", 0) >= 7:
                truths.append(mem)
        return truths
    
    def _generate_reflection_summary(self, themes: List[str], truths: List[Dict]) -> str:
        """生成反思摘要"""
        if not truths:
            return "本期无重要发现"
        
        summary_parts = []
        for truth in truths[:3]:
            summary_parts.append(truth.get("content", ""))
        
        return "；".join(summary_parts)
    
    def _six_dimensional_score(self, memory: Dict) -> float:
        """六维加权评分
        
        1. 相关性 (30%)
        2. 频率 (24%)
        3. 时效性 (15%)
        4. 多样性 (15%)
        5. 整合度 (10%)
        6. 概念丰富度 (6%)
        """
        relevance = memory.get("relevance", 5) / 10 * 0.30
        frequency = memory.get("frequency", 3) / 10 * 0.24
        timeliness = memory.get("timeliness", 5) / 10 * 0.15
        diversity = memory.get("diversity", 5) / 10 * 0.15
        integration = memory.get("integration", 5) / 10 * 0.10
        richness = memory.get("richness", 5) / 10 * 0.06
        
        return relevance + frequency + timeliness + diversity + integration + richness
    
    async def _archive_and_freeze(self, db, agent_id: str):
        """归档和冻结记忆"""
        try:
            config = self._get_agent_config(agent_id)
            await db.apply_forgetting_curve(
                agent_id,
                frozen_days=config.frozen_days,
                archive_days=config.archive_days,
                delete_days=config.delete_days
            )
        except Exception as e:
            logger.error(f"Error archiving and freezing: {e}", exc_info=True)
    
    async def _apply_memory_temperature(self, db, agent_id: str, scored_memories: list):
        """应用记忆温度系统：根据访问频率、重要性、时间衰减计算温度并更新状态
        
        对冷却/冻结记忆写入相应的 tier 和 decay_score。
        与 _archive_and_freeze 互补：温度系统处理活跃/冷却记忆的衰减，
        _archive_and_freeze 处理基于时间的硬性冻结。
        """
        try:
            from qwenpaw.agents.tools.HumanThinking.core.memory_temperature import MemoryTemperature
            
            memories_for_temp = [m for m in scored_memories if m.get("id")]
            if not memories_for_temp:
                logger.debug(f"No memories to calculate temperature for {agent_id}")
                return
            
            temp_results = MemoryTemperature.calculate_batch(memories_for_temp)
            
            frozen_count = 0
            cooled_count = 0
            
            for temp_result in temp_results:
                mem_id = temp_result.get("id")
                if not mem_id:
                    continue
                
                level = temp_result.get("temperature_level", "warm")
                temp_score = temp_result.get("temperature", 0.5)
                
                if level == "frozen":
                    await db.set_memory_tier(mem_id, "frozen")
                    await db.update_memory_score(mem_id, temp_score)
                    frozen_count += 1
                elif level == "cool":
                    await db.set_memory_tier(mem_id, "cool")
                    cooled_count += 1
            
            
            logger.info(f"Temperature applied for {agent_id}: {frozen_count} frozen, {cooled_count} cooled out of {len(temp_results)} scored")
            
        except ImportError:
            logger.debug(f"memory_temperature module not available for {agent_id}")
        except Exception as e:
            logger.error(f"Error applying memory temperature for {agent_id}: {e}", exc_info=True)
    
    async def _consolidate_memories(self, db, agent_id: str):
        """整合记忆"""
        try:
            config = self._get_agent_config(agent_id)
            if not config.auto_consolidate:
                return
            
            memories = await db.get_memories_for_consolidation(
                agent_id, days=config.consolidate_days
            )
            if not memories:
                return
            
            if config.enable_contradiction_detection:
                from .contradiction_detector import batch_detect_contradictions, ConflictResolutionStrategy
                
                strategy_map = {
                    "keep_latest": ConflictResolutionStrategy.KEEP_LATEST,
                    "keep_frequent": ConflictResolutionStrategy.KEEP_FREQUENT,
                    "keep_high_confidence": ConflictResolutionStrategy.KEEP_HIGH_CONFIDENCE,
                    "keep_both": ConflictResolutionStrategy.KEEP_BOTH,
                    "mark_for_review": ConflictResolutionStrategy.MARK_FOR_REVIEW,
                }
                resolution_strategy = strategy_map.get(
                    config.contradiction_resolution_strategy,
                    ConflictResolutionStrategy.KEEP_LATEST
                )
                
                contradictions = batch_detect_contradictions(
                    memories,
                    enable_semantic_check=config.enable_semantic_contradiction_check,
                    enable_temporal_check=config.enable_temporal_contradiction_check,
                    enable_confidence_scoring=config.enable_confidence_scoring,
                    contradiction_threshold=config.contradiction_threshold,
                    auto_resolve=config.auto_resolve_contradiction,
                    min_confidence_for_auto=config.min_confidence_for_auto_resolve,
                    resolution_strategy=resolution_strategy,
                )
                for i, j, result in contradictions:
                    if result.is_contradiction and result.suggested_loser:
                        loser_id = result.suggested_loser.get("id")
                        if loser_id:
                            if config.auto_resolve_contradiction and result.confidence >= config.min_confidence_for_auto_resolve:
                                await db.archive_memory(loser_id)
                            else:
                                logger.info(f"Contradiction detected but not auto-resolved (confidence={result.confidence:.2f}): {result.explanation}")
            
            if config.enable_merge:
                merged = await self._merge_similar_memories(db, agent_id, memories)
                if merged:
                    logger.info(f"Merged {merged} similar memories for {agent_id}")
                    
        except Exception as e:
            logger.error(f"Error consolidating memories: {e}", exc_info=True)
    
    async def _merge_similar_memories(self, db, agent_id: str, memories: List[Dict]) -> int:
        """合并相似记忆
        
        Returns:
            合并的记忆对数
        """
        if not memories or len(memories) < 2:
            return 0
        
        config = self._get_agent_config(agent_id)
        merged_count = 0
        threshold = config.merge_similarity_threshold
        max_distance_hours = config.merge_max_distance_hours
        merged_ids = set()
        
        for i in range(len(memories)):
            if memories[i].get("id") in merged_ids:
                continue
            for j in range(i + 1, len(memories)):
                if memories[j].get("id") in merged_ids:
                    continue
                
                content_i = memories[i].get("content", "")
                content_j = memories[j].get("content", "")
                
                if not content_i or not content_j:
                    continue
                
                similarity = self._calculate_text_similarity(content_i, content_j)
                if similarity < threshold:
                    continue
                
                created_i = memories[i].get("created_at", "")
                created_j = memories[j].get("created_at", "")
                if created_i and created_j:
                    try:
                        dt_i = datetime.fromisoformat(str(created_i).replace('Z', '+00:00'))
                        dt_j = datetime.fromisoformat(str(created_j).replace('Z', '+00:00'))
                        hours_diff = abs((dt_i - dt_j).total_seconds()) / 3600
                        if hours_diff > max_distance_hours:
                            continue
                    except (ValueError, TypeError):
                        pass
                
                importance_i = memories[i].get("importance", 3)
                importance_j = memories[j].get("importance", 3)
                
                if importance_i >= importance_j:
                    loser_id = memories[j].get("id")
                    winner_id = memories[i].get("id")
                else:
                    loser_id = memories[i].get("id")
                    winner_id = memories[j].get("id")
                
                if loser_id and winner_id:
                    await db.archive_memory(loser_id)
                    merged_ids.add(loser_id)
                    merged_count += 1
        
        return merged_count
    
    @staticmethod
    def _calculate_text_similarity(text1: str, text2: str) -> float:
        """计算两个文本的简单相似度（基于字符重叠）"""
        if not text1 or not text2:
            return 0.0
        
        set1 = set(text1)
        set2 = set(text2)
        intersection = set1 & set2
        union = set1 | set2
        
        if not union:
            return 0.0
        
        jaccard = len(intersection) / len(union)
        
        len_ratio = min(len(text1), len(text2)) / max(len(text1), len(text2))
        
        return jaccard * 0.4 + len_ratio * 0.6

    def _write_memory_md(self, agent_id: str, state: AgentSleepState):
        """写入MEMORY.md"""
        try:
            config = self._get_agent_config(agent_id)
            if not config.memory_md_path:
                return
            
            md_path = Path(config.memory_md_path).resolve()
            
            ws_root = _resolve_agent_workspace_dir(agent_id).resolve()
            try:
                md_path.relative_to(ws_root)
            except ValueError:
                logger.error(f"Memory md path {md_path} is outside workspace {ws_root}, rejected")
                return
            
            md_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(f"# {agent_id} 的记忆\n\n")
                f.write(f"## 主题摘要\n{state.theme_summary or '无'}\n\n")
                f.write(f"## 持久真理\n")
                for truth in state.lasting_truths:
                    f.write(f"- {truth.get('content', '')}\n")
            
            logger.info(f"Memory md written to {md_path}")
        
        except Exception as e:
            logger.error(f"Error writing memory md: {e}", exc_info=True)


# ========== 全局实例 ==========

_sleep_manager: Optional[SleepManager] = None


def init_sleep_manager(config: SleepConfig = None) -> SleepManager:
    """初始化睡眠管理器"""
    global _sleep_manager
    _sleep_manager = SleepManager(config)
    return _sleep_manager


def get_sleep_manager() -> SleepManager:
    """获取睡眠管理器实例（懒初始化）"""
    global _sleep_manager
    if _sleep_manager is None:
        _sleep_manager = SleepManager(SleepConfig())
    return _sleep_manager


# ========== 便捷函数（供消息路由调用） ==========

def record_agent_activity(agent_id: str) -> None:
    """记录Agent活动（由消息处理流程调用）
    
    当Agent收到或发送消息时调用此函数，更新Agent的最后活动时间。
    这是一个轻量级操作，仅更新内存中的状态，不涉及数据库查询。
    
    Args:
        agent_id: Agent ID
    """
    global _sleep_manager
    if _sleep_manager is None:
        return
    
    # 获取或创建Agent状态
    if agent_id not in _sleep_manager._agent_states:
        _sleep_manager._agent_states[agent_id] = AgentSleepState(agent_id)
    
    state = _sleep_manager._agent_states[agent_id]
    current_time = time.time()
    
    # 更新最后活动时间
    state.last_active_time = current_time
    
    if not state.is_active:
        if state.forced_state:
            return
    
        logger.info(f"Agent {agent_id} woke up by new activity")
        _sleep_manager._reset_to_active(state)


def is_agent_sleeping(agent_id: str) -> bool:
    """检查Agent是否处于睡眠状态（惰性计算）
    
    查询数据库获取最后活动时间，实时计算Agent是否应处于睡眠状态。
    此函数可以在消息路由中调用，用于决定是否触发睡眠任务。
    
    注意：此函数是同步函数，在异步上下文中只能使用内存中的状态判断。
    如需精确的数据库查询，请使用 check_and_trigger_sleep 异步函数。
    
    Args:
        agent_id: Agent ID
        
    Returns:
        True if Agent应该处于睡眠状态
    """
    global _sleep_manager
    if _sleep_manager is None:
        return False
    
    config = _sleep_manager._get_agent_config(agent_id)
    if not config.enable_agent_sleep:
        return False
    
    if agent_id not in _sleep_manager._agent_states:
        _sleep_manager._agent_states[agent_id] = AgentSleepState(agent_id)
    
    state = _sleep_manager._agent_states[agent_id]
    current_time = time.time()
    
    idle_time = current_time - state.last_active_time
    return idle_time >= config.light_sleep_seconds


async def check_and_trigger_sleep(agent_id: str) -> dict:
    """检查并触发Agent睡眠（供API调用）
    
    此函数在查询睡眠状态时被调用，会：
    1. 查询数据库获取最后活动时间
    2. 计算空闲时间
    3. 如果超过阈值，触发对应的睡眠阶段任务
    4. 返回当前睡眠状态
    
    Args:
        agent_id: Agent ID
        
    Returns:
        睡眠状态字典
    """
    global _sleep_manager
    if _sleep_manager is None:
        _sleep_manager = SleepManager(SleepConfig())
    return await _sleep_manager.get_sleep_status(agent_id)


def get_agent_sleep_config(agent_id: str = None) -> SleepConfig:
    """获取Agent的睡眠配置
    
    优先从文件加载，如果失败则返回全局sleep_manager配置或默认配置
    
    Args:
        agent_id: Agent ID（可选）
        
    Returns:
        SleepConfig实例
    """
    if agent_id:
        try:
            config = _load_config_from_file(agent_id)
            if config is not None:
                return config
        except Exception as e:
            logger.warning(f"Failed to load sleep config from file for {agent_id}: {e}")
    
    global _sleep_manager
    if _sleep_manager is not None:
        if agent_id:
            return _sleep_manager._get_agent_config(agent_id)
        return _sleep_manager._default_config
    return SleepConfig()


def save_agent_sleep_config(agent_id: str, config: SleepConfig) -> bool:
    """保存Agent的睡眠配置
    
    更新全局sleep_manager的配置（如果存在），并保存到文件
    
    Args:
        agent_id: Agent ID
        config: 新的睡眠配置
        
    Returns:
        是否保存成功
    """
    global _sleep_manager
    try:
        if _sleep_manager is not None:
            _sleep_manager.update_config(config, agent_id=agent_id)
        # 保存到Agent专属文件
        _save_config_to_file(agent_id, config)
        # 同时保存到全局配置文件
        _save_global_config_to_file(config)
        return True
    except Exception as e:
        logger.error(f"Failed to save sleep config for {agent_id}: {e}")
        return False


def load_agent_sleep_config(agent_id: str) -> SleepConfig:
    """加载Agent的睡眠配置
    
    优先从Agent文件加载，如果失败则从全局文件加载，
    再失败则返回全局sleep_manager配置或默认配置
    
    Args:
        agent_id: Agent ID
        
    Returns:
        SleepConfig实例
    """
    try:
        config = _load_config_from_file(agent_id)
        if config is not None:
            return config
    except Exception as e:
        logger.warning(f"Failed to load sleep config from file for {agent_id}: {e}")
    
    try:
        config = _load_global_config_from_file()
        if config is not None:
            return config
    except Exception as e:
        logger.warning(f"Failed to load global sleep config from file: {e}")
    
    global _sleep_manager
    if _sleep_manager is not None:
        return _sleep_manager._get_agent_config(agent_id)
    return SleepConfig()


def _get_config_path(agent_id: str) -> Path:
    """获取Agent配置文件路径"""
    return _resolve_agent_workspace_dir(agent_id) / "memory" / "sleep_config.json"


def _get_global_config_path() -> Path:
    """获取全局配置文件路径"""
    return _resolve_qwenpaw_dir() / "config" / "sleep_config.json"


def _save_global_config_to_file(config: SleepConfig) -> bool:
    """保存全局配置到文件"""
    try:
        config_path = _get_global_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            "enable_agent_sleep": config.enable_agent_sleep,
            "light_sleep_minutes": config.light_sleep_minutes,
            "rem_minutes": config.rem_minutes,
            "deep_sleep_minutes": config.deep_sleep_minutes,
            "auto_consolidate": config.auto_consolidate,
            "consolidate_days": config.consolidate_days,
            "frozen_days": config.frozen_days,
            "archive_days": config.archive_days,
            "delete_days": config.delete_days,
            "enable_insight": config.enable_insight,
            "enable_dream_log": config.enable_dream_log,
            "enable_merge": config.enable_merge,
            "merge_similarity_threshold": config.merge_similarity_threshold,
            "merge_max_distance_hours": config.merge_max_distance_hours,
            "enable_contradiction_detection": config.enable_contradiction_detection,
            "contradiction_threshold": config.contradiction_threshold,
            "contradiction_resolution_strategy": config.contradiction_resolution_strategy,
            "enable_semantic_contradiction_check": config.enable_semantic_contradiction_check,
            "enable_temporal_contradiction_check": config.enable_temporal_contradiction_check,
            "enable_confidence_scoring": config.enable_confidence_scoring,
            "auto_resolve_contradiction": config.auto_resolve_contradiction,
            "min_confidence_for_auto_resolve": config.min_confidence_for_auto_resolve,
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Failed to save global config to file: {e}")
        return False


def _load_global_config_from_file() -> Optional[SleepConfig]:
    """从文件加载全局配置"""
    try:
        config_path = _get_global_config_path()
        if not config_path.exists():
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            import json
            config_dict = json.load(f)
        
        import inspect
        sig = inspect.signature(SleepConfig.__init__)
        valid_keys = set(sig.parameters.keys()) - {'self'}
        
        config = SleepConfig(**{k: v for k, v in config_dict.items() 
                                if k in valid_keys})
        
        return config
    except Exception as e:
        logger.warning(f"Failed to load global config from file: {e}")
        return None


def _save_config_to_file(agent_id: str, config: SleepConfig) -> bool:
    """保存配置到文件"""
    try:
        config_path = _get_config_path(agent_id)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            "enable_agent_sleep": config.enable_agent_sleep,
            "light_sleep_minutes": config.light_sleep_minutes,
            "rem_minutes": config.rem_minutes,
            "deep_sleep_minutes": config.deep_sleep_minutes,
            "consolidate_days": config.consolidate_days,
            "frozen_days": config.frozen_days,
            "archive_days": config.archive_days,
            "delete_days": config.delete_days,
            "enable_insight": config.enable_insight,
            "enable_dream_log": config.enable_dream_log,
            "enable_merge": config.enable_merge,
            "merge_similarity_threshold": config.merge_similarity_threshold,
            "merge_max_distance_hours": config.merge_max_distance_hours,
            "enable_contradiction_detection": config.enable_contradiction_detection,
            "contradiction_threshold": config.contradiction_threshold,
            "contradiction_resolution_strategy": config.contradiction_resolution_strategy,
            "enable_semantic_contradiction_check": config.enable_semantic_contradiction_check,
            "enable_temporal_contradiction_check": config.enable_temporal_contradiction_check,
            "enable_confidence_scoring": config.enable_confidence_scoring,
            "auto_resolve_contradiction": config.auto_resolve_contradiction,
            "min_confidence_for_auto_resolve": config.min_confidence_for_auto_resolve,
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
        
        return True
    except Exception as e:
        logger.error(f"Failed to save config to file: {e}")
        return False


def _load_config_from_file(agent_id: str) -> Optional[SleepConfig]:
    """从文件加载配置"""
    try:
        config_path = _get_config_path(agent_id)
        if not config_path.exists():
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            import json
            config_dict = json.load(f)
        
        import inspect
        sig = inspect.signature(SleepConfig.__init__)
        valid_keys = set(sig.parameters.keys()) - {'self'}
        
        config = SleepConfig(**{k: v for k, v in config_dict.items() 
                                if k in valid_keys})
        
        return config
    except Exception as e:
        logger.warning(f"Failed to load config from file: {e}")
        return None
