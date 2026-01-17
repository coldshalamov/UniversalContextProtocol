"""
Registry module for MCP/Skill catalog with rich metadata.

This module provides the data models and infrastructure for maintaining
a centralized catalog of MCPs (Model Context Protocol servers) and agent skills.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolCategory(str, Enum):
    """High-level tool categories for organizing MCPs"""
    
    CODE = "code"
    COMMUNICATION = "communication"
    DATA = "data"
    FILES = "files"
    SEARCH = "search"
    AUTOMATION = "automation"
    ANALYSIS = "analysis"


class MCPRegistryEntry(BaseModel):
    """
    Extended metadata for MCP servers.
    
    This model captures all the information needed to discover, install,
    and recommend MCPs to agents.
    """
    
    # Core identification
    name: str = Field(..., description="Unique identifier for the MCP")
    display_name: str = Field(..., description="Human-readable name")
    version: str = Field(default="1.0.0", description="Version string")
    author: str = Field(default="Unknown", description="Author or organization")
    
    # Discovery metadata
    description: str = Field(..., description="Short description of functionality")
    long_description: Optional[str] = Field(None, description="Detailed description")
    categories: List[ToolCategory] = Field(default_factory=list, description="Tool categories")
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    keywords: List[str] = Field(default_factory=list, description="Keywords for matching")
    
    # Installation
    install_command: str = Field(..., description="Command to install/run the MCP")
    config_template: Dict[str, Any] = Field(default_factory=dict, description="Configuration template")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")
    
    # Usage metadata
    use_cases: List[str] = Field(default_factory=list, description="Common use cases")
    example_queries: List[str] = Field(default_factory=list, description="Example queries that would use this tool")
    
    # Quality signals (populated from telemetry)
    popularity_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Usage-based popularity (0-1)")
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Success rate (0-1)")
    avg_latency_ms: Optional[float] = Field(None, description="Average latency in milliseconds")
    
    # Relationships
    similar_tools: List[str] = Field(default_factory=list, description="Similar/alternative tools")
    replaces: List[str] = Field(default_factory=list, description="Tools this can replace")
    works_well_with: List[str] = Field(default_factory=list, description="Complementary tools")
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    enabled_by_default: bool = Field(default=False, description="Should be enabled by default")
    
    class Config:
        use_enum_values = True


class SkillDefinition(BaseModel):
    """
    Agent skill definition.
    
    A skill is a higher-level capability that may require multiple MCPs.
    For example, "Full-Stack Development" might require filesystem, github, npm, etc.
    """
    
    name: str = Field(..., description="Skill name")
    description: str = Field(..., description="What this skill enables")
    required_mcps: List[str] = Field(default_factory=list, description="MCPs required for this skill")
    optional_mcps: List[str] = Field(default_factory=list, description="MCPs that enhance this skill")
    skill_level: str = Field(default="intermediate", description="beginner, intermediate, or advanced")
    use_cases: List[str] = Field(default_factory=list, description="What you can do with this skill")
    
    class Config:
        use_enum_values = True


class UseCaseTemplate(BaseModel):
    """
    Predefined use case template for agent configuration.
    
    Templates help new users quickly configure agents for common scenarios.
    """
    
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="What this template is for")
    required_tools: List[str] = Field(default_factory=list, description="Required MCPs")
    optional_tools: List[str] = Field(default_factory=list, description="Optional MCPs")
    example_prompts: List[str] = Field(default_factory=list, description="Example prompts for this use case")
    keywords: List[str] = Field(default_factory=list, description="Keywords for matching")
