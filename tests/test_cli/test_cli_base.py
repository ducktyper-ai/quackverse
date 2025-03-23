# tests/test_cli/test_cli_base.py
"""
Tests for CLI bootstrap functionality.
"""
import logging
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from quackcore.cli.boostrap import (
    QuackContext,
    CliOptions,
    _add_file_handler,
    _determine_effective_level,
    _merge_cli_overrides,
    ensure_single_instance,
    format_cli_error,
    get_cli_info,
    get_terminal_size,
    init_cli_env,
    load_config,
    resolve_cli_args,
    setup_logging,
)
from quackcore.config.models import QuackConfig
from quackcore.errors import QuackConfigurationError, QuackError


class TestQuackContext:
    """Tests for the QuackContext class."""

    def test_init(self) -> None:
        """Test initializing QuackContext."""
        config = QuackConfig()
        logger = MagicMock()
        base_dir = Path("/test/base")

        # Basic initialization
        context = QuackContext(
            config=config,
            logger=logger,
            base_dir=base_dir,
            environment="test",
        )

        assert context.config is config
        assert context.logger is logger
        assert context.base_dir == base_dir
        assert context.environment == "test"
        assert context.debug is False  # Default
        assert context.verbose is False  # Default
        assert context.working_dir == Path.cwd()  # Default
        assert context.extra == {}  # Default

        # Test with all parameters
        working_dir = Path("/test/working")
        extra = {"key": "value"}

        context = QuackContext(
            config=config,
            logger=logger,
            base_dir=base_dir,
            environment="test",
            debug=True,
            verbose=True,
            working_dir=working_dir,
            extra=extra,
        )

        assert context.debug is True
        assert context.verbose is True
        assert context.working_dir == working_dir
        assert context.extra == extra

    def test_with_extra(self) -> None:
        """Test the with_extra method."""
        config = QuackConfig()
        logger = MagicMock()
        base_dir = Path("/test/base")

        # Create a context with existing extra
        context = QuackContext(
            config=config,
            logger=logger,
            base_dir=base_dir,
            environment="test",
            extra={"existing": "value"},
        )

        # Add new extra data
        new_context = context.with_extra(new_key="new_value")

        # Verify the new context has both old and new data
        assert new_context.extra == {"existing": "value", "new_key": "new_value"}

        # Original context should be unchanged
        assert context.extra == {"existing": "value"}

        # Verify that all other attributes are copied
        assert new_context.config is context.config
        assert new_context.logger is context.logger
        assert new_context.base_dir == context.base_dir
        assert new_context.environment == context.environment
        assert new_context.debug == context.debug
        assert new_context.verbose == context.verbose
        assert new_context.working_dir == context.working_dir


class TestCliOptions:
    """Tests for the CliOptions class."""

    def test_init(self) -> None:
        """Test initializing CliOptions."""
        # Test with defaults
        options = CliOptions()
        assert options.config_path is None
        assert options.log_level is None
        assert options.debug is False
        assert options.verbose is False
        assert options.quiet is False
        assert options.environment is None
        assert options.base_dir is None
        assert options.no_color is False

        # Test with custom values
        options = CliOptions(
            config_path=Path("/test/config.yaml"),
            log_level="DEBUG",
            debug=True,
            verbose=True,
            quiet=True,
            environment="test",
            base_dir=Path("/test/base"),
            no_color=True,
        )

        assert options.config_path == Path("/test/config.yaml")
        assert options.log_level == "DEBUG"
        assert options.debug is True
        assert options.verbose is True
        assert options.quiet is True
        assert options.environment == "test"
        assert options.base_dir == Path("/test/base")
        assert options.no_color is True


