#!/usr/bin/env python3
"""
Test script for Milestone 1.3: End-to-End Claude Desktop Test

This script simulates Claude Desktop interactions with UCP to validate:
- Server connectivity
- Tool discovery
- Domain detection
- Tool injection
- Context switching
- Session recording

Usage:
    python tests/test_claude_desktop_integration.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from ucp_core.config import UCPConfig
    from ucp_mvp.connection_pool import ConnectionPool
    from ucp_mvp.tool_zoo import HybridToolZoo
    from ucp_mvp.router import create_router
    from ucp_mvp.session import SessionManager
    from ucp_mvp.server import UCPServer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure UCP is installed: pip install -e .")
    sys.exit(1)


class TestResult:
    """Track test results."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def pass_test(self, test_name: str, message: str = ""):
        """Record a passed test."""
        self.passed.append((test_name, message))
        print(f"✅ PASS: {test_name}")
        if message:
            print(f"   {message}")
    
    def fail_test(self, test_name: str, error: str):
        """Record a failed test."""
        self.failed.append((test_name, error))
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {error}")
    
    def warn_test(self, test_name: str, message: str):
        """Record a warning."""
        self.warnings.append((test_name, message))
        print(f"⚠️  WARN: {test_name}")
        print(f"   {message}")
    
    def summary(self) -> str:
        """Generate test summary."""
        total = len(self.passed) + len(self.failed)
        passed = len(self.passed)
        failed = len(self.failed)
        warnings = len(self.warnings)
        
        summary = f"""
{'='*60}
Test Summary
{'='*60}
Total Tests: {total}
Passed: {passed} ✅
Failed: {failed} ❌
Warnings: {warnings} ⚠️
"""
        
        if self.failed:
            summary += "\nFailed Tests:\n"
            for name, error in self.failed:
                summary += f"  - {name}: {error}\n"
        
        if self.warnings:
            summary += "\nWarnings:\n"
            for name, message in self.warnings:
                summary += f"  - {name}: {message}\n"
        
        return summary


