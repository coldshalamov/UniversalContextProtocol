# Milestone 1.3: End-to-End Claude Desktop Test

## Overview

This document provides comprehensive instructions for testing the Universal Context Protocol (UCP) with Claude Desktop to validate end-to-end functionality with multiple domains.

## Prerequisites

1. **UCP Server Installed and Configured**
   - UCP should be installed in a Python virtual environment
   - Configuration file should be properly set up

2. **Claude Desktop Installed**
   - Claude Desktop application installed on your system
   - Access to Claude Desktop's MCP configuration directory

3. **Node.js Installed**
   - Required for downstream MCP servers (filesystem, GitHub)

4. **GitHub Personal Access Token** (for GitHub server)
   - Create a token with `repo` permissions
   - Store securely

## Step 1: Configure Claude Desktop to Use UCP

### 1.1 Locate Claude Desktop Configuration

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### 1.2 Create UCP Configuration

Create or update the `claude_desktop_config.json` file with the following content:

```json
{
  "mcpServers": {
    "ucp": {
      "command": "C:\\Users\\User\\Documents\\GitHub\\Telomere\\UniversalContextProtocol\\.venv\\Scripts\\ucp.exe",
      "args": [
        "serve",
        "-c",
        "C:\\Users\\User\\Documents\\GitHub\\Telomere\\UniversalContextProtocol\\ucp_config.yaml"
      ],
      "env": {
        "UCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Important Notes:**
- Update the `command` path to point to your UCP executable
- Update the `args` path to point to your UCP configuration file
- Use forward slashes (`/`) or escaped backslashes (`\\`) for paths
- Ensure the UCP virtual environment is properly activated

### 1.3 Verify UCP Configuration

Ensure your `ucp_config.yaml` has the following downstream servers configured:

```yaml
downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "D:/GitHub/Telomere/UniversalContextProtocol"
    tags:
      - files
      - local
      - documents
    description: "Local file system access for UCP project"

  - name: github
    transport: stdio
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-github"
      - "D:/GitHub/Telomere/UniversalContextProtocol"
    tags:
      - github
      - code
      - issues
      - pull_requests
    description: "GitHub integration for issues, PRs, and code"
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your-token-here"
```

### 1.4 Restart Claude Desktop

After updating the configuration:
1. Close Claude Desktop completely
2. Reopen Claude Desktop
3. UCP should automatically start and connect

## Step 2: Test Conversation Flow

### 2.1 Test Filesystem Tools Injection

**Test Query:**
```
List my files in the UniversalContextProtocol directory
```

**Expected Behavior:**
1. UCP analyzes the query
2. Detects filesystem domain context
3. Injects filesystem tools (e.g., `read_file`, `list_directory`, `write_file`)
4. Claude uses these tools to list files
5. Response includes file listing

**Tools Expected:**
- `read_file` - Read file contents
- `list_directory` - List directory contents
- `write_file` - Write to files
- `search_files` - Search for files

### 2.2 Test GitHub Tools Injection

**Test Query:**
```
Create a GitHub issue for a bug in the router
```

**Expected Behavior:**
1. UCP analyzes the query
2. Detects GitHub domain context
3. Injects GitHub tools (e.g., `create_issue`, `list_issues`, `get_repository`)
4. Claude uses these tools to create an issue
5. Response confirms issue creation

**Tools Expected:**
- `create_issue` - Create a new issue
- `list_issues` - List repository issues
- `get_issue` - Get issue details
- `update_issue` - Update an existing issue

### 2.3 Test Tool Switching (Context Shift Detection)

**Test Scenario:**
```
User: List my files in the project directory
[Claude uses filesystem tools]
User: Now create a GitHub issue for the README file
[Claude should switch to GitHub tools]
User: Go back and read the contents of the first file
[Claude should switch back to filesystem tools]
```

**Expected Behavior:**
1. UCP detects domain changes between messages
2. Dynamically injects appropriate tools for each context
3. Tool switching happens seamlessly
4. No manual intervention required

## Step 3: Record Session with Dashboard

### 3.1 Start the UCP Dashboard

In a separate terminal, navigate to the UCP project directory and run:

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux

# Run the dashboard
streamlit run local/src/ucp_mvp/dashboard.py
```

### 3.2 Monitor Session Data

