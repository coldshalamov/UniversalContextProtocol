# Milestone 1.4: Telemetry Infrastructure

## Overview

This milestone implements a comprehensive telemetry infrastructure for the Universal Context Protocol (UCP) local MVP. The system captures detailed metrics about routing decisions, tool invocations, and system performance, enabling data-driven optimization and monitoring.

## Components Implemented

### 1. Telemetry Module (`telemetry.py`)

A complete telemetry system with the following components:

#### Event Types
- **RoutingEvent**: Captures router decision metadata
  - `event_id`: Unique identifier for the routing event
  - `session_id`: Session identifier
  - `request_id`: Request identifier for tracing
  - `trace_id`: Trace ID for distributed tracing
  - `timestamp`: When the routing decision was made
  - `query_hash`: Hashed query for privacy
  - `query_text`: Optional raw query text (opt-in)
  - `candidates`: List of candidate tools with scores
  - `selected_tools`: Tools that were selected
  - `total_candidates`: Total number of candidates
  - `context_tokens_used`: Token count used
  - `max_context_tokens`: Maximum context budget
  - `selection_time_ms`: Time taken to make decision
  - `strategy`: Routing strategy used
  - `exploration_triggered`: Whether exploration was triggered

- **ToolCallEvent**: Captures tool invocation metadata
  - `event_id`: Unique identifier for the tool call
  - `session_id`: Session identifier
  - `request_id`: Request identifier
  - `routing_event_id`: Link to routing decision
  - `trace_id`: Trace ID
  - `timestamp`: When the tool was called
  - `tool_name`: Name of the tool
  - `success`: Whether the call succeeded
  - `error_class`: Type of error if failed
  - `error_message`: Error message if failed
  - `execution_time_ms`: Time taken to execute
  - `was_selected`: Whether tool was in selected set
  - `selection_rank`: Position in selected list

- **RewardSignal**: Captures reward for online learning
  - `event_id`: Unique identifier
  - `tool_call_event_id`: Link to tool call
  - `tool_name`: Tool name
  - `timestamp`: When reward was calculated
  - `success_reward`: +1 for success, -1 for failure
  - `latency_penalty`: Negative penalty based on execution time
  - `context_cost_penalty`: Negative penalty based on schema size
  - `followup_penalty`: Negative penalty for immediate retry
  - `total_reward`: Final normalized reward in [-1, +1]

#### Storage Backends

**SQLiteTelemetryStore**: Persistent storage for telemetry events
- Creates tables for routing events, tool calls, and reward signals
- Maintains aggregated statistics cache
- Supports querying and cleanup of old events
- Provides methods for getting tool stats and metrics summaries

**JSONLTelemetryExporter**: Exports events to JSONL files
- Creates date-based log files: `logs/ucp_telemetry_{date}.jsonl`
- Automatically creates logs/ directory if it doesn't exist
- One JSON object per line for easy parsing
- Supports routing events, tool calls, and rewards

**PrometheusMetrics**: Prometheus-formatted metrics collector
- **`ucp_router_latency_ms`**: Histogram of router decision times
  - Buckets: 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000 ms
  - Includes count, sum, and bucket counts
  
- **`ucp_tool_invocations_total`**: Counter for tool calls
  - Labels: `tool_name`, `success` (true/false)
  - Increments on each tool invocation
  
- **`ucp_context_shift_detected_total`**: Counter for context shifts
  - Increments when a context shift is detected

**RewardCalculator**: Computes normalized rewards
- Configurable penalty scales for latency, context cost, and followup
- Normalizes total reward to [-1, +1] range

### 2. HTTP Server Module (`http_server.py`)

Enhanced HTTP server with metrics endpoint:

#### New Endpoint: `/metrics`

