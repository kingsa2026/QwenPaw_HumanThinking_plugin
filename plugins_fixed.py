# -*- coding: utf-8 -*-
"""Plugin API routes: list plugins with UI metadata and serve plugin
static files."""

import json
import logging
import mimetypes
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/plugins", tags=["plugins"])

# -- HumanThinking Config Persistence (Agent Isolated) ---------------------

_HT_CONFIG_BASE = Path('/root/.qwenpaw/config')
_HT_SLEEP_CONFIG_BASE = Path('/root/.qwenpaw/config')
_HT_SLEEP_STATE_BASE = Path('/root/.qwenpaw/config')

def _get_ht_config_file(agent_id: str = None):
    """获取记忆配置文件路径（支持Agent隔离）"""
    if agent_id:
        return _HT_CONFIG_BASE / f'humanthinking_config_{agent_id}.json'
    return _HT_CONFIG_BASE / 'humanthinking_config.json'

def _get_ht_sleep_config_file(agent_id: str = None):
    """获取睡眠配置文件路径（支持Agent隔离）"""
    if agent_id:
        return _HT_SLEEP_CONFIG_BASE / f'humanthinking_sleep_config_{agent_id}.json'
    return _HT_SLEEP_CONFIG_BASE / 'humanthinking_sleep_config.json'

def _get_ht_sleep_state_file(agent_id: str = None):
    """获取睡眠状态文件路径（支持Agent隔离）"""
    if agent_id:
        return _HT_SLEEP_STATE_BASE / f'humanthinking_sleep_state_{agent_id}.json'
    return _HT_SLEEP_STATE_BASE / 'humanthinking_sleep_state.json'

def _ensure_ht_config_dir():
    _HT_CONFIG_BASE.mkdir(parents=True, exist_ok=True)

def _get_agent_json_path(agent_id: str = None):
    """获取agent.json文件路径"""
    if agent_id:
        return Path('/root/.qwenpaw/workspaces') / agent_id / 'agent.json'
    return Path('/root/.qwenpaw/workspaces/default/agent.json')

def _load_ht_config(agent_id: str = None):
    """从agent.json的running对象中读取配置"""
    agent_json_path = _get_agent_json_path(agent_id)
    if agent_json_path.exists():
        try:
            with open(agent_json_path, 'r', encoding='utf-8') as f:
                agent_data = json.load(f)
            running = agent_data.get('running', {})
            memory_config = running.get('reme_light_memory_config', {})
            return {
                'enable_cross_session': running.get('memory_manager_backend') == 'remelight',
                'enable_emotion': True,
                'frozen_days': memory_config.get('frozen_days', 30),
                'archive_days': memory_config.get('archive_days', 90),
                'delete_days': memory_config.get('delete_days', 180),
                'max_results': memory_config.get('auto_memory_search_config', {}).get('max_results', 5),
                'session_idle_timeout': 180,
                'refresh_interval': 5,
                'max_memory_chars': 300,
                'enable_distributed_db': True,
                'db_size_threshold_mb': 1000,
            }
        except Exception:
            pass
    return {
        'enable_cross_session': True,
        'enable_emotion': True,
        'frozen_days': 30,
        'archive_days': 90,
        'delete_days': 180,
        'max_results': 5,
        'session_idle_timeout': 180,
        'refresh_interval': 5,
        'max_memory_chars': 300,
        'enable_distributed_db': True,
        'db_size_threshold_mb': 1000,
    }

