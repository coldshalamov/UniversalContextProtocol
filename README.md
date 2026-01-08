# Universal Context Protocol (UCP)

> **The missing layer between LLMs and their tools.** UCP solves "Tool Overload" by dynamically injecting only the relevant tool schemas based on conversation context.

## The Problem

When you connect an LLM to 100+ tools via MCP (Model Context Protocol), performance degrades:

- **Recall Failure**: The model struggles to pick the right tool among many distractors
- **Context Bloat**: Massive schemas consume your token budget
- **Latency**: Processing huge system prompts increases time-to-first-token
- **Cost**: You're billed for irrelevant tool descriptions on every turn

## The Solution

UCP is an **Intelligent Gateway** that sits between your MCP client (Claude Desktop, Cursor, etc.) and your fleet of MCP servers (GitHub, Slack, Gmail, etc.).

```
                    Traditional MCP                          With UCP
                    ===============                          ========

[Claude] <---> [GitHub MCP]                    [Claude] <---> [UCP Gateway] <---> [GitHub MCP]
         <---> [Slack MCP]                                          |        <---> [Slack MCP]
         <---> [Gmail MCP]                                    Dynamic Tool    <---> [Gmail MCP]
         <---> [100 more...]                                  Selection       <---> [100 more...]

Tools seen: ALL 500                            Tools seen: TOP 5 RELEVANT
```

Instead of `ListTools() -> [All 500 Tools]`, UCP implements `ListTools(context) -> [Top-5 Relevant Tools]`.

## Key Features

- **Semantic Tool Retrieval**: Vector-indexed tool schemas with hybrid semantic + keyword search
- **Context-Aware Routing**: Analyzes conversation to predict needed tools
- **Session Persistence**: Maintains state across turns with SQLite backend
- **Adaptive Learning**: Tracks tool usage patterns to improve predictions
- **Multiple Transports**: Stdio (Claude Desktop), HTTP/SSE (web apps)
- **Debug Dashboard**: Streamlit UI for visualizing routing decisions

## Quick Start

### Installation

```bash
pip install ucp

# Or from source
git clone https://github.com/your-org/UniversalContextProtocol
cd UniversalContextProtocol
pip install -e ".[dev]"
```

### Configuration

Create `ucp_config.yaml`:

```yaml
server:
  name: "My UCP Gateway"
  transport: stdio

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5

router:
  mode: hybrid
  max_tools: 10

downstream_servers:
  - name: github
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your-token"
    tags: [code, git]

  - name: gmail
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-gmail"]
    tags: [email, communication]
```

### Run UCP

```bash
# Index tools from downstream servers
ucp index

# Start the gateway (stdio mode)
ucp serve

# Or with HTTP transport
uvicorn ucp.http_server:get_app --port 8765
```

### Connect Claude Desktop

Add to your Claude Desktop config (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "path/to/ucp_config.yaml"]
    }
  }
}
```

Now Claude sees only the tools relevant to your current conversation!

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      UCP Gateway                             │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  Tool Zoo   │  │   Router    │  │  Session Manager    │ │
│  │  (ChromaDB) │◄─┤ (Semantic)  │◄─┤  (SQLite)           │ │
│  │             │  │             │  │                     │ │
│  │ - Embeddings│  │ - Domain    │  │ - Messages          │ │
│  │ - Hybrid    │  │   Detection │  │ - Tool Usage        │ │
│  │   Search    │  │ - Re-ranking│  │ - Checkpoints       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Connection Pool                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ GitHub   │ │  Gmail   │ │  Slack   │ │  Stripe  │  ...  │
│  │   MCP    │ │   MCP    │ │   MCP    │ │   MCP    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### The Routing Loop

1. **User Message**: "I need to send an email about the PR"
2. **Domain Detection**: Identifies "email" and "code" domains
3. **Tool Zoo Query**: Semantic search for relevant tools
4. **Re-ranking**: Boosts recently used tools, applies diversity filter
5. **Context Injection**: Returns only Gmail + GitHub tools to the LLM
6. **Tool Call**: Routes `gmail.send_email` to the Gmail MCP server
7. **Learning**: Records which tools were actually used

### Adaptive Learning

UCP learns from usage patterns:

```python
# After each session, UCP records:
# - Which tools were predicted
# - Which tools were actually used
# - Co-occurrence patterns (tools used together)

