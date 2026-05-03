# -*- coding: utf-8 -*-
"""
MemoryManager 单元测试

测试范围：
- HumanThinkingConfig 配置类
- 配置管理函数（get_config, save_config, update_config 等）
- MemoryResponse 数据类
- ContextLoadingInMemory 上下文加载
- HumanThinkingMemoryManager 核心记忆管理器
"""

import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest


# ==================== HumanThinkingConfig 测试 ====================

class TestHumanThinkingConfig:
    """测试 HumanThinking 配置类"""
    
    def test_default_values(self):
        """测试默认配置值"""
        from core.memory_manager import HumanThinkingConfig
        
        config = HumanThinkingConfig()
        
        assert config.enable_cross_session is True
        assert config.enable_emotion is True
        assert config.session_idle_timeout == 180
        assert config.refresh_interval == 5
        assert config.max_results == 5
        assert config.max_memory_chars == 150
        assert config.disable_file_memory is True
        assert config.frozen_days == 30
        assert config.archive_days == 90
        assert config.delete_days == 180
        assert config.enable_distributed_db is False
        assert config.db_size_threshold_mb == 800
        assert config.enable_api_fallback is False


# ==================== 配置管理函数测试 ====================

class TestConfigManagement:
    """测试配置管理函数"""
    
    def test_get_config_default(self):
        """测试获取默认配置"""
        from core.memory_manager import get_config, HumanThinkingConfig
        
        config = get_config()
        
        assert isinstance(config, HumanThinkingConfig)
        assert config.enable_cross_session is True
    
    def test_get_config_caching(self):
        """测试配置缓存"""
        from core.memory_manager import get_config, _agent_configs
        
        # 清除缓存
        _agent_configs.clear()
        
        config1 = get_config(agent_id="agent_001")
        config2 = get_config(agent_id="agent_001")
        
        # 应该返回同一个对象（缓存）
        assert config1 is config2
    
    def test_get_config_from_file(self, temp_dir):
        """测试从文件加载配置"""
        from core.memory_manager import get_config, _agent_configs
        
        # 清除缓存
        _agent_configs.clear()
        
        # 创建配置文件
        config_dir = temp_dir / "memory"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "human_thinking_config.json"
        
        custom_config = {
            "enable_cross_session": False,
            "enable_emotion": False,
            "max_results": 10,
            "frozen_days": 60,
        }
        
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(custom_config, f)
        
        config = get_config(agent_id="test_agent", working_dir=str(temp_dir))
        
        assert config.enable_cross_session is False
        assert config.enable_emotion is False
        assert config.max_results == 10
        assert config.frozen_days == 60
    
    def test_get_config_file_not_exist(self):
        """测试配置文件不存在时返回默认配置"""
        from core.memory_manager import get_config, _agent_configs
        
        _agent_configs.clear()
        
        config = get_config(agent_id="nonexistent_agent", working_dir="/nonexistent/path")
        
        assert config.enable_cross_session is True  # 默认值
    
    def test_save_config(self, temp_dir):
        """测试保存配置"""
        from core.memory_manager import save_config, HumanThinkingConfig
        
        config = HumanThinkingConfig(
            enable_cross_session=False,
            max_results=10,
        )
        
        result = save_config(config, agent_id="agent_001", working_dir=str(temp_dir))
        
        assert result is True
        
        # 验证文件内容
        config_file = temp_dir / "memory" / "human_thinking_config.json"
        assert config_file.exists()
        
        with open(config_file, "r", encoding="utf-8") as f:
            saved = json.load(f)
        
        assert saved["enable_cross_session"] is False
        assert saved["max_results"] == 10
    
    def test_save_config_no_agent(self, temp_dir):
        """测试无 Agent ID 时保存到全局配置"""
        from core.memory_manager import save_config, HumanThinkingConfig
        
        config = HumanThinkingConfig()
        
        with patch('pathlib.Path.home', return_value=temp_dir):
            result = save_config(config)
            assert result is True
    
    def test_save_config_failure(self):
        """测试保存配置失败"""
        from core.memory_manager import save_config, HumanThinkingConfig
        
        config = HumanThinkingConfig()
        
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("No permission")):
            result = save_config(config, agent_id="agent_001", working_dir="/root")
            assert result is False
    
    def test_update_config(self):
        """测试更新配置"""
        from core.memory_manager import update_config, get_config, _agent_configs
        
        _agent_configs.clear()
        
        config = HumanThinkingConfig(enable_cross_session=False)
        update_config(config, agent_id="agent_001")
        
        retrieved = get_config(agent_id="agent_001")
        assert retrieved.enable_cross_session is False
    
    def test_update_config_global(self):
        """测试更新全局配置"""
        from core.memory_manager import update_config, get_config, _global_config
        
        config = HumanThinkingConfig(max_results=20)
        update_config(config)
        
        assert _global_config.max_results == 20
    
    def test_update_config_fields(self):
        """测试更新指定字段"""
        from core.memory_manager import update_config_fields, get_config, _agent_configs
        
        _agent_configs.clear()
        
        # 先获取配置创建缓存
        get_config(agent_id="agent_001")
        
        update_config_fields(
            {"max_results": 15, "frozen_days": 45},
            agent_id="agent_001"
        )
        
        config = get_config(agent_id="agent_001")
        assert config.max_results == 15
        assert config.frozen_days == 45
    
    def test_update_config_fields_no_cache(self):
        """测试更新未缓存的配置字段"""
        from core.memory_manager import update_config_fields, get_config, _agent_configs
        
        _agent_configs.clear()
        
        # 直接更新未缓存的配置
        update_config_fields(
            {"max_results": 25},
            agent_id="agent_new"
        )
        
        config = get_config(agent_id="agent_new")
        assert config.max_results == 25


