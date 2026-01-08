# Feedback Loops, Evaluation, and Learning Signals

**Synthesis of:** Gorilla (BFCL), Toolformer, and ReAct

## 1. Evaluation Strategies (Gorilla/BFCL)
Evaluating tool use is harder than evaluating text generation. We need **Abstract Syntax Tree (AST) Matching**.

*   **Exact Match is Bad:** Code can be syntactically different but semantically identical.
*   **AST Matching:** Parse the model's generated tool call into an AST. Compare it against the AST of the "Gold Standard" call. If the function name and arguments match (regardless of whitespace or order), it is a success.
*   **Execution Evaluation:** For safe tools, actually execute the call and check the *result*.

## 2. Learning Signals (Toolformer/Self-Correction)
How does UCP improve over time?

*   **Implicit Feedback:**
    *   **Success:** If the user continues the conversation without correcting the model, assume the tool call was useful. Add this interaction to the "Positive" dataset.
    *   **Failure:** If the user says "That's wrong" or the tool returns an error, mark as "Negative".
*   **Self-Correction:**
    *   If a tool call fails (e.g., Invalid Argument), inject the error message back into the context.
    *   Prompt the model to "Fix the error".
    *   If the model fixes it, this trace (Error -> Fix) becomes excellent training data for fine-tuning.

## 3. Human-in-the-Loop Feedback (LangGraph)
*   **Interrupt-Resume:** Use LangGraph's interruption capability to let users "grade" tool calls before execution.
*   **Critique Node:** Add a "Critic" node (a smaller, cheaper LLM) that reviews the main LLM's plan before execution. If the Critic spots a hallucination, it loops back with feedback.

## 4. Recommendations for UCP
*   **Log Everything:** Store every interaction triplet (User Input, Predicted Tools, Model Action) in a structured log (e.g., SQLite via LangGraph Checkpointer).
*   **Offline RLHF:** Periodically export these logs. Use the "Success" traces to fine-tune the **Router Model** (Gorilla/RAFT approach) to make better tool predictions in the future.
*   **Sanity Checks:** Implement a pre-execution validation layer. If the model tries to call delete_database() and that tool isn't in the *injected* subset, block it immediately.
