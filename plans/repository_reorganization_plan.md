# Universal Context Protocol - Repository Reorganization Plan

**Date:** 2026-01-10  
**Status:** Planning Phase  
**Objective:** Split UCP into local-first MVP and future cloud business version

---

## Executive Summary

The Universal Context Protocol (UCP) project will be reorganized into a dual-track architecture:

1. **Local-First MVP** - Open-source, user-controlled proxy running locally with immediate value
2. **Cloud Version** - Future business deployment with centralized analytics, SaaS model, and enterprise features

This reorganization enables rapid MVP delivery while preserving sophisticated infrastructure for future cloud deployment.

---

## 1. New Repository Structure

### Top-Level Structure

```
UniversalContextProtocol/
├── README.md                          # Updated for dual-track approach
├── LICENSE                            # MIT license
├── .gitignore
├── pyproject.toml                     # Root project config (shared)
├── ucp_config.example.yaml             # Shared config template
│
├── shared/                            # SHARED CODE BETWEEN VERSIONS
│   ├── src/
│   │   ├── ucp_core/                 # Core abstractions and interfaces
│   │   │   ├── __init__.py
│   │   │   ├── models.py             # Shared data models
│   │   │   ├── config.py             # Shared configuration
│   │   │   ├── exceptions.py         # Shared exceptions
│   │   │   └── interfaces.py        # Abstract interfaces
│   │   └── ucp_transport/           # Transport layer abstractions
│   │       ├── __init__.py
│   │       ├── mcp_protocol.py       # MCP protocol implementation
│   │       └── base_transport.py     # Base transport class
│   ├── tests/
│   │   └── test_shared/
│   └── pyproject.toml              # Shared package config
│
├── local/                             # LOCAL-FIRST MVP (Open Source)
│   ├── README.md                     # MVP-specific documentation
│   ├── pyproject.toml               # MVP package config
│   ├── src/
│   │   └── ucp_mvp/
│   │       ├── __init__.py
│   │       ├── server.py             # Local MCP server
│   │       ├── router.py             # Simplified router (baseline + adaptive)
│   │       ├── tool_zoo.py          # Local vector store (ChromaDB)
│   │       ├── session.py            # Local session manager (SQLite)
│   │       ├── connection_pool.py     # Connection pool for downstream servers
│   │       ├── cli.py               # MVP CLI interface
│   │       └── dashboard.py          # Simple Streamlit dashboard
│   ├── tests/
│   │   └── test_mvp/
│   ├── docs/
│   │   ├── mvp_architecture.md
│   │   ├── mvp_user_guide.md
│   │   └── mvp_deployment.md
│   └── clients/
│       ├── cli/                     # CLI client (60% complete)
│       └── desktop/                # Desktop app (30% complete)
│
├── cloud/                            # CLOUD VERSION (Future Business)
│   ├── README.md                     # Cloud-specific documentation
│   ├── pyproject.toml               # Cloud package config
│   ├── src/
│   │   └── ucp_cloud/
│   │       ├── __init__.py
│   │       ├── server.py             # Cloud MCP server
│   │       ├── router.py             # Full SOTA router with all features
│   │       ├── tool_zoo.py          # Cloud vector store (Qdrant/Weaviate)
│   │       ├── session.py            # Cloud session manager (Redis)
│   │       ├── connection_pool.py     # Connection pool with SSE support
│   │       ├── telemetry.py          # Centralized telemetry
│   │       ├── bandit.py            # Shared bandit scorer
│   │       ├── online_opt.py         # Online optimization
│   │       ├── routing_pipeline.py   # Full SOTA pipeline
│   │       ├── raft.py              # RAFT fine-tuning
│   │       ├── graph.py             # LangGraph integration
│   │       ├── api/                # REST API for cloud services
│   │       │   ├── __init__.py
│   │       │   ├── analytics.py
│   │       │   ├── billing.py
│   │       │   └── admin.py
│   │       ├── auth/               # Authentication & authorization
│   │       │   ├── __init__.py
│   │       │   ├── sso.py
│   │       │   └── rbac.py
│   │       └── pipeline/            # Data pipelines
│   │           ├── __init__.py
│   │           ├── training.py
│   │           └── analytics.py
│   ├── tests/
│   │   └── test_cloud/
│   ├── docs/
│   │   ├── cloud_architecture.md
│   │   ├── cloud_deployment.md
│   │   └── cloud_api_reference.md
│   ├── infrastructure/               # Cloud infrastructure (Terraform/Helm)
│   │   ├── terraform/
│   │   ├── kubernetes/
│   │   └── docker/
│   └── clients/
│       ├── vscode/                  # VS Code extension (40% complete)
│       └── web/                    # Future web client
│
├── docs/                             # SHARED DOCUMENTATION
│   ├── index.md                     # Documentation index
│   ├── getting_started.md
│   ├── debugging_playbook.md
│   ├── evaluation_harness.md
│   ├── research/                    # Research papers and synthesis
│   │   ├── synthesis_agent_design.md
│   │   ├── synthesis_context_management.md
│   │   ├── synthesis_feedback_eval.md
│   │   └── synthesis_tool_selection.md
│   └── archive/                    # Archived documentation
│
├── reports/                          # AUDIT AND VALIDATION REPORTS
│   ├── codebase_audit_report.md
│   ├── corpus_integrity_report.md
│   ├── roadmap_edge.md
│   └── validation_report.json
│
├── plans/                            # PLANNING DOCUMENTS
│   ├── repository_reorganization_plan.md  # This document
│   ├── mvp_implementation_roadmap.md
│   ├── cloud_implementation_roadmap.md
│   └── migration_checklist.md
│
└── archive/                           # ARCHIVED CODE (Not needed for MVP)
    ├── src/
    │   └── ucp_original/            # Original monolithic codebase
    └── tests/
        └── test_original/
```

---

## 2. Scope Definitions

### 2.1 Local-First MVP Scope

**Core Philosophy:** Privacy-first, user-controlled, immediate value, minimal dependencies

#### Core Features (MVP v1.0)

**MCP Proxy Functionality:**
- ✅ Stdio transport for Claude Desktop
- ✅ Basic tool discovery and indexing
- ✅ Context-aware tool selection (baseline router)
- ✅ Tool call routing to downstream servers
- ✅ Session persistence (SQLite)
- ✅ Connection pooling

**Routing Capabilities:**
- ✅ Semantic search (sentence-transformers)
- ✅ Keyword search
- ✅ Hybrid search (semantic + keyword)
- ✅ Domain detection
- ✅ Adaptive router with co-occurrence tracking
- ❌ Cross-encoder reranking (deferred to v1.1)
- ❌ Bandit learning (deferred to v1.1)
- ❌ Online optimization (deferred to v1.1)

**Data Storage:**
- ✅ SQLite for sessions
- ✅ ChromaDB for tool embeddings
- ✅ Local file system for configuration
- ❌ No cloud sync
- ❌ No centralized analytics

**User Interface:**
- ✅ CLI interface (ucp serve, ucp index, ucp search)
- ✅ Simple Streamlit dashboard (basic metrics)
- ❌ No web UI (deferred)
- ❌ No mobile app (deferred)

**Analytics:**
- ✅ Local metrics (success rate, latency, tool usage)
- ✅ Session history viewing
- ✅ Basic statistics dashboard
- ❌ No centralized analytics
- ❌ No cross-user learning

**Installation & Distribution:**
- ✅ PyPI package
- ✅ Docker image
- ✅ pip install ucp-mvp
- ✅ One-line setup for Claude Desktop
- ✅ Configuration wizard

**Testing & Quality:**
- ✅ Unit tests for core functionality
- ✅ Integration tests with real MCP servers
- ✅ Evaluation harness for routing quality
- ✅ Documentation (user guide, API reference)

#### MVP v1.1 (Enhanced Routing)
- Cross-encoder reranking
- Bandit-based exploration
- Per-tool bias learning
- Advanced dashboard with routing visualization

#### MVP v1.2 (Performance)
- GPU acceleration for embeddings
- Caching layer
- Performance optimizations
- Better error handling

#### Out of Scope for MVP
- ❌ Cloud infrastructure
- ❌ Multi-tenant architecture
- ❌ SaaS features (billing, accounts)
- ❌ Enterprise features (SSO, RBAC)
- ❌ RAFT fine-tuning pipeline
- ❌ Centralized analytics
- ❌ Model training pipeline
- ❌ SSE/HTTP downstream transports
- ❌ LangGraph orchestration

---

### 2.2 Cloud Version Scope

**Core Philosophy:** Scalable, multi-tenant, feature-rich, business-oriented

#### Additional Features Beyond MVP

**Infrastructure:**
- ✅ Multi-tenant architecture
- ✅ Horizontal scaling (Kubernetes)
- ✅ Load balancing
- ✅ High availability (HA)
- ✅ Disaster recovery
- ✅ Global CDN for static assets

**Advanced Routing:**
- ✅ Full SOTA routing pipeline
- ✅ Cross-encoder reranking
- ✅ Bandit-based exploration
- ✅ Online optimization
- ✅ RAFT fine-tuning
- ✅ LangGraph orchestration
- ✅ Ensemble routing strategies

**Data Storage:**
- ✅ Redis for session management
- ✅ Qdrant/Weaviate for vector store
- ✅ PostgreSQL for relational data
- ✅ S3/GCS for data lake
- ✅ TimescaleDB for analytics

**SaaS Features:**
- ✅ User authentication (OAuth, SSO)
- ✅ Role-based access control (RBAC)
- ✅ Multi-tenant isolation
- ✅ Billing and subscription management
- ✅ Usage-based pricing
- ✅ API keys and rate limiting
- ✅ Audit logging

**Centralized Analytics:**
- ✅ Cross-user routing analytics
- ✅ A/B testing framework
- ✅ Model training pipeline
- ✅ Continuous evaluation
- ✅ Performance monitoring
- ✅ Alerting and observability
- ✅ Business intelligence dashboards

**Enterprise Features:**
- ✅ SSO (SAML, OIDC)
- ✅ SCIM provisioning
- ✅ Advanced RBAC
- ✅ Data residency options
- ✅ Compliance reporting
- ✅ Custom SLAs
- ✅ Dedicated support

