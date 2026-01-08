# Roadmap: Edge & Integration (Agent B)

**Owner:** Agent B
**Focus:** Clients, Documentation, Testing, Validation

## Current Status (v0.1)

- ✅ **Documentation:** Operator manual (Getting Started, Debugging, Eval) created.
- ✅ **Testing:** Contract tests for `tools/list` and `tools/call` established.
- ✅ **Validation:** Evaluation harness (`clients/harness`) ready for regression testing.
- ✅ **Mocks:** Standalone Mock MCP server for deterministic testing.

## Near-Term Goals (v0.2)

### 1. Client Adapters
- **Goal:** Create "thin" adapters for popular frameworks.
- **Items:**
    - `clients/adapters/langchain.py`: Adapter to use UCP as a generic ToolRetriever in LangChain.
    - `clients/adapters/autogen.py`: UCP integration for AutoGen agents.

### 2. Advanced Evaluation
- **Goal:** Real LLM-based evaluation.
- **Items:**
    - Upgrade `run_eval.py` to actually call an LLM (via LiteLLM or similar) instead of simulating the call.
    - Measure "Success Rate" based on actual tool output, not just visibility.

### 3. Resilience Testing
- **Goal:** Verify behavior under failure.
- **Items:**
    - Test UCP behavior when downstream server crashes.
    - Test UCP behavior when downstream server returns malformed JSON.

## Long-Term Vision (v1.0)

- **"One-Click" Installers:** executables that set up UCP + common tools.
- **Visual Debugger:** A web UI that shows the real-time routing decision tree (integrating with `dashboard.py`).
- **Community Tool Zoo:** A shared index of common tool definitions (tags/descriptions) that are known to work well with UCP.
