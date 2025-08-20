# quack-core/src/quack-core/integrations/llms/registry.py
"""
Registry for LLM clients.

This module provides a registry for LLM clients, allowing for
dynamic loading and access to different LLM implementations.
"""


from quackcore.errors import QuackIntegrationError
from quackcore.integrations.llms.clients.anthropic import AnthropicClient
from quackcore.integrations.llms.clients.base import LLMClient
from quackcore.integrations.llms.clients.mock import MockLLMClient
from quackcore.integrations.llms.clients.ollama import OllamaClient
from quackcore.integrations.llms.clients.openai import OpenAIClient
from quackcore.logging import get_logger

# Global registry of LLM clients
_LLM_REGISTRY: dict[str, type[LLMClient]] = {
    "openai": OpenAIClient,
    "anthropic": AnthropicClient,
    "ollama": OllamaClient,
    "mock": MockLLMClient,
}

logger = get_logger(__name__)


def register_llm_client(name: str, client_class: type[LLMClient]) -> None:
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
        provider: Provider name (e.g., "openai", "anthropic", "ollama", "mock")
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
        # Pass provider-specific kwargs correctly
        client_kwargs = {"model": model, "api_key": api_key}
        client_kwargs.update(kwargs)

        return client_class(**client_kwargs)
    except Exception as e:
        raise QuackIntegrationError(
            f"Failed to initialize {provider} client: {e}",
            context={"provider": provider},
            original_error=e,
        ) from e
