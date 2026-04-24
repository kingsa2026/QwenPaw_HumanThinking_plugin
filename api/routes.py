# -*- coding: utf-8 -*-
"""HumanThinking 插件 API 路由

提供侧边栏UI所需的所有后端API
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger("qwenpaw.humanthinking.api")

# 创建路由
# 注意：QwenPaw会在注册时添加 /api 前缀，所以这里不需要 /api
router = APIRouter(prefix="/plugin/humanthinking", tags=["humanthinking"])


# ============ 请求/响应模型 ============

class SearchRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    limit: int = 10


class SearchResponse(BaseModel):
    memories: List[Dict[str, Any]]
    total: int
    query: str


class EmotionResponse(BaseModel):
    current_emotion: str
    intensity: float
    history: List[Dict[str, Any]]


class SessionInfo(BaseModel):
    session_id: str
    agent_id: str
    user_id: Optional[str]
    created_at: str
    last_active: str
    memory_count: int
    status: str


class StatsResponse(BaseModel):
    total_memories: int
    cross_session_memories: int
    frozen_memories: int
    active_sessions: int
    emotional_states: int


class ConfigUpdateRequest(BaseModel):
    enable_cross_session: Optional[bool] = None
    enable_emotion: Optional[bool] = None
    frozen_days: Optional[int] = None
    archive_days: Optional[int] = None
    delete_days: Optional[int] = None
    max_results: Optional[int] = None


# ============ API 路由 ============

@router.get("/stats", response_model=StatsResponse)
async def get_stats():
    """获取记忆统计信息"""
    try:
        from ..core.memory_manager import HumanThinkingMemoryManager
        # 这里需要从某个地方获取manager实例
        # 暂时返回模拟数据
        return StatsResponse(
            total_memories=0,
            cross_session_memories=0,
            frozen_memories=0,
            active_sessions=0,
            emotional_states=0
        )
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search_memories(request: SearchRequest):
    """搜索记忆"""
    try:
        # 这里需要实现实际的搜索逻辑
        return SearchResponse(
            memories=[],
            total=0,
            query=request.query
        )
    except Exception as e:
        logger.error(f"Failed to search memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emotion")
async def get_emotion_context(
    session_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """获取情感状态"""
    try:
        # 这里需要实现实际的情感查询逻辑
        return {
            "current_emotion": "neutral",
            "intensity": 0.5,
            "history": []
        }
    except Exception as e:
        logger.error(f"Failed to get emotion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def get_sessions(
    agent_id: Optional[str] = None,
    active_only: bool = True
):
    """获取会话列表"""
    try:
        # 这里需要实现实际的会话查询逻辑
        return []
    except Exception as e:
        logger.error(f"Failed to get sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories/recent")
async def get_recent_memories(
    limit: int = Query(20, ge=1, le=100),
    session_id: Optional[str] = None
):
    """获取最近记忆"""
    try:
        # 这里需要实现实际的查询逻辑
        return {"memories": [], "total": 0}
    except Exception as e:
        logger.error(f"Failed to get recent memories: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/memories/timeline")
async def get_memory_timeline(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    agent_id: Optional[str] = None
):
    """获取记忆时间线"""
    try:
        # 这里需要实现实际的查询逻辑
        return []
    except Exception as e:
        logger.error(f"Failed to get timeline: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sessions/bridge")
async def bridge_sessions(
    source_session: str,
    target_session: str
):
    """桥接两个会话"""
    try:
        # 这里需要实现实际的桥接逻辑
        return {"success": True, "message": "Sessions bridged"}
    except Exception as e:
        logger.error(f"Failed to bridge sessions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config")
async def get_config():
    """获取HumanThinking配置"""
    try:
        from ..core.memory_manager import get_config
        config = get_config()
        return {
            "enable_cross_session": config.enable_cross_session,
            "enable_emotion": config.enable_emotion,
            "frozen_days": config.frozen_days,
            "archive_days": config.archive_days,
            "delete_days": config.delete_days,
            "max_results": config.max_results,
            "session_idle_timeout": config.session_idle_timeout,
        }
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
async def update_config(request: ConfigUpdateRequest):
    """更新HumanThinking配置"""
    try:
        from ..core.memory_manager import get_config, save_config
        config = get_config()
        
        if request.enable_cross_session is not None:
            config.enable_cross_session = request.enable_cross_session
        if request.enable_emotion is not None:
            config.enable_emotion = request.enable_emotion
        if request.frozen_days is not None:
            config.frozen_days = request.frozen_days
        if request.archive_days is not None:
            config.archive_days = request.archive_days
        if request.delete_days is not None:
            config.delete_days = request.delete_days
        if request.max_results is not None:
            config.max_results = request.max_results
        
        save_config(config)
        return {"success": True}
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dreams")
async def get_dreams(
    limit: int = Query(10, ge=1, le=50)
):
    """获取梦境记录（睡眠期间生成的摘要）"""
    try:
        # 这里需要实现实际的查询逻辑
        return []
    except Exception as e:
        logger.error(f"Failed to get dreams: {e}")
        raise HTTPException(status_code=500, detail=str(e))