Returns Prometheus-formatted metrics:
```text
# HELP ucp_router_latency_ms Router decision latency in milliseconds
# TYPE ucp_router_latency_ms histogram
ucp_router_latency_ms_bucket{le="5"} 0
ucp_router_latency_ms_bucket{le="10"} 2
...
ucp_router_latency_ms_bucket{le="+Inf"} 10
ucp_router_latency_ms_sum 150.5
ucp_router_latency_ms_count 10

# HELP ucp_tool_invocations_total Total tool invocations
# TYPE ucp_tool_invocations_total counter
ucp_tool_invocations_total{tool_name="read_file",success="true"} 5
ucp_tool_invocations_total{tool_name="read_file",success="false"} 1

# HELP ucp_context_shift_detected_total Total context shifts detected
# TYPE ucp_context_shift_detected_total counter
ucp_context_shift_detected_total 0
```

### 3. Session Manager Enhancements (`session.py`)

Enhanced with telemetry integration:

#### New Methods

- **`set_trace_context(trace_id, request_id)`**: Sets trace context for telemetry
  - Associates trace_id and request_id with the session
  - Used for correlating events across the request lifecycle

- **`get_trace_context()`**: Returns current trace context
  - Returns dict with `trace_id` and `request_id`

- **`_export_telemetry_to_jsonl(event_data)`**: Exports events to JSONL
  - Automatically exports tool usage events
  - Creates logs/ directory if needed
  - Uses date-based filenames

#### Integration Points

Telemetry is now logged at:
- Tool usage events (success/failure, execution time, errors)
- Routing decisions (predicted tools, selection time, strategy)
- Tool calls (with trace context linking to routing decisions)

### 4. Server Integration (`server.py`)

UCP server now integrates telemetry throughout:

#### Routing Events
- Captures router decision time
- Logs selected tools and query hash
- Records strategy and exploration status
- Exports to both SQLite and JSONL

#### Tool Call Events
- Captures execution time and success/failure
- Links to routing event via `routing_event_id`
- Records whether tool was in predicted set
- Exports to both SQLite and JSONL

#### Prometheus Metrics Updates
- **Router latency**: Observed on each routing decision
- **Tool invocations**: Incremented on each tool call (success/failure)
- **Context shifts**: Can be incremented when context shifts detected

## Usage

### Querying Telemetry Logs

Telemetry logs are stored in JSONL format in the `logs/` directory:

```bash
# View today's logs
cat logs/ucp_telemetry_$(date +%Y-%m-%d).jsonl

# Query with jq for specific events
cat logs/ucp_telemetry_*.jsonl | jq 'select(.event_type == "tool_call") | .tool_name'

# Count events by type
cat logs/ucp_telemetry_*.jsonl | jq 'group_by(.event_type) | {type: .[0], count: length}'
```

### Accessing Prometheus Metrics

The `/metrics` endpoint provides real-time metrics:

```bash
# Using curl
curl http://localhost:8000/metrics

# Using Prometheus
# Add to prometheus.yml:
scrape_configs:
  - job_name: 'ucp'
    static_configs:
      - targets: ['localhost:8000']
```

### Monitoring with Grafana

1. Add Prometheus as a data source
2. Create dashboard panels:
   - Router latency histogram
   - Tool invocation rate
   - Success rate by tool
   - Context shift detection rate

## Event Flow

### Request Lifecycle

```
1. Request arrives
   ↓
2. SessionManager.set_trace_context(trace_id, request_id)
   ↓
3. Router.route() makes decision
   ↓
4. RoutingEvent logged to SQLite + JSONL
   ↓
5. PrometheusMetrics.observe_router_latency()
   ↓
6. Tools returned to client
   ↓
7. Tool invoked
   ↓
8. ToolCallEvent logged to SQLite + JSONL
   ↓
9. PrometheusMetrics.inc_tool_invocation()
   ↓
10. SessionManager.log_tool_usage()
```

### Trace Correlation

All events in a request share:
- `trace_id`: Distributed trace identifier
- `request_id`: Request identifier
- `session_id`: Session identifier

This enables:
- End-to-end tracing across components
- Performance analysis per request
- Debugging of specific request flows

## Configuration

### Environment Variables

```bash
# Telemetry database location
UCP_TELEMETRY_DB_PATH=./data/telemetry.db

# JSONL logs directory
UCP_TELEMETRY_LOGS_DIR=./logs

# Enable/disable telemetry
UCP_TELEMETRY_ENABLED=true
```

