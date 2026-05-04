# -*- coding: utf-8 -*-
"""HumanThinking Memory Manager - Database Layer

会话隔离版数据库操作，支持 Agent + User + Session 三级隔离
"""

import asyncio
import json
import logging
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

CURRENT_SCHEMA_VERSION = "1.1.0"


@dataclass
class MigrationStep:
    from_version: str
    to_version: str
    description: str
    sql_commands: str = ""              # 纯DDL（CREATE/ALTER），用分号分隔
    recreate_tables: Optional[Dict[str, str]] = None  # {旧表名: 重建的CREATE TABLE SQL}
    data_migration_sql: str = ""         # 数据迁移SQL（INSERT INTO ... SELECT）


MIGRATIONS: List[MigrationStep] = [
    MigrationStep(
        from_version="1.0.0",
        to_version="1.1.0",
        description="添加记忆合并和时间列",
        sql_commands="""
            ALTER TABLE qwenpaw_memory ADD COLUMN last_consolidated_at DATETIME;
            ALTER TABLE qwenpaw_memory ADD COLUMN merge_count INTEGER DEFAULT 0;
            ALTER TABLE qwenpaw_memory ADD COLUMN merged_from TEXT DEFAULT '[]';
            ALTER TABLE qwenpaw_memory ADD COLUMN last_merged_at DATETIME;
            ALTER TABLE qwenpaw_memory ADD COLUMN merge_similarity REAL DEFAULT 0.0;
        """
    ),
]


