# src/quackcore/paths/plugin.py
"""
Plugin interface for the paths module.

This module defines the plugin interface for the paths module,
allowing QuackCore to expose path resolution functionality to other modules.
"""

from typing import Protocol, TypeVar

from quackcore.paths.context import ContentContext, ProjectContext
from quackcore.paths.resolver import PathResolver

T = TypeVar("T")


class PathsPlugin(Protocol):
    """Protocol for paths plugins."""

    @property
    def name(self) -> str:
        """Name of the plugin."""
        ...

    def find_project_root(self, start_dir: str | None = None) -> str:
        """
        Find the project root directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            Path to the project root directory as a string
        """
        ...

    def detect_project_context(self, start_dir: str | None = None) -> ProjectContext:
        """
        Detect project context from a directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            ProjectContext object
        """
        ...

    def detect_content_context(
        self, start_dir: str | None = None, content_type: str | None = None
    ) -> ContentContext:
        """
        Detect content context from a directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)
            content_type: Type of content (optional)

        Returns:
            ContentContext object
        """
        ...


class QuackPathsPlugin:
    """Implementation of the paths plugin protocol."""

    def __init__(self) -> None:
        """Initialize the plugin."""
        self._resolver = PathResolver()

    @property
    def name(self) -> str:
        """Name of the plugin."""
        return "paths"

    def find_project_root(self, start_dir: str | None = None) -> str:
        """
        Find the project root directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            Path to the project root directory as a string
        """
        return str(self._resolver.find_project_root(start_dir))

    def detect_project_context(self, start_dir: str | None = None) -> ProjectContext:
        """
        Detect project context from a directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            ProjectContext object
        """
        return self._resolver.detect_project_context(start_dir)

    def detect_content_context(
        self, start_dir: str | None = None, content_type: str | None = None
    ) -> ContentContext:
        """
        Detect content context from a directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)
            content_type: Type of content (optional)

        Returns:
            ContentContext object
        """
        return self._resolver.detect_content_context(start_dir, content_type)


def create_plugin() -> PathsPlugin:
    """Create a new instance of the paths plugin."""
    return QuackPathsPlugin()