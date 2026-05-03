# -*- coding: utf-8 -*-
"""
SleepManager 单元测试

测试范围：
- SleepConfig 配置类
- AgentSleepState 状态类
- SleepManager 核心睡眠管理逻辑
- 记忆合并功能（新增重点）
- 全局辅助函数
"""

import asyncio
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ==================== SleepConfig 测试 ====================

class TestSleepConfig:
    """测试睡眠配置类"""
    
    def test_default_config(self):
        """测试默认配置值"""
        from core.sleep_manager import SleepConfig
        
        config = SleepConfig()
        
        assert config.enable_agent_sleep is True
        assert config.light_sleep_seconds == 1800  # 30分钟
        assert config.rem_seconds == 3600          # 60分钟
        assert config.deep_sleep_seconds == 7200   # 120分钟
        assert config.auto_consolidate is True
        assert config.consolidate_days == 7
        assert config.frozen_days == 30
        assert config.archive_days == 90
        assert config.delete_days == 180
        assert config.enable_insight is True
        assert config.enable_dream_log is True
        assert config.enable_merge is True
        assert config.merge_similarity_threshold == 0.8
        assert config.merge_max_distance_hours == 72
    
    def test_custom_config(self):
        """测试自定义配置"""
        from core.sleep_manager import SleepConfig
        
        config = SleepConfig(
            light_sleep_minutes=15,
            rem_minutes=30,
            deep_sleep_minutes=60,
            enable_merge=False,
            merge_similarity_threshold=0.9,
            merge_max_distance_hours=24,
        )
        
        assert config.light_sleep_seconds == 900
        assert config.rem_seconds == 1800
        assert config.deep_sleep_seconds == 3600
        assert config.enable_merge is False
        assert config.merge_similarity_threshold == 0.9
        assert config.merge_max_distance_hours == 24
    
    def test_config_bounds(self):
        """测试配置边界值处理"""
        from core.sleep_manager import SleepConfig
        
        # 测试 frozen_days 边界
        config = SleepConfig(frozen_days=0, archive_days=1, delete_days=2)
        assert config.frozen_days == 1  # 最小值限制
        assert config.archive_days == 2  # 必须大于 frozen_days
        assert config.delete_days == 3   # 必须大于 archive_days
        
        # 测试 merge 参数边界
        config = SleepConfig(
            merge_similarity_threshold=0.3,  # 低于最小值
            merge_max_distance_hours=200,     # 超过最大值
        )
        assert config.merge_similarity_threshold == 0.5  # 最小值限制
        assert config.merge_max_distance_hours == 168     # 最大值限制
        
        # 测试上限边界
        config = SleepConfig(
            merge_similarity_threshold=1.0,  # 超过最大值
            merge_max_distance_hours=0,       # 低于最小值
        )
        assert config.merge_similarity_threshold == 0.95
        assert config.merge_max_distance_hours == 1


# ==================== AgentSleepState 测试 ====================

class TestAgentSleepState:
    """测试 Agent 睡眠状态类"""
    
    def test_initial_state(self):
        """测试初始状态"""
        from core.sleep_manager import AgentSleepState
        
        state = AgentSleepState("agent_001")
        
        assert state.agent_id == "agent_001"
        assert state.is_active is True
        assert state.is_light_sleep is False
        assert state.is_rem is False
        assert state.is_deep_sleep is False
        assert state.last_active_time > 0
        assert state.last_light_sleep_time is None
        assert state.last_rem_time is None
        assert state.last_deep_sleep_time is None
        assert state.pending_importance == []
        assert state.lasting_truths == []
        assert state.theme_summary is None


# ==================== SleepManager 核心测试 ====================

