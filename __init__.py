"""HumanThinking Memory Manager v1.0.0-beta0.1

跨Session认知与情感连续性解决方案
"""

__version__ = "1.0.0-beta0.1"
__version_info__ = (1, 0, 0, "beta0.1")

# 核心模块
from .core.memory_manager import HumanThinkingMemoryManager
from .core.channel_adapter import (
    ChannelAdapter,
    ChannelContext,
    ChannelType,
    get_adapter,
    extract_channel_context,
    build_memory_key,
)
from .core.channel_aware_manager import ChannelAwareMemoryManager
from .core.memory_temperature import MemoryTemperature, MemoryTemperatureLevel

# ReMe 借鉴组件 (Phase 1)
from .core.context_checker import ContextChecker
from .core.tool_result_compactor import ToolResultCompactor
from .core.async_summarizer import AsyncSummarizer

# Phase 2 优化组件
from .core.llm_compactor import LLMCompactor
from .core.file_memory_store import FileMemoryStore

# Phase 3 优化组件
from .core.memory_lifecycle import MemoryLifecycle, MemoryState, LifecycleConfig

# 搜索模块
from .search.vector import TFIDFSearchEngine
from .search.cross_session_searcher import CrossSessionSearcher
from .search.relevance_ranker import RelevanceRanker
from .search.specialized_retrievers import (
    BaseRetriever,
    PersonalRetriever,
    TaskRetriever,
    ToolRetriever,
)
from .search.vector_store_backend import (
    VectorStoreBackend,
    VectorBackendType,
    VectorRecord,
    SearchResult,
)
from .search.agentic_retriever import (
    AgenticRetriever,
    RetrievalStrategy,
    RetrievalAction,
    RetrievalResult,
)

# 钩子模块
from .hooks.memory_hooks import MemoryHook, HookManager, DeduplicationHook, ImportanceCalculatorHook
from .hooks.feishu_message_parser import parse_message

# 工具模块
from .utils.migrator import Migration, Migrator
from .utils.version import VersionManager, CURRENT_VERSION, CURRENT_SCHEMA_VERSION

__all__ = [
    # 核心
    "HumanThinkingMemoryManager",
    "ChannelAwareMemoryManager",
    "ChannelAdapter",
    "ChannelContext",
    "ChannelType",
    "get_adapter",
    "extract_channel_context",
    "build_memory_key",
    "MemoryTemperature",
    "MemoryTemperatureLevel",
    # ReMe 借鉴组件 (Phase 1)
    "ContextChecker",
    "ToolResultCompactor",
    "AsyncSummarizer",
    # Phase 2 优化组件
    "LLMCompactor",
    "FileMemoryStore",
    # Phase 3 优化组件
    "MemoryLifecycle",
    "MemoryState",
    "LifecycleConfig",
    "VectorStoreBackend",
    "VectorBackendType",
    "VectorRecord",
    "SearchResult",
    "AgenticRetriever",
    "RetrievalStrategy",
    "RetrievalAction",
    "RetrievalResult",
    # 搜索
    "TFIDFSearchEngine",
    "CrossSessionSearcher",
    "RelevanceRanker",
    "BaseRetriever",
    "PersonalRetriever",
    "TaskRetriever",
    "ToolRetriever",
    # 钩子
    "MemoryHook",
    "HookManager",
    "DeduplicationHook",
    "ImportanceCalculatorHook",
    "parse_message",
    # 工具
    "Migration",
    "Migrator",
    "VersionManager",
    "CURRENT_VERSION",
    "CURRENT_SCHEMA_VERSION",
]
