# -*- coding: utf-8 -*-
"""
API Routes 单元测试

测试范围：
- 健康检查端点
- 统计信息端点
- 记忆搜索端点
- 记忆更新/删除端点
- 会话管理端点
- 配置管理端点
- 睡眠管理端点
- 梦境记录端点
- 卸载端点
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ==================== 健康检查测试 ====================

class TestHealthCheck:
    """测试健康检查端点"""
    
    def test_health_check(self, client):
        """测试健康检查返回正确结构"""
        response = client.get("/api/plugins/humanthinking/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["plugin"] == "humanthinking"
        assert "version" in data
        assert "timestamp" in data


# ==================== 统计信息测试 ====================

class TestStats:
    """测试统计信息端点"""
    
    def test_get_stats(self, client):
        """测试获取统计信息"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_stats = MagicMock(return_value={
                'total': 100,
                'cross_session': 50,
                'frozen': 10,
                'active_sessions': 5,
                'emotional_states': 3
            })
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/stats?agent_id=test_agent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_memories"] == 100
            assert data["cross_session_memories"] == 50
            assert data["frozen_memories"] == 10
            assert data["active_sessions"] == 5
            assert data["emotional_states"] == 3
    
    def test_get_stats_no_agent(self, client):
        """测试不带 agent_id 获取统计"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_stats = MagicMock(return_value={
                'total': 0,
                'cross_session': 0,
                'frozen': 0,
                'active_sessions': 0,
                'emotional_states': 0
            })
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/stats")
            
            assert response.status_code == 200


# ==================== 记忆搜索测试 ====================

class TestMemorySearch:
    """测试记忆搜索端点"""
    
    def test_search_memories(self, client):
        """测试搜索记忆"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.memory_search = MagicMock(return_value=[
                {"content": "记忆1", "score": 0.9},
                {"content": "记忆2", "score": 0.8}
            ])
            mock_db_class.return_value = mock_db
            
            response = client.post(
                "/api/plugins/humanthinking/search?agent_id=test_agent",
                json={"query": "测试", "limit": 10}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["query"] == "测试"
            assert data["total"] == 2
            assert len(data["memories"]) == 2
    
    def test_search_memories_validation_error(self, client):
        """测试搜索参数验证错误"""
        response = client.post(
            "/api/plugins/humanthinking/search",
            json={"query": "", "limit": 10}  # 空查询
        )
        
        assert response.status_code == 422  # 验证错误
    
    def test_search_memories_limit_validation(self, client):
        """测试 limit 参数验证"""
        response = client.post(
            "/api/plugins/humanthinking/search",
            json={"query": "测试", "limit": 100}  # 超过最大值
        )
        
        assert response.status_code == 422


# ==================== 记忆更新/删除测试 ====================

class TestMemoryUpdate:
    """测试记忆更新端点"""
    
    def test_update_memory(self, client):
        """测试更新记忆"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.update_memory = MagicMock()
            mock_db_class.return_value = mock_db
            
            response = client.put(
                "/api/plugins/humanthinking/memories/mem_001",
                json={"content": "更新后的内容", "importance": 0.8}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["memory_id"] == "mem_001"
    
    def test_update_memory_partial(self, client):
        """测试部分更新记忆"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.update_memory = MagicMock()
            mock_db_class.return_value = mock_db
            
            response = client.put(
                "/api/plugins/humanthinking/memories/mem_001",
                json={"memory_type": "fact"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["updated"]["memory_type"] == "fact"
    
    def test_update_memory_type_validation(self, client):
        """测试记忆类型验证"""
        response = client.put(
            "/api/plugins/humanthinking/memories/mem_001",
            json={"memory_type": "invalid_type"}
        )
        
        assert response.status_code == 422


class TestBatchDelete:
    """测试批量删除端点"""
    
    def test_batch_delete_memories(self, client):
        """测试批量删除记忆"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.delete_memory = MagicMock()
            mock_db_class.return_value = mock_db
            
            response = client.delete(
                "/api/plugins/humanthinking/memories/batch",
                json={"memory_ids": ["mem_001", "mem_002", "mem_003"]}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["deleted_count"] == 3
    
    def test_batch_delete_empty(self, client):
        """测试空列表删除"""
        response = client.delete(
            "/api/plugins/humanthinking/memories/batch",
            json={"memory_ids": []}
        )
        
        assert response.status_code == 422


# ==================== 会话管理测试 ====================

class TestSessionManagement:
    """测试会话管理端点"""
    
    def test_get_sessions(self, client):
        """测试获取会话列表"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_sessions = MagicMock(return_value=[
                {"session_id": "s1", "name": "会话1"},
                {"session_id": "s2", "name": "会话2"}
            ])
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/sessions?agent_id=test_agent")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
    
    def test_get_sessions_empty(self, client):
        """测试空会话列表"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_sessions = MagicMock(return_value=None)
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/sessions")
            
            assert response.status_code == 200
            data = response.json()
            assert data == []
    
    def test_rename_session(self, client):
        """测试重命名会话"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.update_session_name = MagicMock()
            mock_db_class.return_value = mock_db
            
            response = client.put(
                "/api/plugins/humanthinking/sessions/s1/rename",
                json={"session_name": "新名称"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["session_name"] == "新名称"
    
    def test_rename_session_validation(self, client):
        """测试重命名参数验证"""
        response = client.put(
            "/api/plugins/humanthinking/sessions/s1/rename",
            json={"session_name": ""}  # 空名称
        )
        
        assert response.status_code == 422
    
    def test_delete_session(self, client):
        """测试删除会话"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.delete_session = MagicMock()
            mock_db_class.return_value = mock_db
            
            response = client.delete("/api/plugins/humanthinking/sessions/s1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_batch_delete_sessions(self, client):
        """测试批量删除会话"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.delete_session = MagicMock()
            mock_db_class.return_value = mock_db
            
            response = client.post(
                "/api/plugins/humanthinking/sessions/batch-delete",
                json={"session_ids": ["s1", "s2"]}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["deleted_count"] == 2
    
    def test_get_session_detail(self, client):
        """测试获取会话详情"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_session = MagicMock(return_value={
                "session_name": "测试会话",
                "user_name": "用户1"
            })
            mock_db.get_session_memories = MagicMock(return_value=[
                {"id": 1, "content": "记忆1"}
            ])
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/sessions/s1/detail")
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "s1"
            assert data["session_name"] == "测试会话"
            assert len(data["memories"]) == 1


# ==================== 最近记忆测试 ====================

class TestRecentMemories:
    """测试最近记忆端点"""
    
    def test_get_recent_memories(self, client):
        """测试获取最近记忆"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_recent_memories = MagicMock(return_value=[
                {"id": 1, "content": "最近记忆1"},
                {"id": 2, "content": "最近记忆2"}
            ])
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/memories/recent?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["memories"]) == 2
            assert data["total"] == 2
    
    def test_get_recent_memories_empty(self, client):
        """测试空最近记忆"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_recent_memories = MagicMock(return_value=None)
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/memories/recent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["memories"] == []
            assert data["total"] == 0


# ==================== 记忆时间线测试 ====================

class TestMemoryTimeline:
    """测试记忆时间线端点"""
    
    def test_get_memory_timeline(self, client):
        """测试获取记忆时间线"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_memory_timeline = MagicMock(return_value=[
                {"date": "2024-01-01", "count": 5},
                {"date": "2024-01-02", "count": 3}
            ])
            mock_db_class.return_value = mock_db
            
            response = client.get(
                "/api/plugins/humanthinking/memories/timeline?start_date=2024-01-01&end_date=2024-01-31"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
    
    def test_get_memory_timeline_empty(self, client):
        """测试空时间线"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_memory_timeline = MagicMock(return_value=None)
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/memories/timeline")
            
            assert response.status_code == 200
            data = response.json()
            assert data == []


# ==================== 配置管理测试 ====================

class TestConfig:
    """测试配置管理端点"""
    
    def test_get_config(self, client):
        """测试获取配置"""
        with patch('api.routes.get_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.enable_cross_session = True
            mock_config.enable_emotion = True
            mock_config.frozen_days = 30
            mock_config.archive_days = 90
            mock_config.delete_days = 180
            mock_config.max_results = 5
            mock_config.session_idle_timeout = 180
            mock_config.refresh_interval = 5
            mock_config.max_memory_chars = 150
            mock_config.enable_distributed_db = False
            mock_config.db_size_threshold_mb = 800
            mock_config.disable_file_memory = True
            mock_get_config.return_value = mock_config
            
            response = client.get("/api/plugins/humanthinking/config?agent_id=test_agent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["enable_cross_session"] is True
            assert data["frozen_days"] == 30
            assert data["max_results"] == 5
    
    def test_get_config_error(self, client):
        """测试获取配置错误"""
        with patch('api.routes.get_config', side_effect=Exception("Config error")):
            response = client.get("/api/plugins/humanthinking/config")
            
            assert response.status_code == 500
    
    def test_update_config(self, client):
        """测试更新配置"""
        with patch('api.routes.get_config') as mock_get_config, \
             patch('api.routes.save_config', return_value=True), \
             patch('api.routes.update_config_fields') as mock_update_fields:
            
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            
            response = client.post(
                "/api/plugins/humanthinking/config?agent_id=test_agent",
                json={
                    "enable_cross_session": False,
                    "frozen_days": 60,
                    "max_results": 10
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_update_config_save_failure(self, client):
        """测试配置保存失败"""
        with patch('api.routes.get_config') as mock_get_config, \
             patch('api.routes.save_config', return_value=False), \
             patch('api.routes.update_config_fields'):
            
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            
            response = client.post(
                "/api/plugins/humanthinking/config?agent_id=test_agent",
                json={"frozen_days": 60}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False


# ==================== 情感状态测试 ====================

class TestEmotion:
    """测试情感状态端点"""
    
    def test_get_emotion_context(self, client):
        """测试获取情感上下文"""
        with patch('api.routes.EmotionalContinuityEngine') as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.get_emotional_context = MagicMock(return_value={
                "current_emotion": "happy",
                "intensity": 0.8,
                "history": [{"emotion": "neutral", "intensity": 0.5}]
            })
            mock_engine_class.return_value = mock_engine
            
            response = client.get(
                "/api/plugins/humanthinking/emotion?session_id=s1&agent_id=test_agent"
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["current_emotion"] == "happy"
            assert data["intensity"] == 0.8
    
    def test_get_emotion_context_empty(self, client):
        """测试无情感状态返回默认值"""
        with patch('api.routes.EmotionalContinuityEngine') as mock_engine_class:
            mock_engine = MagicMock()
            mock_engine.get_emotional_context = MagicMock(return_value=None)
            mock_engine_class.return_value = mock_engine
            
            response = client.get("/api/plugins/humanthinking/emotion")
            
            assert response.status_code == 200
            data = response.json()
            assert data["current_emotion"] == "neutral"
            assert data["intensity"] == 0.0
            assert data["history"] == []


# ==================== 睡眠管理测试 ====================

class TestSleep:
    """测试睡眠管理端点"""
    
    def test_get_sleep_status(self, client):
        """测试获取睡眠状态"""
        with patch('api.routes.get_sleep_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_state = MagicMock()
            mock_state.is_active = True
            mock_state.is_deep_sleep = False
            mock_state.is_rem = False
            mock_state.is_light_sleep = False
            mock_state.last_active_time = 1234567890
            mock_manager.get_agent_state = MagicMock(return_value=mock_state)
            mock_get_manager.return_value = mock_manager
            
            response = client.get("/api/plugins/humanthinking/sleep/status?agent_id=test_agent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"
            assert data["sleep_type"] is None
    
    def test_get_sleep_status_sleeping(self, client):
        """测试获取睡眠中的状态"""
        with patch('api.routes.get_sleep_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_state = MagicMock()
            mock_state.is_active = False
            mock_state.is_deep_sleep = True
            mock_state.is_rem = False
            mock_state.is_light_sleep = False
            mock_state.last_active_time = 1234567890
            mock_manager.get_agent_state = MagicMock(return_value=mock_state)
            mock_get_manager.return_value = mock_manager
            
            response = client.get("/api/plugins/humanthinking/sleep/status?agent_id=test_agent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "sleeping"
            assert data["sleep_type"] == "deep"
    
    def test_get_sleep_status_no_state(self, client):
        """测试无状态时返回默认值"""
        with patch('api.routes.get_sleep_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.get_agent_state = MagicMock(return_value=None)
            mock_get_manager.return_value = mock_manager
            
            response = client.get("/api/plugins/humanthinking/sleep/status")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"
    
    def test_get_sleep_config(self, client):
        """测试获取睡眠配置"""
        with patch('api.routes.load_agent_sleep_config') as mock_load:
            mock_config = MagicMock()
            mock_config.enable_agent_sleep = True
            mock_config.light_sleep_minutes = 30
            mock_config.rem_minutes = 60
            mock_config.deep_sleep_minutes = 120
            mock_config.consolidate_days = 7
            mock_config.frozen_days = 30
            mock_config.archive_days = 90
            mock_config.delete_days = 180
            mock_config.enable_insight = True
            mock_config.enable_dream_log = True
            mock_load.return_value = mock_config
            
            response = client.get("/api/plugins/humanthinking/sleep/config?agent_id=test_agent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["enable_agent_sleep"] is True
            assert data["light_sleep_minutes"] == 30
            assert data["deep_sleep_minutes"] == 120
    
    def test_update_sleep_config(self, client):
        """测试更新睡眠配置"""
        with patch('api.routes.get_agent_sleep_config') as mock_get_config, \
             patch('api.routes.save_agent_sleep_config', return_value=True):
            
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            
            response = client.post(
                "/api/plugins/humanthinking/sleep/config?agent_id=test_agent",
                json={
                    "enable_agent_sleep": False,
                    "light_sleep_minutes": 15,
                    "deep_sleep_minutes": 90
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_update_sleep_config_global(self, client):
        """测试更新全局睡眠配置"""
        with patch('api.routes.get_agent_sleep_config') as mock_get_config, \
             patch('api.routes.get_sleep_manager') as mock_get_manager:
            
            mock_config = MagicMock()
            mock_get_config.return_value = mock_config
            
            mock_manager = MagicMock()
            mock_get_manager.return_value = mock_manager
            
            response = client.post(
                "/api/plugins/humanthinking/sleep/config",
                json={"enable_agent_sleep": False}
            )
            
            assert response.status_code == 200
            assert data["success"] is True
    
    def test_force_sleep(self, client):
        """测试强制睡眠"""
        with patch('api.routes.get_sleep_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.force_light_sleep = MagicMock()
            mock_get_manager.return_value = mock_manager
            
            response = client.post(
                "/api/plugins/humanthinking/sleep/force?agent_id=test_agent",
                json={"sleep_type": "light"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["sleep_type"] == "light"
    
    def test_force_sleep_invalid_type(self, client):
        """测试无效睡眠类型"""
        response = client.post(
            "/api/plugins/humanthinking/sleep/force",
            json={"sleep_type": "invalid"}
        )
        
        assert response.status_code == 422
    
    def test_wakeup(self, client):
        """测试强制唤醒"""
        with patch('api.routes.get_sleep_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.wakeup = MagicMock()
            mock_get_manager.return_value = mock_manager
            
            response = client.post("/api/plugins/humanthinking/sleep/wakeup?agent_id=test_agent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["status"] == "active"
    
    def test_get_sleep_insight(self, client):
        """测试获取睡眠洞察"""
        with patch('api.routes.get_sleep_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.generate_insight = MagicMock(return_value={
                "insight": "测试洞察",
                "suggestions": ["建议1"],
                "memory_consolidation": {"count": 5}
            })
            mock_get_manager.return_value = mock_manager
            
            response = client.get("/api/plugins/humanthinking/sleep/insight?agent_id=test_agent")
            
            assert response.status_code == 200
            data = response.json()
            assert data["insight"] == "测试洞察"
    
    def test_get_sleep_insight_empty(self, client):
        """测试无洞察数据"""
        with patch('api.routes.get_sleep_manager') as mock_get_manager:
            mock_manager = MagicMock()
            mock_manager.generate_insight = MagicMock(return_value=None)
            mock_get_manager.return_value = mock_manager
            
            response = client.get("/api/plugins/humanthinking/sleep/insight")
            
            assert response.status_code == 200
            data = response.json()
            assert "暂无洞察数据" in data["insight"]


# ==================== 梦境记录测试 ====================

class TestDreams:
    """测试梦境记录端点"""
    
    def test_get_dreams(self, client):
        """测试获取梦境记录"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_dreams = MagicMock(return_value=[
                {"id": 1, "action": "LIGHT_SLEEP", "details": "浅睡眠"},
                {"id": 2, "action": "REM", "details": "快速眼动"}
            ])
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/dreams?limit=10")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
    
    def test_get_dreams_empty(self, client):
        """测试空梦境记录"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_dreams = MagicMock(return_value=[])
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/dreams")
            
            assert response.status_code == 200
            data = response.json()
            assert data == []
    
    def test_get_dreams_fallback(self, client):
        """测试梦境记录降级返回"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            mock_db.get_dreams = MagicMock(side_effect=Exception("DB error"))
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/dreams")
            
            assert response.status_code == 200
            data = response.json()
            assert data == []


