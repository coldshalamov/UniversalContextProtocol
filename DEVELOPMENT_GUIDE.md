# UCP Development Guide

This guide explains how to develop for the Universal Context Protocol (UCP) project with its dual-track architecture.

## Overview

UCP is organized into two complementary tracks with shared components:

- **Local-First MVP** ([`local/`](local/)) - Open source, privacy-focused, immediate value
- **Cloud Version** ([`cloud/`](cloud/)) - Future business, scalable, enterprise features
- **Shared Components** ([`shared/`](shared/)) - Common code used by both versions

## Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                  UCP Dual-Track Architecture                │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Local MVP  │  │   Shared     │  │  Cloud Ver. │ │
│  │             │  │             │  │             │ │
│  │  Privacy     │  │   Data       │  │  Scalability │ │
│  │  Simplicity   │  │   Models     │  │  Multi-tenant│ │
│  │  Local Data   │  │   Config     │  │  Cloud Infra │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git (for version control)
- (Recommended) Virtual environment (venv or conda)

### Creating a Virtual Environment

```bash
# Using venv
python -m venv .venv
source .venv/bin/activate

# Or using conda
conda create -n ucp-dev
conda activate ucp-dev
```

### Installing Dependencies

#### For Local MVP Development

```bash
cd local
pip install -e ".[dev]"
```

This installs:
- Core dependencies from `shared/pyproject.toml`
- MVP-specific dependencies from `local/pyproject.toml`
- Development tools (pytest, mypy, ruff, black)

#### For Cloud Version Development

```bash
cd cloud
pip install -e ".[dev]"
```

This installs:
- Core dependencies from `shared/pyproject.toml`
- Cloud-specific dependencies from `cloud/pyproject.toml`
- Development tools
- Additional cloud dependencies (FastAPI, Redis, Qdrant, etc.)

#### For Shared Components Development

```bash
cd shared
pip install -e ".[dev]"
```

This installs:
- Core dependencies only
- Development tools
- No version-specific dependencies

## Code Sharing Strategy

### Shared Components (`shared/`)

The shared layer contains code used by both local and cloud versions:

**What's in Shared:**
- **Data Models**: Common data structures (ToolSchema, SessionState, etc.)
- **Configuration**: Shared configuration classes and validation
- **Interfaces**: Abstract interfaces that both versions must implement
- **Exceptions**: Custom exceptions for error handling
- **Transport**: MCP protocol implementation and base transport class

**Key Principles:**
1. **Version Compatibility**: Shared code must work with both local and cloud versions
2. **No Version-Specific Logic**: Shared code should not contain version-specific features
3. **Interface-Based**: Both versions implement shared interfaces
4. **Semantic Versioning**: Follow semantic versioning (MAJOR.MINOR.PATCH)

**When to Update Shared:**
- Changes affect both versions → Major version bump (e.g., 0.1.0 → 1.0.0)
- New features, backward compatible → Minor version bump (e.g., 0.1.0 → 0.2.0)
- Bug fixes, backward compatible → Patch version bump (e.g., 0.1.0 → 0.1.1)

**Dependency Management:**
```toml
# local/pyproject.toml
[project]
dependencies = [
    "ucp-core>=0.1.0,<0.2.0",  # Allow compatible minor versions
]

# cloud/pyproject.toml
[project]
dependencies = [
    "ucp-core>=0.1.0,<0.2.0",  # Same constraint
]
```

### Local MVP (`local/`)

The local MVP implements simplified versions of shared interfaces:

**What's Different:**
- **Storage**: SQLite for sessions, ChromaDB for tool zoo (local only)
- **Router**: Baseline + Adaptive router (no cross-encoder, no bandit)
- **Transports**: Stdio only (no HTTP/SSE)
- **Dependencies**: Minimal external dependencies

**When to Update Local:**
- Focus on privacy and simplicity
- Avoid cloud-specific features
- Keep dependencies minimal
- Test thoroughly with local storage backends

### Cloud Version (`cloud/`)

The cloud version implements full SOTA versions of shared interfaces:

**What's Different:**
- **Storage**: Redis for sessions, Qdrant/Weaviate for tool zoo (cloud only)
- **Router**: Full SOTA pipeline with all features (cross-encoder, bandit, etc.)
- **Transports**: Stdio + HTTP/SSE support
- **Dependencies**: Cloud infrastructure (Redis, PostgreSQL, etc.)