**Developer Experience:**
- ✅ REST API
- ✅ GraphQL API
- ✅ Webhooks
- ✅ SDKs (Python, JavaScript)
- ✅ API documentation (OpenAPI)
- ✅ Sandbox environment
- ✅ Developer portal

**Clients:**
- ✅ VS Code extension (enhanced)
- ✅ Web application
- ✅ Mobile apps (iOS, Android)
- ✅ Browser extension

---

## 3. Code Sharing Strategy

### 3.1 Shared Components

The `shared/` directory contains code used by both local and cloud versions:

**Core Abstractions (`shared/src/ucp_core/`):**
- [`models.py`](shared/src/ucp_core/models.py) - Data models (ToolSchema, SessionState, RoutingDecision, etc.)
- [`config.py`](shared/src/ucp_core/config.py) - Configuration base classes and validation
- [`exceptions.py`](shared/src/ucp_core/exceptions.py) - Custom exceptions
- [`interfaces.py`](shared/src/ucp_core/interfaces.py) - Abstract interfaces (Router, ToolZoo, SessionManager)

**Transport Layer (`shared/src/ucp_transport/`):**
- [`mcp_protocol.py`](shared/src/ucp_transport/mcp_protocol.py) - MCP protocol implementation
- [`base_transport.py`](shared/src/ucp_transport/base_transport.py) - Base transport class

### 3.2 Version-Specific Implementations

**Local MVP (`local/src/ucp_mvp/`):**
- Uses simplified implementations
- Local storage only (SQLite, ChromaDB)
- Basic routing (baseline + adaptive)
- No external dependencies beyond core

**Cloud Version (`cloud/src/ucp_cloud/`):**
- Uses full SOTA implementations
- Cloud storage (Redis, Qdrant, PostgreSQL)
- Advanced routing with all features
- Additional services (auth, billing, analytics)

### 3.3 Dependency Management

**Shared Package (`shared/pyproject.toml`):**
```toml
[project]
name = "ucp-core"
version = "0.1.0"
dependencies = [
    "mcp>=1.25.0",
    "pydantic>=2.5.0",
    "pyyaml>=6.0",
]
```

**Local MVP (`local/pyproject.toml`):**
```toml
[project]
name = "ucp-mvp"
version = "0.1.0"
dependencies = [
    "ucp-core>=0.1.0",
    "mcp>=1.25.0",
    "chromadb>=0.4.22",
    "sentence-transformers>=2.2.0",
    "structlog>=24.1.0",
    "streamlit>=1.28.0",
]
```

**Cloud Version (`cloud/pyproject.toml`):**
```toml
[project]
name = "ucp-cloud"
version = "0.1.0"
dependencies = [
    "ucp-core>=0.1.0",
    "mcp>=1.25.0",
    "qdrant-client>=1.6.0",
    "redis>=5.0.0",
    "psycopg2-binary>=2.9.0",
    "fastapi>=0.109.0",
    "langgraph>=0.0.40",
    "sentence-transformers>=2.2.0",
    "structlog>=24.1.0",
    "prometheus-client>=0.19.0",
]
```

---

## 4. Migration Strategy

### 4.1 Phase 1: Repository Restructuring (Week 1-2)

**Step 1: Create new directory structure**
```bash
mkdir -p shared/src/ucp_core shared/src/ucp_transport shared/tests
mkdir -p local/src/ucp_mvp local/tests local/docs local/clients
mkdir -p cloud/src/ucp_cloud cloud/tests cloud/docs cloud/infrastructure
mkdir -p archive
```

**Step 2: Extract shared code**
- Move [`models.py`](src/ucp/models.py) → [`shared/src/ucp_core/models.py`](shared/src/ucp_core/models.py)
- Move [`config.py`](src/ucp/config.py) → [`shared/src/ucp_core/config.py`](shared/src/ucp_core/config.py)
- Extract interfaces from existing code → [`shared/src/ucp_core/interfaces.py`](shared/src/ucp_core/interfaces.py)
- Create base transport class → [`shared/src/ucp_transport/base_transport.py`](shared/src/ucp_transport/base_transport.py)

**Step 3: Archive original codebase**
```bash
mv src archive/src/ucp_original
mv tests archive/tests/test_original
```

**Step 4: Create MVP implementations**
- Copy simplified versions to [`local/src/ucp_mvp/`](local/src/ucp_mvp/)
- Implement baseline router (remove SOTA features)
- Implement local storage backends (SQLite, ChromaDB)
- Create MVP CLI interface

**Step 5: Create cloud implementations**
- Copy full versions to [`cloud/src/ucp_cloud/`](cloud/src/ucp_cloud/)
- Keep all SOTA features (bandit, online_opt, routing_pipeline)
- Implement cloud storage backends (Redis, Qdrant)
- Create REST API layer

### 4.2 Phase 2: MVP Implementation (Week 3-8)

**Week 3-4: Core Functionality**
- Implement MVP server with stdio transport
- Implement baseline router with hybrid search
- Implement local tool zoo (ChromaDB)
- Implement session manager (SQLite)
- Basic CLI commands (serve, index, search)

**Week 5-6: Testing & Integration**
- Unit tests for all components
- Integration tests with real MCP servers
- Evaluation harness validation
- Fix bugs and stabilize

**Week 7-8: Polish & Documentation**
- Streamlit dashboard
- User guide and API reference
- PyPI packaging
- Docker image
- Beta testing

### 4.3 Phase 3: Cloud Development (Week 9-16+)

**Week 9-12: Infrastructure**
- Set up cloud infrastructure (Terraform, Kubernetes)
- Implement cloud storage backends
- Implement authentication and authorization
- Set up monitoring and observability

**Week 13-16: Advanced Features**
- Implement full SOTA routing pipeline
- Implement RAFT fine-tuning pipeline
- Implement centralized analytics
- Implement SaaS features (billing, multi-tenant)

**Week 17+: Production & Scaling**
- Performance optimization
- Security hardening
- Load testing
- Production deployment

---

## 5. File Mapping

### 5.1 Current → New Structure

| Current File | New Location | Notes |
|--------------|--------------|-------|
| [`src/ucp/models.py`](src/ucp/models.py) | [`shared/src/ucp_core/models.py`](shared/src/ucp_core/models.py) | Shared data models |
| [`src/ucp/config.py`](src/ucp/config.py) | [`shared/src/ucp_core/config.py`](shared/src/ucp_core/config.py) | Shared configuration |
| [`src/ucp/server.py`](src/ucp/server.py) | [`local/src/ucp_mvp/server.py`](local/src/ucp_mvp/server.py) | Simplified for MVP |
| [`src/ucp/server.py`](src/ucp/server.py) | [`cloud/src/ucp_cloud/server.py`](cloud/src/ucp_cloud/server.py) | Full version |
| [`src/ucp/router.py`](src/ucp/router.py) | [`local/src/ucp_mvp/router.py`](local/src/ucp_mvp/router.py) | Baseline + Adaptive only |
| [`src/ucp/router.py`](src/ucp/router.py) | [`cloud/src/ucp_cloud/router.py`](cloud/src/ucp_cloud/router.py) | Full SOTA router |
| [`src/ucp/tool_zoo.py`](src/ucp/tool_zoo.py) | [`local/src/ucp_mvp/tool_zoo.py`](local/src/ucp_mvp/tool_zoo.py) | ChromaDB only |
| [`src/ucp/tool_zoo.py`](src/ucp/tool_zoo.py) | [`cloud/src/ucp_cloud/tool_zoo.py`](cloud/src/ucp_cloud/tool_zoo.py) | Qdrant + advanced features |
| [`src/ucp/session.py`](src/ucp/session.py) | [`local/src/ucp_mvp/session.py`](local/src/ucp_mvp/session.py) | SQLite only |
| [`src/ucp/session.py`](src/ucp/session.py) | [`cloud/src/ucp_cloud/session.py`](cloud/src/ucp_cloud/session.py) | Redis + advanced features |
| [`src/ucp/connection_pool.py`](src/ucp/connection_pool.py) | [`local/src/ucp_mvp/connection_pool.py`](local/src/ucp_mvp/connection_pool.py) | Stdio only |
| [`src/ucp/connection_pool.py`](src/ucp/connection_pool.py) | [`cloud/src/ucp_cloud/connection_pool.py`](cloud/src/ucp_cloud/connection_pool.py) | Stdio + SSE/HTTP |
| [`src/ucp/cli.py`](src/ucp/cli.py) | [`local/src/ucp_mvp/cli.py`](local/src/ucp_mvp/cli.py) | MVP CLI |
| [`src/ucp/dashboard.py`](src/ucp/dashboard.py) | [`local/src/ucp_mvp/dashboard.py`](local/src/ucp_mvp/dashboard.py) | Simple dashboard |
| [`src/ucp/telemetry.py`](src/ucp/telemetry.py) | [`cloud/src/ucp_cloud/telemetry.py`](cloud/src/ucp_cloud/telemetry.py) | Cloud only |
| [`src/ucp/bandit.py`](src/ucp/bandit.py) | [`cloud/src/ucp_cloud/bandit.py`](cloud/src/ucp_cloud/bandit.py) | Cloud only |
| [`src/ucp/online_opt.py`](src/ucp/online_opt.py) | [`cloud/src/ucp_cloud/online_opt.py`](cloud/src/ucp_cloud/online_opt.py) | Cloud only |
| [`src/ucp/routing_pipeline.py`](src/ucp/routing_pipeline.py) | [`cloud/src/ucp_cloud/routing_pipeline.py`](cloud/src/ucp_cloud/routing_pipeline.py) | Cloud only |
| [`src/ucp/raft.py`](src/ucp/raft.py) | [`cloud/src/ucp_cloud/raft.py`](cloud/src/ucp_cloud/raft.py) | Cloud only |
| [`src/ucp/graph.py`](src/ucp/graph.py) | [`cloud/src/ucp_cloud/graph.py`](cloud/src/ucp_cloud/graph.py) | Cloud only |
| [`src/ucp/http_server.py`](src/ucp/http_server.py) | [`cloud/src/ucp_cloud/http_server.py`](cloud/src/ucp_cloud/http_server.py) | Cloud only |
| [`src/ucp/client_api.py`](src/ucp/client_api.py) | [`cloud/src/ucp_cloud/api/client_api.py`](cloud/src/ucp_cloud/api/client_api.py) | Cloud only |
| [`src/ucp/transports.py`](src/ucp/transports.py) | [`shared/src/ucp_transport/mcp_protocol.py`](shared/src/ucp_transport/mcp_protocol.py) | Shared transport |
| [`clients/cli/`](clients/cli/) | [`local/clients/cli/`](local/clients/cli/) | MVP CLI client |
| [`clients/desktop/`](clients/desktop/) | [`local/clients/desktop/`](local/clients/desktop/) | MVP desktop app |
| [`clients/vscode/`](clients/vscode/) | [`cloud/clients/vscode/`](cloud/clients/vscode/) | Cloud VS Code extension |
| [`clients/harness/`](clients/harness/) | [`shared/tests/evaluation/`](shared/tests/evaluation/) | Shared evaluation |
| [`README.md`](README.md) | [`README.md`](README.md) | Updated for dual-track |
| [`pyproject.toml`](pyproject.toml) | [`pyproject.toml`](pyproject.toml) | Root config |
| [`docs/`](docs/) | [`docs/`](docs/) | Shared docs |

