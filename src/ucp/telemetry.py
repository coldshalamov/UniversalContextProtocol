"""
Telemetry - Structured Logging and Event Store for UCP.

Implements a robust telemetry system for routing events, tool calls,
and learning feedback. This is the foundation for online learning
and evaluation metrics.

Design Principles:
- Privacy-first: Only hash queries by default, raw text is opt-in
- Structured: All events have stable schemas for analysis
- Efficient: Batched writes, TTL-based cleanup
- Extensible: Interface allows different backends (SQLite, future: cloud)
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import structlog

logger = structlog.get_logger(__name__)


class EventType(str, Enum):
    """Types of telemetry events."""
    
    ROUTING_DECISION = "routing_decision"
    TOOL_CALL = "tool_call"
    REWARD_SIGNAL = "reward_signal"
    LEARNING_UPDATE = "learning_update"


@dataclass
class CandidateInfo:
    """Information about a candidate tool during selection."""
    
    tool_name: str
    base_score: float
    keyword_score: float = 0.0
    domain_match: bool = False
    cooccurrence_boost: float = 0.0
    bandit_score: float = 0.0
    bias_adjustment: float = 0.0
    final_score: float = 0.0
    schema_tokens: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "base_score": self.base_score,
            "keyword_score": self.keyword_score,
            "domain_match": self.domain_match,
            "cooccurrence_boost": self.cooccurrence_boost,
            "bandit_score": self.bandit_score,
            "bias_adjustment": self.bias_adjustment,
            "final_score": self.final_score,
            "schema_tokens": self.schema_tokens,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CandidateInfo:
        return cls(**data)


@dataclass
class RoutingEvent:
    """A routing decision event for telemetry."""
    
    event_id: UUID = field(default_factory=uuid4)
    session_id: UUID | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Query info (hashed by default)
    query_hash: str = ""
    query_text: str | None = None  # Only populated if logging enabled
    
    # Candidate and selection info
    candidates: list[CandidateInfo] = field(default_factory=list)
    selected_tools: list[str] = field(default_factory=list)
    
    # Context/budget info
    total_candidates: int = 0
    context_tokens_used: int = 0
    max_context_tokens: int = 0
    selection_time_ms: float = 0.0
    
    # Strategy info
    strategy: str = "baseline"
    exploration_triggered: bool = False
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "session_id": str(self.session_id) if self.session_id else None,
            "timestamp": self.timestamp.isoformat(),
            "query_hash": self.query_hash,
            "query_text": self.query_text,
            "candidates": [c.to_dict() for c in self.candidates],
            "selected_tools": self.selected_tools,
            "total_candidates": self.total_candidates,
            "context_tokens_used": self.context_tokens_used,
            "max_context_tokens": self.max_context_tokens,
            "selection_time_ms": self.selection_time_ms,
            "strategy": self.strategy,
            "exploration_triggered": self.exploration_triggered,
        }


@dataclass  
class ToolCallEvent:
    """A tool invocation event for telemetry."""
    
    event_id: UUID = field(default_factory=uuid4)
    session_id: UUID | None = None
    routing_event_id: UUID | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    tool_name: str = ""
    success: bool = False
    error_class: str | None = None
    execution_time_ms: float = 0.0
    
    # Was this tool in the selected set?
    was_selected: bool = True
    selection_rank: int = -1  # Position in selected list
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "session_id": str(self.session_id) if self.session_id else None,
            "routing_event_id": str(self.routing_event_id) if self.routing_event_id else None,
            "timestamp": self.timestamp.isoformat(),
            "tool_name": self.tool_name,
            "success": self.success,
            "error_class": self.error_class,
            "execution_time_ms": self.execution_time_ms,
            "was_selected": self.was_selected,
            "selection_rank": self.selection_rank,
        }


@dataclass
class RewardSignal:
    """Computed reward for a tool call, used for online learning."""
    
    event_id: UUID = field(default_factory=uuid4)
    tool_call_event_id: UUID | None = None
    tool_name: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Raw components
    success_reward: float = 0.0  # +1 for success, -1 for failure
    latency_penalty: float = 0.0  # Negative, proportional to latency
    context_cost_penalty: float = 0.0  # Negative, proportional to schema size
    followup_penalty: float = 0.0  # Negative if user retries immediately
    
    # Final normalized reward in [-1, +1]
    total_reward: float = 0.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": str(self.event_id),
            "tool_call_event_id": str(self.tool_call_event_id) if self.tool_call_event_id else None,
            "tool_name": self.tool_name,
            "timestamp": self.timestamp.isoformat(),
            "success_reward": self.success_reward,
            "latency_penalty": self.latency_penalty,
            "context_cost_penalty": self.context_cost_penalty,
            "followup_penalty": self.followup_penalty,
            "total_reward": self.total_reward,
        }


def hash_query(query: str) -> str:
    """Generate a stable hash for a query string."""
    return hashlib.sha256(query.encode()).hexdigest()[:16]


class TelemetryStore(ABC):
    """Abstract interface for telemetry storage."""
    
    @abstractmethod
    def log_routing_event(self, event: RoutingEvent) -> None:
        """Log a routing decision event."""
        pass
    
    @abstractmethod
    def log_tool_call(self, event: ToolCallEvent) -> None:
        """Log a tool call event."""
        pass
    
    @abstractmethod
    def log_reward(self, reward: RewardSignal) -> None:
        """Log a reward signal for learning."""
        pass
    
    @abstractmethod
    def get_tool_stats(
        self, 
        tool_name: str | None = None,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Get aggregated statistics for tools."""
        pass
    
    @abstractmethod
    def get_routing_events(
        self,
        session_id: UUID | None = None,
        limit: int = 100,
    ) -> list[RoutingEvent]:
        """Retrieve routing events."""
        pass
    
    @abstractmethod
    def cleanup_old_events(self, max_age_hours: int = 168) -> int:
        """Delete events older than max_age_hours. Returns count deleted."""
        pass


