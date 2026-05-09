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


# ── 设置 mock 必须放在最前面 ──
_mock_qwenpaw_pkg = MagicMock()
_mock_qwenpaw_pkg.constant = MagicMock()
_mock_qwenpaw_pkg.constant.QWENPAW_HOME = str(Path(__file__).parent.parent.parent)
_mock_qwenpaw_pkg.constant.WORKSPACE_DIR = str(Path(__file__).parent.parent.parent / ".qwenpaw")
_mock_qwenpaw_pkg.constant.AGENT_WORKSPACE_DIR = str(Path(__file__).parent.parent.parent / ".qwenpaw" / "workspaces")

_mock_config_pkg = MagicMock()
_mock_config_pkg.base_config = MagicMock()

sys.modules['qwenpaw'] = _mock_qwenpaw_pkg
sys.modules['qwenpaw.constant'] = _mock_qwenpaw_pkg.constant
sys.modules['qwenpaw.config'] = _mock_config_pkg
sys.modules['qwenpaw.config.base_config'] = _mock_config_pkg.base_config
sys.modules['qwenpaw.config.config'] = _mock_config_pkg

# ── 添加 humthink 到 sys.path 以便 HumanThinking 正常导入 ──
_humthink_dir = str(Path(__file__).parent.parent.parent)
if _humthink_dir not in sys.path:
    sys.path.insert(0, _humthink_dir)

# ── 确保 HumanThinking 包可以正常被 Python 发现 ──
# 通过确保 __init__.py 存在，让 Python import 系统自然处理
_project_root = Path(__file__).parent.parent


def _ensure_package(path: Path):
    """确保路径是一个有效的包（通过补充 __init__.py 信息）"""
    pass  # __init__.py 文件已存在于项目中


_ensure_package(_project_root)
_ensure_package(_project_root / "core")
_ensure_package(_project_root / "api")
_ensure_package(_project_root / "utils")


# ── 预注册需要绕过 __init__.py 的模块 ──
# HumanThinking.core.__init__ 会导入 database 和 sleep_manager（会触发 qwenpaw 路径依赖）
# 所以预先注册 core 包和一些关键模块

# 动态发现 core/ 下所有 .py 文件并预加载到 sys.modules
import importlib.util

def _load_module_safe(full_name: str, file_path: str, package_name: str):
    """安全加载模块，设置好 __package__ 以支持相对导入"""
    spec = importlib.util.spec_from_file_location(full_name, file_path,
        submodule_search_locations=[])
    module = importlib.util.module_from_spec(spec)
    module.__package__ = package_name
    sys.modules[full_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"[conftest] Warning: Could not load {full_name}: {e}")
    return module

_core_dir = _project_root / "core"
for _py_file in sorted(_core_dir.glob("*.py")):
    _mod_name = _py_file.stem
    if _mod_name == "__init__":
        continue
    _full_name = f"HumanThinking.core.{_mod_name}"
    if _full_name not in sys.modules:
        _load_module_safe(_full_name, str(_py_file), "HumanThinking.core")

# 注册 core 包（但先不加载 __init__）
if "HumanThinking.core" not in sys.modules:
    _core_pkg = type(sys)("HumanThinking.core")
    _core_pkg.__path__ = [str(_core_dir)]
    _core_pkg.__package__ = "HumanThinking.core"
    _core_pkg.__file__ = str(_core_dir / "__init__.py")
    sys.modules["HumanThinking.core"] = _core_pkg

# 注册 api 包
_api_dir = _project_root / "api"
if "HumanThinking.api" not in sys.modules:
    _api_pkg = type(sys)("HumanThinking.api")
    _api_pkg.__path__ = [str(_api_dir)]
    _api_pkg.__package__ = "HumanThinking.api"
    _api_pkg.__file__ = str(_api_dir / "__init__.py")
    sys.modules["HumanThinking.api"] = _api_pkg

# 注册 utils 包
_utils_dir = _project_root / "utils"
if "HumanThinking.utils" not in sys.modules:
    _utils_pkg = type(sys)("HumanThinking.utils")
    _utils_pkg.__path__ = [str(_utils_dir)]
    _utils_pkg.__package__ = "HumanThinking.utils"
    _utils_pkg.__file__ = str(_utils_dir / "__init__.py")
    sys.modules["HumanThinking.utils"] = _utils_pkg

