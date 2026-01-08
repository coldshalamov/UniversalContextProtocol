# Agent/MCP Design Lessons

**Synthesis of:** LangGraph, Gorilla, and General MCP Principles

## 1. The Cyclic Graph Architecture (LangGraph)
Linear chains (Start -> Step A -> Step B -> End) are insufficient for UCP. UCP requires a **State Machine** architecture.

*   **Cycles are Essential:** The agent must be able to loop:
    1.  User Input -> Model
    2.  Model -> Tool Call
    3.  Tool Output -> Model
    4.  Model -> *Another* Tool Call (Cycle) OR User Response (Exit)
*   **Interruptibility:** The graph must support pausing. If a tool requires human confirmation (e.g., "Delete Database"), the graph pauses, state is saved, and it waits for an external "Resume" signal.

## 2. The Universal Gateway (MCP Design)
UCP acts as a meta-server. It does not implement tools; it *proxies* them.

*   **Standardized Interface:** UCP should expose a standard MCP interface (list_tools, call_tool) to the client.
*   **Dynamic Tool Loading:** The list_tools endpoint should not return *all* tools. It should return the *subset* of tools currently loaded into the context window by the Router. This is a key insight: **The "Available Tools" list is dynamic and context-dependent.**
*   **Error Handling as Feedback:** If a tool call fails, the error message should be returned to the model, not just logged. The model can then self-correct (e.g., retry with different arguments).

## 3. The "Tool Zoo" (Gorilla)
*   **Diversity:** Support disparate tool sources (OpenAPI, Python scripts, MCP Servers).
*   **Normalization:** Convert all tool definitions into a common JSON schema format for indexing.
*   **Indexing:** Use LlamaIndex to create a vector index of these normalized schemas.

## 4. Recommendations for UCP
*   **Build on LangGraph:** Use LangGraph as the core execution engine. Define nodes for Router, Agent, ToolExecutor, and MemoryManager.
*   **Virtual MCP Server:** Implement UCP as a WebSocket/SSE server that adheres to the MCP spec but intercepts list_tools calls to return the *predicted* tools rather than the static list.
*   **Fail-Safe:** If the Router fails or the model hallucinates, have a fallback mechanism (e.g., a simple keyword search for tools).
