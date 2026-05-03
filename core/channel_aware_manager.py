# -*- coding: utf-8 -*-
"""
渠道感知记忆管理器：集成渠道适配器的记忆管理封装

这个模块将 HumanThinking 记忆管理器与 QwenPaw 的各个消息渠道集成，
确保记忆能在不同渠道下正确隔离、检索和桥接。

主要功能：
1. 自动识别渠道类型并提取用户/会话信息
2. 按渠道隔离记忆（Agent + Channel + User + Session）
3. 跨渠道记忆桥接（可选）
4. 情感状态按渠道维护
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List

from .database import HumanThinkingDB
from .cache_pool import AgentCachePool
from .session_bridge import SessionBridgeEngine
from .emotional_engine import EmotionalContinuityEngine
from .channel_adapter import (
    ChannelAdapter,
    ChannelContext,
    ChannelType,
    get_adapter,
    extract_channel_context,
    build_memory_key,
)

logger = logging.getLogger(__name__)


class ChannelAwareMemoryManager:
    """
    渠道感知记忆管理器

    封装 HumanThinking 核心记忆模块，为每个渠道提供独立的记忆上下文，
    同时支持跨渠道记忆桥接。
    """

    def __init__(
        self,
        db_path: str,
        agent_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        enable_cross_channel_bridge: bool = False,
    ):
        """
        初始化渠道感知记忆管理器

        Args:
            db_path: 数据库路径
            agent_id: Agent 标识
            user_id: 用户标识（可选，创建时会覆盖）
            session_id: 会话标识（可选，创建时会覆盖）
            enable_cross_channel_bridge: 是否启用跨渠道记忆桥接
        """
        self.db = HumanThinkingDB(db_path)
        self.agent_id = agent_id
        self.current_user_id = user_id or ""
        self.current_session_id = session_id or ""
        self.enable_cross_channel_bridge = enable_cross_channel_bridge

        # 缓存池：按 agent_id 隔离
        self.cache_pool = AgentCachePool(agent_id=agent_id, db=self.db)

        # 会话桥接：负责新 Session 的记忆继承
        self.session_bridge = SessionBridgeEngine(self.db)

        # 情感引擎：跨 Session 情感连续性
        self.emotional_engine = EmotionalContinuityEngine(self.db)

        # 渠道上下文缓存：每个渠道独立上下文
        self._channel_contexts: Dict[str, ChannelContext] = {}

    async def process_channel_message(
        self,
        channel_payload: Dict[str, Any],
        channel_id: Optional[str] = None,
    ) -> ChannelContext:
        """
        处理渠道消息：提取上下文、加载历史记忆、准备记忆上下文

        Args:
            channel_payload: 渠道原始消息负载
            channel_id: 渠道ID（如果 payload 中没有）

        Returns:
            ChannelContext: 提取并准备好的渠道上下文
        """
        # 1. 提取渠道上下文
        context = extract_channel_context(channel_payload, channel_id)
        cid = context.channel_id

        # 2. 缓存上下文
        self._channel_contexts[cid] = context

        # 3. 加载或创建用户记忆
        await self._load_or_create_user_memory(context)

        # 4. 检查是否需要会话桥接（新 Session）
        if context.session_id != self.current_session_id:
            await self._handle_session_transition(context)

        # 5. 记录渠道活动
        await self.db.record_channel_activity(
            agent_id=self.agent_id,
            user_id=context.user_id,
            session_id=context.session_id,
            channel_id=cid,
            activity_type="message_received",
        )

        return context

    async def store_memory(
        self,
        context: ChannelContext,
        memory_content: str,
        memory_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        存储记忆

        Args:
            context: 渠道上下文
            memory_content: 记忆内容
            memory_type: 记忆类型（conversation, fact, emotion, etc.）
            metadata: 额外元数据

        Returns:
            memory_id: 记忆ID
        """
        # 构建记忆键
        memory_key = build_memory_key(
            agent_id=self.agent_id,
            target_id=context.user_id,
            user_id=context.user_id,
        )

        # 写入数据库
        memory_id = await self.db.insert_memory(
            memory_key=memory_key,
            content=memory_content,
            memory_type=memory_type,
            metadata=metadata or {},
        )

        # 写入缓存
        await self.cache_pool.store(
            memory={"key": memory_key, "content": memory_content},
            session_id=context.session_id,
        )

        logger.debug(
            "Memory stored: key=%s, type=%s",
            memory_key,
            memory_type,
        )

        return memory_id

    async def retrieve_memories(
        self,
        context: ChannelContext,
        query: Optional[str] = None,
        limit: int = 10,
        memory_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        检索记忆

        Args:
            context: 渠道上下文
            query: 查询关键词（可选）
            limit: 返回数量限制
            memory_types: 记忆类型过滤

        Returns:
            记忆列表
        """
        # 先从缓存获取
        cached = await self.cache_pool.retrieve(
            session_id=context.session_id,
            limit=limit,
        )

        if cached:
            return cached

        # 缓存未命中，查询数据库
        memories = await self.db.query_memories(
            agent_id=self.agent_id,
            user_id=context.user_id,
            session_id=context.session_id,
            channel_id=context.channel_id,
            query=query,
            limit=limit,
            memory_types=memory_types,
        )

        # 填充缓存
        for mem in memories:
            await self.cache_pool.store(mem, context.session_id)

        return memories

    async def track_emotion(
        self,
        context: ChannelContext,
        emotion: str,
        intensity: float = 1.0,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        跟踪情感状态

        Args:
            context: 渠道上下文
            emotion: 情感类型（happy, sad, excited, etc.）
            intensity: 情感强度（0.0 - 1.0）
            reason: 情感原因

        Returns:
            情感状态
        """
        return await self.emotional_engine.track_emotional_state(
            session_id=context.session_id,
            agent_id=self.agent_id,
            emotion=emotion,
            intensity=intensity,
            channel_id=context.channel_id,
        )

    async def get_emotional_state(
        self,
        context: ChannelContext,
    ) -> Dict[str, Any]:
        """
        获取当前情感状态

        Args:
            context: 渠道上下文

        Returns:
            情感状态
        """
        return await self.emotional_engine.get_emotional_state(
            session_id=context.session_id,
            agent_id=self.agent_id,
        )

    async def _load_or_create_user_memory(self, context: ChannelContext):
        """加载或创建用户记忆档案"""
        user_memory = await self.db.get_user_memory(
            agent_id=self.agent_id,
            user_id=context.user_id,
        )

        if not user_memory:
            await self.db.create_user_memory(
                agent_id=self.agent_id,
                user_id=context.user_id,
                channel_id=context.channel_id,
            )

    async def _handle_session_transition(self, context: ChannelContext):
        """处理会话转换（新 Session 或切换 Session）"""
        if context.session_id != self.current_session_id:
            logger.info(
                "Session transition: %s -> %s",
                self.current_session_id,
                context.session_id,
            )

            # 检查是否是新 Session（首次出现）
            is_new_session = await self.db.is_new_session(
                session_id=context.session_id,
                agent_id=self.agent_id,
            )

            if is_new_session and self.enable_cross_channel_bridge:
                # 执行会话桥接
                bridge_result = await self.session_bridge.bridge_new_session(
                    agent_id=self.agent_id,
                    user_id=context.user_id,
                    new_session_id=context.session_id,
                    trigger_context=context.to_dict(),
                )

                logger.info(
                    "Session bridged: inherited=%d memories",
                    len(bridge_result.get("inherited_memories", [])),
                )

            # 更新当前会话
            self.current_session_id = context.session_id
            self.current_user_id = context.user_id

    def get_channel_context(self, channel_id: str) -> Optional[ChannelContext]:
        """获取渠道上下文"""
        return self._channel_contexts.get(channel_id)

    async def flush_cache(self, channel_id: Optional[str] = None):
        """刷新缓存到数据库"""
        if channel_id:
            context = self._channel_contexts.get(channel_id)
            if context:
                await self.cache_pool.flush_to_db(
                    session_id=context.session_id,
                )
        else:
            # 刷新所有渠道缓存
            for cid, ctx in self._channel_contexts.items():
                await self.cache_pool.flush_to_db(
                    session_id=ctx.session_id,
                )

    async def close(self):
        """关闭管理器，刷新所有缓存"""
        await self.flush_cache()
        await self.db.close()
        logger.info("ChannelAwareMemoryManager closed")
