# -*- coding: utf-8 -*-
"""额外的API路由，需要添加到plugins.py"""

# 这些路由需要添加到 /root/.qwenpaw/venv/lib/python3.12/site-packages/qwenpaw/app/routers/plugins.py

EXTRA_ROUTES = '''

# ── HumanThinking Extended Routes ──────────────────────────────────────────

@router.get("/humanthinking/sleep/status")
async def humanthinking_sleep_status():
    return {"status": "active", "sleep_type": None, "last_active_time": 0}

@router.get("/humanthinking/sleep/config")
async def humanthinking_sleep_config():
    return {
        "enable_agent_sleep": True,
        "light_sleep_minutes": 30,
        "rem_minutes": 60,
        "deep_sleep_minutes": 120,
        "consolidate_days": 7,
        "frozen_days": 30,
        "archive_days": 90,
        "delete_days": 180,
        "enable_insight": True,
        "enable_dream_log": True
    }

@router.post("/humanthinking/sleep/config")
async def humanthinking_update_sleep_config(request: Request):
    return {"success": True}

@router.post("/humanthinking/sleep/force")
async def humanthinking_force_sleep(request: Request):
    return {"success": True}

@router.post("/humanthinking/sleep/wakeup")
async def humanthinking_wakeup():
    return {"success": True}

@router.put("/humanthinking/memories/{memory_id}")
async def humanthinking_update_memory(memory_id: str, request: Request):
    return {"success": True}

@router.delete("/humanthinking/memories/batch")
async def humanthinking_batch_delete_memories(request: Request):
    return {"success": True, "deleted_count": 0}

@router.put("/humanthinking/sessions/{session_id}/rename")
async def humanthinking_rename_session(session_id: str, request: Request):
    return {"success": True}

@router.delete("/humanthinking/sessions/{session_id}")
async def humanthinking_delete_session(session_id: str):
    return {"success": True}

@router.post("/humanthinking/sessions/batch-delete")
async def humanthinking_batch_delete_sessions(request: Request):
    return {"success": True, "deleted_count": 0}

@router.get("/humanthinking/sessions/{session_id}/detail")
async def humanthinking_session_detail(session_id: str):
    return {"session_id": session_id, "session_name": "", "user_name": "", "messages": [], "memories": []}
'''
