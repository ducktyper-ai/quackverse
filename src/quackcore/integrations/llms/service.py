# src/quackcore/integrations/llms/service.py
"""
LLM integration service for QuackCore.

This module provides the main service class for LLM integration,
handling configuration, client initialization, and conversation management.
"""

import logging
import importlib.util
from collections.abc import Callable, Sequence
from typing import cast

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.core.base import BaseIntegrationService
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.llms.clients import LLMClient, MockLLMClient
from quackcore.integrations.llms.config import LLMConfig, LLMConfigProvider
from quackcore.integrations.llms.models import ChatMessage, LLMOptions


def check_llm_dependencies() -> tuple[bool, str, list[str]]:
    """
    Check if LLM dependencies are available.

    Returns:
        tuple[bool, str, list[str]]: Success status, message, and list of available providers
    """
    available_providers = []

    # Check for OpenAI
    if importlib.util.find_spec("openai") is not None:
        available_providers.append("openai")

    # Check for Anthropic
    if importlib.util.find_spec("anthropic") is not None:
        available_providers.append("anthropic")

    # Always add MockLLM as it has no external dependencies
    available_providers.append("mock")

    if not available_providers or (
            len(available_providers) == 1 and available_providers[0] == "mock"):
        return False, "No LLM providers available. Install OpenAI or Anthropic package.", available_providers

    return True, f"Available LLM providers: {', '.join(available_providers)}", available_providers