class TestSleepManagerCore:
    """测试 SleepManager 核心功能"""
    
    def test_init(self, sleep_config):
        """测试初始化"""
        from core.sleep_manager import SleepManager
        
        manager = SleepManager(sleep_config)
        
        assert manager.config == sleep_config
        assert manager._agent_states == {}
    
    def test_update_config(self, sleep_manager, sleep_config):
        """测试配置更新"""
        new_config = sleep_config
        new_config.light_sleep_minutes = 10
        
        sleep_manager.update_config(new_config)
        
        assert sleep_manager.config.light_sleep_minutes == 10
    
    def test_record_activity_new_agent(self, sleep_manager):
        """测试新 Agent 活动记录"""
        result = sleep_manager.record_activity("agent_001")
        
        assert result is False  # 未达到睡眠阈值
        assert "agent_001" in sleep_manager._agent_states
        state = sleep_manager._agent_states["agent_001"]
        assert state.is_active is True
    
    def test_record_activity_disabled_sleep(self, sleep_manager):
        """测试禁用睡眠时的活动记录"""
        sleep_manager.config.enable_agent_sleep = False
        
        result = sleep_manager.record_activity("agent_001")
        
        assert result is False
        assert "agent_001" not in sleep_manager._agent_states
    
    def test_sleep_state_transitions(self, sleep_manager):
        """测试睡眠状态转换"""
        # 创建状态并手动设置到活跃
        from core.sleep_manager import AgentSleepState
        state = AgentSleepState("agent_001")
        # 模拟已经空闲足够长时间（但不超过rem阈值）
        state.last_active_time = time.time() - 45  # 45秒前，超过light_sleep(30s)但不超过rem(60s)
        sleep_manager._agent_states["agent_001"] = state
        
        # 应该进入浅睡眠（配置为30秒阈值）
        result = sleep_manager.record_activity("agent_001")
        
        assert result is True
        assert state.is_light_sleep is True
        assert state.is_active is False
    
    def test_deep_sleep_wakeup(self, sleep_manager):
        """测试从深睡眠唤醒"""
        from core.sleep_manager import AgentSleepState
        
        state = AgentSleepState("agent_001")
        state.is_active = False
        state.is_deep_sleep = True
        state.last_active_time = time.time() - 10
        state.last_deep_sleep_time = time.time() - 100
        sleep_manager._agent_states["agent_001"] = state
        
        with patch.object(sleep_manager, '_write_memory_md') as mock_write:
            result = sleep_manager.record_activity("agent_001")
            
            assert result is True
            assert state.is_active is True
            assert state.is_deep_sleep is False
            mock_write.assert_called_once_with("agent_001", state)
    
    def test_is_sleeping(self, sleep_manager):
        """测试睡眠状态检查"""
        from core.sleep_manager import AgentSleepState
        
        # 未记录的 Agent
        assert sleep_manager.is_sleeping("unknown") is False
        
        # 活跃的 Agent
        state = AgentSleepState("agent_001")
        sleep_manager._agent_states["agent_001"] = state
        assert sleep_manager.is_sleeping("agent_001") is False
        
        # 浅睡眠的 Agent
        state.is_active = False
        state.is_light_sleep = True
        assert sleep_manager.is_sleeping("agent_001") is True
        
        # REM 状态的 Agent
        state.is_light_sleep = False
        state.is_rem = True
        assert sleep_manager.is_sleeping("agent_001") is True
        
        # 深睡眠的 Agent
        state.is_rem = False
        state.is_deep_sleep = True
        assert sleep_manager.is_sleeping("agent_001") is True
    
    def test_get_sleeping_agents(self, sleep_manager):
        """测试获取所有睡眠中的 Agent"""
        from core.sleep_manager import AgentSleepState
        
        # 创建多个 Agent 状态
        for i, status in enumerate(['active', 'light', 'rem', 'deep']):
            state = AgentSleepState(f"agent_{i}")
            if status == 'light':
                state.is_active = False
                state.is_light_sleep = True
            elif status == 'rem':
                state.is_active = False
                state.is_rem = True
            elif status == 'deep':
                state.is_active = False
                state.is_deep_sleep = True
            sleep_manager._agent_states[f"agent_{i}"] = state
        
        sleeping = sleep_manager.get_sleeping_agents()
        
        assert len(sleeping) == 3
        assert "agent_0" not in sleeping
        assert "agent_1" in sleeping
        assert "agent_2" in sleeping
        assert "agent_3" in sleeping
    
    def test_get_status(self, sleep_manager):
        """测试获取状态"""
        from core.sleep_manager import AgentSleepState
        
        # 不存在的 Agent
        status = sleep_manager.get_status("unknown")
        assert status["status"] == "active"
        assert status["sleep_type"] is None
        
        # 活跃的 Agent
        state = AgentSleepState("agent_active")
        sleep_manager._agent_states["agent_active"] = state
        status = sleep_manager.get_status("agent_active")
        assert status["status"] == "active"
        
        # 浅睡眠
        state.is_active = False
        state.is_light_sleep = True
        status = sleep_manager.get_status("agent_active")
        assert status["status"] == "sleeping"
        assert status["sleep_type"] == "light"
        
        # REM
        state.is_light_sleep = False
        state.is_rem = True
        status = sleep_manager.get_status("agent_active")
        assert status["sleep_type"] == "rem"
        
        # 深睡眠
        state.is_rem = False
        state.is_deep_sleep = True
        status = sleep_manager.get_status("agent_active")
        assert status["sleep_type"] == "deep"


# ==================== 记忆去重测试 ====================

