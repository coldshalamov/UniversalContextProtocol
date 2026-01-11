# UCP Development Roadmap

**Created:** 2026-01-10  
**Status:** Active Roadmap  
**Target:** Production-Ready Universal Context Protocol  
**Based on:** `ucp_source_of_truth_whitepaper.md`, synthesis docs, and proven best practices

---

## Executive Summary

The **Universal Context Protocol (UCP)** is an intelligent gateway that solves the "Tool Overload" problem in Agentic AI. By dynamically injecting only the most relevant tool schemas based on conversation context, UCP prevents performance degradation, reduces latency, and minimizes context costs when connecting LLMs to hundreds of tools.

### What We Created

This roadmap consolidates comprehensive planning documents into a single reference:

- **Roadmap Phases** - 16-week timeline broken into 3 phases
- **Critical Path** - Key milestones that cannot be skipped
- **Prioritization Framework** - RICE scoring and MoSCoW method for decision-making
- **Best Practices** - Proven methodologies from Gorilla, LangGraph, and LlamaIndex

### Strategic Approach: Proven Methodology

This plan follows the **"Crawl → Walk → Run"** methodology validated by production deployments:

1. **Crawl (Weeks 1-4):** Stabilize core, validate with real tools, fix critical bugs
2. **Walk (Weeks 5-10):** Ship usable clients, establish feedback loops, gather real usage data
3. **Run (Weeks 11-16):** Advanced features, RAFT fine-tuning, production hardening

**Key Principle:** *"Observability first, learning second"*  
→ We log everything before we optimize anything.

---

## Current State Assessment

| Component | Status | Blocker to Next Phase |
|-----------|--------|----------------------|
| Core Server | 90% ✅ | Test failures, no real MCP validation |
| Router/Tool Zoo | 95% ✅ | No benchmark data |
| Session Mgmt | 85% ✅ | SQLite only, no distributed mode |
| HTTP Transport | 90% ✅ | No load testing |
| Tests | 80% ⚠️ | 1+ failing tests |
| CLI Client | 60% ⚠️ | Not wired to server |
| Desktop App | 30% ❌ | UI stubs only |
| VS Code Ext | 40% ⚠️ | Commands not implemented |
| Deployment | 10% ❌ | No Docker/PyPI/CI |

---

## Roadmap Phases

### PHASE 1: STABILIZE CORE (Weeks 1-4)

**Goal:** Make the backend bulletproof. Validate the core hypothesis with real MCP servers.

#### Week 1: Fix & Validate

**Milestone 1.1: Fix Failing Tests** (2 days)
- Run `pytest tests/ -v --tb=long` and capture all failures
- Fix protocol contract test (`test_tools_list_protocol`, `test_tools_call_proxy`)
- Ensure all 61 tests pass
- Add missing test for `HybridToolZoo.hybrid_search()`
- **Acceptance:** `pytest tests/ -v` shows 61/61 PASSED

**Milestone 1.2: Real MCP Server Integration** (3 days)
- Test with `@modelcontextprotocol/server-filesystem`
  - Add to `ucp_config.yaml`
  - Run `ucp index` and verify tools are indexed
  - Call `filesystem.read_file()` via UCP
- Test with `@modelcontextprotocol/server-github`
  - Verify GitHub tools appear in `ucp search "create issue"`
  - Test routing: "I need to create a GitHub issue" → GitHub tools injected
- Document failure modes in `docs/debugging_playbook.md`
- **Acceptance:** UCP successfully proxies 2+ real MCP servers

**Milestone 1.3: End-to-End Claude Desktop Test** (2 days)
- Configure Claude Desktop to use UCP as sole MCP server
- Test conversation: "List my files" → filesystem tools → "Create a GitHub issue" → GitHub tools
- Verify tool switching works (context shift detection)
- Record session with `ucp dashboard` running
- **Acceptance:** Video demo of Claude using UCP with 2 domains

#### Week 2: Observability & Metrics

**Milestone 1.4: Telemetry Infrastructure** (3 days)
Following "Log Everything" principle:

