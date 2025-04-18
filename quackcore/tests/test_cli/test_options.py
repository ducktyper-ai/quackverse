# quackcore/tests/test_cli/test_options.py
"""
Tests for the CLI options module.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from quackcore.cli.options import CliOptions, resolve_cli_args


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
            config_path="/path/to/config.yaml",  # String instead of Path
            log_level="DEBUG",
            debug=True,
            verbose=True,
            quiet=False,
            environment="test",
            base_dir="/base/dir",  # String instead of Path
            no_color=True,
        )

        assert options.config_path == "/path/to/config.yaml"
        assert options.log_level == "DEBUG"
        assert options.debug is True
        assert options.verbose is True
        assert options.quiet is False
        assert options.environment == "test"
        assert options.base_dir == "/base/dir"
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

    def test_duplicate_args(self) -> None:
        """Test handling duplicate arguments."""
        # Last occurrence should be kept
        args = ["--config", "first", "--config", "second"]
        result = resolve_cli_args(args)
        assert result == {"config": "second"}

        # Last occurrence should be kept for equals style too
        args = ["--config=first", "--config=second"]
        result = resolve_cli_args(args)
        assert result == {"config": "second"}

        # Mixed styles should also respect last occurrence
        args = ["--config", "first", "--config=second"]
        result = resolve_cli_args(args)
        assert result == {"config": "second"}

        args = ["--config=first", "--config", "second"]
        result = resolve_cli_args(args)
        assert result == {"config": "second"}

    # Use a simplified approach for property-based testing to avoid order issues
    @given(
        st.lists(
            st.sampled_from(
                ["--debug", "--verbose", "--quiet", "--no-color", "-d", "-v", "-q"]
            ),
            min_size=0,
            max_size=5,
        )
    )
    def test_property_based_flags(self, args: list[str]) -> None:
        """Test property-based testing for boolean flags."""
        result = resolve_cli_args(args)

        for flag in ["debug", "verbose", "quiet", "no-color"]:
            # Check if flag should be set (either via long or short form)
            should_be_set = (
                f"--{flag}" in args
                or (flag == "debug" and "-d" in args)
                or (flag == "verbose" and "-v" in args)
                or (flag == "quiet" and "-q" in args)
            )

            if should_be_set:
                assert result.get(flag, False) is True
            else:
                assert flag not in result

    @given(
        st.dictionaries(
            st.sampled_from(["config", "log-level", "environment", "base-dir"]),
            st.text(min_size=1, max_size=20),
            min_size=0,
            max_size=4,
        )
    )
    def test_property_based_values(self, arg_dict: dict[str, str]) -> None:
        """Test property-based testing for arguments with values."""
        # Convert dictionary to CLI arguments
        args = []
        for key, value in arg_dict.items():
            args.extend([f"--{key}", value])

        result = resolve_cli_args(args)

        # Check that all arguments were processed correctly
        for key, value in arg_dict.items():
            assert result.get(key) == value
