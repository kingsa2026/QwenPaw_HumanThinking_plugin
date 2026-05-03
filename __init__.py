# -*- coding: utf-8 -*-
"""HumanThinking Memory Manager Plugin

v1.4.4 - Human Thinking Memory Plugin
"""

try:
    from .plugin import HumanThinkingMemoryPlugin
    __all__ = ["HumanThinkingMemoryPlugin"]
except ImportError:
    # Allow imports during testing when qwenpaw is not available
    __all__ = []

__version__ = "1.4.4"
