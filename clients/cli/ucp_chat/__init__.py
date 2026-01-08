"""
UCP Chat - Universal Context Protocol CLI Client.

A multi-provider LLM chat interface with context observation
and intelligent tool injection.
"""

__version__ = "0.1.0"
__all__ = ["ChatSession", "Provider", "UCPClient"]

from ucp_chat.providers import Provider
from ucp_chat.session import ChatSession
from ucp_chat.ucp_client import UCPClient
