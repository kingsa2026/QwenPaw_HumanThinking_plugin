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
import datetime
import pytest


class TestDatabaseInitialization:
    """数据库初始化测试"""

    @pytest.mark.asyncio
    async def test_initialize_creates_tables(self, db):
        """初始化应该创建所有表"""
        db.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='qwenpaw_memory'"
        )
        assert db.cursor.fetchone() is not None

    @pytest.mark.asyncio
    async def test_initialize_creates_indexes(self, db):
        """初始化应该创建所有索引"""
        db.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index'"
        )
        indexes = [row[0] for row in db.cursor.fetchall()]
        assert "idx_memory_agent" in indexes
        assert "idx_memory_target" in indexes


class TestMemoryCRUD:
    """记忆增删改查测试"""

    @pytest.mark.asyncio
    async def test_add_memory(self, db):
        """添加记忆"""
        memory_id = await db.add_memory(
            agent_id="agent_1",
            session_id="session_1",
            content="测试记忆内容",
            user_id="user_1",
            target_id="user_1",
            importance=4,
            memory_type="episodic"
        )
        assert memory_id > 0

    @pytest.mark.asyncio
    async def test_add_memory_with_metadata(self, db):
        """添加带元数据的记忆"""
        metadata = {"key": "value", "tags": ["test"]}
        memory_id = await db.add_memory(
            agent_id="agent_1",
            session_id="session_1",
            content="带元数据的记忆",
            user_id="user_1",
            target_id="user_1",
            metadata=metadata
        )
        assert memory_id > 0

    @pytest.mark.asyncio
    async def test_batch_insert(self, db):
        """批量插入记忆"""
        memories = [
            {
                "agent_id": "agent_1",
                "session_id": "session_1",
                "user_id": "user_1",
                "target_id": "user_1",
                "content": f"批量记忆 {i}",
                "importance": 3
            }
            for i in range(10)
        ]
        count = await db.batch_insert(memories)
        assert count == 10

    @pytest.mark.asyncio
    async def test_search_memories(self, db):
        """搜索记忆"""
        await db.add_memory(
            agent_id="agent_1",
            session_id="session_1",
            content="电商团队目标讨论",
            user_id="user_1",
            target_id="user_1"
        )
        
        results = await db.search_memories(
            query="电商",
            agent_id="agent_1",
            target_id="user_1",
            max_results=5
        )
        assert len(results) > 0
        assert "电商" in results[0].content

    @pytest.mark.asyncio
    async def test_search_with_target_filter(self, db):
        """搜索时按 target_id 过滤"""
        await db.add_memory(
            agent_id="agent_1",
            session_id="session_1",
            content="与用户A的对话",
            user_id="user_a",
            target_id="user_a"
        )
        await db.add_memory(
            agent_id="agent_1",
            session_id="session_1",
            content="与用户B的对话",
            user_id="user_b",
            target_id="user_b"
        )
        
        results = await db.search_memories(
            query="对话",
            agent_id="agent_1",
            target_id="user_a"
        )
        assert all(r.target_id == "user_a" for r in results)


class TestTargetIsolation:
    """target_id 隔离测试"""

    @pytest.mark.asyncio
    async def test_agent_conversation_isolation(self, db):
        """Agent间对话隔离"""
        # AgentB 与 AgentA 对话
        await db.add_memory(
            agent_id="AgentB",
            session_id="session_1",
            content="AgentA 说：你好",
            user_id="AgentA",
            target_id="AgentA"
        )
        
        # AgentB 与 AgentC 对话
        await db.add_memory(
            agent_id="AgentB",
            session_id="session_1",
            content="AgentC 说：hello",
            user_id="AgentC",
            target_id="AgentC"
        )
        
        # 检索 AgentB 与 AgentA 的记忆
        results = await db.search_memories(
            query="你好",
            agent_id="AgentB",
            target_id="AgentA"
        )
        assert len(results) == 1
        assert results[0].target_id == "AgentA"

    @pytest.mark.asyncio
    async def test_cross_session_memory_sharing(self, db):
        """同一用户跨Session记忆共享"""
        # Session1
        await db.add_memory(
            agent_id="AgentB",
            session_id="session_001",
            content="用户问：今天天气如何？",
            user_id="user_U",
            target_id="user_U"
        )
        
        # Session2
        await db.add_memory(
            agent_id="AgentB",
            session_id="session_002",
            content="用户问：明天呢？",
            user_id="user_U",
            target_id="user_U"
        )
        
        # 跨Session搜索
        results = await db.search_memories(
            query="天气",
            agent_id="AgentB",
            target_id="user_U",
            cross_session=True
        )
        assert len(results) >= 1


