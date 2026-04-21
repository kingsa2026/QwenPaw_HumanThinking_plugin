# -*- coding: utf-8 -*-
"""
记忆温度系统单元测试

测试覆盖：
- 温度计算
- 温度等级判断
- 批量计算
- 温度过滤
- 统计功能
"""

import datetime
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from HumanThinking.core.memory_temperature import (
    MemoryTemperature,
    MemoryTemperatureLevel,
    HOT_THRESHOLD,
    WARM_THRESHOLD,
    COOL_THRESHOLD
)


class TestTemperatureCalculation:
    """温度计算测试"""

    def test_hot_memory(self):
        """频繁访问的重要记忆应该是热的"""
        now = datetime.datetime.now().isoformat()
        temp = MemoryTemperature.calculate(
            access_count=10,
            search_count=5,
            importance=5,
            created_at=now,
            last_accessed_at=now
        )
        assert temp.score >= HOT_THRESHOLD
        assert temp.level == MemoryTemperatureLevel.HOT

    def test_warm_memory(self):
        """偶尔访问的记忆应该是温的"""
        past = (datetime.datetime.now() - datetime.timedelta(hours=12)).isoformat()
        temp = MemoryTemperature.calculate(
            access_count=3,
            search_count=2,
            importance=3,
            created_at=past,
            last_accessed_at=past
        )
        assert WARM_THRESHOLD <= temp.score < HOT_THRESHOLD
        assert temp.level == MemoryTemperatureLevel.WARM

    def test_cool_memory(self):
        """较少访问的记忆应该是冷的"""
        past = (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat()
        temp = MemoryTemperature.calculate(
            access_count=1,
            search_count=0,
            importance=2,
            created_at=past,
            last_accessed_at=past
        )
        assert COOL_THRESHOLD <= temp.score < WARM_THRESHOLD
        assert temp.level == MemoryTemperatureLevel.COOL

    def test_frozen_memory(self):
        """长期未访问的记忆应该是冻结的"""
        past = (datetime.datetime.now() - datetime.timedelta(days=60)).isoformat()
        temp = MemoryTemperature.calculate(
            access_count=0,
            search_count=0,
            importance=1,
            created_at=past,
            last_accessed_at=past
        )
        assert temp.score < COOL_THRESHOLD
        assert temp.level == MemoryTemperatureLevel.FROZEN

    def test_time_decay(self):
        """时间衰减应该起作用"""
        recent = (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat()
        old = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
        
        temp_recent = MemoryTemperature.calculate(
            access_count=5, search_count=2, importance=4,
            created_at=recent, last_accessed_at=recent
        )
        temp_old = MemoryTemperature.calculate(
            access_count=5, search_count=2, importance=4,
            created_at=old, last_accessed_at=old
        )
        
        assert temp_recent.time_score > temp_old.time_score
        assert temp_recent.score > temp_old.score


class TestShouldFreeze:
    """冻结判断测试"""

    def test_should_freeze_old_unimportant(self):
        """旧且不重要的记忆应该冻结"""
        past = (datetime.datetime.now() - datetime.timedelta(days=31)).isoformat()
        should_freeze = MemoryTemperature.should_freeze(
            created_at=past,
            last_accessed_at=past,
            importance=2,
            days_threshold=30,
            importance_threshold=3
        )
        assert should_freeze is True

    def test_should_not_freeze_recent(self):
        """最近访问的记忆不应冻结"""
        recent = (datetime.datetime.now() - datetime.timedelta(days=5)).isoformat()
        should_freeze = MemoryTemperature.should_freeze(
            created_at=recent,
            last_accessed_at=recent,
            importance=2,
            days_threshold=30
        )
        assert should_freeze is False

    def test_should_not_freeze_important(self):
        """重要记忆不应冻结"""
        past = (datetime.datetime.now() - datetime.timedelta(days=31)).isoformat()
        should_freeze = MemoryTemperature.should_freeze(
            created_at=past,
            last_accessed_at=past,
            importance=5,
            days_threshold=30,
            importance_threshold=3
        )
        assert should_freeze is False


class TestBatchOperations:
    """批量操作测试"""

    def test_calculate_batch(self):
        """批量计算温度"""
        now = datetime.datetime.now().isoformat()
        memories = [
            {
                "access_count": 10,
                "search_count": 5,
                "importance": 5,
                "created_at": now,
                "last_accessed_at": now
            },
            {
                "access_count": 0,
                "search_count": 0,
                "importance": 1,
                "created_at": (datetime.datetime.now() - datetime.timedelta(days=60)).isoformat(),
                "last_accessed_at": (datetime.datetime.now() - datetime.timedelta(days=60)).isoformat()
            }
        ]
        
        result = MemoryTemperature.calculate_batch(memories)
        assert "temperature" in result[0]
        assert "temperature_level" in result[0]
        assert result[0]["temperature_level"] == "hot"
        assert result[1]["temperature_level"] == "frozen"

    def test_filter_by_temperature(self):
        """按温度过滤"""
        memories = [
            {"temperature": 0.8, "temperature_level": "hot"},
            {"temperature": 0.5, "temperature_level": "warm"},
            {"temperature": 0.3, "temperature_level": "cool"},
            {"temperature": 0.1, "temperature_level": "frozen"}
        ]
        
        hot_only = MemoryTemperature.filter_by_temperature(
            memories, min_temperature=0.7
        )
        assert len(hot_only) == 1
        assert hot_only[0]["temperature_level"] == "hot"

    def test_filter_by_level(self):
        """按等级过滤"""
        memories = [
            {"temperature": 0.8, "temperature_level": "hot"},
            {"temperature": 0.5, "temperature_level": "warm"},
            {"temperature": 0.3, "temperature_level": "warm"}
        ]
        
        warm_only = MemoryTemperature.filter_by_temperature(
            memories, level=MemoryTemperatureLevel.WARM
        )
        assert len(warm_only) == 2


class TestStats:
    """统计功能测试"""

    def test_get_temperature_stats(self):
        """获取温度统计"""
        memories = [
            {"temperature": 0.8, "temperature_level": "hot"},
            {"temperature": 0.5, "temperature_level": "warm"},
            {"temperature": 0.3, "temperature_level": "cool"},
            {"temperature": 0.1, "temperature_level": "frozen"}
        ]
        
        stats = MemoryTemperature.get_temperature_stats(memories)
        assert stats["total"] == 4
        assert stats["hot"] == 1
        assert stats["warm"] == 1
        assert stats["cool"] == 1
        assert stats["frozen"] == 1
        assert 0.0 < stats["avg_temperature"] < 1.0

    def test_empty_stats(self):
        """空列表统计"""
        stats = MemoryTemperature.get_temperature_stats([])
        assert stats["total"] == 0
        assert stats["avg_temperature"] == 0.0
