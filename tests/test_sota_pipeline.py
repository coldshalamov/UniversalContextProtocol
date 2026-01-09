"""Tests for the SOTA pipeline components."""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from ucp.telemetry import (
    SQLiteTelemetryStore,
    RoutingEvent,
    ToolCallEvent,
    RewardSignal,
    RewardCalculator,
    CandidateInfo,
    hash_query,
)
from ucp.bandit import (
    SharedBanditScorer,
    BanditConfig,
    FeatureExtractor,
)
from ucp.online_opt import (
    ToolBiasStore,
    BiasConfig,
    EmbeddingAdjuster,
)


class TestTelemetry:
    """Tests for the telemetry system."""
    
    @pytest.fixture
    def temp_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "telemetry.db"
    
    @pytest.fixture
    def store(self, temp_db):
        store = SQLiteTelemetryStore(str(temp_db))
        yield store
        store.close()
    
    def test_log_routing_event(self, store):
        """Test logging a routing event."""
        event = RoutingEvent(
            session_id=uuid4(),
            query_hash=hash_query("test query"),
            candidates=[
                CandidateInfo(tool_name="tool1", base_score=0.8),
                CandidateInfo(tool_name="tool2", base_score=0.6),
            ],
            selected_tools=["tool1"],
            total_candidates=2,
            context_tokens_used=100,
            max_context_tokens=8000,
            selection_time_ms=10.5,
            strategy="sota",
        )
        
        store.log_routing_event(event)
        
        # Retrieve and verify
        events = store.get_routing_events(limit=1)
        assert len(events) == 1
        assert events[0].query_hash == event.query_hash
        assert len(events[0].candidates) == 2
        assert events[0].selected_tools == ["tool1"]
    
    def test_log_tool_call(self, store):
        """Test logging a tool call event."""
        event = ToolCallEvent(
            session_id=uuid4(),
            tool_name="test_tool",
            success=True,
            execution_time_ms=50.0,
            was_selected=True,
            selection_rank=1,
        )
        
        store.log_tool_call(event)
        
        # Check stats were updated
        stats = store.get_tool_stats("test_tool")
        assert stats["total_calls"] == 1
        assert stats["success_count"] == 1
    
    def test_log_reward(self, store):
        """Test logging a reward signal."""
        reward = RewardSignal(
            tool_name="test_tool",
            success_reward=1.0,
            latency_penalty=-0.1,
            context_cost_penalty=-0.05,
            total_reward=0.85,
        )
        
        store.log_reward(reward)
        
        rewards = store.get_recent_rewards(tool_name="test_tool", limit=1)
        assert len(rewards) == 1
        assert rewards[0].total_reward == 0.85
    
    def test_reward_calculator_success(self):
        """Test reward calculation for successful call."""
        calc = RewardCalculator()
        reward = calc.calculate(
            success=True,
            execution_time_ms=100,
            schema_tokens=50,
        )
        
        assert reward.success_reward == 1.0
        assert reward.latency_penalty < 0
        assert reward.context_cost_penalty < 0
        assert -1 <= reward.total_reward <= 1
    
    def test_reward_calculator_failure(self):
        """Test reward calculation for failed call."""
        calc = RewardCalculator()
        reward = calc.calculate(
            success=False,
            execution_time_ms=100,
            schema_tokens=50,
        )
        
        assert reward.success_reward == -1.0
        assert reward.total_reward < 0
    
    def test_query_hash(self):
        """Test query hashing is consistent."""
        query = "test query for hashing"
        hash1 = hash_query(query)
        hash2 = hash_query(query)
        
        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated SHA256
    
    def test_metrics_summary(self, store):
        """Test metrics summary generation."""
        # Add some events
        for i in range(3):
            event = RoutingEvent(
                query_hash=f"hash{i}",
                selected_tools=[f"tool{i}"],
                total_candidates=10,
                context_tokens_used=100,
                selection_time_ms=10.0,
                strategy="sota",
            )
            store.log_routing_event(event)
            
            call = ToolCallEvent(
                tool_name=f"tool{i}",
                success=(i % 2 == 0),
                execution_time_ms=50.0,
            )
            store.log_tool_call(call)
        
        summary = store.get_metrics_summary()
        
        assert summary["routing_events"] == 3
        assert summary["tool_calls"] == 3
        assert 0 <= summary["overall_success_rate"] <= 1


