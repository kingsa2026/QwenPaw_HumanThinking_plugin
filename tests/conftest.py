# -*- coding: utf-8 -*-
"""
HumanThinking 测试共享 fixtures

提供跨测试模块的通用 fixtures 和 mocks
"""

import asyncio
import json
import os
import sqlite3
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio


# Mock qwenpaw and agentscope before any imports
sys.modules['qwenpaw'] = MagicMock()
sys.modules['qwenpaw.plugins'] = MagicMock()
sys.modules['qwenpaw.plugins.api'] = MagicMock()
sys.modules['qwenpaw.agents'] = MagicMock()
sys.modules['qwenpaw.agents.memory'] = MagicMock()
sys.modules['qwenpaw.agents.memory.base_memory_manager'] = MagicMock()
sys.modules['agentscope'] = MagicMock()
sys.modules['agentscope.message'] = MagicMock()
sys.modules['agentscope.tool'] = MagicMock()
sys.modules['agentscope.memory'] = MagicMock()

# Mock search.vector module to avoid relative import issues
search_vector_mock = MagicMock()
search_vector_mock.TFIDFSearchEngine = MagicMock()
sys.modules['search'] = MagicMock()
sys.modules['search.vector'] = search_vector_mock

# Prevent core/__init__.py from being loaded during conftest import
# by pre-loading all core submodules individually before pytest discovers conftest
# We need to import database and sleep_manager directly (bypassing __init__.py)
import importlib.util

def load_module_directly(module_name, file_path):
    """Load a module directly from file path, bypassing package __init__.py"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Get the project root
project_root = Path(__file__).parent.parent

# Pre-load all core submodules to avoid __init__.py relative import issues
# These must be loaded before memory_manager because memory_manager imports them
# Order matters: dependencies must be loaded before dependents

core_modules = [
    "session_buffer",      # No internal core dependencies
    "cache_pool",          # Depends on session_buffer
    "emotional_engine",    # No internal core dependencies
    "session_bridge",      # May depend on emotional_engine
    "memory_temperature",  # No internal core dependencies
    "channel_adapter",     # No internal core dependencies
    "context_checker",     # No internal core dependencies
    "tool_result_compactor",  # No internal core dependencies
    "async_summarizer",    # No internal core dependencies
    "llm_compactor",       # No internal core dependencies
    "file_memory_store",   # No internal core dependencies
    "channel_aware_manager",  # Depends on multiple modules
]

for mod_name in core_modules:
    mod_path = project_root / "core" / f"{mod_name}.py"
    if mod_path.exists():
        try:
            load_module_directly(f"core.{mod_name}", str(mod_path))
        except Exception as e:
            # Log but don't fail - some modules may have optional dependencies
            print(f"[conftest] Warning: Could not pre-load core.{mod_name}: {e}")

# Load database module directly
database_path = project_root / "core" / "database.py"
if database_path.exists():
    database_module = load_module_directly("core.database", str(database_path))
    sys.modules['core.database'] = database_module

# Load sleep_manager module directly
sleep_manager_path = project_root / "core" / "sleep_manager.py"
if sleep_manager_path.exists():
    sleep_manager_module = load_module_directly("core.sleep_manager", str(sleep_manager_path))
    sys.modules['core.sleep_manager'] = sleep_manager_module

# Load memory_manager module directly (must be after its dependencies)
memory_manager_path = project_root / "core" / "memory_manager.py"
if memory_manager_path.exists():
    try:
        memory_manager_module = load_module_directly("core.memory_manager", str(memory_manager_path))
        sys.modules['core.memory_manager'] = memory_manager_module
    except Exception as e:
        print(f"[conftest] Warning: Could not pre-load core.memory_manager: {e}")


# ==================== 事件循环 Fixture ====================

@pytest.fixture(scope="session")
def event_loop():
    """创建会话级事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ==================== 临时目录 Fixture ====================

@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db_path(temp_dir):
    """创建临时数据库路径"""
    return temp_dir / "test_memory.db"


# ==================== 数据库 Fixture ====================

@pytest_asyncio.fixture
async def db(temp_db_path):
    """创建并初始化测试数据库实例"""
    from core.database import HumanThinkingDB
    
    database = HumanThinkingDB(str(temp_db_path))
    await database.initialize()
    yield database
    await database.close()


