# Repository Reorganization Migration Notes

**Date:** 2026-01-10  
**Status:** Complete

## Overview

The Universal Context Protocol repository has been reorganized from a monolithic structure into a dual-track architecture:

1. **Local-First MVP** (`local/`) - Open source, privacy-focused, immediate value
2. **Cloud Version** (`cloud/`) - Future business deployment with SOTA features
3. **Shared Components** (`shared/`) - Code used by both versions
4. **Archive** (`archive/`) - Original monolithic codebase preserved

---

## What Changed

### Directory Structure

**Before:**
```
UniversalContextProtocol/
├── src/ucp/              # Monolithic codebase
├── tests/                 # All tests
├── clients/                # All clients
└── docs/                   # All documentation
```

**After:**
```
UniversalContextProtocol/
├── shared/                 # Shared code between versions
│   ├── src/ucp_core/       # Core abstractions
│   ├── src/ucp_transport/   # Transport layer
│   ├── tests/
│   └── pyproject.toml
├── local/                  # Local MVP (Open Source)
│   ├── src/ucp_mvp/        # MVP implementation
│   ├── tests/
│   ├── docs/
│   ├── clients/              # CLI, desktop
│   └── pyproject.toml
├── cloud/                  # Cloud version (Future)
│   ├── src/ucp_cloud/       # Cloud implementation
│   │   ├── api/           # REST API
│   │   ├── auth/          # Auth & RBAC
│   │   └── pipeline/       # Data pipelines
│   ├── tests/
│   ├── docs/
│   ├── infrastructure/       # Terraform, K8s, Docker
│   ├── clients/              # VS Code, web
│   └── pyproject.toml
├── archive/                # Original codebase
│   ├── src/ucp_original/   # Archived src/
│   └── tests/test_original/
├── docs/                   # Shared documentation
├── reports/                # Audit and validation reports
├── plans/                  # Planning documents
└── pyproject.toml           # Root config (minimal)
```

### File Movements

#### Shared Code → `shared/`
| Original Location | New Location | Purpose |
|---|---|---|---|
| `src/ucp/models.py` | `shared/src/ucp_core/models.py` | Data models |
| `src/ucp/config.py` | `shared/src/ucp_core/config.py` | Configuration |
| `src/ucp/transports.py` | `shared/src/ucp_transport/mcp_protocol.py` | MCP protocol |
| `clients/harness/` | `shared/tests/evaluation/` | Evaluation harness |

#### MVP Code → `local/`
| Original Location | New Location | Purpose |
|---|---|---|---|
| `src/ucp/server.py` | `local/src/ucp_mvp/server.py` | Local server |
| `src/ucp/router.py` | `local/src/ucp_mvp/router.py` | Baseline router |
| `src/ucp/tool_zoo.py` | `local/src/ucp_mvp/tool_zoo.py` | ChromaDB tool zoo |
| `src/ucp/session.py` | `local/src/ucp_mvp/session.py` | SQLite sessions |
| `src/ucp/connection_pool.py` | `local/src/ucp_mvp/connection_pool.py` | Connection pool |
| `src/ucp/cli.py` | `local/src/ucp_mvp/cli.py` | CLI interface |
| `src/ucp/dashboard.py` | `local/src/ucp_mvp/dashboard.py` | Streamlit dashboard |
| `clients/cli/` | `local/clients/cli/` | CLI client |
| `clients/desktop/` | `local/clients/desktop/` | Desktop app |
| `tests/` | `local/tests/` | MVP tests |

