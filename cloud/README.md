# UCP Cloud Version

This directory contains the cloud version of UCP with full SOTA features and enterprise capabilities.

## Overview

The cloud version is designed for:
- **Scalability**: Horizontal scaling with Kubernetes
- **Multi-tenancy**: Isolated tenant environments
- **Enterprise-ready**: SSO, RBAC, compliance features
- **SOTA features**: Full routing pipeline, RAFT fine-tuning, LangGraph

## Status

**Note**: This is a future implementation. The cloud version is planned but not yet implemented.

See [`docs/roadmap.md`](docs/roadmap.md) for the implementation timeline.

## Structure

```
cloud/
├── README.md                     # This file
├── pyproject.toml               # Cloud package config
├── src/ucp_cloud/               # Cloud implementation
│   ├── __init__.py
│   ├── server.py                # Main cloud server
│   ├── router.py                # Advanced routing logic
│   ├── tool_zoo.py             # Distributed tool index
│   ├── session.py               # Session management
│   ├── connection_pool.py        # Downstream connections
│   ├── api/                    # REST API
│   │   ├── __init__.py
│   │   ├── routes.py            # API endpoints
│   │   ├── middleware.py        # Auth, rate limiting
│   │   └── schemas.py          # Request/response schemas
│   ├── auth/                   # Authentication & authorization
│   │   ├── __init__.py
│   │   ├── oauth.py             # OAuth2/OIDC
│   │   ├── saml.py              # SAML SSO
│   │   ├── rbac.py              # Role-based access control
│   │   └── scim.py              # SCIM provisioning
│   └── pipeline/                # Data pipelines
│       ├── __init__.py
│       ├── raft.py               # RAFT fine-tuning
│       ├── analytics.py          # Usage analytics
│       ├── training.py           # Model training
│       └── evaluation.py         # Model evaluation
├── tests/                      # Cloud-specific tests
├── docs/                       # Cloud documentation
│   ├── roadmap.md               # Implementation roadmap
│   ├── cloud_architecture.md    # Architecture overview
│   ├── cloud_deployment.md      # Deployment guide
│   └── cloud_api_reference.md   # API reference
├── infrastructure/              # Terraform, Kubernetes, Docker
│   ├── terraform/              # Infrastructure as Code
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── modules/
│   ├── kubernetes/             # K8s manifests
│   │   ├── base/
│   │   ├── overlays/
│   │   └── helm/
│   └── docker/                # Docker configurations
│       ├── Dockerfile
│       ├── docker-compose.yml
│       └── docker-compose.prod.yml
└── clients/                    # VS Code extension and web client
    ├── vscode/                 # VS Code extension
    └── web/                    # Web application
```

## Features

### Core Features
- Full SOTA routing pipeline
- Cross-encoder reranking
- Bandit-based exploration
- Online optimization
- RAFT fine-tuning
- LangGraph orchestration
- Centralized telemetry

### Storage
- **Sessions**: Redis cluster
- **Tool Zoo**: Qdrant/Weaviate vector store
- **Relational**: PostgreSQL
- **Data Lake**: S3/GCS
- **Analytics**: TimescaleDB

### SaaS Features
- OAuth2/OIDC authentication
- SSO (SAML)
- Role-based access control (RBAC)
- Multi-tenant isolation
- Billing and subscription management
- Usage-based pricing
- API keys and rate limiting
- Audit logging

### Enterprise Features
- SCIM provisioning
- Advanced RBAC
- Data residency options
- Compliance reporting
- Custom SLAs
- Dedicated support

## Deployment

### Kubernetes (Production)

```bash
# Install using Helm
helm install ucp-cloud ./infrastructure/kubernetes/helm/ucp-cloud

# Or using kubectl
kubectl apply -f infrastructure/kubernetes/base/
```

### Docker Compose (Development)

```bash
cd infrastructure/docker
docker-compose up -d
```

### Terraform (Infrastructure as Code)

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## Development

### Setup Development Environment