**When to Update Cloud:**
- Implement all shared interfaces fully
- Add cloud-specific features (auth, billing, analytics)
- Test with cloud storage backends
- Ensure multi-tenant isolation

## Development Workflow

### Local MVP Development

1. **Setup Environment**
   ```bash
   cd local
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

3. **Make Changes**
   - Edit files in `local/src/ucp_mvp/`
   - Follow shared interfaces from `shared/src/ucp_core/`
   - Run type checker: `mypy local/src/ucp_mvp/`
   - Run linter: `ruff check local/src/ucp_mvp/`

4. **Test Changes**
   ```bash
   pytest tests/ -v -k "test_name"
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description"
   ```

### Cloud Version Development

1. **Setup Environment**
   ```bash
   cd cloud
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

3. **Make Changes**
   - Edit files in `cloud/src/ucp_cloud/`
   - Follow shared interfaces from `shared/src/ucp_core/`
   - Implement cloud-specific features
   - Run type checker: `mypy cloud/src/ucp_cloud/`
   - Run linter: `ruff check cloud/src/ucp_cloud/`

4. **Test Changes**
   ```bash
   pytest tests/ -v -k "test_name"
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description"
   ```

### Shared Components Development

1. **Setup Environment**
   ```bash
   cd shared
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

3. **Make Changes**
   - Edit files in `shared/src/ucp_core/` or `shared/src/ucp_transport/`
   - Maintain backward compatibility
   - Run type checker: `mypy shared/src/`
   - Run linter: `ruff check shared/src/`

4. **Test Changes**
   ```bash
   pytest tests/ -v
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description"
   ```

## Testing Strategies

### Unit Tests

**What to Test:**
- Individual functions and methods
- Error handling and edge cases
- Configuration validation
- Data model serialization

**Framework:** pytest

**Example Test:**
```python
# tests/test_router.py
import pytest
from ucp_core.interfaces import IRouter

def test_select_tools_basic():
    """Test basic tool selection."""
    router = MyRouter()
    tools = await router.select_tools("send email", 5)
    assert len(tools) == 5
    assert all(hasattr(tool, 'name') for tool in tools)
```

**Run Tests:**
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_router.py -v

# Run with coverage
pytest tests/ --cov=src/ucp_mvp --cov-report=html
```

### Integration Tests

**What to Test:**
- End-to-end workflows
- MCP server connections
- Tool calling and routing
- Session management

**Example Test:**
```python
# tests/integration/test_mcp_integration.py
import pytest
from ucp_mvp.server import UCPServer

@pytest.mark.asyncio
async def test_github_server_connection():
    """Test connection to GitHub MCP server."""
    server = UCPServer(config)
    await server.initialize()
    tools = await server._list_tools()
    assert len(tools) > 0
```

### Evaluation Tests

**What to Test:**
- Routing accuracy and precision
- Tool selection quality
- Performance metrics

**Framework:** Custom evaluation harness in `shared/tests/evaluation/`

**Example Test:**
```python
# tests/evaluation/test_routing_accuracy.py
from evaluation_harness import RoutingEvaluator

def test_routing_accuracy():
    """Test routing accuracy on test dataset."""
    evaluator = RoutingEvaluator(router)
    results = evaluator.evaluate(test_dataset)
    assert results['accuracy'] > 0.9
```

### Performance Tests

**What to Test:**
- Latency (P50, P95, P99)
- Throughput (requests per second)
- Memory usage
- CPU usage

**Example Test:**
```python
# tests/performance/test_benchmarks.py
import pytest
from ucp_mvp.server import UCPServer

@pytest.mark.benchmark
def test_tool_selection_latency():
    """Benchmark tool selection latency."""
    server = UCPServer(config)
    start = time.time()
    tools = await router.select_tools("send email", 5)
    latency = time.time() - start
    assert latency < 0.1  # 100ms
```

## Contributing Guidelines

### For Local MVP

1. **Focus Areas:**
   - Privacy and security
   - Performance optimization
   - User experience improvements
   - Documentation

2. **What to Contribute:**
   - Bug fixes
   - Performance improvements
   - Documentation updates
   - New features (discuss in issue first)

3. **What NOT to Contribute:**
   - Cloud-specific features (multi-tenancy, SaaS, etc.)
   - Complex infrastructure changes
   - Breaking changes to shared interfaces

4. **Pull Request Process:**
   - Fork the repository
   - Create a feature branch: `git checkout -b feature/my-feature`
   - Make your changes
   - Run tests: `pytest tests/ -v`
   - Commit changes with clear message
   - Push to your fork
   - Create pull request to main repository

