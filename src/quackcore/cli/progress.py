# src/quackcore/cli/progress.py
"""
Progress tracking utilities for CLI applications.

This module provides classes and functions for displaying progress
information in CLI applications, such as progress bars and spinners.
"""

import itertools
import sys
import time
from collections.abc import Iterable, Iterator
from io import TextIOBase
from typing import Protocol, TypeVar

from quackcore.cli.terminal import get_terminal_size

T = TypeVar("T")  # Generic type for iterables


class ProgressCallback(Protocol):
    """Protocol for progress callbacks."""

    def __call__(
        self, current: int, total: int | None, message: str | None = None
    ) -> None:
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
        file: TextIOBase = sys.stdout,
    ) -> None:
        """
        Initialize a progress reporter.

        Args:
            total: Total number of items to process
            desc: Description of the process
            unit: Unit of items being processed
            show_eta: Whether to show estimated time remaining
            file: File to write progress to
        """
        self.total: int | None = total
        self.desc: str = desc or "Progress"
        self.unit: str = unit
        self.current: int = 0
        self.show_eta: bool = show_eta
        self.file: TextIOBase = file
        self.start_time: float | None = None
        self.last_update_time: float | None = None
        self.callbacks: list[ProgressCallback] = []

    def start(self) -> None:
        """Start the progress tracking."""
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
        now = time.time()
        if current is not None:
            self.current = current
        else:
            self.current += 1

        # Avoid updating too frequently to prevent flickering
        if (
            self.last_update_time is not None and
            now - self.last_update_time < 0.1 and
            self.current < (self.total or float("inf"))
        ):
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
        """
        Draw the progress bar.

        Args:
            message: Optional status message to display
        """
        if not hasattr(self.file, "isatty") or not self.file.isatty():
            return  # Do not draw progress bars in non-TTY environments

        term_width, _ = get_terminal_size()

        if self.total:
            percentage = min(100, self.current * 100 // self.total)
            bar_length = min(term_width - 30, 50)
            filled_length = int(bar_length * self.current // self.total)
            bar = "█" * filled_length + "░" * (bar_length - filled_length)

            eta_str = ""
            if self.show_eta and self.start_time and self.current > 0:
                elapsed = time.time() - self.start_time
                rate = self.current / elapsed
                remaining = (self.total - self.current) / rate if rate > 0 else 0
                eta_str = f" ETA: {int(remaining)}s"

            progress_str = (
                f"\r{self.desc}: {self.current}/{self.total} "
                f"{self.unit} [{bar}] {percentage}%{eta_str}"
            )
        else:
            spinner = itertools.cycle(["-", "\\", "|", "/"])
            progress_str = f"\r{self.desc}: {self.current} {self.unit} {next(spinner)}"

        if message:
            progress_str += f" | {message}"

        self.file.write(progress_str.ljust(term_width)[:term_width])
        self.file.flush()


class SimpleProgress(Iterator[T]):
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
    ) -> None:
        """
        Initialize a simple progress tracker.

        Args:
            iterable: The iterable to track progress for
            total: Total number of items (if not available from len())
            desc: Description of the process
            unit: Unit of items being processed
        """
        self.iterable = iter(iterable)
        self.total: int | None = total
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

    If tqdm is available, use it; otherwise, fall back to a simpler progress indicator.

    Args:
        iterable: The iterable to process
        total: Total number of items (needed for iterables without __len__)
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