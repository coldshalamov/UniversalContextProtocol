# Failure Mode Documentation for Universal Context Protocol

This document describes the failure scenarios tested in Milestone 1.6,
expected behaviors, and recovery strategies implemented in UCP.

## Overview

UCP implements graceful degradation patterns to handle various failure scenarios
that can occur during operation. The system is designed to never crash and always
provide meaningful feedback to users and AI models.

## Failure Scenarios

### 1. Downstream MCP Server Crashes Mid-Conversation

**Description:** A downstream MCP server unexpectedly terminates during an active conversation.

**Expected Behavior:**
- Connection pool detects the crash through exception handling
- Server is marked as ERROR status with error message
- Circuit breaker for that server is triggered
- Subsequent tool calls to that server are rejected with clear error message
- Session continues operating with other available servers
- No crash or unhandled exception

**Recovery Strategy:**
- Circuit breaker opens after threshold (default: 5 consecutive failures)
- Automatic reconnection attempts with exponential backoff (1s, 2s, 4s, etc.)
- Server status is monitored and updated on each reconnection attempt
- Failed tool calls are logged to telemetry for analysis
- User receives error message: "Circuit breaker is open for server X. Too many consecutive failures. Will retry after timeout."

**Implementation:**
- [`CircuitBreaker`](../src/ucp/connection_pool.py) class tracks failures per server
- [`ConnectionPool._reconnect_server()`](../src/ucp/connection_pool.py) handles reconnection
- Retry logic in [`ConnectionPool.call_tool()`](../src/ucp/connection_pool.py) with exponential backoff

---

### 2. Downstream Server Returns Malformed JSON

**Description:** A downstream MCP server returns invalid or malformed JSON response.

**Expected Behavior:**
- JSON parsing error is caught and handled gracefully
- Server is marked as ERROR status
- Tool call fails with descriptive error message
- No crash or unhandled exception
- Error is logged to telemetry
- Session continues operating

**Recovery Strategy:**
- Circuit breaker records the failure
- Retry with exponential backoff (up to 3 attempts by default)
- If all retries fail, return clear error to caller
- Error message includes context about what was attempted
- User receives error with tool name and parameters

**Implementation:**
- Exception handling in [`ConnectionPool.call_tool()`](../src/ucp/connection_pool.py) catches all exceptions
- Each exception type is logged appropriately
- Retry loop attempts reconnection before giving up
- [`UCPServer._format_error_for_self_correction()`](../src/ucp/server.py) provides helpful error context

---

### 3. Downstream Server Times Out (>30s)

**Description:** A downstream MCP server does not respond within the timeout period.

**Expected Behavior:**
- `asyncio.TimeoutError` is caught after 30 seconds
- Server is marked as ERROR status
- Circuit breaker records the timeout as a failure
- Tool call fails with timeout error message
- No crash or unhandled exception
- User receives clear timeout message

**Recovery Strategy:**
- Circuit breaker opens after consecutive timeouts
- Retry with exponential backoff
- Timeout duration is configurable (default: 30 seconds)
- If server consistently times out, circuit breaker prevents further attempts
- User receives error: "Tool call failed after N attempts: tool_name"

**Implementation:**
- Timeout wrapper in [`ConnectionPool.call_tool()`](../src/ucp/connection_pool.py):
  ```python
  result = await asyncio.wait_for(
      session.call_tool(downstream_tool_name, arguments),
      timeout=30.0  # 30 second timeout
  )
  ```
- Timeout is caught as `asyncio.TimeoutError` and handled gracefully
- Circuit breaker tracks timeout failures same as other failures

---

### 4. Router Fails to Find Relevant Tools

**Description:** The semantic search or tool zoo fails to find relevant tools.

**Expected Behavior:**
- Router catches the exception from search failure
- Falls back to keyword search if available
- If keyword search also fails, uses fallback tools
- Returns a routing decision with available tools
- No crash or unhandled exception
- Reasoning includes which search method was used

**Recovery Strategy:**
- Primary search method (semantic/hybrid) is attempted first
- On failure, keyword search is attempted as fallback
- If all search methods fail, configured fallback tools are returned
- Minimum tool count is enforced (default: 1 tool)
- User receives tools even if search fails
- Router continues functioning for subsequent requests

