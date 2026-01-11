# Getting Started with UCP Local MVP

This guide will help you install, configure, and run of UCP Local MVP.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- (Optional) Claude Desktop for integration

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install ucp-mvp
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/your-org/UniversalContextProtocol.git
cd UniversalContextProtocol/local

# Install in development mode
pip install -e .
```

### Development Installation

If you want to contribute or modify UCP:

```bash
cd local
pip install -e ".[dev]"
```

This installs additional development dependencies:
- pytest (testing)
- mypy (type checking)
- ruff (linting)
- black (code formatting)

## Initial Configuration

### Generate Default Configuration

```bash
ucp init-config
```

This creates a default configuration file at `~/.ucp/ucp_config.yaml`.

### Configuration File Location

- **Linux/macOS**: `~/.ucp/ucp_config.yaml`
- **Windows**: `C:\Users\<username>\.ucp\ucp_config.yaml`

### Configuration Structure

The generated configuration includes:

```yaml
server:
  name: "UCP Gateway"
  transport: stdio
  log_level: INFO
  host: "localhost"
  port: 8765

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5
  similarity_threshold: 0.7
  persist_dir: "~/.ucp/data/tool_zoo"

router:
  mode: hybrid  # Options: semantic, keyword, hybrid
  max_tools: 10
  enable_co_occurrence: true
  enable_learning: true

session:
  persist_dir: "~/.ucp/data/sessions.db"
  max_history: 100

downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    tags: [files, local]
```

## Setting Up Downstream MCP Servers

UCP connects to downstream MCP servers that provide tools. Here's how to configure common servers:

### GitHub MCP Server

```yaml
downstream_servers:
  - name: github
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your-github-token"
    tags: [code, git, development]
```

**Get a GitHub token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`
4. Copy the token

### Gmail MCP Server

```yaml
downstream_servers:
  - name: gmail
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-gmail"]
    env:
      GMAIL_CLIENT_ID: "your-client-id"
      GMAIL_CLIENT_SECRET: "your-client-secret"
      GMAIL_REFRESH_TOKEN: "your-refresh-token"
    tags: [email, communication]
```

**Get Gmail credentials:**
1. Create a Google Cloud project
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Set up redirect URI for MCP server
5. Obtain refresh token

### Slack MCP Server

```yaml
downstream_servers:
  - name: slack
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-slack"]
    env:
      SLACK_BOT_TOKEN: "xoxb-your-bot-token"
      SLACK_APP_TOKEN: "xapp-your-app-token"
    tags: [chat, communication, team]
```

**Get Slack tokens:**
1. Create a Slack app
2. Enable bot permissions
3. Install app to workspace
4. Copy bot token and app token

### Filesystem MCP Server

```yaml
downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    tags: [files, local]
```

**Security Note:** Only allow access to directories you trust.

## Running UCP

### Start Server

```bash
ucp serve
```

This starts UCP with default configuration.

### Start with Custom Configuration

```bash
ucp serve -c /path/to/custom_config.yaml
```

### Start with Debug Logging

```bash
ucp serve --log-level DEBUG
```

### Start in Background (Linux/macOS)

```bash
nohup ucp serve > ucp.log 2>&1 &
```

### Start as Service (Windows)

Create a Windows service using NSSM or similar tools.

## Indexing Tools

After configuring downstream servers, index their tools:

```bash
ucp index
```

This command:
1. Connects to all configured downstream servers
2. Retrieves tool schemas
3. Generates embeddings for each tool
4. Stores in local tool zoo (ChromaDB)

### Re-index After Changes

If you add or modify downstream servers, re-index:

```bash
ucp index --force
```

## Testing Your Setup

### Search for Tools

```bash
ucp search "send email" -k 5 --hybrid
```

This searches tool zoo and returns most relevant tools.

### Check Server Status

```bash
ucp status
```

This displays:
- Connected downstream servers
- Number of indexed tools
- Recent tool usage statistics
- Session information

### Test with Claude Desktop

1. Configure Claude Desktop (see below)
2. Open Claude Desktop
3. Start a conversation
4. Ask: "What tools do I have available?"
5. Claude should show only relevant tools based on context

