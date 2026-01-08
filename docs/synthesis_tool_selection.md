# Best Practices for Tool Selection and Orchestration

**Synthesis of:** Gorilla, ReAct, Toolformer, and LangGraph

## 1. Predictive Tool Selection (The "Gorilla" Approach)
Traditional tool use relies on injecting *all* tool schemas into the prompt. This fails at scale. The **Universal Context Protocol (UCP)** must adopt a **Retrieve-Then-Generate** pattern for tools.

*   **Retrieval-Aware Fine-Tuning (RAFT):** Do not just train the model to use tools. Train the model to *ignore* irrelevant tools.
    *   **Dataset Construction:** Create triplets of {User Query, Relevant Tools + Distractors, Correct API Call}.
    *   **Negative Constraints:** Explicitly teach the model that if the retrieved tools don't solve the problem, it should ask for clarification or search again, rather than hallucinating a function.
*   **The "Tool Zoo" Index:** Maintain a vector index of all available MCP tools. Use semantic search (LlamaIndex) to fetch the top-k candidates before the main inference step.

## 2. Interleaved Reasoning and Acting (The "ReAct" Pattern)
Tool use is not a one-shot process. It requires a cyclic loop.

*   **Thought-Action-Observation:** The model should output a "Thought" (reasoning about *why* it needs a tool), followed by the "Action" (the tool call).
*   **Observation Injection:** The result of the tool execution must be fed back into the context as an "Observation".
*   **Cycle Management:** Use a graph-based runtime (LangGraph) to manage this loop. The graph structure allows for:
    *   **Conditional Branching:** If tool execution fails, branch to a "Self-Correction" node.
    *   **State Persistence:** Save the reasoning trace (Thought chain) so the model doesn't lose context between tool calls.

## 3. Self-Supervised Tool Learning (The "Toolformer" Lesson)
Models can teach themselves to use tools.

*   **Implicit API Calls:** Instead of explicit function calling blocks, the model can learn to emit API calls inline with text (e.g., The capital of France is [QA("capital of France")]Paris).
*   **Bootstrapping:** UCP can start with a rule-based selector and use successful sessions (where the user didn't correct the model) to fine-tune the tool predictor.

## 4. Recommendations for UCP
*   **Implement a two-stage dispatch:**
    1.  **Stage 1 (Router):** A lightweight classifier or vector search identifies the *domain* of the query (e.g., "coding", "finance", "calendar").
    2.  **Stage 2 (Schema Injection):** Load the schemas for that domain into the context window.
*   **Dynamic Schema Pruning:** If a tool is rarely used in a session, unload its schema to save context tokens.