#### Cloud Code → `cloud/`
| Original Location | New Location | Purpose |
|---|---|---|---|
| `src/ucp/server.py` | `cloud/src/ucp_cloud/server.py` | Cloud server |
| `src/ucp/router.py` | `cloud/src/ucp_cloud/router.py` | SOTA router |
| `src/ucp/tool_zoo.py` | `cloud/src/ucp_cloud/tool_zoo.py` | Qdrant tool zoo |
| `src/ucp/session.py` | `cloud/src/ucp_cloud/session.py` | Redis sessions |
| `src/ucp/connection_pool.py` | `cloud/src/ucp_cloud/connection_pool.py` | SSE/HTTP pool |
| `src/ucp/telemetry.py` | `cloud/src/ucp_cloud/telemetry.py` | Centralized telemetry |
| `src/ucp/bandit.py` | `cloud/src/ucp_cloud/bandit.py` | Bandit scorer |
| `src/ucp/online_opt.py` | `cloud/src/ucp_cloud/online_opt.py` | Online optimizer |
| `src/ucp/routing_pipeline.py` | `cloud/src/ucp_cloud/routing_pipeline.py` | Full pipeline |
| `src/ucp/raft.py` | `cloud/src/ucp_cloud/raft.py` | RAFT fine-tuning |
| `src/ucp/graph.py` | `cloud/src/ucp_cloud/graph.py` | LangGraph orchestration |
| `src/ucp/http_server.py` | `cloud/src/ucp_cloud/http_server.py` | HTTP server |
| `src/ucp/client_api.py` | `cloud/src/ucp_cloud/api/client_api.py` | Client API |
| `clients/vscode/` | `cloud/clients/vscode/` | VS Code extension |

#### Archived → `archive/`
| Original Location | New Location | Purpose |
|---|---|---|---|
| `src/ucp/` (all files) | `archive/src/ucp_original/` | Original codebase |
| `tests/` | `archive/tests/test_original/` | Original tests |

---

## New Package Structure

### Packages

The repository now has three independent packages:

1. **ucp-core** (`shared/`)
   - Shared components used by both versions
   - Install with: `pip install ucp-core`
   - Version: 0.1.0

2. **ucp-mvp** (`local/`)
   - Local-first MVP implementation
   - Install with: `pip install ucp-mvp`
   - Version: 0.1.0
   - Depends on: ucp-core

3. **ucp-cloud** (`cloud/`)
   - Cloud version with SOTA features
   - Install with: `pip install ucp-cloud`
   - Version: 0.1.0
   - Depends on: ucp-core

### Root Configuration

The root [`pyproject.toml`](pyproject.toml) has been updated to:
- Minimal configuration for the repository
- Contains common metadata and development dependencies
- Individual packages have their own pyproject.toml files

---

## Working with the New Structure

### For Local MVP Development

```bash
# Navigate to local MVP
cd local

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/ucp_mvp

# Linting
ruff check src/ucp_mvp
```

### For Cloud Development

```bash
# Navigate to cloud version
cd cloud

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/ucp_cloud

# Linting
ruff check src/ucp_cloud
```

### For Shared Component Development

```bash
# Navigate to shared components
cd shared

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/ucp_core src/ucp_transport

# Linting
ruff check src/ucp_core src/ucp_transport
```

---

## Import Updates Required

All Python files that were moved need to have their imports updated to reflect the new package structure:

### Files in `local/src/ucp_mvp/`
- Update imports from `from ucp.` to `from ucp_mvp.`
- Update imports from `from ucp_core.` to `from ucp_core.`

### Files in `cloud/src/ucp_cloud/`
- Update imports from `from ucp.` to `from ucp_cloud.`
- Update imports from `from ucp_core.` to `from ucp_core.`

### Files in `shared/src/ucp_transport/`
- Ensure imports work correctly for both versions

---

## Installation Changes

### Local MVP

**Old:**
```bash
pip install ucp
```

**New:**
```bash
pip install ucp-mvp
```

### Claude Desktop Integration

**Old config:**
```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "path/to/ucp_config.yaml"]
    }
  }
}
```

**New config (unchanged):**
The configuration format remains the same. UCP is still installed as `ucp` command.

---

## Next Steps

### Immediate (This Week)