- Enhance `session.py` to log:
  - `trace_id`, `session_id`, `request_id` (for distributed tracing)
  - Predicted tools (from router)
  - Actually invoked tools
  - Tool success/failure + error messages
  - Latency (router decision time, tool execution time)
- Export logs to JSONL: `logs/ucp_telemetry_{date}.jsonl`
- Add `/metrics` endpoint to `http_server.py` (Prometheus format):
  - `ucp_router_latency_ms`
  - `ucp_tool_invocations_total{tool_name, success}`
  - `ucp_context_shift_detected_total`
- **Acceptance:** Every tool call generates structured telemetry

**Milestone 1.5: Baseline Benchmarks** (2 days)
Run evaluation harness with real LLM (not simulated)

- Update `clients/harness/run_eval.py`:
  - Replace simulated LLM with actual API call (use LiteLLM for multi-provider)
  - Add 10 diverse tasks to `tasks.json` (coding, email, calendar, search)
- Run baseline: All tools exposed (top_k=100)
- Run UCP: Filtered tools (top_k=5)
- Measure:
  - **Recall:** Did expected tool appear in top-K?
  - **Precision:** How many irrelevant tools were shown?
  - **Latency:** Time to first token
  - **Cost:** Input tokens consumed
- Generate `reports/baseline_benchmark_v0.1.json`
- **Acceptance:** Quantitative proof that UCP reduces context bloat by 80%+

#### Week 3: Error Handling & Resilience

**Milestone 1.6: Failure Mode Testing** (3 days)
From "Error Handling as Feedback" principle:

- Test scenarios:
  - Downstream MCP server crashes mid-conversation
  - Downstream server returns malformed JSON
  - Downstream server times out (>30s)
  - Router fails to find any relevant tools
  - Tool call with invalid arguments
- Implement graceful degradation:
  - If router fails → fallback to keyword search
  - If tool call fails → inject error into context for self-correction
  - If server crashes → mark as unhealthy, retry with backoff
- Add circuit breaker pattern to `connection_pool.py`
- **Acceptance:** UCP handles 5 failure modes without crashing

**Milestone 1.7: Documentation Update** (2 days)
- Update `README.md` with real benchmark results
- Add "Troubleshooting" section with common errors
- Create `docs/production_deployment.md`:
  - Resource requirements (RAM for ChromaDB, CPU for embeddings)
  - Security considerations (sandboxing tool execution)
  - Scaling strategies (Redis session backend)
- **Acceptance:** New user can deploy UCP in <30 minutes

#### Week 4: Distribution & CI

**Milestone 1.8: PyPI Release** (2 days)
- Add `MANIFEST.in`, `setup.py` (if needed for legacy compat)
- Test installation in clean virtualenv:
  ```bash
  pip install ucp==0.1.0a1
  ucp init-config
  ucp serve
  ```
- Publish to TestPyPI first
- Publish to PyPI: `ucp==0.1.0-alpha1`
- **Acceptance:** `pip install ucp` works globally

**Milestone 1.9: Docker Image** (2 days)
- Create `Dockerfile`:
  - Base: `python:3.11-slim`
  - Install dependencies + sentence-transformers model
  - ENTRYPOINT: `ucp serve`
  - VOLUME: `/data` (for ChromaDB persistence)
- Create `docker-compose.yml` with example downstream servers
- Push to Docker Hub: `ucpproject/ucp:0.1.0-alpha1`
- **Acceptance:** `docker run ucpproject/ucp` starts UCP server

**Milestone 1.10: GitHub Actions CI** (1 day)
- `.github/workflows/test.yml`:
  - Run pytest on every PR
  - Run linting (ruff, mypy)
  - Upload coverage to Codecov
- `.github/workflows/release.yml`:
  - Trigger on tag push (`v*`)
  - Build Docker image
  - Publish to PyPI
- **Acceptance:** Green checkmark on all PRs

**OUTPUT: Alpha release, 90%+ test coverage, real MCP validation**

---

### PHASE 2: SHIP CLIENTS (Weeks 5-10)

**Goal:** Make UCP usable by developers. Establish feedback loops.

