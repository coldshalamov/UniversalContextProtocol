# Production Deployment Guide for UCP Local MVP

This guide covers deploying UCP in a production environment, including resource requirements, security considerations, and scaling strategies.

## Table of Contents

- [Resource Requirements](#resource-requirements)
- [Security Considerations](#security-considerations)
- [Scaling Strategies](#scaling-strategies)
- [Deployment Steps](#deployment-steps)
- [Monitoring and Observability](#monitoring-and-observability)
- [Troubleshooting Production Issues](#troubleshooting-production-issues)

## Resource Requirements

### Minimum Requirements

For small-scale deployments (1-5 concurrent users, 10-50 tools):

| Resource | Minimum | Recommended | Notes |
|---|---|---|---|
| CPU | 2 cores | 4 cores | Embedding generation is CPU-intensive |
| RAM | 4 GB | 8 GB | ChromaDB in-memory operations |
| Disk | 10 GB | 20 GB | Vector embeddings grow over time |
| Network | 100 Mbps | 1 Gbps | For downstream server communication |

### Resource Breakdown by Component

#### ChromaDB (Tool Zoo)
- **RAM**: 500 MB base + 10-50 MB per 100 tools
- **Disk**: 5-50 MB per 1000 tools (including embeddings)
- **CPU**: Minimal for queries, moderate during indexing

#### Embedding Generation
- **CPU**: Single-threaded, CPU-intensive
- **RAM**: 100-500 MB per embedding operation
- **Model Size**: `all-MiniLM-L6-v2` ~ 80 MB

#### Session Management (SQLite)
- **RAM**: 10-50 MB base + 1-5 MB per active session
- **Disk**: 1-10 MB per 1000 sessions

#### HTTP Server (if using HTTP transport)
- **RAM**: 50-200 MB base + 10-50 MB per 100 concurrent connections
- **CPU**: Low per request, scales with concurrency

### Scaling Resource Requirements

| Tools | Users | CPU | RAM | Disk |
|---|---|---|---|
| 50 | 1-5 | 4 GB | 10 GB |
| 100 | 5-10 | 8 GB | 20 GB |
| 500 | 10-20 | 16 GB | 50 GB |
| 1000 | 20-40 | 32 GB | 100 GB |

## Security Considerations

### Tool Execution Sandboxing

UCP routes tool calls to downstream MCP servers. While UCP itself doesn't execute arbitrary code, it's important to secure the downstream connections.

#### Recommended Practices

1. **Isolate Downstream Servers**
   ```yaml
   downstream_servers:
     - name: github
       # Use dedicated service account
       env:
         GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
       # Limit to read-only operations where possible
       tags: [code, git, read-only]
   ```

2. **Network Isolation**
   - Run UCP in a dedicated network segment
   - Use firewall rules to restrict outbound connections
   - Implement rate limiting on downstream server access

3. **Environment Variable Security**
   ```bash
   # Use secrets management (never hardcode tokens)
   export GITHUB_TOKEN=$(vault get -field=token secret/github)
   export SLACK_TOKEN=$(vault get -field=token secret/slack)
   
   # Start UCP with secure environment
   ucp serve -c production_config.yaml
   ```

4. **Filesystem Access Control**
   - When using filesystem MCP server, restrict to specific directories
   - Use read-only mounts where possible
   - Implement file type whitelisting

### Data Protection

#### Sensitive Data in Logs

UCP logs may contain:
- Tool names and parameters
- Conversation context snippets
- Error messages with potential data

**Mitigation:**
```yaml
server:
  log_level: WARNING  # Avoid logging DEBUG in production
  # Configure log sanitization
  sanitize_logs: true
```

#### Session Data

- Sessions stored in SQLite database
- Contains conversation history and tool usage patterns
- **Recommendation**: Encrypt session database at rest

```bash
# Encrypt SQLite database
sqlite3 ~/.ucp/data/sessions.db ".dump" | \
  gpg --encrypt --recipient admin@company.com > sessions.db.enc
```

### Authentication and Authorization

#### Claude Desktop Integration

For multi-user environments:

1. **Per-User Configuration**
   ```bash
   # Each user has their own config
   /home/user1/.ucp/ucp_config.yaml
   /home/user2/.ucp/ucp_config.yaml
   ```

2. **Service Account Isolation**
   - Use separate service accounts for different users/departments
   - Implement principle of least privilege
   - Rotate tokens regularly

#### HTTP API Authentication

If using HTTP transport:

```yaml
server:
  transport: http
  port: 8765
  # Enable authentication
  auth:
    enabled: true
    provider: jwt  # or oauth2, apikey
    secret: "${JWT_SECRET}"
    # Rate limiting
    rate_limit:
      requests_per_minute: 100
      burst: 20
```

### Network Security

#### TLS/SSL Configuration

```yaml
server:
  transport: http
  ssl:
    enabled: true
    cert_path: /etc/ucp/ssl/cert.pem
    key_path: /etc/ucp/ssl/key.pem
    # Enforce strong ciphers
    min_tls_version: "1.2"
    ciphers: "HIGH:!aNULL:!MD5"
```

#### Firewall Rules

```bash
# Allow inbound to UCP
ufw allow 8765/tcp  # UCP HTTP port

# Restrict outbound to known MCP servers
ufw allow out to api.github.com 443/tcp
ufw allow out to slack.com 443/tcp
```

## Scaling Strategies

### Vertical Scaling (Single Instance)

#### When to Use
- Small teams (1-10 users)
- Development/testing environments
- Low tool count (< 100)

#### Optimization

1. **Increase CPU Resources**
   - More cores = faster embedding generation
   - Consider CPU with AVX-512 support for embeddings

2. **Increase RAM**
   - Larger ChromaDB cache = faster queries
   - More concurrent sessions

3. **Use SSD Storage**
   - Faster vector database operations
   - Quicker session database access

### Horizontal Scaling (Multiple Instances)

#### When to Use
- Large teams (10+ users)
- High tool count (100+)
- High availability requirements

#### Load Balancing

```
                    [Load Balancer]
                           /      |      \
                      [UCP 1]  [UCP 2]  [UCP 3]
                           |      |      |
                      [ChromaDB] [ChromaDB] [ChromaDB]
```

**Implementation:**

1. **Session Affinity**
   ```yaml
   # Use sticky sessions for same user
   session:
     backend: redis  # Shared session store
     affinity: true
   ```

2. **Shared Tool Zoo**
   - All UCP instances connect to same ChromaDB
   - Use ChromaDB server mode (not embedded)
   - Configure connection pooling

3. **Redis Session Backend**

```yaml
session:
  backend: redis
  redis:
    host: redis.internal
    port: 6379
    db: 0
    # Connection pooling
    pool_size: 20
    max_connections: 50
    # Persistence
    save_interval: 60  # seconds
```

**Benefits:**
- Stateless UCP instances
- Easy horizontal scaling
- Session continuity across restarts

### Database Scaling

#### ChromaDB Scaling

**Small Scale (< 1000 tools):**
- Embedded ChromaDB (default)
- Single SQLite backend

**Medium Scale (1000-10000 tools):**
- ChromaDB server mode
- Dedicated PostgreSQL backend

**Large Scale (> 10000 tools):**
- Distributed ChromaDB
- Shard by tool category/domain
- Consider specialized vector database (Pinecone, Weaviate)

#### Configuration for ChromaDB Server

```yaml
tool_zoo:
  persist_dir: "~/.ucp/data/tool_zoo"
  # Use ChromaDB server instead of embedded
  chromadb_server:
    host: chromadb.internal
    port: 8000
    # Connection settings
    pool_size: 10
    timeout: 30
    # Authentication
    auth_token: "${CHROMADB_TOKEN}"
```

### Caching Strategies

#### Embedding Cache

```yaml
tool_zoo:
  # Cache generated embeddings
  cache_embeddings: true
  cache_dir: "~/.ucp/cache/embeddings"
  cache_ttl: 86400  # 24 hours in seconds
```

#### Tool Selection Cache

```yaml
router:
  # Cache recent tool selections
  cache:
    enabled: true
    max_size: 1000
    ttl: 3600  # 1 hour
```

### Geographic Distribution

For global deployments:

1. **Regional UCP Instances**
   - Deploy UCP closer to users
   - Reduce latency for tool selection

2. **Regional Downstream Servers**
   - Connect to regional MCP endpoints
   - Cache responses locally

3. **CDN for Static Assets**
   - Serve embeddings via CDN
   - Cache tool schemas

## Deployment Steps

### Step 1: Environment Preparation

```bash
# 1. Create dedicated user
sudo useradd -r -s /bin/bash ucp
sudo mkdir -p /opt/ucp
sudo chown ucp:ucp /opt/ucp

# 2. Install dependencies
sudo apt update
sudo apt install -y python3.10 python3.10-venv sqlite3

# 3. Create virtual environment
sudo -u ucp python3.10 -m venv /opt/ucp/venv
source /opt/ucp/venv/bin/activate

# 4. Install UCP
pip install ucp-mvp
```

### Step 2: Configuration

```bash
# 1. Generate production config
ucp init-config -o /opt/ucp/ucp_config.yaml

# 2. Edit for production
vi /opt/ucp/ucp_config.yaml
```

**Production Configuration Template:**

```yaml
server:
  name: "UCP Production Gateway"
  transport: http  # or stdio for Claude Desktop
  host: "0.0.0.0"
  port: 8765
  log_level: WARNING
  # SSL configuration
  ssl:
    enabled: true
    cert_path: "/etc/ucp/ssl/cert.pem"
    key_path: "/etc/ucp/ssl/key.pem"

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5
  similarity_threshold: 0.7
  persist_dir: "/opt/ucp/data/tool_zoo"
  # ChromaDB server for scaling
  chromadb_server:
    host: "chromadb.internal"
    port: 8000
  # Caching
  cache_embeddings: true
  cache_dir: "/opt/ucp/cache/embeddings"

router:
  mode: hybrid
  max_tools: 10
  enable_co_occurrence: true
  enable_learning: true
  # Caching
  cache:
    enabled: true
    max_size: 1000
    ttl: 3600

session:
  # Redis for horizontal scaling
  backend: redis
  redis:
    host: "redis.internal"
    port: 6379
    db: 0
    pool_size: 20
  persist_dir: "/opt/ucp/data/sessions.db"
  max_history: 100

downstream_servers:
  # Use environment variables for secrets
  - name: github
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
    tags: [code, git]

  - name: slack
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-slack"]
    env:
      SLACK_BOT_TOKEN: "${SLACK_TOKEN}"
      SLACK_APP_TOKEN: "${SLACK_APP_TOKEN}"
    tags: [communication, team]
```

### Step 3: SSL Certificate Setup

```bash
# 1. Create SSL directory
sudo mkdir -p /etc/ucp/ssl
sudo chown ucp:ucp /etc/ucp/ssl

# 2. Generate self-signed certificate (for testing)
sudo -u ucp openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout /etc/ucp/ssl/key.pem \
  -out /etc/ucp/ssl/cert.pem

# 3. Or use Let's Encrypt for production
sudo certbot certonly --standalone \
  -d ucp.yourdomain.com \
  --email admin@yourdomain.com
sudo cp /etc/letsencrypt/live/ucp.yourdomain.com/fullchain.pem \
  /etc/ucp/ssl/cert.pem
sudo cp /etc/letsencrypt/live/ucp.yourdomain.com/privkey.pem \
  /etc/ucp/ssl/key.pem
```

### Step 4: Systemd Service

```bash
# 1. Create systemd service file
sudo vi /etc/systemd/system/ucp.service
```

**Service File:**

```ini
[Unit]
Description=UCP Gateway Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=ucp
Group=ucp
WorkingDirectory=/opt/ucp
Environment="PATH=/opt/ucp/venv/bin"
EnvironmentFile=/opt/ucp/.env
ExecStart=/opt/ucp/venv/bin/ucp serve -c /opt/ucp/ucp_config.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 2. Create environment file
sudo -u ucp vi /opt/ucp/.env
```

**Environment File:**

```bash
# Secrets (loaded from vault or key management)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxx
SLACK_TOKEN=xoxb-xxxxxxxxxxxx
SLACK_APP_TOKEN=xapp-xxxxxxxxxxxx

# Database credentials
REDIS_PASSWORD=xxxxxxxx
CHROMADB_TOKEN=xxxxxxxx

# JWT secret (if using HTTP auth)
JWT_SECRET=your-super-secret-key-here
```

```bash
# 3. Set permissions
sudo chmod 600 /opt/ucp/.env
sudo chown ucp:ucp /opt/ucp/.env

# 4. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ucp
sudo systemctl start ucp

# 5. Check status
sudo systemctl status ucp
sudo journalctl -u ucp -f
```

### Step 5: Nginx Reverse Proxy (Optional)

```bash
# 1. Install Nginx
sudo apt install -y nginx

# 2. Configure reverse proxy
sudo vi /etc/nginx/sites-available/ucp
```

**Nginx Configuration:**

```nginx
upstream ucp_backend {
    server 127.0.0.1:8765;
    # Add more instances for load balancing
    # server 127.0.0.1:8766;
    # server 127.0.0.1:8767;
}

server {
    listen 80;
    server_name ucp.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ucp.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/ucp/ssl/cert.pem;
    ssl_certificate_key /etc/ucp/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";

    # Proxy settings
    location / {
        proxy_pass http://ucp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://ucp_backend/health;
        access_log off;
    }
}
```

```bash
# 3. Enable site
sudo ln -s /etc/nginx/sites-available/ucp /etc/nginx/sites-enabled/

# 4. Test and restart
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Firewall Configuration

```bash
# 1. Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8765/tcp  # UCP direct (optional)
sudo ufw enable

# 2. Verify
sudo ufw status
```

## Monitoring and Observability

### Health Checks

```bash
# UCP provides health endpoint
curl http://localhost:8765/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "components": {
    "tool_zoo": "healthy",
    "router": "healthy",
    "session_manager": "healthy",
    "downstream_servers": {
      "github": "connected",
      "slack": "connected"
    }
  },
  "metrics": {
    "tools_indexed": 150,
    "active_sessions": 5,
    "uptime_seconds": 86400
  }
}
```

### Metrics Collection

#### Prometheus Integration

```yaml
server:
  metrics:
    enabled: true
    port: 9090
    path: /metrics
```

**Available Metrics:**

```
# Tool selection metrics
ucp_router_selection_duration_seconds{quantile="0.5"} 0.025
ucp_router_selection_duration_seconds{quantile="0.95"} 0.050
ucp_router_selection_duration_seconds{quantile="0.99"} 0.100

# Tool zoo metrics
ucp_tool_zoo_query_duration_seconds 0.010
ucp_tool_zoo_tools_total 150
ucp_tool_zoo_cache_hits_total 1200
ucp_tool_zoo_cache_misses_total 300

# Session metrics
ucp_session_active_total 5
ucp_session_created_total 1000
ucp_session_duration_seconds{quantile="0.5"} 300

# Downstream server metrics
ucp_downstream_requests_total{server="github"} 500
ucp_downstream_errors_total{server="github"} 5
ucp_downstream_latency_seconds{server="github"} 0.100
```

#### Grafana Dashboard

Create dashboard with panels for:
1. **Request Rate**: Requests per minute
2. **Latency**: P50, P95, P99 latencies
3. **Error Rate**: Failed requests percentage
4. **Resource Usage**: CPU, RAM, Disk
5. **Tool Zoo**: Indexed tools, cache hit rate
6. **Sessions**: Active sessions, average duration

### Logging

#### Log Rotation

```bash
# 1. Create logrotate config
sudo vi /etc/logrotate.d/ucp
```

**Logrotate Configuration:**

```
/opt/ucp/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ucp ucp
    sharedscripts
        postrotate
            systemctl reload ucp > /dev/null || true
        endscript
}
```

#### Structured Logging

```yaml
server:
  log_level: INFO
  log_format: json  # or text
  log_output:
    - file:/opt/ucp/logs/ucp.log
    - stdout
```

**JSON Log Format:**
```json
{
  "timestamp": "2025-01-11T04:00:00Z",
  "level": "INFO",
  "component": "router",
  "message": "Selected 3 tools for session abc123",
  "context": {
    "session_id": "abc123",
    "tools_selected": ["gmail.send_email", "github.create_pr"],
    "selection_duration_ms": 25.99
  }
}
```

### Alerting

#### Critical Alerts

1. **UCP Service Down**
   - Trigger: Service not responding for 30 seconds
   - Action: Restart service, notify team

2. **High Error Rate**
   - Trigger: Error rate > 5% for 5 minutes
   - Action: Check logs, investigate downstream servers

3. **High Latency**
   - Trigger: P95 latency > 100ms for 5 minutes
   - Action: Check resource usage, scale if needed

4. **Downstream Server Disconnected**
   - Trigger: Any downstream server disconnected
   - Action: Check server status, restart if needed

#### Alert Configuration (Prometheus Alertmanager)

```yaml
groups:
  - name: ucp_alerts
    rules:
      - alert: UCPServiceDown
        expr: up{job="ucp"} == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "UCP service is down"
          description: "UCP has been down for 30 seconds"

      - alert: UCPHighErrorRate
        expr: |
          rate(ucp_router_errors_total[5m]) / 
          rate(ucp_router_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5%"

      - alert: UCPHighLatency
        expr: |
          histogram_quantile(0.95, 
            rate(ucp_router_selection_duration_seconds_bucket[5m])
          ) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is above 100ms"
```

## Troubleshooting Production Issues

### High Memory Usage

**Symptoms:**
- OOM (Out of Memory) errors
- System swapping
- Slow performance

**Diagnosis:**
```bash
# Check memory usage
free -h
ps aux | grep ucp

# Check ChromaDB memory
sqlite3 ~/.ucp/data/tool_zoo/chroma.sqlite3 ".tables"
```

**Solutions:**
1. Reduce `max_history` in session config
2. Enable embedding cache to reduce recomputation
3. Increase system RAM
4. Use ChromaDB server mode to offload memory

### High CPU Usage

**Symptoms:**
- CPU consistently > 80%
- Slow tool selection
- System sluggish

**Diagnosis:**
```bash
# Check CPU usage
top -p $(pgrep ucp)

# Profile UCP
python -m cProfile -o profile.stats -s cumtime \
  $(which ucp) serve -c config.yaml
```

**Solutions:**
1. Reduce `top_k` in router config
2. Enable caching for tool selections
3. Use GPU for embeddings (if available)
4. Scale horizontally with load balancer

### Database Lock Issues

**Symptoms:**
- "Database is locked" errors
- Slow session operations
- Concurrent request failures

**Diagnosis:**
```bash
# Check for locks
lsof ~/.ucp/data/sessions.db

# Check SQLite settings
sqlite3 ~/.ucp/data/sessions.db "PRAGMA journal_mode;"
sqlite3 ~/.ucp/data/sessions.db "PRAGMA locking_mode;"
```

**Solutions:**
1. Use Redis session backend instead of SQLite
2. Enable WAL mode in SQLite
3. Increase connection pool size
4. Scale to multiple UCP instances with shared Redis

### Downstream Server Timeouts

**Symptoms:**
- "Connection timeout" errors
- Slow tool execution
- Intermittent failures

**Diagnosis:**
```bash
# Test connectivity
curl -v http://api.github.com

# Check firewall
sudo ufw status

# Check logs
journalctl -u ucp -n 100 | grep -i timeout
```

**Solutions:**
1. Increase timeout values in config
2. Check network latency to downstream servers
3. Implement retry logic with exponential backoff
4. Deploy UCP closer to downstream servers

### Performance Degradation Over Time

**Symptoms:**
- Gradual slowdown over days/weeks
- Increasing latency
- Decreasing cache hit rate

**Diagnosis:**
```bash
# Check database size
du -sh ~/.ucp/data/

# Check fragmentation
sqlite3 ~/.ucp/data/sessions.db "PRAGMA integrity_check;"
sqlite3 ~/.ucp/data/tool_zoo/chroma.sqlite3 "VACUUM;"
```

**Solutions:**
1. Regular database maintenance (VACUUM, REINDEX)
2. Implement log rotation
3. Monitor and alert on growth trends
4. Archive old sessions periodically

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup_ucp.sh

BACKUP_DIR="/backup/ucp/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 1. Backup configuration
cp /opt/ucp/ucp_config.yaml "$BACKUP_DIR/"

# 2. Backup sessions
sqlite3 ~/.ucp/data/sessions.db ".backup '$BACKUP_DIR/sessions.db'"

# 3. Backup tool zoo
tar -czf "$BACKUP_DIR/tool_zoo.tar.gz" ~/.ucp/data/tool_zoo/

# 4. Backup cache (optional)
tar -czf "$BACKUP_DIR/cache.tar.gz" ~/.ucp/cache/

# 5. Backup environment
cp /opt/ucp/.env "$BACKUP_DIR/.env"

# 6. Cleanup old backups (keep 30 days)
find /backup/ucp -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
```

### Recovery Procedure

```bash
#!/bin/bash
# restore_ucp.sh

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
  echo "Usage: $0 <backup_directory>"
  exit 1
fi

# 1. Stop UCP
sudo systemctl stop ucp

# 2. Restore configuration
cp "$BACKUP_DIR/ucp_config.yaml" /opt/ucp/

# 3. Restore sessions
rm ~/.ucp/data/sessions.db
sqlite3 ~/.ucp/data/sessions.db < "$BACKUP_DIR/sessions.db"

# 4. Restore tool zoo
rm -rf ~/.ucp/data/tool_zoo
tar -xzf "$BACKUP_DIR/tool_zoo.tar.gz" -C ~/.ucp/data/

# 5. Restore cache (optional)
rm -rf ~/.ucp/cache
tar -xzf "$BACKUP_DIR/cache.tar.gz" -C ~/.ucp/

# 6. Start UCP
sudo systemctl start ucp

echo "Restore completed from: $BACKUP_DIR"
```

## Next Steps

- Read [Getting Started Guide](../local/docs/getting_started.md) for initial setup
- Read [Architecture Overview](../local/docs/mvp_architecture.md) for system design
- Read [Debugging Playbook](debugging_playbook.md) for troubleshooting
- Review [Benchmark Results](../docs/milestone_1_5_baseline_benchmark.md) for performance expectations

## Getting Help

- **Documentation**: See [DOCUMENTATION_MAP.md](../DOCUMENTATION_MAP.md)
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Monitoring**: Check logs at `/opt/ucp/logs/ucp.log`

This guide covers deploying UCP in a production environment, including resource requirements, security considerations, and scaling strategies.

## Table of Contents

- [Resource Requirements](#resource-requirements)
- [Security Considerations](#security-considerations)
- [Scaling Strategies](#scaling-strategies)
- [Deployment Steps](#deployment-steps)
- [Monitoring and Observability](#monitoring-and-observability)
- [Troubleshooting Production Issues](#troubleshooting-production-issues)

## Resource Requirements

### Minimum Requirements

For small-scale deployments (1-5 concurrent users, 10-50 tools):

| Resource | Minimum | Recommended | Notes |
|---|---|---|---|
| CPU | 2 cores | 4 cores | Embedding generation is CPU-intensive |
| RAM | 4 GB | 8 GB | ChromaDB in-memory operations |
| Disk | 10 GB | 20 GB | Vector embeddings grow over time |
| Network | 100 Mbps | 1 Gbps | For downstream server communication |

### Resource Breakdown by Component

#### ChromaDB (Tool Zoo)
- **RAM**: 500 MB base + 10-50 MB per 100 tools
- **Disk**: 5-50 MB per 1000 tools (including embeddings)
- **CPU**: Minimal for queries, moderate during indexing

#### Embedding Generation
- **CPU**: Single-threaded, CPU-intensive
- **RAM**: 100-500 MB per embedding operation
- **Model Size**: `all-MiniLM-L6-v2` ~ 80 MB

#### Session Management (SQLite)
- **RAM**: 10-50 MB base + 1-5 MB per active session
- **Disk**: 1-10 MB per 1000 sessions

#### HTTP Server (if using HTTP transport)
- **RAM**: 50-200 MB base + 10-50 MB per 100 concurrent connections
- **CPU**: Low per request, scales with concurrency

### Scaling Resource Requirements

| Tools | Users | CPU | RAM | Disk |
|---|---|---|---|
| 50 | 1-5 | 4 GB | 10 GB |
| 100 | 5-10 | 8 GB | 20 GB |
| 500 | 10-20 | 16 GB | 50 GB |
| 1000 | 20-40 | 32 GB | 100 GB |

## Security Considerations

### Tool Execution Sandboxing

UCP routes tool calls to downstream MCP servers. While UCP itself doesn't execute arbitrary code, it's important to secure the downstream connections.

#### Recommended Practices

1. **Isolate Downstream Servers**
   ```yaml
   downstream_servers:
     - name: github
       # Use dedicated service account
       env:
         GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
       # Limit to read-only operations where possible
       tags: [code, git, read-only]
   ```

2. **Network Isolation**
   - Run UCP in a dedicated network segment
   - Use firewall rules to restrict outbound connections
   - Implement rate limiting on downstream server access

3. **Environment Variable Security**
   ```bash
   # Use secrets management (never hardcode tokens)
   export GITHUB_TOKEN=$(vault get -field=token secret/github)
   export SLACK_TOKEN=$(vault get -field=token secret/slack)
   
   # Start UCP with secure environment
   ucp serve -c production_config.yaml
   ```

4. **Filesystem Access Control**
   - When using filesystem MCP server, restrict to specific directories
   - Use read-only mounts where possible
   - Implement file type whitelisting

### Data Protection

#### Sensitive Data in Logs

UCP logs may contain:
- Tool names and parameters
- Conversation context snippets
- Error messages with potential data

**Mitigation:**
```yaml
server:
  log_level: WARNING  # Avoid logging DEBUG in production
  # Configure log sanitization
  sanitize_logs: true
```

#### Session Data

- Sessions stored in SQLite database
- Contains conversation history and tool usage patterns
- **Recommendation**: Encrypt session database at rest

```bash
# Encrypt SQLite database
sqlite3 ~/.ucp/data/sessions.db ".dump" | \
  gpg --encrypt --recipient admin@company.com > sessions.db.enc
```

### Authentication and Authorization

#### Claude Desktop Integration

For multi-user environments:

1. **Per-User Configuration**
   ```bash
   # Each user has their own config
   /home/user1/.ucp/ucp_config.yaml
   /home/user2/.ucp/ucp_config.yaml
   ```

2. **Service Account Isolation**
   - Use separate service accounts for different users/departments
   - Implement principle of least privilege
   - Rotate tokens regularly

#### HTTP API Authentication

If using HTTP transport:

```yaml
server:
  transport: http
  port: 8765
  # Enable authentication
  auth:
    enabled: true
    provider: jwt  # or oauth2, apikey
    secret: "${JWT_SECRET}"
    # Rate limiting
    rate_limit:
      requests_per_minute: 100
      burst: 20
```

### Network Security

#### TLS/SSL Configuration

```yaml
server:
  transport: http
  ssl:
    enabled: true
    cert_path: /etc/ucp/ssl/cert.pem
    key_path: /etc/ucp/ssl/key.pem
    # Enforce strong ciphers
    min_tls_version: "1.2"
    ciphers: "HIGH:!aNULL:!MD5"
```

#### Firewall Rules

```bash
# Allow inbound to UCP
ufw allow 8765/tcp  # UCP HTTP port

# Restrict outbound to known MCP servers
ufw allow out to api.github.com 443/tcp
ufw allow out to slack.com 443/tcp
```

## Scaling Strategies

### Vertical Scaling (Single Instance)

#### When to Use
- Small teams (1-10 users)
- Development/testing environments
- Low tool count (< 100)

#### Optimization

1. **Increase CPU Resources**
   - More cores = faster embedding generation
   - Consider CPU with AVX-512 support for embeddings

2. **Increase RAM**
   - Larger ChromaDB cache = faster queries
   - More concurrent sessions

3. **Use SSD Storage**
   - Faster vector database operations
   - Quicker session database access

### Horizontal Scaling (Multiple Instances)

#### When to Use
- Large teams (10+ users)
- High tool count (100+)
- High availability requirements

#### Load Balancing

```
                    [Load Balancer]
                           /      |      \
                      [UCP 1]  [UCP 2]  [UCP 3]
                           |      |      |
                      [ChromaDB] [ChromaDB] [ChromaDB]
```

**Implementation:**

1. **Session Affinity**
   ```yaml
   # Use sticky sessions for same user
   session:
     backend: redis  # Shared session store
     affinity: true
   ```

2. **Shared Tool Zoo**
   - All UCP instances connect to same ChromaDB
   - Use ChromaDB server mode (not embedded)
   - Configure connection pooling

3. **Redis Session Backend**

```yaml
session:
  backend: redis
  redis:
    host: redis.internal
    port: 6379
    db: 0
    # Connection pooling
    pool_size: 20
    max_connections: 50
    # Persistence
    save_interval: 60  # seconds
```

**Benefits:**
- Stateless UCP instances
- Easy horizontal scaling
- Session continuity across restarts

### Database Scaling

#### ChromaDB Scaling

**Small Scale (< 1000 tools):**
- Embedded ChromaDB (default)
- Single SQLite backend

**Medium Scale (1000-10000 tools):**
- ChromaDB server mode
- Dedicated PostgreSQL backend

**Large Scale (> 10000 tools):**
- Distributed ChromaDB
- Shard by tool category/domain
- Consider specialized vector database (Pinecone, Weaviate)

#### Configuration for ChromaDB Server

```yaml
tool_zoo:
  persist_dir: "~/.ucp/data/tool_zoo"
  # Use ChromaDB server instead of embedded
  chromadb_server:
    host: chromadb.internal
    port: 8000
    # Connection settings
    pool_size: 10
    timeout: 30
    # Authentication
    auth_token: "${CHROMADB_TOKEN}"
```

### Caching Strategies

#### Embedding Cache

```yaml
tool_zoo:
  # Cache generated embeddings
  cache_embeddings: true
  cache_dir: "~/.ucp/cache/embeddings"
  cache_ttl: 86400  # 24 hours in seconds
```

#### Tool Selection Cache

```yaml
router:
  # Cache recent tool selections
  cache:
    enabled: true
    max_size: 1000
    ttl: 3600  # 1 hour
```

### Geographic Distribution

For global deployments:

1. **Regional UCP Instances**
   - Deploy UCP closer to users
   - Reduce latency for tool selection

2. **Regional Downstream Servers**
   - Connect to regional MCP endpoints
   - Cache responses locally

3. **CDN for Static Assets**
   - Serve embeddings via CDN
   - Cache tool schemas

## Deployment Steps

### Step 1: Environment Preparation

```bash
# 1. Create dedicated user
sudo useradd -r -s /bin/bash ucp
sudo mkdir -p /opt/ucp
sudo chown ucp:ucp /opt/ucp

# 2. Install dependencies
sudo apt update
sudo apt install -y python3.10 python3.10-venv sqlite3

# 3. Create virtual environment
sudo -u ucp python3.10 -m venv /opt/ucp/venv
source /opt/ucp/venv/bin/activate

# 4. Install UCP
pip install ucp-mvp
```

### Step 2: Configuration

```bash
# 1. Generate production config
ucp init-config -o /opt/ucp/ucp_config.yaml

# 2. Edit for production
vi /opt/ucp/ucp_config.yaml
```

**Production Configuration Template:**

```yaml
server:
  name: "UCP Production Gateway"
  transport: http  # or stdio for Claude Desktop
  host: "0.0.0.0"
  port: 8765
  log_level: WARNING
  # SSL configuration
  ssl:
    enabled: true
    cert_path: "/etc/ucp/ssl/cert.pem"
    key_path: "/etc/ucp/ssl/key.pem"

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  top_k: 5
  similarity_threshold: 0.7
  persist_dir: "/opt/ucp/data/tool_zoo"
  # ChromaDB server for scaling
  chromadb_server:
    host: "chromadb.internal"
    port: 8000
  # Caching
  cache_embeddings: true
  cache_dir: "/opt/ucp/cache/embeddings"

router:
  mode: hybrid
  max_tools: 10
  enable_co_occurrence: true
  enable_learning: true
  # Caching
  cache:
    enabled: true
    max_size: 1000
    ttl: 3600

session:
  # Redis for horizontal scaling
  backend: redis
  redis:
    host: "redis.internal"
    port: 6379
    db: 0
    pool_size: 20
  persist_dir: "/opt/ucp/data/sessions.db"
  max_history: 100

downstream_servers:
  # Use environment variables for secrets
  - name: github
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "${GITHUB_TOKEN}"
    tags: [code, git]

  - name: slack
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-slack"]
    env:
      SLACK_BOT_TOKEN: "${SLACK_TOKEN}"
      SLACK_APP_TOKEN: "${SLACK_APP_TOKEN}"
    tags: [communication, team]
```

### Step 3: SSL Certificate Setup

```bash
# 1. Create SSL directory
sudo mkdir -p /etc/ucp/ssl
sudo chown ucp:ucp /etc/ucp/ssl

# 2. Generate self-signed certificate (for testing)
sudo -u ucp openssl req -x509 -nodes -days 365 \
  -newkey rsa:2048 \
  -keyout /etc/ucp/ssl/key.pem \
  -out /etc/ucp/ssl/cert.pem

# 3. Or use Let's Encrypt for production
sudo certbot certonly --standalone \
  -d ucp.yourdomain.com \
  --email admin@yourdomain.com
sudo cp /etc/letsencrypt/live/ucp.yourdomain.com/fullchain.pem \
  /etc/ucp/ssl/cert.pem
sudo cp /etc/letsencrypt/live/ucp.yourdomain.com/privkey.pem \
  /etc/ucp/ssl/key.pem
```

### Step 4: Systemd Service

```bash
# 1. Create systemd service file
sudo vi /etc/systemd/system/ucp.service
```

**Service File:**

```ini
[Unit]
Description=UCP Gateway Service
After=network.target
Wants=network.target

[Service]
Type=simple
User=ucp
Group=ucp
WorkingDirectory=/opt/ucp
Environment="PATH=/opt/ucp/venv/bin"
EnvironmentFile=/opt/ucp/.env
ExecStart=/opt/ucp/venv/bin/ucp serve -c /opt/ucp/ucp_config.yaml
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# 2. Create environment file
sudo -u ucp vi /opt/ucp/.env
```

**Environment File:**

```bash
# Secrets (loaded from vault or key management)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxx
SLACK_TOKEN=xoxb-xxxxxxxxxxxx
SLACK_APP_TOKEN=xapp-xxxxxxxxxxxx

# Database credentials
REDIS_PASSWORD=xxxxxxxx
CHROMADB_TOKEN=xxxxxxxx

# JWT secret (if using HTTP auth)
JWT_SECRET=your-super-secret-key-here
```

```bash
# 3. Set permissions
sudo chmod 600 /opt/ucp/.env
sudo chown ucp:ucp /opt/ucp/.env

# 4. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable ucp
sudo systemctl start ucp

# 5. Check status
sudo systemctl status ucp
sudo journalctl -u ucp -f
```

### Step 5: Nginx Reverse Proxy (Optional)

```bash
# 1. Install Nginx
sudo apt install -y nginx

# 2. Configure reverse proxy
sudo vi /etc/nginx/sites-available/ucp
```

**Nginx Configuration:**

```nginx
upstream ucp_backend {
    server 127.0.0.1:8765;
    # Add more instances for load balancing
    # server 127.0.0.1:8766;
    # server 127.0.0.1:8767;
}

server {
    listen 80;
    server_name ucp.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ucp.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/ucp/ssl/cert.pem;
    ssl_certificate_key /etc/ucp/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";

    # Proxy settings
    location / {
        proxy_pass http://ucp_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://ucp_backend/health;
        access_log off;
    }
}
```

```bash
# 3. Enable site
sudo ln -s /etc/nginx/sites-available/ucp /etc/nginx/sites-enabled/

# 4. Test and restart
sudo nginx -t
sudo systemctl reload nginx
```

### Step 6: Firewall Configuration

```bash
# 1. Configure firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8765/tcp  # UCP direct (optional)
sudo ufw enable

# 2. Verify
sudo ufw status
```

## Monitoring and Observability

### Health Checks

```bash
# UCP provides health endpoint
curl http://localhost:8765/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "components": {
    "tool_zoo": "healthy",
    "router": "healthy",
    "session_manager": "healthy",
    "downstream_servers": {
      "github": "connected",
      "slack": "connected"
    }
  },
  "metrics": {
    "tools_indexed": 150,
    "active_sessions": 5,
    "uptime_seconds": 86400
  }
}
```

### Metrics Collection

#### Prometheus Integration

```yaml
server:
  metrics:
    enabled: true
    port: 9090
    path: /metrics
```

**Available Metrics:**

```
# Tool selection metrics
ucp_router_selection_duration_seconds{quantile="0.5"} 0.025
ucp_router_selection_duration_seconds{quantile="0.95"} 0.050
ucp_router_selection_duration_seconds{quantile="0.99"} 0.100

# Tool zoo metrics
ucp_tool_zoo_query_duration_seconds 0.010
ucp_tool_zoo_tools_total 150
ucp_tool_zoo_cache_hits_total 1200
ucp_tool_zoo_cache_misses_total 300

# Session metrics
ucp_session_active_total 5
ucp_session_created_total 1000
ucp_session_duration_seconds{quantile="0.5"} 300

# Downstream server metrics
ucp_downstream_requests_total{server="github"} 500
ucp_downstream_errors_total{server="github"} 5
ucp_downstream_latency_seconds{server="github"} 0.100
```

#### Grafana Dashboard

Create dashboard with panels for:
1. **Request Rate**: Requests per minute
2. **Latency**: P50, P95, P99 latencies
3. **Error Rate**: Failed requests percentage
4. **Resource Usage**: CPU, RAM, Disk
5. **Tool Zoo**: Indexed tools, cache hit rate
6. **Sessions**: Active sessions, average duration

### Logging

#### Log Rotation

```bash
# 1. Create logrotate config
sudo vi /etc/logrotate.d/ucp
```

**Logrotate Configuration:**

```
/opt/ucp/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 ucp ucp
    sharedscripts
        postrotate
            systemctl reload ucp > /dev/null || true
        endscript
}
```

#### Structured Logging

```yaml
server:
  log_level: INFO
  log_format: json  # or text
  log_output:
    - file:/opt/ucp/logs/ucp.log
    - stdout
```

**JSON Log Format:**
```json
{
  "timestamp": "2025-01-11T04:00:00Z",
  "level": "INFO",
  "component": "router",
  "message": "Selected 3 tools for session abc123",
  "context": {
    "session_id": "abc123",
    "tools_selected": ["gmail.send_email", "github.create_pr"],
    "selection_duration_ms": 25.99
  }
}
```

### Alerting

#### Critical Alerts

1. **UCP Service Down**
   - Trigger: Service not responding for 30 seconds
   - Action: Restart service, notify team

2. **High Error Rate**
   - Trigger: Error rate > 5% for 5 minutes
   - Action: Check logs, investigate downstream servers

3. **High Latency**
   - Trigger: P95 latency > 100ms for 5 minutes
   - Action: Check resource usage, scale if needed

4. **Downstream Server Disconnected**
   - Trigger: Any downstream server disconnected
   - Action: Check server status, restart if needed

#### Alert Configuration (Prometheus Alertmanager)

```yaml
groups:
  - name: ucp_alerts
    rules:
      - alert: UCPServiceDown
        expr: up{job="ucp"} == 0
        for: 30s
        labels:
          severity: critical
        annotations:
          summary: "UCP service is down"
          description: "UCP has been down for 30 seconds"

      - alert: UCPHighErrorRate
        expr: |
          rate(ucp_router_errors_total[5m]) / 
          rate(ucp_router_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 5%"

      - alert: UCPHighLatency
        expr: |
          histogram_quantile(0.95, 
            rate(ucp_router_selection_duration_seconds_bucket[5m])
          ) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High latency detected"
          description: "P95 latency is above 100ms"
```

## Troubleshooting Production Issues

### High Memory Usage

**Symptoms:**
- OOM (Out of Memory) errors
- System swapping
- Slow performance

**Diagnosis:**
```bash
# Check memory usage
free -h
ps aux | grep ucp

# Check ChromaDB memory
sqlite3 ~/.ucp/data/tool_zoo/chroma.sqlite3 ".tables"
```

**Solutions:**
1. Reduce `max_history` in session config
2. Enable embedding cache to reduce recomputation
3. Increase system RAM
4. Use ChromaDB server mode to offload memory

### High CPU Usage

**Symptoms:**
- CPU consistently > 80%
- Slow tool selection
- System sluggish

**Diagnosis:**
```bash
# Check CPU usage
top -p $(pgrep ucp)

# Profile UCP
python -m cProfile -o profile.stats -s cumtime \
  $(which ucp) serve -c config.yaml
```

**Solutions:**
1. Reduce `top_k` in router config
2. Enable caching for tool selections
3. Use GPU for embeddings (if available)
4. Scale horizontally with load balancer

### Database Lock Issues

**Symptoms:**
- "Database is locked" errors
- Slow session operations
- Concurrent request failures

**Diagnosis:**
```bash
# Check for locks
lsof ~/.ucp/data/sessions.db

# Check SQLite settings
sqlite3 ~/.ucp/data/sessions.db "PRAGMA journal_mode;"
sqlite3 ~/.ucp/data/sessions.db "PRAGMA locking_mode;"
```

**Solutions:**
1. Use Redis session backend instead of SQLite
2. Enable WAL mode in SQLite
3. Increase connection pool size
4. Scale to multiple UCP instances with shared Redis

### Downstream Server Timeouts

**Symptoms:**
- "Connection timeout" errors
- Slow tool execution
- Intermittent failures

**Diagnosis:**
```bash
# Test connectivity
curl -v http://api.github.com

# Check firewall
sudo ufw status

# Check logs
journalctl -u ucp -n 100 | grep -i timeout
```

**Solutions:**
1. Increase timeout values in config
2. Check network latency to downstream servers
3. Implement retry logic with exponential backoff
4. Deploy UCP closer to downstream servers

### Performance Degradation Over Time

**Symptoms:**
- Gradual slowdown over days/weeks
- Increasing latency
- Decreasing cache hit rate

**Diagnosis:**
```bash
# Check database size
du -sh ~/.ucp/data/

# Check fragmentation
sqlite3 ~/.ucp/data/sessions.db "PRAGMA integrity_check;"
sqlite3 ~/.ucp/data/tool_zoo/chroma.sqlite3 "VACUUM;"
```

**Solutions:**
1. Regular database maintenance (VACUUM, REINDEX)
2. Implement log rotation
3. Monitor and alert on growth trends
4. Archive old sessions periodically

## Backup and Recovery

### Backup Strategy

```bash
#!/bin/bash
# backup_ucp.sh

BACKUP_DIR="/backup/ucp/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# 1. Backup configuration
cp /opt/ucp/ucp_config.yaml "$BACKUP_DIR/"

# 2. Backup sessions
sqlite3 ~/.ucp/data/sessions.db ".backup '$BACKUP_DIR/sessions.db'"

# 3. Backup tool zoo
tar -czf "$BACKUP_DIR/tool_zoo.tar.gz" ~/.ucp/data/tool_zoo/

# 4. Backup cache (optional)
tar -czf "$BACKUP_DIR/cache.tar.gz" ~/.ucp/cache/

# 5. Backup environment
cp /opt/ucp/.env "$BACKUP_DIR/.env"

# 6. Cleanup old backups (keep 30 days)
find /backup/ucp -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR"
```

### Recovery Procedure

```bash
#!/bin/bash
# restore_ucp.sh

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
  echo "Usage: $0 <backup_directory>"
  exit 1
fi

# 1. Stop UCP
sudo systemctl stop ucp

# 2. Restore configuration
cp "$BACKUP_DIR/ucp_config.yaml" /opt/ucp/

# 3. Restore sessions
rm ~/.ucp/data/sessions.db
sqlite3 ~/.ucp/data/sessions.db < "$BACKUP_DIR/sessions.db"

# 4. Restore tool zoo
rm -rf ~/.ucp/data/tool_zoo
tar -xzf "$BACKUP_DIR/tool_zoo.tar.gz" -C ~/.ucp/data/

# 5. Restore cache (optional)
rm -rf ~/.ucp/cache
tar -xzf "$BACKUP_DIR/cache.tar.gz" -C ~/.ucp/

# 6. Start UCP
sudo systemctl start ucp

echo "Restore completed from: $BACKUP_DIR"
```

## Next Steps

- Read [Getting Started Guide](../local/docs/getting_started.md) for initial setup
- Read [Architecture Overview](../local/docs/mvp_architecture.md) for system design
- Read [Debugging Playbook](debugging_playbook.md) for troubleshooting
- Review [Benchmark Results](../docs/milestone_1_5_baseline_benchmark.md) for performance expectations

## Getting Help

- **Documentation**: See [DOCUMENTATION_MAP.md](../DOCUMENTATION_MAP.md)
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Ask questions on GitHub Discussions
- **Monitoring**: Check logs at `/opt/ucp/logs/ucp.log`