class TestBandit:
    """Tests for the shared bandit scorer."""
    
    @pytest.fixture
    def temp_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "bandit.db"
    
    @pytest.fixture
    def bandit(self, temp_db):
        config = BanditConfig(db_path=str(temp_db))
        scorer = SharedBanditScorer(config)
        yield scorer
        scorer.close()
    
    def test_score(self, bandit):
        """Test basic scoring."""
        features = np.array([0.5, 0.3, 1.0, 0.1, 0.8, 0.5, 0.6])
        score = bandit.score(features)
        
        # With zero weights and zero bias, sigmoid(0) = 0.5
        assert 0 <= score <= 1
    
    def test_score_with_exploration(self, bandit):
        """Test scoring with exploration."""
        features = np.array([0.5, 0.3, 1.0, 0.1, 0.8, 0.5, 0.6])
        score, explored = bandit.score_with_exploration(features)
        
        assert 0 <= score <= 1
        # Exploration may or may not trigger
    
    def test_update(self, bandit):
        """Test weight updates."""
        features = np.array([0.5, 0.3, 1.0, 0.1, 0.8, 0.5, 0.6])
        
        initial_score = bandit.score(features)
        
        # Update with positive reward
        bandit.update(features, 1.0)
        updated_score = bandit.score(features)
        
        # Score should increase after positive reward
        assert updated_score > initial_score
        assert bandit.update_count == 1
    
    def test_update_negative_reward(self, bandit):
        """Test weight updates with negative reward."""
        features = np.array([0.5, 0.3, 1.0, 0.1, 0.8, 0.5, 0.6])
        
        # First, train with positive
        for _ in range(5):
            bandit.update(features, 1.0)
        
        score_after_positive = bandit.score(features)
        
        # Then train with negative
        for _ in range(5):
            bandit.update(features, -1.0)
        
        score_after_negative = bandit.score(features)
        
        # Score should decrease after negative rewards
        assert score_after_negative < score_after_positive
    
    def test_persistence(self, temp_db):
        """Test weight persistence across restarts."""
        config = BanditConfig(db_path=str(temp_db), persist_every_n_updates=1)
        
        # Train first instance
        scorer1 = SharedBanditScorer(config)
        features = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
        for _ in range(5):
            scorer1.update(features, 1.0)
        score1 = scorer1.score(features)
        scorer1.close()
        
        # Load second instance
        scorer2 = SharedBanditScorer(config)
        score2 = scorer2.score(features)
        scorer2.close()
        
        # Scores should be similar (small floating point differences ok)
        assert abs(score1 - score2) < 0.01
    
    def test_feature_extractor(self):
        """Test feature extraction."""
        extractor = FeatureExtractor()
        features = extractor.extract(
            semantic_score=0.8,
            keyword_score=0.5,
            domain_match=True,
            cooccurrence_boost=0.1,
            success_rate=0.9,
            latency_ms=100,
            schema_tokens=200,
        )
        
        assert len(features) == 7
        assert features[0] == 0.8  # semantic_score
        assert features[2] == 1.0  # domain_match
        assert 0 <= features[5] <= 1  # latency_score (inverted)


