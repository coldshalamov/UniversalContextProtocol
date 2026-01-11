"""
Bandit - Shared Contextual Bandit for Tool Selection.

Implements a cost-aware shared-model bandit scorer that avoids the
scalability issues of per-tool LinUCB matrices. This module provides:

1. SharedBanditScorer: A shared logistic/linear model with epsilon-greedy
   or Thompson sampling exploration
2. Online updates using partial feedback (tool success/failure + latency)
3. Persistent weight storage in SQLite

Key design decisions:
- Shared model: All tools share feature weights, avoiding O(n*d^2) storage
- Feature-based: Tools are scored based on context features, not identity
- Exploration bounded: Configurable epsilon or Thompson uncertainty
- Cheap updates: Single SGD step per observation
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class BanditConfig:
    """Configuration for the bandit scorer."""
    
    # Model parameters
    feature_dim: int = 7  # Number of input features
    learning_rate: float = 0.01
    l2_regularization: float = 0.001
    
    # Exploration parameters
    exploration_type: str = "epsilon"  # "epsilon" or "thompson"
    epsilon: float = 0.1  # For epsilon-greedy
    thompson_scale: float = 0.1  # Uncertainty scale for Thompson
    
    # Persistence
    persist_every_n_updates: int = 10
    db_path: str = "./data/bandit_weights.db"


class SharedBanditScorer:
    """
    Shared linear/logistic model for tool scoring with exploration.
    
    Features are computed from query-tool similarity, tool statistics,
    and context features. The model learns a shared weight vector that
    maps these features to expected reward.
    """
    
    def __init__(self, config: BanditConfig | None = None) -> None:
        self.config = config or BanditConfig()
        
        # Model weights (shared across all tools)
        self.weights = np.zeros(self.config.feature_dim)
        self.bias = 0.0
        
        # For Thompson sampling: track uncertainty via pseudo-counts
        self.feature_sum_sq = np.ones(self.config.feature_dim)  # Avoid div by zero
        self.update_count = 0
        
        # Persistence
        self._db: sqlite3.Connection | None = None
        self._updates_since_persist = 0
        
        # Initialize from persistence
        self._init_db()
        self._load_weights()
    
    def _init_db(self) -> None:
        """Initialize SQLite for weight persistence."""
        db_path = Path(self.config.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS bandit_weights (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                weights_json TEXT NOT NULL,
                bias REAL NOT NULL,
                feature_sum_sq_json TEXT NOT NULL,
                update_count INTEGER NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        self._db.commit()
    
    def _load_weights(self) -> None:
        """Load weights from persistence."""
        if not self._db:
            return
        
        row = self._db.execute(
            "SELECT * FROM bandit_weights WHERE id = 1"
        ).fetchone()
        
        if row:
            self.weights = np.array(json.loads(row[1]))
            self.bias = row[2]
            self.feature_sum_sq = np.array(json.loads(row[3]))
            self.update_count = row[4]
            logger.info(
                "bandit_weights_loaded",
                update_count=self.update_count,
            )
    
    def _save_weights(self) -> None:
        """Persist weights to database."""
        if not self._db:
            return
        
        self._db.execute(
            """
            INSERT OR REPLACE INTO bandit_weights 
            (id, weights_json, bias, feature_sum_sq_json, update_count, last_updated)
            VALUES (1, ?, ?, ?, ?, ?)
            """,
            (
                json.dumps(self.weights.tolist()),
                self.bias,
                json.dumps(self.feature_sum_sq.tolist()),
                self.update_count,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._db.commit()
        self._updates_since_persist = 0
    
    def score(self, features: np.ndarray) -> float:
        """
        Compute the bandit score for a feature vector.
        
        Returns a score in approximately [0, 1] range.
        """
        # Ensure correct shape
        features = np.atleast_1d(features).flatten()
        if len(features) != self.config.feature_dim:
            logger.warning(
                "feature_dim_mismatch",
                expected=self.config.feature_dim,
                got=len(features),
            )
            features = np.pad(
                features, 
                (0, max(0, self.config.feature_dim - len(features))),
            )[:self.config.feature_dim]
        
        # Linear score
        raw_score = float(np.dot(self.weights, features) + self.bias)
        
        # Sigmoid to get probability-like score
        score = 1 / (1 + np.exp(-raw_score))
        
        return score
    
    def score_with_exploration(self, features: np.ndarray) -> tuple[float, bool]:
        """
        Score with exploration component.
        
        Returns (score, exploration_triggered).
        """
        base_score = self.score(features)
        exploration_triggered = False
        
        if self.config.exploration_type == "epsilon":
            # Epsilon-greedy: with probability epsilon, add random noise
            if np.random.random() < self.config.epsilon:
                exploration_bonus = np.random.uniform(-0.3, 0.3)
                base_score += exploration_bonus
                exploration_triggered = True
        
        elif self.config.exploration_type == "thompson":
            # Thompson sampling: sample from posterior
            features = np.atleast_1d(features).flatten()
            
            # Uncertainty proportional to inverse pseudo-counts
            uncertainty = self.config.thompson_scale * np.sqrt(
                1.0 / (self.feature_sum_sq + 1e-8)
            )
            
            # Sample weights from approximate posterior
            sampled_weights = self.weights + np.random.normal(0, uncertainty)
            sampled_score = float(np.dot(sampled_weights, features) + self.bias)
            base_score = 1 / (1 + np.exp(-sampled_score))
            exploration_triggered = True  # Thompson always explores
        
        return base_score, exploration_triggered
    
    def update(self, features: np.ndarray, reward: float) -> None:
        """
        Update model weights using a single observation.
        
        Uses online SGD with L2 regularization.
        
        Args:
            features: Feature vector for the observation
            reward: Observed reward in [-1, +1]
        """
        features = np.atleast_1d(features).flatten()
        if len(features) != self.config.feature_dim:
            features = np.pad(
                features,
                (0, max(0, self.config.feature_dim - len(features))),
            )[:self.config.feature_dim]
        
        # Current prediction
        raw_score = float(np.dot(self.weights, features) + self.bias)
        predicted = 1 / (1 + np.exp(-raw_score))
        
        # Target: scale reward from [-1, 1] to [0, 1]
        target = (reward + 1) / 2
        
        # Gradient for logistic loss
        error = predicted - target
        
        # SGD update with L2 regularization
        gradient = error * features + self.config.l2_regularization * self.weights
        self.weights -= self.config.learning_rate * gradient
        self.bias -= self.config.learning_rate * error
        
        # Update uncertainty estimates for Thompson
        self.feature_sum_sq += features ** 2
        self.update_count += 1
        
        # Periodic persistence
        self._updates_since_persist += 1
        if self._updates_since_persist >= self.config.persist_every_n_updates:
            self._save_weights()
        
        logger.debug(
            "bandit_update",
            reward=reward,
            predicted=predicted,
            error=error,
        )
    
    def batch_update(
        self, 
        features_list: list[np.ndarray], 
        rewards: list[float],
    ) -> None:
        """Update with a batch of observations."""
        for features, reward in zip(features_list, rewards):
            self.update(features, reward)
    
    def get_stats(self) -> dict[str, Any]:
        """Get model statistics."""
        return {
            "update_count": self.update_count,
            "weight_mean": float(np.mean(self.weights)),
            "weight_std": float(np.std(self.weights)),
            "bias": self.bias,
            "feature_dim": self.config.feature_dim,
            "exploration_type": self.config.exploration_type,
        }
    
    def reset(self) -> None:
        """Reset model to initial state."""
        self.weights = np.zeros(self.config.feature_dim)
        self.bias = 0.0
        self.feature_sum_sq = np.ones(self.config.feature_dim)
        self.update_count = 0
        self._save_weights()
        logger.info("bandit_reset")
    
    def close(self) -> None:
        """Close database connection."""
        if self._db:
            self._save_weights()  # Final persist
            self._db.close()
            self._db = None


class FeatureExtractor:
    """
    Extracts feature vectors from routing candidates.
    
    Standard feature set:
    - semantic_score: Base embedding similarity
    - keyword_score: Keyword match score
    - domain_match: Binary domain match
    - cooccurrence_boost: Co-occurrence with recent tools
    - success_rate: Rolling success rate
    - latency_score: Normalized latency (inverted)
    - schema_size: Normalized schema token count
    """
    
    FEATURE_NAMES = [
        "semantic_score",
        "keyword_score",
        "domain_match",
        "cooccurrence_boost",
        "success_rate",
        "latency_score",
        "schema_size",
    ]
    
    def __init__(
        self,
        latency_cap_ms: float = 5000,
        schema_cap_tokens: int = 1000,
    ) -> None:
        self.latency_cap = latency_cap_ms
        self.schema_cap = schema_cap_tokens
    
    def extract(
        self,
        semantic_score: float = 0.0,
        keyword_score: float = 0.0,
        domain_match: bool = False,
        cooccurrence_boost: float = 0.0,
        success_rate: float = 0.5,
        latency_ms: float = 0.0,
        schema_tokens: int = 0,
    ) -> np.ndarray:
        """Extract normalized feature vector."""
        return np.array([
            max(0, min(1, semantic_score)),  # Clamp to [0, 1]
            max(0, min(1, keyword_score)),
            1.0 if domain_match else 0.0,
            max(0, min(1, cooccurrence_boost)),
            max(0, min(1, success_rate)),
            max(0, min(1, 1.0 - (latency_ms / self.latency_cap))),  # Invert: lower is better
            max(0, min(1, 1.0 - (schema_tokens / self.schema_cap))),  # Invert: smaller is better
        ])
    
    @classmethod
    def from_candidate(cls, candidate: Any) -> np.ndarray:
        """Extract features from a Candidate object."""
        extractor = cls()
        return extractor.extract(
            semantic_score=getattr(candidate, 'semantic_score', 0.0),
            keyword_score=getattr(candidate, 'keyword_score', 0.0),
            domain_match=getattr(candidate, 'domain_match', False),
            cooccurrence_boost=getattr(candidate, 'cooccurrence_boost', 0.0),
            success_rate=getattr(candidate, 'rolling_success_rate', 0.5),
            latency_ms=getattr(candidate, 'rolling_latency_ms', 0.0),
            schema_tokens=getattr(candidate, 'schema_tokens', 0),
        )


# Convenience functions

def create_bandit(
    feature_dim: int = 7,
    exploration_type: str = "epsilon",
    epsilon: float = 0.1,
    db_path: str = "./data/bandit_weights.db",
) -> SharedBanditScorer:
    """Create a bandit scorer with common configuration."""
    config = BanditConfig(
        feature_dim=feature_dim,
        exploration_type=exploration_type,
        epsilon=epsilon,
        db_path=db_path,
    )
    return SharedBanditScorer(config)
