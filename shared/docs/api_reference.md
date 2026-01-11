# UCP Shared API Reference

This document provides comprehensive API reference for the shared UCP components used by both local MVP and cloud versions.

## Table of Contents

- [Data Models](#data-models)
- [Configuration](#configuration)
- [Interfaces](#interfaces)
- [Exceptions](#exceptions)
- [Transport Layer](#transport-layer)

## Data Models

### ToolSchema

Represents a tool schema from an MCP server.

```python
from ucp_core.models import ToolSchema

tool = ToolSchema(
    name="github.create_issue",
    description="Create a new GitHub issue",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "body": {"type": "string"}
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "issue_number": {"type": "integer"},
            "url": {"type": "string"}
        }
    },
    tags=["github", "issues", "code"],
    metadata={
        "server": "github",
        "version": "1.0.0"
    }
)
```

**Attributes:**
- `name` (str): Unique tool identifier
- `description` (str): Human-readable description
- `input_schema` (dict): JSON Schema for tool input
- `output_schema` (dict): JSON Schema for tool output
- `tags` (List[str]): Searchable tags
- `metadata` (dict): Additional metadata

### SessionState

Represents the current session state.

```python
from ucp_core.models import SessionState
from datetime import datetime

session = SessionState(
    session_id="abc123",
    messages=[
        {"role": "user", "content": "Send an email"},
        {"role": "assistant", "content": "I'll help with that"}
    ],
    context="send email about project update",
    tool_usage={
        "gmail.send_email": 5,
        "github.create_issue": 2
    },
    created_at=datetime.now(),
    updated_at=datetime.now()
)
```

**Attributes:**
- `session_id` (str): Unique session identifier
- `messages` (List[Message]): Conversation history
- `context` (str): Current conversation context
- `tool_usage` (Dict[str, int]): Tool usage counts
- `created_at` (datetime): Session creation timestamp
- `updated_at` (datetime): Last update timestamp

### ToolCall

Represents a tool call request.

```python
from ucp_core.models import ToolCall

call = ToolCall(
    tool_name="gmail.send_email",
    arguments={
        "to": "user@example.com",
        "subject": "Project Update",
        "body": "Here's the latest update..."
    },
    context="send email about project update",
    timestamp=datetime.now()
)
```

**Attributes:**
- `tool_name` (str): Name of tool to call
- `arguments` (dict): Tool arguments
- `context` (str): Conversation context
- `timestamp` (datetime): Call timestamp

### ToolResult

Represents a tool call result.

```python
from ucp_core.models import ToolResult

result = ToolResult(
    success=True,
    result={"message_id": "12345"},
    error=None,
    execution_time=0.523
)
```

**Attributes:**
- `success` (bool): Whether call succeeded
- `result` (Any): Tool output (if successful)
- `error` (Optional[str]): Error message (if failed)
- `execution_time` (float): Execution time in seconds

## Configuration

### UCPConfig

Main UCP configuration class.

```python
from ucp_core.config import UCPConfig, ServerConfig, ToolZooConfig

config = UCPConfig(
    server=ServerConfig(
        name="UCP Gateway",
        transport="stdio",
        log_level="INFO",
        host="localhost",
        port=8765
    ),
    tool_zoo=ToolZooConfig(
        embedding_model="all-MiniLM-L6-v2",
        top_k=5,
        similarity_threshold=0.7,
        persist_dir="~/.ucp/data/tool_zoo"
    ),
    router=RouterConfig(...),
    session=SessionConfig(...),
    downstream_servers=[...]
)
```

**Methods:**
- `load(path: str) -> UCPConfig`: Load configuration from YAML file
- `save(path: str) -> None`: Save configuration to YAML file
- `validate() -> bool`: Validate configuration

### ServerConfig

Server configuration.

```python
from ucp_core.config import ServerConfig

server_config = ServerConfig(
    name="UCP Gateway",
    transport="stdio",  # "stdio", "http", "sse"
    log_level="INFO",  # "DEBUG", "INFO", "WARNING", "ERROR"
    host="localhost",
    port=8765
)
```

**Attributes:**
- `name` (str): Server name
- `transport` (str): Transport type
- `log_level` (str): Logging level
- `host` (str): Server host
- `port` (int): Server port

### ToolZooConfig

Tool zoo configuration.

```python
from ucp_core.config import ToolZooConfig

zoo_config = ToolZooConfig(
    embedding_model="all-MiniLM-L6-v2",
    top_k=5,
    similarity_threshold=0.7,
    persist_dir="~/.ucp/data/tool_zoo"
)
```

**Attributes:**
- `embedding_model` (str): Sentence transformer model name
- `top_k` (int): Number of tools to return
- `similarity_threshold` (float): Minimum similarity score
- `persist_dir` (str): Directory for persistence

## Interfaces

### IRouter

Router interface for tool selection.

```python
from ucp_core.interfaces import IRouter, ToolSchema
from abc import ABC, abstractmethod

class MyRouter(IRouter):
    @abstractmethod
    async def select_tools(
        self,
        context: str,
        top_k: int
    ) -> List[ToolSchema]:
        """Select tools based on context."""
        pass
    
    @abstractmethod
    async def record_usage(
        self,
        tool_name: str,
        context: str
    ) -> None:
        """Record tool usage for learning."""
        pass
```

**Methods:**
- `select_tools(context: str, top_k: int) -> List[ToolSchema]`: Select relevant tools
- `record_usage(tool_name: str, context: str) -> None`: Record tool usage

### IToolZoo

Tool zoo interface for tool storage and retrieval.

```python
from ucp_core.interfaces import IToolZoo, ToolSchema
from abc import ABC, abstractmethod

class MyToolZoo(IToolZoo):
    @abstractmethod
    async def index_tool(
        self,
        tool: ToolSchema
    ) -> None:
        """Index a tool in the zoo."""
        pass
    
    @abstractmethod
    async def search_tools(
        self,
        query: str,
        top_k: int
    ) -> List[ToolSchema]:
        """Search for tools."""
        pass
    
    @abstractmethod
    async def delete_tool(
        self,
        tool_name: str
    ) -> None:
        """Delete a tool from the zoo."""
        pass
```

**Methods:**
- `index_tool(tool: ToolSchema) -> None`: Index a tool
- `search_tools(query: str, top_k: int) -> List[ToolSchema]`: Search for tools
- `delete_tool(tool_name: str) -> None`: Delete a tool

### ISessionManager

Session manager interface.

```python
from ucp_core.interfaces import ISessionManager, SessionState
from abc import ABC, abstractmethod

class MySessionManager(ISessionManager):
    @abstractmethod
    async def create_session(self) -> SessionState:
        """Create a new session."""
        pass
    
    @abstractmethod
    async def get_session(
        self,
        session_id: str
    ) -> Optional[SessionState]:
        """Get a session by ID."""
        pass
    
    @abstractmethod
    async def update_context(
        self,
        session_id: str,
        context: str
    ) -> None:
        """Update session context."""
        pass
    
    @abstractmethod
    async def delete_session(
        self,
        session_id: str
    ) -> None:
        """Delete a session."""
        pass
```

**Methods:**
- `create_session() -> SessionState`: Create new session
- `get_session(session_id: str) -> Optional[SessionState]`: Get session
- `update_context(session_id: str, context: str) -> None`: Update context
- `delete_session(session_id: str) -> None`: Delete session

## Exceptions

### UCPError

Base UCP exception.

```python
from ucp_core.exceptions import UCPError

raise UCPError("Something went wrong")
```

### ToolNotFoundError

Raised when a tool is not found.

```python
from ucp_core.exceptions import ToolNotFoundError

raise ToolNotFoundError("Tool 'github.create_issue' not found")
```

### SessionNotFoundError

Raised when a session is not found.

```python
from ucp_core.exceptions import SessionNotFoundError

raise SessionNotFoundError("Session 'abc123' not found")
```

### ConfigurationError

Raised when configuration is invalid.

```python
from ucp_core.exceptions import ConfigurationError

raise ConfigurationError("Invalid transport type")
```

### TransportError

Raised when transport operation fails.

```python
from ucp_core.exceptions import TransportError

raise TransportError("Failed to connect to MCP server")
```

### RouterError

Raised when router operation fails.

```python
from ucp_core.exceptions import RouterError

raise RouterError("Failed to select tools")
```

## Transport Layer

### BaseTransport

Abstract base class for all transports.

```python
from ucp_transport.base_transport import BaseTransport

class MyTransport(BaseTransport):
    async def initialize(self) -> None:
        """Initialize the transport."""
        pass
    
    async def list_tools(self) -> List[ToolSchema]:
        """List available tools."""
        pass
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict
    ) -> ToolResult:
        """Call a tool."""
        pass
    
    async def close(self) -> None:
        """Close the transport."""
        pass
```

**Methods:**
- `initialize() -> None`: Initialize transport
- `list_tools() -> List[ToolSchema]`: List tools
- `call_tool(tool_name: str, arguments: dict) -> ToolResult`: Call tool
- `close() -> None`: Close transport

### StdioTransport

Stdio transport for MCP servers.

```python
from ucp_transport.stdio_transport import StdioTransport

transport = StdioTransport(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"],
    env={"GITHUB_PERSONAL_ACCESS_TOKEN": "token"}
)

await transport.initialize()
tools = await transport.list_tools()
result = await transport.call_tool("github.create_issue", {...})
```

### HttpTransport

HTTP/SSE transport for MCP servers.

```python
from ucp_transport.http_transport import HttpTransport

transport = HttpTransport(
    url="http://localhost:3000/mcp",
    api_key="your-api-key"
)

await transport.initialize()
tools = await transport.list_tools()
result = await transport.call_tool("tool.name", {...})
```

## Usage Examples

### Loading Configuration

```python
from ucp_core.config import UCPConfig

# Load from file
config = UCPConfig.load("~/.ucp/ucp_config.yaml")

# Validate
if not config.validate():
    raise ConfigurationError("Invalid configuration")

# Access components
print(config.server.name)
print(config.tool_zoo.top_k)
```

### Creating a Router

```python
from ucp_core.interfaces import IRouter, ToolSchema
from ucp_core.models import SessionState

class SemanticRouter(IRouter):
    async def select_tools(
        self,
        context: str,
        top_k: int
    ) -> List[ToolSchema]:
        # Implement semantic search
        pass
    
    async def record_usage(
        self,
        tool_name: str,
        context: str
    ) -> None:
        # Record usage for learning
        pass
```

### Creating a Tool Zoo

```python
from ucp_core.interfaces import IToolZoo, ToolSchema

class ChromaDBToolZoo(IToolZoo):
    async def index_tool(self, tool: ToolSchema) -> None:
        # Index tool in ChromaDB
        pass
    
    async def search_tools(
        self,
        query: str,
        top_k: int
    ) -> List[ToolSchema]:
        # Search ChromaDB
        pass
```

### Handling Exceptions

```python
from ucp_core.exceptions import (
    UCPError,
    ToolNotFoundError,
    SessionNotFoundError,
    ConfigurationError
)

try:
    tools = await router.select_tools(context, top_k)
except ToolNotFoundError as e:
    print(f"Tool not found: {e}")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except UCPError as e:
    print(f"UCP error: {e}")
```

## Type Hints

All shared components use Python type hints:

```python
from typing import List, Dict, Optional, Any
from datetime import datetime

def select_tools(
    context: str,
    top_k: int
) -> List[ToolSchema]:
    """Select tools based on context."""
    pass
```

## Version Compatibility

The shared package uses semantic versioning. When using shared components:

```toml
[project]
dependencies = [
    "ucp-core>=0.1.0,<0.2.0",  # Compatible with 0.1.x
]
```

## Related Documentation

- [Shared README](../README.md) - Shared components overview
- [Local README](../../local/README.md) - Local MVP documentation
- [Cloud README](../../cloud/README.md) - Cloud version documentation
- [Main README](../../README.md) - Project overview

---

*Last updated: 2026-01-10*

This document provides comprehensive API reference for the shared UCP components used by both local MVP and cloud versions.

## Table of Contents

- [Data Models](#data-models)
- [Configuration](#configuration)
- [Interfaces](#interfaces)
- [Exceptions](#exceptions)
- [Transport Layer](#transport-layer)

## Data Models

### ToolSchema

Represents a tool schema from an MCP server.

```python
from ucp_core.models import ToolSchema

tool = ToolSchema(
    name="github.create_issue",
    description="Create a new GitHub issue",
    input_schema={
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "body": {"type": "string"}
        }
    },
    output_schema={
        "type": "object",
        "properties": {
            "issue_number": {"type": "integer"},
            "url": {"type": "string"}
        }
    },
    tags=["github", "issues", "code"],
    metadata={
        "server": "github",
        "version": "1.0.0"
    }
)
```

**Attributes:**
- `name` (str): Unique tool identifier
- `description` (str): Human-readable description
- `input_schema` (dict): JSON Schema for tool input
- `output_schema` (dict): JSON Schema for tool output
- `tags` (List[str]): Searchable tags
- `metadata` (dict): Additional metadata

### SessionState

Represents the current session state.

```python
from ucp_core.models import SessionState
from datetime import datetime

session = SessionState(
    session_id="abc123",
    messages=[
        {"role": "user", "content": "Send an email"},
        {"role": "assistant", "content": "I'll help with that"}
    ],
    context="send email about project update",
    tool_usage={
        "gmail.send_email": 5,
        "github.create_issue": 2
    },
    created_at=datetime.now(),
    updated_at=datetime.now()
)
```

**Attributes:**
- `session_id` (str): Unique session identifier
- `messages` (List[Message]): Conversation history
- `context` (str): Current conversation context
- `tool_usage` (Dict[str, int]): Tool usage counts
- `created_at` (datetime): Session creation timestamp
- `updated_at` (datetime): Last update timestamp

### ToolCall

Represents a tool call request.

```python
from ucp_core.models import ToolCall

call = ToolCall(
    tool_name="gmail.send_email",
    arguments={
        "to": "user@example.com",
        "subject": "Project Update",
        "body": "Here's the latest update..."
    },
    context="send email about project update",
    timestamp=datetime.now()
)
```

**Attributes:**
- `tool_name` (str): Name of tool to call
- `arguments` (dict): Tool arguments
- `context` (str): Conversation context
- `timestamp` (datetime): Call timestamp

### ToolResult

Represents a tool call result.

```python
from ucp_core.models import ToolResult

result = ToolResult(
    success=True,
    result={"message_id": "12345"},
    error=None,
    execution_time=0.523
)
```

**Attributes:**
- `success` (bool): Whether call succeeded
- `result` (Any): Tool output (if successful)
- `error` (Optional[str]): Error message (if failed)
- `execution_time` (float): Execution time in seconds

## Configuration

### UCPConfig

Main UCP configuration class.

```python
from ucp_core.config import UCPConfig, ServerConfig, ToolZooConfig

config = UCPConfig(
    server=ServerConfig(
        name="UCP Gateway",
        transport="stdio",
        log_level="INFO",
        host="localhost",
        port=8765
    ),
    tool_zoo=ToolZooConfig(
        embedding_model="all-MiniLM-L6-v2",
        top_k=5,
        similarity_threshold=0.7,
        persist_dir="~/.ucp/data/tool_zoo"
    ),
    router=RouterConfig(...),
    session=SessionConfig(...),
    downstream_servers=[...]
)
```

**Methods:**
- `load(path: str) -> UCPConfig`: Load configuration from YAML file
- `save(path: str) -> None`: Save configuration to YAML file
- `validate() -> bool`: Validate configuration

### ServerConfig

Server configuration.

```python
from ucp_core.config import ServerConfig

server_config = ServerConfig(
    name="UCP Gateway",
    transport="stdio",  # "stdio", "http", "sse"
    log_level="INFO",  # "DEBUG", "INFO", "WARNING", "ERROR"
    host="localhost",
    port=8765
)
```

**Attributes:**
- `name` (str): Server name
- `transport` (str): Transport type
- `log_level` (str): Logging level
- `host` (str): Server host
- `port` (int): Server port

### ToolZooConfig

Tool zoo configuration.

```python
from ucp_core.config import ToolZooConfig

zoo_config = ToolZooConfig(
    embedding_model="all-MiniLM-L6-v2",
    top_k=5,
    similarity_threshold=0.7,
    persist_dir="~/.ucp/data/tool_zoo"
)
```

**Attributes:**
- `embedding_model` (str): Sentence transformer model name
- `top_k` (int): Number of tools to return
- `similarity_threshold` (float): Minimum similarity score
- `persist_dir` (str): Directory for persistence

## Interfaces

### IRouter

Router interface for tool selection.

```python
from ucp_core.interfaces import IRouter, ToolSchema
from abc import ABC, abstractmethod

class MyRouter(IRouter):
    @abstractmethod
    async def select_tools(
        self,
        context: str,
        top_k: int
    ) -> List[ToolSchema]:
        """Select tools based on context."""
        pass
    
    @abstractmethod
    async def record_usage(
        self,
        tool_name: str,
        context: str
    ) -> None:
        """Record tool usage for learning."""
        pass
```

**Methods:**
- `select_tools(context: str, top_k: int) -> List[ToolSchema]`: Select relevant tools
- `record_usage(tool_name: str, context: str) -> None`: Record tool usage

### IToolZoo

Tool zoo interface for tool storage and retrieval.

```python
from ucp_core.interfaces import IToolZoo, ToolSchema
from abc import ABC, abstractmethod

class MyToolZoo(IToolZoo):
    @abstractmethod
    async def index_tool(
        self,
        tool: ToolSchema
    ) -> None:
        """Index a tool in the zoo."""
        pass
    
    @abstractmethod
    async def search_tools(
        self,
        query: str,
        top_k: int
    ) -> List[ToolSchema]:
        """Search for tools."""
        pass
    
    @abstractmethod
    async def delete_tool(
        self,
        tool_name: str
    ) -> None:
        """Delete a tool from the zoo."""
        pass
```

**Methods:**
- `index_tool(tool: ToolSchema) -> None`: Index a tool
- `search_tools(query: str, top_k: int) -> List[ToolSchema]`: Search for tools
- `delete_tool(tool_name: str) -> None`: Delete a tool

### ISessionManager

Session manager interface.

```python
from ucp_core.interfaces import ISessionManager, SessionState
from abc import ABC, abstractmethod

class MySessionManager(ISessionManager):
    @abstractmethod
    async def create_session(self) -> SessionState:
        """Create a new session."""
        pass
    
    @abstractmethod
    async def get_session(
        self,
        session_id: str
    ) -> Optional[SessionState]:
        """Get a session by ID."""
        pass
    
    @abstractmethod
    async def update_context(
        self,
        session_id: str,
        context: str
    ) -> None:
        """Update session context."""
        pass
    
    @abstractmethod
    async def delete_session(
        self,
        session_id: str
    ) -> None:
        """Delete a session."""
        pass
```

**Methods:**
- `create_session() -> SessionState`: Create new session
- `get_session(session_id: str) -> Optional[SessionState]`: Get session
- `update_context(session_id: str, context: str) -> None`: Update context
- `delete_session(session_id: str) -> None`: Delete session

## Exceptions

### UCPError

Base UCP exception.

```python
from ucp_core.exceptions import UCPError

raise UCPError("Something went wrong")
```

### ToolNotFoundError

Raised when a tool is not found.

```python
from ucp_core.exceptions import ToolNotFoundError

raise ToolNotFoundError("Tool 'github.create_issue' not found")
```

### SessionNotFoundError

Raised when a session is not found.

```python
from ucp_core.exceptions import SessionNotFoundError

raise SessionNotFoundError("Session 'abc123' not found")
```

### ConfigurationError

Raised when configuration is invalid.

```python
from ucp_core.exceptions import ConfigurationError

raise ConfigurationError("Invalid transport type")
```

### TransportError

Raised when transport operation fails.

```python
from ucp_core.exceptions import TransportError

raise TransportError("Failed to connect to MCP server")
```

### RouterError

Raised when router operation fails.

```python
from ucp_core.exceptions import RouterError

raise RouterError("Failed to select tools")
```

## Transport Layer

### BaseTransport

Abstract base class for all transports.

```python
from ucp_transport.base_transport import BaseTransport

class MyTransport(BaseTransport):
    async def initialize(self) -> None:
        """Initialize the transport."""
        pass
    
    async def list_tools(self) -> List[ToolSchema]:
        """List available tools."""
        pass
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: dict
    ) -> ToolResult:
        """Call a tool."""
        pass
    
    async def close(self) -> None:
        """Close the transport."""
        pass
```

**Methods:**
- `initialize() -> None`: Initialize transport
- `list_tools() -> List[ToolSchema]`: List tools
- `call_tool(tool_name: str, arguments: dict) -> ToolResult`: Call tool
- `close() -> None`: Close transport

### StdioTransport

Stdio transport for MCP servers.

```python
from ucp_transport.stdio_transport import StdioTransport

transport = StdioTransport(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-github"],
    env={"GITHUB_PERSONAL_ACCESS_TOKEN": "token"}
)

await transport.initialize()
tools = await transport.list_tools()
result = await transport.call_tool("github.create_issue", {...})
```

### HttpTransport

HTTP/SSE transport for MCP servers.

```python
from ucp_transport.http_transport import HttpTransport

transport = HttpTransport(
    url="http://localhost:3000/mcp",
    api_key="your-api-key"
)

await transport.initialize()
tools = await transport.list_tools()
result = await transport.call_tool("tool.name", {...})
```

## Usage Examples

### Loading Configuration

```python
from ucp_core.config import UCPConfig

# Load from file
config = UCPConfig.load("~/.ucp/ucp_config.yaml")

# Validate
if not config.validate():
    raise ConfigurationError("Invalid configuration")

# Access components
print(config.server.name)
print(config.tool_zoo.top_k)
```

### Creating a Router

```python
from ucp_core.interfaces import IRouter, ToolSchema
from ucp_core.models import SessionState

class SemanticRouter(IRouter):
    async def select_tools(
        self,
        context: str,
        top_k: int
    ) -> List[ToolSchema]:
        # Implement semantic search
        pass
    
    async def record_usage(
        self,
        tool_name: str,
        context: str
    ) -> None:
        # Record usage for learning
        pass
```

### Creating a Tool Zoo

```python
from ucp_core.interfaces import IToolZoo, ToolSchema

class ChromaDBToolZoo(IToolZoo):
    async def index_tool(self, tool: ToolSchema) -> None:
        # Index tool in ChromaDB
        pass
    
    async def search_tools(
        self,
        query: str,
        top_k: int
    ) -> List[ToolSchema]:
        # Search ChromaDB
        pass
```

### Handling Exceptions

```python
from ucp_core.exceptions import (
    UCPError,
    ToolNotFoundError,
    SessionNotFoundError,
    ConfigurationError
)

try:
    tools = await router.select_tools(context, top_k)
except ToolNotFoundError as e:
    print(f"Tool not found: {e}")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
except UCPError as e:
    print(f"UCP error: {e}")
```

## Type Hints

All shared components use Python type hints:

```python
from typing import List, Dict, Optional, Any
from datetime import datetime

def select_tools(
    context: str,
    top_k: int
) -> List[ToolSchema]:
    """Select tools based on context."""
    pass
```

## Version Compatibility

The shared package uses semantic versioning. When using shared components:

```toml
[project]
dependencies = [
    "ucp-core>=0.1.0,<0.2.0",  # Compatible with 0.1.x
]
```

## Related Documentation

- [Shared README](../README.md) - Shared components overview
- [Local README](../../local/README.md) - Local MVP documentation
- [Cloud README](../../cloud/README.md) - Cloud version documentation
- [Main README](../../README.md) - Project overview

---

*Last updated: 2026-01-10*

