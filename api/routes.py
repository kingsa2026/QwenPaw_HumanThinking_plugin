# -*- coding: utf-8 -*-
"""
HumanThinking API Routes

提供记忆管理、睡眠管理和情感计算的RESTful API
"""

import logging
import time
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger("qwenpaw.humanthinking")

router = APIRouter()


# ============ 请求/响应模型 ============

class StatsResponse(BaseModel):
    total_memories: int = 0
    cross_session_memories: int = 0
    frozen_memories: int = 0
    active_sessions: int = 0
    emotional_states: int = 0


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(10, ge=1, le=50)


class SearchResponse(BaseModel):
    memories: list
    total: int
    query: str


class MemoryUpdateRequest(BaseModel):
    content: Optional[str] = Field(None, max_length=5000)
    memory_type: Optional[str] = Field(None, pattern="^(fact|preference|event|insight)$")
    importance: Optional[float] = Field(None, ge=0.0, le=1.0)


class BatchDeleteRequest(BaseModel):
    memory_ids: List[str] = Field(..., min_length=1)


class SessionRenameRequest(BaseModel):
    session_name: str = Field(..., min_length=1, max_length=100)


class BatchDeleteSessionsRequest(BaseModel):
    session_ids: List[str] = Field(..., min_length=1)


class ConfigUpdateRequest(BaseModel):
    enable_cross_session: Optional[bool] = None
    enable_emotion: Optional[bool] = None
    frozen_days: Optional[int] = Field(None, ge=7, le=365)
    archive_days: Optional[int] = Field(None, ge=30, le=730)
    delete_days: Optional[int] = Field(None, ge=90, le=1095)
    max_results: Optional[int] = Field(None, ge=1, le=50)
    session_idle_timeout: Optional[int] = Field(None, ge=60, le=3600)
    refresh_interval: Optional[int] = Field(None, ge=1, le=60)
    max_memory_chars: Optional[int] = Field(None, ge=50, le=1000)
    enable_distributed_db: Optional[bool] = None
    db_size_threshold_mb: Optional[int] = Field(None, ge=100, le=5000)


class SleepConfigUpdateRequest(BaseModel):
    enable_agent_sleep: Optional[bool] = None
    light_sleep_minutes: Optional[int] = Field(None, ge=1, le=120)
    rem_minutes: Optional[int] = Field(None, ge=1, le=60)
    deep_sleep_minutes: Optional[int] = Field(None, ge=5, le=240)
    consolidate_days: Optional[int] = Field(None, ge=1, le=30)
    frozen_days: Optional[int] = Field(None, ge=7, le=365)
    archive_days: Optional[int] = Field(None, ge=30, le=730)
    delete_days: Optional[int] = Field(None, ge=90, le=1095)
    enable_insight: Optional[bool] = None
    enable_dream_log: Optional[bool] = None


class ForceSleepRequest(BaseModel):
    sleep_type: str = Field(..., pattern="^(light|deep|rem)$")


# ============ 全局状态存储 ============

_sleep_manager = None
_memory_managers = {}
_MAX_MEMORY_MANAGERS = 100  # 防止内存泄漏


def get_sleep_manager():
    """获取或创建睡眠管理器（单例模式）"""
    global _sleep_manager
    if _sleep_manager is None:
        try:
            from ..core.sleep_manager import SleepManager, SleepConfig
            _sleep_manager = SleepManager(SleepConfig())
        except Exception as e:
            logger.error(f"Failed to create sleep manager: {e}")
            raise
    return _sleep_manager


def get_memory_manager(agent_id: str = None):
    """获取或创建记忆管理器（带LRU清理）"""
    global _memory_managers
    
    # 防止内存泄漏：限制最大实例数
    if len(_memory_managers) >= _MAX_MEMORY_MANAGERS:
        # 移除最早的实例
        oldest_key = next(iter(_memory_managers))
        del _memory_managers[oldest_key]
        logger.warning(f"Memory managers exceeded limit, removed {oldest_key}")
    
    if agent_id not in _memory_managers:
        try:
            from ..core.memory_manager import HumanThinkingMemoryManager
            _memory_managers[agent_id] = HumanThinkingMemoryManager(agent_id=agent_id)
        except Exception as e:
            logger.error(f"Failed to create memory manager for {agent_id}: {e}")
            raise
    
    return _memory_managers[agent_id]


# ============ 辅助函数 ============

def _handle_db_operation(operation_name: str, operation_func, fallback_result=None):
    """统一处理数据库操作，避免裸except"""
    try:
        return operation_func()
    except ImportError as e:
        logger.debug(f"{operation_name}: module not available - {e}")
        return fallback_result
    except Exception as e:
        logger.error(f"{operation_name} failed: {e}")
        return fallback_result


