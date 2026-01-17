# Getting Started: ML Pipeline Implementation

**Date:** 2026-01-16  
**Status:** Ready to Begin  
**Prerequisites:** UCP repository cloned, Python 3.11+, basic familiarity with UCP architecture

---

## Quick Start: Phase 1 (Registry Foundation)

This guide will walk you through implementing the first phase of the ML pipeline.

### Step 1: Set Up Development Environment

```bash
# Navigate to UCP repository
cd d:\GitHub\Telomere\UniversalContextProtocol

# Activate virtual environment (or create one)
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Verify installation
ucp --version
```

### Step 2: Create Registry Module

**File:** `src/ucp/registry.py`

Start with the data models from the implementation plan:

```python
"""
Registry module for MCP/Skill catalog with rich metadata.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class ToolCategory(str, Enum):
    """High-level tool categories"""
    CODE = "code"
    COMMUNICATION = "communication"
    DATA = "data"
    FILES = "files"
    SEARCH = "search"
    AUTOMATION = "automation"
    ANALYSIS = "analysis"

class MCPRegistryEntry(BaseModel):
    """Extended metadata for MCP servers"""
    # Core identification
    name: str
    display_name: str
    version: str = "1.0.0"
    author: str = "Unknown"
    
    # Discovery metadata
    description: str
    long_description: Optional[str] = None
    categories: List[ToolCategory] = []
    tags: List[str] = []
    keywords: List[str] = []
    
    # Installation
    install_command: str
    config_template: Dict[str, Any] = {}
    dependencies: List[str] = []
    
    # Usage metadata
    use_cases: List[str] = []
    example_queries: List[str] = []
    
    # Quality signals
    popularity_score: float = 0.0
    quality_score: float = 0.0
    avg_latency_ms: Optional[float] = None
    
    # Relationships
    similar_tools: List[str] = []
    replaces: List[str] = []
    works_well_with: List[str] = []
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    enabled_by_default: bool = False

# Add to __init__.py exports
```

### Step 3: Create Seed Registry Data

**File:** `data/registry_seed.yaml`

```yaml
# UCP Registry Seed Data
# This file contains the initial catalog of MCPs and skills

mcps:
  - name: filesystem
    display_name: "File System"
    version: "1.0.0"
    author: "Anthropic"
    description: "Read and write local files"
    categories: [files]
    tags: [local, files, io, filesystem]
    keywords: [read, write, file, directory, path, folder]
    install_command: "npx -y @modelcontextprotocol/server-filesystem"
    use_cases:
      - "Read configuration files"
      - "Write generated code to files"
      - "List directory contents"
      - "Search for files by pattern"
    example_queries:
      - "Read the package.json file"
      - "Write this code to app.py"
      - "List all Python files in src/"
    enabled_by_default: true
    works_well_with: [github, python]
    
  - name: github
    display_name: "GitHub"
    version: "1.0.0"
    author: "Anthropic"
    description: "Interact with GitHub repositories, issues, and pull requests"
    categories: [code, automation]
    tags: [github, git, code, issues, prs, version-control]
    keywords: [issue, pull request, commit, repository, branch, pr]
    install_command: "npx -y @modelcontextprotocol/server-github"
    use_cases:
      - "Create GitHub issues for bugs"
      - "Review and comment on pull requests"
      - "Search code across repositories"
      - "List commits and branches"
    example_queries:
      - "Create an issue for this bug"
      - "List open PRs in this repo"
      - "Show recent commits"
    enabled_by_default: false
    works_well_with: [filesystem]
    
  # TODO: Add 18+ more MCPs (gmail, slack, calendar, python, npm, docker, etc.)
```

### Step 4: Extend Tool Zoo for Registry

**File:** `src/ucp/tool_zoo.py` (extend existing)

Add this class at the end of the file:

```python
class RegistryToolZoo(HybridToolZoo):
    """Extended Tool Zoo with registry capabilities"""
    
    def __init__(self, config: ToolZooConfig):
        super().__init__(config)
        self._registry: Dict[str, MCPRegistryEntry] = {}
        self._registry_loaded = False
    
    def load_registry(self, registry_path: str) -> int:
        """Load registry from YAML file"""
        import yaml
        from pathlib import Path
        
        registry_file = Path(registry_path)
        if not registry_file.exists():
            logger.warning("registry_not_found", path=registry_path)
            return 0
        
        with open(registry_file) as f:
            data = yaml.safe_load(f)
        
        count = 0
        for mcp_data in data.get("mcps", []):
            try:
                entry = MCPRegistryEntry(**mcp_data)
                self._registry[entry.name] = entry
                count += 1
            except Exception as e:
                logger.error("failed_to_load_registry_entry", error=str(e), data=mcp_data)
        
        self._registry_loaded = True
        logger.info("registry_loaded", count=count)
        return count
    
    def get_registry_entry(self, name: str) -> Optional[MCPRegistryEntry]:
        """Get full registry entry for an MCP"""
        return self._registry.get(name)
    
    def get_all_registry_entries(self) -> List[MCPRegistryEntry]:
        """Get all registry entries"""
        return list(self._registry.values())
    
    def search_by_category(self, category: ToolCategory, top_k: int = 10) -> List[MCPRegistryEntry]:
        """Find MCPs by category"""
        entries = [e for e in self._registry.values() if category in e.categories]
        entries.sort(key=lambda e: e.popularity_score, reverse=True)
        return entries[:top_k]
    
    def search_by_use_case(self, use_case: str, top_k: int = 5) -> List[MCPRegistryEntry]:
        """Find MCPs that match a use case (semantic search)"""
        # Use existing hybrid_search on use_cases field
        results = []
        for entry in self._registry.values():
            for uc in entry.use_cases:
                if use_case.lower() in uc.lower():
                    results.append(entry)
                    break
        
        # TODO: Use semantic search for better matching
        return results[:top_k]
```

