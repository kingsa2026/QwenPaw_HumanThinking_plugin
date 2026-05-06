# -*- coding: utf-8 -*-
"""
HumanThinking API Routes

提供记忆管理、睡眠管理和情感计算的RESTful API
"""

import asyncio
import json
import logging
import time
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

from ..utils.paths import resolve_qwenpaw_dir, resolve_agent_workspace_dir, validate_agent_id, safe_path_join, get_db_path as _get_db_path
from ..utils.version import CURRENT_VERSION

logger = logging.getLogger("qwenpaw.humanthinking")

router = APIRouter()

_db_cache = {}
_db_lock = asyncio.Lock()
_memory_mgr_lock = asyncio.Lock()

security = HTTPBearer(auto_error=True)

_AUTH_TOKENS = {"humthinking-admin-token-2026", "ht-admin-secret-key"}


# ============ 认证依赖 ============

def _check_agent_id(agent_id):
    try:
        result = validate_agent_id(agent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=400, detail="agent_id is required")
    return result


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials and credentials.credentials in _AUTH_TOKENS:
        return credentials.credentials
    try:
        from qwenpaw.app.auth import verify_token as qwenpaw_verify_token
        username = qwenpaw_verify_token(credentials.credentials)
        if username:
            return credentials.credentials
    except (ImportError, Exception):
        pass
    raise HTTPException(status_code=401, detail="Valid authentication token required")


def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials and credentials.credentials in _AUTH_TOKENS:
        return credentials.credentials
    raise HTTPException(status_code=403, detail="Admin token required for this operation")


async def _get_db(agent_id: str):
    """创建并初始化数据库连接（带缓存）"""
    from ..core.database import HumanThinkingDB
    db_path = str(_get_db_path(agent_id))

    if db_path in _db_cache:
        db = _db_cache[db_path]
        try:
            db.cursor.execute("SELECT 1")
        except Exception:
            db = HumanThinkingDB(db_path)
            await db.initialize()
            _db_cache[db_path] = db
        return db

    async with _db_lock:
        if db_path in _db_cache:
            return _db_cache[db_path]
        db = HumanThinkingDB(db_path)
        await db.initialize()
        _db_cache[db_path] = db
        return db


class _DBContext:
    """数据库连接上下文管理器（不关闭缓存连接）"""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.db = None

    async def __aenter__(self):
        self.db = await _get_db(self.agent_id)
        return self.db

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        return False


def _read_qwenpaw_auto_memory_interval(agent_id: str) -> Optional[int]:
    import json
    agent_json_path = f"/root/.qwenpaw/workspaces/{agent_id}/agent.json"
    try:
        with open(agent_json_path, "r") as f:
            config = json.load(f)
        return config.get("running", {}).get("reme_light_memory_config", {}).get("auto_memory_interval")
    except Exception:
        return None


def _write_qwenpaw_auto_memory_interval(agent_id: str, value: int) -> bool:
    import json
    agent_json_path = f"/root/.qwenpaw/workspaces/{agent_id}/agent.json"
    try:
        with open(agent_json_path, "r") as f:
            config = json.load(f)
        config.setdefault("running", {}).setdefault("reme_light_memory_config", {})["auto_memory_interval"] = value
        with open(agent_json_path, "w") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Failed to write auto_memory_interval to agent.json for {agent_id}: {e}")
        return False


def _get_feishu_agent_id() -> Optional[str]:
    """返回当前启用飞书的 agent_id（feishu.enabled=true 且 app_id 非空）。
    如果多个 agent 启用飞书，返回第一个。如果没有，返回 None。
    """
    import json
    import glob as glob_mod
    
    agent_files = glob_mod.glob("/root/.qwenpaw/workspaces/*/agent.json")
    for agent_path in agent_files:
        try:
            agent_name = agent_path.split("/")[-2]
            with open(agent_path, "r") as f:
                agent_config = json.load(f)
            channels = agent_config.get("channels", {})
            feishu_cfg = channels.get("feishu", {})
            if not isinstance(feishu_cfg, dict):
                continue
            if feishu_cfg.get("enabled") and (feishu_cfg.get("app_id") or "").strip():
                return agent_name
        except Exception:
            continue
    return None


def _set_feishu_agent_id(target_agent_id: str) -> bool:
    """将飞书独占切换到指定 agent。
    启用 target_agent 的 feishu，禁用所有其他 agent 的 feishu。
    返回是否成功。
    """
    import json
    import glob as glob_mod
    
    agent_files = glob_mod.glob("/root/.qwenpaw/workspaces/*/agent.json")
    success = False
    
    for agent_path in agent_files:
        try:
            agent_name = agent_path.split("/")[-2]
            with open(agent_path, "r") as f:
                agent_config = json.load(f)
            
            channels = agent_config.get("channels", {})
            feishu_cfg = channels.get("feishu", {})
            if not isinstance(feishu_cfg, dict):
                feishu_cfg = {}
            
            desired = (agent_name == target_agent_id)
            current = feishu_cfg.get("enabled", False)
            
            if current != desired:
                if "channels" not in agent_config:
                    agent_config["channels"] = {}
                if "feishu" not in agent_config["channels"]:
                    agent_config["channels"]["feishu"] = feishu_cfg
                agent_config["channels"]["feishu"]["enabled"] = desired
                with open(agent_path, "w") as f:
                    json.dump(agent_config, f, indent=2, ensure_ascii=False)
                logger.info(f"Feishu exclusive: agent[{agent_name}] enabled={desired}")
                success = True
        except Exception as e:
            logger.error(f"Failed to set feishu for agent[{agent_name}]: {e}")
    
    return success


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
    memory_type: Optional[str] = Field(None, pattern="^(fact|preference|event|insight|general|emotion)$")
    importance: Optional[int] = Field(None, ge=1, le=5)
    importance_score: Optional[float] = Field(None, ge=0.0, le=1.0)


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
    rem_minutes: Optional[int] = Field(None, ge=1, le=120)
    deep_sleep_minutes: Optional[int] = Field(None, ge=5, le=240)
    auto_consolidate: Optional[bool] = None
    consolidate_days: Optional[int] = Field(None, ge=1, le=30)
    frozen_days: Optional[int] = Field(None, ge=1, le=90)
    archive_days: Optional[int] = Field(None, ge=2, le=180)
    delete_days: Optional[int] = Field(None, ge=3, le=365)
    enable_insight: Optional[bool] = None
    enable_dream_log: Optional[bool] = None
    # 记忆合并配置
    enable_merge: Optional[bool] = None
    merge_similarity_threshold: Optional[float] = Field(None, ge=0.5, le=0.95)
    merge_max_distance_hours: Optional[int] = Field(None, ge=1, le=168)
    # 矛盾检测配置
    enable_contradiction_detection: Optional[bool] = None
    contradiction_threshold: Optional[float] = Field(None, ge=0.3, le=0.99)
    contradiction_resolution_strategy: Optional[str] = Field(None, pattern="^(keep_latest|keep_frequent|keep_high_confidence|mark_for_review|keep_both)$")
    enable_semantic_contradiction_check: Optional[bool] = None
    enable_temporal_contradiction_check: Optional[bool] = None
    enable_confidence_scoring: Optional[bool] = None
    auto_resolve_contradiction: Optional[bool] = None
    min_confidence_for_auto_resolve: Optional[float] = Field(None, ge=0.5, le=0.99)
    auto_memory_interval: Optional[int] = Field(None, ge=0, le=20, description="每N轮用户消息触发一次summarize，0/null禁用")
    feishu_agent_id: Optional[str] = Field(None, description="指定飞书专属 agent，切换后需重启生效")