#### Week 5-6: CLI Client

**Milestone 2.1: Wire CLI to UCP** (4 days)
- Update `clients/cli/ucp_chat/ucp_client.py`:
  - Connect to UCP HTTP server (not direct LLM provider)
  - Send messages via `/context/update`
  - Fetch tools via `/mcp/tools/list`
  - Execute tools via `/mcp/tools/call`
- Add streaming support (SSE) for real-time responses
- Test with multiple providers (OpenAI, Anthropic, Groq)
- **Acceptance:** `ucp-chat` CLI works end-to-end with UCP backend

**Milestone 2.2: CLI Polish** (2 days)
- Add rich terminal UI (use `rich` library):
  - Syntax highlighting for code blocks
  - Tool call visualization (show which tools are active)
  - Progress indicators for long-running tools
- Add `--debug` flag to show router decisions
- Package as standalone binary with PyInstaller
- **Acceptance:** Professional CLI experience

#### Week 7-8: VS Code Extension ⭐ CRITICAL PATH

**Milestone 2.3: Implement Core Commands** (5 days)
Priority: `ucp.startChat`, `ucp.showTools`, `ucp.predictTools`

- `src/extension.ts`:
  - Implement `ucp.startChat`: Open webview panel with chat UI
  - Implement `ucp.showTools`: Show predicted tools in sidebar tree view
  - Implement `ucp.predictTools`: Analyze current file + selection, call UCP router
- `src/ucpClient.ts`:
  - HTTP client for UCP server
  - WebSocket connection for streaming
- `src/contextCapture.ts`:
  - Capture workspace context:
    - Active file content
    - Compiler errors (from Problems panel)
    - Git status
    - Open files
  - Send to UCP as "ambient context"
- **Acceptance:** Extension connects to UCP and shows predicted tools

**Milestone 2.4: Webview Chat UI** (3 days)
- Build React chat interface in `src/webview/`:
  - Message list with markdown rendering
  - Input box with autocomplete for tool names
  - Tool execution status indicators
- Integrate with VS Code theme (light/dark mode)
- Add "Copy to Clipboard" for code blocks
- **Acceptance:** Chat UI feels native to VS Code

**Milestone 2.5: Package & Publish** (1 day)
- Test in VS Code Insiders
- Create demo GIF for README
- Publish to VS Code Marketplace (or private registry)
- **Acceptance:** Extension installable via `.vsix`

#### Week 9-10: Desktop App

**Milestone 2.6: Desktop UI Implementation** (6 days)
- `clients/desktop/src/renderer/`:
  - Build chat interface (similar to VS Code webview)
  - Add settings panel for UCP server URL, API keys
  - Add "Tool Zoo Browser" to explore all indexed tools
  - Add "Session History" view
- `clients/desktop/src/main/`:
  - Implement IPC handlers for UCP communication
  - Add auto-updater (electron-updater)
  - Add system tray integration
- **Acceptance:** Desktop app is feature-complete

**Milestone 2.7: Cross-Platform Builds** (2 days)
- Build for Windows (NSIS installer)
- Build for macOS (DMG)
- Build for Linux (AppImage + deb)
- Upload to GitHub Releases
- **Acceptance:** Installers available for all platforms

**OUTPUT: 3 usable clients, VS Code extension on Marketplace**

---

### PHASE 3: ADVANCED FEATURES (Weeks 11-16)

**Goal:** RAFT fine-tuning, production hardening, community launch.

#### Week 11-12: RAFT Fine-Tuning

**Milestone 3.1: Training Data Collection** (3 days)
From "RAFT Dataset Construction" principle:

- Collect 1000+ real UCP sessions from telemetry logs
- Filter for "successful" sessions (no user corrections)
- Export via `router.export_training_data()`:
  - Format: `{query, all_tools, relevant_tools, distractor_tools}`
- Add synthetic negatives (queries where NO tools are relevant)
- **Acceptance:** `data/raft_training_v1.jsonl` with 1000+ examples

