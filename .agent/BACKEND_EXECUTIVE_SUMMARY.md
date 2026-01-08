# UCP Backend Analysis - Executive Summary

**Agent:** Agent A (Backend/Gateway Engineer)  
**Date:** 2026-01-08  
**Status:** ✅ Analysis Complete | 🟡 Awaiting Approval to Implement

---

## TL;DR

**The UCP backend is 85% complete and well-architected.**  
Instead of rewriting, I propose **7 focused improvements (F1-F7)** to reach production-grade v1.

### What Already Works ✅

- ✅ Virtual MCP server (intercepts tools/list and tools/call)
- ✅ Semantic router with hybrid search (keyword + embeddings)
- ✅ Adaptive learning (tracks co-occurrence, precision/recall)
- ✅ Connection pool for downstream servers (stdio transport)
- ✅ Session persistence (SQLite)
- ✅ Clean data models (Pydantic)

### What Needs Work 🔧

1. **F1: Observability Contracts** - Structured trace events for debugging
2. **F2: Error Translation** - Standardize error responses
3. **F3: Request Tracing** - Add trace_id/request_id to all operations
4. **F4: Tool Affordance** - Generate micro-summaries ("Use when: X | Inputs: A,B")
5. **F5: Confidence Fallback** - Don't inject low-quality tools
6. **F6: Tool Bundles** - Pre-defined tool groups (nice-to-have)
7. **F7: Advanced Feature Flags** - Quarantine dashboard/graph/raft behind flags

### Timeline

- **Phase 1-2:** 2-3 days (Observability + Errors)
- **Phase 3-4:** 2 days (Affordance + Confidence)
- **Phase 5:** 0.5 days (Polish)
- **Total:** ~5 days to production-ready backend

---

## Architecture Assessment

### Current Modules in `src/ucp/`

| Module | Status | Purpose |
|--------|--------|---------|
| `server.py` | ✅ Complete | Virtual MCP server core |
| `router.py` | ✅ Complete | Semantic routing + learning |
| `tool_zoo.py` | ✅ Complete | Vector search + keyword search |
| `connection_pool.py` | ⚠️ Needs retry logic | Downstream server management |
| `session.py` | ✅ Complete | SQLite persistence |
| `models.py` | ⚠️ Needs affordance | Data models |
| `config.py` | ⚠️ Needs confidence params | Configuration |
| `cli.py` | ✅ Complete | Entry point |
| `dashboard.py` | 🟡 Quarantine | HTTP status endpoint (optional) |
| `graph.py` | 🟡 Quarantine | Visualization (optional) |
| `raft.py` | 🟡 Quarantine | Fine-tuning export (optional) |

### Keep / Fix / Cut Decision

**KEEP (Core v1):**
- server.py, router.py, tool_zoo.py, connection_pool.py, session.py, models.py, config.py, cli.py

**FIX (7 improvements needed):**
- Add observability contracts
- Add error standardization  
- Add trace context
- Add tool affordances
- Add confidence thresholds
- Add retry/timeout logic
- Feature-flag advanced modules

**CUT (Reduce v1 scope):**
- Dashboard → feature flag (off by default)
- Graph viz → feature flag (off by default)
- RAFT export → feature flag (on by default, low cost)

---

## Data Flow (How UCP Works)

```
┌─────────────┐
│   Client    │  (Claude Desktop, VS Code, CLI)
│  (MCP User) │
└──────┬──────┘
       │ 1. tools/list request
       ▼
┌─────────────────────────────────────────┐
│         UCP Virtual MCP Server          │
│  (server.py: intercepts MCP protocol)   │
└──────┬──────────────────────────────────┘
       │ 2. Get context
       ▼
┌─────────────────────────────────────────┐
│        Session Manager                  │
│  (session.py: load conversation state)  │
└──────┬──────────────────────────────────┘
       │ 3. Route based on context
       ▼
┌─────────────────────────────────────────┐
│            Router (Brain)               │
│  (router.py: semantic + keyword search) │
└──────┬──────────────────────────────────┘
       │ 4. Search tool index
       ▼
┌─────────────────────────────────────────┐
│         Tool Zoo (Registry)             │
│  (tool_zoo.py: vector + keyword index)  │
└──────┬──────────────────────────────────┘
       │ 5. Return top-K tools + reasoning
       ▼
┌─────────────────────────────────────────┐
│    Router Re-ranks & Filters            │
│  (domain boost, diversity, confidence)  │
└──────┬──────────────────────────────────┘
       │ 6. Selected tools → MCP Tool schemas
       ▼
┌─────────────┐
│   Client    │ ← Returns 5-10 tools (not all 500!)
└─────────────┘

       │ 7. tools/call request
       ▼
┌─────────────────────────────────────────┐
│       Connection Pool (Proxy)           │
│  (connection_pool.py: route to server)  │
└──────┬──────────────────────────────────┘
       │ 8. Execute on downstream server
       ▼
┌─────────────────────────────────────────┐
│     Downstream MCP Server               │
│  (GitHub, Filesystem, Slack, etc.)      │
└──────┬──────────────────────────────────┘
       │ 9. Result
       ▼
┌─────────────┐
│   Client    │ ← Returns tool result
└─────────────┘
```