class ForceSleepRequest(BaseModel):
    sleep_type: str = Field(..., pattern="^(light|deep|rem)$")


# ============ 全局状态存储 ============

_memory_managers = {}
_MAX_MEMORY_MANAGERS = 100  # 防止内存泄漏


def get_sleep_manager():
    """获取或创建睡眠管理器（单例模式，委托 sleep_manager 模块）"""
    from ..core.sleep_manager import get_sleep_manager as _gsm
    return _gsm()


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
            working_dir = str(resolve_agent_workspace_dir(agent_id))
            _memory_managers[agent_id] = HumanThinkingMemoryManager(
                working_dir=working_dir,
                agent_id=agent_id
            )
        except Exception as e:
            logger.error(f"Failed to create memory manager for {agent_id}: {e}")
            raise
    
    return _memory_managers[agent_id]


# ============ API 路由 ============

from .error_handler import handle_api_errors


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "plugin": "humanthinking",
        "version": CURRENT_VERSION,
        "timestamp": time.time()
    }


@router.get("/stats", response_model=StatsResponse)
@handle_api_errors(
    operation_name="get_stats",
    allow_fallback=False
)
async def get_stats(
    agent_id: Optional[str] = None,
    token: Optional[str] = Depends(verify_token)
):
    """获取记忆统计信息"""
    agent_id = _check_agent_id(agent_id)
    if not agent_id:
        return StatsResponse(
            total_memories=0,
            cross_session_memories=0,
            frozen_memories=0,
            active_sessions=0,
            emotional_states=0
        )
    db = await _get_db(agent_id)

    if not hasattr(db, 'get_stats'):

        raise HTTPException(
            status_code=501,
            detail="Database method 'get_stats' not implemented"
        )

    stats = await db.get_stats(agent_id)

    return StatsResponse(
        total_memories=stats.get('total_memories', 0),
        cross_session_memories=stats.get('active_memories', 0),
        frozen_memories=stats.get('frozen_memories', 0),
        active_sessions=stats.get('total_sessions', 0),
        emotional_states=0
    )


@router.post("/search", response_model=SearchResponse)
@handle_api_errors(
    operation_name="search_memories",
    allow_fallback=False
)
async def search_memories(
    request: SearchRequest, 
    agent_id: Optional[str] = None,
    token: Optional[str] = Depends(verify_token)
):
    """搜索记忆"""
    agent_id = _check_agent_id(agent_id)
    if not agent_id:
        return SearchResponse(memories=[], total=0, query=request.query)
    db = await _get_db(agent_id)

    if not hasattr(db, 'search_memories'):

        raise HTTPException(
            status_code=501,
            detail="Database method 'search_memories' not implemented"
        )

    results = await db.search_memories(
        query=request.query,
        agent_id=agent_id,
        max_results=request.limit
    )



    return SearchResponse(
        memories=[vars(r) if hasattr(r, '__dict__') else r for r in results],
        total=len(results),
        query=request.query
    )


@router.put("/memories/{memory_id}")
@handle_api_errors(
    operation_name="update_memory",
    allow_fallback=False
)
async def update_memory(
    memory_id: str, 
    request: MemoryUpdateRequest,
    agent_id: Optional[str] = None,
    token: Optional[str] = Depends(verify_token)
):
    """更新记忆内容/类型/重要性"""
    agent_id = _check_agent_id(agent_id)
    db = await _get_db(agent_id)
    
    update_data = {}
    if request.content is not None:
        update_data['content'] = request.content
    if request.memory_type is not None:
        update_data['memory_type'] = request.memory_type
    if request.importance is not None:
        update_data['importance'] = request.importance
    if request.importance_score is not None:
        update_data['importance_score'] = request.importance_score
    
    if hasattr(db, 'update_memory_type') and request.memory_type:
        await db.update_memory_type(int(memory_id), request.memory_type)
    if hasattr(db, 'update_memory_score') and request.importance_score is not None:
        await db.update_memory_score(int(memory_id), request.importance_score)
    if request.importance is not None:
        db.cursor.execute(
            "UPDATE qwenpaw_memory SET importance = ? WHERE id = ? AND agent_id = ?",
            (request.importance, int(memory_id), agent_id)
        )
        db.conn.commit()
    
    logger.info(f"Memory {memory_id} updated: {list(update_data.keys())}")

    return {"success": True, "memory_id": memory_id, "updated": update_data}


