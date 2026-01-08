# UCP Debugging Playbook

**"Why didn't the model call the tool?"**

This is the #1 question. This guide helps you diagnose and fix routing issues immediately.

## Quick Checks

1.  **Is the tool indexed?**
    Run `ucp search "your query"` to see if the tool appears in the vector store.
    ```bash
    ucp search "send email" --top-k 5
    ```
    *If missing:* Run `ucp index` to refresh the tool zoo.

2.  **Is the router confident?**
    Check the logs (default stderr) for the routing decision.
    Look for `[Router] Context: '...' -> Selected: [...]`.

3.  **Is `top_k` too low?**
    If the correct tool is ranked #6 but `top_k` is 5, it gets cut.
    *Fix:* Increase `tool_zoo.top_k` in `ucp_config.yaml`.

## "Today Fixes" (Workarounds)

### Issue: The tool is relevant but never selected.

**Diagnosis:** The semantic embedding of the tool description doesn't match the user's phrasing.

**Fix:** Add "keyword tags" to the downstream server config in `ucp_config.yaml`.

*Before:*
```yaml
- name: my-tool
  # ...
  tags: []
```

*After:*
```yaml
- name: my-tool
  # ...
  tags: ["urgent", "fix", "deploy", "magic_keyword"]
```

UCP's hybrid router heavily boosts tools with matching tags.

### Issue: The model hallucinates a tool that isn't offered.

**Diagnosis:** The model is ignoring the provided tool list and guessing.

**Fix:** Check the System Prompt. UCP injects tools, but if the model has strong priors, it might ignore them.
*Action:* Try changing `router.mode` to `keyword` temporarily to force a deterministic set of tools, checking if it's a retrieval issue or a model behavior issue.

### Issue: Downstream server is slow / timeout.

**Diagnosis:** UCP waits for the downstream server to list tools during indexing or execution.

**Fix:**
- Check downstream server logs.
- Increase timeouts in `connection_pool.py` (requires backend change - ask Agent A).
- Ensure the downstream server is actually running if it's a network service.

## Inspecting Trace IDs

Every UCP turn generates a `trace_id`.

1.  **Locate the log:** `ucp.log` or stderr.
2.  **Find the Trace:** Search for `trace_id=...`
3.  **Read the Decision:**
    ```json
    {
      "trace_id": "abc-123",
      "context_summary": "User wants to deploy",
      "candidates_retrieved": ["deploy.sh", "kubectl.apply"],
      "final_selection": ["deploy.sh"]
    }
    ```

If `candidates_retrieved` is empty, your embeddings are broken or the tool isn't indexed.
If `candidates_retrieved` has the tool but `final_selection` doesn't, the re-ranker or `top_k` cut it.
