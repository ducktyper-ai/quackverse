"""
Utility functions for CLI applications.

This module provides helper functions for common CLI tasks such as
colored output, progress indicators, and user input handling.
"""

import os
import sys
import shutil
from enum import Enum
from functools import wraps
from typing import Any, Callable, Literal, TypeVar, overload, Protocol
from collections.abc import Iterable, Iterator, Mapping

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
    in_ci_with_color = "CI" in os.environ and os.environ.get("CI_FORCE_COLORS", "0") == "1"

    return is_tty or in_github_actions or in_ci_with_color


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

    Only prints if QUACK_DEBUG environment variable is set.

    Args:
        message: The debug message
    """
    if os.environ.get("QUACK_DEBUG") == "1":
        print(colorize(f"DEBUG: {message}", fg="magenta", dim=True))


def confirm(
    prompt: str,
    default: bool = False,
    abort: bool = False,
    abort_message: str = "Operation aborted by user."
) -> bool:
    """
    Ask for user confirmation.

    Args:
        prompt: The prompt to display
        default: Default response if user presses Enter
        abort: Whether to abort (sys.exit) on negative confirmation
        abort_message: Message to display if aborting

    Returns:
        True if confirmed, False otherwise
    """
    suffix = " [Y/n]" if default else " [y/N]"
    response = input(f"{prompt}{suffix} ").lower().strip()

    if not response:
        result = default
    else:
        result = response.startswith("y")

    if abort and not result:
        print_error(abort_message, exit_code=1)

    return result


@overload
def ask(
    prompt: str,
    default: None = None,
    validate: Callable[[str], bool] | None = None,
    hide_input: bool = False,
    required: bool = False,
) -> str: ...


@overload
def ask(
    prompt: str,
    default: str,
    validate: Callable[[str], bool] | None = None,
    hide_input: bool = False,
    required: bool = False,
) -> str: ...


def ask(
    prompt: str,
    default: str | None = None,
    validate: Callable[[str], bool] | None = None,
    hide_input: bool = False,
    required: bool = False,
) -> str:
    """
    Ask the user for input with optional validation.

    Args:
        prompt: The prompt to display
        default: Default value if user presses Enter
        validate: Optional validation function that returns True for valid input
        hide_input: Whether to hide user input (for passwords)
        required: Whether input is required (can't be empty)

    Returns:
        User input
    """
    import getpass

    suffix = f" [{default}]" if default is not None else ""
    prompt_str = f"{prompt}{suffix}: "

    while True:
        if hide_input:
            value = getpass.getpass(prompt_str)
        else:
            value = input(prompt_str)

        if not value:
            if default is not None:
                return default
            elif not required:
                return ""
            else:
                print_error("Input is required. Please try again.")
                continue

        if validate is not None and not validate(value):
            print_error("Invalid input. Please try again.")
            continue

        return value


def ask_choice(
    prompt: str,
    choices: list[str],
    default: int | None = None,
    allow_custom: bool = False,
) -> str:
    """
    Ask the user to select from a list of choices.

    Args:
        prompt: The prompt to display
        choices: List of choices to present
        default: Default choice index if user presses Enter
        allow_custom: Whether to allow custom input not in choices

    Returns:
        Selected choice
    """
    # Display choices
    print(f"{prompt}")
    for i, choice in enumerate(choices, 1):
        print(f"{i}. {choice}" + (" (default)" if default == i - 1 else ""))

    # Get selection
    if allow_custom:
        print(f"{len(choices) + 1}. Enter custom value")

    while True:
        default_str = f" [{default + 1}]" if default is not None else ""
        selection = input(f"Enter selection{default_str}: ").strip()

        if not selection and default is not None:
            return choices[default]

        try:
            index = int(selection) - 1
            if 0 <= index < len(choices):
                return choices[index]
            elif allow_custom and index == len(choices):
                return input("Enter custom value: ").strip()
            else:
                print_error(f"Please enter a number between 1 and {len(choices) + (1 if allow_custom else 0)}")
        except ValueError:
            if allow_custom and selection:
                return selection
            print_error("Please enter a valid number")


class ProgressCallback(Protocol):
    """Protocol for progress callbacks."""

    def __call__(self, current: int, total: int | None, message: str | None = None) -> None:
        """
        Update progress information.

        Args:
            current: Current progress value
            total: Total expected value (None if unknown)
            message: Optional status message
        """
        ...


class ProgressReporter:
    """
    Simple progress reporter for loops and iterative processes.

    This class provides methods to report progress both programmatically
    and visually to users.
    """

    def __init__(
        self,
        total: int | None = None,
        desc: str | None = None,
        unit: str = "it",
        show_eta: bool = True,
        file=sys.stdout,
    ):
        """
        Initialize a progress reporter.

        Args:
            total: Total number of items to process
            desc: Description of the process
            unit: Unit of items being processed
            show_eta: Whether to show estimated time remaining
            file: File to write progress to
        """
        self.total = total
        self.desc = desc or "Progress"
        self.unit = unit
        self.current = 0
        self.show_eta = show_eta
        self.file = file
        self.start_time = None
        self.last_update_time = None
        self.callbacks: list[ProgressCallback] = []

    def start(self) -> None:
        """Start the progress tracking."""
        import time
        self.start_time = time.time()
        self.last_update_time = self.start_time
        self.current = 0
        self._draw()

    def update(self, current: int | None = None, message: str | None = None) -> None:
        """
        Update the progress.

        Args:
            current: Current progress value (increments by 1 if None)
            message: Optional status message to display
        """
        import time

        now = time.time()
        if current is not None:
            self.current = current
        else:
            self.current += 1

        # Don't update too frequently to avoid flickering
        if now - (self.last_update_time or 0) < 0.1 and self.current < (self.total or float('inf')):
            return

        self.last_update_time = now
        self._draw(message)

        # Call any registered callbacks
        for callback in self.callbacks:
            callback(self.current, self.total, message)

    def finish(self, message: str | None = None) -> None:
        """
        Mark the progress as complete.

        Args:
            message: Optional final message to display
        """
        if self.total is None:
            self.total = self.current
        self.update(self.total, message)
        self.file.write("\n")
        self.file.flush()

    def add_callback(self, callback: ProgressCallback) -> None:
        """
        Add a callback to be called on progress updates.

        Args:
            callback: Function to call with progress updates
        """
        self.callbacks.append(callback)

    def _draw(self, message: str | None = None) -> None:
        """Draw the progress bar."""
        import time

        if not hasattr(self.file, "isatty") or not self.file.isatty():
            return  # Don't draw progress bars in non-TTY environments

        term_width = get_terminal_size()[0]

        if self.total:
            percentage = min(100, self.current * 100 // self.total)
            bar_length = min(term_width - 30, 50)
            filled_length = int(bar_length * self.current // self.total)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)

            # Calculate ETA
            eta_str = ""
            if self.show_eta and self.start_time and self.current > 0:
                elapsed = time.time() - self.start_time
                rate = self.current / elapsed
                remaining = (self.total - self.current) / rate if rate > 0 else 0
                eta_str = f" ETA: {int(remaining)}s"

            progress_str = f"\r{self.desc}: {self.current}/{self.total} {self.unit} [{bar}] {percentage}%{eta_str}"
        else:
            # Spinner for unknown total
            import itertools
            spinner = itertools.cycle(['-', '\\', '|', '/'])
            progress_str = f"\r{self.desc}: {self.current} {self.unit} {next(spinner)}"

        if message:
            progress_str += f" | {message}"

        self.file.write(progress_str.ljust(term_width)[:term_width])
        self.file.flush()


class SimpleProgress:
    """
    Simple progress tracker for iterables.

    This is a simple wrapper around ProgressReporter that works with
    iterables (similar to tqdm but with fewer features).
    """

    def __init__(
        self,
        iterable: Iterable[T],
        total: int | None = None,
        desc: str | None = None,
        unit: str = "it",
    ):
        """
        Initialize a simple progress tracker.

        Args:
            iterable: The iterable to track progress for
            total: Total number of items (if not available from len())
            desc: Description of the process
            unit: Unit of items being processed
        """
        self.iterable = iter(iterable)
        self.total = total

        # Try to get length if not provided
        if self.total is None and hasattr(iterable, "__len__"):
            try:
                self.total = len(iterable)  # type: ignore
            except (TypeError, AttributeError):
                pass

        self.reporter = ProgressReporter(self.total, desc, unit)
        self.reporter.start()

    def __iter__(self) -> Iterator[T]:
        """Return the iterator."""
        return self

    def __next__(self) -> T:
        """Get the next item with progress tracking."""
        try:
            value = next(self.iterable)
            self.reporter.update()
            return value
        except StopIteration:
            self.reporter.finish()
            raise


def show_progress(
    iterable: Iterable[T],
    total: int | None = None,
    desc: str | None = None,
    unit: str = "it",
) -> Iterator[T]:
    """
    Show a progress bar for an iterable.

    If tqdm is available, use it. Otherwise, fall back to a simpler progress indicator.

    Args:
        iterable: The iterable to process
        total: Total number of items (needed for iterables with no len())
        desc: Description to show next to the progress bar
        unit: Unit of items being processed

    Returns:
        An iterator that wraps the original iterable with progress reporting
    """
    try:
        from tqdm import tqdm
        return tqdm(iterable, total=total, desc=desc, unit=unit)
    except ImportError:
        return SimpleProgress(iterable, total, desc, unit)


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


def truncate_text(text: str, max_length: int, indicator: str = "...") -> str:
    """
    Truncate text to a maximum length with an indicator.

    Args:
        text: Text to truncate
        max_length: Maximum length
        indicator: String to append to truncated text

    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text

    return text[:max_length - len(indicator)] + indicator


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

    # Calculate column widths
    all_rows = [headers] + rows
    col_widths = [
        max(len(str(row[i])) for row in all_rows)
        for i in range(len(headers))
    ]

    # Adjust for max_width if specified
    if max_width:
        term_width = get_terminal_size()[0]
        available_width = min(term_width, max_width) - len(headers) - 1

        # Calculate total width and reduce proportionally if needed
        total_width = sum(col_widths)
        if total_width > available_width:
            scale = available_width / total_width
            col_widths = [max(3, int(w * scale)) for w in col_widths]

    # Format the rows
    total_width = sum(col_widths) + len(col_widths) * 3 + 1
    separator = "+" + "+".join("-" * (w + 2) for w in col_widths) + "+"
    result = []

    # Add title if provided
    if title:
        title_line = f"| {title.center(total_width - 4)} |"
        result.extend([separator, title_line, separator])
    else:
        result.append(separator)

    # Format headers
    header_row = "|" + "|".join(
        f" {h[:w].ljust(w)} " for h, w in zip(headers, col_widths)
    ) + "|"
    result.append(header_row)
    result.append(separator)

    # Format data rows
    for row in rows:
        # Convert all values to strings and handle missing values
        str_row = [str(cell) if cell is not None else "" for cell in row]
        # Pad or truncate row if needed
        while len(str_row) < len(col_widths):
            str_row.append("")

        data_row = "|" + "|".join(
            f" {truncate_text(cell, w).ljust(w)} "
            for cell, w in zip(str_row, col_widths)
        ) + "|"
        result.append(data_row)

    result.append(separator)

    # Add footer if provided
    if footer:
        footer_line = f"| {footer.ljust(total_width - 4)} |"
        result.extend([footer_line, separator])

    return "\n".join(result)


def with_spinner(desc: str = "Processing"):
    """
    Decorator to show a spinner while a function is running.

    Args:
        desc: Description to show next to the spinner

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., U]) -> Callable[..., U]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> U:
            import itertools
            import threading
            import time

            spinner = itertools.cycle(['-', '\\', '|', '/'])
            spinning = True

            def spin() -> None:
                while spinning:
                    sys.stdout.write(f"\r{desc} {next(spinner)}")
                    sys.stdout.flush()
                    time.sleep(0.1)
                sys.stdout.write("\r" + " " * (len(desc) + 2) + "\r")
                sys.stdout.flush()

            thread = threading.Thread(target=spin)
            thread.daemon = True
            thread.start()

            try:
                return func(*args, **kwargs)
            finally:
                spinning = False
                thread.join()

        return wrapper
    return decorator


def dict_to_table(data: Mapping[str, Any], title: str | None = None) -> str:
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