## Claude Desktop Integration

### Configure Claude Desktop

1. Open Claude Desktop
2. Go to Settings → Developer
3. Edit MCP servers configuration
4. Add UCP:

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

5. Save and restart Claude Desktop

### Verify Integration

1. Open a new Claude conversation
2. Ask: "List all my tools"
3. You should see tools from your configured MCP servers
4. Try a context-specific query: "How do I send an email?"
5. Claude should show only email-related tools

## Debug Dashboard

UCP includes a Streamlit dashboard for debugging and visualization.

### Start Dashboard

```bash
pip install streamlit
streamlit run src/ucp_mvp/dashboard.py
```

### Dashboard Features

- **Tool Search**: Test semantic search with live results
- **Tool Zoo Stats**: View indexed tools and embeddings
- **Session History**: Explore conversation sessions
- **Router Learning**: Monitor tool usage patterns
- **Server Status**: Check downstream server connections

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
1. Check write permissions: `ls -la ~/.ucp`
2. Create directory manually: `mkdir -p ~/.ucp`
3. Check disk space

### Connection Issues

**Problem:** Downstream servers not connecting

**Solutions:**
1. Verify server command is correct
2. Check environment variables are set
3. Test server independently: run the MCP server command directly
4. Check firewall settings
5. Review logs: `~/.ucp/logs/ucp.log`

### Tool Indexing Issues

**Problem:** `ucp index` returns no tools

**Solutions:**
1. Verify downstream servers are configured
2. Check downstream servers are running
3. Run with verbose logging: `ucp index --log-level DEBUG`
4. Check ChromaDB installation: `pip show chromadb`

### Performance Issues

**Problem:** UCP is slow

**Solutions:**
1. Reduce `top_k` in configuration
2. Use smaller embedding model: `all-MiniLM-L6-v2`
3. Enable caching in configuration
4. Check system resources (CPU, memory)

## Next Steps

- Read [Architecture Overview](mvp_architecture.md) to understand how UCP works
- Read [User Guide](mvp_user_guide.md) for advanced usage
- Read [Production Deployment Guide](../../docs/production_deployment.md) for production setup
- Check main [README](../README.md) for project overview

## Getting Help

- **Documentation**: See [DOCUMENTATION_MAP.md](../../DOCUMENTATION_MAP.md)
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Debug**: Enable debug logging and check `~/.ucp/logs/ucp.log`

This guide will help you install, configure, and run of UCP Local MVP.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- (Optional) Claude Desktop for integration

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install ucp-mvp
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/your-org/UniversalContextProtocol.git
cd UniversalContextProtocol/local

# Install in development mode
pip install -e .
```

### Development Installation

If you want to contribute or modify UCP:

```bash
cd local
pip install -e ".[dev]"
```

This installs additional development dependencies:
- pytest (testing)
- mypy (type checking)
- ruff (linting)
- black (code formatting)

## Initial Configuration

### Generate Default Configuration

```bash
ucp init-config
```

This creates a default configuration file at `~/.ucp/ucp_config.yaml`.

### Configuration File Location

- **Linux/macOS**: `~/.ucp/ucp_config.yaml`
- **Windows**: `C:\Users\<username>\.ucp\ucp_config.yaml`

### Configuration Structure

The generated configuration includes:

```yaml
server:
  name: "UCP Gateway"
  transport: stdio
  log_level: INFO
  host: "localhost"
  port: 8765

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5
  similarity_threshold: 0.7
  persist_dir: "~/.ucp/data/tool_zoo"

router:
  mode: hybrid  # Options: semantic, keyword, hybrid
  max_tools: 10
  enable_co_occurrence: true
  enable_learning: true

session:
  persist_dir: "~/.ucp/data/sessions.db"
  max_history: 100

downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    tags: [files, local]
```

## Setting Up Downstream MCP Servers

UCP connects to downstream MCP servers that provide tools. Here's how to configure common servers:

### GitHub MCP Server

```yaml
downstream_servers:
  - name: github
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your-github-token"
    tags: [code, git, development]