@router.delete("/memories/batch")
@handle_api_errors(
    operation_name="batch_delete_memories",
    allow_fallback=False
)
async def batch_delete_memories(
    request: BatchDeleteRequest,
    agent_id: Optional[str] = None,
    token: Optional[str] = Depends(verify_token)
):
    """批量删除记忆"""
    agent_id = _check_agent_id(agent_id)
    db = await _get_db(agent_id)
    
    deleted_count = 0
    for memory_id in request.memory_ids:
        try:
            await db.archive_memory(int(memory_id))
            deleted_count += 1
        except (ValueError, Exception) as e:
            logger.warning(f"Failed to delete memory {memory_id}: {e}")
    
    logger.info(f"Batch deleted {deleted_count} memories")

    return {"success": True, "deleted_count": deleted_count}


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
    agent_id = _check_agent_id(agent_id)
    from ..core.emotional_engine import EmotionalContinuityEngine
    db = await _get_db(agent_id if agent_id else "default")
    engine = EmotionalContinuityEngine(db=db)

    if not hasattr(engine, 'get_emotional_context'):

        raise HTTPException(
            status_code=501,
            detail="Engine method 'get_emotional_context' not implemented"
        )

    emotion = await engine.get_emotional_context(session_id, agent_id, user_id)

    if emotion:
        return {
            "current_emotion": emotion.get("primary_emotion_trend", "neutral"),
            "intensity": emotion.get("continuity_score", 0.0),
            "history": [
                {"emotion": cue.get("emotion", "neutral"), "intensity": cue.get("intensity", 0.5)}
                for cue in emotion.get("emotional_memory_cues", [])
            ],
            "recommended_approach": emotion.get("recommended_approach", ""),
            "patterns": emotion.get("historical_patterns", {})
        }

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
    active_only: bool = True,
    token: Optional[str] = Depends(verify_token)
):
    """获取会话列表"""
    agent_id = _check_agent_id(agent_id)
    if not agent_id:
        return []
    db = await _get_db(agent_id)

    if not hasattr(db, 'get_active_sessions'):
        raise HTTPException(
            status_code=501,
            detail="Database method 'get_active_sessions' not implemented"
        )

    sessions = await db.get_active_sessions(agent_id)

    return sessions if sessions else []


@router.put("/sessions/{session_id}/rename")
@handle_api_errors(
    operation_name="rename_session",
    allow_fallback=False
)
async def rename_session(
    session_id: str, 
    request: SessionRenameRequest,
    agent_id: Optional[str] = None,
    token: Optional[str] = Depends(verify_token)
):
    """重命名会话"""
    agent_id = _check_agent_id(agent_id)
    db = await _get_db(agent_id)
    
    db.cursor.execute(
        "UPDATE sessions SET session_name = ? WHERE session_id = ? AND agent_id = ?",
        (request.session_name, session_id, agent_id)
    )
    db.conn.commit()
    
    logger.info(f"Session {session_id} renamed to: {request.session_name}")

    return {"success": True, "session_id": session_id, "session_name": request.session_name}


@router.delete("/sessions/{session_id}")
@handle_api_errors(
    operation_name="delete_session",
    allow_fallback=False
)
async def delete_session(
    session_id: str,
    agent_id: Optional[str] = None,
    token: Optional[str] = Depends(verify_token)
):
    """删除单个会话"""
    agent_id = _check_agent_id(agent_id)
    db = await _get_db(agent_id)
    
    db.cursor.execute(
        "DELETE FROM sessions WHERE session_id = ? AND agent_id = ?",
        (session_id, agent_id)
    )
    db.conn.commit()
    
    logger.info(f"Session {session_id} deleted")

    return {"success": True, "deleted_count": 1}


@router.post("/sessions/batch-delete")
@handle_api_errors(
    operation_name="batch_delete_sessions",
    allow_fallback=False
)
async def batch_delete_sessions(
    request: BatchDeleteSessionsRequest,
    agent_id: Optional[str] = None,
    token: Optional[str] = Depends(verify_token)
):
    """批量删除会话"""
    agent_id = _check_agent_id(agent_id)
    db = await _get_db(agent_id)
    
    deleted_count = 0
    for sid in request.session_ids:
        try:
            db.cursor.execute(
                "DELETE FROM sessions WHERE session_id = ? AND agent_id = ?",
                (sid, agent_id)
            )
            deleted_count += 1
        except Exception as del_err:
            logger.warning(f"Failed to delete session {sid}: {del_err}")
    db.conn.commit()
    
    logger.info(f"Batch deleted {deleted_count} sessions")

    return {"success": True, "deleted_count": deleted_count}


@router.get("/sessions/{session_id}/detail")
@handle_api_errors(
    operation_name="get_session_detail",
    allow_fallback=False
)
async def get_session_detail(
    session_id: str,
    agent_id: Optional[str] = None,
    token: Optional[str] = Depends(verify_token)
):
    """获取会话详情"""
    agent_id = _check_agent_id(agent_id)
    db = await _get_db(agent_id)
    
    memories = []
    if hasattr(db, 'get_session_memories'):
        memories = await db.get_session_memories(agent_id, session_id)
    

    return {
        "session_id": session_id,
        "session_name": '未命名会话',
        "user_name": '',
        "messages": [],
        "memories": [vars(m) if hasattr(m, '__dict__') else m for m in memories]
    }


@router.get("/memories/recent")
@handle_api_errors(
    operation_name="get_recent_memories",
    allow_fallback=False
)
async def get_recent_memories(
    agent_id: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    days: int = Query(7, ge=1, le=30),
    token: Optional[str] = Depends(verify_token)
):
    """获取最近记忆"""
    agent_id = _check_agent_id(agent_id)
    db = await _get_db(agent_id)

    if not hasattr(db, 'get_recent_memories'):
        raise HTTPException(
            status_code=501,
            detail="Database method 'get_recent_memories' not implemented"
        )

    memories = await db.get_recent_memories(agent_id, days=days)

    return {"memories": memories[:limit] if memories else [], "total": len(memories) if memories else 0}


@router.get("/memories/timeline")
@handle_api_errors(
    operation_name="get_memory_timeline",
    allow_fallback=False
)
async def get_memory_timeline(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_id: Optional[str] = None,
    group_by: Optional[str] = None
):
    """获取记忆时间线（按时间分组统计）
    
    group_by:
        - None/"month": 按月分组（全部标签）
        - "hour": 按小时分组（今天标签）
        - "12h": 按12小时分组（本周标签）
        - "day": 按天分组（本月标签）
    """
    import datetime
    agent_id = _check_agent_id(agent_id)
    db = await _get_db(agent_id)

    days_map = {"hour": 1, "12h": 7, "day": 30}
    days = days_map.get(group_by, 365)
    memories = await db.get_recent_memories(agent_id, days=days)


    if not memories:
        return []

    from collections import defaultdict
    grouped = defaultdict(lambda: {"count": 0, "events": []})

    for m in memories:
        created = m.get("created_at", "")
        if not created:
            continue
        try:
            if "T" in str(created):
                dt = datetime.datetime.fromisoformat(str(created).replace("Z", "+00:00"))
            else:
                dt = datetime.datetime.fromisoformat(str(created))
        except Exception:
            continue

        if group_by == "hour":
            key = dt.strftime("%Y-%m-%d %H:00")
        elif group_by == "12h":
            hour_block = "00-12" if dt.hour < 12 else "12-24"
            key = dt.strftime("%Y-%m-%d") + f" {hour_block}"
        elif group_by == "day":
            key = dt.strftime("%Y-%m-%d")
        else:
            key = dt.strftime("%Y-%m")

        grouped[key]["count"] += 1
        content = str(m.get("content", ""))[:80]
        if content:
            grouped[key]["events"].append(content)

    result = []
    for key in sorted(grouped.keys(), reverse=True):
        data = grouped[key]
        result.append({
            "date": key,
            "count": data["count"],
            "events": data["events"][:5]
        })

    return result