1. **Update Imports**: Update all Python files to use new package structure
2. **Create Documentation**: Write detailed docs for each package
3. **Test**: Verify that all imports work correctly
4. **Clean Up**: Remove any remaining references to old structure

### Short Term (Next 2-4 Weeks)

1. **Implement MVP Features**: Complete local MVP implementation
2. **Create PyPI Packages**: Set up publishing for ucp-mvp
3. **Write Tests**: Comprehensive test coverage for all packages
4. **CI/CD**: Set up automated testing and deployment

### Long Term (Next 1-3 Months)

1. **Cloud Development**: Begin implementing cloud version
2. **Infrastructure**: Set up Terraform and Kubernetes configs
3. **Migration Tools**: Create tools for migrating from local to cloud

---

## Notes

- **No Code Deleted**: All original code has been preserved in [`archive/`](archive/)
- **Git History**: Use `git log --follow` to track file movements
- **Backward Compatibility**: The root [`pyproject.toml`](pyproject.toml) maintains compatibility with existing workflows
- **Gradual Migration**: Both versions can coexist during transition period

---

## Questions or Issues?

If you encounter any issues with the new structure:

1. **Import Errors**: Check that imports reference the correct package
2. **Missing Dependencies**: Ensure ucp-core is installed when using local or cloud packages
3. **Configuration Issues**: Review [`README.md`](README.md) for updated setup instructions
4. **Test Failures**: Run tests in the appropriate directory

---

## Summary

The repository reorganization is **complete**. The new dual-track structure enables:

- ✅ **Separation of Concerns**: Local MVP focuses on privacy, cloud on scalability
- ✅ **Code Reusability**: Shared components prevent duplication
- ✅ **Clear Development Path**: Independent packages with clear responsibilities
- ✅ **Preserved History**: Original codebase archived in [`archive/`](archive/)
- ✅ **Future-Ready**: Structure supports cloud development when needed

**Status**: Ready for development work to begin on the new structure.

---

**Last Updated:** 2026-01-10

**Date:** 2026-01-10  
**Status:** Complete

## Overview

The Universal Context Protocol repository has been reorganized from a monolithic structure into a dual-track architecture:

1. **Local-First MVP** (`local/`) - Open source, privacy-focused, immediate value
2. **Cloud Version** (`cloud/`) - Future business deployment with SOTA features
3. **Shared Components** (`shared/`) - Code used by both versions
4. **Archive** (`archive/`) - Original monolithic codebase preserved

---

## What Changed

### Directory Structure

**Before:**
```
UniversalContextProtocol/
├── src/ucp/              # Monolithic codebase
├── tests/                 # All tests
├── clients/                # All clients
└── docs/                   # All documentation
```

**After:**
```
UniversalContextProtocol/
├── shared/                 # Shared code between versions
│   ├── src/ucp_core/       # Core abstractions
│   ├── src/ucp_transport/   # Transport layer
│   ├── tests/
│   └── pyproject.toml
├── local/                  # Local MVP (Open Source)
│   ├── src/ucp_mvp/        # MVP implementation
│   ├── tests/
│   ├── docs/
│   ├── clients/              # CLI, desktop
│   └── pyproject.toml
├── cloud/                  # Cloud version (Future)
│   ├── src/ucp_cloud/       # Cloud implementation
│   │   ├── api/           # REST API
│   │   ├── auth/          # Auth & RBAC
│   │   └── pipeline/       # Data pipelines
│   ├── tests/
│   ├── docs/
│   ├── infrastructure/       # Terraform, K8s, Docker
│   ├── clients/              # VS Code, web
│   └── pyproject.toml
├── archive/                # Original codebase
│   ├── src/ucp_original/   # Archived src/
│   └── tests/test_original/
├── docs/                   # Shared documentation
├── reports/                # Audit and validation reports
├── plans/                  # Planning documents
└── pyproject.toml           # Root config (minimal)
```

### File Movements