@dataclass
class MemoryRecord:
    """记忆记录"""
    id: int
    agent_id: str
    session_id: str
    user_id: Optional[str]
    target_id: Optional[str]
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
    memory_tier: str = "short_term"
    memory_category: str = "episodic"
    decay_score: float = 1.0
    decay_curve: str = "standard"
    archived_at: Optional[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class HumanThinkingDB:
    """HumanThinking 数据库操作层（会话隔离）"""
    
    def __init__(self, db_path: str, enable_distributed: bool = False, size_threshold_mb: int = 800):
        self.db_path = Path(db_path)
        self.enable_distributed = enable_distributed
        self.size_threshold_bytes = size_threshold_mb * 1024 * 1024
        self.conn: Optional[sqlite3.Connection] = None
        self.cursor: Optional[sqlite3.Cursor] = None
        self._lock = asyncio.Lock()
        self._shard_conns: Dict[int, sqlite3.Connection] = {}
        self._shard_index = 0
        
    def _get_shard_path(self, shard_index: int) -> Path:
        """获取分片数据库路径"""
        if shard_index == 0:
            return self.db_path
        stem = self.db_path.stem
        suffix = self.db_path.suffix
        return self.db_path.parent / f"{stem}_shard_{shard_index}{suffix}"
    
    def _init_shard_manager(self):
        """初始化分片管理器"""
        if not self.enable_distributed:
            return
        
        self._shard_index = 0
        
        # 扫描已存在的分片
        stem = self.db_path.stem
        suffix = self.db_path.suffix
        shard_dir = self.db_path.parent
        
        for f in shard_dir.glob(f"{stem}_shard_*{suffix}"):
            if f == self.db_path:
                continue
            try:
                shard_num = int(f.stem.split("_shard_")[-1])
                conn = sqlite3.connect(str(f), check_same_thread=False)
                self._shard_conns[shard_num] = conn
                self._shard_index = max(self._shard_index, shard_num)
            except (ValueError, sqlite3.Error) as e:
                logger.warning(f"Failed to load shard {f}: {e}")
        
        logger.info(f"Shard manager initialized: {len(self._shard_conns)} shards found")
    
    def _check_and_shard(self) -> int:
        """检查是否需要分片，返回当前应使用的分片索引"""
        if not self.enable_distributed:
            return 0
        
        main_db = self.db_path
        if not main_db.exists():
            return 0
        
        size = main_db.stat().st_size
        if size < self.size_threshold_bytes:
            return 0
        
        # 超过阈值，执行分片
        new_shard = self._shard_index + 1
        shard_path = self._get_shard_path(new_shard)
        
        # 将旧数据迁移到分片数据库
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # 获取要迁移的记忆（按时间排序，保留最近的数据）
        cursor.execute("""
            SELECT id FROM qwenpaw_memory 
            WHERE memory_tier IN ('frozen', 'archived')
            OR (memory_tier = 'short_term' AND last_accessed_at < datetime('now', '-30 days'))
            ORDER BY created_at ASC
            LIMIT 1000
        """)
        memory_ids = [row[0] for row in cursor.fetchall()]
        
        if not memory_ids:
            conn.close()
            return 0
        
        # 创建分片数据库
        import shutil
        shutil.copy2(main_db, shard_path)
        
        # 在分片数据库中只保留要迁移的数据
        shard_conn = sqlite3.connect(str(shard_path))
        shard_cursor = shard_conn.cursor()
        
        # 删除不需要的数据
        shard_cursor.execute(f"DELETE FROM qwenpaw_memory WHERE id NOT IN ({','.join('?' * len(memory_ids))})", memory_ids)
        
        # 在主数据库中标记这些记忆已被分片
        placeholders = ','.join('?' * len(memory_ids))
        cursor.execute(f"""
            INSERT OR REPLACE INTO qwenpaw_memory_shard_index (memory_id, shard_index, original_table)
            SELECT id, {new_shard}, 'qwenpaw_memory' 
            FROM qwenpaw_memory 
            WHERE id IN ({placeholders})
        """, memory_ids)
        
        # 从主数据库删除已分片的数据
        cursor.execute(f"DELETE FROM qwenpaw_memory WHERE id IN ({placeholders})", memory_ids)
        
        conn.commit()
        shard_conn.commit()
        
        conn.close()
        shard_conn.close()
        
        # 打开分片连接
        self._shard_conns[new_shard] = sqlite3.connect(str(shard_path), check_same_thread=False)
        self._shard_index = new_shard
        
        logger.info(f"Database sharded: migrated {len(memory_ids)} memories to shard {new_shard}")
        
        return new_shard
    
    async def _search_shards(
        self,
        query: str,
        agent_id: str,
        target_id: Optional[str] = None,
        user_id: Optional[str] = None,
        max_results: int = 5
    ) -> List[MemoryRecord]:
        """跨分片搜索记忆"""
        if not self._shard_conns:
            return []
        
        results = []
        
        # 1. 先从索引表查找匹配的记忆ID
        self.cursor.execute("""
            SELECT memory_id, shard_index, indexed_content 
            FROM qwenpaw_memory_shard_index 
            WHERE indexed_content LIKE ?
        """, (f"%{query}%",))
        
        index_matches = self.cursor.fetchall()
        
        # 按分片组织记忆ID
        shard_memories: Dict[int, List[int]] = {}
        for mem_id, shard_idx, indexed_content in index_matches:
            if shard_idx not in shard_memories:
                shard_memories[shard_idx] = []
            shard_memories[shard_idx].append(mem_id)
        
        # 2. 从各分片获取完整记忆
        for shard_idx, memory_ids in shard_memories.items():
            if shard_idx not in self._shard_conns:
                continue
            
            shard_conn = self._shard_conns[shard_idx]
            shard_cursor = shard_conn.cursor()
            
            placeholders = ','.join('?' * len(memory_ids))
            shard_cursor.execute(f"""
                SELECT * FROM qwenpaw_memory 
                WHERE id IN ({placeholders})
                AND agent_id = ?
            """, memory_ids + [agent_id])
            
            for row in shard_cursor.fetchall():
                memory = self._row_to_record(row)
                memory_dict = {
                    "id": memory.id,
                    "content": memory.content,
                    "importance": memory.importance,
                    "memory_type": memory.memory_type,
                    "created_at": memory.created_at,
                    "session_id": memory.session_id,
                    "agent_id": memory.agent_id,
                    "from_shard": shard_idx,
                }
                results.append(memory_dict)
                
                if memory.memory_tier == 'frozen':
                    shard_cursor.execute("""
                        UPDATE qwenpaw_memory 
                        SET memory_tier = 'short_term', access_frozen = 0, decay_score = 1.0
                        WHERE id = ?
                    """, (memory.id,))
                    shard_conn.commit()
        
        # 3. 如果索引没匹配，直接搜索各分片
        if len(results) < max_results:
            for shard_idx, shard_conn in self._shard_conns.items():
                shard_cursor = shard_conn.cursor()
                shard_cursor.execute("""
                    SELECT * FROM qwenpaw_memory 
                    WHERE agent_id = ? AND deleted_at IS NULL AND content LIKE ?
                    ORDER BY importance DESC LIMIT ?
                """, (agent_id, f"%{query}%", max_results))
                
                for row in shard_cursor.fetchall():
                    memory = self._row_to_record(row)
                    results.append(memory)
        
        return results[:max_results]
    
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
        await self.migrate_if_needed()
        await self._ensure_fts5_ready()
        
        # 初始化分片管理器
        self._init_shard_manager()
        
        logger.info(f"HumanThinkingDB initialized: {self.db_path}")
    
    async def close(self) -> None:
        if self.conn:
            self.conn.close()
        for conn in self._shard_conns.values():
            try:
                conn.close()
            except Exception:
                pass
        self._shard_conns = {}
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
                
                -- ========== 新增：记忆层级 ==========
                memory_tier TEXT DEFAULT 'short_term',  -- sensory|working|short_term|long_term|archived
                
                -- ========== 新增：记忆分类 ==========
                memory_category TEXT DEFAULT 'episodic',  -- episodic|semantic|procedural
                memory_type TEXT DEFAULT 'general',  -- fact|preference|emotion|general
                
                -- 重要性
                importance INTEGER DEFAULT 3,
                importance_score REAL DEFAULT 0.0,
                
                -- ========== 新增：遗忘曲线 ==========
                decay_score REAL DEFAULT 1.0,  -- 衰减分数
                decay_curve TEXT DEFAULT 'standard',  -- standard|logarithmic|step
                last_decay_at DATETIME,
                
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
                metadata TEXT DEFAULT '{}',
                tags TEXT DEFAULT '[]',
                
                -- ========== 新增：记忆合并 ==========
                merge_count INTEGER DEFAULT 0,  -- 被合并次数
                merged_from TEXT DEFAULT '[]',  -- JSON数组，记录被合并的记忆ID
                last_merged_at DATETIME,        -- 最后合并时间
                merge_similarity REAL DEFAULT 0.0  -- 合并时的相似度
            );
            
            -- 归档记忆表（冷存储）
            CREATE TABLE IF NOT EXISTS qwenpaw_memory_archive (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                
                -- 核心隔离字段（原始数据保留）
                agent_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                user_id TEXT,
                target_id TEXT,
                role TEXT DEFAULT 'assistant',
                
                -- 内容字段
                content TEXT NOT NULL,
                content_summary TEXT,
                
                -- 原始元数据
                memory_tier TEXT,
                memory_category TEXT,
                memory_type TEXT,
                importance INTEGER DEFAULT 3,
                access_count INTEGER DEFAULT 0,
                
                -- 归档信息
                archived_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                original_created_at DATETIME,
                last_accessed_at DATETIME,
                archive_reason TEXT DEFAULT 'frozen_expired',
                recall_count INTEGER DEFAULT 0,
                last_recalled_at DATETIME
            );

            -- 索引（加速检索）
            CREATE INDEX IF NOT EXISTS idx_archive_agent ON qwenpaw_memory_archive (agent_id);
            CREATE INDEX IF NOT EXISTS idx_archive_created ON qwenpaw_memory_archive (original_created_at);
            CREATE INDEX IF NOT EXISTS idx_archive_recalled ON qwenpaw_memory_archive (last_recalled_at);
            
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
            
            -- 6. 分布式分片索引表
            CREATE TABLE IF NOT EXISTS qwenpaw_memory_shard_index (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                shard_index INTEGER NOT NULL,
                original_table TEXT NOT NULL,
                indexed_content TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(memory_id, original_table)
            );
            
            CREATE INDEX IF NOT EXISTS idx_shard_index_lookup ON qwenpaw_memory_shard_index (memory_id);
            CREATE INDEX IF NOT EXISTS idx_shard_content_search ON qwenpaw_memory_shard_index (indexed_content);
        """)
        
        # 洞察表 - 存储睡眠时生成的洞察
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS humanthinking_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                insight_title TEXT NOT NULL,
                insight_content TEXT NOT NULL,
                memory_count INTEGER DEFAULT 0,
                insight_type TEXT DEFAULT 'pattern',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 梦境日记表 - 记录睡眠整理过程
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS humanthinking_dream_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                memories_scanned INTEGER DEFAULT 0,
                memories_consolidated INTEGER DEFAULT 0,
                memories_archived INTEGER DEFAULT 0,
                tokens_saved INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 记忆访问日志表 - 用于遗忘曲线计算和分析
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                agent_id TEXT NOT NULL,
                session_id TEXT,
                access_type TEXT NOT NULL,  -- recall|reference|consolidate|search
                access_latency_ms INTEGER,
                result_relevant INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 工作记忆缓存表 - 快速读写的临时缓存
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_working_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                cache_key TEXT NOT NULL,
                content TEXT NOT NULL,
                content_summary TEXT,
                memory_ids TEXT,  -- JSON数组，关联的记忆ID
                hit_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_accessed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                UNIQUE(agent_id, session_id, cache_key)
            );
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS qwenpaw_memory_contradictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_id TEXT NOT NULL,
                memory_id_1 INTEGER NOT NULL,
                memory_id_2 INTEGER NOT NULL,
                contradiction_type TEXT NOT NULL,
                contradiction_score REAL NOT NULL,
                resolution_status TEXT DEFAULT 'pending',
                resolution_strategy TEXT,
                resolved_memory_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME,
                FOREIGN KEY (memory_id_1) REFERENCES qwenpaw_memory(id),
                FOREIGN KEY (memory_id_2) REFERENCES qwenpaw_memory(id)
            );
        """)
        
        self.cursor.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS qwenpaw_memory_fts USING fts5(
                content,
                indexed_content,
                memory_id UNINDEXED,
                agent_id UNINDEXED,
                session_id UNINDEXED,
                tokenize='unicode61 remove_diacritics 2'
            )
        """)
        
        self.conn.commit()
    
    async def _create_indexes(self) -> None:
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_memory_agent ON qwenpaw_memory(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_session ON qwenpaw_memory(session_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_user ON qwenpaw_memory(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_target ON qwenpaw_memory(target_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_role ON qwenpaw_memory(role)",
            "CREATE INDEX IF NOT EXISTS idx_memory_type ON qwenpaw_memory(memory_type)",
            "CREATE INDEX IF NOT EXISTS idx_memory_agent_session ON qwenpaw_memory(agent_id, session_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_agent_target ON qwenpaw_memory(agent_id, target_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_full_context ON qwenpaw_memory(agent_id, target_id, user_id)",
            "CREATE INDEX IF NOT EXISTS idx_memory_importance ON qwenpaw_memory(importance DESC)",
            "CREATE INDEX IF NOT EXISTS idx_memory_timestamp ON qwenpaw_memory(created_at DESC)",
            "CREATE INDEX IF NOT EXISTS idx_contradiction_agent ON qwenpaw_memory_contradictions(agent_id)",
            "CREATE INDEX IF NOT EXISTS idx_contradiction_mem1 ON qwenpaw_memory_contradictions(memory_id_1)",
            "CREATE INDEX IF NOT EXISTS idx_contradiction_mem2 ON qwenpaw_memory_contradictions(memory_id_2)",
            "CREATE INDEX IF NOT EXISTS idx_contradiction_status ON qwenpaw_memory_contradictions(resolution_status)",
        ]
        for idx in indexes:
            self.cursor.execute(idx)
        self.conn.commit()
    
    async def _init_version(self) -> None:
        self.cursor.execute("SELECT COUNT(*) FROM qwenpaw_memory_version")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("""
                INSERT INTO qwenpaw_memory_version 
                (db_version, schema_version, min_compatible_version)
                VALUES (?, ?, ?)
            """, (CURRENT_SCHEMA_VERSION, CURRENT_SCHEMA_VERSION, CURRENT_SCHEMA_VERSION))
            self.conn.commit()
            logger.info(f"Database version initialized: {CURRENT_SCHEMA_VERSION}")

    def _get_db_schema_version(self) -> str:
        self.cursor.execute("SELECT schema_version FROM qwenpaw_memory_version LIMIT 1")
        row = self.cursor.fetchone()
        return row[0] if row else "0.0.0"

    def _get_migration_chain(self, from_version: str, to_version: str) -> List[MigrationStep]:
        chain = []
        current = from_version
        while current != to_version:
            found = None
            for m in MIGRATIONS:
                if m.from_version == current:
                    found = m
                    break
            if not found:
                available = [m.from_version for m in MIGRATIONS]
                raise RuntimeError(
                    f"无法找到从 {current} 的迁移路径。可用迁移起点: {available}"
                )
            chain.append(found)
            current = found.to_version
        return chain

    async def _backup_before_migration(self) -> Optional[Path]:
        import shutil
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.db_path.with_suffix(f".db.backup_{timestamp}")
        try:
            shutil.copy2(str(self.db_path), str(backup_path))
            logger.info(f"迁移前备份: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"迁移前备份失败: {e}", exc_info=True)
            return None

    async def _execute_migration_step(self, step: MigrationStep) -> None:
        logger.info(f"执行迁移 {step.from_version} → {step.to_version}: {step.description}")

        if step.recreate_tables:
            for old_table, create_sql in step.recreate_tables.items():
                temp_table = f"{old_table}_temp_migration"
                self.cursor.executescript(create_sql.replace(old_table, temp_table, 1))
                self.cursor.executescript(step.data_migration_sql)
                self.cursor.executescript(f"DROP TABLE IF EXISTS {old_table}")
                self.cursor.executescript(f"ALTER TABLE {temp_table} RENAME TO {old_table}")
                self.conn.commit()
        elif step.sql_commands:
            for stmt in step.sql_commands.split(";"):
                stmt = stmt.strip()
                if stmt:
                    try:
                        self.cursor.execute(stmt)
                    except sqlite3.OperationalError as e:
                        if "duplicate column" in str(e).lower():
                            logger.info(f"列已存在，跳过: {e}")
                        else:
                            raise
            self.conn.commit()

        self.cursor.execute("SELECT upgrade_history FROM qwenpaw_memory_version LIMIT 1")
        hist_row = self.cursor.fetchone()
        try:
            history = json.loads(hist_row[0]) if hist_row and hist_row[0] else []
        except (json.JSONDecodeError, TypeError):
            history = []

        history.append({
            "from": step.from_version,
            "to": step.to_version,
            "description": step.description,
            "at": datetime.now().isoformat(),
        })

        self.cursor.execute("""
            UPDATE qwenpaw_memory_version 
            SET schema_version = ?, db_version = ?, updated_at = CURRENT_TIMESTAMP, upgrade_history = ?
        """, (step.to_version, step.to_version, json.dumps(history, ensure_ascii=False)))
        self.conn.commit()

        logger.info(f"迁移完成: {step.from_version} → {step.to_version}")

    async def migrate_if_needed(self) -> None:
        db_version = self._get_db_schema_version()
        code_version = CURRENT_SCHEMA_VERSION

        if db_version == code_version:
            logger.debug(f"数据库版本一致: {db_version}")
            return

        if db_version == "0.0.0":
            await self._init_version()
            return

        try:
            chain = self._get_migration_chain(db_version, code_version)
        except RuntimeError as e:
            logger.error(f"数据库迁移链构建失败: {e}")
            return

        if not chain:
            logger.debug("无需迁移")
            return

        logger.info(f"数据库需要迁移: {db_version} → {code_version}, 共 {len(chain)} 步")
        for i, step in enumerate(chain):
            logger.info(f"  步骤 {i+1}: {step.from_version} → {step.to_version} ({step.description})")

        backup_path = await self._backup_before_migration()

        for step in chain:
            try:
                await self._execute_migration_step(step)
            except Exception as e:
                if backup_path:
                    logger.error(
                        f"迁移失败! 步骤: {step.from_version} → {step.to_version}. "
                        f"备份文件: {backup_path}. 请手动恢复。错误: {e}",
                        exc_info=True,
                    )
                else:
                    logger.error(f"迁移失败且无备份: {e}", exc_info=True)
                raise

        logger.info(f"全部迁移完成: {db_version} → {code_version}")

    def get_version_info(self) -> Dict[str, Any]:
        return {
            "db_schema_version": self._get_db_schema_version(),
            "code_schema_version": CURRENT_SCHEMA_VERSION,
            "needs_migration": self._get_db_schema_version() != CURRENT_SCHEMA_VERSION,
        }

    def get_migration_history(self) -> List[Dict[str, Any]]:
        self.cursor.execute("SELECT upgrade_history FROM qwenpaw_memory_version LIMIT 1")
        row = self.cursor.fetchone()
        if not row or not row[0]:
            return []
        try:
            return json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            return []

    def _search_fts(self, query: str, limit: int = 25) -> list:
        try:
            fts_query = self._build_fts_query(query)
            self.cursor.execute(
                "SELECT memory_id FROM qwenpaw_memory_fts WHERE qwenpaw_memory_fts MATCH ? ORDER BY rank LIMIT ?",
                (fts_query, limit),
            )
            return [row[0] for row in self.cursor.fetchall()]
        except Exception:
            return []

    def _build_fts_query(self, query: str) -> str:
        import re
        terms = []
        for word in query.strip().split():
            word = re.sub(r'[^\w\u4e00-\u9fff]', '', word)
            if len(word) >= 2:
                terms.append(f'"{word}"*')
            elif len(word) == 1:
                terms.append(word)
        if not terms:
            return query.strip()
        return " OR ".join(terms)

    async def _ensure_fts5_ready(self) -> None:
        try:
            self.cursor.execute("SELECT COUNT(*) FROM qwenpaw_memory_fts")
            if self.cursor.fetchone()[0] == 0:
                await self.rebuild_fts_index()
            else:
                logger.debug("FTS5 index ready")
        except Exception:
            pass

    async def rebuild_fts_index(self) -> int:
        self.cursor.execute("DELETE FROM qwenpaw_memory_fts")
        self.cursor.execute(
            "INSERT INTO qwenpaw_memory_fts(content, indexed_content, memory_id, agent_id, session_id) "
            "SELECT content, COALESCE(indexed_content, content), id, agent_id, session_id "
            "FROM qwenpaw_memory WHERE deleted_at IS NULL"
        )
        self.conn.commit()
        count = self.cursor.rowcount
        logger.info(f"FTS5 index rebuilt: {count} records")
        return count

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
        
        # session_key 包含 target_id，确保不同对话对象的记忆隔离
        session_key = f"{agent_id}_{target_id or user_id or 'unknown'}_{session_id or 'default'}"
        
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
        
        self.cursor.execute(
            "INSERT INTO qwenpaw_memory_fts(content, indexed_content, memory_id, agent_id, session_id) VALUES(?,?,?,?,?)",
            (content, content, memory_id, agent_id, session_id)
        )
        self.conn.commit()
        
        if self.enable_distributed and memory_id:
            self.cursor.execute("""
                INSERT INTO qwenpaw_memory_shard_index 
                (memory_id, shard_index, original_table, indexed_content)
                VALUES (?, 0, 'qwenpaw_memory', ?)
            """, (memory_id, content[:200]))
            self.conn.commit()
        
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
        
        if not memories:
            return 0
        
        valid_memories = []
        for m in memories:
            if not m.get("content") or not m.get("agent_id"):
                logger.warning(f"Skipping memory with missing content or agent_id: {m}")
                continue
            valid_memories.append(m)
        
        if not valid_memories:
            return 0
        
        data = [
            (
                m.get("agent_id"),
                m.get("session_id"),
                m.get("user_id"),
                m.get("target_id"),
                m.get("role", "assistant"),
                f"{m.get('agent_id', 'default')}_{m.get('target_id') or m.get('user_id') or 'unknown'}_{m.get('session_id', 'default')}",
                m.get("content"),
                m.get("importance", 3),
                m.get("memory_type", "general"),
                json.dumps(m.get("metadata", {})),
                json.dumps(m.get("tags", []))
            )
            for m in valid_memories
        ]
        
        self.cursor.executemany("""
            INSERT INTO qwenpaw_memory 
            (agent_id, session_id, user_id, target_id, role, session_key, content, 
             importance, memory_type, metadata, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        
        if sync:
            self.conn.commit()
        
        if self.enable_distributed and data:
            self.cursor.execute("SELECT MAX(id) FROM qwenpaw_memory")
            last_id = self.cursor.fetchone()[0] or 0
            start_id = last_id - len(data) + 1
            
            memory_ids = []
            for i, m in enumerate(valid_memories):
                mid = start_id + i
                memory_ids.append((mid, m.get("content", "")[:200]))
            
            for memory_id, content in memory_ids:
                self.cursor.execute("""
                    INSERT INTO qwenpaw_memory_shard_index 
                    (memory_id, shard_index, original_table, indexed_content)
                    VALUES (?, 0, 'qwenpaw_memory', ?)
                """, (memory_id, content))
            
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
        round_duration_seconds: int = 300,
        include_frozen: bool = True,
        include_archived: bool = False
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
            include_frozen: 是否包含冷藏记忆（会唤醒）
            include_archived: 是否包含归档记忆
        
        Returns:
            MemoryRecord 列表
        """
        results = []
        
        fts_memory_ids = self._search_fts(query, max_results * 5)
        
        def _build_sql_and_params(base_condition, filter_params, tier_clause=""):
            sql = base_condition + " AND agent_id = ? AND deleted_at IS NULL"
            params = [agent_id]
            if tier_clause:
                sql += tier_clause
            if target_id:
                sql += " AND target_id = ?"
                params.append(target_id)
            if cross_session:
                pass
            elif session_id:
                sql += " AND session_id = ?"
                params.append(session_id)
            if user_id:
                sql += " AND user_id = ?"
                params.append(user_id)
            if role:
                sql += " AND role = ?"
                params.append(role)
            if fts_memory_ids:
                placeholders = ",".join(["?" for _ in fts_memory_ids])
                sql += f" AND id IN ({placeholders})"
                params.extend(fts_memory_ids)
            else:
                sql += " AND content LIKE ?"
                params.append(f"%{query}%")
            if exclude_recent_rounds > 0:
                exclude_seconds = exclude_recent_rounds * round_duration_seconds
                sql += " AND created_at < datetime('now', '-' || ? || ' seconds')"
                params.append(exclude_seconds)
            sql += " ORDER BY importance DESC, created_at DESC LIMIT ?"
            params.append(max_results * 2)
            return sql, params
        
        active_sql, active_params = _build_sql_and_params("SELECT * FROM qwenpaw_memory")
        self.cursor.execute(active_sql, active_params)
        active_results = [self._row_to_record(row) for row in self.cursor.fetchall()]
        results.extend(active_results)
        
        if include_frozen and len(results) < max_results:
            frozen_sql, frozen_params = _build_sql_and_params(
                "SELECT * FROM qwenpaw_memory", " AND memory_tier = 'frozen'"
            )
            self.cursor.execute(frozen_sql, frozen_params)
            frozen_rows = self.cursor.fetchall()
            for row in frozen_rows:
                memory = self._row_to_record(row)
                await self.wakeup_memory(memory.id)
                results.append(memory)
        
        # 3. 如果启用了分布式，搜索分片索引
        if self.enable_distributed and len(results) < max_results:
            shard_results = await self._search_shards(query, agent_id, target_id, user_id, max_results)
            results.extend(shard_results)
        
        # 4. 可选：搜索归档记忆
        if include_archived and len(results) < max_results:
            archived_sql = "SELECT * FROM qwenpaw_memory_archive WHERE agent_id = ?"
            archived_params = [agent_id]
            
            if target_id:
                archived_sql += " AND target_id = ?"
                archived_params.append(target_id)
            if user_id:
                archived_sql += " AND user_id = ?"
                archived_params.append(user_id)
            archived_sql += " AND content LIKE ?"
            archived_params.append(f"%{query}%")
            archived_sql += " ORDER BY importance DESC LIMIT ?"
            archived_params.append(max_results)
            
            self.cursor.execute(archived_sql, archived_params)
            for row in self.cursor.fetchall():
                row_dict = dict(row)
                results.append(MemoryRecord(
                    id=row_dict.get("id", 0),
                    agent_id=row_dict.get("agent_id", ""),
                    session_id=row_dict.get("session_id", ""),
                    user_id=row_dict.get("user_id"),
                    target_id=row_dict.get("target_id"),
                    role=row_dict.get("role", "assistant"),
                    content=row_dict.get("content", ""),
                    importance=row_dict.get("importance", 3),
                    memory_type=row_dict.get("memory_type", "general"),
                    metadata={},
                    created_at=row_dict.get("original_created_at") or row_dict.get("archived_at", ""),
                    memory_tier="archived",
                    memory_category=row_dict.get("memory_category", "episodic"),
                    tags=[]
                ))
        
        # 4. 排序并返回结果
        results.sort(key=lambda x: (x.importance, x.created_at), reverse=True)
        return results[:max_results]
    
    async def wakeup_memory(self, memory_id: int) -> bool:
        """唤醒冷藏记忆"""
        self.cursor.execute("""
            UPDATE qwenpaw_memory 
            SET memory_tier = 'short_term',
                access_frozen = 0,
                decay_score = 1.0,
                frozen_at = NULL,
                last_accessed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (memory_id,))
        self.conn.commit()
        return self.cursor.rowcount > 0
    
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
        """更新记忆访问统计，唤醒冷藏记忆"""
        import datetime
        
        now = datetime.datetime.now().isoformat()
        
        # 检查是否是冷藏记忆，如果是则唤醒
        self.cursor.execute("SELECT memory_tier FROM qwenpaw_memory WHERE id = ?", (memory_id,))
        row = self.cursor.fetchone()
        
        if row and row[0] == 'frozen':
            # 唤醒冷藏记忆
            self.cursor.execute("""
                UPDATE qwenpaw_memory 
                SET access_count = access_count + 1, 
                    last_accessed_at = ?,
                    memory_tier = 'short_term',
                    access_frozen = 0,
                    decay_score = 1.0,
                    frozen_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (now, memory_id))
        else:
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
        
        # sqlite3.Row 不支持 .get() 方法，使用 try/except 处理可能为 NULL 的字段
        def _get_row_value(row, key, default=None):
            try:
                value = row[key]
                return value if value is not None else default
            except (KeyError, IndexError):
                return default
        
        return MemoryRecord(
            id=row["id"],
            agent_id=row["agent_id"],
            session_id=row["session_id"],
            user_id=row["user_id"],
            target_id=_get_row_value(row, "target_id"),
            role=row["role"],
            content=row["content"],
            importance=row["importance"],
            memory_type=row["memory_type"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
            created_at=row["created_at"],
            session_key=row["session_key"],
            content_embedding=_get_row_value(row, "content_embedding"),
            content_summary=_get_row_value(row, "content_summary"),
            importance_score=_get_row_value(row, "importance_score", 0.0),
            access_count=_get_row_value(row, "access_count", 0),
            search_count=_get_row_value(row, "search_count", 0),
            search_score=_get_row_value(row, "search_score", 0.0),
            access_frozen=_get_row_value(row, "access_frozen", False),
            frozen_at=_get_row_value(row, "frozen_at"),
            last_accessed_at=_get_row_value(row, "last_accessed_at"),
            last_searched_at=_get_row_value(row, "last_searched_at"),
            updated_at=_get_row_value(row, "updated_at"),
            deleted_at=_get_row_value(row, "deleted_at"),
            tags=json.loads(row["tags"]) if row["tags"] else [],
            memory_tier=_get_row_value(row, "memory_tier", "short_term"),
            memory_category=_get_row_value(row, "memory_category", "episodic"),
            decay_score=_get_row_value(row, "decay_score", 1.0),
            decay_curve=_get_row_value(row, "decay_curve", "standard"),
            archived_at=_get_row_value(row, "archived_at")
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
        
        sql += " AND id IN (SELECT id FROM qwenpaw_memory WHERE agent_id = ? AND access_frozen = 1 AND deleted_at IS NULL"
        if query:
            sql += " AND content LIKE ?"
            params.extend([agent_id, f"%{query}%"])
        else:
            params.append(agent_id)
        sql += f" LIMIT {int(limit)})"
        
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
    
    async def add_insight(
        self,
        agent_id: str,
        title: str,
        content: str,
        memory_count: int = 0,
        insight_type: str = "pattern"
    ) -> int:
        """添加洞察"""
        self.cursor.execute("""
            INSERT INTO humanthinking_insights 
            (agent_id, insight_title, insight_content, memory_count, insight_type)
            VALUES (?, ?, ?, ?, ?)
        """, (agent_id, title, content, memory_count, insight_type))
        self.conn.commit()
        return self.cursor.lastrowid
    
    async def get_insights(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取洞察列表"""
        self.cursor.execute("""
            SELECT * FROM humanthinking_insights 
            WHERE agent_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (agent_id, limit))
        return [dict(row) for row in self.cursor.fetchall()]
    
    async def add_dream_log(
        self,
        agent_id: str,
        action: str,
        details: str = None,
        memories_scanned: int = 0,
        memories_consolidated: int = 0,
        memories_archived: int = 0,
        tokens_saved: int = 0
    ) -> int:
        """添加梦境日记"""
        self.cursor.execute("""
            INSERT INTO humanthinking_dream_logs 
            (agent_id, action, details, memories_scanned, memories_consolidated, memories_archived, tokens_saved)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (agent_id, action, details, memories_scanned, memories_consolidated, memories_archived, tokens_saved))
        self.conn.commit()
        return self.cursor.lastrowid
    
    async def get_dream_logs(self, agent_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """获取梦境日记列表"""
        self.cursor.execute("""
            SELECT * FROM humanthinking_dream_logs 
            WHERE agent_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (agent_id, limit))
        return [dict(row) for row in self.cursor.fetchall()]
    
    async def get_memories_for_consolidation(
        self, 
        agent_id: str, 
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """获取需要整理的记忆（过去N天）"""
        self.cursor.execute("""
            SELECT * FROM qwenpaw_memory 
            WHERE agent_id = ? 
            AND deleted_at IS NULL
            AND created_at >= datetime('now', '-' || ? || ' days')
            ORDER BY created_at DESC
        """, (agent_id, days))
        return [dict(row) for row in self.cursor.fetchall()]
    
    async def update_memory_type(
        self, 
        memory_id: int, 
        memory_type: str
    ) -> None:
        """更新记忆类型"""
        self.cursor.execute("""
            UPDATE qwenpaw_memory 
            SET memory_type = ?
            WHERE id = ?
        """, (memory_type, memory_id))
        self.conn.commit()
    
    async def archive_memory(self, memory_id: int) -> None:
        """归档记忆（标记为低优先级）"""
        self.cursor.execute("""
            UPDATE qwenpaw_memory 
            SET memory_tier = 'archived', importance = 1, access_frozen = 1
            WHERE id = ?
        """, (memory_id,))
        self.conn.commit()
    
    async def log_memory_access(
        self,
        memory_id: int,
        agent_id: str,
        session_id: str,
        access_type: str,
        access_latency_ms: int = None,
        result_relevant: int = None
    ) -> int:
        """记录记忆访问日志"""
        self.cursor.execute("""
            INSERT INTO memory_access_log 
            (memory_id, agent_id, session_id, access_type, access_latency_ms, result_relevant)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (memory_id, agent_id, session_id, access_type, access_latency_ms, result_relevant))
        self.conn.commit()
        return self.cursor.lastrowid
    
    async def get_access_stats(self, memory_id: int, days: int = 7) -> Dict[str, Any]:
        """获取记忆访问统计"""
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total_access,
                SUM(CASE WHEN access_type = 'recall' THEN 1 ELSE 0 END) as recall_count,
                SUM(CASE WHEN access_type = 'search' THEN 1 ELSE 0 END) as search_count,
                AVG(access_latency_ms) as avg_latency,
                SUM(CASE WHEN result_relevant = 1 THEN 1 ELSE 0 END) as relevant_count
            FROM memory_access_log
            WHERE memory_id = ? 
            AND created_at >= datetime('now', '-' || ? || ' days')
        """, (memory_id, days))
        row = self.cursor.fetchone()
        return dict(row) if row else {}
    
    async def get_tier_stats(self, agent_id: str) -> Dict[str, int]:
        """获取各层级记忆统计"""
        self.cursor.execute("""
            SELECT memory_tier, COUNT(*) as count 
            FROM qwenpaw_memory 
            WHERE agent_id = ? AND deleted_at IS NULL
            GROUP BY memory_tier
        """, (agent_id,))
        result = {}
        for row in self.cursor.fetchall():
            result[row[0]] = row[1]
        return result
    
    async def get_category_stats(self, agent_id: str) -> Dict[str, int]:
        """获取各分类记忆统计"""
        self.cursor.execute("""
            SELECT memory_category, COUNT(*) as count 
            FROM qwenpaw_memory 
            WHERE agent_id = ? AND deleted_at IS NULL
            GROUP BY memory_category
        """, (agent_id,))
        result = {}
        for row in self.cursor.fetchall():
            result[row[0]] = row[1]
        return result
    
    async def set_memory_tier(self, memory_id: int, tier: str) -> None:
        """设置记忆层级"""
        self.cursor.execute("""
            UPDATE qwenpaw_memory SET memory_tier = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (tier, memory_id))
        self.conn.commit()
    
    async def set_memory_category(self, memory_id: int, category: str) -> None:
        """设置记忆分类"""
        self.cursor.execute("""
            UPDATE qwenpaw_memory SET memory_category = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (category, memory_id))
        self.conn.commit()
    
    async def update_decay(self, memory_id: int, decay_score: float) -> None:
        """更新遗忘分数"""
        self.cursor.execute("""
            UPDATE qwenpaw_memory 
            SET decay_score = ?, last_decay_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (decay_score, memory_id))
        self.conn.commit()
    
    async def update_memory_score(self, memory_id: int, score: float) -> None:
        """更新记忆评分（六维评分结果）"""
        self.cursor.execute("""
            UPDATE qwenpaw_memory 
            SET importance_score = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (score, memory_id))
        self.conn.commit()
    
    async def get_light_sleep_memories(self, agent_id: str, hours: int = 1) -> List[Dict]:
        """获取浅层睡眠需要整理的记忆
        
        只获取最近的 short_term + episodic 类型的记忆
        不归档、不删除、不改变层级
        """
        import datetime
        cutoff_time = datetime.datetime.now() - datetime.timedelta(hours=hours)
        
        self.cursor.execute("""
            SELECT * FROM qwenpaw_memory 
            WHERE agent_id = ? 
              AND deleted_at IS NULL 
              AND memory_tier IN ('short_term', 'working')
              AND memory_category = 'episodic'
              AND created_at > ?
            ORDER BY created_at DESC
            LIMIT 100
        """, (agent_id, cutoff_time.isoformat()))
        
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def get_recent_memories(self, agent_id: str, days: int = 7) -> List[Dict]:
        """获取最近N天的所有记忆"""
        import datetime
        cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days)
        
        self.cursor.execute("""
            SELECT * FROM qwenpaw_memory 
            WHERE agent_id = ? 
              AND deleted_at IS NULL 
              AND created_at > ?
            ORDER BY created_at DESC
            LIMIT 500
        """, (agent_id, cutoff_time.isoformat()))
        
        rows = self.cursor.fetchall()
        return [dict(row) for row in rows]
    
    async def save_reflection_summary(self, agent_id: str, summary: str, patterns: List[Dict], truths: List[Dict]) -> None:
        """保存反思摘要"""
        
        theme_summary = f"主题：{', '.join([p.get('theme', '') for p in patterns[:3]])}"
        
        self.cursor.execute("""
            INSERT INTO humanthinking_dream_logs 
            (agent_id, action, details, memories_scanned, memories_consolidated)
            VALUES (?, ?, ?, ?, ?)
        """, (agent_id, "REFLECTION", theme_summary, len(patterns), len(truths)))
        self.conn.commit()
    
    async def apply_forgetting_curve(self, agent_id: str, frozen_days: int = 30, archive_days: int = 90, delete_days: int = 180) -> int:
        """应用遗忘曲线，处理完整生命周期
        
        流程：
        1. 冷藏：N天无访问 → 标记为冷藏
        2. 归档：冷藏M天无访问 → 移动到归档表
        3. 删除：归档D天无访问 → 彻底删除
        4. 衰减：活跃记忆 → 正常衰减
        
        Args:
            agent_id: Agent ID
            frozen_days: 冷藏天数（默认30天）
            archive_days: 归档天数（默认90天）
            delete_days: 删除天数（默认180天）
        """
        import datetime
        frozen_count = 0
        archived_count = 0
        deleted_count = 0
        
        # 1. 冷藏：frozen_days 无访问的记忆
        self.cursor.execute("""
            UPDATE qwenpaw_memory 
            SET memory_tier = 'frozen',
                access_frozen = 1,
                frozen_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE agent_id = ? 
            AND deleted_at IS NULL 
            AND access_frozen = 0
            AND memory_tier NOT IN ('frozen', 'archived')
            AND (
                last_accessed_at IS NULL 
                OR last_accessed_at < datetime('now', '-' || ? || ' days')
            )
        """, (agent_id, frozen_days))
        frozen_count = self.cursor.rowcount
        
        # 2. 归档：冷藏 archive_days 天无访问的记忆
        self.cursor.execute("""
            SELECT id FROM qwenpaw_memory
            WHERE agent_id = ?
            AND memory_tier = 'frozen'
            AND frozen_at < datetime('now', '-' || ? || ' days')
        """, (agent_id, archive_days))
        to_archive = [row[0] for row in self.cursor.fetchall()]
        
        for memory_id in to_archive:
            await self.archive_to_table(memory_id, 'frozen_expired')
            archived_count += 1
        
        # 3. 删除：归档90天无访问的记忆
        deleted_count = await self.delete_old_archives(agent_id, days=delete_days)
        
        # 4. 衰减：活跃记忆正常衰减
        self.cursor.execute("""
            UPDATE qwenpaw_memory 
            SET decay_score = decay_score * 0.95,
                last_decay_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE agent_id = ? 
            AND deleted_at IS NULL 
            AND access_frozen = 0
            AND memory_tier NOT IN ('frozen', 'archived')
            AND access_count < 10
        """, (agent_id,))
        
        self.conn.commit()
        
        logger.info(f"Forgetting curve: frozen={frozen_count}, archived={archived_count}, deleted={deleted_count}")
        return frozen_count + archived_count
    
    async def get_low_value_memories(self, agent_id: str, threshold: float = 0.3, limit: int = 100) -> List[Dict]:
        """获取低价值记忆（用于归档）"""
        self.cursor.execute("""
            SELECT id, content, decay_score, importance, access_count
            FROM qwenpaw_memory
            WHERE agent_id = ?
            AND deleted_at IS NULL
            AND memory_tier NOT IN ('archived')
            AND (decay_score * importance / 5.0) < ?
            ORDER BY decay_score * importance ASC
            LIMIT ?
        """, (agent_id, threshold, limit))
        return [dict(row) for row in self.cursor.fetchall()]
    
    # ========== 工作缓存方法 ==========
    
    async def set_working_cache(
        self,
        agent_id: str,
        session_id: str,
        cache_key: str,
        content: str,
        content_summary: str = None,
        memory_ids: List[int] = None,
        ttl_seconds: int = 3600
    ) -> None:
        """设置工作缓存"""

        self.cursor.execute("""
            INSERT OR REPLACE INTO memory_working_cache 
            (agent_id, session_id, cache_key, content, content_summary, memory_ids, hit_count, last_accessed_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, datetime('now', '+' || ? || ' seconds'))
        """, (agent_id, session_id, cache_key, content, content_summary, json.dumps(memory_ids) if memory_ids else None, ttl_seconds))
        self.conn.commit()
    
    async def get_working_cache(
        self,
        agent_id: str,
        session_id: str,
        cache_key: str
    ) -> Optional[Dict]:
        """获取工作缓存"""
        self.cursor.execute("""
            SELECT * FROM memory_working_cache
            WHERE agent_id = ? AND session_id = ? AND cache_key = ?
            AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        """, (agent_id, session_id, cache_key))
        row = self.cursor.fetchone()
        if row:
            self.cursor.execute("""
                UPDATE memory_working_cache SET hit_count = hit_count + 1, last_accessed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (row[0],))
            self.conn.commit()
            return dict(row)
        return None
    
    async def clear_working_cache(self, agent_id: str = None, session_id: str = None) -> int:
        """清理工作缓存"""
        if agent_id and session_id:
            self.cursor.execute("DELETE FROM memory_working_cache WHERE agent_id = ? AND session_id = ?", (agent_id, session_id))
        elif agent_id:
            self.cursor.execute("DELETE FROM memory_working_cache WHERE agent_id = ?", (agent_id,))
        else:
            self.cursor.execute("DELETE FROM memory_working_cache WHERE expires_at < CURRENT_TIMESTAMP")
        self.conn.commit()
        return self.cursor.rowcount
    
    # ========== 归档相关方法 ==========
    
    async def archive_to_table(self, memory_id: int, reason: str = 'frozen_expired') -> bool:
        """将记忆归档到归档表"""
        # 获取原始记忆
        self.cursor.execute("SELECT * FROM qwenpaw_memory WHERE id = ?", (memory_id,))
        row = self.cursor.fetchone()
        if not row:
            return False
        
        memory = dict(row)
        
        # 插入归档表
        self.cursor.execute("""
            INSERT INTO qwenpaw_memory_archive (
                agent_id, session_id, user_id, target_id, role,
                content, content_summary,
                memory_tier, memory_category, memory_type, importance, access_count,
                original_created_at, last_accessed_at, archive_reason
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory.get('agent_id'), memory.get('session_id'), memory.get('user_id'),
            memory.get('target_id'), memory.get('role'),
            memory.get('content'), memory.get('content_summary'),
            memory.get('memory_tier'), memory.get('memory_category'), memory.get('memory_type'),
            memory.get('importance'), memory.get('access_count'),
            memory.get('created_at'), memory.get('last_accessed_at'), reason
        ))
        
        # 删除主表记录
        self.cursor.execute("DELETE FROM qwenpaw_memory WHERE id = ?", (memory_id,))
        self.conn.commit()
        return True
    
    async def recall_from_archive(self, archive_id: int) -> bool:
        """从归档表恢复记忆到主表"""
        self.cursor.execute("SELECT * FROM qwenpaw_memory_archive WHERE id = ?", (archive_id,))
        row = self.cursor.fetchone()
        if not row:
            return False
        
        archive = dict(row)
        
        session_key = f"{archive.get('agent_id', 'default')}_{archive.get('target_id') or archive.get('user_id') or 'unknown'}_{archive.get('session_id', 'default')}"
        
        self.cursor.execute("""
            INSERT INTO qwenpaw_memory (
                agent_id, session_id, user_id, target_id, role, session_key,
                content, content_summary,
                memory_tier, memory_category, memory_type, importance, access_count,
                created_at, last_accessed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            archive.get('agent_id'), archive.get('session_id'), archive.get('user_id'),
            archive.get('target_id'), archive.get('role'), session_key,
            archive.get('content'), archive.get('content_summary'),
            'short_term', archive.get('memory_category'), archive.get('memory_type'),
            archive.get('importance'), 0,
            archive.get('original_created_at'), __import__('datetime').datetime.now().isoformat()
        ))
        
        # 更新归档表的召回次数
        self.cursor.execute("""
            UPDATE qwenpaw_memory_archive 
            SET recall_count = recall_count + 1, last_recalled_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (archive_id,))
        
        self.conn.commit()
        return True
    
    async def get_archive_memories(self, agent_id: str, limit: int = 100) -> List[Dict]:
        """获取归档记忆列表"""
        self.cursor.execute("""
            SELECT * FROM qwenpaw_memory_archive
            WHERE agent_id = ?
            ORDER BY archived_at DESC
            LIMIT ?
        """, (agent_id, limit))
        return [dict(row) for row in self.cursor.fetchall()]
    
    async def delete_old_archives(self, agent_id: str = None, days: int = 90) -> int:
        """删除超期归档（默认90天）"""
        if agent_id:
            self.cursor.execute("""
                DELETE FROM qwenpaw_memory_archive 
                WHERE agent_id = ? AND archived_at < datetime('now', '-' || ? || ' days')
            """, (agent_id, days))
        else:
            self.cursor.execute("""
                DELETE FROM qwenpaw_memory_archive 
                WHERE archived_at < datetime('now', '-' || ? || ' days')
            """, (days,))
        self.conn.commit()
        return self.cursor.rowcount
    
    async def get_archive_stats(self, agent_id: str = None) -> Dict:
        """获取归档统计"""
        if agent_id:
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN recall_count > 0 THEN 1 ELSE 0 END) as recalled,
                    SUM(CASE WHEN archived_at > datetime('now', '-30 days') THEN 1 ELSE 0 END) as last_30_days
                FROM qwenpaw_memory_archive
                WHERE agent_id = ?
            """, (agent_id,))
        else:
            self.cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN recall_count > 0 THEN 1 ELSE 0 END) as recalled,
                    SUM(CASE WHEN archived_at > datetime('now', '-30 days') THEN 1 ELSE 0 END) as last_30_days
                FROM qwenpaw_memory_archive
            """)
        row = self.cursor.fetchone()
        return dict(row) if row else {}
