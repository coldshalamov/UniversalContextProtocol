# UCP Shared Components

This directory contains shared code used by both the local MVP and cloud versions of UCP.

## Overview

The shared layer provides the foundation for both UCP implementations, ensuring compatibility and code reuse across versions.

## Purpose

The shared layer provides:
- **Data Models**: Common data structures (ToolSchema, SessionState, etc.)
- **Configuration**: Shared configuration classes and validation
- **Interfaces**: Abstract interfaces that both versions must implement
- **Exceptions**: Custom exceptions for error handling
- **Transport**: MCP protocol implementation and base transport class

## Structure

```
shared/
├── README.md                     # This file
├── pyproject.toml               # Shared package config
├── src/
│   ├── ucp_core/               # Core abstractions and interfaces
│   │   ├── __init__.py
│   │   ├── models.py             # Data models
│   │   ├── config.py             # Configuration classes
│   │   ├── interfaces.py         # Abstract interfaces
│   │   └── exceptions.py         # Custom exceptions
│   └── ucp_transport/           # Transport layer abstractions
│       ├── __init__.py
│       ├── base_transport.py     # Base transport class
│       ├── stdio_transport.py   # Stdio implementation
│       ├── http_transport.py     # HTTP/SSE implementation
│       └── mcp_protocol.py       # MCP protocol utilities
├── tests/                       # Shared tests and evaluation harness
│   ├── test_models.py
│   ├── test_config.py
│   ├── test_interfaces.py
│   └── test_transport.py
└── docs/
    └── api_reference.md        # Shared API documentation
```

## Components

### Data Models (`ucp_core/models.py`)

Common data structures used across both versions:

```python
@dataclass
class ToolSchema:
    """Represents a tool schema from an MCP server."""
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    tags: List[str]
    metadata: dict

@dataclass
class SessionState:
    """Represents the current session state."""
    session_id: str
    messages: List[Message]
    context: str
    tool_usage: Dict[str, int]
    created_at: datetime
    updated_at: datetime

@dataclass
class ToolCall:
    """Represents a tool call request."""
    tool_name: str
    arguments: dict
    context: str
    timestamp: datetime

@dataclass
class ToolResult:
    """Represents a tool call result."""
    success: bool
    result: Any
    error: Optional[str]
    execution_time: float
```

### Configuration (`ucp_core/config.py`)

Shared configuration classes:

```python
@dataclass
class UCPConfig:
    """Main UCP configuration."""
    server: ServerConfig
    tool_zoo: ToolZooConfig
    router: RouterConfig
    session: SessionConfig
    downstream_servers: List[DownstreamServerConfig]

@dataclass
class ServerConfig:
    """Server configuration."""
    name: str
    transport: str  # "stdio", "http", "sse"
    log_level: str
    host: str
    port: int

@dataclass
class ToolZooConfig:
    """Tool zoo configuration."""
    embedding_model: str
    top_k: int
    similarity_threshold: float
    persist_dir: str
```

### Interfaces (`ucp_core/interfaces.py`)

Abstract interfaces that both versions must implement:

```python
class IRouter(ABC):
    """Router interface for tool selection."""
    
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

class IToolZoo(ABC):
    """Tool zoo interface for tool storage and retrieval."""
    
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

class ISessionManager(ABC):
    """Session manager interface."""
    
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
```

### Exceptions (`ucp_core/exceptions.py`)

Custom exceptions for error handling:

```python
class UCPError(Exception):
    """Base UCP exception."""
    pass

class ToolNotFoundError(UCPError):
    """Raised when a tool is not found."""
    pass

class SessionNotFoundError(UCPError):
    """Raised when a session is not found."""
    pass

class ConfigurationError(UCPError):
    """Raised when configuration is invalid."""
    pass

class TransportError(UCPError):
    """Raised when transport operation fails."""
    pass

class RouterError(UCPError):
    """Raised when router operation fails."""
    pass
```

