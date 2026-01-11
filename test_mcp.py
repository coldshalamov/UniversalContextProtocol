import asyncio
import sys

async def main():
    print("Testing filesystem MCP server connection...")
    
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    
    server_params = StdioServerParameters(
        command='npx',
        args=['-y', '@modelcontextprotocol/server-filesystem', 'D:/GitHub/Telomere/UniversalContextProtocol'],
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools_result = await session.list_tools()
            print(f"Connected! Found {len(tools_result.tools)} tools:")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description[:60]}")
            print(f"\nTotal: {len(tools_result.tools)} tools from filesystem server")

if __name__ == "__main__":
    asyncio.run(main())
