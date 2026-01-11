# UCP Debugging Playbook

This document provides troubleshooting steps for common issues when working with UCP (Universal Context Protocol).

## Table of Contents

- [Real MCP Server Integration Issues](#real-mcp-server-integration-issues)
- [Common Configuration Problems](#common-configuration-problems)
- [Connection Issues](#connection-issues)
- [Tool Indexing Problems](#tool-indexing-problems)
- [Routing Issues](#routing-issues)
- [Environment Setup Issues](#environment-setup-issues)

---

## Real MCP Server Integration Issues

### Issue: MCP Server Connection Fails

**Symptoms:**
- Error: `Connection closed` when trying to connect to MCP server
- Server shows as `ERROR` status in connection pool
- Tools from server not discovered

**Common Causes:**
1. **Incorrect server path in configuration** - The filesystem path in `ucp_config.yaml` doesn't exist
2. **Missing dependencies** - Required MCP packages not installed
3. **Server command not found** - The npx command or server package isn't available

**Solutions:**

#### Solution 1: Verify Server Path
```yaml
# Check ucp_config.yaml
downstream_servers:
  - name: filesystem
    args:
      - "-y"
      - "@modelcontextprotocol/server-filesystem"
      - "D:/GitHub/Telomere/UniversalContextProtocol"  # Make sure this path exists
```

#### Solution 2: Install Missing Dependencies
```bash
# Install MCP client library
pip install mcp

# Install required MCP servers
npx -y @modelcontextprotocol/server-filesystem
npx -y @modelcontextprotocol/server-github
```

#### Solution 3: Test Server Connection Directly
```python
# Test MCP server connection without UCP
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_server():
    server_params = StdioServerParameters(
        command='npx',
        args=['-y', '@modelcontextprotocol/server-filesystem', '/path/to/project']
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            print(f"Found {len(tools_result.tools)} tools")
            for tool in tools_result.tools:
                print(f"  - {tool.name}")

asyncio.run(test_server())
```

---

## Common Configuration Problems

### Issue: Module Import Errors

**Symptoms:**
- `ImportError: cannot import name 'X' from 'ucp_core'`
- `AttributeError: module 'ucp_mvp' has no attribute 'Y'`
- `SyntaxError: invalid syntax` in __init__.py files

**Common Causes:**
1. **Duplicate content in __init__.py files** - File has been written twice
2. **Missing docstring quotes** - Docstrings not properly enclosed in triple quotes
3. **Wrong import paths** - Python path not set correctly

**Solutions:**

#### Solution 1: Fix Duplicate Content
Check `__init__.py` files for duplicate lines and remove them:
```bash
# Check for duplicates
grep -n "from" local/src/ucp_mvp/__init__.py
```

#### Solution 2: Fix Docstrings
Ensure docstrings use triple quotes:
```python
"""Correct docstring"""
# NOT:
UCP MVP - Local-first implementation
```

#### Solution 3: Fix Import Paths
Add correct paths before imports:
```python
import sys
sys.path.insert(0, 'D:/GitHub/Telomere/UniversalContextProtocol/local/src')
sys.path.insert(0, 'D:/GitHub/Telomere/UniversalContextProtocol/shared/src')

from ucp_mvp.connection_pool import ConnectionPool
```

---

## Connection Issues

### Issue: Connection Pool Fails to Connect

**Symptoms:**
- `AttributeError: 'ConnectionPool' object has no attribute 'connect'`
- `AttributeError: 'ConnectionPool' object has no attribute 'get_connection'`
- Server connections not established

**Common Causes:**
1. **Wrong method names** - Using non-existent methods
2. **Server not started** - Trying to get connection before connecting
3. **Connection failed silently** - Server process started but didn't initialize

**Solutions:**

#### Solution 1: Use Correct Connection Pool Methods
```python
# Correct usage:
pool = ConnectionPool(config)
await pool.connect_all()  # Connect to all servers

# Get tools from pool (no get_connection method)
tools = pool.all_tools  # Returns list of ToolSchema

# Call tools through pool
result = await pool.call_tool('tool_name', {'arg': 'value'})
```

#### Solution 2: Check Server Status Before Accessing Tools
```python
await pool.connect_all()

# Check server status
for server_name, server in pool._servers.items():
    print(f"{server_name}: {server.status}")
    
# Only proceed if connected
if pool._servers['filesystem'].status == ServerStatus.CONNECTED:
    tools = pool.all_tools
```

---

## Tool Indexing Problems

### Issue: Tool Zoo Initialization Fails

**Symptoms:**
- `TypeError: object NoneType can't be used in 'await' expression`
- `AttributeError: 'HybridToolZoo' object has no attribute 'index_tools'`
- ChromaDB directory creation fails with permission error

**Common Causes:**
1. **Wrong method name** - `index_tools` doesn't exist, use `index` instead
2. **Running from wrong directory** - Script not in project root
3. **Permission denied** - Can't create data directories

**Solutions:**

#### Solution 1: Use Correct Tool Zoo Methods
```python
# Correct usage:
tool_zoo = HybridToolZoo(config.tool_zoo)
tool_zoo.initialize()  # NOT async

# Index tools
await tool_zoo.index_tools(tools)  # This is async
```

#### Solution 2: Change to Project Directory Before Running
```python
import os
import sys

# Change to project directory
os.chdir('D:/GitHub/Telomere/UniversalContextProtocol')
sys.path.insert(0, 'D:/GitHub/Telomere/UniversalContextProtocol/local/src')
sys.path.insert(0, 'D:/GitHub/Telomere/UniversalContextProtocol/shared/src')

# Now run your code
from ucp_mvp.tool_zoo import HybridToolZoo
```

#### Solution 3: Create Data Directory Manually
```bash
# Create data directory
mkdir -p data

# Ensure permissions
chmod 755 data
```

---

## Routing Issues

### Issue: Router Doesn't Select Expected Tools

**Symptoms:**
- Query about GitHub returns filesystem tools instead
- Query about files returns GitHub tools instead
- Wrong tools selected for domain

**Common Causes:**
1. **Tools not indexed** - Tool zoo doesn't have the tools
2. **Embedding model not loaded** - Sentence transformer not initialized
3. **Similarity threshold too high** - No tools pass the threshold

**Solutions:**

#### Solution 1: Verify Tools Are Indexed
```python
# Check what's in the tool zoo
tools = tool_zoo.search("github")
print(f"Found {len(tools)} GitHub-related tools")

# Verify tools are indexed
if len(tools) == 0:
    print("No tools found - need to index first")
    await tool_zoo.index_tools(pool.all_tools)
```

#### Solution 2: Adjust Similarity Threshold
```yaml
# In ucp_config.yaml, lower the threshold
tool_zoo:
  similarity_threshold: 0.1  # Lower value = more tools returned
```

---

## Environment Setup Issues

### Issue: Package Installation Fails

**Symptoms:**
- `ModuleNotFoundError: No module named 'ucp_core'`
- `ModuleNotFoundError: No module named 'ucp_mvp'`
- `ImportError: cannot import name 'UCPConfig'`

**Common Causes:**
1. **Packages not installed** - ucp-core and ucp-mvp not installed
2. **Installed in wrong environment** - Different Python version
3. **Editable install not done** - Packages installed in development mode

**Solutions:**

#### Solution 1: Install Packages in Editable Mode
```bash
# Install shared package
cd D:/GitHub/Telomere/UniversalContextProtocol/shared
pip install -e .

# Install local package
cd D:/GitHub/Telomere/UniversalContextProtocol/local
pip install -e .
```

#### Solution 2: Verify Installation
```bash
# Verify packages are installed
pip list | grep ucp

# Verify they're in editable mode
pip show ucp-core
pip show ucp-mvp
```

---

## Testing MCP Server Integration

### Quick Test Script

```python
import asyncio
import sys
import os

# Change to project directory
os.chdir('D:/GitHub/Telomere/UniversalContextProtocol')
sys.path.insert(0, 'D:/GitHub/Telomere/UniversalContextProtocol/local/src')
sys.path.insert(0, 'D:/GitHub/Telomere/UniversalContextProtocol/shared/src')

async def test_ucp():
    print("Testing UCP MCP Server Integration...")
    
    from ucp_mvp.connection_pool import ConnectionPool
    from ucp_core.config import UCPConfig
    
    # Load config
    config = UCPConfig.load('ucp_config.yaml')
    print(f"Loaded config with {len(config.downstream_servers)} servers")
    
    # Create connection pool
    pool = ConnectionPool(config)
    
    # Connect to all servers
    print("\nConnecting to all servers...")
    await pool.connect_all()
    
    # List tools
    tools = pool.all_tools
    print(f"\nFound {len(tools)} tools from all servers:")
    for tool in tools:
        print(f"  - {tool.name} (server: {tool.server_name})")
    
    # Test calling a tool
    if tools:
        print(f"\nTesting {tools[0].name}...")
        result = await pool.call_tool(tools[0].name, {})
        print(f"Result: {result}")
    
    # Cleanup
    await pool.disconnect_all()
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_ucp())
```

---

## Success Criteria Checklist

When testing UCP with real MCP servers, verify:

- [ ] UCP successfully connects to 2+ real MCP servers
- [ ] Tools from both servers are indexed and searchable
- [ ] Tools can be called via UCP
- [ ] Context shift detection works between domains
- [ ] All functionality documented in this playbook

---

## Getting Help

If you encounter issues not covered in this playbook:

1. Check the logs in the data directory
2. Enable debug logging in `ucp_config.yaml`:
   ```yaml
   log_level: DEBUG
   ```
3. Review the source code for the relevant module
4. Check MCP server documentation at https://modelcontextprotocol.io