class ClaudeDesktopSimulator:
    """Simulate Claude Desktop interactions with UCP."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.connection_pool = None
        self.tool_zoo = None
        self.router = None
        self.session_manager = None
        self.results = TestResult()
    
    async def initialize(self):
        """Initialize UCP components."""
        print("\n" + "="*60)
        print("Initializing UCP Components")
        print("="*60)
        
        try:
            # Load configuration
            self.config = UCPConfig.load(self.config_path)
            self.results.pass_test("Load Configuration", f"Config loaded from {self.config_path}")
        except Exception as e:
            self.results.fail_test("Load Configuration", str(e))
            return False
        
        try:
            # Initialize connection pool
            self.connection_pool = ConnectionPool(self.config)
            await self.connection_pool.connect_all()
            self.results.pass_test(
                "Connect to Downstream Servers",
                f"Connected to {len(self.connection_pool.connections)} servers"
            )
        except Exception as e:
            self.results.fail_test("Connect to Downstream Servers", str(e))
            return False
        
        try:
            # Initialize tool zoo
            self.tool_zoo = HybridToolZoo(self.config.tool_zoo)
            self.tool_zoo.initialize()
            
            # Add tools from connection pool
            all_tools = self.connection_pool.all_tools
            if all_tools:
                self.tool_zoo.add_tools(all_tools)
                self.results.pass_test(
                    "Initialize Tool Zoo",
                    f"Indexed {len(all_tools)} tools"
                )
            else:
                self.results.warn_test("Initialize Tool Zoo", "No tools found from downstream servers")
        except Exception as e:
            self.results.fail_test("Initialize Tool Zoo", str(e))
            return False
        
        try:
            # Initialize session manager
            self.session_manager = SessionManager(self.config.session)
            self.results.pass_test("Initialize Session Manager", "Session manager ready")
        except Exception as e:
            self.results.fail_test("Initialize Session Manager", str(e))
            return False
        
        try:
            # Initialize router
            self.router = create_router(
                self.config.router,
                self.tool_zoo,
                None  # No telemetry store for testing
            )
            self.results.pass_test("Initialize Router", f"Router mode: {self.config.router.mode}")
        except Exception as e:
            self.results.fail_test("Initialize Router", str(e))
            return False
        
        return True
    
    async def test_filesystem_domain(self):
        """Test filesystem domain detection and tool injection."""
        print("\n" + "="*60)
        print("Test 1: Filesystem Domain")
        print("="*60)
        
        query = "List my files in the UniversalContextProtocol directory"
        
        try:
            # Simulate domain detection
            domains = self.router.detect_domain(query)
            print(f"Query: {query}")
            print(f"Detected domains: {domains}")
            
            # Check for filesystem-related domains
            filesystem_domains = [d for d in domains if 'file' in d.lower() or 'local' in d.lower()]
            
            if filesystem_domains:
                self.results.pass_test("Filesystem Domain Detection", f"Detected: {filesystem_domains}")
            else:
                self.results.warn_test("Filesystem Domain Detection", f"Only detected: {domains}")
            
            # Test tool selection
            selected_tools = self.router.select_tools(query, max_tools=5)
            print(f"Selected tools: {[t.name for t in selected_tools]}")
            
            # Check for filesystem tools
            filesystem_tools = [
                t for t in selected_tools
                if 'file' in t.name.lower() or 'read' in t.name.lower() or 'list' in t.name.lower()
            ]
            
            if filesystem_tools:
                self.results.pass_test(
                    "Filesystem Tool Injection",
                    f"Injected {len(filesystem_tools)} filesystem tools"
                )
            else:
                self.results.fail_test(
                    "Filesystem Tool Injection",
                    "No filesystem tools selected"
                )
            
            # Record session
            session_id = self.session_manager.create_session()
            self.session_manager.add_message(session_id, "user", query)
            
            for tool in selected_tools:
                self.session_manager.record_tool_call(
                    session_id,
                    tool.name,
                    {"query": query},
                    success=True,
                    duration_ms=100
                )
            
            self.results.pass_test("Session Recording", f"Session {session_id} recorded")
            
        except Exception as e:
            self.results.fail_test("Filesystem Domain Test", str(e))
    
    async def test_github_domain(self):
        """Test GitHub domain detection and tool injection."""
        print("\n" + "="*60)
        print("Test 2: GitHub Domain")
        print("="*60)
        
        query = "Create a GitHub issue for a bug in the router"
        
        try:
            # Simulate domain detection
            domains = self.router.detect_domain(query)
            print(f"Query: {query}")
            print(f"Detected domains: {domains}")
            
            # Check for GitHub-related domains
            github_domains = [d for d in domains if 'github' in d.lower() or 'git' in d.lower()]
            
            if github_domains:
                self.results.pass_test("GitHub Domain Detection", f"Detected: {github_domains}")
            else:
                self.results.warn_test("GitHub Domain Detection", f"Only detected: {domains}")
            
            # Test tool selection
            selected_tools = self.router.select_tools(query, max_tools=5)
            print(f"Selected tools: {[t.name for t in selected_tools]}")
            
            # Check for GitHub tools
            github_tools = [
                t for t in selected_tools
                if 'github' in t.name.lower() or 'issue' in t.name.lower() or 'pr' in t.name.lower()
            ]
            
            if github_tools:
                self.results.pass_test(
                    "GitHub Tool Injection",
                    f"Injected {len(github_tools)} GitHub tools"
                )
            else:
                self.results.fail_test(
                    "GitHub Tool Injection",
                    "No GitHub tools selected"
                )
            
            # Record session
            session_id = self.session_manager.create_session()
            self.session_manager.add_message(session_id, "user", query)
            
            for tool in selected_tools:
                self.session_manager.record_tool_call(
                    session_id,
                    tool.name,
                    {"query": query},
                    success=True,
                    duration_ms=150
                )
            
            self.results.pass_test("Session Recording", f"Session {session_id} recorded")
            
        except Exception as e:
            self.results.fail_test("GitHub Domain Test", str(e))
    
    async def test_context_switching(self):
        """Test context switching between domains."""
        print("\n" + "="*60)
        print("Test 3: Context Switching")
        print("="*60)
        
        queries = [
            "List my files in the project directory",
            "Create a GitHub issue for the README file",
            "Read the contents of the first file",
        ]
        
        session_id = self.session_manager.create_session()
        
        try:
            previous_domain = None
            domain_changes = 0
            
            for i, query in enumerate(queries, 1):
                print(f"\nQuery {i}: {query}")
                
                # Add message to session
                self.session_manager.add_message(session_id, "user", query)
                
                # Detect domain
                domains = self.router.detect_domain(query)
                current_domain = domains[0] if domains else "unknown"
                
                print(f"  Domain: {current_domain}")
                
                # Check for domain change
                if previous_domain and current_domain != previous_domain:
                    domain_changes += 1
                    print(f"  ↪️ Domain switch: {previous_domain} → {current_domain}")
                
                # Select tools
                selected_tools = self.router.select_tools(query, max_tools=5)
                print(f"  Tools: {[t.name for t in selected_tools]}")
                
                # Record tool calls
                for tool in selected_tools:
                    self.session_manager.record_tool_call(
                        session_id,
                        tool.name,
                        {"query": query},
                        success=True,
                        duration_ms=100
                    )
                
                previous_domain = current_domain
            
            if domain_changes >= 2:
                self.results.pass_test(
                    "Context Switching",
                    f"Detected {domain_changes} domain changes"
                )
            else:
                self.results.warn_test(
                    "Context Switching",
                    f"Only detected {domain_changes} domain changes (expected >= 2)"
                )
            
            self.results.pass_test("Session Continuity", f"Session {session_id} maintained across queries")
            
        except Exception as e:
            self.results.fail_test("Context Switching Test", str(e))
    
    async def test_tool_search(self):
        """Test tool search functionality."""
        print("\n" + "="*60)
        print("Test 4: Tool Search")
        print("="*60)
        
        search_queries = [
            "read file",
            "create issue",
            "list directory",
        ]
        
        for query in search_queries:
            try:
                results = self.tool_zoo.hybrid_search(query, top_k=3)
                print(f"\nSearch: '{query}'")
                print(f"Results: {len(results)} tools")
                
                for tool, score in results:
                    print(f"  - {tool.name} (score: {score:.3f})")
                
                if results:
                    self.results.pass_test(f"Tool Search: '{query}'", f"Found {len(results)} tools")
                else:
                    self.results.warn_test(f"Tool Search: '{query}'", "No tools found")
                
            except Exception as e:
                self.results.fail_test(f"Tool Search: '{query}'", str(e))
    
    async def test_session_tracking(self):
        """Test session tracking and statistics."""
        print("\n" + "="*60)
        print("Test 5: Session Tracking")
        print("="*60)
        
        try:
            # Get tool usage stats
            usage_stats = self.session_manager.get_tool_usage_stats()
            
            print(f"Tools with usage data: {len(usage_stats)}")
            
            if usage_stats:
                for tool_name, stats in list(usage_stats.items())[:5]:
                    print(f"  - {tool_name}: {stats['uses']} uses, {stats['success_rate']:.1%} success")
                
                self.results.pass_test("Session Tracking", f"Tracking {len(usage_stats)} tools")
            else:
                self.results.warn_test("Session Tracking", "No usage data yet")
            
            # Test session cleanup
            cleaned = self.session_manager.cleanup_old_sessions()
            print(f"Cleaned up {cleaned} old sessions")
            self.results.pass_test("Session Cleanup", f"Removed {cleaned} old sessions")
            
        except Exception as e:
            self.results.fail_test("Session Tracking Test", str(e))
    
    async def test_downstream_connectivity(self):
        """Test connectivity to downstream servers."""
        print("\n" + "="*60)
        print("Test 6: Downstream Server Connectivity")
        print("="*60)
        
        for server_config in self.config.downstream_servers:
            server_name = server_config.name
            try:
                # Check if connection exists
                if server_name in self.connection_pool.connections:
                    connection = self.connection_pool.connections[server_name]
                    tools = self.connection_pool.get_tools(server_name)
                    
                    print(f"\n{server_name}:")
                    print(f"  Status: Connected")
                    print(f"  Tools: {len(tools)}")
                    
                    self.results.pass_test(
                        f"Downstream: {server_name}",
                        f"Connected with {len(tools)} tools"
                    )
                else:
                    print(f"\n{server_name}:")
                    print(f"  Status: Not connected")
                    
                    self.results.fail_test(
                        f"Downstream: {server_name}",
                        "Connection not established"
                    )
                
            except Exception as e:
                self.results.fail_test(f"Downstream: {server_name}", str(e))
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*60)
        print("Starting Claude Desktop Integration Tests")
        print("="*60)
        
        # Initialize components
        if not await self.initialize():
            print("\n❌ Initialization failed. Aborting tests.")
            return self.results
        
        # Run tests
        await self.test_downstream_connectivity()
        await self.test_filesystem_domain()
        await self.test_github_domain()
        await self.test_context_switching()
        await self.test_tool_search()
        await self.test_session_tracking()
        
        # Cleanup
        try:
            await self.connection_pool.disconnect_all()
            print("\n✓ Disconnected from all downstream servers")
        except Exception as e:
            print(f"\n⚠️  Error during cleanup: {e}")
        
        return self.results


async def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test UCP integration with Claude Desktop"
    )
    parser.add_argument(
        "-c", "--config",
        default="ucp_config.yaml",
        help="Path to UCP configuration file"
    )
    parser.add_argument(
        "--output",
        default="test_results.json",
        help="Path to save test results"
    )
    
    args = parser.parse_args()
    
    # Check if config exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {args.config}")
        print(f"   Current directory: {Path.cwd()}")
        print(f"   Please provide a valid config path with -c option")
        sys.exit(1)
    
    # Run tests
    simulator = ClaudeDesktopSimulator(str(config_path))
    results = await simulator.run_all_tests()
    
    # Print summary
    print(results.summary())
    
    # Save results to JSON
    output_data = {
        "passed": [{"test": name, "message": msg} for name, msg in results.passed],
        "failed": [{"test": name, "error": err} for name, err in results.failed],
        "warnings": [{"test": name, "message": msg} for name, msg in results.warnings],
        "summary": {
            "total": len(results.passed) + len(results.failed),
            "passed": len(results.passed),
            "failed": len(results.failed),
            "warnings": len(results.warnings),
        }
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n📄 Test results saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if len(results.failed) == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
"""
Test script for Milestone 1.3: End-to-End Claude Desktop Test