```

**Get a GitHub token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`
4. Copy the token

### Gmail MCP Server

```yaml
downstream_servers:
  - name: gmail
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-gmail"]
    env:
      GMAIL_CLIENT_ID: "your-client-id"
      GMAIL_CLIENT_SECRET: "your-client-secret"
      GMAIL_REFRESH_TOKEN: "your-refresh-token"
    tags: [email, communication]
```

**Get Gmail credentials:**
1. Create a Google Cloud project
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Set up redirect URI for MCP server
5. Obtain refresh token

### Slack MCP Server

```yaml
downstream_servers:
  - name: slack
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-slack"]
    env:
      SLACK_BOT_TOKEN: "xoxb-your-bot-token"
      SLACK_APP_TOKEN: "xapp-your-app-token"
    tags: [chat, communication, team]
```

**Get Slack tokens:**
1. Create a Slack app
2. Enable bot permissions
3. Install app to workspace
4. Copy bot token and app token

### Filesystem MCP Server

```yaml
downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    tags: [files, local]
```

**Security Note:** Only allow access to directories you trust.

## Running UCP

### Start Server

```bash
ucp serve
```

This starts UCP with default configuration.

### Start with Custom Configuration

```bash
ucp serve -c /path/to/custom_config.yaml
```

### Start with Debug Logging

```bash
ucp serve --log-level DEBUG
```

### Start in Background (Linux/macOS)

```bash
nohup ucp serve > ucp.log 2>&1 &
```

### Start as Service (Windows)

Create a Windows service using NSSM or similar tools.

## Indexing Tools

After configuring downstream servers, index their tools:

```bash
ucp index
```

This command:
1. Connects to all configured downstream servers
2. Retrieves tool schemas
3. Generates embeddings for each tool
4. Stores in local tool zoo (ChromaDB)

### Re-index After Changes

If you add or modify downstream servers, re-index:

```bash
ucp index --force
```

## Testing Your Setup

### Search for Tools

```bash
ucp search "send email" -k 5 --hybrid
```

This searches tool zoo and returns most relevant tools.

### Check Server Status

```bash
ucp status
```

This displays:
- Connected downstream servers
- Number of indexed tools
- Recent tool usage statistics
- Session information

### Test with Claude Desktop

1. Configure Claude Desktop (see below)
2. Open Claude Desktop
3. Start a conversation
4. Ask: "What tools do I have available?"
5. Claude should show only relevant tools based on context

## Claude Desktop Integration

### Configure Claude Desktop

1. Open Claude Desktop
2. Go to Settings → Developer
3. Edit MCP servers configuration
4. Add UCP:

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

5. Save and restart Claude Desktop

### Verify Integration

1. Open a new Claude conversation
2. Ask: "List all my tools"
3. You should see tools from your configured MCP servers
4. Try a context-specific query: "How do I send an email?"
5. Claude should show only email-related tools

## Debug Dashboard

UCP includes a Streamlit dashboard for debugging and visualization.

### Start Dashboard

```bash
pip install streamlit
streamlit run src/ucp_mvp/dashboard.py
```

### Dashboard Features

- **Tool Search**: Test semantic search with live results
- **Tool Zoo Stats**: View indexed tools and embeddings
- **Session History**: Explore conversation sessions
- **Router Learning**: Monitor tool usage patterns
- **Server Status**: Check downstream server connections

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
1. Check write permissions: `ls -la ~/.ucp`
2. Create directory manually: `mkdir -p ~/.ucp`
3. Check disk space

### Connection Issues

**Problem:** Downstream servers not connecting

**Solutions:**
1. Verify server command is correct
2. Check environment variables are set
3. Test server independently: run the MCP server command directly
4. Check firewall settings
5. Review logs: `~/.ucp/logs/ucp.log`

### Tool Indexing Issues

**Problem:** `ucp index` returns no tools

**Solutions:**
1. Verify downstream servers are configured
2. Check downstream servers are running
3. Run with verbose logging: `ucp index --log-level DEBUG`
4. Check ChromaDB installation: `pip show chromadb`

### Performance Issues