```bash
cd cloud
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v
```

### Type Checking

```bash
mypy src/ucp_cloud/
```

### Linting

```bash
ruff check src/ucp_cloud/
```

## Documentation

- [Roadmap](docs/roadmap.md) - Implementation roadmap
- [Architecture](docs/cloud_architecture.md) - Architecture overview
- [Deployment](docs/cloud_deployment.md) - Deployment guide
- [API Reference](docs/cloud_api_reference.md) - API reference

## Architecture Overview

### Cloud Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Load Balancer (ALB/NLB)                │
└────────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────▼────────┐    ┌────────▼────────┐
│  UCP Gateway 1  │    │  UCP Gateway 2  │
│  (Pod/Node)    │    │  (Pod/Node)    │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐    ┌────▼─────┐    ┌───▼──────┐
│ Redis  │    │ PostgreSQL│    │  Qdrant   │
│Cluster │    │  Primary │    │  Vector   │
└────────┘    └────┬─────┘    └───────────┘
                   │
            ┌──────▼──────┐
            │ PostgreSQL  │
            │  Replica   │
            └─────────────┘
```

### Multi-Tenant Architecture

Each tenant has:
- Isolated database schema
- Separate Redis namespace
- Dedicated tool zoo collection
- Isolated API keys
- Independent usage tracking

## API Reference

### Authentication

```bash
# OAuth2 flow
POST /api/v1/auth/oauth/token
POST /api/v1/auth/oauth/refresh

# SAML SSO
POST /api/v1/auth/saml/sso
POST /api/v1/auth/saml/acs

# API keys
POST /api/v1/auth/api-keys
GET /api/v1/auth/api-keys
DELETE /api/v1/auth/api-keys/:id
```

### Tools

```bash
# List tools (context-aware)
GET /api/v1/tools?session_id=xxx&context=send+email

# Call tool
POST /api/v1/tools/call
{
  "name": "gmail.send_email",
  "arguments": {"to": "...", "subject": "...", "body": "..."}
}

# Search tools
GET /api/v1/tools/search?query=send+email&top_k=5
```

### Sessions

```bash
# Create session
POST /api/v1/sessions

# Get session
GET /api/v1/sessions/:id

# Update context
POST /api/v1/sessions/:id/context
{
  "message": "I need to send an email",
  "role": "user"
}

# Get session history
GET /api/v1/sessions/:id/history
```

### Analytics

```bash
# Get usage stats
GET /api/v1/analytics/usage?start_date=2024-01-01&end_date=2024-01-31

# Get tool usage
GET /api/v1/analytics/tools?top_k=10

