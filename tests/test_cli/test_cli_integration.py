# tests/test_cli/test_cli_integration.py
"""
Integration tests for CLI functionality.
"""

import logging
import os
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
import yaml

from quackcore.cli.boostrap import (
    CliOptions,
    QuackContext,
    from_cli_options,
    init_cli_env,
    load_config,
    setup_logging,
)
from quackcore.errors import QuackConfigurationError


@pytest.fixture
def temp_config_file(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary config file."""
    config_data = {
        "general": {
            "project_name": "TestProject",
            "debug": True,
            "verbose": False,
        },
        "logging": {
            "level": "DEBUG",
            "console": True,
        },
        "paths": {
            "base_dir": str(tmp_path),
            "output_dir": "output",
        },
    }

    config_file = tmp_path / "quack_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    yield config_file


@pytest.fixture
def temp_project_structure(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary project structure."""
    # Create marker files for project root detection
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / ".git").mkdir()

    # Create source directory
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").touch()

    # Create config directory with config file
    config_dir = tmp_path / "config"
    config_dir.mkdir()

    config_data = {
        "general": {
            "project_name": "TestProject",
            "debug": False,
        },
        "logging": {
            "level": "INFO",
            "console": True,
        },
    }

    config_file = config_dir / "default.yaml"
    with open(config_file, "w") as f:
        yaml.dump(config_data, f)

    # Create output directory
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    yield tmp_path


class TestCliIntegration:
    """Integration tests for CLI functionality."""

    def test_logging_with_config(self, temp_config_file: Path) -> None:
        """Test logging setup with configuration."""
        # Load config from the temporary file
        config = load_config(temp_config_file)

        # Reset root logger to avoid affecting other tests
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # Set up logging from the config
        logger, get_logger = setup_logging(config=config)

        # Verify logger was configured with the right level
        assert logger.level == logging.DEBUG

        # Verify we can get a child logger
        child_logger = get_logger("test")
        assert child_logger.name == "quack.test"
        assert child_logger.level == logging.DEBUG

        # Verify logger handlers
        assert any(isinstance(h, logging.StreamHandler) for h in logger.handlers)

    def test_cli_env_initialization(self, temp_project_structure: Path) -> None:
        """Test initializing the CLI environment with project structure."""
        # Change current directory to the test project root
        original_cwd = os.getcwd()
        os.chdir(temp_project_structure)

        try:
            # Initialize CLI environment without explicit config_path
            # (should discover project structure)
            context = init_cli_env()

            # Verify context properties from auto-discovered config
            assert context.base_dir == temp_project_structure
            assert context.config.general.project_name == "TestProject"
            assert not context.debug  # False from config
            assert not context.verbose  # Default

            # Verify with explicit debug override
            context = init_cli_env(debug=True)
            assert context.debug is True
            assert context.config.general.debug is True  # Config should be updated

            # Verify with explicit config path
            config_path = temp_project_structure / "config" / "default.yaml"
            context = init_cli_env(config_path=str(config_path))
            assert context.config.general.project_name == "TestProject"

            # Verify environment is set correctly
            assert context.environment == "development"  # Default

            context = init_cli_env(environment="test")
            assert context.environment == "test"

            # Test with CLI args
            cli_args = {"general.project_name": "OverrideProject"}
            context = init_cli_env(cli_args=cli_args)
            assert context.config.general.project_name == "OverrideProject"
        finally:
            # Restore original working directory
            os.chdir(original_cwd)

    def test_cli_options_to_env(self) -> None:
        """Test converting CliOptions to environment with from_cli_options."""
        # Create options
        options = CliOptions(
            config_path=Path("/test/config.yaml"),
            log_level="DEBUG",
            debug=True,
            verbose=True,
            quiet=False,
            environment="test",
            base_dir=Path("/test/base"),
        )

        cli_args = {"general.project_name": "CliProject"}

        # Mock dependencies to avoid actual file operations
        with patch("quackcore.cli.boostrap.init_cli_env") as mock_init_env:
            mock_context = MagicMock(spec=QuackContext)
            mock_init_env.return_value = mock_context

            # Call from_cli_options
            context = from_cli_options(options, cli_args, "test_app")

            # Verify init_cli_env was called with the right parameters
            mock_init_env.assert_called_once_with(
                config_path=options.config_path,
                log_level=options.log_level,
                debug=options.debug,
                verbose=options.verbose,
                quiet=options.quiet,
                environment=options.environment,
                base_dir=options.base_dir,
                cli_args=cli_args,
                app_name="test_app",
            )

            # Verify context was returned
            assert context is mock_context

    def test_load_config_with_env_vars(self, temp_config_file: Path) -> None:
        """Test loading config with environment variable overrides."""
        # Set environment variables
        with patch.dict(os.environ, {
            "QUACK_GENERAL__PROJECT_NAME": "EnvProject",
            "QUACK_LOGGING__LEVEL": "ERROR",
            "QUACK_GENERAL__DEBUG": "false",
        }):
            # Load config with environment variables
            config = load_config(temp_config_file, merge_env=True)

            # Verify environment variables override config file
            assert config.general.project_name == "EnvProject"
            assert config.logging.level == "ERROR"
            assert config.general.debug is False

            # Load without environment variables
            config = load_config(temp_config_file, merge_env=False)

            # Verify config file values are used
            assert config.general.project_name == "TestProject"
            assert config.logging.level == "DEBUG"
            assert config.general.debug is True

    def test_load_config_errors(self) -> None:
        """Test error handling in load_config."""
        # Test with non-existent config path
        non_existent = "/path/to/nonexistent/config.yaml"

        with pytest.raises(QuackConfigurationError):
            load_config(non_existent)

        # Test with invalid config format
        with patch("quackcore.cli.boostrap.quack_load_config") as mock_load:
            mock_load.side_effect = QuackConfigurationError("Invalid format")

            with pytest.raises(QuackConfigurationError):
                load_config("/path/to/invalid.yaml")