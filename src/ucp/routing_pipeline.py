"""
Routing Pipeline - SOTA Tool Selection Architecture.

Implements the "Retrieve → Rerank → Budgeted Slate → Online Learning" pipeline:

1. Candidate Retrieval (fast): Hybrid search over tool zoo
2. Reranking (quality): Cross-encoder or lightweight reranker
3. Budgeted Slate Selection: Select k tools under token budget
4. Online Learning: Integrate bandit scores and bias adjustments

This module contains the core abstractions and implementations for
each pipeline stage.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np
import structlog

from ucp.config import RouterConfig
from ucp.models import SessionState, ToolSchema
from ucp.telemetry import CandidateInfo, RoutingEvent, hash_query

if TYPE_CHECKING:
    from ucp.tool_zoo import HybridToolZoo
    from ucp.bandit import SharedBanditScorer
    from ucp.online_opt import ToolBiasStore

logger = structlog.get_logger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class Candidate:
    """A candidate tool with scoring features."""
    
    tool: ToolSchema
    
    # Base scores from retrieval
    semantic_score: float = 0.0
    keyword_score: float = 0.0
    
    # Computed features
    domain_match: bool = False
    tag_match: bool = False
    recency_score: float = 0.0
    cooccurrence_boost: float = 0.0
    
    # Learned adjustments
    bandit_score: float = 0.0
    bias_adjustment: float = 0.0
    rolling_success_rate: float = 0.5
    rolling_latency_ms: float = 0.0
    
    # Budget features
    schema_tokens: int = 0
    
    # Final score after all adjustments
    final_score: float = 0.0
    
    def to_candidate_info(self) -> CandidateInfo:
        """Convert to telemetry-compatible format."""
        return CandidateInfo(
            tool_name=self.tool.name,
            base_score=self.semantic_score,
            keyword_score=self.keyword_score,
            domain_match=self.domain_match,
            cooccurrence_boost=self.cooccurrence_boost,
            bandit_score=self.bandit_score,
            bias_adjustment=self.bias_adjustment,
            final_score=self.final_score,
            schema_tokens=self.schema_tokens,
        )


@dataclass
class SlateConfig:
    """Configuration for slate selection."""
    
    max_tools: int = 10
    max_context_tokens: int = 8000  # Approximate token budget for schemas
    min_tools: int = 1
    diversity_penalty: float = 0.1  # Penalize multiple tools from same server
    max_per_server: int = 3


@dataclass
class SelectionResult:
    """Result of the selection pipeline."""
    
    selected: list[Candidate] = field(default_factory=list)
    all_candidates: list[Candidate] = field(default_factory=list)
    total_tokens: int = 0
    exploration_triggered: bool = False
    selection_time_ms: float = 0.0
    strategy: str = "baseline"


# =============================================================================
# Candidate Retrieval Stage
# =============================================================================

class CandidateRetriever:
    """
    Stage 1: Fast candidate retrieval from tool zoo.
    
    Expands the candidate pool beyond what might be selected to give
    the reranker more options.
    """
    
    def __init__(
        self,
        tool_zoo: HybridToolZoo,
        candidate_pool_size: int = 50,
    ) -> None:
        self.tool_zoo = tool_zoo
        self.candidate_pool_size = candidate_pool_size
    
    def retrieve(
        self,
        query: str,
        session: SessionState,
        filter_domain: str | None = None,
    ) -> list[Candidate]:
        """
        Retrieve candidates from the tool zoo.
        
        Uses hybrid search (semantic + keyword) to maximize recall.
        """
        # Get hybrid search results with expanded pool
        if hasattr(self.tool_zoo, 'hybrid_search'):
            raw_results = self.tool_zoo.hybrid_search(
                query, 
                top_k=self.candidate_pool_size,
            )
        else:
            raw_results = self.tool_zoo.search(
                query,
                top_k=self.candidate_pool_size,
                min_score=0.0,  # Get all candidates
            )
        
        # Also get keyword results for diversity
        keyword_results: dict[str, float] = {}
        if hasattr(self.tool_zoo, 'keyword_search'):
            kw_results = self.tool_zoo.keyword_search(query, top_k=self.candidate_pool_size)
            keyword_results = {t.name: score for t, score in kw_results}
        
        # Build candidates
        candidates = []
        for tool, semantic_score in raw_results:
            candidate = Candidate(
                tool=tool,
                semantic_score=semantic_score,
                keyword_score=keyword_results.get(tool.name, 0.0),
                schema_tokens=self._estimate_schema_tokens(tool),
            )
            candidates.append(candidate)
        
        logger.debug(
            "candidates_retrieved",
            count=len(candidates),
            query_length=len(query),
        )
        
        return candidates
    
    def _estimate_schema_tokens(self, tool: ToolSchema) -> int:
        """
        Estimate the token footprint of a tool schema.
        
        Uses a simple heuristic: ~4 chars per token for JSON.
        """
        import json
        schema_str = json.dumps({
            "name": tool.name,
            "description": tool.description,
            "inputSchema": tool.input_schema,
        })
        return len(schema_str) // 4


# =============================================================================
# Reranking Stage
# =============================================================================

class Reranker(ABC):
    """Abstract base for rerankers."""
    
    @abstractmethod
    def rerank(
        self,
        query: str,
        candidates: list[Candidate],
    ) -> list[Candidate]:
        """Rerank candidates and return sorted list."""
        pass


class LightweightReranker(Reranker):
    """
    Fast heuristic reranker using lexical features and boosts.
    
    This is the default reranker that doesn't require additional models.
    """
    
    def __init__(
        self,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.2,
        domain_boost: float = 0.1,
        recency_weight: float = 0.1,
    ) -> None:
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.domain_boost = domain_boost
        self.recency_weight = recency_weight
    
    def rerank(
        self,
        query: str,
        candidates: list[Candidate],
    ) -> list[Candidate]:
        """Rerank using weighted combination of features."""
        for c in candidates:
            # Base score
            score = (
                self.semantic_weight * c.semantic_score +
                self.keyword_weight * c.keyword_score
            )
            
            # Domain/tag boost
            if c.domain_match or c.tag_match:
                score += self.domain_boost
            
            # Recency boost
            score += self.recency_weight * c.recency_score
            
            # Cooccurrence boost
            score += c.cooccurrence_boost * 0.1
            
            c.final_score = score
        
        # Sort by final score
        candidates.sort(key=lambda c: c.final_score, reverse=True)
        return candidates


class CrossEncoderReranker(Reranker):
    """
    High-quality reranker using sentence-transformers CrossEncoder.
    
    Optional - only used if sentence-transformers is available and
    cross-encoder mode is enabled in config.
    """
    
    _model_cache: dict[str, Any] = {}
    
    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        cache_ttl_seconds: int = 300,
    ) -> None:
        self.model_name = model_name
        self.cache_ttl = cache_ttl_seconds
        self._cross_encoder: Any = None
        self._score_cache: dict[str, tuple[float, float]] = {}  # (score, timestamp)
    
    @property
    def cross_encoder(self) -> Any:
        """Lazy load the cross encoder model."""
        if self._cross_encoder is None:
            try:
                from sentence_transformers import CrossEncoder
                logger.info("loading_cross_encoder", model=self.model_name)
                self._cross_encoder = CrossEncoder(self.model_name)
            except ImportError:
                logger.warning("cross_encoder_not_available")
                self._cross_encoder = None
        return self._cross_encoder
    
    def _cache_key(self, query_hash: str, tool_name: str) -> str:
        return f"{query_hash}:{tool_name}"
    
    def _get_cached_score(self, cache_key: str) -> float | None:
        """Get cached score if not expired."""
        if cache_key in self._score_cache:
            score, timestamp = self._score_cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return score
            del self._score_cache[cache_key]
        return None
    
    def _cache_score(self, cache_key: str, score: float) -> None:
        """Cache a score with current timestamp."""
        self._score_cache[cache_key] = (score, time.time())
        
        # Limit cache size
        if len(self._score_cache) > 10000:
            # Remove oldest entries
            sorted_keys = sorted(
                self._score_cache.keys(),
                key=lambda k: self._score_cache[k][1],
            )
            for k in sorted_keys[:5000]:
                del self._score_cache[k]
    
    def rerank(
        self,
        query: str,
        candidates: list[Candidate],
    ) -> list[Candidate]:
        """Rerank using cross-encoder scores."""
        if not self.cross_encoder or not candidates:
            # Fall back to lightweight reranking
            return LightweightReranker().rerank(query, candidates)
        
        query_hash = hash_query(query)
        
        # Prepare pairs for scoring
        pairs_to_score = []
        cached_scores: dict[str, float] = {}
        
        for c in candidates:
            cache_key = self._cache_key(query_hash, c.tool.name)
            cached = self._get_cached_score(cache_key)
            
            if cached is not None:
                cached_scores[c.tool.name] = cached
            else:
                # Build tool text for cross-encoder
                tool_text = f"{c.tool.display_name}: {c.tool.description}"
                pairs_to_score.append((query, tool_text, c.tool.name))
        
        # Score uncached pairs
        if pairs_to_score:
            texts = [(p[0], p[1]) for p in pairs_to_score]
            scores = self.cross_encoder.predict(texts)
            
            for (_, _, tool_name), score in zip(pairs_to_score, scores):
                cache_key = self._cache_key(query_hash, tool_name)
                self._cache_score(cache_key, float(score))
                cached_scores[tool_name] = float(score)
        
        # Apply scores
        for c in candidates:
            cross_score = cached_scores.get(c.tool.name, 0.0)
            # Combine with existing scores
            c.final_score = 0.5 * cross_score + 0.3 * c.semantic_score + 0.2 * c.keyword_score
        
        candidates.sort(key=lambda c: c.final_score, reverse=True)
        return candidates


def get_reranker(
    use_cross_encoder: bool = False,
    model_name: str | None = None,
) -> Reranker:
    """Factory function for rerankers."""
    if use_cross_encoder:
        try:
            return CrossEncoderReranker(
                model_name=model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2" 
            )
        except ImportError:
            logger.warning("cross_encoder_not_available_falling_back")

    return LightweightReranker()


# =============================================================================
# Budgeted Slate Selection Stage
# =============================================================================

class SlateSelector:
    """
    Stage 3: Select tools under budget constraints.
    
    Implements cost-aware selection with diversity constraints.
    Optionally integrates bandit exploration.
    """
    
    def __init__(
        self,
        config: SlateConfig,
        bandit_scorer: SharedBanditScorer | None = None,
        bias_store: ToolBiasStore | None = None,
        exploration_rate: float = 0.1,
    ) -> None:
        self.config = config
        self.bandit_scorer = bandit_scorer
        self.bias_store = bias_store
        self.exploration_rate = exploration_rate
    
    def select(
        self,
        candidates: list[Candidate],
        enable_exploration: bool = True,
    ) -> SelectionResult:
        """
        Select tools under budget constraints.
        
        Uses a greedy algorithm with diversity penalties.
        """
        if not candidates:
            return SelectionResult()
        
        # Apply bandit scores if available
        if self.bandit_scorer:
            for c in candidates:
                features = self._extract_features(c)
                c.bandit_score = self.bandit_scorer.score(features)
                c.final_score = 0.7 * c.final_score + 0.3 * c.bandit_score
        
        # Apply bias adjustments if available
        if self.bias_store:
            for c in candidates:
                c.bias_adjustment = self.bias_store.get_bias(c.tool.name)
                c.final_score += c.bias_adjustment
        
        # Exploration: with probability epsilon, boost a random candidate
        exploration_triggered = False
        if enable_exploration and np.random.random() < self.exploration_rate:
            exploration_triggered = True
            # Epsilon-greedy on the margin: boost a random non-top candidate
            if len(candidates) > 3:
                explore_idx = np.random.randint(3, min(len(candidates), 10))
                candidates[explore_idx].final_score += 0.5
                logger.debug("exploration_triggered", tool=candidates[explore_idx].tool.name)
        
        # Re-sort after exploration
        candidates.sort(key=lambda c: c.final_score, reverse=True)
        
        # Greedy selection under budget
        selected: list[Candidate] = []
        total_tokens = 0
        server_counts: dict[str, int] = {}
        
        for c in candidates:
            # Check budget constraints
            if len(selected) >= self.config.max_tools:
                break
            if total_tokens + c.schema_tokens > self.config.max_context_tokens:
                continue
            
            # Check diversity constraint
            server = c.tool.server_name
            if server_counts.get(server, 0) >= self.config.max_per_server:
                # Apply diversity penalty instead of hard skip
                c.final_score -= self.config.diversity_penalty
                continue
            
            selected.append(c)
            total_tokens += c.schema_tokens
            server_counts[server] = server_counts.get(server, 0) + 1
        
        # Ensure minimum tools
        if len(selected) < self.config.min_tools and len(candidates) > len(selected):
            for c in candidates:
                if c not in selected:
                    selected.append(c)
                    total_tokens += c.schema_tokens
                    if len(selected) >= self.config.min_tools:
                        break
        
        return SelectionResult(
            selected=selected,
            all_candidates=candidates,
            total_tokens=total_tokens,
            exploration_triggered=exploration_triggered,
        )
    
    def _extract_features(self, candidate: Candidate) -> np.ndarray:
        """Extract feature vector for bandit scoring."""
        return np.array([
            candidate.semantic_score,
            candidate.keyword_score,
            1.0 if candidate.domain_match else 0.0,
            candidate.cooccurrence_boost,
            candidate.rolling_success_rate,
            min(candidate.rolling_latency_ms / 1000, 1.0),  # Normalized latency
            min(candidate.schema_tokens / 500, 1.0),  # Normalized schema size
        ])


# =============================================================================
# Full Pipeline
# =============================================================================

class RoutingPipeline:
    """
    Complete routing pipeline orchestrating all stages.
    
    This is the main entry point for the SOTA tool selection system.
    """
    
    def __init__(
        self,
        tool_zoo: HybridToolZoo,
        config: RouterConfig,
        slate_config: SlateConfig | None = None,
        use_cross_encoder: bool = False,
        bandit_scorer: SharedBanditScorer | None = None,
        bias_store: ToolBiasStore | None = None,
        exploration_rate: float = 0.1,
        candidate_pool_size: int = 50,
    ) -> None:
        self.tool_zoo = tool_zoo
        self.config = config
        self.slate_config = slate_config or SlateConfig(
            max_tools=config.max_tools,
            min_tools=config.min_tools,
        )
        
        # Initialize stages
        self.retriever = CandidateRetriever(tool_zoo, candidate_pool_size)
        self.reranker = get_reranker(use_cross_encoder)
        self.selector = SlateSelector(
            self.slate_config,
            bandit_scorer=bandit_scorer,
            bias_store=bias_store,
            exploration_rate=exploration_rate,
        )
        
        # Domain detection keywords
        self._domain_keywords = self._build_domain_keywords()
    
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
    
    def detect_domains(self, context: str) -> list[str]:
        """Detect domains from context."""
        context_lower = context.lower()
        detected = []
        
        for domain, keywords in self._domain_keywords.items():
            for keyword in keywords:
                if keyword in context_lower:
                    detected.append(domain)
                    break
        
        return detected
    
    def run(
        self,
        query: str,
        session: SessionState,
        cooccurrence_data: dict[str, dict[str, int]] | None = None,
        telemetry_store: Any | None = None,
        log_query_text: bool = False,
    ) -> SelectionResult:
        """
        Run the full routing pipeline.
        
        Args:
            query: The routing query (context + current message)
            session: Current session state
            cooccurrence_data: Tool co-occurrence counts
            telemetry_store: Optional telemetry store for logging
            log_query_text: Whether to log raw query text (privacy-sensitive)
        
        Returns:
            SelectionResult with selected tools and metadata
        """
        start_time = time.time()
        
        # Stage 1: Retrieve candidates
        candidates = self.retriever.retrieve(query, session)
        
        if not candidates:
            logger.warning("no_candidates_retrieved")
            return SelectionResult(strategy="baseline")
        
        # Enrich candidates with session/context features
        domains = self.detect_domains(query)
        self._enrich_candidates(candidates, session, domains, cooccurrence_data)
        
        # Stage 2: Rerank
        candidates = self.reranker.rerank(query, candidates)
        
        # Stage 3: Select slate
        result = self.selector.select(candidates)
        result.strategy = "sota"
        result.selection_time_ms = (time.time() - start_time) * 1000
        
        # Log telemetry
        if telemetry_store:
            event = RoutingEvent(
                session_id=session.session_id,
                query_hash=hash_query(query),
                query_text=query if log_query_text else None,
                candidates=[c.to_candidate_info() for c in result.all_candidates[:20]],
                selected_tools=[c.tool.name for c in result.selected],
                total_candidates=len(result.all_candidates),
                context_tokens_used=result.total_tokens,
                max_context_tokens=self.slate_config.max_context_tokens,
                selection_time_ms=result.selection_time_ms,
                strategy=result.strategy,
                exploration_triggered=result.exploration_triggered,
            )
            telemetry_store.log_routing_event(event)
        
        logger.info(
            "pipeline_complete",
            selected=len(result.selected),
            candidates=len(result.all_candidates),
            tokens=result.total_tokens,
            time_ms=result.selection_time_ms,
            exploration=result.exploration_triggered,
        )
        
        return result
    
    def _enrich_candidates(
        self,
        candidates: list[Candidate],
        session: SessionState,
        domains: list[str],
        cooccurrence_data: dict[str, dict[str, int]] | None,
    ) -> None:
        """Add session and context features to candidates."""
        recently_used = list(session.tool_usage.keys())[-5:] if session.tool_usage else []
        
        for c in candidates:
            # Domain/tag matching
            if c.tool.domain and c.tool.domain in domains:
                c.domain_match = True
            
            for tag in c.tool.tags:
                if tag.lower() in [d.lower() for d in domains]:
                    c.tag_match = True
                    break
            
            # Recency score
            if c.tool.name in session.tool_usage:
                usage_count = session.tool_usage[c.tool.name]
                c.recency_score = min(usage_count * 0.02, 0.1)
            
            # Co-occurrence boost
            if cooccurrence_data and recently_used:
                for recent_tool in recently_used:
                    if recent_tool in cooccurrence_data:
                        cooccur = cooccurrence_data[recent_tool]
                        if c.tool.name in cooccur:
                            c.cooccurrence_boost += cooccur[c.tool.name] * 0.01
                c.cooccurrence_boost = min(c.cooccurrence_boost, 0.2)  # Cap
