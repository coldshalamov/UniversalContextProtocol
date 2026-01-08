# Universal Context Protocol (UCP): Source of Truth Whitepaper + Developer Plan

**Repo status:** bootstrap stage (documents + synthesis + reports present; `src/` and `tests/` currently empty).

---

## 1. The problem UCP solves

Modern tool-using LLM workflows suffer from **Tool Overload**:

- If you inject *no* tool schemas, the model can’t call tools and quality collapses.
- If you inject *many* tool schemas, context bloat and choice paralysis degrade quality, increase cost/latency, and reduce reliability.

UCP is a **meta–MCP server** that sits between a model and many MCP servers, and serves *only the most relevant* tool schemas **just-in-time** for a given task and conversation state.

Think: *a router + registry + runtime* for tools, where the model always sees a small, high-salience tool menu.

---

## 2. Product thesis

> **“The only MCP you’ll ever have to install.”**

UCP aims to:
1. **Minimize context bloat** (inject top-K tools, not the tool universe).
2. **Increase tool-calling reliability** (make the relevant tools obvious and available).
3. **Continuously improve** via feedback signals from tool invocation outcomes and user interaction patterns.
4. **Act as a stable gateway** (security/sandboxing, container orchestration, observability).

---

## 3. What’s in this repo today

### Core artifacts
- `docs/index.md`: catalog of OCR’d papers + extracted docs.
- `docs/pdfs/*.md`: OCR conversions (ReAct, Toolformer, Gorilla, MetaGPT, MemGPT, MobileAgent, etc.).
- `docs/synthesis_*.md`: distilled lessons on tool selection, context management, agent design, and feedback/eval.
- `docs/ucp_design_plan.md`: a longer “optimal design + build plan” draft.
- `reports/corpus_integrity_report.md`: notes on OCR quality/completeness.
- `reports/codebase_audit_report.md`: current audit (no significant code yet).

### Current gaps
- No implementation yet in `src/`
- No tests yet in `tests/`
- No runnable MCP server stub

This document is the consolidated “north star” to guide implementation and future contributors/agents.

---

## 4. System requirements (engineering constraints)

### Functional
- Accept a model request and return a **tool schema subset** (top-K) appropriate for the request.
- Proxy tool invocations to underlying MCP servers (or to a unified executor).
- Track **which tools were injected**, **which were invoked**, and **whether they succeeded**.

### Non-functional
- **Low latency:** selection must be fast (10–50ms target for local heuristics; 100–300ms if embedding lookup).
- **Deterministic enough to debug:** explain why a tool was included.
- **Safe execution:** isolate tools (containers, permissions, quotas).
- **Composable:** can front existing MCP servers without rewriting them.

---

## 5. Architecture: the simplest correct shape

### 5.1 Components

1. **Tool Registry**
   - Stores tool metadata: name, description, schema, tags, version, cost/latency hints, permissions.
   - Stores embeddings (optional at MVP, highly recommended).

2. **Selector Policy**
   - Input: request context (prompt, recent messages, optional intent block).
   - Output: ranked list of tools to inject (top-K) + rationale.

3. **Gateway / Runtime**
   - Presents selected tool schemas to the model.
   - Routes calls to underlying MCP servers or an internal executor.
   - Pre-warms selected backends when possible.

4. **Telemetry + Feedback Store**
   - Logs injections, invocations, failures, latency, user corrections/retries.
   - Feeds learning/weights later.

### 5.2 Dataflow (high level)

1) User prompt → (optional client wrapper adds minimal “tool affordance” header)  
2) Model asks UCP for tools (or UCP intercepts before model run, depending on integration)  
3) Selector picks top-K tools → returns schemas  
4) Model calls tools → Gateway executes → returns results  
5) Telemetry logs outcomes → updates tool priors / bandit stats

---

## 6. MVP: the easiest algorithm that actually works

**Goal:** reliability today, learning tomorrow.

### MVP selection algorithm (v0.1)
- Maintain a small curated set of “obvious” tools (file IO, shell exec, web fetch, python exec, search).
- For each tool: a **short affordance description** + keywords/tags.
- Selection: **keyword + embedding similarity** (if embeddings available), then return top-K.

