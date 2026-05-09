"""
ReAct 模式智能检索器 - 自适应选择检索策略

使用 ReAct (Reasoning + Acting) 模式进行智能检索，
根据查询意图自动选择最佳检索策略。

Author: Qwen3.6-Plus
Version: 1.0.0-beta0.1
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RetrievalStrategy(Enum):
    """检索策略"""
    VECTOR_SIMILARITY = "vector_similarity"    # 向量相似度检索
    KEYWORD_MATCH = "keyword_match"            # 关键词匹配
    HYBRID_SEARCH = "hybrid_search"            # 混合搜索
    TEMPORAL_SEARCH = "temporal_search"        # 时间范围检索
    SEMANTIC_FILTER = "semantic_filter"        # 语义过滤
    PERSONAL_MEMORY = "personal_memory"        # 个人记忆检索
    TASK_MEMORY = "task_memory"                # 任务记忆检索
    TOOL_MEMORY = "tool_memory"                # 工具记忆检索


@dataclass
class RetrievalAction:
    """检索动作"""
    strategy: RetrievalStrategy
    params: Dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    confidence: float = 0.0


@dataclass
class RetrievalResult:
    """检索结果"""
    query: str
    strategy_used: RetrievalStrategy
    memories: List[Any]
    total_candidates: int
    time_cost_ms: float
    reasoning_trace: List[str] = field(default_factory=list)


class AgenticRetriever:
    """
    ReAct 模式智能检索器
    
    使用推理-行动循环，根据查询意图自动选择最佳检索策略：
    
    1. Thought: 分析查询意图
    2. Action: 选择检索策略
    3. Observation: 观察检索结果
    4. Refine: 根据结果调整策略（可选多轮）
    
    支持：
    - 多策略自动选择
    - 多轮检索优化
    - 意图识别
    - 结果评估与重排序
    """

    def __init__(
        self,
        retrieve_func: Optional[Callable] = None,
        vector_search_func: Optional[Callable] = None,
        keyword_search_func: Optional[Callable] = None,
        llm_analyze_func: Optional[Callable] = None,
        max_retries: int = 2,
        enable_multi_hop: bool = True,
        max_hops: int = 3
    ):
        """
        初始化智能检索器
        
        Args:
            retrieve_func: 基础检索函数
            vector_search_func: 向量搜索函数
            keyword_search_func: 关键词搜索函数
            llm_analyze_func: LLM 意图分析函数
            max_retries: 最大重试次数
            enable_multi_hop: 是否启用多跳检索
            max_hops: 最大跳跃次数
        """
        self.retrieve_func = retrieve_func
        self.vector_search_func = vector_search_func
        self.keyword_search_func = keyword_search_func
        self.llm_analyze_func = llm_analyze_func
        self.max_retries = max_retries
        self.enable_multi_hop = enable_multi_hop
        self.max_hops = max_hops
    
    async def retrieve(
        self,
        query: str,
        agent_id: str,
        user_id: str,
        target_id: Optional[str] = None,
        top_k: int = 10,
        time_range: Optional[Tuple[str, str]] = None,
        memory_type: Optional[str] = None
    ) -> RetrievalResult:
        """
        执行智能检索
        
        Args:
            query: 查询文本
            agent_id: Agent ID
            user_id: 用户 ID
            target_id: 目标 ID（可选）
            top_k: 返回结果数量
            time_range: 时间范围 (start, end)
            memory_type: 记忆类型过滤
            
        Returns:
            检索结果
        """
        import time
        start_time = time.time()
        
        reasoning_trace = []
        
        # Step 1: 分析查询意图
        intent_analysis = await self._analyze_intent(query)
        reasoning_trace.append(f"意图分析: {intent_analysis['reasoning']}")
        
        # Step 2: 选择检索策略
        selected_strategy = self._select_strategy(intent_analysis, memory_type, time_range)
        reasoning_trace.append(f"选择策略: {selected_strategy.strategy.value}")
        
        # Step 3: 执行检索
        memories = await self._execute_search(
            query,
            selected_strategy,
            agent_id,
            user_id,
            target_id,
            top_k,
            time_range
        )
        
        # Step 4: 多跳检索（如果启用）
        if self.enable_multi_hop and memories:
            for hop in range(1, self.max_hops):
                # 检查是否需要进一步检索
                need_more = await self._evaluate_results(query, memories, top_k)
                if not need_more:
                    break
                
                reasoning_trace.append(f"第 {hop+1} 跳检索")
                
                # 基于当前结果生成新查询
                new_query = await self._generate_follow_up_query(query, memories)
                new_strategy = self._select_follow_up_strategy(intent_analysis, hop)
                
                follow_up_memories = await self._execute_search(
                    new_query,
                    new_strategy,
                    agent_id,
                    user_id,
                    target_id,
                    top_k // 2,
                    time_range
                )
                
                # 合并结果
                memories = self._merge_results(memories, follow_up_memories)
        
        # Step 5: 结果排序
        memories = self._rank_results(query, memories, top_k)
        
        time_cost = (time.time() - start_time) * 1000
        
        return RetrievalResult(
            query=query,
            strategy_used=selected_strategy.strategy,
            memories=memories,
            total_candidates=len(memories),
            time_cost_ms=time_cost,
            reasoning_trace=reasoning_trace
        )
    
    async def _analyze_intent(self, query: str) -> Dict[str, Any]:
        """
        分析查询意图
        
        Returns:
            意图分析结果
        """
        default_result = {
            "intent": "general",
            "entities": [],
            "time_mentions": [],
            "memory_types": [],
            "reasoning": "使用默认分析"
        }
        
        if not self.llm_analyze_func:
            # 启发式意图分析
            return self._heuristic_intent_analysis(query)
        
        try:
            # 使用 LLM 分析
            prompt = f"""分析以下查询的意图，返回 JSON 格式：