# Get router performance
GET /api/v1/analytics/router/performance
```

## Pricing

### Plans

- **Starter**: $29/month - Up to 100 tools, 10K sessions/month
- **Professional**: $99/month - Up to 500 tools, 100K sessions/month
- **Enterprise**: Custom - Unlimited tools, dedicated support

### Usage-Based Pricing

- Additional sessions: $0.001 per session
- Additional tools: $0.10 per tool/month
- RAFT fine-tuning: $0.50 per training run

## Security

### Data Protection
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Data residency options (EU, US, APAC)
- GDPR compliance
- SOC 2 Type II certified

### Access Control
- OAuth2/OIDC
- SAML SSO
- SCIM provisioning
- RBAC with fine-grained permissions
- API key management
- Audit logging

## Monitoring & Observability

### Metrics
- Request latency
- Tool selection accuracy
- Router performance
- System resources
- Error rates

### Logging
- Structured JSON logs
- Centralized log aggregation
- Log retention (90 days)
- Audit logs (365 days)

### Tracing
- Distributed tracing (OpenTelemetry)
- Request correlation
- Performance profiling
- Error tracking

## Contributing

Contributions welcome! Please read the main repository's [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) for guidelines.

## License

MIT License

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the complete implementation timeline.

This directory contains the cloud version of UCP with full SOTA features and enterprise capabilities.

## Overview

The cloud version is designed for:
- **Scalability**: Horizontal scaling with Kubernetes
- **Multi-tenancy**: Isolated tenant environments
- **Enterprise-ready**: SSO, RBAC, compliance features
- **SOTA features**: Full routing pipeline, RAFT fine-tuning, LangGraph

## Status

**Note**: This is a future implementation. The cloud version is planned but not yet implemented.

See [`docs/roadmap.md`](docs/roadmap.md) for the implementation timeline.

## Structure

```
cloud/
├── README.md                     # This file
├── pyproject.toml               # Cloud package config
├── src/ucp_cloud/               # Cloud implementation
│   ├── __init__.py
│   ├── server.py                # Main cloud server
│   ├── router.py                # Advanced routing logic
│   ├── tool_zoo.py             # Distributed tool index
│   ├── session.py               # Session management
│   ├── connection_pool.py        # Downstream connections
│   ├── api/                    # REST API
│   │   ├── __init__.py
│   │   ├── routes.py            # API endpoints
│   │   ├── middleware.py        # Auth, rate limiting
│   │   └── schemas.py          # Request/response schemas
│   ├── auth/                   # Authentication & authorization
│   │   ├── __init__.py
│   │   ├── oauth.py             # OAuth2/OIDC
│   │   ├── saml.py              # SAML SSO
│   │   ├── rbac.py              # Role-based access control
│   │   └── scim.py              # SCIM provisioning
│   └── pipeline/                # Data pipelines
│       ├── __init__.py
│       ├── raft.py               # RAFT fine-tuning
│       ├── analytics.py          # Usage analytics
│       ├── training.py           # Model training
│       └── evaluation.py         # Model evaluation
├── tests/                      # Cloud-specific tests
├── docs/                       # Cloud documentation
│   ├── roadmap.md               # Implementation roadmap
│   ├── cloud_architecture.md    # Architecture overview
│   ├── cloud_deployment.md      # Deployment guide
│   └── cloud_api_reference.md   # API reference
├── infrastructure/              # Terraform, Kubernetes, Docker
│   ├── terraform/              # Infrastructure as Code
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── modules/
│   ├── kubernetes/             # K8s manifests
│   │   ├── base/
│   │   ├── overlays/
│   │   └── helm/
│   └── docker/                # Docker configurations
│       ├── Dockerfile
│       ├── docker-compose.yml
│       └── docker-compose.prod.yml
└── clients/                    # VS Code extension and web client
    ├── vscode/                 # VS Code extension
    └── web/                    # Web application
```

## Features

### Core Features
- Full SOTA routing pipeline
- Cross-encoder reranking
- Bandit-based exploration
- Online optimization
- RAFT fine-tuning
- LangGraph orchestration
- Centralized telemetry

### Storage
- **Sessions**: Redis cluster
- **Tool Zoo**: Qdrant/Weaviate vector store
- **Relational**: PostgreSQL
- **Data Lake**: S3/GCS
- **Analytics**: TimescaleDB

### SaaS Features
- OAuth2/OIDC authentication
- SSO (SAML)
- Role-based access control (RBAC)
- Multi-tenant isolation
- Billing and subscription management
- Usage-based pricing
- API keys and rate limiting
- Audit logging

### Enterprise Features
- SCIM provisioning
- Advanced RBAC
- Data residency options
- Compliance reporting
- Custom SLAs
- Dedicated support

## Deployment

### Kubernetes (Production)

```bash
# Install using Helm
helm install ucp-cloud ./infrastructure/kubernetes/helm/ucp-cloud

# Or using kubectl
kubectl apply -f infrastructure/kubernetes/base/
```

### Docker Compose (Development)

```bash
cd infrastructure/docker
docker-compose up -d
```

### Terraform (Infrastructure as Code)

```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

## Development

### Setup Development Environment

```bash
cd cloud
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v
```

### Type Checking

```bash
mypy src/ucp_cloud/
```

### Linting

```bash
ruff check src/ucp_cloud/
```