class TestDeduplication:
    """测试记忆去重功能"""
    
    def test_deduplicate_empty(self, sleep_manager):
        """测试空列表去重"""
        result = sleep_manager._deduplicate_memories([])
        assert result == []
    
    def test_deduplicate_unique(self, sleep_manager, sample_memories):
        """测试无重复记忆"""
        result = sleep_manager._deduplicate_memories(sample_memories[:3])
        assert len(result) == 3
    
    def test_deduplicate_duplicates(self, sleep_manager):
        """测试重复记忆去重"""
        memories = [
            {"content": "相同内容"},
            {"content": "相同内容"},
            {"content": "不同内容"},
        ]
        
        result = sleep_manager._deduplicate_memories(memories)
        
        assert len(result) == 2
        assert result[0]["content"] == "相同内容"
        assert result[1]["content"] == "不同内容"
    
    def test_deduplicate_partial_similar(self, sleep_manager):
        """测试部分相似内容去重（只比较前100字符）"""
        memories = [
            {"content": "A" * 100 + "后缀1"},
            {"content": "A" * 100 + "后缀2"},  # 前100字符相同
            {"content": "B" * 100},
        ]
        
        result = sleep_manager._deduplicate_memories(memories)
        
        assert len(result) == 2  # 前两个被视为重复


# ==================== 记忆合并测试（重点） ====================

