# -*- coding: utf-8 -*-
"""
HumanThinking 备份管理器

功能：
- 手动备份：导出单个/多个 Agent 记忆
- 自动备份：定时备份所有 Agent
- 导入恢复：从备份恢复
- 导出为 JSON/SQL
"""

import os
import shutil
import json
import sqlite3
import logging
import hashlib
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


def _resolve_qwenpaw_dir() -> Path:
    env_dir = os.environ.get('QWENPAW_WORKING_DIR', '')
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    try:
        from qwenpaw.constant import WORKING_DIR
        return WORKING_DIR
    except (ImportError, AttributeError):
        pass
    legacy = Path("~/.copaw").expanduser()
    if legacy.exists():
        return legacy.resolve()
    return Path("~/.qwenpaw").expanduser().resolve()


def _resolve_all_agent_workspace_dirs() -> list[Path]:
    try:
        from qwenpaw.config.utils import load_config
        config = load_config()
        return [
            Path(ref.workspace_dir).expanduser().resolve()
            for ref in config.agents.profiles.values()
        ]
    except Exception:
        pass
    workspaces_dir = _resolve_qwenpaw_dir() / "workspaces"
    if workspaces_dir.exists():
        return [d for d in workspaces_dir.iterdir() if d.is_dir()]
    return []


def _resolve_agent_workspace_dir(agent_id: str) -> Path:
    try:
        from qwenpaw.config.utils import load_config
        config = load_config()
        if agent_id in config.agents.profiles:
            ws_dir = config.agents.profiles[agent_id].workspace_dir
            return Path(ws_dir).expanduser().resolve()
    except Exception:
        pass
    return _resolve_qwenpaw_dir() / "workspaces" / agent_id


@dataclass
class BackupInfo:
    """备份信息"""
    id: str
    agent_id: str
    backup_path: str
    size_bytes: int
    created_at: str
    db_version: str
    checksum: str


