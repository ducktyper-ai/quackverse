# tests/test_integrations/llms/test_protocols.py
"""
Tests for LLM protocols.

This module tests the runtime protocol implementations for LLMs, ensuring
all required methods are present and correctly implemented.
"""

from unittest.mock import MagicMock

from quackcore.integrations.llms.models import ChatMessage, LLMOptions
from quackcore.integrations.llms.protocols import LLMProviderProtocol
from tests.test_integrations.llms.mocks.clients import MockClient


class TestLLMProtocols:
    """Tests for LLM protocol implementations."""

    def test_llm_provider_protocol(self) -> None:
        """Test that LLMClient properly implements the LLMProviderProtocol."""
        # Create a mock client
        client = MockClient(model="test-model")

        # Check that it implements the protocol
        assert isinstance(client, LLMProviderProtocol)

        # Test the protocol methods
        messages = [ChatMessage.from_dict({"role": "user", "content": "Test message"})]
        options = LLMOptions(temperature=0.5)

        # Call chat method
        result = client.chat(messages, options)
        assert result.success is True

        # Call count_tokens method
        result = client.count_tokens(messages)
        assert result.success is True

        # Check model property
        assert client.model == "test-model"

    def test_incomplete_protocol_implementation(self) -> None:
        """Test that incomplete implementations don't satisfy the protocol."""
        # Create a mock that's missing methods
        incomplete_mock = MagicMock()
        # Only implement some methods from the protocol
        incomplete_mock.chat = MagicMock(return_value=MagicMock(success=True))
        # Missing count_tokens and model property

        # Should not be recognized as implementing the protocol
        assert not isinstance(incomplete_mock, LLMProviderProtocol)

        # Add count_tokens but not model property
        incomplete_mock.count_tokens = MagicMock(return_value=MagicMock(success=True))
        assert not isinstance(incomplete_mock, LLMProviderProtocol)

        # Add model as an attribute, not a property
        incomplete_mock.model = "test-model"
        assert not isinstance(incomplete_mock, LLMProviderProtocol)

        # Create a new mock with model as a property
        class ProperMock:
            def chat(self, *args, **kwargs):
                return MagicMock(success=True)

            def count_tokens(self, *args, **kwargs):
                return MagicMock(success=True)

            @property
            def model(self):
                return "test-model"

        proper_mock = ProperMock()
        # Now it should satisfy the protocol
        assert isinstance(proper_mock, LLMProviderProtocol)