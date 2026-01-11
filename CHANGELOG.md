# Changelog

All notable changes to the Universal Context Protocol (UCP) project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Cloud version implementation
- Cross-encoder reranking
- Bandit exploration for tool discovery
- Online optimization
- RAFT fine-tuning
- LangGraph orchestration
- Centralized telemetry

## [0.1.0-alpha1] - 2026-01-10

### Added
- Initial PyPI package release
- Package distribution configuration (pyproject.toml, setup.py, MANIFEST.in)
- Semantic tool retrieval with ChromaDB
- Context-aware routing
- Session persistence with SQLite
- Adaptive learning for tool usage patterns
- Multiple transport support (Stdio, HTTP/SSE)
- Debug dashboard with Streamlit
- CLI commands: serve, status, index, search, init-config
- Claude Desktop integration support
- Telemetry infrastructure
- Baseline benchmark evaluation harness
- Comprehensive documentation

### Fixed
- Import error in src/ucp/__init__.py (removed non-existent UCPServerBuilder)

### Performance
- Tool selection: 8.9% faster than baseline (25.99ms vs 28.53ms)
- Semantic search with hybrid (keyword + vector) approach
- Efficient session management with SQLite

### Documentation
- Updated README.md with PyPI installation instructions
- Added PyPI version badge
- Created comprehensive troubleshooting guide
- Added benchmark results documentation
- Created development guidelines

### Known Issues
- Context reduction target (80%+) not achieved due to hardcoded `max_per_server = 3` limit in router reranking logic
- This limitation affects single-server deployments
- See [`docs/milestone_1_5_baseline_benchmark.md`](docs/milestone_1_5_baseline_benchmark.md) for detailed analysis

### Dependencies
- mcp (Model Context Protocol)
- fastapi
- uvicorn
- pydantic
- chromadb
- langgraph
- sentence-transformers
- pyyaml
- python-dotenv

### Installation
```bash
pip install ucp
```

### Quick Start
```bash
ucp init-config
ucp serve
```

## [0.0.1] - 2025-XX-XX

### Added
- Initial project setup
- Basic MCP server implementation
- Tool zoo concept
- Initial routing logic
- Configuration system

---

[Unreleased]: https://github.com/yourusername/UniversalContextProtocol/compare/v0.1.0-alpha1...HEAD
[0.1.0-alpha1]: https://github.com/yourusername/UniversalContextProtocol/releases/tag/v0.1.0-alpha1
[0.0.1]: https://github.com/yourusername/UniversalContextProtocol/releases/tag/v0.0.1
