# src/quackcore/integrations/llms/registry.py
"""
Registry for LLM clients.

This module provides a registry for LLM clients, allowing for
dynamic loading and access to different LLM implementations.
"""

import logging
from typing import Type

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.llms.clients import (
    AnthropicClient,
    LLMClient,
    MockLLMClient,
    OpenAIClient,
)

# Global registry of LLM clients
_LLM_REGISTRY: dict[str, Type[LLMClient]] = {
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "mock": MockLLMClient,
}

logger = logging.getLogger(__name__)


def register_llm_client(name: str, client_class: Type[LLMClient]) -> None:
    """
    Register an LLM client implementation.

    Args:
        name: Name to register the client under
        client_class: LLM client class to register
    """
    _LLM_REGISTRY[name.lower()] = client_class
    logger.debug(f"Registered LLM client: {name}")


def get_llm_client(
    provider: str = "openai",
    model: str | None = None,
    api_key: str | None = None,
    **kwargs,
) -> LLMClient:
    """
    Get an LLM client instance.

    Args:
        provider: Provider name (e.g., "openai", "anthropic", "mock")
        model: Model name to use
        api_key: API key for authentication
        **kwargs: Additional provider-specific arguments

    Returns:
        LLMClient: LLM client instance

    Raises:
        QuackIntegrationError: If the provider is not supported
    """
    provider_lower = provider.lower()

    if provider_lower not in _LLM_REGISTRY:
        registered = ", ".join(_LLM_REGISTRY.keys())
        raise QuackIntegrationError(
            f"Unsupported LLM provider: {provider}. Registered providers: {registered}"
        )

    client_class = _LLM_REGISTRY[provider_lower]

    try:
        return client_class(model=model, api_key=api_key, **kwargs)
    except Exception as e:
        raise QuackIntegrationError(
            f"Failed to initialize {provider} client: {e}",
            context={"provider": provider},
            original_error=e,
        ) from e