### 5.2 New Files to Create

**Shared:**
- [`shared/src/ucp_core/__init__.py`](shared/src/ucp_core/__init__.py)
- [`shared/src/ucp_core/exceptions.py`](shared/src/ucp_core/exceptions.py)
- [`shared/src/ucp_core/interfaces.py`](shared/src/ucp_core/interfaces.py)
- [`shared/src/ucp_transport/__init__.py`](shared/src/ucp_transport/__init__.py)
- [`shared/src/ucp_transport/base_transport.py`](shared/src/ucp_transport/base_transport.py)
- [`shared/pyproject.toml`](shared/pyproject.toml)

**Local MVP:**
- [`local/README.md`](local/README.md)
- [`local/pyproject.toml`](local/pyproject.toml)
- [`local/src/ucp_mvp/__init__.py`](local/src/ucp_mvp/__init__.py)
- [`local/docs/mvp_architecture.md`](local/docs/mvp_architecture.md)
- [`local/docs/mvp_user_guide.md`](local/docs/mvp_user_guide.md)
- [`local/docs/mvp_deployment.md`](local/docs/mvp_deployment.md)

**Cloud:**
- [`cloud/README.md`](cloud/README.md)
- [`cloud/pyproject.toml`](cloud/pyproject.toml)
- [`cloud/src/ucp_cloud/__init__.py`](cloud/src/ucp_cloud/__init__.py)
- [`cloud/src/ucp_cloud/api/__init__.py`](cloud/src/ucp_cloud/api/__init__.py)
- [`cloud/src/ucp_cloud/api/analytics.py`](cloud/src/ucp_cloud/api/analytics.py)
- [`cloud/src/ucp_cloud/api/billing.py`](cloud/src/ucp_cloud/api/billing.py)
- [`cloud/src/ucp_cloud/api/admin.py`](cloud/src/ucp_cloud/api/admin.py)
- [`cloud/src/ucp_cloud/auth/__init__.py`](cloud/src/ucp_cloud/auth/__init__.py)
- [`cloud/src/ucp_cloud/auth/sso.py`](cloud/src/ucp_cloud/auth/sso.py)
- [`cloud/src/ucp_cloud/auth/rbac.py`](cloud/src/ucp_cloud/auth/rbac.py)
- [`cloud/src/ucp_cloud/pipeline/__init__.py`](cloud/src/ucp_cloud/pipeline/__init__.py)
- [`cloud/src/ucp_cloud/pipeline/training.py`](cloud/src/ucp_cloud/pipeline/training.py)
- [`cloud/src/ucp_cloud/pipeline/analytics.py`](cloud/src/ucp_cloud/pipeline/analytics.py)
- [`cloud/docs/cloud_architecture.md`](cloud/docs/cloud_architecture.md)
- [`cloud/docs/cloud_deployment.md`](cloud/docs/cloud_deployment.md)
- [`cloud/docs/cloud_api_reference.md`](cloud/docs/cloud_api_reference.md)

**Planning:**
- [`plans/mvp_implementation_roadmap.md`](plans/mvp_implementation_roadmap.md)
- [`plans/cloud_implementation_roadmap.md`](plans/cloud_implementation_roadmap.md)
- [`plans/migration_checklist.md`](plans/migration_checklist.md)

---

## 6. Implementation Roadmap

### 6.1 MVP Implementation Roadmap

#### Phase 1: Repository Reorganization (Week 1-2)

**Week 1: Structure & Shared Code**
- [ ] Create new directory structure
- [ ] Extract shared code to [`shared/`](shared/)
- [ ] Define interfaces in [`interfaces.py`](shared/src/ucp_core/interfaces.py)
- [ ] Archive original codebase
- [ ] Update root [`README.md`](README.md)

**Week 2: MVP Foundation**
- [ ] Create MVP package structure
- [ ] Implement simplified server
- [ ] Implement baseline router
- [ ] Implement local tool zoo (ChromaDB)
- [ ] Implement session manager (SQLite)

#### Phase 2: Core Functionality (Week 3-6)

**Week 3: Routing & Storage**
- [ ] Implement hybrid search (semantic + keyword)
- [ ] Implement domain detection
- [ ] Implement adaptive router with co-occurrence
- [ ] Implement connection pooling
- [ ] Implement stdio transport

**Week 4: CLI & Dashboard**
- [ ] Implement CLI commands (serve, index, search, status)
- [ ] Implement configuration wizard
- [ ] Implement basic Streamlit dashboard
- [ ] Add metrics visualization

**Week 5: Testing**
- [ ] Write unit tests for all components
- [ ] Write integration tests with real MCP servers
- [ ] Set up evaluation harness
- [ ] Run validation suite

**Week 6: Bug Fixes & Stabilization**
- [ ] Fix identified issues
- [ ] Improve error handling
- [ ] Add logging and debugging
- [ ] Performance profiling

#### Phase 3: Polish & Release (Week 7-8)

**Week 7: Documentation**
- [ ] Write MVP architecture doc
- [ ] Write user guide
- [ ] Write API reference
- [ ] Create quick start tutorial

**Week 8: Packaging & Release**
- [ ] PyPI packaging
- [ ] Docker image
- [ ] Beta testing
- [ ] v1.0 release

#### Phase 4: Enhanced Features (Week 9-12)

**Week 9-10: Advanced Routing**
- [ ] Implement cross-encoder reranking
- [ ] Implement bandit exploration
- [ ] Implement per-tool bias learning
- [ ] Add routing visualization

**Week 11-12: Performance**
- [ ] GPU acceleration for embeddings
- [ ] Implement caching layer
- [ ] Optimize database queries
- [ ] Performance testing

---

### 6.2 Cloud Implementation Roadmap

#### Phase 1: Infrastructure Setup (Week 1-4)

**Week 1: Cloud Foundation**
- [ ] Set up cloud infrastructure (AWS/GCP)
- [ ] Configure Kubernetes cluster
- [ ] Set up CI/CD pipeline
- [ ] Configure monitoring stack

**Week 2: Storage Backends**
- [ ] Implement Redis session manager
- [ ] Implement Qdrant vector store
- [ ] Implement PostgreSQL integration
- [ ] Set up S3/GCS data lake

**Week 3: Authentication & Authorization**
- [ ] Implement OAuth2/OIDC
- [ ] Implement SSO (SAML)
- [ ] Implement RBAC
- [ ] Set up SCIM provisioning

**Week 4: API Layer**
- [ ] Implement REST API
- [ ] Implement GraphQL API
- [ ] Set up API gateway
- [ ] Configure rate limiting

#### Phase 2: Advanced Features (Week 5-12)

**Week 5-6: SOTA Routing**
- [ ] Port full SOTA routing pipeline
- [ ] Implement cross-encoder reranking
- [ ] Implement bandit scorer
- [ ] Implement online optimization

**Week 7-8: Analytics & Training**
- [ ] Implement centralized telemetry
- [ ] Set up analytics pipeline
- [ ] Implement RAFT fine-tuning
- [ ] Set up model training pipeline

**Week 9-10: SaaS Features**
- [ ] Implement billing system
- [ ] Implement subscription management
- [ ] Implement usage tracking
- [ ] Set up payment processing

**Week 11-12: Enterprise Features**
- [ ] Implement advanced RBAC
- [ ] Implement audit logging
- [ ] Implement compliance reporting
- [ ] Set up dedicated support

#### Phase 3: Production & Scaling (Week 13-16+)

**Week 13-14: Hardening**
- [ ] Security audit
- [ ] Penetration testing
- [ ] Performance optimization
- [ ] Load testing

**Week 15-16: Launch**
- [ ] Beta testing
- [ ] User onboarding
- [ ] Documentation
- [ ] Production deployment

**Week 17+: Iteration**
- [ ] Gather user feedback
- [ ] Iterate on features
- [ ] Scale infrastructure
- [ ] Expand client support

---

## 7. Architecture Documentation

### 7.1 Local-First MVP Architecture

```mermaid
graph TB
    subgraph "User Environment"
        Claude[Claude Desktop]
        UCP_MVP[UCP MVP Server]
    end
    
    subgraph "UCP MVP Components"
        Server[MCP Server]
        Router[Router - Baseline + Adaptive]
        ToolZoo[Tool Zoo - ChromaDB]
        Session[Session Manager - SQLite]
        Pool[Connection Pool]
    end
    
    subgraph "Downstream MCP Servers"
        GitHub[GitHub MCP]
        Gmail[Gmail MCP]
        Slack[Slack MCP]
    end
    
    Claude -->|stdio| Server
    Server --> Router
    Server --> Session
    Server --> Pool
    Router --> ToolZoo
    Pool --> GitHub
    Pool --> Gmail
    Pool --> Slack
```

**Key Design Principles:**
- **Privacy-First:** All data stays local
- **Simplicity:** Minimal dependencies, easy to install
- **Performance:** Fast routing with local storage
- **User Control:** User owns all data and configuration

**Data Flow:**
1. User sends message to Claude Desktop
2. Claude Desktop calls UCP MVP via stdio
3. UCP MVP analyzes context and selects relevant tools
4. UCP MVP routes tool calls to downstream servers
5. Results returned to Claude Desktop
6. All data stored locally (SQLite, ChromaDB)