class BackupScheduler:
    """自动备份调度器"""
    
    def __init__(self, backup_manager: 'BackupManager'):
        self.backup_manager = backup_manager
        self._running = False
        self._thread = None
        self._interval_hours = 24
    
    def start(self, interval_hours: int = 24):
        """启动自动备份"""
        if self._running:
            logger.warning("Backup scheduler already running")
            return
        
        self._interval_hours = interval_hours
        self._running = True
        self._thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._thread.start()
        logger.info(f"Backup scheduler started: interval={interval_hours}h")
    
    def stop(self):
        """停止自动备份"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Backup scheduler stopped")
    
    def _run_scheduler(self):
        """运行调度器"""
        while self._running:
            try:
                logger.info("Running scheduled backup...")
                results = self.backup_manager.backup_all_agents()
                logger.info(f"Scheduled backup completed: {len(results)} agents backed up")
            except Exception as e:
                logger.error(f"Scheduled backup failed: {e}")
            
            for _ in range(self._interval_hours * 60):
                if not self._running:
                    break
                time.sleep(60)


class BackupManager:
    """备份管理器"""
    
    def __init__(self, working_dir: str):
        self.working_dir = Path(working_dir)
        self.backup_dir = self.working_dir / "memory" / "backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.export_dir = self.working_dir / "memory" / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"BackupManager initialized: {self.backup_dir}")
    
    def get_all_agent_dbs(self) -> List[Dict[str, Any]]:
        agents = []
        for ws_dir in _resolve_all_agent_workspace_dirs():
            memory_dir = ws_dir / "memory"
            if not memory_dir.exists():
                continue
            db_files = list(memory_dir.glob("human_thinking_memory_*.db"))
            for db_file in db_files:
                agent_id = db_file.stem.replace("human_thinking_memory_", "")
                stat = db_file.stat()
                agents.append({
                    "agent_id": agent_id,
                    "db_path": str(db_file),
                    "db_size_mb": round(stat.st_size / 1024 / 1024, 2),
                    "last_modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
        return agents
    
    def backup_agent(self, agent_id: str) -> BackupInfo:
        """备份单个 Agent"""
        source_db = _resolve_agent_workspace_dir(agent_id) / "memory" / f"human_thinking_memory_{agent_id}.db"
        
        if not source_db.exists():
            raise FileNotFoundError(f"Database not found: {source_db}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{agent_id}_{timestamp}"
        backup_file = self.backup_dir / f"{backup_id}.db"
        
        shutil.copy2(source_db, backup_file)
        
        checksum = self._calculate_checksum(backup_file)
        size_bytes = backup_file.stat().st_size
        
        db_version = self._get_db_version(source_db)
        
        info = BackupInfo(
            id=backup_id,
            agent_id=agent_id,
            backup_path=str(backup_file),
            size_bytes=size_bytes,
            created_at=datetime.now().isoformat(),
            db_version=db_version,
            checksum=checksum
        )
        
        self._save_backup_info(backup_id, info)
        
        logger.info(f"Backed up agent {agent_id}: {backup_file}")
        return info
    
    def backup_multiple_agents(self, agent_ids: List[str]) -> List[BackupInfo]:
        """批量备份多个 Agent"""
        results = []
        for agent_id in agent_ids:
            try:
                info = self.backup_agent(agent_id)
                results.append(info)
            except Exception as e:
                logger.error(f"Failed to backup {agent_id}: {e}")
        
        return results
    
    def backup_all_agents(self) -> List[BackupInfo]:
        """备份所有 Agent"""
        agents = self.get_all_agent_dbs()
        agent_ids = [a["agent_id"] for a in agents]
        return self.backup_multiple_agents(agent_ids)
    
    def restore_agent(self, backup_id: str, agent_id: Optional[str] = None) -> bool:
        """恢复 Agent"""
        backup_file = self._find_backup_file(backup_id)
        if not backup_file:
            raise FileNotFoundError(f"Backup not found: {backup_id}")
        
        target_agent = agent_id or backup_id.split("_")[0]
        target_db = _resolve_agent_workspace_dir(target_agent) / "memory" / f"human_thinking_memory_{target_agent}.db"
        
        shutil.copy2(backup_file, target_db)
        
        logger.info(f"Restored agent {target_agent} from {backup_id}")
        return True
    
    def list_backups(self, agent_id: Optional[str] = None) -> List[BackupInfo]:
        """列出备份"""
        if agent_id:
            pattern = f"{agent_id}_*.db"
        else:
            pattern = "*.db"
        
        backup_files = list(self.backup_dir.glob(pattern))
        
        backups = []
        for bf in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True):
            info = self._load_backup_info(bf.stem)
            if info:
                backups.append(info)
        
        return backups
    
    def delete_backup(self, backup_id: str) -> bool:
        """删除备份"""
        backup_file = self._find_backup_file(backup_id)
        if backup_file and backup_file.exists():
            backup_file.unlink()
            
            info_file = self.backup_dir / f"{backup_id}.json"
            if info_file.exists():
                info_file.unlink()
            
            logger.info(f"Deleted backup: {backup_id}")
            return True
        return False
    
    def export_to_json(self, agent_id: str) -> str:
        """导出为 JSON"""
        source_db = _resolve_agent_workspace_dir(agent_id) / "memory" / f"human_thinking_memory_{agent_id}.db"
        
        if not source_db.exists():
            raise FileNotFoundError(f"Database not found: {source_db}")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_file = self.export_dir / f"{agent_id}_{timestamp}.json"
        
        conn = sqlite3.connect(str(source_db))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM qwenpaw_memory WHERE deleted_at IS NULL")
        rows = cursor.fetchall()
        
        memories = [dict(row) for row in rows]
        
        cursor.execute("SELECT * FROM humanthinking_insights")
        insights = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT * FROM humanthinking_dream_logs")
        dream_logs = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now().isoformat(),
            "agent_id": agent_id,
            "memories": memories,
            "insights": insights,
            "dream_logs": dream_logs
        }
        
        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported agent {agent_id} to JSON: {export_file}")
        return str(export_file)
    
    def import_from_json(self, json_file: str, agent_id: str) -> int:
        """从 JSON 导入"""
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        target_db = _resolve_agent_workspace_dir(agent_id) / "memory" / f"human_thinking_memory_{agent_id}.db"
        
        conn = sqlite3.connect(str(target_db))
        cursor = conn.cursor()
        
        imported = 0
        for memory in data.get("memories", []):
            try:
                cursor.execute("""
                    INSERT INTO qwenpaw_memory (
                        agent_id, session_id, user_id, target_id, role, content,
                        memory_tier, memory_category, memory_type, importance,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory.get("agent_id"),
                    memory.get("session_id"),
                    memory.get("user_id"),
                    memory.get("target_id"),
                    memory.get("role", "assistant"),
                    memory.get("content"),
                    memory.get("memory_tier", "short_term"),
                    memory.get("memory_category", "episodic"),
                    memory.get("memory_type", "general"),
                    memory.get("importance", 3),
                    memory.get("created_at")
                ))
                imported += 1
            except Exception as e:
                logger.warning(f"Failed to import memory: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Imported {imported} memories for agent {agent_id}")
        return imported
    
    def get_backup_stats(self) -> Dict[str, Any]:
        """获取备份统计"""
        backup_files = list(self.backup_dir.glob("*.db"))
        
        total_size = sum(f.stat().st_size for f in backup_files)
        
        agent_backups = {}
        for bf in backup_files:
            agent_id = bf.stem.split("_")[0]
            if agent_id not in agent_backups:
                agent_backups[agent_id] = 0
            agent_backups[agent_id] += 1
        
        return {
            "total_backups": len(backup_files),
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "backup_count_by_agent": agent_backups,
            "backup_dir": str(self.backup_dir)
        }
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """计算文件校验和"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def _get_db_version(self, db_path: Path) -> str:
        """获取数据库版本"""
        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT db_version FROM qwenpaw_memory_version LIMIT 1")
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "unknown"
        except:
            return "unknown"
    
    def _find_backup_file(self, backup_id: str) -> Optional[Path]:
        """查找备份文件"""
        patterns = [
            f"{backup_id}.db",
            f"*.db"
        ]
        
        for pattern in patterns:
            if "*" in pattern:
                files = list(self.backup_dir.glob(pattern))
                for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True):
                    if backup_id in f.stem:
                        return f
            else:
                f = self.backup_dir / pattern
                if f.exists():
                    return f
        return None
    
    def _save_backup_info(self, backup_id: str, info: BackupInfo):
        """保存备份信息"""
        info_file = self.backup_dir / f"{backup_id}.json"
        with open(info_file, "w", encoding="utf-8") as f:
            json.dump({
                "id": info.id,
                "agent_id": info.agent_id,
                "backup_path": info.backup_path,
                "size_bytes": info.size_bytes,
                "created_at": info.created_at,
                "db_version": info.db_version,
                "checksum": info.checksum
            }, f, ensure_ascii=False, indent=2)
    
    def _load_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """加载备份信息"""
        info_file = self.backup_dir / f"{backup_id}.json"
        if not info_file.exists():
            backup_file = self._find_backup_file(backup_id)
            if backup_file:
                stat = backup_file.stat()
                return BackupInfo(
                    id=backup_id,
                    agent_id=backup_id.split("_")[0],
                    backup_path=str(backup_file),
                    size_bytes=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    db_version="unknown",
                    checksum=""
                )
            return None
        
        with open(info_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return BackupInfo(**data)


_global_backup_manager: Optional[BackupManager] = None
_global_scheduler: Optional[BackupScheduler] = None


def get_backup_manager() -> Optional[BackupManager]:
    return _global_backup_manager


def get_backup_scheduler() -> Optional[BackupScheduler]:
    return _global_scheduler


def init_backup_manager(working_dir: str, auto_backup_hours: int = 0) -> BackupManager:
    global _global_backup_manager, _global_scheduler
    _global_backup_manager = BackupManager(working_dir)
    
    if auto_backup_hours > 0:
        _global_scheduler = BackupScheduler(_global_backup_manager)
        _global_scheduler.start(auto_backup_hours)
    
    return _global_backup_manager
