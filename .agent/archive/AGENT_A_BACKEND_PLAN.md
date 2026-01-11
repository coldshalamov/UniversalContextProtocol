<!--
ARCHIVED DOCUMENT - 2026-01-10

This document has been archived because its detailed backend implementation plan
has been consolidated into the executive summary: .agent/BACKEND_EXECUTIVE_SUMMARY.md

The 7 focused improvements (F1-F7), implementation phases (C1-C9),
and backend analysis from this document are now part of the executive summary.

This file is preserved for historical reference but should not be used for current development.
For the latest backend analysis, see: .agent/BACKEND_EXECUTIVE_SUMMARY.md
-->

# UCP Backend - Agent A Implementation Plan

**Role:** Backend/Gateway Engineer  
**Scope:** `src/ucp/**` only (+ minimal `pyproject.toml` changes if needed)  
**Status:** Analysis Complete | Implementation Ready

---

## A) BACKEND ARCHITECTURE SUMMARY

### Current State Assessment ✅

The UCP backend is **SUBSTANTIALLY COMPLETE** and follows solid engineering patterns:

#### Core Modules in `src/ucp/`

1. **`server.py`** - Virtual MCP Server Core  
   - ✅ Implements MCP protocol handlers (`list_tools`, `call_tool`)
   - ✅ Dynamic tool injection via Router
   - ✅ Session management integration
   - ✅ Observability hooks (structlog)
   - ✅ Builder pattern for composition

2. **`router.py`** - Tool Selection Brain  
   - ✅ Base `Router` with semantic/keyword/hybrid search
   - ✅ `AdaptiveRouter` with co-occurrence learning
   - ✅ Domain detection (keyword-based)
   - ✅ Re-ranking with domain/tag/usage boosts
   - ✅ Diversity filtering (max 3 tools per server)
   - ✅ Structured `RoutingDecision` output

3. **`tool_zoo.py`** - Tool Registry & Search  
   - ✅ `ToolZoo` with semantic search (ChromaDB + embeddings)
   - ✅ `HybridToolZoo` with keyword + semantic fusion
   - ✅ Tool schema normalization
   - ✅ Stats and inspection methods

4. **`connection_pool.py`** - Downstream Server Manager  
   - ✅ `ConnectionPool` for eager connection
   - ✅ `LazyConnectionPool` for on-demand connection
   - ✅ Stdio transport implemented
   - ⚠️ SSE/HTTP transports stubbed (not v1 blocker)
   - ✅ Tool discovery and caching
   - ✅ Error handling and health status

5. **`session.py`** - Session State & Persistence  
   - ✅ SQLite persistence
   - ✅ Message archiving
   - ✅ Tool usage tracking
   - ✅ Session cleanup

6. **`models.py`** - Data Models  
   - ✅ `ToolSchema` (canonical representation)
   - ✅ `SessionState`, `Message`, `RoutingDecision`
   - ✅ Pydantic validation throughout

7. **`config.py`** - Configuration Management  
   - ✅ YAML-based config loading
   - ✅ Server/Router/ToolZoo/Session config models
   - ✅ Directory creation helpers

8. **`cli.py`** - Entry Point (assumed present)
9. **`http_server.py`** - HTTP/SSE transport (exists, not critical for v1)
10. **Other files** - `transports.py`, `dashboard.py`, `graph.py`, `raft.py`, `client_api.py`

---

## B) KEEP / FIX / CUT PLAN

### KEEP (Core v1 Components)

✅ **Keep as-is:**
- `server.py` - Solid virtual MCP implementation
- `router.py` - Well-designed routing logic
- `tool_zoo.py` - Functional hybrid search
- `connection_pool.py` - Robust connection management
- `session.py` - Good persistence layer
- `models.py` - Clean data models
- `config.py` - Adequate config system
- `cli.py` - Entry point

### FIX (Required Improvements for Production-Grade v1)

#### 🔧 F1: Add Observability Contracts (HIGH PRIORITY)
**What:** Create structured trace/event schemas for observability  
**Why:** Currently logs exist but no formal contract for clients/observability tools  
**Action:**
- Create `src/ucp/contracts/` with Pydantic event models
- Create `src/ucp/contracts/routing_decision.py` (expose from models)
- Create `src/ucp/observability.py` for trace management

**Events to emit:**
- `ToolListRequestEvent` - Client asked for tools
- `ToolListDecisionEvent` - Router selected tools (with scores, reasoning)
- `ToolCallProxyStartEvent` - Tool execution started
- `ToolCallProxyEndEvent` - Tool execution finished (success/error)
- `RouterFallbackEvent` - Low confidence triggered fallback

Each event has: `trace_id`, `request_id`, `session_id`, `timestamp`

