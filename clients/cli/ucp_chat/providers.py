"""
LLM Provider implementations.

Provides a unified interface for multiple LLM providers,
with context capture and tool injection support.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncIterator

import httpx


@dataclass
class Message:
    """A chat message."""
    role: str
    content: str
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class StreamChunk:
    """A chunk from a streaming response."""
    content: str
    finish_reason: str | None = None
    tool_calls: list[dict] | None = None


@dataclass
class ChatResponse:
    """A complete chat response."""
    message: Message
    model: str
    usage: dict[str, int] | None = None
    finish_reason: str | None = None
    raw_response: dict | None = None


class Provider(ABC):
    """Abstract base class for LLM providers."""
    
    name: str
    supports_streaming: bool = True
    supports_tools: bool = True
    supports_vision: bool = False
    
    def __init__(
        self,
        api_key: str,
        api_base: str | None = None,
        default_model: str | None = None,
        **kwargs: Any,
    ):
        self.api_key = api_key
        self.api_base = api_base
        self.default_model = default_model
        self.client = httpx.AsyncClient(timeout=120.0)
    
    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        tools: list[dict] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatResponse | AsyncIterator[StreamChunk]:
        """Send a chat request to the provider."""
        pass
    
    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


class OpenAICompatibleProvider(Provider):
    """Provider for OpenAI-compatible APIs (OpenAI, Groq, Together, etc.)."""
    
    name = "openai_compatible"
    
    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        default_model: str = "gpt-4o",
        **kwargs: Any,
    ):
        super().__init__(api_key, api_base, default_model, **kwargs)
        self.api_base = api_base.rstrip("/")
    
    def _build_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
    
    def _format_messages(self, messages: list[Message]) -> list[dict]:
        formatted = []
        for msg in messages:
            m = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            if msg.name:
                m["name"] = msg.name
            formatted.append(m)
        return formatted
    
    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        tools: list[dict] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatResponse | AsyncIterator[StreamChunk]:
        model = model or self.default_model
        
        payload: dict[str, Any] = {
            "model": model,
            "messages": self._format_messages(messages),
            "stream": stream,
        }
        
        if tools:
            payload["tools"] = tools
        
        # Add any extra kwargs (temperature, max_tokens, etc.)
        payload.update(kwargs)
        
        if stream:
            return self._stream_chat(payload)
        else:
            return await self._sync_chat(payload)
    
    async def _sync_chat(self, payload: dict) -> ChatResponse:
        response = await self.client.post(
            f"{self.api_base}/chat/completions",
            headers=self._build_headers(),
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        
        choice = data["choices"][0]
        message = choice["message"]
        
        return ChatResponse(
            message=Message(
                role=message.get("role", "assistant"),
                content=message.get("content", ""),
                tool_calls=message.get("tool_calls"),
            ),
            model=data.get("model", payload["model"]),
            usage=data.get("usage"),
            finish_reason=choice.get("finish_reason"),
            raw_response=data,
        )
    
    async def _stream_chat(self, payload: dict) -> AsyncIterator[StreamChunk]:
        async with self.client.stream(
            "POST",
            f"{self.api_base}/chat/completions",
            headers=self._build_headers(),
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        choice = data["choices"][0]
                        delta = choice.get("delta", {})
                        yield StreamChunk(
                            content=delta.get("content", ""),
                            finish_reason=choice.get("finish_reason"),
                            tool_calls=delta.get("tool_calls"),
                        )
                    except json.JSONDecodeError:
                        continue


class AnthropicProvider(Provider):
    """Provider for Anthropic's Claude API."""
    
    name = "anthropic"
    supports_vision = True
    
    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.anthropic.com",
        default_model: str = "claude-sonnet-4-20250514",
        **kwargs: Any,
    ):
        super().__init__(api_key, api_base, default_model, **kwargs)
        self.api_base = api_base.rstrip("/")
    
    def _build_headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
    
    def _format_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Convert to Anthropic format, extracting system message."""
        system = None
        formatted = []
        
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                role = "user" if msg.role == "user" else "assistant"
                if msg.tool_call_id:
                    # Tool result
                    formatted.append({
                        "role": "user",
                        "content": [{
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content,
                        }]
                    })
                elif msg.tool_calls:
                    # Assistant with tool use
                    formatted.append({
                        "role": "assistant",
                        "content": [
                            {"type": "text", "text": msg.content or ""},
                            *[{
                                "type": "tool_use",
                                "id": tc["id"],
                                "name": tc["function"]["name"],
                                "input": json.loads(tc["function"]["arguments"]),
                            } for tc in msg.tool_calls]
                        ]
                    })
                else:
                    formatted.append({"role": role, "content": msg.content})
        
        return system, formatted
    
    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI tool format to Anthropic format."""
        anthropic_tools = []
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tools.append({
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {"type": "object", "properties": {}}),
                })
        return anthropic_tools
    
    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        tools: list[dict] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatResponse | AsyncIterator[StreamChunk]:
        model = model or self.default_model
        system, formatted_messages = self._format_messages(messages)
        
        payload: dict[str, Any] = {
            "model": model,
            "messages": formatted_messages,
            "max_tokens": kwargs.pop("max_tokens", 8192),
        }
        
        if system:
            payload["system"] = system
        
        if tools:
            payload["tools"] = self._convert_tools(tools)
        
        if stream:
            payload["stream"] = True
            return self._stream_chat(payload)
        else:
            return await self._sync_chat(payload)
    
    async def _sync_chat(self, payload: dict) -> ChatResponse:
        response = await self.client.post(
            f"{self.api_base}/v1/messages",
            headers=self._build_headers(),
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        
        # Extract content
        content_blocks = data.get("content", [])
        text_content = ""
        tool_calls = []
        
        for block in content_blocks:
            if block["type"] == "text":
                text_content += block.get("text", "")
            elif block["type"] == "tool_use":
                tool_calls.append({
                    "id": block["id"],
                    "type": "function",
                    "function": {
                        "name": block["name"],
                        "arguments": json.dumps(block["input"]),
                    }
                })
        
        return ChatResponse(
            message=Message(
                role="assistant",
                content=text_content,
                tool_calls=tool_calls if tool_calls else None,
            ),
            model=data.get("model", payload["model"]),
            usage={
                "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
            },
            finish_reason=data.get("stop_reason"),
            raw_response=data,
        )
    
    async def _stream_chat(self, payload: dict) -> AsyncIterator[StreamChunk]:
        async with self.client.stream(
            "POST",
            f"{self.api_base}/v1/messages",
            headers=self._build_headers(),
            json=payload,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    try:
                        data = json.loads(data_str)
                        event_type = data.get("type")
                        
                        if event_type == "content_block_delta":
                            delta = data.get("delta", {})
                            if delta.get("type") == "text_delta":
                                yield StreamChunk(content=delta.get("text", ""))
                        elif event_type == "message_stop":
                            yield StreamChunk(content="", finish_reason="stop")
                            break
                    except json.JSONDecodeError:
                        continue


class GoogleProvider(Provider):
    """Provider for Google's Gemini API."""
    
    name = "google"
    supports_vision = True
    
    def __init__(
        self,
        api_key: str,
        api_base: str = "https://generativelanguage.googleapis.com/v1beta",
        default_model: str = "gemini-2.0-flash",
        **kwargs: Any,
    ):
        super().__init__(api_key, api_base, default_model, **kwargs)
        self.api_base = api_base.rstrip("/")
    
    def _format_messages(self, messages: list[Message]) -> tuple[str | None, list[dict]]:
        """Convert to Gemini format."""
        system = None
        formatted = []
        
        for msg in messages:
            if msg.role == "system":
                system = msg.content
            else:
                role = "user" if msg.role == "user" else "model"
                formatted.append({
                    "role": role,
                    "parts": [{"text": msg.content}]
                })
        
        return system, formatted
    
    async def chat(
        self,
        messages: list[Message],
        model: str | None = None,
        tools: list[dict] | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> ChatResponse | AsyncIterator[StreamChunk]:
        model = model or self.default_model
        system, formatted_messages = self._format_messages(messages)
        
        payload: dict[str, Any] = {
            "contents": formatted_messages,
        }
        
        if system:
            payload["systemInstruction"] = {"parts": [{"text": system}]}
        
        if tools:
            # Convert OpenAI tools to Gemini format
            function_declarations = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool["function"]
                    function_declarations.append({
                        "name": func["name"],
                        "description": func.get("description", ""),
                        "parameters": func.get("parameters", {}),
                    })
            if function_declarations:
                payload["tools"] = [{"functionDeclarations": function_declarations}]
        
        endpoint = f"{self.api_base}/models/{model}:generateContent"
        if stream:
            endpoint = f"{self.api_base}/models/{model}:streamGenerateContent"
            return self._stream_chat(endpoint, payload)
        else:
            return await self._sync_chat(endpoint, payload)
    
    async def _sync_chat(self, endpoint: str, payload: dict) -> ChatResponse:
        response = await self.client.post(
            endpoint,
            params={"key": self.api_key},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        
        candidate = data["candidates"][0]
        content = candidate.get("content", {})
        parts = content.get("parts", [])
        
        text_content = ""
        tool_calls = []
        
        for part in parts:
            if "text" in part:
                text_content += part["text"]
            elif "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append({
                    "id": f"call_{fc['name']}",
                    "type": "function",
                    "function": {
                        "name": fc["name"],
                        "arguments": json.dumps(fc.get("args", {})),
                    }
                })
        
        return ChatResponse(
            message=Message(
                role="assistant",
                content=text_content,
                tool_calls=tool_calls if tool_calls else None,
            ),
            model=payload.get("model", "gemini"),
            usage=data.get("usageMetadata"),
            finish_reason=candidate.get("finishReason"),
            raw_response=data,
        )
    
    async def _stream_chat(self, endpoint: str, payload: dict) -> AsyncIterator[StreamChunk]:
        response = await self.client.post(
            endpoint,
            params={"key": self.api_key, "alt": "sse"},
            json=payload,
        )
        response.raise_for_status()
        
        for line in response.text.split("\n"):
            if line.startswith("data: "):
                data_str = line[6:]
                try:
                    data = json.loads(data_str)
                    candidate = data.get("candidates", [{}])[0]
                    content = candidate.get("content", {})
                    parts = content.get("parts", [])
                    
                    for part in parts:
                        if "text" in part:
                            yield StreamChunk(content=part["text"])
                    
                    if candidate.get("finishReason"):
                        yield StreamChunk(content="", finish_reason=candidate["finishReason"])
                except json.JSONDecodeError:
                    continue


# Factory function to create providers
def create_provider(
    name: str,
    api_key: str,
    api_base: str | None = None,
    default_model: str | None = None,
    **kwargs: Any,
) -> Provider:
    """Create a provider instance by name."""
    
    # OpenAI-compatible providers
    openai_compatible = {
        "openai", "groq", "together", "openrouter", "deepseek", "ollama",
        "lmstudio", "zai", "fireworks", "xai", "perplexity", "sambanova",
        "cerebras", "hyperbolic", "nebius", "mistral",
    }
    
    if name in openai_compatible:
        provider = OpenAICompatibleProvider(
            api_key=api_key,
            api_base=api_base or get_default_base(name),
            default_model=default_model or get_default_model(name),
            **kwargs,
        )
        provider.name = name
        return provider
    elif name == "anthropic":
        return AnthropicProvider(
            api_key=api_key,
            api_base=api_base,
            default_model=default_model,
            **kwargs,
        )
    elif name == "google":
        return GoogleProvider(
            api_key=api_key,
            api_base=api_base,
            default_model=default_model,
            **kwargs,
        )
    else:
        # Default to OpenAI-compatible
        return OpenAICompatibleProvider(
            api_key=api_key,
            api_base=api_base or "https://api.openai.com/v1",
            default_model=default_model,
            **kwargs,
        )


def get_default_base(name: str) -> str:
    """Get default API base for a provider."""
    bases = {
        "openai": "https://api.openai.com/v1",
        "groq": "https://api.groq.com/openai/v1",
        "together": "https://api.together.xyz/v1",
        "openrouter": "https://openrouter.ai/api/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "ollama": "http://localhost:11434/v1",
        "lmstudio": "http://localhost:1234/v1",
        "zai": "https://zai-api.zuzu.so/v1",
        "fireworks": "https://api.fireworks.ai/inference/v1",
        "xai": "https://api.x.ai/v1",
        "perplexity": "https://api.perplexity.ai",
        "sambanova": "https://api.sambanova.ai/v1",
        "cerebras": "https://api.cerebras.ai/v1",
        "hyperbolic": "https://api.hyperbolic.xyz/v1",
        "nebius": "https://api.studio.nebius.ai/v1",
        "mistral": "https://api.mistral.ai/v1",
    }
    return bases.get(name, "https://api.openai.com/v1")


def get_default_model(name: str) -> str:
    """Get default model for a provider."""
    models = {
        "openai": "gpt-4o",
        "groq": "llama-3.3-70b-versatile",
        "together": "meta-llama/Llama-3.3-70B-Instruct-Turbo",
        "openrouter": "anthropic/claude-3.5-sonnet",
        "deepseek": "deepseek-chat",
        "ollama": "llama3.2",
        "lmstudio": "local-model",
        "zai": "gemini-2.5-pro",
        "fireworks": "accounts/fireworks/models/llama-v3p3-70b-instruct",
        "xai": "grok-beta",
        "perplexity": "sonar-pro",
        "sambanova": "Meta-Llama-3.3-70B-Instruct",
        "cerebras": "llama-3.3-70b",
        "hyperbolic": "meta-llama/Llama-3.3-70B-Instruct",
        "nebius": "meta-llama/Meta-Llama-3.1-70B-Instruct",
        "mistral": "mistral-large-latest",
    }
    return models.get(name, "gpt-4o")