**Milestone 3.2: Fine-Tune Router Model** (4 days)
- Use Gorilla's RAFT recipe:
  - Base model: `meta-llama/Llama-3.2-3B-Instruct`
  - LoRA fine-tuning (PEFT library)
  - Training objective: Predict top-K tools given query + all tools
- Train on GPU (use Modal/RunPod for compute)
- Evaluate on held-out test set:
  - Recall@5, Recall@10
  - Compare to baseline (sentence-transformers semantic search)
- If RAFT model beats baseline by 10%+ → deploy
- **Acceptance:** Fine-tuned model improves recall by 10%+

**Milestone 3.3: Deploy RAFT Model** (2 days)
- Add `router_mode: raft` to config
- Load fine-tuned model in `router.py`
- A/B test: 50% traffic to RAFT, 50% to semantic search
- Monitor metrics for 1 week
- **Acceptance:** RAFT mode available in production

#### Week 13-14: Production Hardening

**Milestone 3.4: Redis Session Backend** (3 days)
For distributed deployments

- Implement `RedisSessionManager` in `session.py`
- Add config option: `session.backend: redis`
- Test with multiple UCP instances sharing Redis
- Add session migration script (SQLite → Redis)
- **Acceptance:** UCP scales horizontally with Redis

**Milestone 3.5: Security Hardening** (3 days)
- Add authentication to HTTP server (API keys)
- Implement tool execution sandboxing:
  - Run tools in Docker containers (via `connection_pool.py`)
  - Set resource limits (CPU, memory, timeout)
  - Allowlist file paths for filesystem tools
- Add rate limiting (per session, per tool)
- Security audit with `bandit`, `safety`
- **Acceptance:** UCP passes security checklist

**Milestone 3.6: Performance Optimization** (2 days)
- Profile embedding generation (use GPU if available)
- Cache frequent queries in Redis
- Optimize ChromaDB queries (batch embeddings)
- Add connection pooling for downstream servers
- Target: <100ms router latency (p95)
- **Acceptance:** Latency reduced by 50%

#### Week 15-16: Community Launch

**Milestone 3.7: Documentation Overhaul** (3 days)
- Create video tutorial (15 min):
  - "Getting Started with UCP"
  - Demo with Claude Desktop + GitHub/Slack/Gmail
- Write blog post: "Solving Tool Overload with UCP"
- Add interactive examples to README
- Create `CONTRIBUTING.md` with dev setup guide
- **Acceptance:** New contributor can submit PR in <1 hour

**Milestone 3.8: v1.0 Release** (2 days)
- Tag `v1.0.0` in Git
- Publish to PyPI: `ucp==1.0.0`
- Update Docker image: `ucpproject/ucp:1.0.0`
- Publish VS Code extension to Marketplace
- Post on:
  - Hacker News
  - r/LocalLLaMA
  - LangChain Discord
  - Anthropic Discord
- **Acceptance:** 100+ GitHub stars in first week

**Milestone 3.9: Community Tool Zoo** (3 days)
Long-term vision from roadmap edge concepts:

- Create `community-tools/` repo:
  - Curated tool definitions (tags, descriptions)
  - Pre-computed embeddings for common tools
  - "Verified" badge for well-tested tools
- Add `ucp import-community-tools` command
- Seed with 50+ popular MCP servers
- **Acceptance:** Users can bootstrap UCP with community tools

**OUTPUT: v1.0 production release, 500+ GitHub stars**

---

## Critical Path

If you only do 3 things, do these:

1. **Week 1-2:** Fix tests + validate with real MCP servers
   - **Blocker:** Everything else depends on this
   - Workflow: `.agent/workflows/start-phase1.md`

2. **Week 7-8:** Ship VS Code extension
   - **Highest Impact:** 80 reach × 9 impact = 720 value points
   - **Largest Audience:** Millions of VS Code users

3. **Week 11-12:** RAFT fine-tuning pipeline
   - **Core Innovation:** What makes UCP unique
   - **Fallback:** Keep semantic search if RAFT fails

**If timeline slips, CUT:**
- Desktop app (Week 9-10) → defer to v1.1
- Community Tool Zoo (Week 16) → defer to v1.1

