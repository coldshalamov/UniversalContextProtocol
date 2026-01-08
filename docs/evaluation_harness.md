# UCP Evaluation Harness

We don't guess; we measure. The evaluation harness proves whether UCP is actually helping or hurting compared to a raw MCP connection.

## The Baselines

We compare three modes:

1.  **Baseline (All Tools):** The "Control". `top_k=100`. The LLM sees every tool available.
    -   *Pros:* Maximum recall.
    -   *Cons:* High token cost, confusion, latency.

2.  **UCP (Filtered):** The "Test". `top_k=N` (usually 5-10). The LLM sees a curated list.
    -   *Goal:* Maintain Recall while drastically reducing Context Size.

## Running the Harness

The harness is located in `clients/harness/`.

1.  **Define Tasks:**
    Edit `clients/harness/tasks.json`. Add prompt/expected_tool pairs.
    ```json
    {
      "id": "test_payment_01",
      "prompt": "Charge the user $50",
      "expected_tool": "stripe.charge",
      "expected_args_subset": {"amount": 50}
    }
    ```

2.  **Run the Script:**
    ```bash
    python clients/harness/run_eval.py
    ```

3.  **View Report:**
    Results are saved to `reports/validation_report.json`.
    Summary is printed to stdout.

## Interpreting Results

**Success Criteria:**

-   **Recall:** UCP should have >90% recall compared to Baseline. (i.e., it didn't hide the tool we needed).
-   **Context Reduction:** Avg Tools Exposed should be `top_k` (e.g., 5) vs Baseline (e.g., 50).

If Recall drops, your Router needs tuning (better embeddings, more keywords, or higher `top_k`).
