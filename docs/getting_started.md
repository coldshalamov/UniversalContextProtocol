# Getting Started with UCP

This guide takes you from zero to running the Universal Context Protocol (UCP) gateway.

## Prerequisites

- Python 3.11+ (tested on 3.11/3.12)
- pip (or `uv`)

## 1. Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/Telomere/UniversalContextProtocol.git
cd UniversalContextProtocol
pip install -e ".[dev]"
```

If you have `uv` installed, this is typically faster and avoids system-Python issues:

```bash
uv python install 3.12
uv venv --python 3.12
uv pip install --python .venv -e ".[dev]"
```

## 2. Minimal Configuration

Create a file named `ucp_config.yaml` in the root directory. This example proxies a simple Echo server (you'll need to install it first or use any MCP server you have).

For this guide, we'll assume you have the `github` MCP server installed via `npx` (requires Node.js), or you can just run the internal mock if you are developing.

**Example `ucp_config.yaml`:**

```yaml
server:
  name: "My UCP Gateway"
  transport: stdio

tool_zoo:
  persist_directory: "./data/chromadb"
  top_k: 5
  similarity_threshold: 0.1

router:
  mode: hybrid
  max_tools: 10

session:
  persistence: sqlite
  sqlite_path: "./data/sessions.db"

downstream_servers:
  - name: github
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your_token_here" # Optional if not using github
    tags: [code, git]
```

## 3. Indexing Tools

Before UCP can route, it needs to know what tools are available. Run the index command:

```bash
ucp index
```

This connects to all downstream servers, fetches their tool lists, and builds the semantic index.

## 4. Running the Server

Start the UCP gateway:

```bash
ucp serve
```

This starts the server in `stdio` mode, ready to be connected to an MCP client like Claude Desktop.

## 5. Connecting Claude Desktop

Locate your Claude Desktop configuration file:
- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

Add the UCP entry:

```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "C:/absolute/path/to/ucp_config.yaml"]
    }
  }
}
```

Restart Claude Desktop. You should now see the UCP gateway. As you chat, UCP will dynamically swap the available tools.

## 6. Verification

To verify it's working:

1. Open Claude Desktop.
2. Ask "What tools do you have?" -> You might see a generic list or nothing if no context matches.
3. Ask "Check the pull requests in this repo" -> UCP detects "code" context and injects the GitHub tools. Claude sees them and answers.
