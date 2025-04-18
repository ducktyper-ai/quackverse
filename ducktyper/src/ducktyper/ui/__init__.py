# ducktyper/src/ducktyper/ui/__init__.py
"""
UI components for DuckTyper.

This package provides all the UI components and utilities for rendering
the DuckTyper CLI interface with its retro RPG-inspired aesthetics.
"""

from ducktyper.ui.mode import (
    get_current_mode,
    is_playful_mode,
    set_mode,
    set_mode_from_env,
)

__all__ = [
    # Color and styling
    "COLOR_PALETTE",

    # Mode utilities
    "is_playful_mode",
    "get_current_mode",
    "set_mode",
    "set_mode_from_env",

    # UI components
    "duck_dance",
    "get_retro_progress",
    "print_banner",
    "print_error",
    "print_info",
    "print_loading",
    "print_success",
    "print_warning",
    "quack_alert",
    "quack_say",
    "retro_box",
    "retro_choice",
    "retro_table",
]