# ============ API 路由 ============

from .error_handler import handle_api_errors


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "plugin": "humanthinking",
        "version": "1.4.1",
        "timestamp": time.time()
    }


@router.get("/stats", response_model=StatsResponse)
@handle_api_errors(
    operation_name="get_stats",
    allow_fallback=False
)
async def get_stats(agent_id: Optional[str] = None):
    """获取记忆统计信息"""
    from ..core.database import HumanThinkingDB
    db = HumanThinkingDB()

    if not hasattr(db, 'get_stats'):
        raise HTTPException(
            status_code=501,
            detail="Database method 'get_stats' not implemented"
        )

    stats = db.get_stats(agent_id)
    return StatsResponse(
        total_memories=stats.get('total', 0),
        cross_session_memories=stats.get('cross_session', 0),
        frozen_memories=stats.get('frozen', 0),
        active_sessions=stats.get('active_sessions', 0),
        emotional_states=stats.get('emotional_states', 0)
    )


@router.post("/search", response_model=SearchResponse)
@handle_api_errors(
    operation_name="search_memories",
    allow_fallback=False
)
async def search_memories(request: SearchRequest, agent_id: Optional[str] = None):
    """搜索记忆"""
    from ..core.database import HumanThinkingDB
    db = HumanThinkingDB()

    if not hasattr(db, 'memory_search'):
        raise HTTPException(
            status_code=501,
            detail="Database method 'memory_search' not implemented"
        )

    results = db.memory_search(
        query=request.query,
        agent_id=agent_id,
        limit=request.limit
    )

    return SearchResponse(
        memories=results,
        total=len(results),
        query=request.query
    )


@router.put("/memories/{memory_id}")
async def update_memory(memory_id: str, request: MemoryUpdateRequest):
    """更新记忆内容/类型/重要性"""
    try:
        from ..core.database import HumanThinkingDB
        db = HumanThinkingDB()
        
        update_data = {}
        if request.content is not None:
            update_data['content'] = request.content
        if request.memory_type is not None:
            update_data['memory_type'] = request.memory_type
        if request.importance is not None:
            update_data['importance'] = request.importance
        
        if hasattr(db, 'update_memory'):
            db.update_memory(memory_id, **update_data)
            logger.info(f"Memory {memory_id} updated: {list(update_data.keys())}")
        
        return {"success": True, "memory_id": memory_id, "updated": update_data}
    except Exception as e:
        logger.error(f"Failed to update memory {memory_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memories/batch")
