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
from pathlib import Path
from typing import Dict, Optional, List, TYPE_CHECKING
from dataclasses import dataclass, field


def _resolve_qwenpaw_dir():
    env_dir = os.environ.get('QWENPAW_WORKING_DIR', '')
    if env_dir:
        resolved = Path(env_dir).expanduser().resolve()
        logger.debug(f"[qwenpaw_dir] using env QWENPAW_WORKING_DIR: {resolved}")
        return resolved
    try:
        from qwenpaw.constant import WORKING_DIR
        logger.debug(f"[qwenpaw_dir] using qwenpaw.constant.WORKING_DIR: {WORKING_DIR}")
        return WORKING_DIR
    except (ImportError, AttributeError):
        pass
    legacy = Path("~/.copaw").expanduser()
    if legacy.exists():
        resolved = legacy.resolve()
        logger.debug(f"[qwenpaw_dir] using legacy ~/.copaw: {resolved}")
        return resolved
    fallback = Path("~/.qwenpaw").expanduser().resolve()
    logger.info(f"[qwenpaw_dir] using fallback ~/.qwenpaw: {fallback}")
    return fallback


def _resolve_agent_workspace_dir(agent_id: str) -> Path:
    try:
        from qwenpaw.config.utils import load_config
        config = load_config()
        if agent_id in config.agents.profiles:
            ws_dir = config.agents.profiles[agent_id].workspace_dir
            resolved = Path(ws_dir).expanduser().resolve()
            logger.debug(f"[workspace_resolve] agent={agent_id} -> custom workspace: {resolved}")
            return resolved
        else:
            logger.warning(f"[workspace_resolve] agent={agent_id} not found in profiles, keys={list(config.agents.profiles.keys())}")
    except ImportError as e:
        logger.warning(f"[workspace_resolve] cannot import load_config: {e}")
    except Exception as e:
        logger.warning(f"[workspace_resolve] failed for agent={agent_id}: {e}", exc_info=True)
    fallback = _resolve_qwenpaw_dir() / "workspaces" / agent_id
    logger.info(f"[workspace_resolve] agent={agent_id} -> fallback: {fallback}")
    return fallback
from datetime import datetime, timedelta
import re

logger = logging.getLogger(__name__)

# 模块级别导入 HumanThinkingDB 以便测试 patch
# 使用 try/except 避免循环导入问题
try:
    from .database import HumanThinkingDB
except ImportError:
    HumanThinkingDB = None


# ========== 安全工具函数 ==========

_AGENT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]+$')
_MAX_AGENT_ID_LENGTH = 128


def _get_db_path(agent_id: str) -> str:
    """根据agent_id获取数据库文件路径
    
    Args:
        agent_id: Agent ID
        
    Returns:
        数据库文件路径字符串
    """
    base_dir = _resolve_agent_workspace_dir(agent_id)
    db_path = base_dir / "memory" / f"human_thinking_memory_{agent_id}.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return str(db_path)


def _get_db(agent_id: str):
    """创建并初始化数据库连接
    
    Args:
        agent_id: Agent ID
        
    Returns:
        初始化后的HumanThinkingDB实例
    """
    if HumanThinkingDB is None:
        from .database import HumanThinkingDB as DBClass
    else:
        DBClass = HumanThinkingDB
    
    db_path = _get_db_path(agent_id)
    db = DBClass(db_path)
    return db

def validate_agent_id(agent_id: Optional[str]) -> Optional[str]:
    """验证 agent_id 格式，防止路径遍历攻击
    
    Args:
        agent_id: Agent ID
        
    Returns:
        验证通过的 agent_id，或 None
        
    Raises:
        ValueError: 如果 agent_id 格式无效
    """
    if not agent_id:
        return None
    
    # 检查长度
    if len(agent_id) > _MAX_AGENT_ID_LENGTH:
        raise ValueError(f"agent_id too long: {len(agent_id)} > {_MAX_AGENT_ID_LENGTH}")
    
    # 检查格式：只允许字母、数字、下划线、连字符
    if not _AGENT_ID_PATTERN.match(agent_id):
        raise ValueError(f"Invalid agent_id format: {agent_id}")
    
    # 检查路径遍历特征
    if '..' in agent_id or '/' in agent_id or '\\' in agent_id:
        raise ValueError(f"agent_id contains path traversal characters: {agent_id}")
    
    return agent_id


