# -*- coding: utf-8 -*-
"""HumanThinking Memory Manager - Database Layer

会话隔离版数据库操作，支持 Agent + User + Session 三级隔离
"""

import asyncio
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class MemoryRecord:
    """记忆记录"""
    id: int
    agent_id: str
    session_id: str
    user_id: Optional[str]
    target_id: Optional[str]  # 对话对象标识（区分不同 Agent/用户）
    role: str
    content: str
    importance: int
    memory_type: str
    metadata: Dict[str, Any]
    created_at: str
    session_key: Optional[str] = None
    content_embedding: Optional[str] = None
    content_summary: Optional[str] = None
    importance_score: float = 0.0
    access_count: int = 0
    search_count: int = 0
    search_score: float = 0.0
    access_frozen: int = 0
    frozen_at: Optional[str] = None
    last_accessed_at: Optional[str] = None
    last_searched_at: Optional[str] = None
    updated_at: Optional[str] = None
    deleted_at: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class HumanThinkingDB:
    """HumanThinking 数据库操作层（会话隔离）"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """初始化数据库"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False
        )
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        
        # 启用 WAL 模式
        self.cursor.execute("PRAGMA journal_mode=WAL")
        self.cursor.execute("PRAGMA synchronous=NORMAL")
        self.cursor.execute("PRAGMA cache_size=10000")
        self.conn.commit()
        
        await self._create_tables()
        await self._create_indexes()
        await self._init_version()
        
        logger.info(f"HumanThinkingDB initialized: {self.db_path}")
    
    async def close(self) -> None:
        """关闭数据库"""
        if self.conn:
            self.conn.close()
            logger.info("HumanThinkingDB closed")
    
    async def _create_tables(self) -> None:
        """创建表结构"""
        self.cursor.executescript("""
            -- 1. 版本管理表
            CREATE TABLE IF NOT EXISTS qwenpaw_memory_version (
                id INTEGER PRIMARY KEY,
                db_version TEXT NOT NULL,
                schema_version TEXT NOT NULL,
                min_compatible_version TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                upgrade_history TEXT DEFAULT '[]'
            );
            
            -- 2. 记忆主表（会话隔离 + 对话对象隔离版）
            CREATE TABLE IF NOT EXISTS qwenpaw_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- 核心隔离字段
                agent_id TEXT NOT NULL,           -- 当前Agent
                session_id TEXT NOT NULL,         -- 会话ID
                user_id TEXT,                     -- 发起者ID
                target_id TEXT,                   -- 对话对象ID（区分不同Agent/用户）
                role TEXT DEFAULT 'assistant',
                session_key TEXT,
                
                -- 内容字段
                content TEXT NOT NULL,
                content_embedding TEXT,
                content_summary TEXT,
                
                -- 重要性
                importance INTEGER DEFAULT 3,
                importance_score REAL DEFAULT 0.0,
                
                -- 访问统计
                access_count INTEGER DEFAULT 0,
                search_count INTEGER DEFAULT 0,
                search_score REAL DEFAULT 0.0,
                
                -- 冷藏状态
                access_frozen INTEGER DEFAULT 0,
                frozen_at DATETIME,
                
                -- 时间字段
                last_accessed_at DATETIME,
                last_searched_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                deleted_at DATETIME,
                
                -- 关联字段
                memory_type TEXT DEFAULT 'general',
                metadata TEXT DEFAULT '{}',
                tags TEXT DEFAULT '[]'
            );
            
            -- 3. 记忆关联表
            CREATE TABLE IF NOT EXISTS qwenpaw_memory_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id1 INTEGER NOT NULL,
                memory_id2 INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                similarity_score REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(memory_id1, memory_id2)
            );
            
            -- 4. Session关系表
            CREATE TABLE IF NOT EXISTS session_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_session TEXT NOT NULL,
                target_session TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                relationship_type TEXT NOT NULL,
                strength REAL DEFAULT 0.5,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_session, target_session, relationship_type)
            );
            
            -- 5. 情感连续性表
            CREATE TABLE IF NOT EXISTS session_emotional_continuity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                user_id TEXT,
                emotional_state TEXT NOT NULL,
                continuity_from_previous REAL DEFAULT 0.0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()
    
    async def _create_indexes(self) -> None:
        """创建索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_memory_agent ON qwenpaw_memory(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_session ON qwenpaw_memory(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_user ON qwenpaw_memory(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_target ON qwenpaw_memory(target_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_role ON qwenpaw_memory(role)",
            "CREATE INDEX IF NOT EXISTS idx_memory_agent_session ON qwenpaw_memory(agent_id, session_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_agent_target ON qwenpaw_memory(agent_id, target_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_full_context ON qwenpaw_memory(agent_id, target_id, user_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_importance ON qwenpaw_memory(importance DESC)",
            "CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON qwenpaw_memory(created_at DESC)",
        ]
        for idx in indexes:
            self.cursor.execute(idx)
        self.conn.commit()
    
    async def _init_version(self) -> None:
        """初始化版本"""
        self.cursor.execute("SELECT COUNT(*) FROM qwenpaw_memory_version")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("""
                INSERT INTO qwenpaw_memory_version 
                (db_version, schema_version, min_compatible_version)
                VALUES ('1.0.0', '1.0.0', '1.0.0')
            """)
            self.conn.commit()
    
    async def add_memory(
        self,
        agent_id: str,
        session_id: str,
        content: str,
        user_id: Optional[str] = None,
        target_id: Optional[str] = None,
        role: str = "assistant",
        importance: int = 3,
        memory_type: str = "general",
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> int:
        """
        添加记忆（会话隔离 + 对话对象隔离）
        
        Args:
            agent_id: 当前Agent
            session_id: 会话ID
            content: 记忆内容
            user_id: 发起者ID
            target_id: 对话对象ID（区分不同Agent/用户）
            role: 角色
            importance: 重要性
            memory_type: 记忆类型
            metadata: 元数据
            tags: 标签
        
        Returns:
            memory_id
        """
        import json
        
        # session_key 包含 target_id，确保不同对话对象的记忆隔离
        session_key = f"{agent_id}_{target_id or user_id}_{session_id}"
        
        self.cursor.execute("""
            INSERT INTO qwenpaw_memory 
            (agent_id, session_id, user_id, target_id, role, session_key, content, 
             importance, memory_type, metadata, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            agent_id, session_id, user_id, target_id, role, session_key, content,
            importance, memory_type, 
            json.dumps(metadata or {}),
            json.dumps(tags or [])
        ))
        self.conn.commit()
        
        memory_id = self.cursor.lastrowid
        logger.debug(f"Added memory {memory_id}: agent={agent_id}, target={target_id}, session={session_id}")
        return memory_id
    
    async def batch_insert(self, memories: List[Dict[str, Any]], sync: bool = True) -> int:
        """
        批量插入记忆
        
        Args:
            memories: 记忆列表
            sync: 是否同步
        
        Returns:
            插入数量
        """
        import json
        
        if not memories:
            return 0
        
        data = [
            (
                m.get("agent_id"),
                m.get("session_id"),
                m.get("user_id"),
                m.get("target_id"),
                m.get("role", "assistant"),
                f"{m.get('agent_id')}_{m.get('target_id') or m.get('user_id')}_{m.get('session_id')}",
                m.get("content"),
                m.get("importance", 3),
                m.get("memory_type", "general"),
                json.dumps(m.get("metadata", {})),
                json.dumps(m.get("tags", []))
            )
            for m in memories
        ]
        
        self.cursor.executemany("""
            INSERT INTO qwenpaw_memory 
            (agent_id, session_id, user_id, target_id, role, session_key, content, 
             importance, memory_type, metadata, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        
        if sync:
            self.conn.commit()
        
        logger.info(f"Batch inserted {len(data)} memories")
        return len(data)
    
    async def search_memories(
        self,
        query: str,
        agent_id: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        target_id: Optional[str] = None,
        role: Optional[str] = None,
        cross_session: bool = True,
        max_results: int = 5,
        min_score: float = 0.1,
        exclude_recent_rounds: int = 0,
        round_duration_seconds: int = 300
    ) -> List[MemoryRecord]:
        """
        搜索记忆（会话隔离 + 对话对象隔离）
        
        Args:
            query: 查询内容
            agent_id: Agent ID
            session_id: 会话ID
            user_id: 用户ID
            target_id: 对话对象ID（隔离不同Agent的对话）
            role: 角色
            cross_session: 是否跨Session
            max_results: 最大结果数
            min_score: 最小分数
            exclude_recent_rounds: 排除最近N轮对话的记忆（防止与压缩摘要重复）
            round_duration_seconds: 每次对话轮次的时长（秒），默认300秒
        
        Returns:
            MemoryRecord 列表
        """
        # 基础查询
        sql = "SELECT * FROM qwenpaw_memory WHERE agent_id = ? AND deleted_at IS NULL"
        params = [agent_id]
        
        # Target 过滤（对话对象隔离）
        if target_id:
            sql += " AND target_id = ?"
            params.append(target_id)
        
        # Session 过滤
        if cross_session:
            # 跨 session 时，不添加 session_id 过滤
            pass
        elif session_id:
            sql += " AND session_id = ?"
            params.append(session_id)
        
        # User 过滤
        if user_id:
            sql += " AND user_id = ?"
            params.append(user_id)
        
        # Role 过滤
        if role:
            sql += " AND role = ?"
            params.append(role)
        
        # 内容搜索（LIKE）
        sql += " AND content LIKE ?"
        params.append(f"%{query}%")
        
        # 排除最近N轮对话的记忆（防止与QwenPaw压缩摘要重复）
        if exclude_recent_rounds > 0:
            exclude_seconds = exclude_recent_rounds * round_duration_seconds
            sql += f" AND created_at < datetime('now', '-{exclude_seconds} seconds')"
        
        # 排序
        sql += " ORDER BY importance DESC, created_at DESC"
        sql += " LIMIT ?"
        params.append(max_results)
        
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()
        
        return [self._row_to_record(row) for row in rows]
    
    async def get_session_memories(
        self,
        agent_id: str,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[MemoryRecord]:
        """获取 Session 的所有记忆"""
        self.cursor.execute("""
            SELECT * FROM qwenpaw_memory 
            WHERE agent_id = ? AND session_id = ? AND deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (agent_id, session_id, limit, offset))
        
        rows = self.cursor.fetchall()
        return [self._row_to_record(row) for row in rows]
    
    async def get_active_sessions(self, agent_id: str) -> List[Dict[str, Any]]:
        """获取 Agent 的所有活跃 Session"""
        self.cursor.execute("""
            SELECT 
                session_id,
                COUNT(*) as memory_count,
                MAX(created_at) as last_activity
            FROM qwenpaw_memory
            WHERE agent_id = ? AND deleted_at IS NULL
            GROUP BY session_id
            ORDER BY last_activity DESC
        """, (agent_id,))
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    async def update_memory_access(self, memory_id: int) -> None:
        """更新记忆访问统计"""
        import datetime
        
        now = datetime.datetime.now().isoformat()
        
        self.cursor.execute("""
            UPDATE qwenpaw_memory 
            SET access_count = access_count + 1, last_accessed_at = ?
            WHERE id = ?
        """, (now, memory_id))
        self.conn.commit()
    
    async def count_memories(
        self,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        since: Optional[str] = None
    ) -> int:
        """统计记忆数量"""
        sql = "SELECT COUNT(*) FROM qwenpaw_memory WHERE deleted_at IS NULL"
        params = []
        
        if agent_id:
            sql += " AND agent_id = ?"
            params.append(agent_id)
        
        if session_id:
            sql += " AND session_id = ?"
            params.append(session_id)
        
        if since:
            sql += " AND created_at > ?"
            params.append(since)
        
        self.cursor.execute(sql, params)
        return self.cursor.fetchone()[0]
    
    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        """转换数据库行为 MemoryRecord"""
        import json
        
        return MemoryRecord(
            id=row["id"],
            agent_id=row["agent_id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            target_id=row.get("target_id"),
            role=row["role"],
            content=row["content"],
            importance=row["importance"],
            memory_type=row["memory_type"],
            metadata=json.loads(row["metadata"]),
            created_at=row["created_at"],
            session_key=row["session_key"],
            content_embedding=row["content_embedding"],
            content_summary=row["content_summary"],
            importance_score=row["importance_score"],
            access_count=row["access_count"],
            search_count=row["search_count"],
            search_score=row["search_score"],
            access_frozen=row["access_frozen"],
            frozen_at=row["frozen_at"],
            last_accessed_at=row["last_accessed_at"],
            last_searched_at=row["last_searched_at"],
            updated_at=row["updated_at"],
            deleted_at=row["deleted_at"],
            tags=json.loads(row["tags"])
        )

    async def create_memory_relation(
        self,
        memory_id1: int,
        memory_id2: int,
        relation_type: str,
        similarity_score: float = 0.0
    ) -> int:
        """
        创建记忆关联
        
        Args:
            memory_id1: 记忆1 ID
            memory_id2: 记忆2 ID
            relation_type: 关联类型 (related, causes, contradicts, supports)
            similarity_score: 相似度分数
        
        Returns:
            relation_id
        """
        try:
            self.cursor.execute("""
                INSERT INTO qwenpaw_memory_relations 
                (memory_id1, memory_id2, relation_type, similarity_score)
                VALUES (?, ?, ?, ?)
            """, (memory_id1, memory_id2, relation_type, similarity_score))
            self.conn.commit()
            relation_id = self.cursor.lastrowid
            logger.debug(f"Created relation {relation_id}: {memory_id1} -[{relation_type}]-> {memory_id2}")
            return relation_id
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                logger.debug(f"Relation already exists: {memory_id1} -[{relation_type}]-> {memory_id2}")
                return -1
            raise

    async def get_related_memories(
        self,
        memory_id: int,
        max_results: int = 10,
        relation_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        获取相关记忆
        
        Args:
            memory_id: 记忆 ID
            max_results: 最大结果数
            relation_types: 关联类型过滤
        
        Returns:
            相关记忆列表
        """
        sql = """
            SELECT m.*, r.relation_type, r.similarity_score
            FROM qwenpaw_memory_relations r
            JOIN qwenpaw_memory m ON (
                (r.memory_id1 = ? AND m.id = r.memory_id2) OR
                (r.memory_id2 = ? AND m.id = r.memory_id1)
            )
            WHERE m.deleted_at IS NULL
        """
        params = [memory_id, memory_id]
        
        if relation_types:
            placeholders = ",".join(["?" for _ in relation_types])
            sql += f" AND r.relation_type IN ({placeholders})"
            params.extend(relation_types)
        
        sql += " ORDER BY r.similarity_score DESC LIMIT ?"
        params.append(max_results)
        
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()
        
        return [dict(row) for row in rows]

    async def delete_memory_relation(
        self,
        memory_id1: int,
        memory_id2: int,
        relation_type: str
    ) -> bool:
        """删除记忆关联"""
        self.cursor.execute("""
            DELETE FROM qwenpaw_memory_relations 
            WHERE memory_id1 = ? AND memory_id2 = ? AND relation_type = ?
        """, (memory_id1, memory_id2, relation_type))
        self.conn.commit()
        return self.cursor.rowcount > 0

    async def freeze_memories(
        self,
        agent_id: str,
        days: int = 30,
        importance_threshold: int = 3
    ) -> int:
        """
        冷藏旧记忆
        
        Args:
            agent_id: Agent ID
            days: 天数阈值
            importance_threshold: 重要性阈值
        
        Returns:
            冷藏数量
        """
        import datetime
        
        cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        
        self.cursor.execute("""
            UPDATE qwenpaw_memory 
            SET access_frozen = 1, frozen_at = CURRENT_TIMESTAMP
            WHERE agent_id = ? 
              AND deleted_at IS NULL
              AND access_frozen = 0
              AND created_at < ?
              AND importance < ?
        """, (agent_id, cutoff_date, importance_threshold))
        self.conn.commit()
        
        frozen_count = self.cursor.rowcount
        logger.info(f"Frozen {frozen_count} memories for agent={agent_id}")
        return frozen_count

    async def defrost_memories(
        self,
        agent_id: str,
        query: Optional[str] = None,
        limit: int = 50
    ) -> int:
        """
        解冻相关记忆
        
        Args:
            agent_id: Agent ID
            query: 查询关键词（可选）
            limit: 解冻数量限制
        
        Returns:
            解冻数量
        """
        sql = """
            UPDATE qwenpaw_memory 
            SET access_frozen = 0, frozen_at = NULL
            WHERE agent_id = ? AND access_frozen = 1 AND deleted_at IS NULL
        """
        params = [agent_id]
        
        if query:
            sql += " AND content LIKE ?"
            params.append(f"%{query}%")
        
        sql += " LIMIT ?"
        params.append(limit)
        
        self.cursor.execute(sql, params)
        self.conn.commit()
        
        defrosted_count = self.cursor.rowcount
        logger.info(f"Defrosted {defrosted_count} memories for agent={agent_id}")
        return defrosted_count

    async def get_frozen_memories(
        self,
        agent_id: str,
        target_id: Optional[str] = None,
        limit: int = 50
    ) -> List[MemoryRecord]:
        """获取冷藏记忆"""
        sql = """
            SELECT * FROM qwenpaw_memory 
            WHERE agent_id = ? AND access_frozen = 1 AND deleted_at IS NULL
        """
        params = [agent_id]
        
        if target_id:
            sql += " AND target_id = ?"
            params.append(target_id)
        
        sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
        params.append(limit)
        
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()
        return [self._row_to_record(row) for row in rows]

    async def get_active_memories(
        self,
        agent_id: str,
        target_id: Optional[str] = None,
        limit: int = 100,
        order_by: str = "importance"
    ) -> List[MemoryRecord]:
        """获取活跃记忆（未冷藏）"""
        sql = """
            SELECT * FROM qwenpaw_memory 
            WHERE agent_id = ? AND access_frozen = 0 AND deleted_at IS NULL
        """
        params = [agent_id]
        
        if target_id:
            sql += " AND target_id = ?"
            params.append(target_id)
        
        # 排序
        if order_by == "importance":
            sql += " ORDER BY importance DESC, created_at DESC"
        elif order_by == "access_count":
            sql += " ORDER BY access_count DESC, created_at DESC"
        else:
            sql += " ORDER BY created_at DESC"
        
        sql += " LIMIT ?"
        params.append(limit)
        
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()
        return [self._row_to_record(row) for row in rows]

    async def get_stats(self, agent_id: str) -> Dict[str, Any]:
        """
        获取记忆统计信息
        
        Args:
            agent_id: Agent ID
        
        Returns:
            统计信息
        """
        stats = {}
        
        # 总记忆数
        self.cursor.execute(
            "SELECT COUNT(*) FROM qwenpaw_memory WHERE agent_id = ? AND deleted_at IS NULL",
            (agent_id,)
        )
        stats["total_memories"] = self.cursor.fetchone()[0]
        
        # 冷藏记忆数
        self.cursor.execute(
            "SELECT COUNT(*) FROM qwenpaw_memory WHERE agent_id = ? AND access_frozen = 1 AND deleted_at IS NULL",
            (agent_id,)
        )
        stats["frozen_memories"] = self.cursor.fetchone()[0]
        
        # 活跃记忆数
        stats["active_memories"] = stats["total_memories"] - stats["frozen_memories"]
        
        # 重要性分布
        self.cursor.execute("""
            SELECT importance, COUNT(*) as count 
            FROM qwenpaw_memory 
            WHERE agent_id = ? AND deleted_at IS NULL
            GROUP BY importance
            ORDER BY importance
        """, (agent_id,))
        stats["importance_stats"] = {
            str(row["importance"]): row["count"] 
            for row in self.cursor.fetchall()
        }
        
        # Session 统计
        self.cursor.execute("""
            SELECT COUNT(DISTINCT session_id) as total_sessions
            FROM qwenpaw_memory
            WHERE agent_id = ? AND deleted_at IS NULL
        """, (agent_id,))
        stats["total_sessions"] = self.cursor.fetchone()[0]
        
        return stats