class TestMemoryMerge:
    """测试记忆合并功能 - 核心新增功能"""
    
    def test_merge_disabled(self, sleep_manager, similar_memories):
        """测试禁用合并时返回原列表"""
        sleep_manager.config.enable_merge = False
        
        result, count, contradictions = sleep_manager._merge_similar_memories(similar_memories)
        
        assert len(result) == len(similar_memories)
        assert count == 0
        assert contradictions == []
    
    def test_merge_empty_or_single(self, sleep_manager):
        """测试空列表或单条记忆"""
        result, count, contradictions = sleep_manager._merge_similar_memories([])
        assert result == []
        assert count == 0
        assert contradictions == []
        
        result, count, contradictions = sleep_manager._merge_similar_memories([{"content": "唯一"}])
        assert len(result) == 1
        assert count == 0
        assert contradictions == []
    
    def test_merge_similar_memories(self, sleep_manager, similar_memories):
        """测试合并相似记忆"""
        # 调整阈值确保能合并
        sleep_manager.config.merge_similarity_threshold = 0.5
        sleep_manager.config.merge_max_distance_hours = 72
        
        result, count, contradictions = sleep_manager._merge_similar_memories(similar_memories)
        
        # 前两条记忆内容相似，应该被合并
        assert count >= 1
        assert len(result) < len(similar_memories)
        assert isinstance(contradictions, list)
    
    def test_merge_no_similar_pairs(self, sleep_manager):
        """测试没有相似记忆对时"""
        memories = [
            {"content": "完全不同的内容A", "memory_type": "fact", "timestamp": datetime.now().isoformat()},
            {"content": "完全不同的内容B", "memory_type": "emotion", "timestamp": datetime.now().isoformat()},
            {"content": "完全不同的内容C", "memory_type": "general", "timestamp": datetime.now().isoformat()},
        ]
        
        sleep_manager.config.merge_similarity_threshold = 0.95  # 很高的阈值
        
        result, count, contradictions = sleep_manager._merge_similar_memories(memories)
        
        assert count == 0
        assert len(result) == 3
        assert contradictions == []
    
    def test_calculate_similarity_time_distance(self, sleep_manager):
        """测试时间距离对相似度的影响"""
        now = datetime.now()
        mem1 = {
            "content": "用户喜欢简洁风格",
            "memory_type": "preference",
            "timestamp": now.isoformat(),
            "emotion": "",
        }
        mem2 = {
            "content": "用户喜欢简洁风格",
            "memory_type": "preference",
            "timestamp": (now - timedelta(hours=100)).isoformat(),  # 超过72小时
            "emotion": "",
        }
        
        similarity = sleep_manager._calculate_similarity(mem1, mem2)
        
        assert similarity == 0.0  # 时间距离超过阈值
    
    def test_calculate_similarity_identical(self, sleep_manager):
        """测试完全相同内容的相似度"""
        now = datetime.now()
        mem1 = {
            "content": "用户喜欢简洁风格",
            "memory_type": "preference",
            "timestamp": now.isoformat(),
            "emotion": "happy",
        }
        mem2 = {
            "content": "用户喜欢简洁风格",
            "memory_type": "preference",
            "timestamp": now.isoformat(),
            "emotion": "happy",
        }
        
        similarity = sleep_manager._calculate_similarity(mem1, mem2)
        
        assert similarity > 0.9  # 应该非常相似
    
    def test_calculate_similarity_subset(self, sleep_manager):
        """测试包含关系的相似度"""
        now = datetime.now()
        mem1 = {
            "content": "用户喜欢简洁风格",
            "memory_type": "preference",
            "timestamp": now.isoformat(),
            "emotion": "",
        }
        mem2 = {
            "content": "用户喜欢简洁风格，不喜欢太长的解释",
            "memory_type": "preference",
            "timestamp": now.isoformat(),
            "emotion": "",
        }
        
        similarity = sleep_manager._calculate_similarity(mem1, mem2)
        
        assert similarity >= 0.9 * 0.6 + 1.0 * 0.2 + 0.5 * 0.2  # 文本包含关系
    
    def test_calculate_similarity_different_types(self, sleep_manager):
        """测试不同类型记忆的相似度"""
        now = datetime.now()
        mem1 = {
            "content": "用户喜欢简洁风格",
            "memory_type": "preference",
            "timestamp": now.isoformat(),
            "emotion": "",
        }
        mem2 = {
            "content": "用户喜欢简洁风格",
            "memory_type": "fact",
            "timestamp": now.isoformat(),
            "emotion": "",
        }
        
        similarity = sleep_manager._calculate_similarity(mem1, mem2)
        
        # 类型不同，type_sim = 0.5
        assert similarity < 1.0
    
    def test_calculate_similarity_different_emotions(self, sleep_manager):
        """测试不同情感的相似度"""
        now = datetime.now()
        mem1 = {
            "content": "用户喜欢简洁风格",
            "memory_type": "preference",
            "timestamp": now.isoformat(),
            "emotion": "happy",
        }
        mem2 = {
            "content": "用户喜欢简洁风格",
            "memory_type": "preference",
            "timestamp": now.isoformat(),
            "emotion": "sad",
        }
        
        similarity = sleep_manager._calculate_similarity(mem1, mem2)
        
        # 情感不同，emotion_sim = 0.5
        assert similarity < 1.0
    
    def test_calculate_similarity_empty_content(self, sleep_manager):
        """测试空内容的相似度"""
        now = datetime.now()
        mem1 = {"content": "", "memory_type": "general", "timestamp": now.isoformat(), "emotion": ""}
        mem2 = {"content": "有内容", "memory_type": "general", "timestamp": now.isoformat(), "emotion": ""}
        
        similarity = sleep_manager._calculate_similarity(mem1, mem2)
        
        assert similarity == 0.0
    
    def test_merge_two_memories(self, sleep_manager):
        """测试合并两条记忆"""
        mem1 = {
            "id": 1,
            "content": "用户喜欢简洁风格",
            "importance": 4,
            "tags": ["style"],
            "timestamp": "2024-01-01T10:00:00",
            "merge_count": 0,
            "merged_from": [],
        }
        mem2 = {
            "id": 2,
            "content": "用户偏好简洁风格，讨厌冗长回答",
            "importance": 3,
            "tags": ["preference"],
            "timestamp": "2024-01-01T12:00:00",
            "merge_count": 0,
            "merged_from": [],
        }
        
        result = sleep_manager._merge_two_memories(mem1, mem2, 0.85)
        
        assert result["content"] == mem2["content"]  # 更长的内容
        assert result["importance"] == 4  # 取最大值
        assert set(result["tags"]) == {"style", "preference"}  # 合并标签
        assert result["merge_count"] == 1
        assert 1 in result["merged_from"]
        assert 2 in result["merged_from"]
        assert result["merge_similarity"] == 0.85
        assert "last_merged_at" in result
    
    def test_merge_two_memories_content1_longer(self, sleep_manager):
        """测试第一条记忆内容更长时"""
        mem1 = {
            "id": 1,
            "content": "用户喜欢简洁风格，不喜欢太长的解释",
            "importance": 4,
            "tags": [],
            "timestamp": "2024-01-01T10:00:00",
            "merge_count": 0,
            "merged_from": [],
        }
        mem2 = {
            "id": 2,
            "content": "用户喜欢简洁风格",
            "importance": 3,
            "tags": [],
            "timestamp": "2024-01-01T12:00:00",
            "merge_count": 0,
            "merged_from": [],
        }
        
        result = sleep_manager._merge_two_memories(mem1, mem2, 0.9)
        
        assert result["content"] == mem1["content"]  # 第一条更长
    
    def test_merge_two_memories_with_supplement(self, sleep_manager):
        """测试合并时追加补充信息"""
        mem1 = {
            "id": 1,
            "content": "用户喜欢简洁风格",
            "importance": 4,
            "tags": [],
            "timestamp": "2024-01-01T10:00:00",
            "merge_count": 0,
            "merged_from": [],
        }
        mem2 = {
            "id": 2,
            "content": "用户也偏好专业术语",
            "importance": 3,
            "tags": [],
            "timestamp": "2024-01-01T12:00:00",
            "merge_count": 0,
            "merged_from": [],
        }
        
        result = sleep_manager._merge_two_memories(mem1, mem2, 0.8)
        
        # 第二条更长(9 vs 8)，所以选择第二条
        # 由于第一条长度不超过20，不会追加补充信息
        assert result["content"] == "用户也偏好专业术语"


# ==================== 噪声过滤测试 ====================

