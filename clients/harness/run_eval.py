"""
UCP Evaluation Harness - Baseline vs SOTA Comparison.

Runs evaluation tasks against both baseline and SOTA routing strategies,
measuring:
- Retrieval metrics: Recall@k, Precision@k for expected tool presence
- End-to-end proxy success: tool call success rate on mocks
- Cost metrics: avg selected tools, avg schema chars/tokens
- Latency metrics: selection pipeline time

Outputs a side-by-side comparison and summary JSON artifact.
"""

import asyncio
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from ucp.server import UCPServer
from ucp.config import (
    UCPConfig,
    DownstreamServerConfig,
    ToolZooConfig,
    RouterConfig,
    SessionConfig,
    TelemetryConfig,
    BanditConfig,
    BiasLearningConfig,
)
from ucp.connection_pool import ConnectionPool


@dataclass
class TaskResult:
    """Result for a single evaluation task."""
    
    mode: str
    task_id: str
    prompt: str = ""
    expected_tool: str = ""
    
    # Retrieval metrics
    visible_tools_count: int = 0
    expected_tool_visible: bool = False
    expected_tool_rank: int = -1  # Position in selected list (-1 = not found)
    
    # Execution metrics
    success: bool = False
    execution_time_ms: float = 0.0
    error: str | None = None
    
    # Cost metrics
    context_tokens: int = 0
    selection_time_ms: float = 0.0
    
    # Trace
    trace: list[str] = field(default_factory=list)
    exploration_triggered: bool = False


@dataclass
class EvalMetrics:
    """Aggregated metrics for an evaluation run."""
    
    mode: str
    total_tasks: int = 0
    
    # Retrieval
    recall_at_k: float = 0.0  # % of expected tools in selected set
    precision_at_k: float = 0.0  # % of selected tools that were used
    mean_reciprocal_rank: float = 0.0
    
    # Success
    success_rate: float = 0.0
    
    # Cost
    avg_tools_selected: float = 0.0
    avg_context_tokens: float = 0.0
    
    # Latency
    avg_selection_time_ms: float = 0.0
    avg_execution_time_ms: float = 0.0
    
    # Exploration
    exploration_rate: float = 0.0


def compute_metrics(results: list[TaskResult]) -> EvalMetrics:
    """Compute aggregated metrics from task results."""
    if not results:
        return EvalMetrics(mode="unknown")
    
    mode = results[0].mode
    n = len(results)
    
    # Recall@k: % of expected tools in selected set
    visible_count = sum(1 for r in results if r.expected_tool_visible)
    recall = visible_count / n if n else 0
    
    # Mean Reciprocal Rank
    mrr_sum = 0.0
    for r in results:
        if r.expected_tool_rank > 0:
            mrr_sum += 1.0 / r.expected_tool_rank
    mrr = mrr_sum / n if n else 0
    
    # Success rate
    success_count = sum(1 for r in results if r.success)
    success_rate = success_count / n if n else 0
    
    # Precision: Among tasks where expected tool was selected, % that succeeded
    selected_tasks = [r for r in results if r.expected_tool_visible]
    precision = sum(1 for r in selected_tasks if r.success) / len(selected_tasks) if selected_tasks else 0
    
    # Cost metrics
    avg_tools = sum(r.visible_tools_count for r in results) / n if n else 0
    avg_tokens = sum(r.context_tokens for r in results) / n if n else 0
    
    # Latency
    avg_selection = sum(r.selection_time_ms for r in results) / n if n else 0
    avg_execution = sum(r.execution_time_ms for r in results) / n if n else 0
    
    # Exploration
    exploration = sum(1 for r in results if r.exploration_triggered) / n if n else 0
    
    return EvalMetrics(
        mode=mode,
        total_tasks=n,
        recall_at_k=recall,
        precision_at_k=precision,
        mean_reciprocal_rank=mrr,
        success_rate=success_rate,
        avg_tools_selected=avg_tools,
        avg_context_tokens=avg_tokens,
        avg_selection_time_ms=avg_selection,
        avg_execution_time_ms=avg_execution,
        exploration_rate=exploration,
    )


