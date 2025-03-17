# tests/test_config/test_models.py
"""
Tests for configuration models.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from quackcore.config.models import (
    GeneralConfig,
    GoogleConfig,
    IntegrationsConfig,
    LoggingConfig,
    NotionConfig,
    PathsConfig,
    PluginsConfig,
    QuackConfig,
)


class TestConfigModels:
    """Tests for configuration model classes."""

    def test_logging_config(self) -> None:
        """Test the LoggingConfig model."""
        # Test default values
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.file is None
        assert config.console is True

        # Test with custom values
        config = LoggingConfig(level="DEBUG", file=Path("/test/log.txt"), console=False)
        assert config.level == "DEBUG"
        assert config.file == Path("/test/log.txt")
        assert config.console is False

        # Test invalid level (should normalize to INFO)
        config = LoggingConfig(level="INVALID")
        # Assert that the invalid level
        # was normalized to INFO
        assert config.level == "INFO"

        # Test setup_logging method
        with patch("logging.basicConfig") as mock_basic_config:
            with patch("logging.StreamHandler") as mock_stream_handler:
                with patch("logging.FileHandler") as mock_file_handler:
                    with patch("logging.getLogger") as mock_get_logger:
                        # Mock objects
                        mock_handler = MagicMock()
                        mock_stream_handler.return_value = mock_handler
                        mock_file_handler.return_value = mock_handler
                        mock_logger = MagicMock()
                        mock_get_logger.return_value = mock_logger

                        # Test with default config (console only)
                        config = LoggingConfig()
                        config.setup_logging()

                        # Verify basicConfig called
                        mock_basic_config.assert_called_once()
                        # Verify console handler added
                        mock_stream_handler.assert_called_once()
                        # Verify file handler not added
                        mock_file_handler.assert_not_called()

                        # Reset mocks
                        mock_basic_config.reset_mock()
                        mock_stream_handler.reset_mock()
                        mock_file_handler.reset_mock()

                        # Test with file config
                        with patch.object(Path, "mkdir", return_value=None):
                            config = LoggingConfig(file=Path("/test/log.txt"))
                            config.setup_logging()

                        # Verify file handler added
                        mock_file_handler.assert_called_once_with(
                            str(Path("/test/log.txt"))
                        )

                        # Test with error during file handler setup
                        mock_basic_config.reset_mock()
                        mock_stream_handler.reset_mock()
                        mock_file_handler.reset_mock()
                        mock_file_handler.side_effect = Exception("Test error")

                        config = LoggingConfig(file=Path("/test/log.txt"))
                        # Should not raise exception, but log the error
                        config.setup_logging()

                        # Verify error logged
                        mock_get_logger.return_value.error.assert_called_once()

    def test_paths_config(self) -> None:
        """Test the PathsConfig model."""
        # Test default values
        config = PathsConfig()
        assert config.base_dir == Path("./")
        assert config.output_dir == Path("./output")
        assert config.assets_dir == Path("./assets")
        assert config.data_dir == Path("./data")
        assert config.temp_dir == Path("./temp")

        # Test with custom values
        config = PathsConfig(
            base_dir=Path("/test/base"),
            output_dir=Path("/test/output"),
            assets_dir=Path("/test/assets"),
            data_dir=Path("/test/data"),
            temp_dir=Path("/test/temp"),
        )
        assert config.base_dir == Path("/test/base")
        assert config.output_dir == Path("/test/output")
        assert config.assets_dir == Path("/test/assets")
        assert config.data_dir == Path("/test/data")
        assert config.temp_dir == Path("/test/temp")

    def test_google_config(self) -> None:
        """Test the GoogleConfig model."""
        # Test default values
        config = GoogleConfig()
        assert config.client_secrets_file is None
        assert config.credentials_file is None
        assert config.shared_folder_id is None
        assert config.gmail_labels == []
        assert config.gmail_days_back == 1

        # Test with custom values
        config = GoogleConfig(
            client_secrets_file=Path("/test/secrets.json"),
            credentials_file=Path("/test/credentials.json"),
            shared_folder_id="test_folder_id",
            gmail_labels=["INBOX", "IMPORTANT"],
            gmail_days_back=7,
        )
        assert config.client_secrets_file == Path("/test/secrets.json")
        assert config.credentials_file == Path("/test/credentials.json")
        assert config.shared_folder_id == "test_folder_id"
        assert config.gmail_labels == ["INBOX", "IMPORTANT"]
        assert config.gmail_days_back == 7

    def test_notion_config(self) -> None:
        """Test the NotionConfig model."""
        # Test default values
        config = NotionConfig()
        assert config.api_key is None
        assert config.database_ids == {}

        # Test with custom values
        config = NotionConfig(
            api_key="test_api_key", database_ids={"projects": "db1", "tasks": "db2"}
        )
        assert config.api_key == "test_api_key"
        assert config.database_ids == {"projects": "db1", "tasks": "db2"}

    def test_integrations_config(self) -> None:
        """Test the IntegrationsConfig model."""
        # Test default values
        config = IntegrationsConfig()
        assert isinstance(config.google, GoogleConfig)
        assert isinstance(config.notion, NotionConfig)

        # Test with custom values
        config = IntegrationsConfig(
            google=GoogleConfig(client_secrets_file=Path("/test/secrets.json")),
            notion=NotionConfig(api_key="test_api_key"),
        )
        assert config.google.client_secrets_file == Path("/test/secrets.json")
        assert config.notion.api_key == "test_api_key"

    def test_general_config(self) -> None:
        """Test the GeneralConfig model."""
        # Test default values
        config = GeneralConfig()
        assert config.project_name == "QuackCore"
        assert config.environment == "development"
        assert config.debug is False
        assert config.verbose is False

        # Test with custom values
        config = GeneralConfig(
            project_name="TestProject",
            environment="production",
            debug=True,
            verbose=True,
        )
        assert config.project_name == "TestProject"
        assert config.environment == "production"
        assert config.debug is True
        assert config.verbose is True

    def test_plugins_config(self) -> None:
        """Test the PluginsConfig model."""
        # Test default values
        config = PluginsConfig()
        assert config.enabled == []
        assert config.disabled == []
        assert config.paths == []

        # Test with custom values
        config = PluginsConfig(
            enabled=["plugin1", "plugin2"],
            disabled=["plugin3"],
            paths=[Path("/test/plugins"), Path("/test/more_plugins")],
        )
        assert config.enabled == ["plugin1", "plugin2"]
        assert config.disabled == ["plugin3"]
        assert config.paths == [Path("/test/plugins"), Path("/test/more_plugins")]

    def test_quack_config(self) -> None:
        """Test the QuackConfig model."""
        # Test default values
        config = QuackConfig()
        assert isinstance(config.general, GeneralConfig)
        assert isinstance(config.paths, PathsConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.integrations, IntegrationsConfig)
        assert isinstance(config.plugins, PluginsConfig)
        assert config.custom == {}

        # Test with custom values
        config = QuackConfig(
            general=GeneralConfig(project_name="TestProject"),
            paths=PathsConfig(base_dir=Path("/test/base")),
            logging=LoggingConfig(level="DEBUG"),
            plugins=PluginsConfig(enabled=["plugin1"]),
            custom={"key": "value"},
        )
        assert config.general.project_name == "TestProject"
        assert config.paths.base_dir == Path("/test/base")
        assert config.logging.level == "DEBUG"
        assert config.plugins.enabled == ["plugin1"]
        assert config.custom == {"key": "value"}

        # Test setup_logging method
        with patch.object(LoggingConfig, "setup_logging") as mock_setup:
            config.setup_logging()
            mock_setup.assert_called_once()

        # Test to_dict method
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert "general" in config_dict
        assert "paths" in config_dict
        assert "logging" in config_dict
        assert "integrations" in config_dict
        assert "plugins" in config_dict
        assert "custom" in config_dict

        # Test get_plugin_enabled method
        assert config.get_plugin_enabled("plugin1") is True  # In enabled list
        assert config.get_plugin_enabled("plugin2") is False  # Not in enabled list

        # Test with disabled plugin
        config.plugins.disabled = ["plugin3", "plugin1"]
        assert (
            config.get_plugin_enabled("plugin1") is False
        )  # In disabled list, even if in enabled

        # Test get_custom method
        assert config.get_custom("key") == "value"
        assert config.get_custom("nonexistent") is None
        assert config.get_custom("nonexistent", "default") == "default"