class TestBiasLearning:
    """Tests for per-tool bias learning."""
    
    @pytest.fixture
    def temp_db(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir) / "biases.db"
    
    @pytest.fixture
    def bias_store(self, temp_db):
        config = BiasConfig(db_path=str(temp_db))
        store = ToolBiasStore(config)
        yield store
        store.close()
    
    def test_get_initial_bias(self, bias_store):
        """Test getting initial bias for new tool."""
        bias = bias_store.get_bias("new_tool")
        assert bias == 0.0  # Default initial bias
    
    def test_update_positive(self, bias_store):
        """Test bias update with positive reward."""
        tool = "test_tool"
        
        bias_store.update(tool, 1.0)
        bias = bias_store.get_bias(tool)
        
        assert bias > 0  # Positive reward should increase bias
    
    def test_update_negative(self, bias_store):
        """Test bias update with negative reward."""
        tool = "test_tool"
        
        bias_store.update(tool, -1.0)
        bias = bias_store.get_bias(tool)
        
        assert bias < 0  # Negative reward should decrease bias
    
    def test_bias_clamping(self, bias_store):
        """Test that bias is clamped to max value."""
        tool = "test_tool"
        
        # Many positive updates
        for _ in range(100):
            bias_store.update(tool, 1.0)
        
        bias = bias_store.get_bias(tool)
        assert bias <= bias_store.config.max_bias
    
    def test_persistence(self, temp_db):
        """Test bias persistence across restarts."""
        config = BiasConfig(db_path=str(temp_db), persist_every_n_updates=1)
        
        # Train first instance
        store1 = ToolBiasStore(config)
        tool = "persistent_tool"
        for _ in range(5):
            store1.update(tool, 1.0)
        bias1 = store1.get_bias(tool)
        store1.close()
        
        # Load second instance
        store2 = ToolBiasStore(config)
        bias2 = store2.get_bias(tool)
        store2.close()
        
        assert abs(bias1 - bias2) < 0.001
    
    def test_get_top_biased_tools(self, bias_store):
        """Test getting top biased tools."""
        # Create some biased tools
        bias_store.update("good_tool", 1.0)
        bias_store.update("good_tool", 1.0)
        bias_store.update("bad_tool", -1.0)
        bias_store.update("bad_tool", -1.0)
        
        top_positive = bias_store.get_top_biased_tools(5, positive=True)
        top_negative = bias_store.get_top_biased_tools(5, positive=False)
        
        assert len(top_positive) >= 1
        assert len(top_negative) >= 1
        assert top_positive[0][0] == "good_tool"
        assert top_negative[0][0] == "bad_tool"
    
    def test_embedding_adjuster(self, bias_store):
        """Test similarity adjustment with bias."""
        bias_store.update("test_tool", 1.0)
        
        adjuster = EmbeddingAdjuster(bias_store)
        
        base_similarity = 0.5
        adjusted = adjuster.adjust_similarity("test_tool", base_similarity)
        
        # Should be higher than base due to positive bias
        assert adjusted > base_similarity
    
    def test_stats(self, bias_store):
        """Test statistics collection."""
        bias_store.update("tool1", 1.0)
        bias_store.update("tool2", -0.5)
        
        stats = bias_store.get_stats()
        
        assert stats["tool_count"] == 2
        assert stats["total_updates"] == 2


class TestBudgetSelection:
    """Tests for budgeted slate selection."""
    
    def test_respects_max_tools(self):
        """Test that selection respects max_tools limit."""
        from ucp.routing_pipeline import SlateConfig, SlateSelector, Candidate
        from ucp.models import ToolSchema
        
        config = SlateConfig(max_tools=3, max_context_tokens=10000)
        selector = SlateSelector(config)
        
        # Create more candidates than max
        candidates = []
        for i in range(10):
            tool = ToolSchema(
                name=f"tool{i}",
                display_name=f"Tool {i}",
                description=f"Description {i}",
                server_name="server",
            )
            candidate = Candidate(
                tool=tool,
                semantic_score=1.0 - i * 0.1,
                schema_tokens=100,
            )
            candidate.final_score = candidate.semantic_score
            candidates.append(candidate)
        
        result = selector.select(candidates)
        
        assert len(result.selected) <= 3
    
    def test_respects_token_budget(self):
        """Test that selection respects token budget."""
        from ucp.routing_pipeline import SlateConfig, SlateSelector, Candidate
        from ucp.models import ToolSchema
        
        config = SlateConfig(max_tools=10, max_context_tokens=500)
        selector = SlateSelector(config)
        
        # Create candidates with large schemas
        candidates = []
        for i in range(5):
            tool = ToolSchema(
                name=f"tool{i}",
                display_name=f"Tool {i}",
                description=f"Description {i}",
                server_name="server",
            )
            candidate = Candidate(
                tool=tool,
                semantic_score=0.9,
                schema_tokens=200,  # Each tool uses 200 tokens
            )
            candidate.final_score = candidate.semantic_score
            candidates.append(candidate)
        
        result = selector.select(candidates)
        
        # Should only fit 2 tools (500 / 200 = 2.5)
        assert result.total_tokens <= 500
    
    def test_diversity_constraint(self):
        """Test that diversity limits tools per server."""
        from ucp.routing_pipeline import SlateConfig, SlateSelector, Candidate
        from ucp.models import ToolSchema
        
        config = SlateConfig(max_tools=10, max_per_server=2)
        selector = SlateSelector(config)
        
        # Create many tools from same server
        candidates = []
        for i in range(5):
            tool = ToolSchema(
                name=f"tool{i}",
                display_name=f"Tool {i}",
                description=f"Description {i}",
                server_name="same_server",
            )
            candidate = Candidate(
                tool=tool,
                semantic_score=0.9 - i * 0.01,
                schema_tokens=50,
            )
            candidate.final_score = candidate.semantic_score
            candidates.append(candidate)
        
        result = selector.select(candidates)
        
        # Should only select max_per_server from same server
        server_counts = {}
        for c in result.selected:
            server = c.tool.server_name
            server_counts[server] = server_counts.get(server, 0) + 1
        
        for count in server_counts.values():
            assert count <= 2
