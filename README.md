# HumanThinking Memory Manager

> QwenPaw Agent 跨Session认知与情感连续性记忆管理器

## 概述

HumanThinking Memory Manager 是 QwenPaw V1.1.4.post2+ 的第三方记忆管理插件，**不修改 QwenPaw 源码**，通过官方插件机制集成。

支持：
- ✅ QwenPaw V1.1.4.post2+
- ✅ 官方 Console Plugin 侧边栏页面
- ✅ 跨 Session 记忆连续性
- ✅ 情感连续性引擎
- ✅ 多渠道支持
- ✅ Agent 配置隔离

***

## 核心特性

### 🧠 仿生记忆机制

HumanThinking 模拟人类大脑的记忆模式：

| 人类记忆特点 | HumanThinking 实现 |
|-------------|------------------|
| **短期记忆** | SessionBuffer - 当前会话消息缓冲 |
| **长期记忆** | HumanThinkingDB - SQLite 持久化存储 |
| **情境记忆** | SessionBridgeEngine - 跨 Session 自动继承 |
| **情感记忆** | EmotionalContinuityEngine - 情感状态跟踪 |
| **记忆冷藏** | freeze_memories() - 7天无访问自动冷藏 |
| **压缩提炼** | 原生 QwenPaw 压缩机制 |

### 🔄 记忆检索流程

```
用户输入 → get_memory()
              ↓
        从当前对话提取查询关键词
              ↓
        直接查询数据库（排除最近3轮）
              ↓
        构建上下文（最多5条，每条150字符）
              ↓
        返回给 LLM
```

### ✅ 技术特性

- **直接查 DB** — 简洁可靠，无缓存同步问题
- **原生压缩** — 复用 QwenPaw V1.1.3 上下文压缩
- **多渠道支持** — Web/Discord/飞书/微信等
- **Agent 隔离** — 每个 Agent 独立数据库
- **智能索引** — 复合索引加速查询

***

## 安装

### 方式一：官方插件安装（推荐）

```bash
# 方式1：从 GitHub 安装
qwenpaw plugin install https://github.com/kingsa2026/QwenPaw_HumanThinking_plugin/archive/refs/heads/main.zip

# 方式2：本地安装
# 将 HumanThinking 文件夹复制到 ~/.qwenpaw/plugins/
```

### 方式二：手动安装

```bash
# 1. 复制插件到 QwenPaw 插件目录
cp -r HumanThinking ~/.qwenpaw/plugins/HumanThinking

# 2. 关闭 QwenPaw
qwenpaw shutdown

# 3. 以 reload 模式启动（加载插件）
qwenpaw app --reload

# 4. 等待加载完成后关闭
qwenpaw shutdown

# 5. 正常启动
qwenpaw app
```

### 方式三：Docker 安装

如果 QwenPaw 使用的是 Docker：

```dockerfile
# 在 Dockerfile 中添加插件
COPY HumanThinking/ ~/.qwenpaw/plugins/HumanThinking
```

或挂载插件目录：

```bash
# 启动 QwenPaw 时挂载插件
docker run -v ~/.qwenpaw/plugins:/root/.qwenpaw/plugins ...
```

### 方式四：Windows 桌面端

```powershell
# 复制插件到 QwenPaw 插件目录
Copy-Item -Recurse HumanThinking "$env:USERPROFILE\.qwenpaw\plugins\HumanThinking"

# 重启 QwenPaw
qwenpaw shutdown
qwenpaw app
```

### 方式五：构建前端（如需自定义）

```bash
cd HumanThinking
npm install && npm run build
cp -r . ~/.qwenpaw/plugins/HumanThinking
```

***

## 使用

### 1. 启用插件

启动 QwenPaw 后，在侧边栏可以看到 **记忆管理** 和 **记忆设置** 页面。

### 2. 配置 Agent

在 Agent 配置中选择 **Memory Manager Backend: Human Thinking**：

```
Agent配置 → React Agent → Memory Manager Backend → Human Thinking
```

### 3. 配置 Agent 提示词

在你的 Agent 工作目录的 `AGENT.md` 顶部添加：

```markdown
# HumanThinking 记忆管理系统

## 前置说明

本 Agent 已配置使用 HumanThinking 作为记忆管理系统。
...
```

详见 [AGENT.md](AGENT.md)

***

## 侧边栏页面

安装后可在侧边栏访问：

| 页面 | 路径 | 说明 |
|------|------|------|
| 🧠 记忆管理 | `/plugin/humanthinking/dashboard` | 统计面板 + 最近记忆 |
| ⚙️ 记忆设置 | `/plugin/humanthinking/settings` | 插件信息 |

***

## 核心功能

### 1. 记忆存储

- **Session 缓冲** — 消息存入内存缓冲区
- **Idle 检测** — 180秒后自动刷新到数据库
- **完整性保证** — 确保对话完整后才写入

### 2. 上下文加载

- **直接查 DB** — 每次检索相关历史记忆
- **排除最近3轮** — 防止与原生压缩重复
- **重要性+时间排序** — 优先返回重要记忆

### 3. 跨 Session 记忆

- 新 Session 自动继承相关历史记忆
- 关键词关联检索
- 跨渠道（Web/飞书/Discord）记忆互通

### 4. 情感连续性

- 记录每轮对话的情感倾向
- 可查询历史情感变化
- 情感状态可注入上下文

***

## 数据库

### 文件位置

```
~/.qwenpaw/workspaces/{agent_id}/memory/human_thinking_{agent_id}.db
```

### 表结构

| 表名 | 说明 |
|------|------|
| qwenpaw_memory | 记忆主表（会话隔离） |
| qwenpaw_memory_relations | 记忆关联 |
| session_relationships | 跨会话关系 |
| session_emotional_continuity | 情感连续性 |

详见 [DATABASE.md](DATABASE.md)

***

## 配置参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| session_idle_timeout | 180秒 | 会话空闲检测阈值 |
| max_results | 5 | DB 查询返回数 |
| max_memory_chars | 150 | 单条记忆最大字符 |
| refresh_interval | 5 | 上下文刷新间隔(轮) |
| exclude_recent_rounds | 3 | 排除最近N轮对话 |

***

## 常见问题

### Q: 侧边栏没有显示记忆管理页面

A: 确保已正确安装插件，尝试重启 QwenPaw

### Q: 选择 HumanThinking 后保存报错

A: 需要重启 QwenPaw 让所有 worker 进程加载新配置

### Q: 记忆没有写入数据库

A: 确保 Agent 的 AGENT.md 中已配置使用 HumanThinking

### Q: 上下文超过限制

A: v1.1.0 已修复，使用原生压缩机制 + 排除最近3轮策略

***

## 版本

**v1.4.1** - 适配 QwenPaw V1.1.4.post2

- 兼容 QwenPaw V1.1.4.post2
- Agent 配置隔离支持
- Storage 事件监听优化 Agent 切换检测
- 无痕模式兼容性修复

**v1.4.0** - 适配 QwenPaw V1.1.4.post1

- 初始版本支持
- 官方 Console Plugin 支持
- 侧边栏页面（记忆管理 + 记忆设置）
- 直接查 DB 检索
- 原生压缩机制
- 排除最近3轮防止重复

***

## 许可

MIT License