### Transport (`ucp_transport/`)

Transport layer implementations:

- **base_transport.py**: Abstract base class for all transports
- **stdio_transport.py**: Stdio transport (for Claude Desktop)
- **http_transport.py**: HTTP/SSE transport (for web apps)
- **mcp_protocol.py**: MCP protocol utilities and helpers

## Usage

This package is a dependency for both `local/` and `cloud/` versions:

```toml
# local/pyproject.toml or cloud/pyproject.toml
[project]
dependencies = [
    "ucp-core>=0.1.0",
]
```

### Installation

```bash
pip install ucp-core
```

### Development Installation

```bash
cd shared
pip install -e ".[dev]"
```

## Testing

### Run Tests

```bash
pytest tests/ -v
```

### Type Checking

```bash
mypy src/ucp_core/
mypy src/ucp_transport/
```

### Linting

```bash
ruff check src/ucp_core/
ruff check src/ucp_transport/
```

## Versioning

The shared package follows semantic versioning:

- **Major version**: Breaking changes
- **Minor version**: New features, backward compatible
- **Patch version**: Bug fixes, backward compatible

Both local and cloud versions should pin to specific shared versions:

```toml
[project]
dependencies = [
    "ucp-core==0.1.0",  # Pin to exact version
]
```

## Documentation

- [API Reference](docs/api_reference.md) - Shared API documentation
- [Main README](../README.md) - Project overview
- [Local README](../local/README.md) - Local MVP documentation
- [Cloud README](../cloud/README.md) - Cloud version documentation

## Contributing

When contributing to shared components:

1. **Maintain Compatibility**: Changes must work with both local and cloud versions
2. **Update Interfaces**: If changing interfaces, update both implementations
3. **Add Tests**: Ensure all changes have test coverage
4. **Update Docs**: Keep API reference up to date
5. **Version Carefully**: Consider impact on dependent versions

See main repository's [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) for contribution guidelines.

## License

MIT License

This directory contains shared code used by both the local MVP and cloud versions of UCP.

## Overview

The shared layer provides the foundation for both UCP implementations, ensuring compatibility and code reuse across versions.

## Purpose

The shared layer provides:
- **Data Models**: Common data structures (ToolSchema, SessionState, etc.)
- **Configuration**: Shared configuration classes and validation
- **Interfaces**: Abstract interfaces that both versions must implement
- **Exceptions**: Custom exceptions for error handling
- **Transport**: MCP protocol implementation and base transport class

## Structure

```
shared/
├── README.md                     # This file
├── pyproject.toml               # Shared package config
├── src/
│   ├── ucp_core/               # Core abstractions and interfaces
│   │   ├── __init__.py
│   │   ├── models.py             # Data models
│   │   ├── config.py             # Configuration classes
│   │   ├── interfaces.py         # Abstract interfaces
│   │   └── exceptions.py         # Custom exceptions
│   └── ucp_transport/           # Transport layer abstractions
│       ├── __init__.py
│       ├── base_transport.py     # Base transport class
│       ├── stdio_transport.py   # Stdio implementation
│       ├── http_transport.py     # HTTP/SSE implementation
│       └── mcp_protocol.py       # MCP protocol utilities
├── tests/                       # Shared tests and evaluation harness
│   ├── test_models.py
│   ├── test_config.py
│   ├── test_interfaces.py
│   └── test_transport.py
└── docs/
    └── api_reference.md        # Shared API documentation
```

## Components

### Data Models (`ucp_core/models.py`)

Common data structures used across both versions:

```python
@dataclass
class ToolSchema:
    """Represents a tool schema from an MCP server."""
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    tags: List[str]
    metadata: dict

@dataclass
class SessionState:
    """Represents the current session state."""
    session_id: str
    messages: List[Message]
    context: str
    tool_usage: Dict[str, int]
    created_at: datetime
    updated_at: datetime

@dataclass
class ToolCall:
    """Represents a tool call request."""
    tool_name: str
    arguments: dict
    context: str
    timestamp: datetime

@dataclass
class ToolResult:
    """Represents a tool call result."""
    success: bool
    result: Any
    error: Optional[str]
    execution_time: float
```

