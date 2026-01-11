# Milestone 1.5: Baseline Benchmarks for Universal Context Protocol

**Date:** 2025-01-10  
**Version:** v0.1  
**Status:** Completed with Limitations

## Executive Summary

This document presents the baseline benchmark results for the Universal Context Protocol (UCP) local MVP. The benchmark compares tool selection performance between a baseline approach (exposing all tools) and the UCP approach (intelligent tool filtering).

### Key Findings

- **Context Reduction:** 0.0% (both modes selected 3 tools on average)
- **Recall@k:** 60.0% for both baseline and UCP
- **Precision@k:** 20.0% for both baseline and UCP
- **Selection Latency:** Baseline 28.53ms, UCP 25.99ms (8.9% faster)

### Critical Limitation

The benchmark did **NOT achieve the 80%+ context reduction target** due to a hardcoded `max_per_server = 3` limit in the router's reranking logic. This limit prevents selecting more than 3 tools from a single server, regardless of the configuration parameter.

## Methodology

### Test Environment

- **Repository:** `D:\GitHub\Telomere\UniversalContextProtocol`
- **UCP Version:** Local MVP
- **Test Date:** 2025-01-10
- **Python Version:** 3.x
- **Embedding Model:** `all-MiniLM-L6-v2`
- **Vector Database:** ChromaDB

### Test Tasks

A diverse set of 10 tasks covering multiple domains:

| ID | Domain | Prompt | Expected Tool |
|---|---|---|---|
| email_send_001 | Email | Send an email to john@example.com about the project update | `mock-server.mock.send_email` |
| email_read_001 | Email | Check my inbox for new messages | `mock-server.mock.read_inbox` |
| code_pr_001 | Code | Create a pull request for the feature branch | `mock-server.mock.create_pr` |
| code_commit_001 | Code | List the recent commits on main branch | `mock-server.mock.list_commits` |
| calendar_schedule_001 | Calendar | Schedule a meeting with the team for tomorrow at 2pm | `mock-server.mock.create_event` |
| slack_notify_001 | Communication | Send a Slack message to the engineering channel about the outage | `mock-server.mock.send_slack` |
| file_upload_001 | Files | Upload the quarterly report to Google Drive | `mock-server.mock.upload_file` |
| search_web_001 | Web | Search the web for Python async best practices | `mock-server.mock.web_search` |
| database_query_001 | Database | Query the users table for active accounts | `mock-server.mock.sql_query` |
| payment_charge_001 | Finance | Process a $50 payment for the subscription | `mock-server.mock.stripe_charge` |

### Mock Tools

28 mock tools were manually injected into the tool zoo, organized by domain:

**Email (2 tools):**
- `send_email`: Send an email to a recipient
- `read_inbox`: Read inbox messages

**Code (4 tools):**
- `create_pr`: Create a pull request
- `list_commits`: List commits on a branch
- `git_pull`: Pull changes from remote
- `git_push`: Push changes to remote

**Calendar (1 tool):**
- `create_event`: Create a calendar event

**Communication (1 tool):**
- `send_slack`: Send a Slack message

**Files (1 tool):**
- `upload_file`: Upload a file to cloud storage

**Web (1 tool):**
- `web_search`: Search the web

**Database (1 tool):**
- `sql_query`: Execute SQL queries

**Finance (1 tool):**
- `stripe_charge`: Process a payment

**Additional tools (16 tools):** Various tools across different domains

### Configuration

#### Baseline Mode

```python
UCPConfig(
    tool_zoo=ToolZooConfig(
        top_k=100,
        similarity_threshold=0.0,
    ),
    router=RouterConfig(
        mode="hybrid",
        strategy="baseline",
        max_tools=100,
        max_per_server=28,  # Allow all tools from same server
        min_tools=1,
    ),
)
```

#### UCP Mode

```python
UCPConfig(
    tool_zoo=ToolZooConfig(
        top_k=10,
        similarity_threshold=0.1,
    ),
    router=RouterConfig(
        mode="hybrid",
        strategy="sota",
        max_tools=5,
        max_per_server=3,  # Diversity limit
        min_tools=1,
        rerank=True,
    ),
)
```

### Metrics

The following metrics were measured:

1. **Recall@k:** Percentage of expected tools found in the selected tool set
2. **Precision@k:** Percentage of selected tools that were actually used (expected)
3. **Average Tools Selected:** Mean number of tools selected across all tasks
4. **Selection Latency:** Time taken to select tools (milliseconds)
5. **Execution Latency:** Time taken to execute tools (milliseconds) - N/A for mock tools
6. **Context Reduction:** Percentage reduction in tools shown compared to baseline

## Results

### Overall Performance

| Metric | Baseline | UCP | Difference |
|---|---|---|---|
| Avg Tools Selected | 3.00 | 3.00 | 0.0% |
| Recall@k | 60.0% | 60.0% | 0.0% |
| Precision@k | 20.0% | 20.0% | 0.0% |
| Selection Time (ms) | 28.53 | 25.99 | -8.9% |
| Execution Time (ms) | 0.00 | 0.00 | 0.0% |

### Context Reduction

- **Baseline Average:** 3.00 tools
- **UCP Average:** 3.00 tools
- **Context Reduction:** 0.0%
- **Target:** 80%+
- **Status:** ❌ **NOT ACHIEVED**

### Task-Level Results

| Task | Baseline Tools | Expected Found | UCP Tools | Expected Found |
|---|---|---|---|---|
| email_send_001 | 3 | ✅ | 3 | ✅ |
| email_read_001 | 3 | ✅ | 3 | ✅ |
| code_pr_001 | 3 | ✅ | 3 | ✅ |
| code_commit_001 | 3 | ✅ | 3 | ✅ |
| calendar_schedule_001 | 3 | ❌ | 3 | ❌ |
| slack_notify_001 | 3 | ✅ | 3 | ✅ |
| file_upload_001 | 3 | ❌ | 3 | ❌ |
| search_web_001 | 3 | ❌ | 3 | ❌ |
| database_query_001 | 3 | ❌ | 3 | ❌ |
| payment_charge_001 | 3 | ✅ | 3 | ✅ |

**Tasks with expected tool found:** 6/10 (60%)

## Analysis

### Why Context Reduction Failed

The benchmark failed to demonstrate context reduction because both baseline and UCP modes selected exactly 3 tools on average. This is due to a **hardcoded limitation** in the router's reranking logic.

#### Root Cause

In [`local/src/ucp_mvp/router.py`](local/src/ucp_mvp/router.py), the `_rerank_and_filter` method has a hardcoded `max_per_server = 3` limit:

```python
def _rerank_and_filter(
    self,
    results: list[tuple[ToolSchema, float]],
    session: SessionState,
    domains: list[str],
) -> tuple[list[str], dict[str, float]]:
    """Re-rank and filter search results."""
    
    # Apply diversity filter - limit tools per server
    selected: list[str] = []
    scores: dict[str, float] = {}
    server_counts: dict[str, int] = {}
    max_per_server = 3  # HARDCODED LIMIT
    
    for tool_name, score in sorted_tools:
        tool = self.tool_zoo.get_tool(tool_name)
        if not tool:
            continue
        
        server = tool.server_name
        if server_counts.get(server, 0) >= max_per_server:
            continue
        
        selected.append(tool_name)
        scores[tool_name] = score
        server_counts[server] = server_counts.get(server, 0) + 1
        
        if len(selected) >= self.config.max_tools:
            break
    
    return selected, scores
```

#### Impact

Since all 28 mock tools are from the same server (`mock-server`), the router can only select a maximum of 3 tools, regardless of:
- The `max_tools` configuration parameter (100 for baseline, 5 for UCP)
- The `max_per_server` configuration parameter (28 for baseline, 3 for UCP)

The hardcoded `max_per_server = 3` value is used instead of the configuration parameter.

### Recall and Precision Analysis

**Recall@k = 60%**: 6 out of 10 tasks had the expected tool in the selected set.

**Precision@k = 20%**: Only 1 out of 3 selected tools was the expected tool on average.

The low precision indicates that the router is selecting tools that are semantically related to the query but not necessarily the correct tool for the specific task.

### Latency Analysis

UCP mode was 8.9% faster in tool selection (25.99ms vs 28.53ms). This is likely due to:
- Lower `top_k` value (10 vs 100) reducing candidate retrieval time
- Fewer tools to process in the reranking stage

However, the difference is minimal (2.54ms) and may not be statistically significant.

## Recommendations

### Immediate Actions

1. **Fix the hardcoded `max_per_server` limit:**
   - Update [`local/src/ucp_mvp/router.py`](local/src/ucp_mvp/router.py) to use `self.config.max_per_server` instead of the hardcoded value
   - Re-run the benchmark to demonstrate 80%+ context reduction