# This data can be exported for RAFT fine-tuning:
training_data = router.export_training_data()
```

## CLI Reference

```bash
# Start the UCP server
ucp serve [-c CONFIG] [--log-level DEBUG|INFO|WARNING|ERROR]

# Index tools from downstream servers
ucp index [-c CONFIG]

# Search for tools
ucp search QUERY [-k TOP_K] [--hybrid]

# Show server status
ucp status [-c CONFIG]

# Generate sample configuration
ucp init-config [-o OUTPUT_PATH]
```

## Debug Dashboard

Launch the Streamlit dashboard to visualize UCP internals:

```bash
pip install streamlit
streamlit run src/ucp/dashboard.py
```

Features:
- Search tools with live results
- View Tool Zoo statistics
- Explore session history
- Monitor router learning

## API Reference

### Python API

```python
from ucp import UCPServer, UCPConfig

# Load configuration
config = UCPConfig.load("ucp_config.yaml")

# Create server
server = UCPServer(config)

# Initialize (connects to downstream servers, indexes tools)
await server.initialize()

# Update conversation context
await server.update_context("I need to send an email")

# Get dynamically selected tools
tools = await server._list_tools()
# Returns only email-related tools!

# Execute a tool
result = await server._call_tool("gmail.send_email", {
    "to": "boss@company.com",
    "subject": "Update",
    "body": "Here's the update..."
})
```

### HTTP API

```bash
# List tools (context-aware)
GET /mcp/tools/list?session_id=xxx

# Call a tool
POST /mcp/tools/call
{
  "name": "gmail.send_email",
  "arguments": {"to": "...", "subject": "...", "body": "..."}
}

# Update context
POST /context/update
{
  "message": "I need to send an email",
  "role": "user"
}

# Search tools
GET /tools/search?query=send+email&top_k=5
```

## Structure

```
UniversalContextProtocol/
├── src/ucp/              # Core implementation
│   ├── server.py         # Main UCP server
│   ├── router.py         # Semantic routing
│   ├── tool_zoo.py       # Vector index
│   ├── session.py        # State management
│   ├── connection_pool.py # Downstream connections
│   ├── graph.py          # LangGraph integration
│   ├── http_server.py    # HTTP/SSE transport
│   └── dashboard.py      # Debug UI
├── tests/                # Test suite
├── docs/                 # Research & design docs
├── reports/              # Audit reports
└── ucp_config.yaml       # Configuration
```

## Research Foundation

UCP synthesizes ideas from:

- **[Gorilla](https://arxiv.org/abs/2305.15334)**: RAFT (Retrieval-Augmented Fine-Tuning) for tool selection
- **[ReAct](https://arxiv.org/abs/2210.03629)**: Interleaved reasoning and acting
- **[MemGPT](https://arxiv.org/abs/2310.11511)**: OS-style context management
- **[LangGraph](https://github.com/langchain-ai/langgraph)**: Cyclic state machine orchestration

See the [docs/](docs/) folder for detailed synthesis documents.

## Roadmap

- [x] Core MCP proxy functionality
- [x] Semantic tool retrieval (ChromaDB + sentence-transformers)
- [x] Hybrid search (semantic + keyword)
- [x] Session persistence (SQLite)
- [x] Adaptive learning from usage
- [x] HTTP/SSE transport
- [x] Debug dashboard
- [ ] GPU acceleration for embeddings
- [ ] Automated RAFT fine-tuning pipeline
- [ ] Redis session backend for distributed deployments
- [ ] Tool schema auto-discovery from OpenAPI specs

## Contributing

Contributions welcome! Please read the research docs in [docs/](docs/) first to understand the design philosophy.

```bash
# Setup development environment
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/ucp

# Linting
ruff check src/ucp
```

## License

MIT License

---

**UCP: Because your LLM shouldn't need to read 500 tool manuals to send an email.**