#### Shared Code → `shared/`
| Original Location | New Location | Purpose |
|---|---|---|---|
| `src/ucp/models.py` | `shared/src/ucp_core/models.py` | Data models |
| `src/ucp/config.py` | `shared/src/ucp_core/config.py` | Configuration |
| `src/ucp/transports.py` | `shared/src/ucp_transport/mcp_protocol.py` | MCP protocol |
| `clients/harness/` | `shared/tests/evaluation/` | Evaluation harness |

#### MVP Code → `local/`
| Original Location | New Location | Purpose |
|---|---|---|---|
| `src/ucp/server.py` | `local/src/ucp_mvp/server.py` | Local server |
| `src/ucp/router.py` | `local/src/ucp_mvp/router.py` | Baseline router |
| `src/ucp/tool_zoo.py` | `local/src/ucp_mvp/tool_zoo.py` | ChromaDB tool zoo |
| `src/ucp/session.py` | `local/src/ucp_mvp/session.py` | SQLite sessions |
| `src/ucp/connection_pool.py` | `local/src/ucp_mvp/connection_pool.py` | Connection pool |
| `src/ucp/cli.py` | `local/src/ucp_mvp/cli.py` | CLI interface |
| `src/ucp/dashboard.py` | `local/src/ucp_mvp/dashboard.py` | Streamlit dashboard |
| `clients/cli/` | `local/clients/cli/` | CLI client |
| `clients/desktop/` | `local/clients/desktop/` | Desktop app |
| `tests/` | `local/tests/` | MVP tests |

#### Cloud Code → `cloud/`
| Original Location | New Location | Purpose |
|---|---|---|---|
| `src/ucp/server.py` | `cloud/src/ucp_cloud/server.py` | Cloud server |
| `src/ucp/router.py` | `cloud/src/ucp_cloud/router.py` | SOTA router |
| `src/ucp/tool_zoo.py` | `cloud/src/ucp_cloud/tool_zoo.py` | Qdrant tool zoo |
| `src/ucp/session.py` | `cloud/src/ucp_cloud/session.py` | Redis sessions |
| `src/ucp/connection_pool.py` | `cloud/src/ucp_cloud/connection_pool.py` | SSE/HTTP pool |
| `src/ucp/telemetry.py` | `cloud/src/ucp_cloud/telemetry.py` | Centralized telemetry |
| `src/ucp/bandit.py` | `cloud/src/ucp_cloud/bandit.py` | Bandit scorer |
| `src/ucp/online_opt.py` | `cloud/src/ucp_cloud/online_opt.py` | Online optimizer |
| `src/ucp/routing_pipeline.py` | `cloud/src/ucp_cloud/routing_pipeline.py` | Full pipeline |
| `src/ucp/raft.py` | `cloud/src/ucp_cloud/raft.py` | RAFT fine-tuning |
| `src/ucp/graph.py` | `cloud/src/ucp_cloud/graph.py` | LangGraph orchestration |
| `src/ucp/http_server.py` | `cloud/src/ucp_cloud/http_server.py` | HTTP server |
| `src/ucp/client_api.py` | `cloud/src/ucp_cloud/api/client_api.py` | Client API |
| `clients/vscode/` | `cloud/clients/vscode/` | VS Code extension |

#### Archived → `archive/`
| Original Location | New Location | Purpose |
|---|---|---|---|
| `src/ucp/` (all files) | `archive/src/ucp_original/` | Original codebase |
| `tests/` | `archive/tests/test_original/` | Original tests |

---

## New Package Structure

### Packages

The repository now has three independent packages:

1. **ucp-core** (`shared/`)
   - Shared components used by both versions
   - Install with: `pip install ucp-core`
   - Version: 0.1.0

2. **ucp-mvp** (`local/`)
   - Local-first MVP implementation
   - Install with: `pip install ucp-mvp`
   - Version: 0.1.0
   - Depends on: ucp-core

