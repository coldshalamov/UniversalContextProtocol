"""
Simple UCP Benchmark Script for Milestone 1.5
Demonstrates context reduction by comparing all tools vs filtered tools.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Add src to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(repo_root, "src"))

from ucp.server import UCPServer
from ucp.config import (
    UCPConfig,
    ToolZooConfig,
    RouterConfig,
    SessionConfig,
    TelemetryConfig,
    BanditConfig,
    BiasLearningConfig,
)
from ucp.models import ToolSchema


async def run_benchmark():
    """Run baseline and UCP benchmarks."""
    print("=" * 60)
    print("UCP BASELINE BENCHMARK - MILESTONE 1.5")
    print("=" * 60)
    
    # Load tasks
    tasks_path = os.path.join(os.path.dirname(__file__), "tasks.json")
    print(f"\nLoading tasks from {tasks_path}...")
    with open(tasks_path, "r") as f:
        tasks = json.load(f)
    print(f"Loaded {len(tasks)} tasks")
    
    # Create mock tools manually
    mock_tools = create_mock_tools()
    print(f"\nLoaded {len(mock_tools)} mock tools")
    
    # Create persistent directory for evaluation
    base_dir = os.path.join(repo_root, "data/eval_runs")
    os.makedirs(base_dir, exist_ok=True)
    
    run_id = f"run_{int(time.time())}"
    temp_dir = os.path.join(base_dir, run_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    print(f"\nEvaluation data directory: {temp_dir}")
    
    # Results storage
    baseline_results = []
    ucp_results = []
    
    # Create baseline config (all tools exposed)
    baseline_config = UCPConfig(
        server={"name": "baseline", "transport": "stdio"},
        tool_zoo=ToolZooConfig(
            top_k=100,
            similarity_threshold=0.0,
            persist_directory=os.path.join(temp_dir, "baseline_chromadb"),
        ),
        router=RouterConfig(
            mode="hybrid",
            strategy="baseline",
            max_tools=100,
            max_per_server=28,  # Allow all tools from same server
            min_tools=1,
        ),
        session=SessionConfig(
            persistence="memory",
            sqlite_path=os.path.join(temp_dir, "baseline_sessions.db"),
        ),
        telemetry=TelemetryConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "baseline_telemetry.db"),
        ),
        bandit=BanditConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "baseline_bandit.db"),
        ),
        bias_learning=BiasLearningConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "baseline_bias.db"),
        ),
        downstream_servers=[],
    )
    
    # Create UCP config (filtered tools)
    ucp_config = UCPConfig(
        server={"name": "ucp", "transport": "stdio"},
        tool_zoo=ToolZooConfig(
            top_k=10,
            similarity_threshold=0.1,
            persist_directory=os.path.join(temp_dir, "ucp_chromadb"),
        ),
        router=RouterConfig(
            mode="hybrid",
            strategy="sota",
            max_tools=5,
            max_per_server=3,
            min_tools=1,
            rerank=True,
        ),
        session=SessionConfig(
            persistence="memory",
            sqlite_path=os.path.join(temp_dir, "ucp_sessions.db"),
        ),
        telemetry=TelemetryConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "ucp_telemetry.db"),
        ),
        bandit=BanditConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "ucp_bandit.db"),
        ),
        bias_learning=BiasLearningConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "ucp_bias.db"),
        ),
        downstream_servers=[],
    )
    
    # Run baseline
    print("\n" + "-" * 60)
    print("RUNNING BASELINE (all tools)")
    print("-" * 60)
    baseline_server = UCPServer(baseline_config)
    try:
        await baseline_server.initialize()
        # Manually inject tools
        baseline_server.tool_zoo.add_tools(mock_tools)
        print(f"Injected {len(mock_tools)} tools into baseline server")
        
        for i, task in enumerate(tasks, 1):
            print(f"\n[{i}/{len(tasks)}] Task: {task['id']}")
            result = await run_single_task(baseline_server, task, "baseline", mock_tools)
            baseline_results.append(result)
            print(f"  Selected {result['tools_selected']} tools")
            print(f"  Expected tool found: {result['expected_tool_found']}")
    except Exception as e:
        print(f"Error in baseline run: {e}")
        import traceback
        traceback.print_exc()
    
    # Run UCP
    print("\n" + "-" * 60)
    print("RUNNING UCP (filtered tools)")
    print("-" * 60)
    ucp_server = UCPServer(ucp_config)
    try:
        await ucp_server.initialize()
        # Manually inject tools
        ucp_server.tool_zoo.add_tools(mock_tools)
        print(f"Injected {len(mock_tools)} tools into UCP server")
        
        for i, task in enumerate(tasks, 1):
            print(f"\n[{i}/{len(tasks)}] Task: {task['id']}")
            result = await run_single_task(ucp_server, task, "ucp", mock_tools)
            ucp_results.append(result)
            print(f"  Selected {result['tools_selected']} tools")
            print(f"  Expected tool found: {result['expected_tool_found']}")
    except Exception as e:
        print(f"Error in UCP run: {e}")
        import traceback
        traceback.print_exc()
    
    # Compute metrics
    baseline_metrics = compute_metrics(baseline_results)
    ucp_metrics = compute_metrics(ucp_results)
    
    # Print results
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    
    print("\nBASELINE:")
    print(f"  Avg tools selected: {baseline_metrics['avg_tools_selected']:.2f}")
    print(f"  Recall@k: {baseline_metrics['recall']:.1%}")
    print(f"  Precision@k: {baseline_metrics['precision']:.1%}")
    print(f"  Avg selection time (ms): {baseline_metrics['avg_selection_time']:.2f}")
    print(f"  Avg execution time (ms): {baseline_metrics['avg_execution_time']:.2f}")
    
    print("\nUCP:")
    print(f"  Avg tools selected: {ucp_metrics['avg_tools_selected']:.2f}")
    print(f"  Recall@k: {ucp_metrics['recall']:.1%}")
    print(f"  Precision@k: {ucp_metrics['precision']:.1%}")
    print(f"  Avg selection time (ms): {ucp_metrics['avg_selection_time']:.2f}")
    print(f"  Avg execution time (ms): {ucp_metrics['avg_execution_time']:.2f}")
    
    # Calculate context reduction
    if baseline_metrics['avg_tools_selected'] > 0:
        context_reduction = (
            1 - ucp_metrics['avg_tools_selected'] / baseline_metrics['avg_tools_selected']
        ) * 100
    else:
        context_reduction = 0.0
    
    print("\nCONTEXT REDUCTION:")
    print(f"  Tools reduced by: {context_reduction:.1f}%")
    print(f"  Baseline avg: {baseline_metrics['avg_tools_selected']:.2f} tools")
    print(f"  UCP avg: {ucp_metrics['avg_tools_selected']:.2f} tools")
    
    if context_reduction < 80:
        print("\n  WARNING: UCP did not achieve 80%+ context reduction")
    else:
        print("\n  SUCCESS: UCP achieved 80%+ context reduction!")
    
    # Generate report
    report = {
        "version": "0.1",
        "generated_at": datetime.utcnow().isoformat(),
        "tasks": tasks,
        "baseline": {
            "config": {
                "top_k": baseline_config.tool_zoo.top_k,
                "strategy": baseline_config.router.strategy,
                "max_tools": baseline_config.router.max_tools,
                "max_per_server": baseline_config.router.max_per_server,
            },
            "results": baseline_results,
            "metrics": baseline_metrics,
        },
        "ucp": {
            "config": {
                "top_k": ucp_config.tool_zoo.top_k,
                "strategy": ucp_config.router.strategy,
                "max_tools": ucp_config.router.max_tools,
                "max_per_server": ucp_config.router.max_per_server,
            },
            "results": ucp_results,
            "metrics": ucp_metrics,
        },
        "context_reduction": {
            "percentage": context_reduction,
            "baseline_avg": baseline_metrics['avg_tools_selected'],
            "ucp_avg": ucp_metrics['avg_tools_selected'],
            "target_80_percent": context_reduction >= 80,
        },
    }
    
    # Save report
    reports_dir = os.path.join(repo_root, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, "baseline_benchmark_v0.1.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")
    print(f"Evaluation data saved to: {temp_dir}")


async def run_single_task(server: UCPServer, task: dict, mode: str, all_tools: list[ToolSchema]) -> dict:
    """Run a single task and return results."""
    # Update context with task prompt
    await server.update_context(task["prompt"], role="user")
    
    # Get tool list (this triggers routing)
    start_time = time.time()
    tools = await server._list_tools()
    selection_time = (time.time() - start_time) * 1000
    
    # Check if expected tool is in selected tools
    expected_tool = task["expected_tool"]
    expected_tool_found = any(t.name == expected_tool for t in tools)
    
    # Estimate tokens (rough approximation)
    tools_json = json.dumps([{"name": t.name, "description": t.description} for t in tools])
    estimated_tokens = len(tools_json.split())  # Rough word count
    
    return {
        "task_id": task["id"],
        "mode": mode,
        "tools_selected": len(tools),
        "selected_tool_names": [t.name for t in tools],
        "expected_tool": expected_tool,
        "expected_tool_found": expected_tool_found,
        "selection_time_ms": selection_time,
        "execution_time_ms": 0.0,  # Not executing tools
        "estimated_tokens": estimated_tokens,
        "success": expected_tool_found,  # Success if tool found
    }


def compute_metrics(results: list) -> dict:
    """Compute metrics from results."""
    if not results:
        return {
            "avg_tools_selected": 0.0,
            "recall": 0.0,
            "precision": 0.0,
            "avg_selection_time": 0.0,
            "avg_execution_time": 0.0,
        }
    
    total_tools = sum(r["tools_selected"] for r in results)
    found_count = sum(1 for r in results if r["expected_tool_found"])
    total_selection_time = sum(r["selection_time_ms"] for r in results)
    total_execution_time = sum(r["execution_time_ms"] for r in results)
    
    # Precision: how many selected tools were actually used
    # For this benchmark, we consider tool found as "used"
    total_used = sum(1 for r in results if r["success"])
    total_selected = sum(r["tools_selected"] for r in results)
    
    avg_tools = total_tools / len(results)
    recall = found_count / len(results)
    precision = total_used / total_selected if total_selected > 0 else 0.0
    avg_selection_time = total_selection_time / len(results)
    avg_execution_time = total_execution_time / len(results)
    
    return {
        "avg_tools_selected": avg_tools,
        "recall": recall,
        "precision": precision,
        "avg_selection_time": avg_selection_time,
        "avg_execution_time": avg_execution_time,
    }


def create_mock_tools() -> list[ToolSchema]:
    """Create mock tools for benchmarking."""
    tools = [
        # Email tools
        ToolSchema(
            name="mock-server.mock.send_email",
            display_name="send_email",
            description="Send an email to a recipient",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"},
                },
                "required": ["to"],
            },
            tags=["email", "communication"],
        ),
        ToolSchema(
            name="mock-server.mock.read_inbox",
            display_name="read_inbox",
            description="Read and list emails from inbox",
            server_name="mock-server",
            input_schema={},
            tags=["email", "communication"],
        ),
        # Code tools
        ToolSchema(
            name="mock-server.mock.create_pr",
            display_name="create_pr",
            description="Create a pull request for a branch",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch name"},
                    "title": {"type": "string", "description": "PR title"},
                },
                "required": ["branch"],
            },
            tags=["code", "git"],
        ),
        ToolSchema(
            name="mock-server.mock.list_commits",
            display_name="list_commits",
            description="List recent commits on a branch",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch name"},
                    "limit": {"type": "integer", "description": "Max commits to return"},
                },
                "required": ["branch"],
            },
            tags=["code", "git"],
        ),
        # Calendar tools
        ToolSchema(
            name="mock-server.mock.create_event",
            display_name="create_event",
            description="Create a calendar event",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Event start time"},
                    "end_time": {"type": "string", "description": "Event end time"},
                },
                "required": ["title"],
            },
            tags=["calendar", "scheduling"],
        ),
        # Communication tools
        ToolSchema(
            name="mock-server.mock.send_slack",
            display_name="send_slack",
            description="Send a message to a Slack channel",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Slack channel"},
                    "message": {"type": "string", "description": "Message to send"},
                },
                "required": ["channel", "message"],
            },
            tags=["communication", "slack"],
        ),
        # File tools
        ToolSchema(
            name="mock-server.mock.upload_file",
            display_name="upload_file",
            description="Upload a file to cloud storage",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file"},
                    "destination": {"type": "string", "description": "Destination folder"},
                },
                "required": ["file_path"],
            },
            tags=["files", "storage"],
        ),
        # Web search tools
        ToolSchema(
            name="mock-server.mock.web_search",
            display_name="web_search",
            description="Search web for information",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results"},
                },
                "required": ["query"],
            },
            tags=["web", "search"],
        ),
        # Database tools
        ToolSchema(
            name="mock-server.mock.sql_query",
            display_name="sql_query",
            description="Execute a SQL query against database",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query"},
                },
                "required": ["query"],
            },
            tags=["database", "sql"],
        ),
        # Finance tools
        ToolSchema(
            name="mock-server.mock.stripe_charge",
            display_name="stripe_charge",
            description="Process a payment using Stripe",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Payment amount"},
                    "currency": {"type": "string", "description": "Currency code"},
                },
                "required": ["amount"],
            },
            tags=["finance", "payment"],
        ),
        # Additional tools for context bloat testing
        ToolSchema(
            name="mock-server.mock.list_files",
            display_name="list_files",
            description="List files in a directory",
            server_name="mock-server",
            input_schema={},
            tags=["files", "filesystem"],
        ),
        ToolSchema(
            name="mock-server.mock.read_file",
            display_name="read_file",
            description="Read file contents",
            server_name="mock-server",
            input_schema={},
            tags=["files", "filesystem"],
        ),
        ToolSchema(
            name="mock-server.mock.write_file",
            display_name="write_file",
            description="Write content to a file",
            server_name="mock-server",
            input_schema={},
            tags=["files", "filesystem"],
        ),
        ToolSchema(
            name="mock-server.mock.delete_file",
            display_name="delete_file",
            description="Delete a file",
            server_name="mock-server",
            input_schema={},
            tags=["files", "filesystem"],
        ),
        ToolSchema(
            name="mock-server.mock.create_directory",
            display_name="create_directory",
            description="Create a directory",
            server_name="mock-server",
            input_schema={},
            tags=["files", "filesystem"],
        ),
        ToolSchema(
            name="mock-server.mock.http_get",
            display_name="http_get",
            description="Make HTTP GET request",
            server_name="mock-server",
            input_schema={},
            tags=["http", "api"],
        ),
        ToolSchema(
            name="mock-server.mock.http_post",
            display_name="http_post",
            description="Make HTTP POST request",
            server_name="mock-server",
            input_schema={},
            tags=["http", "api"],
        ),
        ToolSchema(
            name="mock-server.mock.run_command",
            display_name="run_command",
            description="Execute a shell command",
            server_name="mock-server",
            input_schema={},
            tags=["system", "command"],
        ),
        ToolSchema(
            name="mock-server.mock.git_clone",
            display_name="git_clone",
            description="Clone a git repository",
            server_name="mock-server",
            input_schema={},
            tags=["git", "version-control"],
        ),
        ToolSchema(
            name="mock-server.mock.git_pull",
            display_name="git_pull",
            description="Pull from remote repository",
            server_name="mock-server",
            input_schema={},
            tags=["git", "version-control"],
        ),
        ToolSchema(
            name="mock-server.mock.git_push",
            display_name="git_push",
            description="Push to remote repository",
            server_name="mock-server",
            input_schema={},
            tags=["git", "version-control"],
        ),
        ToolSchema(
            name="mock-server.mock.docker_build",
            display_name="docker_build",
            description="Build a Docker image",
            server_name="mock-server",
            input_schema={},
            tags=["docker", "containers"],
        ),
        ToolSchema(
            name="mock-server.mock.docker_run",
            display_name="docker_run",
            description="Run a Docker container",
            server_name="mock-server",
            input_schema={},
            tags=["docker", "containers"],
        ),
        ToolSchema(
            name="mock-server.mock.kubectl_apply",
            display_name="kubectl_apply",
            description="Apply Kubernetes manifest",
            server_name="mock-server",
            input_schema={},
            tags=["kubernetes", "k8s"],
        ),
        ToolSchema(
            name="mock-server.mock.kubectl_get",
            display_name="kubectl_get",
            description="Get Kubernetes resources",
            server_name="mock-server",
            input_schema={},
            tags=["kubernetes", "k8s"],
        ),
        ToolSchema(
            name="mock-server.mock.aws_s3_upload",
            display_name="aws_s3_upload",
            description="Upload file to AWS S3",
            server_name="mock-server",
            input_schema={},
            tags=["aws", "cloud"],
        ),
        ToolSchema(
            name="mock-server.mock.aws_ec2_start",
            display_name="aws_ec2_start",
            description="Start AWS EC2 instance",
            server_name="mock-server",
            input_schema={},
            tags=["aws", "cloud"],
        ),
        ToolSchema(
            name="mock-server.mock.aws_lambda_invoke",
            display_name="aws_lambda_invoke",
            description="Invoke AWS Lambda function",
            server_name="mock-server",
            input_schema={},
            tags=["aws", "cloud"],
        ),
    ]
    
    return tools


if __name__ == "__main__":
    asyncio.run(run_benchmark())
Simple UCP Benchmark Script for Milestone 1.5
Demonstrates context reduction by comparing all tools vs filtered tools.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

# Add src to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, os.path.join(repo_root, "src"))

from ucp.server import UCPServer
from ucp.config import (
    UCPConfig,
    ToolZooConfig,
    RouterConfig,
    SessionConfig,
    TelemetryConfig,
    BanditConfig,
    BiasLearningConfig,
)
from ucp.models import ToolSchema


async def run_benchmark():
    """Run baseline and UCP benchmarks."""
    print("=" * 60)
    print("UCP BASELINE BENCHMARK - MILESTONE 1.5")
    print("=" * 60)
    
    # Load tasks
    tasks_path = os.path.join(os.path.dirname(__file__), "tasks.json")
    print(f"\nLoading tasks from {tasks_path}...")
    with open(tasks_path, "r") as f:
        tasks = json.load(f)
    print(f"Loaded {len(tasks)} tasks")
    
    # Create mock tools manually
    mock_tools = create_mock_tools()
    print(f"\nLoaded {len(mock_tools)} mock tools")
    
    # Create persistent directory for evaluation
    base_dir = os.path.join(repo_root, "data/eval_runs")
    os.makedirs(base_dir, exist_ok=True)
    
    run_id = f"run_{int(time.time())}"
    temp_dir = os.path.join(base_dir, run_id)
    os.makedirs(temp_dir, exist_ok=True)
    
    print(f"\nEvaluation data directory: {temp_dir}")
    
    # Results storage
    baseline_results = []
    ucp_results = []
    
    # Create baseline config (all tools exposed)
    baseline_config = UCPConfig(
        server={"name": "baseline", "transport": "stdio"},
        tool_zoo=ToolZooConfig(
            top_k=100,
            similarity_threshold=0.0,
            persist_directory=os.path.join(temp_dir, "baseline_chromadb"),
        ),
        router=RouterConfig(
            mode="hybrid",
            strategy="baseline",
            max_tools=100,
            max_per_server=28,  # Allow all tools from same server
            min_tools=1,
        ),
        session=SessionConfig(
            persistence="memory",
            sqlite_path=os.path.join(temp_dir, "baseline_sessions.db"),
        ),
        telemetry=TelemetryConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "baseline_telemetry.db"),
        ),
        bandit=BanditConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "baseline_bandit.db"),
        ),
        bias_learning=BiasLearningConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "baseline_bias.db"),
        ),
        downstream_servers=[],
    )
    
    # Create UCP config (filtered tools)
    ucp_config = UCPConfig(
        server={"name": "ucp", "transport": "stdio"},
        tool_zoo=ToolZooConfig(
            top_k=10,
            similarity_threshold=0.1,
            persist_directory=os.path.join(temp_dir, "ucp_chromadb"),
        ),
        router=RouterConfig(
            mode="hybrid",
            strategy="sota",
            max_tools=5,
            max_per_server=3,
            min_tools=1,
            rerank=True,
        ),
        session=SessionConfig(
            persistence="memory",
            sqlite_path=os.path.join(temp_dir, "ucp_sessions.db"),
        ),
        telemetry=TelemetryConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "ucp_telemetry.db"),
        ),
        bandit=BanditConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "ucp_bandit.db"),
        ),
        bias_learning=BiasLearningConfig(
            enabled=False,
            db_path=os.path.join(temp_dir, "ucp_bias.db"),
        ),
        downstream_servers=[],
    )
    
    # Run baseline
    print("\n" + "-" * 60)
    print("RUNNING BASELINE (all tools)")
    print("-" * 60)
    baseline_server = UCPServer(baseline_config)
    try:
        await baseline_server.initialize()
        # Manually inject tools
        baseline_server.tool_zoo.add_tools(mock_tools)
        print(f"Injected {len(mock_tools)} tools into baseline server")
        
        for i, task in enumerate(tasks, 1):
            print(f"\n[{i}/{len(tasks)}] Task: {task['id']}")
            result = await run_single_task(baseline_server, task, "baseline", mock_tools)
            baseline_results.append(result)
            print(f"  Selected {result['tools_selected']} tools")
            print(f"  Expected tool found: {result['expected_tool_found']}")
    except Exception as e:
        print(f"Error in baseline run: {e}")
        import traceback
        traceback.print_exc()
    
    # Run UCP
    print("\n" + "-" * 60)
    print("RUNNING UCP (filtered tools)")
    print("-" * 60)
    ucp_server = UCPServer(ucp_config)
    try:
        await ucp_server.initialize()
        # Manually inject tools
        ucp_server.tool_zoo.add_tools(mock_tools)
        print(f"Injected {len(mock_tools)} tools into UCP server")
        
        for i, task in enumerate(tasks, 1):
            print(f"\n[{i}/{len(tasks)}] Task: {task['id']}")
            result = await run_single_task(ucp_server, task, "ucp", mock_tools)
            ucp_results.append(result)
            print(f"  Selected {result['tools_selected']} tools")
            print(f"  Expected tool found: {result['expected_tool_found']}")
    except Exception as e:
        print(f"Error in UCP run: {e}")
        import traceback
        traceback.print_exc()
    
    # Compute metrics
    baseline_metrics = compute_metrics(baseline_results)
    ucp_metrics = compute_metrics(ucp_results)
    
    # Print results
    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    
    print("\nBASELINE:")
    print(f"  Avg tools selected: {baseline_metrics['avg_tools_selected']:.2f}")
    print(f"  Recall@k: {baseline_metrics['recall']:.1%}")
    print(f"  Precision@k: {baseline_metrics['precision']:.1%}")
    print(f"  Avg selection time (ms): {baseline_metrics['avg_selection_time']:.2f}")
    print(f"  Avg execution time (ms): {baseline_metrics['avg_execution_time']:.2f}")
    
    print("\nUCP:")
    print(f"  Avg tools selected: {ucp_metrics['avg_tools_selected']:.2f}")
    print(f"  Recall@k: {ucp_metrics['recall']:.1%}")
    print(f"  Precision@k: {ucp_metrics['precision']:.1%}")
    print(f"  Avg selection time (ms): {ucp_metrics['avg_selection_time']:.2f}")
    print(f"  Avg execution time (ms): {ucp_metrics['avg_execution_time']:.2f}")
    
    # Calculate context reduction
    if baseline_metrics['avg_tools_selected'] > 0:
        context_reduction = (
            1 - ucp_metrics['avg_tools_selected'] / baseline_metrics['avg_tools_selected']
        ) * 100
    else:
        context_reduction = 0.0
    
    print("\nCONTEXT REDUCTION:")
    print(f"  Tools reduced by: {context_reduction:.1f}%")
    print(f"  Baseline avg: {baseline_metrics['avg_tools_selected']:.2f} tools")
    print(f"  UCP avg: {ucp_metrics['avg_tools_selected']:.2f} tools")
    
    if context_reduction < 80:
        print("\n  WARNING: UCP did not achieve 80%+ context reduction")
    else:
        print("\n  SUCCESS: UCP achieved 80%+ context reduction!")
    
    # Generate report
    report = {
        "version": "0.1",
        "generated_at": datetime.utcnow().isoformat(),
        "tasks": tasks,
        "baseline": {
            "config": {
                "top_k": baseline_config.tool_zoo.top_k,
                "strategy": baseline_config.router.strategy,
                "max_tools": baseline_config.router.max_tools,
                "max_per_server": baseline_config.router.max_per_server,
            },
            "results": baseline_results,
            "metrics": baseline_metrics,
        },
        "ucp": {
            "config": {
                "top_k": ucp_config.tool_zoo.top_k,
                "strategy": ucp_config.router.strategy,
                "max_tools": ucp_config.router.max_tools,
                "max_per_server": ucp_config.router.max_per_server,
            },
            "results": ucp_results,
            "metrics": ucp_metrics,
        },
        "context_reduction": {
            "percentage": context_reduction,
            "baseline_avg": baseline_metrics['avg_tools_selected'],
            "ucp_avg": ucp_metrics['avg_tools_selected'],
            "target_80_percent": context_reduction >= 80,
        },
    }
    
    # Save report
    reports_dir = os.path.join(repo_root, "reports")
    os.makedirs(reports_dir, exist_ok=True)
    report_path = os.path.join(reports_dir, "baseline_benchmark_v0.1.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nReport saved to: {report_path}")
    print(f"Evaluation data saved to: {temp_dir}")


async def run_single_task(server: UCPServer, task: dict, mode: str, all_tools: list[ToolSchema]) -> dict:
    """Run a single task and return results."""
    # Update context with task prompt
    await server.update_context(task["prompt"], role="user")
    
    # Get tool list (this triggers routing)
    start_time = time.time()
    tools = await server._list_tools()
    selection_time = (time.time() - start_time) * 1000
    
    # Check if expected tool is in selected tools
    expected_tool = task["expected_tool"]
    expected_tool_found = any(t.name == expected_tool for t in tools)
    
    # Estimate tokens (rough approximation)
    tools_json = json.dumps([{"name": t.name, "description": t.description} for t in tools])
    estimated_tokens = len(tools_json.split())  # Rough word count
    
    return {
        "task_id": task["id"],
        "mode": mode,
        "tools_selected": len(tools),
        "selected_tool_names": [t.name for t in tools],
        "expected_tool": expected_tool,
        "expected_tool_found": expected_tool_found,
        "selection_time_ms": selection_time,
        "execution_time_ms": 0.0,  # Not executing tools
        "estimated_tokens": estimated_tokens,
        "success": expected_tool_found,  # Success if tool found
    }


def compute_metrics(results: list) -> dict:
    """Compute metrics from results."""
    if not results:
        return {
            "avg_tools_selected": 0.0,
            "recall": 0.0,
            "precision": 0.0,
            "avg_selection_time": 0.0,
            "avg_execution_time": 0.0,
        }
    
    total_tools = sum(r["tools_selected"] for r in results)
    found_count = sum(1 for r in results if r["expected_tool_found"])
    total_selection_time = sum(r["selection_time_ms"] for r in results)
    total_execution_time = sum(r["execution_time_ms"] for r in results)
    
    # Precision: how many selected tools were actually used
    # For this benchmark, we consider tool found as "used"
    total_used = sum(1 for r in results if r["success"])
    total_selected = sum(r["tools_selected"] for r in results)
    
    avg_tools = total_tools / len(results)
    recall = found_count / len(results)
    precision = total_used / total_selected if total_selected > 0 else 0.0
    avg_selection_time = total_selection_time / len(results)
    avg_execution_time = total_execution_time / len(results)
    
    return {
        "avg_tools_selected": avg_tools,
        "recall": recall,
        "precision": precision,
        "avg_selection_time": avg_selection_time,
        "avg_execution_time": avg_execution_time,
    }


def create_mock_tools() -> list[ToolSchema]:
    """Create mock tools for benchmarking."""
    tools = [
        # Email tools
        ToolSchema(
            name="mock-server.mock.send_email",
            display_name="send_email",
            description="Send an email to a recipient",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"},
                },
                "required": ["to"],
            },
            tags=["email", "communication"],
        ),
        ToolSchema(
            name="mock-server.mock.read_inbox",
            display_name="read_inbox",
            description="Read and list emails from inbox",
            server_name="mock-server",
            input_schema={},
            tags=["email", "communication"],
        ),
        # Code tools
        ToolSchema(
            name="mock-server.mock.create_pr",
            display_name="create_pr",
            description="Create a pull request for a branch",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch name"},
                    "title": {"type": "string", "description": "PR title"},
                },
                "required": ["branch"],
            },
            tags=["code", "git"],
        ),
        ToolSchema(
            name="mock-server.mock.list_commits",
            display_name="list_commits",
            description="List recent commits on a branch",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch name"},
                    "limit": {"type": "integer", "description": "Max commits to return"},
                },
                "required": ["branch"],
            },
            tags=["code", "git"],
        ),
        # Calendar tools
        ToolSchema(
            name="mock-server.mock.create_event",
            display_name="create_event",
            description="Create a calendar event",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Event start time"},
                    "end_time": {"type": "string", "description": "Event end time"},
                },
                "required": ["title"],
            },
            tags=["calendar", "scheduling"],
        ),
        # Communication tools
        ToolSchema(
            name="mock-server.mock.send_slack",
            display_name="send_slack",
            description="Send a message to a Slack channel",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Slack channel"},
                    "message": {"type": "string", "description": "Message to send"},
                },
                "required": ["channel", "message"],
            },
            tags=["communication", "slack"],
        ),
        # File tools
        ToolSchema(
            name="mock-server.mock.upload_file",
            display_name="upload_file",
            description="Upload a file to cloud storage",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to file"},
                    "destination": {"type": "string", "description": "Destination folder"},
                },
                "required": ["file_path"],
            },
            tags=["files", "storage"],
        ),
        # Web search tools
        ToolSchema(
            name="mock-server.mock.web_search",
            display_name="web_search",
            description="Search web for information",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "integer", "description": "Number of results"},
                },
                "required": ["query"],
            },
            tags=["web", "search"],
        ),
        # Database tools
        ToolSchema(
            name="mock-server.mock.sql_query",
            display_name="sql_query",
            description="Execute a SQL query against database",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query"},
                },
                "required": ["query"],
            },
            tags=["database", "sql"],
        ),
        # Finance tools
        ToolSchema(
            name="mock-server.mock.stripe_charge",
            display_name="stripe_charge",
            description="Process a payment using Stripe",
            server_name="mock-server",
            input_schema={
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Payment amount"},
                    "currency": {"type": "string", "description": "Currency code"},
                },
                "required": ["amount"],
            },
            tags=["finance", "payment"],
        ),
        # Additional tools for context bloat testing
        ToolSchema(
            name="mock-server.mock.list_files",
            display_name="list_files",
            description="List files in a directory",
            server_name="mock-server",
            input_schema={},
            tags=["files", "filesystem"],
        ),
        ToolSchema(
            name="mock-server.mock.read_file",
            display_name="read_file",
            description="Read file contents",
            server_name="mock-server",
            input_schema={},
            tags=["files", "filesystem"],
        ),
        ToolSchema(
            name="mock-server.mock.write_file",
            display_name="write_file",
            description="Write content to a file",
            server_name="mock-server",
            input_schema={},
            tags=["files", "filesystem"],
        ),
        ToolSchema(
            name="mock-server.mock.delete_file",
            display_name="delete_file",
            description="Delete a file",
            server_name="mock-server",
            input_schema={},
            tags=["files", "filesystem"],
        ),
        ToolSchema(
            name="mock-server.mock.create_directory",
            display_name="create_directory",
            description="Create a directory",
            server_name="mock-server",
            input_schema={},
            tags=["files", "filesystem"],
        ),
        ToolSchema(
            name="mock-server.mock.http_get",
            display_name="http_get",
            description="Make HTTP GET request",
            server_name="mock-server",
            input_schema={},
            tags=["http", "api"],
        ),
        ToolSchema(
            name="mock-server.mock.http_post",
            display_name="http_post",
            description="Make HTTP POST request",
            server_name="mock-server",
            input_schema={},
            tags=["http", "api"],
        ),
        ToolSchema(
            name="mock-server.mock.run_command",
            display_name="run_command",
            description="Execute a shell command",
            server_name="mock-server",
            input_schema={},
            tags=["system", "command"],
        ),
        ToolSchema(
            name="mock-server.mock.git_clone",
            display_name="git_clone",
            description="Clone a git repository",
            server_name="mock-server",
            input_schema={},
            tags=["git", "version-control"],
        ),
        ToolSchema(
            name="mock-server.mock.git_pull",
            display_name="git_pull",
            description="Pull from remote repository",
            server_name="mock-server",
            input_schema={},
            tags=["git", "version-control"],
        ),
        ToolSchema(
            name="mock-server.mock.git_push",
            display_name="git_push",
            description="Push to remote repository",
            server_name="mock-server",
            input_schema={},
            tags=["git", "version-control"],
        ),
        ToolSchema(
            name="mock-server.mock.docker_build",
            display_name="docker_build",
            description="Build a Docker image",
            server_name="mock-server",
            input_schema={},
            tags=["docker", "containers"],
        ),
        ToolSchema(
            name="mock-server.mock.docker_run",
            display_name="docker_run",
            description="Run a Docker container",
            server_name="mock-server",
            input_schema={},
            tags=["docker", "containers"],
        ),
        ToolSchema(
            name="mock-server.mock.kubectl_apply",
            display_name="kubectl_apply",
            description="Apply Kubernetes manifest",
            server_name="mock-server",
            input_schema={},
            tags=["kubernetes", "k8s"],
        ),
        ToolSchema(
            name="mock-server.mock.kubectl_get",
            display_name="kubectl_get",
            description="Get Kubernetes resources",
            server_name="mock-server",
            input_schema={},
            tags=["kubernetes", "k8s"],
        ),
        ToolSchema(
            name="mock-server.mock.aws_s3_upload",
            display_name="aws_s3_upload",
            description="Upload file to AWS S3",
            server_name="mock-server",
            input_schema={},
            tags=["aws", "cloud"],
        ),
        ToolSchema(
            name="mock-server.mock.aws_ec2_start",
            display_name="aws_ec2_start",
            description="Start AWS EC2 instance",
            server_name="mock-server",
            input_schema={},
            tags=["aws", "cloud"],
        ),
        ToolSchema(
            name="mock-server.mock.aws_lambda_invoke",
            display_name="aws_lambda_invoke",
            description="Invoke AWS Lambda function",
            server_name="mock-server",
            input_schema={},
            tags=["aws", "cloud"],
        ),
    ]
    
    return tools


if __name__ == "__main__":
    asyncio.run(run_benchmark())