**Problem:** UCP is slow

**Solutions:**
1. Reduce `top_k` in configuration
2. Use smaller embedding model: `all-MiniLM-L6-v2`
3. Enable caching in configuration
4. Check system resources (CPU, memory)

## Next Steps

- Read [Architecture Overview](mvp_architecture.md) to understand how UCP works
- Read [User Guide](mvp_user_guide.md) for advanced usage
- Read [Production Deployment Guide](../../docs/production_deployment.md) for production setup
- Check main [README](../README.md) for project overview

## Getting Help

- **Documentation**: See [DOCUMENTATION_MAP.md](../../DOCUMENTATION_MAP.md)
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Debug**: Enable debug logging and check `~/.ucp/logs/ucp.log`

This guide will help you install, configure, and run the UCP Local MVP.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- (Optional) Claude Desktop for integration

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install ucp-mvp
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/your-org/UniversalContextProtocol.git
cd UniversalContextProtocol/local

# Install in development mode
pip install -e .
```

### Development Installation

If you want to contribute or modify UCP:

```bash
cd local
pip install -e ".[dev]"
```

This installs additional development dependencies:
- pytest (testing)
- mypy (type checking)
- ruff (linting)
- black (code formatting)

## Initial Configuration

### Generate Default Configuration

```bash
ucp init-config
```

This creates a default configuration file at `~/.ucp/ucp_config.yaml`.

### Configuration File Location

- **Linux/macOS**: `~/.ucp/ucp_config.yaml`
- **Windows**: `C:\Users\<username>\.ucp\ucp_config.yaml`

### Configuration Structure

The generated configuration includes:

```yaml
server:
  name: "UCP Gateway"
  transport: stdio
  log_level: INFO
  host: "localhost"
  port: 8765

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5
  similarity_threshold: 0.7
  persist_dir: "~/.ucp/data/tool_zoo"

router:
  mode: hybrid  # Options: semantic, keyword, hybrid
  max_tools: 10
  enable_co_occurrence: true
  enable_learning: true

session:
  persist_dir: "~/.ucp/data/sessions.db"
  max_history: 100

downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    tags: [files, local]
```

## Setting Up Downstream MCP Servers

UCP connects to downstream MCP servers that provide tools. Here's how to configure common servers:

### GitHub MCP Server

```yaml
downstream_servers:
  - name: github
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your-github-token"
    tags: [code, git, development]
```

**Get a GitHub token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`
4. Copy the token

### Gmail MCP Server

```yaml
downstream_servers:
  - name: gmail
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-gmail"]
    env:
      GMAIL_CLIENT_ID: "your-client-id"
      GMAIL_CLIENT_SECRET: "your-client-secret"
      GMAIL_REFRESH_TOKEN: "your-refresh-token"
    tags: [email, communication]
```

**Get Gmail credentials:**
1. Create a Google Cloud project
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Set up redirect URI for MCP server
5. Obtain refresh token

### Slack MCP Server

```yaml
downstream_servers:
  - name: slack
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-slack"]
    env:
      SLACK_BOT_TOKEN: "xoxb-your-bot-token"
      SLACK_APP_TOKEN: "xapp-your-app-token"
    tags: [chat, communication, team]
```

**Get Slack tokens:**
1. Create a Slack app
2. Enable bot permissions
3. Install app to workspace
4. Copy bot token and app token

### Filesystem MCP Server

```yaml
downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    tags: [files, local]
```

**Security Note:** Only allow access to directories you trust.

## Running UCP

### Start the Server

```bash
ucp serve
```

This starts UCP with the default configuration.

### Start with Custom Configuration

```bash
ucp serve -c /path/to/custom_config.yaml
```

### Start with Debug Logging

```bash
ucp serve --log-level DEBUG
```

### Start in Background (Linux/macOS)

```bash
nohup ucp serve > ucp.log 2>&1 &
```

### Start as Service (Windows)

Create a Windows service using NSSM or similar tools.

## Indexing Tools

After configuring downstream servers, index their tools:

```bash
ucp index
```