2. **Improve tool descriptions:**
   - Enhance mock tool descriptions to be more specific
   - Add more domain-specific keywords to improve semantic matching

3. **Increase task diversity:**
   - Add more tasks with different complexity levels
   - Include multi-tool scenarios

### Future Improvements

1. **Cross-encoder reranking:**
   - Enable `use_cross_encoder` in the router configuration for more accurate tool ranking
   - This will improve precision but may increase latency

2. **Multi-server setup:**
   - Create mock tools from multiple servers to test diversity filtering
   - This will better demonstrate the `max_per_server` parameter's purpose

3. **Real-world evaluation:**
   - Test with actual MCP servers and tools
   - Use real-world tasks from production systems

4. **Additional metrics:**
   - Measure token usage for LLM context
   - Track end-to-end latency including LLM generation
   - Measure cost savings from reduced context

## Conclusion

The baseline benchmark infrastructure is complete and functional. However, the benchmark did not achieve the 80%+ context reduction target due to a hardcoded limitation in the router's reranking logic.

Once the `max_per_server` limit is fixed to respect the configuration parameter, the benchmark should demonstrate significant context reduction, with baseline mode selecting all 28 tools (or close to it) and UCP mode selecting only 3-5 tools.

The benchmark provides a solid foundation for ongoing evaluation and improvement of the UCP system.

## Appendix

### Files Created/Modified

- `clients/harness/tasks.json` - Test tasks for evaluation
- `clients/harness/run_baseline.py` - Simplified benchmark script
- `clients/reports/baseline_benchmark_v0.1.json` - Benchmark results
- `docs/milestone_1_5_baseline_benchmark.md` - This document

### Running the Benchmark

```bash
cd D:\GitHub\Telomere\UniversalContextProtocol
python clients\harness\run_baseline.py
```

### Benchmark Report Location

```
D:\GitHub\Telomere\UniversalContextProtocol\clients\reports\baseline_benchmark_v0.1.json
```

### Evaluation Data Location

```
D:\GitHub\Telomere\UniversalContextProtocol\clients\data\eval_runs\run_<timestamp>
```

**Date:** 2025-01-10  
**Version:** v0.1  
**Status:** Completed with Limitations

## Executive Summary

This document presents the baseline benchmark results for the Universal Context Protocol (UCP) local MVP. The benchmark compares tool selection performance between a baseline approach (exposing all tools) and the UCP approach (intelligent tool filtering).

### Key Findings

- **Context Reduction:** 0.0% (both modes selected 3 tools on average)
- **Recall@k:** 60.0% for both baseline and UCP
- **Precision@k:** 20.0% for both baseline and UCP
- **Selection Latency:** Baseline 28.53ms, UCP 25.99ms (8.9% faster)

### Critical Limitation

The benchmark did **NOT achieve the 80%+ context reduction target** due to a hardcoded `max_per_server = 3` limit in the router's reranking logic. This limit prevents selecting more than 3 tools from a single server, regardless of the configuration parameter.

## Methodology

### Test Environment

- **Repository:** `D:\GitHub\Telomere\UniversalContextProtocol`
- **UCP Version:** Local MVP
- **Test Date:** 2025-01-10
- **Python Version:** 3.x
- **Embedding Model:** `all-MiniLM-L6-v2`
- **Vector Database:** ChromaDB

### Test Tasks

A diverse set of 10 tasks covering multiple domains:

| ID | Domain | Prompt | Expected Tool |
|---|---|---|---|
| email_send_001 | Email | Send an email to john@example.com about the project update | `mock-server.mock.send_email` |
| email_read_001 | Email | Check my inbox for new messages | `mock-server.mock.read_inbox` |
| code_pr_001 | Code | Create a pull request for the feature branch | `mock-server.mock.create_pr` |
| code_commit_001 | Code | List the recent commits on main branch | `mock-server.mock.list_commits` |
| calendar_schedule_001 | Calendar | Schedule a meeting with the team for tomorrow at 2pm | `mock-server.mock.create_event` |
| slack_notify_001 | Communication | Send a Slack message to the engineering channel about the outage | `mock-server.mock.send_slack` |
| file_upload_001 | Files | Upload the quarterly report to Google Drive | `mock-server.mock.upload_file` |
| search_web_001 | Web | Search the web for Python async best practices | `mock-server.mock.web_search` |
| database_query_001 | Database | Query the users table for active accounts | `mock-server.mock.sql_query` |
| payment_charge_001 | Finance | Process a $50 payment for the subscription | `mock-server.mock.stripe_charge` |

