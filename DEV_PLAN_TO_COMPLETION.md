# UCP Development Plan to v1.0 Completion

**Created:** 2026-01-09  
**Status:** Active Roadmap  
**Target:** Production-Ready Universal Context Protocol  
**Based on:** `ucp_source_of_truth_whitepaper.md`, synthesis docs, and proven best practices

---

## 🎯 **Strategic Approach: Proven Methodology**

This plan follows the **"Crawl → Walk → Run"** methodology validated by Gorilla, LangGraph, and production MCP deployments:

1. **Crawl (Weeks 1-4):** Stabilize core, validate with real tools, fix critical bugs
2. **Walk (Weeks 5-10):** Ship usable clients, establish feedback loops, gather real usage data
3. **Run (Weeks 11-16):** Advanced features, RAFT fine-tuning, production hardening

**Key Principle:** *"Observability first, learning second"* (from synthesis_feedback_eval.md)  
→ We log everything before we optimize anything.

---

## 📊 **Current State Assessment**

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

## 🏗️ **PHASE 1: STABILIZE CORE (Weeks 1-4)**

**Goal:** Make the backend bulletproof. Validate the core hypothesis with real MCP servers.

### **Week 1: Fix & Validate**

#### **Milestone 1.1: Fix Failing Tests** (2 days)
- [ ] Run `pytest tests/ -v --tb=long` and capture all failures
- [ ] Fix protocol contract test (`test_tools_list_protocol`, `test_tools_call_proxy`)
- [ ] Ensure all 61 tests pass
- [ ] Add missing test for `HybridToolZoo.hybrid_search()`
- **Acceptance:** `pytest tests/ -v` shows 61/61 PASSED

#### **Milestone 1.2: Real MCP Server Integration** (3 days)
- [ ] Test with `@modelcontextprotocol/server-filesystem`
  - Add to `ucp_config.yaml`
  - Run `ucp index` and verify tools are indexed
  - Call `filesystem.read_file()` via UCP
- [ ] Test with `@modelcontextprotocol/server-github`
  - Verify GitHub tools appear in `ucp search "create issue"`
  - Test routing: "I need to create a GitHub issue" → GitHub tools injected
- [ ] Document failure modes in `docs/debugging_playbook.md`
- **Acceptance:** UCP successfully proxies 2+ real MCP servers

#### **Milestone 1.3: End-to-End Claude Desktop Test** (2 days)
- [ ] Configure Claude Desktop to use UCP as sole MCP server
- [ ] Test conversation: "List my files" → filesystem tools → "Create a GitHub issue" → GitHub tools
- [ ] Verify tool switching works (context shift detection)
- [ ] Record session with `ucp dashboard` running
- **Acceptance:** Video demo of Claude using UCP with 2 domains

---

### **Week 2: Observability & Metrics**

#### **Milestone 1.4: Telemetry Infrastructure** (3 days)
Following `synthesis_feedback_eval.md` → "Log Everything"

- [ ] Enhance `session.py` to log:
  - `trace_id`, `session_id`, `request_id` (for distributed tracing)
  - Predicted tools (from router)
  - Actually invoked tools
  - Tool success/failure + error messages
  - Latency (router decision time, tool execution time)
- [ ] Export logs to JSONL: `logs/ucp_telemetry_{date}.jsonl`
- [ ] Add `/metrics` endpoint to `http_server.py` (Prometheus format):
  - `ucp_router_latency_ms`
  - `ucp_tool_invocations_total{tool_name, success}`
  - `ucp_context_shift_detected_total`
- **Acceptance:** Every tool call generates structured telemetry

#### **Milestone 1.5: Baseline Benchmarks** (2 days)
Run evaluation harness with real LLM (not simulated)

- [ ] Update `clients/harness/run_eval.py`:
  - Replace simulated LLM with actual API call (use LiteLLM for multi-provider)
  - Add 10 diverse tasks to `tasks.json` (coding, email, calendar, search)
- [ ] Run baseline: All tools exposed (top_k=100)
- [ ] Run UCP: Filtered tools (top_k=5)
- [ ] Measure:
  - **Recall:** Did expected tool appear in top-K?
  - **Precision:** How many irrelevant tools were shown?
  - **Latency:** Time to first token
  - **Cost:** Input tokens consumed
- [ ] Generate `reports/baseline_benchmark_v0.1.json`
- **Acceptance:** Quantitative proof that UCP reduces context bloat by 80%+

---

### **Week 3: Error Handling & Resilience**

#### **Milestone 1.6: Failure Mode Testing** (3 days)
From `synthesis_agent_design.md` → "Error Handling as Feedback"