### For Cloud Version

1. **Focus Areas:**
   - Scalability and reliability
   - Enterprise features (SSO, RBAC, SCIM)
   - Performance at scale
   - Security and compliance

2. **What to Contribute:**
   - Bug fixes
   - Performance optimizations
   - Security improvements
   - Documentation
   - New features (discuss in issue first)

3. **What NOT to Contribute:**
   - Local-specific features
   - Privacy-focused changes that conflict with cloud model
   - Breaking changes to shared interfaces

4. **Pull Request Process:**
   - Same as Local MVP
   - Additional cloud-specific tests required

### For Shared Components

1. **Focus Areas:**
   - Interface stability
   - Backward compatibility
   - Documentation completeness
   - Type safety

2. **What to Contribute:**
   - Bug fixes
   - New features (discuss impact on both versions)
   - Documentation improvements
   - Type hints and annotations

3. **What NOT to Contribute:**
   - Version-specific logic
   - Breaking changes without major version bump
   - Changes that only benefit one version

4. **Pull Request Process:**
   - Same as Local MVP
   - Additional review required for backward compatibility

## Code Style Guidelines

### Python Style

Follow PEP 8 style guidelines:

```python
# Good
def select_tools(self, context: str, top_k: int) -> List[ToolSchema]:
    """Select tools based on context."""
    pass

# Bad
def selectTools(self,context,top_k):
    """Select tools based on context."""
    pass
```

### Type Hints

Use type hints for all public functions:

```python
from typing import List, Dict, Optional

def select_tools(
    self,
    context: str,
    top_k: int
) -> List[ToolSchema]:
    """Select tools based on context."""
    pass
```

### Docstrings

Use docstrings for all modules, classes, and functions:

```python
class SemanticRouter(IRouter):
    """Router for semantic tool selection.
    
    Uses embeddings to find relevant tools based on
    conversation context.
    """
    
    async def select_tools(
        self,
        context: str,
        top_k: int
    ) -> List[ToolSchema]:
        """Select tools based on context."""
        pass
```

## Version Management

### Semantic Versioning

UCP follows semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes, incompatible API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

**Examples:**
- `0.1.0` → `0.2.0` (Minor: New features)
- `0.2.0` → `0.2.1` (Patch: Bug fixes)
- `1.0.0` → `2.0.0` (Major: Breaking changes)

### Release Process

1. Update version numbers in `pyproject.toml` files
2. Update `__init__.py` files with version
3. Create git tag: `git tag -a v0.1.0`
4. Create release notes
5. Push to PyPI (for local) or deploy (for cloud)

## Documentation

### Where to Document

- **Code**: Docstrings in source code
- **API**: [`shared/docs/api_reference.md`](shared/docs/api_reference.md)
- **Architecture**: [`docs/`](docs/) folder
- **User Guides**: Version-specific guides in `local/docs/` and `cloud/docs/`

### Documentation Standards

- Clear and concise
- Include examples
- Explain "why" and "how"
- Keep up to date with code changes
- Use consistent terminology

## Common Issues and Solutions

### Import Errors

**Problem**: Cannot import from shared package

**Solution**:
```bash
# Make sure you're in the right directory
cd local  # or cd cloud
# Install in development mode
pip install -e "../shared"
```

### Type Checking Errors

**Problem**: mypy reports type errors

**Solution**:
```python
# Add type hints
from typing import List, Optional

# Use type ignore comments if needed
# type: ignore
```

### Test Failures

**Problem**: Tests fail locally but pass in CI

**Solution**:
```bash
# Check environment variables
echo $PYTHONPATH

# Run tests with verbose output
pytest tests/ -v -s

# Check for specific test
pytest tests/ -k "test_name"
```

### Performance Issues

**Problem**: UCP is slow

**Solutions:**
1. Reduce `top_k` in configuration
2. Use smaller embedding model
3. Enable caching (if available)
4. Profile code: `python -m cProfile`
5. Check database queries

## Debugging

### Local Development

```bash
# Enable debug logging
ucp serve --log-level DEBUG

# Run with debug dashboard
streamlit run local/src/ucp_mvp/dashboard.py

# Check logs
tail -f ~/.ucp/logs/ucp.log
```

### Cloud Development

```bash
# Enable debug logging
UCP_LOG_LEVEL=DEBUG ucp-cloud serve

# Check logs (cloud infrastructure)
kubectl logs -f deployment/ucp-cloud

# Use debug dashboard
streamlit run cloud/src/ucp_cloud/dashboard.py
```

