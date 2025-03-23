# src/quackcore/cli/formatting.py
"""
Text formatting utilities for CLI applications.

This module provides functions for formatting text output in CLI applications,
including color formatting, table rendering, and general message formatting.
"""

import sys
from collections.abc import Mapping
from enum import Enum
from typing import Literal

from quackcore.cli.terminal import supports_color, truncate_text, get_terminal_size


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


def colorize(
        text: str,
        fg: Literal[
                "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "reset"
            ] | None = None,
        bg: Literal[
                "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white", "reset"
            ] | None = None,
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

    codes: list[str] = []

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


def print_error(message: str, *, exit_code: int | None = None) -> None:
    """
    Print an error message to stderr.

    Args:
        message: The error message
        exit_code: If provided, exit with this code after printing
    """
    print(colorize(f"Error: {message}", fg="red", bold=True), file=sys.stderr)

    if exit_code is not None:
        sys.exit(exit_code)


def print_warning(message: str) -> None:
    """
    Print a warning message to stderr.

    Args:
        message: The warning message
    """
    print(colorize(f"Warning: {message}", fg="yellow"), file=sys.stderr)


def print_success(message: str) -> None:
    """
    Print a success message.

    Args:
        message: The success message
    """
    print(colorize(f"✓ {message}", fg="green"))


def print_info(message: str) -> None:
    """
    Print an informational message.

    Args:
        message: The informational message
    """
    print(colorize(f"ℹ {message}", fg="blue"))


def print_debug(message: str) -> None:
    """
    Print a debug message.

    Only prints if the QUACK_DEBUG environment variable is set.

    Args:
        message: The debug message
    """
    import os

    if os.environ.get("QUACK_DEBUG") == "1":
        print(colorize(f"DEBUG: {message}", fg="magenta", dim=True))


def table(
        headers: list[str],
        rows: list[list[str]],
        max_width: int | None = None,
        title: str | None = None,
        footer: str | None = None,
) -> str:
    """
    Format data as a text table.

    Args:
        headers: Table headers
        rows: Table rows
        max_width: Maximum width of the table in characters
        title: Optional title for the table
        footer: Optional footer for the table

    Returns:
        Formatted table as a string
    """
    if not rows:
        return ""

    all_rows = [headers] + rows
    col_widths = [
        max(len(str(row[i])) for row in all_rows) for i in range(len(headers))
    ]

    if max_width:
        term_width, _ = get_terminal_size()
        available_width = min(term_width, max_width) - len(headers) - 1
        total_width = sum(col_widths)
        if total_width > available_width:
            scale = available_width / total_width
            col_widths = [max(3, int(w * scale)) for w in col_widths]

    total_width = sum(col_widths) + len(col_widths) * 3 + 1
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    result: list[str] = []

    if title:
        title_line = f"| {title.center(total_width - 4)} |"
        result.extend([separator, title_line, separator])
    else:
        result.append(separator)

    header_row = (
            "|"
            + "|".join(
        f" {h[:w].ljust(w)} " for h, w in zip(headers, col_widths, strict=True)
    )
            + "|"
    )
    result.append(header_row)
    result.append(separator)

    for row in rows:
        str_row = [str(cell) if cell is not None else "" for cell in row]
        while len(str_row) < len(col_widths):
            str_row.append("")
        data_row = (
                "|"
                + "|".join(
            f" {truncate_text(cell, w).ljust(w)} "
            for cell, w in zip(str_row, col_widths, strict=True)
        )
                + "|"
        )
        result.append(data_row)

    result.append(separator)

    if footer:
        footer_line = f"| {footer.ljust(total_width - 4)} |"
        result.extend([footer_line, separator])

    return "\n".join(result)


def dict_to_table(data: Mapping[str, object], title: str | None = None) -> str:
    """
    Convert a dictionary to a formatted table.

    Args:
        data: Dictionary to convert
        title: Optional title for the table

    Returns:
        Formatted table as a string
    """
    headers = ["Key", "Value"]
    rows = [[str(k), str(v)] for k, v in data.items()]
    return table(headers, rows, title=title)