"""
Configuration management for UCP Chat.

Handles loading/saving config from ~/.ucp/config.yaml
and managing API keys securely via keyring.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class ProviderConfig(BaseModel):
    """Configuration for a single LLM provider."""
    
    api_key: str | None = None
    api_base: str | None = None
    default_model: str | None = None
    enabled: bool = True
    extra: dict[str, Any] = Field(default_factory=dict)


class UCPSettings(BaseModel):
    """Settings for UCP integration."""
    
    enabled: bool = False
    server_url: str = "http://localhost:8765"
    log_directory: str = "~/.ucp/logs"
    capture_context: bool = True
    inject_tools: bool = True


class ThemeSettings(BaseModel):
    """UI theme settings."""
    
    primary_color: str = "#7c3aed"  # Purple
    accent_color: str = "#10b981"  # Emerald
    dark_mode: bool = True
    font_family: str = "JetBrains Mono"


class Config(BaseModel):
    """Main configuration model."""
    
    default_provider: str = "anthropic"
    providers: dict[str, ProviderConfig] = Field(default_factory=dict)
    ucp: UCPSettings = Field(default_factory=UCPSettings)
    theme: ThemeSettings = Field(default_factory=ThemeSettings)
    log_level: str = "INFO"
    history_limit: int = 1000
    
    @classmethod
    def default(cls) -> "Config":
        """Create default configuration with all providers."""
        return cls(
            providers={
                "openai": ProviderConfig(
                    default_model="gpt-4o",
                    api_base="https://api.openai.com/v1",
                ),
                "anthropic": ProviderConfig(
                    default_model="claude-sonnet-4-20250514",
                    api_base="https://api.anthropic.com",
                ),
                "google": ProviderConfig(
                    default_model="gemini-2.0-flash",
                ),
                "mistral": ProviderConfig(
                    default_model="mistral-large-latest",
                    api_base="https://api.mistral.ai/v1",
                ),
                "groq": ProviderConfig(
                    default_model="llama-3.3-70b-versatile",
                    api_base="https://api.groq.com/openai/v1",
                ),
                "together": ProviderConfig(
                    default_model="meta-llama/Llama-3.3-70B-Instruct-Turbo",
                    api_base="https://api.together.xyz/v1",
                ),
                "openrouter": ProviderConfig(
                    default_model="anthropic/claude-3.5-sonnet",
                    api_base="https://openrouter.ai/api/v1",
                ),
                "deepseek": ProviderConfig(
                    default_model="deepseek-chat",
                    api_base="https://api.deepseek.com/v1",
                ),
                "ollama": ProviderConfig(
                    default_model="llama3.2",
                    api_base="http://localhost:11434/v1",
                    api_key="ollama",  # Ollama doesn't need real key
                ),
                "lmstudio": ProviderConfig(
                    default_model="local-model",
                    api_base="http://localhost:1234/v1",
                    api_key="lmstudio",  # Local doesn't need real key
                ),
                "zai": ProviderConfig(
                    default_model="gemini-2.5-pro",
                    api_base="https://zai-api.zuzu.so/v1",
                ),
                "fireworks": ProviderConfig(
                    default_model="accounts/fireworks/models/llama-v3p3-70b-instruct",
                    api_base="https://api.fireworks.ai/inference/v1",
                ),
                "xai": ProviderConfig(
                    default_model="grok-beta",
                    api_base="https://api.x.ai/v1",
                ),
                "cohere": ProviderConfig(
                    default_model="command-r-plus",
                    api_base="https://api.cohere.ai/v1/chat",
                ),
                "perplexity": ProviderConfig(
                    default_model="sonar-pro",
                    api_base="https://api.perplexity.ai",
                ),
                "sambanova": ProviderConfig(
                    default_model="Meta-Llama-3.3-70B-Instruct",
                    api_base="https://api.sambanova.ai/v1",
                ),
                "cerebras": ProviderConfig(
                    default_model="llama-3.3-70b",
                    api_base="https://api.cerebras.ai/v1",
                ),
                "hyperbolic": ProviderConfig(
                    default_model="meta-llama/Llama-3.3-70B-Instruct",
                    api_base="https://api.hyperbolic.xyz/v1",
                ),
                "nebius": ProviderConfig(
                    default_model="meta-llama/Meta-Llama-3.1-70B-Instruct",
                    api_base="https://api.studio.nebius.ai/v1",
                ),
            }
        )


class ConfigManager:
    """Manages loading, saving, and accessing configuration."""
    
    DEFAULT_PATH = Path.home() / ".ucp" / "config.yaml"
    
    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or self.DEFAULT_PATH
        self._config: Config | None = None
    
    @property
    def config(self) -> Config:
        """Get the current configuration, loading if necessary."""
        if self._config is None:
            self._config = self.load()
        return self._config
    
    def load(self) -> Config:
        """Load configuration from file, creating default if needed."""
        if not self.config_path.exists():
            # Create default config
            config = Config.default()
            self.save(config)
            return config
        
        try:
            with open(self.config_path, "r") as f:
                data = yaml.safe_load(f) or {}
            
            # Expand environment variables in API keys
            if "providers" in data:
                for name, pconfig in data["providers"].items():
                    if isinstance(pconfig, dict) and "api_key" in pconfig:
                        key = pconfig["api_key"]
                        if isinstance(key, str) and key.startswith("${") and key.endswith("}"):
                            env_var = key[2:-1]
                            pconfig["api_key"] = os.environ.get(env_var)
            
            return Config(**data)
        except Exception as e:
            print(f"Warning: Failed to load config: {e}")
            return Config.default()
    
    def save(self, config: Config | None = None) -> None:
        """Save configuration to file."""
        config = config or self._config or Config.default()
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, "w") as f:
            yaml.safe_dump(config.model_dump(exclude_none=True), f, default_flow_style=False)
        
        self._config = config
    
    def get_provider_config(self, name: str) -> ProviderConfig | None:
        """Get configuration for a specific provider."""
        return self.config.providers.get(name)
    
    def set_api_key(self, provider: str, api_key: str, use_keyring: bool = True) -> None:
        """Set API key for a provider, optionally storing in keyring."""
        if use_keyring:
            try:
                import keyring
                keyring.set_password("ucp-chat", provider, api_key)
                # Store a reference in config
                if provider in self.config.providers:
                    self.config.providers[provider].api_key = f"keyring:{provider}"
            except ImportError:
                # Fall back to storing in config
                if provider in self.config.providers:
                    self.config.providers[provider].api_key = api_key
        else:
            if provider in self.config.providers:
                self.config.providers[provider].api_key = api_key
        
        self.save()
    
    def get_api_key(self, provider: str) -> str | None:
        """Get API key for a provider, checking keyring if necessary."""
        config = self.get_provider_config(provider)
        if not config:
            return None
        
        key = config.api_key
        if key and key.startswith("keyring:"):
            try:
                import keyring
                return keyring.get_password("ucp-chat", provider)
            except ImportError:
                return None
        
        return key


# Global config manager instance
_config_manager: ConfigManager | None = None


def get_config() -> Config:
    """Get the global configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config


def get_config_manager() -> ConfigManager:
    """Get the global config manager."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
