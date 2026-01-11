"""
Semantic Router - The Brain of UCP.

The router analyzes conversation context and decides which tools
to inject into the model's context window. It implements the
two-stage dispatch pattern from the design docs:

1. Stage 1: Semantic/keyword search to identify candidate tools
2. Stage 2: Re-ranking and filtering to select the minimal set

This is the Gorilla/RAFT-inspired component that solves Tool Overload.

Extended with SOTA pipeline for:
- Cross-encoder reranking
- Bandit-based selection
- Online learning from feedback
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from ucp.config import RouterConfig
from ucp.models import RoutingDecision, SessionState, ToolSchema

if TYPE_CHECKING:
    from ucp.bandit import SharedBanditScorer
    from ucp.online_opt import ToolBiasStore
    from ucp.routing_pipeline import RoutingPipeline
    from ucp.telemetry import SQLiteTelemetryStore
    from ucp.tool_zoo import ToolZoo

logger = structlog.get_logger(__name__)


class Router:
    """
    Semantic router for dynamic tool selection.

    Analyzes the conversation context and predicts which tools
    will be needed, returning only the relevant subset.
    """

    def __init__(self, config: RouterConfig, tool_zoo: ToolZoo) -> None:
        self.config = config
        self.tool_zoo = tool_zoo
        self._domain_keywords: dict[str, list[str]] = self._build_domain_keywords()

    def _build_domain_keywords(self) -> dict[str, list[str]]:
        """Build keyword mappings for domain detection."""
        return {
            "email": ["email", "mail", "inbox", "send", "reply", "forward", "gmail", "outlook"],
            "calendar": ["calendar", "schedule", "meeting", "event", "appointment", "book", "time"],
            "code": ["code", "git", "github", "commit", "branch", "pull request", "merge", "repo"],
            "files": ["file", "document", "folder", "drive", "upload", "download", "save", "open"],
            "database": ["database", "sql", "query", "table", "insert", "update", "delete", "db"],
            "web": ["browse", "search", "website", "url", "fetch", "scrape", "http"],
            "finance": ["pay", "invoice", "charge", "refund", "stripe", "payment", "transaction"],
            "communication": ["slack", "message", "chat", "notify", "alert", "send"],
        }

    def detect_domain(self, context: str) -> list[str]:
        """
        Detect likely domains from the context.

        Returns a list of domain names that match keywords in the context.
        """
        context_lower = context.lower()
        detected = []

        for domain, keywords in self._domain_keywords.items():
            for keyword in keywords:
                if keyword in context_lower:
                    detected.append(domain)
                    break

        return detected

    async def route(
        self,
        session: SessionState,
        current_message: str | None = None,
    ) -> RoutingDecision:
        """
        Determine which tools to inject based on current context.

        Args:
            session: The current session state with conversation history
            current_message: Optional current user message (if not in session yet)

        Returns:
            RoutingDecision with selected tools and reasoning
        """
        # Build context for routing
        context_parts = []

        # Include recent conversation
        context_parts.append(session.get_context_for_routing(n_messages=5))

        # Include current message if provided
        if current_message:
            context_parts.append(f"user: {current_message}")

        query = "\n".join(filter(None, context_parts))

        if not query.strip():
            # No context - return fallback tools
            return RoutingDecision(
                selected_tools=self.config.fallback_tools[:],
                scores={},
                reasoning="No context available, using fallback tools",
                query_used="",
            )

        # Stage 1: Detect domains for filtering
        domains = self.detect_domain(query)
        logger.debug("domains_detected", domains=domains, query_preview=query[:100])

        # Stage 2: Search the tool zoo
        if self.config.mode == "hybrid" and hasattr(self.tool_zoo, "hybrid_search"):
            results = self.tool_zoo.hybrid_search(query, top_k=self.config.max_tools * 2)
        elif self.config.mode == "keyword" and hasattr(self.tool_zoo, "keyword_search"):
            results = self.tool_zoo.keyword_search(query, top_k=self.config.max_tools * 2)
        else:
            # Default semantic search
            results = self.tool_zoo.search(query, top_k=self.config.max_tools * 2)

        # Stage 3: Re-rank and filter
        selected_tools, scores = self._rerank_and_filter(results, session, domains)

        # Ensure minimum tools
        if len(selected_tools) < self.config.min_tools:
            # Add fallback tools
            for fallback in self.config.fallback_tools:
                if fallback not in selected_tools:
                    selected_tools.append(fallback)
                    scores[fallback] = 0.1  # Low score for fallback
                if len(selected_tools) >= self.config.min_tools:
                    break

        # Build reasoning
        reasoning = self._build_reasoning(query, domains, results, selected_tools)

        decision = RoutingDecision(
            selected_tools=selected_tools,
            scores=scores,
            reasoning=reasoning,
            query_used=query[:500],  # Truncate for storage
        )

        logger.info(
            "routing_decision",
            selected_count=len(selected_tools),
            top_tool=selected_tools[0] if selected_tools else None,
            domains=domains,
        )

        return decision

    def _rerank_and_filter(
        self,
        results: list[tuple[ToolSchema, float]],
        session: SessionState,
        domains: list[str],
    ) -> tuple[list[str], dict[str, float]]:
        """
        Re-rank and filter search results.

        Applies:
        - Domain boosting (tools matching detected domains get higher scores)
        - Usage recency (recently used tools get slight boost)
        - Diversity (avoid too many tools from same server)
        """
        if not results:
            return [], {}

        # Score adjustments
        adjusted_scores: dict[str, float] = {}

        for tool, base_score in results:
            score = base_score

            # Domain boost
            if tool.domain and tool.domain in domains:
                score *= 1.3

            # Tag boost
            for tag in tool.tags:
                if tag.lower() in [d.lower() for d in domains]:
                    score *= 1.2
                    break

            # Recent usage boost (small)
            if tool.name in session.tool_usage:
                recency_boost = min(0.1, session.tool_usage[tool.name] * 0.02)
                score += recency_boost

            adjusted_scores[tool.name] = score

        # Sort by adjusted score
        sorted_tools = sorted(adjusted_scores.items(), key=lambda x: x[1], reverse=True)

        # Apply diversity filter - limit tools per server
        selected: list[str] = []
        scores: dict[str, float] = {}
        server_counts: dict[str, int] = {}
        max_per_server = 3

        for tool_name, score in sorted_tools:
            tool = self.tool_zoo.get_tool(tool_name)
            if not tool:
                continue

            server = tool.server_name
            if server_counts.get(server, 0) >= max_per_server:
                continue

            selected.append(tool_name)
            scores[tool_name] = score
            server_counts[server] = server_counts.get(server, 0) + 1

            if len(selected) >= self.config.max_tools:
                break

        return selected, scores

    def _build_reasoning(
        self,
        query: str,
        domains: list[str],
        results: list[tuple[ToolSchema, float]],
        selected: list[str],
    ) -> str:
        """Build human-readable reasoning for the selection."""
        parts = []

        if domains:
            parts.append(f"Detected domains: {', '.join(domains)}")

        if results:
            top_matches = [(t.display_name, f"{s:.2f}") for t, s in results[:3]]
            parts.append(f"Top matches: {top_matches}")

        parts.append(f"Selected {len(selected)} tools")

        return " | ".join(parts)


class AdaptiveRouter(Router):
    """
    Router that learns from usage patterns.

    Tracks which tools are actually used after selection and adjusts
    future predictions accordingly. This is the foundation for
    RAFT-style fine-tuning.
    """

    def __init__(self, config: RouterConfig, tool_zoo: ToolZoo) -> None:
        super().__init__(config, tool_zoo)
        # Track prediction -> usage for learning
        self._prediction_history: list[dict] = []
        self._tool_cooccurrence: dict[str, dict[str, int]] = {}

    def record_usage(
        self,
        prediction: RoutingDecision,
        actually_used: list[str],
    ) -> None:
        """
        Record which tools were actually used after a prediction.

        This data can be used to fine-tune the router.
        """
        record = {
            "predicted": prediction.selected_tools,
            "used": actually_used,
            "query": prediction.query_used,
            "precision": len(set(actually_used) & set(prediction.selected_tools)) / len(prediction.selected_tools) if prediction.selected_tools else 0,
            "recall": len(set(actually_used) & set(prediction.selected_tools)) / len(actually_used) if actually_used else 1,
        }
        self._prediction_history.append(record)

        # Update co-occurrence matrix
        for tool_a in actually_used:
            if tool_a not in self._tool_cooccurrence:
                self._tool_cooccurrence[tool_a] = {}
            for tool_b in actually_used:
                if tool_a != tool_b:
                    self._tool_cooccurrence[tool_a][tool_b] = (
                        self._tool_cooccurrence[tool_a].get(tool_b, 0) + 1
                    )

        logger.debug(
            "usage_recorded",
            precision=record["precision"],
            recall=record["recall"],
        )

    def get_cooccurring_tools(self, tool_name: str, top_k: int = 3) -> list[str]:
        """Get tools that frequently co-occur with the given tool."""
        if tool_name not in self._tool_cooccurrence:
            return []

        cooccur = self._tool_cooccurrence[tool_name]
        sorted_tools = sorted(cooccur.items(), key=lambda x: x[1], reverse=True)
        return [t for t, _ in sorted_tools[:top_k]]

    def _rerank_and_filter(
        self,
        results: list[tuple[ToolSchema, float]],
        session: SessionState,
        domains: list[str],
    ) -> tuple[list[str], dict[str, float]]:
        """Extended re-ranking with co-occurrence boost."""
        selected, scores = super()._rerank_and_filter(results, session, domains)

        # Boost tools that co-occur with recently used tools
        if session.tool_usage:
            recent_tools = list(session.tool_usage.keys())[-3:]
            cooccur_boost: dict[str, float] = {}

            for recent in recent_tools:
                for cooccur in self.get_cooccurring_tools(recent):
                    cooccur_boost[cooccur] = cooccur_boost.get(cooccur, 0) + 0.1

            # Apply boosts and re-sort
            for tool_name in list(scores.keys()):
                if tool_name in cooccur_boost:
                    scores[tool_name] += cooccur_boost[tool_name]

            # Re-sort by updated scores
            sorted_by_score = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            selected = [t for t, _ in sorted_by_score[:self.config.max_tools]]

        return selected, scores

    def get_learning_stats(self) -> dict:
        """Get statistics about router learning."""
        if not self._prediction_history:
            return {"predictions": 0}

        precisions = [r["precision"] for r in self._prediction_history]
        recalls = [r["recall"] for r in self._prediction_history]

        return {
            "predictions": len(self._prediction_history),
            "avg_precision": sum(precisions) / len(precisions),
            "avg_recall": sum(recalls) / len(recalls),
            "cooccurrence_pairs": sum(len(v) for v in self._tool_cooccurrence.values()),
        }

    def export_training_data(self) -> list[dict]:
        """
        Export prediction history for RAFT fine-tuning.

        Returns triplets of (query, all_tools, correct_tools) suitable
        for training a selector model.
        """
        training_data = []

        for record in self._prediction_history:
            if record["used"]:  # Only include examples where tools were actually used
                training_data.append({
                    "query": record["query"],
                    "candidates": record["predicted"],
                    "correct": record["used"],
                })

        return training_data


class SOTARouter(AdaptiveRouter):
    """
    SOTA Router with full pipeline integration.
    
    Extends AdaptiveRouter with:
    - RoutingPipeline for retrieve-rerank-select
    - SharedBanditScorer for learned selection
    - ToolBiasStore for per-tool adjustments
    - SQLiteTelemetryStore for event logging
    """
    
    def __init__(
        self,
        config: RouterConfig,
        tool_zoo: ToolZoo,
        bandit_scorer: SharedBanditScorer | None = None,
        bias_store: ToolBiasStore | None = None,
        telemetry_store: SQLiteTelemetryStore | None = None,
    ) -> None:
        super().__init__(config, tool_zoo)
        
        # SOTA components
        self.bandit_scorer = bandit_scorer
        self.bias_store = bias_store
        self.telemetry_store = telemetry_store
        
        # Lazy-initialize pipeline
        self._pipeline: RoutingPipeline | None = None
        
        # Track last routing for feedback
        self._last_routing_event_id: Any = None
    
    def _get_pipeline(self) -> RoutingPipeline:
        """Lazy-init the routing pipeline."""
        if self._pipeline is None:
            from ucp.routing_pipeline import RoutingPipeline, SlateConfig
            
            slate_config = SlateConfig(
                max_tools=self.config.max_tools,
                min_tools=self.config.min_tools,
                max_context_tokens=getattr(self.config, 'max_context_tokens', 8000),
                max_per_server=getattr(self.config, 'max_per_server', 3),
            )
            
            self._pipeline = RoutingPipeline(
                tool_zoo=self.tool_zoo,  # type: ignore
                config=self.config,
                slate_config=slate_config,
                use_cross_encoder=getattr(self.config, 'use_cross_encoder', False),
                bandit_scorer=self.bandit_scorer,
                bias_store=self.bias_store,
                exploration_rate=getattr(self.config, 'exploration_rate', 0.1),
                candidate_pool_size=getattr(self.config, 'candidate_pool_size', 50),
            )
        
        return self._pipeline
    
    async def route(
        self,
        session: SessionState,
        current_message: str | None = None,
    ) -> RoutingDecision:
        """
        Route using the SOTA pipeline.
        
        Falls back to baseline routing if no pipeline is available.
        """
        # Check if we should use SOTA or baseline
        if getattr(self.config, 'strategy', 'baseline') != 'sota':
            return await super().route(session, current_message)
        
        # Build query
        context_parts = []
        context_parts.append(session.get_context_for_routing(n_messages=5))
        if current_message:
            context_parts.append(f"user: {current_message}")
        query = "\n".join(filter(None, context_parts))
        
        if not query.strip():
            return RoutingDecision(
                selected_tools=self.config.fallback_tools[:],
                scores={},
                reasoning="No context available, using fallback tools",
                query_used="",
            )
        
        # Run SOTA pipeline
        pipeline = self._get_pipeline()
        result = pipeline.run(
            query=query,
            session=session,
            cooccurrence_data=self._tool_cooccurrence,
            telemetry_store=self.telemetry_store,
            log_query_text=False,  # Privacy default
        )
        
        # Convert to RoutingDecision
        selected_tools = [c.tool.name for c in result.selected]
        scores = {c.tool.name: c.final_score for c in result.selected}
        
        # Ensure minimum tools
        if len(selected_tools) < self.config.min_tools:
            for fallback in self.config.fallback_tools:
                if fallback not in selected_tools:
                    selected_tools.append(fallback)
                    scores[fallback] = 0.1
                if len(selected_tools) >= self.config.min_tools:
                    break
        
        # Build reasoning
        reasoning_parts = [
            "Strategy: SOTA",
            f"Candidates: {len(result.all_candidates)}",
            f"Selected: {len(selected_tools)}",
            f"Tokens: {result.total_tokens}",
            f"Time: {result.selection_time_ms:.1f}ms",
        ]
        if result.exploration_triggered:
            reasoning_parts.append("Exploration: triggered")
        
        decision = RoutingDecision(
            selected_tools=selected_tools,
            scores=scores,
            reasoning=" | ".join(reasoning_parts),
            query_used=query[:500],
        )
        
        logger.info(
            "sota_routing_decision",
            selected_count=len(selected_tools),
            top_tool=selected_tools[0] if selected_tools else None,
            strategy="sota",
            exploration=result.exploration_triggered,
        )
        
        return decision
    
    def record_outcome(
        self,
        tool_name: str,
        success: bool,
        execution_time_ms: float = 0.0,
        schema_tokens: int = 0,
    ) -> None:
        """
        Record a tool call outcome for online learning.
        
        This updates both the bandit scorer and bias store.
        """
        from ucp.telemetry import RewardCalculator
        
        # Calculate reward
        calculator = RewardCalculator()
        reward = calculator.calculate(
            success=success,
            execution_time_ms=execution_time_ms,
            schema_tokens=schema_tokens,
        )
        
        # Log to telemetry
        if self.telemetry_store:
            self.telemetry_store.log_reward(reward)
        
        # Update bandit
        if self.bandit_scorer:
            from ucp.bandit import FeatureExtractor
            
            # We need the original features - approximate from tool stats
            stats = self.telemetry_store.get_tool_stats(tool_name) if self.telemetry_store else {}
            features = FeatureExtractor().extract(
                success_rate=stats.get('rolling_success_rate', 0.5),
                latency_ms=stats.get('avg_latency_ms', 0.0),
            )
            self.bandit_scorer.update(features, reward.total_reward)
        
        # Update bias
        if self.bias_store:
            self.bias_store.update(tool_name, reward.total_reward)
        
        logger.debug(
            "outcome_recorded",
            tool=tool_name,
            success=success,
            reward=reward.total_reward,
        )
    
    def get_sota_stats(self) -> dict[str, Any]:
        """Get statistics from SOTA components."""
        stats = self.get_learning_stats()
        
        if self.bandit_scorer:
            stats["bandit"] = self.bandit_scorer.get_stats()
        
        if self.bias_store:
            stats["bias"] = self.bias_store.get_stats()
        
        if self.telemetry_store:
            stats["telemetry"] = self.telemetry_store.get_metrics_summary()
        
        return stats


def create_router(
    config: RouterConfig,
    tool_zoo: ToolZoo,
    telemetry_store: SQLiteTelemetryStore | None = None,
) -> Router:
    """
    Factory function to create the appropriate router based on config.
    
    Args:
        config: Router configuration
        tool_zoo: Tool zoo for retrieval
        telemetry_store: Optional telemetry store for SOTA mode
    
    Returns:
        Router instance (baseline, adaptive, or SOTA)
    """
    strategy = getattr(config, 'strategy', 'baseline')
    
    if strategy == 'sota':
        # Initialize SOTA components
        from ucp.bandit import SharedBanditScorer, BanditConfig as BanditCfg
        from ucp.online_opt import ToolBiasStore, BiasConfig
        
        bandit_scorer = SharedBanditScorer(BanditCfg(
            exploration_type=getattr(config, 'exploration_type', 'epsilon'),
            epsilon=getattr(config, 'exploration_rate', 0.1),
        ))
        
        bias_store = ToolBiasStore(BiasConfig())
        
        return SOTARouter(
            config=config,
            tool_zoo=tool_zoo,
            bandit_scorer=bandit_scorer,
            bias_store=bias_store,
            telemetry_store=telemetry_store,
        )
    else:
        # Use adaptive router for baseline (still tracks co-occurrence)
        return AdaptiveRouter(config, tool_zoo)

