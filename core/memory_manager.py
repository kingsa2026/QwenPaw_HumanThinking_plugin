# -*- coding: utf-8 -*-
"""HumanThinking Memory Manager - Main Module v1.0.0

实现 QwenPaw BaseMemoryManager 接口，支持会话隔离和情感连续性
"""

import asyncio
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from qwenpaw.agents.memory.base_memory_manager import BaseMemoryManager
from agentscope.message import Msg
from agentscope.tool import ToolResponse
from agentscope.memory import InMemoryMemory

from .database import HumanThinkingDB
from .cache_pool import AgentCachePool
from .session_buffer import MemoryItem
from .session_bridge import SessionBridgeEngine
from .emotional_engine import EmotionalContinuityEngine
from ..search.vector import TFIDFSearchEngine

logger = logging.getLogger(__name__)


@dataclass
class HumanThinkingConfig:
    """HumanThinking 配置"""
    enable_cross_session: bool = True
    enable_emotion: bool = True
    enable_session_isolation: bool = True
    enable_memory_freeze: bool = True
    session_idle_timeout: int = 180
    refresh_interval: int = 5
    max_results: int = 5
    max_memory_chars: int = 150


_global_config = HumanThinkingConfig()


def get_config() -> HumanThinkingConfig:
    """获取全局配置"""
    return _global_config


def update_config(config: HumanThinkingConfig):
    """更新全局配置"""
    global _global_config
    _global_config = config


@dataclass
class MemoryResponse:
    """记忆搜索响应结果"""
    memories: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    query: str = ""


