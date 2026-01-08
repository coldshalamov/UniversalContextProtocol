# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

**Universal Context Protocol (UCP)** is an intelligent gateway that solves "Tool Overload" in agentic AI systems. It presents itself as a single MCP server to upstream clients (Claude Desktop, Cursor, etc.) while internally orchestrating a fleet of downstream MCP servers. The core innovation is **context-aware dynamic injection**—instead of flooding the LLM with all available tool schemas, UCP uses a predictive router to inject only the most relevant subset based on conversation context.

**The Problem:** When an LLM has access to 100+ tools, it struggles to select the right one. Context bloat, latency, and cost explode.

**The Solution:** `ListTools() -> [All 500 Tools]` becomes `ListTools(context) -> [Top-5 Relevant Tools]`

## Commands

```bash
# Install dependencies
pip install -e ".[dev]"

# Run UCP server (stdio mode for Claude Desktop)
ucp serve

# Run UCP server with custom config
ucp serve -c ucp_config.yaml

# Run HTTP server (for web applications)
uvicorn ucp.http_server:get_app --host 0.0.0.0 --port 8765

# Index tools from downstream servers
ucp index

# Search for tools
ucp search "send email" --top-k 5

# Generate sample config
ucp init-config -o ucp_config.yaml

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/ucp --cov-report=html

# Type checking
mypy src/ucp

# Linting
ruff check src/ucp
```

## Architecture

```
[MCP Client] <===> [UCP Gateway] <===> [Downstream Fleet]
(Claude/IDE)          |                    |
                      +-- Control Plane    +-- Gmail MCP
                      |   (Router/Index)   +-- GitHub MCP
                      |                    +-- Slack MCP
                      +-- Data Plane
                          (Proxy/Exec)
```

### Control Plane ("Brain")
- **Tool Zoo** ([tool_zoo.py](src/ucp/tool_zoo.py)): ChromaDB vector index of all tool schemas. Semantic + keyword hybrid search.
- **Router** ([router.py](src/ucp/router.py)): Predicts relevant tools from conversation context. Two-stage: retrieval → re-ranking.
- **Session Manager** ([session.py](src/ucp/session.py)): SQLite-backed state persistence. MemGPT-style context management.

### Data Plane ("Body")
- **Connection Pool** ([connection_pool.py](src/ucp/connection_pool.py)): Manages MCP server connections (stdio/SSE).
- **UCP Server** ([server.py](src/ucp/server.py)): Virtual MCP server that intercepts `tools/list` and `tools/call`.

### Runtime Loop
1. Client sends message → Session updated
2. Router analyzes context → Queries Tool Zoo
3. Top-k tools selected → `tools/list` returns subset
4. LLM sees only relevant tools → Makes better decisions
5. `tools/call` routed to correct downstream server
6. Result returned → Router may update active tools on topic shift

## Key Files

| File | Purpose |
|------|---------|
| [src/ucp/server.py](src/ucp/server.py) | Main UCP server - intercepts MCP protocol |
| [src/ucp/router.py](src/ucp/router.py) | Semantic router - predicts tool relevance |
| [src/ucp/tool_zoo.py](src/ucp/tool_zoo.py) | Vector index for tool retrieval |
| [src/ucp/session.py](src/ucp/session.py) | Session state and persistence |
| [src/ucp/connection_pool.py](src/ucp/connection_pool.py) | Downstream server connections |
| [src/ucp/graph.py](src/ucp/graph.py) | LangGraph state machine integration |
| [src/ucp/http_server.py](src/ucp/http_server.py) | HTTP/SSE transport for web clients |
| [src/ucp/config.py](src/ucp/config.py) | Configuration management |
| [src/ucp/models.py](src/ucp/models.py) | Core data models |

## Configuration

UCP is configured via `ucp_config.yaml`. See [ucp_config.example.yaml](ucp_config.example.yaml) for full options.

Key sections:
- `server`: Transport mode (stdio/sse/http), host, port
- `tool_zoo`: Embedding model, similarity threshold, top-k
- `router`: Mode (semantic/keyword/hybrid), max tools, fallbacks
- `session`: Persistence (memory/sqlite), TTL, max messages
- `downstream_servers`: List of MCP servers to connect

