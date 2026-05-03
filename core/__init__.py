"""HumanThinking Memory Manager - Core Modules v1.0.0"""

import logging

logger = logging.getLogger(__name__)

# 基础模块（无外部依赖）
from .database import HumanThinkingDB
from .sleep_manager import (
    SleepManager, get_sleep_manager, init_sleep_manager,
    record_agent_activity, pulse_agent, is_agent_sleeping, check_and_trigger_sleep,
    get_agent_sleep_config, save_agent_sleep_config, load_agent_sleep_config
)

# 可选模块（有外部依赖，导入失败时记录日志但不阻塞）
_optional_imports = {
    'memory_manager': ['HumanThinkingMemoryManager'],
    'cache_pool': ['AgentCachePool'],
    'session_buffer': ['SessionBuffer', 'MemoryItem'],
    'session_bridge': ['SessionBridgeEngine'],
    'emotional_engine': ['EmotionalContinuityEngine'],
    'memory_temperature': ['MemoryTemperature', 'MemoryTemperatureLevel'],
    'channel_adapter': ['ChannelAdapter', 'ChannelContext', 'ChannelType', 'get_adapter', 'extract_channel_context', 'build_memory_key'],
    'channel_aware_manager': ['ChannelAwareMemoryManager'],
    'context_checker': ['ContextChecker'],
    'tool_result_compactor': ['ToolResultCompactor'],
    'async_summarizer': ['AsyncSummarizer'],
    'llm_compactor': ['LLMCompactor'],
    'file_memory_store': ['FileMemoryStore'],
}

# 动态导入可选模块
for module_name, exports in _optional_imports.items():
    try:
        module = __import__(f'{__name__}.{module_name}', fromlist=exports)
        for export in exports:
            try:
                globals()[export] = getattr(module, export)
            except AttributeError:
                logger.debug(f"Optional export '{export}' not found in '{module_name}'")
                if export not in globals():
                    globals()[export] = None
    except ImportError as e:
        logger.debug(f"Optional module '{module_name}' not available: {e}")
        # 创建占位符，避免 NameError
        for export in exports:
            if export not in globals():
                globals()[export] = None

__all__ = [
    # 核心
    "HumanThinkingDB",
    "SleepManager",
    "get_sleep_manager",
    "init_sleep_manager",
    "record_agent_activity",
    "pulse_agent",
    "is_agent_sleeping",
    "check_and_trigger_sleep",
    "get_agent_sleep_config",
    "save_agent_sleep_config",
    "load_agent_sleep_config",
    # 可选（可能为 None）
    "HumanThinkingMemoryManager",
    "AgentCachePool",
    "SessionBuffer",
    "MemoryItem",
    "SessionBridgeEngine",
    "EmotionalContinuityEngine",
    "MemoryTemperature",
    "MemoryTemperatureLevel",
    "ChannelAdapter",
    "ChannelContext",
    "ChannelType",
    "get_adapter",
    "extract_channel_context",
    "build_memory_key",
    "ChannelAwareMemoryManager",
    "ContextChecker",
    "ToolResultCompactor",
    "AsyncSummarizer",
    "LLMCompactor",
    "FileMemoryStore",
]