@pytest.fixture
def mock_db():
    """创建 Mock 数据库实例"""
    db = MagicMock()
    db.initialize = AsyncMock(return_value=None)
    db.close = AsyncMock(return_value=None)
    db.add_memory = AsyncMock(return_value=1)
    db.get_stats = AsyncMock(return_value={
        "total_memories": 10,
        "frozen_memories": 2,
        "active_memories": 8,
        "total_sessions": 3,
        "importance_stats": {"1": 2, "3": 5, "5": 3}
    })
    db.search_memories = AsyncMock(return_value=[])
    db.get_recent_memories = AsyncMock(return_value=[])
    db.get_active_sessions = AsyncMock(return_value=[])
    db.get_session_memories = AsyncMock(return_value=[])
    db.count_memories = AsyncMock(return_value=0)
    db.add_dream_log = AsyncMock(return_value=1)
    db.add_insight = AsyncMock(return_value=1)
    db.set_memory_tier = AsyncMock(return_value=None)
    db.update_memory_score = AsyncMock(return_value=None)
    db.apply_forgetting_curve = AsyncMock(return_value=0)
    db.get_memories_for_consolidation = AsyncMock(return_value=[])
    db.get_active_memories = AsyncMock(return_value=[])
    db.update_memory_access = AsyncMock(return_value=None)
    db.wakeup_memory = AsyncMock(return_value=True)
    db.freeze_memories = AsyncMock(return_value=0)
    db.defrost_memories = AsyncMock(return_value=0)
    db.archive_to_table = AsyncMock(return_value=True)
    db.delete_old_archives = AsyncMock(return_value=0)
    db.create_memory_relation = AsyncMock(return_value=1)
    db.get_related_memories = AsyncMock(return_value=[])
    db.delete_memory_relation = AsyncMock(return_value=True)
    db.get_frozen_memories = AsyncMock(return_value=[])
    db.get_tier_stats = AsyncMock(return_value={})
    db.get_category_stats = AsyncMock(return_value={})
    db.set_working_cache = AsyncMock(return_value=None)
    db.get_working_cache = AsyncMock(return_value=None)
    db.clear_working_cache = AsyncMock(return_value=0)
    db.get_insights = AsyncMock(return_value=[])
    db.get_dream_logs = AsyncMock(return_value=[])
    db.get_access_stats = AsyncMock(return_value={})
    db.log_memory_access = AsyncMock(return_value=1)
    db.update_memory_type = AsyncMock(return_value=None)
    db.archive_memory = AsyncMock(return_value=None)
    db.update_decay = AsyncMock(return_value=None)
    db.set_memory_category = AsyncMock(return_value=None)
    db.get_low_value_memories = AsyncMock(return_value=[])
    db.recall_from_archive = AsyncMock(return_value=True)
    db.get_archive_memories = AsyncMock(return_value=[])
    db.get_archive_stats = AsyncMock(return_value={})
    db.save_reflection_summary = AsyncMock(return_value=None)
    db.get_light_sleep_memories = AsyncMock(return_value=[])
    db.batch_insert = AsyncMock(return_value=0)
    return db


# ==================== 记忆数据 Fixtures ====================

@pytest.fixture
def sample_memory():
    """创建示例记忆数据"""
    return {
        "id": 1,
        "agent_id": "test_agent",
        "session_id": "session_001",
        "user_id": "user_001",
        "target_id": "target_001",
        "role": "user",
        "content": "用户喜欢简洁的回答风格",
        "importance": 4,
        "memory_type": "preference",
        "metadata": {},
        "tags": ["preference", "style"],
        "created_at": datetime.now().isoformat(),
        "timestamp": datetime.now().isoformat(),
    }


@pytest.fixture
def sample_memories():
    """创建多条示例记忆数据"""
    base_time = datetime.now()
    return [
        {
            "id": i,
            "agent_id": "test_agent",
            "session_id": f"session_{i % 3:03d}",
            "user_id": "user_001",
            "target_id": "target_001",
            "role": "user" if i % 2 == 0 else "assistant",
            "content": f"记忆内容 {i}: {'用户喜欢简洁风格' if i == 0 else '订单号12345' if i == 1 else '感谢帮助' if i == 2 else f'一般对话内容 {i}'}",
            "importance": 5 if i < 2 else 3,
            "memory_type": "preference" if i == 0 else "fact" if i == 1 else "emotion" if i == 2 else "general",
            "metadata": {},
            "tags": [],
            "created_at": (base_time - timedelta(hours=i)).isoformat(),
            "timestamp": (base_time - timedelta(hours=i)).isoformat(),
            "emotion": "happy" if i == 2 else "",
        }
        for i in range(10)
    ]


@pytest.fixture
def similar_memories():
    """创建相似的记忆数据（用于测试合并功能）"""
    base_time = datetime.now()
    return [
        {
            "id": 1,
            "agent_id": "test_agent",
            "session_id": "session_001",
            "content": "用户喜欢简洁的回答风格，不喜欢太长的解释",
            "importance": 4,
            "memory_type": "preference",
            "tags": ["style"],
            "timestamp": base_time.isoformat(),
            "emotion": "",
        },
        {
            "id": 2,
            "agent_id": "test_agent",
            "session_id": "session_002",
            "content": "用户偏好简洁风格，不喜欢冗长回答",
            "importance": 4,
            "memory_type": "preference",
            "tags": ["preference"],
            "timestamp": (base_time - timedelta(hours=2)).isoformat(),
            "emotion": "",
        },
        {
            "id": 3,
            "agent_id": "test_agent",
            "session_id": "session_003",
            "content": "完全不同的内容，关于订单信息",
            "importance": 5,
            "memory_type": "fact",
            "tags": ["order"],
            "timestamp": (base_time - timedelta(hours=5)).isoformat(),
            "emotion": "",
        },
    ]


# ==================== SleepManager Fixtures ====================