**NEVER CUT:**
- Test fixes (Week 1)
- VS Code extension (Week 7-8)
- RAFT pipeline (Week 11-12)

---

## Prioritization Framework

### Feature Prioritization (RICE Score)

Based on the **RICE Score** (Reach × Impact × Confidence / Effort):

| Feature | Reach | Impact | Confidence | Effort | RICE | Priority |
|---------|-------|--------|------------|--------|------|----------|
| **Fix Failing Tests** | 100 | 10 | 100% | 2d | 500 | 🔴 P0 |
| **Real MCP Validation** | 100 | 10 | 90% | 3d | 300 | 🔴 P0 |
| **VS Code Extension** | 80 | 9 | 80% | 9d | 64 | 🔴 P0 |
| **Telemetry/Logging** | 100 | 8 | 100% | 3d | 267 | 🟠 P1 |
| **RAFT Fine-Tuning** | 60 | 10 | 70% | 7d | 60 | 🟠 P1 |
| **PyPI Release** | 90 | 7 | 100% | 2d | 315 | 🟠 P1 |
| **CLI Client** | 40 | 6 | 90% | 6d | 36 | 🟡 P2 |
| **Desktop App** | 30 | 6 | 80% | 8d | 18 | 🟡 P2 |
| **Redis Backend** | 20 | 5 | 70% | 3d | 23 | 🟢 P3 |
| **GPU Acceleration** | 10 | 4 | 60% | 5d | 5 | 🟢 P3 |
| **Community Tool Zoo** | 50 | 5 | 50% | 3d | 42 | 🟢 P3 |

**Legend:**
- **Reach:** % of users affected (0-100)
- **Impact:** Value to users (1-10)
- **Confidence:** Certainty of success (0-100%)
- **Effort:** Days of work
- **RICE:** (Reach × Impact × Confidence) / Effort

### MoSCoW Prioritization

**MUST Have (v1.0 Blockers)**
1. ✅ All tests passing
2. ✅ Real MCP server integration (2+ servers)
3. ✅ VS Code extension with core features
4. ✅ Telemetry infrastructure
5. ✅ PyPI + Docker distribution
6. ✅ Benchmark showing 80%+ context reduction

**SHOULD Have (v1.0 Goals)**
1. ✅ RAFT fine-tuning pipeline
2. ✅ CLI client
3. ✅ GitHub Actions CI
4. ✅ Security hardening
5. ✅ Performance optimization (<100ms latency)

**COULD Have (v1.1 Candidates)**
1. 🔄 Desktop app
2. 🔄 Redis session backend
3. 🔄 GPU acceleration
4. 🔄 Community Tool Zoo
5. 🔄 Advanced analytics dashboard

**WON'T Have (Out of Scope)**
1. ❌ Mobile apps (iOS/Android)
2. ❌ Browser extension
3. ❌ SaaS hosted service
4. ❌ Enterprise SSO integration
5. ❌ Multi-tenant architecture

### Time-Boxed Decision Tree

```
IF timeline slips by 2+ weeks:
  ├─ CUT: Desktop app → defer to v1.1
  ├─ CUT: Community Tool Zoo → defer to v1.1
  └─ KEEP: VS Code extension (critical path)

IF timeline slips by 4+ weeks:
  ├─ CUT: RAFT fine-tuning → ship with semantic search only
  ├─ CUT: CLI client → defer to v1.1
  └─ KEEP: Core backend + VS Code extension

IF critical bug discovered:
  ├─ PAUSE: All feature work
  ├─ FIX: Bug immediately
  └─ REASSESS: Timeline after fix

IF RAFT doesn't improve baseline:
  ├─ SHIP: v1.0 with semantic search
  ├─ LABEL: "RAFT mode" as experimental
  └─ ITERATE: Collect more training data for v1.1
```

---

## Success Metrics (KPIs)

Track these throughout development:

| Metric | Baseline | Target (v1.0) |
|--------|----------|---------------|
| **Recall@5** (expected tool in top-5) | 60% | 90%+ |
| **Context Reduction** (tokens saved) | 0% | 80%+ |
| **Router Latency** (p95) | N/A | <100ms |
| **Test Coverage** | 80% | 90%+ |
| **GitHub Stars** | 0 | 500+ |
| **Active Users** (monthly) | 0 | 100+ |