## Documentation

- [Roadmap](docs/roadmap.md) - Implementation roadmap
- [Architecture](docs/cloud_architecture.md) - Architecture overview
- [Deployment](docs/cloud_deployment.md) - Deployment guide
- [API Reference](docs/cloud_api_reference.md) - API reference

## Architecture Overview

### Cloud Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Load Balancer (ALB/NLB)                │
└────────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────▼────────┐    ┌────────▼────────┐
│  UCP Gateway 1  │    │  UCP Gateway 2  │
│  (Pod/Node)    │    │  (Pod/Node)    │
└────────┬─────────┘    └────────┬─────────┘
         │                       │
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼────┐    ┌────▼─────┐    ┌───▼──────┐
│ Redis  │    │ PostgreSQL│    │  Qdrant   │
│Cluster │    │  Primary │    │  Vector   │
└────────┘    └────┬─────┘    └───────────┘
                   │
            ┌──────▼──────┐
            │ PostgreSQL  │
            │  Replica   │
            └─────────────┘
```

### Multi-Tenant Architecture

Each tenant has:
- Isolated database schema
- Separate Redis namespace
- Dedicated tool zoo collection
- Isolated API keys
- Independent usage tracking

## API Reference

### Authentication

```bash
# OAuth2 flow
POST /api/v1/auth/oauth/token
POST /api/v1/auth/oauth/refresh

# SAML SSO
POST /api/v1/auth/saml/sso
POST /api/v1/auth/saml/acs

# API keys
POST /api/v1/auth/api-keys
GET /api/v1/auth/api-keys
DELETE /api/v1/auth/api-keys/:id
```

### Tools

```bash
# List tools (context-aware)
GET /api/v1/tools?session_id=xxx&context=send+email

# Call tool
POST /api/v1/tools/call
{
  "name": "gmail.send_email",
  "arguments": {"to": "...", "subject": "...", "body": "..."}
}

# Search tools
GET /api/v1/tools/search?query=send+email&top_k=5
```

### Sessions

```bash
# Create session
POST /api/v1/sessions

# Get session
GET /api/v1/sessions/:id

# Update context
POST /api/v1/sessions/:id/context
{
  "message": "I need to send an email",
  "role": "user"
}

# Get session history
GET /api/v1/sessions/:id/history
```

### Analytics

```bash
# Get usage stats
GET /api/v1/analytics/usage?start_date=2024-01-01&end_date=2024-01-31

# Get tool usage
GET /api/v1/analytics/tools?top_k=10

# Get router performance
GET /api/v1/analytics/router/performance
```

## Pricing

### Plans

- **Starter**: $29/month - Up to 100 tools, 10K sessions/month
- **Professional**: $99/month - Up to 500 tools, 100K sessions/month
- **Enterprise**: Custom - Unlimited tools, dedicated support

### Usage-Based Pricing

- Additional sessions: $0.001 per session
- Additional tools: $0.10 per tool/month
- RAFT fine-tuning: $0.50 per training run

## Security

### Data Protection
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)
- Data residency options (EU, US, APAC)
- GDPR compliance
- SOC 2 Type II certified

### Access Control
- OAuth2/OIDC
- SAML SSO
- SCIM provisioning
- RBAC with fine-grained permissions
- API key management
- Audit logging

## Monitoring & Observability

### Metrics
- Request latency
- Tool selection accuracy
- Router performance
- System resources
- Error rates

### Logging
- Structured JSON logs
- Centralized log aggregation
- Log retention (90 days)
- Audit logs (365 days)

### Tracing
- Distributed tracing (OpenTelemetry)
- Request correlation
- Performance profiling
- Error tracking

## Contributing

Contributions welcome! Please read the main repository's [DEVELOPMENT_GUIDE.md](../DEVELOPMENT_GUIDE.md) for guidelines.

## License

MIT License

## Roadmap

See [docs/roadmap.md](docs/roadmap.md) for the complete implementation timeline.