# ==================== MemoryResponse 测试 ====================

class TestMemoryResponse:
    """测试记忆响应数据类"""
    
    def test_default_values(self):
        """测试默认值"""
        from core.memory_manager import MemoryResponse
        
        response = MemoryResponse()
        
        assert response.memories == []
        assert response.total_count == 0
        assert response.query == ""
    
    def test_custom_values(self):
        """测试自定义值"""
        from core.memory_manager import MemoryResponse
        
        response = MemoryResponse(
            memories=[{"content": "test"}],
            total_count=1,
            query="test query"
        )
        
        assert len(response.memories) == 1
        assert response.total_count == 1
        assert response.query == "test query"


# ==================== ContextLoadingInMemory 测试 ====================

class TestContextLoadingInMemory:
    """测试上下文加载内存"""
    
    def test_init(self):
        """测试初始化"""
        from core.memory_manager import ContextLoadingInMemory
        
        memory = ContextLoadingInMemory()
        
        assert memory._memory_manager_ref is None
        assert memory._context_loaded is False
        assert memory._compressed_summary == ""
    
    @pytest.mark.asyncio
    async def test_get_memory_first_call(self):
        """测试首次调用 get_memory"""
        from core.memory_manager import ContextLoadingInMemory
        
        memory = ContextLoadingInMemory()
        
        # Mock 父类方法
        with patch('agentscope.memory.InMemoryMemory.get_memory', new_callable=AsyncMock) as mock_super:
            mock_super.return_value = []
            
            result = await memory.get_memory()
            
            mock_super.assert_called_once()
            assert memory._context_loaded is True
    
    @pytest.mark.asyncio
    async def test_get_memory_subsequent_calls(self):
        """测试后续调用 get_memory（应跳过加载）"""
        from core.memory_manager import ContextLoadingInMemory
        
        memory = ContextLoadingInMemory()
        memory._context_loaded = True
        
        with patch('agentscope.memory.InMemoryMemory.get_memory', new_callable=AsyncMock) as mock_super:
            mock_super.return_value = []
            
            result = await memory.get_memory()
            
            mock_super.assert_called_once()
    
    def test_extract_channel_name(self):
        """测试渠道名称提取"""
        from core.memory_manager import ContextLoadingInMemory
        
        memory = ContextLoadingInMemory()
        
        assert memory._extract_channel_name("discord:alice") == "Discord"
        assert memory._extract_channel_name("feishu:12345") == "飞书"
        assert memory._extract_channel_name("wechat:user") == "微信"
        assert memory._extract_channel_name("web:user") == "Web"
        assert memory._extract_channel_name("unknown:user") == "Unknown"
        assert memory._extract_channel_name("") == ""
        assert memory._extract_channel_name("nocolon") == ""
    
    def test_build_query_from_context_empty(self):
        """测试空上下文构建查询"""
        from core.memory_manager import ContextLoadingInMemory
        
        memory = ContextLoadingInMemory()
        memory.content = []
        
        query = memory._build_query_from_context()
        assert query == ""
    
    def test_get_compressed_summary(self):
        """测试获取压缩摘要"""
        from core.memory_manager import ContextLoadingInMemory
        
        memory = ContextLoadingInMemory()
        memory._compressed_summary = "测试摘要"
        
        assert memory.get_compressed_summary() == "测试摘要"
    
    @pytest.mark.asyncio
    async def test_update_compressed_summary(self):
        """测试更新压缩摘要"""
        from core.memory_manager import ContextLoadingInMemory
        
        memory = ContextLoadingInMemory()
        await memory.update_compressed_summary("新摘要")
        
        assert memory._compressed_summary == "新摘要"
    
    @pytest.mark.asyncio
    async def test_clear_context(self):
        """测试清除上下文"""
        from core.memory_manager import ContextLoadingInMemory
        
        memory = ContextLoadingInMemory()
        memory._context_loaded = True
        memory._long_term_memory = "一些记忆"
        
        await memory.clear_context()
        
        assert memory._context_loaded is False
        assert memory._long_term_memory == ""


