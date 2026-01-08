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
- Create `src/ucp/contracts/trace_event.py` with structured event models
- Create `src/ucp/contracts/routing_decision.py` (expose from models)
- Create `src/ucp/observability.py` for trace management

#### 🔧 F2: Improve Error Translation (MEDIUM PRIORITY)
**What:** Standardize error responses from downstream servers  
**Why:** MCP errors need consistent format for clients  
**Action:**
- Add `src/ucp/errors.py` with standard error classes
- Wrap connection_pool errors in consistent format
- Add timeout/retry handling with exponential backoff

#### 🔧 F3: Add Request Tracing Infrastructure (MEDIUM PRIORITY)
**What:** Add trace_id/request_id to all operations  
**Why:** Required for debugging and correlation  
**Action:**
- Add `trace_context.py` for context vars
- Thread trace IDs through router → tool_zoo → connection_pool
- Emit structured trace events

#### 🔧 F4: Add Tool Affordance Generation (BACKEND SALIENCE HACK)
**What:** Generate micro-summaries for each tool  
**Why:** Increase LLM tool usage without touching clients  
**Action:**
- Add `generate_affordance_summary()` to ToolSchema
- Format: "Use when: X | Inputs: A,B | Output: Y"
- Include in MCP Tool.description field

#### 🔧 F5: Add Confidence Thresholds & Fallback Logic (HIGH PRIORITY)
**What:** Router should return confidence + fallback behavior  
**Why:** Prevent injecting low-quality tools that confuse models  
**Action:**
- Add `confidence: float` to RoutingDecision
- Add fallback logic: if confidence < threshold → return minimal safe set
- Make fallback tools configurable (currently empty in example config)

#### 🔧 F6: Tool Bundles (NICE-TO-HAVE)
**What:** Allow pre-defined tool groups (e.g., "git-workflow", "data-science")  
**Why:** Co-occurring tools should be selected together  
**Action:**
- Add `tool_bundles` to config
- Add bundle expansion logic in router

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
- Modify `connection_pool.py`:call_tool()` to raise `UCPError` variants
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
  min_confidence: 0.2
  fallback_tools:
    - "filesystem.read_file"  # Example safe tools
    - "filesystem.list_directory"

advanced:
  enable_dashboard: false
  enable_graph_viz: false
  enable_raft_export: true  # Useful for learning
```

#### C9. Expose Contract JSON Schemas
**Add to:** `src/ucp/contracts/__init__.py`

```python
"""
UCP Backend Contracts

These schemas define the stable interface between UCP backend
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

## F) REQUESTS FOR AGENT B

### R1. Update Example Config (HIGH PRIORITY)
**File:** `ucp_config.example.yaml`

**Add:**
```yaml
router:
  # ... existing fields ...
  min_confidence: 0.2  # NEW
  fallback_tools:      # NEW (populate with real tool names after testing)
    - "example.safe_tool"

advanced:  # NEW section
  enable_dashboard: false
  enable_graph_viz: false
  enable_raft_export: true
