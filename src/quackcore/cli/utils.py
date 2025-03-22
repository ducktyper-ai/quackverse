# src/quackcore/cli/utils.py
"""
Utility functions for CLI applications.

This module provides helper functions for common CLI tasks such as
colored output, progress indicators, and user input handling.
"""

import os
import shutil
import sys
from enum import Enum
from typing import Literal, TypeVar

T = TypeVar("T")
U = TypeVar("U")


class Color(str, Enum):
    """ANSI color codes."""

    # Foreground colors
    BLACK = "30"
    RED = "31"
    GREEN = "32"
    YELLOW = "33"
    BLUE = "34"
    MAGENTA = "35"
    CYAN = "36"
    WHITE = "37"
    RESET = "39"

    # Background colors
    BG_BLACK = "40"
    BG_RED = "41"
    BG_GREEN = "42"
    BG_YELLOW = "43"
    BG_BLUE = "44"
    BG_MAGENTA = "45"
    BG_CYAN = "46"
    BG_WHITE = "47"
    BG_RESET = "49"

    # Styles
    BOLD = "1"
    DIM = "2"
    ITALIC = "3"
    UNDERLINE = "4"
    BLINK = "5"
    REVERSE = "7"
    STRIKE = "9"

    # Reset all
    RESET_ALL = "0"


def supports_color() -> bool:
    """
    Check if the terminal supports color output.

    Returns:
        True if color is supported, False otherwise
    """
    # Return False if NO_COLOR env var is set (https://no-color.org/)
    if os.environ.get("NO_COLOR") is not None:
        return False

    # Return False if --no-color flag was used
    if "--no-color" in sys.argv:
        return False

    # Check if stdout is a TTY
    is_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    # If running in GitHub Actions, colors are supported
    in_github_actions = "GITHUB_ACTIONS" in os.environ

    # If running in CI that supports color, allow it
    in_ci_with_color = (
        "CI" in os.environ and os.environ.get("CI_FORCE_COLORS", "0") == "1"
    )

    return is_tty or in_github_actions or in_ci_with_color


def colorize(
    text: str,
    fg: Literal[
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "reset"
    ]
    | None = None,
    bg: Literal[
        "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "reset"
    ]
    | None = None,
    bold: bool = False,
    dim: bool = False,
    underline: bool = False,
    italic: bool = False,
    blink: bool = False,
    force: bool = False,
) -> str:
    """
    Add ANSI color and style to text.

    Args:
        text: The text to colorize
        fg: Foreground color
        bg: Background color
        bold: Whether to make the text bold
        dim: Whether to make the text dim
        underline: Whether to underline the text
        italic: Whether to italicize the text
        blink: Whether to make the text blink
        force: Whether to force color even if the terminal doesn't support it

    Returns:
        Colorized text
    """
    if not (force or supports_color()):
        return text

    fg_codes = {
        "black": Color.BLACK,
        "red": Color.RED,
        "green": Color.GREEN,
        "yellow": Color.YELLOW,
        "blue": Color.BLUE,
        "magenta": Color.MAGENTA,
        "cyan": Color.CYAN,
        "white": Color.WHITE,
        "reset": Color.RESET,
    }

    bg_codes = {
        "black": Color.BG_BLACK,
        "red": Color.BG_RED,
        "green": Color.BG_GREEN,
        "yellow": Color.BG_YELLOW,
        "blue": Color.BG_BLUE,
        "magenta": Color.BG_MAGENTA,
        "cyan": Color.BG_CYAN,
        "white": Color.BG_WHITE,
        "reset": Color.BG_RESET,
    }

    codes = []

    if bold:
        codes.append(Color.BOLD)
    if dim:
        codes.append(Color.DIM)
    if underline:
        codes.append(Color.UNDERLINE)
    if italic:
        codes.append(Color.ITALIC)
    if blink:
        codes.append(Color.BLINK)
    if fg:
        codes.append(fg_codes[fg])
    if bg:
        codes.append(bg_codes[bg])

    if not codes:
        return text

    return f"\033[{';'.join(codes)}m{text}\033[0m"


def get_terminal_size() -> tuple[int, int]:
    """
    Get the terminal size.

    Returns:
        Tuple of (columns, lines)
    """
    try:
        terminal_size = shutil.get_terminal_size((80, 24))
        return terminal_size.columns, terminal_size.lines
    except (ImportError, OSError):
        # Fallback to default size if not available
        return 80, 24