# ==================== HumanThinkingMemoryManager 初始化测试 ====================

class TestMemoryManagerInit:
    """测试记忆管理器初始化"""
    
    def test_init_required_params(self):
        """测试必需参数"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        assert mm.agent_id == "test_agent"
        assert mm.working_dir == "/tmp/test"
        assert mm.user_id is None
        assert mm._current_session_id is None
        assert mm.db is None
        assert mm.cache_pool is None
    
    def test_init_optional_params(self):
        """测试可选参数"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent",
            user_id="user_001",
            current_session_id="session_001"
        )
        
        assert mm.user_id == "user_001"
        assert mm._current_session_id == "session_001"
    
    def test_init_missing_agent_id(self):
        """测试缺少 agent_id 时抛出异常"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        with pytest.raises(ValueError, match="agent_id is required"):
            HumanThinkingMemoryManager(working_dir="/tmp/test", agent_id="")
    
    def test_set_context(self):
        """测试设置上下文"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        mm.set_context(
            session_id="session_002",
            user_id="user_002",
            target_id="target_002",
            role="user"
        )
        
        assert mm._current_session_id == "session_002"
        assert mm.user_id == "user_002"
        assert mm._current_target_id == "target_002"


# ==================== HumanThinkingMemoryManager 核心方法测试 ====================

