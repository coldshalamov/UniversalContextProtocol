<!--
ARCHIVED DOCUMENT - 2026-01-10

This document has been archived because its visual timeline content has been
consolidated into the single unified roadmap: docs/roadmap.md

The critical path identification, timeline visualization, and resource allocation
guidance from this document are now part of the consolidated roadmap's
Critical Path and Roadmap Phases sections.

This file is preserved for historical reference but should not be used for current development.
For the latest roadmap, see: docs/roadmap.md
-->

# UCP Development Roadmap - Visual Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UCP v1.0 DEVELOPMENT TIMELINE                             │
│                         16 Weeks to Production                               │
└─────────────────────────────────────────────────────────────────────────────┘

PHASE 1: STABILIZE CORE (Weeks 1-4) 🔧
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Week 1: Fix & Validate
├─ M1.1: Fix Failing Tests ✅ [2d]
├─ M1.2: Real MCP Integration (filesystem, github) ✅ [3d]
└─ M1.3: Claude Desktop E2E Test ✅ [2d]

Week 2: Observability & Metrics
├─ M1.4: Telemetry Infrastructure (trace_id, metrics) ✅ [3d]
└─ M1.5: Baseline Benchmarks (recall, latency, cost) ✅ [2d]

Week 3: Error Handling
├─ M1.6: Failure Mode Testing (5 scenarios) ✅ [3d]
└─ M1.7: Documentation Update ✅ [2d]

Week 4: Distribution
├─ M1.8: PyPI Release (ucp==0.1.0-alpha1) ✅ [2d]
├─ M1.9: Docker Image ✅ [2d]
└─ M1.10: GitHub Actions CI ✅ [1d]

OUTPUT: Alpha release, 90%+ test coverage, real MCP validation


PHASE 2: SHIP CLIENTS (Weeks 5-10) 🚀
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Week 5-6: CLI Client
├─ M2.1: Wire CLI to UCP HTTP Server ✅ [4d]
└─ M2.2: CLI Polish (rich UI, debug mode) ✅ [2d]

Week 7-8: VS Code Extension ⭐ CRITICAL PATH
├─ M2.3: Core Commands (startChat, showTools, predictTools) ✅ [5d]
├─ M2.4: Webview Chat UI ✅ [3d]
└─ M2.5: Package & Publish to Marketplace ✅ [1d]

Week 9-10: Desktop App
├─ M2.6: Desktop UI Implementation ✅ [6d]
└─ M2.7: Cross-Platform Builds (Win/Mac/Linux) ✅ [2d]

OUTPUT: 3 usable clients, VS Code extension on Marketplace


PHASE 3: ADVANCED FEATURES (Weeks 11-16) 🏆
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Week 11-12: RAFT Fine-Tuning
├─ M3.1: Training Data Collection (1000+ sessions) ✅ [3d]
├─ M3.2: Fine-Tune Router Model (Llama-3.2-3B) ✅ [4d]
└─ M3.3: Deploy RAFT Model (A/B test) ✅ [2d]

Week 13-14: Production Hardening
├─ M3.4: Redis Session Backend ✅ [3d]
├─ M3.5: Security Hardening (sandboxing, auth) ✅ [3d]
└─ M3.6: Performance Optimization (<100ms latency) ✅ [2d]

Week 15-16: Community Launch
├─ M3.7: Documentation Overhaul (video, blog) ✅ [3d]
├─ M3.8: v1.0 Release (PyPI, Docker, Marketplace) ✅ [2d]
└─ M3.9: Community Tool Zoo ✅ [3d]

OUTPUT: v1.0 production release, 500+ GitHub stars


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                            KEY MILESTONES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📅 Week 1  → All tests pass, real MCP servers work
📅 Week 4  → Alpha release on PyPI + Docker
📅 Week 8  → VS Code extension published ⭐
📅 Week 10 → All 3 clients shipped
📅 Week 12 → RAFT model beats baseline by 10%+
📅 Week 16 → v1.0 production launch 🎉


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          SUCCESS METRICS (v1.0)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Recall@5:           90%+ (expected tool in top-5)
Context Reduction:  80%+ (tokens saved vs baseline)
Router Latency:     <100ms (p95)
Test Coverage:      90%+
GitHub Stars:       500+
Active Users:       100+/month


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          CRITICAL PATH
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Week 1-2:  Fix tests + real MCP validation (BLOCKER for everything)
Week 7-8:  VS Code extension (highest user impact)
Week 11-12: RAFT fine-tuning (core innovation)

If timeline slips, CUT:
- Desktop app (Week 9-10) → defer to v1.1
- Community Tool Zoo (Week 16) → defer to v1.1

NEVER CUT:
- Test fixes (Week 1)
- VS Code extension (Week 7-8)
- RAFT pipeline (Week 11-12)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    PROVEN METHODOLOGIES APPLIED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Two-Stage Dispatch (Gorilla)
   → Domain detection + semantic search
   → Already in router.py

✅ Cyclic Graph Architecture (LangGraph)
   → State machine for tool loops
   → Already in graph.py

✅ Log Everything (Feedback/Eval Best Practices)
   → Structured telemetry for RAFT training
   → Implement in Week 2

✅ AST Matching for Eval (Gorilla BFCL)
   → Semantic tool call validation
   → Add to evaluation harness

✅ Self-Correction Loop (ReAct)
   → Inject errors back into context
   → Already in server.py

✅ RAFT Fine-Tuning (Gorilla)
   → Train on real usage data
   → Week 11-12


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          RISK MITIGATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RISK: RAFT doesn't improve over baseline
→ MITIGATION: Keep semantic search as fallback

RISK: ChromaDB performance issues at scale
→ MITIGATION: Add Redis caching layer

RISK: Downstream MCP servers unstable
→ MITIGATION: Circuit breaker + health checks

RISK: Low user adoption
→ MITIGATION: Focus on VS Code (largest audience)

RISK: Security vulnerability
→ MITIGATION: Sandboxing + security audit (Week 13)


━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                        NEXT IMMEDIATE ACTION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

START HERE: Milestone 1.1 - Fix Failing Tests (2 days)

Command: pytest tests/ -v --tb=long > test_results.txt 2>&1

See: .agent/workflows/start-phase1.md for step-by-step guide
```

---

## Resource Allocation

**Solo Developer:**
- Focus on critical path only
- Skip desktop app → defer to v1.1
- Timeline: 12 weeks (Phases 1-2 + RAFT)

**2-Person Team:**
- Developer A: Backend + RAFT (Phases 1 & 3)
- Developer B: Clients (Phase 2)
- Timeline: 10 weeks (parallel work)

**3+ Person Team:**
- Developer A: Core backend
- Developer B: VS Code extension
- Developer C: CLI + Desktop
- Timeline: 8 weeks (full parallelization)

---

## Weekly Review Checklist

Every Friday:
- [ ] Review completed milestones
- [ ] Update metrics dashboard
- [ ] Adjust timeline if needed
- [ ] Identify blockers
- [ ] Plan next week's work

---

**Document Status:** Living roadmap, update as we learn from real usage
**Last Updated:** 2026-01-09
**Next Review:** Week 1 completion (2026-01-16)
