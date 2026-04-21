"""HumanThinking Memory Manager - Core Modules v1.0.0"""

from .database import HumanThinkingDB
from .memory_manager import HumanThinkingMemoryManager
from .cache_pool import AgentCachePool
from .session_buffer import SessionBuffer, MemoryItem
from .session_bridge import SessionBridgeEngine
from .emotional_engine import EmotionalContinuityEngine
from .memory_temperature import MemoryTemperature, MemoryTemperatureLevel
from .channel_adapter import (
    ChannelAdapter,
    ChannelContext,
    ChannelType,
    get_adapter,
    extract_channel_context,
    build_memory_key,
)
from .channel_aware_manager import ChannelAwareMemoryManager

# ReMe 借鉴组件 (Phase 1)
from .context_checker import ContextChecker
from .tool_result_compactor import ToolResultCompactor
from .async_summarizer import AsyncSummarizer

# Phase 2 优化组件
from .llm_compactor import LLMCompactor
from .file_memory_store import FileMemoryStore

__all__ = [
    # 核心
    "HumanThinkingDB",
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
    # ReMe 借鉴组件 (Phase 1)
    "ContextChecker",
    "ToolResultCompactor",
    "AsyncSummarizer",
    # Phase 2 优化组件
    "LLMCompactor",
    "FileMemoryStore",
]