### 7.2 Cloud Version Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        VSCode[VS Code Extension]
        Web[Web App]
        Mobile[Mobile Apps]
    end
    
    subgraph "API Gateway"
        Gateway[API Gateway]
        Auth[Auth Service]
        RateLimit[Rate Limiter]
    end
    
    subgraph "Application Layer"
        UCP_Cloud[UCP Cloud Server]
        Router[Router - SOTA Pipeline]
        ToolZoo[Tool Zoo - Qdrant]
        Session[Session Manager - Redis]
        Pool[Connection Pool - SSE/HTTP]
    end
    
    subgraph "Data Layer"
        Redis[Redis Cluster]
        Qdrant[Qdrant Vector DB]
        PostgreSQL[PostgreSQL]
        S3[S3 Data Lake]
        Timescale[TimescaleDB Analytics]
    end
    
    subgraph "Infrastructure"
        K8s[Kubernetes]
        Monitoring[Monitoring Stack]
        CI/CD[CI/CD Pipeline]
    end
    
    VSCode -->|HTTPS| Gateway
    Web -->|HTTPS| Gateway
    Mobile -->|HTTPS| Gateway
    Gateway --> Auth
    Gateway --> RateLimit
    Gateway --> UCP_Cloud
    UCP_Cloud --> Router
    UCP_Cloud --> Session
    UCP_Cloud --> Pool
    Router --> ToolZoo
    Session --> Redis
    ToolZoo --> Qdrant
    UCP_Cloud --> PostgreSQL
    UCP_Cloud --> S3
    UCP_Cloud --> Timescale
```

**Key Design Principles:**
- **Scalability:** Horizontal scaling with Kubernetes
- **Multi-Tenancy:** Isolated tenant environments
- **Observability:** Comprehensive monitoring and logging
- **Enterprise-Ready:** SSO, RBAC, compliance

**Data Flow:**
1. Client authenticates via Auth Service
2. Client sends request via API Gateway
3. UCP Cloud processes request with SOTA routing
4. Results cached in Redis
5. Analytics logged to TimescaleDB
6. Training data stored in S3
7. Models fine-tuned periodically

### 7.3 Code Sharing Architecture

```mermaid
graph TB
    subgraph "Shared Layer"
        Models[Data Models]
        Config[Configuration]
        Interfaces[Abstract Interfaces]
        Transport[MCP Protocol]
    end
    
    subgraph "Local MVP Layer"
        LocalServer[Local Server]
        LocalRouter[Local Router]
        LocalToolZoo[Local Tool Zoo]
        LocalSession[Local Session Manager]
    end
    
    subgraph "Cloud Layer"
        CloudServer[Cloud Server]
        CloudRouter[Cloud Router]
        CloudToolZoo[Cloud Tool Zoo]
        CloudSession[Cloud Session Manager]
        CloudAPI[REST API]
        CloudAuth[Auth Service]
    end
    
    LocalServer -->|implements| Interfaces
    LocalRouter -->|implements| Interfaces
    LocalToolZoo -->|implements| Interfaces
    LocalSession -->|implements| Interfaces
    
    CloudServer -->|implements| Interfaces
    CloudRouter -->|implements| Interfaces
    CloudToolZoo -->|implements| Interfaces
    CloudSession -->|implements| Interfaces
    CloudAPI -->|implements| Interfaces
    CloudAuth -->|implements| Interfaces
    
    LocalServer -->|uses| Models
    CloudServer -->|uses| Models
    LocalRouter -->|uses| Models
    CloudRouter -->|uses| Models
    
    LocalServer -->|uses| Config
    CloudServer -->|uses| Config
    
    LocalServer -->|uses| Transport
    CloudServer -->|uses| Transport
```

**Interface Boundaries:**
- **Router Interface:** [`route(session, query) -> RoutingDecision`](shared/src/ucp_core/interfaces.py)
- **ToolZoo Interface:** [`search(query, top_k) -> list[ToolSchema]`](shared/src/ucp_core/interfaces.py)
- **SessionManager Interface:** [`create_session(), get_session(), save_session()`](shared/src/ucp_core/interfaces.py)
- **Transport Interface:** [`connect(), call_tool(), disconnect()`](shared/src/ucp_transport/base_transport.py)

**Migration Path:**
1. Start with Local MVP (simple implementations)
2. Implement interfaces in shared layer
3. Local MVP implements interfaces
4. Cloud version implements same interfaces
5. Users can migrate by switching implementations
6. Data migration tools provided for transition

---

## 8. Deployment Strategy

### 8.1 Local MVP Deployment

**Installation Methods:**

1. **PyPI (Recommended)**
```bash
pip install ucp-mvp
ucp init-config
ucp serve
```

2. **Docker**
```bash
docker pull ucp/mvp:latest
docker run -v ~/.ucp:/data ucp/mvp
```

3. **From Source**
```bash
git clone https://github.com/your-org/UniversalContextProtocol
cd UniversalContextProtocol/local
pip install -e .
```

**Claude Desktop Integration:**
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

**Data Storage:**
- Configuration: `~/.ucp/ucp_config.yaml`
- Sessions: `~/.ucp/data/sessions.db`
- Tool Zoo: `~/.ucp/data/tool_zoo`
- Logs: `~/.ucp/logs/`

### 8.2 Cloud Version Deployment

**Infrastructure:**

1. **Kubernetes (Production)**
```bash
helm install ucp-cloud ./infrastructure/kubernetes/ucp-cloud
```

2. **Docker Compose (Development)**
```bash
cd infrastructure/docker
docker-compose up -d
```

3. **Terraform (Infrastructure as Code)**
```bash
cd infrastructure/terraform
terraform init
terraform apply
```

**Environment Variables:**
```bash
# Database
REDIS_URL=redis://redis-cluster:6379
QDRANT_URL=http://qdrant:6333
POSTGRES_URL=postgresql://user:pass@postgres:5432/ucp

# Storage
S3_BUCKET=ucp-data-lake
S3_REGION=us-east-1

# Auth
OAUTH_CLIENT_ID=xxx
OAUTH_CLIENT_SECRET=xxx
SSO_PROVIDER=okta

