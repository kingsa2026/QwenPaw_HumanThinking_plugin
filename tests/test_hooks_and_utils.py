# -*- coding: utf-8 -*-
"""
钩子模块和工具模块单元测试

测试覆盖：
- 记忆钩子（去重、重要性计算）
- HookManager
- 渠道消息解析
- 数据迁移器
- 版本管理器
"""

import asyncio
import datetime
import pytest
import sqlite3
import tempfile
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from HumanThinking.hooks.memory_hooks import (
    MemoryHook,
    HookManager,
    DeduplicationHook,
    ImportanceCalculatorHook
)
from HumanThinking.hooks.feishu_message_parser import (
    FeishuMessageParser,
    WechatMessageParser,
    parse_message
)
from HumanThinking.utils.migrator import Migration, Migrator
from HumanThinking.utils.version import VersionManager


class TestHookManager:
    """HookManager 测试"""

    @pytest.mark.asyncio
    async def test_register_and_run_hooks(self):
        """注册并运行钩子"""
        manager = HookManager()
        
        class TestHook(MemoryHook):
            async def before_store(self, memory_data):
                memory_data["processed"] = True
                return memory_data
        
        hook = TestHook()
        manager.register(hook)
        
        result = await manager.run_before_store({"content": "test"})
        assert result.get("processed") is True

    @pytest.mark.asyncio
    async def test_multiple_hooks(self):
        """多个钩子按顺序执行"""
        manager = HookManager()
        
        class AddHook(MemoryHook):
            async def before_store(self, memory_data):
                memory_data.setdefault("steps", []).append("add")
                return memory_data
        
        class ModifyHook(MemoryHook):
            async def before_store(self, memory_data):
                memory_data.setdefault("steps", []).append("modify")
                return memory_data
        
        manager.register(AddHook())
        manager.register(ModifyHook())
        
        result = await manager.run_before_store({})
        assert result["steps"] == ["add", "modify"]


class TestDeduplicationHook:
    """去重钩子测试"""

    @pytest.mark.asyncio
    async def test_prevent_duplicate(self):
        """防止重复存储"""
        hook = DeduplicationHook()
        
        data1 = {"content": "相同内容"}
        await hook.before_store(data1)
        
        data2 = {"content": "相同内容"}
        with pytest.raises(ValueError, match="Duplicate"):
            await hook.before_store(data2)

    @pytest.mark.asyncio
    async def test_allow_different_content(self):
        """允许不同内容"""
        hook = DeduplicationHook()
        
        data1 = {"content": "内容1"}
        await hook.before_store(data1)
        
        data2 = {"content": "内容2"}
        result = await hook.before_store(data2)
        assert result["content"] == "内容2"


class TestImportanceCalculatorHook:
    """重要性计算钩子测试"""

    @pytest.mark.asyncio
    async def test_calculate_importance(self):
        """自动计算重要性"""
        hook = ImportanceCalculatorHook()
        
        data = {"content": "这是一个非常重要的决定，必须认真处理"}
        result = await hook.before_store(data)
        
        assert "importance" in result
        assert result["importance"] >= 3

    @pytest.mark.asyncio
    async def test_preserve_existing_importance(self):
        """保留已有重要性"""
        hook = ImportanceCalculatorHook()
        
        data = {"content": "内容", "importance": 5}
        result = await hook.before_store(data)
        
        assert result["importance"] == 5


class TestMessageParsers:
    """消息解析器测试"""

    def test_feishu_parser(self):
        """飞书消息解析"""
        message = {
            "channel_id": "feishu",
            "user_id": "ou_xxx",
            "session_id": "feishu:s1",
            "content_parts": [{"type": "text", "content": "你好"}],
            "meta": {
                "feishu_sender_id": "ou_xxx",
                "feishu_chat_id": "oc_xxx",
                "feishu_chat_type": "group"
            }
        }
        
        result = FeishuMessageParser.parse(message)
        assert result["channel_id"] == "feishu"
        assert result["user_id"] == "ou_xxx"
        assert result["target_id"] == "oc_xxx"  # 群聊使用 chat_id
        assert result["meta"]["is_group"] is True

    def test_wechat_parser(self):
        """微信消息解析"""
        message = {
            "channel_id": "wechat",
            "user_id": "wx_user",
            "content": "你好",
            "meta": {"weixin_group_id": "group_123"}
        }
        
        result = WechatMessageParser.parse(message)
        assert result["channel_id"] == "wechat"
        assert result["target_id"] == "group_123"
        assert result["meta"]["is_group"] is True


class TestMigrator:
    """数据迁移器测试"""

    def test_create_new_database(self):
        """创建新数据库"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            migrator = Migrator(db_path)
            
            result = migrator.migrate()
            assert result["status"] == "success"

    def test_register_and_migrate(self):
        """注册并执行迁移"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            
            # 先创建数据库
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE qwenpaw_memory_version (
                    id INTEGER PRIMARY KEY,
                    db_version TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    min_compatible_version TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    upgrade_history TEXT DEFAULT '[]'
                )
            """)
            conn.execute("INSERT INTO qwenpaw_memory_version (db_version, schema_version, min_compatible_version) VALUES ('1.0.0', '1.0.0', '0.0.1')")
            conn.commit()
            conn.close()
            
            migrator = Migrator(db_path)
            migrator.register_migration(Migration(
                version="1.1.0",
                description="Add new table",
                upgrade_sql="CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY)"
            ))
            
            result = migrator.migrate()
            assert result["status"] == "success"
            assert result["migrated_count"] == 1

    def test_get_current_version(self):
        """获取当前版本"""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")
            
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE qwenpaw_memory_version (
                    id INTEGER PRIMARY KEY,
                    db_version TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    min_compatible_version TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    upgrade_history TEXT DEFAULT '[]'
                )
            """)
            conn.execute("INSERT INTO qwenpaw_memory_version (db_version, schema_version, min_compatible_version) VALUES ('1.0.0', '1.0.0', '0.0.1')")
            conn.commit()
            conn.close()
            
            migrator = Migrator(db_path)
            version = migrator.get_current_version()
            assert version == "1.0.0"


class TestVersionManager:
    """版本管理器测试"""

    def test_parse_version(self):
        """解析版本号"""
        major, minor, patch, prerelease = VersionManager.parse_version("1.0.0-beta0.1")
        assert major == 1
        assert minor == 0
        assert patch == 0
        assert prerelease == "beta0.1"

    def test_parse_version_without_prerelease(self):
        """解析无预发布标识的版本"""
        major, minor, patch, prerelease = VersionManager.parse_version("1.0.0")
        assert major == 1
        assert minor == 0
        assert patch == 0
        assert prerelease == ""

    def test_is_compatible(self):
        """检查兼容性"""
        assert VersionManager.is_compatible("1.0.0", "0.0.1") is True
        assert VersionManager.is_compatible("0.0.1", "0.0.5") is False

    def test_needs_migration(self):
        """检查是否需要迁移"""
        assert VersionManager.needs_migration(
            "1.0.0", "1.0.0",
            target_version="1.1.0"
        ) is True
        
        assert VersionManager.needs_migration(
            "1.0.0", "1.0.0",
            target_version="1.0.0",
            target_schema="1.0.0"
        ) is False

    def test_get_version_info(self):
        """获取版本信息"""
        info = VersionManager.get_version_info()
        assert "version" in info
        assert "schema_version" in info