class TestLoggingSetup:
    """Tests for logging setup functions."""

    def test_determine_effective_level(self) -> None:
        """Test determining the effective logging level."""
        # Test debug flag overrides everything
        level = _determine_effective_level(None, True, False, None)
        assert level == "DEBUG"

        # Test quiet flag takes precedence over config but not debug
        level = _determine_effective_level(None, False, True, None)
        assert level == "ERROR"

        # Test CLI log level takes precedence over config
        config = MagicMock()
        config.logging.level = "INFO"
        level = _determine_effective_level("WARNING", False, False, config)
        assert level == "WARNING"

        # Test config level is used when no CLI options
        level = _determine_effective_level(None, False, False, config)
        assert level == "INFO"

        # Test default is INFO when no other options
        level = _determine_effective_level(None, False, False, None)
        assert level == "INFO"

    def test_add_file_handler(self) -> None:
        """Test adding a file handler to the logger."""
        # Create mock objects
        root_logger = MagicMock()
        config = MagicMock()
        config.logging.file = Path("/test/log/app.log")

        # Test successful file handler creation
        with patch("quackcore.cli.boostrap.fs.create_directory") as mock_create_dir:
            mock_create_dir.return_value.success = True

            with patch("logging.FileHandler") as mock_file_handler:
                handler_instance = MagicMock()
                mock_file_handler.return_value = handler_instance

                _add_file_handler(root_logger, config, logging.INFO)

                # Verify the directory was created
                mock_create_dir.assert_called_once_with(Path("/test/log"),
                                                        exist_ok=True)

                # Verify handler was created and configured
                mock_file_handler.assert_called_once_with(str(config.logging.file))
                handler_instance.setLevel.assert_called_once_with(logging.INFO)
                assert handler_instance.setFormatter.called

                # Verify handler was added to logger
                root_logger.addHandler.assert_called_once_with(handler_instance)

                # Verify debug message was logged
                root_logger.debug.assert_called_once()

        # Test with directory creation failure
        root_logger.reset_mock()
        with patch("quackcore.cli.boostrap.fs.create_directory") as mock_create_dir:
            mock_create_dir.side_effect = Exception("Directory creation failed")

            _add_file_handler(root_logger, config, logging.INFO)

            # Verify warning was logged
            root_logger.warning.assert_called_once()

    @patch("logging.StreamHandler")
    def test_setup_logging(self, mock_stream_handler: MagicMock) -> None:
        """Test setting up logging."""
        # Mock handler instance
        handler_instance = MagicMock()
        mock_stream_handler.return_value = handler_instance

        # Test with defaults
        logger, get_logger = setup_logging()

        # Verify root logger was configured
        assert logger.level == logging.INFO
        assert handler_instance.setFormatter.called

        # Test get_logger function
        child_logger = get_logger("child")
        assert child_logger.name == "quack.child"

        # Test with debug mode
        with patch("quackcore.cli.boostrap._add_file_handler") as mock_add_file_handler:
            config = MagicMock()
            config.logging.file = Path("/test/log/app.log")

            logger, _ = setup_logging(log_level="DEBUG", debug=True, config=config)

            # Debug mode should create a detailed formatter
            assert logger.level == logging.DEBUG
            assert mock_add_file_handler.called