```

**Rationale:** Backend needs these knobs for fallback behavior

---

### R2. Add Integration Tests (MEDIUM PRIORITY)
**Files:** `tests/integration/test_virtual_mcp_server.py`

**Test scenarios:**
1. **Test dynamic tool selection:**
   - Given: Session with message "read file X"
   - When: Request tools/list
   - Then: Contains filesystem tools, excludes unrelated tools

2. **Test tool call proxying:**
   - Given: Tool injected in previous step
   - When: Call tool
   - Then: Routed correctly, result returned

3. **Test confidence fallback:**
   - Given: Session with ambiguous/empty context
   - When: Request tools/list
   - Then: Returns fallback tools with low confidence

4. **Test trace context:**
   - Given: Any request
   - When: Check logs
   - Then: All log entries have trace_id and request_id

**Rationale:** Backend is testable now; Agent B should validate contracts

---

### R3. Create Observability Dashboard Spec (LOW PRIORITY)
**File:** `docs/observability_dashboard_spec.md`

**Content:**
- What trace events are emitted
- How to parse them
- What metrics to track (tool selection precision/recall, latency, error rates)
- Example Grafana/Datadog queries

**Rationale:** Backend provides observability; Agent B documents how to consume it

---

### R4. Create CLI User Guide (MEDIUM PRIORITY)
**File:** `docs/cli_usage.md`

**Content:**
- How to install: `pip install -e .`
- How to configure: `cp ucp_config.example.yaml ucp_config.yaml`
- How to run: `ucp serve --config ucp_config.yaml`
- How to test: `ucp status` (if status command exists)
- How to enable logging: `LOG_LEVEL=DEBUG ucp serve`

**Rationale:** Backend is runnable; Agent B provides user-facing docs

---

### R5. Create Contract Documentation (HIGH PRIORITY)
**File:** `docs/backend_contracts.md`

**Content:**
- Purpose of contract schemas
- How to consume trace events (parsing, validation)
- How to interpret RoutingDecision fields
- How to use ToolSchema for tool discovery UIs
- Example code snippets (Python) for parsing events

**Rationale:** Backend exports contracts; Agent B documents how to use them

---

## G) IMPLEMENTATION SEQUENCE (Checklist)

### Week 1: Core Improvements
- [ ] C1: Create contracts directory & trace events
- [ ] C2: Add trace context management
- [ ] C3: Add structured event emitter
- [ ] C4: Standardize error responses
- [ ] C5: Add timeout & retry logic
- [ ] C6: Add tool affordance generation

### Week 2: Routing Enhancements
- [ ] C7: Add confidence scoring & fallback logic
- [ ] C8: Request Agent B config updates (R1)
- [ ] C9: Export contract JSON schemas

### Week 3: Verification
- [ ] Run end-to-end manual test (stdio mode)
- [ ] Request Agent B integration tests (R2)
- [ ] Request Agent B documentation (R3, R4, R5)
- [ ] Verify trace events in logs
- [ ] Verify tool affordance in MCP responses
- [ ] Verify fallback behavior with low-confidence scenarios

---

## H) TECHNICAL DECISIONS & RATIONALE

### H1. Why Keep Existing Architecture?
**Decision:** No major rewrites; incremental improvements only  
**Rationale:**
- Current code is well-structured (separation of concerns)
- Router/ToolZoo/ConnectionPool are solid abstractions
- Pydantic models enforce contracts
- Rewriting would introduce risk without proven value

### H2. Why Quarantine Advanced Features?
**Decision:** Feature-flag `dashboard`, `graph`, `raft` exports  
**Rationale:**
- v1 goal is reliability, not feature completeness
- Dashboard/graph are observability UX (not core runtime)
- RAFT export is useful but not blocking (logging already exists)
- Reduces testing surface and cognitive load

### H3. Why Add Affordance Summaries in Backend?
**Decision:** Generate "Use when: X | Inputs: A,B" in tool descriptions  
**Rationale:**
- Increases tool salience WITHOUT changing MCP protocol
- Models are more likely to use tools with clear affordances
- Backend-only change (no client modifications needed)
- Low cost, high impact

### H4. Why Confidence-Based Fallback?
**Decision:** Add min_confidence threshold + fallback_tools  
**Rationale:**
- Prevents injecting low-quality tools that confuse models
- Explicit is better than implicit (clear fallback behavior)
- Allows graceful degradation when context is ambiguous
- Makes routing failures debuggable (trace events show fallback trigger)

### H5. Why Structured Trace Events?
**Decision:** Use Pydantic models for events, not just structlog dicts  
**Rationale:**
- Type safety (clients can deserialize reliably)
- JSON Schema export for tooling
- Versioning support (Pydantic v2 migration path)
- Validation (catch malformed events early)

### H6. Why Exponential Backoff?
**Decision:** Retry tool calls with 2^attempt delay  
**Rationale:**
- Standard practice for transient failures
- Avoids thundering herd on downstream servers
- Configurable timeout/retry separately per use case
- Fail-fast on hard errors, retry on transients

---

## I) RISK ANALYSIS & MITIGATION

### R1: ChromaDB Dependency (MEDIUM RISK)
**Risk:** ChromaDB might be flaky, requires disk persistence  
**Mitigation:**
- Already has in-memory fallback (HybridToolZoo with keyword search)
- Graceful degradation: if embeddings fail, use keyword-only mode
- Document ChromaDB setup issues in troubleshooting guide (Agent B)

### R2: Stdio Connection Lifecycle (MEDIUM RISK)
**Risk:** Stdio subprocesses might hang or crash  
**Mitigation:**
- Add process health checks (ping/pong if MCP supports)
- Add connection restart logic (LazyConnectionPool already supports)
- Document signal handling for graceful shutdown (Agent B)

### R3: Tool Name Collisions (LOW RISK)
**Risk:** Two servers might have tools with same name  
**Mitigation:**
- Already handled: tools are prefixed with server name (e.g., `github.search`)
- Connection pool maps `server.tool` → server_name
- Clear error if ambiguous tool name used without prefix

### R4: Session SQLite Locking (LOW RISK)
**Risk:** SQLite might lock under high concurrency  
**Mitigation:**
- Document SQLite WAL mode for better concurrency (Agent B)
- Provide Redis backend option (already in config, stubbed)
- For v1 single-client mode, SQLite is sufficient

### R5: Embedding Model Download (LOW RISK)
**Risk:** First run downloads sentence-transformers model (slow)  
**Mitigation:**
- Document in setup guide: "First run may download ~100MB model" (Agent B)
- Optionally pre-download in Docker image (future)
- Fail gracefully if no internet: use keyword-only mode

---

## J) PERFORMANCE TARGETS

### Latency Targets (v1)
- **Tool selection:** < 100ms (p50), < 300ms (p99)
- **Tool call proxy:** < 50ms overhead + downstream latency
- **Session load:** < 10ms (from SQLite)

### Scalability Targets (v1)
- **Concurrent sessions:** 10 (single client, multiple conversations)
- **Downstream servers:** 20
- **Total tools indexed:** 500
- **Tools per server:** Average 25

### Observability Targets (v1)
- **Trace coverage:** 100% of tool_list/tool_call operations
- **Log volume:** < 1000 events/hour under normal load
- **Trace retention:** Last 1000 events in memory (for status endpoint)

---

## K) OPEN QUESTIONS (For Agent B / User)

### Q1: Client Integration Priority
**Question:** Which client should we prioritize first?
- [ ] CLI (simple, good for testing)
- [ ] VS Code extension (high value, complex)
- [ ] Claude Desktop config (easiest onboarding)

**Impact:** Affects test planning and documentation focus

### Q2: Default Fallback Tools
**Question:** What should `fallback_tools` contain?
- Option A: Empty (fail explicitly if no tools match)
- Option B: Generic safe tools (filesystem.read_file, etc.)
- Option C: All tools (defeats purpose of UCP)

**Recommendation:** Option B, but needs user to specify based on their setup

### Q3: Observability Sink
**Question:** Where should trace events go?
- [ ] Stdout (structlog JSON)
- [ ] File (rolling JSONL)
- [ ] HTTP endpoint (Grafana Loki, Datadog)
- [ ] All of the above (configurable)

**Recommendation:** Start with stdout, add file in v1.1

### Q4: Feature Flag Defaults
**Question:** Should advanced features be opt-in or opt-out?
- Dashboard: Opt-in (off by default) ✅
- Graph viz: Opt-in (off by default) ✅
- RAFT export: Opt-in (off by default) or Opt-out (on by default)?

**Recommendation:** RAFT export opt-out (useful for learning, low cost)

---

## L) BACKEND SUCCESS METRICS (How to Know It's Working)

### M1: Tool Selection Quality
**Metric:** Precision & Recall of tool selection  
**Measurement:**
- Precision = (tools selected AND used) / (tools selected)
- Recall = (tools selected AND used) / (tools used)
- Target: Precision > 60%, Recall > 80%

**How to measure:**
- AdaptiveRouter already tracks this in `get_learning_stats()`
- Expose via status endpoint or logs

### M2: Fallback Rate
**Metric:** % of routing decisions that triggered fallback  
**Measurement:**
- Count `RouterFallbackEvent` events
- Target: < 10% (most contexts should have clear routing)

### M3: Downstream Error Rate
**Metric:** % of tool calls that fail  
**Measurement:**
- Count `ToolCallProxyEndEvent` with `success=false`
- Target: < 5% (excluding user errors like bad args)

### M4: Tool Diversity
**Metric:** % of available tools that get used at least once  
**Measurement:**
- Count unique tools in `session.tool_usage`
- Target: > 30% of all indexed tools used across sessions

---

## M) END STATE VISION (What Good Looks Like)

### Backend Running Well:
- ✅ `ucp serve` starts with no errors
- ✅ Connects to all configured downstream servers
- ✅ Indexes tools (logs "X tools indexed from Y servers")
- ✅ Responds to MCP `tools/list` with context-aware subset
- ✅ Routes `tools/call` correctly, returns results
- ✅ Emits trace events (parseable JSON in stdout)
- ✅ Handles errors gracefully (clear error messages)
- ✅ Falls back to safe tools on low confidence
- ✅ Session state persists across restarts (SQLite)

### Backend Debugging Experience:
- ✅ Every routing decision has reasoning
- ✅ Every tool call has trace_id for correlation
- ✅ Logs show: "Selected 5 tools | Precision: 0.75 | Domains: [code, files]"
- ✅ Status endpoint shows: connected servers, tool stats, learning metrics
- ✅ Contract schemas validate correctly in client code

### Backend Performance:
- ✅ Tool selection completes in < 100ms
- ✅ No visible latency added to tool calls
- ✅ ChromaDB loads embeddings in < 1s on startup
- ✅ SQLite queries complete in < 10ms

---

**HANDOFF TO IMPLEMENTATION:**

Agent A (me) will now implement C1-C9 in order, creating files in `src/ucp/` only.

Agent B will handle:
- R1: Config updates
- R2: Integration tests
- R3-R5: Documentation

User approval required before starting.
