# tests/test_cli/test_bootstrap.py
"""
Tests for the CLI bootstrap module.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.cli.boostrap import from_cli_options, init_cli_env
from quackcore.cli.context import QuackContext
from quackcore.cli.options import CliOptions
from quackcore.errors import QuackError


class TestInitCliEnv:
    """Tests for init_cli_env function."""

    def test_successful_initialization(self) -> None:
        """Test successful initialization of CLI environment."""
        # Mock all the dependencies
        with patch("quackcore.cli.config.find_project_root") as mock_find_root:
            mock_find_root.return_value = Path("/project/root")

            with patch("quackcore.cli.config.load_config") as mock_load_config:
                mock_config = MagicMock()
                mock_config.general.debug = False
                mock_config.general.verbose = False
                mock_load_config.return_value = mock_config

                with patch("quackcore.cli.logging.setup_logging") as mock_setup_logging:
                    mock_logger = MagicMock()
                    mock_get_logger = MagicMock()
                    mock_setup_logging.return_value = (mock_logger, mock_get_logger)

                    with patch.dict(os.environ, {"QUACK_ENV": "development"}):
                        # Call the function under test
                        context = init_cli_env()

                        # Verify the results
                        assert isinstance(context, QuackContext)
                        assert context.config is mock_config
                        assert context.logger is mock_logger
                        assert context.base_dir == Path("/project/root")
                        assert context.environment == "development"
                        assert context.debug is False
                        assert context.verbose is False
                        assert context.working_dir == Path.cwd()

                        # Verify the mock calls
                        mock_find_root.assert_called_once()
                        mock_load_config.assert_called_once_with(None, None, None)
                        mock_setup_logging.assert_called_once_with(
                            None, False, False, mock_config, "quack"
                        )
                        mock_logger.debug.assert_called()

    def test_with_explicit_parameters(self) -> None:
        """Test initialization with explicit parameters."""
        with patch("quackcore.cli.config.find_project_root"):
            with patch("quackcore.cli.config.load_config") as mock_load_config:
                mock_config = MagicMock()
                mock_config.general.debug = False
                mock_config.general.verbose = False
                mock_load_config.return_value = mock_config

                with patch("quackcore.cli.logging.setup_logging") as mock_setup_logging:
                    mock_logger = MagicMock()
                    mock_get_logger = MagicMock()
                    mock_setup_logging.return_value = (mock_logger, mock_get_logger)

                    # Call with explicit parameters
                    context = init_cli_env(
                        config_path="/path/to/config.yaml",
                        log_level="DEBUG",
                        debug=True,
                        verbose=True,
                        quiet=True,
                        environment="test",
                        base_dir="/custom/base/dir",
                        cli_args={"key": "value"},
                        app_name="test_app",
                    )

                    # Verify the parameters were passed correctly
                    mock_load_config.assert_called_once_with(
                        "/path/to/config.yaml", {"key": "value"}, "test"
                    )
                    mock_setup_logging.assert_called_once_with(
                        "DEBUG", True, True, mock_config, "test_app"
                    )

                    # Verify the context properties
                    assert context.base_dir == Path("/custom/base/dir")
                    assert context.debug is True
                    assert context.verbose is True

    def test_with_debug_flag(self) -> None:
        """Test that debug flag sets config.general.debug."""
        with patch("quackcore.cli.config.find_project_root"):
            with patch("quackcore.cli.config.load_config") as mock_load_config:
                mock_config = MagicMock()
                mock_config.general.debug = False
                mock_config.general.verbose = False
                mock_load_config.return_value = mock_config

                with patch("quackcore.cli.logging.setup_logging"):
                    # Call with debug=True
                    init_cli_env(debug=True)

                    # Verify debug was set in config
                    assert mock_config.general.debug is True

    def test_with_verbose_flag(self) -> None:
        """Test that verbose flag sets config.general.verbose."""
        with patch("quackcore.cli.config.find_project_root"):
            with patch("quackcore.cli.config.load_config") as mock_load_config:
                mock_config = MagicMock()
                mock_config.general.debug = False
                mock_config.general.verbose = False
                mock_load_config.return_value = mock_config

                with patch("quackcore.cli.logging.setup_logging"):
                    # Call with verbose=True
                    init_cli_env(verbose=True)

                    # Verify verbose was set in config
                    assert mock_config.general.verbose is True

    def test_error_handling(self) -> None:
        """Test error handling during initialization."""
        # Test QuackError is re-raised
        with patch("quackcore.cli.config.find_project_root") as mock_find_root:
            mock_find_root.side_effect = QuackError("Project root error")

            with patch("logging.error") as mock_error:
                with pytest.raises(QuackError) as excinfo:
                    init_cli_env()

                assert "Project root error" in str(excinfo.value)
                mock_error.assert_called_once()

        # Test other exceptions are wrapped in QuackError
        with patch("quackcore.cli.config.find_project_root") as mock_find_root:
            mock_find_root.side_effect = ValueError("Unexpected error")

            with patch("logging.error") as mock_error:
                with pytest.raises(QuackError) as excinfo:
                    init_cli_env()

                assert "Unexpected error initializing CLI environment" in str(
                    excinfo.value
                )
                assert "Unexpected error" in str(excinfo.value)
                mock_error.assert_called_once()


class TestFromCliOptions:
    """Tests for from_cli_options function."""

    def test_from_cli_options(self) -> None:
        """Test creating a context from CliOptions."""
        options = CliOptions(
            config_path=Path("/path/to/config.yaml"),
            log_level="DEBUG",
            debug=True,
            verbose=True,
            quiet=False,
            environment="test",
            base_dir=Path("/custom/base/dir"),
            no_color=True,
        )

        # Mock init_cli_env to verify it's called with the right parameters
        with patch("quackcore.cli.boostrap.init_cli_env") as mock_init_cli_env:
            mock_context = MagicMock(spec=QuackContext)
            mock_init_cli_env.return_value = mock_context

            # Call the function under test
            context = from_cli_options(options, {"key": "value"}, "test_app")

            # Verify init_cli_env was called with the right parameters
            mock_init_cli_env.assert_called_once_with(
                config_path=Path("/path/to/config.yaml"),
                log_level="DEBUG",
                debug=True,
                verbose=True,
                quiet=False,
                environment="test",
                base_dir=Path("/custom/base/dir"),
                cli_args={"key": "value"},
                app_name="test_app",
            )

            # Verify the function returns the context from init_cli_env
            assert context is mock_context
