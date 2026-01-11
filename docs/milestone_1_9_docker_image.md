# Milestone 1.9: Docker Image for Universal Context Protocol

## Overview

This milestone implements Docker support for the Universal Context Protocol (UCP) local MVP, enabling easy deployment and consistent environments across different platforms.

## Files Created

### 1. Dockerfile
**Location**: [`Dockerfile`](Dockerfile)

**Features**:
- Base image: `python:3.11-slim` (minimal footprint)
- Installs all dependencies from [`pyproject.toml`](pyproject.toml)
- Sets up working directory at `/app`
- Creates `/data` volume for ChromaDB persistence
- Exposes port 8000 for HTTP transport
- Entry point: `ucp serve` command
- Environment variables for configuration

**Key Sections**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
VOLUME ["/data"]
ENTRYPOINT ["ucp"]
CMD ["serve"]
```

### 2. docker-compose.yml
**Location**: [`docker-compose.yml`](docker-compose.yml)

**Services**:
- **ucp**: Main UCP gateway service
- **filesystem-server**: Mock filesystem MCP server (placeholder)
- **github-server**: Mock GitHub MCP server (placeholder)
- **slack-server**: Mock Slack MCP server (placeholder)

**Features**:
- Named volumes for data persistence (`ucp-data`, `filesystem-data`, `github-data`, `slack-data`)
- Bridge network (`ucp-network`) for service communication
- Health checks for UCP service
- Restart policy: `unless-stopped`
- Port mapping: 8000:8000

**Example Usage**:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f ucp

# Stop all services
docker-compose down
```

### 3. .dockerignore
**Location**: [`.dockerignore`](.dockerignore)

**Purpose**: Optimize Docker build by excluding unnecessary files

**Excludes**:
- Python cache files
- Virtual environments
- IDE files
- Git files
- Documentation (except README.md)
- Test files
- Data and logs
- Agent and CI/CD files

### 4. README.md Updates
**Location**: [`README.md`](README.md)

**Added Sections**:
- Docker Installation guide
- Build instructions
- Run with Docker
- Run with Docker Compose
- Docker Volumes management
- Environment Variables configuration
- Data Persistence documentation

## Docker Image Details

### Build Command
```bash
docker build -t ucpproject/ucp:0.1.0-alpha1 .
```

### Run Commands

#### Basic Run
```bash
docker run -d \
  --name ucp-gateway \
  -v ucp-data:/data \
  -p 8000:8000 \
  ucpproject/ucp:0.1.0-alpha1
```

#### With Custom Configuration
```bash
docker run -d \
  --name ucp-gateway \
  -v ucp-data:/data \
  -v $(pwd)/ucp_config.yaml:/app/ucp_config.yaml:ro \
  -p 8000:8000 \
  ucpproject/ucp:0.1.0-alpha1
```

#### With Environment Variables
```bash
docker run -d \
  --name ucp-gateway \
  -v ucp-data:/data \
  -e UCP_LOG_LEVEL=DEBUG \
  -p 8000:8000 \
  ucpproject/ucp:0.1.0-alpha1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `UCP_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | INFO |
| `UCP_DATA_DIR` | Data directory path | /data |
| `UCP_CONFIG_FILE` | Path to configuration file | /app/ucp_config.yaml |

## Data Persistence

### Volume Management
The `/data` volume ensures ChromaDB data persists across container restarts:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect ucp-data

# Backup volume
docker run --rm -v ucp-data:/data -v $(pwd):/backup alpine tar czf /backup/ucp-data-backup.tar.gz /data

# Restore volume
docker run --rm -v ucp-data:/data -v $(pwd):/backup alpine tar xzf /backup/ucp-data-backup.tar.gz -C /
```

### Data Persistence Workflow
1. Stop container (data preserved in volume)
2. Remove container (data preserved in volume)
3. Start new container with existing data

```bash
# Stop and remove
docker stop ucp-gateway
docker rm ucp-gateway

