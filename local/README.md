# UCP Local MVP

This directory contains the local-first MVP implementation of UCP.

## Overview

The local MVP is designed for:
- **Privacy-first**: All data stays on your machine
- **Simplicity**: Easy to install and use
- **Immediate value**: Core routing functionality without complexity
- **Open source**: Free to use and modify

## Structure

```
local/
├── README.md                     # This file
├── pyproject.toml               # MVP package config
├── src/ucp_mvp/               # MVP implementation
│   ├── __init__.py
│   ├── server.py                # Main MCP server
│   ├── router.py                # Semantic routing logic
│   ├── tool_zoo.py             # Vector index for tools
│   ├── session.py               # Session management
│   ├── connection_pool.py        # Downstream connections
│   └── dashboard.py            # Streamlit debug UI
├── tests/                      # MVP-specific tests
├── docs/                       # MVP documentation
│   ├── getting_started.md        # Installation and setup
│   ├── mvp_architecture.md     # Architecture overview
│   ├── mvp_user_guide.md       # User guide
│   └── mvp_deployment.md       # Deployment guide
└── clients/                    # CLI and desktop clients
    ├── cli/                    # Command-line interface
    └── desktop/                # Desktop integration
```

## Features

### Core Features (v1.0)
- MCP proxy server with stdio transport
- Baseline router with semantic search
- Adaptive router with co-occurrence tracking
- Local tool zoo (ChromaDB)
- SQLite session management
- Connection pooling for downstream servers
- CLI interface (serve, index, search, status)
- Simple Streamlit dashboard

### Storage
- **Sessions**: SQLite (`~/.ucp/data/sessions.db`)
- **Tool Zoo**: ChromaDB (`~/.ucp/data/tool_zoo`)
- **Config**: YAML (`~/.ucp/ucp_config.yaml`)
- **Logs**: `~/.ucp/logs/`

## Installation

### Quick Install

```bash
pip install ucp-mvp
```

### From Source

```bash
cd local
pip install -e .
```

### Generate Configuration

```bash
ucp init-config
```

This creates `~/.ucp/ucp_config.yaml` with default settings.

## Usage

### Start the Server

```bash
ucp serve
```

Or with custom config:

```bash
ucp serve -c /path/to/config.yaml
```

### Index Tools

```bash
ucp index
```

This connects to all downstream MCP servers and indexes their tools.

### Search Tools

```bash
ucp search "send email" -k 5 --hybrid
```

### Check Status

```bash
ucp status
```

## Claude Desktop Integration

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

## Configuration

Edit `~/.ucp/ucp_config.yaml`:

```yaml
server:
  name: "My UCP Gateway"
  transport: stdio
  log_level: INFO

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5
  similarity_threshold: 0.7

router:
  mode: hybrid  # semantic, keyword, or hybrid
  max_tools: 10
  enable_co_occurrence: true

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

## Development

### Setup Development Environment

```bash
cd local
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v
```

### Type Checking

```bash
mypy src/ucp_mvp/
```

### Linting

```bash
ruff check src/ucp_mvp/
```

## Debug Dashboard

Launch the Streamlit dashboard to visualize UCP internals:

```bash
pip install streamlit
streamlit run src/ucp_mvp/dashboard.py
```

Features:
- Search tools with live results
- View Tool Zoo statistics
- Explore session history
- Monitor router learning

## Documentation

- [Getting Started](docs/getting_started.md) - Installation and setup guide
- [Architecture](docs/mvp_architecture.md) - Architecture overview
- [User Guide](docs/mvp_user_guide.md) - User guide
- [Deployment](docs/mvp_deployment.md) - Deployment guide

## Future Enhancements

### v1.1
- Cross-encoder reranking
- Bandit exploration
- Improved confidence thresholds

### v1.2
- GPU acceleration
- Caching layer
- HTTP/SSE transport support

## Troubleshooting

### Tools Not Appearing

1. Check that downstream servers are running
2. Run `ucp index` to refresh tool index
3. Check logs: `~/.ucp/logs/ucp.log`

### Performance Issues

1. Reduce `top_k` in config
2. Use smaller embedding model
3. Enable caching in config

### Connection Errors

1. Verify downstream server commands are correct
2. Check environment variables are set
3. Test downstream servers independently

## Contributing

Contributions welcome! Please read the main repository's [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) for guidelines.

## License

MIT License

This directory contains the local-first MVP implementation of UCP.

## Overview

The local MVP is designed for:
- **Privacy-first**: All data stays on your machine
- **Simplicity**: Easy to install and use
- **Immediate value**: Core routing functionality without complexity
- **Open source**: Free to use and modify

## Structure

```
local/
├── README.md                     # This file
├── pyproject.toml               # MVP package config
├── src/ucp_mvp/               # MVP implementation
│   ├── __init__.py
│   ├── server.py                # Main MCP server
│   ├── router.py                # Semantic routing logic
│   ├── tool_zoo.py             # Vector index for tools
│   ├── session.py               # Session management
│   ├── connection_pool.py        # Downstream connections
│   └── dashboard.py            # Streamlit debug UI
├── tests/                      # MVP-specific tests
├── docs/                       # MVP documentation
│   ├── getting_started.md        # Installation and setup
│   ├── mvp_architecture.md     # Architecture overview
│   ├── mvp_user_guide.md       # User guide
│   └── mvp_deployment.md       # Deployment guide
└── clients/                    # CLI and desktop clients
    ├── cli/                    # Command-line interface
    └── desktop/                # Desktop integration