**Implementation:**
- Try-catch in [`Router.route()`](../src/ucp/router.py):
  ```python
  try:
      results = self.tool_zoo.search(query, top_k=self.config.max_tools * 2)
  except Exception as e:
      logger.warning("primary_search_failed", method=search_method, error=str(e))
      # Fallback to keyword search
      if hasattr(self.tool_zoo, "keyword_search"):
          results = self.tool_zoo.keyword_search(query, top_k=self.config.max_tools * 2)
  ```
- Multiple fallback levels ensure some tools are always available

---

### 5. Tool Call with Invalid Arguments

**Description:** User or AI model attempts to call a tool with incorrect or missing arguments.

**Expected Behavior:**
- Tool schema validation catches invalid arguments
- Clear error message is returned describing the problem
- Available parameters are listed to help user correct the call
- Tool is not executed
- No crash or unhandled exception
- User receives helpful error message with suggestions

**Recovery Strategy:**
- Error message includes:
  - Tool name and description
  - What parameters are available
  - What was attempted
  - Suggestions for fixing the issue
- AI model can use this information to retry with correct parameters
- Session continues normally
- Error is logged to telemetry for analysis

**Implementation:**
- Error formatting in [`UCPServer._format_error_for_self_correction()`](../src/ucp/server.py):
  ```python
  def _format_error_for_self_correction(
      self, tool_name: str, arguments: dict[str, Any], error: str
  ) -> str:
      error_parts = [
          f"Error calling tool '{tool_name}':",
          f"  {error}",
      ]
      
      # Add tool information for context
      if tool_schema:
          error_parts.append(f"  Tool description: {tool_schema.description}")
          if tool_schema.input_schema and tool_schema.input_schema.get("properties"):
              params = list(tool_schema.input_schema["properties"].keys())
              error_parts.append(f"  Available parameters: {', '.join(params)}")
      
      # Suggest potential fixes
      error_parts.append("  Please try again with:")
      error_parts.append("    - Different or corrected arguments")
      error_parts.append("    - A different tool if this one is unavailable")
      
      return "\n".join(error_parts)
  ```
- Special handling for "tool not found" errors with available tools list

---

## Circuit Breaker Pattern

### Overview

The circuit breaker pattern prevents cascading failures by temporarily stopping
requests to a failing server after a threshold of consecutive failures.

### States

1. **CLOSED**: Normal operation, all requests allowed
2. **OPEN**: Circuit is open, rejecting requests after threshold failures
3. **HALF_OPEN**: Testing if service has recovered, allowing limited requests

### Configuration

- **Failure Threshold**: 5 consecutive failures (configurable)
- **Timeout**: 60 seconds before attempting half-open (configurable)
- **Half-Open Max Calls**: 3 test calls before closing circuit (configurable)

### Behavior

- Each failure increments failure counter
- Each success resets failure counter
- After threshold, circuit opens and rejects requests
- After timeout, transitions to half-open for testing
- After successful half-open calls, circuit closes

### Monitoring

Circuit breaker state is exposed via [`ConnectionPool.get_server_status()`](../src/ucp/connection_pool.py):
```python
{
    "server_name": {
        "status": "connected",
        "tool_count": 5,
        "circuit_breaker": {
            "state": "closed",  # or "open" or "half_open"
            "failure_count": 0,
            "can_attempt": true
        }
    }
}
```

---

## Graceful Degradation Features

### Router Fallback

**Multi-Level Fallback:**
1. Primary: Semantic/hybrid search
2. Secondary: Keyword search
3. Tertiary: Fallback tools from config
4. Quaternary: All available tools (last resort)

**Fallback Triggers:**
- Primary search throws exception
- Primary search returns no results
- Tool zoo is unavailable

### Connection Pool Resilience

**Retry Logic:**
- Maximum retries: 3 (configurable)
- Exponential backoff: 1s, 2s, 4s (base * 2^attempt)
- Timeout per attempt: 30 seconds (configurable)

**Reconnection:**
- Automatic on server crash
- Cleanup of existing connections
- Fresh connection attempt
- Status tracking through reconnection

### Error Injection

**Self-Correction Support:**
- Errors include tool schema information
- Available parameters are listed
- Attempted arguments are shown
- Suggestions for fixing the issue are provided
- Enables AI model to understand and correct its mistakes

---

## Testing

Comprehensive tests are provided in [`tests/test_failure_modes.py`](../tests/test_failure_modes.py):

### Test Coverage

1. **Circuit Breaker Tests** ([`TestCircuitBreaker`](../tests/test_failure_modes.py))
   - Initial state verification
   - Opens after threshold failures
   - Transitions to half-open after timeout
   - Closes after successful calls
   - Reopens on half-open failure
   - State retrieval