async def run_single_task(
    server: UCPServer,
    task: dict,
    mode: str,
) -> TaskResult:
    """Run a single evaluation task."""
    result = TaskResult(
        mode=mode,
        task_id=task["id"],
        prompt=task["prompt"],
        expected_tool=task["expected_tool"],
    )
    
    try:
        # Reset session for each task
        server._current_session = None
        
        start_time = time.time()
        
        # 1. Update context with prompt
        await server.update_context(task["prompt"])
        
        # 2. List tools (trigger routing)
        selection_start = time.time()
        tools_list = await server._list_tools()
        selection_time = (time.time() - selection_start) * 1000
        
        visible_names = [t.name for t in tools_list]
        result.visible_tools_count = len(visible_names)
        result.trace = visible_names
        result.selection_time_ms = selection_time
        
        # 3. Check if expected tool is visible
        expected = task["expected_tool"]
        if expected in visible_names:
            result.expected_tool_visible = True
            result.expected_tool_rank = visible_names.index(expected) + 1
        
        # 4. Try to call the tool if visible
        if result.expected_tool_visible:
            args = task.get("expected_args_subset", {})
            exec_start = time.time()
            
            call_result = await server._call_tool(expected, args)
            exec_time = (time.time() - exec_start) * 1000
            
            result.success = call_result.success
            result.execution_time_ms = exec_time
            if not call_result.success:
                result.error = call_result.error
        
        # 5. Get context token estimate
        if server._last_routing:
            # Rough token estimate from reasoning length
            result.context_tokens = sum(len(t) // 4 for t in visible_names) * 10
            
            # Check if exploration was triggered (from reasoning)
            reasoning = server._last_routing.reasoning or ""
            if "exploration" in reasoning.lower():
                result.exploration_triggered = True
        
    except Exception as e:
        result.error = str(e)
    
    return result


async def run_suite(
    mode: str,
    config: UCPConfig,
    tasks: list[dict],
) -> list[TaskResult]:
    """Run evaluation suite for a single mode."""
    print(f"\n--- Running {mode.upper()} Mode ---")
    
    server = UCPServer(config)
    
    # Force eager connection pool for testing
    server.connection_pool = ConnectionPool(config)
    
    await server.initialize()
    
    results = []
    for i, task in enumerate(tasks, 1):
        print(f"  [{mode}] Task {i}/{len(tasks)}: {task['id']}")
        result = await run_single_task(server, task, mode)
        results.append(result)
        
        status = "✓" if result.success else ("○" if result.expected_tool_visible else "✗")
        print(f"    {status} Visible: {result.visible_tools_count}, Expected: {result.expected_tool_visible}")
    
    return results


def create_baseline_config(temp_dir: str, mock_server_path: str) -> UCPConfig:
    """Create baseline configuration (expose many tools)."""
    downstream = DownstreamServerConfig(
        name="mock-server",
        transport="stdio",
        command=sys.executable,
        args=[mock_server_path],
        tags=["mock"],
    )
    
    return UCPConfig(
        server={"name": "baseline", "transport": "stdio"},
        tool_zoo=ToolZooConfig(
            top_k=100,
            similarity_threshold=0.0,
            persist_directory=os.path.join(temp_dir, "baseline_chromadb"),
        ),
        router=RouterConfig(
            mode="hybrid",
            strategy="baseline",
            max_tools=20,
            min_tools=1,
        ),
        session=SessionConfig(persistence="memory"),
        telemetry=TelemetryConfig(enabled=False),
        bandit=BanditConfig(enabled=False),
        bias_learning=BiasLearningConfig(enabled=False),
        downstream_servers=[downstream],
    )


def create_sota_config(temp_dir: str, mock_server_path: str) -> UCPConfig:
    """Create SOTA configuration (intelligent selection)."""
    downstream = DownstreamServerConfig(
        name="mock-server",
        transport="stdio",
        command=sys.executable,
        args=[mock_server_path],
        tags=["mock"],
    )
    
    return UCPConfig(
        server={"name": "sota", "transport": "stdio"},
        tool_zoo=ToolZooConfig(
            top_k=10,
            similarity_threshold=0.1,
            persist_directory=os.path.join(temp_dir, "sota_chromadb"),
        ),
        router=RouterConfig(
            mode="hybrid",
            strategy="sota",
            max_tools=5,
            min_tools=1,
            candidate_pool_size=20,
            exploration_rate=0.0,  # Disable for eval
            use_cross_encoder=False,
        ),
        session=SessionConfig(persistence="memory"),
        telemetry=TelemetryConfig(
            enabled=True,
            db_path=os.path.join(temp_dir, "telemetry.db"),
        ),
        bandit=BanditConfig(
            enabled=True,
            db_path=os.path.join(temp_dir, "bandit.db"),
        ),
        bias_learning=BiasLearningConfig(
            enabled=True,
            db_path=os.path.join(temp_dir, "biases.db"),
        ),
        downstream_servers=[downstream],
    )


def generate_report(
    baseline_results: list[TaskResult],
    sota_results: list[TaskResult],
) -> dict:
    """Generate comparison report."""
    baseline_metrics = compute_metrics(baseline_results)
    sota_metrics = compute_metrics(sota_results)
    
    # Compute deltas
    deltas = {}
    for field_name in ["recall_at_k", "precision_at_k", "success_rate", "avg_tools_selected"]:
        baseline_val = getattr(baseline_metrics, field_name)
        sota_val = getattr(sota_metrics, field_name)
        deltas[field_name] = sota_val - baseline_val
    
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "baseline": asdict(baseline_metrics),
        "sota": asdict(sota_metrics),
        "deltas": deltas,
        "baseline_results": [asdict(r) for r in baseline_results],
        "sota_results": [asdict(r) for r in sota_results],
    }


