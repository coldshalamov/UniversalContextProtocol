# SOTA Tool Selection Prototype

This document describes the State-of-the-Art (SOTA) tool selection pipeline 
implemented in UCP. The pipeline extends the baseline routing with online 
learning capabilities:

## Overview

The SOTA pipeline implements a **Retrieve → Rerank → Budgeted Slate → Online Learning** 
architecture that:

1. **Retrieves** candidate tools fast (hybrid semantic + keyword search)
2. **Reranks** them intelligently (optional cross-encoder)
3. **Selects** a small budgeted slate (k tools under token budget)
4. **Learns** online from partial feedback (tool success/failure + latency)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOTA Routing Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Query ─► Candidate     ─► Reranking   ─► Slate      ─► Output  │
│           Retrieval         Stage          Selection             │
│           (ToolZoo)         (Reranker)     (Selector)           │
│                                                                  │
│  ┌────────────┐    ┌─────────────┐    ┌──────────────┐         │
│  │ Hybrid     │─►  │ Lightweight │─►  │ Bandit       │         │
│  │ Search     │    │ or Cross-   │    │ Scorer       │         │
│  │ (50+ cand) │    │ Encoder     │    │ + Biases     │         │
│  └────────────┘    └─────────────┘    └──────────────┘         │
│                                              │                   │
│                                              ▼                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Telemetry Store                         │  │
│  │  (Routing Events, Tool Calls, Reward Signals)             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                              │                   │
│                                              ▼                   │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Online Learning                         │  │
│  │  - SharedBanditScorer (shared weights, SGD)               │  │
│  │  - ToolBiasStore (per-tool scalar biases)                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Candidate Retrieval (`routing_pipeline.py`)

- Expands candidate pool to 50-200 tools (configurable)
- Uses hybrid search: semantic embeddings + keyword matching
- Estimates token footprint per tool schema

### 2. Reranking (`routing_pipeline.py`)

Two modes available:

**Lightweight Reranker** (default):
- Weighted combination of semantic + keyword scores
- Domain/tag match boosts
- Recency and co-occurrence boosts
- Fast (~1ms per query)

**Cross-Encoder Reranker** (optional):
- Uses sentence-transformers CrossEncoder
- Higher quality but slower (~100ms per query)
- Results cached with TTL

### 3. Budgeted Slate Selection (`routing_pipeline.py`)

- Greedy selection under token budget
- Diversity constraint (max tools per server)
- Integrates bandit scores and bias adjustments
- Epsilon-greedy or Thompson sampling exploration

### 4. Online Learning

**Shared Bandit Scorer** (`bandit.py`):
- Shared linear/logistic model (NOT per-tool LinUCB)
- Feature-based: tools scored by context features
- Online SGD updates with L2 regularization
- Persistent weights in SQLite

**Per-Tool Bias Store** (`online_opt.py`):
- Scalar bias per tool (1 float each)
- Updates based on reward signal
- Decay mechanism prevents overfitting
- Optional delta vectors for embeddings

### 5. Telemetry (`telemetry.py`)

Structured event logging with:
- **Routing Events**: candidates, selections, timing
- **Tool Calls**: success/failure, latency, errors
- **Reward Signals**: computed rewards for learning

Privacy-first: query hashing by default, raw text opt-in.

### 6. Reward Calculation

Proxy-based reward signal:
```
reward = success_reward         # +1 success, -1 failure
       + latency_penalty        # -(time * scale), capped
       + context_cost_penalty   # -(tokens * scale), capped
       + followup_penalty       # -0.2 if immediate retry

total = clamp(sum, -1, +1)
```

## Configuration

Enable SOTA mode in `ucp_config.yaml`:

```yaml
router:
  strategy: sota              # 'baseline' or 'sota'
  mode: hybrid
  max_tools: 10
  min_tools: 1
  
  # SOTA-specific options
  use_cross_encoder: false    # Enable cross-encoder reranking
  cross_encoder_model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
  candidate_pool_size: 50     # Candidates before reranking
  max_context_tokens: 8000    # Token budget for schemas
  max_per_server: 3           # Diversity limit
  exploration_rate: 0.1       # Epsilon for exploration
  exploration_type: epsilon   # 'epsilon' or 'thompson'

telemetry:
  enabled: true
  db_path: "./data/telemetry.db"
  log_query_text: false       # Privacy: don't log raw queries
  cleanup_hours: 168          # 1 week retention

bandit:
  enabled: true
  db_path: "./data/bandit_weights.db"
  learning_rate: 0.01
  feature_dim: 7

bias_learning:
  enabled: true
  db_path: "./data/tool_biases.db"
  learning_rate: 0.05
  max_bias: 0.5
```

