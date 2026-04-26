# HumanThinking 记忆管理系统 - Agent 使用指南

> 本文档路径：`/root/.qwenpaw/plugins/HumanThinking/agent-read.md`
> 版本：v1.4.1
> 首次阅读后，请将要点记入你的记忆数据库（importance=5）

---

## 一、系统概述

HumanThinking 是你的专属记忆管理系统。它替代了传统的 MEMORY.md 文件记忆方式，提供更智能、更持久的记忆能力。

**核心特点：**
- ✅ 自动存储 - 对话结束后自动保存重要内容
- ✅ 跨会话 - 永久保留，不受会话重启影响
- ✅ 智能检索 - 关键词匹配 + 重要性排序 + 时间优先
- ✅ Agent 隔离 - 每个 Agent 拥有独立的记忆空间
- ✅ 睡眠整理 - 空闲时自动整理记忆，提取洞察

---

## 二、数据库架构

HumanThinking 使用 SQLite 数据库存储记忆，主要包含以下表：

### 1. qwenpaw_memory（主表）
存储所有活跃记忆：
- `id` - 记忆唯一标识
- `agent_id` - Agent 标识（实现 Agent 隔离）
- `session_id` - 会话标识
- `content` - 记忆内容
- `importance` - 重要性（1-5级）
- `memory_type` - 记忆类型：fact / preference / emotion / general
- `created_at` - 创建时间
- `access_count` - 访问次数（用于遗忘曲线）
- `metadata` - 元数据（JSON格式）

### 2. qwenpaw_memory_archive（归档表）
存储长期不访问的冷记忆：
- 当记忆超过 `archive_days` 未访问时自动归档
- 归档记忆仍可通过搜索找回

### 3. humanthinking_insights（洞察表）
存储睡眠期间生成的洞察：
- 睡眠时会分析记忆，提取模式和洞察
- 洞察可以帮助你更好地理解用户

### 4. session_emotional_continuity（情感表）
存储情感状态：
- 跟踪用户的情感变化
- 实现情感连续性

---

## 三、记忆类型说明

存储记忆时，请正确选择记忆类型：

| 类型 | 说明 | 示例 |
|------|------|------|
| **fact** | 客观事实 | 用户姓名、职业、项目信息 |
| **preference** | 用户偏好 | 喜欢的颜色、工作习惯 |
| **emotion** | 情感状态 | 用户的情绪变化 |
| **general** | 一般信息 | 其他不适合分类的信息 |

**重要性分级：**
- 1 - 不重要，可遗忘
- 2 - 不太重要
- 3 - 一般重要（默认）
- 4 - 很重要
- 5 - 极其重要（如系统说明、关键配置）

---

## 四、可用工具

### 1. memory_search - 记忆搜索
```
memory_search(query="关键词", max_results=5)
```

**使用场景：**
- 用户问"之前我跟你说过的..."
- 用户问"我之前提到过..."
- 用户提到之前的话题
- 需要回忆之前的决策或信息

**示例：**
```
用户："我上次跟你说的那个电影叫什么来着？"
你：memory_search(query="电影")
回答："根据之前的记录，您提到过最喜欢的电影是《盗梦空间》。"
```

### 2. get_stats - 记忆统计
```
get_stats()
```

返回记忆库的整体状态，包括：
- 总记忆数
- 跨会话记忆数
- 冷藏记忆数
- 活跃会话数

---

## 五、睡眠功能

### 什么是睡眠？
睡眠是 HumanThinking 的自动整理机制。当 Agent 空闲时，系统会：

1. **合并相似记忆** - 将内容相似的记忆合并
2. **提取洞察** - 从大量记忆中提取模式和见解
3. **归档旧记忆** - 将长期不访问的记忆移到归档表
4. **更新情感模型** - 分析用户的情感变化趋势

### 睡眠触发条件
- 自动：Agent 空闲超过配置时间
- 手动：通过 API 触发

### 查看睡眠状态
```
GET /api/plugins/humanthinking/sleep/status
```

### 查看睡眠洞察
```
GET /api/plugins/humanthinking/sleep/insight
```

---

## 六、重要原则

### ❌ 不要做的事情
1. **不要手动创建 MEMORY.md** - 系统会自动管理记忆
2. **不要手动创建 memory/YYYY-MM-DD.md** - 使用数据库存储
3. **不要重复记录相同信息** - 系统会自动去重

### ✅ 应该做的事情
1. **主动使用记忆搜索** - 当用户提到过往内容时，先搜索再回答
2. **正确标记记忆类型** - 帮助系统更好地组织记忆
3. **标记重要信息** - 重要性 4-5 级的记忆更容易被检索
4. **让系统自动处理** - 记忆的存储和整理是自动的

---

## 七、Agent 隔离说明

**重要：每个 Agent 的记忆是完全隔离的！**

- Agent A 无法访问 Agent B 的记忆
- 每个 Agent 有自己的数据库文件：`human_thinking_memory_{agent_id}.db`
- 切换 Agent 时，记忆空间也会切换

这意味着：
- 你需要为每个 Agent 单独建立记忆
- 系统记忆（如本说明）也会按 Agent 隔离

---

## 八、首次使用建议

作为 Agent，建议你：

1. **阅读本文档** - 了解 HumanThinking 的工作原理
2. **将要点记入记忆** - 使用 `store_memory` 将重要信息保存（importance=5）
3. **实践使用** - 在对话中主动使用 `memory_search`
4. **观察睡眠洞察** - 定期查看睡眠生成的洞察

---

## 九、常见问题

**Q: 我需要手动管理记忆文件吗？**
A: 不需要。HumanThinking 会自动处理所有记忆的存储和检索。

**Q: 记忆会丢失吗？**
A: 不会。记忆存储在 SQLite 数据库中，持久化保存。

**Q: 如何确保重要记忆不被遗忘？**
A: 设置高重要性（4-5级），系统会优先保留和检索重要记忆。

**Q: 睡眠期间会丢失记忆吗？**
A: 不会。睡眠只是整理和归档，不会删除重要记忆。

---

## 十、API 参考

### Health 检查
```
GET /api/plugins/humanthinking/health
```

### 记忆统计
```
GET /api/plugins/humanthinking/stats
```

### 睡眠状态
```
GET /api/plugins/humanthinking/sleep/status
```

### 睡眠洞察
```
GET /api/plugins/humanthinking/sleep/insight
```

---

*本文档由 HumanThinking v1.4.1 生成*
*最后更新：2026-04-26*
