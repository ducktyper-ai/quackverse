# src/ducktyper/ui/mode.py
"""
UI Mode handling for DuckTyper.

This module provides utilities for determining and setting the UI mode
(teaching or production) in DuckTyper.
"""

import os
from enum import Enum, auto
from typing import Literal

# UI mode options
UIMode = Literal["teaching", "production"]

# Current mode (default to teaching mode)
_CURRENT_MODE: UIMode = "teaching"


class Mode(Enum):
    """Enumeration of UI modes."""

    TEACHING = auto()
    PRODUCTION = auto()


def set_mode(mode: UIMode) -> None:
    """
    Set the UI mode for DuckTyper.

    Args:
        mode: The UI mode to set, either 'teaching' or 'production'
    """
    global _CURRENT_MODE
    if mode in ("teaching", "production"):
        _CURRENT_MODE = mode
    else:
        raise ValueError(f"Invalid mode: {mode}. Must be 'teaching' or 'production'")


def get_current_mode() -> UIMode:
    """
    Get the current UI mode.

    Returns:
        The current UI mode, either 'teaching' or 'production'
    """
    return _CURRENT_MODE


def is_playful_mode() -> bool:
    """
    Check if DuckTyper is in playful (teaching) mode.

    Returns:
        True if in teaching mode, False if in production mode
    """
    return _CURRENT_MODE == "teaching"


def set_mode_from_env() -> None:
    """
    Set the UI mode based on the DUCKTYPER_MODE environment variable.

    The default is 'teaching' if the environment variable is not set.
    """
    mode = os.environ.get("DUCKTYPER_MODE", "teaching").lower()

    # Validate and set mode
    if mode in ("teaching", "production"):
        set_mode(mode)
    else:
        # Default to teaching mode if invalid
        set_mode("teaching")