## Deployment

### Local MVP

**Development:**
```bash
# Test locally
cd local
pytest tests/ -v

# Build package
python -m build
```

**Release:**
```bash
# Build PyPI package
cd local
python -m build
twine upload dist/*

# Build Docker image
docker build -t ucp-mvp .
docker tag ucp-mvp:latest
docker push ucp-mvp:latest
```

### Cloud Version

**Development:**
```bash
# Test locally
cd cloud
pytest tests/ -v

# Build package
python -m build
```

**Release:**
```bash
# Deploy to Kubernetes
cd infrastructure/kubernetes
kubectl apply -f .

# Or use Helm
helm upgrade ucp-cloud ./ucp-cloud
```

## Continuous Integration

### GitHub Actions

**Workflow:**
1. On push to main → Run tests
2. On pull request → Run tests
3. On merge → Deploy to staging
4. On release → Deploy to production

**Example Workflow File** (`.github/workflows/ci.yml`):
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest tests/ -v
```

## Best Practices

### 1. Write Tests First

Write tests before or alongside code:

```python
# tests/test_router.py
import pytest
from ucp_core.interfaces import IRouter

@pytest.mark.asyncio
async def test_select_tools_returns_list():
    """Test that select_tools returns a list."""
    router = MyRouter()
    tools = await router.select_tools("test", 5)
    assert isinstance(tools, list)
```

### 2. Keep Tests Simple

Avoid complex test setup:

```python
# Bad: Complex setup
@pytest.fixture
def complex_setup():
    # ... lots of setup code ...
    return router, session, tool_zoo

def test_with_complex_setup(complex_setup):
    # ... test uses complex setup ...
    pass

# Good: Simple setup
@pytest.mark.asyncio
async def test_select_tools_simple():
    """Test with simple setup."""
    router = MyRouter()
    tools = await router.select_tools("test", 5)
    assert len(tools) == 5
```

### 3. Test Edge Cases

Test error conditions and edge cases:

```python
@pytest.mark.asyncio
async def test_select_tools_with_empty_context():
    """Test with empty context."""
    router = MyRouter()
    tools = await router.select_tools("", 5)
    assert len(tools) == 5  # Should still return tools
```

### 4. Use Async Tests Properly

Use async test fixtures and await properly:

```python
@pytest.mark.asyncio
async def test_async_operations():
    """Test async operations correctly."""
    server = UCPServer(config)
    await server.initialize()
    tools = await server._list_tools()
    assert len(tools) > 0
```

## Getting Help

### Documentation

- [README.md](README.md) - Project overview
- [DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md) - Documentation navigation
- [shared/docs/api_reference.md](shared/docs/api_reference.md) - Shared API reference
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP guide
- [cloud/docs/roadmap.md](cloud/docs/roadmap.md) - Cloud roadmap

### Issues and Discussions

- **GitHub Issues**: Report bugs and feature requests
- **GitHub Discussions**: Ask questions and discuss ideas

### Code Review

- All pull requests require review
- At least one maintainer must approve
- Focus on code quality, not just functionality

## Resources

### Internal Documentation

- [Shared Components](shared/README.md) - Shared layer overview
- [Local MVP](local/README.md) - Local MVP documentation
- [Cloud Version](cloud/README.md) - Cloud version documentation
- [Repository Reorganization Plan](plans/repository_reorganization_plan.md) - Reorganization details

### External References

- [MCP Specification](https://modelcontextprotocol.io/) - MCP protocol
- [Gorilla Paper](https://arxiv.org/abs/2305.15334) - Tool selection research
- [RAFT Paper](https://arxiv.org/abs/2309.15217) - Fine-tuning research
- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow orchestration

## Summary

This guide provides comprehensive development guidelines for UCP's dual-track architecture:

- **Shared Components**: Foundation for both versions
- **Local MVP**: Privacy-focused, immediate value, open source
- **Cloud Version**: Scalable, multi-tenant, enterprise features

Key principles:
1. Maintain backward compatibility in shared components
2. Keep version-specific features separate
3. Write tests alongside code
4. Follow semantic versioning
5. Document all changes
6. Test thoroughly before committing

For specific questions or issues, please refer to the relevant documentation or open a GitHub issue.

---

*Last updated: 2026-01-10*

This guide explains how to develop for the Universal Context Protocol (UCP) project with its dual-track architecture.

## Overview

UCP is organized into two complementary tracks with shared components:

- **Local-First MVP** ([`local/`](local/)) - Open source, privacy-focused, immediate value
- **Cloud Version** ([`cloud/`](cloud/)) - Future business, scalable, enterprise features
- **Shared Components** ([`shared/`](shared/)) - Common code used by both versions

## Architecture Summary

```
┌─────────────────────────────────────────────────────────┐
│                  UCP Dual-Track Architecture                │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Local MVP  │  │   Shared     │  │  Cloud Ver. │ │
│  │             │  │             │  │             │ │
│  │  Privacy     │  │   Data       │  │  Scalability │ │
│  │  Simplicity   │  │   Models     │  │  Multi-tenant│ │
│  │  Local Data   │  │   Config     │  │  Cloud Infra │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Development Setup

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git (for version control)
- (Recommended) Virtual environment (venv or conda)