async def batch_delete_memories(request: BatchDeleteRequest):
    """批量删除记忆"""
    try:
        from ..core.database import HumanThinkingDB
        db = HumanThinkingDB()
        
        deleted_count = 0
        for memory_id in request.memory_ids:
            if hasattr(db, 'delete_memory'):
                db.delete_memory(memory_id)
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} memories")
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"Failed to batch delete memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotion")
@handle_api_errors(
    operation_name="get_emotion_context",
    allow_fallback=False
)
async def get_emotion_context(
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """获取情感状态"""
    from ..core.emotional_engine import EmotionalContinuityEngine
    engine = EmotionalContinuityEngine()

    if not hasattr(engine, 'get_emotional_context'):
        raise HTTPException(
            status_code=501,
            detail="Engine method 'get_emotional_context' not implemented"
        )

    emotion = engine.get_emotional_context(agent_id, user_id)
    if emotion:
        return emotion

    # 返回空数据表示没有找到情感状态
    return {
        "current_emotion": "neutral",
        "intensity": 0.0,
        "history": []
    }


@router.get("/sessions")
@handle_api_errors(
    operation_name="get_sessions",
    allow_fallback=False
)
async def get_sessions(
    agent_id: Optional[str] = None,
    active_only: bool = True
):
    """获取会话列表"""
    from ..core.database import HumanThinkingDB
    db = HumanThinkingDB()

    if not hasattr(db, 'get_sessions'):
        raise HTTPException(
            status_code=501,
            detail="Database method 'get_sessions' not implemented"
        )

    sessions = db.get_sessions(agent_id, active_only)
    return sessions if sessions else []


@router.put("/sessions/{session_id}/rename")
async def rename_session(session_id: str, request: SessionRenameRequest):
    """重命名会话"""
    try:
        from ..core.database import HumanThinkingDB
        db = HumanThinkingDB()
        
        if hasattr(db, 'update_session_name'):
            db.update_session_name(session_id, request.session_name)
            logger.info(f"Session {session_id} renamed to: {request.session_name}")
        
        return {"success": True, "session_id": session_id, "session_name": request.session_name}
    except Exception as e:
        logger.error(f"Failed to rename session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除单个会话"""
    try:
        from ..core.database import HumanThinkingDB
        db = HumanThinkingDB()
        
        if hasattr(db, 'delete_session'):
            db.delete_session(session_id)
            logger.info(f"Session {session_id} deleted")
        
        return {"success": True, "deleted_count": 1}
    except Exception as e:
        logger.error(f"Failed to delete session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/batch-delete")
async def batch_delete_sessions(request: BatchDeleteSessionsRequest):
    """批量删除会话"""
    try:
        from ..core.database import HumanThinkingDB
        db = HumanThinkingDB()
        
        deleted_count = 0
        for session_id in request.session_ids:
            if hasattr(db, 'delete_session'):
                db.delete_session(session_id)
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} sessions")
        return {"success": True, "deleted_count": deleted_count}
    except Exception as e:
        logger.error(f"Failed to batch delete sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/detail")
async def get_session_detail(session_id: str):
    """获取会话详情"""
    try:
        from ..core.database import HumanThinkingDB
        db = HumanThinkingDB()
        
        session = {}
        if hasattr(db, 'get_session'):
            session = db.get_session(session_id)
        
        memories = []
        if hasattr(db, 'get_session_memories'):
            memories = db.get_session_memories(session_id)
        
        return {
            "session_id": session_id,
            "session_name": session.get('session_name', '未命名会话'),
            "user_name": session.get('user_name', ''),
            "messages": [],
            "memories": memories
        }
    except Exception as e:
        logger.error(f"Failed to get session detail {session_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories/recent")
@handle_api_errors(
    operation_name="get_recent_memories",
    allow_fallback=False
)
async def get_recent_memories(
    limit: int = Query(20, ge=1, le=100),
    session_id: Optional[str] = None
):
    """获取最近记忆"""
    from ..core.database import HumanThinkingDB
    db = HumanThinkingDB()

    if not hasattr(db, 'get_recent_memories'):
        raise HTTPException(
            status_code=501,
            detail="Database method 'get_recent_memories' not implemented"
        )

    memories = db.get_recent_memories(limit, session_id)
    return {"memories": memories if memories else [], "total": len(memories) if memories else 0}


@router.get("/memories/timeline")
@handle_api_errors(
    operation_name="get_memory_timeline",
    allow_fallback=False
)
async def get_memory_timeline(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_id: Optional[str] = None
):
    """获取记忆时间线"""
    from ..core.database import HumanThinkingDB
    db = HumanThinkingDB()

    if not hasattr(db, 'get_memory_timeline'):
        raise HTTPException(
            status_code=501,
            detail="Database method 'get_memory_timeline' not implemented"
        )

    timeline = db.get_memory_timeline(start_date, end_date, agent_id)
    return timeline if timeline else []


@router.get("/config")
async def get_config(agent_id: Optional[str] = None):
    """获取HumanThinking配置（支持按Agent隔离）"""
    try:
        from ..core.memory_manager import get_config
        effective_agent_id = agent_id if agent_id else None
        config = get_config(agent_id=effective_agent_id)
        return {
            "enable_cross_session": config.enable_cross_session,
            "enable_emotion": config.enable_emotion,
            "frozen_days": config.frozen_days,
            "archive_days": config.archive_days,
            "delete_days": config.delete_days,
            "max_results": config.max_results,
            "session_idle_timeout": config.session_idle_timeout,
            "refresh_interval": config.refresh_interval,
            "max_memory_chars": config.max_memory_chars,
            "enable_distributed_db": config.enable_distributed_db,
            "db_size_threshold_mb": config.db_size_threshold_mb,
            "disable_file_memory": config.disable_file_memory,
        }
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_config(request: Request, agent_id: Optional[str] = None):
    """更新HumanThinking配置（支持按Agent隔离）"""
    try:
        from ..core.memory_manager import get_config, save_config, update_config_fields
        
        # 直接读取JSON数据，支持前端发送的完整配置对象
        data = await request.json()
        effective_agent_id = agent_id if agent_id else None
        config = get_config(agent_id=effective_agent_id)
        
        update_fields = {}
        field_mapping = {
            'enable_cross_session': data.get('enable_cross_session'),
            'enable_emotion': data.get('enable_emotion'),
            'frozen_days': data.get('frozen_days'),
            'archive_days': data.get('archive_days'),
            'delete_days': data.get('delete_days'),
            'max_results': data.get('max_results'),
            'session_idle_timeout': data.get('session_idle_timeout'),
            'refresh_interval': data.get('refresh_interval'),
            'max_memory_chars': data.get('max_memory_chars'),
            'enable_distributed_db': data.get('enable_distributed_db'),
            'db_size_threshold_mb': data.get('db_size_threshold_mb'),
        }
        
        for field_name, value in field_mapping.items():
            if value is not None:
                setattr(config, field_name, value)
                update_fields[field_name] = value
        
        if update_fields:
            update_config_fields(update_fields, agent_id=effective_agent_id)
        
        success = save_config(config, agent_id=effective_agent_id)
        if not success:
            return {"success": False, "message": "配置保存失败，请检查日志"}
        
        # 保存配置时自动初始化数据库（如果尚未初始化）
        try:
            from ..core.memory_manager import HumanThinkingMemoryManager
            import os
            from pathlib import Path
            
            # 获取当前 agent 的工作目录
            if effective_agent_id:
                working_dir = str(Path.home() / ".qwenpaw" / "workspaces" / effective_agent_id)
            else:
                working_dir = str(Path.home() / ".qwenpaw" / "workspaces" / "default")
            
            db_path = Path(working_dir) / "memory" / f"human_thinking_memory_{effective_agent_id or 'default'}.db"
            
            if not db_path.exists():
                # 数据库不存在，创建并初始化
                Path(working_dir).mkdir(parents=True, exist_ok=True)
                mm = HumanThinkingMemoryManager(
                    working_dir=working_dir,
                    agent_id=effective_agent_id or "default",
                    user_id=None
                )
                await mm.start()
                logger.info(f"Database auto-created on config save: {mm.db_path}")
        except Exception as db_err:
            logger.warning(f"Failed to auto-create database on config save: {db_err}")
        
        logger.info(f"Config updated for agent {effective_agent_id}: {list(update_fields.keys())}")
        return {"success": True, "config": data}
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dreams")
async def get_dreams(
    limit: int = Query(10, ge=1, le=50)
):
    """获取梦境记录（睡眠期间生成的摘要）"""
    def _get_real_dreams():
        from ..core.database import HumanThinkingDB
        db = HumanThinkingDB()
        if hasattr(db, 'get_dreams'):
            return db.get_dreams(limit)
        return []
    
    dreams = _handle_db_operation("get_dreams", _get_real_dreams, [])
    return dreams


# ============ 睡眠管理 API ============

@router.get("/sleep/status")
async def get_sleep_status(agent_id: Optional[str] = None):
    """获取睡眠状态"""
    try:
        manager = get_sleep_manager()
        state = manager.get_agent_state(agent_id) if hasattr(manager, 'get_agent_state') else None
        
        if state:
            return {
                "status": "active" if state.is_active else "sleeping",
                "sleep_type": "deep" if state.is_deep_sleep else ("rem" if state.is_rem else ("light" if state.is_light_sleep else None)),
                "last_active_time": state.last_active_time,
            }
        
        return {
            "status": "active",
            "sleep_type": None,
            "last_active_time": time.time()
        }
    except Exception as e:
        logger.error(f"Failed to get sleep status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sleep/config")
async def get_sleep_config(agent_id: Optional[str] = None):
    """获取睡眠配置（支持按Agent隔离）"""
    try:
        # 如果有 agent_id，尝试加载该 Agent 的专属配置
        if agent_id:
            from ..core.sleep_manager import load_agent_sleep_config
            config = load_agent_sleep_config(agent_id)
        else:
            manager = get_sleep_manager()
            config = manager.config if manager else SleepConfig()
        
        return {
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
        }
    except Exception as e:
        logger.error(f"Failed to get sleep config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sleep/config")
async def update_sleep_config(request: SleepConfigUpdateRequest, agent_id: Optional[str] = None):
    """更新睡眠配置（支持按Agent隔离）"""
    try:
        from ..core.sleep_manager import get_agent_sleep_config, save_agent_sleep_config
        
        # 获取当前配置（Agent 专属或全局）
        config = get_agent_sleep_config(agent_id)
        
        if request.enable_agent_sleep is not None:
            config.enable_agent_sleep = request.enable_agent_sleep
        if request.light_sleep_minutes is not None:
            config.light_sleep_minutes = request.light_sleep_minutes
        if request.rem_minutes is not None:
            config.rem_minutes = request.rem_minutes
        if request.deep_sleep_minutes is not None:
            config.deep_sleep_minutes = request.deep_sleep_minutes
        if request.consolidate_days is not None:
            config.consolidate_days = request.consolidate_days
        if request.frozen_days is not None:
            config.frozen_days = request.frozen_days
        if request.archive_days is not None:
            config.archive_days = request.archive_days
        if request.delete_days is not None:
            config.delete_days = request.delete_days
        if request.enable_insight is not None:
            config.enable_insight = request.enable_insight
        if request.enable_dream_log is not None:
            config.enable_dream_log = request.enable_dream_log
        
        # 如果有 agent_id，保存到 Agent 专属配置
        if agent_id:
            success = save_agent_sleep_config(agent_id, config)
            if not success:
                return {"success": False, "message": "配置保存失败，请检查日志"}
        else:
            # 更新全局配置
            manager = get_sleep_manager()
            if manager:
                manager.update_config(config)
        
        logger.info(f"Sleep config updated for agent {agent_id}: {request.model_dump(exclude_unset=True)}")
        return {"success": True, "config": request.model_dump(exclude_unset=True)}
    except Exception as e:
        logger.error(f"Failed to update sleep config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sleep/force")
async def force_sleep(request: ForceSleepRequest, agent_id: Optional[str] = None):
    """强制进入睡眠"""
    try:
        manager = get_sleep_manager()
        
        sleep_methods = {
            "light": "force_light_sleep",
            "rem": "force_rem",
            "deep": "force_deep_sleep"
        }
        
        method_name = sleep_methods.get(request.sleep_type)
        if method_name and hasattr(manager, method_name):
            getattr(manager, method_name)(agent_id)
            logger.info(f"Forced {request.sleep_type} sleep for agent {agent_id}")
        
        return {"success": True, "sleep_type": request.sleep_type}
    except Exception as e:
        logger.error(f"Failed to force sleep: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sleep/wakeup")
async def wakeup(agent_id: Optional[str] = None):
    """强制唤醒"""
    try:
        manager = get_sleep_manager()
        
        if hasattr(manager, 'wakeup'):
            manager.wakeup(agent_id)
            logger.info(f"Wakeup agent {agent_id}")
        
        return {"success": True, "status": "active"}
    except Exception as e:
        logger.error(f"Failed to wakeup: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sleep/insight")
async def get_sleep_insight(agent_id: Optional[str] = None):
    """获取睡眠洞察"""
    def _get_real_insight():
        if hasattr(get_sleep_manager(), 'generate_insight'):
            return get_sleep_manager().generate_insight(agent_id)
        return None
    
    insight = _handle_db_operation("get_insight", _get_real_insight)
    
    if insight:
        return insight
    
    return {
        "insight": "暂无洞察数据",
        "suggestions": [],
        "memory_consolidation": {}
    }


# ============ 卸载接口 ============

import shutil
import os
from pathlib import Path

@router.post("/uninstall")
async def uninstall_plugin(request: Request):
    """
    一键卸载 HumanThinking 插件
    
    执行以下操作：
    1. 删除插件目录
    2. 删除所有记忆数据库文件
    3. 删除配置文件
    4. 从 QwenPaw 配置中移除插件
    """
    try:
        logger.info("Starting HumanThinking plugin uninstallation...")
        
        # 1. 获取插件目录
        plugin_dir = Path(__file__).parent.parent
        qwenpaw_dir = plugin_dir.parent.parent
        
        # 2. 删除所有工作区的记忆数据
        workspaces_dir = qwenpaw_dir / "workspaces"
        if workspaces_dir.exists():
            for workspace in workspaces_dir.iterdir():
                if workspace.is_dir():
                    # 删除记忆目录
                    memory_dir = workspace / "memory"
                    if memory_dir.exists():
                        shutil.rmtree(memory_dir)
                        logger.info(f"Deleted memory dir: {memory_dir}")
                    
                    # 删除配置文件
                    config_file = workspace / "human_thinking_config.json"
                    if config_file.exists():
                        config_file.unlink()
                        logger.info(f"Deleted config: {config_file}")
        
        # 3. 删除插件目录
        if plugin_dir.exists():
            shutil.rmtree(plugin_dir)
            logger.info(f"Deleted plugin dir: {plugin_dir}")
        
        # 4. 从 QwenPaw 配置中移除插件
        config_file = qwenpaw_dir / "config.json"
        if config_file.exists():
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if 'plugins' in config and 'humanthinking' in config['plugins']:
                del config['plugins']['humanthinking']
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                logger.info("Removed plugin from QwenPaw config")
        
        return {
            "success": True,
            "message": "HumanThinking 插件已成功卸载。请刷新页面或重启 QwenPaw。"
        }
        
    except Exception as e:
        logger.error(f"Uninstallation failed: {e}")
        return {
            "success": False,
            "message": f"卸载失败: {str(e)}"
        }
