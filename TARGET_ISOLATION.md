# HumanThinking 会话对象隔离机制

## 核心设计

HumanThinking 通过 `target_id`（对话对象标识）实现会话对象的精确区分，确保不同对话方的记忆完全隔离，同时允许同一用户跨 Session 共享记忆。

## 隔离规则

### 场景1：Agent间对话隔离

```
AgentB 与 AgentA 对话：
  - agent_id = "AgentB"
  - target_id = "AgentA"
  - 记忆存储在 AgentB 的 "AgentA 对话空间"

AgentB 与 AgentC 对话：
  - agent_id = "AgentB"
  - target_id = "AgentC"
  - 记忆存储在 AgentB 的 "AgentC 对话空间"

结果：两个对话空间完全隔离，互不影响
```

### 场景2：同一用户跨Session记忆共享

```
用户U 通过 Session1 与 AgentB 对话：
  - agent_id = "AgentB"
  - user_id = "user_U"
  - target_id = "user_U"
  - session_id = "session_001"
  - 记忆检索：target_id="user_U" → 包含所有历史记忆

用户U 通过 Session2 与 AgentB 对话：
  - agent_id = "AgentB"
  - user_id = "user_U"
  - target_id = "user_U"
  - session_id = "session_002"
  - 记忆检索：target_id="user_U" → 共享 Session1 的记忆

结果：同一用户跨Session记忆共享，AgentB 能记住之前的对话内容
```

## 记忆键格式

```
{agent_id}:{target_id}:{channel_id}:{user_id}

示例：
AgentB_vs_AgentA_feishu:ou_xxx        # AgentB与AgentA的飞书对话
AgentB_vs_AgentC_wechat:wx_user       # AgentB与AgentC的微信对话
AgentB_vs_userU_wechat:wx_user        # AgentB与用户U的微信对话（Session1）
AgentB_vs_userU_telegram:tg_user      # AgentB与用户U的Telegram对话（Session2，记忆共享）
```

**关键设计**：`session_id` 不在记忆键中，实现跨Session记忆共享！

## 数据库设计

### qwenpaw_memory 表

```sql
CREATE TABLE qwenpaw_memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- 核心隔离字段
    agent_id TEXT NOT NULL,           -- 当前Agent
    target_id TEXT,                   -- 对话对象ID（区分不同Agent/用户）
    user_id TEXT,                     -- 发起者ID
    session_id TEXT NOT NULL,         -- 会话ID（用于上下文，不用于隔离）
    ...
    
    -- 索引
    idx_memory_agent_target ON (agent_id, target_id),
    idx_memory_full_context ON (agent_id, target_id, user_id)
);
```

### session_key 生成

```python
# session_key 用于确保不同对话对象的记忆隔离
session_key = f"{agent_id}_{target_id or user_id}_{session_id}"

# 示例：
# AgentB_vs_AgentA_session1
# AgentB_vs_userU_session2
```

## 渠道适配

各渠道的 `target_id` 提取策略：

### 飞书 (Feishu)
```python
# 群聊：target_id = chat_id
# 单聊：target_id = sender_id (open_id)
if chat_type == "group":
    return meta.get("feishu_chat_id")
return meta.get("feishu_sender_id")
```

### 微信 (WeChat)
```python
# 群聊：target_id = group_id
# 单聊：target_id = sender_id
if group_id:
    return group_id
return payload.get("sender_id")
```

### QQ
```python
# 群聊：target_id = group_openid
# 频道：target_id = channel_id
# 私聊：target_id = user_id
if msg_type == "group":
    return meta.get("group_openid")
elif msg_type == "guild":
    return meta.get("channel_id")
return payload.get("user_id")
```

## 使用示例

### 存储记忆

```python
from humanthinking import ChannelAwareMemoryManager

manager = ChannelAwareMemoryManager(
    db_path="/path/to/db",
    agent_id="AgentB",
)

# AgentB 与 AgentA 对话
context = extract_channel_context({
    "channel_id": "feishu",
    "user_id": "AgentA",
    "target_id": "AgentA",  # 对话对象是 AgentA
    "session_id": "session_001"
})

await manager.store_memory(
    context=context,
    memory_content="AgentA 说：你好",
)

# AgentB 与 AgentC 对话
context2 = extract_channel_context({
    "channel_id": "feishu",
    "user_id": "AgentC",
    "target_id": "AgentC",  # 对话对象是 AgentC
    "session_id": "session_002"
})

await manager.store_memory(
    context=context2,
    memory_content="AgentC 说：hello",
)

# 两个对话的记忆完全隔离
```

### 检索记忆

```python
# 检索 AgentB 与 AgentA 的所有历史记忆（跨Session）
memories = await manager.retrieve_memories(
    context=context,  # target_id="AgentA"
    query="你好",
    limit=10,
)
# 结果：只包含 target_id="AgentA" 的记忆

# 检索 AgentB 与用户U 的所有历史记忆（跨Session共享）
memories = await manager.retrieve_memories(
    context=context_user,  # target_id="user_U"
    query="天气",
    limit=10,
)
# 结果：包含用户在 Session1、Session2 等所有Session的记忆
```

## 架构优势

1. **精确隔离**：通过 `target_id` 区分不同对话对象
2. **记忆共享**：同一用户跨Session记忆共享
3. **渠道无关**：记忆键不依赖具体渠道实现
4. **扩展性**：新增渠道只需添加 target_id 提取逻辑

## 版本信息

- **版本**：v1.0.0-beta0.1
- **更新日期**：2026-04-20
- **核心特性**：target_id 会话对象隔离机制