def safe_path_join(base: Path, *parts: str) -> Path:
    """安全地拼接路径，防止路径遍历
    
    Args:
        base: 基础路径
        *parts: 路径组件
        
    Returns:
        解析后的安全路径
        
    Raises:
        ValueError: 如果结果路径超出基础路径范围
    """
    result = base.joinpath(*parts).resolve()
    base_resolved = base.resolve()
    
    # 确保结果路径在基础路径范围内
    try:
        result.relative_to(base_resolved)
    except ValueError:
        raise ValueError(f"Path traversal detected: {result} is outside {base_resolved}")
    
    return result


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
        self.last_active_time = time.time()
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

    def to_dict(self) -> dict:
        """将睡眠状态转换为字典"""
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
    
    支持Agent隔离：每个Agent独立维护自己的睡眠状态
    触发机制：
    1. 查询时触发：每次查询睡眠状态时，从数据库获取最后活动时间，实时计算
    2. 状态转换时执行对应的睡眠任务（每个阶段只执行一次）
    """
    
    def __init__(self, config: SleepConfig = None):
        self.config = config or SleepConfig()
        self._agent_states: Dict[str, AgentSleepState] = {}
        
        logger.info(f"SleepManager initialized: {self.config.__dict__}")
    
    def update_config(self, config: SleepConfig):
        """更新配置"""
        self.config = config
        logger.info(f"SleepManager config updated: {config.__dict__}")
    
    async def get_sleep_status(self, agent_id: str) -> dict:
        """获取Agent的睡眠状态（基于数据库查询的惰性计算）"""
        if not self.config.enable_agent_sleep:
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
            result["idle_time"] = int(current_time - state.last_active_time)
            result["next_sleep_in"] = -1
            return result
        
        last_activity_time = await self._get_last_activity_time(agent_id)
        if last_activity_time and last_activity_time > state.last_active_time:
            state.last_active_time = last_activity_time
        
        idle_time = current_time - state.last_active_time
        
        await self._update_sleep_state(agent_id, state, idle_time, current_time)
        
        result = state.to_dict()
        result["idle_time"] = int(idle_time)
        
        if state.is_active:
            result["next_sleep_in"] = max(0, self.config.light_sleep_seconds - idle_time)
        elif state.is_light_sleep:
            elapsed_in_stage = current_time - (state.last_light_sleep_time or state.last_active_time)
            result["next_sleep_in"] = max(0, self.config.rem_seconds - self.config.light_sleep_seconds - elapsed_in_stage)
        elif state.is_rem:
            elapsed_in_stage = current_time - (state.last_rem_time or state.last_active_time)
            result["next_sleep_in"] = max(0, self.config.deep_sleep_seconds - self.config.rem_seconds - elapsed_in_stage)
        else:
            result["next_sleep_in"] = -1
        
        return result
    
    async def _get_last_activity_time(self, agent_id: str) -> Optional[float]:
        """从数据库获取Agent的最后活动时间
        
        Returns:
            最后活动时间戳，如果没有记录则返回None
        """
        db = None
        try:
            if HumanThinkingDB is None:
                from .database import HumanThinkingDB as DBClass
            else:
                DBClass = HumanThinkingDB
            
            db = DBClass(_get_db_path(agent_id))
            await db.initialize()
            
            recent = await db.get_recent_memories(agent_id, days=365)
            if recent and len(recent) > 0:
                ts = recent[0].get("created_at") or recent[0].get("timestamp")
                if ts:
                    dt = datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
                    return dt.timestamp()
            
            return None
        except Exception as e:
            logger.warning(f"Failed to get last activity time for {agent_id}: {e}")
            return None
        finally:
            if db:
                try:
                    await db.close()
                except Exception:
                    pass
    
    async def _update_sleep_state(self, agent_id: str, state: AgentSleepState, idle_time: float, current_time: float):
        """根据空闲时间更新睡眠状态并执行对应任务
        
        Args:
            agent_id: Agent ID
            state: Agent睡眠状态
            idle_time: 空闲时间（秒）
            current_time: 当前时间戳
        """
        if not self.config.enable_agent_sleep:
            return
        
        # 状态转换逻辑 - 按顺序执行，不跳过中间阶段
        if idle_time >= self.config.light_sleep_seconds and state.is_active:
            logger.info(f"Agent {agent_id} entering light sleep (idle {idle_time:.0f}s)")
            await self._enter_light_sleep(state, current_time)
        
        if idle_time >= self.config.rem_seconds and state.is_light_sleep and not state.is_rem and not state.is_deep_sleep:
            logger.info(f"Agent {agent_id} entering REM (idle {idle_time:.0f}s)")
            await self._enter_rem(state, current_time)
        
        if idle_time >= self.config.deep_sleep_seconds and state.is_rem and not state.is_deep_sleep:
            logger.info(f"Agent {agent_id} entering deep sleep (idle {idle_time:.0f}s)")
            await self._enter_deep_sleep(state, current_time)
        
        # 如果空闲时间超过深睡阈值但跳过了中间阶段，按顺序补执行
        if idle_time >= self.config.deep_sleep_seconds and not state.is_deep_sleep:
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
        if idle_time >= self.config.rem_seconds and not state.is_rem and not state.is_deep_sleep:
            if state.is_active:
                logger.info(f"Agent {agent_id} fast-forwarding: active -> light sleep (idle {idle_time:.0f}s)")
                await self._enter_light_sleep(state, current_time)
            if state.is_light_sleep and not state.is_rem:
                logger.info(f"Agent {agent_id} fast-forwarding: light sleep -> REM (idle {idle_time:.0f}s)")
                await self._enter_rem(state, current_time)
        
        # 如果空闲时间低于浅睡阈值，恢复活跃状态
        if idle_time < self.config.light_sleep_seconds and not state.is_active:
            logger.info(f"Agent {agent_id} waking up to active")
            self._reset_to_active(state)
    
    async def _enter_light_sleep(self, state: AgentSleepState, current_time: float):
        """进入浅层睡眠"""
        state.is_active = False
        state.is_light_sleep = True
        state.is_rem = False
        state.is_deep_sleep = False
        state.last_light_sleep_time = current_time
        
        # 执行浅睡任务（只执行一次）
        if not state._light_sleep_executed:
            state._light_sleep_executed = True
            await self._execute_light_sleep(state.agent_id, state)
    
    async def _enter_rem(self, state: AgentSleepState, current_time: float):
        """进入REM阶段"""
        state.is_active = False
        state.is_light_sleep = False
        state.is_rem = True
        state.is_deep_sleep = False
        state.last_rem_time = current_time
        
        # 执行REM任务（只执行一次）
        if not state._rem_executed:
            state._rem_executed = True
            await self._execute_rem(state.agent_id, state)
    
    async def _enter_deep_sleep(self, state: AgentSleepState, current_time: float):
        """进入深层睡眠"""
        state.is_active = False
        state.is_light_sleep = False
        state.is_rem = False
        state.is_deep_sleep = True
        state.last_deep_sleep_time = current_time
        
        # 执行深睡任务（只执行一次）
        if not state._deep_sleep_executed:
            state._deep_sleep_executed = True
            await self._execute_deep_sleep(state.agent_id, state)
    
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
        """强制进入浅睡"""
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        state = self._agent_states[agent_id]
        self._reset_to_active(state)
        await self._enter_light_sleep(state, time.time())
        state.forced_state = "light_sleep"
        return {"success": True, "agent_id": agent_id, "status": "light_sleep"}
    
    async def force_rem(self, agent_id: str) -> dict:
        """强制进入REM"""
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        state = self._agent_states[agent_id]
        self._reset_to_active(state)
        await self._enter_light_sleep(state, time.time())
        await self._enter_rem(state, time.time())
        state.forced_state = "rem"
        return {"success": True, "agent_id": agent_id, "status": "rem"}
    
    async def force_deep_sleep(self, agent_id: str) -> dict:
        """强制进入深睡"""
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        state = self._agent_states[agent_id]
        self._reset_to_active(state)
        await self._enter_light_sleep(state, time.time())
        await self._enter_rem(state, time.time())
        await self._enter_deep_sleep(state, time.time())
        state.forced_state = "deep_sleep"
        return {"success": True, "agent_id": agent_id, "status": "deep_sleep"}
    
    async def wakeup(self, agent_id: str) -> dict:
        """唤醒Agent"""
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        state = self._agent_states[agent_id]
        self._reset_to_active(state)
        state.forced_state = None
        state.last_active_time = time.time()
        return {"success": True, "agent_id": agent_id, "status": "active"}
    
    async def record_activity(self, agent_id: str) -> bool:
        """记录Agent活动（由消息钩子调用）
        
        当Agent响应消息时调用此方法：
        - 如果Agent处于深睡状态，唤醒它
        - 更新最后活动时间
        
        Returns:
            True 表示Agent被唤醒
        """
        if not self.config.enable_agent_sleep:
            return False
        
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        
        state = self._agent_states[agent_id]
        current_time = time.time()
        
        if not state.is_active:
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
            if HumanThinkingDB is None:
                from .database import HumanThinkingDB as DBClass
            else:
                DBClass = HumanThinkingDB
            
            db = DBClass(_get_db_path(agent_id))
            await db.initialize()
            
            if self.config.enable_dream_log:
                await db.add_dream_log(agent_id, "LIGHT_SLEEP", "阶段一：浅层睡眠 - 扫描7天日志，去重过滤")
            
            memories = await db.get_recent_memories(agent_id, days=7)
            
            if not memories:
                logger.info(f"No memories to process in light sleep")
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
            if HumanThinkingDB is None:
                from .database import HumanThinkingDB as DBClass
            else:
                DBClass = HumanThinkingDB
            
            db = DBClass(_get_db_path(agent_id))
            await db.initialize()
            
            if self.config.enable_dream_log:
                await db.add_dream_log(agent_id, "REM", "阶段二：REM - 提取主题，发现跨对话模式")
            
            # 提取主题
            themes = self._extract_themes(state.pending_importance)
            
            # 发现持久真理
            truths = self._discover_truths(state.pending_importance)
            state.lasting_truths = truths
            
            # 生成反思摘要
            if self.config.enable_insight:
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
            if HumanThinkingDB is None:
                from .database import HumanThinkingDB as DBClass
            else:
                DBClass = HumanThinkingDB
            
            db = DBClass(_get_db_path(agent_id))
            await db.initialize()
            
            if self.config.enable_dream_log:
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
            
            
            await self._archive_and_freeze(db, agent_id)
            
            if self.config.auto_consolidate:
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
    
    async def _apply_forgetting_curve(self, db, agent_id: str):
        """应用遗忘曲线算法"""
        try:
            await db.apply_forgetting_curve(
                agent_id,
                frozen_days=self.config.frozen_days,
                archive_days=self.config.archive_days,
                delete_days=self.config.delete_days
            )
        except Exception as e:
            logger.error(f"Error applying forgetting curve: {e}", exc_info=True)
    
    async def _archive_and_freeze(self, db, agent_id: str):
        """归档和冻结记忆"""
        try:
            await db.apply_forgetting_curve(
                agent_id,
                frozen_days=self.config.frozen_days,
                archive_days=self.config.archive_days,
                delete_days=self.config.delete_days
            )
        except Exception as e:
            logger.error(f"Error archiving and freezing: {e}", exc_info=True)
    
    async def _consolidate_memories(self, db, agent_id: str):
        """整合记忆"""
        try:
            if not self.config.auto_consolidate:
                return
            
            memories = await db.get_memories_for_consolidation(
                agent_id, days=self.config.consolidate_days
            )
            if not memories:
                return
            
            if self.config.enable_contradiction_detection:
                from .contradiction_detector import batch_detect_contradictions, ConflictResolutionStrategy
                
                strategy_map = {
                    "keep_latest": ConflictResolutionStrategy.KEEP_LATEST,
                    "keep_frequent": ConflictResolutionStrategy.KEEP_FREQUENT,
                    "keep_high_confidence": ConflictResolutionStrategy.KEEP_HIGH_CONFIDENCE,
                    "keep_both": ConflictResolutionStrategy.KEEP_BOTH,
                    "mark_for_review": ConflictResolutionStrategy.MARK_FOR_REVIEW,
                }
                resolution_strategy = strategy_map.get(
                    self.config.contradiction_resolution_strategy,
                    ConflictResolutionStrategy.KEEP_LATEST
                )
                
                contradictions = batch_detect_contradictions(
                    memories,
                    enable_semantic_check=self.config.enable_semantic_contradiction_check,
                    enable_temporal_check=self.config.enable_temporal_contradiction_check,
                    enable_confidence_scoring=self.config.enable_confidence_scoring,
                    contradiction_threshold=self.config.contradiction_threshold,
                    auto_resolve=self.config.auto_resolve_contradiction,
                    min_confidence_for_auto=self.config.min_confidence_for_auto_resolve,
                    resolution_strategy=resolution_strategy,
                )
                for i, j, result in contradictions:
                    if result.is_contradiction and result.suggested_loser:
                        loser_id = result.suggested_loser.get("id")
                        if loser_id:
                            if self.config.auto_resolve_contradiction and result.confidence >= self.config.min_confidence_for_auto_resolve:
                                await db.archive_memory(loser_id)
                            else:
                                logger.info(f"Contradiction detected but not auto-resolved (confidence={result.confidence:.2f}): {result.explanation}")
            
            if self.config.enable_merge:
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
        
        merged_count = 0
        threshold = self.config.merge_similarity_threshold
        max_distance_hours = self.config.merge_max_distance_hours
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
            if not self.config.memory_md_path:
                return
            
            md_path = Path(self.config.memory_md_path)
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
        logger.info(f"Agent {agent_id} woke up by new activity")
        _sleep_manager._reset_to_active(state)
    
    state.forced_state = None


def pulse_agent(agent_id: str) -> None:
    """Agent心跳（由消息处理流程调用）
    
    与record_agent_activity相同，保持兼容性。
    当Agent参与消息交互时调用。
    
    Args:
        agent_id: Agent ID
    """
    record_agent_activity(agent_id)


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
    if _sleep_manager is None or not _sleep_manager.config.enable_agent_sleep:
        return False
    
    if agent_id not in _sleep_manager._agent_states:
        _sleep_manager._agent_states[agent_id] = AgentSleepState(agent_id)
    
    state = _sleep_manager._agent_states[agent_id]
    current_time = time.time()
    
    idle_time = current_time - state.last_active_time
    return idle_time >= _sleep_manager.config.light_sleep_seconds


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
    
    如果有全局sleep_manager，返回其配置；否则返回默认配置
    
    Args:
        agent_id: Agent ID（可选）
        
    Returns:
        SleepConfig实例
    """
    global _sleep_manager
    if _sleep_manager is not None:
        return _sleep_manager.config
    return SleepConfig()


def save_agent_sleep_config(agent_id: str, config: SleepConfig) -> bool:
    """保存Agent的睡眠配置
    
    更新全局sleep_manager的配置（如果存在）
    
    Args:
        agent_id: Agent ID
        config: 新的睡眠配置
        
    Returns:
        是否保存成功
    """
    global _sleep_manager
    try:
        if _sleep_manager is not None:
            _sleep_manager.update_config(config)
        # 同时保存到文件以便持久化
        _save_config_to_file(agent_id, config)
        return True
    except Exception as e:
        logger.error(f"Failed to save sleep config for {agent_id}: {e}")
        return False


def load_agent_sleep_config(agent_id: str) -> SleepConfig:
    """加载Agent的睡眠配置
    
    优先从文件加载，如果失败则返回全局配置或默认配置
    
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
    
    global _sleep_manager
    if _sleep_manager is not None:
        return _sleep_manager.config
    return SleepConfig()


# Agent配置缓存（内存中）
_agent_sleep_configs: Dict[str, SleepConfig] = {}


def _get_config_path(agent_id: str) -> Path:
    """获取Agent配置文件路径"""
    return _resolve_agent_workspace_dir(agent_id) / "memory" / "sleep_config.json"


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