# Monitoring
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
```

**Scaling:**
- Horizontal Pod Autoscaler for UCP servers
- Redis Cluster for session management
- Qdrant distributed cluster for vector search
- PostgreSQL read replicas for analytics

---

## 9. Risk Mitigation

### 9.1 Technical Risks

**Risk: Code duplication between versions**
- **Mitigation:** Shared interfaces and models in [`shared/`](shared/)
- **Fallback:** Regular code reviews to identify duplication

**Risk: MVP lacks features users want**
- **Mitigation:** Focus on core value (tool selection, privacy)
- **Fallback:** Gather feedback and iterate quickly

**Risk: Cloud version complexity causes delays**
- **Mitigation:** Start with MVP, add cloud features incrementally
- **Fallback:** Use managed services (AWS, GCP) to reduce complexity

**Risk: Migration from local to cloud is difficult**
- **Mitigation:** Design migration path from day one
- **Fallback:** Provide migration tools and documentation

### 9.2 Business Risks

**Risk: MVP doesn't generate revenue**
- **Mitigation:** MVP is open-source, builds community
- **Fallback:** Cloud version monetizes advanced features

**Risk: Cloud version faces competition**
- **Mitigation:** Focus on enterprise features and quality
- **Fallback:** Differentiate with privacy and compliance

**Risk: Team size insufficient for both versions**
- **Mitigation:** Prioritize MVP first, cloud second
- **Fallback:** Hire additional engineers as needed

---

## 10. Success Metrics

### 10.1 MVP Success Metrics

**Adoption:**
- 1,000+ PyPI downloads in first month
- 100+ GitHub stars
- 50+ active users (based on telemetry opt-in)

**Quality:**
- 95%+ routing precision (evaluation harness)
- <100ms average routing time
- 99%+ uptime (based on error logs)

**Engagement:**
- 10+ GitHub issues/PRs per month
- 5+ community contributors
- Positive feedback from early adopters

### 10.2 Cloud Success Metrics

**Revenue:**
- $10k MRR within 6 months
- 100+ paying customers
- $50k ARR within 12 months

**Adoption:**
- 1,000+ registered users
- 100+ enterprise customers
- 50%+ conversion from MVP to cloud

**Quality:**
- 99.9%+ uptime
- <50ms p95 latency
- 4.5+ star rating on app stores

---

## 11. Next Steps

### Immediate Actions (This Week)

1. **Review and Approve Plan**
   - [ ] Stakeholder review
   - [ ] Architecture review
   - [ ] Resource planning

2. **Setup Development Environment**
   - [ ] Create new repository structure
   - [ ] Set up CI/CD for MVP
   - [ ] Set up CI/CD for cloud

3. **Begin Migration**
   - [ ] Extract shared code
   - [ ] Archive original codebase
   - [ ] Create MVP implementations

### Short-Term Goals (Month 1)

- Complete repository reorganization
- Implement MVP core functionality
- Set up testing infrastructure
- Begin cloud infrastructure planning

### Long-Term Goals (Year 1)

- MVP v1.0 release
- MVP v1.2 release with advanced routing
- Cloud beta launch
- Cloud v1.0 release
- 100+ paying customers

---

## 12. Appendix

### 12.1 Glossary

- **MCP:** Model Context Protocol
- **UCP:** Universal Context Protocol
- **MVP:** Minimum Viable Product
- **SOTA:** State of the Art
- **RAFT:** Retrieval-Augmented Fine-Tuning
- **SaaS:** Software as a Service
- **SSO:** Single Sign-On
- **RBAC:** Role-Based Access Control
- **SCIM:** System for Cross-domain Identity Management

### 12.2 References

- [MCP Specification](https://modelcontextprotocol.io/)
- [Gorilla Paper](https://arxiv.org/abs/2305.15334)
- [RAFT Paper](https://arxiv.org/abs/2309.15217)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [ChromaDB](https://www.trychroma.com/)
- [Qdrant](https://qdrant.tech/)

### 12.3 Contact

**Project Lead:** [Name]  
**Email:** [email]  
**GitHub:** [repository]  
**Discord:** [server]

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-10  
**Status:** Draft for Review

**Date:** 2026-01-10  
**Status:** Planning Phase  
**Objective:** Split UCP into local-first MVP and future cloud business version

---

## Executive Summary

The Universal Context Protocol (UCP) project will be reorganized into a dual-track architecture:

1. **Local-First MVP** - Open-source, user-controlled proxy running locally with immediate value
2. **Cloud Version** - Future business deployment with centralized analytics, SaaS model, and enterprise features

This reorganization enables rapid MVP delivery while preserving sophisticated infrastructure for future cloud deployment.

---

## 1. New Repository Structure

### Top-Level Structure

```
UniversalContextProtocol/
├── README.md                          # Updated for dual-track approach
├── LICENSE                            # MIT license
├── .gitignore
├── pyproject.toml                     # Root project config (shared)
├── ucp_config.example.yaml             # Shared config template
│
├── shared/                            # SHARED CODE BETWEEN VERSIONS
│   ├── src/
│   │   ├── ucp_core/                 # Core abstractions and interfaces
│   │   │   ├── __init__.py
│   │   │   ├── models.py             # Shared data models
│   │   │   ├── config.py             # Shared configuration
│   │   │   ├── exceptions.py         # Shared exceptions
│   │   │   └── interfaces.py        # Abstract interfaces
│   │   └── ucp_transport/           # Transport layer abstractions
│   │       ├── __init__.py
│   │       ├── mcp_protocol.py       # MCP protocol implementation
│   │       └── base_transport.py     # Base transport class
│   ├── tests/
│   │   └── test_shared/
│   └── pyproject.toml              # Shared package config
│
├── local/                             # LOCAL-FIRST MVP (Open Source)
│   ├── README.md                     # MVP-specific documentation
│   ├── pyproject.toml               # MVP package config
│   ├── src/
│   │   └── ucp_mvp/
│   │       ├── __init__.py
│   │       ├── server.py             # Local MCP server
│   │       ├── router.py             # Simplified router (baseline + adaptive)
│   │       ├── tool_zoo.py          # Local vector store (ChromaDB)
│   │       ├── session.py            # Local session manager (SQLite)
│   │       ├── connection_pool.py     # Connection pool for downstream servers
│   │       ├── cli.py               # MVP CLI interface
│   │       └── dashboard.py          # Simple Streamlit dashboard
│   ├── tests/
│   │   └── test_mvp/
│   ├── docs/
│   │   ├── mvp_architecture.md
│   │   ├── mvp_user_guide.md
│   │   └── mvp_deployment.md
│   └── clients/
│       ├── cli/                     # CLI client (60% complete)
│       └── desktop/                # Desktop app (30% complete)
│
├── cloud/                            # CLOUD VERSION (Future Business)
│   ├── README.md                     # Cloud-specific documentation
│   ├── pyproject.toml               # Cloud package config
│   ├── src/
│   │   └── ucp_cloud/
│   │       ├── __init__.py
│   │       ├── server.py             # Cloud MCP server
│   │       ├── router.py             # Full SOTA router with all features
│   │       ├── tool_zoo.py          # Cloud vector store (Qdrant/Weaviate)
│   │       ├── session.py            # Cloud session manager (Redis)
│   │       ├── connection_pool.py     # Connection pool with SSE support
│   │       ├── telemetry.py          # Centralized telemetry
│   │       ├── bandit.py            # Shared bandit scorer
│   │       ├── online_opt.py         # Online optimization
│   │       ├── routing_pipeline.py   # Full SOTA pipeline
│   │       ├── raft.py              # RAFT fine-tuning
│   │       ├── graph.py             # LangGraph integration
│   │       ├── api/                # REST API for cloud services
│   │       │   ├── __init__.py
│   │       │   ├── analytics.py
│   │       │   ├── billing.py
│   │       │   └── admin.py
│   │       ├── auth/               # Authentication & authorization
│   │       │   ├── __init__.py
│   │       │   ├── sso.py
│   │       │   └── rbac.py
│   │       └── pipeline/            # Data pipelines
│   │           ├── __init__.py
│   │           ├── training.py
│   │           └── analytics.py
│   ├── tests/
│   │   └── test_cloud/
│   ├── docs/
│   │   ├── cloud_architecture.md
│   │   ├── cloud_deployment.md
│   │   └── cloud_api_reference.md
│   ├── infrastructure/               # Cloud infrastructure (Terraform/Helm)
│   │   ├── terraform/
│   │   ├── kubernetes/
│   │   └── docker/
│   └── clients/
│       ├── vscode/                  # VS Code extension (40% complete)
│       └── web/                    # Future web client
│
├── docs/                             # SHARED DOCUMENTATION
│   ├── index.md                     # Documentation index
│   ├── getting_started.md
│   ├── debugging_playbook.md
│   ├── evaluation_harness.md
│   ├── research/                    # Research papers and synthesis
│   │   ├── synthesis_agent_design.md
│   │   ├── synthesis_context_management.md
│   │   ├── synthesis_feedback_eval.md
│   │   └── synthesis_tool_selection.md
│   └── archive/                    # Archived documentation
│
├── reports/                          # AUDIT AND VALIDATION REPORTS
│   ├── codebase_audit_report.md
│   ├── corpus_integrity_report.md
│   ├── roadmap_edge.md
│   └── validation_report.json
│
├── plans/                            # PLANNING DOCUMENTS
│   ├── repository_reorganization_plan.md  # This document
│   ├── mvp_implementation_roadmap.md
│   ├── cloud_implementation_roadmap.md
│   └── migration_checklist.md
│
└── archive/                           # ARCHIVED CODE (Not needed for MVP)
    ├── src/
    │   └── ucp_original/            # Original monolithic codebase
    └── tests/
        └── test_original/