### Creating a Virtual Environment

```bash
# Using venv
python -m venv .venv
source .venv/bin/activate

# Or using conda
conda create -n ucp-dev
conda activate ucp-dev
```

### Installing Dependencies

#### For Local MVP Development

```bash
cd local
pip install -e ".[dev]"
```

This installs:
- Core dependencies from `shared/pyproject.toml`
- MVP-specific dependencies from `local/pyproject.toml`
- Development tools (pytest, mypy, ruff, black)

#### For Cloud Version Development

```bash
cd cloud
pip install -e ".[dev]"
```

This installs:
- Core dependencies from `shared/pyproject.toml`
- Cloud-specific dependencies from `cloud/pyproject.toml`
- Development tools
- Additional cloud dependencies (FastAPI, Redis, Qdrant, etc.)

#### For Shared Components Development

```bash
cd shared
pip install -e ".[dev]"
```

This installs:
- Core dependencies only
- Development tools
- No version-specific dependencies

## Code Sharing Strategy

### Shared Components (`shared/`)

The shared layer contains code used by both local and cloud versions:

**What's in Shared:**
- **Data Models**: Common data structures (ToolSchema, SessionState, etc.)
- **Configuration**: Shared configuration classes and validation
- **Interfaces**: Abstract interfaces that both versions must implement
- **Exceptions**: Custom exceptions for error handling
- **Transport**: MCP protocol implementation and base transport class

**Key Principles:**
1. **Version Compatibility**: Shared code must work with both local and cloud versions
2. **No Version-Specific Logic**: Shared code should not contain version-specific features
3. **Interface-Based**: Both versions implement shared interfaces
4. **Semantic Versioning**: Follow semantic versioning (MAJOR.MINOR.PATCH)

**When to Update Shared:**
- Changes affect both versions → Major version bump (e.g., 0.1.0 → 1.0.0)
- New features, backward compatible → Minor version bump (e.g., 0.1.0 → 0.2.0)
- Bug fixes, backward compatible → Patch version bump (e.g., 0.1.0 → 0.1.1)

**Dependency Management:**
```toml
# local/pyproject.toml
[project]
dependencies = [
    "ucp-core>=0.1.0,<0.2.0",  # Allow compatible minor versions
]

# cloud/pyproject.toml
[project]
dependencies = [
    "ucp-core>=0.1.0,<0.2.0",  # Same constraint
]
```

### Local MVP (`local/`)

The local MVP implements simplified versions of shared interfaces:

**What's Different:**
- **Storage**: SQLite for sessions, ChromaDB for tool zoo (local only)
- **Router**: Baseline + Adaptive router (no cross-encoder, no bandit)
- **Transports**: Stdio only (no HTTP/SSE)
- **Dependencies**: Minimal external dependencies

**When to Update Local:**
- Focus on privacy and simplicity
- Avoid cloud-specific features
- Keep dependencies minimal
- Test thoroughly with local storage backends

### Cloud Version (`cloud/`)

The cloud version implements full SOTA versions of shared interfaces:

**What's Different:**
- **Storage**: Redis for sessions, Qdrant/Weaviate for tool zoo (cloud only)
- **Router**: Full SOTA pipeline with all features (cross-encoder, bandit, etc.)
- **Transports**: Stdio + HTTP/SSE support
- **Dependencies**: Cloud infrastructure (Redis, PostgreSQL, etc.)

**When to Update Cloud:**
- Implement all shared interfaces fully
- Add cloud-specific features (auth, billing, analytics)
- Test with cloud storage backends
- Ensure multi-tenant isolation

## Development Workflow