class TestMemoryManagerCore:
    """测试记忆管理器核心方法"""
    
    @pytest.mark.asyncio
    async def test_start(self, temp_dir):
        """测试启动记忆管理器"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        
        assert mm.db is not None
        assert mm.cache_pool is not None
        assert mm.session_bridge is not None
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_close(self, temp_dir):
        """测试关闭记忆管理器"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        result = await mm.close()
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_store_memory(self, temp_dir):
        """测试存储记忆"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent",
            user_id="user_001",
            current_session_id="session_001"
        )
        
        await mm.start()
        
        memory_id = await mm.store_memory(
            content="用户喜欢简洁风格",
            importance=4,
            memory_type="preference"
        )
        
        assert isinstance(memory_id, int)
        assert memory_id > 0
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_store_memory_no_session(self, temp_dir):
        """测试无会话 ID 时抛出异常"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        
        with pytest.raises(ValueError, match="session_id is required"):
            await mm.store_memory(content="测试内容")
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_memory_search(self, temp_dir):
        """测试记忆搜索"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent",
            current_session_id="session_001"
        )
        
        await mm.start()
        
        # 先存储一些记忆
        await mm.store_memory(
            content="用户喜欢简洁风格",
            importance=4,
            memory_type="preference"
        )
        
        # 搜索记忆
        result = await mm.memory_search(query="简洁")
        
        assert result is not None
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_memory_search_db_not_initialized(self):
        """测试数据库未初始化时搜索"""
        from core.memory_manager import HumanThinkingMemoryManager
        from agentscope.tool import ToolResponse
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        result = await mm.memory_search(query="测试")
        
        assert isinstance(result, ToolResponse)
        assert "Database not initialized" in result.content
    
    @pytest.mark.asyncio
    async def test_get_stats(self, temp_dir):
        """测试获取统计信息"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        
        stats = await mm.get_stats()
        
        assert "total_memories" in stats
        assert "cache_pool" in stats
        assert "current_session" in stats
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_create_session(self, temp_dir):
        """测试创建会话"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent",
            user_id="user_001"
        )
        
        await mm.start()
        
        result = await mm.create_session(
            session_id="new_session",
            trigger_context="测试上下文"
        )
        
        assert "session_id" in result
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_get_session_memories(self, temp_dir):
        """测试获取会话记忆"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent",
            current_session_id="session_001"
        )
        
        await mm.start()
        
        # 存储记忆
        await mm.store_memory(content="测试记忆", importance=3)
        
        memories = await mm.get_session_memories("session_001")
        
        assert isinstance(memories, list)
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_get_active_sessions(self, temp_dir):
        """测试获取活跃会话"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent",
            current_session_id="session_001"
        )
        
        await mm.start()
        
        await mm.store_memory(content="测试", importance=3)
        
        sessions = await mm.get_active_sessions()
        
        assert isinstance(sessions, list)
        assert len(sessions) >= 1
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_track_emotional_state(self, temp_dir):
        """测试跟踪情感状态"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent",
            user_id="user_001"
        )
        
        await mm.start()
        
        result = await mm.track_emotional_state(
            session_id="session_001",
            emotion="happy",
            intensity=0.8
        )
        
        assert "emotion" in result
        assert result["emotion"] == "happy"
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_get_emotional_context(self, temp_dir):
        """测试获取情感上下文"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent",
            user_id="user_001"
        )
        
        await mm.start()
        
        result = await mm.get_emotional_context("session_001")
        
        assert "current_emotion" in result
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_emotional_engine_disabled(self, temp_dir):
        """测试禁用情感引擎"""
        from core.memory_manager import HumanThinkingMemoryManager, get_config, update_config_fields
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        # 禁用情感引擎
        update_config_fields({"enable_emotion": False}, agent_id="test_agent")
        
        await mm.start()
        
        # 情感引擎应该为 None
        assert mm.emotional_engine is None
        
        # 调用情感相关方法应返回空结果
        result = await mm.track_emotional_state("session_001", "happy", 0.8)
        assert result == {}
        
        result = await mm.get_emotional_context("session_001")
        assert result == {}
        
        await mm.close()


# ==================== 记忆压缩测试 ====================

class TestMemoryCompaction:
    """测试记忆压缩功能"""
    
    @pytest.mark.asyncio
    async def test_compact_memory_empty(self):
        """测试空消息压缩"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        result = await mm.compact_memory(messages=[])
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_compact_memory_simple(self):
        """测试简单消息压缩"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        # 创建 Mock 消息
        mock_msg = MagicMock()
        mock_msg.content = "测试消息内容"
        mock_msg.role = "user"
        
        result = await mm.compact_memory(messages=[mock_msg])
        
        assert isinstance(result, str)
        assert "测试消息内容" in result
    
    @pytest.mark.asyncio
    async def test_summary_memory_empty(self):
        """测试空消息摘要"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        result = await mm.summary_memory(messages=[])
        assert result == ""
    
    @pytest.mark.asyncio
    async def test_summary_memory(self):
        """测试消息摘要"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        mock_msg = MagicMock()
        mock_msg.content = "这是需要摘要的内容"
        
        result = await mm.summary_memory(messages=[mock_msg])
        
        assert "这是需要摘要的内容" in result


# ==================== 上下文检查测试 ====================

class TestContextCheck:
    """测试上下文检查功能"""
    
    @pytest.mark.asyncio
    async def test_check_context_empty(self):
        """测试空消息上下文检查"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        to_compact, remaining, is_valid = await mm.check_context(messages=[])
        
        assert to_compact == []
        assert remaining == []
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_check_context_under_threshold(self):
        """测试未达阈值的上下文"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        mock_msg = MagicMock()
        mock_msg.content = "短消息"
        
        to_compact, remaining, is_valid = await mm.check_context(
            messages=[mock_msg],
            memory_compact_threshold=100000
        )
        
        assert to_compact == []
        assert len(remaining) == 1
        assert is_valid is True


# ==================== Prompt 和工具测试 ====================

class TestPromptsAndTools:
    """测试提示词和工具"""
    
    def test_get_memory_prompt_zh(self):
        """测试中文记忆提示词"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        prompt = mm.get_memory_prompt("zh")
        
        assert "HumanThinking" in prompt
        assert "memory_search" in prompt
    
    def test_get_memory_prompt_en(self):
        """测试英文记忆提示词"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        prompt = mm.get_memory_prompt("en")
        
        assert "HumanThinking" in prompt
        assert "memory_search" in prompt
    
    def test_get_memory_prompt_default(self):
        """测试默认语言提示词"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        prompt = mm.get_memory_prompt("unknown")
        
        assert "HumanThinking" in prompt
    
    def test_list_memory_tools(self):
        """测试列出记忆工具"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        tools = mm.list_memory_tools()
        
        assert isinstance(tools, list)


# ==================== 系统记忆初始化测试 ====================

class TestSystemMemory:
    """测试系统记忆初始化"""
    
    @pytest.mark.asyncio
    async def test_init_system_memory_first_time(self, temp_dir):
        """测试首次初始化系统记忆"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        
        # 检查系统记忆是否已写入
        memories = await mm.db.search_memories(
            agent_id="test_agent",
            query="HumanThinking 系统使用说明",
            max_results=1
        )
        
        assert len(memories) >= 1
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_init_system_memory_already_exists(self, temp_dir):
        """测试系统记忆已存在时跳过"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        
        # 再次调用应该跳过
        await mm._init_system_memory()
        
        # 应该只有一条系统记忆
        memories = await mm.db.search_memories(
            agent_id="test_agent",
            query="HumanThinking 系统使用说明",
            max_results=10
        )
        
        assert len(memories) == 1
        
        await mm.close()


# ==================== 桥接和会话管理测试 ====================

class TestSessionBridge:
    """测试会话桥接功能"""
    
    @pytest.mark.asyncio
    async def test_bridge_session(self, temp_dir):
        """测试桥接会话"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        
        result = await mm.bridge_session(
            old_session_id="old_session",
            new_session_id="new_session",
            trigger_context="测试上下文"
        )
        
        assert isinstance(result, dict)
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_close_session(self, temp_dir):
        """测试关闭会话"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        
        # 不应抛出异常
        await mm.close_session("session_001")
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_get_related_historical_memories(self, temp_dir):
        """测试获取相关历史记忆"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        
        result = await mm.get_related_historical_memories(
            context="测试上下文"
        )
        
        assert hasattr(result, 'memories')
        assert hasattr(result, 'total_count')
        
        await mm.close()