@router.get("/config")
@handle_api_errors(
    operation_name="get_config",
    allow_fallback=False
)
async def get_config(agent_id: Optional[str] = None):
    """获取HumanThinking配置（支持按Agent隔离）"""
    agent_id = _check_agent_id(agent_id)
    from ..core.memory_manager import get_config
    config = await get_config(agent_id=agent_id)
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
        "compression_mode": getattr(config, 'compression_mode', 'auto'),
    }


@router.post("/config")
@handle_api_errors(
    operation_name="update_config",
    allow_fallback=False
)
async def update_config(request: Request, agent_id: Optional[str] = None):
    """更新HumanThinking配置（支持按Agent隔离）"""
    agent_id = _check_agent_id(agent_id)
    from ..core.memory_manager import get_config, save_config, update_config_fields
    
    data = await request.json()
    config = get_config(agent_id=agent_id)
    
    ALLOWED_COMPRESSION_MODES = ('auto', 'llm', 'simple')
    if 'compression_mode' in data and data['compression_mode'] not in ALLOWED_COMPRESSION_MODES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid compression_mode: {data['compression_mode']}. Allowed: {ALLOWED_COMPRESSION_MODES}"
        )
    
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
        'compression_mode': data.get('compression_mode'),
    }
    
    for field_name, value in field_mapping.items():
        if value is not None:
            setattr(config, field_name, value)
            update_fields[field_name] = value
    
    if update_fields:
        update_config_fields(update_fields, agent_id=agent_id)
    
    logger.info(f"准备保存配置 agent={agent_id or 'default'}, 更新字段: {list(update_fields.keys())}")
    success = save_config(config, agent_id=agent_id)
    if not success:
        logger.error(f"save_config 返回 False, agent={agent_id or 'default'}")
        return {"success": False, "message": "配置保存失败，请检查日志"}
    
    logger.info(f"配置已保存成功 agent={agent_id or 'default'}, 检查数据库...")
    
    try:
        from ..core.memory_manager import HumanThinkingMemoryManager
        import os
        from pathlib import Path
        
        if agent_id:
            working_dir = str(resolve_agent_workspace_dir(agent_id))
        else:
            working_dir = str(resolve_agent_workspace_dir("default"))
        
        db_path = Path(working_dir) / "memory" / f"human_thinking_memory_{agent_id or 'default'}.db"
        logger.info(f"检查数据库: db_path={db_path}, working_dir={working_dir}")
        
        if not db_path.exists():
            logger.info(f"数据库不存在，开始创建: {db_path}")
            Path(working_dir).mkdir(parents=True, exist_ok=True)
            mm = HumanThinkingMemoryManager(
                working_dir=working_dir,
                agent_id=agent_id or "default",
                user_id=None
            )
            logger.info(f"HumanThinkingMemoryManager 已创建, 调用 mm.start()...")
            await mm.start()
            logger.info(f"数据库自动创建成功: {mm.db_path}")
        else:
            logger.info(f"数据库已存在，跳过创建: {db_path}")
    except Exception as db_err:
        logger.error(f"数据库自动创建失败 agent={agent_id or 'default'}: {db_err}", exc_info=True)
    
    logger.info(f"配置更新完成 agent={agent_id or 'default'}: {list(update_fields.keys())}")
    return {"success": True, "config": data}


@router.get("/db/version")
@handle_api_errors(
    operation_name="get_db_version",
    allow_fallback=False
)
async def get_db_version(request: Request, agent_id: Optional[str] = None):
    """获取数据库版本和迁移状态"""
    agent_id = _check_agent_id(agent_id)
    from pathlib import Path
    if agent_id:
        working_dir = str(resolve_agent_workspace_dir(agent_id))
    else:
        working_dir = str(resolve_agent_workspace_dir("default"))
    db_path = Path(working_dir) / "memory" / f"human_thinking_memory_{agent_id or 'default'}.db"

    if not db_path.exists():
        from ..core.database import CURRENT_SCHEMA_VERSION as csv
        return {
            "exists": False,
            "code_schema_version": csv,
            "db_schema_version": None,
            "needs_migration": False,
            "migration_history": [],
        }

    from ..core.database import HumanThinkingDB
    db = HumanThinkingDB(str(db_path))
    await db.initialize()
    version_info = db.get_version_info()
    version_info["exists"] = True
    version_info["migration_history"] = db.get_migration_history()
    version_info["db_path"] = str(db_path)

    return version_info


@router.get("/dreams")
@handle_api_errors(
    operation_name="get_dreams",
    allow_fallback=False
)
async def get_dreams(
    agent_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50)
):
    """获取梦境记录（睡眠期间生成的摘要）"""
    agent_id = _check_agent_id(agent_id)
    if not agent_id:
        return []
    db = await _get_db(agent_id)
    dreams = await db.get_dream_logs(agent_id, limit=limit)

    return dreams


# ============ 睡眠管理 API ============

@router.get("/sleep/status")
@handle_api_errors(
    operation_name="get_sleep_status",
    allow_fallback=False
)
async def get_sleep_status(agent_id: Optional[str] = None):
    """获取睡眠状态（惰性计算）
    
    查询数据库获取Agent最后活动时间，实时计算当前睡眠状态。
    如果空闲时间超过阈值，会自动触发对应的睡眠阶段任务。
    
    Args:
        agent_id: Agent ID
        
    Returns:
        睡眠状态信息，包含状态、空闲时间、距离下一阶段时间等
    """
    from ..core.sleep_manager import check_and_trigger_sleep
    
    if not agent_id:
        return {
            "status": "active",
            "status_text": "活跃",
            "icon": "☀️",
            "color": "#52c41a",
            "idle_time": 0,
            "next_sleep_in": -1
        }
    
    # 使用惰性计算获取睡眠状态（会自动触发状态转换）
    status = await check_and_trigger_sleep(agent_id)
    return status


