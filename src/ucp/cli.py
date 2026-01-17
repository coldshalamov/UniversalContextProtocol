"""
UCP Command Line Interface.

Provides commands for:
- Running the UCP server
- Managing configuration
- Debugging and diagnostics
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import structlog


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging."""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.dev.ConsoleRenderer() if sys.stderr.isatty() else structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    import logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=getattr(logging, level.upper()),
    )


def cmd_serve(args: argparse.Namespace) -> None:
    """Run the UCP server."""
    from ucp.config import UCPConfig
    from ucp.server import UCPServer

    setup_logging(args.log_level)
    logger = structlog.get_logger(__name__)

    # Load config
    config = UCPConfig.load(args.config)

    if args.log_level:
        config.log_level = args.log_level.upper()

    logger.info(
        "starting_ucp_server",
        transport=config.server.transport,
        downstream_count=len(config.downstream_servers),
    )

    # Create and run server
    server = UCPServer(config)

    if config.server.transport == "stdio":
        asyncio.run(server.run_stdio())
    else:
        logger.error("transport_not_implemented", transport=config.server.transport)
        sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:
    """Show UCP status."""
    from ucp.config import UCPConfig
    from ucp.server import UCPServer

    setup_logging("WARNING")

    config = UCPConfig.load(args.config)
    server = UCPServer(config)

    # Initialize without running
    asyncio.run(server.initialize())
    status = server.get_status()

    print(json.dumps(status, indent=2, default=str))

    asyncio.run(server.shutdown())


def cmd_index(args: argparse.Namespace) -> None:
    """Index tools from downstream servers."""
    from ucp.config import UCPConfig
    from ucp.connection_pool import ConnectionPool
    from ucp.tool_zoo import HybridToolZoo

    setup_logging(args.log_level)
    logger = structlog.get_logger(__name__)

    config = UCPConfig.load(args.config)

    async def do_index():
        # Connect to servers
        pool = ConnectionPool(config)
        await pool.connect_all()

        # Index tools
        zoo = HybridToolZoo(config.tool_zoo)
        zoo.initialize()

        tools = pool.all_tools
        if tools:
            zoo.add_tools(tools)
            logger.info("tools_indexed", count=len(tools))

            # Print tool list
            for tool in tools:
                print(f"  {tool.name}: {tool.description[:60]}...")
        else:
            logger.warning("no_tools_found")

        await pool.disconnect_all()

    asyncio.run(do_index())


def cmd_search(args: argparse.Namespace) -> None:
    """Search for tools by query."""
    from ucp.config import UCPConfig
    from ucp.tool_zoo import HybridToolZoo

    setup_logging("WARNING")

    config = UCPConfig.load(args.config)
    zoo = HybridToolZoo(config.tool_zoo)
    zoo.initialize()

    if args.hybrid:
        results = zoo.hybrid_search(args.query, top_k=args.top_k)
    else:
        results = zoo.search(args.query, top_k=args.top_k)

    print(f"\nSearch results for: '{args.query}'\n")

    for tool, score in results:
        print(f"  [{score:.3f}] {tool.name}")
        print(f"          {tool.description[:80]}")
        if tool.tags:
            print(f"          Tags: {', '.join(tool.tags)}")
        print()


def cmd_init_config(args: argparse.Namespace) -> None:
    """Generate a sample configuration file."""
    sample_config = """# UCP Configuration
# See docs/ucp_design_plan.md for architecture details

server:
  name: "UCP Gateway"
  version: "0.1.0"
  transport: stdio  # stdio, sse, or streamable-http
  host: "127.0.0.1"
  port: 8765

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  collection_name: "ucp_tools"
  persist_directory: "./data/chromadb"
  top_k: 5
  similarity_threshold: 0.3

router:
  mode: hybrid  # semantic, keyword, or hybrid
  rerank: true
  max_tools: 10
  min_tools: 1
  fallback_tools: []

session:
  persistence: sqlite  # memory, sqlite, or redis
  sqlite_path: "./data/sessions.db"
  ttl_seconds: 3600
  max_messages: 100

log_level: INFO

# Downstream MCP servers to connect to
downstream_servers:
  # Example: File system server
  # - name: filesystem
  #   transport: stdio
  #   command: npx
  #   args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
  #   tags: [files, local]
  #   description: "Local file system access"

  # Example: GitHub server
  # - name: github
  #   transport: stdio
  #   command: npx
  #   args: ["-y", "@modelcontextprotocol/server-github"]
  #   env:
  #     GITHUB_PERSONAL_ACCESS_TOKEN: "your-token"
  #   tags: [code, git, github]
  #   description: "GitHub repository operations"

  # Example: Brave search
  # - name: brave-search
  #   transport: stdio
  #   command: npx
  #   args: ["-y", "@modelcontextprotocol/server-brave-search"]
  #   env:
  #     BRAVE_API_KEY: "your-api-key"
  #   tags: [search, web]
  #   description: "Web search via Brave"
"""

    output_path = Path(args.output)
    output_path.write_text(sample_config)
    print(f"Created sample config at: {output_path}")


