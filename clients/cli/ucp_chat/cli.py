"""
UCP Chat CLI - Beautiful terminal interface for LLM chat.

Features:
- Multi-provider support with live switching
- Streaming responses with rich formatting
- UCP tool injection integration
- Session management and export
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.theme import Theme
from rich.text import Text

from ucp_chat.config import Config, ConfigManager, get_config, get_config_manager
from ucp_chat.providers import (
    Message, Provider, create_provider, StreamChunk,
    get_default_base, get_default_model,
)
from ucp_chat.session import ChatSession, SessionManager, get_session_manager
from ucp_chat.ucp_client import UCPClient, create_ucp_client, ToolPrediction

# Rich console with custom theme
custom_theme = Theme({
    "user": "bold cyan",
    "assistant": "bold green",
    "system": "bold yellow",
    "error": "bold red",
    "info": "dim",
    "tool": "bold magenta",
})

console = Console(theme=custom_theme)
app = typer.Typer(
    name="ucp-chat",
    help="Universal Context Protocol Chat - Multi-provider LLM chat with intelligent tools",
    no_args_is_help=False,
)


class ChatApp:
    """Main chat application."""
    
    def __init__(
        self,
        provider_name: str | None = None,
        model: str | None = None,
        ucp_enabled: bool = False,
    ):
        self.config = get_config()
        self.session_manager = get_session_manager()
        self.provider_name = provider_name or self.config.default_provider
        self.model = model
        self.ucp_enabled = ucp_enabled or self.config.ucp.enabled
        
        self.provider: Provider | None = None
        self.ucp_client: UCPClient | None = None
        self.session = ChatSession(
            provider=self.provider_name,
            model=model or "unknown",
            ucp_enabled=self.ucp_enabled,
        )
        self._running = False
    
    async def initialize(self) -> bool:
        """Initialize the chat app."""
        # Get API key
        config_manager = get_config_manager()
        api_key = config_manager.get_api_key(self.provider_name)
        
        if not api_key:
            # Try environment variable
            env_var = f"{self.provider_name.upper()}_API_KEY"
            api_key = os.environ.get(env_var)
        
        if not api_key:
            console.print(
                f"[error]No API key found for {self.provider_name}.[/error]\n"
                f"Set {self.provider_name.upper()}_API_KEY environment variable or run: ucp-chat configure"
            )
            return False
        
        # Get provider config
        prov_config = config_manager.get_provider_config(self.provider_name)
        api_base = prov_config.api_base if prov_config else None
        default_model = prov_config.default_model if prov_config else None
        
        self.model = self.model or default_model or get_default_model(self.provider_name)
        self.session.model = self.model
        
        # Create provider
        self.provider = create_provider(
            name=self.provider_name,
            api_key=api_key,
            api_base=api_base,
            default_model=self.model,
        )
        
        # Initialize UCP client if enabled
        if self.ucp_enabled:
            self.ucp_client = create_ucp_client(
                server_url=self.config.ucp.server_url,
            )
            if await self.ucp_client.connect():
                console.print("[info]Connected to UCP server[/info]")
            else:
                console.print("[info]UCP server unavailable, running without tool injection[/info]")
                self.ucp_client = None
        
        return True
    
    async def shutdown(self) -> None:
        """Clean up resources."""
        if self.provider:
            await self.provider.close()
        if self.ucp_client:
            await self.ucp_client.close()
        
        # Save session
        self.session_manager.save(self.session)
    
    def print_welcome(self) -> None:
        """Print welcome message."""
        console.print()
        console.print(Panel.fit(
            Text.assemble(
                ("UCP Chat", "bold cyan"),
                " - ",
                ("Universal Context Protocol", "italic"),
                "\n\n",
                ("Provider: ", "dim"),
                (self.provider_name, "bold"),
                ("  Model: ", "dim"),
                (self.model, "bold"),
                ("\nUCP: ", "dim"),
                ("Enabled ✓" if self.ucp_client else "Disabled", "green" if self.ucp_client else "dim"),
            ),
            title="[bold]Welcome[/bold]",
            border_style="cyan",
        ))
        console.print()
        console.print("[info]Commands: /help, /switch, /clear, /export, /quit[/info]")
        console.print()
    
    async def get_predicted_tools(self) -> list[dict]:
        """Get predicted tools from UCP."""
        if not self.ucp_client:
            return []
        
        context = self.session.get_context_for_ucp()
        recent_tools = [u["tool_name"] for u in self.session.tool_usages[-5:]]
        
        prediction = await self.ucp_client.predict_tools(
            context=context,
            recent_tools=recent_tools,
            max_tools=5,
        )
        
        if prediction.tools:
            self.session.record_tool_prediction(
                query=context,
                predicted_tools=[t.get("function", {}).get("name", str(t)) for t in prediction.tools],
                scores=prediction.scores,
            )
        
        return prediction.tools
    
    async def send_message(self, user_input: str) -> None:
        """Send a message and stream the response."""
        # Add user message
        self.session.add_message("user", user_input)
        
        # Get predicted tools from UCP
        tools = await self.get_predicted_tools() if self.ucp_enabled else None
        
        if tools:
            tool_names = [t["function"]["name"] for t in tools]
            console.print(f"[tool]📦 Predicted tools: {', '.join(tool_names)}[/tool]")
        
        # Prepare messages for API
        messages = [
            Message(role="system", content="You are a helpful AI assistant."),
            *self.session.messages,
        ]
        
        try:
            # Stream the response
            console.print()
            full_response = ""
            
            with Live(Markdown(""), refresh_per_second=10, console=console) as live:
                async for chunk in await self.provider.chat(
                    messages=messages,
                    model=self.model,
                    tools=tools,
                    stream=True,
                ):
                    if chunk.content:
                        full_response += chunk.content
                        live.update(Markdown(full_response))
                    
                    if chunk.tool_calls:
                        # Handle tool calls
                        for tc in chunk.tool_calls:
                            tool_name = tc.get("function", {}).get("name", "unknown")
                            console.print(f"\n[tool]🔧 Tool call: {tool_name}[/tool]")
            
            # Add assistant response
            if full_response:
                self.session.add_message("assistant", full_response)
            
            console.print()
            
        except Exception as e:
            console.print(f"[error]Error: {e}[/error]")
    
    def handle_command(self, command: str) -> bool:
        """Handle a slash command. Returns True if should continue, False to quit."""
        parts = command.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd in ("/quit", "/q", "/exit"):
            return False
        
        elif cmd == "/help":
            help_table = Table(title="Commands")
            help_table.add_column("Command", style="cyan")
            help_table.add_column("Description")
            
            help_table.add_row("/help", "Show this help message")
            help_table.add_row("/switch <provider> [model]", "Switch provider and/or model")
            help_table.add_row("/clear", "Clear conversation history")
            help_table.add_row("/history", "Show conversation history")
            help_table.add_row("/export", "Export session for training")
            help_table.add_row("/sessions", "List saved sessions")
            help_table.add_row("/ucp", "Toggle UCP tool injection")
            help_table.add_row("/tools", "Show available tools")
            help_table.add_row("/quit", "Exit the chat")
            
            console.print(help_table)
        
        elif cmd == "/switch":
            if args:
                switch_parts = args.split()
                new_provider = switch_parts[0]
                new_model = switch_parts[1] if len(switch_parts) > 1 else None
                
                # This would need to reinitialize - simplified version
                console.print(f"[info]Switching to {new_provider}" + 
                            (f" with model {new_model}" if new_model else "") + 
                            "...[/info]")
                self.provider_name = new_provider
                if new_model:
                    self.model = new_model
                console.print("[info]Switch complete. Note: Full switch requires restart.[/info]")
            else:
                console.print("[info]Usage: /switch <provider> [model][/info]")
        
        elif cmd == "/clear":
            self.session.messages.clear()
            console.print("[info]Conversation cleared.[/info]")
        
        elif cmd == "/history":
            if not self.session.messages:
                console.print("[info]No messages yet.[/info]")
            else:
                for msg in self.session.messages:
                    style = msg.role
                    prefix = "🧑" if msg.role == "user" else "🤖"
                    content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                    console.print(f"[{style}]{prefix} {msg.role.capitalize()}:[/{style}] {content}")
        
        elif cmd == "/export":
            path = self.session_manager.export_training_data()
            console.print(f"[info]Exported training data to: {path}[/info]")
        
        elif cmd == "/sessions":
            sessions = self.session_manager.list_sessions()
            if not sessions:
                console.print("[info]No saved sessions.[/info]")
            else:
                table = Table(title="Saved Sessions")
                table.add_column("ID", style="dim")
                table.add_column("Name")
                table.add_column("Provider")
                table.add_column("Messages")
                
                for s in sessions[:10]:
                    table.add_row(
                        s["id"][:8],
                        s["name"],
                        s["provider"],
                        str(s["message_count"]),
                    )
                console.print(table)
        
        elif cmd == "/ucp":
            self.ucp_enabled = not self.ucp_enabled
            status = "enabled" if self.ucp_enabled else "disabled"
            console.print(f"[info]UCP tool injection {status}.[/info]")
        
        elif cmd == "/tools":
            if self.ucp_client:
                asyncio.get_event_loop().run_until_complete(self._show_tools())
            else:
                console.print("[info]UCP not connected, no tools available.[/info]")
        
        else:
            console.print(f"[error]Unknown command: {cmd}. Type /help for help.[/error]")
        
        return True
    
    async def _show_tools(self) -> None:
        """Show available UCP tools."""
        tools = await self.ucp_client.get_available_tools()
        if not tools:
            console.print("[info]No tools available.[/info]")
            return
        
        table = Table(title="Available Tools")
        table.add_column("Name", style="cyan")
        table.add_column("Description")
        
        for tool in tools:
            func = tool.get("function", tool)
            table.add_row(func.get("name", "unknown"), func.get("description", "")[:60])
        
        console.print(table)
    
    async def run(self) -> None:
        """Run the main chat loop."""
        if not await self.initialize():
            return
        
        self.print_welcome()
        self._running = True
        
        try:
            while self._running:
                try:
                    # Get user input
                    user_input = Prompt.ask("[user]You[/user]")
                    
                    if not user_input.strip():
                        continue
                    
                    # Handle commands
                    if user_input.startswith("/"):
                        self._running = self.handle_command(user_input)
                        continue
                    
                    # Send message
                    await self.send_message(user_input)
                    
                except KeyboardInterrupt:
                    console.print("\n[info]Use /quit to exit.[/info]")
                    continue
                
        finally:
            await self.shutdown()
            console.print("\n[info]Goodbye![/info]")


@app.command()
def chat(
    provider: str = typer.Option(None, "--provider", "-p", help="LLM provider to use"),
    model: str = typer.Option(None, "--model", "-m", help="Model to use"),
    ucp: bool = typer.Option(False, "--ucp", help="Enable UCP tool injection"),
):
    """Start an interactive chat session."""
    chat_app = ChatApp(
        provider_name=provider,
        model=model,
        ucp_enabled=ucp,
    )
    asyncio.run(chat_app.run())


@app.command()
def configure():
    """Configure API keys and settings."""
    config_manager = get_config_manager()
    
    console.print(Panel.fit(
        "[bold]UCP Chat Configuration[/bold]\n\n"
        "Configure your API keys for different providers.",
        border_style="cyan",
    ))
    
    # Show available providers
    providers = list(config_manager.config.providers.keys())
    
    console.print("\n[bold]Available Providers:[/bold]")
    for i, p in enumerate(providers, 1):
        has_key = bool(config_manager.get_api_key(p))
        status = "✓" if has_key else "✗"
        color = "green" if has_key else "dim"
        console.print(f"  [{color}]{i}. {p} {status}[/{color}]")
    
    # Let user select provider to configure
    console.print()
    provider = Prompt.ask(
        "Select provider to configure",
        choices=providers,
        default=config_manager.config.default_provider,
    )
    
    # Get API key
    current_key = config_manager.get_api_key(provider)
    masked_key = f"****{current_key[-4:]}" if current_key else "not set"
    console.print(f"Current key: {masked_key}")
    
    new_key = Prompt.ask(f"Enter API key for {provider} (or press Enter to skip)")
    
    if new_key:
        use_keyring = Confirm.ask("Store in system keyring?", default=True)
        config_manager.set_api_key(provider, new_key, use_keyring=use_keyring)
        console.print(f"[green]✓ API key saved for {provider}[/green]")
    
    # Set default provider
    if Confirm.ask(f"Set {provider} as default provider?"):
        config_manager.config.default_provider = provider
        config_manager.save()
        console.print(f"[green]✓ {provider} set as default[/green]")


@app.command()
def providers():
    """List available providers and their status."""
    config_manager = get_config_manager()
    
    table = Table(title="Available Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Default Model")
    table.add_column("API Base")
    table.add_column("Key Set", justify="center")
    
    for name, pconfig in config_manager.config.providers.items():
        has_key = bool(config_manager.get_api_key(name))
        table.add_row(
            name,
            pconfig.default_model or "—",
            (pconfig.api_base or "—")[:40],
            "[green]✓[/green]" if has_key else "[dim]✗[/dim]",
        )
    
    console.print(table)
    console.print(f"\n[info]Default provider: {config_manager.config.default_provider}[/info]")


@app.command()
def sessions():
    """List and manage chat sessions."""
    session_manager = get_session_manager()
    session_list = session_manager.list_sessions()
    
    if not session_list:
        console.print("[info]No saved sessions.[/info]")
        return
    
    table = Table(title="Chat Sessions")
    table.add_column("ID", style="dim")
    table.add_column("Name")
    table.add_column("Provider")
    table.add_column("Model")
    table.add_column("Messages", justify="right")
    table.add_column("Updated")
    
    for s in session_list:
        table.add_row(
            s["id"][:8],
            s["name"][:20],
            s["provider"],
            s["model"][:20] if s["model"] else "—",
            str(s["message_count"]),
            s["updated_at"][:10] if s["updated_at"] else "—",
        )
    
    console.print(table)


@app.command(name="export")
def export_data(
    output: Path = typer.Option(None, "--output", "-o", help="Output file path"),
):
    """Export all sessions as training data for UCP."""
    session_manager = get_session_manager()
    path = session_manager.export_training_data(output)
    console.print(f"[green]✓ Exported training data to: {path}[/green]")


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """UCP Chat - Universal Context Protocol CLI."""
    if ctx.invoked_subcommand is None:
        # Default to chat command
        chat()


if __name__ == "__main__":
    app()
