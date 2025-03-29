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

        # Create a class that's missing methods
        class IncompleteMock:
            def chat(self, *args, **kwargs):
                return MagicMock(success=True)

        incomplete = IncompleteMock()
        # Should not be recognized as implementing the protocol
        assert not isinstance(incomplete, LLMProviderProtocol)

        # Add count_tokens but not model property
        class PartialMock:
            def chat(self, *args, **kwargs):
                return MagicMock(success=True)

            def count_tokens(self, *args, **kwargs):
                return MagicMock(success=True)

        partial = PartialMock()
        assert not isinstance(partial, LLMProviderProtocol)

        # Add model as an attribute, not a property
        class MockWithAttribute:
            def chat(self, *args, **kwargs):
                return MagicMock(success=True)

            def count_tokens(self, *args, **kwargs):
                return MagicMock(success=True)

            model = "test-model"

        attribute_mock = MockWithAttribute()
        assert not isinstance(attribute_mock, LLMProviderProtocol)