# -*- coding: utf-8 -*-
"""
HumanThinking 睡眠管理器

三阶段睡眠设计：
- 阶段一：浅睡眠（Light Sleep）- 扫描7天日志，去重过滤，标记重要信息，暂存
- 阶段二：REM - 提取主题，发现跨对话模式，生成反思摘要，识别持久真理
- 阶段三：深睡眠（Deep Sleep）- 六维评分，高分写入MEMORY.md长期记忆
"""

import logging
import time
import os
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class SleepConfig:
    """睡眠配置"""
    def __init__(
        self,
        enable_agent_sleep: bool = True,
        light_sleep_minutes: float = 30,
        rem_minutes: float = 60,
        deep_sleep_minutes: float = 120,
        auto_consolidate: bool = True,
        consolidate_days: int = 7,
        frozen_days: int = 30,
        archive_days: int = 90,
        delete_days: int = 180,
        enable_insight: bool = True,
        enable_dream_log: bool = True,
        memory_md_path: str = None,
    ):
        self.enable_agent_sleep = enable_agent_sleep
        self.light_sleep_seconds = int(light_sleep_minutes * 60)
        self.rem_seconds = int(rem_minutes * 60)
        self.deep_sleep_seconds = int(deep_sleep_minutes * 60)
        self.light_sleep_minutes = light_sleep_minutes
        self.rem_minutes = rem_minutes
        self.deep_sleep_minutes = deep_sleep_minutes
        self.auto_consolidate = auto_consolidate
        self.consolidate_days = consolidate_days
        self.frozen_days = min(max(frozen_days, 1), 90)
        self.archive_days = min(max(archive_days, frozen_days + 1), 180)
        self.delete_days = min(max(delete_days, archive_days + 1), 365)
        self.enable_insight = enable_insight
        self.enable_dream_log = enable_dream_log
        self.memory_md_path = memory_md_path


class AgentSleepState:
    """Agent 睡眠状态
    
    状态转换：
    active → light_sleep → rem → deep_sleep → active(唤醒)
    """
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.is_active = True
        self.is_light_sleep = False
        self.is_rem = False
        self.is_deep_sleep = False
        self.last_active_time = time.time()
        self.last_light_sleep_time: Optional[float] = None
        self.last_rem_time: Optional[float] = None
        self.last_deep_sleep_time: Optional[float] = None
        self.last_consolidate_time: Optional[float] = None
        
        self.pending_importance: List[Dict] = []
        self.lasting_truths: List[Dict] = []
        self.theme_summary: Optional[str] = None