# ==================== InMemoryMemory 获取测试 ====================

class TestInMemoryMemory:
    """测试内存记忆获取"""
    
    def test_get_in_memory_memory(self, temp_dir):
        """测试获取内存记忆对象"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        memory = mm.get_in_memory_memory()
        
        assert memory is not None
        assert memory._memory_manager_ref is mm
        
        # 再次获取应该是同一个对象
        memory2 = mm.get_in_memory_memory()
        assert memory is memory2


# ==================== 后处理钩子测试 ====================

class TestPostOperation:
    """测试后处理操作"""
    
    @pytest.mark.asyncio
    async def test_post_memory_operation_completed(self, temp_dir):
        """测试完成的操作后处理"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        
        # 不应抛出异常
        await mm.post_memory_operation(
            agent_id="test_agent",
            session_id="session_001",
            user_id="user_001",
            operation_type="turn_end",
            status="completed"
        )
        
        await mm.close()
    
    @pytest.mark.asyncio
    async def test_post_memory_operation_not_completed(self, temp_dir):
        """测试未完成状态不触发刷新"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir=str(temp_dir),
            agent_id="test_agent"
        )
        
        await mm.start()
        
        # 未完成状态不应触发刷新
        await mm.post_memory_operation(
            agent_id="test_agent",
            session_id="session_001",
            user_id="user_001",
            operation_type="turn_end",
            status="failed"
        )
        
        await mm.close()


# ==================== 梦境和工具压缩测试 ====================

class TestDreamAndCompact:
    """测试梦境和工具压缩"""
    
    @pytest.mark.asyncio
    async def test_dream_memory(self):
        """测试梦境记忆"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        # 不应抛出异常
        await mm.dream_memory()
    
    @pytest.mark.asyncio
    async def test_compact_tool_result(self):
        """测试工具结果压缩"""
        from core.memory_manager import HumanThinkingMemoryManager
        
        mm = HumanThinkingMemoryManager(
            working_dir="/tmp/test",
            agent_id="test_agent"
        )
        
        # 不应抛出异常
        await mm.compact_tool_result()
