# HumanThinking Memory Manager - 功能文档

## 1. 项目概述

HumanThinking 是一个仿生记忆管理系统，模拟人类记忆机制，为 AI Agent 提供跨会话的认知与情感连续性记忆能力。

## 2. 核心架构

### 2.1 模块结构

```
HumanThinking/
├── plugin.py                 # 插件入口
├── core/
│   ├── database.py          # 数据库管理
│   ├── memory_manager.py     # 记忆管理器
│   ├── session_buffer.py     # 会话缓冲
│   ├── cache_pool.py        # 缓存池
│   ├── sleep_manager.py      # 睡眠管理器
│   ├── emotional_engine.py   # 情感引擎
│   ├── session_bridge.py     # 会话桥接
│   ├── channel_aware_manager.py  # 渠道感知
│   └── ...
├── search/
│   ├── cross_session_searcher.py  # 跨Session检索
│   ├── agentic_retriever.py      # Agentic检索
│   └── ...
├── hooks/
│   ├── memory_hooks.py      # 记忆钩子
│   └── feishu_message_parser.py  # 飞书消息解析
└── dist/
    └── index.js             # 前端UI
```

## 3. 核心功能

### 3.1 记忆存储

- **会话隔离**: 按 AgentID + UserID + SessionID 隔离
- **记忆类型**: fact / preference / emotion / general
- **记忆层级**: sensory / working / short_term / long_term / archived
- **记忆分类**: episodic / semantic / procedural

### 3.2 跨 Session 记忆

- 自动关联相关历史会话
- 基于相似度检索跨会话记忆
- 重要性 + 时间衰减排序

### 3.3 情感连续性

- 跟踪对话情感变化
- 维护情感状态上下文
- 注入情感状态到生成内容

### 3.4 睡眠模式

- 空闲自动进入睡眠
- 心跳/任务唤醒
- 自动整理记忆
- 生成洞察与梦境日记

### 3.5 遗忘曲线

- 基于访问频率和重要性
- 自动归档低价值记忆
- 优化 Token 使用

## 4. 数据库表结构

### 4.1 核心记忆表 qwenpaw_memory

| 字段 | 类型 | 说明 |
|------|------|------|
| agent_id | TEXT | Agent ID |
| session_id | TEXT | 会话 ID |
| user_id | TEXT | 用户 ID |
| target_id | TEXT | 对话对象 ID |
| content | TEXT | 记忆内容 |
| memory_tier | TEXT | 记忆层级 |
| memory_category | TEXT | 记忆分类 |
| memory_type | TEXT | 记忆类型 |
| importance | INTEGER | 重要性 1-5 |
| decay_score | REAL | 遗忘分数 |
| access_count | INTEGER | 访问次数 |
| access_frozen | INTEGER | 冷藏状态 |

### 4.2 其他表

| 表名 | 用途 |
|------|------|
| qwenpaw_memory_relations | 记忆关联 |
| session_relationships | 会话关系 |
| session_emotional_continuity | 情感连续性 |
| humanthinking_insights | 洞察 |
| humanthinking_dream_logs | 梦境日记 |
| memory_access_log | 访问日志 |
| memory_working_cache | 工作缓存 |

## 5. 前端功能

### 5.1 侧边栏页面

| 页面 | 路径 | 功能 |
|------|------|------|
| 记忆管理 | /plugin/humanthinking/dashboard | 总览 + Agent列表 |
| 睡眠模式 | /plugin/humanthinking/sleep | 睡眠配置 |
| 记忆设置 | /plugin/humanthinking/settings | 功能开关 |

### 5.2 记忆管理

- 统计卡片（Agent数、记忆数等）
- Agent列表（显示大小、时间、类型统计）
- 备份设置（自动/手动）

### 5.3 睡眠设置

- 睡眠开关
- 空闲时间
- 自动整理配置
- 洞察生成开关
- 梦境日记开关

### 5.4 记忆设置

- 跨Session记忆开关
- 情感连续性开关
- 会话隔离开关
- 记忆冷藏开关

## 6. API 接口

### 6.1 记忆存储

```python
await memory_manager.store_memory(
    content: str,           # 记忆内容
    role: str,              # 角色
    memory_type: str,       # 记忆类型
    importance: int,         # 重要性 1-5
    session_id: str,         # 会话ID
    user_id: str,           # 用户ID
    metadata: dict = {}      # 元数据
)
```

### 6.2 记忆检索

```python
memories = await memory_manager.search_memories(
    query: str,             # 查询内容
    session_id: str,        # 当前会话ID
    user_id: str,          # 用户ID
    cross_session: bool,    # 是否跨Session
    max_tokens: int,       # 最大Token
    time_filter_hours: int # 时间过滤
)
```

### 6.3 统计接口

```python
stats = await db.get_stats(agent_id)
tier_stats = await db.get_tier_stats(agent_id)
category_stats = await db.get_category_stats(agent_id)
```

## 7. 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| enable_cross_session | true | 跨Session记忆 |
| enable_emotion | true | 情感连续性 |
| enable_session_isolation | true | 会话隔离 |
| enable_memory_freeze | true | 记忆冷藏 |
| session_idle_timeout | 180 | 会话空闲超时(秒) |

## 8. 安装使用

### 8.1 安装

```bash
# 克隆项目
git clone https://github.com/kingsa2026/QwenPaw_HumanThinking_plugin.git

# 复制到 QwenPaw 插件目录
cp -r HumanThinking ~/.qwenpaw/plugins/

# 重启 QwenPaw
qwenpaw shutdown && qwenpaw app
```

### 8.2 配置

1. 在 QwenPaw Console 选择 "Human Thinking" 作为 Memory Manager Backend
2. 访问侧边栏配置功能

## 9. 版本信息

当前版本: 1.x.x

## 10. 技术栈

- Python 3.10+
- SQLite
- React + Ant Design (前端)
- QwenPaw Plugin System
