# UCP ML Pipeline Implementation Plan

**Date:** 2026-01-16  
**Status:** Planning Phase  
**Related Plans:**
- [Repository Reorganization Plan](repository_reorganization_plan.md) - ✅ Completed
- [Roadmap](../docs/roadmap.md) - Active
- [Task Checklist](C:\Users\User\.gemini\antigravity\brain\07cae792-2b8e-4df6-bb6a-749bb7b616a6\task.md)
- [Full Implementation Plan](C:\Users\User\.gemini\antigravity\brain\07cae792-2b8e-4df6-bb6a-749bb7b616a6\implementation_plan.md)

---

## Quick Reference: What's Missing vs What Exists

### ✅ What Exists (From Previous Work)

| Component | Status | Location | Notes |
|-----------|--------|----------|-------|
| Tool Zoo | 90% | `src/ucp/tool_zoo.py` | ChromaDB vector storage, semantic + keyword search |
| Router | 85% | `src/ucp/router.py` | Baseline + adaptive routing |
| RAFT Data Gen | 70% | `src/ucp/raft.py` | Training data generation framework |
| Telemetry | 60% | `src/ucp/telemetry.py` | Logging infrastructure |
| Session Mgmt | 80% | `src/ucp/session.py` | SQLite persistence |
| CLI | 70% | `src/ucp/cli.py` | Basic commands (serve, index, search) |
| Bandit Scorer | 50% | `src/ucp/bandit.py` | Thompson sampling framework |
| Online Opt | 50% | `src/ucp/online_opt.py` | Online optimization framework |

### ❌ Critical Gaps (What You Need to Build)

| Missing Component | Why It's Critical | Estimated Effort |
|-------------------|-------------------|------------------|
| **MCP/Skill Registry** | No centralized catalog of available tools | 2 weeks |
| **Metadata Schema** | Can't match tools to use cases without rich metadata | 1 week |
| **Baseline Recommender** | Cold-start problem for new agents | 2 weeks |
| **ML Training Loop** | RAFT data gen exists but no actual training pipeline | 3 weeks |
| **Feedback Pipeline** | No way to learn from usage patterns | 2 weeks |
| **Registry GUI** | Manual config is tedious and error-prone | 2 weeks |
| **Cross-Agent Learning** | Each agent starts from scratch | 2 weeks |

---

## The Core Problem

**You asked:** "I'd need a registry right? I'd need things to choose from, plus I'd need like some keywords and baseline recommendations, but I'd also probably need a lot more things, I don't think all these pieces are wired up into a viable protocol."

**You're absolutely right.** Here's what's missing:

### 1. No Registry = No Discovery
- **Current State:** UCP can route to tools that are already configured
- **Missing:** No way to discover what tools/MCPs exist
- **Impact:** Users must manually research and configure every MCP
- **Solution:** Build centralized registry with metadata (Phase 1)

### 2. No Baseline Recommendations = Cold Start Problem
- **Current State:** Semantic search only works if you know what to search for
- **Missing:** No recommendations for "I want to build a coding agent"
- **Impact:** New users are lost, don't know where to start
- **Solution:** Use case templates + keyword matching (Phase 2)

### 3. No ML Pipeline = No Learning
- **Current State:** RAFT data generation exists but no training loop
- **Missing:** No way to train models from actual usage
- **Impact:** System can't improve over time
- **Solution:** Wire telemetry → training → deployment (Phase 3)

### 4. No Feedback Loop = No Improvement
- **Current State:** Tools are used but no learning from outcomes
- **Missing:** No tracking of which recommendations were good/bad
- **Impact:** Same mistakes repeated forever
- **Solution:** Usage tracking + implicit feedback (Phase 4)

### 5. No GUI = Poor UX
- **Current State:** Everything is CLI or YAML editing
- **Missing:** Visual interface for registry and configuration
- **Impact:** High barrier to entry, tedious workflow
- **Solution:** Web dashboard with configurator (Phase 5)

---

## High-Level Architecture (After Implementation)