### Configuration (`ucp_core/config.py`)

Shared configuration classes:

```python
@dataclass
class UCPConfig:
    """Main UCP configuration."""
    server: ServerConfig
    tool_zoo: ToolZooConfig
    router: RouterConfig
    session: SessionConfig
    downstream_servers: List[DownstreamServerConfig]

@dataclass
class ServerConfig:
    """Server configuration."""
    name: str
    transport: str  # "stdio", "http", "sse"
    log_level: str
    host: str
    port: int

@dataclass
class ToolZooConfig:
    """Tool zoo configuration."""
    embedding_model: str
    top_k: int
    similarity_threshold: float
    persist_dir: str
```

### Interfaces (`ucp_core/interfaces.py`)

Abstract interfaces that both versions must implement:

```python
class IRouter(ABC):
    """Router interface for tool selection."""
    
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

class IToolZoo(ABC):
    """Tool zoo interface for tool storage and retrieval."""
    
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

class ISessionManager(ABC):
    """Session manager interface."""
    
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
```

### Exceptions (`ucp_core/exceptions.py`)

Custom exceptions for error handling:

```python
class UCPError(Exception):
    """Base UCP exception."""
    pass

class ToolNotFoundError(UCPError):
    """Raised when a tool is not found."""
    pass

class SessionNotFoundError(UCPError):
    """Raised when a session is not found."""
    pass

class ConfigurationError(UCPError):
    """Raised when configuration is invalid."""
    pass

class TransportError(UCPError):
    """Raised when transport operation fails."""
    pass

class RouterError(UCPError):
    """Raised when router operation fails."""
    pass
```

### Transport (`ucp_transport/`)

Transport layer implementations:

- **base_transport.py**: Abstract base class for all transports
- **stdio_transport.py**: Stdio transport (for Claude Desktop)
- **http_transport.py**: HTTP/SSE transport (for web apps)
- **mcp_protocol.py**: MCP protocol utilities and helpers

## Usage

This package is a dependency for both `local/` and `cloud/` versions:

```toml
# local/pyproject.toml or cloud/pyproject.toml
[project]
dependencies = [
    "ucp-core>=0.1.0",
]
```

### Installation

```bash
pip install ucp-core
```

### Development Installation

```bash
cd shared
pip install -e ".[dev]"
```

## Testing

### Run Tests

```bash
pytest tests/ -v
```

### Type Checking

```bash
mypy src/ucp_core/
mypy src/ucp_transport/
```

### Linting

```bash
ruff check src/ucp_core/
ruff check src/ucp_transport/
```

## Versioning

The shared package follows semantic versioning:

- **Major version**: Breaking changes
- **Minor version**: New features, backward compatible
- **Patch version**: Bug fixes, backward compatible

Both local and cloud versions should pin to specific shared versions:

```toml
[project]
dependencies = [
    "ucp-core==0.1.0",  # Pin to exact version
]
```

## Documentation

- [API Reference](docs/api_reference.md) - Shared API documentation
- [Main README](../README.md) - Project overview
- [Local README](../local/README.md) - Local MVP documentation
- [Cloud README](../cloud/README.md) - Cloud version documentation

## Contributing

When contributing to shared components:

1. **Maintain Compatibility**: Changes must work with both local and cloud versions
2. **Update Interfaces**: If changing interfaces, update both implementations
3. **Add Tests**: Ensure all changes have test coverage
4. **Update Docs**: Keep API reference up to date
5. **Version Carefully**: Consider impact on dependent versions

See main repository's [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) for contribution guidelines.

## License

MIT License