### Config File Settings

```yaml
telemetry:
  enabled: true
  db_path: "./data/telemetry.db"
  logs_dir: "./logs"
  cleanup_age_hours: 168  # 7 days
```

## Performance Considerations

### Storage Efficiency

- **SQLite**: Indexed for fast queries on session_id, timestamp, tool_name
- **JSONL**: Append-only writes, efficient for streaming
- **Batch writes**: Multiple events written in single transaction
- **Cleanup**: Automatic cleanup of events older than 7 days

### Memory Usage

- **Prometheus metrics**: In-memory counters (minimal overhead)
- **SQLite**: Connection pooling, row factory for efficient access
- **JSONL**: Streaming writes (no large in-memory buffers)

### Privacy

- **Query hashing**: Queries are SHA256 hashed by default (first 16 chars)
- **Opt-in**: Raw query text only logged if explicitly enabled
- **No PII**: System does not log user content, only metadata

## Success Criteria

✅ Every tool call generates structured telemetry
   - ToolCallEvent captures all required fields
   - Links to routing decisions via routing_event_id
   - Includes trace_id, session_id, request_id

✅ Logs are exported to JSONL format with date-based filenames
   - JSONLTelemetryExporter creates logs/ directory
   - Filename format: `ucp_telemetry_YYYY-MM-DD.jsonl`
   - One JSON per line for easy parsing

✅ /metrics endpoint returns Prometheus-formatted metrics
   - UCPHttpServer exposes `/metrics` endpoint
   - Returns properly formatted Prometheus metrics
   - Includes HELP and TYPE comments

✅ All required metrics are tracked
   - Router latency: `ucp_router_latency_ms` histogram
   - Tool invocations: `ucp_tool_invocations_total` counter
   - Context shifts: `ucp_context_shift_detected_total` counter

## Testing

### Manual Testing

```bash
# Start UCP server
python -m ucp_mvp.server

# Make some tool calls via MCP client
# (This will generate telemetry events)

# Check metrics
curl http://localhost:8000/metrics

# Check logs
ls -la logs/
cat logs/ucp_telemetry_*.jsonl
```

### Automated Testing

```python
import requests
import json

# Start server
# Make tool calls
response = requests.post("http://localhost:8000/mcp/tools/call", json={
    "name": "read_file",
    "arguments": {"path": "test.txt"}
})

# Check metrics
metrics = requests.get("http://localhost:8000/metrics").text
print(metrics)

# Verify metrics format
assert "# HELP ucp_router_latency_ms" in metrics
assert "# TYPE ucp_router_latency_ms histogram" in metrics
```

## Troubleshooting

### Logs Not Being Written

1. Check logs directory exists:
   ```bash
   ls -la logs/
   ```

2. Check file permissions:
   ```bash
   chmod 755 logs/
   ```

3. Verify telemetry is enabled:
   ```python
   from ucp.telemetry import get_telemetry_store
   store = get_telemetry_store()
   print(store._db is not None)
   ```

### Metrics Not Updating

1. Check PrometheusMetrics is being used:
   - Verify `_prometheus_metrics.observe_router_latency()` is called
   - Verify `_prometheus_metrics.inc_tool_invocation()` is called

2. Check /metrics endpoint:
   - Verify it returns data, not empty string
   - Check for errors in server logs

### Database Issues

1. Check SQLite database:
   ```bash
   sqlite3 data/telemetry.db ".schema routing_events"
   sqlite3 data/telemetry.db "SELECT COUNT(*) FROM routing_events"
   ```

2. Check for locked database:
   ```bash
   lsof data/telemetry.db
   ```

## Future Enhancements

### Planned Improvements

1. **Streaming Metrics**: Real-time metric updates via WebSocket
2. **Aggregated Metrics**: Pre-computed rollups for faster queries
3. **Alerting**: Integration with Prometheus alerting rules
4. **Export Formats**: Support for CSV, Parquet, and Avro
5. **Query API**: REST API for querying telemetry data
6. **Dashboard**: Built-in Grafana dashboard templates

### Integration Opportunities

