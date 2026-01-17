#!/usr/bin/env python3
"""
Test script for Phase 1: Registry Foundation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ucp.registry import MCPRegistryEntry, ToolCategory, UseCaseTemplate
from ucp.tool_zoo import RegistryToolZoo
from ucp.config import ToolZooConfig

def test_registry_loading():
    """Test loading the registry"""
    print("=" * 80)
    print("Testing Registry Loading")
    print("=" * 80)
    
    # Create registry tool zoo (without initializing ChromaDB)
    config = ToolZooConfig()
    zoo = RegistryToolZoo(config)
    
    # Load registry
    registry_file = "./data/registry_seed.yaml"
    print(f"\nLoading registry from: {registry_file}")
    count = zoo.load_registry(registry_file)
    
    print(f"✓ Loaded {count} MCPs")
    
    # Test getting all entries
    entries = zoo.get_all_registry_entries()
    print(f"✓ Retrieved {len(entries)} registry entries")
    
    # Test getting specific entry
    fs_entry = zoo.get_registry_entry("filesystem")
    if fs_entry:
        print(f"✓ Found filesystem MCP: {fs_entry.display_name}")
    
    # Test category search
    code_mcps = zoo.search_by_category("code")  # Use string instead of enum
    print(f"✓ Found {len(code_mcps)} code-related MCPs")
    
    # Test use case search
    results = zoo.search_by_use_case("create github issue")
    print(f"✓ Found {len(results)} MCPs for 'create github issue'")
    
    # Test templates
    templates = zoo.get_all_use_case_templates()
    print(f"✓ Loaded {len(templates)} use case templates")
    
    print("\n" + "=" * 80)
    print("Registry Test: PASSED ✓")
    print("=" * 80)
    
    return True

def show_registry_contents():
    """Display registry contents"""
    print("\n" + "=" * 80)
    print("Registry Contents")
    print("=" * 80 + "\n")
    
    config = ToolZooConfig()
    zoo = RegistryToolZoo(config)
    zoo.load_registry("./data/registry_seed.yaml")
    
    entries = zoo.get_all_registry_entries()
    
    for entry in entries:
        enabled = "✓" if entry.enabled_by_default else " "
        # Handle both enum and string values
        if entry.categories:
            if isinstance(entry.categories[0], str):
                categories = ", ".join(entry.categories)
            else:
                categories = ", ".join([c.value for c in entry.categories])
        else:
            categories = ""
        print(f"[{enabled}] {entry.display_name} ({entry.name})")
        print(f"    {entry.description}")
        print(f"    Categories: {categories}")
        print(f"    Install: {entry.install_command}")
        print()
    
    print(f"Total: {len(entries)} MCPs\n")

def show_use_case_templates():
    """Display use case templates"""
    print("\n" + "=" * 80)
    print("Use Case Templates")
    print("=" * 80 + "\n")
    
    config = ToolZooConfig()
    zoo = RegistryToolZoo(config)
    zoo.load_registry("./data/registry_seed.yaml")
    
    templates = zoo.get_all_use_case_templates()
    
    for template in templates:
        print(f"{template.name}")
        print(f"  {template.description}")
        print(f"  Required: {', '.join(template.required_tools)}")
        if template.optional_tools:
            print(f"  Optional: {', '.join(template.optional_tools)}")
        print()
    
    print(f"Total: {len(templates)} templates\n")

if __name__ == "__main__":
    try:
        # Run tests
        test_registry_loading()
        
        # Show contents
        show_registry_contents()
        show_use_case_templates()
        
        print("\n✓ Phase 1 implementation is working!")
        print("\nNext steps:")
        print("  1. Add more MCPs to data/registry_seed.yaml (target: 20+)")
        print("  2. Test CLI commands: python -m ucp.cli registry list")
        print("  3. Move to Phase 2: Baseline Recommendations")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
