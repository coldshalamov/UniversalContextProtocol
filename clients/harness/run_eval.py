import asyncio
import json
import sys
import os
import time
from typing import List, Dict, Any
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from ucp.server import UCPServer
from ucp.config import UCPConfig, DownstreamServerConfig, ToolZooConfig, RouterConfig, SessionConfig

async def run_eval(tasks_path: str, report_path: str):
    print(f"Loading tasks from {tasks_path}...")
    with open(tasks_path, "r") as f:
        tasks = json.load(f)

    # Setup configurations
    mock_server_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../tests/mocks/mock_mcp_server.py"))
    
    downstream = DownstreamServerConfig(
        name="mock-server",
        transport="stdio",
        command=sys.executable,
        args=[mock_server_path],
        tags=["mock"]
    )

    # Baseline Config: Expose ALL tools (simulated by high top_k)
    baseline_config = UCPConfig(
        server={"name": "baseline", "transport": "stdio"},
        tool_zoo=ToolZooConfig(top_k=100, similarity_threshold=0.0, persist_directory=":memory:"),
        router=RouterConfig(mode="keyword", max_tools=100),
        session=SessionConfig(persistence="memory"),
        downstream_servers=[downstream]
    )

    # UCP Config: Strict filtering
    ucp_config = UCPConfig(
        server={"name": "ucp", "transport": "stdio"},
        tool_zoo=ToolZooConfig(top_k=1, similarity_threshold=0.1, persist_directory=":memory:"),
        router=RouterConfig(mode="keyword", max_tools=1),
        session=SessionConfig(persistence="memory"),
        downstream_servers=[downstream]
    )

    results = []

    print("\n--- Running Baseline (All Tools) ---")
    baseline_results = await run_suite("baseline", baseline_config, tasks)
    results.extend(baseline_results)

    print("\n--- Running UCP (Top-1 Filter) ---")
    ucp_results = await run_suite("ucp", ucp_config, tasks)
    results.extend(ucp_results)

    # Generate Report
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nEvaluation complete. Results saved to {report_path}")
    print_summary(results)

async def run_suite(mode: str, config: UCPConfig, tasks: List[Dict]) -> List[Dict]:
    server = UCPServer(config)
    await server.initialize()
    
    suite_results = []
    
    for task in tasks:
        print(f"[{mode}] Running task: {task['id']}")
        start_time = time.time()
        
        # 1. Update Context
        await server.update_context(task['prompt'])
        
        # 2. List Tools (Simulate LLM seeing tools)
        tools_resp = await server.list_tools()
        tools_list = tools_resp.get("tools", [])
        visible_tool_names = [t['name'] for t in tools_list]
        
        # 3. Check if expected tool is visible
        expected_tool = task['expected_tool']
        tool_visible = expected_tool in visible_tool_names
        
        # 4. Call Tool (Simulate LLM picking correct tool if visible)
        success = False
        execution_result = None
        
        if tool_visible:
            # Simulate correct args (idealized LLM)
            # In a real harness, we'd use an LLM here to generate args
            args = task.get("expected_args_subset", {})
            try:
                execution_result = await server.call_tool(expected_tool, args)
                success = True
            except Exception as e:
                execution_result = str(e)
                success = False
        
        duration = time.time() - start_time
        
        suite_results.append({
            "mode": mode,
            "task_id": task['id'],
            "visible_tools_count": len(visible_tool_names),
            "expected_tool_visible": tool_visible,
            "success": success,
            "duration": duration,
            "trace": visible_tool_names
        })
        
    return suite_results

def print_summary(results: List[Dict]):
    modes = set(r['mode'] for r in results)
    print("\n--- Summary ---")
    for mode in modes:
        mode_results = [r for r in results if r['mode'] == mode]
        total = len(mode_results)
        visible = sum(1 for r in mode_results if r['expected_tool_visible'])
        avg_tools = sum(r['visible_tools_count'] for r in mode_results) / total
        print(f"{mode.upper()}:")
        print(f"  Recall: {visible}/{total} ({visible/total:.1%})")
        print(f"  Avg Tools Exposed: {avg_tools:.1f}")

if __name__ == "__main__":
    tasks_file = os.path.join(os.path.dirname(__file__), "tasks.json")
    report_file = os.path.join(os.path.dirname(__file__), "../../reports/validation_report.json")
    asyncio.run(run_eval(tasks_file, report_file))
