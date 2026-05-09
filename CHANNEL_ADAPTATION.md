# HumanThinking 渠道适配说明

## 概述

已完成 QwenPaw 所有内置消息渠道的功能适配，确保 HumanThinking 记忆管理器能在不同渠道下正确工作。

## 支持的渠道列表（15个）

### 主流社交渠道
1. **飞书 (Feishu)** - `feishu/channel.py`
   - 用户标识：`feishu_sender_id` (open_id)
   - 会话标识：短化的 chat_id 或 open_id
   - 群聊支持：`feishu_chat_type = "group"`
   - 特殊处理：receive_id 映射、消息去重

2. **微信 (WeChat)** - `weixin/channel.py`
   - 用户标识：`from_user_id`
   - 会话标识：`weixin:<from_user_id>` 或 `weixin:group:<group_id>`
   - 群聊支持：`weixin_group_id`
   - 特殊处理：context_token、QR登录

3. **企业微信 (WeCom)** - `wecom/channel.py`
   - 用户标识：`userid`
   - 会话标识：`wecom:<userid>` 或 `wecom:group:<chatid>`
   - 群聊支持：`wecom_chat_type = "group"`
   - 特殊处理：WebSocket长连接

4. **QQ** - `qq/channel.py`
   - 用户标识：`user_openid` / `member_openid`
   - 会话标识：根据消息类型区分
     - `qq:c2c:<openid>` - 私聊
     - `qq:group:<group_openid>` - 群聊
     - `qq:guild:<channel_id>` - 频道
   - 群聊支持：`GROUP_AT_MESSAGE_CREATE`
   - 特殊处理：msg_seq、富媒体上传

5. **钉钉 (DingTalk)** - `dingtalk/channel.py`
   - 用户标识：`sender_staff_id`
   - 会话标识：conversation_id 短后缀
   - 群聊支持：`conversation_type = "2"`
   - 特殊处理：sessionWebhook、AI卡片

6. **Telegram** - `telegram/channel.py`
   - 用户标识：`user.id`
   - 会话标识：`telegram:<chat_id>`
   - 群聊支持：`is_group = chat_type in ("group", "supergroup")`
   - 特殊处理：Bot API、文件下载

7. **Discord** - `discord_/channel.py`
   - 用户标识：`message.author.id`
   - 会话标识：`discord:<channel_id>` 或 `discord:thread:<thread_id>`
   - 群聊支持：`is_group = message.guild is not None`
   - 特殊处理：Thread支持、消息去重

### 其他渠道

8. **iMessage** - `imessage/channel.py`
   - 用户标识：`sender` (手机号/邮箱)
   - 会话标识：`imessage:<sender>`
   - 群聊支持：暂不支持
   - 特殊处理：SQLite数据库轮询

9. **控制台 (Console)** - `console/channel.py`
   - 用户标识：`sender_id`
   - 会话标识：`console:<sender_id>` 或 meta中的session_id
   - 群聊支持：不支持
   - 特殊处理：stdout输出

10. **语音 (Voice)** - `voice/channel.py`
    - 用户标识：`from_number`
    - 会话标识：`voice:<call_sid>`
    - 群聊支持：不支持
    - 特殊处理：Twilio ConversationRelay

11. **小艺 (XiaoYi)** - `xiaoyi/channel.py`
    - 华为小艺渠道

12. **OneBot** - `onebot/channel.py`
    - OneBot协议渠道

13. **MQTT** - `mqtt/channel.py`
    - MQTT协议渠道

14. **Mattermost** - `mattermost/channel.py`
    - Mattermost渠道

15. **Matrix** - `matrix/channel.py`
    - Matrix协议渠道

## 架构设计

### 1. 渠道适配器层 (`core/channel_adapter.py`)

```python
# 统一接口
context = extract_channel_context(payload, channel_id)

# 自动识别渠道并提取关键信息
{
    "channel_id": "feishu",
    "user_id": "ou_xxx",
    "session_id": "abc123",
    "is_group": True,
    "group_id": "oc_xxx",
    "meta": {...}
}
```

**核心功能**：
- ✅ 统一接口：所有渠道使用相同的 `ChannelContext`
- ✅ 自动识别：根据 `channel_id` 自动选择适配器
- ✅ 会话隔离：保持各渠道原有的会话规则
- ✅ 群聊支持：正确识别群聊和单聊

### 2. 渠道感知记忆管理器 (`core/channel_aware_manager.py`)

```python
# 创建管理器
manager = ChannelAwareMemoryManager(
    db_path="/path/to/db",
    agent_id="agent_123",
    enable_cross_channel_bridge=True,  # 可选跨渠道桥接
)

# 处理渠道消息
context = await manager.process_channel_message(payload)

# 存储记忆
await manager.store_memory(
    context=context,
    memory_content="用户询问天气",
    memory_type="conversation",
)

# 检索记忆
memories = await manager.retrieve_memories(
    context=context,
    query="天气",
    limit=5,
)

# 情感跟踪
await manager.track_emotion(
    context=context,
    emotion="happy",
    intensity=0.8,
)
```