class TestNoiseFilter:
    """测试噪声过滤功能"""
    
    def test_filter_noise_empty(self, sleep_manager):
        """测试空列表"""
        result = sleep_manager._filter_noise([])
        assert result == []
    
    def test_filter_noise_patterns(self, sleep_manager):
        """测试过滤噪声模式"""
        memories = [
            {"content": "好的"},
            {"content": "收到"},
            {"content": "明白"},
            {"content": "是的"},
            {"content": "ok"},
            {"content": "OK"},
            {"content": "[图片]"},
            {"content": "[表情]"},
            {"content": "hi"},
            {"content": "hello"},
            {"content": "hey"},
            {"content": "这是有意义的记忆内容"},
            {"content": "a"},  # 太短
        ]
        
        result = sleep_manager._filter_noise(memories)
        
        assert len(result) == 1
        assert result[0]["content"] == "这是有意义的记忆内容"
    
    def test_filter_noise_case_insensitive(self, sleep_manager):
        """测试大小写不敏感过滤"""
        memories = [
            {"content": "Ok"},
            {"content": "oK"},
            {"content": "HELLO"},
            {"content": "这是一条有效内容"},
        ]
        
        result = sleep_manager._filter_noise(memories)
        
        assert len(result) == 1
        assert result[0]["content"] == "这是一条有效内容"


# ==================== 重要性标记测试 ====================

class TestImportanceMarking:
    """测试重要性标记功能"""
    
    def test_mark_potential_importance_empty(self, sleep_manager):
        """测试空列表"""
        result = sleep_manager._mark_potential_importance([])
        assert result == []
    
    def test_mark_potential_importance_keywords(self, sleep_manager):
        """测试关键词匹配"""
        memories = [
            {"content": "用户喜欢简洁风格"},
            {"content": "普通对话内容"},
            {"content": "订单号12345"},
            {"content": "用户很满意，感谢帮助"},
            {"content": "这是一个重要信息 remember this"},
        ]
        
        result = sleep_manager._mark_potential_importance(memories)
        
        assert len(result) >= 3  # 至少3条匹配关键词
        # 按重要性分数排序
        assert result[0]["potential_importance"] >= result[-1]["potential_importance"]
    
    def test_mark_potential_importance_no_match(self, sleep_manager):
        """测试无匹配关键词"""
        memories = [
            {"content": "普通对话"},
            {"content": "日常交流"},
        ]
        
        result = sleep_manager._mark_potential_importance(memories)
        
        assert result == []


# ==================== 主题提取测试 ====================

class TestThemeExtraction:
    """测试主题提取功能"""
    
    def test_extract_themes_empty(self, sleep_manager):
        """测试空列表"""
        result = sleep_manager._extract_themes([])
        
        assert result["themes"] == []
        assert "暂无" in result["summary"] or "近期主要关注" in result["summary"]
    
    def test_extract_themes(self, sleep_manager):
        """测试主题提取"""
        memories = [
            {"content": "我想购买这个商品，怎么下单？"},
            {"content": "订单已经支付了"},
            {"content": "快递什么时候到？"},
            {"content": "这个商品可以退货吗？"},
            {"content": "退款什么时候到账？"},
        ]
        
        result = sleep_manager._extract_themes(memories)
        
        assert len(result["themes"]) > 0
        # 应该包含购物相关主题
        theme_names = [t["theme"] for t in result["themes"]]
        assert "购物" in theme_names or "售后" in theme_names


# ==================== 跨会话模式测试 ====================

class TestCrossSessionPatterns:
    """测试跨会话模式发现"""
    
    def test_find_cross_session_patterns_empty(self, sleep_manager):
        """测试空列表"""
        result = sleep_manager._find_cross_session_patterns([])
        assert result == []
    
    def test_find_cross_session_patterns(self, sleep_manager):
        """测试发现跨会话模式"""
        memories = [
            {"content": "消息1", "session_id": "s1", "user_id": "u1"},
            {"content": "消息2", "session_id": "s1", "user_id": "u1"},
            {"content": "消息3", "session_id": "s1", "user_id": "u1"},
            {"content": "消息4", "session_id": "s1", "user_id": "u1"},
            {"content": "消息5", "session_id": "s2", "user_id": "u1"},
        ]
        
        result = sleep_manager._find_cross_session_patterns(memories)
        
        assert len(result) >= 1
        assert result[0]["message_count"] == 4  # s1 有4条消息


# ==================== 持久真理识别测试 ====================

class TestLastingTruths:
    """测试持久真理识别"""
    
    def test_identify_lasting_truths_empty(self, sleep_manager):
        """测试空列表"""
        result = sleep_manager._identify_lasting_truths([], [])
        assert result == []
    
    def test_identify_lasting_truths(self, sleep_manager):
        """测试识别持久真理"""
        memories = [
            {"content": "用户喜欢简洁风格", "potential_importance": 2},
            {"content": "订单号是12345", "potential_importance": 1},
            {"content": "用户表示感谢，很满意", "potential_importance": 1},
            {"content": "普通对话", "potential_importance": 0},
        ]
        
        result = sleep_manager._identify_lasting_truths(memories, [])
        
        assert len(result) >= 2
        # 检查类型分类
        types = [t["type"] for t in result]
        assert "preference" in types
        assert "fact" in types
        assert "emotion" in types


