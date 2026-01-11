<!--
ARCHIVED DOCUMENT - 2026-01-10

This document has been archived because its prioritization framework content has been
consolidated into the single unified roadmap: docs/roadmap.md

The RICE scoring, MoSCoW prioritization, and decision trees from this document
are now part of the consolidated roadmap's Prioritization Framework section.

This file is preserved for historical reference but should not be used for current development.
For the latest prioritization guidance, see: docs/roadmap.md
-->

# UCP Development Prioritization Matrix

**Purpose:** Guide decision-making when time/resources are constrained.

---

## 🎯 **Feature Prioritization Framework**

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

---

## 🚨 **Must-Have vs Nice-to-Have (MoSCoW Method)**

### **MUST Have (v1.0 Blockers)**
1. ✅ All tests passing
2. ✅ Real MCP server integration (2+ servers)
3. ✅ VS Code extension with core features
4. ✅ Telemetry infrastructure
5. ✅ PyPI + Docker distribution
6. ✅ Benchmark showing 80%+ context reduction

### **SHOULD Have (v1.0 Goals)**
1. ✅ RAFT fine-tuning pipeline
2. ✅ CLI client
3. ✅ GitHub Actions CI
4. ✅ Security hardening
5. ✅ Performance optimization (<100ms latency)

### **COULD Have (v1.1 Candidates)**
1. 🔄 Desktop app
2. 🔄 Redis session backend
3. 🔄 GPU acceleration
4. 🔄 Community Tool Zoo
5. 🔄 Advanced analytics dashboard

### **WON'T Have (Out of Scope)**
1. ❌ Mobile apps (iOS/Android)
2. ❌ Browser extension
3. ❌ SaaS hosted service
4. ❌ Enterprise SSO integration
5. ❌ Multi-tenant architecture

---

## ⏱️ **Time-Boxed Decision Tree**

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

## 📊 **Impact vs Effort Matrix**

```
High Impact, Low Effort (DO FIRST) 🟢
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Fix failing tests (2d)
- PyPI release (2d)
- Telemetry logging (3d)
- Real MCP validation (3d)

High Impact, High Effort (PLAN CAREFULLY) 🟡
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- VS Code extension (9d)
- RAFT fine-tuning (7d)
- Desktop app (8d)

Low Impact, Low Effort (FILL GAPS) 🔵
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- GitHub Actions CI (1d)
- Documentation updates (2d)
- Redis backend (3d)

Low Impact, High Effort (AVOID) 🔴
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- GPU acceleration (5d, only 10% reach)
- Browser extension (10d, different audience)
```

---

## 🎓 **Best Practices from Research Synthesis**

### **From Gorilla (Tool Selection)**
✅ **Priority:** RAFT fine-tuning (Week 11-12)  
⚠️ **Risk:** May not beat baseline → keep semantic search as fallback  
📊 **Metric:** Recall@5 improvement

### **From LangGraph (State Management)**
✅ **Priority:** Cyclic graph architecture (already implemented)  
✅ **Priority:** Session persistence (already implemented)  
🔄 **Future:** Human-in-the-loop interrupts (v1.1)

### **From LlamaIndex (Context Retrieval)**
✅ **Priority:** Vector indexing (already implemented)  
✅ **Priority:** Hybrid search (already implemented)  
🔄 **Future:** Metadata filtering optimization (v1.1)

### **From Feedback/Eval Synthesis**
✅ **Priority:** Log everything (Week 2)  
✅ **Priority:** AST matching for eval (Week 2)  
🔄 **Future:** Offline RLHF (v1.1)

---

## 🔄 **Iteration Strategy**

### **Week 1-4: Validate Core Hypothesis**
**Question:** Does UCP reduce context bloat while maintaining recall?

**Experiments:**
1. Benchmark: All tools vs Top-5 filtered
2. Measure: Recall, latency, cost
3. Decision: If recall <80% → revisit router logic

### **Week 5-10: Validate User Experience**
**Question:** Will developers actually use UCP?

**Experiments:**
1. Ship VS Code extension to 10 beta users
2. Collect feedback via telemetry
3. Decision: If <50% retention → revisit UX

### **Week 11-16: Validate Learning**
**Question:** Does RAFT improve over semantic search?

**Experiments:**
1. A/B test: RAFT vs baseline
2. Measure: Recall@5, latency
3. Decision: If <10% improvement → ship baseline, iterate in v1.1

---

## 🚀 **Launch Readiness Checklist**

### **v0.1-alpha (Week 4)**
- [ ] All tests pass
- [ ] 2+ real MCP servers tested
- [ ] PyPI package published
- [ ] Docker image available
- [ ] Basic documentation

### **v0.5-beta (Week 10)**
- [ ] VS Code extension on Marketplace
- [ ] CLI client functional
- [ ] Telemetry infrastructure live
- [ ] Benchmark results published
- [ ] 10+ beta users

### **v1.0-production (Week 16)**
- [ ] RAFT fine-tuning complete
- [ ] Security audit passed
- [ ] Performance <100ms (p95)
- [ ] 90%+ test coverage
- [ ] Video tutorial published
- [ ] 100+ GitHub stars

---

## 💡 **Decision-Making Heuristics**

### **When to Ship**
✅ Ship when: Core value prop is proven (context reduction + recall)  
✅ Ship when: At least 1 client is production-ready (VS Code)  
✅ Ship when: Tests pass and docs exist  
❌ Don't ship when: Critical bugs exist  
❌ Don't ship when: No real MCP server validation

### **When to Cut Features**
✅ Cut when: Feature is <30 RICE score  
✅ Cut when: Timeline slips by 2+ weeks  
✅ Cut when: Feature blocks other critical work  
❌ Don't cut: Test fixes, VS Code extension, RAFT pipeline

### **When to Pivot**
🔄 Pivot when: RAFT doesn't improve baseline (ship semantic search)  
🔄 Pivot when: User feedback contradicts assumptions  
🔄 Pivot when: Better approach discovered mid-development  
❌ Don't pivot: Based on one user's opinion  
❌ Don't pivot: Without data to support decision

---

## 📈 **Success Criteria (Quantitative)**

| Metric | Baseline | Alpha | Beta | v1.0 |
|--------|----------|-------|------|------|
| **Tests Passing** | 59/61 | 61/61 | 61/61 | 90/90 |
| **Recall@5** | 60% | 75% | 85% | 90%+ |
| **Context Reduction** | 0% | 50% | 70% | 80%+ |
| **Router Latency (p95)** | N/A | 200ms | 150ms | <100ms |
| **GitHub Stars** | 0 | 10 | 50 | 500+ |
| **Active Users** | 0 | 5 | 20 | 100+ |

---

## 🎯 **Final Prioritization (If Only 8 Weeks)**

**Minimum Viable v1.0:**

1. **Week 1-2:** Fix tests + real MCP validation + telemetry
2. **Week 3-4:** PyPI release + Docker + CI
3. **Week 5-8:** VS Code extension (full focus)

**Ship with:**
- ✅ Core backend (semantic search only, no RAFT)
- ✅ VS Code extension
- ✅ PyPI + Docker distribution
- ✅ Benchmark showing value prop

**Defer to v1.1:**
- 🔄 RAFT fine-tuning
- 🔄 CLI client
- 🔄 Desktop app
- 🔄 Redis backend

**Rationale:** VS Code extension has highest reach (80) and impact (9). Ship the core innovation (context-aware tool injection) with the most accessible client.

---

**Last Updated:** 2026-01-09  
**Review Cadence:** Weekly during development  
**Owner:** Project lead / Product manager
