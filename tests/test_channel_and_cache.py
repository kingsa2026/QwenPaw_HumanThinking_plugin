# -*- coding: utf-8 -*-
"""
渠道适配器和缓存池单元测试

测试覆盖：
- 渠道上下文提取
- 记忆键生成
- 各渠道适配器
- AgentCachePool
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from HumanThinking.core.channel_adapter import (
    ChannelAdapter,
    ChannelContext,
    ChannelType,
    FeishuAdapter,
    WeixinAdapter,
    QQAdapter,
    DingTalkAdapter,
    TelegramAdapter,
    DiscordAdapter,
    get_adapter,
    extract_channel_context,
    build_memory_key,
    parse_memory_key
)
from HumanThinking.core.cache_pool import AgentCachePool, SessionCache


class TestChannelContext:
    """ChannelContext 测试"""

    def test_create_context(self):
        """创建上下文"""
        ctx = ChannelContext(
            channel_id="feishu",
            user_id="user_1",
            session_id="session_1",
            target_id="user_1"
        )
        assert ctx.channel_id == "feishu"
        assert ctx.user_id == "user_1"
        assert ctx.target_id == "user_1"

    def test_to_dict_and_from_dict(self):
        """字典转换"""
        ctx = ChannelContext(
            channel_id="feishu",
            user_id="user_1",
            session_id="session_1",
            target_id="user_1",
            is_group=True,
            group_id="group_1"
        )
        
        data = ctx.to_dict()
        restored = ChannelContext.from_dict(data)
        
        assert restored.channel_id == ctx.channel_id
        assert restored.target_id == ctx.target_id
        assert restored.is_group == ctx.is_group


class TestMemoryKey:
    """记忆键测试"""

    def test_build_memory_key(self):
        """构建记忆键"""
        key = build_memory_key(
            agent_id="AgentB",
            target_id="user_U",
            user_id="user_U"
        )
        assert key == "AgentB:user_U:user_U"

    def test_parse_memory_key(self):
        """解析记忆键"""
        key = "AgentB:user_U:user_U"
        parsed = parse_memory_key(key)
        
        assert parsed["agent_id"] == "AgentB"
        assert parsed["target_id"] == "user_U"
        assert parsed["user_id"] == "user_U"

    def test_cross_channel_memory_sharing(self):
        """跨渠道记忆共享（记忆键不包含 channel_id）"""
        key_feishu = build_memory_key("AgentB", "user_U", "user_U")
        key_wechat = build_memory_key("AgentB", "user_U", "user_U")
        
        # 相同用户应该生成相同的记忆键
        assert key_feishu == key_wechat


class TestFeishuAdapter:
    """飞书适配器测试"""

    def test_extract_user_id(self):
        """提取用户ID"""
        payload = {
            "user_id": "ou_xxx",
            "sender_id": "张三#1234"
        }
        meta = {"feishu_sender_id": "ou_real_id"}
        
        user_id = FeishuAdapter.extract_user_id(payload, meta)
        assert user_id == "ou_real_id"

    def test_extract_target_id_group(self):
        """群聊提取 target_id"""
        payload = {"user_id": "ou_xxx"}
        meta = {
            "feishu_chat_type": "group",
            "feishu_chat_id": "oc_xxx"
        }
        
        target_id = FeishuAdapter.extract_target_id(payload, meta)
        assert target_id == "oc_xxx"

    def test_extract_target_id_p2p(self):
        """单聊提取 target_id"""
        payload = {"user_id": "ou_xxx"}
        meta = {"feishu_chat_type": "p2p"}
        
        target_id = FeishuAdapter.extract_target_id(payload, meta)
        assert target_id == "ou_xxx"


class TestQQAdapter:
    """QQ适配器测试"""

    def test_group_message(self):
        """群聊消息"""
        payload = {"user_id": "user_1"}
        meta = {
            "qq_message_type": "group",
            "group_openid": "group_123"
        }
        
        target_id = QQAdapter.extract_target_id(payload, meta)
        session_id = QQAdapter.extract_session_id(payload, meta, "qq")
        
        assert target_id == "group_123"
        assert session_id == "qq:group:group_123"

    def test_guild_message(self):
        """频道消息"""
        payload = {"user_id": "user_1"}
        meta = {
            "qq_message_type": "guild",
            "channel_id": "channel_123",
            "guild_id": "guild_456"
        }
        
        target_id = QQAdapter.extract_target_id(payload, meta)
        session_id = QQAdapter.extract_session_id(payload, meta, "qq")
        
        assert target_id == "channel_123"
        assert session_id == "qq:guild:channel_123"


class TestGetAdapter:
    """适配器注册表测试"""

    def test_get_feishu_adapter(self):
        """获取飞书适配器"""
        adapter = get_adapter("feishu")
        assert adapter == FeishuAdapter

    def test_get_weixin_adapter(self):
        """获取微信适配器"""
        adapter = get_adapter("wechat")
        assert adapter == WeixinAdapter

    def test_get_unknown_adapter(self):
        """未知渠道返回默认适配器"""
        adapter = get_adapter("unknown")
        assert adapter == ChannelAdapter


class TestExtractChannelContext:
    """提取渠道上下文测试"""

    def test_extract_feishu_context(self):
        """提取飞书上下文"""
        payload = {
            "channel_id": "feishu",
            "user_id": "ou_xxx",
            "meta": {
                "feishu_sender_id": "ou_xxx",
                "feishu_chat_id": "oc_xxx",
                "feishu_chat_type": "group"
            }
        }
        
        ctx = extract_channel_context(payload)
        assert ctx.channel_id == "feishu"
        assert ctx.target_id == "oc_xxx"
        assert ctx.is_group is True


class TestAgentCachePool:
    """AgentCachePool 测试"""

    @pytest.mark.asyncio
    async def test_store_memory(self):
        """存储记忆到缓存"""
        pool = AgentCachePool("agent_1")
        
        await pool.store({"key": "mem_1", "content": "测试"}, "session_1")
        
        memories = await pool.retrieve("session_1")
        assert len(memories) == 1

    @pytest.mark.asyncio
    async def test_multi_session_concurrency(self):
        """多Session并发"""
        pool = AgentCachePool("agent_1")
        
        # 同时向不同Session写入
        await asyncio.gather(
            pool.store({"key": "mem_1", "content": "session1"}, "session_1"),
            pool.store({"key": "mem_2", "content": "session2"}, "session_2"),
        )
        
        mem1 = await pool.retrieve("session_1")
        mem2 = await pool.retrieve("session_2")
        
        assert len(mem1) == 1
        assert len(mem2) == 1
        assert mem1[0]["content"] != mem2[0]["content"]

    @pytest.mark.asyncio
    async def test_capacity_limit(self):
        """缓存容量限制"""
        pool = AgentCachePool("agent_1", max_memories=3)
        
        for i in range(5):
            await pool.store({"key": f"mem_{i}", "content": f"content_{i}"}, "session_1")
        
        memories = await pool.retrieve("session_1")
        # 应该只保留最新的 3 条
        assert len(memories) <= 3

    @pytest.mark.asyncio
    async def test_flush_to_db(self):
        """刷新到数据库"""
        pool = AgentCachePool("agent_1")
        await pool.store({"key": "mem_1", "content": "测试"}, "session_1")
        
        await pool.flush_to_db("session_1")
        
        write_queue = await pool._write_queue.get_all()
        assert len(write_queue) == 0


class TestSessionCache:
    """SessionCache 测试"""

    @pytest.mark.asyncio
    async def test_session_isolation(self):
        """Session隔离"""
        pool = AgentCachePool("agent_1")
        
        await pool.store({"key": "mem_1"}, "session_1")
        await pool.store({"key": "mem_2"}, "session_2")
        
        mem1 = await pool.retrieve("session_1")
        mem2 = await pool.retrieve("session_2")
        
        assert mem1[0]["key"] != mem2[0]["key"]

    @pytest.mark.asyncio
    async def test_eviction(self):
        """缓存淘汰"""
        pool = AgentCachePool("agent_1", max_memories=2)
        
        await pool.store({"key": "mem_1"}, "session_1")
        await pool.store({"key": "mem_2"}, "session_1")
        await pool.store({"key": "mem_3"}, "session_1")
        
        memories = await pool.retrieve("session_1")
        assert len(memories) <= 2
