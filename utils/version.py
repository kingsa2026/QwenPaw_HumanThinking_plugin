# -*- coding: utf-8 -*-
"""
版本管理器：管理 HumanThinking 版本信息和兼容性检查
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# 当前版本
CURRENT_VERSION = "1.1.5.post1"
CURRENT_SCHEMA_VERSION = "5.0.0"
MIN_COMPATIBLE_VERSION = "0.0.5"


class VersionManager:
    """版本管理器"""

    @staticmethod
    def parse_version(version_str: str) -> Tuple[int, int, int, str]:
        """
        解析版本号字符串
        
        Args:
            version_str: 版本号字符串，如 "1.0.0-beta0.1"
        
        Returns:
            (major, minor, patch, prerelease)
        """
        # 分离预发布标识
        if "-" in version_str:
            main_part, prerelease = version_str.split("-", 1)
        else:
            main_part = version_str
            prerelease = ""
        
        parts = main_part.split(".")
        major = int(parts[0]) if len(parts) > 0 and parts[0] else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1] else 0
        patch = int(parts[2]) if len(parts) > 2 and parts[2] else 0
        
        return (major, minor, patch, prerelease)

    @staticmethod
    def is_compatible(
        db_version: str,
        min_compatible: str = MIN_COMPATIBLE_VERSION
    ) -> bool:
        """
        检查版本兼容性
        
        Args:
            db_version: 数据库版本
            min_compatible: 最低兼容版本
        
        Returns:
            是否兼容
        """
        db_parsed = VersionManager.parse_version(db_version)
        min_parsed = VersionManager.parse_version(min_compatible)
        
        # 比较主版本、次版本、补丁版本
        return (
            db_parsed[0] >= min_parsed[0] and
            db_parsed[1] >= min_parsed[1] and
            db_parsed[2] >= min_parsed[2]
        )

    @staticmethod
    def get_version_info() -> Dict[str, str]:
        """获取版本信息"""
        return {
            "version": CURRENT_VERSION,
            "schema_version": CURRENT_SCHEMA_VERSION,
            "min_compatible_version": MIN_COMPATIBLE_VERSION,
        }

    @staticmethod
    def needs_migration(
        db_version: str,
        db_schema_version: str,
        target_version: str = CURRENT_VERSION,
        target_schema: str = CURRENT_SCHEMA_VERSION
    ) -> bool:
        """
        检查是否需要迁移
        
        Args:
            db_version: 数据库版本
            db_schema_version: 数据库 schema 版本
            target_version: 目标版本
            target_schema: 目标 schema 版本
        
        Returns:
            是否需要迁移
        """
        return (
            db_version != target_version or
            db_schema_version != target_schema
        )