This command:
1. Connects to all configured downstream servers
2. Retrieves tool schemas
3. Generates embeddings for each tool
4. Stores in the local tool zoo (ChromaDB)

### Re-index After Changes

If you add or modify downstream servers, re-index:

```bash
ucp index --force
```

## Testing Your Setup

### Search for Tools

```bash
ucp search "send email" -k 5 --hybrid
```

This searches the tool zoo and returns the most relevant tools.

### Check Server Status

```bash
ucp status
```

This displays:
- Connected downstream servers
- Number of indexed tools
- Recent tool usage statistics
- Session information

### Test with Claude Desktop

1. Configure Claude Desktop (see below)
2. Open Claude Desktop
3. Start a conversation
4. Ask: "What tools do I have available?"
5. Claude should show only relevant tools based on context

## Claude Desktop Integration

### Configure Claude Desktop

1. Open Claude Desktop
2. Go to Settings → Developer
3. Edit the MCP servers configuration
4. Add UCP:

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

5. Save and restart Claude Desktop

### Verify Integration

1. Open a new Claude conversation
2. Ask: "List all my tools"
3. You should see tools from your configured MCP servers
4. Try a context-specific query: "How do I send an email?"
5. Claude should show only email-related tools

## Debug Dashboard

UCP includes a Streamlit dashboard for debugging and visualization.

### Start the Dashboard

```bash
pip install streamlit
streamlit run src/ucp_mvp/dashboard.py
```

### Dashboard Features

- **Tool Search**: Test semantic search with live results
- **Tool Zoo Stats**: View indexed tools and embeddings
- **Session History**: Explore conversation sessions
- **Router Learning**: Monitor tool usage patterns
- **Server Status**: Check downstream server connections

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
1. Check write permissions: `ls -la ~/.ucp`
2. Create directory manually: `mkdir -p ~/.ucp`
3. Check disk space

### Connection Issues

**Problem:** Downstream servers not connecting

**Solutions:**
1. Verify server command is correct
2. Check environment variables are set
3. Test server independently: run the MCP server command directly
4. Check firewall settings
5. Review logs: `~/.ucp/logs/ucp.log`

### Tool Indexing Issues

**Problem:** `ucp index` returns no tools

**Solutions:**
1. Verify downstream servers are configured
2. Check downstream servers are running
3. Run with verbose logging: `ucp index --log-level DEBUG`
4. Check ChromaDB installation: `pip show chromadb`

### Performance Issues

**Problem:** UCP is slow

**Solutions:**
1. Reduce `top_k` in configuration
2. Use smaller embedding model: `all-MiniLM-L6-v2`
3. Enable caching in configuration
4. Check system resources (CPU, memory)

## Next Steps

- Read [Architecture Overview](mvp_architecture.md) to understand how UCP works
- Read [User Guide](mvp_user_guide.md) for advanced usage
- Read [Deployment Guide](mvp_deployment.md) for production setup
- Check the main [README](../README.md) for project overview

## Getting Help

- **Documentation**: See [DOCUMENTATION_MAP.md](../../DOCUMENTATION_MAP.md)
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Debug**: Enable debug logging and check `~/.ucp/logs/ucp.log`


This guide will help you install, configure, and run the UCP Local MVP.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- (Optional) Claude Desktop for integration

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install ucp-mvp
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/your-org/UniversalContextProtocol.git
cd UniversalContextProtocol/local

# Install in development mode
pip install -e .
```

### Development Installation

If you want to contribute or modify UCP:

```bash
cd local
pip install -e ".[dev]"
```

This installs additional development dependencies:
- pytest (testing)
- mypy (type checking)
- ruff (linting)
- black (code formatting)

## Initial Configuration

### Generate Default Configuration

```bash
ucp init-config
```

This creates a default configuration file at `~/.ucp/ucp_config.yaml`.

### Configuration File Location

- **Linux/macOS**: `~/.ucp/ucp_config.yaml`
- **Windows**: `C:\Users\<username>\.ucp\ucp_config.yaml`

### Configuration Structure

The generated configuration includes:

```yaml
server:
  name: "UCP Gateway"
  transport: stdio
  log_level: INFO
  host: "localhost"
  port: 8765

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5
  similarity_threshold: 0.7
  persist_dir: "~/.ucp/data/tool_zoo"

