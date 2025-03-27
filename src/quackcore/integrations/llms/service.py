# src/quackcore/integrations/llms/service.py
"""
LLM integration service for QuackCore.

This module provides the main service class for LLM integration,
handling configuration, client initialization, and conversation management.
"""

import logging
from collections.abc import Callable, Sequence
from typing import cast

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.core.base import BaseIntegrationService
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.llms.clients import LLMClient
from quackcore.integrations.llms.config import LLMConfig, LLMConfigProvider
from quackcore.integrations.llms.models import ChatMessage, LLMOptions
from quackcore.integrations.llms.registry import get_llm_client


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

            # Extract and validate config
            llm_config = self._extract_config()

            # Determine provider
            provider = self.provider or llm_config.get("default_provider", "openai")

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

            self.client = get_llm_client(**client_args)
            self._initialized = True

            return IntegrationResult.success_result(
                message=f"LLM integration initialized successfully with provider: {provider}"
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

            config_result = self.config_provider.load_config(self.config_path)
            if not config_result.success or not config_result.content:
                self.config = self.config_provider.get_default_config()
            else:
                self.config = config_result.content

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

        return self.client.chat(messages, options, callback)

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

        return self.client.count_tokens(messages)

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