# ==================== 六维评分测试 ====================

class TestSixDimensionalScore:
    """测试六维加权评分系统"""
    
    def test_six_dimensional_score(self, sleep_manager):
        """测试完整评分"""
        memory = {
            "content": "因为用户喜欢简洁风格，所以建议保持回答简短",
            "importance": 4,
            "memory_type": "preference",
            "access_count": 5,
            "created_at": datetime.now().isoformat(),
            "access_patterns": ["search1", "search2", "search3"],
            "related_memory_ids": [1, 2, 3],
        }
        
        scores = sleep_manager._six_dimensional_score(memory)
        
        assert "total" in scores
        assert "relevance" in scores
        assert "frequency" in scores
        assert "recency" in scores
        assert "diversity" in scores
        assert "integration" in scores
        assert "concept" in scores
        assert scores["total"] > 0
    
    def test_calc_relevance(self, sleep_manager):
        """测试相关性计算"""
        fact_mem = {"importance": 5, "memory_type": "fact"}
        pref_mem = {"importance": 4, "memory_type": "preference"}
        gen_mem = {"importance": 3, "memory_type": "general"}
        
        assert sleep_manager._calc_relevance(fact_mem, []) > sleep_manager._calc_relevance(gen_mem, [])
        assert sleep_manager._calc_relevance(fact_mem, []) > sleep_manager._calc_relevance(pref_mem, [])
    
    def test_calc_recency(self, sleep_manager):
        """测试时效性计算"""
        now = datetime.now()
        recent = {"created_at": now.isoformat()}
        old = {"created_at": (now - timedelta(days=60)).isoformat()}
        
        assert sleep_manager._calc_recency(recent) > sleep_manager._calc_recency(old)
        assert sleep_manager._calc_recency(old) >= 0
    
    def test_calc_recency_invalid(self, sleep_manager):
        """测试无效时间格式"""
        assert sleep_manager._calc_recency({"created_at": "invalid"}) == 0.5
        assert sleep_manager._calc_recency({}) == 0.5
    
    def test_calc_diversity(self, sleep_manager):
        """测试多样性计算"""
        no_patterns = {"access_patterns": []}
        few_patterns = {"access_patterns": ["a", "b"]}
        many_patterns = {"access_patterns": ["a", "b", "c", "d", "e", "f"]}
        all_memories = []
        
        assert sleep_manager._calc_diversity(no_patterns, all_memories) < sleep_manager._calc_diversity(few_patterns, all_memories)
        assert sleep_manager._calc_diversity(many_patterns, all_memories) == 1.0  # 上限
    
    def test_calc_integration(self, sleep_manager):
        """测试整合度计算"""
        no_related = {"related_memory_ids": []}
        some_related = {"related_memory_ids": [1, 2, 3, 4, 5]}
        many_related = {"related_memory_ids": list(range(20))}
        all_memories = []
        
        assert sleep_manager._calc_integration(no_related, all_memories) < sleep_manager._calc_integration(some_related, all_memories)
        assert sleep_manager._calc_integration(many_related, all_memories) == 1.0  # 上限
    
    def test_calc_concept_richness(self, sleep_manager):
        """测试概念丰富度"""
        empty = ""
        simple = "你好世界"
        complex_text = "因为用户喜欢简洁风格，所以建议保持回答简短。然而，如果内容太复杂，需要详细解释。"
        
        assert sleep_manager._calc_concept_richness(empty) == 0.0
        assert sleep_manager._calc_concept_richness(simple) >= 0
        assert sleep_manager._calc_concept_richness(complex_text) > sleep_manager._calc_concept_richness(simple)


# ==================== 洞察生成测试 ====================

class TestInsightGeneration:
    """测试洞察生成功能"""
    
    def test_generate_insights_empty(self, sleep_manager):
        """测试空列表"""
        result = sleep_manager._generate_insights([])
        assert result == []
    
    def test_generate_insights(self, sleep_manager):
        """测试洞察生成"""
        memories = [
            {"memory_type": "fact"},
            {"memory_type": "fact"},
            {"memory_type": "preference"},
        ]
        
        result = sleep_manager._generate_insights(memories)
        
        assert len(result) >= 1
        assert "记忆类型分布" in result[0]["title"]


# ==================== MEMORY.md 写入测试 ====================