@router.get("/sleep/config")
@handle_api_errors(
    operation_name="get_sleep_config",
    allow_fallback=False
)
async def get_sleep_config(agent_id: Optional[str] = None):
    """获取睡眠配置（支持按Agent隔离）"""
    from ..core.sleep_manager import get_agent_sleep_config
    config = get_agent_sleep_config(agent_id)
    
    return {
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
        # 记忆合并配置
        "enable_merge": config.enable_merge,
        "merge_similarity_threshold": config.merge_similarity_threshold,
        "merge_max_distance_hours": config.merge_max_distance_hours,
        # 矛盾检测配置
        "enable_contradiction_detection": config.enable_contradiction_detection,
        "contradiction_threshold": config.contradiction_threshold,
        "contradiction_resolution_strategy": config.contradiction_resolution_strategy,
        "enable_semantic_contradiction_check": config.enable_semantic_contradiction_check,
        "enable_temporal_contradiction_check": config.enable_temporal_contradiction_check,
        "enable_confidence_scoring": config.enable_confidence_scoring,
        "auto_resolve_contradiction": config.auto_resolve_contradiction,
        "min_confidence_for_auto_resolve": config.min_confidence_for_auto_resolve,
        # QwenPaw 写入链开关
        "auto_memory_interval": _read_qwenpaw_auto_memory_interval(agent_id or "default"),
        # 飞书独占 agent
        "feishu_agent_id": _get_feishu_agent_id(),
    }


@router.post("/sleep/config")
@handle_api_errors(
    operation_name="update_sleep_config",
    allow_fallback=False
)
async def update_sleep_config(payload: Request, agent_id: Optional[str] = None):
    """更新睡眠配置（支持按Agent隔离）"""
    import json as _json
    
    raw_body = None
    try:
        raw_body = await payload.body()
        raw_text = raw_body.decode("utf-8", errors="replace")
        request_data = _json.loads(raw_text)
        request = SleepConfigUpdateRequest(**request_data)
    except Exception as e:
        raw_preview = (raw_body.decode("utf-8", errors="replace")[:300] if raw_body else "<empty>")
        logger.error(f"update_sleep_config parse failed: body={raw_preview} error={e}")
        raise HTTPException(status_code=422, detail=f"Invalid request body: {str(e)}")
    from ..core.sleep_manager import get_agent_sleep_config, save_agent_sleep_config, SleepConfig
    
    old_config = get_agent_sleep_config(agent_id)
    
    config_dict = {
        "enable_agent_sleep": request.enable_agent_sleep if request.enable_agent_sleep is not None else old_config.enable_agent_sleep,
        "light_sleep_minutes": request.light_sleep_minutes if request.light_sleep_minutes is not None else old_config.light_sleep_minutes,
        "rem_minutes": request.rem_minutes if request.rem_minutes is not None else old_config.rem_minutes,
        "deep_sleep_minutes": request.deep_sleep_minutes if request.deep_sleep_minutes is not None else old_config.deep_sleep_minutes,
        "auto_consolidate": request.auto_consolidate if request.auto_consolidate is not None else old_config.auto_consolidate,
        "consolidate_days": request.consolidate_days if request.consolidate_days is not None else old_config.consolidate_days,
        "frozen_days": request.frozen_days if request.frozen_days is not None else old_config.frozen_days,
        "archive_days": request.archive_days if request.archive_days is not None else old_config.archive_days,
        "delete_days": request.delete_days if request.delete_days is not None else old_config.delete_days,
        "enable_insight": request.enable_insight if request.enable_insight is not None else old_config.enable_insight,
        "enable_dream_log": request.enable_dream_log if request.enable_dream_log is not None else old_config.enable_dream_log,
        "enable_merge": request.enable_merge if request.enable_merge is not None else old_config.enable_merge,
        "merge_similarity_threshold": request.merge_similarity_threshold if request.merge_similarity_threshold is not None else old_config.merge_similarity_threshold,
        "merge_max_distance_hours": request.merge_max_distance_hours if request.merge_max_distance_hours is not None else old_config.merge_max_distance_hours,
        "enable_contradiction_detection": request.enable_contradiction_detection if request.enable_contradiction_detection is not None else old_config.enable_contradiction_detection,
        "contradiction_threshold": request.contradiction_threshold if request.contradiction_threshold is not None else old_config.contradiction_threshold,
        "contradiction_resolution_strategy": request.contradiction_resolution_strategy if request.contradiction_resolution_strategy is not None else old_config.contradiction_resolution_strategy,
        "enable_semantic_contradiction_check": request.enable_semantic_contradiction_check if request.enable_semantic_contradiction_check is not None else old_config.enable_semantic_contradiction_check,
        "enable_temporal_contradiction_check": request.enable_temporal_contradiction_check if request.enable_temporal_contradiction_check is not None else old_config.enable_temporal_contradiction_check,
        "enable_confidence_scoring": request.enable_confidence_scoring if request.enable_confidence_scoring is not None else old_config.enable_confidence_scoring,
        "auto_resolve_contradiction": request.auto_resolve_contradiction if request.auto_resolve_contradiction is not None else old_config.auto_resolve_contradiction,
        "min_confidence_for_auto_resolve": request.min_confidence_for_auto_resolve if request.min_confidence_for_auto_resolve is not None else old_config.min_confidence_for_auto_resolve,
    }
    
    config = SleepConfig(**config_dict)
    
    manager = get_sleep_manager()
    if manager and agent_id:
        manager.update_config(config, agent_id=agent_id)
    elif manager:
        manager.update_config(config)
    
    # 保存到全局配置文件（无论是否有agent_id）
    from ..core.sleep_manager import _save_global_config_to_file
    _save_global_config_to_file(config)
    
    if agent_id:
        success = save_agent_sleep_config(agent_id, config)
        if not success:
            return {"success": False, "message": "配置保存失败，请检查日志"}
    
    if request.auto_memory_interval is not None:
        qwenpaw_ok = _write_qwenpaw_auto_memory_interval(agent_id or "default", request.auto_memory_interval)
        if not qwenpaw_ok:
            logger.warning("HumanThinking config saved but failed to sync auto_memory_interval to agent.json")
    
    if request.feishu_agent_id is not None:
        feishu_ok = _set_feishu_agent_id(request.feishu_agent_id)
        if feishu_ok:
            logger.info(f"Feishu exclusive switched to agent: {request.feishu_agent_id}")
        else:
            logger.warning(f"Failed to set Feishu exclusive agent to: {request.feishu_agent_id}")
    
    logger.info(f"Sleep config updated for agent {agent_id}: {request.model_dump(exclude_unset=True)}")
    return {"success": True, "config": request.model_dump(exclude_unset=True)}


