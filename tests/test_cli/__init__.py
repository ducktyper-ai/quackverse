# tests/test_cli/test_cli_init.py
"""
Tests for CLI module initialization.
"""


class TestCliInit:
    """Tests for CLI module initialization."""

    def test_imports(self) -> None:
        """Test that all expected functions and classes are exported."""
        # Import the CLI module
        import quackcore.cli as cli

        # Test bootstrap exports
        assert hasattr(cli, "QuackContext")
        assert hasattr(cli, "CliOptions")
        assert hasattr(cli, "init_cli_env")
        assert hasattr(cli, "setup_logging")
        assert hasattr(cli, "load_config")
        assert hasattr(cli, "resolve_cli_args")
        assert hasattr(cli, "format_cli_error")
        assert hasattr(cli, "ensure_single_instance")

        # Test utils exports
        assert hasattr(cli, "colorize")
        assert hasattr(cli, "print_error")
        assert hasattr(cli, "print_warning")
        assert hasattr(cli, "print_success")
        assert hasattr(cli, "print_info")
        assert hasattr(cli, "confirm")
        assert hasattr(cli, "ask")
        assert hasattr(cli, "show_progress")
        assert hasattr(cli, "get_terminal_size")
        assert hasattr(cli, "truncate_text")
        assert hasattr(cli, "table")
        assert hasattr(cli, "supports_color")

        # Check __all__ list
        assert len(cli.__all__) >= 18  # At least these many exports

        # Ensure every exported name is actually available
        for name in cli.__all__:
            assert hasattr(cli, name)