def cmd_registry_list(args: argparse.Namespace) -> None:
    """List all MCPs in the registry."""
    from ucp.config import UCPConfig
    from ucp.tool_zoo import RegistryToolZoo
    
    setup_logging("WARNING")
    
    # Load config to get tool_zoo settings
    try:
        config = UCPConfig.load(args.config)
        tool_zoo_config = config.tool_zoo
    except Exception:
        # Use defaults if config doesn't exist
        from ucp.config import ToolZooConfig
        tool_zoo_config = ToolZooConfig()
    
    # Load registry
    zoo = RegistryToolZoo(tool_zoo_config)
    count = zoo.load_registry(args.registry_file)
    
    if count == 0:
        print(f"No MCPs found in {args.registry_file}")
        return
    
    # Get entries
    entries = zoo.get_all_registry_entries()
    
    # Apply filters
    if args.category:
        entries = [e for e in entries if args.category in [c.value for c in e.categories]]
    if args.tag:
        entries = [e for e in entries if args.tag in e.tags]
    
    # Display
    print(f"\n{'='*80}")
    print(f"MCP Registry ({len(entries)} MCPs)")
    print(f"{'='*80}\n")
    
    for entry in entries:
        enabled = "✓" if entry.enabled_by_default else " "
        categories = ", ".join([c.value for c in entry.categories])
        print(f"[{enabled}] {entry.display_name} ({entry.name})")
        print(f"    {entry.description}")
        print(f"    Categories: {categories}")
        if entry.tags:
            print(f"    Tags: {', '.join(entry.tags[:5])}")
        print()
    
    print(f"Total: {len(entries)} MCPs")
    if args.category or args.tag:
        print(f"(Filtered from {count} total MCPs)")
    print()


def cmd_registry_search(args: argparse.Namespace) -> None:
    """Search registry by query."""
    from ucp.config import UCPConfig
    from ucp.tool_zoo import RegistryToolZoo
    
    setup_logging("WARNING")
    
    # Load config
    try:
        config = UCPConfig.load(args.config)
        tool_zoo_config = config.tool_zoo
    except Exception:
        from ucp.config import ToolZooConfig
        tool_zoo_config = ToolZooConfig()
    
    # Load registry
    zoo = RegistryToolZoo(tool_zoo_config)
    zoo.load_registry(args.registry_file)
    
    # Search
    results = zoo.search_by_use_case(args.query, top_k=args.top_k)
    
    # Display
    print(f"\n{'='*80}")
    print(f"Search results for: '{args.query}'")
    print(f"{'='*80}\n")
    
    if not results:
        print("No results found.")
        print("\nTry:")
        print("  - Using different keywords")
        print("  - Searching by category: ucp registry list --category code")
        print("  - Browsing all MCPs: ucp registry list")
        return
    
    for i, entry in enumerate(results, 1):
        print(f"{i}. {entry.display_name} ({entry.name})")
        print(f"   {entry.description}")
        print(f"   Install: {entry.install_command}")
        if entry.use_cases:
            print(f"   Use cases: {', '.join(entry.use_cases[:3])}")
        print()


def cmd_registry_show(args: argparse.Namespace) -> None:
    """Show detailed information for an MCP."""
    from ucp.config import UCPConfig
    from ucp.tool_zoo import RegistryToolZoo
    
    setup_logging("WARNING")
    
    # Load config
    try:
        config = UCPConfig.load(args.config)
        tool_zoo_config = config.tool_zoo
    except Exception:
        from ucp.config import ToolZooConfig
        tool_zoo_config = ToolZooConfig()
    
    # Load registry
    zoo = RegistryToolZoo(tool_zoo_config)
    zoo.load_registry(args.registry_file)
    
    # Get entry
    entry = zoo.get_registry_entry(args.name)
    
    if not entry:
        print(f"MCP '{args.name}' not found in registry.")
        print(f"\nAvailable MCPs:")
        for e in zoo.get_all_registry_entries()[:10]:
            print(f"  - {e.name}")
        return
    
    # Display detailed information
    print(f"\n{'='*80}")
    print(f"{entry.display_name}")
    print(f"{'='*80}\n")
    
    print(f"Name:        {entry.name}")
    print(f"Version:     {entry.version}")
    print(f"Author:      {entry.author}")
    print(f"Enabled:     {'Yes' if entry.enabled_by_default else 'No'}")
    print()
    
    print(f"Description:")
    print(f"  {entry.description}")
    if entry.long_description:
        print(f"\n  {entry.long_description}")
    print()
    
    print(f"Categories:  {', '.join([c.value for c in entry.categories])}")
    print(f"Tags:        {', '.join(entry.tags)}")
    print()
    
    print(f"Installation:")
    print(f"  {entry.install_command}")
    print()
    
    if entry.use_cases:
        print(f"Use Cases:")
        for uc in entry.use_cases:
            print(f"  • {uc}")
        print()
    
    if entry.example_queries:
        print(f"Example Queries:")
        for eq in entry.example_queries:
            print(f"  • \"{eq}\"")
        print()
    
    if entry.works_well_with:
        print(f"Works well with: {', '.join(entry.works_well_with)}")
    if entry.similar_tools:
        print(f"Similar tools:   {', '.join(entry.similar_tools)}")
    print()