@pytest.fixture
def sleep_config():
    """创建测试睡眠配置"""
    from core.sleep_manager import SleepConfig
    return SleepConfig(
        enable_agent_sleep=True,
        light_sleep_minutes=0.5,  # 30秒，加速测试
        rem_minutes=1.0,          # 60秒
        deep_sleep_minutes=2.0,   # 120秒
        auto_consolidate=True,
        consolidate_days=7,
        frozen_days=30,
        archive_days=90,
        delete_days=180,
        enable_insight=True,
        enable_dream_log=True,
        enable_merge=True,
        merge_similarity_threshold=0.8,
        merge_max_distance_hours=72,
    )


@pytest.fixture
def sleep_manager(sleep_config):
    """创建测试睡眠管理器"""
    from core.sleep_manager import SleepManager
    manager = SleepManager(sleep_config)
    yield manager
    # 清理全局状态
    import core.sleep_manager as sm
    sm._global_sleep_manager = None
    sm._agent_sleep_configs = {}


# ==================== MemoryManager Fixtures ====================

@pytest.fixture
def mock_memory_manager():
    """创建 Mock 记忆管理器"""
    mm = MagicMock()
    mm.agent_id = "test_agent"
    mm.user_id = "test_user"
    mm.working_dir = "/tmp/test"
    mm._current_session_id = "session_001"
    mm._current_target_id = "target_001"
    mm.db = MagicMock()
    mm.cache_pool = MagicMock()
    mm.session_bridge = MagicMock()
    mm.emotional_engine = MagicMock()
    mm.start = AsyncMock(return_value=None)
    mm.close = AsyncMock(return_value=True)
    mm.store_memory = AsyncMock(return_value=12345)
    mm.memory_search = AsyncMock(return_value=MagicMock(content="搜索结果"))
    mm.get_stats = AsyncMock(return_value={"total_memories": 10})
    mm.create_session = AsyncMock(return_value={"session_id": "new_session"})
    mm.get_session_memories = AsyncMock(return_value=[])
    mm.get_active_sessions = AsyncMock(return_value=[])
    mm.track_emotional_state = AsyncMock(return_value={})
    mm.get_emotional_context = AsyncMock(return_value={})
    mm.set_context = MagicMock(return_value=None)
    mm.get_memory_prompt = MagicMock(return_value="记忆提示词")
    mm.list_memory_tools = MagicMock(return_value=[])
    mm.post_memory_operation = AsyncMock(return_value=None)
    mm.check_context = AsyncMock(return_value=([], [], True))
    mm.compact_memory = AsyncMock(return_value="摘要")
    mm.summary_memory = AsyncMock(return_value="摘要")
    mm.get_related_historical_memories = AsyncMock(return_value=MagicMock(memories=[], total_count=0))
    mm.bridge_session = AsyncMock(return_value={})
    mm.close_session = AsyncMock(return_value=None)
    mm.dream_memory = AsyncMock(return_value=None)
    mm.compact_tool_result = AsyncMock(return_value=None)
    mm.get_in_memory_memory = MagicMock(return_value=MagicMock())
    return mm


# ==================== 情感引擎 Fixtures ====================

@pytest.fixture
def mock_emotional_engine():
    """创建 Mock 情感引擎"""
    engine = MagicMock()
    engine.track_emotional_state = AsyncMock(return_value={
        "emotion": "happy",
        "intensity": 0.8,
        "session_id": "session_001"
    })
    engine.get_emotional_context = AsyncMock(return_value={
        "current_emotion": "happy",
        "intensity": 0.8,
        "history": []
    })
    return engine


# ==================== Session Bridge Fixtures ====================

@pytest.fixture
def mock_session_bridge():
    """创建 Mock 会话桥接引擎"""
    bridge = MagicMock()
    bridge.bridge_new_session = AsyncMock(return_value={
        "session_id": "new_session",
        "inherited_sessions": ["old_session"],
        "inherited_memories": 5,
        "emotional_context": {}
    })
    return bridge


# ==================== 环境 Fixtures ====================

@pytest.fixture(autouse=True)
def reset_global_state():
    """每个测试后重置全局状态"""
    yield
    # 清理 sleep_manager 全局状态 - use direct module path
    try:
        from core import sleep_manager as sm
        sm._global_sleep_manager = None
        sm._agent_sleep_configs = {}
    except Exception:
        pass
    
    # 清理 memory_manager 全局状态
    try:
        from core import memory_manager as mm
        mm._agent_configs = {}
        mm._global_config = mm.HumanThinkingConfig()
    except Exception:
        pass


# ==================== FastAPI Test Client Fixture ====================

@pytest.fixture
def app():
    """创建 FastAPI 测试应用"""
    from fastapi import FastAPI
    from api.routes import router
    
    application = FastAPI()
    application.include_router(router, prefix="/api/plugins/humanthinking")
    return application


@pytest.fixture
def client(app):
    """创建测试客户端"""
    from fastapi.testclient import TestClient
    return TestClient(app)


# ==================== 日志 Fixture ====================

@pytest.fixture
def caplog_handler(caplog):
    """配置日志捕获级别"""
    caplog.set_level("DEBUG")
    return caplog
