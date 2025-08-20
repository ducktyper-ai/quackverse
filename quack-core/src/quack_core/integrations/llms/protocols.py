# quack-core/src/quack-core/integrations/llms/protocols.py
"""
Protocol definitions for LLM integration.

This module defines the interfaces that LLM clients should implement,
ensuring consistent behavior across different LLM providers.
"""

from collections.abc import Callable, Sequence
from typing import Protocol, TypeVar, runtime_checkable

from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.llms.models import ChatMessage, LLMOptions

T = TypeVar("T")  # Generic type for result content


@runtime_checkable
class LLMProviderProtocol(Protocol):
    """Protocol for LLM providers."""

    def chat(
        self,
        messages: Sequence[ChatMessage] | Sequence[dict],
        options: LLMOptions | None = None,
        callback: Callable[[str], None] | None = None,
    ) -> IntegrationResult[str]:
        """
        Send a chat completion request to the LLM.

        Args:
            messages: Sequence of messages for the conversation.
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
        ...

    @property
    def model(self) -> str:
        """Get the model name."""
        ...
