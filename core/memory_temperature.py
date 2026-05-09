# -*- coding: utf-8 -*-
"""
记忆温度系统：基于认知心理学记忆模型

核心原理：
- 热记忆（HOT >= 0.7）：频繁访问，保持在缓存中
- 温记忆（WARM 0.4-0.7）：偶尔访问，正常检索
- 冷记忆（COOL 0.2-0.4）：较少访问，降低检索优先级
- 冻结记忆（FROZEN < 0.2）：长期未访问，需要解冻才能检索

温度计算：
温度 = 访问频率 × 0.3 + 重要性 × 0.4 + 时间衰减 × 0.3
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class MemoryTemperatureLevel(Enum):
    """记忆温度等级"""
    HOT = "hot"       # 热度 >= 0.7
    WARM = "warm"     # 热度 0.4-0.7
    COOL = "cool"     # 热度 0.2-0.4
    FROZEN = "frozen" # 热度 < 0.2


# 温度阈值
HOT_THRESHOLD = 0.7
WARM_THRESHOLD = 0.4
COOL_THRESHOLD = 0.2


@dataclass
class TemperatureScore:
    """温度分数"""
    score: float
    level: MemoryTemperatureLevel
    access_score: float
    importance_score: float
    time_score: float


class MemoryTemperature:
    """记忆温度计算"""

    @staticmethod
    def calculate(
        access_count: int = 0,
        search_count: int = 0,
        importance: int = 3,
        created_at: str = None,
        last_accessed_at: str = None,
    ) -> TemperatureScore:
        """
        计算记忆温度
        
        温度 = 访问频率 × 0.3 + 重要性 × 0.4 + 时间衰减 × 0.3
        
        Args:
            access_count: 访问次数
            search_count: 搜索次数
            importance: 重要性 (1-5)
            created_at: 创建时间 (ISO 格式)
            last_accessed_at: 最后访问时间 (ISO 格式)
        
        Returns:
            TemperatureScore: 温度分数和等级
        """
        now = datetime.datetime.now()
        
        # 1. 访问频率权重 (0.0 - 1.0) × 0.3
        total_accesses = access_count + search_count
        access_score = min(total_accesses / 10.0, 1.0) * 0.3
        
        # 2. 重要性权重 (0.0 - 1.0) × 0.4
        importance_score = (importance / 5.0) * 0.4
        
        # 3. 时间衰减（基于艾宾浩斯遗忘曲线）(0.0 - 1.0) × 0.3
        if created_at:
            created_time = datetime.datetime.fromisoformat(created_at)
            time_diff_hours = (now - created_time).total_seconds() / 3600
            # 艾宾浩斯遗忘曲线：R = e^(-t/S)，这里用简化公式
            time_score = (1 / (1 + time_diff_hours / 168)) * 0.3  # 168小时 = 1周
        else:
            time_score = 0.15  # 默认中间值
        
        # 总温度分数
        total_score = access_score + importance_score + time_score
        
        # 确定温度等级
        if total_score >= HOT_THRESHOLD:
            level = MemoryTemperatureLevel.HOT
        elif total_score >= WARM_THRESHOLD:
            level = MemoryTemperatureLevel.WARM
        elif total_score >= COOL_THRESHOLD:
            level = MemoryTemperatureLevel.COOL
        else:
            level = MemoryTemperatureLevel.FROZEN
        
        return TemperatureScore(
            score=round(total_score, 4),
            level=level,
            access_score=round(access_score, 4),
            importance_score=round(importance_score, 4),
            time_score=round(time_score, 4)
        )

    @staticmethod
    def should_freeze(
        created_at: str,
        last_accessed_at: str,
        importance: int = 3,
        days_threshold: int = 30,
        importance_threshold: int = 3
    ) -> bool:
        """
        判断记忆是否应该冻结
        
        Args:
            created_at: 创建时间
            last_accessed_at: 最后访问时间
            importance: 重要性
            days_threshold: 天数阈值
            importance_threshold: 重要性阈值
        
        Returns:
            是否应该冻结
        """
        if not created_at or not last_accessed_at:
            return False
        
        now = datetime.datetime.now()
        last_access = datetime.datetime.fromisoformat(last_accessed_at)
        days_since_access = (now - last_access).total_seconds() / 86400
        
        # 冻结条件：
        # 1. 超过阈值天数未访问
        # 2. 重要性低于阈值
        return (
            days_since_access >= days_threshold and
            importance < importance_threshold
        )

    @staticmethod
    def calculate_batch(memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量计算记忆温度
        
        Args:
            memories: 记忆列表
        
        Returns:
            带温度分数的记忆列表
        """
        for memory in memories:
            temp = MemoryTemperature.calculate(
                access_count=memory.get("access_count", 0),
                search_count=memory.get("search_count", 0),
                importance=memory.get("importance", 3),
                created_at=memory.get("created_at"),
                last_accessed_at=memory.get("last_accessed_at"),
            )
            memory["temperature"] = temp.score
            memory["temperature_level"] = temp.level.value
        
        return memories

    @staticmethod
    def filter_by_temperature(
        memories: List[Dict[str, Any]],
        min_temperature: float = 0.0,
        max_temperature: float = 1.0,
        level: MemoryTemperatureLevel = None
    ) -> List[Dict[str, Any]]:
        """
        按温度过滤记忆
        
        Args:
            memories: 记忆列表
            min_temperature: 最低温度
            max_temperature: 最高温度
            level: 温度等级过滤
        
        Returns:
            过滤后的记忆列表
        """
        result = []
        for memory in memories:
            temp = memory.get("temperature", 0.5)
            if min_temperature <= temp <= max_temperature:
                if level is None or memory.get("temperature_level") == level.value:
                    result.append(memory)
        return result

    @staticmethod
    def get_temperature_stats(memories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取温度统计信息
        
        Args:
            memories: 记忆列表
        
        Returns:
            温度统计
        """
        stats = {
            "total": len(memories),
            "hot": 0,
            "warm": 0,
            "cool": 0,
            "frozen": 0,
            "avg_temperature": 0.0,
        }
        
        if not memories:
            return stats
        
        total_temp = 0.0
        for memory in memories:
            level = memory.get("temperature_level", "warm")
            temp = memory.get("temperature", 0.5)
            total_temp += temp
            
            if level == "hot":
                stats["hot"] += 1
            elif level == "warm":
                stats["warm"] += 1
            elif level == "cool":
                stats["cool"] += 1
            else:
                stats["frozen"] += 1
        
        stats["avg_temperature"] = round(total_temp / len(memories), 4)
        return stats
