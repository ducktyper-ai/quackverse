# tests/test_cli/test_cli_properties.py
"""
Property-based tests for CLI functionality using Hypothesis.
"""

from pathlib import Path
from typing import Any

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from quackcore.cli.boostrap import (
    CliOptions,
    QuackContext,
    _merge_cli_overrides,
    resolve_cli_args,
)
from quackcore.config.models import QuackConfig

# Strategy for CLI argument names
cli_arg_name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Lu", "Ll"), blacklist_characters="-"),
    min_size=1,
    max_size=20,
).map(lambda s: s.lower())

# Strategy for CLI argument values
cli_arg_value_strategy = st.one_of(
    st.text(min_size=0, max_size=50),
    st.booleans().map(str),
    st.integers(min_value=-1000, max_value=1000).map(str),
    st.floats(min_value=-100.0, max_value=100.0).map(lambda f: f"{f:.2f}"),
)

# Strategy for basic CLI args dictionaries
cli_args_strategy = st.dictionaries(
    keys=cli_arg_name_strategy, values=cli_arg_value_strategy, max_size=10
)

# Strategy for filesystem paths
path_strategy = st.one_of(
    # Relative paths
    st.lists(
        st.text(
            min_size=1,
            max_size=10,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                blacklist_characters='\\/:*?"<>|',
            ),
        ),
        min_size=1,
        max_size=3,
    ).map(lambda parts: str(Path(*parts))),
    # "Absolute" paths (for testing)
    st.lists(
        st.text(
            min_size=1,
            max_size=10,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                blacklist_characters='\\/:*?"<>|',
            ),
        ),
        min_size=1,
        max_size=3,
    ).map(lambda parts: str(Path("/") / Path(*parts))),
)

# Strategy for basic CLI options
cli_options_strategy = st.builds(
    CliOptions,
    config_path=st.one_of(st.none(), path_strategy.map(Path)),
    log_level=st.one_of(
        st.none(), st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    ),
    debug=st.booleans(),
    verbose=st.booleans(),
    quiet=st.booleans(),
    environment=st.one_of(
        st.none(), st.sampled_from(["development", "test", "production"])
    ),
    base_dir=st.one_of(st.none(), path_strategy.map(Path)),
    no_color=st.booleans(),
)


class TestCliPropertyBased:
    """Property-based tests for CLI functionality."""

    @given(args=st.lists(st.text(min_size=1), min_size=1))
    @settings(max_examples=100)
    def test_resolve_cli_args_properties(self, args: list[str]) -> None:
        """Test properties of the resolve_cli_args function."""
        # Add some flag-like arguments for testing
        flags = ["--debug", "--verbose", "--quiet", "--no-color"]
        args_with_flags = [*flags[:2], *args]  # Add first two flags

        # Add an argument with a value using equals
        assume(len(args) > 0 and "=" not in args[0])
        args_with_flags.append(f"--config={args[0]}")

        # Add an argument with a value using space
        if len(args) > 1:
            assume("--" not in args[1])
            args_with_flags.extend(["--log-level", args[1]])

        # Parse the arguments
        result = resolve_cli_args(args_with_flags)

        # Check that flags were properly parsed
        assert result["debug"] is True
        assert result["verbose"] is True

        # Check that key-value pairs were properly parsed
        assert "config" in result and result["config"] == args[0]

        if len(args) > 1:
            assert "log-level" in result and result["log-level"] == args[1]

    @given(config=st.builds(QuackConfig), overrides=cli_args_strategy)
    @settings(max_examples=50)
    def test_merge_cli_overrides_properties(
        self, config: QuackConfig, overrides: dict[str, str]
    ) -> None:
        """Test properties of the _merge_cli_overrides function."""
        # Skip None values, config/help/version keys which are ignored
        filtered_overrides = {
            k: v
            for k, v in overrides.items()
            if v is not None and k not in ("config", "help", "version")
        }

        # Merge the overrides into the config
        merged = _merge_cli_overrides(config, filtered_overrides)

        # The merged result should always be a QuackConfig
        assert isinstance(merged, QuackConfig)

        # For each override that maps to a simple field, check it was applied
        for key, value in filtered_overrides.items():
            # Skip complex keys with dots for simplicity
            if "." not in key:
                # Convert from CLI style (kebab-case) to Python style (snake_case)
                py_key = key.replace("-", "_")

                # Try to find this key in one of the top-level config objects
                for section in ["general", "logging", "paths", "plugins"]:
                    section_obj = getattr(merged, section)
                    if hasattr(section_obj, py_key):
                        config_value = getattr(section_obj, py_key)

                        # For boolean flags, the value should be True regardless of the string
                        if isinstance(config_value, bool):
                            assert config_value is True or config_value == (
                                value.lower() == "true"
                            )
                        # For other types, we can't easily check the exact value due to type conversion
                        # But we could add more specific checks if needed

    @given(options=cli_options_strategy)
    @settings(max_examples=50)
    def test_cli_options_properties(self, options: CliOptions) -> None:
        """Test properties of the CliOptions class."""
        # Test immutability - options should be frozen
        with pytest.raises(Exception):
            options.debug = not options.debug  # type: ignore

        # Convert to dict and back - should be equivalent
        options_dict = options.model_dump()
        reconstructed = CliOptions(**options_dict)

        assert reconstructed.config_path == options.config_path
        assert reconstructed.log_level == options.log_level
        assert reconstructed.debug == options.debug
        assert reconstructed.verbose == options.verbose
        assert reconstructed.quiet == options.quiet
        assert reconstructed.environment == options.environment
        assert reconstructed.base_dir == options.base_dir
        assert reconstructed.no_color == options.no_color

    @given(
        config=st.builds(QuackConfig),
        extra_data=st.dictionaries(
            keys=st.text(min_size=1, max_size=10), values=st.text(), max_size=5
        ),
    )
    @settings(max_examples=50)
    def test_quack_context_properties(
        self, config: QuackConfig, extra_data: dict[str, Any]
    ) -> None:
        """Test properties of the QuackContext class."""
        # Create a basic context
        logger = object()  # Mock logger
        base_dir = Path("/test/base")

        context = QuackContext(
            config=config,
            logger=logger,
            base_dir=base_dir,
            environment="test",
            extra={},
        )

        # Test with_extra method
        for key, value in extra_data.items():
            # Add each item one by one
            context = context.with_extra(**{key: value})

            # The key should be present in the extra dict
            assert key in context.extra
            assert context.extra[key] == value

            # Other properties should be unchanged
            assert context.config is config
            assert context.logger is logger
            assert context.base_dir == base_dir
            assert context.environment == "test"

        # Final context should have all extra data
        for key, value in extra_data.items():
            assert context.extra[key] == value