The dashboard provides several tabs to monitor UCP activity:

1. **Tool Search** - Test tool discovery and search
2. **Tool Zoo Stats** - View indexed tools and statistics
3. **Session Explorer** - Monitor active sessions and tool usage
4. **Router Learning** - View learning statistics and patterns
5. **SOTA Metrics** - Advanced metrics (if SOTA mode enabled)
6. **Telemetry Details** - Detailed telemetry analysis

### 3.3 Capture Session Data

While testing with Claude Desktop:
1. Keep the dashboard open in a browser
2. Monitor the "Session Explorer" tab for real-time activity
3. Observe tool injection and routing decisions
4. Take screenshots of key moments

## Step 4: Verification Checklist

### Success Criteria

- [ ] Claude Desktop successfully connects to UCP
- [ ] Filesystem tools are injected for file-related queries
- [ ] GitHub tools are injected for GitHub-related queries
- [ ] Tool switching works seamlessly between domains
- [ ] Session data is captured in the dashboard
- [ ] No errors in UCP logs
- [ ] All downstream servers are accessible

### Expected Logs

When UCP is working correctly, you should see logs like:

```
INFO     starting_ucp_server transport=stdio downstream_count=2
INFO     Connected to downstream server: filesystem
INFO     Connected to downstream server: github
INFO     Tools indexed: 15
INFO     Routing decision: filesystem domain detected
INFO     Injected tools: read_file, list_directory, write_file
INFO     Tool call executed: list_directory
INFO     Routing decision: github domain detected
INFO     Injected tools: create_issue, list_issues
```

## Troubleshooting

### UCP Not Starting

**Symptom:** Claude Desktop shows connection error

**Solutions:**
1. Verify the UCP executable path is correct
2. Check that the virtual environment is properly activated
3. Ensure the configuration file path is valid
4. Check UCP logs for detailed error messages

### Tools Not Being Injected

**Symptom:** Claude doesn't have access to expected tools

**Solutions:**
1. Run `ucp index` to populate the Tool Zoo
2. Check that downstream servers are running
3. Verify tool descriptions and tags are set correctly
4. Check similarity threshold in configuration

### Context Shift Not Detected

**Symptom:** Tools don't switch between domains

**Solutions:**
1. Verify router mode is set to `hybrid` in config
2. Check that domain detection is enabled
3. Review tool tags and descriptions
4. Increase context window if needed

### Dashboard Not Showing Data

**Symptom:** Dashboard shows empty or no data

**Solutions:**
1. Ensure telemetry is enabled in configuration
2. Check that the database path is writable
3. Verify Streamlit is properly installed
4. Clear browser cache and reload dashboard

## Test Script

For automated testing, use the provided test script:

```bash
python tests/test_claude_desktop_integration.py
```

This script simulates Claude Desktop interactions and validates:
- Server connectivity
- Tool discovery
- Domain detection
- Tool injection
- Context switching
- Session recording

## Documentation

For more information, see:
- [UCP README](../README.md)
- [Getting Started Guide](../local/docs/getting_started.md)
- [API Reference](../shared/docs/api_reference.md)
- [Development Guide](../DEVELOPMENT_GUIDE.md)

## Next Steps

After successful testing:
1. Document any issues encountered
2. Record performance metrics
3. Create video demo if possible
4. Update test report with findings
5. Plan for next milestone

## Appendix: Configuration Examples

### Minimal Configuration

```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "ucp_config.yaml"]
    }
  }
}
```

### Configuration with Multiple MCP Servers

```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "ucp_config.yaml"],
      "env": {
        "UCP_LOG_LEVEL": "DEBUG"
      }
    },
    "filesystem-direct": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
  }
}
```

### Environment Variables

You can set environment variables in the Claude Desktop configuration:

```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "ucp_config.yaml"],
      "env": {
        "UCP_LOG_LEVEL": "INFO",
        "UCP_CONFIG_PATH": "/custom/path/config.yaml"
      }
    }
  }
}
```

## Contact and Support

For issues or questions:
- Check existing GitHub issues
- Create a new issue with detailed logs
- Include configuration files (sanitized)
- Provide screenshots of errors

## Overview

This document provides comprehensive instructions for testing the Universal Context Protocol (UCP) with Claude Desktop to validate end-to-end functionality with multiple domains.