- **OpenTelemetry**: Replace custom metrics with OpenTelemetry SDK
- **Jaeger**: Distributed tracing integration
- **Grafana Loki**: Centralized log aggregation
- **Prometheus Remote**: Push gateway instead of pull

## Migration Notes

### From Archive to Local MVP

The telemetry system in `archive/src/ucp_original/ucp/telemetry.py` has been adapted for the local MVP:

**Removed**:
- Cloud-specific features (remote storage, multi-tenancy)
- Advanced analytics (cohort analysis, A/B testing)
- Complex reward models (only basic reward calculation kept)

**Simplified**:
- Single-tenant SQLite storage
- Basic Prometheus metrics (histogram + counters)
- JSONL export for simple log analysis
- Core telemetry events (routing, tool calls, rewards)

**Kept**:
- Core event data structures (RoutingEvent, ToolCallEvent, RewardSignal)
- SQLiteTelemetryStore with indexed tables
- RewardCalculator for online learning signals
- JSONLTelemetryExporter for log export

## Related Documentation

- [Getting Started Guide](../local/docs/getting_started.md)
- [API Reference](../shared/docs/api_reference.md)
- [Development Guide](../DEVELOPMENT_GUIDE.md)
- [Milestone 1.3: Claude Desktop Test](./milestone_1_3_claude_desktop_test.md)

## Summary

Milestone 1.4 successfully implements a comprehensive telemetry infrastructure that:

1. **Captures all relevant events**: Routing decisions, tool invocations, rewards
2. **Provides multiple storage backends**: SQLite for queries, JSONL for export, Prometheus for monitoring
3. **Enables traceability**: trace_id, session_id, request_id correlation
4. **Supports monitoring**: Prometheus-formatted metrics endpoint
5. **Maintains privacy**: Query hashing by default, no PII logging
6. **Performance optimized**: Indexed queries, batch writes, in-memory metrics

The telemetry system is production-ready and provides the foundation for:
- Data-driven optimization of routing decisions
- Performance monitoring and alerting
- Debugging and troubleshooting
- Historical analysis and reporting

## Overview

This milestone implements a comprehensive telemetry infrastructure for the Universal Context Protocol (UCP) local MVP. The system captures detailed metrics about routing decisions, tool invocations, and system performance, enabling data-driven optimization and monitoring.

## Components Implemented

### 1. Telemetry Module (`telemetry.py`)

A complete telemetry system with the following components:

#### Event Types
- **RoutingEvent**: Captures router decision metadata
  - `event_id`: Unique identifier for the routing event
  - `session_id`: Session identifier
  - `request_id`: Request identifier for tracing
  - `trace_id`: Trace ID for distributed tracing
  - `timestamp`: When the routing decision was made
  - `query_hash`: Hashed query for privacy
  - `query_text`: Optional raw query text (opt-in)
  - `candidates`: List of candidate tools with scores
  - `selected_tools`: Tools that were selected
  - `total_candidates`: Total number of candidates
  - `context_tokens_used`: Token count used
  - `max_context_tokens`: Maximum context budget
  - `selection_time_ms`: Time taken to make decision
  - `strategy`: Routing strategy used
  - `exploration_triggered`: Whether exploration was triggered

- **ToolCallEvent**: Captures tool invocation metadata
  - `event_id`: Unique identifier for the tool call
  - `session_id`: Session identifier
  - `request_id`: Request identifier
  - `routing_event_id`: Link to routing decision
  - `trace_id`: Trace ID
  - `timestamp`: When the tool was called
  - `tool_name`: Name of the tool
  - `success`: Whether the call succeeded
  - `error_class`: Type of error if failed
  - `error_message`: Error message if failed
  - `execution_time_ms`: Time taken to execute
  - `was_selected`: Whether tool was in selected set
  - `selection_rank`: Position in selected list