```

---

## 2. Scope Definitions

### 2.1 Local-First MVP Scope

**Core Philosophy:** Privacy-first, user-controlled, immediate value, minimal dependencies

#### Core Features (MVP v1.0)

**MCP Proxy Functionality:**
- ✅ Stdio transport for Claude Desktop
- ✅ Basic tool discovery and indexing
- ✅ Context-aware tool selection (baseline router)
- ✅ Tool call routing to downstream servers
- ✅ Session persistence (SQLite)
- ✅ Connection pooling

**Routing Capabilities:**
- ✅ Semantic search (sentence-transformers)
- ✅ Keyword search
- ✅ Hybrid search (semantic + keyword)
- ✅ Domain detection
- ✅ Adaptive router with co-occurrence tracking
- ❌ Cross-encoder reranking (deferred to v1.1)
- ❌ Bandit learning (deferred to v1.1)
- ❌ Online optimization (deferred to v1.1)

**Data Storage:**
- ✅ SQLite for sessions
- ✅ ChromaDB for tool embeddings
- ✅ Local file system for configuration
- ❌ No cloud sync
- ❌ No centralized analytics

**User Interface:**
- ✅ CLI interface (ucp serve, ucp index, ucp search)
- ✅ Simple Streamlit dashboard (basic metrics)
- ❌ No web UI (deferred)
- ❌ No mobile app (deferred)

**Analytics:**
- ✅ Local metrics (success rate, latency, tool usage)
- ✅ Session history viewing
- ✅ Basic statistics dashboard
- ❌ No centralized analytics
- ❌ No cross-user learning

**Installation & Distribution:**
- ✅ PyPI package
- ✅ Docker image
- ✅ pip install ucp-mvp
- ✅ One-line setup for Claude Desktop
- ✅ Configuration wizard

**Testing & Quality:**
- ✅ Unit tests for core functionality
- ✅ Integration tests with real MCP servers
- ✅ Evaluation harness for routing quality
- ✅ Documentation (user guide, API reference)

#### MVP v1.1 (Enhanced Routing)
- Cross-encoder reranking
- Bandit-based exploration
- Per-tool bias learning
- Advanced dashboard with routing visualization

#### MVP v1.2 (Performance)
- GPU acceleration for embeddings
- Caching layer
- Performance optimizations
- Better error handling

#### Out of Scope for MVP
- ❌ Cloud infrastructure
- ❌ Multi-tenant architecture
- ❌ SaaS features (billing, accounts)
- ❌ Enterprise features (SSO, RBAC)
- ❌ RAFT fine-tuning pipeline
- ❌ Centralized analytics
- ❌ Model training pipeline
- ❌ SSE/HTTP downstream transports
- ❌ LangGraph orchestration

---

### 2.2 Cloud Version Scope

**Core Philosophy:** Scalable, multi-tenant, feature-rich, business-oriented

#### Additional Features Beyond MVP

**Infrastructure:**
- ✅ Multi-tenant architecture
- ✅ Horizontal scaling (Kubernetes)
- ✅ Load balancing
- ✅ High availability (HA)
- ✅ Disaster recovery
- ✅ Global CDN for static assets

**Advanced Routing:**
- ✅ Full SOTA routing pipeline
- ✅ Cross-encoder reranking
- ✅ Bandit-based exploration
- ✅ Online optimization
- ✅ RAFT fine-tuning
- ✅ LangGraph orchestration
- ✅ Ensemble routing strategies

**Data Storage:**
- ✅ Redis for session management
- ✅ Qdrant/Weaviate for vector store
- ✅ PostgreSQL for relational data
- ✅ S3/GCS for data lake
- ✅ TimescaleDB for analytics

**SaaS Features:**
- ✅ User authentication (OAuth, SSO)
- ✅ Role-based access control (RBAC)
- ✅ Multi-tenant isolation
- ✅ Billing and subscription management
- ✅ Usage-based pricing
- ✅ API keys and rate limiting
- ✅ Audit logging

**Centralized Analytics:**
- ✅ Cross-user routing analytics
- ✅ A/B testing framework
- ✅ Model training pipeline
- ✅ Continuous evaluation
- ✅ Performance monitoring
- ✅ Alerting and observability
- ✅ Business intelligence dashboards

**Enterprise Features:**
- ✅ SSO (SAML, OIDC)
- ✅ SCIM provisioning
- ✅ Advanced RBAC
- ✅ Data residency options
- ✅ Compliance reporting
- ✅ Custom SLAs
- ✅ Dedicated support

**Developer Experience:**
- ✅ REST API
- ✅ GraphQL API
- ✅ Webhooks
- ✅ SDKs (Python, JavaScript)
- ✅ API documentation (OpenAPI)
- ✅ Sandbox environment
- ✅ Developer portal

**Clients:**
- ✅ VS Code extension (enhanced)
- ✅ Web application
- ✅ Mobile apps (iOS, Android)
- ✅ Browser extension

---

## 3. Code Sharing Strategy

### 3.1 Shared Components

The `shared/` directory contains code used by both local and cloud versions:

**Core Abstractions (`shared/src/ucp_core/`):**
- [`models.py`](shared/src/ucp_core/models.py) - Data models (ToolSchema, SessionState, RoutingDecision, etc.)
- [`config.py`](shared/src/ucp_core/config.py) - Configuration base classes and validation
- [`exceptions.py`](shared/src/ucp_core/exceptions.py) - Custom exceptions
- [`interfaces.py`](shared/src/ucp_core/interfaces.py) - Abstract interfaces (Router, ToolZoo, SessionManager)

**Transport Layer (`shared/src/ucp_transport/`):**
- [`mcp_protocol.py`](shared/src/ucp_transport/mcp_protocol.py) - MCP protocol implementation
- [`base_transport.py`](shared/src/ucp_transport/base_transport.py) - Base transport class

### 3.2 Version-Specific Implementations

**Local MVP (`local/src/ucp_mvp/`):**
- Uses simplified implementations
- Local storage only (SQLite, ChromaDB)
- Basic routing (baseline + adaptive)
- No external dependencies beyond core

**Cloud Version (`cloud/src/ucp_cloud/`):**
- Uses full SOTA implementations
- Cloud storage (Redis, Qdrant, PostgreSQL)
- Advanced routing with all features
- Additional services (auth, billing, analytics)

### 3.3 Dependency Management

**Shared Package (`shared/pyproject.toml`):**
```toml
[project]
name = "ucp-core"
version = "0.1.0"
dependencies = [
    "mcp>=1.25.0",
    "pydantic>=2.5.0",
    "pyyaml>=6.0",
]
```

**Local MVP (`local/pyproject.toml`):**
```toml
[project]
name = "ucp-mvp"
version = "0.1.0"
dependencies = [
    "ucp-core>=0.1.0",
    "mcp>=1.25.0",
    "chromadb>=0.4.22",
    "sentence-transformers>=2.2.0",
    "structlog>=24.1.0",
    "streamlit>=1.28.0",
]
```

**Cloud Version (`cloud/pyproject.toml`):**
```toml
[project]
name = "ucp-cloud"
version = "0.1.0"
dependencies = [
    "ucp-core>=0.1.0",
    "mcp>=1.25.0",
    "qdrant-client>=1.6.0",
    "redis>=5.0.0",
    "psycopg2-binary>=2.9.0",
    "fastapi>=0.109.0",
    "langgraph>=0.0.40",
    "sentence-transformers>=2.2.0",
    "structlog>=24.1.0",
    "prometheus-client>=0.19.0",
]
```

---

## 4. Migration Strategy

### 4.1 Phase 1: Repository Restructuring (Week 1-2)

**Step 1: Create new directory structure**
```bash
mkdir -p shared/src/ucp_core shared/src/ucp_transport shared/tests
mkdir -p local/src/ucp_mvp local/tests local/docs local/clients
mkdir -p cloud/src/ucp_cloud cloud/tests cloud/docs cloud/infrastructure
mkdir -p archive
```

**Step 2: Extract shared code**
- Move [`models.py`](src/ucp/models.py) → [`shared/src/ucp_core/models.py`](shared/src/ucp_core/models.py)
- Move [`config.py`](src/ucp/config.py) → [`shared/src/ucp_core/config.py`](shared/src/ucp_core/config.py)
- Extract interfaces from existing code → [`shared/src/ucp_core/interfaces.py`](shared/src/ucp_core/interfaces.py)
- Create base transport class → [`shared/src/ucp_transport/base_transport.py`](shared/src/ucp_transport/base_transport.py)

**Step 3: Archive original codebase**
```bash
mv src archive/src/ucp_original
mv tests archive/tests/test_original
```

**Step 4: Create MVP implementations**
- Copy simplified versions to [`local/src/ucp_mvp/`](local/src/ucp_mvp/)
- Implement baseline router (remove SOTA features)
- Implement local storage backends (SQLite, ChromaDB)
- Create MVP CLI interface

**Step 5: Create cloud implementations**
- Copy full versions to [`cloud/src/ucp_cloud/`](cloud/src/ucp_cloud/)
- Keep all SOTA features (bandit, online_opt, routing_pipeline)
- Implement cloud storage backends (Redis, Qdrant)
- Create REST API layer

### 4.2 Phase 2: MVP Implementation (Week 3-8)

**Week 3-4: Core Functionality**
- Implement MVP server with stdio transport
- Implement baseline router with hybrid search
- Implement local tool zoo (ChromaDB)
- Implement session manager (SQLite)
- Basic CLI commands (serve, index, search)

**Week 5-6: Testing & Integration**
- Unit tests for all components
- Integration tests with real MCP servers
- Evaluation harness validation
- Fix bugs and stabilize

**Week 7-8: Polish & Documentation**
- Streamlit dashboard
- User guide and API reference
- PyPI packaging
- Docker image
- Beta testing

### 4.3 Phase 3: Cloud Development (Week 9-16+)

**Week 9-12: Infrastructure**
- Set up cloud infrastructure (Terraform, Kubernetes)
- Implement cloud storage backends
- Implement authentication and authorization
- Set up monitoring and observability

**Week 13-16: Advanced Features**
- Implement full SOTA routing pipeline
- Implement RAFT fine-tuning pipeline
- Implement centralized analytics
- Implement SaaS features (billing, multi-tenant)

**Week 17+: Production & Scaling**
- Performance optimization
- Security hardening
- Load testing
- Production deployment

---

## 5. File Mapping

### 5.1 Current → New Structure

| Current File | New Location | Notes |
|--------------|--------------|-------|
| [`src/ucp/models.py`](src/ucp/models.py) | [`shared/src/ucp_core/models.py`](shared/src/ucp_core/models.py) | Shared data models |
| [`src/ucp/config.py`](src/ucp/config.py) | [`shared/src/ucp_core/config.py`](shared/src/ucp_core/config.py) | Shared configuration |
| [`src/ucp/server.py`](src/ucp/server.py) | [`local/src/ucp_mvp/server.py`](local/src/ucp_mvp/server.py) | Simplified for MVP |
| [`src/ucp/server.py`](src/ucp/server.py) | [`cloud/src/ucp_cloud/server.py`](cloud/src/ucp_cloud/server.py) | Full version |
| [`src/ucp/router.py`](src/ucp/router.py) | [`local/src/ucp_mvp/router.py`](local/src/ucp_mvp/router.py) | Baseline + Adaptive only |
| [`src/ucp/router.py`](src/ucp/router.py) | [`cloud/src/ucp_cloud/router.py`](cloud/src/ucp_cloud/router.py) | Full SOTA router |
| [`src/ucp/tool_zoo.py`](src/ucp/tool_zoo.py) | [`local/src/ucp_mvp/tool_zoo.py`](local/src/ucp_mvp/tool_zoo.py) | ChromaDB only |
| [`src/ucp/tool_zoo.py`](src/ucp/tool_zoo.py) | [`cloud/src/ucp_cloud/tool_zoo.py`](cloud/src/ucp_cloud/tool_zoo.py) | Qdrant + advanced features |
| [`src/ucp/session.py`](src/ucp/session.py) | [`local/src/ucp_mvp/session.py`](local/src/ucp_mvp/session.py) | SQLite only |
| [`src/ucp/session.py`](src/ucp/session.py) | [`cloud/src/ucp_cloud/session.py`](cloud/src/ucp_cloud/session.py) | Redis + advanced features |
| [`src/ucp/connection_pool.py`](src/ucp/connection_pool.py) | [`local/src/ucp_mvp/connection_pool.py`](local/src/ucp_mvp/connection_pool.py) | Stdio only |
| [`src/ucp/connection_pool.py`](src/ucp/connection_pool.py) | [`cloud/src/ucp_cloud/connection_pool.py`](cloud/src/ucp_cloud/connection_pool.py) | Stdio + SSE/HTTP |
| [`src/ucp/cli.py`](src/ucp/cli.py) | [`local/src/ucp_mvp/cli.py`](local/src/ucp_mvp/cli.py) | MVP CLI |
| [`src/ucp/dashboard.py`](src/ucp/dashboard.py) | [`local/src/ucp_mvp/dashboard.py`](local/src/ucp_mvp/dashboard.py) | Simple dashboard |
| [`src/ucp/telemetry.py`](src/ucp/telemetry.py) | [`cloud/src/ucp_cloud/telemetry.py`](cloud/src/ucp_cloud/telemetry.py) | Cloud only |
| [`src/ucp/bandit.py`](src/ucp/bandit.py) | [`cloud/src/ucp_cloud/bandit.py`](cloud/src/ucp_cloud/bandit.py) | Cloud only |
| [`src/ucp/online_opt.py`](src/ucp/online_opt.py) | [`cloud/src/ucp_cloud/online_opt.py`](cloud/src/ucp_cloud/online_opt.py) | Cloud only |
| [`src/ucp/routing_pipeline.py`](src/ucp/routing_pipeline.py) | [`cloud/src/ucp_cloud/routing_pipeline.py`](cloud/src/ucp_cloud/routing_pipeline.py) | Cloud only |
| [`src/ucp/raft.py`](src/ucp/raft.py) | [`cloud/src/ucp_cloud/raft.py`](cloud/src/ucp_cloud/raft.py) | Cloud only |
| [`src/ucp/graph.py`](src/ucp/graph.py) | [`cloud/src/ucp_cloud/graph.py`](cloud/src/ucp_cloud/graph.py) | Cloud only |
| [`src/ucp/http_server.py`](src/ucp/http_server.py) | [`cloud/src/ucp_cloud/http_server.py`](cloud/src/ucp_cloud/http_server.py) | Cloud only |
| [`src/ucp/client_api.py`](src/ucp/client_api.py) | [`cloud/src/ucp_cloud/api/client_api.py`](cloud/src/ucp_cloud/api/client_api.py) | Cloud only |
| [`src/ucp/transports.py`](src/ucp/transports.py) | [`shared/src/ucp_transport/mcp_protocol.py`](shared/src/ucp_transport/mcp_protocol.py) | Shared transport |
| [`clients/cli/`](clients/cli/) | [`local/clients/cli/`](local/clients/cli/) | MVP CLI client |
| [`clients/desktop/`](clients/desktop/) | [`local/clients/desktop/`](local/clients/desktop/) | MVP desktop app |
| [`clients/vscode/`](clients/vscode/) | [`cloud/clients/vscode/`](cloud/clients/vscode/) | Cloud VS Code extension |
| [`clients/harness/`](clients/harness/) | [`shared/tests/evaluation/`](shared/tests/evaluation/) | Shared evaluation |
| [`README.md`](README.md) | [`README.md`](README.md) | Updated for dual-track |
| [`pyproject.toml`](pyproject.toml) | [`pyproject.toml`](pyproject.toml) | Root config |
| [`docs/`](docs/) | [`docs/`](docs/) | Shared docs |

### 5.2 New Files to Create

**Shared:**
- [`shared/src/ucp_core/__init__.py`](shared/src/ucp_core/__init__.py)
- [`shared/src/ucp_core/exceptions.py`](shared/src/ucp_core/exceptions.py)
- [`shared/src/ucp_core/interfaces.py`](shared/src/ucp_core/interfaces.py)
- [`shared/src/ucp_transport/__init__.py`](shared/src/ucp_transport/__init__.py)
- [`shared/src/ucp_transport/base_transport.py`](shared/src/ucp_transport/base_transport.py)
- [`shared/pyproject.toml`](shared/pyproject.toml)

**Local MVP:**
- [`local/README.md`](local/README.md)
- [`local/pyproject.toml`](local/pyproject.toml)
- [`local/src/ucp_mvp/__init__.py`](local/src/ucp_mvp/__init__.py)
- [`local/docs/mvp_architecture.md`](local/docs/mvp_architecture.md)
- [`local/docs/mvp_user_guide.md`](local/docs/mvp_user_guide.md)
- [`local/docs/mvp_deployment.md`](local/docs/mvp_deployment.md)

**Cloud:**
- [`cloud/README.md`](cloud/README.md)
- [`cloud/pyproject.toml`](cloud/pyproject.toml)
- [`cloud/src/ucp_cloud/__init__.py`](cloud/src/ucp_cloud/__init__.py)
- [`cloud/src/ucp_cloud/api/__init__.py`](cloud/src/ucp_cloud/api/__init__.py)
- [`cloud/src/ucp_cloud/api/analytics.py`](cloud/src/ucp_cloud/api/analytics.py)
- [`cloud/src/ucp_cloud/api/billing.py`](cloud/src/ucp_cloud/api/billing.py)
- [`cloud/src/ucp_cloud/api/admin.py`](cloud/src/ucp_cloud/api/admin.py)
- [`cloud/src/ucp_cloud/auth/__init__.py`](cloud/src/ucp_cloud/auth/__init__.py)
- [`cloud/src/ucp_cloud/auth/sso.py`](cloud/src/ucp_cloud/auth/sso.py)
- [`cloud/src/ucp_cloud/auth/rbac.py`](cloud/src/ucp_cloud/auth/rbac.py)
- [`cloud/src/ucp_cloud/pipeline/__init__.py`](cloud/src/ucp_cloud/pipeline/__init__.py)
- [`cloud/src/ucp_cloud/pipeline/training.py`](cloud/src/ucp_cloud/pipeline/training.py)
- [`cloud/src/ucp_cloud/pipeline/analytics.py`](cloud/src/ucp_cloud/pipeline/analytics.py)
- [`cloud/docs/cloud_architecture.md`](cloud/docs/cloud_architecture.md)
- [`cloud/docs/cloud_deployment.md`](cloud/docs/cloud_deployment.md)
- [`cloud/docs/cloud_api_reference.md`](cloud/docs/cloud_api_reference.md)

**Planning:**
- [`plans/mvp_implementation_roadmap.md`](plans/mvp_implementation_roadmap.md)
- [`plans/cloud_implementation_roadmap.md`](plans/cloud_implementation_roadmap.md)
- [`plans/migration_checklist.md`](plans/migration_checklist.md)

---

## 6. Implementation Roadmap

### 6.1 MVP Implementation Roadmap

#### Phase 1: Repository Reorganization (Week 1-2)

**Week 1: Structure & Shared Code**
- [ ] Create new directory structure
- [ ] Extract shared code to [`shared/`](shared/)
- [ ] Define interfaces in [`interfaces.py`](shared/src/ucp_core/interfaces.py)
- [ ] Archive original codebase
- [ ] Update root [`README.md`](README.md)

**Week 2: MVP Foundation**
- [ ] Create MVP package structure
- [ ] Implement simplified server
- [ ] Implement baseline router
- [ ] Implement local tool zoo (ChromaDB)
- [ ] Implement session manager (SQLite)

#### Phase 2: Core Functionality (Week 3-6)

**Week 3: Routing & Storage**
- [ ] Implement hybrid search (semantic + keyword)
- [ ] Implement domain detection
- [ ] Implement adaptive router with co-occurrence
- [ ] Implement connection pooling
- [ ] Implement stdio transport

**Week 4: CLI & Dashboard**
- [ ] Implement CLI commands (serve, index, search, status)
- [ ] Implement configuration wizard
- [ ] Implement basic Streamlit dashboard
- [ ] Add metrics visualization

**Week 5: Testing**
- [ ] Write unit tests for all components
- [ ] Write integration tests with real MCP servers
- [ ] Set up evaluation harness
- [ ] Run validation suite

**Week 6: Bug Fixes & Stabilization**
- [ ] Fix identified issues
- [ ] Improve error handling
- [ ] Add logging and debugging
- [ ] Performance profiling

#### Phase 3: Polish & Release (Week 7-8)

**Week 7: Documentation**
- [ ] Write MVP architecture doc
- [ ] Write user guide
- [ ] Write API reference
- [ ] Create quick start tutorial

**Week 8: Packaging & Release**
- [ ] PyPI packaging
- [ ] Docker image
- [ ] Beta testing
- [ ] v1.0 release

#### Phase 4: Enhanced Features (Week 9-12)

**Week 9-10: Advanced Routing**
- [ ] Implement cross-encoder reranking
- [ ] Implement bandit exploration
- [ ] Implement per-tool bias learning
- [ ] Add routing visualization

**Week 11-12: Performance**
- [ ] GPU acceleration for embeddings
- [ ] Implement caching layer
- [ ] Optimize database queries
- [ ] Performance testing

---

### 6.2 Cloud Implementation Roadmap

#### Phase 1: Infrastructure Setup (Week 1-4)

**Week 1: Cloud Foundation**
- [ ] Set up cloud infrastructure (AWS/GCP)
- [ ] Configure Kubernetes cluster
- [ ] Set up CI/CD pipeline
- [ ] Configure monitoring stack

**Week 2: Storage Backends**
- [ ] Implement Redis session manager
- [ ] Implement Qdrant vector store
- [ ] Implement PostgreSQL integration
- [ ] Set up S3/GCS data lake

**Week 3: Authentication & Authorization**
- [ ] Implement OAuth2/OIDC
- [ ] Implement SSO (SAML)
- [ ] Implement RBAC
- [ ] Set up SCIM provisioning

**Week 4: API Layer**
- [ ] Implement REST API
- [ ] Implement GraphQL API
- [ ] Set up API gateway
- [ ] Configure rate limiting

#### Phase 2: Advanced Features (Week 5-12)

**Week 5-6: SOTA Routing**
- [ ] Port full SOTA routing pipeline
- [ ] Implement cross-encoder reranking
- [ ] Implement bandit scorer
- [ ] Implement online optimization

**Week 7-8: Analytics & Training**
- [ ] Implement centralized telemetry
- [ ] Set up analytics pipeline
- [ ] Implement RAFT fine-tuning
- [ ] Set up model training pipeline

**Week 9-10: SaaS Features**
- [ ] Implement billing system
- [ ] Implement subscription management
- [ ] Implement usage tracking
- [ ] Set up payment processing

**Week 11-12: Enterprise Features**
- [ ] Implement advanced RBAC
- [ ] Implement audit logging
- [ ] Implement compliance reporting
- [ ] Set up dedicated support

#### Phase 3: Production & Scaling (Week 13-16+)

**Week 13-14: Hardening**
- [ ] Security audit
- [ ] Penetration testing
- [ ] Performance optimization
- [ ] Load testing

**Week 15-16: Launch**
- [ ] Beta testing
- [ ] User onboarding
- [ ] Documentation
- [ ] Production deployment

**Week 17+: Iteration**
- [ ] Gather user feedback
- [ ] Iterate on features
- [ ] Scale infrastructure
- [ ] Expand client support

---

## 7. Architecture Documentation

### 7.1 Local-First MVP Architecture

```mermaid
graph TB
    subgraph "User Environment"
        Claude[Claude Desktop]
        UCP_MVP[UCP MVP Server]
    end
    
    subgraph "UCP MVP Components"
        Server[MCP Server]
        Router[Router - Baseline + Adaptive]
        ToolZoo[Tool Zoo - ChromaDB]
        Session[Session Manager - SQLite]
        Pool[Connection Pool]
    end
    
    subgraph "Downstream MCP Servers"
        GitHub[GitHub MCP]
        Gmail[Gmail MCP]
        Slack[Slack MCP]
    end
    
    Claude -->|stdio| Server
    Server --> Router
    Server --> Session
    Server --> Pool
    Router --> ToolZoo
    Pool --> GitHub
    Pool --> Gmail
    Pool --> Slack