def print_comparison(baseline_metrics: EvalMetrics, sota_metrics: EvalMetrics) -> None:
    """Print side-by-side comparison."""
    print("\n" + "=" * 60)
    print("EVALUATION COMPARISON: BASELINE vs SOTA")
    print("=" * 60)
    
    headers = ["Metric", "Baseline", "SOTA", "Delta"]
    rows = [
        ("Recall@k", f"{baseline_metrics.recall_at_k:.1%}", f"{sota_metrics.recall_at_k:.1%}", 
         f"{sota_metrics.recall_at_k - baseline_metrics.recall_at_k:+.1%}"),
        ("Precision@k", f"{baseline_metrics.precision_at_k:.1%}", f"{sota_metrics.precision_at_k:.1%}",
         f"{sota_metrics.precision_at_k - baseline_metrics.precision_at_k:+.1%}"),
        ("MRR", f"{baseline_metrics.mean_reciprocal_rank:.3f}", f"{sota_metrics.mean_reciprocal_rank:.3f}",
         f"{sota_metrics.mean_reciprocal_rank - baseline_metrics.mean_reciprocal_rank:+.3f}"),
        ("Success Rate", f"{baseline_metrics.success_rate:.1%}", f"{sota_metrics.success_rate:.1%}",
         f"{sota_metrics.success_rate - baseline_metrics.success_rate:+.1%}"),
        ("Avg Tools", f"{baseline_metrics.avg_tools_selected:.1f}", f"{sota_metrics.avg_tools_selected:.1f}",
         f"{sota_metrics.avg_tools_selected - baseline_metrics.avg_tools_selected:+.1f}"),
        ("Avg Selection (ms)", f"{baseline_metrics.avg_selection_time_ms:.1f}", f"{sota_metrics.avg_selection_time_ms:.1f}",
         f"{sota_metrics.avg_selection_time_ms - baseline_metrics.avg_selection_time_ms:+.1f}"),
        ("Exploration Rate", f"{baseline_metrics.exploration_rate:.1%}", f"{sota_metrics.exploration_rate:.1%}",
         f"{sota_metrics.exploration_rate - baseline_metrics.exploration_rate:+.1%}"),
    ]
    
    # Print table
    col_widths = [18, 12, 12, 12]
    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, col_widths))
    print(header_line)
    print("-" * len(header_line))
    
    for row in rows:
        print("  ".join(str(v).ljust(w) for v, w in zip(row, col_widths)))
    
    print("=" * 60)
    
    # Summary
    print("\nSUMMARY:")
    if sota_metrics.avg_tools_selected < baseline_metrics.avg_tools_selected:
        reduction = (1 - sota_metrics.avg_tools_selected / baseline_metrics.avg_tools_selected) * 100
        print(f"  ✓ SOTA reduces tools by {reduction:.0f}%")
    
    if sota_metrics.recall_at_k >= baseline_metrics.recall_at_k:
        print(f"  ✓ SOTA maintains or improves recall")
    else:
        print(f"  ✗ SOTA recall dropped by {baseline_metrics.recall_at_k - sota_metrics.recall_at_k:.1%}")


async def run_eval(tasks_path: str, report_path: str) -> None:
    """Run the full evaluation."""
    print(f"Loading tasks from {tasks_path}...")
    with open(tasks_path, "r") as f:
        tasks = json.load(f)
    
    print(f"Loaded {len(tasks)} tasks")
    
    # Setup
    mock_server_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../tests/mocks/mock_mcp_server.py")
    )
    
    # Check mock server exists
    if not os.path.exists(mock_server_path):
        print(f"Warning: Mock server not found at {mock_server_path}")
        print("Creating minimal mock server for evaluation...")
        os.makedirs(os.path.dirname(mock_server_path), exist_ok=True)
        with open(mock_server_path, "w") as f:
            f.write('''
# Minimal mock MCP server for evaluation
import sys
sys.exit(0)
''')
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run baseline
        baseline_config = create_baseline_config(temp_dir, mock_server_path)
        baseline_results = await run_suite("baseline", baseline_config, tasks)
        
        # Run SOTA
        sota_config = create_sota_config(temp_dir, mock_server_path)
        sota_results = await run_suite("sota", sota_config, tasks)
    
    # Generate report
    report = generate_report(baseline_results, sota_results)
    
    # Save report
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")
    
    # Print comparison
    baseline_metrics = compute_metrics(baseline_results)
    sota_metrics = compute_metrics(sota_results)
    print_comparison(baseline_metrics, sota_metrics)


def main() -> None:
    """Main entry point."""
    tasks_file = os.environ.get(
        "EVAL_TASKS",
        os.path.join(os.path.dirname(__file__), "tasks.json"),
    )
    report_file = os.environ.get(
        "EVAL_REPORT",
        os.path.join(os.path.dirname(__file__), "../../reports/eval_comparison.json"),
    )
    
    asyncio.run(run_eval(tasks_file, report_file))


if __name__ == "__main__":
    main()