## Prerequisites

1. **UCP Server Installed and Configured**
   - UCP should be installed in a Python virtual environment
   - Configuration file should be properly set up

2. **Claude Desktop Installed**
   - Claude Desktop application installed on your system
   - Access to Claude Desktop's MCP configuration directory

3. **Node.js Installed**
   - Required for downstream MCP servers (filesystem, GitHub)

4. **GitHub Personal Access Token** (for GitHub server)
   - Create a token with `repo` permissions
   - Store securely

## Step 1: Configure Claude Desktop to Use UCP

### 1.1 Locate Claude Desktop Configuration

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

### 1.2 Create UCP Configuration

Create or update the `claude_desktop_config.json` file with the following content:

```json
{
  "mcpServers": {
    "ucp": {
      "command": "C:\\Users\\User\\Documents\\GitHub\\Telomere\\UniversalContextProtocol\\.venv\\Scripts\\ucp.exe",
      "args": [
        "serve",
        "-c",
        "C:\\Users\\User\\Documents\\GitHub\\Telomere\\UniversalContextProtocol\\ucp_config.yaml"
      ],
      "env": {
        "UCP_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

**Important Notes:**
- Update the `command` path to point to your UCP executable
- Update the `args` path to point to your UCP configuration file
- Use forward slashes (`/`) or escaped backslashes (`\\`) for paths
- Ensure the UCP virtual environment is properly activated

### 1.3 Verify UCP Configuration

Ensure your `ucp_config.yaml` has the following downstream servers configured:

```yaml
downstream_servers:
  - name: filesystem
    transport: stdio
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "D:/GitHub/Telomere/UniversalContextProtocol"
    tags:
      - files
      - local
      - documents
    description: "Local file system access for UCP project"

  - name: github
    transport: stdio
    command: npx
    args:
      - "-y"
      - "@modelcontextprotocol/server-github"
      - "D:/GitHub/Telomere/UniversalContextProtocol"
    tags:
      - github
      - code
      - issues
      - pull_requests
    description: "GitHub integration for issues, PRs, and code"
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "your-token-here"
```

### 1.4 Restart Claude Desktop

After updating the configuration:
1. Close Claude Desktop completely
2. Reopen Claude Desktop
3. UCP should automatically start and connect

## Step 2: Test Conversation Flow

### 2.1 Test Filesystem Tools Injection

**Test Query:**
```
List my files in the UniversalContextProtocol directory
```

**Expected Behavior:**
1. UCP analyzes the query
2. Detects filesystem domain context
3. Injects filesystem tools (e.g., `read_file`, `list_directory`, `write_file`)
4. Claude uses these tools to list files
5. Response includes file listing

**Tools Expected:**
- `read_file` - Read file contents
- `list_directory` - List directory contents
- `write_file` - Write to files
- `search_files` - Search for files

### 2.2 Test GitHub Tools Injection

**Test Query:**
```
Create a GitHub issue for a bug in the router
```

**Expected Behavior:**
1. UCP analyzes the query
2. Detects GitHub domain context
3. Injects GitHub tools (e.g., `create_issue`, `list_issues`, `get_repository`)
4. Claude uses these tools to create an issue
5. Response confirms issue creation

**Tools Expected:**
- `create_issue` - Create a new issue
- `list_issues` - List repository issues
- `get_issue` - Get issue details
- `update_issue` - Update an existing issue

### 2.3 Test Tool Switching (Context Shift Detection)

**Test Scenario:**
```
User: List my files in the project directory
[Claude uses filesystem tools]
User: Now create a GitHub issue for the README file
[Claude should switch to GitHub tools]
User: Go back and read the contents of the first file
[Claude should switch back to filesystem tools]
```

**Expected Behavior:**
1. UCP detects domain changes between messages
2. Dynamically injects appropriate tools for each context
3. Tool switching happens seamlessly
4. No manual intervention required

## Step 3: Record Session with Dashboard

### 3.1 Start the UCP Dashboard

In a separate terminal, navigate to the UCP project directory and run:

```bash
# Activate virtual environment
.venv\Scripts\activate  # Windows
# or
source .venv/bin/activate  # macOS/Linux

