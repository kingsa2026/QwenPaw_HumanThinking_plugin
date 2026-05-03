# -*- coding: utf-8 -*-
"""HumanThinking Memory Manager Plugin

v1.1.5.post1 - 跟随QwenPaw版本
"""

try:
    from .plugin import HumanThinkingMemoryPlugin
    __all__ = ["HumanThinkingMemoryPlugin"]
except ImportError:
    # Allow imports during testing when qwenpaw is not available
    __all__ = []

__version__ = "1.1.5.post1"