#### 🔧 F2: Improve Error Translation (MEDIUM PRIORITY)
**What:** Standardize error responses from downstream servers  
**Why:** MCP errors need consistent format for clients  
**Action:**
- Add `src/ucp/errors.py` with standard error classes
- Wrap connection_pool errors in consistent format
- Add timeout/retry handling with exponential backoff

**Error types:**
- `ToolNotFoundError` (code: TOOL_NOT_FOUND)
- `ServerConnectionError` (code: SERVER_CONNECTION_FAILED)
- `ToolExecutionError` (code: TOOL_EXECUTION_FAILED)

#### 🔧 F3: Add Request Tracing Infrastructure (MEDIUM PRIORITY)
**What:** Add trace_id/request_id to all operations  
**Why:** Required for debugging and correlation  
**Action:**
- Add `trace_context.py` for context vars
- Thread trace IDs through router → tool_zoo → connection_pool
- Emit structured trace events

#### 🔧 F4: Add Tool Affordance (BACKEND SALIENCE HACK)
**What:** Generate micro-summaries for each tool  
**Why:** Increase LLM tool usage without changing MCP protocol  
**Action:**
- Add `generate_affordance_summary()` to ToolSchema
- Format: "Use when: X | Inputs: A,B | Output: Y"
- Include in MCP Tool.description field

**Example:**
```
Before: "Search GitHub repositories"

After: "Search GitHub repositories
       Use when: searching for code or projects on GitHub
       Inputs: query*, per_page, sort
       Output: List of repository objects"
```

This makes tools **more obvious** to LLMs.

#### 🔧 F5: Add Confidence Thresholds & Fallback Logic (HIGH PRIORITY)
**What:** Router should return confidence + fallback behavior  
**Why:** Prevent injecting low-quality tools that confuse models  
**Action:**
- Add `confidence: float` to RoutingDecision
- Add fallback logic: if confidence < threshold → return minimal safe set
- Make fallback tools configurable (currently empty in example config)

**Logic:**
```python
if confidence < 0.2:  # Configurable
    return fallback_tools  # Safe minimal set
else:
    return top_k_predictions
```

#### 🔧 F6: Tool Bundles (Nice-to-Have)

**What:** Allow pre-defined tool groups (e.g., "git-workflow", "data-science")  
**Why:** Co-occurring tools should be selected together  
**Action:**
- Add `tool_bundles` to config
- Add bundle expansion logic in router

#### 🔧 F7: Feature Flags

**What:** Quarantine advanced modules behind feature flags  
**Why:** Advanced modules (dashboard, graph, raft) add complexity  
**Action:** Quarantine behind `advanced: {}` config section  
**Impact:** Simpler v1, clear upgrade path

### CUT / DISABLE (Reduce Complexity)

❌ **Quarantine behind feature flags:**
- `dashboard.py` - Not core to v1 gateway; can be optional HTTP endpoint
- `graph.py` - Unclear purpose; seems like planning/visualization (not runtime)
- `raft.py` - RAFT fine-tuning export (good for learning, not runtime critical)
- `client_api.py` - If this is a high-level client wrapper, quarantine for v1

**Action:** Add `enable_advanced_features` config flag:
```yaml
advanced:
  enable_dashboard: false  # HTTP /status endpoint
  enable_graph_viz: false  # Tool dependency graphs
  enable_raft_export: false  # Export training data
```

---

## C) CONCRETE IMPLEMENTATION PLAN (Ordered)

### Phase 1: Observability & Contracts (1-2 days)

#### C1. Create Backend Contracts Directory
**New files:**
```
src/ucp/contracts/
  __init__.py
  trace_event.py       # Structured event models
  routing_decision.py  # Re-export from models with JSON schema
  tool_descriptor.py   # Re-export ToolSchema with JSON schema
```

**Purpose:** These are the ONLY interfaces Agent B should depend on.

**Implementation:**
1. Define `TraceEvent` BaseModel with variants:
   - `ToolListRequestEvent`
   - `ToolListDecisionEvent` (includes candidates, scores, selected)
   - `ToolCallProxyStartEvent`
   - `ToolCallProxyEndEvent`
   - `DownstreamConnectEvent`
   - `RouterFallbackEvent`

2. Each event has:
   - `trace_id: str`
   - `session_id: str | None`
   - `request_id: str`
   - `timestamp: datetime`
   - Event-specific fields

3. Export JSON schemas via `.model_json_schema()`

#### C2. Add Trace Context Management
**New file:** `src/ucp/trace_context.py`

