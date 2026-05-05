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
        sessions = await self.db.get_active_sessions(agent_id)

        user_sessions = [
            s for s in sessions
            if s.get("user_id") == user_id or user_id is None
        ]

        if not user_sessions:
            return []

        scored = []
        for s in user_sessions:
            score = 0.0
            recency = s.get("last_activity", "")
            if recency:
                score += 0.3
            if not trigger_context:
                scored.append((s["session_id"], score))
                continue
            try:
                results = await self.db.search_memories(
                    query=trigger_context,
                    agent_id=agent_id,
                    session_id=s["session_id"],
                    user_id=user_id,
                    max_results=3,
                    include_frozen=True,
                )
                if results:
                    avg_importance = sum(
                        getattr(r, "importance", 0) or 0 for r in results
                    ) / max(len(results), 1)
                    score += 0.4 + avg_importance * 0.1
            except Exception:
                pass
            scored.append((s["session_id"], score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [sid for sid, _ in scored[:5]]

    def generate_transition_summary(
        self,
        memories: List,
        trigger_context: str
    ) -> str:
        if not memories:
            return "\u6ca1\u6709\u627e\u5230\u76f8\u5173\u7684\u5386\u53f2\u8bb0\u5fc6"

        topics = []
        for m in memories[:5]:
            content = m.content if hasattr(m, 'content') else m.get('content', '')
            topics.append(content[:60])

        sep = ';\u3002'
        return f"\u57fa\u4e8e\u4e4b\u524d\u7684\u5bf9\u8bdd\uff1a{sep.join(topics)}"

    async def build_emotional_bridge(
        self,
        agent_id: str,
        user_id: str,
        related_sessions: List[str]
    ) -> Dict:
        if not related_sessions:
            return {
                "primary_emotion": "neutral",
                "continuity_score": 0.0,
                "recommended_approach": "\u4fdd\u6301\u4e2d\u6027\u8bed\u6c14\uff0c\u6839\u636e\u7528\u6237\u53cd\u5e94\u8c03\u6574",
                "emotional_memory_cues": [],
            }

        try:
            placeholders = ",".join(["?" for _ in related_sessions])
            self.db.cursor.execute(
                f"SELECT emotional_state, continuity_from_previous "
                f"FROM session_emotional_continuity "
                f"WHERE agent_id = ? AND session_id IN ({placeholders}) "
                f"ORDER BY created_at DESC LIMIT 10",
                [agent_id] + related_sessions,
            )
            rows = self.db.cursor.fetchall()

            if not rows:
                return {
                    "primary_emotion": "neutral",
                    "continuity_score": 0.0,
                    "recommended_approach": "\u4fdd\u6301\u4e2d\u6027\u8bed\u6c14\uff0c\u6839\u636e\u7528\u6237\u53cd\u5e94\u8c03\u6574",
                    "emotional_memory_cues": [],
                }

            import json
            emotion_counts = {}
            total_continuity = 0.0
            cues = []

            for state_json, continuity in rows:
                total_continuity += continuity or 0.0
                try:
                    state = json.loads(state_json) if state_json else {}
                except (json.JSONDecodeError, TypeError):
                    state = {}
                primary = state.get("primary_emotion", "neutral")
                emotion_counts[primary] = emotion_counts.get(primary, 0) + 1
                if state.get("cues"):
                    cues.extend(state["cues"])

            dominant = max(emotion_counts, key=emotion_counts.get) if emotion_counts else "neutral"
            avg_continuity = total_continuity / len(rows)

            approaches = {
                "positive": "\u4fdd\u6301\u79ef\u6781\u4e50\u89c2\uff0c\u53ef\u9002\u5f53\u5f00\u73a9\u7b11",
                "negative": "\u8c28\u614e\u56de\u5e94\uff0c\u5148\u8868\u793a\u7406\u89e3\u518d\u63d0\u4f9b\u5efa\u8bae",
                "neutral": "\u4fdd\u6301\u4e2d\u6027\u8bed\u6c14\uff0c\u6839\u636e\u7528\u6237\u53cd\u5e94\u8c03\u6574",
                "anxious": "\u5b89\u629a\u4e3a\u4e3b\uff0c\u51cf\u5c11\u4e0d\u786e\u5b9a\u6027\u56de\u7b54",
                "angry": "\u5148\u8ba4\u540c\u60c5\u7eea\uff0c\u907f\u514d\u6fc0\u5316\u77db\u76fe",
            }
            recommended = approaches.get(dominant, approaches["neutral"])

            return {
                "primary_emotion": dominant,
                "continuity_score": round(avg_continuity, 2),
                "recommended_approach": recommended,
                "emotional_memory_cues": list(set(cues))[:5],
            }
        except Exception as e:
            logger.warning(f"build_emotional_bridge failed: {e}")
            return {
                "primary_emotion": "neutral",
                "continuity_score": 0.0,
                "recommended_approach": "\u4fdd\u6301\u4e2d\u6027\u8bed\u6c14\uff0c\u6839\u636e\u7528\u6237\u53cd\u5e94\u8c03\u6574",
                "emotional_memory_cues": [],
            }
