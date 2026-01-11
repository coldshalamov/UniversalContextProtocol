"""
Simple test to verify mock MCP server tool discovery.
"""
import asyncio
import json
import sys
import os

# Add src to path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, os.path.join(repo_root, "src"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mock_server():
    """Test connecting to mock MCP server and listing tools."""
    mock_server_path = os.path.abspath(
        os.path.join(repo_root, "tests/mocks/mock_mcp_server.py")
    )
    
    print(f"Testing mock server: {mock_server_path}")
    
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[mock_server_path],
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize session
                print("Initializing session...")
                await session.initialize()
                
                # List tools
                print("Listing tools...")
                tools_result = await session.list_tools()
                
                print(f"\nFound {len(tools_result.tools)} tools:")
                for tool in tools_result.tools:
                    print(f"  - {tool.name}: {tool.description}")
                
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_mock_server())