class ContextLoadingInMemory(InMemoryMemory):
    """自定义 InMemoryMemory，从读缓存和向量检索加载历史上下文
    
    重写 get_memory() 方法，在返回上下文时注入历史会话记忆，
    实现跨 session 的认知连续性。
    
    刷新机制：
    - 首次加载：对话开始时从缓存/DB 检索相关记忆
    - 定时刷新：每 5 轮对话重新检索（跟随话题变化）
    """
    
    # 每 N 轮对话重新加载上下文
    REFRESH_INTERVAL = 5
    
    # 对齐 ReMeLight 标准的上下文加载参数
    MAX_RESULTS_DB_MISS = 5    # 缓存未命中时 DB 查询数量（同 ReMeLight max_results=5）
    MAX_RESULTS_DB_HIT = 3     # 缓存命中时 DB 补充数量
    MAX_RESULTS_FINAL = 5      # 最终注入上下文的最大记忆数
    MAX_MEMORY_CHARS = 150     # 单条记忆最大字符数（对齐 ReMeLight 摘要压缩机制）
    
    # 排除最近N轮对话的记忆，防止与QwenPaw压缩摘要重复
    # QwenPaw压缩后保留最近3轮，所以排除最近3轮
    EXCLUDE_RECENT_ROUNDS = 3
    ROUND_DURATION_SECONDS = 300  # 每轮约5分钟
    
    def __init__(self):
        super().__init__()
        self._memory_manager_ref: Optional["HumanThinkingMemoryManager"] = None
        self._context_loaded = False
        self._message_count_since_load = 0
        self._compressed_summary = ""
    
    async def get_memory(self, prepend_summary: bool = True, **kwargs) -> List[Msg]:
        """
        获取上下文记忆，注入向量检索的历史记忆
        
        刷新机制：
        - 首次调用时，从当前对话内容提取查询词，向量检索相关历史记忆
        - 每 5 轮对话后自动重新检索，跟随话题变化
        """
        self._message_count_since_load += 1
        
        # 首次加载 或 达到刷新阈值
        should_refresh = (
            not self._context_loaded or
            self._message_count_since_load >= self.REFRESH_INTERVAL
        )
        
        if should_refresh and self._memory_manager_ref:
            await self._load_context_from_cache()
            self._context_loaded = True
            self._message_count_since_load = 0
        
        return await super().get_memory(prepend_summary=prepend_summary, **kwargs)
    
    async def _load_context_from_cache(self):
        """从数据库加载相关历史记忆到长期记忆
        
        流程：
        1. 从当前对话提取查询词
        2. 直接查询数据库（排除最近N轮，防止与原生压缩重复）
        3. 构建长期记忆（包含渠道来源标识）
        
        注：不使用读缓存，直接查DB更简洁
        """
        manager = self._memory_manager_ref
        if not manager or not manager.db:
            return
        
        # 1. 从当前对话内容提取查询词
        query = self._build_query_from_context()
        if not query:
            return
        
        # 2. 直接查询数据库（排除最近N轮，防止与原生压缩重复）
        db_results = await manager.db.search_memories(
            query=query,
            agent_id=manager.agent_id,
            session_id=None,
            user_id=manager.user_id,
            role=None,
            cross_session=True,
            max_results=self.MAX_RESULTS_FINAL,  # 5
            exclude_recent_rounds=self.EXCLUDE_RECENT_ROUNDS,
            round_duration_seconds=self.ROUND_DURATION_SECONDS
        )
        
        if not db_results:
            return
        
        # 3. 构建长期记忆
        self._build_long_term_memory(db_results)
    
    def _build_long_term_memory(self, memories: list):
        """构建长期记忆字符串"""
        # 按重要性排序
        memories.sort(key=lambda m: m.importance, reverse=True)
        top_memories = memories[:self.MAX_RESULTS_FINAL]
        
        # 构建格式化的记忆字符串
        memory_parts = []
        for m in top_memories:
            role_prefix = "用户" if m.role == "user" else "助手"
            channel_name = self._extract_channel_name(m.session_id)
            channel_tag = f" ({channel_name})" if channel_name else ""
            
            # 格式: [角色 (渠道)]: 内容
            memory_parts.append(f"[{role_prefix}{channel_tag}]: {m.content[:self.MAX_MEMORY_CHARS]}")
        
        if memory_parts:
            self._long_term_memory = "## 相关历史记忆\n\n" + "\n\n".join(memory_parts)
            logger.debug(f"Loaded {len(memory_parts)} relevant memories into context")
    
    def _extract_channel_name(self, session_id: str) -> str:
        """从 session_id 中提取渠道名称
        
        session_id 格式: channel:user_id  (如 discord:alice, feishu:12345)
        
        Returns:
            渠道名称（如 discord, feishu, web），如果没有渠道前缀则返回空字符串
        """
        if not session_id:
            return ""
        
        parts = session_id.split(":", 1)
        if len(parts) > 1:
            channel = parts[0].lower()
            # 渠道名称映射
            channel_names = {
                "web": "Web",
                "discord": "Discord",
                "feishu": "飞书",
                "wechat": "微信",
                "dingtalk": "钉钉",
                "telegram": "Telegram",
                "slack": "Slack",
                "xiaoyi": "小艺",
                "voice": "语音",
            }
            return channel_names.get(channel, channel.capitalize())
        
        return ""
    
    def _build_query_from_context(self) -> str:
        """从当前对话内容中提取查询词"""
        # 从 content 中获取最近的对话内容
        if not self.content:
            return ""
        
        # 取最近 3 条对话的内容作为查询
        recent_messages = []
        for msg, marks in reversed(self.content):
            if hasattr(msg, "content"):
                content = msg.content if isinstance(msg.content, str) else str(msg.content)
                recent_messages.append(content)
            if len(recent_messages) >= 3:
                break
        
        if not recent_messages:
            return ""
        
        # 拼接作为查询词
        query = " ".join(recent_messages[::-1])
        # 截断到 500 字符
        return query[:500]
    
    async def clear_context(self):
        """清除已加载的上下文标记，允许重新加载"""
        self._context_loaded = False
        self._long_term_memory = ""
        self._message_count_since_load = 0
    
    # ====== Memory Compaction Hook 兼容方法 ======
    
    def get_compressed_summary(self) -> str:
        """返回压缩摘要（供 memory_compact_hook 调用）"""
        return self._compressed_summary
    
    async def update_compressed_summary(self, content: str) -> None:
        """更新压缩摘要（供 memory_compact_hook 调用）"""
        self._compressed_summary = content
    
    async def mark_messages_compressed(self, messages: list) -> int:
        """标记消息为已压缩（供 memory_compact_hook 调用）"""
        return 0