This script simulates Claude Desktop interactions with UCP to validate:
- Server connectivity
- Tool discovery
- Domain detection
- Tool injection
- Context switching
- Session recording

Usage:
    python tests/test_claude_desktop_integration.py
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from ucp_core.config import UCPConfig
    from ucp_mvp.connection_pool import ConnectionPool
    from ucp_mvp.tool_zoo import HybridToolZoo
    from ucp_mvp.router import create_router
    from ucp_mvp.session import SessionManager
    from ucp_mvp.server import UCPServer
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure UCP is installed: pip install -e .")
    sys.exit(1)


class TestResult:
    """Track test results."""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def pass_test(self, test_name: str, message: str = ""):
        """Record a passed test."""
        self.passed.append((test_name, message))
        print(f"✅ PASS: {test_name}")
        if message:
            print(f"   {message}")
    
    def fail_test(self, test_name: str, error: str):
        """Record a failed test."""
        self.failed.append((test_name, error))
        print(f"❌ FAIL: {test_name}")
        print(f"   Error: {error}")
    
    def warn_test(self, test_name: str, message: str):
        """Record a warning."""
        self.warnings.append((test_name, message))
        print(f"⚠️  WARN: {test_name}")
        print(f"   {message}")
    
    def summary(self) -> str:
        """Generate test summary."""
        total = len(self.passed) + len(self.failed)
        passed = len(self.passed)
        failed = len(self.failed)
        warnings = len(self.warnings)
        
        summary = f"""
{'='*60}
Test Summary
{'='*60}
Total Tests: {total}
Passed: {passed} ✅
Failed: {failed} ❌
Warnings: {warnings} ⚠️
"""
        
        if self.failed:
            summary += "\nFailed Tests:\n"
            for name, error in self.failed:
                summary += f"  - {name}: {error}\n"
        
        if self.warnings:
            summary += "\nWarnings:\n"
            for name, message in self.warnings:
                summary += f"  - {name}: {message}\n"
        
        return summary


