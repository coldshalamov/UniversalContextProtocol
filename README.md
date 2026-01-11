# Universal Context Protocol (UCP)

> **The missing layer between LLMs and their tools.** UCP solves "Tool Overload" by dynamically injecting only the relevant tool schemas based on conversation context.

## Dual-Track Architecture

UCP is now organized into two complementary tracks with shared components:

### 🏠 Local-First MVP (Open Source)
- **Privacy-first**: All data stays on your machine
- **Simplicity**: Easy to install and use
- **Immediate value**: Core routing functionality without complexity
- **Open source**: Free to use and modify

**Location**: [`local/`](local/)  
**Installation**: `pip install ucp-mvp`  
**Status**: ✅ Available now

### ☁️ Cloud Version (Future Business)
- **Scalability**: Horizontal scaling with Kubernetes
- **Multi-tenancy**: Isolated tenant environments
- **Enterprise-ready**: SSO, RBAC, compliance features
- **SOTA features**: Full routing pipeline, RAFT fine-tuning, LangGraph

**Location**: [`cloud/`](cloud/)  
**Status**: 📋 Planned, not yet implemented

### 🔗 Shared Components
Common code used by both versions:
- **Data Models**: Common data structures
- **Configuration**: Shared configuration classes
- **Interfaces**: Abstract interfaces for compatibility
- **Transport**: MCP protocol implementation

**Location**: [`shared/`](shared/)  
**Package**: `pip install ucp-core`

---

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

### Local MVP Features
- **Semantic Tool Retrieval**: Vector-indexed tool schemas with hybrid semantic + keyword search
- **Context-Aware Routing**: Analyzes conversation to predict needed tools
- **Session Persistence**: Maintains state across turns with SQLite backend
- **Adaptive Learning**: Tracks tool usage patterns to improve predictions
- **Multiple Transports**: Stdio (Claude Desktop), HTTP/SSE (web apps)
- **Debug Dashboard**: Streamlit UI for visualizing routing decisions

### Cloud Version Features (Future)
- All Local MVP features plus:
- **Cross-Encoder Reranking**: Advanced tool ranking
- **Bandit Exploration**: Intelligent tool discovery
- **Online Optimization**: Continuous improvement
- **RAFT Fine-Tuning**: Custom model training
- **LangGraph Orchestration**: Complex workflow support
- **Centralized Telemetry**: Enterprise observability

## Benchmark Results

UCP has been tested with a baseline benchmark comparing tool selection performance between traditional MCP (exposing all tools) and UCP (intelligent tool filtering).

### Performance Metrics (v0.1)

| Metric | Baseline (All Tools) | UCP (Filtered) | Improvement |
|---|---|---|---|
| Avg Tools Selected | 3.00 | 3.00 | 0.0% |
| Recall@k | 60.0% | 60.0% | 0.0% |
| Precision@k | 20.0% | 20.0% | 0.0% |
| Selection Time (ms) | 28.53 | 25.99 | 8.9% faster |
| Execution Time (ms) | 0.00 | 0.00 | N/A |

### Context Reduction

- **Baseline Average:** 3.00 tools
- **UCP Average:** 3.00 tools
- **Context Reduction:** 0.0%
- **Target:** 80%+

**Note:** The current benchmark did not achieve the 80%+ context reduction target due to a hardcoded `max_per_server = 3` limit in the router's reranking logic. This limitation affects single-server deployments. See [`docs/milestone_1_5_baseline_benchmark.md`](docs/milestone_1_5_baseline_benchmark.md) for detailed analysis.

### Test Coverage

The benchmark tested 10 diverse tasks across multiple domains:
- Email (send, read)
- Code (PR creation, commit listing)
- Calendar (event scheduling)
- Communication (Slack messaging)
- Files (upload)
- Web (search)
- Database (SQL queries)
- Finance (payment processing)

For complete benchmark details, see [`clients/reports/baseline_benchmark_v0.1.json`](clients/reports/baseline_benchmark_v0.1.json).

## Quick Start

### Local MVP (Available Now)

```bash
pip install ucp-mvp
ucp init-config
ucp serve
```