### MVP learning algorithm (v0.2)
Add a contextual bandit over the candidate set:
- Candidates: top-N tools by similarity.
- Choose: top-K for injection using Thompson sampling or ε-greedy.
- Reward signals (start conservative):
  - +1 if tool invoked and succeeded
  - -1 if tool invoked and failed
  - small penalty if injected and unused (don’t over-penalize early)

This gives you exploration without needing a complex intent taxonomy.

---

## 7. “Intent blocks” and category evolution (later, not MVP)

Intent categorization is useful, but expensive in complexity. The recommended timeline:

- **v0:** no intent categories; operate on text similarity + tags.
- **v1:** add coarse intent buckets (e.g., coding, retrieval, data-wrangling, writing, vision).
- **v2:** allow emergent categories *provisionally* with pruning/merging based on predictive utility.

**Key constraint:** category survival must be tied to downstream outcomes (tool success + user satisfaction proxies), not just votes.

---

## 8. Interfaces: how users and models interact with UCP

### 8.1 MCP server interface
UCP should expose:
- `list_tools(context)` → returns tool schemas (subset)
- `call_tool(name, args)` → routes to appropriate backend
- `report_outcome(...)` → optional explicit feedback hook

### 8.2 Optional client integrations
- **CLI wrapper:** prepends a tiny “available actions” header to increase salience.
- **VS Code extension:** captures workspace context, files, errors; passes to UCP.
- **Proxy mode:** sits between model and MCP tools to inject schemas automatically.

---

## 9. Dev plan (milestones you can execute)

### Milestone 0 — Repo cleanup (1–2 hours)
- Replace README ellipsis with a crisp description.
- Add `docs/` pointers: “Start here: docs/index.md + this whitepaper.”

### Milestone 1 — Minimal UCP server stub (1–2 days)
Deliverables:
- `src/ucp_server.py`: an MCP-compatible server exposing:
  - `register_tool`, `list_tools`, `call_tool`
- `src/tool_registry.py`: in-memory registry + JSON persistence
- `tests/test_registry.py`

### Milestone 2 — Gateway to one backend “executor” (1–3 days)
Deliverables:
- One tool schema: `execute` (runs shell/python, reads/writes allowed files).
- Internal routing to your docker gateway.
- Safety: allowlist paths, timeouts, CPU/mem quotas.

### Milestone 3 — Tool selection v0 (1–2 days)
Deliverables:
- Simple similarity:
  - keyword scoring + tag match
  - optional embedding lookup
- Return top-K schemas + rationale.

### Milestone 4 — Telemetry (1–2 days)
Deliverables:
- Log injection decisions and tool outcomes:
  - JSONL event log
  - fields: context hash, injected tools, invoked tools, success, latency, error codes

### Milestone 5 — Bandit learning (2–5 days)
Deliverables:
- Thompson sampling stats per tool (and later per tool×intent bucket).
- Exploration controls + decay.

### Milestone 6 — Multi-tool + real MCP proxying (time varies)
Deliverables:
- Proxy multiple MCP servers behind UCP.
- Pre-warm selected backends.
- Concurrency and rate limiting.

---

## 10. How “Claude (or any agent) should navigate these docs”

Start order:
1. `docs/index.md` — what exists
2. `docs/synthesis_tool_selection.md` — selection and orchestration patterns
3. `docs/synthesis_context_management.md` — memory/context patterns
4. `docs/synthesis_feedback_eval.md` — signals and evaluation
5. `docs/ucp_design_plan.md` — longer vision and future system
6. This whitepaper — “what we’re building next” with milestones

---

## 11. Guiding principles (keep the project sane)

- **Salience beats completeness:** a small, obvious tool menu outperforms a giant schema dump.
- **Observability first:** if you can’t explain tool selection, you can’t improve it.
- **Learning comes after logging:** don’t build a fancy learner without clean events.
- **Prefer simple baselines:** if the “smart” router can’t beat top-K similarity, it’s not ready.
- **One hammer first:** start with a single `execute` tool; add specialized tools later.

---

## 12. Definition of done (for the MVP)

UCP MVP is “done” when:
- It can inject a small tool subset reliably (top-K).
- The model uses tools more often *when it should* (measured via invocation rate + fewer retries).
- It logs enough telemetry to improve selection over time.
- It runs safely (path sandboxing, timeouts, resource limits).

---

*End of source-of-truth document.*
