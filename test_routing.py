import asyncio
import sys
import os

# Change to project directory
os.chdir('D:/GitHub/Telomere/UniversalContextProtocol')
sys.path.insert(0, 'D:/GitHub/Telomere/UniversalContextProtocol/local/src')
sys.path.insert(0, 'D:/GitHub/Telomere/UniversalContextProtocol/shared/src')

async def main():
    print("Testing UCP routing with filesystem and GitHub servers...")
    
    from ucp_mvp.connection_pool import ConnectionPool
    from ucp_mvp.router import Router
    from ucp_mvp.tool_zoo import HybridToolZoo
    from ucp_core.config import UCPConfig
    
    # Load config
    config = UCPConfig.load('D:/GitHub/Telomere/UniversalContextProtocol/ucp_config.yaml')
    print(f"Loaded config with {len(config.downstream_servers)} servers")
    
    # Create connection pool
    pool = ConnectionPool(config)
    
    # Connect to all servers
    print("\nConnecting to all servers...")
    await pool.connect_all()
    
    # Create tool zoo
    tool_zoo = HybridToolZoo(config.tool_zoo)
    tool_zoo.initialize()
    
    # Index tools from connection pool
    tools = pool.all_tools
    await tool_zoo.index_tools(tools)
    print(f"\nIndexed {len(tools)} tools in tool zoo")
    
    # Create router
    router = Router(config.router, tool_zoo)
    
    # Test routing for GitHub issue query
    query = "I need to create a GitHub issue"
    print(f"\nTest 1: Query: '{query}'")
    routing_decision = await router.route(query, session_id="test_session")
    
    print(f"Selected {len(routing_decision.tools)} tools:")
    for tool in routing_decision.tools:
        print(f"  - {tool.name} (server: {tool.server_name})")
    
    # Check if GitHub tools are included
    github_tools = [t for t in routing_decision.tools if t.server_name == "github"]
    print(f"\nGitHub tools in result: {len(github_tools)}")
    for tool in github_tools:
        print(f"  - {tool.name}")
    
    # Test routing for filesystem query
    query2 = "I need to read a file"
    print(f"\nTest 2: Query: '{query2}'")
    routing_decision2 = await router.route(query2, session_id="test_session")
    
    print(f"Selected {len(routing_decision2.tools)} tools:")
    for tool in routing_decision2.tools:
        print(f"  - {tool.name} (server: {tool.server_name})")
    
    # Check if filesystem tools are included
    fs_tools = [t for t in routing_decision2.tools if t.server_name == "filesystem"]
    print(f"\nFilesystem tools in result: {len(fs_tools)}")
    for tool in fs_tools:
        print(f"  - {tool.name}")
    
    # Cleanup
    await pool.disconnect_all()
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