def cmd_init_config(args: argparse.Namespace) -> None:
    """Generate a sample configuration file."""
    sample_config = """# UCP Configuration
# See docs/ucp_design_plan.md for architecture details

server:
  name: "UCP Gateway"
  version: "0.1.0"
  transport: stdio  # stdio, sse, or streamable-http
  host: "127.0.0.1"
  port: 8765

tool_zoo:
  embedding_model: "all-MiniLM-L6-v2"
  collection_name: "ucp_tools"
  persist_directory: "./data/chromadb"
  top_k: 5
  similarity_threshold: 0.3

router:
  mode: hybrid  # semantic, keyword, or hybrid
  rerank: true
  max_tools: 10
  min_tools: 1
  fallback_tools: []

session:
  persistence: sqlite  # memory, sqlite, or redis
  sqlite_path: "./data/sessions.db"
  ttl_seconds: 3600
  max_messages: 100

log_level: INFO

# Downstream MCP servers to connect to
downstream_servers:
  # Example: File system server
  # - name: filesystem
  #   transport: stdio
  #   command: npx
  #   args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
  #   tags: [files, local]
  #   description: "Local file system access"

  # Example: GitHub server
  # - name: github
  #   transport: stdio
  #   command: npx
  #   args: ["-y", "@modelcontextprotocol/server-github"]
  #   env:
  #     GITHUB_PERSONAL_ACCESS_TOKEN: "your-token"
  #   tags: [code, git, github]
  #   description: "GitHub repository operations"

  # Example: Brave search
  # - name: brave-search
  #   transport: stdio
  #   command: npx
  #   args: ["-y", "@modelcontextprotocol/server-brave-search"]
  #   env:
  #     BRAVE_API_KEY: "your-api-key"
  #   tags: [search, web]
  #   description: "Web search via Brave"
"""

    output_path = Path(args.output)
    output_path.write_text(sample_config)
    print(f"Created sample config at: {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ucp",
        description="Universal Context Protocol - Intelligent Tool Gateway",
    )
    parser.add_argument(
        "-c", "--config",
        help="Path to config file (default: ucp_config.yaml)",
        default=None,
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Run the UCP server")
    serve_parser.set_defaults(func=cmd_serve)

    # status command
    status_parser = subparsers.add_parser("status", help="Show UCP status")
    status_parser.set_defaults(func=cmd_status)

    # index command
    index_parser = subparsers.add_parser("index", help="Index tools from downstream servers")
    index_parser.set_defaults(func=cmd_index)

    # search command
    search_parser = subparsers.add_parser("search", help="Search for tools")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("-k", "--top-k", type=int, default=5, help="Number of results")
    search_parser.add_argument("--hybrid", action="store_true", help="Use hybrid search")
    search_parser.set_defaults(func=cmd_search)

    # registry commands
    registry_parser = subparsers.add_parser("registry", help="Manage MCP registry")
    registry_subparsers = registry_parser.add_subparsers(dest="registry_command", help="Registry commands")
    
    # registry list
    registry_list_parser = registry_subparsers.add_parser("list", help="List all MCPs in registry")
    registry_list_parser.add_argument("--category", help="Filter by category")
    registry_list_parser.add_argument("--tag", help="Filter by tag")
    registry_list_parser.add_argument("--registry-file", default="./data/registry_seed.yaml", help="Registry file path")
    registry_list_parser.set_defaults(func=cmd_registry_list)
    
    # registry search
    registry_search_parser = registry_subparsers.add_parser("search", help="Search registry")
    registry_search_parser.add_argument("query", help="Search query")
    registry_search_parser.add_argument("-k", "--top-k", type=int, default=5, help="Number of results")
    registry_search_parser.add_argument("--registry-file", default="./data/registry_seed.yaml", help="Registry file path")
    registry_search_parser.set_defaults(func=cmd_registry_search)
    
    # registry show
    registry_show_parser = registry_subparsers.add_parser("show", help="Show details for an MCP")
    registry_show_parser.add_argument("name", help="MCP name")
    registry_show_parser.add_argument("--registry-file", default="./data/registry_seed.yaml", help="Registry file path")
    registry_show_parser.set_defaults(func=cmd_registry_show)

    # init-config command
    init_parser = subparsers.add_parser("init-config", help="Generate sample config")
    init_parser.add_argument("-o", "--output", default="ucp_config.yaml", help="Output path")
    init_parser.set_defaults(func=cmd_init_config)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