class TestConfigLoading:
    """Tests for configuration loading."""

    def test_merge_cli_overrides(self) -> None:
        """Test merging CLI overrides into config."""
        # Create a base config
        config = QuackConfig(
            general={"debug": False},
            logging={"level": "INFO"},
        )

        # Test with simple overrides
        overrides = {
            "debug": True,
            "log-level": "DEBUG",
        }

        merged = _merge_cli_overrides(config, overrides)
        assert merged.general.debug is True
        assert merged.logging.level == "DEBUG"

        # Test with nested overrides using dot notation
        overrides = {
            "general.verbose": True,
            "logging.file": "/test/log/app.log",
        }

        merged = _merge_cli_overrides(config, overrides)
        assert merged.general.verbose is True
        assert str(merged.logging.file) == "/test/log/app.log"

        # Test with None values (should be ignored)
        overrides = {
            "debug": None,
            "config": "/path/to/config.yaml",  # Should be ignored
            "help": True,  # Should be ignored
            "version": "1.0.0",  # Should be ignored
        }

        merged = _merge_cli_overrides(config, overrides)
        assert merged.general.debug is False  # Unchanged

    @patch("quackcore.cli.boostrap.quack_load_config")
    def test_load_config(self, mock_load_config: MagicMock) -> None:
        """Test loading configuration."""
        # Mock the config loading
        mock_config = QuackConfig(
            general={"debug": False},
            logging={"level": "INFO"},
        )
        mock_load_config.return_value = mock_config

        # Test with explicit config path
        config_path = "/path/to/config.yaml"
        with patch.dict(os.environ, {}, clear=True):
            config = load_config(config_path)

            mock_load_config.assert_called_once_with(config_path)
            assert config is mock_config

        # Test with environment variable override
        mock_load_config.reset_mock()
        with patch.dict(os.environ, {"QUACK_ENV": "test"}):
            load_config(config_path)

            assert os.environ["QUACK_ENV"] == "test"

        # Test with explicit environment override
        mock_load_config.reset_mock()
        with patch.dict(os.environ, {}, clear=True):
            load_config(config_path, environment="prod")

            assert os.environ["QUACK_ENV"] == "prod"

        # Test with CLI overrides
        mock_load_config.reset_mock()
        with patch("quackcore.cli.boostrap._merge_cli_overrides") as mock_merge:
            mock_merge.return_value = mock_config
            cli_overrides = {"debug": True}

            load_config(config_path, cli_overrides)

            mock_merge.assert_called_once_with(mock_config, cli_overrides)

        # Test with loading error
        mock_load_config.reset_mock()
        mock_load_config.side_effect = QuackConfigurationError("Config error")

        # Should raise if explicit path is provided
        with pytest.raises(QuackConfigurationError):
            load_config(config_path)

        # Should return default config if no path is provided
        config = load_config()
        assert isinstance(config, QuackConfig)