**Key Innovation:** Steps 3-6 (dynamic tool selection) prevent "Tool Overload"

---

## The 7 Improvements Explained

### F1: Observability Contracts ⭐ HIGH PRIORITY

**Problem:** Logs exist but no structured contract for observability tools  
**Solution:** Create `src/ucp/contracts/` with Pydantic event models  
**Impact:** Clients can parse trace events, build dashboards, debug routing

**Events to emit:**
- `ToolListRequestEvent` - Client asked for tools
- `ToolListDecisionEvent` - Router selected tools (with scores, reasoning)
- `ToolCallProxyStartEvent` - Tool execution started
- `ToolCallProxyEndEvent` - Tool execution finished (success/error)
- `RouterFallbackEvent` - Low confidence triggered fallback

Each event has: `trace_id`, `request_id`, `session_id`, `timestamp`

### F2: Error Translation ⭐ MEDIUM PRIORITY

**Problem:** Downstream errors not standardized (hard for clients to handle)  
**Solution:** Create `src/ucp/errors.py` with UCPError hierarchy  
**Impact:** Clients get consistent error codes/messages

**Error types:**
- `ToolNotFoundError` (code: TOOL_NOT_FOUND)
- `ServerConnectionError` (code: SERVER_CONNECTION_FAILED)
- `ToolExecutionError` (code: TOOL_EXECUTION_FAILED)

### F3: Request Tracing ⭐ MEDIUM PRIORITY