### Local MVP Development

1. **Setup Environment**
   ```bash
   cd local
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

3. **Make Changes**
   - Edit files in `local/src/ucp_mvp/`
   - Follow shared interfaces from `shared/src/ucp_core/`
   - Run type checker: `mypy local/src/ucp_mvp/`
   - Run linter: `ruff check local/src/ucp_mvp/`

4. **Test Changes**
   ```bash
   pytest tests/ -v -k "test_name"
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description"
   ```

### Cloud Version Development

1. **Setup Environment**
   ```bash
   cd cloud
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

3. **Make Changes**
   - Edit files in `cloud/src/ucp_cloud/`
   - Follow shared interfaces from `shared/src/ucp_core/`
   - Implement cloud-specific features
   - Run type checker: `mypy cloud/src/ucp_cloud/`
   - Run linter: `ruff check cloud/src/ucp_cloud/`

4. **Test Changes**
   ```bash
   pytest tests/ -v -k "test_name"
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description"
   ```

### Shared Components Development

1. **Setup Environment**
   ```bash
   cd shared
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

2. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

3. **Make Changes**
   - Edit files in `shared/src/ucp_core/` or `shared/src/ucp_transport/`
   - Maintain backward compatibility
   - Run type checker: `mypy shared/src/`
   - Run linter: `ruff check shared/src/`

4. **Test Changes**
   ```bash
   pytest tests/ -v
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: description"
   ```

## Testing Strategies

### Unit Tests

**What to Test:**
- Individual functions and methods
- Error handling and edge cases
- Configuration validation
- Data model serialization

**Framework:** pytest

**Example Test:**
```python
# tests/test_router.py
import pytest
from ucp_core.interfaces import IRouter

def test_select_tools_basic():
    """Test basic tool selection."""
    router = MyRouter()
    tools = await router.select_tools("send email", 5)
    assert len(tools) == 5
    assert all(hasattr(tool, 'name') for tool in tools)
```

**Run Tests:**
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_router.py -v

# Run with coverage
pytest tests/ --cov=src/ucp_mvp --cov-report=html
```

### Integration Tests

**What to Test:**
- End-to-end workflows
- MCP server connections
- Tool calling and routing
- Session management

**Example Test:**
```python
# tests/integration/test_mcp_integration.py
import pytest
from ucp_mvp.server import UCPServer

@pytest.mark.asyncio
async def test_github_server_connection():
    """Test connection to GitHub MCP server."""
    server = UCPServer(config)
    await server.initialize()
    tools = await server._list_tools()
    assert len(tools) > 0
```

### Evaluation Tests

**What to Test:**
- Routing accuracy and precision
- Tool selection quality
- Performance metrics

**Framework:** Custom evaluation harness in `shared/tests/evaluation/`

**Example Test:**
```python
# tests/evaluation/test_routing_accuracy.py
from evaluation_harness import RoutingEvaluator

def test_routing_accuracy():
    """Test routing accuracy on test dataset."""
    evaluator = RoutingEvaluator(router)
    results = evaluator.evaluate(test_dataset)
    assert results['accuracy'] > 0.9
```

### Performance Tests

**What to Test:**
- Latency (P50, P95, P99)
- Throughput (requests per second)
- Memory usage
- CPU usage

**Example Test:**
```python
# tests/performance/test_benchmarks.py
import pytest
from ucp_mvp.server import UCPServer

@pytest.mark.benchmark
def test_tool_selection_latency():
    """Benchmark tool selection latency."""
    server = UCPServer(config)
    start = time.time()
    tools = await router.select_tools("send email", 5)
    latency = time.time() - start
    assert latency < 0.1  # 100ms
```

## Contributing Guidelines

### For Local MVP

1. **Focus Areas:**
   - Privacy and security
   - Performance optimization
   - User experience improvements
   - Documentation

2. **What to Contribute:**
   - Bug fixes
   - Performance improvements
   - Documentation updates
   - New features (discuss in issue first)

3. **What NOT to Contribute:**
   - Cloud-specific features (multi-tenancy, SaaS, etc.)
   - Complex infrastructure changes
   - Breaking changes to shared interfaces

4. **Pull Request Process:**
   - Fork the repository
   - Create a feature branch: `git checkout -b feature/my-feature`
   - Make your changes
   - Run tests: `pytest tests/ -v`
   - Commit changes with clear message
   - Push to your fork
   - Create pull request to main repository

### For Cloud Version