class TestMemoryRelations:
    """记忆关联测试"""

    @pytest.mark.asyncio
    async def test_create_relation(self, db):
        """创建记忆关联"""
        id1 = await db.add_memory(
            agent_id="agent_1", session_id="s1",
            content="记忆1", user_id="u1", target_id="u1"
        )
        id2 = await db.add_memory(
            agent_id="agent_1", session_id="s1",
            content="记忆2", user_id="u1", target_id="u1"
        )
        
        relation_id = await db.create_memory_relation(
            memory_id1=id1,
            memory_id2=id2,
            relation_type="supports",
            similarity_score=0.85
        )
        assert relation_id > 0

    @pytest.mark.asyncio
    async def test_get_related_memories(self, db):
        """获取相关记忆"""
        id1 = await db.add_memory(
            agent_id="agent_1", session_id="s1",
            content="记忆1", user_id="u1", target_id="u1"
        )
        id2 = await db.add_memory(
            agent_id="agent_1", session_id="s1",
            content="记忆2", user_id="u1", target_id="u1"
        )
        
        await db.create_memory_relation(
            memory_id1=id1, memory_id2=id2,
            relation_type="related", similarity_score=0.9
        )
        
        related = await db.get_related_memories(id1)
        assert len(related) > 0
        assert related[0]["id"] == id2

    @pytest.mark.asyncio
    async def test_duplicate_relation_returns_negative(self, db):
        """重复关联返回 -1"""
        id1 = await db.add_memory(
            agent_id="agent_1", session_id="s1",
            content="记忆1", user_id="u1", target_id="u1"
        )
        id2 = await db.add_memory(
            agent_id="agent_1", session_id="s1",
            content="记忆2", user_id="u1", target_id="u1"
        )
        
        result1 = await db.create_memory_relation(id1, id2, "related")
        result2 = await db.create_memory_relation(id1, id2, "related")
        assert result2 == -1


class TestMemoryTemperature:
    """记忆温度测试"""

    @pytest.mark.asyncio
    async def test_freeze_memories(self, db):
        """冷藏旧记忆"""
        # 插入30天前的记忆
        old_date = (datetime.datetime.now() - datetime.timedelta(days=31)).isoformat()
        db.cursor.execute("""
            INSERT INTO qwenpaw_memory 
            (agent_id, session_id, user_id, target_id, role, session_key, content, importance, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ("agent_1", "s1", "u1", "u1", "assistant", "key", "旧记忆", 2, old_date))
        db.conn.commit()
        
        # 冷藏
        frozen_count = await db.freeze_memories("agent_1", days=30, importance_threshold=3)
        assert frozen_count >= 1

    @pytest.mark.asyncio
    async def test_defrost_memories(self, db):
        """解冻记忆"""
        id1 = await db.add_memory(
            agent_id="agent_1", session_id="s1",
            content="电商架构讨论", user_id="u1", target_id="u1"
        )
        
        # 先冷藏
        db.cursor.execute(
            "UPDATE qwenpaw_memory SET access_frozen = 1 WHERE id = ?", (id1,)
        )
        db.conn.commit()
        
        # 解冻
        defrosted = await db.defrost_memories("agent_1", query="电商")
        assert defrosted >= 1

    @pytest.mark.asyncio
    async def test_get_frozen_memories(self, db):
        """获取冷藏记忆"""
        id1 = await db.add_memory(
            agent_id="agent_1", session_id="s1",
            content="冷藏记忆", user_id="u1", target_id="u1"
        )
        
        db.cursor.execute(
            "UPDATE qwenpaw_memory SET access_frozen = 1 WHERE id = ?", (id1,)
        )
        db.conn.commit()
        
        frozen = await db.get_frozen_memories("agent_1")
        assert len(frozen) >= 1
        assert any(m.content == "冷藏记忆" for m in frozen)

    @pytest.mark.asyncio
    async def test_get_active_memories(self, db):
        """获取活跃记忆"""
        await db.add_memory(
            agent_id="agent_1", session_id="s1",
            content="活跃记忆", user_id="u1", target_id="u1"
        )
        
        active = await db.get_active_memories("agent_1")
        assert len(active) >= 1


class TestStats:
    """统计功能测试"""

    @pytest.mark.asyncio
    async def test_get_stats(self, db):
        """获取统计信息"""
        for i in range(5):
            await db.add_memory(
                agent_id="agent_1", session_id=f"s{i}",
                content=f"记忆{i}", user_id="u1", target_id="u1",
                importance=(i % 5) + 1
            )
        
        stats = await db.get_stats("agent_1")
        assert stats["total_memories"] == 5
        assert stats["active_memories"] == 5
        assert stats["total_sessions"] == 5
        assert "importance_stats" in stats
