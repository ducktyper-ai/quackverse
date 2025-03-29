# tests/test_integrations/llms/mocks/__init__.py
"""
Mock objects for LLM integration testing.

This module brings together all mock implementations from submodules,
making them available through a single import.
"""

# Import from base module
from tests.test_integrations.llms.mocks.base import (
    MockLLMResponse,
    MockTokenResponse,
    MockStreamingGenerator
)

# Import from clients module
from tests.test_integrations.llms.mocks.clients import (
    MockClient,
    create_mock_client
)

# Import from openai module
from tests.test_integrations.llms.mocks.openai import (
    MockOpenAIResponse,
    MockOpenAIStreamingResponse,
    MockOpenAIErrorResponse,
    MockOpenAIClient
)

# Import from anthropic module
from tests.test_integrations.llms.mocks.anthropic import (
    MockAnthropicResponse,
    MockAnthropicStreamingResponse,
    MockAnthropicErrorResponse,
    MockAnthropicClient
)

# Export all symbols
__all__ = [
    # Base mocks
    "MockLLMResponse",
    "MockTokenResponse",
    "MockStreamingGenerator",

    # Client mocks
    "MockClient",
    "create_mock_client",

    # OpenAI mocks
    "MockOpenAIResponse",
    "MockOpenAIStreamingResponse",
    "MockOpenAIErrorResponse",
    "MockOpenAIClient",

    # Anthropic mocks
    "MockAnthropicResponse",
    "MockAnthropicStreamingResponse",
    "MockAnthropicErrorResponse",
    "MockAnthropicClient",
]