```

**Key Design Principles:**
- **Privacy-First:** All data stays local
- **Simplicity:** Minimal dependencies, easy to install
- **Performance:** Fast routing with local storage
- **User Control:** User owns all data and configuration

**Data Flow:**
1. User sends message to Claude Desktop
2. Claude Desktop calls UCP MVP via stdio
3. UCP MVP analyzes context and selects relevant tools
4. UCP MVP routes tool calls to downstream servers
5. Results returned to Claude Desktop
6. All data stored locally (SQLite, ChromaDB)

### 7.2 Cloud Version Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        VSCode[VS Code Extension]
        Web[Web App]
        Mobile[Mobile Apps]
    end
    
    subgraph "API Gateway"
        Gateway[API Gateway]
        Auth[Auth Service]
        RateLimit[Rate Limiter]
    end
    
    subgraph "Application Layer"
        UCP_Cloud[UCP Cloud Server]
        Router[Router - SOTA Pipeline]
        ToolZoo[Tool Zoo - Qdrant]
        Session[Session Manager - Redis]
        Pool[Connection Pool - SSE/HTTP]
    end
    
    subgraph "Data Layer"
        Redis[Redis Cluster]
        Qdrant[Qdrant Vector DB]
        PostgreSQL[PostgreSQL]
        S3[S3 Data Lake]
        Timescale[TimescaleDB Analytics]
    end
    
    subgraph "Infrastructure"
        K8s[Kubernetes]
        Monitoring[Monitoring Stack]
        CI/CD[CI/CD Pipeline]
    end
    
    VSCode -->|HTTPS| Gateway
    Web -->|HTTPS| Gateway
    Mobile -->|HTTPS| Gateway
    Gateway --> Auth
    Gateway --> RateLimit
    Gateway --> UCP_Cloud
    UCP_Cloud --> Router
    UCP_Cloud --> Session
    UCP_Cloud --> Pool
    Router --> ToolZoo
    Session --> Redis
    ToolZoo --> Qdrant
    UCP_Cloud --> PostgreSQL
    UCP_Cloud --> S3
    UCP_Cloud --> Timescale
```

