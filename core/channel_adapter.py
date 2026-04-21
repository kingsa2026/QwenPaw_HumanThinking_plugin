# -*- coding: utf-8 -*-
"""
渠道适配器：为 HumanThinking 记忆管理器统一各渠道的 user_id、session_id
和 channel_id 标识，确保记忆管理能在不同渠道下正确工作。

核心设计原则：
1. 渠道无关：MemoryManager 使用统一接口，不依赖具体渠道实现
2. 自动识别：从渠道元数据中提取 user_id、session_id 等关键信息
3. 会话隔离：保持各渠道原有的会话隔离规则
4. 记忆桥接：新会话自动继承历史记忆
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ChannelType(Enum):
    """支持的渠道类型"""
    FEISHU = "feishu"
    WEIXIN = "wechat"
    WECOM = "wecom"
    QQ = "qq"
    DINGTALK = "dingtalk"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    IMESSAGE = "imessage"
    XIAOYI = "xiaoyi"
    ONEBOT = "onebot"
    MQTT = "mqtt"
    MATTERMOST = "mattermost"
    MATRIX = "matrix"
    VOICE = "voice"
    CONSOLE = "console"
    UNKNOWN = "unknown"


class ChannelContext:
    """渠道上下文：封装从渠道消息中提取的关键信息"""

    def __init__(
        self,
        channel_id: str,
        user_id: str,
        session_id: str,
        target_id: Optional[str] = None,  # 新增：对话对象（区分 Agent/用户）
        is_group: bool = False,
        group_id: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ):
        self.channel_id = channel_id
        self.user_id = user_id
        self.session_id = session_id
        self.target_id = target_id  # 对话对象标识
        self.is_group = is_group
        self.group_id = group_id
        self.meta = meta or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channel_id": self.channel_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "target_id": self.target_id,
            "is_group": self.is_group,
            "group_id": self.group_id,
            "meta": self.meta,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChannelContext":
        return cls(
            channel_id=data.get("channel_id", ""),
            user_id=data.get("user_id", ""),
            session_id=data.get("session_id", ""),
            target_id=data.get("target_id"),
            is_group=data.get("is_group", False),
            group_id=data.get("group_id"),
            meta=data.get("meta", {}),
        )


class ChannelAdapter:
    """渠道适配器基类：定义各渠道的适配接口"""

    channel_type: ChannelType = ChannelType.UNKNOWN

    @staticmethod
    def extract_user_id(payload: Dict[str, Any], meta: Dict[str, Any]) -> str:
        """从渠道负载中提取用户ID"""
        return payload.get("user_id") or payload.get("sender_id") or ""

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        """从渠道负载中提取会话ID"""
        return payload.get("session_id") or f"{channel_id}:unknown"

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """从元数据中提取群聊信息"""
        is_group = meta.get("is_group", False)
        group_id = meta.get("group_id") or meta.get("chat_id")
        return is_group, group_id

    @staticmethod
    def extract_target_id(payload: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
        """
        提取对话对象标识（target_id）
        
        target_id 用于区分不同的对话方：
        - 用户与 Agent 对话：target_id = user_id
        - AgentA 与 AgentB 对话：target_id = other_agent_id
        
        这样确保：
        - AgentB 与 AgentA 的对话 ≠ AgentB 与 AgentC 的对话（隔离）
        - 同一用户通过不同 session 与 AgentB 对话 → 记忆共享（相同 target_id）
        """
        # 优先从 meta 中提取
        target = meta.get("target_id") or meta.get("target_agent_id")
        if target:
            return target
        
        # 从 payload 中提取
        return payload.get("target_id") or payload.get("target_agent_id")

    @staticmethod
    def build_context(
        payload: Dict[str, Any],
        channel_id: Optional[str] = None,
    ) -> ChannelContext:
        """从渠道负载构建完整的上下文"""
        meta = payload.get("meta", {})
        cid = channel_id or payload.get("channel_id", "unknown")
        uid = ChannelAdapter.extract_user_id(payload, meta)
        sid = ChannelAdapter.extract_session_id(payload, meta, cid)
        target_id = ChannelAdapter.extract_target_id(payload, meta)
        is_group, group_id = ChannelAdapter.extract_group_info(meta)

        return ChannelContext(
            channel_id=cid,
            user_id=uid,
            session_id=sid,
            target_id=target_id or uid,  # 默认 target_id = user_id
            is_group=is_group,
            group_id=group_id,
            meta=meta,
        )


# ============================================================
# 各渠道具体适配器
# ============================================================


class FeishuAdapter(ChannelAdapter):
    """飞书渠道适配器"""

    channel_type = ChannelType.FEISHU

    @staticmethod
    def extract_user_id(payload: Dict[str, Any], meta: Dict[str, Any]) -> str:
        # 优先使用真实的 open_id
        return (
            meta.get("feishu_sender_id")
            or payload.get("user_id")
            or payload.get("sender_id")
            or ""
        )

    @staticmethod
    def extract_target_id(payload: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
        # 飞书：如果是群聊，target 是 chat_id；如果是单聊，target 是 sender_id
        chat_type = meta.get("feishu_chat_type", "p2p")
        if chat_type == "group":
            return meta.get("feishu_chat_id")
        return meta.get("feishu_sender_id") or payload.get("user_id")

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        # 飞书使用短化的 chat_id 或 open_id
        return (
            payload.get("session_id")
            or f"feishu:{meta.get('feishu_chat_id', 'unknown')}"
        )

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        is_group = meta.get("feishu_chat_type") == "group"
        group_id = meta.get("feishu_chat_id")
        return is_group, group_id


class WeixinAdapter(ChannelAdapter):
    """微信渠道适配器"""

    channel_type = ChannelType.WEIXIN

    @staticmethod
    def extract_target_id(payload: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
        # 微信：群聊 target 是 group_id，单聊 target 是 sender_id
        group_id = meta.get("weixin_group_id")
        if group_id:
            return group_id
        return payload.get("sender_id")

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        group_id = meta.get("weixin_group_id")
        if group_id:
            return f"weixin:group:{group_id}"
        sender = payload.get("sender_id", "")
        return f"weixin:{sender}" if sender else "weixin:unknown"

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        group_id = meta.get("weixin_group_id")
        return bool(group_id), group_id


class WecomAdapter(ChannelAdapter):
    """企业微信渠道适配器"""

    channel_type = ChannelType.WECOM

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        # 企业微信使用 userid 或 chatid
        chat_type = meta.get("wecom_chat_type", "single")
        if chat_type == "group":
            chatid = meta.get("wecom_chatid", "unknown")
            return f"wecom:group:{chatid}"
        sender = payload.get("sender_id", "")
        return f"wecom:{sender}" if sender else "wecom:unknown"

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        chat_type = meta.get("wecom_chat_type", "single")
        is_group = chat_type == "group"
        group_id = meta.get("wecom_chatid") if is_group else None
        return is_group, group_id


class QQAdapter(ChannelAdapter):
    """QQ渠道适配器"""

    channel_type = ChannelType.QQ

    @staticmethod
    def extract_target_id(payload: Dict[str, Any], meta: Dict[str, Any]) -> Optional[str]:
        # QQ：根据消息类型返回 target
        msg_type = meta.get("qq_message_type", "")
        if msg_type == "group":
            return meta.get("group_openid")
        elif msg_type == "guild":
            return meta.get("channel_id") or meta.get("guild_id")
        return payload.get("user_id")

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        # QQ 有复杂的消息类型：c2c, guild, dm, group
        msg_type = meta.get("qq_message_type", "")
        if msg_type == "c2c":
            return f"qq:c2c:{payload.get('user_id', 'unknown')}"
        elif msg_type == "group":
            group_id = meta.get("group_openid", "unknown")
            return f"qq:group:{group_id}"
        elif msg_type == "guild":
            channel_id_meta = meta.get("channel_id", "unknown")
            return f"qq:guild:{channel_id_meta}"
        return payload.get("session_id") or f"qq:{payload.get('user_id', 'unknown')}"

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        msg_type = meta.get("qq_message_type", "")
        if msg_type == "group":
            return True, meta.get("group_openid")
        elif msg_type == "guild":
            return True, meta.get("guild_id")
        return False, None


class DingTalkAdapter(ChannelAdapter):
    """钉钉渠道适配器"""

    channel_type = ChannelType.DINGTALK

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        # 钉钉使用 conversation_id 的短后缀
        conv_id = meta.get("conversation_id", "")
        if conv_id:
            # 使用短 session_id（与钉钉渠道逻辑一致）
            return conv_id[-16:] if len(conv_id) > 16 else conv_id
        return payload.get("session_id") or f"dingtalk:unknown"

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        conv_type = meta.get("conversation_type", "1")
        is_group = conv_type != "1"  # 1=单聊，2=群聊
        return is_group, meta.get("conversation_id")


class TelegramAdapter(ChannelAdapter):
    """Telegram渠道适配器"""

    channel_type = ChannelType.TELEGRAM

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        chat_id = meta.get("chat_id", "")
        return f"telegram:{chat_id}" if chat_id else "telegram:unknown"

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        is_group = meta.get("is_group", False)
        group_id = meta.get("chat_id") if is_group else None
        return is_group, group_id


class DiscordAdapter(ChannelAdapter):
    """Discord渠道适配器"""

    channel_type = ChannelType.DISCORD

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        # Discord 支持 channel、thread、DM
        if meta.get("is_thread"):
            thread_id = meta.get("thread_id", "unknown")
            return f"discord:thread:{thread_id}"
        ch_id = meta.get("channel_id", "unknown")
        return f"discord:{ch_id}"

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        is_group = meta.get("is_group", False)
        group_id = meta.get("guild_id") if is_group else None
        return is_group, group_id


class IMessageAdapter(ChannelAdapter):
    """iMessage渠道适配器"""

    channel_type = ChannelType.IMESSAGE

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        # iMessage 使用发送者手机号或邮箱作为 session_id
        sender = payload.get("sender_id", "")
        return f"imessage:{sender}" if sender else "imessage:unknown"

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        # iMessage 目前不支持群聊
        return False, None


class ConsoleAdapter(ChannelAdapter):
    """控制台渠道适配器"""

    channel_type = ChannelType.CONSOLE

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        # 控制台使用 meta 中的 session_id 或 sender_id
        if meta.get("session_id"):
            return meta["session_id"]
        sender = payload.get("sender_id", "")
        return f"console:{sender}" if sender else "console:unknown"

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        # 控制台不支持群聊
        return False, None


class VoiceAdapter(ChannelAdapter):
    """语音渠道适配器（Twilio）"""

    channel_type = ChannelType.VOICE

    @staticmethod
    def extract_user_id(payload: Dict[str, Any], meta: Dict[str, Any]) -> str:
        # 语音渠道使用 from_number 作为 user_id
        return payload.get("from_number") or payload.get("user_id") or ""

    @staticmethod
    def extract_session_id(
        payload: Dict[str, Any],
        meta: Dict[str, Any],
        channel_id: str,
    ) -> str:
        # 语音渠道使用 call_sid 作为 session_id
        session_id = payload.get("session_id") or payload.get("call_sid", "")
        return f"voice:{session_id}" if session_id else "voice:unknown"

    @staticmethod
    def extract_group_info(meta: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        # 语音渠道不支持群聊
        return False, None


class XiaoYiAdapter(ChannelAdapter):
    """小艺渠道适配器"""

    channel_type = ChannelType.XIAOYI


class OneBotAdapter(ChannelAdapter):
    """OneBot 渠道适配器"""

    channel_type = ChannelType.ONEBOT


class MqttAdapter(ChannelAdapter):
    """MQTT 渠道适配器"""

    channel_type = ChannelType.MQTT


class MattermostAdapter(ChannelAdapter):
    """Mattermost 渠道适配器"""

    channel_type = ChannelType.MATTERMOST


class MatrixAdapter(ChannelAdapter):
    """Matrix 渠道适配器"""

    channel_type = ChannelType.MATRIX


# ============================================================
# 渠道适配器注册表
# ============================================================

_CHANNEL_ADAPTERS: Dict[str, type] = {
    ChannelType.FEISHU.value: FeishuAdapter,
    ChannelType.WEIXIN.value: WeixinAdapter,
    ChannelType.WECOM.value: WecomAdapter,
    ChannelType.QQ.value: QQAdapter,
    ChannelType.DINGTALK.value: DingTalkAdapter,
    ChannelType.TELEGRAM.value: TelegramAdapter,
    ChannelType.DISCORD.value: DiscordAdapter,
    ChannelType.IMESSAGE.value: IMessageAdapter,
    ChannelType.CONSOLE.value: ConsoleAdapter,
    ChannelType.VOICE.value: VoiceAdapter,
    ChannelType.XIAOYI.value: XiaoYiAdapter,
    ChannelType.ONEBOT.value: OneBotAdapter,
    ChannelType.MQTT.value: MqttAdapter,
    ChannelType.MATTERMOST.value: MattermostAdapter,
    ChannelType.MATRIX.value: MatrixAdapter,
}


def get_adapter(channel_id: str) -> type:
    """获取指定渠道的适配器类"""
    return _CHANNEL_ADAPTERS.get(channel_id, ChannelAdapter)


def extract_channel_context(
    payload: Dict[str, Any],
    channel_id: Optional[str] = None,
) -> ChannelContext:
    """
    统一接口：从任意渠道的负载中提取上下文

    Args:
        payload: 渠道消息负载（native dict）
        channel_id: 渠道ID，如果未提供则从 payload 中提取

    Returns:
        ChannelContext: 包含 user_id、session_id、channel_id 等的上下文
    """
    cid = channel_id or payload.get("channel_id", "unknown")
    adapter = get_adapter(cid)
    return adapter.build_context(payload, cid)


def build_memory_key(
    agent_id: str,
    target_id: str,
    user_id: str,
) -> str:
    """
    构建记忆键：用于在 HumanThinking 数据库中定位记忆

    格式：{agent_id}:{target_id}:{user_id}

    核心设计：
    - agent_id: 当前 Agent 标识
    - target_id: 对话对象标识（区分 AgentA/AgentC 等不同对话方）
    - user_id: 发起者标识

    隔离规则：
    1. AgentB 与 AgentA 对话：target_id=AgentA → 独立记忆空间
    2. AgentB 与 AgentC 对话：target_id=AgentC → 独立记忆空间（与上面隔离）
    3. 同一用户通过不同渠道/Session 与 AgentB 对话：target_id=user_id → 记忆共享

    注意：
    - session_id 不在记忆键中 → 跨 Session 记忆共享
    - channel_id 不在记忆键中 → 跨渠道记忆共享
    """
    return f"{agent_id}:{target_id or user_id}:{user_id}"


def parse_memory_key(key: str) -> Dict[str, str]:
    """解析记忆键"""
    parts = key.split(":")
    if len(parts) >= 4:
        return {
            "agent_id": parts[0],
            "target_id": parts[1],
            "channel_id": parts[2],
            "user_id": parts[3],
        }
    return {"agent_id": "", "target_id": "", "channel_id": "", "user_id": ""}