router:
  mode: hybrid  # Options: semantic, keyword, hybrid
  max_tools: 10
  enable_co_occurrence: true
  enable_learning: true

session:
  persist_dir: "~/.ucp/data/sessions.db"
  max_history: 100

downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    tags: [files, local]
```

## Setting Up Downstream MCP Servers

UCP connects to downstream MCP servers that provide tools. Here's how to configure common servers:

### GitHub MCP Server

```yaml
downstream_servers:
  - name: github
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your-github-token"
    tags: [code, git, development]
```

**Get a GitHub token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`
4. Copy the token

### Gmail MCP Server

```yaml
downstream_servers:
  - name: gmail
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-gmail"]
    env:
      GMAIL_CLIENT_ID: "your-client-id"
      GMAIL_CLIENT_SECRET: "your-client-secret"
      GMAIL_REFRESH_TOKEN: "your-refresh-token"
    tags: [email, communication]
```

**Get Gmail credentials:**
1. Create a Google Cloud project
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Set up redirect URI for MCP server
5. Obtain refresh token

### Slack MCP Server

```yaml
downstream_servers:
  - name: slack
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-slack"]
    env:
      SLACK_BOT_TOKEN: "xoxb-your-bot-token"
      SLACK_APP_TOKEN: "xapp-your-app-token"
    tags: [chat, communication, team]
```

**Get Slack tokens:**
1. Create a Slack app
2. Enable bot permissions
3. Install app to workspace
4. Copy bot token and app token

### Filesystem MCP Server

```yaml
downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    tags: [files, local]
```

**Security Note:** Only allow access to directories you trust.

## Running UCP

### Start the Server

```bash
ucp serve
```

This starts UCP with the default configuration.

### Start with Custom Configuration

```bash
ucp serve -c /path/to/custom_config.yaml
```

### Start with Debug Logging

```bash
ucp serve --log-level DEBUG
```

### Start in Background (Linux/macOS)

```bash
nohup ucp serve > ucp.log 2>&1 &
```

### Start as Service (Windows)

Create a Windows service using NSSM or similar tools.

## Indexing Tools

After configuring downstream servers, index their tools:

```bash
ucp index
```

This command:
1. Connects to all configured downstream servers
2. Retrieves tool schemas
3. Generates embeddings for each tool
4. Stores in the local tool zoo (ChromaDB)

### Re-index After Changes

If you add or modify downstream servers, re-index:

```bash
ucp index --force
```

## Testing Your Setup

### Search for Tools

```bash
ucp search "send email" -k 5 --hybrid
```

This searches the tool zoo and returns the most relevant tools.

### Check Server Status

```bash
ucp status
```

This displays:
- Connected downstream servers
- Number of indexed tools
- Recent tool usage statistics
- Session information

### Test with Claude Desktop

1. Configure Claude Desktop (see below)
2. Open Claude Desktop
3. Start a conversation
4. Ask: "What tools do I have available?"
5. Claude should show only relevant tools based on context

## Claude Desktop Integration

### Configure Claude Desktop

1. Open Claude Desktop
2. Go to Settings → Developer
3. Edit the MCP servers configuration
4. Add UCP:

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

5. Save and restart Claude Desktop

### Verify Integration

1. Open a new Claude conversation
2. Ask: "List all my tools"
3. You should see tools from your configured MCP servers
4. Try a context-specific query: "How do I send an email?"
5. Claude should show only email-related tools

## Debug Dashboard

UCP includes a Streamlit dashboard for debugging and visualization.

### Start the Dashboard

```bash
pip install streamlit
streamlit run src/ucp_mvp/dashboard.py
```

### Dashboard Features

- **Tool Search**: Test semantic search with live results
- **Tool Zoo Stats**: View indexed tools and embeddings
- **Session History**: Explore conversation sessions
- **Router Learning**: Monitor tool usage patterns
- **Server Status**: Check downstream server connections

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
1. Check write permissions: `ls -la ~/.ucp`
2. Create directory manually: `mkdir -p ~/.ucp`
3. Check disk space

