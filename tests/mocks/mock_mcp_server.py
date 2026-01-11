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
            if "error" in tool_name or tool_name.endswith(".fail") or tool_name == "mock.fail":
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
    # Define mock tools matching tasks.json expectations
    tools = [
        # Email tools
        {
            "name": "mock.send_email",
            "description": "Send an email to a recipient",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "Email address of recipient"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body content"}
                },
                "required": ["to"]
            }
        },
        {
            "name": "mock.read_inbox",
            "description": "Read and list emails from inbox",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "number", "description": "Maximum number of emails to retrieve"}
                }
            }
        },
        # Code tools
        {
            "name": "mock.create_pr",
            "description": "Create a pull request for a branch",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch name for PR"},
                    "title": {"type": "string", "description": "PR title"},
                    "description": {"type": "string", "description": "PR description"}
                },
                "required": ["branch"]
            }
        },
        {
            "name": "mock.list_commits",
            "description": "List recent commits on a branch",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch name"},
                    "limit": {"type": "number", "description": "Number of commits to list"}
                },
                "required": ["branch"]
            }
        },
        # Calendar tools
        {
            "name": "mock.create_event",
            "description": "Create a calendar event",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Event title"},
                    "start_time": {"type": "string", "description": "Event start time"},
                    "duration": {"type": "number", "description": "Duration in minutes"},
                    "attendees": {"type": "array", "items": {"type": "string"}, "description": "List of attendees"}
                }
            }
        },
        # Communication tools
        {
            "name": "mock.send_slack",
            "description": "Send a message to a Slack channel",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "channel": {"type": "string", "description": "Slack channel name"},
                    "message": {"type": "string", "description": "Message to send"}
                },
                "required": ["channel", "message"]
            }
        },
        # File tools
        {
            "name": "mock.upload_file",
            "description": "Upload a file to cloud storage",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Local file path"},
                    "destination": {"type": "string", "description": "Destination path"}
                }
            }
        },
        # Web search tools
        {
            "name": "mock.web_search",
            "description": "Search the web for information",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "num_results": {"type": "number", "description": "Number of results to return"}
                },
                "required": ["query"]
            }
        },
        # Database tools
        {
            "name": "mock.sql_query",
            "description": "Execute a SQL query against the database",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query string"},
                    "database": {"type": "string", "description": "Database name"}
                },
                "required": ["query"]
            }
        },
        # Finance tools
        {
            "name": "mock.stripe_charge",
            "description": "Process a payment using Stripe",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount in cents"},
                    "currency": {"type": "string", "description": "Currency code (e.g., 'usd')"},
                    "customer_id": {"type": "string", "description": "Customer ID"}
                },
                "required": ["amount"]
            }
        },
        # Utility tools
        {
            "name": "mock.calculate",
            "description": "Perform a calculation or evaluate expression",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Mathematical expression to evaluate"}
                },
                "required": ["expression"]
            }
        },
        {
            "name": "mock.echo",
            "description": "Echo back the input message",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to echo back"}
                },
                "required": ["message"]
            }
        },
        # Additional tools for testing context bloat
        {
            "name": "mock.list_files",
            "description": "List files in a directory",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"},
                    "recursive": {"type": "boolean", "description": "List recursively"}
                }
            }
        },
        {
            "name": "mock.read_file",
            "description": "Read contents of a file",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "mock.write_file",
            "description": "Write content to a file",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        },
        {
            "name": "mock.delete_file",
            "description": "Delete a file",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "mock.create_directory",
            "description": "Create a directory",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path"}
                },
                "required": ["path"]
            }
        },
        {
            "name": "mock.http_get",
            "description": "Make an HTTP GET request",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to request"},
                    "headers": {"type": "object", "description": "HTTP headers"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "mock.http_post",
            "description": "Make an HTTP POST request",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to request"},
                    "body": {"type": "object", "description": "Request body"},
                    "headers": {"type": "object", "description": "HTTP headers"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "mock.run_command",
            "description": "Execute a shell command",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Command to execute"},
                    "args": {"type": "array", "items": {"type": "string"}, "description": "Command arguments"}
                },
                "required": ["command"]
            }
        },
        {
            "name": "mock.git_clone",
            "description": "Clone a git repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "Repository URL"},
                    "destination": {"type": "string", "description": "Destination directory"}
                },
                "required": ["url"]
            }
        },
        {
            "name": "mock.git_pull",
            "description": "Pull latest changes from git repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch to pull"}
                }
            }
        },
        {
            "name": "mock.git_push",
            "description": "Push changes to git repository",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "branch": {"type": "string", "description": "Branch to push"}
                }
            }
        },
        {
            "name": "mock.docker_build",
            "description": "Build a Docker image",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "dockerfile": {"type": "string", "description": "Dockerfile path"},
                    "tag": {"type": "string", "description": "Image tag"}
                }
            }
        },
        {
            "name": "mock.docker_run",
            "description": "Run a Docker container",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "image": {"type": "string", "description": "Docker image name"},
                    "command": {"type": "string", "description": "Command to run"},
                    "ports": {"type": "array", "items": {"type": "string"}, "description": "Port mappings"}
                },
                "required": ["image"]
            }
        },
        {
            "name": "mock.kubectl_apply",
            "description": "Apply Kubernetes configuration",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "description": "Configuration file path"},
                    "namespace": {"type": "string", "description": "Kubernetes namespace"}
                }
            }
        },
        {
            "name": "mock.kubectl_get",
            "description": "Get Kubernetes resources",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "resource": {"type": "string", "description": "Resource type (pods, services, etc.)"},
                    "namespace": {"type": "string", "description": "Kubernetes namespace"}
                },
                "required": ["resource"]
            }
        },
        {
            "name": "mock.aws_s3_upload",
            "description": "Upload file to AWS S3",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "bucket": {"type": "string", "description": "S3 bucket name"},
                    "key": {"type": "string", "description": "S3 object key"},
                    "file_path": {"type": "string", "description": "Local file path"}
                },
                "required": ["bucket", "key", "file_path"]
            }
        },
        {
            "name": "mock.aws_ec2_start",
            "description": "Start an EC2 instance",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "instance_id": {"type": "string", "description": "EC2 instance ID"}
                },
                "required": ["instance_id"]
            }
        },
        {
            "name": "mock.aws_lambda_invoke",
            "description": "Invoke an AWS Lambda function",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "function_name": {"type": "string", "description": "Lambda function name"},
                    "payload": {"type": "object", "description": "Function payload"}
                },
                "required": ["function_name"]
            }
        },
        {
            "name": "mock.fail",
            "description": "Always fails for testing error handling",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        }
    ]
    
    server = MockMCPServer("mock-server", tools)
    asyncio.run(server.run())
