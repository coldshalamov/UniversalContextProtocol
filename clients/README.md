# UCP Clients

This directory contains the client applications for the Universal Context Protocol (UCP).

## Overview

These clients provide the **observation layer** that captures context flowing in and out of LLM interactions, enabling UCP to learn and predict the right tools.

## Components

### 1. CLI (`cli/`)

A powerful command-line chat interface that:
- Supports 20+ LLM providers (OpenAI, Anthropic, Google, Groq, Together, OpenRouter, etc.)
- Captures conversation context for UCP learning
- Integrates with UCP server for tool injection
- Exports training data in JSONL format

```bash
cd cli
pip install -e .
ucp-chat
```

### 2. VS Code Extension (`vscode/`)

A VS Code extension that:
- Captures editor context (current file, diagnostics, open files)
- Shows predicted tools based on code context
- Provides an in-IDE chat interface
- Exports training data for UCP learning

```bash
cd vscode
npm install
npm run compile
```

### 3. Desktop App (`desktop/`)

A beautiful Electron-based desktop application that:
- Provides a ChatGPT/Claude Desktop-like experience
- Manages multiple conversations
- Configures API keys for all providers
- Shows real-time UCP connection status
- Supports dark/light themes

```bash
cd desktop
npm install
npm run dev
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                          User                                    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐     ┌─────────┐
    │   CLI   │     │ VS Code │     │ Desktop │
    │ Client  │     │   Ext   │     │   App   │
    └────┬────┘     └────┬────┘     └────┬────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │    UCP Server       │
              │  (Tool Prediction)  │
              └──────────┬──────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │  Downstream MCP     │
              │     Servers         │
              └─────────────────────┘
```

## Data Flow

1. **Context Capture**: Clients capture conversation context, editor state, or user input
2. **Tool Prediction**: Clients send context to UCP Server, which returns predicted tools
3. **LLM Interaction**: Clients inject predicted tools into LLM requests
4. **Feedback Loop**: Clients report which tools were actually used back to UCP
5. **Learning**: UCP uses feedback to improve future predictions

## Configuration

All clients read from `~/.ucp/config.yaml`:

```yaml
providers:
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    default_model: claude-sonnet-4-20250514
  openai:
    api_key: ${OPENAI_API_KEY}
    default_model: gpt-4o
  # ... more providers

default_provider: anthropic

ucp:
  enabled: true
  server_url: http://localhost:8765
  log_directory: ~/.ucp/logs
```

## Training Data Export

All clients can export training data for UCP learning:

```bash
# CLI
ucp-chat export -o training_data.jsonl

# VS Code
# Run "UCP: Export Training Data" command

# Desktop
# Settings > Export Training Data
```

The exported JSONL contains:
- Conversation messages
- Tool predictions (predicted vs used)
- Context snapshots
- Session metadata

This data feeds the RAFT fine-tuning pipeline for improved tool prediction.

## Development

### Prerequisites

- Python 3.10+ (CLI)
- Node.js 18+ (VS Code, Desktop)
- UCP Server running on localhost:8765

### Building

```bash
# CLI
cd cli && pip install -e ".[dev]"

# VS Code Extension
cd vscode && npm install && npm run compile

# Desktop App
cd desktop && npm install && npm run build
```

### Packaging

```bash
# VS Code Extension
cd vscode && npx vsce package

# Desktop App (Windows)
cd desktop && npm run package:win

# Desktop App (macOS)
cd desktop && npm run package:mac

# Desktop App (Linux)
cd desktop && npm run package:linux
```