# ==================== 卸载测试 ====================

class TestUninstall:
    """测试卸载端点"""
    
    def test_uninstall_keep_data(self, client, temp_dir):
        """测试保留数据卸载"""
        with patch('api.routes.detect_qwenpaw_env') as mock_detect, \
             patch('pathlib.Path.home', return_value=temp_dir):
            
            mock_env = MagicMock()
            mock_env.working_dir = temp_dir
            mock_env.qwenpaw_package_dir = temp_dir / "packages"
            mock_env.install_type = "local"
            mock_env.python_executable = None
            mock_env.venv_dir = None
            mock_env.is_windows = True
            mock_detect.return_value = mock_env
            
            response = client.post(
                "/api/plugins/humanthinking/uninstall",
                json={"keep_data": True}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["keep_data"] is True
    
    def test_uninstall_delete_data(self, client, temp_dir):
        """测试删除数据卸载"""
        with patch('api.routes.detect_qwenpaw_env') as mock_detect, \
             patch('pathlib.Path.home', return_value=temp_dir):
            
            mock_env = MagicMock()
            mock_env.working_dir = temp_dir
            mock_env.qwenpaw_package_dir = temp_dir / "packages"
            mock_env.install_type = "local"
            mock_env.python_executable = None
            mock_env.venv_dir = None
            mock_env.is_windows = True
            mock_detect.return_value = mock_env
            
            response = client.post(
                "/api/plugins/humanthinking/uninstall",
                json={"keep_data": False}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["keep_data"] is False


# ==================== 辅助函数测试 ====================

class TestHelperFunctions:
    """测试辅助函数"""
    
    def test_get_sleep_manager_singleton(self):
        """测试睡眠管理器单例"""
        from api.routes import get_sleep_manager
        
        with patch('api.routes.SleepManager') as mock_class:
            mock_manager = MagicMock()
            mock_class.return_value = mock_manager
            
            manager1 = get_sleep_manager()
            manager2 = get_sleep_manager()
            
            # 应该只创建一次
            mock_class.assert_called_once()
    
    def test_get_memory_manager_lru(self):
        """测试记忆管理器 LRU 清理"""
        from api.routes import get_memory_manager, _MAX_MEMORY_MANAGERS
        
        # 先填充到上限
        with patch('api.routes.HumanThinkingMemoryManager') as mock_class:
            for i in range(_MAX_MEMORY_MANAGERS + 5):
                mock_mm = MagicMock()
                mock_class.return_value = mock_mm
                get_memory_manager(f"agent_{i}")
    
    def test_handle_db_operation_success(self):
        """测试数据库操作成功处理"""
        from api.routes import _handle_db_operation
        
        result = _handle_db_operation("test", lambda: "success")
        assert result == "success"
    
    def test_handle_db_operation_import_error(self):
        """测试导入错误处理"""
        from api.routes import _handle_db_operation
        
        def raise_import_error():
            raise ImportError("Module not found")
        
        result = _handle_db_operation("test", raise_import_error, fallback_result="fallback")
        assert result == "fallback"
    
    def test_handle_db_operation_general_error(self):
        """测试一般错误处理"""
        from api.routes import _handle_db_operation
        
        def raise_error():
            raise RuntimeError("Some error")
        
        result = _handle_db_operation("test", raise_error, fallback_result="fallback")
        assert result == "fallback"


# ==================== 请求模型验证测试 ====================

class TestRequestModels:
    """测试请求模型验证"""
    
    def test_search_request_valid(self):
        """测试有效搜索请求"""
        from api.routes import SearchRequest
        
        request = SearchRequest(query="测试", limit=10)
        assert request.query == "测试"
        assert request.limit == 10
    
    def test_search_request_limit_bounds(self):
        """测试搜索 limit 边界"""
        from api.routes import SearchRequest
        
        with pytest.raises(ValueError):
            SearchRequest(query="测试", limit=0)
        
        with pytest.raises(ValueError):
            SearchRequest(query="测试", limit=100)
    
    def test_memory_update_request(self):
        """测试记忆更新请求"""
        from api.routes import MemoryUpdateRequest
        
        request = MemoryUpdateRequest(content="新内容", importance=0.8)
        assert request.content == "新内容"
        assert request.importance == 0.8
    
    def test_memory_update_request_importance_bounds(self):
        """测试重要性边界"""
        from api.routes import MemoryUpdateRequest
        
        with pytest.raises(ValueError):
            MemoryUpdateRequest(importance=1.5)
        
        with pytest.raises(ValueError):
            MemoryUpdateRequest(importance=-0.1)
    
    def test_sleep_config_update_request(self):
        """测试睡眠配置更新请求"""
        from api.routes import SleepConfigUpdateRequest
        
        request = SleepConfigUpdateRequest(
            enable_agent_sleep=False,
            light_sleep_minutes=15
        )
        assert request.enable_agent_sleep is False
        assert request.light_sleep_minutes == 15
    
    def test_force_sleep_request(self):
        """测试强制睡眠请求"""
        from api.routes import ForceSleepRequest
        
        request = ForceSleepRequest(sleep_type="deep")
        assert request.sleep_type == "deep"
    
    def test_force_sleep_request_invalid(self):
        """测试无效睡眠类型"""
        from api.routes import ForceSleepRequest
        
        with pytest.raises(ValueError):
            ForceSleepRequest(sleep_type="invalid")
    
    def test_config_update_request(self):
        """测试配置更新请求"""
        from api.routes import ConfigUpdateRequest
        
        request = ConfigUpdateRequest(
            frozen_days=60,
            max_results=10
        )
        assert request.frozen_days == 60
        assert request.max_results == 10
    
    def test_config_update_request_bounds(self):
        """测试配置更新边界值"""
        from api.routes import ConfigUpdateRequest
        
        with pytest.raises(ValueError):
            ConfigUpdateRequest(frozen_days=5)  # 小于最小值
        
        with pytest.raises(ValueError):
            ConfigUpdateRequest(frozen_days=400)  # 大于最大值


# ==================== 错误处理装饰器测试 ====================

class TestErrorHandler:
    """测试错误处理装饰器"""
    
    def test_handle_api_errors_success(self, client):
        """测试 API 错误处理成功情况"""
        response = client.get("/api/plugins/humanthinking/health")
        assert response.status_code == 200
    
    def test_handle_api_errors_not_implemented(self, client):
        """测试未实现方法处理"""
        with patch('api.routes.HumanThinkingDB') as mock_db_class:
            mock_db = MagicMock()
            # 移除 get_stats 方法
            del mock_db.get_stats
            mock_db_class.return_value = mock_db
            
            response = client.get("/api/plugins/humanthinking/stats")
            
            assert response.status_code == 501
