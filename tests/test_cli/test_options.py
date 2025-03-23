# tests/test_cli/test_options.py
"""
Tests for the CLI options module.
"""

from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from quackcore.cli.options import CliOptions, LogLevel, resolve_cli_args


class TestCliOptions:
    """Tests for the CliOptions class."""

    def test_init_with_defaults(self) -> None:
        """Test initializing with default values."""
        options = CliOptions()

        assert options.config_path is None
        assert options.log_level is None
        assert options.debug is False
        assert options.verbose is False
        assert options.quiet is False
        assert options.environment is None
        assert options.base_dir is None
        assert options.no_color is False

    def test_init_with_custom_values(self) -> None:
        """Test initializing with custom values."""
        options = CliOptions(
            config_path=Path("/path/to/config.yaml"),
            log_level="DEBUG",
            debug=True,
            verbose=True,
            quiet=False,
            environment="test",
            base_dir=Path("/base/dir"),
            no_color=True,
        )

        assert options.config_path == Path("/path/to/config.yaml")
        assert options.log_level == "DEBUG"
        assert options.debug is True
        assert options.verbose is True
        assert options.quiet is False
        assert options.environment == "test"
        assert options.base_dir == Path("/base/dir")
        assert options.no_color is True

    def test_frozen_model(self) -> None:
        """Test that the model is frozen (immutable)."""
        options = CliOptions()

        with pytest.raises(Exception):
            # This should raise an error because the model is frozen
            options.debug = True

    def test_ignore_extra_fields(self) -> None:
        """Test that extra fields are ignored."""
        # Create with an extra field
        options = CliOptions(extra_field="value")

        # The model should ignore the extra field
        assert not hasattr(options, "extra_field")

    def test_log_level_type(self) -> None:
        """Test that log_level is properly typed."""
        # Valid log levels
        options = CliOptions(log_level="DEBUG")
        assert options.log_level == "DEBUG"

        options = CliOptions(log_level="INFO")
        assert options.log_level == "INFO"

        options = CliOptions(log_level="WARNING")
        assert options.log_level == "WARNING"

        options = CliOptions(log_level="ERROR")
        assert options.log_level == "ERROR"

        options = CliOptions(log_level="CRITICAL")
        assert options.log_level == "CRITICAL"

        # Invalid log level should be caught by pydantic validation
        with pytest.raises(Exception):
            CliOptions(log_level="INVALID")


class TestResolveCliArgs:
    """Tests for the resolve_cli_args function."""

    def test_empty_args(self) -> None:
        """Test with empty arguments."""
        args = []
        result = resolve_cli_args(args)
        assert result == {}

    def test_double_dash_args(self) -> None:
        """Test arguments with double dashes."""
        args = ["--config", "/path/to/config.yaml", "--log-level", "DEBUG"]
        result = resolve_cli_args(args)
        assert result == {"config": "/path/to/config.yaml", "log-level": "DEBUG"}

    def test_double_dash_equals(self) -> None:
        """Test arguments with equals sign."""
        args = ["--config=/path/to/config.yaml", "--log-level=DEBUG"]
        result = resolve_cli_args(args)
        assert result == {"config": "/path/to/config.yaml", "log-level": "DEBUG"}

    def test_double_dash_boolean_flags(self) -> None:
        """Test boolean flags with double dashes."""
        args = ["--debug", "--verbose", "--quiet", "--no-color"]
        result = resolve_cli_args(args)
        assert result == {
            "debug": True,
            "verbose": True,
            "quiet": True,
            "no-color": True,
        }

    def test_single_dash_flags(self) -> None:
        """Test flags with single dash."""
        args = ["-d", "-v", "-q"]
        result = resolve_cli_args(args)
        assert result == {"debug": True, "verbose": True, "quiet": True}

    def test_mixed_args(self) -> None:
        """Test a mix of argument types."""
        args = [
            "--config=/path/to/config.yaml",
            "-d",
            "--environment",
            "test",
            "--no-color",
        ]
        result = resolve_cli_args(args)
        assert result == {
            "config": "/path/to/config.yaml",
            "debug": True,
            "environment": "test",
            "no-color": True,
        }

    @given(
        st.lists(
            st.one_of(
                # Double dash arguments with values
                st.tuples(
                    st.sampled_from(
                        ["--config", "--log-level", "--environment", "--base-dir"]
                    ),
                    st.text(min_size=1, max_size=20),
                ),
                # Double dash arguments with equals
                st.sampled_from(
                    ["--config=value", "--log-level=DEBUG", "--environment=test"]
                ),
                # Boolean flags with double dash
                st.sampled_from(["--debug", "--verbose", "--quiet", "--no-color"]),
                # Boolean flags with single dash
                st.sampled_from(["-d", "-v", "-q"]),
            )
        )
    )
    def test_property_based(self, args_tuples: list) -> None:
        """
        Property-based test for resolve_cli_args.

        Generates various combinations of CLI arguments and ensures
        the function handles them appropriately.
        """
        # Convert tuple-based arguments to flat list
        args = []
        for item in args_tuples:
            if isinstance(item, tuple):
                args.extend(item)
            else:
                args.append(item)

        result = resolve_cli_args(args)

        # Basic validation of the result
        assert isinstance(result, dict)

        # Check that boolean flags are set to True
        for flag in ["debug", "verbose", "quiet", "no-color"]:
            if (
                f"--{flag}" in args
                or (flag == "debug" and "-d" in args)
                or (flag == "verbose" and "-v" in args)
                or (flag == "quiet" and "-q" in args)
            ):
                assert result.get(flag, False) is True

        # Check that arguments with values are properly parsed
        for i in range(len(args) - 1):
            if args[i] in [
                "--config",
                "--log-level",
                "--environment",
                "--base-dir",
            ] and i + 1 < len(args):
                if not args[i + 1].startswith("-"):
                    arg_name = args[i][2:]  # Remove '--'
                    assert result.get(arg_name) == args[i + 1]

        # Check for arguments with equals sign
        for arg in args:
            if "=" in arg and arg.startswith("--"):
                name, value = arg[2:].split("=", 1)
                assert result.get(name) == value