class SleepManager:
    """睡眠管理器 - 事件驱动模式"""
    
    def __init__(self, config: SleepConfig = None):
        self.config = config or SleepConfig()
        self._agent_states: Dict[str, AgentSleepState] = {}
        
        logger.info(f"SleepManager initialized: {self.config.__dict__}")
    
    def update_config(self, config: SleepConfig):
        """更新配置"""
        self.config = config
        logger.info(f"SleepManager config updated: {config.__dict__}")
    
    def record_activity(self, agent_id: str) -> bool:
        """记录活动并检查睡眠状态
        
        Returns:
            True 表示执行了睡眠任务
        """
        if not self.config.enable_agent_sleep:
            return False
        
        if agent_id not in self._agent_states:
            self._agent_states[agent_id] = AgentSleepState(agent_id)
        
        state = self._agent_states[agent_id]
        current_time = time.time()
        
        if state.is_deep_sleep:
            logger.info(f"Agent {agent_id} woke up from deep sleep")
            self._write_memory_md(agent_id, state)
            self._reset_to_active(state)
            return True
        
        if state.is_rem:
            idle_time = current_time - state.last_active_time
            if idle_time >= self.config.deep_sleep_seconds:
                logger.info(f"Agent {agent_id} entering deep sleep (was REM)")
                state.is_rem = False
                state.is_deep_sleep = True
                state.last_deep_sleep_time = current_time
                self._execute_deep_sleep(agent_id, state)
                return True
            else:
                return False
        
        if state.is_light_sleep:
            idle_time = current_time - state.last_active_time
            if idle_time >= self.config.rem_seconds:
                logger.info(f"Agent {agent_id} entering REM (was light sleep)")
                state.is_light_sleep = False
                state.is_rem = True
                state.last_rem_time = current_time
                self._execute_rem(agent_id, state)
                return True
            elif idle_time >= self.config.deep_sleep_seconds:
                logger.info(f"Agent {agent_id} entering deep sleep (was light sleep)")
                state.is_light_sleep = False
                state.is_deep_sleep = True
                state.last_deep_sleep_time = current_time
                self._execute_deep_sleep(agent_id, state)
                return True
            else:
                return False
        
        if state.is_active:
            idle_time = current_time - state.last_active_time
            
            if idle_time >= self.config.deep_sleep_seconds:
                logger.info(f"Agent {agent_id} entering deep sleep (from active)")
                self._enter_deep_sleep(state, current_time)
                return True
            elif idle_time >= self.config.rem_seconds:
                logger.info(f"Agent {agent_id} entering REM (from active)")
                self._enter_rem(state, current_time)
                return True
            elif idle_time >= self.config.light_sleep_seconds:
                logger.info(f"Agent {agent_id} entering light sleep")
                self._enter_light_sleep(state, current_time)
                return True
        
        state.last_active_time = current_time
        return False
    
    def _reset_to_active(self, state: AgentSleepState):
        """重置为活跃状态"""
        state.is_active = True
        state.is_light_sleep = False
        state.is_rem = False
        state.is_deep_sleep = False
        state.last_active_time = time.time()
    
    def _enter_light_sleep(self, state: AgentSleepState, current_time: float):
        """进入浅层睡眠"""
        state.is_active = False
        state.is_light_sleep = True
        state.last_light_sleep_time = current_time
        
        self._execute_light_sleep(state.agent_id, state)
    
    def _enter_rem(self, state: AgentSleepState, current_time: float):
        """进入REM阶段"""
        state.is_active = False
        state.is_rem = True
        state.last_rem_time = current_time
        
        self._execute_rem(state.agent_id, state)
    
    def _enter_deep_sleep(self, state: AgentSleepState, current_time: float):
        """进入深层睡眠"""
        state.is_active = False
        state.is_deep_sleep = True
        state.last_deep_sleep_time = current_time
        
        self._execute_deep_sleep(state.agent_id, state)
    
    def _execute_light_sleep(self, agent_id: str, state: AgentSleepState):
        """阶段一：浅层睡眠
        
        扫描最近7天内的对话日志
        去重、过滤废话、标记潜在重要信息
        仅暂存，不写入长期记忆
        """
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_light_sleep(agent_id, state))
            loop.close()
        except Exception as e:
            logger.error(f"Error in light sleep: {e}", exc_info=True)
    
    async def _async_light_sleep(self, agent_id: str, state: AgentSleepState):
        """异步执行浅层睡眠任务"""
        from .database import HumanThinkingDB
        
        db = HumanThinkingDB(agent_id)
        await db.initialize()
        
        try:
            if self.config.enable_dream_log:
                await db.add_dream_log(agent_id, "LIGHT_SLEEP", "阶段一：浅层睡眠 - 扫描7天日志，去重过滤")
            
            memories = await db.get_recent_memories(agent_id, days=7)
            
            if not memories:
                logger.info(f"No memories to process in light sleep")
                return
            
            deduplicated = self._deduplicate_memories(memories)
            filtered = self._filter_noise(deduplicated)
            important = self._mark_potential_importance(filtered)
            
            state.pending_importance = important
            
            if self.config.enable_dream_log:
                await db.add_dream_log(
                    agent_id, "LIGHT_SLEEP_COMPLETE",
                    f"阶段一完成：扫描{len(memories)}条，去重{len(deduplicated)}条，标记{len(important)}条潜在重要",
                    memories_scanned=len(memories),
                    memories_deduped=len(deduplicated),
                    important_count=len(important)
                )
            
            logger.info(f"Light sleep: scanned={len(memories)}, deduped={len(deduplicated)}, important={len(important)}")
            
        finally:
            await db.close()
    
    def _deduplicate_memories(self, memories: List[Dict]) -> List[Dict]:
        """去重 - 基于内容相似度"""
        if not memories:
            return []
        
        deduplicated = []
        seen_contents = set()
        
        for memory in memories:
            content = memory.get("content", "")
            content_hash = hash(content[:100])
            
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                deduplicated.append(memory)
        
        return deduplicated
    
    def _filter_noise(self, memories: List[Dict]) -> List[Dict]:
        """过滤废话"""
        noise_patterns = [
            r"^好的$",
            r"^收到$",
            r"^明白$",
            r"^是的$",
            r"^ok$",
            r"^OK$",
            r"^\[图片\]",
            r"^\[表情\]",
            r"^hi$",
            r"^hello$",
            r"^hey$",
        ]
        
        filtered = []
        for memory in memories:
            content = memory.get("content", "").strip()
            is_noise = any(re.match(pattern, content, re.IGNORECASE) for pattern in noise_patterns)
            
            if not is_noise and len(content) > 5:
                filtered.append(memory)
        
        return filtered
    
    def _mark_potential_importance(self, memories: List[Dict]) -> List[Dict]:
        """标记潜在重要信息"""
        important_keywords = [
            "喜欢", "讨厌", "偏好", "想要", "希望", "需要", "要求",
            "订单", "地址", "电话", "账号", "密码", "支付",
            "价格", "优惠", "折扣", "活动", "促销",
            "问题", "错误", "故障", "解决", "修复",
            "喜欢", "感谢", "满意", "不满意", "投诉",
            "first", "important", "remember", "never forget",
        ]
        
        important = []
        for memory in memories:
            content = memory.get("content", "").lower()
            importance_score = sum(1 for kw in important_keywords if kw.lower() in content)
            
            if importance_score > 0:
                memory["potential_importance"] = importance_score
                important.append(memory)
        
        return sorted(important, key=lambda x: x.get("potential_importance", 0), reverse=True)
    
    def _execute_rem(self, agent_id: str, state: AgentSleepState):
        """阶段二：REM - 快速眼动
        
        提取主题、发现跨对话的关联模式
        生成"反思摘要"，识别"持久真理"（Lasting Truths）
        仍不写入长期记忆，仅为决策提供依据
        """
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_rem(agent_id, state))
            loop.close()
        except Exception as e:
            logger.error(f"Error in REM: {e}", exc_info=True)
    
    async def _async_rem(self, agent_id: str, state: AgentSleepState):
        """异步执行REM阶段"""
        from .database import HumanThinkingDB
        
        db = HumanThinkingDB(agent_id)
        await db.initialize()
        
        try:
            if self.config.enable_dream_log:
                await db.add_dream_log(agent_id, "REM", "阶段二：REM - 提取主题，发现关联模式")
            
            pending = state.pending_importance
            if not pending:
                memories = await db.get_recent_memories(agent_id, days=7)
                pending = self._deduplicate_memories(memories)
                pending = self._filter_noise(pending)
            
            themes = self._extract_themes(pending)
            state.theme_summary = themes["summary"]
            
            patterns = self._find_cross_session_patterns(pending)
            lasting_truths = self._identify_lasting_truths(pending, patterns)
            state.lasting_truths = lasting_truths
            
            if self.config.enable_insight:
                theme_summary = f"近期主要关注：{', '.join([p.get('theme', '') for p in themes['themes'][:3]])}"
                await db.add_dream_log(
                    agent_id=agent_id,
                    action="REFLECTION",
                    details=theme_summary,
                    memories_scanned=len(themes['themes']) if themes.get('themes') else 0,
                    memories_consolidated=len(lasting_truths) if lasting_truths else 0
                )
            
            if self.config.enable_dream_log:
                await db.add_dream_log(
                    agent_id, "REM_COMPLETE",
                    f"阶段二完成：提取{len(themes['themes'])}个主题，识别{len(lasting_truths)}条持久真理",
                    themes_count=len(themes["themes"]),
                    truths_count=len(lasting_truths)
                )
            
            logger.info(f"REM: themes={len(themes['themes'])}, truths={len(lasting_truths)}")
            
        finally:
            await db.close()
    
    def _extract_themes(self, memories: List[Dict]) -> Dict:
        """提取主题"""
        themes = []
        theme_keywords = {
            "购物": ["订单", "商品", "购买", "支付", "快递", "收货"],
            "售后": ["退货", "退款", "换货", "维修", "投诉"],
            "咨询": ["价格", "优惠", "活动", "推荐", "介绍"],
            "技术支持": ["问题", "错误", "故障", "解决", "使用"],
            "账户": ["账号", "密码", "登录", "注册", "绑定"],
        }
        
        theme_counts = {theme: 0 for theme in theme_keywords}
        
        for memory in memories:
            content = memory.get("content", "")
            for theme, keywords in theme_keywords.items():
                if any(kw in content for kw in keywords):
                    theme_counts[theme] += 1
        
        for theme, count in theme_counts.items():
            if count > 0:
                themes.append({"theme": theme, "count": count})
        
        themes = sorted(themes, key=lambda x: x["count"], reverse=True)[:5]
        
        summary = f"近期主要关注：{', '.join([t['theme'] for t in themes[:3]])}"
        
        return {"themes": themes, "summary": summary}
    
    def _find_cross_session_patterns(self, memories: List[Dict]) -> List[Dict]:
        """发现跨对话关联模式"""
        patterns = []
        
        user_sessions = {}
        for memory in memories:
            session_id = memory.get("session_id", "unknown")
            user_id = memory.get("user_id", "unknown")
            key = f"{user_id}:{session_id}"
            
            if key not in user_sessions:
                user_sessions[key] = []
            user_sessions[key].append(memory)
        
        for key, session_memories in user_sessions.items():
            if len(session_memories) > 3:
                content_preview = session_memories[0].get("content", "")[:50]
                patterns.append({
                    "session": key,
                    "message_count": len(session_memories),
                    "preview": content_preview
                })
        
        return patterns[:10]
    
    def _identify_lasting_truths(self, memories: List[Dict], patterns: List[Dict]) -> List[Dict]:
        """识别持久真理"""
        truths = []
        
        preference_keywords = ["喜欢", "想要", "偏好", "希望", "讨厌", "不要"]
        fact_keywords = ["订单号", "地址", "电话", "账号"]
        emotion_keywords = ["感谢", "满意", "开心", "生气", "失望"]
        
        for memory in memories:
            content = memory.get("content", "")
            
            truth_type = None
            if any(kw in content for kw in preference_keywords):
                truth_type = "preference"
            elif any(kw in content for kw in fact_keywords):
                truth_type = "fact"
            elif any(kw in content for kw in emotion_keywords):
                truth_type = "emotion"
            
            if truth_type and memory.get("potential_importance", 0) >= 1:
                truths.append({
                    "type": truth_type,
                    "content": content[:200],
                    "importance": memory.get("potential_importance", 1)
                })
        
        return sorted(truths, key=lambda x: x.get("importance", 0), reverse=True)[:20]
    
    def _execute_deep_sleep(self, agent_id: str, state: AgentSleepState):
        """阶段三：深层睡眠
        
        对候选信息进行六维加权评分
        高分条目写入 MEMORY.md，成为AI的"长期记忆"
        """
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._async_deep_sleep(agent_id, state))
            loop.close()
        except Exception as e:
            logger.error(f"Error in deep sleep: {e}", exc_info=True)
    
    async def _async_deep_sleep(self, agent_id: str, state: AgentSleepState):
        """异步执行深层睡眠任务"""
        from .database import HumanThinkingDB
        
        db = HumanThinkingDB(agent_id)
        await db.initialize()
        
        try:
            if self.config.enable_dream_log:
                await db.add_dream_log(agent_id, "DEEP_SLEEP", "阶段三：深层睡眠 - 六维评分，写入长期记忆")
            
            forgetting_result = await db.apply_forgetting_curve(
                agent_id,
                frozen_days=self.config.frozen_days,
                archive_days=self.config.archive_days,
                delete_days=self.config.delete_days
            )
            
            all_memories = await db.get_memories_for_consolidation(agent_id, self.config.consolidate_days)
            
            candidates = state.pending_importance + all_memories
            
            promoted_count = 0
            long_term_memories = []
            
            for memory in candidates:
                memory_importance = memory.get("importance", 3)
                scores = self._six_dimensional_score(memory, all_memories)
                
                # 两种情况提升为长期记忆：
                # 1. importance >= 4 直接提升
                # 2. 六维评分 >= 0.5 提升
                should_promote = memory_importance >= 4 or scores["total"] >= 0.5
                
                if should_promote:
                    memory_id = memory.get("id")
                    await db.set_memory_tier(memory_id, "long_term")
                    await db.update_memory_score(memory_id, scores["total"])
                    
                    long_term_memories.append({
                        "content": memory.get("content", "")[:300],
                        "score": scores["total"],
                        "importance": memory_importance,
                        "type": memory.get("memory_type", "general")
                    })
                    promoted_count += 1
            
            state.lasting_truths.extend(long_term_memories[:10])
            
            if self.config.enable_insight:
                insights = self._generate_insights(all_memories)
                for insight in insights:
                    await db.add_insight(
                        agent_id=agent_id,
                        title=insight["title"],
                        content=insight["content"],
                        memory_count=len(all_memories),
                        insight_type=insight.get("type", "pattern")
                    )
            
            if self.config.enable_dream_log:
                await db.add_dream_log(
                    agent_id, "DEEP_SLEEP_COMPLETE",
                    f"阶段三完成：六维评分，{promoted_count}条写入长期记忆",
                    promoted_count=promoted_count,
                    forgetting_result=forgetting_result
                )
            
            logger.info(f"Deep sleep: promoted={promoted_count}, forgetting={forgetting_result}")
            
        finally:
            await db.close()
    
    def _write_memory_md(self, agent_id: str, state: AgentSleepState):
        """写入 MEMORY.md 长期记忆文件"""
        if not self.config.memory_md_path:
            return
        
        try:
            memory_file = Path(self.config.memory_md_path) / agent_id / "MEMORY.md"
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            
            content_lines = ["# AI 长期记忆\n", f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"]
            
            if state.lasting_truths:
                content_lines.append("## 持久真理 (Lasting Truths)\n\n")
                for i, truth in enumerate(state.lasting_truths[:20], 1):
                    truth_type = truth.get("type", "general")
                    truth_content = truth.get("content", "")
                    content_lines.append(f"{i}. [{truth_type}] {truth_content}\n")
                content_lines.append("\n")
            
            content_lines.append("## 反思摘要 (Reflection Summary)\n\n")
            content_lines.append(f"{state.theme_summary or '暂无'}\n\n")
            
            content_lines.append("---\n*此文件由AI自动生成，定期更新*\n")
            
            memory_file.write_text("".join(content_lines), encoding="utf-8")
            logger.info(f"MEMORY.md written for agent {agent_id}")
            
        except Exception as e:
            logger.error(f"Error writing MEMORY.md: {e}")
    
    def _six_dimensional_score(self, memory: Dict, all_memories: List[Dict] = None) -> Dict[str, float]:
        """六维加权评分系统
        
        评分维度及权重：
        - 相关性（30%）：与用户长期兴趣的相关程度
        - 频率（24%）：出现频率
        - 时效性（15%）：时效性权重
        - 查询多样性（15%）：被查询的模式多样性
        - 整合度（10%）：与其他记忆的关联程度
        - 概念丰富度（6%）：内容的概念密度
        """
        scores = {}
        
        content = memory.get("content", "")
        importance = memory.get("importance", 3)
        access_count = memory.get("access_count", 0)
        memory_type = memory.get("memory_type", "general")
        
        relevance_score = self._calc_relevance(memory, all_memories or [])
        frequency_score = min(access_count / 10.0, 1.0)
        recency_score = self._calc_recency(memory)
        diversity_score = self._calc_diversity(memory, all_memories or [])
        integration_score = self._calc_integration(memory, all_memories or [])
        concept_score = self._calc_concept_richness(content)
        
        scores["relevance"] = relevance_score * 0.30
        scores["frequency"] = frequency_score * 0.24
        scores["recency"] = recency_score * 0.15
        scores["diversity"] = diversity_score * 0.15
        scores["integration"] = integration_score * 0.10
        scores["concept"] = concept_score * 0.06
        
        scores["total"] = sum(scores.values())
        return scores
    
    def _calc_relevance(self, memory: Dict, all_memories: List[Dict]) -> float:
        """计算相关性分数"""
        importance = memory.get("importance", 3)
        memory_type = memory.get("memory_type", "general")
        
        type_weights = {"fact": 0.9, "preference": 0.85, "emotion": 0.8, "general": 0.5}
        type_weight = type_weights.get(memory_type, 0.5)
        
        return min((importance / 5.0) * type_weight, 1.0)
    
    def _calc_recency(self, memory: Dict) -> float:
        """计算时效性分数"""
        created_at = memory.get("created_at")
        if not created_at:
            return 0.5
        
        if isinstance(created_at, str):
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                age_days = (datetime.now() - dt.replace(tzinfo=None)).days
            except (ValueError, TypeError):
                return 0.5
        else:
            age_days = (time.time() - created_at) / 86400
        
        return max(0, 1.0 - (age_days / 30.0))
    
    def _calc_diversity(self, memory: Dict, all_memories: List[Dict]) -> float:
        """计算查询多样性分数"""
        access_patterns = memory.get("access_patterns", [])
        if not access_patterns:
            return 0.3
        
        unique_contexts = len(set(str(p) for p in access_patterns[-10:]))
        return min(unique_contexts / 5.0, 1.0)
    
    def _calc_integration(self, memory: Dict, all_memories: List[Dict]) -> float:
        """计算整合度分数"""
        related_ids = memory.get("related_memory_ids", [])
        if not related_ids:
            return 0.2
        
        return min(len(related_ids) / 10.0, 1.0)
    
    def _calc_concept_richness(self, content: str) -> float:
        """计算概念丰富度分数"""
        if not content:
            return 0.0
        
        concept_keywords = [
            "因为", "所以", "但是", "如果", "虽然", "而且", "或者",
            "first", "then", "because", "however", "therefore",
            "分析", "比较", "总结", "结论", "建议"
        ]
        
        keyword_count = sum(1 for kw in concept_keywords if kw.lower() in content.lower())
        return min(keyword_count / 5.0, 1.0)
    
    def _generate_insights(self, memories: List[Dict]) -> List[Dict]:
        """生成洞察"""
        insights = []
        
        if not memories:
            return insights
        
        memory_types = {}
        for m in memories:
            mtype = m.get("memory_type", "general")
            memory_types[mtype] = memory_types.get(mtype, 0) + 1
        
        if memory_types:
            dominant = max(memory_types.items(), key=lambda x: x[1])
            type_names = {"fact": "事实", "preference": "偏好", "emotion": "情感", "general": "一般"}
            insights.append({
                "title": f"记忆类型分布",
                "content": f"近期{dominant[1]}条记忆主要为【{type_names.get(dominant[0], dominant[0])}】类型",
                "type": "pattern"
            })
        
        return insights[:3]
    
    def is_sleeping(self, agent_id: str) -> bool:
        """检查 Agent 是否在睡眠"""
        state = self._agent_states.get(agent_id)
        if not state:
            return False
        return state.is_light_sleep or state.is_rem or state.is_deep_sleep
    
    def get_sleeping_agents(self) -> List[str]:
        """获取所有睡眠中的 Agent"""
        return [
            agent_id for agent_id, state in self._agent_states.items()
            if state.is_light_sleep or state.is_rem or state.is_deep_sleep
        ]
    
    def get_status(self, agent_id: str) -> dict:
        """获取 Agent 睡眠状态"""
        state = self._agent_states.get(agent_id)
        if not state:
            return {"agent_id": agent_id, "status": "active", "sleep_type": None}
        
        if state.is_deep_sleep:
            return {"agent_id": agent_id, "status": "sleeping", "sleep_type": "deep"}
        elif state.is_rem:
            return {"agent_id": agent_id, "status": "sleeping", "sleep_type": "rem"}
        elif state.is_light_sleep:
            return {"agent_id": agent_id, "status": "sleeping", "sleep_type": "light"}
        else:
            return {"agent_id": agent_id, "status": "active", "sleep_type": None}


# Agent 配置隔离 - 每个 Agent 拥有独立的睡眠配置
_agent_sleep_configs: Dict[str, SleepConfig] = {}
_global_sleep_manager: Optional[SleepManager] = None


def get_sleep_manager(agent_id: str = None) -> Optional[SleepManager]:
    """获取睡眠管理器
    
    Args:
        agent_id: Agent ID，用于获取 Agent 专属配置
    
    Returns:
        SleepManager: 如果指定了 agent_id，返回带有该 Agent 配置的 SleepManager
    """
    global _global_sleep_manager, _agent_sleep_configs
    
    if not _global_sleep_manager:
        return None
    
    if agent_id and agent_id in _agent_sleep_configs:
        # 返回带有 Agent 专属配置的管理器副本
        agent_config = _agent_sleep_configs[agent_id]
        agent_manager = SleepManager(agent_config)
        # 复制状态
        agent_manager._agent_states = _global_sleep_manager._agent_states
        return agent_manager
    
    return _global_sleep_manager


def init_sleep_manager(config: SleepConfig = None) -> SleepManager:
    global _global_sleep_manager
    _global_sleep_manager = SleepManager(config or SleepConfig())
    return _global_sleep_manager


def get_agent_sleep_config(agent_id: str = None) -> SleepConfig:
    """获取 Agent 专属睡眠配置
    
    Args:
        agent_id: Agent ID
    
    Returns:
        SleepConfig: 如果存在 Agent 专属配置则返回，否则返回全局配置
    """
    global _agent_sleep_configs, _global_sleep_manager
    
    if agent_id and agent_id in _agent_sleep_configs:
        return _agent_sleep_configs[agent_id]
    
    if _global_sleep_manager:
        return _global_sleep_manager.config
    
    return SleepConfig()


def set_agent_sleep_config(agent_id: str, config: SleepConfig):
    """设置 Agent 专属睡眠配置
    
    Args:
        agent_id: Agent ID
        config: 睡眠配置对象
    """
    global _agent_sleep_configs
    _agent_sleep_configs[agent_id] = config
    logger.info(f"Sleep config set for agent {agent_id}: {config.__dict__}")


def load_agent_sleep_config(agent_id: str) -> SleepConfig:
    """从文件加载 Agent 专属睡眠配置
    
    Args:
        agent_id: Agent ID
    
    Returns:
        SleepConfig: 加载的配置，如果文件不存在则返回默认配置
    """
    from pathlib import Path
    import json
    
    config_path = Path.home() / ".qwenpaw" / "workspaces" / agent_id / "sleep_config.json"
    
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            config = SleepConfig()
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            
            # 缓存配置
            set_agent_sleep_config(agent_id, config)
            logger.info(f"Loaded sleep config for agent {agent_id} from {config_path}")
            return config
        except Exception as e:
            logger.warning(f"Failed to load sleep config for agent {agent_id}: {e}")
    
    return get_agent_sleep_config(agent_id)


def save_agent_sleep_config(agent_id: str, config: SleepConfig) -> bool:
    """保存 Agent 专属睡眠配置到文件
    
    Args:
        agent_id: Agent ID
        config: 睡眠配置对象
    
    Returns:
        bool: 是否保存成功
    """
    from pathlib import Path
    import json
    
    try:
        config_path = Path.home() / ".qwenpaw" / "workspaces" / agent_id / "sleep_config.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            "enable_agent_sleep": config.enable_agent_sleep,
            "light_sleep_minutes": config.light_sleep_minutes,
            "rem_minutes": config.rem_minutes,
            "deep_sleep_minutes": config.deep_sleep_minutes,
            "auto_consolidate": config.auto_consolidate,
            "consolidate_days": config.consolidate_days,
            "frozen_days": config.frozen_days,
            "archive_days": config.archive_days,
            "delete_days": config.delete_days,
            "enable_insight": config.enable_insight,
            "enable_dream_log": config.enable_dream_log,
        }
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, ensure_ascii=False, indent=2)
        
        # 更新缓存
        set_agent_sleep_config(agent_id, config)
        logger.info(f"Saved sleep config for agent {agent_id} to {config_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save sleep config for agent {agent_id}: {e}")
        return False


def record_agent_activity(agent_id: str) -> bool:
    """记录活动并检查睡眠状态"""
    if _global_sleep_manager:
        return _global_sleep_manager.record_activity(agent_id)
    return False


def pulse_agent(agent_id: str) -> bool:
    """心跳"""
    return record_agent_activity(agent_id)


def notify_task_start(agent_id: str) -> bool:
    """定时任务"""
    return record_agent_activity(agent_id)


def is_agent_sleeping(agent_id: str) -> bool:
    if _global_sleep_manager:
        return _global_sleep_manager.is_sleeping(agent_id)
    return False
