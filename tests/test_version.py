# -*- coding: utf-8 -*-
"""
Version 单元测试

测试范围：
- 版本常量
- VersionManager.parse_version
- VersionManager.is_compatible
- VersionManager.get_version_info
- VersionManager.needs_migration
- 边界情况和错误处理
"""

import pytest


# ==================== 版本常量测试 ====================

class TestVersionConstants:
    """测试版本常量"""
    
    def test_current_version(self):
        """测试当前版本号格式正确"""
        from utils.version import CURRENT_VERSION
        
        # 版本号应该非空
        assert CURRENT_VERSION
        assert isinstance(CURRENT_VERSION, str)
        
        # 基本格式检查（允许 pre-release 标识）
        parts = CURRENT_VERSION.split("-")
        main_version = parts[0]
        version_parts = main_version.split(".")
        
        # 至少应该有 major.minor.patch
        assert len(version_parts) >= 3
        
        # 每部分都应该是数字（允许 post1 等后缀）
        for i, part in enumerate(version_parts):
            if i < 3:
                # 前三部分必须是纯数字
                assert part.isdigit(), f"版本部分 '{part}' 不是数字"
    
    def test_current_schema_version(self):
        """测试当前 Schema 版本"""
        from utils.version import CURRENT_SCHEMA_VERSION
        
        assert CURRENT_SCHEMA_VERSION
        assert isinstance(CURRENT_SCHEMA_VERSION, str)
    
    def test_min_compatible_version(self):
        """测试最低兼容版本"""
        from utils.version import MIN_COMPATIBLE_VERSION
        
        assert MIN_COMPATIBLE_VERSION
        assert isinstance(MIN_COMPATIBLE_VERSION, str)


# ==================== 版本解析测试 ====================

class TestParseVersion:
    """测试版本解析功能"""
    
    def test_parse_standard_version(self):
        """测试标准版本号解析"""
        from utils.version import VersionManager
        
        major, minor, patch, prerelease = VersionManager.parse_version("1.2.3")
        
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert prerelease == ""
    
    def test_parse_prerelease_version(self):
        """测试预发布版本号解析"""
        from utils.version import VersionManager
        
        major, minor, patch, prerelease = VersionManager.parse_version("1.2.3-beta.1")
        
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert prerelease == "beta.1"
    
    def test_parse_complex_prerelease(self):
        """测试复杂预发布版本"""
        from utils.version import VersionManager
        
        # 注意：当前实现只支持一个横线分隔 prerelease
        # "1.1.5.post1" 会被解析为 major=1, minor=1, patch=5, prerelease=""
        # 因为 "post1" 不在主版本部分
        major, minor, patch, prerelease = VersionManager.parse_version("1.1.5.post1")
        
        assert major == 1
        assert minor == 1
        assert patch == 5
        # 当前实现不支持 post1 格式
        assert prerelease == ""
    
    def test_parse_short_version(self):
        """测试短版本号解析"""
        from utils.version import VersionManager
        
        major, minor, patch, prerelease = VersionManager.parse_version("2.1")
        
        assert major == 2
        assert minor == 1
        assert patch == 0
        assert prerelease == ""
    
    def test_parse_single_number(self):
        """测试单数字版本号"""
        from utils.version import VersionManager
        
        major, minor, patch, prerelease = VersionManager.parse_version("3")
        
        assert major == 3
        assert minor == 0
        assert patch == 0
        assert prerelease == ""
    
    def test_parse_with_multiple_dashes(self):
        """测试包含多个横线的版本号"""
        from utils.version import VersionManager
        
        major, minor, patch, prerelease = VersionManager.parse_version("1.0.0-alpha-beta")
        
        assert major == 1
        assert minor == 0
        assert patch == 0
        assert prerelease == "alpha-beta"
    
    def test_parse_empty_string(self):
        """测试空字符串版本号"""
        from utils.version import VersionManager
        
        # 空字符串应该返回 0,0,0,""
        major, minor, patch, prerelease = VersionManager.parse_version("")
        
        assert major == 0
        assert minor == 0
        assert patch == 0
        assert prerelease == ""
    
    def test_parse_zero_version(self):
        """测试零版本号"""
        from utils.version import VersionManager
        
        major, minor, patch, prerelease = VersionManager.parse_version("0.0.0")
        
        assert major == 0
        assert minor == 0
        assert patch == 0
        assert prerelease == ""
    
    def test_parse_large_numbers(self):
        """测试大数字版本号"""
        from utils.version import VersionManager
        
        major, minor, patch, prerelease = VersionManager.parse_version("999.888.777")
        
        assert major == 999
        assert minor == 888
        assert patch == 777