@router.post("/sleep/force")
@handle_api_errors(
    operation_name="force_sleep",
    allow_fallback=False
)
async def force_sleep(request: ForceSleepRequest, agent_id: Optional[str] = None):
    """强制进入睡眠"""
    agent_id = _check_agent_id(agent_id)
    manager = get_sleep_manager()
    
    sleep_methods = {
        "light": "force_light_sleep",
        "rem": "force_rem",
        "deep": "force_deep_sleep"
    }
    
    method_name = sleep_methods.get(request.sleep_type)
    if method_name and hasattr(manager, method_name):
        result = await getattr(manager, method_name)(agent_id)
        logger.info(f"Forced {request.sleep_type} sleep for agent {agent_id}")
        return result
    
    return {"success": True, "sleep_type": request.sleep_type}


@router.post("/sleep/wakeup")
@handle_api_errors(
    operation_name="wakeup",
    allow_fallback=False
)
async def wakeup(agent_id: Optional[str] = None):
    """强制唤醒"""
    agent_id = _check_agent_id(agent_id)
    manager = get_sleep_manager()
    
    if hasattr(manager, 'wakeup'):
        result = await manager.wakeup(agent_id)
        logger.info(f"Wakeup agent {agent_id}")
        return result
    
    return {"success": True, "status": "active"}


@router.post("/sleep/activity")
@handle_api_errors(
    operation_name="record_activity",
    allow_fallback=False
)
async def record_activity(agent_id: Optional[str] = None):
    """记录Agent活动（由消息路由调用）
    
    当Agent收到或发送消息时，调用此端点记录活动。
    这会更新Agent的最后活动时间，如果Agent处于睡眠状态则会唤醒它。
    
    Args:
        agent_id: Agent ID
        
    Returns:
        记录结果
    """
    from ..core.sleep_manager import record_agent_activity
    
    if agent_id:
        record_agent_activity(agent_id)
        logger.debug(f"Recorded activity for agent {agent_id}")
        return {"success": True, "agent_id": agent_id, "action": "activity_recorded"}
    else:
        return {"success": False, "message": "agent_id is required"}


@router.get("/sleep/insight")
@handle_api_errors(
    operation_name="get_sleep_insight",
    allow_fallback=False
)
async def get_sleep_insight(agent_id: Optional[str] = None):
    """获取睡眠洞察"""
    manager = get_sleep_manager()
    if hasattr(manager, 'generate_insight'):
        insight = manager.generate_insight(agent_id)
        if insight:
            return insight
    
    return {
        "insight": "暂无洞察数据",
        "suggestions": [],
        "memory_consolidation": {}
    }


# ============ 卸载接口 ============

import os

from ..utils.env_detector import detect_qwenpaw_env, get_cache_dirs