# 注册 HumanThinking 顶级包
if "HumanThinking" not in sys.modules:
    _ht_pkg = type(sys)("HumanThinking")
    _ht_pkg.__path__ = [str(_project_root)]
    _ht_pkg.__package__ = "HumanThinking"
    _ht_pkg.__file__ = str(_project_root / "__init__.py")
    sys.modules["HumanThinking"] = _ht_pkg


# ── Fixtures ──

@pytest.fixture
def temp_db_path():
    """创建临时数据库文件路径"""
    fd, path = tempfile.mkstemp(suffix='.db', prefix='test_humthink_')
    os.close(fd)
    yield Path(path)
    try:
        os.unlink(path)
        for suffix in ['.db-shm', '.db-wal']:
            wal_path = path + suffix
            if os.path.exists(wal_path):
                os.unlink(wal_path)
    except OSError:
        pass


@pytest.fixture
def sample_memory_record():
    """创建示例记忆记录"""
    return {
        "id": 1,
        "agent_id": "test_agent",
        "session_id": "test_session",
        "user_id": "test_user",
        "target_id": "test_target",
        "role": "assistant",
        "content": "用户喜欢简洁的界面设计风格",
        "importance": 4,
        "memory_type": "preference",
        "metadata": {"source": "chat", "confidence": 0.9},
        "created_at": datetime.now().isoformat(),
        "session_key": "test_session_key",
        "content_embedding": None,
        "content_summary": "偏好简洁设计",
        "importance_score": 0.8,
        "access_count": 5,
        "search_count": 2,
        "search_score": 0.5,
        "access_frozen": False,
        "frozen_at": None,
        "last_accessed_at": datetime.now().isoformat(),
        "last_searched_at": None,
        "updated_at": datetime.now().isoformat(),
        "deleted_at": None,
        "tags": ["preference", "ui", "design"]
    }


@pytest.fixture
def sample_memories():
    """创建多个示例记忆"""
    return [
        {
            "agent_id": "agent_001",
            "session_id": "session_001",
            "content": f"测试记忆内容 {i}",
            "importance": 3,
            "memory_type": "general",
            "metadata": {"index": i}
        }
        for i in range(5)
    ]


@pytest.fixture
def mock_llm_client():
    """创建模拟的 LLM 客户端"""
    client = AsyncMock()
    client.complete = AsyncMock(return_value=MagicMock(
        content="这是 LLM 生成的总结内容"
    ))
    return client


@pytest.fixture
def test_agent_id():
    """测试用的 Agent ID"""
    return "test_agent_001"


@pytest.fixture
def test_session_id():
    """测试用的 Session ID"""
    return "test_session_001"


@pytest_asyncio.fixture
async def db(temp_db_path):
    """创建已初始化的数据库实例"""
    from HumanThinking.core.database import HumanThinkingDB
    
    db = HumanThinkingDB(str(temp_db_path))
    await db.initialize()
    yield db
    try:
        await db.close()
    except Exception:
        pass


@pytest.fixture
def sleep_manager():
    """创建 SleepManager 实例"""
    from HumanThinking.core.sleep_manager import SleepManager
    
    sm = SleepManager()
    return sm


@pytest.fixture
def mock_sleep_manager():
    """创建模拟的 SleepManager"""
    sm = MagicMock()
    sm.record_activity = AsyncMock()
    sm.is_sleeping = MagicMock(return_value=False)
    sm.get_status = MagicMock(return_value={"state": "active"})
    sm.config = MagicMock()
    sm.config.sleep_enabled = True
    sm.config.light_sleep_seconds = 300
    sm.config.rem_interval = 1800
    sm.config.deep_sleep_hour = 3
    return sm


@pytest.fixture
def mock_memory_registry():
    """模拟 memory_registry"""
    with patch('HumanThinking.core.memory_manager.memory_registry', MagicMock()) as mock:
        mock.register = MagicMock()
        yield mock
