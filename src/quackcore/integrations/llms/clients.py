# src/quackcore/integrations/llms/clients.py
"""
LLM client implementations.

This module provides implementations of LLM clients for various providers,
including a base class with common functionality and provider-specific clients.
"""

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from typing import Any

from quackcore import QuackIntegrationError
from quackcore.errors import QuackApiError
from quackcore.integrations.llms.models import ChatMessage, LLMOptions
from quackcore.integrations.llms.protocols import LLMProviderProtocol
from quackcore.integrations.core.results import IntegrationResult


class LLMClient(ABC, LLMProviderProtocol):
    """Base class for LLM clients."""

    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
        timeout: int = 60,
        retry_count: int = 3,
        initial_retry_delay: float = 1.0,
        max_retry_delay: float = 30.0,
        log_level: int = logging.INFO,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the LLM client.

        Args:
            model: Model name to use
            api_key: API key for authentication
            timeout: Request timeout in seconds
            retry_count: Number of retries for failed requests
            initial_retry_delay: Initial delay for exponential backoff
            max_retry_delay: Maximum delay between retries
            log_level: Logging level
            **kwargs: Additional provider-specific arguments
        """
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.setLevel(log_level)

        self._model = model
        self._api_key = api_key
        self._timeout = timeout
        self._retry_count = retry_count
        self._initial_retry_delay = initial_retry_delay
        self._max_retry_delay = max_retry_delay
        self._kwargs = kwargs

    @property
    def model(self) -> str:
        """Get the model name."""
        if not self._model:
            raise ValueError("Model name not specified")
        return self._model

    def chat(
        self,
        messages: Sequence[ChatMessage] | Sequence[dict],
        options: LLMOptions | None = None,
        callback: Callable[[str], None] | None = None,
    ) -> IntegrationResult[str]:
        """
        Send a chat completion request to the LLM.

        This method normalizes the messages, calls the provider-specific
        implementation, and applies retry logic for failed requests.

        Args:
            messages: Sequence of messages for the conversation.
            options: Additional options for the completion request.
            callback: Optional callback function for streaming responses.

        Returns:
            IntegrationResult[str]: Result of the chat completion request.
        """
        try:
            # Normalize messages
            normalized_messages = self._normalize_messages(messages)

            # Use default options if not provided
            request_options = options or LLMOptions()
            if request_options.model is None:
                # Override with instance model if not specified in options
                try:
                    request_options.model = self.model
                except ValueError:
                    pass  # If model is not specified, let the concrete implementation handle it

            # Apply retry logic
            retry_count = 0
            delay = self._initial_retry_delay

            while True:
                try:
                    return self._chat_with_provider(
                        normalized_messages, request_options, callback
                    )
                except QuackApiError as e:
                    retry_count += 1
                    if retry_count > self._retry_count:
                        raise

                    # Log retry information
                    self.logger.warning(
                        f"Retrying chat request ({retry_count}/{self._retry_count}) after error: {e}"
                    )

                    # Sleep with exponential backoff
                    time.sleep(delay)
                    delay = min(delay * 2, self._max_retry_delay)

        except QuackApiError as e:
            self.logger.error(f"API error during chat request: {e}")
            return IntegrationResult.error_result(f"API error: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error during chat request: {e}")
            return IntegrationResult.error_result(f"Unexpected error: {e}")

    @abstractmethod
    def _chat_with_provider(
        self,
        messages: list[ChatMessage],
        options: LLMOptions,
        callback: Callable[[str], None] | None = None,
    ) -> IntegrationResult[str]:
        """
        Provider-specific implementation of chat completion request.

        Args:
            messages: Normalized list of messages for the conversation.
            options: Additional options for the completion request.
            callback: Optional callback function for streaming responses.

        Returns:
            IntegrationResult[str]: Result of the chat completion request.
        """
        ...

    def count_tokens(
        self, messages: Sequence[ChatMessage] | Sequence[dict]
    ) -> IntegrationResult[int]:
        """
        Count the number of tokens in the messages.

        Args:
            messages: Sequence of messages to count tokens for.

        Returns:
            IntegrationResult[int]: Result containing the token count.
        """
        try:
            # Normalize messages
            normalized_messages = self._normalize_messages(messages)

            # Call provider-specific implementation
            return self._count_tokens_with_provider(normalized_messages)
        except Exception as e:
            self.logger.error(f"Error counting tokens: {e}")
            return IntegrationResult.error_result(f"Error counting tokens: {e}")

    @abstractmethod
    def _count_tokens_with_provider(self, messages: list[ChatMessage]) -> IntegrationResult[int]:
        """
        Provider-specific implementation of token counting.

        Args:
            messages: Normalized list of messages to count tokens for.

        Returns:
            IntegrationResult[int]: Result containing the token count.
        """
        ...

    def _normalize_messages(
        self, messages: Sequence[ChatMessage] | Sequence[dict]
    ) -> list[ChatMessage]:
        """
        Normalize messages to a list of ChatMessage objects.

        Args:
            messages: Messages to normalize.

        Returns:
            list[ChatMessage]: Normalized list of messages.
        """
        normalized_messages: list[ChatMessage] = []

        for message in messages:
            if isinstance(message, dict):
                normalized_messages.append(ChatMessage.from_dict(message))
            elif isinstance(message, ChatMessage):
                normalized_messages.append(message)
            else:
                raise ValueError(f"Unsupported message type: {type(message)}")

        return normalized_messages

class OpenAIClient(LLMClient):
    """OpenAI LLM client implementation."""

    def __init__(
            self,
            model: str | None = None,
            api_key: str | None = None,
            api_base: str | None = None,
            organization: str | None = None,
            timeout: int = 60,
            retry_count: int = 3,
            initial_retry_delay: float = 1.0,
            max_retry_delay: float = 30.0,
            log_level: int = logging.INFO,
            **kwargs: Any,
    ) -> None:
        """
        Initialize the OpenAI client.

        Args:
            model: Model name to use
            api_key: OpenAI API key
            api_base: OpenAI API base URL
            organization: OpenAI organization ID
            timeout: Request timeout in seconds
            retry_count: Number of retries for failed requests
            initial_retry_delay: Initial delay for exponential backoff
            max_retry_delay: Maximum delay between retries
            log_level: Logging level
            **kwargs: Additional OpenAI-specific arguments
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
        self._organization = organization
        self._client = None

    def _get_client(self) -> Any:
        """
        Get the OpenAI client instance.

        Returns:
            Any: OpenAI client.

        Raises:
            QuackIntegrationError: If OpenAI package is not installed.
        """
        if self._client is None:
            try:
                from openai import OpenAI

                # Get API key from environment variable if not provided
                api_key = self._api_key or self._get_api_key_from_env()

                kwargs = {
                    "api_key": api_key,
                    "timeout": self._timeout,
                }

                if self._api_base:
                    kwargs["base_url"] = self._api_base
                if self._organization:
                    kwargs["organization"] = self._organization

                self._client = OpenAI(**kwargs)
            except ImportError:
                raise QuackIntegrationError(
                    "OpenAI package not installed. "
                    "Please install it with: pip install openai"
                )

        return self._client

    def _get_api_key_from_env(self) -> str:
        """
        Get the OpenAI API key from environment variables.

        Returns:
            str: OpenAI API key.

        Raises:
            QuackIntegrationError: If API key is not provided or available in environment.
        """
        import os

        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise QuackIntegrationError(
                "OpenAI API key not provided. "
                "Please provide it as an argument or set the OPENAI_API_KEY environment variable."
            )
        return api_key

    @property
    def model(self) -> str:
        """
        Get the model name.

        Returns:
            str: Model name.

        Raises:
            ValueError: If model name is not specified.
        """
        if not self._model:
            # Check for default model in configuration
            self._model = "gpt-4o"  # Default model if not specified
        return self._model

    def _chat_with_provider(
            self,
            messages: list[ChatMessage],
            options: LLMOptions,
            callback: Callable[[str], None] | None = None,
    ) -> IntegrationResult[str]:
        """
        Send a chat completion request to the OpenAI API.

        Args:
            messages: List of messages for the conversation.
            options: Additional options for the completion request.
            callback: Optional callback function for streaming responses.

        Returns:
            IntegrationResult[str]: Result of the chat completion request.
        """
        try:
            client = self._get_client()

            # Convert messages to the format expected by OpenAI
            openai_messages = [self._convert_message_to_openai(msg) for msg in messages]

            # Get OpenAI parameters from options
            params = options.to_openai_params()

            # Override model if specified in options
            model = options.model or self.model

            # Handle streaming if callback is provided
            if callback and not options.stream:
                options.stream = True
                params["stream"] = True

            if options.stream:
                response_text = self._handle_streaming(
                    client, model, openai_messages, params, callback
                )
                return IntegrationResult.success_result(response_text)
            else:
                # Make the API call
                response = client.chat.completions.create(
                    model=model,
                    messages=openai_messages,
                    **params
                )

                # Process the response
                result = self._process_response(response)
                return IntegrationResult.success_result(result)

        except ImportError as e:
            raise QuackIntegrationError(
                f"Failed to import OpenAI package: {e}",
                original_error=e,
            ) from e
        except Exception as e:
            # Convert OpenAI errors to QuackApiError
            raise self._convert_error(e)

    def _handle_streaming(
            self,
            client: Any,
            model: str,
            messages: list[dict],
            params: dict,
            callback: Callable[[str], None] | None,
    ) -> str:
        """
        Handle streaming responses from the OpenAI API.

        Args:
            client: OpenAI client instance.
            model: Model name.
            messages: List of messages in OpenAI format.
            params: OpenAI API parameters.
            callback: Callback function for streaming responses.

        Returns:
            str: Complete response text.
        """
        collected_content = []

        try:
            stream = client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True,
                **params
            )

            for chunk in stream:
                if not chunk.choices:
                    continue

                delta = chunk.choices[0].delta

                if delta.content:
                    collected_content.append(delta.content)
                    if callback:
                        callback(delta.content)

            return "".join(collected_content)
        except Exception as e:
            # Convert OpenAI errors to QuackApiError
            raise self._convert_error(e)

    def _convert_message_to_openai(self, message: ChatMessage) -> dict:
        """
        Convert a ChatMessage to the format expected by OpenAI.

        Args:
            message: ChatMessage to convert.

        Returns:
            dict: Message in OpenAI format.
        """
        openai_message = {"role": message.role.value}

        if message.content is not None:
            openai_message["content"] = message.content

        if message.name:
            openai_message["name"] = message.name

        if message.function_call:
            openai_message["function_call"] = message.function_call

        if message.tool_calls:
            openai_message["tool_calls"] = message.tool_calls

        return openai_message

    def _process_response(self, response: Any) -> str:
        """
        Process a response from the OpenAI API.

        Args:
            response: Response from OpenAI API.

        Returns:
            str: Response content.
        """
        if not response.choices:
            return ""

        choice = response.choices[0]

        if not hasattr(choice, "message"):
            return ""

        message = choice.message

        if not hasattr(message, "content") or message.content is None:
            return ""

        return message.content

    def _convert_error(self, error: Exception) -> QuackApiError:
        """
        Convert OpenAI errors to QuackApiError.

        Args:
            error: Original error.

        Returns:
            QuackApiError: Converted error.
        """
        error_str = str(error)

        # Check for specific error types
        if "rate limit" in error_str.lower():
            return QuackApiError(
                f"OpenAI rate limit exceeded: {error}",
                service="OpenAI",
                api_method="chat.completions.create",
                original_error=error,
                retry_after=60,  # Suggest a retry after 60 seconds
            )
        elif "invalid api key" in error_str.lower():
            return QuackApiError(
                f"Invalid OpenAI API key: {error}",
                service="OpenAI",
                api_method="chat.completions.create",
                original_error=error,
            )
        elif "insufficient quota" in error_str.lower():
            return QuackApiError(
                f"Insufficient OpenAI quota: {error}",
                service="OpenAI",
                api_method="chat.completions.create",
                original_error=error,
            )
        else:
            return QuackApiError(
                f"OpenAI API error: {error}",
                service="OpenAI",
                api_method="chat.completions.create",
                original_error=error,
            )

    def _count_tokens_with_provider(self, messages: list[ChatMessage]) -> \
        IntegrationResult[int]:
            """
            Count the number of tokens in the messages using OpenAI's tokenizer.

            Args:
                messages: List of messages to count tokens for.

            Returns:
                IntegrationResult[int]: Result containing the token count.
            """
            try:
                # Try to use tiktoken for more accurate counts
                try:
                    import tiktoken

                    # Get the appropriate encoding for the model
                    model = self.model

                    # Default to cl100k_base encoding for newer models
                    encoding_name = "cl100k_base"

                    # Try to get model-specific encoding
                    try:
                        encoding = tiktoken.encoding_for_model(model)
                    except KeyError:
                        # Fall back to cl100k_base if model-specific encoding is not available
                        encoding = tiktoken.get_encoding(encoding_name)

                    # Count tokens for each message
                    token_count = 0

                    # Convert messages to OpenAI format for counting
                    openai_messages = [self._convert_message_to_openai(msg) for msg in
                                       messages]

                    # OpenAI's token counting logic
                    tokens_per_message = 3  # Every message follows <|start|>{role/name}\n{content}<|end|>
                    tokens_per_name = 1  # If there's a name, the role is omitted

                    for message in openai_messages:
                        token_count += tokens_per_message

                        for key, value in message.items():
                            if isinstance(value, str):
                                token_count += len(encoding.encode(value))
                            elif isinstance(value, dict):
                                # For function_call or similar nested structures
                                json_str = str(value)
                                token_count += len(encoding.encode(json_str))

                        if message.get("name"):
                            token_count += tokens_per_name

                    # Add 3 tokens for the assistant's reply
                    token_count += 3

                    return IntegrationResult.success_result(token_count)

                except ImportError:
                    import tiktoken
                    # Fall back to a simple estimation if tiktoken is not available
                    self.logger.warning(
                        "tiktoken not installed. Using simple token estimation. "
                        "Install tiktoken for more accurate counts: pip install tiktoken"
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
                        message="Token count is an estimation. Install tiktoken for accuracy.",
                    )

            except Exception as e:
                self.logger.error(f"Error counting tokens: {e}")
                return IntegrationResult.error_result(f"Error counting tokens: {e}")