### Mock Tools

28 mock tools were manually injected into the tool zoo, organized by domain:

**Email (2 tools):**
- `send_email`: Send an email to a recipient
- `read_inbox`: Read inbox messages

**Code (4 tools):**
- `create_pr`: Create a pull request
- `list_commits`: List commits on a branch
- `git_pull`: Pull changes from remote
- `git_push`: Push changes to remote

**Calendar (1 tool):**
- `create_event`: Create a calendar event

**Communication (1 tool):**
- `send_slack`: Send a Slack message

**Files (1 tool):**
- `upload_file`: Upload a file to cloud storage

**Web (1 tool):**
- `web_search`: Search the web

**Database (1 tool):**
- `sql_query`: Execute SQL queries

**Finance (1 tool):**
- `stripe_charge`: Process a payment

**Additional tools (16 tools):** Various tools across different domains

### Configuration

#### Baseline Mode

```python
UCPConfig(
    tool_zoo=ToolZooConfig(
        top_k=100,
        similarity_threshold=0.0,
    ),
    router=RouterConfig(
        mode="hybrid",
        strategy="baseline",
        max_tools=100,
        max_per_server=28,  # Allow all tools from same server
        min_tools=1,
    ),
)
```

#### UCP Mode

```python
UCPConfig(
    tool_zoo=ToolZooConfig(
        top_k=10,
        similarity_threshold=0.1,
    ),
    router=RouterConfig(
        mode="hybrid",
        strategy="sota",
        max_tools=5,
        max_per_server=3,  # Diversity limit
        min_tools=1,
        rerank=True,
    ),
)
```

### Metrics

The following metrics were measured:

1. **Recall@k:** Percentage of expected tools found in the selected tool set
2. **Precision@k:** Percentage of selected tools that were actually used (expected)
3. **Average Tools Selected:** Mean number of tools selected across all tasks
4. **Selection Latency:** Time taken to select tools (milliseconds)
5. **Execution Latency:** Time taken to execute tools (milliseconds) - N/A for mock tools
6. **Context Reduction:** Percentage reduction in tools shown compared to baseline

## Results

### Overall Performance

| Metric | Baseline | UCP | Difference |
|---|---|---|---|
| Avg Tools Selected | 3.00 | 3.00 | 0.0% |
| Recall@k | 60.0% | 60.0% | 0.0% |
| Precision@k | 20.0% | 20.0% | 0.0% |
| Selection Time (ms) | 28.53 | 25.99 | -8.9% |
| Execution Time (ms) | 0.00 | 0.00 | 0.0% |

### Context Reduction

- **Baseline Average:** 3.00 tools
- **UCP Average:** 3.00 tools
- **Context Reduction:** 0.0%
- **Target:** 80%+
- **Status:** ❌ **NOT ACHIEVED**

### Task-Level Results

| Task | Baseline Tools | Expected Found | UCP Tools | Expected Found |
|---|---|---|---|---|
| email_send_001 | 3 | ✅ | 3 | ✅ |
| email_read_001 | 3 | ✅ | 3 | ✅ |
| code_pr_001 | 3 | ✅ | 3 | ✅ |
| code_commit_001 | 3 | ✅ | 3 | ✅ |
| calendar_schedule_001 | 3 | ❌ | 3 | ❌ |
| slack_notify_001 | 3 | ✅ | 3 | ✅ |
| file_upload_001 | 3 | ❌ | 3 | ❌ |
| search_web_001 | 3 | ❌ | 3 | ❌ |
| database_query_001 | 3 | ❌ | 3 | ❌ |
| payment_charge_001 | 3 | ✅ | 3 | ✅ |

**Tasks with expected tool found:** 6/10 (60%)

## Analysis

### Why Context Reduction Failed

The benchmark failed to demonstrate context reduction because both baseline and UCP modes selected exactly 3 tools on average. This is due to a **hardcoded limitation** in the router's reranking logic.

#### Root Cause

In [`local/src/ucp_mvp/router.py`](local/src/ucp_mvp/router.py), the `_rerank_and_filter` method has a hardcoded `max_per_server = 3` limit:

