# tests/test_integrations/llms/test_registry.py
"""
Tests for the LLM client registry.

This module tests the registry functionality that allows dynamic loading
and management of LLM client implementations.
"""

from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.llms.clients.base import LLMClient
from quackcore.integrations.llms.clients.mock import MockLLMClient
from quackcore.integrations.llms.registry import (
    _LLM_REGISTRY,
    get_llm_client,
    register_llm_client,
)


class TestLLMRegistry:
    """Tests for the LLM client registry."""

    def test_registry_initial_state(self) -> None:
        """Test that the registry has the expected initial state."""
        # The registry should have these providers by default
        expected_providers = {"openai", "anthropic", "mock"}
        assert set(_LLM_REGISTRY.keys()) >= expected_providers

    def test_register_llm_client(self) -> None:
        """Test registering a new LLM client."""

        # Create a test client class
        class TestClient(LLMClient):
            def _chat_with_provider(self, *args, **kwargs):
                return MagicMock()

            def _count_tokens_with_provider(self, *args, **kwargs):
                return MagicMock()

        # Register the test client
        register_llm_client("test", TestClient)

        # Check that it was added to the registry
        assert "test" in _LLM_REGISTRY
        assert _LLM_REGISTRY["test"] == TestClient

        # Clean up
        del _LLM_REGISTRY["test"]

    def test_register_llm_client_lowercase(self) -> None:
        """Test that client names are converted to lowercase in the registry."""

        # Create a test client class
        class TestClient(LLMClient):
            def _chat_with_provider(self, *args, **kwargs):
                return MagicMock()

            def _count_tokens_with_provider(self, *args, **kwargs):
                return MagicMock()

        # Register the test client with mixed case
        register_llm_client("TestClient", TestClient)

        # Check that it was added to the registry with lowercase name
        assert "testclient" in _LLM_REGISTRY
        assert _LLM_REGISTRY["testclient"] == TestClient

        # Clean up
        del _LLM_REGISTRY["testclient"]

    # tests/test_integrations/llms/test_registry.py

    def test_get_llm_client_openai(self) -> None:
        """Test getting the OpenAI client."""
        with patch(
                "quackcore.integrations.llms.registry.OpenAIClient"
        ) as mock_openai:
            mock_instance = MagicMock()
            mock_openai.return_value = mock_instance

            client = get_llm_client("openai", model="gpt-4o", api_key="test-key")

            assert client == mock_instance
            mock_openai.assert_called_once_with(
                model="gpt-4o", api_key="test-key"
            )

    def test_get_llm_client_anthropic(self) -> None:
        """Test getting the Anthropic client."""
        with patch(
            "quackcore.integrations.llms.clients.anthropic.AnthropicClient"
        ) as mock_anthropic:
            mock_instance = MagicMock()
            mock_anthropic.return_value = mock_instance

            client = get_llm_client(
                "anthropic", model="claude-3-opus", api_key="test-key"
            )

            assert client == mock_instance
            mock_anthropic.assert_called_once_with(
                model="claude-3-opus", api_key="test-key"
            )

    def test_get_llm_client_mock(self) -> None:
        """Test getting the Mock client."""
        client = get_llm_client("mock", script=["Test response"])

        assert isinstance(client, MockLLMClient)
        assert client._script == ["Test response"]

    def test_get_llm_client_case_insensitive(self) -> None:
        """Test that provider names are case-insensitive."""
        with patch(
            "quackcore.integrations.llms.clients.openai.OpenAIClient"
        ) as mock_openai:
            mock_instance = MagicMock()
            mock_openai.return_value = mock_instance

            # Try with mixed case
            client = get_llm_client("OpenAI", model="gpt-4o", api_key="test-key")

            assert client == mock_instance
            mock_openai.assert_called_once()

    def test_get_llm_client_unknown(self) -> None:
        """Test getting an unknown client."""
        with pytest.raises(QuackIntegrationError) as excinfo:
            get_llm_client("unknown")

        assert "Unsupported LLM provider: unknown" in str(excinfo.value)
        assert "Registered providers" in str(excinfo.value)

    def test_get_llm_client_initialization_error(self) -> None:
        """Test handling client initialization errors."""
        with patch(
            "quackcore.integrations.llms.clients.openai.OpenAIClient"
        ) as mock_openai:
            mock_openai.side_effect = Exception("Initialization error")

            with pytest.raises(QuackIntegrationError) as excinfo:
                get_llm_client("openai")

            assert "Failed to initialize openai client" in str(excinfo.value)
            assert "Initialization error" in str(excinfo.value)