**核心功能**：
- ✅ 渠道独立上下文：每个渠道独立的记忆上下文
- ✅ 记忆桥接：新Session自动继承历史记忆
- ✅ 情感连续性：跨Session维护情感状态
- ✅ 缓存优化：Agent级缓存池加速读写

### 3. 记忆键格式

```
{agent_id}:{channel_id}:{user_id}:{session_id}

示例：
agent_123:feishu:ou_xxx:abc123
agent_123:wechat:wx_user:def456
agent_123:qq:c2c:openid:ghi789
```

**隔离级别**：
1. Agent 级别隔离
2. 渠道级别隔离
3. 用户级别隔离
4. 会话级别隔离

## 使用示例

### 飞书渠道

```python
# 飞书消息负载
payload = {
    "channel_id": "feishu",
    "sender_id": "张三#1234",
    "user_id": "ou_xxxxxxxxx",
    "session_id": "app123_abc",
    "content_parts": [...],
    "meta": {
        "feishu_message_id": "om_xxx",
        "feishu_chat_id": "oc_xxx",
        "feishu_chat_type": "group",  # 群聊
        "feishu_sender_id": "ou_xxx",
        "is_group": True,
        "feishu_receive_id": "oc_xxx",
        "feishu_receive_id_type": "chat_id",
    }
}

# 提取上下文
context = extract_channel_context(payload)
# 结果：
# context.user_id = "ou_xxx" (真实的open_id)
# context.session_id = "app123_abc"
# context.is_group = True
# context.group_id = "oc_xxx"
```

### QQ渠道

```python
# QQ群聊消息
payload = {
    "channel_id": "qq",
    "sender_id": "用户#1234",
    "content_parts": [...],
    "meta": {
        "qq_message_type": "group",
        "member_openid": "xxx",
        "group_openid": "yyy",
        "is_group": True,
    }
}

context = extract_channel_context(payload)
# context.user_id = "xxx"
# context.session_id = "qq:group:yyy"
# context.is_group = True
```

### Telegram渠道

```python
# Telegram私聊
payload = {
    "channel_id": "telegram",
    "sender_id": "12345678",
    "content_parts": [...],
    "meta": {
        "chat_id": "12345678",
        "user_id": "12345678",
        "is_group": False,
    }
}

context = extract_channel_context(payload)
# context.user_id = "12345678"
# context.session_id = "telegram:12345678"
# context.is_group = False
```

## 特殊渠道适配

### 飞书
- ✅ receive_id 映射管理（open_id / chat_id）
- ✅ 消息去重（message_id）
- ✅ 群聊/单聊自动识别
- ✅ 短化session_id用于cron

### QQ
- ✅ 四种消息类型适配（c2c/guild/dm/group）
- ✅ msg_seq 管理
- ✅ 富媒体路径处理
- ✅ 频道/群聊/私聊区分

### 钉钉
- ✅ conversation_id 短后缀
- ✅ sessionWebhook 管理
- ✅ AI卡片状态
- ✅ 单聊/群聊识别

### Discord
- ✅ Thread 支持
- ✅ 消息去重（500条缓存）
- ✅ 频道/线程/DM区分
- ✅ Role mention 识别

### Telegram
- ✅ Bot API 集成
- ✅ 文件下载管理
- ✅ 群聊/私聊识别
- ✅ message_thread_id 支持

## 版本信息

- **版本**：v1.0.0-beta0.1
- **创建日期**：2026-04-20
- **支持渠道**：15个
- **架构**：插件化（符合QwenPaw官方规范）

## 文件清单

```
HumanThinking/
├── plugin.py                           # 插件入口
├── __init__.py                         # 版本信息
├── ui_injector.py                      # UI注入器
├── core/
│   ├── channel_adapter.py              # 渠道适配器（新增）
│   ├── channel_aware_manager.py        # 渠道感知管理器（新增）
│   ├── database.py                     # 数据库
│   ├── cache_pool.py                   # 缓存池
│   ├── session_bridge.py               # 会话桥接
│   ├── emotional_engine.py             # 情感引擎
│   └── memory_manager.py               # 主管理器
└── README.md                           # 文档
```

## 下一步计划

1. ✅ 渠道适配器层 - 完成
2. ✅ 渠道感知管理器 - 完成
3. ⏳ 渠道集成测试 - 待实现
4. ⏳ 跨渠道桥接策略优化 - 待实现
5. ⏳ 各渠道UI适配完善 - 待实现