2. **Router Failure Tests** ([`TestRouterFailureModes`](../tests/test_failure_modes.py))
   - Fallback to keyword search on semantic search failure
   - Returns fallback tools on empty context
   - Handles tool zoo search failure gracefully

3. **Connection Pool Failure Tests** ([`TestConnectionPoolFailureModes`](../tests/test_failure_modes.py))
   - Handles tool call timeout gracefully
   - Retries with exponential backoff
   - Circuit breaker blocks requests when open

4. **Server Error Injection Tests** ([`TestServerErrorInjection`](../tests/test_failure_modes.py))
   - Injects error context on tool failure
   - Handles tool not found gracefully
   - Includes available tools in error message

5. **Integration Failure Tests** ([`TestIntegrationFailureScenarios`](../tests/test_failure_modes.py))
   - Server crash mid-conversation
   - Malformed JSON response handling
   - Multiple consecutive failures

### Running Tests

```bash
# Run all failure mode tests
python -m pytest tests/test_failure_modes.py -v

# Run specific test class
python -m pytest tests/test_failure_modes.py::TestCircuitBreaker -v
python -m pytest tests/test_failure_modes.py::TestRouterFailureModes -v
python -m pytest tests/test_failure_modes.py::TestConnectionPoolFailureModes -v
python -m pytest tests/test_failure_modes.py::TestServerErrorInjection -v
```

---

## Success Criteria

✅ **UCP handles 5 failure modes without crashing**
   - All failure scenarios are caught and handled
   - No unhandled exceptions propagate to top level
   - System continues operating after failures

✅ **Graceful degradation implemented for each scenario**
   - Router: Multi-level fallback (semantic → keyword → fallback tools)
   - Connection Pool: Retry with backoff, circuit breaker, reconnection
   - Server: Error injection with helpful context for self-correction

✅ **Circuit breaker pattern added to connection_pool.py**
   - Full implementation with CLOSED, OPEN, HALF_OPEN states
   - Configurable thresholds and timeouts
   - State monitoring and reporting

✅ **All failure mode tests pass**
   - Circuit breaker tests verify state transitions
   - Router tests verify fallback behavior
   - Connection pool tests verify retry logic
   - Server tests verify error injection
   - Integration tests verify end-to-end scenarios

✅ **Failure modes documented**
   - Each scenario has detailed documentation
   - Expected behaviors are clearly specified
   - Recovery strategies are explained
   - Implementation references are provided

---

## Monitoring and Debugging

### Server Status

The [`UCPServer.get_status()`](../src/ucp/server.py) method provides comprehensive status:

```python
{
    "server": {"name": "ucp", "version": "0.1.0"},
    "downstream_servers": {
        "server1": {
            "status": "connected",
            "circuit_breaker": {
                "state": "closed",
                "failure_count": 0,
                "can_attempt": true
            }
        }
    },
    "tool_zoo": {"total_tools": 25, "indexed": true},
    "router": {
        "predictions": 150,
        "avg_precision": 0.85,
        "avg_recall": 0.92
    }
}
```

### Telemetry

All failures are logged to telemetry store:
- Tool call failures (timeout, error, not found)
- Server connection failures
- Circuit breaker state changes
- Router search failures and fallbacks

This enables post-mortem analysis and continuous improvement.

---

## Best Practices

### For Users

1. **Monitor circuit breaker state**: Check server status if tools are failing
2. **Review error messages**: Error messages include suggestions for fixing issues
3. **Use appropriate tools**: Error messages suggest alternative tools when one is unavailable
4. **Allow retries**: System will automatically retry failed operations

### For Developers

1. **Configure thresholds**: Adjust circuit breaker thresholds for your use case
2. **Monitor telemetry**: Review failure patterns to identify problematic servers
3. **Test failure scenarios**: Use provided tests to verify graceful degradation
4. **Add fallback tools**: Configure fallback tools for critical operations
5. **Adjust timeouts**: Tune timeout values based on server performance

---

## Conclusion

UCP's failure mode handling ensures:
- **Resilience**: System continues operating despite failures
- **Transparency**: Clear error messages inform users of issues
- **Recovery**: Automatic retry and fallback mechanisms
- **Observability**: Comprehensive logging and status reporting
- **No Crashes**: All exceptions are caught and handled gracefully

The system is production-ready for handling real-world failure scenarios.