def _save_ht_config(data, agent_id: str = None):
    """保存配置到agent.json的running对象中"""
    agent_json_path = _get_agent_json_path(agent_id)
    if agent_json_path.exists():
        try:
            with open(agent_json_path, 'r', encoding='utf-8') as f:
                agent_data = json.load(f)
            
            # 更新running对象中的配置
            if 'running' not in agent_data:
                agent_data['running'] = {}
            running = agent_data['running']
            
            # 更新memory_manager_backend
            running['memory_manager_backend'] = 'remelight' if data.get('enable_cross_session', True) else 'none'
            
            # 更新reme_light_memory_config
            if 'reme_light_memory_config' not in running:
                running['reme_light_memory_config'] = {}
            memory_config = running['reme_light_memory_config']
            
            memory_config['frozen_days'] = data.get('frozen_days', 30)
            memory_config['archive_days'] = data.get('archive_days', 90)
            memory_config['delete_days'] = data.get('delete_days', 180)
            
            if 'auto_memory_search_config' not in memory_config:
                memory_config['auto_memory_search_config'] = {}
            memory_config['auto_memory_search_config']['max_results'] = data.get('max_results', 5)
            
            # 保存回agent.json
            with open(agent_json_path, 'w', encoding='utf-8') as f:
                json.dump(agent_data, f, ensure_ascii=False, indent=2)
            return
        except Exception as e:
            logger.error(f"Failed to save config to agent.json: {e}")
    
    # 如果agent.json不存在，回退到独立配置文件
    _ensure_ht_config_dir()
    config_file = _get_ht_config_file(agent_id)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _load_ht_sleep_config(agent_id: str = None):
    _ensure_ht_config_dir()
    config_file = _get_ht_sleep_config_file(agent_id)
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'enable_agent_sleep': True,
        'light_sleep_minutes': 30,
        'rem_minutes': 60,
        'deep_sleep_minutes': 120,
        'consolidate_days': 7,
        'frozen_days': 30,
        'archive_days': 90,
        'delete_days': 180,
        'enable_insight': True,
        'enable_dream_log': True,
        'enable_insight_light': True,
    }

def _save_ht_sleep_config(data, agent_id: str = None):
    _ensure_ht_config_dir()
    config_file = _get_ht_sleep_config_file(agent_id)
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _load_ht_sleep_state(agent_id: str = None):
    _ensure_ht_config_dir()
    state_file = _get_ht_sleep_state_file(agent_id)
    if state_file.exists():
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {'status': 'active', 'sleep_type': None, 'last_active_time': time.time()}

def _save_ht_sleep_state(data, agent_id: str = None):
    _ensure_ht_config_dir()
    state_file = _get_ht_sleep_state_file(agent_id)
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# -- Helpers ---------------------------------------------------------------


