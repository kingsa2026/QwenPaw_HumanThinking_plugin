# -*- coding: utf-8 -*-
"""
HumanThinking 睡眠管理器

功能：
- 监控 Agent 会话空闲时间
- 空闲超过阈值自动进入睡眠
- 有新会话自动唤醒
- 睡眠时自动整理记忆
"""

import asyncio
import logging
import time
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


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
    
    def __init__(
        self,
        sleep_idle_hours: int = 2,
        enable_sleep: bool = True,
        auto_consolidate: bool = True,
        consolidate_interval_hours: int = 6
    ):
        self.enable_sleep = enable_sleep
        self.sleep_idle_seconds = sleep_idle_hours * 3600
        self.auto_consolidate = auto_consolidate
        self.consolidate_interval_seconds = consolidate_interval_hours * 3600
        
        self._agent_states: Dict[str, AgentSleepState] = {}
        self._monitor_task: Optional[asyncio.Task] = None
        self._running = False
        
        logger.info(f"SleepManager initialized: enable={enable_sleep}, "
                   f"idle={sleep_idle_hours}h, consolidate={auto_consolidate}")
    
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
            # 从睡眠中唤醒
            state.is_sleeping = False
            state.sleep_start_time = None
            logger.info(f"Agent {agent_id} woke up from sleep")
        
        state.last_active_time = time.time()
        logger.debug(f"Agent {agent_id} activity recorded, last_active: {datetime.fromtimestamp(state.last_active_time)}")
    
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
        """监控循环 - 检查是否需要进入睡眠"""
        while self._running:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                
                if not self.enable_sleep:
                    continue
                
                current_time = time.time()
                
                for agent_id, state in list(self._agent_states.items()):
                    if state.is_sleeping:
                        # 检查是否需要自动整理
                        if self.auto_consolidate:
                            await self._maybe_consolidate(agent_id, state, current_time)
                    else:
                        # 检查是否需要进入睡眠
                        idle_time = current_time - state.last_active_time
                        if idle_time >= self.sleep_idle_seconds:
                            await self._enter_sleep(agent_id, state, current_time)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sleep monitor loop: {e}", exc_info=True)
    
    async def _enter_sleep(self, agent_id: str, state: AgentSleepState, current_time: float):
        """让 Agent 进入睡眠状态"""
        state.is_sleeping = True
        state.sleep_start_time = current_time
        
        logger.info(
            f"Agent {agent_id} entering sleep mode "
            f"(idle for {current_time - state.last_active_time:.0f}s)"
        )
        
        # 触发睡眠回调 - 可以在这里清理资源
        await self._on_agent_sleep(agent_id)
    
    async def _on_agent_sleep(self, agent_id: str):
        """Agent 进入睡眠时的回调"""
        logger.info(f"Agent {agent_id} sleep callback triggered")
        # 这里可以添加清理缓存、释放资源等逻辑
    
    async def _maybe_consolidate(
        self, 
        agent_id: str, 
        state: AgentSleepState, 
        current_time: float
    ):
        """检查是否需要整理记忆"""
        if state.last_consolidate_time is None:
            need_consolidate = True
        else:
            elapsed = current_time - state.last_consolidate_time
            need_consolidate = elapsed >= self.consolidate_interval_seconds
        
        if need_consolidate:
            logger.info(f"Agent {agent_id} consolidating memories during sleep...")
            await self._consolidate_memories(agent_id)
            state.last_consolidate_time = current_time
    
    async def _consolidate_memories(self, agent_id: str):
        """整理 Agent 的记忆
        
        睡眠时自动整理对话经验，生成为持久化固定记忆
        按四种类型分类存储：fact, preference, emotion, general
        """
        logger.info(f"Consolidating memories for agent {agent_id}")
        
        # TODO: 实现具体的记忆整理逻辑
        # 1. 从数据库读取近期对话
        # 2. 使用 LLM 分析并分类
        # 3. 生成结构化的持久记忆
        # 4. 按类型存储到数据库
        
        pass
    
    def get_status(self, agent_id: str) -> dict:
        """获取 Agent 睡眠状态"""
        state = self._agent_states.get(agent_id)
        if not state:
            return {
                "agent_id": agent_id,
                "is_sleeping": False,
                "last_active": None,
                "sleep_duration": 0
            }
        
        current_time = time.time()
        sleep_duration = 0
        if state.sleep_start_time:
            sleep_duration = current_time - state.sleep_start_time
        
        return {
            "agent_id": agent_id,
            "is_sleeping": state.is_sleeping,
            "last_active": datetime.fromtimestamp(state.last_active_time).isoformat(),
            "sleep_duration_seconds": sleep_duration,
            "last_consolidate": (
                datetime.fromtimestamp(state.last_consolidate_time).isoformat()
                if state.last_consolidate_time else None
            )
        }


# 全局睡眠管理器实例
_sleep_manager: Optional[SleepManager] = None


def get_sleep_manager() -> Optional[SleepManager]:
    """获取全局睡眠管理器"""
    return _sleep_manager


def init_sleep_manager(
    enable_sleep: bool = True,
    sleep_idle_hours: int = 2,
    auto_consolidate: bool = True,
    consolidate_interval_hours: int = 6
) -> SleepManager:
    """初始化睡眠管理器"""
    global _sleep_manager
    
    if _sleep_manager:
        _sleep_manager.stop()
    
    _sleep_manager = SleepManager(
        enable_sleep=enable_sleep,
        sleep_idle_hours=sleep_idle_hours,
        auto_consolidate=auto_consolidate,
        consolidate_interval_hours=consolidate_interval_hours
    )
    _sleep_manager.start()
    
    logger.info(f"SleepManager initialized with config: "
               f"enable={enable_sleep}, idle={sleep_idle_hours}h, "
               f"consolidate={auto_consolidate}, interval={consolidate_interval_hours}h")
    
    return _sleep_manager


def record_agent_activity(agent_id: str):
    """记录 Agent 活动 - 唤醒"""
    if _sleep_manager:
        _sleep_manager.record_activity(agent_id)


def is_agent_sleeping(agent_id: str) -> bool:
    """检查 Agent 是否在睡眠"""
    if _sleep_manager:
        return _sleep_manager.is_sleeping(agent_id)
    return False
