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
    from ucp_core.config import UCPConfig
    from ucp_mvp.server import UCPServer

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
    from ucp_core.config import UCPConfig
    from ucp_mvp.server import UCPServer

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
    from ucp_core.config import UCPConfig
    from ucp_mvp.connection_pool import ConnectionPool
    from ucp_mvp.tool_zoo import HybridToolZoo

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
    from ucp_core.config import UCPConfig
    from ucp_mvp.tool_zoo import HybridToolZoo

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


def main() -> None:
    """Main CLI entry point."""
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