**Key Design Principles:**
- **Scalability:** Horizontal scaling with Kubernetes
- **Multi-Tenancy:** Isolated tenant environments
- **Observability:** Comprehensive monitoring and logging
- **Enterprise-Ready:** SSO, RBAC, compliance

**Data Flow:**
1. Client authenticates via Auth Service
2. Client sends request via API Gateway
3. UCP Cloud processes request with SOTA routing
4. Results cached in Redis
5. Analytics logged to TimescaleDB
6. Training data stored in S3
7. Models fine-tuned periodically

### 7.3 Code Sharing Architecture

```mermaid
graph TB
    subgraph "Shared Layer"
        Models[Data Models]
        Config[Configuration]
        Interfaces[Abstract Interfaces]
        Transport[MCP Protocol]
    end
    
    subgraph "Local MVP Layer"
        LocalServer[Local Server]
        LocalRouter[Local Router]
        LocalToolZoo[Local Tool Zoo]
        LocalSession[Local Session Manager]
    end
    
    subgraph "Cloud Layer"
        CloudServer[Cloud Server]
        CloudRouter[Cloud Router]
        CloudToolZoo[Cloud Tool Zoo]
        CloudSession[Cloud Session Manager]
        CloudAPI[REST API]
        CloudAuth[Auth Service]
    end
    
    LocalServer -->|implements| Interfaces
    LocalRouter -->|implements| Interfaces
    LocalToolZoo -->|implements| Interfaces
    LocalSession -->|implements| Interfaces
    
    CloudServer -->|implements| Interfaces
    CloudRouter -->|implements| Interfaces
    CloudToolZoo -->|implements| Interfaces
    CloudSession -->|implements| Interfaces
    CloudAPI -->|implements| Interfaces
    CloudAuth -->|implements| Interfaces
    
    LocalServer -->|uses| Models
    CloudServer -->|uses| Models
    LocalRouter -->|uses| Models
    CloudRouter -->|uses| Models
    
    LocalServer -->|uses| Config
    CloudServer -->|uses| Config
    
    LocalServer -->|uses| Transport
    CloudServer -->|uses| Transport
```

**Interface Boundaries:**
- **Router Interface:** [`route(session, query) -> RoutingDecision`](shared/src/ucp_core/interfaces.py)
- **ToolZoo Interface:** [`search(query, top_k) -> list[ToolSchema]`](shared/src/ucp_core/interfaces.py)
- **SessionManager Interface:** [`create_session(), get_session(), save_session()`](shared/src/ucp_core/interfaces.py)
- **Transport Interface:** [`connect(), call_tool(), disconnect()`](shared/src/ucp_transport/base_transport.py)

**Migration Path:**
1. Start with Local MVP (simple implementations)
2. Implement interfaces in shared layer
3. Local MVP implements interfaces
4. Cloud version implements same interfaces
5. Users can migrate by switching implementations
6. Data migration tools provided for transition

---

## 8. Deployment Strategy

### 8.1 Local MVP Deployment

**Installation Methods:**

1. **PyPI (Recommended)**
```bash
pip install ucp-mvp
ucp init-config
ucp serve
```

2. **Docker**
```bash
docker pull ucp/mvp:latest
docker run -v ~/.ucp:/data ucp/mvp
```

3. **From Source**
```bash
git clone https://github.com/your-org/UniversalContextProtocol
cd UniversalContextProtocol/local
pip install -e .
```

**Claude Desktop Integration:**
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

**Data Storage:**
- Configuration: `~/.ucp/ucp_config.yaml`
- Sessions: `~/.ucp/data/sessions.db`
- Tool Zoo: `~/.ucp/data/tool_zoo`
- Logs: `~/.ucp/logs/`

### 8.2 Cloud Version Deployment

**Infrastructure:**

1. **Kubernetes (Production)**
```bash
helm install ucp-cloud ./infrastructure/kubernetes/ucp-cloud
```

2. **Docker Compose (Development)**
```bash
cd infrastructure/docker
docker-compose up -d
```

3. **Terraform (Infrastructure as Code)**
```bash
cd infrastructure/terraform
terraform init
terraform apply
```

**Environment Variables:**
```bash
# Database
REDIS_URL=redis://redis-cluster:6379
QDRANT_URL=http://qdrant:6333
POSTGRES_URL=postgresql://user:pass@postgres:5432/ucp

# Storage
S3_BUCKET=ucp-data-lake
S3_REGION=us-east-1

# Auth
OAUTH_CLIENT_ID=xxx
OAUTH_CLIENT_SECRET=xxx
SSO_PROVIDER=okta

# Monitoring
PROMETHEUS_URL=http://prometheus:9090
GRAFANA_URL=http://grafana:3000
```

**Scaling:**
- Horizontal Pod Autoscaler for UCP servers
- Redis Cluster for session management
- Qdrant distributed cluster for vector search
- PostgreSQL read replicas for analytics

---

## 9. Risk Mitigation

### 9.1 Technical Risks

**Risk: Code duplication between versions**
- **Mitigation:** Shared interfaces and models in [`shared/`](shared/)
- **Fallback:** Regular code reviews to identify duplication

**Risk: MVP lacks features users want**
- **Mitigation:** Focus on core value (tool selection, privacy)
- **Fallback:** Gather feedback and iterate quickly

**Risk: Cloud version complexity causes delays**
- **Mitigation:** Start with MVP, add cloud features incrementally
- **Fallback:** Use managed services (AWS, GCP) to reduce complexity

**Risk: Migration from local to cloud is difficult**
- **Mitigation:** Design migration path from day one
- **Fallback:** Provide migration tools and documentation

### 9.2 Business Risks

**Risk: MVP doesn't generate revenue**
- **Mitigation:** MVP is open-source, builds community
- **Fallback:** Cloud version monetizes advanced features

**Risk: Cloud version faces competition**
- **Mitigation:** Focus on enterprise features and quality
- **Fallback:** Differentiate with privacy and compliance

**Risk: Team size insufficient for both versions**
- **Mitigation:** Prioritize MVP first, cloud second
- **Fallback:** Hire additional engineers as needed

---

## 10. Success Metrics

### 10.1 MVP Success Metrics

**Adoption:**
- 1,000+ PyPI downloads in first month
- 100+ GitHub stars
- 50+ active users (based on telemetry opt-in)

**Quality:**
- 95%+ routing precision (evaluation harness)
- <100ms average routing time
- 99%+ uptime (based on error logs)

**Engagement:**
- 10+ GitHub issues/PRs per month
- 5+ community contributors
- Positive feedback from early adopters

### 10.2 Cloud Success Metrics

**Revenue:**
- $10k MRR within 6 months
- 100+ paying customers
- $50k ARR within 12 months

**Adoption:**
- 1,000+ registered users
- 100+ enterprise customers
- 50%+ conversion from MVP to cloud

**Quality:**
- 99.9%+ uptime
- <50ms p95 latency
- 4.5+ star rating on app stores

---

## 11. Next Steps

### Immediate Actions (This Week)

1. **Review and Approve Plan**
   - [ ] Stakeholder review
   - [ ] Architecture review
   - [ ] Resource planning

2. **Setup Development Environment**
   - [ ] Create new repository structure
   - [ ] Set up CI/CD for MVP
   - [ ] Set up CI/CD for cloud

3. **Begin Migration**
   - [ ] Extract shared code
   - [ ] Archive original codebase
   - [ ] Create MVP implementations

### Short-Term Goals (Month 1)

- Complete repository reorganization
- Implement MVP core functionality
- Set up testing infrastructure
- Begin cloud infrastructure planning

### Long-Term Goals (Year 1)

- MVP v1.0 release
- MVP v1.2 release with advanced routing
- Cloud beta launch
- Cloud v1.0 release
- 100+ paying customers

---

## 12. Appendix

### 12.1 Glossary

- **MCP:** Model Context Protocol
- **UCP:** Universal Context Protocol
- **MVP:** Minimum Viable Product
- **SOTA:** State of the Art
- **RAFT:** Retrieval-Augmented Fine-Tuning
- **SaaS:** Software as a Service
- **SSO:** Single Sign-On
- **RBAC:** Role-Based Access Control
- **SCIM:** System for Cross-domain Identity Management

### 12.2 References

- [MCP Specification](https://modelcontextprotocol.io/)
- [Gorilla Paper](https://arxiv.org/abs/2305.15334)
- [RAFT Paper](https://arxiv.org/abs/2309.15217)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [ChromaDB](https://www.trychroma.com/)
- [Qdrant](https://qdrant.tech/)

### 12.3 Contact

**Project Lead:** [Name]  
**Email:** [email]  
**GitHub:** [repository]  
**Discord:** [server]

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-10  
**Status:** Draft for Review

