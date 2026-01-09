"""
Online Embedding Optimization - Per-Tool Bias and Delta Updates.

Implements lightweight online learning for tool embeddings:

1. Per-tool scalar bias: Adjusts similarity scores based on feedback
2. Delta vectors (optional): Small adjustment vectors for embeddings
3. Persistent storage in SQLite that integrates with ToolZoo

Key design decisions:
- Start simple with scalar bias (1 float per tool)
- Delta vectors are optional and can be enabled for higher capacity
- Updates are tied to reward signals from telemetry
- Decay mechanism prevents overfitting to recent observations
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
class BiasConfig:
    """Configuration for tool bias learning."""
    
    # Bias parameters
    initial_bias: float = 0.0
    learning_rate: float = 0.05
    decay_rate: float = 0.001  # Slow decay toward zero
    max_bias: float = 0.5  # Clamp bias magnitude
    
    # Delta vector parameters (optional)
    enable_delta_vectors: bool = False
    embedding_dim: int = 384  # Dimension for MiniLM
    delta_learning_rate: float = 0.01
    delta_l2_reg: float = 0.01
    
    # Persistence
    db_path: str = "./data/tool_biases.db"
    persist_every_n_updates: int = 5


class ToolBiasStore:
    """
    Per-tool bias storage and update mechanism.
    
    Each tool has a scalar bias that adjusts its similarity score:
    adjusted_score = base_score + bias
    
    Bias is updated based on tool call outcomes:
    - Success: move bias toward +max_bias
    - Failure: move bias toward -max_bias
    """
    
    def __init__(self, config: BiasConfig | None = None) -> None:
        self.config = config or BiasConfig()
        
        # In-memory bias cache
        self._biases: dict[str, float] = {}
        
        # Delta vectors (optional)
        self._deltas: dict[str, np.ndarray] = {}
        
        # Update tracking
        self._update_counts: dict[str, int] = {}
        self._updates_since_persist = 0
        
        # Database
        self._db: sqlite3.Connection | None = None
        self._init_db()
        self._load_all()
    
    def _init_db(self) -> None:
        """Initialize SQLite database."""
        db_path = Path(self.config.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._db = sqlite3.connect(str(db_path), check_same_thread=False)
        self._db.execute("""
            CREATE TABLE IF NOT EXISTS tool_biases (
                tool_name TEXT PRIMARY KEY,
                bias REAL NOT NULL,
                delta_vector_json TEXT,
                update_count INTEGER NOT NULL,
                total_reward REAL NOT NULL,
                last_updated TEXT NOT NULL
            )
        """)
        self._db.commit()
        logger.info("bias_store_initialized", path=str(db_path))
    
    def _load_all(self) -> None:
        """Load all biases from database."""
        if not self._db:
            return
        
        rows = self._db.execute("SELECT * FROM tool_biases").fetchall()
        
        for row in rows:
            tool_name = row[0]
            self._biases[tool_name] = row[1]
            self._update_counts[tool_name] = row[3]
            
            if row[2] and self.config.enable_delta_vectors:
                self._deltas[tool_name] = np.array(json.loads(row[2]))
        
        logger.info("biases_loaded", count=len(self._biases))
    
    def get_bias(self, tool_name: str) -> float:
        """Get the current bias for a tool."""
        if tool_name not in self._biases:
            self._biases[tool_name] = self.config.initial_bias
            self._update_counts[tool_name] = 0
        return self._biases[tool_name]
    
    def get_delta(self, tool_name: str) -> np.ndarray | None:
        """Get the delta vector for a tool (if enabled)."""
        if not self.config.enable_delta_vectors:
            return None
        return self._deltas.get(tool_name)
    
    def update(
        self,
        tool_name: str,
        reward: float,
        query_embedding: np.ndarray | None = None,
    ) -> None:
        """
        Update bias (and optionally delta) based on reward.
        
        Args:
            tool_name: Name of the tool
            reward: Reward signal in [-1, +1]
            query_embedding: Optional query embedding for delta updates
        """
        # Initialize if needed
        if tool_name not in self._biases:
            self._biases[tool_name] = self.config.initial_bias
            self._update_counts[tool_name] = 0
        
        current_bias = self._biases[tool_name]
        
        # Update bias toward reward direction
        # Positive reward -> increase bias (tool is better than expected)
        # Negative reward -> decrease bias (tool is worse than expected)
        target = reward * self.config.max_bias
        new_bias = current_bias + self.config.learning_rate * (target - current_bias)
        
        # Apply decay toward zero (regularization)
        new_bias *= (1 - self.config.decay_rate)
        
        # Clamp
        new_bias = max(-self.config.max_bias, min(self.config.max_bias, new_bias))
        
        self._biases[tool_name] = new_bias
        self._update_counts[tool_name] += 1
        
        # Update delta vector if enabled
        if self.config.enable_delta_vectors and query_embedding is not None:
            self._update_delta(tool_name, reward, query_embedding)
        
        # Periodic persistence
        self._updates_since_persist += 1
        if self._updates_since_persist >= self.config.persist_every_n_updates:
            self._persist(tool_name)
        
        logger.debug(
            "bias_updated",
            tool=tool_name,
            old_bias=current_bias,
            new_bias=new_bias,
            reward=reward,
        )
    
    def _update_delta(
        self,
        tool_name: str,
        reward: float,
        query_embedding: np.ndarray,
    ) -> None:
        """Update the delta vector for a tool."""
        # Initialize delta if needed
        if tool_name not in self._deltas:
            self._deltas[tool_name] = np.zeros(self.config.embedding_dim)
        
        delta = self._deltas[tool_name]
        query_embedding = query_embedding.flatten()
        
        # Ensure dimensions match
        if len(query_embedding) != self.config.embedding_dim:
            logger.warning(
                "embedding_dim_mismatch",
                expected=self.config.embedding_dim,
                got=len(query_embedding),
            )
            return
        
        # Gradient: move delta toward query if positive reward, away if negative
        # This effectively adjusts the tool's "virtual embedding"
        gradient = reward * query_embedding
        
        # L2 regularization
        gradient -= self.config.delta_l2_reg * delta
        
        # Update
        self._deltas[tool_name] = delta + self.config.delta_learning_rate * gradient
    
    def _persist(self, tool_name: str) -> None:
        """Persist a single tool's bias to database."""
        if not self._db:
            return
        
        bias = self._biases.get(tool_name, 0.0)
        update_count = self._update_counts.get(tool_name, 0)
        
        delta_json = None
        if tool_name in self._deltas:
            delta_json = json.dumps(self._deltas[tool_name].tolist())
        
        # Calculate total reward (approximation from bias)
        total_reward = bias * update_count  # Rough estimate
        
        self._db.execute(
            """
            INSERT OR REPLACE INTO tool_biases
            (tool_name, bias, delta_vector_json, update_count, total_reward, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                tool_name,
                bias,
                delta_json,
                update_count,
                total_reward,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._db.commit()
        self._updates_since_persist = 0
    
    def persist_all(self) -> None:
        """Persist all biases to database."""
        for tool_name in self._biases:
            self._persist(tool_name)
    
    def get_all_biases(self) -> dict[str, float]:
        """Get all tool biases."""
        return dict(self._biases)
    
    def get_top_biased_tools(self, n: int = 10, positive: bool = True) -> list[tuple[str, float]]:
        """Get tools with highest (or lowest) biases."""
        sorted_biases = sorted(
            self._biases.items(),
            key=lambda x: x[1],
            reverse=positive,
        )
        return sorted_biases[:n]
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics about learned biases."""
        if not self._biases:
            return {"tool_count": 0}
        
        biases = list(self._biases.values())
        return {
            "tool_count": len(self._biases),
            "mean_bias": float(np.mean(biases)),
            "std_bias": float(np.std(biases)),
            "max_bias": float(np.max(biases)),
            "min_bias": float(np.min(biases)),
            "total_updates": sum(self._update_counts.values()),
            "has_deltas": bool(self._deltas),
        }
    
    def reset_tool(self, tool_name: str) -> None:
        """Reset a single tool's bias to initial value."""
        self._biases[tool_name] = self.config.initial_bias
        self._update_counts[tool_name] = 0
        if tool_name in self._deltas:
            del self._deltas[tool_name]
        self._persist(tool_name)
    
    def reset_all(self) -> None:
        """Reset all biases."""
        self._biases.clear()
        self._deltas.clear()
        self._update_counts.clear()
        
        if self._db:
            self._db.execute("DELETE FROM tool_biases")
            self._db.commit()
        
        logger.info("bias_store_reset")
    
    def close(self) -> None:
        """Close database connection."""
        if self._db:
            self.persist_all()
            self._db.close()
            self._db = None


class EmbeddingAdjuster:
    """
    Adjusts tool embeddings using learned biases and deltas.
    
    This integrates with ToolZoo to modify similarity scoring.
    """
    
    def __init__(self, bias_store: ToolBiasStore) -> None:
        self.bias_store = bias_store
    
    def adjust_similarity(
        self,
        tool_name: str,
        base_similarity: float,
        query_embedding: np.ndarray | None = None,
        tool_embedding: np.ndarray | None = None,
    ) -> float:
        """
        Adjust similarity score using learned bias and delta.
        
        Args:
            tool_name: Name of the tool
            base_similarity: Original similarity score
            query_embedding: Query embedding (for delta adjustment)
            tool_embedding: Tool embedding (for delta adjustment)
        
        Returns:
            Adjusted similarity score
        """
        # Start with bias adjustment
        bias = self.bias_store.get_bias(tool_name)
        adjusted = base_similarity + bias
        
        # Apply delta if available
        delta = self.bias_store.get_delta(tool_name)
        if delta is not None and query_embedding is not None:
            # Delta adjusts the effective tool embedding
            # similarity(q, t + delta) ≈ similarity(q, t) + dot(q, delta) / ||q||
            query_embedding = query_embedding.flatten()
            query_norm = np.linalg.norm(query_embedding)
            if query_norm > 0:
                delta_contribution = np.dot(query_embedding, delta) / query_norm
                adjusted += 0.1 * delta_contribution  # Scale factor
        
        # Clamp to valid range
        return max(0.0, min(1.0, adjusted))
    
    def bulk_adjust(
        self,
        similarities: dict[str, float],
        query_embedding: np.ndarray | None = None,
    ) -> dict[str, float]:
        """Adjust similarities for multiple tools."""
        return {
            tool_name: self.adjust_similarity(
                tool_name, score, query_embedding
            )
            for tool_name, score in similarities.items()
        }


def create_bias_store(
    learning_rate: float = 0.05,
    enable_deltas: bool = False,
    db_path: str = "./data/tool_biases.db",
) -> ToolBiasStore:
    """Create a bias store with common configuration."""
    config = BiasConfig(
        learning_rate=learning_rate,
        enable_delta_vectors=enable_deltas,
        db_path=db_path,
    )
    return ToolBiasStore(config)
