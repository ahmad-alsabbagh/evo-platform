"""Unified LLM provider interface with cost tracking.

Supports OpenAI, Anthropic, Groq, and Ollama with automatic token counting and cost calculation.
Costs are tracked per request and integrated with the existing CostTracker.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple


@dataclass
class LLMResponse:
    """Unified response from any LLM provider."""
    content: str
    input_tokens: int
    output_tokens: int
    model: str
    provider: str
    cost_usd: float


class LLMProviderBase(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        """Call the LLM with messages and return unified response."""
        pass


class OllamaProvider(LLMProviderBase):
    """Ollama local LLM provider - FREE, no API key needed.
    
    Runs models locally via Ollama (ollama.ai).
    Supports: llama3, mistral, gemma, phi, and more.
    """

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        # Ollama is free - running locally
        self.pricing = {"input": 0.0, "output": 0.0}

    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        import httpx
        
        response = httpx.post(
            f"{self.base_url}/api/chat",
            json={
                "model": self.model,
                "messages": messages,
                "stream": False,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        
        content = data["message"]["content"]
        # Ollama doesn't provide token counts in older versions
        # Estimate: ~4 chars per token
        input_chars = sum(len(m["content"]) for m in messages)
        output_chars = len(content)
        input_tokens = input_chars // 4
        output_tokens = output_chars // 4
        
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            provider="ollama",
            cost_usd=0.0,  # Free!
        )


class GroqProvider(LLMProviderBase):
    """Groq Cloud LLM provider - FREE tier available.
    
    Ultra-fast inference on Llama 3.1, Mixtral, and more.
    Sign up at https://console.groq.com for free API key.
    Free tier: ~30 requests/minute, no credit card needed.
    """

    # Pricing per 1K tokens (Groq free tier)
    PRICING = {
        "llama-3.1-70b-versatile": {"input": 0.0, "output": 0.0},  # Free tier
        "llama-3.1-8b-instant": {"input": 0.0, "output": 0.0},  # Free tier
        "mixtral-8x7b-32768": {"input": 0.0, "output": 0.0},  # Free tier
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-70b-versatile"):
        from groq import Groq
        self.client = Groq(api_key=api_key or os.environ.get("GROQ_API_KEY", ""))
        self.model = model

    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        pricing = self.PRICING.get(self.model, self.PRICING["llama-3.1-70b-versatile"])
        cost_usd = (
            (input_tokens / 1000.0) * pricing["input"] +
            (output_tokens / 1000.0) * pricing["output"]
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            provider="groq",
            cost_usd=cost_usd,
        )


class OpenAIProvider(LLMProviderBase):
    """OpenAI API provider with cost tracking."""

    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"])
        self.model = model

    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        
        pricing = self.PRICING.get(self.model, self.PRICING["gpt-4o-mini"])
        cost_usd = (
            (input_tokens / 1000.0) * pricing["input"] +
            (output_tokens / 1000.0) * pricing["output"]
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            provider="openai",
            cost_usd=cost_usd,
        )


class AnthropicProvider(LLMProviderBase):
    """Anthropic API provider with cost tracking."""

    # Pricing per 1K tokens (as of 2024)
    PRICING = {
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
    }

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key or os.environ["ANTHROPIC_API_KEY"])
        self.model = model

    def call(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        # Convert OpenAI format to Anthropic format
        system_msg = ""
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                chat_messages.append(msg)

        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1000),
            system=system_msg,
            messages=chat_messages,
        )

        input_tokens = response.usage.input_tokens
        output_tokens = response.usage.output_tokens
        
        pricing = self.PRICING.get(self.model, self.PRICING["claude-3-haiku-20240307"])
        cost_usd = (
            (input_tokens / 1000.0) * pricing["input"] +
            (output_tokens / 1000.0) * pricing["output"]
        )

        return LLMResponse(
            content=response.content[0].text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            model=self.model,
            provider="anthropic",
            cost_usd=cost_usd,
        )


def get_llm_provider(provider: Optional[str] = None, model: Optional[str] = None) -> LLMProviderBase:
    """Factory function to get LLM provider from environment or explicit config.
    
    Priority:
    1. Explicit provider/model arguments
    2. Environment variables (LLM_PROVIDER, LLM_MODEL)
    3. Default: Ollama with llama3 (FREE, no API key)
    
    Supported providers:
    - ollama: FREE, local, no API key (models: llama3, mistral, gemma)
    - groq: FREE tier, fast, needs API key from groq.com (models: llama-3.1-70b, mixtral)
    - openai: Paid, needs API key (models: gpt-4o-mini, gpt-4o)
    - anthropic: Paid, needs API key (models: claude-3-haiku, claude-3-sonnet)
    """
    provider = provider or os.environ.get("LLM_PROVIDER", "ollama")
    
    if provider == "ollama":
        model = model or os.environ.get("LLM_MODEL", "llama3")
        return OllamaProvider(model=model)
    elif provider == "groq":
        model = model or os.environ.get("LLM_MODEL", "llama-3.1-70b-versatile")
        return GroqProvider(model=model)
    elif provider == "openai":
        model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        return OpenAIProvider(model=model)
    elif provider == "anthropic":
        model = model or os.environ.get("LLM_MODEL", "claude-3-haiku-20240307")
        return AnthropicProvider(model=model)
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: ollama, groq, openai, anthropic")