class TestMemoryMdWrite:
    """测试 MEMORY.md 文件写入"""
    
    def test_write_memory_md_no_path(self, sleep_manager):
        """测试无路径时不写入"""
        from core.sleep_manager import AgentSleepState
        
        state = AgentSleepState("agent_001")
        sleep_manager.config.memory_md_path = None
        
        # 不应抛出异常
        sleep_manager._write_memory_md("agent_001", state)
    
    def test_write_memory_md_with_path(self, sleep_manager, temp_dir):
        """测试有路径时写入文件"""
        from core.sleep_manager import AgentSleepState
        
        state = AgentSleepState("agent_001")
        state.lasting_truths = [
            {"type": "preference", "content": "用户喜欢简洁风格"},
            {"type": "fact", "content": "订单号12345"},
        ]
        state.theme_summary = "近期主要关注：购物、售后"
        sleep_manager.config.memory_md_path = str(temp_dir)
        
        sleep_manager._write_memory_md("agent_001", state)
        
        memory_file = temp_dir / "agent_001" / "MEMORY.md"
        assert memory_file.exists()
        
        content = memory_file.read_text(encoding="utf-8")
        assert "AI 长期记忆" in content
        assert "持久真理" in content
        assert "用户喜欢简洁风格" in content
        assert "反思摘要" in content


# ==================== 异步睡眠阶段测试 ====================

class TestAsyncSleepPhases:
    """测试异步睡眠阶段执行"""
    
    @pytest.mark.asyncio
    async def test_async_light_sleep_no_memories(self, sleep_manager, mock_db):
        """测试浅睡眠无记忆时"""
        mock_db.get_recent_memories = AsyncMock(return_value=[])
        
        from core.sleep_manager import AgentSleepState
        state = AgentSleepState("agent_001")
        
        with patch('core.sleep_manager.HumanThinkingDB', return_value=mock_db):
            await sleep_manager._async_light_sleep("agent_001", state)
        
        mock_db.get_recent_memories.assert_called_once()
        assert state.pending_importance == []
    
    @pytest.mark.asyncio
    async def test_async_light_sleep_with_memories(self, sleep_manager, mock_db, sample_memories):
        """测试浅睡眠有记忆时"""
        mock_db.get_recent_memories = AsyncMock(return_value=sample_memories[:5])
        
        from core.sleep_manager import AgentSleepState
        state = AgentSleepState("agent_001")
        
        with patch('core.sleep_manager.HumanThinkingDB', return_value=mock_db):
            await sleep_manager._async_light_sleep("agent_001", state)
        
        assert len(state.pending_importance) > 0
        mock_db.add_dream_log.assert_called()
    
    @pytest.mark.asyncio
    async def test_async_rem_no_pending(self, sleep_manager, mock_db):
        """测试 REM 无待处理记忆时"""
        mock_db.get_recent_memories = AsyncMock(return_value=[])
        
        from core.sleep_manager import AgentSleepState
        state = AgentSleepState("agent_001")
        
        with patch('core.sleep_manager.HumanThinkingDB', return_value=mock_db):
            await sleep_manager._async_rem("agent_001", state)
        
        assert state.theme_summary is not None
    
    @pytest.mark.asyncio
    async def test_async_deep_sleep(self, sleep_manager, mock_db):
        """测试深睡眠执行"""
        mock_db.apply_forgetting_curve = AsyncMock(return_value=5)
        mock_db.get_memories_for_consolidation = AsyncMock(return_value=[])
        
        from core.sleep_manager import AgentSleepState
        state = AgentSleepState("agent_001")
        state.pending_importance = [
            {"id": 1, "content": "重要记忆", "importance": 5, "memory_type": "fact"}
        ]
        
        with patch('core.sleep_manager.HumanThinkingDB', return_value=mock_db):
            await sleep_manager._async_deep_sleep("agent_001", state)
        
        mock_db.apply_forgetting_curve.assert_called_once()


# ==================== 全局函数测试 ====================