```python
from contextvars import ContextVar
from uuid import uuid4

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

def init_trace_context() -> dict[str, str]:
    """Initialize trace context for a new request."""
    trace_id = str(uuid4())
    request_id = str(uuid4())
    trace_id_var.set(trace_id)
    request_id_var.set(request_id)
    return {"trace_id": trace_id, "request_id": request_id}

def get_trace_context() -> dict[str, str]:
    """Get current trace context."""
    return {
        "trace_id": trace_id_var.get(),
        "request_id": request_id_var.get(),
    }
```

**Integration points:**
- `server.py`: Call `init_trace_context()` at start of each MCP handler
- `router.py`, `tool_zoo.py`, `connection_pool.py`: Use `get_trace_context()` in logs

#### C3. Add Structured Event Emitter
**New file:** `src/ucp/observability.py`

```python
from ucp.contracts.trace_event import TraceEvent
import structlog

logger = structlog.get_logger(__name__)

def emit_trace_event(event: TraceEvent) -> None:
    """Emit a structured trace event."""
    logger.info(
        event.event_type,
        **event.model_dump(exclude_none=True)
    )
```

**Usage:** Replace ad-hoc logging with structured events where critical

### Phase 2: Error Handling & Resilience (1 day)

#### C4. Standardize Error Response
**New file:** `src/ucp/errors.py`

```python
class UCPError(Exception):
    """Base UCP error."""
    def __init__(self, message: str, code: str, details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(message)

class ToolNotFoundError(UCPError):
    def __init__(self, tool_name: str):
        super().__init__(
            f"Tool not found: {tool_name}",
            "TOOL_NOT_FOUND",
            {"tool_name": tool_name}
        )

class ServerConnectionError(UCPError):
    def __init__(self, server_name: str, reason: str):
        super().__init__(
            f"Failed to connect to server: {server_name}",
            "SERVER_CONNECTION_FAILED",
            {"server_name": server_name, "reason": reason}
        )

class ToolExecutionError(UCPError):
    def __init__(self, tool_name: str, reason: str):
        super().__init__(
            f"Tool execution failed: {tool_name}",
            "TOOL_EXECUTION_FAILED",
            {"tool_name": tool_name, "reason": reason}
        )
```

**Integration:**
- Modify `connection_pool.py:call_tool()` to raise `UCPError` variants
- Modify `server.py:_call_tool()` to catch and format MCP errors

#### C5. Add Timeout & Retry Logic
**Modify:** `src/ucp/connection_pool.py`

Add to `ConnectionPool`:
```python
async def call_tool_with_retry(
    self,
    tool_name: str,
    arguments: dict[str, Any],
    timeout: float = 30.0,
    max_retries: int = 2
) -> Any:
    """Call tool with timeout and exponential backoff retry."""
    for attempt in range(max_retries + 1):
        try:
            return await asyncio.wait_for(
                self.call_tool(tool_name, arguments),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            if attempt == max_retries:
                raise ToolExecutionError(tool_name, "Timeout")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            if attempt == max_retries:
                raise
            await asyncio.sleep(2 ** attempt)
```

Use this in `server.py` instead of direct `call_tool()`

### Phase 3: Tool Affordance & Salience (1 day)

#### C6. Add Tool Affordance Generation
**Modify:** `src/ucp/models.py`

Add method to `ToolSchema`:
```python
def generate_affordance_summary(self) -> str:
    """Generate a crisp 1-2 line affordance hint."""
    parts = []
    
    # Use when
    if self.description:
        use_when = self.description.split(".")[0]  # First sentence
        parts.append(f"Use when: {use_when}")
    
    # Inputs
    if self.input_schema.get("properties"):
        required = self.input_schema.get("required", [])
        params = [
            f"{k}{'*' if k in required else ''}"
            for k in self.input_schema["properties"].keys()
        ]
        parts.append(f"Inputs: {', '.join(params[:5])}")  # Max 5 params
    
    # Output hint (if available in description)
    # Could be enhanced with output_schema if we track it
    
    return " | ".join(parts)
```

**Modify:** `src/ucp/server.py`

In `_list_tools()`, enhance tool descriptions:
```python
for tool_schema in self._last_routing.selected_tools:
    tool = self.tool_zoo.get_tool(tool_schema)
    if tool:
        # Enhance description with affordance
        enhanced_desc = f"{tool.description}\n\n{tool.generate_affordance_summary()}"
        tools.append(Tool(
            name=tool.name,
            description=enhanced_desc,
            inputSchema=tool.input_schema,
        ))
```

### Phase 4: Routing Confidence & Fallback (1 day)

#### C7. Add Confidence Scoring
**Modify:** `src/ucp/models.py`

Add field to `RoutingDecision`:
```python
confidence: float = Field(
    default=1.0,
    ge=0.0,
    le=1.0,
    description="Confidence in tool selection (0-1)"
)
```

**Modify:** `src/ucp/router.py`