### Connection Issues

**Problem:** Downstream servers not connecting

**Solutions:**
1. Verify server command is correct
2. Check environment variables are set
3. Test server independently: run the MCP server command directly
4. Check firewall settings
5. Review logs: `~/.ucp/logs/ucp.log`

### Tool Indexing Issues

**Problem:** `ucp index` returns no tools

**Solutions:**
1. Verify downstream servers are configured
2. Check downstream servers are running
3. Run with verbose logging: `ucp index --log-level DEBUG`
4. Check ChromaDB installation: `pip show chromadb`

### Performance Issues

**Problem:** UCP is slow

**Solutions:**
1. Reduce `top_k` in configuration
2. Use smaller embedding model: `all-MiniLM-L6-v2`
3. Enable caching in configuration
4. Check system resources (CPU, memory)

## Next Steps

- Read [Architecture Overview](mvp_architecture.md) to understand how UCP works
- Read [User Guide](mvp_user_guide.md) for advanced usage
- Read [Production Deployment Guide](../../docs/production_deployment.md) for production setup
- Check the main [README](../README.md) for project overview

## Getting Help

- **Documentation**: See [DOCUMENTATION_MAP.md](../../DOCUMENTATION_MAP.md)
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Debug**: Enable debug logging and check `~/.ucp/logs/ucp.log`

This guide will help you install, configure, and run the UCP Local MVP.

## Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- (Optional) Claude Desktop for integration

## Installation

### Option 1: Install from PyPI (Recommended)

```bash
pip install ucp-mvp
```

### Option 2: Install from Source

```bash
# Clone the repository
git clone https://github.com/your-org/UniversalContextProtocol.git
cd UniversalContextProtocol/local

# Install in development mode
pip install -e .
```

### Development Installation

If you want to contribute or modify UCP:

```bash
cd local
pip install -e ".[dev]"
```

This installs additional development dependencies:
- pytest (testing)
- mypy (type checking)
- ruff (linting)
- black (code formatting)

## Initial Configuration

### Generate Default Configuration

```bash
ucp init-config
```

This creates a default configuration file at `~/.ucp/ucp_config.yaml`.

### Configuration File Location

- **Linux/macOS**: `~/.ucp/ucp_config.yaml`
- **Windows**: `C:\Users\<username>\.ucp\ucp_config.yaml`

### Configuration Structure

The generated configuration includes:

```yaml
server:
  name: "UCP Gateway"
  transport: stdio
  log_level: INFO
  host: "localhost"
  port: 8765

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5
  similarity_threshold: 0.7
  persist_dir: "~/.ucp/data/tool_zoo"

router:
  mode: hybrid  # Options: semantic, keyword, hybrid
  max_tools: 10
  enable_co_occurrence: true
  enable_learning: true

session:
  persist_dir: "~/.ucp/data/sessions.db"
  max_history: 100

downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    tags: [files, local]
```

## Setting Up Downstream MCP Servers

UCP connects to downstream MCP servers that provide tools. Here's how to configure common servers:

### GitHub MCP Server

```yaml
downstream_servers:
  - name: github
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your-github-token"
    tags: [code, git, development]
```

**Get a GitHub token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `read:org`
4. Copy the token

### Gmail MCP Server

```yaml
downstream_servers:
  - name: gmail
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-gmail"]
    env:
      GMAIL_CLIENT_ID: "your-client-id"
      GMAIL_CLIENT_SECRET: "your-client-secret"
      GMAIL_REFRESH_TOKEN: "your-refresh-token"
    tags: [email, communication]
```

**Get Gmail credentials:**
1. Create a Google Cloud project
2. Enable Gmail API
3. Create OAuth 2.0 credentials
4. Set up redirect URI for MCP server
5. Obtain refresh token

### Slack MCP Server

```yaml
downstream_servers:
  - name: slack
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-slack"]
    env:
      SLACK_BOT_TOKEN: "xoxb-your-bot-token"
      SLACK_APP_TOKEN: "xapp-your-app-token"
    tags: [chat, communication, team]
```

