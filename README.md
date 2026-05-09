# HumanThinking Memory Manager

> QwenPaw 智能体记忆系统增强插件 — 跨会话认知连续 · 情感追踪 · 语义检索 · 智能睡眠

[![Version](https://img.shields.io/badge/version-1.5.0-blue)](https://github.com/kingsa2026/QwenPaw_HumanThinking_plugin)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![QwenPaw](https://img.shields.io/badge/QwenPaw-1.1.5+-orange)](https://github.com/kingsa2026/QwenPaw_HumanThinking_plugin)

---

## 概述

HumanThinking Memory Manager 是 QwenPaw 的第三方记忆管理插件，**不修改 QwenPaw 源码**，通过官方 Console Plugin 机制集成。为智能体提供仿生记忆能力、情感连续性、语义搜索和智能睡眠压缩。

### 兼容性

| 环境 | 支持 |
|------|------|
| QwenPaw | 1.1.5+ |
| 安装方式 | Console Plugin 侧边栏 |
| Python | 3.10+ |
| 数据库 | SQLite (per-agent) |

---

## 架构

```
┌─────────────────────────────────────────────────────┐
│                   QwenPaw Console                    │
│  ┌──────────────┐  ┌──────────────┐                 │
│  │ 记忆管理面板  │  │ 睡眠配置面板  │                 │
│  │  统计/会话/   │  │  压缩参数/    │                 │
│  │  情绪/时间线  │  │  触发策略     │                 │
│  └──────┬───────┘  └──────┬───────┘                 │
│         │                 │                          │
│  ┌──────┴─────────────────┴───────┐                 │
│  │       frontend.js (React)      │                 │
│  │   1500ms 防抖 · 无 AbortController  │            │
│  └──────────────┬─────────────────┘                 │
└─────────────────┼───────────────────────────────────┘
                  │ HTTP API (/api/plugins/humanthinking/)
┌─────────────────┼───────────────────────────────────┐
│            plugin.py (FastAPI Plugin)                │
│  ┌──────────────┼──────────────────────────────┐    │
│  │           api/routes.py                     │    │
│  │  /stats  /sessions  /emotion  /timeline     │    │
│  │  /search  /memories  /sleep/config          │    │
│  │  /config  /semantic-search  /lifecycle      │    │
│  └──────────────┼──────────────────────────────┘    │
│         ┌───────┴────────┐                          │
│         │   core/ (20 modules)  │                    │
│         ├────────────────┤                          │
│         │ MemoryManager  │ 记忆增删改查               │
│         │ SleepManager   │ 智能睡眠压缩               │
│         │ EmotionalEngine│ 情感追踪分析               │
│         │ SessionBridge  │ 跨会话继承                 │
│         │ VectorStore    │ 向量语义搜索               │
│         │ MemoryLifecycle│ 生命周期管理               │
│         │ CachePool      │ 连接池优化                 │
│         │ ChannelAdapter │ 多通道适配                 │
│         └───────┬────────┘                          │
│         ┌───────┴────────┐                          │
│         │  search/ (6 modules)  │                    │
│         ├────────────────┤                          │
│         │ CrossSession   │ 跨会话搜索                │
│         │ AgenticRetriev.│ 智能检索                  │
│         │ RelevanceRanker│ 相关性排序                │
│         └───────┬────────┘                          │
│              SQLite DB (per-agent)                   │
└─────────────────────────────────────────────────────┘
```

---

## 核心特性

### 🧠 仿生记忆机制

| 人类记忆 | HumanThinking 实现 | 模块 |
|---------|-------------------|------|
| **短期记忆** | SessionBuffer — 当前会话消息缓冲 | `session_buffer.py` |
| **工作记忆** | 会话上下文窗口管理 | `context_checker.py` |
| **长期记忆** | SQLite 持久化 + 多维度索引 | `database.py` |
| **情境记忆** | SessionBridge — 跨会话自动继承 | `session_bridge.py` |
| **情感记忆** | EmotionalEngine — 情感状态追踪 | `emotional_engine.py` |
| **记忆温度** | 访问频率驱动的热/温/冷分级 | `memory_temperature.py` |
| **记忆冷藏** | MemoryLifecycle — 自动归档与清理 | `memory_lifecycle.py` |
| **睡眠压缩** | SleepManager — 阶段性摘要压缩 | `sleep_manager.py` |

### 🔍 智能检索

| 能力 | 说明 |
|------|------|
| **语义搜索** | 向量相似度检索 (VectorStore) |
| **跨会话搜索** | 跨 Session 记忆关联查询 |
| **智能检索** | AgenticRetriever — 多策略融合检索 |
| **相关性排序** | RelevanceRanker — 时间+重要性排序 |

### 🛠 辅助能力

- **矛盾检测** — ContradictionDetector 自动发现冲突记忆
- **异步摘要** — AsyncSummarizer 后台摘要生成
- **LLM 压缩** — LLMCompactor 调用 LLM 进行记忆压缩
- **工具结果压缩** — ToolResultCompactor 压缩工具调用结果
- **多通道适配** — ChannelAdapter 支持 Web/Discord/飞书/企微
- **文件记忆** — FileMemoryStore 文件内容记忆存储
- **备份管理** — BackupManager 自动定时备份
- **缓存连接池** — CachePool WAL 模式 + 共享缓存优化

---

## 快速开始

### 安装

```bash
# 1. 复制插件到 QwenPaw 插件目录
cp -r HumanThinking ~/.qwenpaw/plugins/HumanThinking

# 2. 重启 QwenPaw（需两次）
qwenpaw shutdown
qwenpaw app

# 3. 配置 Agent Memory Manager Backend
# 控制台 → Agent 配置 → Memory Manager Backend → Human Thinking
```

### 手动安装（完整步骤）

```bash
cp -r HumanThinking ~/.qwenpaw/plugins/HumanThinking
qwenpaw shutdown
qwenpaw app --reload
# 等待加载完成
qwenpaw shutdown
qwenpaw app
```

### Docker

```bash
# 挂载插件目录
docker run -v ~/.qwenpaw/plugins:/root/.qwenpaw/plugins ...
```

---

## 侧边栏面板

安装后在 QwenPaw 控制台侧边栏可见：

| 面板 | 功能 |
|------|------|
| 🧠 **记忆管理** | 统计面板 · 记忆列表 · 会话记录 · 情感趋势 · 时间线 |
| 😴 **睡眠配置** | 压缩参数 · 触发策略 · 摘要配置 |

---

## 数据库

Per-agent 独立数据库（SQLite WAL 模式）：

```
~/.qwenpaw/workspaces/{agent_id}/memory/human_thinking_memory_{agent_id}.db
```

| 表 | 用途 |
|---|------|
| `qwenpaw_memory` | 记忆主表 |
| `qwenpaw_memory_relations` | 记忆关联 |
| `session_relationships` | 跨会话关系 |
| `session_emotional_continuity` | 情感连续性 |

详见 [DATABASE.md](DATABASE.md)

---

## 项目结构

```
HumanThinking/
├── plugin.py              # 插件入口 · API 注册 · 生命周期
├── plugin.json            # 插件元信息
├── frontend.js            # React 侧边栏 UI (24KB)
├── prod_ui_patcher.py     # QwenPaw 生产包注入
├── api/
│   ├── routes.py          # FastAPI 路由 (13 endpoints)
│   └── error_handler.py   # 统一错误处理
├── core/                  # 20 个核心模块
│   ├── memory_manager.py  # 记忆增删改查
│   ├── sleep_manager.py   # 智能睡眠压缩
│   ├── emotional_engine.py# 情感追踪分析
│   ├── session_bridge.py  # 跨会话继承
│   ├── database.py        # SQLite 封装
│   ├── cache_pool.py      # 连接池 (WAL + shared cache)
│   ├── memory_lifecycle.py# 生命周期管理
│   ├── memory_temperature.py # 记忆温度分级
│   ├── channel_adapter.py # 多通道适配
│   ├── channel_aware_manager.py # 通道感知管理
│   ├── context_checker.py # 上下文窗口
│   ├── contradiction_detector.py # 矛盾检测
│   ├── session_buffer.py  # 会话缓冲
│   ├── async_summarizer.py# 异步摘要
│   ├── llm_compactor.py   # LLM 压缩
│   ├── tool_result_compactor.py # 工具结果压缩
│   ├── file_memory_store.py # 文件记忆
│   └── backup_manager.py  # 自动备份
├── search/                # 6 个检索模块
│   ├── vector.py          # 向量存储
│   ├── cross_session_searcher.py # 跨会话搜索
│   ├── agentic_retriever.py # 智能检索
│   ├── relevance_ranker.py # 相关性排序
│   ├── specialized_retrievers.py # 专项检索
│   └── vector_store_backend.py # 向量后端
├── hooks/                 # 飞书钩子
│   └── feishu_message_parser.py
├── utils/                 # 工具函数
│   └── logger.py
├── tests/                 # 8 个单元测试
│   ├── test_memory_manager.py
│   ├── test_sleep_manager.py
│   ├── test_database.py
│   ├── test_routes.py
│   ├── test_contradiction_detector.py
│   ├── test_version.py
│   └── conftest.py
├── locales/               # 国际化 (en/ja/ru/zh)
├── img/                   # GIF 素材
├── docs/                  # 文档
│   ├── CODE_STANDARDS.md
│   └── FEATURES.md
├── DATABASE.md            # 数据库文档
├── CHANGELOG.md           # 更新日志
└── README.md              # 本文件
```

---

## API 端点

Base URL: `http://localhost:8088/api/plugins/humanthinking`

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/stats?agent_id=` | 记忆统计 (总数/重要性分布/类型分布) |
| GET | `/sessions?agent_id=` | 会话列表 |
| GET | `/emotion?agent_id=` | 情感趋势分析 |
| GET | `/memories/timeline?agent_id=&group_by=` | 记忆时间线 (day/week/month) |
| GET | `/memories?agent_id=&page=&limit=` | 记忆分页列表 |
| GET | `/sleep/config?agent_id=` | 睡眠配置查询 |
| POST | `/sleep/config?agent_id=` | 睡眠配置更新 |
| POST | `/memories/search` | 关键词搜索 |
| POST | `/semantic-search` | 语义向量搜索 |
| POST | `/lifecycle/{action}` | 生命周期操作 (freeze/archive/purge) |

---

## 最近更新 (v1.5.0)

- **前端重构**: 彻底移除 AbortController，消除 `net::ERR_ABORTED` 错误
- **防抖优化**: 所有代理轮询延迟从 500ms → 1500ms
- **Bug 修复**: `prod_ui_patcher.py` `_DEBUG` 未定义错误
- **代码整理**: 统一项目结构，移除冗余文件

详见 [CHANGELOG.md](CHANGELOG.md)

---

## 常见问题

**Q: 侧边栏未显示记忆管理面板**

A: 确保已正确安装插件，重启 QwenPaw 两次。检查日志: `qwenpaw.log`

**Q: 切换智能体时记忆统计不加载**

A: v1.5.0 已修复。若仍有问题，清除浏览器缓存后重试。

**Q: 记忆没有写入数据库**

A: 确认 Agent 配置中 Memory Manager Backend 已选为 Human Thinking。

**Q: Docker 环境下数据库无法创建**

A: v1.4.4 已修复，启动时自动为所有 Agent 创建数据库和配置。

---

## 许可

MIT License