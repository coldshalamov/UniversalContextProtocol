# UCP CLI - Universal Context Protocol Command Line Interface

A powerful CLI wrapper that proxies LLM requests through UCP, enabling context observation and intelligent tool injection.

## Features

- **Multi-Provider Support**: Works with OpenAI, Anthropic, Google, Mistral, Groq, Together, OpenRouter, and local models
- **Context Capture**: Logs all context flowing in/out for UCP learning
- **Tool Injection**: Automatically injects predicted tools based on context
- **Conversation History**: Maintains and manages conversation sessions
- **Export/Import**: Export conversations for training data

## Installation

```bash
pip install -e .
```

## Quick Start

```bash
# Configure your API keys
ucp-chat configure

# Start a chat session
ucp-chat

# Use a specific provider and model
ucp-chat --provider openai --model gpt-4o

# Use with UCP tool injection enabled
ucp-chat --ucp-enabled
```

## Configuration

Create `~/.ucp/config.yaml` or use environment variables:

```yaml
providers:
  openai:
    api_key: ${OPENAI_API_KEY}
    default_model: gpt-4o
  anthropic:
    api_key: ${ANTHROPIC_API_KEY}
    default_model: claude-sonnet-4-20250514
  google:
    api_key: ${GOOGLE_API_KEY}
    default_model: gemini-2.0-flash
  # ... more providers

default_provider: anthropic
ucp:
  enabled: true
  server_url: http://localhost:8765
  log_directory: ~/.ucp/logs
```

## Commands

- `ucp-chat` - Interactive chat mode
- `ucp-chat configure` - Configure API keys
- `ucp-chat providers` - List available providers
- `ucp-chat export` - Export conversation logs
- `ucp-chat sessions` - Manage chat sessions
