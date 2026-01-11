import asyncio
import sys
sys.path.insert(0, 'D:/GitHub/Telomere/UniversalContextProtocol/local/src')
sys.path.insert(0, 'D:/GitHub/Telomere/UniversalContextProtocol/shared/src')

async def main():
    print("Testing UCP with filesystem and GitHub servers...")
    
    from ucp_mvp.connection_pool import ConnectionPool
    from ucp_core.config import UCPConfig
    
    # Load config
    config = UCPConfig.load('D:/GitHub/Telomere/UniversalContextProtocol/ucp_config.yaml')
    print(f"Loaded config with {len(config.downstream_servers)} servers")
    
    # Create connection pool
    pool = ConnectionPool(config)
    
    # Connect to all servers
    print("\nConnecting to all servers...")
    await pool.connect_all()
    
    # List tools
    tools = pool.all_tools
    print(f"\nFound {len(tools)} tools from all servers:")
    for tool in tools:
        print(f"  - {tool.name} (server: {tool.server_name})")
    
    # Test calling a filesystem tool
    print("\nTesting filesystem.read_text_file tool...")
    result = await pool.call_tool('read_text_file', {
        'path': 'D:/GitHub/Telomere/UniversalContextProtocol/README.md'
    })
    print(f"Result: {result.content[0].text[:100]}...")
    
    # Cleanup
    await pool.disconnect_all()
    print("\nTest completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())