---

## Proven Methodologies Applied

### From Gorilla (Tool Selection)
✅ **RAFT Fine-Tuning:** Week 11-12 pipeline for training router on real usage  
✅ **AST Evaluation:** Semantic tool call validation (not exact string match)  
✅ **Negative Examples:** Train model to reject irrelevant tools

### From LangGraph (State Management)
✅ **Cyclic Graph Architecture:** Already implemented in `graph.py`  
✅ **Checkpointing:** Session persistence for resumable workflows  
✅ **Human-in-the-Loop:** Interrupt-resume pattern for confirmations

### From LlamaIndex (Context Retrieval)
✅ **Vector Indexing:** ChromaDB + sentence-transformers (already implemented)  
✅ **Hybrid Search:** Semantic + keyword matching (already implemented)  
✅ **Metadata Filtering:** Domain-based tool filtering

### From Feedback/Eval Synthesis
✅ **Log Everything:** Structured telemetry (Week 2, Milestone 1.4)  
✅ **Self-Correction:** Inject errors back into context (already in `server.py`)  
✅ **Offline RLHF:** Export logs for RAFT training (Week 11)

---

## Timeline Flexibility

### Aggressive (8 weeks):
Focus on VS Code extension only. Skip CLI, Desktop, RAFT.
- Week 1-2: Core validation
- Week 3-4: PyPI + Docker
- Week 5-8: VS Code extension

### Standard (16 weeks):
Full roadmap as outlined above.

### Conservative (20 weeks):
Add 4-week buffer for unexpected issues, community feedback iteration

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RAFT doesn't improve over baseline | Medium | High | Keep semantic search as fallback |
| ChromaDB performance issues at scale | Medium | Medium | Add Redis caching layer |
| Downstream MCP servers are unstable | High | Medium | Circuit breaker + health checks |
| Users don't adopt (low traction) | Medium | High | Focus on VS Code ext (largest audience) |
| Security vulnerability in tool execution | Low | Critical | Sandboxing + security audit |

---

## Launch Readiness Checklist

### v0.1-alpha (Week 4)
- [ ] All tests pass
- [ ] 2+ real MCP servers tested
- [ ] PyPI package published
- [ ] Docker image available
- [ ] Basic documentation

### v0.5-beta (Week 10)
- [ ] VS Code extension on Marketplace
- [ ] CLI client functional
- [ ] Telemetry infrastructure live
- [ ] Benchmark results published
- [ ] 10+ beta users

### v1.0-production (Week 16)
- [ ] RAFT fine-tuning complete
- [ ] Security audit passed
- [ ] Performance <100ms (p95)
- [ ] 90%+ test coverage
- [ ] Video tutorial published
- [ ] 100+ GitHub stars

---

## Definition of Done (v1.0)

UCP v1.0 is complete when:

- [x] Core server passes all tests with 3+ real MCP servers
- [x] Published to PyPI and Docker Hub
- [x] VS Code extension available on Marketplace
- [x] Benchmark shows 80%+ context reduction with 90%+ recall
- [x] RAFT fine-tuning pipeline is documented and reproducible
- [x] 100+ GitHub stars and 10+ community contributors
- [x] Production deployment guide exists

---

## Next Immediate Action

**START HERE:** Milestone 1.1 - Fix Failing Tests (2 days)

```bash
# Open the workflow
code .agent/workflows/start-phase1.md

# Run the first test
pytest tests/ -v --tb=long
```

**Then:** Follow the workflow step-by-step. Each milestone has clear acceptance criteria.

---

**Questions?** See PRIORITIZATION_MATRIX.md for decision-making guidance.  
**Stuck?** See `docs/debugging_playbook.md` for troubleshooting.  
**Need context?** See `ucp_source_of_truth_whitepaper.md` for the vision.

---

*This roadmap is a living document. Update weekly as you learn from real usage.*

**Good luck! 🚀**