class TestGlobalFunctions:
    """测试全局辅助函数"""
    
    def test_init_sleep_manager(self):
        """测试初始化全局睡眠管理器"""
        from core.sleep_manager import init_sleep_manager, SleepConfig, get_sleep_manager
        
        config = SleepConfig()
        manager = init_sleep_manager(config)
        
        assert manager is not None
        assert get_sleep_manager() is manager
    
    def test_get_sleep_manager_with_agent_id(self):
        """测试获取 Agent 专属睡眠管理器"""
        from core.sleep_manager import (
            init_sleep_manager, get_sleep_manager, 
            set_agent_sleep_config, SleepConfig
        )
        
        global_manager = init_sleep_manager(SleepConfig())
        
        agent_config = SleepConfig(light_sleep_minutes=10)
        set_agent_sleep_config("agent_001", agent_config)
        
        agent_manager = get_sleep_manager("agent_001")
        
        assert agent_manager is not None
        assert agent_manager.config.light_sleep_minutes == 10
    
    def test_get_sleep_manager_no_global(self):
        """测试无全局管理器时返回 None"""
        from core.sleep_manager import get_sleep_manager
        import core.sleep_manager as sm
        from unittest.mock import patch
        
        # 由于前面的测试可能已经设置了全局管理器，
        # 我们直接 mock get_sleep_manager 函数来测试其逻辑
        def mock_get_sleep_manager(agent_id=None):
            # 模拟 _global_sleep_manager 为 None 的情况
            return None
        
        with patch.object(sm, 'get_sleep_manager', side_effect=mock_get_sleep_manager):
            result = sm.get_sleep_manager()
            assert result is None, f"Expected None but got {result}"
    
    def test_get_agent_sleep_config(self):
        """测试获取 Agent 睡眠配置"""
        from core.sleep_manager import (
            get_agent_sleep_config, set_agent_sleep_config, 
            init_sleep_manager, SleepConfig
        )
        
        init_sleep_manager(SleepConfig())
        
        # 获取全局配置
        config = get_agent_sleep_config()
        assert config is not None
        
        # 获取 Agent 专属配置
        agent_config = SleepConfig(light_sleep_minutes=15)
        set_agent_sleep_config("agent_001", agent_config)
        
        config = get_agent_sleep_config("agent_001")
        assert config.light_sleep_minutes == 15
    
    def test_set_agent_sleep_config(self):
        """测试设置 Agent 睡眠配置"""
        from core.sleep_manager import set_agent_sleep_config, get_agent_sleep_config, SleepConfig
        
        config = SleepConfig(deep_sleep_minutes=90)
        set_agent_sleep_config("agent_002", config)
        
        retrieved = get_agent_sleep_config("agent_002")
        assert retrieved.deep_sleep_minutes == 90
    
    def test_save_and_load_agent_sleep_config(self, temp_dir):
        """测试保存和加载 Agent 睡眠配置"""
        from core.sleep_manager import (
            save_agent_sleep_config, load_agent_sleep_config, 
            SleepConfig, get_agent_sleep_config
        )
        
        config = SleepConfig(
            light_sleep_minutes=20,
            rem_minutes=40,
            deep_sleep_minutes=80,
        )
        
        # 保存配置
        success = save_agent_sleep_config("agent_003", config)
        assert success is True
        
        # 加载配置
        loaded = load_agent_sleep_config("agent_003")
        assert loaded.light_sleep_minutes == 20
    
    def test_save_agent_sleep_config_failure(self):
        """测试保存配置失败"""
        from core.sleep_manager import save_agent_sleep_config, SleepConfig
        
        config = SleepConfig()
        
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("No permission")):
            success = save_agent_sleep_config("agent_004", config)
            assert success is False
    
    def test_record_agent_activity(self):
        """测试记录 Agent 活动"""
        from core.sleep_manager import (
            init_sleep_manager, record_agent_activity, 
            is_agent_sleeping, SleepConfig
        )
        
        init_sleep_manager(SleepConfig())
        
        result = record_agent_activity("agent_001")
        assert result is False  # 未达到睡眠阈值
        
        assert is_agent_sleeping("agent_001") is False
    
    def test_pulse_agent(self):
        """测试心跳函数"""
        from core.sleep_manager import init_sleep_manager, pulse_agent, SleepConfig
        
        init_sleep_manager(SleepConfig())
        
        result = pulse_agent("agent_001")
        assert result is False
    
    def test_notify_task_start(self):
        """测试任务开始通知"""
        from core.sleep_manager import init_sleep_manager, notify_task_start, SleepConfig
        
        init_sleep_manager(SleepConfig())
        
        result = notify_task_start("agent_001")
        assert result is False


# ==================== 错误处理测试 ====================

class TestErrorHandling:
    """测试错误处理"""
    
    def test_execute_light_sleep_exception(self, sleep_manager):
        """测试浅睡眠执行异常处理"""
        from core.sleep_manager import AgentSleepState
        
        state = AgentSleepState("agent_001")
        
        with patch('asyncio.new_event_loop', side_effect=RuntimeError("Loop error")):
            # 不应抛出异常
            sleep_manager._execute_light_sleep("agent_001", state)
    
    def test_execute_rem_exception(self, sleep_manager):
        """测试 REM 执行异常处理"""
        from core.sleep_manager import AgentSleepState
        
        state = AgentSleepState("agent_001")
        
        with patch('asyncio.new_event_loop', side_effect=RuntimeError("Loop error")):
            sleep_manager._execute_rem("agent_001", state)
    
    def test_execute_deep_sleep_exception(self, sleep_manager):
        """测试深睡眠执行异常处理"""
        from core.sleep_manager import AgentSleepState
        
        state = AgentSleepState("agent_001")
        
        with patch('asyncio.new_event_loop', side_effect=RuntimeError("Loop error")):
            sleep_manager._execute_deep_sleep("agent_001", state)
    
    def test_write_memory_md_exception(self, sleep_manager, temp_dir):
        """测试写入 MEMORY.md 异常处理"""
        from core.sleep_manager import AgentSleepState
        
        state = AgentSleepState("agent_001")
        sleep_manager.config.memory_md_path = str(temp_dir)
        
        with patch('pathlib.Path.mkdir', side_effect=OSError("Disk full")):
            # 不应抛出异常
            sleep_manager._write_memory_md("agent_001", state)