1. **Focus Areas:**
   - Scalability and reliability
   - Enterprise features (SSO, RBAC, SCIM)
   - Performance at scale
   - Security and compliance

2. **What to Contribute:**
   - Bug fixes
   - Performance optimizations
   - Security improvements
   - Documentation
   - New features (discuss in issue first)

3. **What NOT to Contribute:**
   - Local-specific features
   - Privacy-focused changes that conflict with cloud model
   - Breaking changes to shared interfaces

4. **Pull Request Process:**
   - Same as Local MVP
   - Additional cloud-specific tests required

### For Shared Components

1. **Focus Areas:**
   - Interface stability
   - Backward compatibility
   - Documentation completeness
   - Type safety

2. **What to Contribute:**
   - Bug fixes
   - New features (discuss impact on both versions)
   - Documentation improvements
   - Type hints and annotations

3. **What NOT to Contribute:**
   - Version-specific logic
   - Breaking changes without major version bump
   - Changes that only benefit one version

4. **Pull Request Process:**
   - Same as Local MVP
   - Additional review required for backward compatibility

## Code Style Guidelines

### Python Style

Follow PEP 8 style guidelines:

```python
# Good
def select_tools(self, context: str, top_k: int) -> List[ToolSchema]:
    """Select tools based on context."""
    pass

# Bad
def selectTools(self,context,top_k):
    """Select tools based on context."""
    pass
```

### Type Hints

Use type hints for all public functions:

```python
from typing import List, Dict, Optional

def select_tools(
    self,
    context: str,
    top_k: int
) -> List[ToolSchema]:
    """Select tools based on context."""
    pass
```

### Docstrings

Use docstrings for all modules, classes, and functions:

```python
class SemanticRouter(IRouter):
    """Router for semantic tool selection.
    
    Uses embeddings to find relevant tools based on
    conversation context.
    """
    
    async def select_tools(
        self,
        context: str,
        top_k: int
    ) -> List[ToolSchema]:
        """Select tools based on context."""
        pass
```

## Version Management

### Semantic Versioning

UCP follows semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes, incompatible API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

**Examples:**
- `0.1.0` → `0.2.0` (Minor: New features)
- `0.2.0` → `0.2.1` (Patch: Bug fixes)
- `1.0.0` → `2.0.0` (Major: Breaking changes)

### Release Process

1. Update version numbers in `pyproject.toml` files
2. Update `__init__.py` files with version
3. Create git tag: `git tag -a v0.1.0`
4. Create release notes
5. Push to PyPI (for local) or deploy (for cloud)

## Documentation

### Where to Document

- **Code**: Docstrings in source code
- **API**: [`shared/docs/api_reference.md`](shared/docs/api_reference.md)
- **Architecture**: [`docs/`](docs/) folder
- **User Guides**: Version-specific guides in `local/docs/` and `cloud/docs/`

### Documentation Standards

- Clear and concise
- Include examples
- Explain "why" and "how"
- Keep up to date with code changes
- Use consistent terminology

## Common Issues and Solutions

### Import Errors

**Problem**: Cannot import from shared package

**Solution**:
```bash
# Make sure you're in the right directory
cd local  # or cd cloud
# Install in development mode
pip install -e "../shared"
```

### Type Checking Errors

**Problem**: mypy reports type errors

**Solution**:
```python
# Add type hints
from typing import List, Optional

# Use type ignore comments if needed
# type: ignore
```

### Test Failures

**Problem**: Tests fail locally but pass in CI

**Solution**:
```bash
# Check environment variables
echo $PYTHONPATH

# Run tests with verbose output
pytest tests/ -v -s

# Check for specific test
pytest tests/ -k "test_name"
```

### Performance Issues

**Problem**: UCP is slow

**Solutions:**
1. Reduce `top_k` in configuration
2. Use smaller embedding model
3. Enable caching (if available)
4. Profile code: `python -m cProfile`
5. Check database queries

## Debugging

### Local Development

```bash
# Enable debug logging
ucp serve --log-level DEBUG

# Run with debug dashboard
streamlit run local/src/ucp_mvp/dashboard.py

# Check logs
tail -f ~/.ucp/logs/ucp.log
```

### Cloud Development

```bash
# Enable debug logging
UCP_LOG_LEVEL=DEBUG ucp-cloud serve

# Check logs (cloud infrastructure)
kubectl logs -f deployment/ucp-cloud

# Use debug dashboard
streamlit run cloud/src/ucp_cloud/dashboard.py
```

