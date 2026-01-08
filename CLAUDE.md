# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Universal Context Protocol (UCP) is an intelligent gateway that solves "Tool Overload" in agentic AI systems. It presents itself as a single MCP server to clients while internally orchestrating a fleet of downstream MCP servers. The core innovation is **context-aware dynamic injection**—instead of flooding the LLM with all available tool schemas, UCP uses a predictive router to inject only the most relevant subset based on conversation context.

**Status:** Design/research phase. No implementation code exists yet.

## Architecture (Planned)

### Control Plane ("Brain")
- **Tool Zoo (LlamaIndex)**: Vector database storing tool schemas from all connected MCP servers
- **Router (Gorilla/RAFT)**: Semantic router or fine-tuned selector model that picks the minimal relevant toolset
- **Session Manager (LangGraph)**: Maintains conversation state and tracks the "Active Toolset"

### Data Plane ("Body")
- **Virtual MCP Server**: Intercepts `tools/list` to return predicted tools, routes `tools/call` to correct downstream server
- **Connection Pool**: Manages persistent connections to downstream MCP servers

### Runtime Loop
1. User message → Router analyzes intent
2. Router queries Tool Zoo → Returns top-k relevant tools
3. UCP constructs filtered `tools/list` response
4. Client/LLM only sees relevant tools
5. Tool execution → Result fed back → Router may update toolset on topic shift

## Documentation Structure

| Path | Contents |
|------|----------|
| [docs/ucp_design_plan.md](docs/ucp_design_plan.md) | Master architecture and implementation roadmap |
| [docs/synthesis_*.md](docs/) | Synthesized lessons from research papers |
| [docs/pdfs/](docs/pdfs/) | Research paper conversions (ReAct, Toolformer, Gorilla, etc.) |
| [docs/index.md](docs/index.md) | Catalog of all documentation |
| [reports/](reports/) | Audit and integrity reports |

## Key Research Papers

- **Gorilla** (2305.15334): API selection via retrieval-aware fine-tuning (RAFT)
- **ReAct** (2210.03629): Interleaved reasoning and acting pattern
- **Toolformer** (2302.04761): Self-supervised tool learning
- **MemGPT** (2310.11511): OS-style context management with virtual memory
- **LangGraph**: Cyclic graph-based agent orchestration
- **LlamaIndex**: Vector indexing for schema retrieval

## Implementation Roadmap (from design doc)

1. **Phase 1 (MVP)**: Virtual MCP server skeleton that proxies to one downstream server
2. **Phase 2**: Tool Zoo indexer using LlamaIndex + vector DB
3. **Phase 3**: Semantic router with sentence-transformers for dynamic `tools/list`
4. **Phase 4**: LangGraph integration for state persistence
5. **Phase 5**: RAFT fine-tuning for improved accuracy

## Planned Tech Stack

- **Language**: Python (FastAPI/Starlette for SSE)
- **MCP**: MCP Python SDK
- **Vector DB**: ChromaDB or Qdrant
- **Embeddings**: sentence-transformers
- **Orchestration**: LangGraph
- **Indexing**: LlamaIndex

## Known Corpus Issues

Per [reports/corpus_integrity_report.md](reports/corpus_integrity_report.md):
- `docs/pdfs/2310.11511v1.md` is mislabeled (contains Self-Route, not MemGPT)
- Use `docs/2310.11511v1_MemGPT.md` for MemGPT content
- Papers 2403.03572v1 and 2405.12166v1 are noise (unrelated math papers)