```python
def _rerank_and_filter(
    self,
    results: list[tuple[ToolSchema, float]],
    session: SessionState,
    domains: list[str],
) -> tuple[list[str], dict[str, float]]:
    """Re-rank and filter search results."""
    
    # Apply diversity filter - limit tools per server
    selected: list[str] = []
    scores: dict[str, float] = {}
    server_counts: dict[str, int] = {}
    max_per_server = 3  # HARDCODED LIMIT
    
    for tool_name, score in sorted_tools:
        tool = self.tool_zoo.get_tool(tool_name)
        if not tool:
            continue
        
        server = tool.server_name
        if server_counts.get(server, 0) >= max_per_server:
            continue
        
        selected.append(tool_name)
        scores[tool_name] = score
        server_counts[server] = server_counts.get(server, 0) + 1
        
        if len(selected) >= self.config.max_tools:
            break
    
    return selected, scores
```

#### Impact

Since all 28 mock tools are from the same server (`mock-server`), the router can only select a maximum of 3 tools, regardless of:
- The `max_tools` configuration parameter (100 for baseline, 5 for UCP)
- The `max_per_server` configuration parameter (28 for baseline, 3 for UCP)

The hardcoded `max_per_server = 3` value is used instead of the configuration parameter.

### Recall and Precision Analysis

**Recall@k = 60%**: 6 out of 10 tasks had the expected tool in the selected set.

**Precision@k = 20%**: Only 1 out of 3 selected tools was the expected tool on average.

The low precision indicates that the router is selecting tools that are semantically related to the query but not necessarily the correct tool for the specific task.

### Latency Analysis

UCP mode was 8.9% faster in tool selection (25.99ms vs 28.53ms). This is likely due to:
- Lower `top_k` value (10 vs 100) reducing candidate retrieval time
- Fewer tools to process in the reranking stage

However, the difference is minimal (2.54ms) and may not be statistically significant.

## Recommendations

### Immediate Actions

1. **Fix the hardcoded `max_per_server` limit:**
   - Update [`local/src/ucp_mvp/router.py`](local/src/ucp_mvp/router.py) to use `self.config.max_per_server` instead of the hardcoded value
   - Re-run the benchmark to demonstrate 80%+ context reduction

2. **Improve tool descriptions:**
   - Enhance mock tool descriptions to be more specific
   - Add more domain-specific keywords to improve semantic matching

3. **Increase task diversity:**
   - Add more tasks with different complexity levels
   - Include multi-tool scenarios

### Future Improvements

1. **Cross-encoder reranking:**
   - Enable `use_cross_encoder` in the router configuration for more accurate tool ranking
   - This will improve precision but may increase latency

2. **Multi-server setup:**
   - Create mock tools from multiple servers to test diversity filtering
   - This will better demonstrate the `max_per_server` parameter's purpose

3. **Real-world evaluation:**
   - Test with actual MCP servers and tools
   - Use real-world tasks from production systems

4. **Additional metrics:**
   - Measure token usage for LLM context
   - Track end-to-end latency including LLM generation
   - Measure cost savings from reduced context

## Conclusion

The baseline benchmark infrastructure is complete and functional. However, the benchmark did not achieve the 80%+ context reduction target due to a hardcoded limitation in the router's reranking logic.

Once the `max_per_server` limit is fixed to respect the configuration parameter, the benchmark should demonstrate significant context reduction, with baseline mode selecting all 28 tools (or close to it) and UCP mode selecting only 3-5 tools.

The benchmark provides a solid foundation for ongoing evaluation and improvement of the UCP system.

## Appendix

### Files Created/Modified

- `clients/harness/tasks.json` - Test tasks for evaluation
- `clients/harness/run_baseline.py` - Simplified benchmark script
- `clients/reports/baseline_benchmark_v0.1.json` - Benchmark results
- `docs/milestone_1_5_baseline_benchmark.md` - This document

### Running the Benchmark

```bash
cd D:\GitHub\Telomere\UniversalContextProtocol
python clients\harness\run_baseline.py
```

### Benchmark Report Location

```
D:\GitHub\Telomere\UniversalContextProtocol\clients\reports\baseline_benchmark_v0.1.json
```

### Evaluation Data Location

```
D:\GitHub\Telomere\UniversalContextProtocol\clients\data\eval_runs\run_<timestamp>
```