**Get Slack tokens:**
1. Create a Slack app
2. Enable bot permissions
3. Install app to workspace
4. Copy bot token and app token

### Filesystem MCP Server

```yaml
downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    tags: [files, local]
```

**Security Note:** Only allow access to directories you trust.

## Running UCP

### Start the Server

```bash
ucp serve
```

This starts UCP with the default configuration.

### Start with Custom Configuration

```bash
ucp serve -c /path/to/custom_config.yaml
```

### Start with Debug Logging

```bash
ucp serve --log-level DEBUG
```

### Start in Background (Linux/macOS)

```bash
nohup ucp serve > ucp.log 2>&1 &
```

### Start as Service (Windows)

Create a Windows service using NSSM or similar tools.

## Indexing Tools

After configuring downstream servers, index their tools:

```bash
ucp index
```

This command:
1. Connects to all configured downstream servers
2. Retrieves tool schemas
3. Generates embeddings for each tool
4. Stores in the local tool zoo (ChromaDB)

### Re-index After Changes

If you add or modify downstream servers, re-index:

```bash
ucp index --force
```

## Testing Your Setup

### Search for Tools

```bash
ucp search "send email" -k 5 --hybrid
```

This searches the tool zoo and returns the most relevant tools.

### Check Server Status

```bash
ucp status
```

This displays:
- Connected downstream servers
- Number of indexed tools
- Recent tool usage statistics
- Session information

### Test with Claude Desktop

1. Configure Claude Desktop (see below)
2. Open Claude Desktop
3. Start a conversation
4. Ask: "What tools do I have available?"
5. Claude should show only relevant tools based on context

## Claude Desktop Integration

### Configure Claude Desktop

1. Open Claude Desktop
2. Go to Settings → Developer
3. Edit the MCP servers configuration
4. Add UCP:

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

5. Save and restart Claude Desktop

### Verify Integration

1. Open a new Claude conversation
2. Ask: "List all my tools"
3. You should see tools from your configured MCP servers
4. Try a context-specific query: "How do I send an email?"
5. Claude should show only email-related tools

## Debug Dashboard

UCP includes a Streamlit dashboard for debugging and visualization.

### Start the Dashboard

```bash
pip install streamlit
streamlit run src/ucp_mvp/dashboard.py
```

### Dashboard Features

- **Tool Search**: Test semantic search with live results
- **Tool Zoo Stats**: View indexed tools and embeddings
- **Session History**: Explore conversation sessions
- **Router Learning**: Monitor tool usage patterns
- **Server Status**: Check downstream server connections

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
1. Check write permissions: `ls -la ~/.ucp`
2. Create directory manually: `mkdir -p ~/.ucp`
3. Check disk space

### Connection Issues

**Problem:** Downstream servers not connecting

**Solutions:**
1. Verify server command is correct
2. Check environment variables are set
3. Test server independently: run the MCP server command directly
4. Check firewall settings
5. Review logs: `~/.ucp/logs/ucp.log`

### Tool Indexing Issues

**Problem:** `ucp index` returns no tools

**Solutions:**
1. Verify downstream servers are configured
2. Check downstream servers are running
3. Run with verbose logging: `ucp index --log-level DEBUG`
4. Check ChromaDB installation: `pip show chromadb`

### Performance Issues

**Problem:** UCP is slow

**Solutions:**
1. Reduce `top_k` in configuration
2. Use smaller embedding model: `all-MiniLM-L6-v2`
3. Enable caching in configuration
4. Check system resources (CPU, memory)

## Next Steps

- Read [Architecture Overview](mvp_architecture.md) to understand how UCP works
- Read [User Guide](mvp_user_guide.md) for advanced usage
- Read [Deployment Guide](mvp_deployment.md) for production setup
- Check the main [README](../README.md) for project overview

## Getting Help

- **Documentation**: See [DOCUMENTATION_MAP.md](../../DOCUMENTATION_MAP.md)
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Debug**: Enable debug logging and check `~/.ucp/logs/ucp.log`


