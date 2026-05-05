# -*- coding: utf-8 -*-
"""
数据迁移器：支持数据库 schema 升级和数据迁移

支持：
- 版本检测
- 迁移脚本执行
- 回滚支持
- 数据校验
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

from .version import VersionManager

logger = logging.getLogger(__name__)


def _parse_version_tuple(version: str) -> tuple:
    """解析版本号为元组用于比较"""
    parsed = VersionManager.parse_version(version)
    return (parsed[0], parsed[1], parsed[2])


class Migration:
    """单次迁移"""

    def __init__(
        self,
        version: str,
        description: str,
        upgrade_sql: str,
        downgrade_sql: Optional[str] = None
    ):
        self.version = version
        self.description = description
        self.upgrade_sql = upgrade_sql
        self.downgrade_sql = downgrade_sql


class Migrator:
    """数据库迁移器"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self._migrations: List[Migration] = []

    def register_migration(self, migration: Migration) -> None:
        """注册迁移"""
        self._migrations.append(migration)
        logger.debug(f"Registered migration: {migration.version} - {migration.description}")

    def get_current_version(self) -> Optional[str]:
        """获取当前数据库版本"""
        if not self.db_path.exists():
            return None
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT db_version FROM qwenpaw_memory_version ORDER BY updated_at DESC LIMIT 1")
            row = cursor.fetchone()
            return row[0] if row else None
        except Exception:
            return None
        finally:
            conn.close()

    def migrate(self, target_version: Optional[str] = None) -> Dict[str, Any]:
        """
        执行迁移
        
        Args:
            target_version: 目标版本（可选，默认升级到最新）
        
        Returns:
            迁移结果
        """
        current_version = self.get_current_version()
        
        if not current_version:
            logger.info("No existing database found, creating new database")
            return self._create_new_database()
        
        # 按版本排序（使用元组比较）
        sorted_migrations = sorted(
            self._migrations, 
            key=lambda m: _parse_version_tuple(m.version)
        )
        
        current_version_tuple = _parse_version_tuple(current_version)
        target_version_tuple = _parse_version_tuple(target_version) if target_version else None
        
        # 找到需要执行的迁移
        pending_migrations = []
        for migration in sorted_migrations:
            migration_tuple = _parse_version_tuple(migration.version)
            if migration_tuple > current_version_tuple:
                if target_version_tuple and migration_tuple > target_version_tuple:
                    break
                pending_migrations.append(migration)
        
        if not pending_migrations:
            logger.info(f"Database is already at latest version: {current_version}")
            return {
                "status": "success",
                "current_version": current_version,
                "migrated_count": 0,
            }
        
        # 执行迁移
        migrated = []
        for migration in pending_migrations:
            logger.info(f"Migrating to {migration.version}: {migration.description}")
            try:
                self._execute_migration(migration)
                migrated.append(migration.version)
            except Exception as e:
                logger.error(f"Migration {migration.version} failed: {e}")
                return {
                    "status": "error",
                    "current_version": current_version,
                    "migrated_count": len(migrated),
                    "failed_version": migration.version,
                    "error": str(e),
                }
        
        new_version = migrated[-1] if migrated else current_version
        return {
            "status": "success",
            "previous_version": current_version,
            "current_version": new_version,
            "migrated_count": len(migrated),
            "migrated_versions": migrated,
        }

    def _execute_migration(self, migration: Migration) -> None:
        """执行单次迁移"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # 执行升级 SQL
            if migration.upgrade_sql:
                cursor.executescript(migration.upgrade_sql)
            
            # 更新版本记录
            cursor.execute("""
                INSERT INTO qwenpaw_memory_version (db_version, schema_version, upgrade_history)
                VALUES (?, ?, ?)
            """, (migration.version, migration.version, "[]"))
            
            conn.commit()
            logger.info(f"Successfully migrated to {migration.version}")
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _create_new_database(self) -> Dict[str, Any]:
        """创建新数据库"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            # 创建版本表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS qwenpaw_memory_version (
                    id INTEGER PRIMARY KEY,
                    db_version TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    min_compatible_version TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    upgrade_history TEXT DEFAULT '[]'
                )
            """)
            
            conn.commit()
            logger.info(f"Created new database: {self.db_path}")
            return {
                "status": "success",
                "current_version": "1.0.0",
                "migrated_count": 0,
            }
        finally:
            conn.close()

    def rollback(self, target_version: str) -> Dict[str, Any]:
        """
        回滚到指定版本
        
        Args:
            target_version: 目标版本
        
        Returns:
            回滚结果
        """
        current_version = self.get_current_version()
        if not current_version:
            return {"status": "error", "error": "No database found"}
        
        current_version_tuple = _parse_version_tuple(current_version)
        target_version_tuple = _parse_version_tuple(target_version)
        
        if current_version_tuple <= target_version_tuple:
            return {"status": "success", "message": "Already at or before target version"}
        
        # 找到需要回滚的迁移（倒序，使用元组比较）
        sorted_migrations = sorted(
            self._migrations, 
            key=lambda m: _parse_version_tuple(m.version), 
            reverse=True
        )
        rollback_migrations = []
        for migration in sorted_migrations:
            if _parse_version_tuple(migration.version) > target_version_tuple:
                rollback_migrations.append(migration)
        
        if not rollback_migrations:
            return {"status": "error", "error": "No downgrade SQL available"}
        
        # 执行回滚
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        try:
            for migration in rollback_migrations:
                if migration.downgrade_sql:
                    cursor.executescript(migration.downgrade_sql)
                    logger.info(f"Rolled back to {migration.version}")
            
            conn.commit()
            return {
                "status": "success",
                "previous_version": current_version,
                "current_version": target_version,
                "rolled_back_count": len(rollback_migrations),
            }
        except Exception as e:
            conn.rollback()
            return {"status": "error", "error": str(e)}
        finally:
            conn.close()