# ==================== 兼容性检查测试 ====================

class TestIsCompatible:
    """测试版本兼容性检查"""
    
    def test_exact_version(self):
        """测试完全匹配的版本"""
        from utils.version import VersionManager
        
        assert VersionManager.is_compatible("1.0.0", "1.0.0") is True
    
    def test_higher_major_version(self):
        """测试更高主版本"""
        from utils.version import VersionManager
        
        assert VersionManager.is_compatible("2.0.0", "1.0.0") is True
    
    def test_higher_minor_version(self):
        """测试更高次版本"""
        from utils.version import VersionManager
        
        assert VersionManager.is_compatible("1.5.0", "1.0.0") is True
    
    def test_higher_patch_version(self):
        """测试更高补丁版本"""
        from utils.version import VersionManager
        
        assert VersionManager.is_compatible("1.0.5", "1.0.0") is True
    
    def test_lower_major_version(self):
        """测试更低主版本（不兼容）"""
        from utils.version import VersionManager
        
        assert VersionManager.is_compatible("1.0.0", "2.0.0") is False
    
    def test_lower_minor_version(self):
        """测试更低次版本（不兼容）"""
        from utils.version import VersionManager
        
        assert VersionManager.is_compatible("1.0.0", "1.5.0") is False
    
    def test_lower_patch_version(self):
        """测试更低补丁版本（不兼容）"""
        from utils.version import VersionManager
        
        assert VersionManager.is_compatible("1.0.0", "1.0.5") is False
    
    def test_with_prerelease(self):
        """测试预发布版本兼容性"""
        from utils.version import VersionManager
        
        # 预发布标识不影响数字版本比较
        assert VersionManager.is_compatible("1.2.3-beta", "1.0.0") is True
        assert VersionManager.is_compatible("1.0.0-alpha", "1.0.0") is True
    
    def test_current_version_compatibility(self):
        """测试当前版本兼容性"""
        from utils.version import VersionManager, CURRENT_VERSION, MIN_COMPATIBLE_VERSION
        
        # 当前版本应该兼容最低版本
        assert VersionManager.is_compatible(CURRENT_VERSION, MIN_COMPATIBLE_VERSION) is True
    
    def test_custom_min_compatible(self):
        """测试自定义最低兼容版本"""
        from utils.version import VersionManager
        
        assert VersionManager.is_compatible("2.5.0", "2.0.0") is True
        assert VersionManager.is_compatible("2.5.0", "3.0.0") is False
    
    def test_edge_case_same_version(self):
        """测试相同版本边界情况"""
        from utils.version import VersionManager
        
        assert VersionManager.is_compatible("0.0.5", "0.0.5") is True
    
    def test_zero_version_compatibility(self):
        """测试零版本兼容性"""
        from utils.version import VersionManager
        
        assert VersionManager.is_compatible("0.0.0", "0.0.1") is False
        assert VersionManager.is_compatible("0.0.1", "0.0.0") is True


# ==================== 版本信息测试 ====================

class TestGetVersionInfo:
    """测试获取版本信息"""
    
    def test_version_info_structure(self):
        """测试版本信息结构"""
        from utils.version import VersionManager, CURRENT_VERSION, CURRENT_SCHEMA_VERSION, MIN_COMPATIBLE_VERSION
        
        info = VersionManager.get_version_info()
        
        assert isinstance(info, dict)
        assert "version" in info
        assert "schema_version" in info
        assert "min_compatible_version" in info
        assert info["version"] == CURRENT_VERSION
        assert info["schema_version"] == CURRENT_SCHEMA_VERSION
        assert info["min_compatible_version"] == MIN_COMPATIBLE_VERSION
    
    def test_version_info_types(self):
        """测试版本信息类型"""
        from utils.version import VersionManager
        
        info = VersionManager.get_version_info()
        
        assert isinstance(info["version"], str)
        assert isinstance(info["schema_version"], str)
        assert isinstance(info["min_compatible_version"], str)


