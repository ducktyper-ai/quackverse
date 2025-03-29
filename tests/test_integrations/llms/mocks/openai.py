# tests/test_integrations/llms/mocks/openai.py
"""
Mock OpenAI classes for LLM testing.
"""

from typing import Any, Dict, Iterator, List, Optional, Union
from unittest.mock import MagicMock

from tests.test_integrations.llms.mocks.base import MockLLMResponse, \
    MockStreamingGenerator
from tests.test_integrations.llms.mocks.clients import MockClient


class MockOpenAIResponse(MockLLMResponse):
    """A mock response mimicking the OpenAI API format."""

    def __init__(
            self,
            content: str = "This is a mock OpenAI response",
            model: str = "gpt-4o",
            usage: Optional[Dict[str, int]] = None,
            finish_reason: str = "stop",
            error: Optional[Exception] = None,
            object_type: str = "chat.completion",
            id: str = "chatcmpl-123",
            created: int = 1677858242,
    ):
        """
        Initialize a mock OpenAI response.

        Args:
            content: The text content of the response
            model: The model name that generated the response
            usage: Token usage statistics
            finish_reason: Reason the generation finished
            error: Optional error to raise instead of returning a response
            object_type: Type of OpenAI object
            id: The ID of the completion
            created: Unix timestamp for when the completion was created
        """
        super().__init__(
            content=content,
            model=model,
            usage=usage,
            finish_reason=finish_reason,
            error=error,
        )

        self.id = id
        self.object = object_type
        self.created = created

    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI API format."""
        if self.error:
            raise self.error

        return {
            "id": self.id,
            "object": self.object,
            "created": self.created,
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": self.content,
                    },
                    "finish_reason": self.finish_reason,
                }
            ],
            "usage": self.usage,
        }


class MockOpenAIStreamingResponse(MockStreamingGenerator):
    """A generator that yields chunks in OpenAI streaming format."""

    def __iter__(self) -> Iterator[Any]:
        """Return self as iterator."""
        return self

    def __next__(self) -> Dict[str, Any]:
        """
        Get the next chunk in OpenAI streaming format.

        Returns:
            Dict: A chunk of the response in OpenAI format

        Raises:
            StopIteration: When all chunks have been yielded
            Exception: If error is set and error_after chunks have been yielded
        """
        try:
            chunk_text = next(self.generate_chunks())

            # Create a mock chunk in OpenAI format
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta = MagicMock()
            mock_chunk.choices[0].delta.content = chunk_text
            mock_chunk.choices[0].delta.role = "assistant"
            mock_chunk.choices[0].finish_reason = None
            mock_chunk.model = self.model

            return mock_chunk
        except StopIteration:
            # For the last chunk, set finish_reason
            mock_chunk = MagicMock()
            mock_chunk.choices = [MagicMock()]
            mock_chunk.choices[0].delta = MagicMock()
            mock_chunk.choices[0].delta.content = None
            mock_chunk.choices[0].finish_reason = "stop"
            mock_chunk.model = self.model

            # This will end the iteration next time
            self.content = ""
            return mock_chunk


class MockOpenAIErrorResponse:
    """A mock error response mimicking OpenAI API errors."""

    def __init__(
            self,
            message: str = "OpenAI API error",
            code: str = "rate_limit_exceeded",
            type: str = "server_error",
            param: Optional[str] = None,
            status_code: int = 429,
    ):
        """
        Initialize a mock OpenAI error response.

        Args:
            message: Error message
            code: Error code
            type: Error type
            param: Parameter that caused the error
            status_code: HTTP status code
        """
        self.message = message
        self.code = code
        self.type = type
        self.param = param
        self.status_code = status_code

    def to_exception(self) -> Exception:
        """
        Convert to an exception that mimics OpenAI's error format.

        Returns:
            Exception: An exception with OpenAI error attributes
        """
        # Create a mock response with status_code
        response = MagicMock()
        response.status_code = self.status_code

        # Create an error object similar to what OpenAI would return
        error = {
            "message": self.message,
            "type": self.type,
            "code": self.code,
        }
        if self.param:
            error["param"] = self.param

        # Create an exception with OpenAI-like attributes
        exception = Exception(f"OpenAI API error: {self.message}")
        exception.response = response
        exception.error = error

        return exception


class MockOpenAIClient(MockClient):
    """A mock OpenAI client."""

    def __init__(
            self,
            responses: List[str] = None,
            token_counts: List[int] = None,
            model: str = "gpt-4o",
            errors: List[Exception] = None,
            **kwargs: Any
    ):
        """
        Initialize a mock OpenAI client.

        Args:
            responses: List of responses to return
            token_counts: List of token counts to return
            model: Model name
            errors: List of errors to raise
            **kwargs: Additional keyword arguments
        """
        super().__init__(
            responses=responses,
            token_counts=token_counts,
            model=model,
            errors=errors,
            **kwargs
        )

        # Track OpenAI-specific data
        self.openai_requests = []

    def chat_completions_create(self, *args, **kwargs):
        """
        Mock OpenAI's chat.completions.create method.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Union[MockOpenAIResponse, MockOpenAIStreamingResponse]: Response object

        Raises:
            Exception: If configured to raise an error
        """
        self.openai_requests.append(kwargs)

        # Get the response for this call
        response_idx = min(len(self.openai_requests) - 1, len(self.responses) - 1)
        response_text = self.responses[response_idx]

        # Check if we should raise an error
        if self.errors and len(self.openai_requests) <= len(self.errors):
            error = self.errors[len(self.openai_requests) - 1]
            if error:
                raise error

        # Handle streaming
        if kwargs.get("stream", False):
            return MockOpenAIStreamingResponse(content=response_text, model=self.model)

        # Return a normal response
        return MockOpenAIResponse(content=response_text, model=self.model)