class TestCliEnvironment:
    """Tests for CLI environment initialization."""

    @patch("quackcore.cli.boostrap.load_config")
    @patch("quackcore.cli.boostrap.setup_logging")
    @patch("quackcore.cli.boostrap.find_project_root")
    def test_init_cli_env(
            self,
            mock_find_project_root: MagicMock,
            mock_setup_logging: MagicMock,
            mock_load_config: MagicMock,
    ) -> None:
        """Test initializing the CLI environment."""
        # Mock dependencies
        mock_config = QuackConfig(
            general={"debug": False, "verbose": False},
            logging={"level": "INFO"},
        )
        mock_load_config.return_value = mock_config

        mock_logger = MagicMock()
        mock_get_logger = MagicMock(return_value=mock_logger)
        mock_setup_logging.return_value = (mock_logger, mock_get_logger)

        mock_project_root = Path("/test/project")
        mock_find_project_root.return_value = mock_project_root

        # Test basic initialization
        context = init_cli_env()

        assert context.config is mock_config
        assert context.logger is mock_logger
        assert context.base_dir == mock_project_root
        assert not context.debug
        assert not context.verbose

        # Test with explicit parameters
        config_path = "/path/to/config.yaml"
        base_dir = "/test/base"
        context = init_cli_env(
            config_path=config_path,
            log_level="DEBUG",
            debug=True,
            verbose=True,
            quiet=False,
            environment="test",
            base_dir=base_dir,
            cli_args={"key": "value"},
            app_name="test_app",
        )

        mock_load_config.assert_called_with(
            config_path, {"key": "value"}, "test"
        )
        mock_setup_logging.assert_called_with(
            "DEBUG", True, False, mock_config, "test_app"
        )
        assert context.base_dir == Path(base_dir)
        assert context.debug
        assert context.verbose

        # Test with error
        mock_load_config.side_effect = QuackError("Test error")

        with pytest.raises(QuackError):
            init_cli_env()

    @patch("quackcore.cli.boostrap.init_cli_env")
    def test_from_cli_options(self, mock_init_cli_env: MagicMock) -> None:
        """Test initializing from CLI options."""
        # Create CLI options
        options = CliOptions(
            config_path=Path("/test/config.yaml"),
            log_level="DEBUG",
            debug=True,
            verbose=True,
            quiet=False,
            environment="test",
            base_dir=Path("/test/base"),
        )

        # Test with default arguments
        from quackcore.cli.boostrap import from_cli_options

        cli_args = {"key": "value"}
        from_cli_options(options, cli_args, "test_app")

        # Verify init_cli_env was called with the right parameters
        mock_init_cli_env.assert_called_once_with(
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


class TestUtilityFunctions:
    """Tests for CLI utility functions."""

    def test_format_cli_error(self) -> None:
        """Test formatting a CLI error."""
        # Test with QuackError
        error = QuackError("Test error", context={"key": "value"})
        formatted = format_cli_error(error)

        assert "Test error" in formatted
        assert "Context:" in formatted
        assert "key: value" in formatted

        # Test with standard exception
        error = ValueError("Standard error")
        formatted = format_cli_error(error)

        assert "Standard error" in formatted

    @given(st.lists(st.text(), min_size=1))
    def test_resolve_cli_args(self, args: list[str]) -> None:
        """Test resolving CLI arguments."""
        # Add some flag arguments
        args = ["--debug", "--verbose", f"--config={args[0]}", *args[1:]]

        result = resolve_cli_args(args)

        # Verify flags were parsed
        assert result["debug"] is True
        assert result["verbose"] is True
        assert result["config"] == args[0]

        # Test with short flags
        result = resolve_cli_args(["-d", "-v", "--config=test.yaml"])

        assert result["debug"] is True
        assert result["verbose"] is True
        assert result["config"] == "test.yaml"

    def test_ensure_single_instance(self) -> None:
        """Test ensuring a single instance."""
        # Mock socket operations
        with patch("socket.socket") as mock_socket:
            socket_instance = MagicMock()
            mock_socket.return_value = socket_instance

            # Test successful binding (no other instance)
            socket_instance.bind.return_value = None

            with patch("pathlib.Path.write_text"):
                with patch("atexit.register"):
                    result = ensure_single_instance("test_app")

                    assert result is True
                    socket_instance.bind.assert_called_once()

            # Test failed binding (another instance exists)
            socket_instance.bind.side_effect = OSError("Address already in use")

            result = ensure_single_instance("test_app")

            assert result is False

    def test_get_terminal_size(self) -> None:
        """Test getting terminal size."""
        # Test with shutil.get_terminal_size available
        with patch("shutil.get_terminal_size") as mock_get_size:
            mock_get_size.return_value = MagicMock(columns=100, lines=50)

            cols, lines = get_terminal_size()

            assert cols == 100
            assert lines == 50

            # Test with error
            mock_get_size.side_effect = OSError("Error getting terminal size")

            cols, lines = get_terminal_size()

            # Should return defaults
            assert cols == 80
            assert lines == 24

    def test_get_cli_info(self) -> None:
        """Test getting CLI information."""
        # Mock platform and other dependencies
        with patch("platform.platform", return_value="Linux-test"):
            with patch("platform.python_version", return_value="3.13.0"):
                with patch("datetime.datetime") as mock_datetime:
                    mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"

                    with patch("os.getpid", return_value=12345):
                        with patch.dict(os.environ, {"USER": "testuser"}):
                            with patch("quackcore.cli.boostrap.get_env",
                                       return_value="test"):
                                with patch("quackcore.cli.boostrap.get_terminal_size",
                                           return_value=(100, 50)):
                                    info = get_cli_info()

                                    # Verify info contains expected keys
                                    assert info["platform"] == "Linux-test"
                                    assert info["python_version"] == "3.13.0"
                                    assert info["time"] == "2023-01-01T00:00:00"
                                    assert info["pid"] == 12345
                                    assert info["environment"] == "test"
                                    assert info["terminal_size"] == "100x50"
                                    assert info["username"] == "testuser"