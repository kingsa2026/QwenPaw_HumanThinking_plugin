# -*- coding: utf-8 -*-
"""
HumanThinking 数据库单元测试

测试覆盖：
- 数据库初始化
- 记忆增删改查
- target_id 隔离
- 记忆关联
- 温度/冻结系统
- 统计功能
"""

import asyncio
import os
import pytest
import tempfile
import sys
import importlib.util
from pathlib import Path

# 直接导入模块文件，绕过包初始化
test_dir = Path(__file__).parent.parent

def load_module(name, path):
    """动态加载模块"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# 按依赖顺序加载模块
db_module = load_module("database", test_dir / "core" / "database.py")
HumanThinkingDB = db_module.HumanThinkingDB
MemoryRecord = db_module.MemoryRecord

# 缓存模块
cache_module = load_module("cache_pool", test_dir / "core" / "cache_pool.py")
AgentCachePool = cache_module.AgentCachePool

# 渠道适配器模块
adapter_module = load_module("channel_adapter", test_dir / "core" / "channel_adapter.py")
ChannelAdapter = adapter_module.ChannelAdapter
ChannelContext = adapter_module.ChannelContext
ChannelType = adapter_module.ChannelType
FeishuAdapter = adapter_module.FeishuAdapter
WeixinAdapter = adapter_module.WeixinAdapter
QQAdapter = adapter_module.QQAdapter
DingTalkAdapter = adapter_module.DingTalkAdapter
TelegramAdapter = adapter_module.TelegramAdapter
DiscordAdapter = adapter_module.DiscordAdapter
get_adapter = adapter_module.get_adapter
extract_channel_context = adapter_module.extract_channel_context
build_memory_key = adapter_module.build_memory_key
parse_memory_key = adapter_module.parse_memory_key

# 温度模块
temp_module = load_module("memory_temperature", test_dir / "core" / "memory_temperature.py")
MemoryTemperature = temp_module.MemoryTemperature
MemoryTemperatureLevel = temp_module.MemoryTemperatureLevel
HOT_THRESHOLD = temp_module.HOT_THRESHOLD
WARM_THRESHOLD = temp_module.WARM_THRESHOLD
COOL_THRESHOLD = temp_module.COOL_THRESHOLD

# 搜索模块
vector_module = load_module("vector_search", test_dir / "search" / "vector.py")
TFIDFSearchEngine = vector_module.TFIDFSearchEngine

cross_session_module = load_module("cross_session_searcher", test_dir / "search" / "cross_session_searcher.py")
CrossSessionSearcher = cross_session_module.CrossSessionSearcher

ranker_module = load_module("relevance_ranker", test_dir / "search" / "relevance_ranker.py")
RelevanceRanker = ranker_module.RelevanceRanker

# 钩子模块
hooks_module = load_module("memory_hooks", test_dir / "hooks" / "memory_hooks.py")
MemoryHook = hooks_module.MemoryHook
HookManager = hooks_module.HookManager
DeduplicationHook = hooks_module.DeduplicationHook
ImportanceCalculatorHook = hooks_module.ImportanceCalculatorHook

parser_module = load_module("feishu_message_parser", test_dir / "hooks" / "feishu_message_parser.py")
FeishuMessageParser = parser_module.FeishuMessageParser
WechatMessageParser = parser_module.WechatMessageParser
parse_message = parser_module.parse_message

# 工具模块
migrator_module = load_module("migrator", test_dir / "utils" / "migrator.py")
Migration = migrator_module.Migration
Migrator = migrator_module.Migrator

version_module = load_module("version_manager", test_dir / "utils" / "version.py")
VersionManager = version_module.VersionManager


@pytest.fixture
def db_path():
    """创建临时数据库路径"""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test_memory.db")
        yield path


@pytest.fixture
async def db(db_path):
    """创建并初始化数据库"""
    database = HumanThinkingDB(db_path)
    await database.initialize()
    yield database
    await database.close()
