"""Unified LLM provider interface with cost tracking.

Supports OpenAI and Anthropic with automatic token counting and cost calculation.
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
    3. Default: OpenAI with gpt-4o-mini
    """
    provider = provider or os.environ.get("LLM_PROVIDER", "openai")
    
    if provider == "openai":
        model = model or os.environ.get("LLM_MODEL", "gpt-4o-mini")
        return OpenAIProvider(model=model)
    elif provider == "anthropic":
        model = model or os.environ.get("LLM_MODEL", "claude-3-haiku-20240307")
        return AnthropicProvider(model=model)
    else:
        raise ValueError(f"Unknown provider: {provider}. Supported: openai, anthropic")