class HumanThinkingMemoryManager(BaseMemoryManager):
    """
    HumanThinking Memory Manager v1.0.0
    
    解决 QwenPaw Agent 跨Session认知与情感连续性问题
    """
    
    def __init__(
        self,
        working_dir: str,
        agent_id: str,
        user_id: Optional[str] = None,
        current_session_id: Optional[str] = None
    ):
        """
        Args:
            working_dir: QwenPaw 工作目录
            agent_id: Agent ID (必填)
            user_id: User ID (可选)
            current_session_id: 当前 Session ID (可选)
        """
        if not agent_id:
            raise ValueError("agent_id is required")
        
        super().__init__(working_dir=working_dir, agent_id=agent_id)
        
        self.user_id = user_id
        self._current_session_id = current_session_id
        
        # 核心组件
        self.db: Optional[HumanThinkingDB] = None
        self.cache_pool: Optional[AgentCachePool] = None
        self.session_bridge: Optional[SessionBridgeEngine] = None
        self.emotional_engine: Optional[EmotionalContinuityEngine] = None
        
        # 内存记忆适配器（持久化）
        self._in_memory_memory: Optional[ContextLoadingInMemory] = None
        
        # 数据库路径
        self.db_path = Path(working_dir) / "memory" / f"human_thinking_memory_{agent_id}.db"
        
        logger.info(
            f"HumanThinkingMemoryManager v1.0.0 initialized: "
            f"agent_id={agent_id}, user_id={user_id}"
        )
    
    def set_context(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        role: str = "assistant"
    ):
        """
        设置会话上下文
        
        Args:
            session_id: Session ID
            user_id: User ID
            role: Role
        """
        self._current_session_id = session_id
        if user_id:
            self.user_id = user_id
        
        # 新 session 时重置上下文加载标记
        if self._in_memory_memory:
            self._in_memory_memory._context_loaded = False
            self._in_memory_memory._long_term_memory = ""
        
        logger.debug(
            f"Context set: session={session_id}, user={user_id}, role={role}"
        )
    
    async def start(self) -> None:
        """启动记忆管理器"""
        logger.info(f"Starting HumanThinkingMemoryManager v1.0.0...")
        
        # 1. 初始化数据库
        self.db = HumanThinkingDB(str(self.db_path))
        await self.db.initialize()
        
        # 2. 初始化缓存池
        self.cache_pool = AgentCachePool(
            agent_id=self.agent_id,
            db=self.db
        )
        await self.cache_pool.start()
        
        # 3. 初始化会话桥接引擎
        self.session_bridge = SessionBridgeEngine(
            db=self.db,
            search_engine=None
        )
        
        # 4. 初始化情感引擎
        self.emotional_engine = EmotionalContinuityEngine(db=self.db)
        
        logger.info("HumanThinkingMemoryManager v1.0.0 started successfully")
    
    async def close(self) -> None:
        """关闭记忆管理器"""
        logger.info("Closing HumanThinkingMemoryManager v1.0.0...")
        
        if self.cache_pool:
            await self.cache_pool.close()
        
        if self.db:
            await self.db.close()
        
        logger.info("HumanThinkingMemoryManager v1.0.0 closed")
    
    async def post_memory_operation(
        self,
        agent_id: str,
        session_id: str,
        user_id: Optional[str],
        operation_type: str,
        status: str,
        **kwargs
    ) -> None:
        """
        对话轮次结束后触发的缓存刷新钩子
        
        Args:
            agent_id: Agent ID
            session_id: Session ID
            user_id: User ID
            operation_type: 操作类型 (turn_end, session_end, etc.)
            status: 操作状态 (completed, failed, etc.)
        """
        if status != "completed" or not self.cache_pool:
            return
        
        await self.cache_pool.flush_on_turn_end()
        
        logger.debug(
            f"post_memory_operation: op={operation_type}, "
            f"session={session_id}, status={status}"
        )
    
    async def store_memory(
        self,
        content: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        role: str = "assistant",
        importance: int = 3,
        memory_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        存储记忆（会话隔离）
        """
        sid = session_id or self._current_session_id
        uid = user_id or self.user_id
        
        if not sid:
            raise ValueError("session_id is required (call set_context() or pass explicitly)")
        
        memory = MemoryItem(
            content=content,
            agent_id=self.agent_id,
            session_id=sid,
            user_id=uid,
            role=role,
            importance=importance,
            memory_type=memory_type,
            metadata=metadata or {}
        )
        
        temp_id = await self.cache_pool.store(memory, sid)
        
        logger.debug(f"Stored memory: temp_id={temp_id}, session={sid}")
        return hash(temp_id) % 1000000
    
    async def memory_search(
        self,
        query: str,
        max_results: int = 5,
        min_score: float = 0.1,
    ) -> ToolResponse:
        """
        搜索记忆（TF-IDF 语义搜索）
        
        对齐 ReMeLight 的 memory_search 实现：
        1. TF-IDF 语义检索（优于简单 LIKE）
        2. 按相关性排序
        3. 跨 Session 检索
        """
        sid = self._current_session_id
        uid = self.user_id
        
        if not self.db:
            return ToolResponse(content="Database not initialized")
        
        # 1. 使用 TF-IDF 语义搜索数据库
        tfidf_engine = TFIDFSearchEngine()
        
        # 从数据库获取所有记忆用于 TF-IDF 索引
        # 注：实际使用中可预先构建索引，此处为简化实现
        memories = await self.db.get_active_memories(
            agent_id=self.agent_id,
            limit=1000  # 限制搜索范围
        )
        
        # 构建 TF-IDF 索引
        for m in memories:
            tfidf_engine.add_document(str(m.id), m.content)
        
        # TF-IDF 语义搜索
        tfidf_results = tfidf_engine.search(
            query=query,
            max_results=max_results * 2,  # 多取一些以便后续合并
            min_score=min_score
        )
        
        # 2. 获取对应的 MemoryRecord
        all_memories = []
        memory_map = {str(m.id): m for m in memories}
        
        for doc_id, tfidf_score in tfidf_results:
            if doc_id in memory_map:
                m = memory_map[doc_id]
                all_memories.append({
                    "content": m.content,
                    "score": tfidf_score,
                    "source": m.session_id,
                    "session_id": m.session_id,
                    "created_at": m.created_at
                })
        
        # 3. 合并缓存中的相关记忆（缓存优先级更高）
        cached_memories = await self.cache_pool.search(query, sid) if self.cache_pool else []
        for m in cached_memories[:max_results]:
            # 检查是否已在结果中
            if not any(existing["content"] == m.content for existing in all_memories):
                all_memories.append({
                    "content": m.content,
                    "score": 0.95,  # 缓存命中赋予较高分数
                    "source": m.session_id,
                    "session_id": m.session_id,
                    "created_at": m.created_at
                })
        
        # 4. 按分数排序并限制结果数
        all_memories.sort(key=lambda x: x["score"], reverse=True)
        filtered_memories = all_memories[:max_results]
        
        # 5. 构建响应
        if not filtered_memories:
            return ToolResponse(content="未找到相关记忆")
        
        result_parts = []
        for m in filtered_memories:
            result_parts.append(
                f"[{m['source']}] (相关性: {m['score']:.2f})\n{m['content']}"
            )
        
        return ToolResponse(content="\n---\n".join(result_parts))
    
    async def get_related_historical_memories(
        self,
        context: str,
        current_session_id: Optional[str] = None,
        max_results: int = 5
    ) -> MemoryResponse:
        """获取相关历史记忆"""
        return await self.memory_search(
            query=context,
            session_id=current_session_id,
            cross_session=True,
            max_results=max_results
        )
    
    async def compact_memory(
        self,
        messages: list[Msg],
        previous_summary: str = "",
        extra_instruction: str = "",
        **kwargs,
    ) -> str:
        """
        压缩消息为摘要（对齐 ReMeLight 标准）
        
        使用 LLM 将旧消息压缩为简洁摘要，保持上下文连续性。
        对齐 ReMeLight 的 compact_memory 实现。
        """
        if not messages:
            return ""
        
        # 使用配置的 LLM 进行摘要（如果可用）
        if self.chat_model and self.formatter:
            try:
                return await self._llm_compact_memory(
                    messages=messages,
                    previous_summary=previous_summary,
                    extra_instruction=extra_instruction,
                )
            except Exception as e:
                logger.warning(f"LLM compact failed, falling back to simple: {e}")
        
        # 回退方案：简单拼接
        return self._simple_compact(messages, previous_summary)
    
    async def _llm_compact_memory(
        self,
        messages: list[Msg],
        previous_summary: str = "",
        extra_instruction: str = "",
    ) -> str:
        """使用 LLM 压缩记忆（对齐 ReMeLight）"""
        from agentscope.message import Msg as AgentMsg, TextBlock
        
        # 构建压缩提示词
        prompt_parts = []
        
        if previous_summary:
            prompt_parts.append(f"## 之前的摘要\n{previous_summary}\n")
        
        prompt_parts.append("## 需要压缩的消息\n")
        for msg in messages:
            content = msg.content if hasattr(msg, "content") else str(msg)
            if isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text":
                            text_parts.append(block.get("text", ""))
                        elif block.get("type") == "tool_use":
                            tool_name = block.get("name", "unknown")
                            tool_input = str(block.get("input", ""))[:200]
                            text_parts.append(f"[工具调用: {tool_name}] {tool_input}")
                    elif hasattr(block, "text"):
                        text_parts.append(block.text)
                content = "\n".join(text_parts)
            
            role = msg.role if hasattr(msg, "role") else "unknown"
            prompt_parts.append(f"[{role}]: {content[:500]}")
        
        if extra_instruction:
            prompt_parts.append(f"\n## 额外指令\n{extra_instruction}")
        
        prompt_parts.append(
            "\n\n请将以上对话压缩为简洁的摘要，保留关键信息、决策和事实。"
            "摘要应简洁明了，不超过原文的 25%。"
        )
        
        user_msg = AgentMsg(
            name="system",
            role="user",
            content=[TextBlock(type="text", text="\n".join(prompt_parts))],
        )
        
        response = await self.chat_model(user_msg)
        
        if response and hasattr(response, "content"):
            content = response.content
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        return block.get("text", "")
                    elif hasattr(block, "text"):
                        return block.text
            elif isinstance(content, str):
                return content
        
        return ""
    
    def _simple_compact(self, messages: list[Msg], previous_summary: str = "") -> str:
        """简单压缩方案（回退用）"""
        compacted = []
        current_length = 0
        max_length = 4000  # 简单限制
        
        for msg in reversed(messages):
            content = msg.content if hasattr(msg, "content") else str(msg)
            if isinstance(content, list):
                content = str(content)
            
            if current_length + len(content) > max_length:
                break
            compacted.insert(0, content[:300])
            current_length += len(content)
        
        result = "\n".join(compacted)
        if previous_summary:
            result = f"{previous_summary}\n\n---\n\n{result}"
        
        return result
    
    async def summary_memory(
        self,
        messages: list[Msg],
        **kwargs,
    ) -> str:
        """记忆摘要"""
        if not messages:
            return ""
        
        summary_parts = []
        total_length = 0
        
        for msg in messages[:10]:
            content = msg.content if hasattr(msg, "content") else str(msg)
            if total_length + len(content) > 1000:
                break
            summary_parts.append(content)
            total_length += len(content)
        
        return "\n".join(summary_parts)
    
    async def check_context(self, **kwargs) -> tuple:
        """
        上下文检查（对齐 ReMeLight 标准）
        
        ReMeLight 标准：
        - max_input_length: 128K tokens
        - compact_threshold: 75% of max = 96K tokens 触发压缩
        - compact_reserve: 10% of max = 12.8K tokens 保留最近消息
        
        使用 byte/4 近似 token 计数（对齐 ReMeLight 的 token 估算方式）
        """
        messages = kwargs.get("messages", [])
        memory_compact_threshold = kwargs.get("memory_compact_threshold", 96 * 1024)
        memory_compact_reserve = kwargs.get("memory_compact_reserve", 12 * 1024)
        
        if not messages:
            return [], [], True
        
        # 使用 byte/4 近似 token 计数
        def estimate_tokens(text: str) -> int:
            if isinstance(text, str):
                return len(text.encode("utf-8")) // 4
            return len(str(text).encode("utf-8")) // 4
        
        def msg_tokens(msg) -> int:
            content = msg.content if hasattr(msg, "content") else ""
            if isinstance(content, list):
                total = 0
                for block in content:
                    if isinstance(block, dict):
                        total += estimate_tokens(block.get("text", ""))
                    elif hasattr(block, "text"):
                        total += estimate_tokens(block.text)
                return total
            return estimate_tokens(content)
        
        # 计算总 token 数
        total_tokens = sum(msg_tokens(m) for m in messages)
        
        if total_tokens <= memory_compact_threshold:
            # 未达阈值，不需要压缩
            return [], messages, True
        
        # 需要压缩：从旧到新累积，保留最近 reserve 数量的消息
        tokens_to_compact = 0
        messages_to_compact = []
        remaining_messages = []
        
        # 先从新到旧找需要保留的消息
        reserved_tokens = 0
        keep_from_idx = len(messages)
        
        for i in range(len(messages) - 1, -1, -1):
            if reserved_tokens >= memory_compact_reserve:
                keep_from_idx = i + 1
                break
            reserved_tokens += msg_tokens(messages[i])
        
        # 分割消息
        messages_to_compact = messages[:keep_from_idx]
        remaining_messages = messages[keep_from_idx:]
        
        if not messages_to_compact:
            return [], messages, True
        
        is_valid = total_tokens < (memory_compact_threshold * 1.5)
        
        logger.debug(
            f"Context check: total={total_tokens}, threshold={memory_compact_threshold}, "
            f"reserve={memory_compact_reserve}, compact={len(messages_to_compact)}, "
            f"keep={len(remaining_messages)}"
        )
        
        return messages_to_compact, remaining_messages, is_valid
    
    async def create_session(
        self,
        session_id: str,
        user_id: Optional[str] = None,
        trigger_context: Optional[str] = None
    ) -> Dict:
        """创建新Session并继承历史记忆"""
        uid = user_id or self.user_id
        
        if not self.session_bridge:
            return {
                "session_id": session_id,
                "inherited_sessions": [],
                "inherited_memories": 0,
                "emotional_context": {}
            }
        
        bridge_context = await self.session_bridge.bridge_new_session(
            agent_id=self.agent_id,
            user_id=uid,
            new_session_id=session_id,
            trigger_context=trigger_context or ""
        )
        
        self.set_context(session_id, uid)
        
        return bridge_context
    
    async def bridge_session(
        self,
        old_session_id: str,
        new_session_id: str,
        trigger_context: str
    ) -> Dict:
        """桥接两个Session"""
        if not self.session_bridge:
            return {}
        
        return await self.session_bridge.bridge_new_session(
            agent_id=self.agent_id,
            user_id=self.user_id,
            new_session_id=new_session_id,
            trigger_context=trigger_context
        )
    
    async def close_session(self, session_id: str) -> None:
        """关闭Session"""
        if self.cache_pool:
            await self.cache_pool.close_session(session_id)
    
    async def get_session_memories(
        self,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """获取Session记忆"""
        memories = await self.db.get_session_memories(
            agent_id=self.agent_id,
            session_id=session_id,
            limit=limit,
            offset=offset
        )
        
        return [
            {
                "id": m.id,
                "content": m.content,
                "importance": m.importance,
                "created_at": m.created_at
            }
            for m in memories
        ]
    
    async def get_active_sessions(self) -> List[Dict]:
        """获取活跃Session列表"""
        return await self.db.get_active_sessions(self.agent_id)
    
    async def track_emotional_state(
        self,
        session_id: str,
        emotion: str,
        intensity: float,
        triggers: List[str] = None
    ) -> Dict:
        """跟踪情感状态"""
        if not self.emotional_engine:
            return {}
        
        return await self.emotional_engine.track_emotional_state(
            session_id=session_id,
            agent_id=self.agent_id,
            user_id=self.user_id,
            emotion=emotion,
            intensity=intensity,
            triggers=triggers or []
        )
    
    async def get_emotional_context(self, session_id: str) -> Dict:
        """获取情感上下文"""
        if not self.emotional_engine:
            return {}
        
        return await self.emotional_engine.get_emotional_context(
            session_id=session_id,
            agent_id=self.agent_id,
            user_id=self.user_id
        )
    
    async def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            "total_memories": await self.db.count_memories(agent_id=self.agent_id),
            "cache_pool": self.cache_pool.get_stats() if self.cache_pool else {},
            "current_session": self._current_session_id
        }
        
        return stats
    
    async def dream_memory(self, **kwargs) -> None:
        """梦境记忆优化（未实现）"""
        logger.info("dream_memory called - not implemented")
        pass

    async def compact_tool_result(self, **kwargs) -> None:
        """Compact tool results by truncating large outputs."""
        logger.info("compact_tool_result called - not implemented")
        pass

    def get_in_memory_memory(self, **kwargs) -> "ContextLoadingInMemory":
        """Retrieve the in-memory memory object for the agent.
        
        Returns ContextLoadingInMemory which injects historical memories
        from read cache into the conversation context.
        """
        if self._in_memory_memory is None:
            self._in_memory_memory = ContextLoadingInMemory()
            self._in_memory_memory._memory_manager_ref = self
            logger.info("Created ContextLoadingInMemory with cache injection")
        return self._in_memory_memory

    async def post_memory_operation(
        self,
        agent_id: str,
        operation_type: str,
        status: str,
        **kwargs
    ):
        """记忆操作后钩子"""
        pass