# ==================== 迁移检查测试 ====================

class TestNeedsMigration:
    """测试迁移需求检查"""
    
    def test_same_version_no_migration(self):
        """测试相同版本不需要迁移"""
        from utils.version import VersionManager
        
        needs = VersionManager.needs_migration("1.0.0", "1.0.0", "1.0.0", "1.0.0")
        
        assert needs is False
    
    def test_different_version_needs_migration(self):
        """测试不同版本需要迁移"""
        from utils.version import VersionManager
        
        needs = VersionManager.needs_migration("1.0.0", "1.0.0", "2.0.0", "2.0.0")
        
        assert needs is True
    
    def test_different_schema_needs_migration(self):
        """测试不同 schema 需要迁移"""
        from utils.version import VersionManager
        
        needs = VersionManager.needs_migration("1.0.0", "1.0.0", "1.0.0", "2.0.0")
        
        assert needs is True
    
    def test_only_version_different(self):
        """测试仅版本不同"""
        from utils.version import VersionManager
        
        needs = VersionManager.needs_migration("1.0.0", "5.0.0", "1.1.0", "5.0.0")
        
        assert needs is True
    
    def test_only_schema_different(self):
        """测试仅 schema 不同"""
        from utils.version import VersionManager
        
        needs = VersionManager.needs_migration("1.1.5.post1", "4.0.0", "1.1.5.post1", "5.0.0")
        
        assert needs is True
    
    def test_current_version_check(self):
        """测试当前版本检查"""
        from utils.version import VersionManager, CURRENT_VERSION, CURRENT_SCHEMA_VERSION
        
        # 与当前版本相同不需要迁移
        needs = VersionManager.needs_migration(
            CURRENT_VERSION, CURRENT_SCHEMA_VERSION
        )
        
        assert needs is False
    
    def test_default_target_params(self):
        """测试默认目标参数"""
        from utils.version import VersionManager, CURRENT_VERSION, CURRENT_SCHEMA_VERSION
        
        # 使用默认目标版本
        needs = VersionManager.needs_migration("0.0.1", "1.0.0")
        
        # 默认目标应该是当前版本
        assert needs is True


# ==================== 综合场景测试 ====================

class TestVersionScenarios:
    """测试版本管理综合场景"""
    
    def test_version_comparison_scenarios(self):
        """测试版本比较场景"""
        from utils.version import VersionManager
        
        test_cases = [
            ("1.0.0", "1.0.0", True),
            ("2.0.0", "1.0.0", True),
            ("1.1.0", "1.0.0", True),
            ("1.0.1", "1.0.0", True),
            ("1.0.0", "2.0.0", False),
            ("1.0.0", "1.1.0", False),
            ("1.0.0", "1.0.1", False),
            ("0.0.5", "0.0.5", True),
            ("0.0.6", "0.0.5", True),
            ("0.0.4", "0.0.5", False),
            ("10.20.30", "5.10.15", True),
            ("5.10.15", "10.20.30", False),
        ]
        
        for db_version, min_version, expected in test_cases:
            result = VersionManager.is_compatible(db_version, min_version)
            assert result == expected, \
                f"is_compatible({db_version}, {min_version}) 应该返回 {expected}，但返回 {result}"
    
    def test_migration_scenarios(self):
        """测试迁移场景"""
        from utils.version import VersionManager
        
        test_cases = [
            # (db_version, db_schema, target_version, target_schema, expected)
            ("1.0.0", "1.0.0", "1.0.0", "1.0.0", False),
            ("1.0.0", "1.0.0", "2.0.0", "1.0.0", True),
            ("1.0.0", "1.0.0", "1.0.0", "2.0.0", True),
            ("2.0.0", "2.0.0", "1.0.0", "1.0.0", True),
            ("1.1.5.post1", "5.0.0", "1.1.5.post1", "5.0.0", False),
            ("1.1.4", "5.0.0", "1.1.5.post1", "5.0.0", True),
        ]
        
        for db_ver, db_schema, target_ver, target_schema, expected in test_cases:
            result = VersionManager.needs_migration(db_ver, db_schema, target_ver, target_schema)
            assert result == expected, \
                f"needs_migration({db_ver}, {db_schema}, {target_ver}, {target_schema}) 应该返回 {expected}"
    
    def test_realistic_version_flow(self):
        """测试真实版本流程"""
        from utils.version import VersionManager, CURRENT_VERSION, CURRENT_SCHEMA_VERSION
        
        # 模拟数据库版本
        db_version = "1.1.0"
        db_schema = "4.0.0"
        
        # 检查兼容性
        is_compat = VersionManager.is_compatible(db_version)
        assert isinstance(is_compat, bool)
        
        # 检查是否需要迁移
        needs_migrate = VersionManager.needs_migration(
            db_version, db_schema, CURRENT_VERSION, CURRENT_SCHEMA_VERSION
        )
        assert isinstance(needs_migrate, bool)
        
        # 获取版本信息
        info = VersionManager.get_version_info()
        assert info["version"] == CURRENT_VERSION


