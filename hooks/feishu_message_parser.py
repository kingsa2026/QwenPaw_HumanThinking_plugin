# -*- coding: utf-8 -*-
"""
渠道消息解析器：解析各渠道的消息格式

支持：
- 飞书消息解析
- 微信消息解析
- QQ消息解析
- 其他渠道消息解析
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ChannelMessageParser:
    """渠道消息解析器基类"""

    @staticmethod
    def parse(message: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析消息
        
        Args:
            message: 原始消息
        
        Returns:
            结构化消息
        """
        return {
            "channel_id": message.get("channel_id", "unknown"),
            "user_id": message.get("user_id") or message.get("sender_id", ""),
            "content": message.get("content", ""),
            "content_parts": message.get("content_parts", []),
            "meta": message.get("meta", {}),
        }


class FeishuMessageParser(ChannelMessageParser):
    """飞书消息解析器"""

    @staticmethod
    def parse(message: Dict[str, Any]) -> Dict[str, Any]:
        """解析飞书消息"""
        meta = message.get("meta", {})
        
        # 提取文本内容
        content_parts = message.get("content_parts", [])
        text_content = ""
        for part in content_parts:
            if part.get("type") == "text":
                text_content += part.get("content", "")
        
        # 提取用户信息
        user_id = meta.get("feishu_sender_id") or message.get("user_id", "")
        chat_id = meta.get("feishu_chat_id", "")
        chat_type = meta.get("feishu_chat_type", "p2p")
        
        return {
            "channel_id": "feishu",
            "user_id": user_id,
            "target_id": chat_id if chat_type == "group" else user_id,
            "session_id": message.get("session_id", f"feishu:{chat_id}"),
            "content": text_content,
            "content_parts": content_parts,
            "meta": {
                **meta,
                "is_group": chat_type == "group",
                "group_id": chat_id if chat_type == "group" else None,
            }
        }


class WechatMessageParser(ChannelMessageParser):
    """微信消息解析器"""

    @staticmethod
    def parse(message: Dict[str, Any]) -> Dict[str, Any]:
        """解析微信消息"""
        meta = message.get("meta", {})
        
        content = message.get("content", "")
        user_id = message.get("user_id") or message.get("sender_id", "")
        group_id = meta.get("weixin_group_id")
        
        return {
            "channel_id": "wechat",
            "user_id": user_id,
            "target_id": group_id or user_id,
            "session_id": message.get("session_id", f"wechat:{group_id or user_id}"),
            "content": content,
            "content_parts": [{"type": "text", "content": content}],
            "meta": {
                **meta,
                "is_group": bool(group_id),
                "group_id": group_id,
            }
        }


class QQMessageParser(ChannelMessageParser):
    """QQ消息解析器"""

    @staticmethod
    def parse(message: Dict[str, Any]) -> Dict[str, Any]:
        """解析QQ消息"""
        meta = message.get("meta", {})
        
        msg_type = meta.get("qq_message_type", "c2c")
        user_id = message.get("user_id", "")
        
        if msg_type == "group":
            target_id = meta.get("group_openid", user_id)
            session_id = f"qq:group:{target_id}"
        elif msg_type == "guild":
            target_id = meta.get("channel_id") or meta.get("guild_id", user_id)
            session_id = f"qq:guild:{target_id}"
        else:
            target_id = user_id
            session_id = f"qq:c2c:{user_id}"
        
        return {
            "channel_id": "qq",
            "user_id": user_id,
            "target_id": target_id,
            "session_id": message.get("session_id", session_id),
            "content": message.get("content", ""),
            "content_parts": message.get("content_parts", []),
            "meta": {
                **meta,
                "is_group": msg_type in ("group", "guild"),
                "group_id": target_id if msg_type in ("group", "guild") else None,
            }
        }


# 解析器注册表
PARSERS = {
    "feishu": FeishuMessageParser,
    "wechat": WechatMessageParser,
    "weixin": WechatMessageParser,
    "qq": QQMessageParser,
}


def parse_message(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    通用消息解析器
    
    Args:
        message: 原始消息
    
    Returns:
        结构化消息
    """
    channel_id = message.get("channel_id", "unknown")
    parser = PARSERS.get(channel_id, ChannelMessageParser)
    return parser.parse(message)
