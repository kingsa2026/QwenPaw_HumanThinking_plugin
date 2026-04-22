# HumanThinking Memory Manager(AI电商团队必备)

> QwenPaw Agent 跨Session认知与情感连续性记忆管理器

## 概述

HumanThinking Memory Manager 是 QwenPaw 的第三方记忆管理插件，**不修改 QwenPaw 源码**，通过插件机制集成。

***

## 核心特性（仿生记忆）

### 🧠 仿生记忆机制

HumanThinking 模拟人类大脑的记忆模式，实现更自然的认知连续性：

| 人类记忆特点   | HumanThinking 实现 | 代码组件                                             |
| -------- | ---------------- | ------------------------------------------------ |
| **短期记忆** | 当前会话消息缓冲         | `SessionBuffer` - 线程安全会话缓冲                       |
| **工作记忆** | 快速检索历史上下文        | `ReadCache` - LRU缓存，读缓存                          |
| **长期记忆** | 持久化存储            | `HumanThinkingDB` - SQLite数据库                    |
| **情境记忆** | 跨Session记忆桥接     | `SessionBridgeEngine` - 自动继承历史                   |
| **情感记忆** | 跟踪情绪变化           | `EmotionalContinuityEngine` - 情感状态维护             |
| **记忆热度** | 动态调整记忆活跃度        | `MemoryTemperature` - 热度计算(HOT/WARM/COOL/FROZEN) |
| **记忆冷藏** | 7天无访问自动冷藏        | `freeze_memories()` - 冷藏低频记忆，释放缓存空间              |
| **记忆遗忘** | 不活跃会话自动清理        | LRU淘汰 + 会话冷却(600秒)                               |
| **压缩提炼** | 超阈值时LLM摘要        | `check_context()` + `compact_memory()`           |

### 🔄 记忆检索与加载

HumanThinking 的记忆检索机制（基于实际代码实现）：

```
用户输入 → ContextLoadingInMemory.get_memory()
                 │
                 ├── 1. 刷新检测 (每5轮刷新)
                 │
                 ├── 2. 检索流程 (_load_context_from_cache)
                 │      │
                 │      ├── 从当前对话提取查询关键词
                 │      │
                 │      └── 直接查询数据库
                 │             ├── HumanThinkingDB.search_memories()
                 │             ├── 关键词 LIKE 匹配
                 │             ├── 排除最近3轮（防止与原生压缩重复）
                 │             ├── 重要性 + 就近时间排序
                 │             └── 最多返回5条
                 │
                 └── 3. 上下文构建
                       ├── 最多5条(max_results=5)
                       ├── 每条150字符(max_memory_chars=150)
                       └── 包含渠道来源标识
                 
                 ↓
        原生压缩机制处理当前会话消息
                 ↓
        返回完整上下文给 LLM
```

**简化后的检索流程**：

| 步骤 | 操作     | 说明                                |
| -- | ------ | --------------------------------- |
| 1  | 提取查询词  | 从当前对话内容提取                         |
| 2  | 直接查 DB | 使用 `exclude_recent_rounds=3` 防止重复 |
| 3  | 构建上下文  | 最多5条，每条150字符                      |

**注意**：不使用读缓存，直接查 DB 更简洁可靠。

***

### ✅ 技术特性

- 直接查 DB 检索 — 简洁可靠，无缓存同步问题
- 原生压缩机制 — 使用 QwenPaw 自带的上下文压缩
- 多渠道支持 — Web/Discord/飞书/微信等
- Agent隔离 — 每个Agent独立缓存和数据库
- 智能索引优化 — 复合索引加速查询

***

## 安装

### 第一步：将HumanThinking放入/.qwenpaw/plugins文件夹下，如果没有可以手动创建

```bash
mkdir -p .qwenpaw/plugins
```

### 第二步：运行

```bash
qwenpaw shutdown
```

### 第三步：运行

```bash
qwenpaw app --reload
```

### 第四步：再次运行

```bash
qwenpaw shutdown
```

### 第🈚步：运行

```bash
qwenpaw app
```

### 第六步：启动WebUI界面，在 QwenPaw UI 中选择 **Memory Manager Backend: Human Thinking** 

### 第七步：保存后重启QwenPaw即可（一定要重启，否则不生效）。

注意：不同的Agent需要左上角切换后分别开启

### 第八步：重要！把Agent.md中的内容复制进你的agent工作目录中的agent.md顶部

***

## 核心功能