In `Router.route()`, calculate confidence:
```python
# After getting scores, calculate confidence
if scores:
    top_score = max(scores.values())
    avg_score = sum(scores.values()) / len(scores)
    confidence = min(1.0, (top_score + avg_score) / 2)  # Simple heuristic
else:
    confidence = 0.0

decision.confidence = confidence
```

Add fallback logic:
```python
# Before returning decision
if confidence < self.config.min_confidence:  # Add to RouterConfig
    logger.warning(
        "low_confidence_fallback",
        confidence=confidence,
        threshold=self.config.min_confidence
    )
    # Return safe minimal set
    return RoutingDecision(
        selected_tools=self.config.fallback_tools[:self.config.min_tools],
        scores={},
        reasoning=f"Low confidence ({confidence:.2f}), using fallback",
        query_used=query,
        confidence=0.0
    )
```

**Modify:** `src/ucp/config.py`

Add to `RouterConfig`:
```python
min_confidence: float = Field(
    default=0.2,
    description="Minimum confidence to use predictions (else fallback)"
)
```

### Phase 5: Polish & Documentation (0.5 days)

#### C8. Update Config Example
**Modify:** `ucp_config.example.yaml` (READ-ONLY, but REQUEST AGENT B)

Request Agent B to add:
```yaml
router:
  # ... existing fields ...
  min_confidence: 0.2
  fallback_tools:
    - "filesystem.read_file"  # Example safe tools
    - "filesystem.list_directory"

advanced:
  enable_dashboard: false
  enable_graph_viz: false
  enable_raft_export: true  # Useful for learning
```

**Rationale:** Backend needs these knobs for fallback behavior

#### C9. Expose Contract JSON Schemas
**Add to:** `src/ucp/contracts/__init__.py`

```python
"""
UCP Backend Contracts

These schemas define stable interface between UCP backend
and clients/observability tools.
"""

from .trace_event import (
    TraceEvent,
    ToolListRequestEvent,
    ToolListDecisionEvent,
    ToolCallProxyStartEvent,
    ToolCallProxyEndEvent,
)
from .routing_decision import RoutingDecision
from .tool_descriptor import ToolSchema

__all__ = [
    "TraceEvent",
    "ToolListRequestEvent",
    "ToolListDecisionEvent",
    "ToolCallProxyStartEvent",
    "ToolCallProxyEndEvent",
    "RoutingDecision",
    "ToolSchema",
]

def export_schemas() -> dict[str, dict]:
    """Export all contract schemas as JSON Schema."""
    return {
        "trace_event": TraceEvent.model_json_schema(),
        "routing_decision": RoutingDecision.model_json_schema(),
        "tool_schema": ToolSchema.model_json_schema(),
    }
```

---

## D) CONTRACT ARTIFACTS (Backend-Owned)

### D1. Trace Event Schema
**File:** `src/ucp/contracts/trace_event.jsonschema`

Generated from `TraceEvent.model_json_schema()`

### D2. Routing Decision Schema
**File:** `src/ucp/contracts/routing_decision.jsonschema`

Generated from `RoutingDecision.model_json_schema()`

### D3. Tool Descriptor Schema
**File:** `src/ucp/contracts/tool_descriptor.jsonschema`

Generated from `ToolSchema.model_json_schema()`

**Usage by Agent B:**
- Clients can parse trace events for observability UIs
- Evaluation harness can validate routing decisions
- Tool discovery UIs can render tool schemas

---

## E) DEFINITION OF DONE (Backend)

UCP Backend v1 is DONE when:

✅ **F1-F7 implemented** (Observability, Errors, Tracing, Affordance, Confidence, Fallback)  
✅ **All MCP protocol methods work** (tools/list, tools/call)  
✅ **Routing is deterministic and explainable** (trace events show WHY)  
✅ **Downstream calls are robust** (timeouts, retries, error translation)  
✅ **Tool schemas have affordance hints** (increased salience)  
✅ **Confidence-based fallback prevents bad selections**  
✅ **Contract schemas exported and documented**  
✅ **Backend can run standalone** (via CLI with config file)

### Not Required for Backend v1:
- ❌ SSE/HTTP transports (stdio sufficient)
- ❌ Dashboard HTTP endpoint (can be feature-flagged)
- ❌ Graph visualization (nice-to-have)
- ❌ RAFT fine-tuning pipeline (logging exists, export is bonus)

---

**HANDOFF TO IMPLEMENTATION:**

Agent A (me) will now implement C1-C9 in order, creating files in `src/ucp/` only.

Agent B will handle:
- R1: Config updates
- R2: Integration tests
- R3: Observability dashboard spec
- R4: CLI user guide
- R5: Contract documentation

User approval required before starting.