# Run the dashboard
streamlit run local/src/ucp_mvp/dashboard.py
```

### 3.2 Monitor Session Data

The dashboard provides several tabs to monitor UCP activity:

1. **Tool Search** - Test tool discovery and search
2. **Tool Zoo Stats** - View indexed tools and statistics
3. **Session Explorer** - Monitor active sessions and tool usage
4. **Router Learning** - View learning statistics and patterns
5. **SOTA Metrics** - Advanced metrics (if SOTA mode enabled)
6. **Telemetry Details** - Detailed telemetry analysis

### 3.3 Capture Session Data

While testing with Claude Desktop:
1. Keep the dashboard open in a browser
2. Monitor the "Session Explorer" tab for real-time activity
3. Observe tool injection and routing decisions
4. Take screenshots of key moments

## Step 4: Verification Checklist

### Success Criteria

- [ ] Claude Desktop successfully connects to UCP
- [ ] Filesystem tools are injected for file-related queries
- [ ] GitHub tools are injected for GitHub-related queries
- [ ] Tool switching works seamlessly between domains
- [ ] Session data is captured in the dashboard
- [ ] No errors in UCP logs
- [ ] All downstream servers are accessible

### Expected Logs

When UCP is working correctly, you should see logs like:

```
INFO     starting_ucp_server transport=stdio downstream_count=2
INFO     Connected to downstream server: filesystem
INFO     Connected to downstream server: github
INFO     Tools indexed: 15
INFO     Routing decision: filesystem domain detected
INFO     Injected tools: read_file, list_directory, write_file
INFO     Tool call executed: list_directory
INFO     Routing decision: github domain detected
INFO     Injected tools: create_issue, list_issues
```

## Troubleshooting

### UCP Not Starting

**Symptom:** Claude Desktop shows connection error

**Solutions:**
1. Verify the UCP executable path is correct
2. Check that the virtual environment is properly activated
3. Ensure the configuration file path is valid
4. Check UCP logs for detailed error messages

### Tools Not Being Injected

**Symptom:** Claude doesn't have access to expected tools

**Solutions:**
1. Run `ucp index` to populate the Tool Zoo
2. Check that downstream servers are running
3. Verify tool descriptions and tags are set correctly
4. Check similarity threshold in configuration

### Context Shift Not Detected

**Symptom:** Tools don't switch between domains

**Solutions:**
1. Verify router mode is set to `hybrid` in config
2. Check that domain detection is enabled
3. Review tool tags and descriptions
4. Increase context window if needed

### Dashboard Not Showing Data

**Symptom:** Dashboard shows empty or no data

**Solutions:**
1. Ensure telemetry is enabled in configuration
2. Check that the database path is writable
3. Verify Streamlit is properly installed
4. Clear browser cache and reload dashboard

## Test Script

For automated testing, use the provided test script:

```bash
python tests/test_claude_desktop_integration.py
```

This script simulates Claude Desktop interactions and validates:
- Server connectivity
- Tool discovery
- Domain detection
- Tool injection
- Context switching
- Session recording

## Documentation

For more information, see:
- [UCP README](../README.md)
- [Getting Started Guide](../local/docs/getting_started.md)
- [API Reference](../shared/docs/api_reference.md)
- [Development Guide](../DEVELOPMENT_GUIDE.md)

## Next Steps

After successful testing:
1. Document any issues encountered
2. Record performance metrics
3. Create video demo if possible
4. Update test report with findings
5. Plan for next milestone

## Appendix: Configuration Examples

### Minimal Configuration

```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "ucp_config.yaml"]
    }
  }
}
```

### Configuration with Multiple MCP Servers

```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "ucp_config.yaml"],
      "env": {
        "UCP_LOG_LEVEL": "DEBUG"
      }
    },
    "filesystem-direct": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/dir"]
    }
  }
}
```

### Environment Variables

You can set environment variables in the Claude Desktop configuration:

```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "ucp_config.yaml"],
      "env": {
        "UCP_LOG_LEVEL": "INFO",
        "UCP_CONFIG_PATH": "/custom/path/config.yaml"
      }
    }
  }
}
```

## Contact and Support

For issues or questions:
- Check existing GitHub issues
- Create a new issue with detailed logs
- Include configuration files (sanitized)
- Provide screenshots of errors