@router.post("/uninstall")
async def uninstall_plugin(request: Request, token: Optional[str] = Depends(verify_admin_token)):
    """
    一键卸载 HumanThinking 插件 - 适配多环境（Docker/Windows/macOS/Linux）
    
    参数:
        keep_data: 是否保留数据（默认True）
        
    执行以下操作：
    1. 自动检测QwenPaw安装环境
    2. 导出记忆数据为 Markdown 文件（如果不保留数据）
    3. 恢复被修改的QwenPaw系统文件
    4. 删除插件目录
    5. 根据 keep_data 决定是否删除数据文件
    6. 从 QwenPaw 配置中移除插件
    7. 清除Python缓存
    """
    try:
        # 解析请求参数
        body = await request.json() if await request.body() else {}
        keep_data = body.get('keep_data', True)
        
        logger.info(f"Starting HumanThinking plugin uninstallation... keep_data={keep_data}")
        
        # 1. 自动检测QwenPaw安装环境
        env = detect_qwenpaw_env()
        
        # 2. 获取插件目录
        plugin_dir = Path(__file__).parent.parent
        
        # 使用检测到的环境信息
        qwenpaw_dir = env.working_dir or plugin_dir.parent.parent
        qwenpaw_packages_dir = env.qwenpaw_package_dir
        
        logger.info(f"Environment detected: {env.install_type}")
        logger.info(f"Working dir: {qwenpaw_dir}")
        logger.info(f"Package dir: {qwenpaw_packages_dir}")
        
        # 2. 获取所有工作区的记忆数据
        workspaces_dir = qwenpaw_dir / "workspaces"
        exported_files = []
        
        if workspaces_dir.exists():
            for workspace in workspaces_dir.iterdir():
                if workspace.is_dir():
                    memory_dir = workspace / "memory"
                    config_file = memory_dir / "human_thinking_config.json"
                    
                    # 如果不保留数据，先导出记忆
                    if not keep_data and memory_dir.exists():
                        # 创建 Memory 导出目录
                        export_dir = workspace / "Memory"
                        export_dir.mkdir(exist_ok=True)
                        
                        # 生成导出文件名
                        date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
                        export_file = export_dir / f"memory_backup_{date_str}.md"
                        
                        # 导出记忆数据为 Markdown
                        try:
                            await export_memories_to_md(memory_dir, export_file, workspace.name)
                            exported_files.append(str(export_file))
                            logger.info(f"Exported memories to: {export_file}")
                        except Exception as e:
                            logger.error(f"Failed to export memories: {e}")
                    
                    # 如果不保留数据，删除记忆目录
                    if not keep_data and memory_dir.exists():
                        shutil.rmtree(memory_dir)
                        logger.info(f"Deleted memory dir: {memory_dir}")
                    
                    # 如果不保留数据，删除配置文件
                    if not keep_data and config_file.exists():
                        config_file.unlink()
                        logger.info(f"Deleted config: {config_file}")
        
        # 3. 恢复被修改的 QwenPaw 文件（在删除插件目录之前执行）
        restored_files = []
        
        # 先缓存原始文件内容（因为插件目录即将被删除）
        original_files_cache = {}
        original_files_dir = plugin_dir / "original_files"
        if original_files_dir.exists():
            for original_file in original_files_dir.iterdir():
                if original_file.is_file():
                    try:
                        with open(original_file, 'r', encoding='utf-8') as f:
                            original_files_cache[original_file.name] = f.read()
                        logger.info(f"Cached original file: {original_file.name}")
                    except Exception as e:
                        logger.warning(f"Failed to cache {original_file.name}: {e}")
        
        # 使用检测到的qwenpaw包目录
        if qwenpaw_packages_dir and qwenpaw_packages_dir.exists():
            try:
                # 方式1：从备份文件恢复（主要方式，最可靠）
                for bak_file in qwenpaw_packages_dir.rglob("*.humanthinking.bak"):
                    original_str = str(bak_file).replace(".humanthinking.bak", "")
                    original_path = Path(original_str)
                    
                    if original_path.exists() and bak_file.exists():
                        shutil.copy2(bak_file, original_path)
                        bak_file.unlink()
                        restored_files.append(str(original_path.relative_to(qwenpaw_packages_dir)))
                        logger.info(f"Restored from backup: {original_path}")
                
                # 方式2：使用缓存的原始文件直接覆盖（仅当备份不存在时）
                if original_files_cache:
                    for filename, original_content in original_files_cache.items():
                        if filename == "plugins.py":
                            target_file = qwenpaw_packages_dir / "app" / "routers" / "plugins.py"
                        elif filename == "workspace.py":
                            target_file = qwenpaw_packages_dir / "app" / "workspace" / "workspace.py"
                        elif filename == "_app.py":
                            target_file = qwenpaw_packages_dir / "app" / "_app.py"
                        else:
                            continue
                        
                        target_bak = target_file.with_suffix(target_file.suffix + ".humanthinking.bak")
                        if target_file.exists() and not target_bak.exists():
                            try:
                                with open(target_file, 'r', encoding='utf-8') as f:
                                    current_content = f.read()
                                
                                if original_content != current_content:
                                    with open(target_file, 'w', encoding='utf-8') as f:
                                        f.write(original_content)
                                    restored_files.append(f"{target_file.relative_to(qwenpaw_packages_dir)} (replaced with original)")
                                    logger.info(f"Replaced {target_file} with original file")
                            except Exception as restore_err:
                                logger.warning(f"Failed to restore {target_file}: {restore_err}")
                
                # 方式3：删除注入的代码块（最后降级方式）
                # 检查 plugins.py 是否还有 humanthinking 路由且没有备份
                plugins_py = qwenpaw_packages_dir / "app" / "routers" / "plugins.py"
                plugins_bak = plugins_py.with_suffix(".py.humanthinking.bak")
                
                if plugins_py.exists() and not plugins_bak.exists():
                    try:
                        with open(plugins_py, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        begin_marker = '# ── HumanThinking Plugin Routes [BEGIN'
                        end_marker = '# ── HumanThinking Plugin Routes [END'
                        
                        if begin_marker in content:
                            begin_pos = content.find(begin_marker)
                            if end_marker in content:
                                end_pos = content.find(end_marker) + len(end_marker)
                                while end_pos < len(content) and content[end_pos] == '\n':
                                    end_pos += 1
                                new_content = content[:begin_pos].rstrip('\n')
                                if end_pos < len(content):
                                    new_content += content[end_pos:]
                            else:
                                new_content = content[:begin_pos].rstrip('\n')
                            
                            with open(plugins_py, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            
                            restored_files.append("app/routers/plugins.py (by removing injected code)")
                            logger.info("Removed injected HumanThinking routes from plugins.py")
                    except Exception as remove_err:
                        logger.warning(f"Failed to remove injected code from plugins.py: {remove_err}")
                
                # 检查 workspace.py 是否还有 humanthinking 代码且没有备份
                workspace_py = qwenpaw_packages_dir / "app" / "workspace" / "workspace.py"
                workspace_bak = workspace_py.with_suffix(".py.humanthinking.bak")
                
                if workspace_py.exists() and not workspace_bak.exists():
                    try:
                        with open(workspace_py, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        begin_marker = '# ── HumanThinking Plugin Routes [BEGIN'
                        if begin_marker in content:
                            begin_pos = content.find(begin_marker)
                            new_content = content[:begin_pos].rstrip('\n')
                            
                            with open(workspace_py, 'w', encoding='utf-8') as f:
                                f.write(new_content)
                            
                            restored_files.append("app/workspace/workspace.py (by removing injected code)")
                            logger.info("Removed injected HumanThinking code from workspace.py")
                    except Exception as remove_err:
                        logger.warning(f"Failed to remove injected code from workspace.py: {remove_err}")
                
            except Exception as e:
                logger.error(f"Failed to restore QwenPaw files: {e}")
        
        # 4. 删除插件目录
        if plugin_dir.exists():
            try:
                shutil.rmtree(plugin_dir)
                logger.info(f"Deleted plugin dir: {plugin_dir}")
            except Exception as rm_err:
                logger.warning(f"Failed to delete plugin dir (may be in use): {rm_err}")
                marker_file = plugin_dir / ".uninstall_pending"
                marker_file.write_text(f"Uninstall requested at {datetime.now().isoformat()}\nkeep_data={keep_data}", encoding='utf-8')
                logger.info(f"Created uninstall marker: {marker_file}")
        
        # 5. 从 QwenPaw 配置中移除插件
        config_file = qwenpaw_dir / "config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 支持多种配置结构
                if 'plugins' in config:
                    if isinstance(config['plugins'], dict) and 'humanthinking' in config['plugins']:
                        del config['plugins']['humanthinking']
                    elif isinstance(config['plugins'], list):
                        config['plugins'] = [p for p in config['plugins'] 
                                           if (isinstance(p, dict) and p.get('id') != 'humanthinking')]
                
                with open(config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                logger.info("Removed plugin from QwenPaw config")
            except Exception as cfg_err:
                logger.warning(f"Failed to update config: {cfg_err}")
        
        # 6. 清除 Python 缓存，确保还原后的文件立即生效
        # 使用外部脚本调用，确保即使插件目录被删除后也能执行
        try:
            import subprocess
            
            # 使用环境检测模块获取所有需要清除缓存的目录
            cache_dirs = get_cache_dirs(env)
            
            # 方式A：直接清除（当前进程内）
            for cache_dir in cache_dirs:
                if cache_dir.exists():
                    for root, dirs, files in os.walk(cache_dir):
                        for f in files:
                            if f.endswith(".pyc"):
                                try:
                                    os.remove(os.path.join(root, f))
                                except:
                                    pass
                    for root, dirs, files in os.walk(cache_dir):
                        pycache_dirs_to_remove = []
                        for d in dirs:
                            if d == "__pycache__":
                                try:
                                    shutil.rmtree(os.path.join(root, d))
                                    pycache_dirs_to_remove.append(d)
                                except Exception:
                                    pass
                        for d in pycache_dirs_to_remove:
                            dirs.remove(d)
                    logger.info(f"Cleared Python cache: {cache_dir}")
            
            # 方式B：外部脚本调用（确保彻底清除，即使当前进程有缓存）
            # 根据环境确定Python解释器路径
            python_exe = None
            if env.python_executable and env.python_executable.exists():
                python_exe = env.python_executable
            elif env.venv_dir:
                if env.is_windows:
                    python_exe = env.venv_dir / "Scripts" / "python.exe"
                else:
                    python_exe = env.venv_dir / "bin" / "python"
            
            if python_exe and python_exe.exists():
                # 创建临时脚本
                cache_clear_script = qwenpaw_dir / "clear_cache_after_uninstall.py"
                cache_dirs_str = ', '.join([f'"{d}"' for d in cache_dirs if d.exists()])
                
                script_content = f'''#!/usr/bin/env python3
import os
import shutil
import sys

cache_dirs = [{cache_dirs_str}]
for cache_dir in cache_dirs:
    if os.path.exists(cache_dir):
        for root, dirs, files in os.walk(cache_dir):
            for f in files:
                if f.endswith(".pyc"):
                    try:
                        os.remove(os.path.join(root, f))
                    except:
                        pass
        for root, dirs, files in os.walk(cache_dir):
            if "__pycache__" in dirs:
                try:
                    shutil.rmtree(os.path.join(root, "__pycache__"))
                except:
                    pass
print("Cache cleared by external script")
'''
                with open(cache_clear_script, 'w') as f:
                    f.write(script_content)
                
                subprocess.run([str(python_exe), str(cache_clear_script)], 
                             capture_output=True, timeout=10)
                logger.info("Cleared Python cache via external script")
                
                # 删除临时脚本
                try:
                    cache_clear_script.unlink()
                except:
                    pass
        except Exception as cache_err:
            logger.warning(f"Failed to clear Python cache: {cache_err}")
        
        # 构建返回消息
        if keep_data:
            message = "HumanThinking 插件已卸载。\n\n✅ 已保留数据：\n- 记忆数据库文件\n- 配置文件\n\n如需完全清理，请手动删除工作区下的 memory 目录和 human_thinking_config.json 文件。"
        else:
            message = "HumanThinking 插件已完全卸载。\n\n"
            if exported_files:
                message += f"✅ 已导出 {len(exported_files)} 个记忆备份文件到 Memory 文件夹。\n"
                for f in exported_files:
                    message += f"  - {f}\n"
            message += "\n❌ 已删除所有数据文件。"
        
        # 添加恢复文件信息
        if restored_files:
            message += f"\n\n✅ 已还原 {len(restored_files)} 个 QwenPaw 系统文件：\n"
            for f in restored_files:
                message += f"  - {f}\n"
        
        return {
            "success": True,
            "message": message,
            "keep_data": keep_data,
            "exported_files": exported_files,
            "restored_files": restored_files
        }
        
    except Exception as e:
        logger.error(f"Uninstallation failed: {e}")
        return {
            "success": False,
            "message": f"卸载失败: {str(e)}"
        }


async def export_memories_to_md(memory_dir: Path, export_file: Path, workspace_name: str):
    """将记忆数据导出为 Markdown 文件"""
    try:
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")
        
        db_files = list(memory_dir.glob("human_thinking_memory_*.db"))
        
        all_memories = []
        for db_file in db_files:
            conn = None
            try:
                conn = sqlite3.connect(str(db_file))
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT id, content, importance, memory_type, memory_tier, 
                           created_at, session_id, agent_id, tags
                    FROM qwenpaw_memory 
                    WHERE deleted_at IS NULL
                    ORDER BY importance DESC, created_at DESC
                """)
                
                for row in cursor.fetchall():
                    r = dict(row)
                    all_memories.append(r)
                
                cursor.execute("""
                    SELECT id, content, importance, memory_type, 
                           original_created_at, session_id, agent_id
                    FROM qwenpaw_archive
                    ORDER BY importance DESC, original_created_at DESC
                """)
                
                for row in cursor.fetchall():
                    r = dict(row)
                    r['memory_tier'] = 'archived'
                    all_memories.append(r)
            except Exception as db_err:
                logger.warning(f"Failed to read {db_file}: {db_err}")
            finally:
                if conn:
                    conn.close()
        md_lines = [
            f"# HumanThinking 记忆备份",
            f"",
            f"## 导出信息",
            f"- **工作区**: {workspace_name}",
            f"- **导出时间**: {date_str}",
            f"- **记忆总数**: {len(all_memories)}",
            f"",
            f"---",
            f"",
        ]
        
        for m in all_memories:
            tier = m.get('memory_tier', 'unknown')
            imp = m.get('importance', '?')
            mtype = m.get('memory_type', 'unknown')
            content = m.get('content', '')
            created = m.get('created_at') or m.get('original_created_at', '')
            sid = m.get('session_id', '')
            tags = m.get('tags', '[]')
            
            md_lines.append(f"### #{m.get('id', '?')} [{tier}] 重要性:{imp} 类型:{mtype}")
            md_lines.append(f"")
            md_lines.append(f"{content}")
            md_lines.append(f"")
            md_lines.append(f"- 创建时间: {created}")
            md_lines.append(f"- 会话: {sid}")
            if tags and tags != '[]':
                md_lines.append(f"- 标签: {tags}")
            md_lines.append(f"")
            md_lines.append(f"---")
            md_lines.append(f"")
        
        md_content = "\n".join(md_lines)
        
        with open(export_file, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        logger.info(f"Exported {len(all_memories)} memories to {export_file}")
            
    except Exception as e:
        logger.error(f"Export failed: {e}")
        raise