查询：{query}

返回格式：
{{
    "intent": "意图类型 (personal/task/tool/general)",
    "entities": ["实体列表"],
    "time_mentions": ["时间提及"],
    "memory_types": ["记忆类型"],
    "reasoning": "分析原因"
}}
"""
            result = await self.llm_analyze_func(prompt)
            # 解析 LLM 返回的 JSON
            # 简化处理，实际需要 JSON 解析
            return {
                "intent": "general",
                "entities": [],
                "time_mentions": [],
                "memory_types": [],
                "reasoning": result[:100]
            }
        except Exception:
            return self._heuristic_intent_analysis(query)
    
    def _heuristic_intent_analysis(self, query: str) -> Dict[str, Any]:
        """启发式意图分析"""
        import re
        
        query_lower = query.lower()
        
        # 检测个人记忆意图
        personal_keywords = ["我", "我的", "偏好", "习惯", "喜欢", "关系"]
        if any(kw in query_lower for kw in personal_keywords):
            intent = "personal"
            memory_types = ["preference", "habit", "relationship"]
        
        # 检测任务记忆意图
        elif any(kw in query_lower for kw in ["任务", "项目", "进度", "计划", "完成"]):
            intent = "task"
            memory_types = ["task", "progress", "plan"]
        
        # 检测工具记忆意图
        elif any(kw in query_lower for kw in ["工具", "使用", "方法", "命令", "报错"]):
            intent = "tool"
            memory_types = ["tool_usage", "error", "solution"]
        
        else:
            intent = "general"
            memory_types = []
        
        # 检测时间提及
        time_patterns = [
            r"昨天|今天|明天|上周|下周|上月|下月",
            r"\d{4}-\d{2}-\d{2}",
            r"最近|以前|之前|之后"
        ]
        time_mentions = []
        for pattern in time_patterns:
            matches = re.findall(pattern, query)
            time_mentions.extend(matches)
        
        # 提取实体（简化）
        entities = re.findall(r'["「『]([^"」』]+)["」』]', query)
        
        return {
            "intent": intent,
            "entities": entities,
            "time_mentions": time_mentions,
            "memory_types": memory_types,
            "reasoning": f"启发式分析: 意图={intent}, 实体={entities}"
        }
    
    def _select_strategy(
        self,
        intent_analysis: Dict[str, Any],
        memory_type: Optional[str],
        time_range: Optional[Tuple[str, str]]
    ) -> RetrievalAction:
        """
        选择检索策略
        
        Returns:
            选中的检索动作
        """
        intent = intent_analysis.get("intent", "general")
        memory_types = intent_analysis.get("memory_types", [])
        time_mentions = intent_analysis.get("time_mentions", [])
        
        # 根据记忆类型选择策略
        if memory_type == "personal" or intent == "personal":
            return RetrievalAction(
                strategy=RetrievalStrategy.PERSONAL_MEMORY,
                confidence=0.9,
                reasoning="检测到个人记忆意图"
            )
        elif memory_type == "task" or intent == "task":
            return RetrievalAction(
                strategy=RetrievalStrategy.TASK_MEMORY,
                confidence=0.9,
                reasoning="检测到任务记忆意图"
            )
        elif memory_type == "tool" or intent == "tool":
            return RetrievalAction(
                strategy=RetrievalStrategy.TOOL_MEMORY,
                confidence=0.9,
                reasoning="检测到工具记忆意图"
            )
        
        # 根据时间范围选择策略
        if time_range:
            return RetrievalAction(
                strategy=RetrievalStrategy.TEMPORAL_SEARCH,
                params={"time_range": time_range},
                confidence=0.85,
                reasoning="指定了时间范围"
            )
        
        # 根据时间提及选择策略
        if time_mentions:
            return RetrievalAction(
                strategy=RetrievalStrategy.TEMPORAL_SEARCH,
                params={"time_mentions": time_mentions},
                confidence=0.8,
                reasoning="检测到时间提及"
            )
        
        # 默认使用混合搜索
        return RetrievalAction(
            strategy=RetrievalStrategy.HYBRID_SEARCH,
            confidence=0.7,
            reasoning="默认使用混合搜索"
        )
    
    def _select_follow_up_strategy(
        self,
        intent_analysis: Dict[str, Any],
        hop_count: int
    ) -> RetrievalAction:
        """
        选择后续检索策略（多跳）
        
        Returns:
            后续检索动作
        """
        # 跳跃次数越多，使用更精确的策略
        if hop_count == 1:
            return RetrievalAction(
                strategy=RetrievalStrategy.VECTOR_SIMILARITY,
                confidence=0.7,
                reasoning="第一次跳跃：向量相似度"
            )
        elif hop_count == 2:
            return RetrievalAction(
                strategy=RetrievalStrategy.SEMANTIC_FILTER,
                confidence=0.6,
                reasoning="第二次跳跃：语义过滤"
            )
        else:
            return RetrievalAction(
                strategy=RetrievalStrategy.KEYWORD_MATCH,
                confidence=0.5,
                reasoning="后续跳跃：关键词匹配"
            )
    
    async def _execute_search(
        self,
        query: str,
        action: RetrievalAction,
        agent_id: str,
        user_id: str,
        target_id: Optional[str],
        top_k: int,
        time_range: Optional[Tuple[str, str]]
    ) -> List[Any]:
        """
        执行搜索
        
        Returns:
            检索结果列表
        """
        strategy = action.strategy
        
        # 分发到不同的搜索函数
        if strategy == RetrievalStrategy.HYBRID_SEARCH:
            if self.retrieve_func:
                return await self.retrieve_func(
                    query=query,
                    agent_id=agent_id,
                    user_id=user_id,
                    target_id=target_id,
                    top_k=top_k
                )
        
        elif strategy == RetrievalStrategy.VECTOR_SIMILARITY:
            if self.vector_search_func:
                return await self.vector_search_func(
                    query=query,
                    agent_id=agent_id,
                    user_id=user_id,
                    top_k=top_k
                )
        
        elif strategy == RetrievalStrategy.KEYWORD_MATCH:
            if self.keyword_search_func:
                return await self.keyword_search_func(
                    query=query,
                    agent_id=agent_id,
                    user_id=user_id,
                    top_k=top_k
                )
        
        elif strategy == RetrievalStrategy.TEMPORAL_SEARCH:
            # 时间范围检索
            if self.retrieve_func:
                return await self.retrieve_func(
                    query=query,
                    agent_id=agent_id,
                    user_id=user_id,
                    target_id=target_id,
                    top_k=top_k,
                    time_range=action.params.get("time_range", time_range)
                )
        
        elif strategy in [
            RetrievalStrategy.PERSONAL_MEMORY,
            RetrievalStrategy.TASK_MEMORY,
            RetrievalStrategy.TOOL_MEMORY
        ]:
            # 专用记忆检索（通过基础检索函数 + 类型过滤）
            if self.retrieve_func:
                memory_type_map = {
                    RetrievalStrategy.PERSONAL_MEMORY: "personal",
                    RetrievalStrategy.TASK_MEMORY: "task",
                    RetrievalStrategy.TOOL_MEMORY: "tool"
                }
                return await self.retrieve_func(
                    query=query,
                    agent_id=agent_id,
                    user_id=user_id,
                    target_id=target_id,
                    top_k=top_k,
                    memory_type=memory_type_map.get(strategy)
                )
        
        # 默认回退
        if self.retrieve_func:
            return await self.retrieve_func(
                query=query,
                agent_id=agent_id,
                user_id=user_id,
                target_id=target_id,
                top_k=top_k
            )
        
        return []
    
    async def _evaluate_results(
        self,
        query: str,
        memories: List[Any],
        top_k: int
    ) -> bool:
        """
        评估检索结果是否需要进一步检索
        
        Returns:
            True 表示需要更多检索
        """
        # 启发式评估
        if len(memories) < top_k // 2:
            return True
        
        if not memories:
            return True
        
        # 可以扩展为使用 LLM 评估结果相关性
        return False
    
    async def _generate_follow_up_query(
        self,
        original_query: str,
        current_results: List[Any]
    ) -> str:
        """
        基于当前结果生成后续查询
        
        Returns:
            新的查询文本
        """
        # 简化实现：从当前结果中提取关键词
        if not current_results:
            return original_query
        
        # 可以扩展为使用 LLM 生成更有针对性的查询
        return original_query
    
    def _merge_results(
        self,
        primary_results: List[Any],
        secondary_results: List[Any]
    ) -> List[Any]:
        """
        合并多跳检索结果
        
        Returns:
            合并后的结果
        """
        # 去重合并
        seen_ids = set()
        merged = []
        
        for memory in primary_results:
            memory_id = getattr(memory, 'id', str(memory))
            if memory_id not in seen_ids:
                seen_ids.add(memory_id)
                merged.append(memory)
        
        for memory in secondary_results:
            memory_id = getattr(memory, 'id', str(memory))
            if memory_id not in seen_ids:
                seen_ids.add(memory_id)
                merged.append(memory)
        
        return merged
    
    def _rank_results(
        self,
        query: str,
        memories: List[Any],
        top_k: int
    ) -> List[Any]:
        """
        结果排序
        
        Returns:
            排序后的结果
        """
        # 默认按内存顺序返回
        # 可以实现更复杂的排序算法（相关性、时间、温度等）
        return memories[:top_k]