- **RewardSignal**: Captures reward for online learning
  - `event_id`: Unique identifier
  - `tool_call_event_id`: Link to tool call
  - `tool_name`: Tool name
  - `timestamp`: When reward was calculated
  - `success_reward`: +1 for success, -1 for failure
  - `latency_penalty`: Negative penalty based on execution time
  - `context_cost_penalty`: Negative penalty based on schema size
  - `followup_penalty`: Negative penalty for immediate retry
  - `total_reward`: Final normalized reward in [-1, +1]

#### Storage Backends

**SQLiteTelemetryStore**: Persistent storage for telemetry events
- Creates tables for routing events, tool calls, and reward signals
- Maintains aggregated statistics cache
- Supports querying and cleanup of old events
- Provides methods for getting tool stats and metrics summaries

**JSONLTelemetryExporter**: Exports events to JSONL files
- Creates date-based log files: `logs/ucp_telemetry_{date}.jsonl`
- Automatically creates logs/ directory if it doesn't exist
- One JSON object per line for easy parsing
- Supports routing events, tool calls, and rewards

**PrometheusMetrics**: Prometheus-formatted metrics collector
- **`ucp_router_latency_ms`**: Histogram of router decision times
  - Buckets: 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, 10000 ms
  - Includes count, sum, and bucket counts
  
- **`ucp_tool_invocations_total`**: Counter for tool calls
  - Labels: `tool_name`, `success` (true/false)
  - Increments on each tool invocation
  
- **`ucp_context_shift_detected_total`**: Counter for context shifts
  - Increments when a context shift is detected

**RewardCalculator**: Computes normalized rewards
- Configurable penalty scales for latency, context cost, and followup
- Normalizes total reward to [-1, +1] range

### 2. HTTP Server Module (`http_server.py`)

Enhanced HTTP server with metrics endpoint:

#### New Endpoint: `/metrics`

Returns Prometheus-formatted metrics:
```text
# HELP ucp_router_latency_ms Router decision latency in milliseconds
# TYPE ucp_router_latency_ms histogram
ucp_router_latency_ms_bucket{le="5"} 0
ucp_router_latency_ms_bucket{le="10"} 2
...
ucp_router_latency_ms_bucket{le="+Inf"} 10
ucp_router_latency_ms_sum 150.5
ucp_router_latency_ms_count 10

# HELP ucp_tool_invocations_total Total tool invocations
# TYPE ucp_tool_invocations_total counter
ucp_tool_invocations_total{tool_name="read_file",success="true"} 5
ucp_tool_invocations_total{tool_name="read_file",success="false"} 1

# HELP ucp_context_shift_detected_total Total context shifts detected
# TYPE ucp_context_shift_detected_total counter
ucp_context_shift_detected_total 0
```

### 3. Session Manager Enhancements (`session.py`)

Enhanced with telemetry integration:

#### New Methods

- **`set_trace_context(trace_id, request_id)`**: Sets trace context for telemetry
  - Associates trace_id and request_id with the session
  - Used for correlating events across the request lifecycle

- **`get_trace_context()`**: Returns current trace context
  - Returns dict with `trace_id` and `request_id`

- **`_export_telemetry_to_jsonl(event_data)`**: Exports events to JSONL
  - Automatically exports tool usage events
  - Creates logs/ directory if needed
  - Uses date-based filenames

#### Integration Points

Telemetry is now logged at:
- Tool usage events (success/failure, execution time, errors)
- Routing decisions (predicted tools, selection time, strategy)
- Tool calls (with trace context linking to routing decisions)

### 4. Server Integration (`server.py`)

UCP server now integrates telemetry throughout:

#### Routing Events
- Captures router decision time
- Logs selected tools and query hash
- Records strategy and exploration status
- Exports to both SQLite and JSONL

#### Tool Call Events
- Captures execution time and success/failure
- Links to routing event via `routing_event_id`
- Records whether tool was in predicted set
- Exports to both SQLite and JSONL

#### Prometheus Metrics Updates
- **Router latency**: Observed on each routing decision
- **Tool invocations**: Incremented on each tool call (success/failure)
- **Context shifts**: Can be incremented when context shifts detected

## Usage

### Querying Telemetry Logs

Telemetry logs are stored in JSONL format in the `logs/` directory:

```bash
# View today's logs
cat logs/ucp_telemetry_$(date +%Y-%m-%d).jsonl

# Query with jq for specific events
cat logs/ucp_telemetry_*.jsonl | jq 'select(.event_type == "tool_call") | .tool_name'

# Count events by type
cat logs/ucp_telemetry_*.jsonl | jq 'group_by(.event_type) | {type: .[0], count: length}'
```

### Accessing Prometheus Metrics

The `/metrics` endpoint provides real-time metrics:

```bash
# Using curl
curl http://localhost:8000/metrics

# Using Prometheus
# Add to prometheus.yml:
scrape_configs:
  - job_name: 'ucp'
    static_configs:
      - targets: ['localhost:8000']
```

### Monitoring with Grafana

1. Add Prometheus as a data source
2. Create dashboard panels:
   - Router latency histogram
   - Tool invocation rate
   - Success rate by tool
   - Context shift detection rate

## Event Flow

### Request Lifecycle

```
1. Request arrives
   ↓
2. SessionManager.set_trace_context(trace_id, request_id)
   ↓
3. Router.route() makes decision
   ↓
4. RoutingEvent logged to SQLite + JSONL
   ↓
5. PrometheusMetrics.observe_router_latency()
   ↓
6. Tools returned to client
   ↓
7. Tool invoked
   ↓
8. ToolCallEvent logged to SQLite + JSONL
   ↓
9. PrometheusMetrics.inc_tool_invocation()
   ↓
10. SessionManager.log_tool_usage()
```

### Trace Correlation

All events in a request share:
- `trace_id`: Distributed trace identifier
- `request_id`: Request identifier
- `session_id`: Session identifier

This enables:
- End-to-end tracing across components
- Performance analysis per request
- Debugging of specific request flows

## Configuration

### Environment Variables

```bash
# Telemetry database location
UCP_TELEMETRY_DB_PATH=./data/telemetry.db

# JSONL logs directory
UCP_TELEMETRY_LOGS_DIR=./logs

# Enable/disable telemetry
UCP_TELEMETRY_ENABLED=true
```

### Config File Settings

```yaml
telemetry:
  enabled: true
  db_path: "./data/telemetry.db"
  logs_dir: "./logs"
  cleanup_age_hours: 168  # 7 days
```

## Performance Considerations

### Storage Efficiency

- **SQLite**: Indexed for fast queries on session_id, timestamp, tool_name
- **JSONL**: Append-only writes, efficient for streaming
- **Batch writes**: Multiple events written in single transaction
- **Cleanup**: Automatic cleanup of events older than 7 days

### Memory Usage

- **Prometheus metrics**: In-memory counters (minimal overhead)
- **SQLite**: Connection pooling, row factory for efficient access
- **JSONL**: Streaming writes (no large in-memory buffers)

### Privacy

- **Query hashing**: Queries are SHA256 hashed by default (first 16 chars)
- **Opt-in**: Raw query text only logged if explicitly enabled
- **No PII**: System does not log user content, only metadata

## Success Criteria

✅ Every tool call generates structured telemetry
   - ToolCallEvent captures all required fields
   - Links to routing decisions via routing_event_id
   - Includes trace_id, session_id, request_id

✅ Logs are exported to JSONL format with date-based filenames
   - JSONLTelemetryExporter creates logs/ directory
   - Filename format: `ucp_telemetry_YYYY-MM-DD.jsonl`
   - One JSON per line for easy parsing

✅ /metrics endpoint returns Prometheus-formatted metrics
   - UCPHttpServer exposes `/metrics` endpoint
   - Returns properly formatted Prometheus metrics
   - Includes HELP and TYPE comments

✅ All required metrics are tracked
   - Router latency: `ucp_router_latency_ms` histogram
   - Tool invocations: `ucp_tool_invocations_total` counter
   - Context shifts: `ucp_context_shift_detected_total` counter

## Testing

### Manual Testing

```bash
# Start UCP server
python -m ucp_mvp.server

# Make some tool calls via MCP client
# (This will generate telemetry events)

# Check metrics
curl http://localhost:8000/metrics

# Check logs
ls -la logs/
cat logs/ucp_telemetry_*.jsonl
```