class LLMIntegration(BaseIntegrationService):
    """Integration service for LLMs."""

    def __init__(
            self,
            provider: str | None = None,
            model: str | None = None,
            api_key: str | None = None,
            config_path: str | None = None,
            log_level: int = logging.INFO,
    ) -> None:
        """
        Initialize the LLM integration service.

        Args:
            provider: LLM provider name
            model: Model name to use
            api_key: API key for authentication
            config_path: Path to configuration file
            log_level: Logging level
        """
        config_provider = LLMConfigProvider(log_level)
        super().__init__(config_provider, None, config_path, log_level)

        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.client: LLMClient | None = None
        self._using_mock = False

    @property
    def name(self) -> str:
        """
        Get the name of the integration.

        Returns:
            str: Integration name
        """
        return "LLM"

    @property
    def version(self) -> str:
        """
        Get the version of the integration.

        Returns:
            str: Integration version
        """
        return "1.0.0"

    def initialize(self) -> IntegrationResult:
        """
        Initialize the LLM integration.

        This method loads the configuration and initializes the LLM client.

        Returns:
            IntegrationResult: Result of initialization
        """
        try:
            init_result = super().initialize()
            if not init_result.success:
                return init_result

            # Check available LLM providers
            deps_available, deps_message, available_providers = check_llm_dependencies()
            self.logger.info(deps_message)

            # Extract and validate config
            llm_config = self._extract_config()

            # Determine provider
            requested_provider = self.provider or llm_config.get("default_provider",
                                                                 "openai")

            # Fall back to an available provider if the requested one is not available
            provider = requested_provider
            if provider not in available_providers:
                # If we have any real providers, use the first one
                for p in ["openai", "anthropic"]:
                    if p in available_providers:
                        provider = p
                        self.logger.warning(
                            f"Requested provider '{requested_provider}' not available. "
                            f"Using '{provider}' instead."
                        )
                        break
                else:
                    # Fall back to mock if no real providers are available
                    provider = "mock"
                    self._using_mock = True
                    self.logger.warning(
                        f"Requested provider '{requested_provider}' not available and no "
                        f"other LLM providers found. Using MockLLMClient instead."
                    )

            # Get provider-specific config
            provider_config = cast(dict, llm_config.get(provider, {}))

            # Initialize client with appropriate arguments
            client_args = {
                "provider": provider,
                "model": self.model or provider_config.get("default_model"),
                "api_key": self.api_key or provider_config.get("api_key"),
                "timeout": llm_config.get("timeout", 60),
                "retry_count": llm_config.get("retry_count", 3),
                "initial_retry_delay": llm_config.get("initial_retry_delay", 1.0),
                "max_retry_delay": llm_config.get("max_retry_delay", 30.0),
                "log_level": self.log_level,
            }

            # Add provider-specific config
            if provider == "openai":
                client_args["api_base"] = provider_config.get("api_base")
                client_args["organization"] = provider_config.get("organization")
            elif provider == "anthropic":
                client_args["api_base"] = provider_config.get("api_base")

            try:
                # Import the registry functions for getting an LLM client
                from quackcore.integrations.llms.registry import get_llm_client
                self.client = get_llm_client(**client_args)
            except QuackIntegrationError as e:
                # If we can't initialize the requested client, fall back to MockLLMClient
                self.logger.warning(f"Failed to initialize {provider} client: {e}")
                self.logger.warning("Falling back to MockLLMClient")

                # Create a mock client with default responses
                self.client = MockLLMClient()
                self._using_mock = True

            self._initialized = True

            return IntegrationResult.success_result(
                message=(
                    f"LLM integration initialized successfully with provider: {provider}"
                    f"{' (using mock client)' if self._using_mock else ''}"
                )
            )

        except QuackIntegrationError as e:
            self.logger.error(f"Integration error during initialization: {e}")
            return IntegrationResult.error_result(str(e))
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM integration: {e}")
            return IntegrationResult.error_result(
                f"Failed to initialize LLM integration: {e}"
            )

    def _extract_config(self) -> dict:
        """
        Extract and validate the LLM configuration.

        Returns:
            dict: LLM configuration

        Raises:
            QuackIntegrationError: If configuration is invalid
        """
        if not self.config:
            # Get default configuration
            if not self.config_provider:
                raise QuackIntegrationError("Configuration provider not initialized")

            try:
                config_result = self.config_provider.load_config(self.config_path)

                # Handle both ConfigResult and DataResult
                if config_result.success:
                    if hasattr(config_result, "content") and config_result.content:
                        self.config = config_result.content
                    elif hasattr(config_result, "data") and config_result.data:
                        self.config = config_result.data
                    else:
                        self.config = self.config_provider.get_default_config()
                else:
                    self.config = self.config_provider.get_default_config()

            except Exception as e:
                # If loading fails, use default config
                self.logger.warning(f"Failed to load config, using defaults: {e}")
                self.config = self.config_provider.get_default_config()

        # Validate configuration
        try:
            LLMConfig(**self.config)
            return self.config
        except Exception as e:
            raise QuackIntegrationError(f"Invalid LLM configuration: {e}")

    def chat(
            self,
            messages: Sequence[ChatMessage] | Sequence[dict],
            options: LLMOptions | None = None,
            callback: Callable[[str], None] | None = None,
    ) -> IntegrationResult[str]:
        """
        Send a chat completion request to the LLM.

        Args:
            messages: Sequence of messages for the conversation
            options: Additional options for the completion request
            callback: Optional callback function for streaming responses

        Returns:
            IntegrationResult[str]: Result of the chat completion request
        """
        if init_error := self._ensure_initialized():
            return init_error

        if not self.client:
            return IntegrationResult.error_result("LLM client not initialized")

        result = self.client.chat(messages, options, callback)

        # Add a note if we're using the mock client
        if self._using_mock and result.success:
            result.message = f"{result.message or 'Success'} (using mock LLM)"

        return result

    def count_tokens(
            self, messages: Sequence[ChatMessage] | Sequence[dict]
    ) -> IntegrationResult[int]:
        """
        Count the number of tokens in the messages.

        Args:
            messages: Sequence of messages to count tokens for

        Returns:
            IntegrationResult[int]: Result containing the token count
        """
        if init_error := self._ensure_initialized():
            return init_error

        if not self.client:
            return IntegrationResult.error_result("LLM client not initialized")

        result = self.client.count_tokens(messages)

        # Add a note if we're using the mock client
        if self._using_mock and result.success:
            result.message = f"{result.message or 'Success'} (using mock estimation)"

        return result

    def get_client(self) -> LLMClient:
        """
        Get the LLM client instance.

        Returns:
            LLMClient: LLM client instance

        Raises:
            QuackIntegrationError: If the client is not initialized
        """
        if not self._initialized or not self.client:
            raise QuackIntegrationError("LLM client not initialized")

        return self.client

    @property
    def is_using_mock(self) -> bool:
        """
        Check if the service is using a mock client.

        Returns:
            bool: True if using a mock client, False otherwise
        """
        return self._using_mock