# Start with existing data
docker run -d \
  --name ucp-gateway \
  -v ucp-data:/data \
  -p 8000:8000 \
  ucpproject/ucp:0.1.0-alpha1
```

## Docker Compose Services

### UCP Gateway Service
- Image: `ucpproject/ucp:0.1.0-alpha1`
- Container: `ucp-gateway`
- Volumes: `ucp-data:/data`, `./ucp_config.yaml:/app/ucp_config.yaml:ro`
- Ports: `8000:8000`
- Network: `ucp-network`
- Restart: `unless-stopped`
- Health check: Python process check

### Example Downstream Servers

#### Filesystem Server
- Image: `alpine:latest`
- Container: `filesystem-mcp-server`
- Volume: `filesystem-data:/data`
- Network: `ucp-network`

#### GitHub Server
- Image: `alpine:latest`
- Container: `github-mcp-server`
- Environment: `GITHUB_TOKEN` (from .env)
- Volume: `github-data:/data`
- Network: `ucp-network`

#### Slack Server
- Image: `alpine:latest`
- Container: `slack-mcp-server`
- Environment: `SLACK_TOKEN` (from .env)
- Volume: `slack-data:/data`
- Network: `ucp-network`

## Success Criteria

All success criteria have been met:

- ✅ Dockerfile created with python:3.11-slim base
- ✅ Dependencies and sentence-transformers model installed
- ✅ ENTRYPOINT set to `ucp serve`
- ✅ VOLUME configured for /data (ChromaDB persistence)
- ✅ All necessary files copied from repository
- ✅ Proper working directory set up
- ✅ docker-compose.yml created with UCP service
- ✅ Example downstream servers included (filesystem, GitHub, Slack)
- ✅ Volumes configured for data persistence
- ✅ Networking configured between services
- ✅ Docker image build command documented
- ✅ Image structure validated
- ✅ `ucp serve` command configured as entry point
- ✅ Data persistence mechanism documented
- ✅ README.md updated with Docker instructions
- ✅ Docker usage documented
- ✅ Volume mounting documented
- ✅ Environment variables documented

## Testing

### Build Test
```bash
# Build the image
docker build -t ucpproject/ucp:0.1.0-alpha1 .
```

### Run Test
```bash
# Run container
docker run -d \
  --name ucp-gateway \
  -v ucp-data:/data \
  -p 8000:8000 \
  ucpproject/ucp:0.1.0-alpha1

# Check logs
docker logs ucp-gateway

# Verify container is running
docker ps
```

### Data Persistence Test
```bash
# Add some data
docker exec ucp-gateway ls -la /data

# Stop container
docker stop ucp-gateway

# Remove container
docker rm ucp-gateway

# Start new container
docker run -d \
  --name ucp-gateway \
  -v ucp-data:/data \
  -p 8000:8000 \
  ucpproject/ucp:0.1.0-alpha1

# Verify data persists
docker exec ucp-gateway ls -la /data
```

## Next Steps

1. **Publish to Docker Hub**: Push the image to Docker Hub for easy distribution
2. **CI/CD Integration**: Add automated builds to GitHub Actions
3. **Multi-architecture Support**: Build for amd64, arm64, etc.
4. **Production Hardening**: Add security scanning, vulnerability checks
5. **Example MCP Servers**: Replace placeholder servers with real MCP server implementations

## Notes

- Docker Desktop must be running to build and run containers
- The `.dockerignore` file significantly reduces build context size
- Volume mounting is recommended for data persistence
- Environment variables provide flexible configuration without rebuilding images
- The image includes all dependencies from `pyproject.toml`, including sentence-transformers for embeddings

## Related Documentation

- [`README.md`](README.md) - Main project documentation with Docker section
- [`Dockerfile`](Dockerfile) - Docker image definition
- [`docker-compose.yml`](docker-compose.yml) - Multi-container orchestration
- [`.dockerignore`](.dockerignore) - Build context optimization