3. **ucp-cloud** (`cloud/`)
   - Cloud version with SOTA features
   - Install with: `pip install ucp-cloud`
   - Version: 0.1.0
   - Depends on: ucp-core

### Root Configuration

The root [`pyproject.toml`](pyproject.toml) has been updated to:
- Minimal configuration for the repository
- Contains common metadata and development dependencies
- Individual packages have their own pyproject.toml files

---

## Working with the New Structure

### For Local MVP Development

```bash
# Navigate to local MVP
cd local

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/ucp_mvp

# Linting
ruff check src/ucp_mvp
```

### For Cloud Development

```bash
# Navigate to cloud version
cd cloud

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/ucp_cloud

# Linting
ruff check src/ucp_cloud
```

### For Shared Component Development

```bash
# Navigate to shared components
cd shared

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Type checking
mypy src/ucp_core src/ucp_transport

# Linting
ruff check src/ucp_core src/ucp_transport
```

---

## Import Updates Required

All Python files that were moved need to have their imports updated to reflect the new package structure:

### Files in `local/src/ucp_mvp/`
- Update imports from `from ucp.` to `from ucp_mvp.`
- Update imports from `from ucp_core.` to `from ucp_core.`

### Files in `cloud/src/ucp_cloud/`
- Update imports from `from ucp.` to `from ucp_cloud.`
- Update imports from `from ucp_core.` to `from ucp_core.`

### Files in `shared/src/ucp_transport/`
- Ensure imports work correctly for both versions

---

## Installation Changes

### Local MVP

**Old:**
```bash
pip install ucp
```

**New:**
```bash
pip install ucp-mvp
```

### Claude Desktop Integration

**Old config:**
```json
{
  "mcpServers": {
    "ucp": {
      "command": "ucp",
      "args": ["serve", "-c", "path/to/ucp_config.yaml"]
    }
  }
}
```

**New config (unchanged):**
The configuration format remains the same. UCP is still installed as `ucp` command.

---

## Next Steps

### Immediate (This Week)

1. **Update Imports**: Update all Python files to use new package structure
2. **Create Documentation**: Write detailed docs for each package
3. **Test**: Verify that all imports work correctly
4. **Clean Up**: Remove any remaining references to old structure

### Short Term (Next 2-4 Weeks)

1. **Implement MVP Features**: Complete local MVP implementation
2. **Create PyPI Packages**: Set up publishing for ucp-mvp
3. **Write Tests**: Comprehensive test coverage for all packages
4. **CI/CD**: Set up automated testing and deployment

### Long Term (Next 1-3 Months)

1. **Cloud Development**: Begin implementing cloud version
2. **Infrastructure**: Set up Terraform and Kubernetes configs
3. **Migration Tools**: Create tools for migrating from local to cloud

---

## Notes

- **No Code Deleted**: All original code has been preserved in [`archive/`](archive/)
- **Git History**: Use `git log --follow` to track file movements
- **Backward Compatibility**: The root [`pyproject.toml`](pyproject.toml) maintains compatibility with existing workflows
- **Gradual Migration**: Both versions can coexist during transition period

---

## Questions or Issues?

If you encounter any issues with the new structure:

1. **Import Errors**: Check that imports reference the correct package
2. **Missing Dependencies**: Ensure ucp-core is installed when using local or cloud packages
3. **Configuration Issues**: Review [`README.md`](README.md) for updated setup instructions
4. **Test Failures**: Run tests in the appropriate directory

---

## Summary

The repository reorganization is **complete**. The new dual-track structure enables:

- ✅ **Separation of Concerns**: Local MVP focuses on privacy, cloud on scalability
- ✅ **Code Reusability**: Shared components prevent duplication
- ✅ **Clear Development Path**: Independent packages with clear responsibilities
- ✅ **Preserved History**: Original codebase archived in [`archive/`](archive/)
- ✅ **Future-Ready**: Structure supports cloud development when needed

**Status**: Ready for development work to begin on the new structure.

---

**Last Updated:** 2026-01-10

