# Patterns for Context Management

**Synthesis of:** MemGPT, LlamaIndex, and LangGraph

## 1. The Operating System Metaphor (MemGPT)
UCP should treat the LLM as a CPU and the Context Window as RAM.

*   **Virtual Memory:** Just as an OS pages memory to disk, UCP must "page out" old conversation turns and tool schemas to a persistent store (Vector DB or SQL).
*   **System Instructions (The Kernel):** The "Core Instructions" of UCP (e.g., "You are a helpful assistant...") act as the read-only kernel memory. They must always be present.
*   **Working Context (RAM):** Contains the immediate conversation history and the *currently active* tool schemas.
*   **Long-Term Storage (Disk):** Contains archival memory (user facts), the full Tool Zoo, and complete conversation logs.

## 2. Event-Driven Context (LangGraph)
Context is not static; it is a stream of events.

*   **State as a Graph:** The "Context" is the current state of the LangGraph. This state includes:
    *   messages: The list of chat messages.
    *   ctive_tools: The list of tools currently injected.
    *   scratchpad: Temporary variables for the current reasoning chain.
*   **Checkpoints:** Save this state after every node execution. This allows UCP to "hibernate" (save to DB) and "wake up" (load from DB) seamlessly, preserving the illusion of a continuous session.

## 3. Retrieval as Context Injection (LlamaIndex)
Don't stuff context; retrieve it.

*   **Schema RAG:** Instead of keeping all 100 available tools in the system prompt, use LlamaIndex to retrieve the 5 most relevant tools based on the user's latest message.
*   **Recursive Retrieval:** If a tool returns a massive JSON object (e.g., a 5MB log file), don't dump it into the context. Index that JSON on the fly and let the model query *it* with a secondary tool.

## 4. Recommendations for UCP
*   **Implement a Memory Manager Node:** In the LangGraph execution loop, add a node specifically for "Context Garbage Collection". This node runs before the LLM inference and summarizes/archives old messages.
*   **Separate Control Plane from Data Plane:**
    *   **Control Plane:** The LLM's reasoning and tool selection. Keep this context lean.
    *   **Data Plane:** The heavy lifting of tool execution and data processing. Keep this out of the context window.