### 1. 记忆存储（写缓存）

- **Session缓冲**：每轮对话的消息先存入内存缓冲区
- **Idle检测**：对话结束后180秒自动刷新到数据库
- **完整性保证**：确保一轮对话完整后才写入

### 2. 上下文加载

- **直接查DB**：每次从数据库检索相关历史记忆
- **排除最近3轮**：防止与原生压缩机制重复
- **重要性+时间排序**：优先返回重要的近期记忆
- **按序加载**：每5轮对话刷新一次上下文

### 3. 跨Session记忆

- **自动桥接**：新Session自动继承相关历史记忆
- **关键词关联**：基于对话内容检索历史
- **跨渠道**：同一Agent在Web/Discord/飞书的对话可互相检索

  为什么要跨Session？
- 想象一下：你给一个朋友发微信说晚上一起吃火锅，他回复你收到了，然后你又打电话问他，问他吃哪家的火锅，他回答你：什么火锅？什么时候要吃火锅了？
- QwenPaw中有agent之间的沟通会话sesson，而且都是一次性的，那么这记忆不就混乱了？每次会话都是陌生人么？

### 4. 情感连续性

- **状态跟踪**：记录每轮对话的情感倾向
- **历史情感**：可查询历史情感变化曲线
- **上下文注入**：情感状态可注入对话上下文

***

## 搜索机制

### 关键词 + 重要性 + 就近时间

```
ORDER BY importance DESC, created_at DESC
```

| 策略       | 说明                      |
| -------- | ----------------------- |
| 关键词匹配    | LIKE 子字符串匹配             |
| 重要性排序    | importance DESC         |
| 就近时间     | created\_at DESC（最新的在前） |
| 跨Session | cross\_session=True     |

***

## 上下文压缩

触发条件：总token > 96K (128K × 75%)

压缩流程：

```
消息 → check_context()
  ├── ≤96K: 不压缩
  └── >96K: 分割消息
        ├── 旧消息 → LLM压缩为摘要
        └── 新消息(≤12.8K) → 保留
```

***

## 数据库结构

### 文件位置

```
~/.qwenpaw/workspaces/{agent_id}/memory/human_thinking_{agent_id}.db
```

### 表结构

| 表名                             | 说明         |
| ------------------------------ | ---------- |
| qwenpaw\_memory                | 记忆主表（会话隔离） |
| qwenpaw\_memory\_relations     | 记忆关联       |
| session\_relationships         | 跨会话关系      |
| session\_emotional\_continuity | 情感连续性      |
| qwenpaw\_memory\_version       | 版本管理       |

详见 [DATABASE.md](DATABASE.md)

***

## 配置参数

| 参数                        | 默认值   | 说明         |
| ------------------------- | ----- | ---------- |
| `session_idle_timeout`    | 180秒  | 会话空闲检测阈值   |
| `max_results_db_miss`     | 5     | 缓存未命中DB查询数 |
| `max_results_db_hit`      | 3     | 缓存命中DB补充数  |
| `max_memory_chars`        | 150   | 单条记忆最大字符   |
| `refresh_interval`        | 5     | 上下文刷新间隔(轮) |
| `read_cache_max_items`    | 500   | 读缓存最大条数    |
| `read_cache_max_chars`    | 512KB | 读缓存最大字符    |
| `read_cache_session_idle` | 600秒  | 读缓存会话冷却    |

***

## 使用方法

### UI选择

```
Agent配置 → React Agent → Memory Manager Backend → Human Thinking
```

### 配置文件

```json
{
  "agents": {
    "running": {
      "memory_manager_backend": "human_thinking"
    }
  }
}
```

***

## 常见问题

### Q: 选择HumanThinking后保存报错

A: 需要重启QwenPaw让所有worker进程加载新配置。

### Q: 下拉菜单不显示HumanThink选项

A: 清除浏览器缓存，或使用无痕模式。

### Q: 记忆没有写入数据库

A：你要在agent工作目录里面的AGENT.MD中告诉他，你是用的是HUmanThinking记忆管理系统

B：检查session是否Idle（180秒无活动），或手动调用 `await cache_pool.flush()`。

***

## 版本

**v1.1.0** - 架构版本

- 直接查 DB 检索 — 简洁可靠
- 原生压缩机制 — 复用 QwenPaw
- 排除最近3轮 — 防止重复
- 跨Session记忆
- 情感连续性
- 多渠道支持

***

## 许可

MIT License
