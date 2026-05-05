# -*- coding: utf-8 -*-
"""HumanThinking Memory Manager - Emotional Continuity Engine

情感连续性引擎，维护同一User-Agent跨Session的情感状态
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class EmotionalContinuityEngine:
    """情感连续性引擎"""
    
    def __init__(self, db):
        """
        Args:
            db: HumanThinkingDB 实例
        """
        self.db = db
        self._emotional_states: Dict[str, List[Dict]] = {}
    
    async def track_emotional_state(
        self,
        session_id: str,
        agent_id: str,
        user_id: Optional[str] = None,
        emotion: str = "neutral",
        intensity: float = 0.5,
        triggers: List[str] = None
    ) -> Dict:
        """
        跟踪情感状态
        
        Args:
            session_id: Session ID
            agent_id: Agent ID
            user_id: User ID
            emotion: 情感类型 (satisfied, frustrated, neutral, excited...)
            intensity: 情感强度 (0.0 - 1.0)
            triggers: 触发因素列表
        
        Returns:
            情感状态记录
        """
        import json
        
        emotional_data = {
            "emotion": emotion,
            "intensity": intensity,
            "triggers": triggers or []
        }
        
        # 计算情感连续性
        continuity_score = await self.calculate_emotional_continuity(
            session_id, agent_id
        )
        
        # 存储到数据库
        self.db.cursor.execute("""
            INSERT INTO session_emotional_continuity
            (session_id, agent_id, user_id, emotional_state, continuity_from_previous)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            agent_id,
            user_id,
            json.dumps(emotional_data),
            continuity_score
        ))
        self.db.conn.commit()
        
        # 缓存到内存
        cache_key = f"{agent_id}_{user_id}"
        if cache_key not in self._emotional_states:
            self._emotional_states[cache_key] = []
        
        self._emotional_states[cache_key].append({
            "session_id": session_id,
            "emotion": emotion,
            "intensity": intensity,
            "continuity": continuity_score
        })
        
        logger.debug(
            f"Tracked emotional state: session={session_id}, "
            f"emotion={emotion}, intensity={intensity}"
        )
        
        return {
            "session_id": session_id,
            "emotion": emotion,
            "intensity": intensity,
            "continuity_score": continuity_score
        }
    
    async def get_emotional_context(
        self,
        session_id: str,
        agent_id: str,
        user_id: Optional[str] = None
    ) -> Dict:
        """
        获取情感上下文（用于新Session）
        
        Returns:
            情感上下文
        """
        import json
        
        # 从缓存获取最近的情感状态
        cache_key = f"{agent_id}_{user_id}"
        recent_states = self._emotional_states.get(cache_key, [])[-5:]
        
        if not recent_states:
            # 从数据库查询
            self.db.cursor.execute("""
                SELECT emotional_state, continuity_from_previous
                FROM session_emotional_continuity
                WHERE agent_id = ? AND (? IS NULL OR user_id = ?)
                ORDER BY created_at DESC
                LIMIT 5
            """, (agent_id, user_id, user_id))
            
            rows = self.db.cursor.fetchall()
            recent_states = [
                {
                    **json.loads(row["emotional_state"]),
                    "continuity": row["continuity_from_previous"]
                }
                for row in rows
            ]
        
        if not recent_states:
            return {
                "primary_emotion_trend": "neutral",
                "continuity_score": 0.0,
                "recommended_approach": "保持友好、专业的语气",
                "emotional_memory_cues": [],
                "historical_patterns": {}
            }
        
        # 分析情感趋势
        primary_emotion = recent_states[-1].get("emotion", "neutral")
        avg_continuity = sum(s.get("continuity", 0) for s in recent_states) / len(recent_states)
        
        # 生成推荐方法
        recommended = self._recommend_approach(primary_emotion, avg_continuity)
        
        # 提取情感线索
        emotional_cues = self._extract_emotional_cues(recent_states)
        
        # 历史模式
        historical_patterns = self._analyze_historical_patterns(recent_states)
        
        return {
            "primary_emotion_trend": primary_emotion,
            "continuity_score": avg_continuity,
            "recommended_approach": recommended,
            "emotional_memory_cues": emotional_cues,
            "historical_patterns": historical_patterns
        }
    
    async def calculate_emotional_continuity(
        self,
        session_id: str,
        agent_id: str,
        user_id: Optional[str] = None
    ) -> float:
        """
        计算情感连续性分数
        
        Returns:
            连续性分数 (0.0 - 1.0)
        """
        import json
        
        # 获取最近的情感状态
        self.db.cursor.execute("""
            SELECT emotional_state
            FROM session_emotional_continuity
            WHERE agent_id = ? AND (? IS NULL OR user_id = ?)
            ORDER BY created_at DESC
            LIMIT 3
        """, (agent_id, user_id, user_id))
        
        rows = self.db.cursor.fetchall()
        if len(rows) < 2:
            return 0.0
        
        states = [json.loads(row["emotional_state"]) for row in rows]
        
        # 计算情感一致性
        emotions = [s.get("emotion", "neutral") for s in states]
        unique_emotions = set(emotions)
        
        if len(unique_emotions) == 1:
            return 1.0  # 完全一致
        elif len(unique_emotions) == 2:
            return 0.6  # 部分一致
        else:
            return 0.3  # 不一致
    
    def _recommend_approach(self, emotion: str, continuity: float) -> str:
        """推荐交互方法"""
        if continuity >= 0.8:
            return f"保持{emotion}的情感基调，延续良好的互动"
        elif continuity >= 0.5:
            return "适度调整情感表达，关注用户反馈"
        else:
            return "采用中性情感基调，建立新的情感连接"
    
    def _extract_emotional_cues(self, states: List[Dict]) -> List[Dict]:
        """提取情感线索"""
        cues = []
        for state in states:
            cues.append({
                "emotion": state.get("emotion", "neutral"),
                "intensity": state.get("intensity", 0.5),
                "triggers": state.get("triggers", [])[:3]
            })
        return cues
    
    def _analyze_historical_patterns(self, states: List[Dict]) -> Dict:
        """分析历史情感模式"""
        emotions = [s.get("emotion", "neutral") for s in states]
        intensities = [s.get("intensity", 0.5) for s in states]
        
        # 统计情感频率
        emotion_counts = {}
        for e in emotions:
            emotion_counts[e] = emotion_counts.get(e, 0) + 1
        
        # 找出最常见的情感
        most_frequent = max(emotion_counts.items(), key=lambda x: x[1])[0] if emotion_counts else "neutral"
        
        return {
            "frequent_emotions": list(emotion_counts.keys()),
            "typical_intensity_range": [min(intensities), max(intensities)] if intensities else [0.0, 0.0],
            "most_frequent_emotion": most_frequent
        }