- [ ] Test scenarios:
  - Downstream MCP server crashes mid-conversation
  - Downstream server returns malformed JSON
  - Downstream server times out (>30s)
  - Router fails to find any relevant tools
  - Tool call with invalid arguments
- [ ] Implement graceful degradation:
  - If router fails → fallback to keyword search
  - If tool call fails → inject error into context for self-correction
  - If server crashes → mark as unhealthy, retry with backoff
- [ ] Add circuit breaker pattern to `connection_pool.py`
- **Acceptance:** UCP handles 5 failure modes without crashing

#### **Milestone 1.7: Documentation Update** (2 days)
- [ ] Update `README.md` with real benchmark results
- [ ] Add "Troubleshooting" section with common errors
- [ ] Create `docs/production_deployment.md`:
  - Resource requirements (RAM for ChromaDB, CPU for embeddings)
  - Security considerations (sandboxing tool execution)
  - Scaling strategies (Redis session backend)
- **Acceptance:** New user can deploy UCP in <30 minutes

---

### **Week 4: Distribution & CI**

#### **Milestone 1.8: PyPI Release** (2 days)
- [ ] Add `MANIFEST.in`, `setup.py` (if needed for legacy compat)
- [ ] Test installation in clean virtualenv:
  ```bash
  pip install ucp==0.1.0a1
  ucp init-config
  ucp serve
  ```
- [ ] Publish to TestPyPI first
- [ ] Publish to PyPI: `ucp==0.1.0-alpha1`
- **Acceptance:** `pip install ucp` works globally

#### **Milestone 1.9: Docker Image** (2 days)
- [ ] Create `Dockerfile`:
  - Base: `python:3.11-slim`
  - Install dependencies + sentence-transformers model
  - ENTRYPOINT: `ucp serve`
  - VOLUME: `/data` (for ChromaDB persistence)
- [ ] Create `docker-compose.yml` with example downstream servers
- [ ] Push to Docker Hub: `ucpproject/ucp:0.1.0-alpha1`
- **Acceptance:** `docker run ucpproject/ucp` starts UCP server

#### **Milestone 1.10: GitHub Actions CI** (1 day)
- [ ] `.github/workflows/test.yml`:
  - Run pytest on every PR
  - Run linting (ruff, mypy)
  - Upload coverage to Codecov
- [ ] `.github/workflows/release.yml`:
  - Trigger on tag push (`v*`)
  - Build Docker image
  - Publish to PyPI
- **Acceptance:** Green checkmark on all PRs

---

## 🚶 **PHASE 2: SHIP CLIENTS (Weeks 5-10)**

**Goal:** Make UCP usable by developers. Establish feedback loops.

### **Week 5-6: CLI Client**

#### **Milestone 2.1: Wire CLI to UCP** (4 days)
- [ ] Update `clients/cli/ucp_chat/ucp_client.py`:
  - Connect to UCP HTTP server (not direct LLM provider)
  - Send messages via `/context/update`
  - Fetch tools via `/mcp/tools/list`
  - Execute tools via `/mcp/tools/call`
- [ ] Add streaming support (SSE) for real-time responses
- [ ] Test with multiple providers (OpenAI, Anthropic, Groq)
- **Acceptance:** `ucp-chat` CLI works end-to-end with UCP backend

#### **Milestone 2.2: CLI Polish** (2 days)
- [ ] Add rich terminal UI (use `rich` library):
  - Syntax highlighting for code blocks
  - Tool call visualization (show which tools are active)
  - Progress indicators for long-running tools
- [ ] Add `--debug` flag to show router decisions
- [ ] Package as standalone binary with PyInstaller
- **Acceptance:** Professional CLI experience

---

### **Week 7-8: VS Code Extension**

#### **Milestone 2.3: Implement Core Commands** (5 days)
Priority: `ucp.startChat`, `ucp.showTools`, `ucp.predictTools`

- [ ] `src/extension.ts`:
  - Implement `ucp.startChat`: Open webview panel with chat UI
  - Implement `ucp.showTools`: Show predicted tools in sidebar tree view
  - Implement `ucp.predictTools`: Analyze current file + selection, call UCP router
- [ ] `src/ucpClient.ts`:
  - HTTP client for UCP server
  - WebSocket connection for streaming
- [ ] `src/contextCapture.ts`:
  - Capture workspace context:
    - Active file content
    - Compiler errors (from Problems panel)
    - Git status
    - Open files
  - Send to UCP as "ambient context"
- **Acceptance:** Extension connects to UCP and shows predicted tools

#### **Milestone 2.4: Webview Chat UI** (3 days)
- [ ] Build React chat interface in `src/webview/`:
  - Message list with markdown rendering
  - Input box with autocomplete for tool names
  - Tool execution status indicators
