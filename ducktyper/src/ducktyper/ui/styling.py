# ducktyper/src/ducktyper/ui/styling.py
"""
Styling utilities for DuckTyper UI.

This module provides additional styling utilities beyond the core branding
components, including text formatting, color handling, and layout helpers.
"""

import os
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from rich.console import Console

from ducktyper.src.ducktyper.ui.mode import is_playful_mode

# Type variable for generic functions
T = TypeVar("T")

# Create console for styled output
console = Console()


@dataclass
class TerminalSize:
    """Terminal dimensions."""

    width: int
    height: int


def get_terminal_size() -> TerminalSize:
    """
    Get the current terminal size.

    Returns:
        A TerminalSize object with width and height
    """
    width, height = shutil.get_terminal_size((80, 24))
    return TerminalSize(width=width, height=height)


def truncate_text(text: str, max_length: int, indicator: str = "...") -> str:
    """
    Truncate text to a maximum length, adding an indicator if truncated.

    Args:
        text: The text to truncate
        max_length: Maximum length of the truncated text
        indicator: String to append if truncated

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(indicator)] + indicator


def colorize(text: str, fg: str | None = None, bg: str | None = None,
             **styles) -> str:
    """
    Colorize text using Rich's style syntax.

    Args:
        text: The text to colorize
        fg: Foreground color
        bg: Background color
        **styles: Additional styles (bold, italic, underline, etc.)

    Returns:
        Styled text if in teaching mode, otherwise plain text
    """
    if not is_playful_mode():
        return text

    style_parts = []

    if fg:
        style_parts.append(fg)
    if bg:
        style_parts.append(f"on {bg}")

    for style_name, value in styles.items():
        if value:
            style_parts.append(style_name)

    style_str = " ".join(style_parts)
    return f"[{style_str}]{text}[/{style_str}]"


def style_if_playful(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that applies styling only in playful mode.

    Args:
        func: The function to decorate

    Returns:
        Decorated function that skips styling in non-playful mode
    """

    def wrapper(*args, **kwargs):
        if is_playful_mode():
            return func(*args, **kwargs)

        # In production mode, strip styling if result is a string
        result = func(*args, **kwargs)
        if isinstance(result, str):
            # Remove Rich style tags
            return re.sub(r"\[\/?[a-zA-Z0-9 _\-\.#]+\]", "", result)
        return result

    return wrapper


def center_text(text: str, width: int | None = None) -> str:
    """
    Center text in the terminal.

    Args:
        text: The text to center
        width: Terminal width (auto-detected if not provided)

    Returns:
        Centered text
    """
    if width is None:
        width = get_terminal_size().width

    lines = text.splitlines()
    centered_lines = []

    for line in lines:
        # Remove Rich tags for length calculation
        clean_line = re.sub(r"\[\/?[a-zA-Z0-9 _\-\.#]+\]", "", line)
        padding = (width - len(clean_line)) // 2
        centered_lines.append(" " * padding + line)

    return "\n".join(centered_lines)


def clear_screen() -> None:
    """Clear the terminal screen."""
    if os.name == "nt":  # Windows
        os.system("cls")
    else:  # Unix/Linux/MacOS
        os.system("clear")


def format_dict_for_display(data: dict, indent: int = 0) -> str:
    """
    Format a dictionary for user-friendly display.

    Args:
        data: The dictionary to format
        indent: Indentation level

    Returns:
        Formatted string representation of the dictionary
    """
    result = []
    indent_str = "  " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            if is_playful_mode():
                key_str = colorize(str(key), fg="bright_yellow", bold=True)
            else:
                key_str = str(key)
            result.append(f"{indent_str}{key_str}:")
            result.append(format_dict_for_display(value, indent + 1))
        else:
            if is_playful_mode():
                key_str = colorize(str(key), fg="bright_yellow")
                value_str = colorize(str(value), fg="cyan")
            else:
                key_str = str(key)
                value_str = str(value)
            result.append(f"{indent_str}{key_str}: {value_str}")

    return "\n".join(result)


def format_as_header(text: str, char: str = "=") -> str:
    """
    Format text as a header with underline.

    Args:
        text: The header text
        char: The character to use for underlining

    Returns:
        Formatted header
    """
    if is_playful_mode():
        styled_text = colorize(text, bold=True, fg="bright_white")
        underline = colorize(char * len(text), fg="bright_white")
        return f"{styled_text}\n{underline}"
    else:
        return f"{text}\n{char * len(text)}"


def render_progress_bar(
        value: float, total: float = 100.0, width: int = 40, fill_char: str = "█",
        empty_char: str = "░"
) -> str:
    """
    Render a simple text-based progress bar.

    Args:
        value: Current value
        total: Total value
        width: Width of the progress bar in characters
        fill_char: Character for filled part
        empty_char: Character for empty part

    Returns:
        Text progress bar
    """
    percentage = min(1.0, value / total)
    filled_width = int(width * percentage)
    empty_width = width - filled_width

    if is_playful_mode():
        filled = colorize(fill_char * filled_width, fg="bright_yellow")
        empty = colorize(empty_char * empty_width, fg="gray50")
        percentage_text = colorize(f"{percentage * 100:.1f}%", fg="bright_white")
        return f"{filled}{empty} {percentage_text}"
    else:
        return f"{fill_char * filled_width}{empty_char * empty_width} {percentage * 100:.1f}%"


def get_styled_text_length(text: str) -> int:
    """
    Get the visible length of styled text (ignoring style tags).

    Args:
        text: The text with potential style tags

    Returns:
        Visible length of the text
    """
    # Remove Rich tags for length calculation
    clean_text = re.sub(r"\[\/?[a-zA-Z0-9 _\-\.#]+\]", "", text)
    return len(clean_text)
