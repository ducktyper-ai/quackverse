# tests/test_integrations/llms/test_service.py
"""
Tests for the LLM integration service.

This module tests the main service class for LLM integration, including
initialization, configuration, and client communication.
"""

from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.core import BaseIntegrationService
from quackcore.integrations.core.results import IntegrationResult
from quackcore.integrations.llms.models import ChatMessage, LLMOptions, RoleType
from quackcore.integrations.llms.service import LLMIntegration
from tests.test_integrations.llms.mocks.clients import MockClient


class TestLLMService:
    """Tests for the LLM integration service."""

    @pytest.fixture
    def llm_service(self) -> LLMIntegration:
        """Create an LLM integration service with mock configuration."""
        with patch("quackcore.config.loader.load_config") as mock_load:
            # Provide a default config that should work
            mock_load.return_value.success = True
            mock_load.return_value.content = {
                "llm": {
                    "default_provider": "openai",
                    "timeout": 60,
                    "openai": {
                        "api_key": "test-key",
                    },
                },
            }

            # Mock the path resolution to return the original path
            with patch.object(BaseIntegrationService, "_resolve_path") as mock_resolve:
                mock_resolve.side_effect = lambda x: x
                return LLMIntegration()

    def test_init(self) -> None:
        """Test initializing the LLM integration service."""
        # Test with default parameters
        with patch.object(BaseIntegrationService, "_resolve_path") as mock_resolve:
            mock_resolve.side_effect = lambda x: x
            service = LLMIntegration()
            assert service.provider is None
            assert service.model is None
            assert service.api_key is None
            assert service.client is None
            assert service._initialized is False

            # Test with custom parameters
            service = LLMIntegration(
                provider="anthropic",
                model="claude-3-opus",
                api_key="test-key",
                config_path="config.yaml",
                log_level=20,
            )
            assert service.provider == "anthropic"
            assert service.model == "claude-3-opus"
            assert service.api_key == "test-key"
            assert service.config_path == "config.yaml"
            assert service.logger.level == 20

    def test_name_and_version(self, llm_service: LLMIntegration) -> None:
        """Test the name and version properties."""
        assert llm_service.name == "LLM"
        assert llm_service.version == "1.0.0"  # This should match what's in the code

    def test_initialize(self, llm_service: LLMIntegration) -> None:
        """Test initializing the LLM integration."""
        # Test successful initialization
        with patch(
            "quackcore.integrations.llms.registry.get_llm_client"
        ) as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client

            result = llm_service.initialize()

            assert result.success is True
            assert llm_service._initialized is True
            assert llm_service.client == mock_client

            # Should call get_llm_client with config values
            mock_get_client.assert_called_once()
            assert mock_get_client.call_args[1]["provider"] == "openai"
            assert mock_get_client.call_args[1]["api_key"] == "test-key"

        # Test base initialization failure
        with patch(
            "quackcore.integrations.core.base.BaseIntegrationService.initialize"
        ) as mock_init:
            mock_init.return_value = IntegrationResult(
                success=False,
                error="Base initialization failed",
            )

            result = llm_service.initialize()

            assert result.success is False
            assert "Base initialization failed" in result.error
            assert llm_service._initialized is False

        # Test config extraction failure
        with patch.object(llm_service, "_extract_config") as mock_extract:
            mock_extract.side_effect = QuackIntegrationError("Config extraction failed")

            result = llm_service.initialize()

            assert result.success is False
            assert "Config extraction failed" in result.error
            assert llm_service._initialized is False

        # Test client initialization failure
        with patch(
            "quackcore.integrations.llms.registry.get_llm_client"
        ) as mock_get_client:
            mock_get_client.side_effect = QuackIntegrationError(
                "Client initialization failed"
            )

            result = llm_service.initialize()

            assert result.success is False
            assert "Client initialization failed" in result.error
            assert llm_service._initialized is False

    def test_extract_config(self, llm_service: LLMIntegration) -> None:
        """Test extracting and validating the LLM configuration."""
        # Set up a config for testing
        llm_service.config = {
            "default_provider": "openai",
            "timeout": 60,
            "openai": {
                "api_key": "test-key",
            },
        }

        # Test successful extraction
        config = llm_service._extract_config()
        assert config == llm_service.config

        # Test with missing config
        llm_service.config = None

        with patch(
            "quackcore.integrations.llms.config.LLMConfigProvider.load_config"
        ) as mock_load:
            # Simulate successful config loading
            mock_load.return_value.success = True
            mock_load.return_value.content = {
                "default_provider": "anthropic",
                "timeout": 30,
            }

            config = llm_service._extract_config()
            assert config["default_provider"] == "anthropic"
            assert config["timeout"] == 30

        # Test with config loading failure
        with patch(
            "quackcore.integrations.llms.config.LLMConfigProvider.load_config"
        ) as mock_load:
            mock_load.return_value.success = False

            with patch(
                "quackcore.integrations.llms.config.LLMConfigProvider.get_default_config"
            ) as mock_default:
                mock_default.return_value = {
                    "default_provider": "mock",
                    "timeout": 10,
                }

                config = llm_service._extract_config()
                assert config["default_provider"] == "mock"
                assert config["timeout"] == 10

        # Test validation failure
        with patch("quackcore.integrations.llms.config.LLMConfig") as mock_config:
            mock_config.side_effect = Exception("Validation error")

            with pytest.raises(QuackIntegrationError) as excinfo:
                llm_service._extract_config()

            assert "Invalid LLM configuration" in str(excinfo.value)

    def test_chat(self, llm_service: LLMIntegration) -> None:
        """Test the chat method."""
        # Set up mock client
        mock_client = MockClient(responses=["Test response"])
        llm_service.client = mock_client
        llm_service._initialized = True

        # Test successful chat
        messages = [
            ChatMessage(role=RoleType.USER, content="Test message"),
        ]
        options = LLMOptions(temperature=0.5)

        result = llm_service.chat(messages, options)

        assert result.success is True
        assert result.content == "Test response"

        # Mock client should have been called with our parameters
        assert mock_client.last_messages == messages
        assert mock_client.last_options == options

        # Test with callback
        callback = MagicMock()
        result = llm_service.chat(messages, options, callback)

        assert result.success is True
        assert mock_client.last_callback == callback

        # Test not initialized
        llm_service._initialized = False
        result = llm_service.chat(messages)

        assert result.success is False
        assert "LLM integration not initialized" in result.error

    def test_count_tokens(self, llm_service: LLMIntegration) -> None:
        """Test the count_tokens method."""
        # Set up mock client
        mock_client = MockClient(token_counts=[42])
        llm_service.client = mock_client
        llm_service._initialized = True

        # Test successful token counting
        messages = [
            ChatMessage(role=RoleType.USER, content="Test message"),
        ]

        result = llm_service.count_tokens(messages)

        assert result.success is True
        assert result.content == 42

        # Test not initialized
        llm_service._initialized = False
        result = llm_service.count_tokens(messages)

        assert result.success is False
        assert "LLM integration not initialized" in result.error

    def test_get_client(self, llm_service: LLMIntegration) -> None:
        """Test the get_client method."""
        # Set up mock client
        mock_client = MockClient()
        llm_service.client = mock_client
        llm_service._initialized = True

        # Test successful client retrieval
        client = llm_service.get_client()
        assert client == mock_client

        # Test not initialized
        llm_service._initialized = False
        with pytest.raises(QuackIntegrationError) as excinfo:
            llm_service.get_client()

        assert "LLM client not initialized" in str(excinfo.value)