- [ ] Integrate with VS Code theme (light/dark mode)
- [ ] Add "Copy to Clipboard" for code blocks
- **Acceptance:** Chat UI feels native to VS Code

#### **Milestone 2.5: Package & Publish** (1 day)
- [ ] Test in VS Code Insiders
- [ ] Create demo GIF for README
- [ ] Publish to VS Code Marketplace (or private registry)
- **Acceptance:** Extension installable via `.vsix`

---

### **Week 9-10: Desktop App**

#### **Milestone 2.6: Desktop UI Implementation** (6 days)
- [ ] `clients/desktop/src/renderer/`:
  - Build chat interface (similar to VS Code webview)
  - Add settings panel for UCP server URL, API keys
  - Add "Tool Zoo Browser" to explore all indexed tools
  - Add "Session History" view
- [ ] `clients/desktop/src/main/`:
  - Implement IPC handlers for UCP communication
  - Add auto-updater (electron-updater)
  - Add system tray integration
- **Acceptance:** Desktop app is feature-complete

#### **Milestone 2.7: Cross-Platform Builds** (2 days)
- [ ] Build for Windows (NSIS installer)
- [ ] Build for macOS (DMG)
- [ ] Build for Linux (AppImage + deb)
- [ ] Upload to GitHub Releases
- **Acceptance:** Installers available for all platforms

---

## 🏃 **PHASE 3: ADVANCED FEATURES (Weeks 11-16)**

**Goal:** RAFT fine-tuning, production hardening, community launch.

### **Week 11-12: RAFT Fine-Tuning Pipeline**

#### **Milestone 3.1: Training Data Collection** (3 days)
From `synthesis_tool_selection.md` → "RAFT Dataset Construction"

- [ ] Collect 1000+ real UCP sessions from telemetry logs
- [ ] Filter for "successful" sessions (no user corrections)
- [ ] Export via `router.export_training_data()`:
  - Format: `{query, all_tools, relevant_tools, distractor_tools}`
- [ ] Add synthetic negatives (queries where NO tools are relevant)
- **Acceptance:** `data/raft_training_v1.jsonl` with 1000+ examples

#### **Milestone 3.2: Fine-Tune Router Model** (4 days)
- [ ] Use Gorilla's RAFT recipe:
  - Base model: `meta-llama/Llama-3.2-3B-Instruct`
  - LoRA fine-tuning (PEFT library)
  - Training objective: Predict top-K tools given query + all tools
- [ ] Train on GPU (use Modal/RunPod for compute)
- [ ] Evaluate on held-out test set:
  - Recall@5, Recall@10
  - Compare to baseline (sentence-transformers semantic search)
- [ ] If RAFT model beats baseline by 10%+ → deploy
- **Acceptance:** Fine-tuned model improves recall by 10%+

#### **Milestone 3.3: Deploy RAFT Model** (2 days)
- [ ] Add `router_mode: raft` to config
- [ ] Load fine-tuned model in `router.py`
- [ ] A/B test: 50% traffic to RAFT, 50% to semantic search
- [ ] Monitor metrics for 1 week
- **Acceptance:** RAFT mode available in production

---

### **Week 13-14: Production Hardening**

#### **Milestone 3.4: Redis Session Backend** (3 days)
For distributed deployments

- [ ] Implement `RedisSessionManager` in `session.py`
- [ ] Add config option: `session.backend: redis`
- [ ] Test with multiple UCP instances sharing Redis
- [ ] Add session migration script (SQLite → Redis)
- **Acceptance:** UCP scales horizontally with Redis

#### **Milestone 3.5: Security Hardening** (3 days)
- [ ] Add authentication to HTTP server (API keys)
- [ ] Implement tool execution sandboxing:
  - Run tools in Docker containers (via `connection_pool.py`)
  - Set resource limits (CPU, memory, timeout)
  - Allowlist file paths for filesystem tools
- [ ] Add rate limiting (per session, per tool)
- [ ] Security audit with `bandit`, `safety`
- **Acceptance:** UCP passes security checklist

#### **Milestone 3.6: Performance Optimization** (2 days)
- [ ] Profile embedding generation (use GPU if available)
- [ ] Cache frequent queries in Redis
- [ ] Optimize ChromaDB queries (batch embeddings)
- [ ] Add connection pooling for downstream servers
- [ ] Target: <100ms router latency (p95)
- **Acceptance:** Latency reduced by 50%

---

### **Week 15-16: Community Launch**