# ==================== 边界情况测试 ====================

class TestEdgeCases:
    """测试边界情况"""
    
    def test_parse_version_with_v_prefix(self):
        """测试带 v 前缀的版本号"""
        from utils.version import VersionManager
        
        # 注意：当前实现不支持 v 前缀，会抛出 ValueError
        with pytest.raises(ValueError):
            VersionManager.parse_version("v1.0.0")
    
    def test_parse_version_with_plus(self):
        """测试带 + 的版本号"""
        from utils.version import VersionManager
        
        # 当前实现不支持 + 号，会抛出 ValueError
        with pytest.raises(ValueError):
            VersionManager.parse_version("1.0.0+build.123")
    
    def test_parse_version_non_numeric(self):
        """测试非数字版本部分"""
        from utils.version import VersionManager
        
        with pytest.raises(ValueError):
            VersionManager.parse_version("a.b.c")
    
    def test_parse_version_with_spaces(self):
        """测试带空格的版本号"""
        from utils.version import VersionManager
        
        # 当前实现会忽略空格，将 "1. 0. 0" 解析为 "1.0.0"
        major, minor, patch, prerelease = VersionManager.parse_version("1. 0. 0")
        
        # 空格被去除后，应该能正常解析
        assert major == 1
        assert minor == 0
        assert patch == 0
    
    def test_is_compatible_with_empty_version(self):
        """测试空版本兼容性"""
        from utils.version import VersionManager
        
        # 空版本解析为 0.0.0
        result = VersionManager.is_compatible("", "0.0.1")
        assert result is False
        
        result = VersionManager.is_compatible("0.0.1", "")
        assert result is True
    
    def test_very_long_version(self):
        """测试超长版本号"""
        from utils.version import VersionManager
        
        major, minor, patch, prerelease = VersionManager.parse_version("9999.9999.9999")
        
        assert major == 9999
        assert minor == 9999
        assert patch == 9999
    
    def test_negative_version_not_allowed(self):
        """测试负版本号（当前实现会将其解析为 0）"""
        from utils.version import VersionManager
        
        # 当前实现中，"-1.0.0" 会被 split 后得到空字符串，然后解析为 0
        major, minor, patch, prerelease = VersionManager.parse_version("-1.0.0")
        
        # 横线前的空字符串被解析为 0
        assert major == 0
        assert minor == 0
        assert patch == 0
        assert prerelease == "1.0.0"


# ==================== 性能测试 ====================

class TestVersionPerformance:
    """测试版本管理性能"""
    
    def test_parse_version_performance(self):
        """测试版本解析性能"""
        from utils.version import VersionManager
        
        import time
        
        start = time.time()
        for _ in range(10000):
            VersionManager.parse_version("1.2.3-beta.1")
        elapsed = time.time() - start
        
        # 10000 次解析应该在 1 秒内完成
        assert elapsed < 1.0, f"版本解析性能测试失败: {elapsed:.2f}s"
    
    def test_is_compatible_performance(self):
        """测试兼容性检查性能"""
        from utils.version import VersionManager
        
        import time
        
        start = time.time()
        for _ in range(10000):
            VersionManager.is_compatible("1.2.3", "1.0.0")
        elapsed = time.time() - start
        
        # 10000 次检查应该在 1 秒内完成
        assert elapsed < 1.0, f"兼容性检查性能测试失败: {elapsed:.2f}s"