### Claude Desktop Integration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "~/.ucp/ucp_config.yaml"]
    }
  }
}
```

### Cloud Version (Coming Soon)

The cloud version is currently in planning. See [`cloud/docs/roadmap.md`](cloud/docs/roadmap.md) for the implementation timeline.

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

1. **User Message**: "I need to send an email about a PR"
2. **Domain Detection**: Identifies "email" and "code" domains
3. **Tool Zoo Query**: Semantic search for relevant tools
4. **Re-ranking**: Boosts recently used tools, applies diversity filter
5. **Context Injection**: Returns only Gmail + GitHub tools to LLM
6. **Tool Call**: Routes `gmail.send_email` to Gmail MCP server
7. **Learning**: Records which tools were actually used

## Project Structure

```
UniversalContextProtocol/
├── README.md                          # This file
├── DEVELOPMENT_GUIDE.md              # Development guidelines
├── LICENSE                            # MIT license
├── .gitignore
├── pyproject.toml                     # Root project config
├── ucp_config.example.yaml            # Shared config template
│
├── shared/                            # SHARED CODE BETWEEN VERSIONS
│   ├── README.md                     # Shared components documentation
│   ├── src/
│   │   ├── ucp_core/                # Core abstractions and interfaces
│   │   └── ucp_transport/            # Transport layer abstractions
│   ├── tests/
│   ├── docs/
│   │   └── api_reference.md         # Shared API documentation
│   └── pyproject.toml               # Shared package config
│
├── local/                             # LOCAL-FIRST MVP (Open Source)
│   ├── README.md                     # MVP-specific documentation
│   ├── pyproject.toml               # MVP package config
│   ├── src/ucp_mvp/                 # MVP implementation
│   ├── tests/
│   ├── docs/
│   │   ├── getting_started.md       # MVP getting started guide
│   │   ├── mvp_architecture.md      # Architecture overview
│   │   ├── mvp_user_guide.md        # User guide
│   │   └── mvp_deployment.md        # Deployment guide
│   └── clients/                      # CLI and desktop clients
│
├── cloud/                            # CLOUD VERSION (Future Business)
│   ├── README.md                     # Cloud-specific documentation
│   ├── pyproject.toml               # Cloud package config
│   ├── src/ucp_cloud/               # Cloud implementation
│   │   ├── api/                     # REST API
│   │   ├── auth/                    # Authentication & authorization
│   │   └── pipeline/                 # Data pipelines
│   ├── tests/
│   ├── docs/
│   │   ├── roadmap.md               # Cloud implementation roadmap
│   │   ├── cloud_architecture.md    # Architecture overview
│   │   ├── cloud_deployment.md      # Deployment guide
│   │   └── cloud_api_reference.md   # API reference
│   ├── infrastructure/              # Terraform/Helm/Docker
│   └── clients/                      # VS Code extension, web client
│
├── docs/                             # SHARED DOCUMENTATION
│   ├── index.md
│   ├── getting_started.md
│   ├── debugging_playbook.md
│   ├── evaluation_harness.md
│   └── research/
│
├── reports/                          # AUDIT AND VALIDATION REPORTS
├── plans/                            # PLANNING DOCUMENTS
└── archive/                          # ARCHIVED CODE (Original monolithic codebase)
```

## CLI Reference

```bash
# Start UCP server
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

Launch Streamlit dashboard to visualize UCP internals:

```bash
pip install streamlit
streamlit run local/src/ucp_mvp/dashboard.py
```

Features:
- Search tools with live results
- View Tool Zoo statistics
- Explore session history
- Monitor router learning

## Research Foundation

UCP synthesizes ideas from:

- **[Gorilla](https://arxiv.org/abs/2305.15334)**: RAFT (Retrieval-Augmented Fine-Tuning) for tool selection
- **[ReAct](https://arxiv.org/abs/2210.03629)**: Interleaved reasoning and acting
- **[MemGPT](https://arxiv.org/abs/2310.11511)**: OS-style context management
- **[LangGraph](https://github.com/langchain-ai/langgraph)**: Cyclic state machine orchestration

See [`docs/`](docs/) folder for detailed synthesis documents.

## Development

For detailed development guidelines, see [`DEVELOPMENT_GUIDE.md`](DEVELOPMENT_GUIDE.md).

### Local MVP Development

```bash
cd local
pip install -e ".[dev]"
```

### Cloud Development

```bash
cd cloud
pip install -e ".[dev]"
```

### Shared Components Development

```bash
cd shared
pip install -e ".[dev]"
```

### Testing

```bash
# Run tests
pytest tests/ -v

# Type checking
mypy src/

# Linting
ruff check src/
```

## Troubleshooting

### Installation Issues

**Problem:** `pip install ucp-mvp` fails

**Solutions:**
1. Update pip: `pip install --upgrade pip`
2. Use virtual environment: `python -m venv venv && source venv/bin/activate`
3. Install from source instead

### Configuration Issues

**Problem:** `ucp init-config` fails

**Solutions:**
1. Check write permissions: `ls -la ~/.ucp` (Linux/macOS) or check `C:\Users\<username>\.ucp` (Windows)
2. Create directory manually: `mkdir -p ~/.ucp` (Linux/macOS) or manually create folder on Windows
3. Check disk space

### Connection Issues

**Problem:** Downstream servers not connecting

**Solutions:**
1. Verify server command is correct in config
2. Check environment variables are set properly
3. Test server independently: run the MCP server command directly
4. Check firewall settings
5. Review logs: `~/.ucp/logs/ucp.log` or `C:\Users\<username>\.ucp\logs\ucp.log`

### Tool Indexing Issues

**Problem:** `ucp index` returns no tools

**Solutions:**
1. Verify downstream servers are configured in `ucp_config.yaml`
2. Check downstream servers are accessible
3. Run with verbose logging: `ucp index --log-level DEBUG`
4. Check ChromaDB installation: `pip show chromadb`

### Performance Issues

**Problem:** UCP is slow

**Solutions:**
1. Reduce `top_k` in configuration (default is 5, try 3)
2. Use smaller embedding model: `all-MiniLM-L6-v2` (already default)
3. Enable caching in configuration
4. Check system resources (CPU, memory usage)

### Claude Desktop Integration Issues

**Problem:** Claude Desktop doesn't show UCP tools

**Solutions:**
1. Verify UCP server is running: `ucp status`
2. Check Claude Desktop config path is correct
3. Restart Claude Desktop after config changes
4. Check Claude Desktop logs for errors
5. Test with debug logging: `ucp serve --log-level DEBUG`

### Common Errors

| Error | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'ucp_mvp'` | Package not installed | Run `pip install ucp-mvp` |
| `Permission denied: '~/.ucp'` | No write permissions | Create directory manually or run with appropriate permissions |
| `Connection refused` | Downstream server not running | Start the MCP server or check configuration |
| `No tools found` | Tool zoo empty | Run `ucp index` to populate tools |
| `ChromaDB error` | Vector database issue | Reinstall chromadb: `pip install --force-reinstall chromadb` |

### Getting Help

For more detailed troubleshooting steps, see:
- **[docs/debugging_playbook.md](docs/debugging_playbook.md)** - Comprehensive debugging guide
- **[local/docs/getting_started.md](local/docs/getting_started.md)** - Detailed setup instructions
- **GitHub Issues** - Report bugs and get community help

## Documentation

- **[DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md)** - Complete documentation navigation guide
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Development guidelines for both versions
- **[local/README.md](local/README.md)** - Local MVP documentation
- **[cloud/README.md](cloud/README.md)** - Cloud version documentation
- **[shared/README.md](shared/README.md)** - Shared components documentation
- **[docs/production_deployment.md](docs/production_deployment.md)** - Production deployment guide

## License

MIT License

---

**UCP: Because your LLM shouldn't need to read 500 tool manuals to send an email.**

### Performance Issues

**Problem:** UCP is slow

**Solutions:**
1. Reduce `top_k` in configuration (default is 5, try 3)
2. Use smaller embedding model: `all-MiniLM-L6-v2` (already default)
3. Enable caching in configuration
4. Check system resources (CPU, memory usage)

### Claude Desktop Integration Issues

**Problem:** Claude Desktop doesn't show UCP tools

**Solutions:**
1. Verify UCP server is running: `ucp status`
2. Check Claude Desktop config path is correct
3. Restart Claude Desktop after config changes
4. Check Claude Desktop logs for errors
5. Test with debug logging: `ucp serve --log-level DEBUG`

### Common Errors

| Error | Cause | Solution |
|---|---|---|
| `ModuleNotFoundError: No module named 'ucp_mvp'` | Package not installed | Run `pip install ucp-mvp` |
| `Permission denied: '~/.ucp'` | No write permissions | Create directory manually or run with appropriate permissions |
| `Connection refused` | Downstream server not running | Start the MCP server or check configuration |
| `No tools found` | Tool zoo empty | Run `ucp index` to populate tools |
| `ChromaDB error` | Vector database issue | Reinstall chromadb: `pip install --force-reinstall chromadb` |

### Getting Help

For more detailed troubleshooting steps, see:
- **[docs/debugging_playbook.md](docs/debugging_playbook.md)** - Comprehensive debugging guide
- **[local/docs/getting_started.md](local/docs/getting_started.md)** - Detailed setup instructions
- **GitHub Issues** - Report bugs and get community help

## Documentation

- **[DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md)** - Complete documentation navigation guide
- **[DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md)** - Development guidelines for both versions
- **[local/README.md](local/README.md)** - Local MVP documentation
- **[cloud/README.md](cloud/README.md)** - Cloud version documentation
- **[shared/README.md](shared/README.md)** - Shared components documentation
- **[docs/production_deployment.md](docs/production_deployment.md)** - Production deployment guide

## License

MIT License

---

**UCP: Because your LLM shouldn't need to read 500 tool manuals to send an email.**