### Automated Testing

```python
import requests
import json

# Start server
# Make tool calls
response = requests.post("http://localhost:8000/mcp/tools/call", json={
    "name": "read_file",
    "arguments": {"path": "test.txt"}
})

# Check metrics
metrics = requests.get("http://localhost:8000/metrics").text
print(metrics)

# Verify metrics format
assert "# HELP ucp_router_latency_ms" in metrics
assert "# TYPE ucp_router_latency_ms histogram" in metrics
```

## Troubleshooting

### Logs Not Being Written

1. Check logs directory exists:
   ```bash
   ls -la logs/
   ```

2. Check file permissions:
   ```bash
   chmod 755 logs/
   ```

3. Verify telemetry is enabled:
   ```python
   from ucp.telemetry import get_telemetry_store
   store = get_telemetry_store()
   print(store._db is not None)
   ```

### Metrics Not Updating

1. Check PrometheusMetrics is being used:
   - Verify `_prometheus_metrics.observe_router_latency()` is called
   - Verify `_prometheus_metrics.inc_tool_invocation()` is called

2. Check /metrics endpoint:
   - Verify it returns data, not empty string
   - Check for errors in server logs

### Database Issues

1. Check SQLite database:
   ```bash
   sqlite3 data/telemetry.db ".schema routing_events"
   sqlite3 data/telemetry.db "SELECT COUNT(*) FROM routing_events"
   ```

2. Check for locked database:
   ```bash
   lsof data/telemetry.db
   ```

## Future Enhancements

### Planned Improvements

1. **Streaming Metrics**: Real-time metric updates via WebSocket
2. **Aggregated Metrics**: Pre-computed rollups for faster queries
3. **Alerting**: Integration with Prometheus alerting rules
4. **Export Formats**: Support for CSV, Parquet, and Avro
5. **Query API**: REST API for querying telemetry data
6. **Dashboard**: Built-in Grafana dashboard templates

### Integration Opportunities

- **OpenTelemetry**: Replace custom metrics with OpenTelemetry SDK
- **Jaeger**: Distributed tracing integration
- **Grafana Loki**: Centralized log aggregation
- **Prometheus Remote**: Push gateway instead of pull

## Migration Notes

### From Archive to Local MVP

The telemetry system in `archive/src/ucp_original/ucp/telemetry.py` has been adapted for the local MVP:

**Removed**:
- Cloud-specific features (remote storage, multi-tenancy)
- Advanced analytics (cohort analysis, A/B testing)
- Complex reward models (only basic reward calculation kept)

**Simplified**:
- Single-tenant SQLite storage
- Basic Prometheus metrics (histogram + counters)
- JSONL export for simple log analysis
- Core telemetry events (routing, tool calls, rewards)

**Kept**:
- Core event data structures (RoutingEvent, ToolCallEvent, RewardSignal)
- SQLiteTelemetryStore with indexed tables
- RewardCalculator for online learning signals
- JSONLTelemetryExporter for log export

## Related Documentation

- [Getting Started Guide](../local/docs/getting_started.md)
- [API Reference](../shared/docs/api_reference.md)
- [Development Guide](../DEVELOPMENT_GUIDE.md)
- [Milestone 1.3: Claude Desktop Test](./milestone_1_3_claude_desktop_test.md)

## Summary

Milestone 1.4 successfully implements a comprehensive telemetry infrastructure that:

1. **Captures all relevant events**: Routing decisions, tool invocations, rewards
2. **Provides multiple storage backends**: SQLite for queries, JSONL for export, Prometheus for monitoring
3. **Enables traceability**: trace_id, session_id, request_id correlation
4. **Supports monitoring**: Prometheus-formatted metrics endpoint
5. **Maintains privacy**: Query hashing by default, no PII logging
6. **Performance optimized**: Indexed queries, batch writes, in-memory metrics

The telemetry system is production-ready and provides the foundation for:
- Data-driven optimization of routing decisions
- Performance monitoring and alerting
- Debugging and troubleshooting
- Historical analysis and reporting

