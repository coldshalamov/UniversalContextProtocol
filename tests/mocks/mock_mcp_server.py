import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional

# Set up logging to stderr so it doesn't interfere with stdio communication
logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger("mock_mcp")

class MockMCPServer:
    def __init__(self, name: str, tools: List[Dict[str, Any]]):
        self.name = name
        self.tools = tools
        self.logger = logger

    async def run(self):
        """Run the mock MCP server loop."""
        self.logger.info(f"Starting Mock MCP Server: {self.name}")
        
        # Simple JSON-RPC over stdio loop
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                
                request = json.loads(line)
                self.logger.info(f"Received request: {request}")
                
                response = await self.handle_request(request)
                if response:
                    print(json.dumps(response), flush=True)
                    
            except json.JSONDecodeError:
                self.logger.error("Failed to decode JSON")
                continue
            except Exception as e:
                self.logger.error(f"Error: {e}")
                break

    async def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        msg_type = request.get("method")
        msg_id = request.get("id")
        
        if not msg_type or msg_id is None:
            return None

        response = {
            "jsonrpc": "2.0",
            "id": msg_id,
        }

        if msg_type == "initialize":
            response["result"] = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": self.name,
                    "version": "0.1.0"
                }
            }
        
        elif msg_type == "notifications/initialized":
             # Notification, no response needed
             return None

        elif msg_type == "tools/list":
            response["result"] = {
                "tools": self.tools
            }

        elif msg_type == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            args = params.get("arguments", {})
            
            # Simple mock execution
            result_content = [{"type": "text", "text": f"Executed {tool_name} with {args}"}]
            
            # Allow controlling errors via tool name
            if "error" in tool_name:
                response["error"] = {
                    "code": -32000,
                    "message": "Tool execution failed intentionally"
                }
            else:
                response["result"] = {
                    "content": result_content,
                    "isError": False
                }

        else:
             response["error"] = {
                 "code": -32601,
                 "message": "Method not found"
             }

        return response

if __name__ == "__main__":
    # Define some mock tools
    tools = [
        {
            "name": "mock.echo",
            "description": "Echoes back the input",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        },
        {
            "name": "mock.calculate",
            "description": "Perform a calculation",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        },
        {
             "name": "mock.fail",
             "description": "Always fails",
             "inputSchema": {
                 "type": "object",
                 "properties": {}
             }
        }
    ]
    
    server = MockMCPServer("mock-server", tools)
    asyncio.run(server.run())