## Running the Evaluation

Compare baseline vs SOTA performance:

```bash
# Run evaluation harness
python clients/harness/run_eval.py

# Or with custom paths
EVAL_TASKS=path/to/tasks.json \
EVAL_REPORT=path/to/report.json \
python clients/harness/run_eval.py
```

Output includes:
- **Recall@k**: % of expected tools in selected set
- **Precision@k**: % of selected tools that were used
- **MRR**: Mean Reciprocal Rank
- **Avg Tools**: Average tools exposed to model
- **Selection Time**: Pipeline latency

## Running the Dashboard

Visualize routing decisions and learning progress:

```bash
# Install streamlit if needed
pip install streamlit pandas

# Run dashboard
streamlit run src/ucp/dashboard.py
```

Dashboard tabs:
1. **Tool Search**: Interactive search testing
2. **Tool Zoo Stats**: Index statistics
3. **Session Explorer**: Usage patterns
4. **Router Learning**: Co-occurrence and precision/recall
5. **SOTA Metrics**: Bandit stats, bias learning
6. **Telemetry Details**: Recent events and rewards

## Interpreting Metrics

### Good Signs
- **Recall@k ≥ baseline**: Not losing expected tools
- **Avg Tools ↓**: Reducing context cost
- **Selection Time < 100ms**: Fast enough for interactive use
- **Exploration Rate ~10%**: Balanced exploration

### Warning Signs
- **Recall@k drops significantly**: May need higher candidate pool
- **Bias variance high**: Learning may be overfitting
- **Selection Time > 100ms**: Consider disabling cross-encoder

## Online Learning Dynamics

### Cold Start
- First requests use semantic similarity only
- Biases at 0, bandit weights neutral
- Exploration discovers tool performance

### Warm State
- Biases shift toward consistently good/bad tools
- Bandit learns which features predict success
- Exploration rate can be reduced

### Monitoring
```python
# Get learning stats
stats = router.get_sota_stats()
print(f"Bandit updates: {stats['bandit']['update_count']}")
print(f"Mean bias: {stats['bias']['mean_bias']}")
print(f"Exploration: {stats['telemetry']['exploration_rate']}")
```

## Why This is "SOTA-Feasible"

This prototype implements key ideas from the research literature:

1. **Retrieve-Rerank pattern** (like RAG, ColBERT)
   - Fast first-stage retrieval
   - Quality second-stage reranking

2. **Contextual Bandits** (like LinUCB but simpler)
   - Shared model avoids O(n*d²) per-tool matrices
   - Online learning without massive training infrastructure

3. **Cost-Aware Selection** (like budget-constrained optimization)
   - Token budget enforcement
   - Diversity constraints

4. **Partial Feedback** (like bandit reward signals)
   - Learn from tool success/failure
   - No need for explicit labels

## Next Research Steps

1. **Offline Reranker Training**
   - Fine-tune cross-encoder on (query, tool) relevance pairs
   - Use collected telemetry as training data

2. **ToolRet-Style Fine-tuning**
   - Train retriever specifically for tool selection
   - Contrastive learning on tool usage data

3. **Better Counterfactual Evaluation**
   - Estimate reward for unselected tools
   - Inverse propensity weighting

4. **Multi-Turn Context**
   - Model conversation trajectory
   - Predict tool sequences

## File Reference

| File | Description |
|------|-------------|
| `src/ucp/routing_pipeline.py` | Retrieve-Rerank-Select pipeline |
| `src/ucp/bandit.py` | Shared bandit scorer |
| `src/ucp/online_opt.py` | Per-tool bias learning |
| `src/ucp/telemetry.py` | Event logging and rewards |
| `src/ucp/router.py` | SOTARouter integration |
| `src/ucp/config.py` | Configuration models |
| `src/ucp/dashboard.py` | Visualization dashboard |
| `clients/harness/run_eval.py` | Evaluation harness |
| `tests/test_sota_pipeline.py` | Unit tests |