### Step 5: Add CLI Commands

**File:** `src/ucp/cli.py` (extend existing)

Add these commands to the CLI:

```python
@cli.group()
def registry():
    """Registry management commands"""
    pass

@registry.command()
@click.option("--category", help="Filter by category")
@click.option("--tag", help="Filter by tag")
def list(category, tag):
    """List all MCPs in the registry"""
    from rich.console import Console
    from rich.table import Table
    
    # Load registry
    config = load_config()
    tool_zoo = RegistryToolZoo(config.tool_zoo)
    tool_zoo.load_registry("./data/registry_seed.yaml")
    
    # Get entries
    entries = tool_zoo.get_all_registry_entries()
    
    # Apply filters
    if category:
        entries = [e for e in entries if category in [c.value for c in e.categories]]
    if tag:
        entries = [e for e in entries if tag in e.tags]
    
    # Display
    console = Console()
    table = Table(title="MCP Registry")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="white")
    table.add_column("Categories", style="magenta")
    table.add_column("Enabled", style="green")
    
    for entry in entries:
        table.add_row(
            entry.name,
            entry.description[:50] + "..." if len(entry.description) > 50 else entry.description,
            ", ".join([c.value for c in entry.categories]),
            "✓" if entry.enabled_by_default else ""
        )
    
    console.print(table)
    console.print(f"\n[bold]Total:[/bold] {len(entries)} MCPs")

@registry.command()
@click.argument("query")
@click.option("--top-k", default=5, help="Number of results")
def search(query, top_k):
    """Search registry by query"""
    from rich.console import Console
    from rich.panel import Panel
    
    # Load registry
    config = load_config()
    tool_zoo = RegistryToolZoo(config.tool_zoo)
    tool_zoo.load_registry("./data/registry_seed.yaml")
    
    # Search
    results = tool_zoo.search_by_use_case(query, top_k=top_k)
    
    # Display
    console = Console()
    console.print(f"\n[bold]Search results for:[/bold] '{query}'\n")
    
    for i, entry in enumerate(results, 1):
        panel = Panel(
            f"[bold]{entry.display_name}[/bold]\n"
            f"{entry.description}\n\n"
            f"[dim]Categories:[/dim] {', '.join([c.value for c in entry.categories])}\n"
            f"[dim]Install:[/dim] {entry.install_command}",
            title=f"{i}. {entry.name}",
            border_style="cyan"
        )
        console.print(panel)
```

### Step 6: Test the Registry

```bash
# Create the seed data file
mkdir -p data
# Copy the YAML content above to data/registry_seed.yaml

# Test CLI commands
ucp registry list
ucp registry list --category code
ucp registry search "create github issue"
```

### Step 7: Expand the Registry

Now expand `data/registry_seed.yaml` with more MCPs:

**Common MCPs to add:**
- `gmail` - Email management
- `slack` - Team communication
- `calendar` - Calendar and scheduling
- `python` - Python code execution
- `npm` - Node.js package management
- `docker` - Container management
- `sql` - Database queries
- `web-search` - Web search
- `weather` - Weather information
- `time` - Time and timezone utilities

**Target:** 20+ MCPs in seed data

---

## Next Steps (Phase 2)

Once Phase 1 is complete:

1. **Baseline Recommender** - Build use case matching system
2. **Agent Profiles** - Define agent configuration schema
3. **CLI Integration** - Add `ucp recommend` command

See the full implementation plan for details.

---

## Troubleshooting

### Registry not loading
- Check YAML syntax in `data/registry_seed.yaml`
- Verify file path is correct
- Check logs for parsing errors

### Import errors
- Ensure `MCPRegistryEntry` is imported in `tool_zoo.py`
- Add to `__init__.py` exports if needed

### CLI commands not found
- Reinstall package: `pip install -e .`
- Check `cli.py` has the new commands

---

## Resources

- **Implementation Plan:** `implementation_plan.md` (artifact)
- **Task Checklist:** `task.md` (artifact)
- **Quick Reference:** `plans/ml_pipeline_plan_2026-01-16.md`
- **UCP Roadmap:** `docs/roadmap.md`

---

**Ready to start?** Begin with Step 2 (Create Registry Module) and work through each step sequentially.

**Questions?** Refer to the detailed implementation plan for code examples and architectural guidance.

**Good luck! 🚀**