**Problem:** No correlation between logs (can't trace a request end-to-end)  
**Solution:** Add `trace_context.py` with context vars  
**Impact:** Every log entry has `trace_id` and `request_id` for debugging

### F4: Tool Affordance ⭐⭐ HIGH PRIORITY (Salience Hack)

**Problem:** Models don't use tools even when available  
**Solution:** Add `generate_affordance_summary()` to ToolSchema  
**Impact:** Increase tool usage without changing MCP protocol

**Example:**
```
Before: "Search GitHub repositories"

After: "Search GitHub repositories
       Use when: searching for code or projects on GitHub
       Inputs: query*, per_page, sort
       Output: List of repository objects"
```

This makes tools **more obvious** to LLMs.

### F5: Confidence Fallback ⭐⭐ HIGH PRIORITY

**Problem:** Router sometimes selects bad tools (low similarity scores)  
**Solution:** Add confidence threshold + fallback behavior  
**Impact:** Prevents injecting garbage tools that confuse models

**Logic:**
```python
if confidence < 0.2:  # Configurable
    return fallback_tools  # Safe minimal set
else:
    return top_k_predictions
```

### F6: Tool Bundles (Nice-to-Have)

**Problem:** Some tools always used together (e.g., git-commit + git-push)  
**Solution:** Allow pre-defined bundles in config  
**Impact:** Better tool selection for multi-step workflows

### F7: Feature Flags

**Problem:** Advanced modules (dashboard, graph, raft) add complexity  
**Solution:** Quarantine behind `advanced: {}` config section  
**Impact:** Simpler v1, clear upgrade path

---

## Contract Artifacts (Backend → Agent B Interface)

These are the ONLY things Agent B should depend on:

### 1. Trace Event Schema
**File:** `src/ucp/contracts/trace_event.jsonschema`  
**Purpose:** Parse trace events for observability  
**Consumers:** Dashboard, evaluation harness, monitoring tools

### 2. Routing Decision Schema
**File:** `src/ucp/contracts/routing_decision.jsonschema`  
**Purpose:** Understand why tools were selected  
**Consumers:** Debugging UIs, evaluation scripts

### 3. Tool Descriptor Schema
**File:** `src/ucp/contracts/tool_descriptor.jsonschema`  
**Purpose:** Tool discovery and rendering  
**Consumers:** Tool palette UIs, documentation generators

---

## Requests for Agent B (Outside My Scope)

### R1: Update Config Example ⭐ HIGH PRIORITY
**File:** `ucp_config.example.yaml`  
**Add:** `min_confidence`, `fallback_tools`, `advanced: {}` section  
**Why:** Backend needs these knobs to work

### R2: Integration Tests ⭐ MEDIUM PRIORITY
**File:** `tests/integration/test_virtual_mcp_server.py`  
**Tests:** Dynamic tool selection, proxying, fallback, tracing  
**Why:** Validate backend contracts work end-to-end

### R3: Observability Dashboard Spec 🟡 LOW PRIORITY
**File:** `docs/observability_dashboard_spec.md`  
**Content:** How to consume trace events, metrics to track  
**Why:** Backend provides observability; Agent B documents consumption

### R4: CLI User Guide ⭐ MEDIUM PRIORITY
**File:** `docs/cli_usage.md`  
**Content:** Install, configure, run, test, debug  
**Why:** Backend is runnable; Agent B provides UX docs

### R5: Contract Documentation ⭐ HIGH PRIORITY
**File:** `docs/backend_contracts.md`  
**Content:** How to parse/use trace events, routing decisions, tool schemas  
**Why:** Backend exports contracts; Agent B documents integration

---

## Success Criteria (How to Know It's Done)

### Backend DONE when:

✅ All 7 improvements implemented (F1-F7)  
✅ `ucp serve` starts with no errors  
✅ Connects to downstream servers, indexes tools  
✅ `tools/list` returns context-aware subset (not all tools)  
✅ `tools/call` routes correctly, returns results  
✅ Trace events emitted (parseable JSON)  
✅ Errors are standardized (consistent codes/messages)  
✅ Confidence fallback prevents bad selections  
✅ Contract schemas exported and documented  

### NOT Required for v1:

❌ SSE/HTTP transports (stdio sufficient)  
❌ Dashboard HTTP endpoint (feature-flagged)  
❌ Graph visualization (feature-flagged)  
❌ RAFT fine-tuning pipeline (export exists, usage is bonus)

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| ChromaDB flaky | Medium | Medium | Fallback to keyword-only mode |
| Stdio hangs | Medium | High | Add health checks + restart logic |
| Tool name collisions | Low | Low | Already prefixed (server.tool) |
| SQLite locking | Low | Low | Document WAL mode, provide Redis option |
| Embedding download slow | Low | Low | Document first-run delay |

---

## Performance Targets (v1)

- **Tool selection:** < 100ms (p50), < 300ms (p99)
- **Tool call overhead:** < 50ms
- **Session load:** < 10ms
- **Concurrent sessions:** 10
- **Downstream servers:** 20
- **Total tools:** 500

---

## Open Questions (Need User Input)

### Q1: Client Priority?
- [ ] CLI (simplest, good for testing)
- [ ] VS Code extension (high value)
- [ ] Claude Desktop (easiest onboarding)

### Q2: Default Fallback Tools?
- Option A: Empty (fail explicitly)
- Option B: Generic safe tools (filesystem.read_file, etc.) ✅ Recommended
- Option C: All tools (defeats purpose)

### Q3: Observability Sink?
- [ ] Stdout (structlog JSON) ✅ v1
- [ ] File (rolling JSONL) - v1.1
- [ ] HTTP (Grafana/Datadog) - v2

### Q4: RAFT Export Default?
- [ ] Opt-in (off by default)
- [ ] Opt-out (on by default) ✅ Recommended (low cost, useful)

---

## Next Steps

**Awaiting User Approval:**

1. **Review this plan** (`.agent/AGENT_A_BACKEND_PLAN.md` for full details)
2. **Answer open questions** (Q1-Q4 above)
3. **Approve implementation** (I'll execute F1-F7 in order)
4. **Notify Agent B** (for R1-R5 tasks)

**Estimated Timeline:** 5 days to production-ready backend

**Files I Will Modify:**
- ✅ `src/ucp/contracts/` (NEW directory)
- ✅ `src/ucp/trace_context.py` (NEW)
- ✅ `src/ucp/observability.py` (NEW)
- ✅ `src/ucp/errors.py` (NEW)
- ✅ `src/ucp/models.py` (add affordance method)
- ✅ `src/ucp/router.py` (add confidence logic)
- ✅ `src/ucp/connection_pool.py` (add retry/timeout)
- ✅ `src/ucp/server.py` (integrate trace context + affordance)
- ✅ `src/ucp/config.py` (add confidence params)

**Files I Will NOT Modify:**
- ❌ Anything in `clients/`, `docs/`, `reports/`, `tests/`
- ❌ README.md, CLAUDE.md, config examples (Agent B handles)

---

**Ready to proceed?** 🚀