## Deployment

### Local MVP

**Development:**
```bash
# Test locally
cd local
pytest tests/ -v

# Build package
python -m build
```

**Release:**
```bash
# Build PyPI package
cd local
python -m build
twine upload dist/*

# Build Docker image
docker build -t ucp-mvp .
docker tag ucp-mvp:latest
docker push ucp-mvp:latest
```

### Cloud Version

**Development:**
```bash
# Test locally
cd cloud
pytest tests/ -v

# Build package
python -m build
```

**Release:**
```bash
# Deploy to Kubernetes
cd infrastructure/kubernetes
kubectl apply -f .

# Or use Helm
helm upgrade ucp-cloud ./ucp-cloud
```

## Continuous Integration

### GitHub Actions

**Workflow:**
1. On push to main → Run tests
2. On pull request → Run tests
3. On merge → Deploy to staging
4. On release → Deploy to production

**Example Workflow File** (`.github/workflows/ci.yml`):
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest tests/ -v
```

## Best Practices

### 1. Write Tests First

Write tests before or alongside code:

```python
# tests/test_router.py
import pytest
from ucp_core.interfaces import IRouter

@pytest.mark.asyncio
async def test_select_tools_returns_list():
    """Test that select_tools returns a list."""
    router = MyRouter()
    tools = await router.select_tools("test", 5)
    assert isinstance(tools, list)
```

### 2. Keep Tests Simple

Avoid complex test setup:

```python
# Bad: Complex setup
@pytest.fixture
def complex_setup():
    # ... lots of setup code ...
    return router, session, tool_zoo

def test_with_complex_setup(complex_setup):
    # ... test uses complex setup ...
    pass

# Good: Simple setup
@pytest.mark.asyncio
async def test_select_tools_simple():
    """Test with simple setup."""
    router = MyRouter()
    tools = await router.select_tools("test", 5)
    assert len(tools) == 5
```

### 3. Test Edge Cases

Test error conditions and edge cases:

```python
@pytest.mark.asyncio
async def test_select_tools_with_empty_context():
    """Test with empty context."""
    router = MyRouter()
    tools = await router.select_tools("", 5)
    assert len(tools) == 5  # Should still return tools
```

### 4. Use Async Tests Properly

Use async test fixtures and await properly:

```python
@pytest.mark.asyncio
async def test_async_operations():
    """Test async operations correctly."""
    server = UCPServer(config)
    await server.initialize()
    tools = await server._list_tools()
    assert len(tools) > 0
```

## Getting Help

### Documentation

- [README.md](README.md) - Project overview
- [DOCUMENTATION_MAP.md](DOCUMENTATION_MAP.md) - Documentation navigation
- [shared/docs/api_reference.md](shared/docs/api_reference.md) - Shared API reference
- [local/docs/getting_started.md](local/docs/getting_started.md) - Local MVP guide
- [cloud/docs/roadmap.md](cloud/docs/roadmap.md) - Cloud roadmap

### Issues and Discussions

- **GitHub Issues**: Report bugs and feature requests
- **GitHub Discussions**: Ask questions and discuss ideas

### Code Review

- All pull requests require review
- At least one maintainer must approve
- Focus on code quality, not just functionality

## Resources

### Internal Documentation

- [Shared Components](shared/README.md) - Shared layer overview
- [Local MVP](local/README.md) - Local MVP documentation
- [Cloud Version](cloud/README.md) - Cloud version documentation
- [Repository Reorganization Plan](plans/repository_reorganization_plan.md) - Reorganization details

### External References

- [MCP Specification](https://modelcontextprotocol.io/) - MCP protocol
- [Gorilla Paper](https://arxiv.org/abs/2305.15334) - Tool selection research
- [RAFT Paper](https://arxiv.org/abs/2309.15217) - Fine-tuning research
- [LangGraph](https://github.com/langchain-ai/langgraph) - Workflow orchestration

## Summary

This guide provides comprehensive development guidelines for UCP's dual-track architecture:

- **Shared Components**: Foundation for both versions
- **Local MVP**: Privacy-focused, immediate value, open source
- **Cloud Version**: Scalable, multi-tenant, enterprise features

Key principles:
1. Maintain backward compatibility in shared components
2. Keep version-specific features separate
3. Write tests alongside code
4. Follow semantic versioning
5. Document all changes
6. Test thoroughly before committing

For specific questions or issues, please refer to the relevant documentation or open a GitHub issue.

---

*Last updated: 2026-01-10*