class SQLiteTelemetryStore(TelemetryStore):
    """SQLite-backed telemetry storage."""
    
    def __init__(self, db_path: str | Path = "./data/telemetry.db") -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._db: sqlite3.Connection | None = None
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database schema."""
        self._db = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        
        self._db.executescript("""
            -- Routing decisions
            CREATE TABLE IF NOT EXISTS routing_events (
                event_id TEXT PRIMARY KEY,
                session_id TEXT,
                timestamp TEXT NOT NULL,
                query_hash TEXT NOT NULL,
                query_text TEXT,
                candidates_json TEXT NOT NULL,
                selected_tools_json TEXT NOT NULL,
                total_candidates INTEGER NOT NULL,
                context_tokens_used INTEGER NOT NULL,
                max_context_tokens INTEGER NOT NULL,
                selection_time_ms REAL NOT NULL,
                strategy TEXT NOT NULL,
                exploration_triggered INTEGER NOT NULL
            );
            
            CREATE INDEX IF NOT EXISTS idx_routing_session 
            ON routing_events(session_id, timestamp);
            
            CREATE INDEX IF NOT EXISTS idx_routing_timestamp 
            ON routing_events(timestamp);
            
            -- Tool calls
            CREATE TABLE IF NOT EXISTS tool_call_events (
                event_id TEXT PRIMARY KEY,
                session_id TEXT,
                routing_event_id TEXT,
                timestamp TEXT NOT NULL,
                tool_name TEXT NOT NULL,
                success INTEGER NOT NULL,
                error_class TEXT,
                execution_time_ms REAL NOT NULL,
                was_selected INTEGER NOT NULL,
                selection_rank INTEGER NOT NULL,
                FOREIGN KEY (routing_event_id) REFERENCES routing_events(event_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_tool_call_session 
            ON tool_call_events(session_id, timestamp);
            
            CREATE INDEX IF NOT EXISTS idx_tool_call_tool 
            ON tool_call_events(tool_name, timestamp);
            
            -- Reward signals
            CREATE TABLE IF NOT EXISTS reward_signals (
                event_id TEXT PRIMARY KEY,
                tool_call_event_id TEXT,
                tool_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                success_reward REAL NOT NULL,
                latency_penalty REAL NOT NULL,
                context_cost_penalty REAL NOT NULL,
                followup_penalty REAL NOT NULL,
                total_reward REAL NOT NULL,
                FOREIGN KEY (tool_call_event_id) REFERENCES tool_call_events(event_id)
            );
            
            CREATE INDEX IF NOT EXISTS idx_reward_tool 
            ON reward_signals(tool_name, timestamp);
            
            -- Aggregated tool statistics (materialized view, updated periodically)
            CREATE TABLE IF NOT EXISTS tool_stats_cache (
                tool_name TEXT PRIMARY KEY,
                total_calls INTEGER NOT NULL DEFAULT 0,
                success_count INTEGER NOT NULL DEFAULT 0,
                failure_count INTEGER NOT NULL DEFAULT 0,
                avg_latency_ms REAL NOT NULL DEFAULT 0,
                avg_reward REAL NOT NULL DEFAULT 0,
                rolling_success_rate REAL NOT NULL DEFAULT 0.5,
                last_updated TEXT NOT NULL
            );
        """)
        self._db.commit()
        
        logger.info("telemetry_db_initialized", path=str(self.db_path))
    
    def log_routing_event(self, event: RoutingEvent) -> None:
        """Log a routing decision event."""
        if not self._db:
            return
        
        self._db.execute(
            """
            INSERT OR REPLACE INTO routing_events 
            (event_id, session_id, timestamp, query_hash, query_text,
             candidates_json, selected_tools_json, total_candidates,
             context_tokens_used, max_context_tokens, selection_time_ms,
             strategy, exploration_triggered)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(event.event_id),
                str(event.session_id) if event.session_id else None,
                event.timestamp.isoformat(),
                event.query_hash,
                event.query_text,
                json.dumps([c.to_dict() for c in event.candidates]),
                json.dumps(event.selected_tools),
                event.total_candidates,
                event.context_tokens_used,
                event.max_context_tokens,
                event.selection_time_ms,
                event.strategy,
                1 if event.exploration_triggered else 0,
            ),
        )
        self._db.commit()
    
    def log_tool_call(self, event: ToolCallEvent) -> None:
        """Log a tool call event."""
        if not self._db:
            return
        
        self._db.execute(
            """
            INSERT OR REPLACE INTO tool_call_events
            (event_id, session_id, routing_event_id, timestamp, tool_name,
             success, error_class, execution_time_ms, was_selected, selection_rank)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(event.event_id),
                str(event.session_id) if event.session_id else None,
                str(event.routing_event_id) if event.routing_event_id else None,
                event.timestamp.isoformat(),
                event.tool_name,
                1 if event.success else 0,
                event.error_class,
                event.execution_time_ms,
                1 if event.was_selected else 0,
                event.selection_rank,
            ),
        )
        self._db.commit()
        
        # Update cached stats
        self._update_tool_stats(event.tool_name)
    
    def log_reward(self, reward: RewardSignal) -> None:
        """Log a reward signal for learning."""
        if not self._db:
            return
        
        self._db.execute(
            """
            INSERT OR REPLACE INTO reward_signals
            (event_id, tool_call_event_id, tool_name, timestamp,
             success_reward, latency_penalty, context_cost_penalty,
             followup_penalty, total_reward)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(reward.event_id),
                str(reward.tool_call_event_id) if reward.tool_call_event_id else None,
                reward.tool_name,
                reward.timestamp.isoformat(),
                reward.success_reward,
                reward.latency_penalty,
                reward.context_cost_penalty,
                reward.followup_penalty,
                reward.total_reward,
            ),
        )
        self._db.commit()
    
    def _update_tool_stats(self, tool_name: str) -> None:
        """Update cached statistics for a tool."""
        if not self._db:
            return
        
        # Calculate stats from recent events
        row = self._db.execute(
            """
            SELECT 
                COUNT(*) as total_calls,
                SUM(success) as success_count,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failure_count,
                AVG(execution_time_ms) as avg_latency
            FROM tool_call_events
            WHERE tool_name = ?
            """,
            (tool_name,),
        ).fetchone()
        
        # Get average reward
        reward_row = self._db.execute(
            """
            SELECT AVG(total_reward) as avg_reward
            FROM reward_signals
            WHERE tool_name = ?
            """,
            (tool_name,),
        ).fetchone()
        
        total = row["total_calls"] or 0
        successes = row["success_count"] or 0
        
        # Rolling success rate with smoothing (add-1 smoothing)
        rolling_rate = (successes + 1) / (total + 2)
        
        self._db.execute(
            """
            INSERT OR REPLACE INTO tool_stats_cache
            (tool_name, total_calls, success_count, failure_count,
             avg_latency_ms, avg_reward, rolling_success_rate, last_updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tool_name,
                total,
                successes,
                row["failure_count"] or 0,
                row["avg_latency"] or 0,
                reward_row["avg_reward"] or 0,
                rolling_rate,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        self._db.commit()
    
    def get_tool_stats(
        self,
        tool_name: str | None = None,
        since: datetime | None = None,
    ) -> dict[str, Any]:
        """Get aggregated statistics for tools."""
        if not self._db:
            return {}
        
        if tool_name:
            row = self._db.execute(
                "SELECT * FROM tool_stats_cache WHERE tool_name = ?",
                (tool_name,),
            ).fetchone()
            
            if row:
                return dict(row)
            return {}
        
        # All tools
        rows = self._db.execute("SELECT * FROM tool_stats_cache").fetchall()
        return {row["tool_name"]: dict(row) for row in rows}
    
    def get_rolling_success_rate(self, tool_name: str) -> float:
        """Get the rolling success rate for a tool."""
        stats = self.get_tool_stats(tool_name)
        return stats.get("rolling_success_rate", 0.5)
    
    def get_avg_latency(self, tool_name: str) -> float:
        """Get the average latency for a tool."""
        stats = self.get_tool_stats(tool_name)
        return stats.get("avg_latency_ms", 0.0)
    
    def get_routing_events(
        self,
        session_id: UUID | None = None,
        limit: int = 100,
    ) -> list[RoutingEvent]:
        """Retrieve routing events."""
        if not self._db:
            return []
        
        if session_id:
            rows = self._db.execute(
                """
                SELECT * FROM routing_events 
                WHERE session_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (str(session_id), limit),
            ).fetchall()
        else:
            rows = self._db.execute(
                """
                SELECT * FROM routing_events 
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        
        events = []
        for row in rows:
            candidates = [
                CandidateInfo.from_dict(c) 
                for c in json.loads(row["candidates_json"])
            ]
            events.append(RoutingEvent(
                event_id=UUID(row["event_id"]),
                session_id=UUID(row["session_id"]) if row["session_id"] else None,
                timestamp=datetime.fromisoformat(row["timestamp"]),
                query_hash=row["query_hash"],
                query_text=row["query_text"],
                candidates=candidates,
                selected_tools=json.loads(row["selected_tools_json"]),
                total_candidates=row["total_candidates"],
                context_tokens_used=row["context_tokens_used"],
                max_context_tokens=row["max_context_tokens"],
                selection_time_ms=row["selection_time_ms"],
                strategy=row["strategy"],
                exploration_triggered=bool(row["exploration_triggered"]),
            ))
        
        return events
    
    def get_recent_rewards(
        self,
        tool_name: str | None = None,
        limit: int = 100,
    ) -> list[RewardSignal]:
        """Get recent reward signals."""
        if not self._db:
            return []
        
        if tool_name:
            rows = self._db.execute(
                """
                SELECT * FROM reward_signals 
                WHERE tool_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (tool_name, limit),
            ).fetchall()
        else:
            rows = self._db.execute(
                """
                SELECT * FROM reward_signals 
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        
        return [
            RewardSignal(
                event_id=UUID(row["event_id"]),
                tool_call_event_id=UUID(row["tool_call_event_id"]) if row["tool_call_event_id"] else None,
                tool_name=row["tool_name"],
                timestamp=datetime.fromisoformat(row["timestamp"]),
                success_reward=row["success_reward"],
                latency_penalty=row["latency_penalty"],
                context_cost_penalty=row["context_cost_penalty"],
                followup_penalty=row["followup_penalty"],
                total_reward=row["total_reward"],
            )
            for row in rows
        ]
    
    def cleanup_old_events(self, max_age_hours: int = 168) -> int:
        """Delete events older than max_age_hours. Returns count deleted."""
        if not self._db:
            return 0
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)
        cutoff_str = cutoff.isoformat()
        
        # Count before delete
        count = self._db.execute(
            "SELECT COUNT(*) FROM routing_events WHERE timestamp < ?",
            (cutoff_str,),
        ).fetchone()[0]
        
        # Delete old events (cascade manually since SQLite FK support varies)
        self._db.execute(
            "DELETE FROM reward_signals WHERE timestamp < ?",
            (cutoff_str,),
        )
        self._db.execute(
            "DELETE FROM tool_call_events WHERE timestamp < ?",
            (cutoff_str,),
        )
        self._db.execute(
            "DELETE FROM routing_events WHERE timestamp < ?",
            (cutoff_str,),
        )
        self._db.commit()
        
        logger.info("telemetry_cleanup", deleted=count)
        return count
    
    def get_metrics_summary(self) -> dict[str, Any]:
        """Get a summary of key metrics for dashboard."""
        if not self._db:
            return {}
        
        # Basic counts
        routing_count = self._db.execute(
            "SELECT COUNT(*) FROM routing_events"
        ).fetchone()[0]
        
        call_count = self._db.execute(
            "SELECT COUNT(*) FROM tool_call_events"
        ).fetchone()[0]
        
        # Success rate
        success_row = self._db.execute(
            """
            SELECT 
                SUM(success) as successes,
                COUNT(*) as total
            FROM tool_call_events
            """
        ).fetchone()
        
        success_rate = (
            success_row["successes"] / success_row["total"] 
            if success_row["total"] else 0
        )
        
        # Avg tools selected
        avg_tools = self._db.execute(
            """
            SELECT AVG(json_array_length(selected_tools_json)) as avg_tools
            FROM routing_events
            """
        ).fetchone()["avg_tools"] or 0
        
        # Avg selection time
        avg_time = self._db.execute(
            "SELECT AVG(selection_time_ms) FROM routing_events"
        ).fetchone()[0] or 0
        
        # Exploration rate
        exploration_row = self._db.execute(
            """
            SELECT 
                SUM(exploration_triggered) as explored,
                COUNT(*) as total
            FROM routing_events
            """
        ).fetchone()
        
        exploration_rate = (
            exploration_row["explored"] / exploration_row["total"]
            if exploration_row["total"] else 0
        )
        
        return {
            "routing_events": routing_count,
            "tool_calls": call_count,
            "overall_success_rate": success_rate,
            "avg_tools_selected": avg_tools,
            "avg_selection_time_ms": avg_time,
            "exploration_rate": exploration_rate,
        }
    
    def close(self) -> None:
        """Close database connection."""
        if self._db:
            self._db.close()
            self._db = None


class RewardCalculator:
    """Calculates normalized rewards from tool call outcomes."""
    
    def __init__(
        self,
        latency_scale: float = 0.001,  # 1ms = 0.001 penalty
        latency_cap: float = 0.3,  # Max latency penalty
        context_scale: float = 0.0001,  # Per schema token penalty
        context_cap: float = 0.2,  # Max context penalty
        followup_penalty: float = 0.2,  # Penalty for immediate retry
    ) -> None:
        self.latency_scale = latency_scale
        self.latency_cap = latency_cap
        self.context_scale = context_scale
        self.context_cap = context_cap
        self.followup_penalty_value = followup_penalty
    
    def calculate(
        self,
        success: bool,
        execution_time_ms: float,
        schema_tokens: int = 0,
        is_followup_retry: bool = False,
    ) -> RewardSignal:
        """Calculate a normalized reward signal."""
        reward = RewardSignal()
        
        # Success/failure component
        reward.success_reward = 1.0 if success else -1.0
        
        # Latency penalty (only on success, don't double-penalize failures)
        if success:
            latency_penalty = min(
                execution_time_ms * self.latency_scale,
                self.latency_cap,
            )
            reward.latency_penalty = -latency_penalty
        
        # Context cost penalty (applied always - we want efficient tool use)
        context_penalty = min(
            schema_tokens * self.context_scale,
            self.context_cap,
        )
        reward.context_cost_penalty = -context_penalty
        
        # Follow-up retry penalty
        if is_followup_retry:
            reward.followup_penalty = -self.followup_penalty_value
        
        # Total reward, clamped to [-1, +1]
        total = (
            reward.success_reward +
            reward.latency_penalty +
            reward.context_cost_penalty +
            reward.followup_penalty
        )
        reward.total_reward = max(-1.0, min(1.0, total))
        
        return reward


# Global telemetry store (lazy initialization)
_telemetry_store: SQLiteTelemetryStore | None = None


def get_telemetry_store(db_path: str | Path | None = None) -> SQLiteTelemetryStore:
    """Get or create the global telemetry store."""
    global _telemetry_store
    
    if _telemetry_store is None:
        path = db_path or "./data/telemetry.db"
        _telemetry_store = SQLiteTelemetryStore(path)
    
    return _telemetry_store