```

## Features

### Core Features (v1.0)
- MCP proxy server with stdio transport
- Baseline router with semantic search
- Adaptive router with co-occurrence tracking
- Local tool zoo (ChromaDB)
- SQLite session management
- Connection pooling for downstream servers
- CLI interface (serve, index, search, status)
- Simple Streamlit dashboard

### Storage
- **Sessions**: SQLite (`~/.ucp/data/sessions.db`)
- **Tool Zoo**: ChromaDB (`~/.ucp/data/tool_zoo`)
- **Config**: YAML (`~/.ucp/ucp_config.yaml`)
- **Logs**: `~/.ucp/logs/`

## Installation

### Quick Install

```bash
pip install ucp-mvp
```

### From Source

```bash
cd local
pip install -e .
```

### Generate Configuration

```bash
ucp init-config
```

This creates `~/.ucp/ucp_config.yaml` with default settings.

## Usage

### Start the Server

```bash
ucp serve
```

Or with custom config:

```bash
ucp serve -c /path/to/config.yaml
```

### Index Tools

```bash
ucp index
```

This connects to all downstream MCP servers and indexes their tools.

### Search Tools

```bash
ucp search "send email" -k 5 --hybrid
```

### Check Status

```bash
ucp status
```

## Claude Desktop Integration

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

## Configuration

Edit `~/.ucp/ucp_config.yaml`:

```yaml
server:
  name: "My UCP Gateway"
  transport: stdio
  log_level: INFO

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5
  similarity_threshold: 0.7

router:
  mode: hybrid  # semantic, keyword, or hybrid
  max_tools: 10
  enable_co_occurrence: true

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

## Development

### Setup Development Environment

```bash
cd local
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v
```

### Type Checking

```bash
mypy src/ucp_mvp/
```

### Linting

```bash
ruff check src/ucp_mvp/
```

## Debug Dashboard

Launch the Streamlit dashboard to visualize UCP internals:

```bash
pip install streamlit
streamlit run src/ucp_mvp/dashboard.py
```

Features:
- Search tools with live results
- View Tool Zoo statistics
- Explore session history
- Monitor router learning

## Documentation

- [Getting Started](docs/getting_started.md) - Installation and setup guide
- [Architecture](docs/mvp_architecture.md) - Architecture overview
- [User Guide](docs/mvp_user_guide.md) - User guide
- [Deployment](docs/mvp_deployment.md) - Deployment guide

## Future Enhancements

### v1.1
- Cross-encoder reranking
- Bandit exploration
- Improved confidence thresholds

### v1.2
- GPU acceleration
- Caching layer
- HTTP/SSE transport support

## Troubleshooting

### Tools Not Appearing

1. Check that downstream servers are running
2. Run `ucp index` to refresh tool index
3. Check logs: `~/.ucp/logs/ucp.log`

### Performance Issues

1. Reduce `top_k` in config
2. Use smaller embedding model
3. Enable caching in config

### Connection Errors

1. Verify downstream server commands are correct
2. Check environment variables are set
3. Test downstream servers independently

## Contributing

Contributions welcome! Please read the main repository's [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) for guidelines.

## License

MIT License

