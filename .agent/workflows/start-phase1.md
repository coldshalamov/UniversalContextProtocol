---
description: Start Phase 1 - Stabilize Core (Week 1, Milestone 1.1-1.3)
---

# Quick Start: Phase 1 Development

This workflow gets you started on the critical path to v1.0.

## Prerequisites
- Python 3.11+ installed
- UCP repo cloned
- Dependencies installed: `pip install -e ".[dev]"`

## Week 1, Day 1-2: Fix Failing Tests

// turbo
1. Run full test suite with verbose output
```bash
pytest tests/ -v --tb=long > test_results.txt 2>&1
```

2. Identify failing tests
```bash
grep "FAILED" test_results.txt
```

3. Fix each failing test:
   - Read the test file
   - Understand the assertion
   - Fix the implementation or test
   - Re-run: `pytest tests/contract/test_protocol.py -v`

4. Verify all tests pass
```bash
pytest tests/ -v
```

**Acceptance Criteria:** All 61 tests pass ✅

---

## Week 1, Day 3-5: Real MCP Server Integration

// turbo
1. Install filesystem MCP server
```bash
npm install -g @modelcontextprotocol/server-filesystem
```

2. Create test config `ucp_config_test.yaml`
```yaml
server:
  name: "UCP Test"
  transport: stdio

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5
  persist_directory: "./test_data/chromadb"

router:
  mode: hybrid
  max_tools: 10

session:
  persistence: sqlite
  db_path: "./test_data/sessions.db"

downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
    tags: [files, io]
```

// turbo
3. Index tools
```bash
ucp index -c ucp_config_test.yaml
```

// turbo
4. Test search
```bash
ucp search "read a file" -c ucp_config_test.yaml
```

5. Start UCP server in one terminal
```bash
ucp serve -c ucp_config_test.yaml --log-level DEBUG
```

6. In another terminal, test with Python client
```python
import asyncio
from ucp.client_api import UCPClient

async def test():
    client = UCPClient("http://localhost:8765")
    await client.update_context("I need to read a file")
    tools = await client.list_tools()
    print(f"Tools: {[t.name for t in tools]}")
    
asyncio.run(test())
```

**Acceptance Criteria:** UCP successfully indexes and routes filesystem tools ✅

---

## Week 1, Day 6-7: Claude Desktop Integration

1. Backup your Claude Desktop config
```bash
cp "%APPDATA%\Claude\claude_desktop_config.json" "%APPDATA%\Claude\claude_desktop_config.json.backup"
```

2. Update Claude config to use UCP
```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "C:/path/to/ucp_config_test.yaml"]
    }
  }
}
```

3. Restart Claude Desktop

4. Test conversation:
   - "List files in /tmp"
   - Verify filesystem tools are used
   - "What's the weather?" (should NOT show filesystem tools)

5. Record session with dashboard
```bash
streamlit run src/ucp/dashboard.py
```

**Acceptance Criteria:** Video demo of Claude using UCP with context switching ✅

---

## Next Steps

After completing Week 1:
- Move to Week 2: Observability & Metrics (Milestone 1.4-1.5)
- See `DEV_PLAN_TO_COMPLETION.md` for full roadmap

## Troubleshooting

**Tests still failing?**
- Check Python version: `python --version` (need 3.11+)
- Reinstall deps: `pip install -e ".[dev]" --force-reinstall`
- Clear pytest cache: `rm -rf .pytest_cache`

**UCP index fails?**
- Check ChromaDB directory exists: `mkdir -p test_data/chromadb`
- Verify embedding model downloads: `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"`

**Claude Desktop doesn't see UCP?**
- Check UCP is in PATH: `where ucp` (Windows) or `which ucp` (Mac/Linux)
- View Claude logs: `%APPDATA%\Claude\logs\mcp.log`
- Test stdio manually: `echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | ucp serve -c config.yaml`
