# src/quackcore/cli/__init__.py
"""
CLI package for QuackCore.

This package provides utilities for building command-line interfaces
for QuackVerse tools with consistent behavior and user experience.
"""

from quackcore.cli.boostrap import (
    CliOptions,
    QuackContext,
    ensure_single_instance,
    format_cli_error,
    init_cli_env,
    load_config,
    resolve_cli_args,
    setup_logging,
)
from quackcore.cli.utils import (
    ask,
    colorize,
    confirm,
    get_terminal_size,
    print_error,
    print_info,
    print_success,
    print_warning,
    show_progress,
    supports_color,
    table,
    truncate_text,
)

__all__ = [
    # Bootstrap module exports
    "QuackContext",
    "CliOptions",
    "init_cli_env",
    "setup_logging",
    "load_config",
    "resolve_cli_args",
    "format_cli_error",
    "ensure_single_instance",
    # Utils module exports
    "colorize",
    "print_error",
    "print_warning",
    "print_success",
    "print_info",
    "confirm",
    "ask",
    "show_progress",
    "get_terminal_size",
    "truncate_text",
    "table",
    "supports_color",
]