```
┌─────────────────────────────────────────────────────────────┐
│                     UCP ML Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Registry   │  │  Baseline    │  │  RAFT Model  │      │
│  │  (Metadata)  │  │ Recommender  │  │  (Trained)   │      │
│  │              │  │              │  │              │      │
│  │ • 50+ MCPs   │  │ • Use cases  │  │ • Fine-tuned │      │
│  │ • Keywords   │  │ • Keywords   │  │ • Learned    │      │
│  │ • Categories │  │ • Popularity │  │ • Patterns   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                    ┌───────▼────────┐                        │
│                    │  ML Pipeline   │                        │
│                    │  Orchestrator  │                        │
│                    └───────┬────────┘                        │
│                            │                                 │
│         ┌──────────────────┼──────────────────┐             │
│         │                  │                  │             │
│  ┌──────▼───────┐  ┌──────▼───────┐  ┌──────▼───────┐     │
│  │  Telemetry   │  │   Feedback   │  │   Training   │     │
│  │  Collector   │  │  Collector   │  │   Pipeline   │     │
│  │              │  │              │  │              │     │
│  │ • Usage logs │  │ • Implicit   │  │ • Daily job  │     │
│  │ • Success    │  │ • Explicit   │  │ • Retrain    │     │
│  │ • Latency    │  │ • Ratings    │  │ • Deploy     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                      User Interfaces                         │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │     CLI      │  │  Web Dashboard│  │     API      │      │
│  │              │  │              │  │              │      │
│  │ • recommend  │  │ • Registry   │  │ • REST       │      │
│  │ • configure  │  │ • Configurator│  │ • GraphQL    │      │
│  │ • train      │  │ • Analytics  │  │ • Webhooks   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases (14 Weeks)

### Phase 1: Registry Foundation (Week 1-2)
**Goal:** Create centralized catalog of MCPs with rich metadata

**Deliverables:**
- [ ] Registry data model (`MCPRegistryEntry`, `SkillDefinition`)
- [ ] Extended `RegistryToolZoo` class
- [ ] Seed data with 20+ MCPs
- [ ] CLI commands: `ucp registry list`, `ucp registry search`

**Key Files:**
- `src/ucp/registry.py` (NEW)
- `src/ucp/tool_zoo.py` (EXTEND)
- `data/registry_seed.yaml` (NEW)

### Phase 2: Baseline Recommendations (Week 3-4)
**Goal:** Provide intelligent recommendations without ML training (cold-start)

**Deliverables:**
- [ ] `BaselineRecommender` class
- [ ] Use case templates (coding, email, data analysis, etc.)
- [ ] CLI: `ucp recommend --use-case coding`
- [ ] Agent profile system

**Key Files:**
- `src/ucp/recommender.py` (NEW)
- `src/ucp/use_cases.py` (NEW)
- `src/ucp/cli.py` (EXTEND)

### Phase 3: ML Training Pipeline (Week 5-7)
**Goal:** Wire RAFT to production with continuous learning

**Deliverables:**
- [ ] Telemetry → training data pipeline
- [ ] Training script with LoRA fine-tuning
- [ ] Model serving layer (`RAFTRouter`)
- [ ] A/B testing framework
- [ ] Automated retraining job

**Key Files:**
- `src/ucp/telemetry.py` (EXTEND)
- `scripts/train_raft_model.py` (NEW)
- `src/ucp/ml_router.py` (NEW)
- `src/ucp/ab_testing.py` (NEW)
- `scripts/continuous_training.py` (NEW)

### Phase 4: Feedback Loop (Week 8-9)
**Goal:** Create continuous improvement from usage

**Deliverables:**
- [ ] Usage tracking in session manager
- [ ] Implicit feedback collection
- [ ] Explicit feedback API
- [ ] Feedback aggregation pipeline

**Key Files:**
- `src/ucp/session.py` (EXTEND)
- `src/ucp/feedback.py` (NEW)

### Phase 5: Registry GUI (Week 10-11)
**Goal:** Visual interface for registry management

**Deliverables:**
- [ ] Streamlit web dashboard
- [ ] Registry browser with search/filter
- [ ] Agent configurator
- [ ] Analytics dashboard
- [ ] Config export (YAML)

**Key Files:**
- `src/ucp/web_dashboard.py` (NEW)
- `src/ucp/config_generator.py` (NEW)

### Phase 6: Advanced ML (Week 12-14)
**Goal:** Personalization and cross-agent learning

**Deliverables:**
- [ ] Thompson Sampling bandits
- [ ] Federated learning for cross-agent intelligence
- [ ] Online learning with ensemble
- [ ] Performance benchmarks

**Key Files:**
- `src/ucp/bandits.py` (EXTEND existing)
- `src/ucp/federated_learning.py` (NEW)
- `src/ucp/online_learning.py` (NEW)
- `src/ucp/ml_pipeline.py` (NEW - orchestrator)

---

## Success Criteria

### Registry Completeness
- ✅ 50+ MCPs cataloged with metadata
- ✅ 100+ skills defined
- ✅ 90%+ coverage of common use cases

### Recommendation Quality
- ✅ 80%+ precision@5 (recommended tools are used)
- ✅ 90%+ recall@10 (needed tools are recommended)
- ✅ 50%+ reduction in manual tool selection time

### ML Pipeline Health
- ✅ 100+ training examples collected daily
- ✅ Weekly automated model retraining
- ✅ <5% model performance degradation over time

### User Experience
- ✅ <2 minutes to configure optimal agent setup
- ✅ <10 seconds to get tool recommendations
- ✅ 80%+ user satisfaction with recommendations

---

## Quick Start Guide (For Implementation)

### Step 1: Review Full Plan
Read the detailed implementation plan:
```
C:\Users\User\.gemini\antigravity\brain\07cae792-2b8e-4df6-bb6a-749bb7b616a6\implementation_plan.md
```

### Step 2: Check Task Checklist
Track progress in:
```
C:\Users\User\.gemini\antigravity\brain\07cae792-2b8e-4df6-bb6a-749bb7b616a6\task.md
```

### Step 3: Start with Phase 1
Begin with registry foundation:
1. Design `MCPRegistryEntry` schema
2. Extend `RegistryToolZoo` class
3. Create seed data with 20+ MCPs
4. Add CLI commands

### Step 4: Iterate
- Build one phase at a time
- Test each component before moving on
- Collect feedback and adjust

---

## Key Insights from Audit

### What UCP Does Well ✅
1. **Tool routing** - Semantic + keyword search works
2. **Vector storage** - ChromaDB integration is solid
3. **RAFT framework** - Data generation is well-designed
4. **Telemetry** - Logging infrastructure exists

### What UCP Needs ❌
1. **Registry** - No centralized catalog
2. **Recommendations** - No cold-start system
3. **Training loop** - RAFT exists but not wired to production
4. **Feedback** - No learning from usage
5. **GUI** - No visual interface
6. **Integration** - Pieces exist but not connected

### The Gap
**UCP is 60% of the way to a complete ML pipeline.** The routing infrastructure is solid, but it lacks the **discovery, recommendation, and learning** layers needed for a viable protocol.

---

## Related Documentation

- **[Full Implementation Plan](C:\Users\User\.gemini\antigravity\brain\07cae792-2b8e-4df6-bb6a-749bb7b616a6\implementation_plan.md)** - Detailed technical specs
- **[Task Checklist](C:\Users\User\.gemini\antigravity\brain\07cae792-2b8e-4df6-bb6a-749bb7b616a6\task.md)** - Progress tracking
- **[Roadmap](../docs/roadmap.md)** - Overall UCP roadmap
- **[Repository Reorganization](repository_reorganization_plan.md)** - Completed restructuring
- **[Whitepaper](../ucp_source_of_truth_whitepaper.md)** - Original vision

---

**Next Steps:**
1. Review this plan and the detailed implementation plan
2. Decide on timeline and resource allocation
3. Begin Phase 1: Registry Foundation
4. Set up monitoring for success metrics

---

*Created: 2026-01-16*  
*Status: Planning Phase*  
*Estimated Duration: 14 weeks*  
*Estimated Effort: 1-2 developers full-time*