## Design Principles (from research)

1. **Retrieve-Then-Generate** (Gorilla/RAFT): Train the router to *ignore* irrelevant tools, not just find relevant ones.

2. **Cyclic Graph Architecture** (LangGraph): Tool use is a loop: Reason → Act → Observe → Reason. Not a linear chain.

3. **Virtual Memory** (MemGPT): Context window = RAM. Page out old messages. Keep tool schemas lean.

4. **Two-Stage Dispatch**: Stage 1 detects domain (email, code, finance). Stage 2 retrieves specific tools.

5. **Dynamic Pruning**: Tools unused in a session get unloaded. Frequently used tools get boosted.

## Adding a New Downstream Server

1. Add to `ucp_config.yaml`:
```yaml
downstream_servers:
  - name: my-server
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-example"]
    tags: [category, subcategory]
    description: "What this server does"
```

2. Run `ucp index` to discover and index its tools

3. Tools are automatically available through UCP

## Extending the Router

The `AdaptiveRouter` in [router.py](src/ucp/router.py) learns from usage patterns:

```python
# Record which tools were actually used
router.record_usage(routing_decision, actually_used_tools)

# Export data for RAFT fine-tuning
training_data = router.export_training_data()
```

## Research Foundation

This implementation synthesizes:
- **Gorilla** (RAFT): Retrieval-aware fine-tuning for tool selection
- **ReAct**: Interleaved reasoning and acting
- **MemGPT**: OS-style context management
- **LangGraph**: Cyclic state machine orchestration
- **LlamaIndex**: Vector indexing patterns

See [docs/](docs/) for detailed synthesis documents and research papers.

## RAFT Training Pipeline

UCP includes a complete training data pipeline for improving tool selection:

```python
from ucp import create_raft_pipeline, HybridToolZoo

# Create pipeline
generator, trainer = create_raft_pipeline(tool_zoo)

# Collect training data from router usage
generator.generate_example(query, candidates, correct_tools)

# Export for fine-tuning
trainer.prepare_dataset(router.export_training_data())
trainer.generate_training_config(base_model="meta-llama/Llama-3-8B")
```

See [src/ucp/raft.py](src/ucp/raft.py) for the full RAFT implementation.

## Debug Dashboard

Launch the Streamlit dashboard for debugging:

```bash
streamlit run src/ucp/dashboard.py
```

Features:
- Search tools with live preview
- View Tool Zoo statistics
- Explore session history and tool usage
- Monitor router learning and export training data

## Known Issues

- GPU acceleration not yet implemented for embeddings

## Project Structure

```
UniversalContextProtocol/
├── src/ucp/               # Core implementation
│   ├── __init__.py        # Public API exports
│   ├── server.py          # Main UCP server (MCP protocol)
│   ├── router.py          # Semantic router (Gorilla-style)
│   ├── tool_zoo.py        # Vector index (ChromaDB)
│   ├── session.py         # State persistence (SQLite)
│   ├── connection_pool.py # Downstream server connections
│   ├── graph.py           # LangGraph state machine
│   ├── http_server.py     # HTTP/SSE transport (FastAPI)
│   ├── transports.py      # SSE/HTTP client transports
│   ├── raft.py            # RAFT training pipeline
│   ├── dashboard.py       # Streamlit debug UI
│   ├── config.py          # Configuration management
│   ├── models.py          # Data models (Pydantic)
│   └── cli.py             # CLI entry point
├── tests/                 # Test suite
│   ├── test_tool_zoo.py   # Tool Zoo tests
│   ├── test_router.py     # Router tests
│   ├── test_session.py    # Session tests
│   ├── test_raft.py       # RAFT pipeline tests
│   └── test_integration.py # Full integration tests
├── docs/                  # Research & design docs
├── reports/               # Audit reports
├── data/                  # Runtime data (gitignored)
│   ├── chromadb/          # Vector database
│   ├── sessions.db        # Session storage
│   └── raft/              # Training data
└── ucp_config.yaml        # Configuration file
```