# src/quackcore/integrations/llms/clients.py (continued)

class MockLLMClient(LLMClient):
    """Mock LLM client for testing and educational purposes."""

    def __init__(
            self,
            script: list[str] | None = None,
            model: str = "mock-model",
            log_level: int = logging.INFO,
            **kwargs: Any,
    ) -> None:
        """
        Initialize the mock LLM client.

        Args:
            script: List of responses to return in sequence
            model: Mock model name
            log_level: Logging level
            **kwargs: Additional arguments
        """
        super().__init__(model=model, log_level=log_level, **kwargs)
        self._script = script or ["This is a mock response from the LLM."]
        self._current_index = 0

    def _chat_with_provider(
            self,
            messages: list[ChatMessage],
            options: LLMOptions,
            callback: Callable[[str], None] | None = None,
    ) -> IntegrationResult[str]:
        """
        Return a mock response from the script.

        Args:
            messages: List of messages for the conversation.
            options: Additional options for the completion request.
            callback: Optional callback function for streaming responses.

        Returns:
            IntegrationResult[str]: Result of the chat completion request.
        """
        # Get the next response from the script
        if not self._script:
            return IntegrationResult.error_result("No mock responses available")

        response = self._script[self._current_index % len(self._script)]
        self._current_index += 1

        # Handle streaming if callback is provided
        if callback and options.stream:
            self._mock_streaming(response, callback)

        return IntegrationResult.success_result(response)

    def _mock_streaming(self, response: str, callback: Callable[[str], None]) -> None:
        """
        Simulate streaming by sending chunks of the response to the callback.

        Args:
            response: Full response text.
            callback: Callback function for streaming responses.
        """
        # Split the response into chunks (words for simplicity)
        chunks = response.split(" ")

        for chunk in chunks:
            # Add the space back except for the last chunk
            chunk_with_space = chunk + " "
            callback(chunk_with_space)
            time.sleep(0.1)  # Simulate delay between chunks

    def _count_tokens_with_provider(self, messages: list[ChatMessage]) -> \
    IntegrationResult[int]:
        """
        Provide a mock token count.

        Args:
            messages: List of messages to count tokens for.

        Returns:
            IntegrationResult[int]: Result containing the token count.
        """
        # Simple mock implementation: count characters and divide by 4
        total_chars = 0
        for message in messages:
            if message.content:
                total_chars += len(message.content)

        # Rough approximation: 1 token ≈ 4 characters
        mock_token_count = total_chars // 4

        return IntegrationResult.success_result(mock_token_count)

    def set_responses(self, responses: list[str]) -> None:
        """
        Set the list of responses to return.

        Args:
            responses: List of responses to return in sequence.
        """
        self._script = responses
        self._current_index = 0