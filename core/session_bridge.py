# -*- coding: utf-8 -*-
"""HumanThinking Memory Manager - Session Bridge Engine

会话桥接引擎，负责新Session开始时继承历史记忆
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionBridgeEngine:
    """会话桥接引擎"""
    
    def __init__(self, db, search_engine=None):
        """
        Args:
            db: HumanThinkingDB 实例
            search_engine: 向量搜索引擎（可选）
        """
        self.db = db
        self.search_engine = search_engine
    
    async def bridge_new_session(
        self,
        agent_id: str,
        user_id: str,
        new_session_id: str,
        trigger_context: str
    ) -> Dict:
        """
        为新Session桥接相关历史记忆
        
        Args:
            agent_id: Agent ID
            user_id: User ID
            new_session_id: 新 Session ID
            trigger_context: 触发上下文（用户初始查询）
        
        Returns:
            桥接上下文
        """
        # 1. 识别相关历史 Session
        related_sessions = await self.identify_related_sessions(
            agent_id, user_id, new_session_id, trigger_context
        )
        
        # 2. 提取需要桥接的记忆
        bridged_memories = []
        for session_id in related_sessions:
            memories = await self.db.get_session_memories(
                agent_id=agent_id,
                session_id=session_id,
                limit=20
            )
            
            # 过滤重要记忆
            important = [
                m for m in memories 
                if m.importance >= 4 or m.access_count > 0
            ]
            bridged_memories.extend(important)
        
        # 3. 生成过渡摘要
        transition_summary = self.generate_transition_summary(
            bridged_memories, trigger_context
        )
        
        # 4. 构建情感桥接
        emotional_bridge = await self.build_emotional_bridge(
            agent_id, user_id, related_sessions
        )
        
        result = {
            "session_id": new_session_id,
            "inherited_sessions": related_sessions,
            "inherited_memories": len(bridged_memories),
            "transition_summary": transition_summary,
            "emotional_bridge": emotional_bridge,
            "bridged_memories": [
                {
                    "id": m.id,
                    "content": m.content,
                    "session_id": m.session_id,
                    "importance": m.importance
                }
                for m in bridged_memories[:10]  # 最多返回10条
            ]
        }
        
        logger.info(
            f"Session bridge completed: {new_session_id}, "
            f"inherited {len(bridged_memories)} memories from "
            f"{len(related_sessions)} sessions"
        )
        
        return result
    
    async def identify_related_sessions(
        self,
        agent_id: str,
        user_id: str,
        new_session_id: str,
        trigger_context: str
    ) -> List[str]:
        """
        识别相关历史 Session
        
        基于：
        1. 同一用户
        2. 时间接近性
        3. 内容相关性
        """
        # 获取所有活跃 Session
        sessions = await self.db.get_active_sessions(agent_id)
        
        # 过滤同一用户
        user_sessions = [
            s for s in sessions
            if s.get("user_id") == user_id or user_id is None
        ]
        
        # 按时间排序（最近优先）
        user_sessions.sort(
            key=lambda s: s.get("last_activity", ""),
            reverse=True
        )
        
        # 返回最近5个Session
        return [s["session_id"] for s in user_sessions[:5]]
    
    def generate_transition_summary(
        self,
        memories: List,
        trigger_context: str
    ) -> str:
        """生成过渡摘要"""
        if not memories:
            return "没有找到相关的历史记忆"
        
        # 提取重要话题
        topics = []
        for m in memories[:5]:
            # 简单提取：取内容前50字符
            content = m.content if hasattr(m, 'content') else m.get('content', '')
            topics.append(content[:50])
        
        summary = f"基于之前的对话：{'；'.join(topics)}"
        
        return summary
    
    async def build_emotional_bridge(
        self,
        agent_id: str,
        user_id: str,
        related_sessions: List[str]
    ) -> Dict:
        """
        构建情感桥接
        
        Returns:
            情感上下文
        """
        # 默认情感上下文
        emotional_context = {
            "primary_emotion": "neutral",
            "continuity_score": 0.0,
            "recommended_approach": "保持中性语气，根据用户反应调整",
            "emotional_memory_cues": []
        }
        
        # TODO: 从 session_emotional_continuity 表读取情感历史
        
        return emotional_context