class ClaudeDesktopSimulator:
    """Simulate Claude Desktop interactions with UCP."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = None
        self.connection_pool = None
        self.tool_zoo = None
        self.router = None
        self.session_manager = None
        self.results = TestResult()
    
    async def initialize(self):
        """Initialize UCP components."""
        print("\n" + "="*60)
        print("Initializing UCP Components")
        print("="*60)
        
        try:
            # Load configuration
            self.config = UCPConfig.load(self.config_path)
            self.results.pass_test("Load Configuration", f"Config loaded from {self.config_path}")
        except Exception as e:
            self.results.fail_test("Load Configuration", str(e))
            return False
        
        try:
            # Initialize connection pool
            self.connection_pool = ConnectionPool(self.config)
            await self.connection_pool.connect_all()
            self.results.pass_test(
                "Connect to Downstream Servers",
                f"Connected to {len(self.connection_pool.connections)} servers"
            )
        except Exception as e:
            self.results.fail_test("Connect to Downstream Servers", str(e))
            return False
        
        try:
            # Initialize tool zoo
            self.tool_zoo = HybridToolZoo(self.config.tool_zoo)
            self.tool_zoo.initialize()
            
            # Add tools from connection pool
            all_tools = self.connection_pool.all_tools
            if all_tools:
                self.tool_zoo.add_tools(all_tools)
                self.results.pass_test(
                    "Initialize Tool Zoo",
                    f"Indexed {len(all_tools)} tools"
                )
            else:
                self.results.warn_test("Initialize Tool Zoo", "No tools found from downstream servers")
        except Exception as e:
            self.results.fail_test("Initialize Tool Zoo", str(e))
            return False
        
        try:
            # Initialize session manager
            self.session_manager = SessionManager(self.config.session)
            self.results.pass_test("Initialize Session Manager", "Session manager ready")
        except Exception as e:
            self.results.fail_test("Initialize Session Manager", str(e))
            return False
        
        try:
            # Initialize router
            self.router = create_router(
                self.config.router,
                self.tool_zoo,
                None  # No telemetry store for testing
            )
            self.results.pass_test("Initialize Router", f"Router mode: {self.config.router.mode}")
        except Exception as e:
            self.results.fail_test("Initialize Router", str(e))
            return False
        
        return True
    
    async def test_filesystem_domain(self):
        """Test filesystem domain detection and tool injection."""
        print("\n" + "="*60)
        print("Test 1: Filesystem Domain")
        print("="*60)
        
        query = "List my files in the UniversalContextProtocol directory"
        
        try:
            # Simulate domain detection
            domains = self.router.detect_domain(query)
            print(f"Query: {query}")
            print(f"Detected domains: {domains}")
            
            # Check for filesystem-related domains
            filesystem_domains = [d for d in domains if 'file' in d.lower() or 'local' in d.lower()]
            
            if filesystem_domains:
                self.results.pass_test("Filesystem Domain Detection", f"Detected: {filesystem_domains}")
            else:
                self.results.warn_test("Filesystem Domain Detection", f"Only detected: {domains}")
            
            # Test tool selection
            selected_tools = self.router.select_tools(query, max_tools=5)
            print(f"Selected tools: {[t.name for t in selected_tools]}")
            
            # Check for filesystem tools
            filesystem_tools = [
                t for t in selected_tools
                if 'file' in t.name.lower() or 'read' in t.name.lower() or 'list' in t.name.lower()
            ]
            
            if filesystem_tools:
                self.results.pass_test(
                    "Filesystem Tool Injection",
                    f"Injected {len(filesystem_tools)} filesystem tools"
                )
            else:
                self.results.fail_test(
                    "Filesystem Tool Injection",
                    "No filesystem tools selected"
                )
            
            # Record session
            session_id = self.session_manager.create_session()
            self.session_manager.add_message(session_id, "user", query)
            
            for tool in selected_tools:
                self.session_manager.record_tool_call(
                    session_id,
                    tool.name,
                    {"query": query},
                    success=True,
                    duration_ms=100
                )
            
            self.results.pass_test("Session Recording", f"Session {session_id} recorded")
            
        except Exception as e:
            self.results.fail_test("Filesystem Domain Test", str(e))
    
    async def test_github_domain(self):
        """Test GitHub domain detection and tool injection."""
        print("\n" + "="*60)
        print("Test 2: GitHub Domain")
        print("="*60)
        
        query = "Create a GitHub issue for a bug in the router"
        
        try:
            # Simulate domain detection
            domains = self.router.detect_domain(query)
            print(f"Query: {query}")
            print(f"Detected domains: {domains}")
            
            # Check for GitHub-related domains
            github_domains = [d for d in domains if 'github' in d.lower() or 'git' in d.lower()]
            
            if github_domains:
                self.results.pass_test("GitHub Domain Detection", f"Detected: {github_domains}")
            else:
                self.results.warn_test("GitHub Domain Detection", f"Only detected: {domains}")
            
            # Test tool selection
            selected_tools = self.router.select_tools(query, max_tools=5)
            print(f"Selected tools: {[t.name for t in selected_tools]}")
            
            # Check for GitHub tools
            github_tools = [
                t for t in selected_tools
                if 'github' in t.name.lower() or 'issue' in t.name.lower() or 'pr' in t.name.lower()
            ]
            
            if github_tools:
                self.results.pass_test(
                    "GitHub Tool Injection",
                    f"Injected {len(github_tools)} GitHub tools"
                )
            else:
                self.results.fail_test(
                    "GitHub Tool Injection",
                    "No GitHub tools selected"
                )
            
            # Record session
            session_id = self.session_manager.create_session()
            self.session_manager.add_message(session_id, "user", query)
            
            for tool in selected_tools:
                self.session_manager.record_tool_call(
                    session_id,
                    tool.name,
                    {"query": query},
                    success=True,
                    duration_ms=150
                )
            
            self.results.pass_test("Session Recording", f"Session {session_id} recorded")
            
        except Exception as e:
            self.results.fail_test("GitHub Domain Test", str(e))
    
    async def test_context_switching(self):
        """Test context switching between domains."""
        print("\n" + "="*60)
        print("Test 3: Context Switching")
        print("="*60)
        
        queries = [
            "List my files in the project directory",
            "Create a GitHub issue for the README file",
            "Read the contents of the first file",
        ]
        
        session_id = self.session_manager.create_session()
        
        try:
            previous_domain = None
            domain_changes = 0
            
            for i, query in enumerate(queries, 1):
                print(f"\nQuery {i}: {query}")
                
                # Add message to session
                self.session_manager.add_message(session_id, "user", query)
                
                # Detect domain
                domains = self.router.detect_domain(query)
                current_domain = domains[0] if domains else "unknown"
                
                print(f"  Domain: {current_domain}")
                
                # Check for domain change
                if previous_domain and current_domain != previous_domain:
                    domain_changes += 1
                    print(f"  ↪️ Domain switch: {previous_domain} → {current_domain}")
                
                # Select tools
                selected_tools = self.router.select_tools(query, max_tools=5)
                print(f"  Tools: {[t.name for t in selected_tools]}")
                
                # Record tool calls
                for tool in selected_tools:
                    self.session_manager.record_tool_call(
                        session_id,
                        tool.name,
                        {"query": query},
                        success=True,
                        duration_ms=100
                    )
                
                previous_domain = current_domain
            
            if domain_changes >= 2:
                self.results.pass_test(
                    "Context Switching",
                    f"Detected {domain_changes} domain changes"
                )
            else:
                self.results.warn_test(
                    "Context Switching",
                    f"Only detected {domain_changes} domain changes (expected >= 2)"
                )
            
            self.results.pass_test("Session Continuity", f"Session {session_id} maintained across queries")
            
        except Exception as e:
            self.results.fail_test("Context Switching Test", str(e))
    
    async def test_tool_search(self):
        """Test tool search functionality."""
        print("\n" + "="*60)
        print("Test 4: Tool Search")
        print("="*60)
        
        search_queries = [
            "read file",
            "create issue",
            "list directory",
        ]
        
        for query in search_queries:
            try:
                results = self.tool_zoo.hybrid_search(query, top_k=3)
                print(f"\nSearch: '{query}'")
                print(f"Results: {len(results)} tools")
                
                for tool, score in results:
                    print(f"  - {tool.name} (score: {score:.3f})")
                
                if results:
                    self.results.pass_test(f"Tool Search: '{query}'", f"Found {len(results)} tools")
                else:
                    self.results.warn_test(f"Tool Search: '{query}'", "No tools found")
                
            except Exception as e:
                self.results.fail_test(f"Tool Search: '{query}'", str(e))
    
    async def test_session_tracking(self):
        """Test session tracking and statistics."""
        print("\n" + "="*60)
        print("Test 5: Session Tracking")
        print("="*60)
        
        try:
            # Get tool usage stats
            usage_stats = self.session_manager.get_tool_usage_stats()
            
            print(f"Tools with usage data: {len(usage_stats)}")
            
            if usage_stats:
                for tool_name, stats in list(usage_stats.items())[:5]:
                    print(f"  - {tool_name}: {stats['uses']} uses, {stats['success_rate']:.1%} success")
                
                self.results.pass_test("Session Tracking", f"Tracking {len(usage_stats)} tools")
            else:
                self.results.warn_test("Session Tracking", "No usage data yet")
            
            # Test session cleanup
            cleaned = self.session_manager.cleanup_old_sessions()
            print(f"Cleaned up {cleaned} old sessions")
            self.results.pass_test("Session Cleanup", f"Removed {cleaned} old sessions")
            
        except Exception as e:
            self.results.fail_test("Session Tracking Test", str(e))
    
    async def test_downstream_connectivity(self):
        """Test connectivity to downstream servers."""
        print("\n" + "="*60)
        print("Test 6: Downstream Server Connectivity")
        print("="*60)
        
        for server_config in self.config.downstream_servers:
            server_name = server_config.name
            try:
                # Check if connection exists
                if server_name in self.connection_pool.connections:
                    connection = self.connection_pool.connections[server_name]
                    tools = self.connection_pool.get_tools(server_name)
                    
                    print(f"\n{server_name}:")
                    print(f"  Status: Connected")
                    print(f"  Tools: {len(tools)}")
                    
                    self.results.pass_test(
                        f"Downstream: {server_name}",
                        f"Connected with {len(tools)} tools"
                    )
                else:
                    print(f"\n{server_name}:")
                    print(f"  Status: Not connected")
                    
                    self.results.fail_test(
                        f"Downstream: {server_name}",
                        "Connection not established"
                    )
                
            except Exception as e:
                self.results.fail_test(f"Downstream: {server_name}", str(e))
    
    async def run_all_tests(self):
        """Run all integration tests."""
        print("\n" + "="*60)
        print("Starting Claude Desktop Integration Tests")
        print("="*60)
        
        # Initialize components
        if not await self.initialize():
            print("\n❌ Initialization failed. Aborting tests.")
            return self.results
        
        # Run tests
        await self.test_downstream_connectivity()
        await self.test_filesystem_domain()
        await self.test_github_domain()
        await self.test_context_switching()
        await self.test_tool_search()
        await self.test_session_tracking()
        
        # Cleanup
        try:
            await self.connection_pool.disconnect_all()
            print("\n✓ Disconnected from all downstream servers")
        except Exception as e:
            print(f"\n⚠️  Error during cleanup: {e}")
        
        return self.results


async def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Test UCP integration with Claude Desktop"
    )
    parser.add_argument(
        "-c", "--config",
        default="ucp_config.yaml",
        help="Path to UCP configuration file"
    )
    parser.add_argument(
        "--output",
        default="test_results.json",
        help="Path to save test results"
    )
    
    args = parser.parse_args()
    
    # Check if config exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"❌ Configuration file not found: {args.config}")
        print(f"   Current directory: {Path.cwd()}")
        print(f"   Please provide a valid config path with -c option")
        sys.exit(1)
    
    # Run tests
    simulator = ClaudeDesktopSimulator(str(config_path))
    results = await simulator.run_all_tests()
    
    # Print summary
    print(results.summary())
    
    # Save results to JSON
    output_data = {
        "passed": [{"test": name, "message": msg} for name, msg in results.passed],
        "failed": [{"test": name, "error": err} for name, err in results.failed],
        "warnings": [{"test": name, "message": msg} for name, msg in results.warnings],
        "summary": {
            "total": len(results.passed) + len(results.failed),
            "passed": len(results.passed),
            "failed": len(results.failed),
            "warnings": len(results.warnings),
        }
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n📄 Test results saved to: {args.output}")
    
    # Exit with appropriate code
    sys.exit(0 if len(results.failed) == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())

