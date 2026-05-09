# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_MAX_AGENT_ID_LENGTH = 128
_AGENT_ID_PATTERN = re.compile(r'^[a-zA-Z0-9_.-]+$')


def is_docker_environment() -> bool:
    return (
        os.environ.get('QWENPAW_RUNNING_IN_CONTAINER') == '1'
        or bool(os.environ.get('QWENPAW_WORKING_DIR', '').startswith('/app'))
        or os.path.exists('/.dockerenv')
    )


def resolve_qwenpaw_dir() -> Path:
    env_dir = os.environ.get('QWENPAW_WORKING_DIR', '')
    if env_dir:
        resolved = Path(env_dir).expanduser().resolve()
        if is_docker_environment():
            logger.info(f"[paths] Docker detected, QWENPAW_WORKING_DIR={env_dir} -> {resolved}")
        return resolved
    try:
        from qwenpaw.constant import WORKING_DIR
        return WORKING_DIR
    except (ImportError, AttributeError):
        pass
    legacy = Path("~/.copaw").expanduser()
    if legacy.exists():
        return legacy.resolve()
    fallback = Path("~/.qwenpaw").expanduser().resolve()
    if is_docker_environment() and not fallback.exists():
        logger.warning(f"[paths] Docker env but QWENPAW_WORKING_DIR not set, fallback: {fallback}")
    return fallback


def resolve_agent_workspace_dir(agent_id: str) -> Path:
    try:
        from qwenpaw.config.utils import load_config
        config = load_config()
        if agent_id in config.agents.profiles:
            ws_dir = config.agents.profiles[agent_id].workspace_dir
            resolved = Path(ws_dir).expanduser().resolve()
            logger.debug(f"[workspace_resolve] agent={agent_id} -> custom workspace: {resolved}")
            return resolved
    except ImportError as e:
        logger.debug(f"[workspace_resolve] cannot import load_config: {e}")
    except Exception as e:
        logger.debug(f"[workspace_resolve] failed for agent={agent_id}: {e}")
    fallback = resolve_qwenpaw_dir() / "workspaces" / agent_id
    if is_docker_environment():
        alt = Path("/app/working") / "workspaces" / agent_id
        if alt.exists() or not fallback.exists():
            logger.info(f"[workspace_resolve] Docker: using {alt} for agent={agent_id}")
            return alt
    logger.debug(f"[workspace_resolve] agent={agent_id} -> fallback: {fallback}")
    return fallback


def validate_agent_id(agent_id: Optional[str]) -> Optional[str]:
    if not agent_id:
        return None
    if len(agent_id) > _MAX_AGENT_ID_LENGTH:
        raise ValueError(f"agent_id too long: {len(agent_id)} > {_MAX_AGENT_ID_LENGTH}")
    if not _AGENT_ID_PATTERN.match(agent_id):
        raise ValueError(f"Invalid agent_id format: {agent_id}")
    return agent_id


def safe_path_join(base: Path, *parts: str) -> Path:
    result = base.joinpath(*parts).resolve()
    base_resolved = base.resolve()
    try:
        result.relative_to(base_resolved)
    except ValueError:
        raise ValueError(f"Path traversal detected: {result} is outside {base_resolved}")
    return result


def get_db_path(agent_id: str) -> Path:
    db_path = resolve_agent_workspace_dir(agent_id) / "memory" / f"human_thinking_memory_{agent_id}.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path