#### **Milestone 3.7: Documentation Overhaul** (3 days)
- [ ] Create video tutorial (15 min):
  - "Getting Started with UCP"
  - Demo with Claude Desktop + GitHub/Slack/Gmail
- [ ] Write blog post: "Solving Tool Overload with UCP"
- [ ] Add interactive examples to README
- [ ] Create `CONTRIBUTING.md` with dev setup guide
- **Acceptance:** New contributor can submit PR in <1 hour

#### **Milestone 3.8: v1.0 Release** (2 days)
- [ ] Tag `v1.0.0` in Git
- [ ] Publish to PyPI: `ucp==1.0.0`
- [ ] Update Docker image: `ucpproject/ucp:1.0.0`
- [ ] Publish VS Code extension to Marketplace
- [ ] Post on:
  - Hacker News
  - r/LocalLLaMA
  - LangChain Discord
  - Anthropic Discord
- **Acceptance:** 100+ GitHub stars in first week

#### **Milestone 3.9: Community Tool Zoo** (3 days)
Long-term vision from `roadmap_edge.md`

- [ ] Create `community-tools/` repo:
  - Curated tool definitions (tags, descriptions)
  - Pre-computed embeddings for common tools
  - "Verified" badge for well-tested tools
- [ ] Add `ucp import-community-tools` command
- [ ] Seed with 50+ popular MCP servers
- **Acceptance:** Users can bootstrap UCP with community tools

---

## 📈 **Success Metrics (KPIs)**

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

## 🛠️ **Development Best Practices**

### **From Synthesis Docs:**

1. **Two-Stage Dispatch** (`synthesis_tool_selection.md`):
   - Stage 1: Domain detection (fast, keyword-based)
   - Stage 2: Semantic search within domain
   - ✅ Already implemented in `router.py`

2. **Cyclic Graph Architecture** (`synthesis_agent_design.md`):
   - Use LangGraph for state machine
   - ✅ Already implemented in `graph.py`

3. **Log Everything** (`synthesis_feedback_eval.md`):
   - Every interaction → structured log
   - ✅ Implement in Phase 1, Week 2

4. **AST Matching for Eval** (`synthesis_feedback_eval.md`):
   - Don't use exact string match for tool calls
   - ⚠️ TODO: Add to evaluation harness

5. **Self-Correction Loop** (`synthesis_feedback_eval.md`):
   - Inject tool errors back into context
   - ✅ Already implemented in `server.py`

---

## 🚨 **Risk Mitigation**

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| RAFT doesn't improve over baseline | Medium | High | Keep semantic search as fallback |
| ChromaDB performance issues at scale | Medium | Medium | Add Redis caching layer |
| Downstream MCP servers are unstable | High | Medium | Circuit breaker + health checks |
| Users don't adopt (low traction) | Medium | High | Focus on VS Code ext (largest audience) |
| Security vulnerability in tool execution | Low | Critical | Sandboxing + security audit |

---

## 📅 **Timeline Summary**

```
Week 1-4:   PHASE 1 - Stabilize Core ✅
Week 5-10:  PHASE 2 - Ship Clients 🚀
Week 11-16: PHASE 3 - Advanced Features 🏆

Total: 16 weeks to v1.0
```

**Critical Path:** Weeks 1-2 (fix tests + real MCP validation) → Week 7-8 (VS Code ext)

---

## 🎓 **Learning from Best Practices**

This plan is based on proven methodologies:

- **Gorilla:** RAFT fine-tuning, AST evaluation, BFCL benchmarks
- **LangGraph:** Cyclic graphs, checkpointing, human-in-the-loop
- **LlamaIndex:** Vector indexing, metadata filtering, ingestion pipelines
- **Production MCP Servers:** Error handling, transport abstraction, observability

**Key Insight:** *"Salience beats completeness"* (from whitepaper)  
→ We ship a working 5-tool selector before a perfect 100-tool selector.

---

## ✅ **Definition of Done (v1.0)**

UCP v1.0 is complete when:

- [x] Core server passes all tests with 3+ real MCP servers
- [x] Published to PyPI and Docker Hub
- [x] VS Code extension available on Marketplace
- [x] Desktop app has installers for Win/Mac/Linux
- [x] Benchmark shows 80%+ context reduction with 90%+ recall
- [x] RAFT fine-tuning pipeline is documented and reproducible
- [x] 100+ GitHub stars and 10+ community contributors
- [x] Production deployment guide exists

---

**Next Action:** Start with **Milestone 1.1** (Fix Failing Tests) → 2 days

**Owner:** Assign milestones to agents/developers based on expertise  
**Review Cadence:** Weekly sync to assess progress and adjust timeline

---

*This plan is a living document. Update as we learn from real-world usage.*
