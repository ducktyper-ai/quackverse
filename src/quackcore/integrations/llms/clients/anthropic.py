# src/quackcore/integrations/llms/clients/anthropic.py
"""
Anthropic LLM client implementation.

This module provides a client for the Anthropic API, supporting chat completions
and token counting with proper error handling and retry logic.
"""

import logging
import os
from collections.abc import Callable
from typing import Any

from quackcore.errors import QuackApiError, QuackIntegrationError
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.llms.clients.base import LLMClient
from quackcore.integrations.llms.models import ChatMessage, LLMOptions, RoleType


class AnthropicClient(LLMClient):
    """Anthropic LLM client implementation."""

    def __init__(
            self,
            model: str | None = None,
            api_key: str | None = None,
            api_base: str | None = None,
            timeout: int = 60,
            retry_count: int = 3,
            initial_retry_delay: float = 1.0,
            max_retry_delay: float = 30.0,
            log_level: int = logging.INFO,
            **kwargs: Any,
    ) -> None:
        """
        Initialize the Anthropic client.

        Args:
            model: Model name to use
            api_key: Anthropic API key
            api_base: Anthropic API base URL
            timeout: Request timeout in seconds
            retry_count: Number of retries for failed requests
            initial_retry_delay: Initial delay for exponential backoff
            max_retry_delay: Maximum delay between retries
            log_level: Logging level
            **kwargs: Additional Anthropic-specific arguments
        """
        super().__init__(
            model=model,
            api_key=api_key,
            timeout=timeout,
            retry_count=retry_count,
            initial_retry_delay=initial_retry_delay,
            max_retry_delay=max_retry_delay,
            log_level=log_level,
            **kwargs,
        )
        self._api_base = api_base
        self._client = None

    def _get_client(self) -> Any:
        """
        Get the Anthropic client instance.

        Returns:
            Any: Anthropic client instance

        Raises:
            QuackIntegrationError: If Anthropic package is not installed
        """
        if self._client is None:
            try:
                from anthropic import Anthropic

                # Get API key from environment variable if not provided
                api_key = self._api_key or self._get_api_key_from_env()

                kwargs = {}
                if self._api_base:
                    kwargs["base_url"] = self._api_base

                self._client = Anthropic(api_key=api_key, **kwargs)
            except ImportError:
                raise QuackIntegrationError(
                    "Anthropic package not installed. "
                    "Please install it with: pip install anthropic"
                )

        return self._client

    def _get_api_key_from_env(self) -> str:
        """
        Get the Anthropic API key from environment variables.

        Returns:
            str: Anthropic API key

        Raises:
            QuackIntegrationError: If API key is not provided or available in environment
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise QuackIntegrationError(
                "Anthropic API key not provided. "
                "Please provide it as an argument or set the ANTHROPIC_API_KEY environment variable."
            )
        return api_key

    @property
    def model(self) -> str:
        """
        Get the model name.

        Returns:
            str: Model name to use for requests
        """
        if not self._model:
            # Set default model if not specified
            self._model = "claude-3-opus-20240229"
        return self._model

    def _convert_message_to_anthropic(self, message: ChatMessage) -> dict:
        """
        Convert a ChatMessage to the format expected by Anthropic.

        Args:
            message: ChatMessage to convert

        Returns:
            dict: Message in Anthropic format
        """
        role = "user" if message.role == RoleType.USER else "assistant"
        return {
            "role": role,
            "content": message.content or "",
        }

    def _handle_streaming(
            self,
            client: Any,
            model: str,
            system: str | None,
            messages: list[dict],
            params: dict,
            callback: Callable[[str], None] | None,
    ) -> str:
        """
        Handle streaming responses from the Anthropic API.

        Args:
            client: Anthropic client instance
            model: Model name
            system: System message
            messages: List of messages in Anthropic format
            params: Anthropic API parameters
            callback: Callback function for streaming responses

        Returns:
            str: Complete response text

        Raises:
            QuackApiError: If there's an error with the Anthropic API
        """
        collected_content = []

        try:
            with client.messages.stream(
                    model=model,
                    messages=messages,
                    system=system,
                    stream=True,
                    **params
            ) as stream:
                for chunk in stream:
                    if chunk.type == "content_block_delta" and chunk.delta.text:
                        collected_content.append(chunk.delta.text)
                        if callback:
                            callback(chunk.delta.text)

            return "".join(collected_content)
        except Exception as e:
            # Convert Anthropic errors to QuackApiError
            raise self._convert_error(e)

    def _convert_error(self, error: Exception) -> QuackApiError:
        """
        Convert Anthropic errors to QuackApiError.

        Args:
            error: Original error

        Returns:
            QuackApiError: Converted error
        """
        error_str = str(error)

        # Check for specific error types
        if "rate" in error_str.lower() and "limit" in error_str.lower():
            return QuackApiError(
                f"Anthropic rate limit exceeded: {error}",
                service="Anthropic",
                api_method="messages.create",
                original_error=error
            )
        elif "api_key" in error_str.lower() and (
                "invalid" in error_str.lower() or "incorrect" in error_str.lower()
        ):
            return QuackApiError(
                f"Invalid Anthropic API key: {error}",
                service="Anthropic",
                api_method="messages.create",
                original_error=error,
            )
        elif "quota" in error_str.lower():
            return QuackApiError(
                f"Insufficient Anthropic quota: {error}",
                service="Anthropic",
                api_method="messages.create",
                original_error=error,
            )
        else:
            return QuackApiError(
                f"Anthropic API error: {error}",
                service="Anthropic",
                api_method="messages.create",
                original_error=error,
            )

    def _chat_with_provider(
            self,
            messages: list[ChatMessage],
            options: LLMOptions,
            callback: Callable[[str], None] | None = None,
    ) -> IntegrationResult[str]:
        """
        Send a chat completion request to the Anthropic API.

        Args:
            messages: List of messages for the conversation
            options: Additional options for the completion request
            callback: Optional callback function for streaming responses

        Returns:
            IntegrationResult[str]: Result of the chat completion request

        Raises:
            QuackIntegrationError: If Anthropic package is not installed
            QuackApiError: If there's an error with the Anthropic API
        """
        try:
            client = self._get_client()

            # Convert messages to the format expected by Anthropic
            system_message = None
            anthropic_messages = []

            for msg in messages:
                if msg.role == RoleType.SYSTEM:
                    system_message = msg.content
                else:
                    anthropic_messages.append(self._convert_message_to_anthropic(msg))

            # Prepare parameters for Anthropic API call
            params = {
                "top_p": options.top_p,
            }

            if options.stop:
                params["stop_sequences"] = options.stop

            # Override model if specified in options
            model = options.model or self.model

            # Handle streaming if callback is provided
            if callback and not options.stream:
                options.stream = True
                params["stream"] = True

            if options.stream:
                response_text = self._handle_streaming(
                    client, model, system_message, anthropic_messages, params, callback
                )
                return IntegrationResult.success_result(response_text)
            else:
                # Make the API call
                response = client.messages.create(
                    model=model,
                    messages=anthropic_messages,
                    system=system_message,
                    max_tokens=options.max_tokens or 1024,
                    temperature=options.temperature,
                    **params
                )

                # Process the response
                result = response.content[0].text
                return IntegrationResult.success_result(result)

        except ImportError as e:
            raise QuackIntegrationError(
                f"Failed to import Anthropic package: {e}",
                original_error=e,
            ) from e
        except Exception as e:
            # Convert Anthropic errors to QuackApiError
            raise self._convert_error(e)

    def _count_tokens_with_provider(self, messages: list[ChatMessage]) -> \
    IntegrationResult[int]:
        """
        Count the number of tokens in the messages using Anthropic's tokenizer.

        Args:
            messages: List of messages to count tokens for

        Returns:
            IntegrationResult[int]: Result containing the token count
        """
        try:
            # Separate system message from other messages
            system_message = None
            anthropic_messages = []

            for msg in messages:
                if msg.role == RoleType.SYSTEM:
                    system_message = msg.content
                else:
                    anthropic_messages.append(self._convert_message_to_anthropic(msg))

            try:
                # Get the client (which imports the anthropic module)
                client = self._get_client()

                # Use Anthropic's tokenizer API
                count_result = client.count_tokens(
                    model=self.model,
                    messages=anthropic_messages,
                    system=system_message
                )

                return IntegrationResult.success_result(count_result.input_tokens)

            except (ImportError, AttributeError):
                # Fall back to a simple estimation if anthropic package doesn't support token counting
                self.logger.warning(
                    "Anthropic token counting API not available. Using simple token estimation."
                )

                # Simple estimation based on words (very rough approximation)
                total_text = ""
                for message in messages:
                    if message.content:
                        total_text += message.content + " "

                # Rough approximation: 1 token ≈ 4 characters
                estimated_tokens = len(total_text) // 4

                return IntegrationResult.success_result(
                    estimated_tokens,
                    message="Token count is an estimation. Actual count may vary.",
                )

        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            return IntegrationResult.error_result(f"Error counting tokens: {e}")