def _list_plugins_from_disk() -> list[dict]:
    """Read plugin manifests directly from the plugins directory on disk.

    Used as a fallback when the plugin loader has not finished initialising
    (e.g. the frontend opens before the backend startup coroutine completes).
    Returns the same shape as the normal list endpoint so the frontend does
    not need to handle a different schema.
    """
    from ...config.utils import get_plugins_dir

    plugins_dir: Path = get_plugins_dir()
    if not plugins_dir.exists():
        return []

    result: list[dict] = []
    for item in sorted(plugins_dir.iterdir()):
        if not item.is_dir():
            continue
        manifest_path = item / "plugin.json"
        if not manifest_path.exists():
            continue
        try:
            with open(manifest_path, encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to read %s: %s", manifest_path, exc)
            continue

        plugin_id = manifest.get("id", item.name)
        frontend_entry = manifest.get("entry", {}).get("frontend")

        result.append(
            {
                "id": plugin_id,
                "name": manifest.get("name", plugin_id),
                "version": manifest.get("version", "0.0.0"),
                "description": manifest.get("description", ""),
                "enabled": True,  # disk-listed plugins are assumed enabled
                "frontend_entry": frontend_entry,
            },
        )
    return result


# -- Routes ----------------------------------------------------------------


@router.get(
    "",
    summary="List loaded plugins",
    description="Return all loaded plugins with optional UI metadata.",
)
async def list_plugins(request: Request):
    """Return every loaded plugin with basic metadata and entry points.

    If the plugin loader has not yet finished initialising (backend still
    starting up when the frontend first requests the list), the response is
    built by scanning the plugins directory on disk -- the same approach used
    by the CLI ``qwenpaw plugin list`` command.  This prevents a 503 error
    that would cause the frontend to miss all plugin JS bundles.

    Plugins that declare ``entry.frontend`` in their ``plugin.json``
    include a ``frontend_entry`` URL so the frontend can dynamically
    load the plugin's JS module.
    """
    loader = getattr(request.app.state, "plugin_loader", None)

    if loader is None:
        # Backend not ready yet -- read manifests from disk (same as CLI)
        logger.debug(
            "[plugins] plugin_loader not ready, falling back to disk scan",
        )
        return _list_plugins_from_disk()

    result = []
    for _plugin_id, record in loader.get_all_loaded_plugins().items():
        manifest = record.manifest
        frontend_entry = manifest.entry.frontend
        plugin_info: dict = {
            "id": manifest.id,
            "name": manifest.name,
            "version": manifest.version,
            "description": manifest.description,
            "enabled": record.enabled,
            "frontend_entry": frontend_entry,
        }
        result.append(plugin_info)

    return result


@router.get(
    "/{plugin_id}/files/{file_path:path}",
    summary="Serve plugin static file",
    description="Serve a static file from a plugin's directory.",
)
async def serve_plugin_ui_file(
    plugin_id: str,
    file_path: str,
    request: Request,
):
    """Serve a static file that belongs to a plugin (JS / CSS / images ...).

    When the plugin loader is ready, the plugin's source path is taken from
    the in-memory record.  If the loader is not yet initialised, the file is
    resolved directly from the plugins directory on disk so that the frontend
    can still fetch JS bundles during backend startup.

    A path-traversal guard ensures the resolved path stays inside the
    plugin's source directory.
    """
    # Resolve source path -- prefer in-memory loader, fall back to disk
    loader = getattr(request.app.state, "plugin_loader", None)

    if loader is not None:
        record = loader.get_loaded_plugin(plugin_id)
        if record is None:
            raise HTTPException(404, f"Plugin '{plugin_id}' not found")
        source_path: Path = record.source_path
    else:
        # Loader not ready -- resolve from disk (same logic as CLI)
        from ...config.utils import get_plugins_dir

        candidate = get_plugins_dir() / plugin_id
        if not candidate.is_dir() or not (candidate / "plugin.json").exists():
            raise HTTPException(404, f"Plugin '{plugin_id}' not found")
        source_path = candidate

    full_path = (source_path / file_path).resolve()

    # Security: prevent path traversal
    if not full_path.is_relative_to(source_path.resolve()):
        raise HTTPException(403, "Access denied")

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(404, f"File not found: {file_path}")

    # Guess MIME type; default to application/octet-stream
    content_type, _ = mimetypes.guess_type(str(full_path))

    # For JS modules, ensure correct MIME so browsers accept dynamic import()
    if full_path.suffix in (".js", ".mjs"):
        content_type = "application/javascript"
    elif full_path.suffix == ".css":
        content_type = "text/css"

    if content_type:
        return FileResponse(
            str(full_path),
            media_type=content_type,
        )

    return FileResponse(str(full_path))


# -- HumanThinking Plugin Routes -------------------------------------------

@router.get("/humanthinking/stats")
async def humanthinking_stats():
    """Get HumanThinking memory statistics"""
    return {
        "total_memories": 0,
        "cross_session_memories": 0,
        "frozen_memories": 0,
        "active_sessions": 0,
        "emotional_states": 0
    }

@router.get("/humanthinking/config")
async def humanthinking_get_config(agent_id: str = None):
    """Get HumanThinking configuration（支持Agent隔离）"""
    return _load_ht_config(agent_id=agent_id)

@router.post("/humanthinking/config")
async def humanthinking_update_config(request: Request, agent_id: str = None):
    """Update HumanThinking configuration（支持Agent隔离）"""
    try:
        data = await request.json()
        config = _load_ht_config(agent_id=agent_id)
        config.update(data)
        _save_ht_config(config, agent_id=agent_id)
        return {"success": True, "config": config}
    except Exception as e:
        import traceback
        logger.error(f"ERROR in update_config: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/humanthinking/search")
async def humanthinking_search(request: Request):
    """Search memories"""
    data = await request.json()
    return {"memories": [], "total": 0, "query": data.get("query", "")}

@router.get("/humanthinking/emotion")
async def humanthinking_emotion():
    """Get emotional state"""
    return {
        "current_emotion": "neutral",
        "intensity": 0.5,
        "history": []
    }

@router.get("/humanthinking/sessions")
async def humanthinking_sessions():
    """Get session list"""
    return []

@router.get("/humanthinking/memories/recent")
async def humanthinking_recent_memories(limit: int = 20):
    """Get recent memories"""
    return {"memories": [], "total": 0}

@router.get("/humanthinking/memories/timeline")
async def humanthinking_timeline():
    """Get memory timeline"""
    return []

@router.post("/humanthinking/sessions/bridge")
async def humanthinking_bridge_sessions(request: Request):
    """Bridge two sessions"""
    return {"success": True}

@router.get("/humanthinking/dreams")
async def humanthinking_dreams(limit: int = 10):
    """Get dream records"""
    return []

@router.put("/humanthinking/memories/{memory_id}")
async def humanthinking_update_memory(memory_id: str, request: Request):
    """Update memory content/type/importance"""
    data = await request.json()
    return {"success": True, "memory_id": memory_id, "updated": data}

@router.delete("/humanthinking/memories/batch")
async def humanthinking_batch_delete_memories(request: Request):
    """Batch delete memories"""
    data = await request.json()
    return {"success": True, "deleted_count": len(data.get("memory_ids", []))}

@router.get("/humanthinking/sleep/status")
async def humanthinking_sleep_status(agent_id: str = None):
    """Get sleep status（支持Agent隔离）"""
    return _load_ht_sleep_state(agent_id=agent_id)

@router.get("/humanthinking/sleep/config")
async def humanthinking_sleep_config(agent_id: str = None):
    """Get sleep configuration（支持Agent隔离）"""
    return _load_ht_sleep_config(agent_id=agent_id)

@router.post("/humanthinking/sleep/config")
async def humanthinking_sleep_update_config(request: Request, agent_id: str = None):
    """Update sleep configuration（支持Agent隔离）"""
    try:
        data = await request.json()
        config = _load_ht_sleep_config(agent_id=agent_id)
        config.update(data)
        _save_ht_sleep_config(config, agent_id=agent_id)
        return {"success": True, "config": config}
    except Exception as e:
        import traceback
        logger.error(f"ERROR in sleep_update_config: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/humanthinking/sleep/force")
async def humanthinking_sleep_force(request: Request, agent_id: str = None):
    """Force sleep（支持Agent隔离）"""
    try:
        data = await request.json()
        sleep_type = data.get("sleep_type", "light")
        state = {
            "status": "sleeping",
            "sleep_type": sleep_type,
            "last_active_time": time.time()
        }
        _save_ht_sleep_state(state, agent_id=agent_id)
        return {"success": True, "sleep_type": sleep_type, "status": "sleeping"}
    except Exception as e:
        import traceback
        logger.error(f"ERROR in sleep_force: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/humanthinking/sleep/wakeup")
async def humanthinking_sleep_wakeup(agent_id: str = None):
    """Force wakeup（支持Agent隔离）"""
    try:
        state = {
            "status": "active",
            "sleep_type": None,
            "last_active_time": time.time()
        }
        _save_ht_sleep_state(state, agent_id=agent_id)
        return {"success": True, "status": "active"}
    except Exception as e:
        import traceback
        logger.error(f"ERROR in sleep_wakeup: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
