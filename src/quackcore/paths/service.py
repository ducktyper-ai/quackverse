# src/quackcore/paths/service.py
"""
Path service for QuackCore.

This module provides a high-level service for path operations in QuackCore projects.
"""

import os

from quackcore.logging import get_logger
from quackcore.paths._internal.resolver import PathResolver
from quackcore.paths._internal.utils import _infer_module_from_path
from quackcore.paths.api.public.results import ContextResult, PathResult


class PathService:
    """
    Public service for path-related operations in QuackCore.

    This service provides methods for resolving paths, detecting project structure,
    and inferring context from file locations in QuackCore projects.
    """

    def __init__(self) -> None:
        """Initialize the path service."""
        self._resolver = PathResolver()
        self.logger = get_logger(__name__)

    def get_project_root(self, start_dir: str | None = None) -> PathResult:
        """
        Find the project root directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            PathResult with the project root directory if successful.
        """
        try:
            path = self._resolver._get_project_root(start_dir)
            return PathResult(success=True, path=path)
        except Exception as e:
            self.logger.error(f"Failed to get project root: {e}")
            return PathResult(success=False, error=str(e))

    def resolve_project_path(
        self, path: str, project_root: str | None = None
    ) -> PathResult:
        """
        Resolve a path relative to the project root.

        Args:
            path: Path to resolve.
            project_root: Project root directory (default: auto-detected)

        Returns:
            PathResult with the resolved absolute path if successful.
        """
        try:
            resolved = self._resolver._resolve_project_path(path, project_root)
            return PathResult(success=True, path=resolved)
        except Exception as e:
            self.logger.error(f"Failed to resolve project path: {e}")
            return PathResult(success=False, error=str(e))

    def detect_project_context(self, start_dir: str | None = None) -> ContextResult:
        """
        Detect project context from a directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            ContextResult with the project context if successful.
        """
        try:
            ctx = self._resolver._detect_project_context(start_dir)
            return ContextResult(success=True, context=ctx)
        except Exception as e:
            self.logger.error(f"Failed to detect project context: {e}")
            return ContextResult(success=False, error=str(e))

    def detect_content_context(
        self, start_dir: str | None = None, content_type: str | None = None
    ) -> ContextResult:
        """
        Detect content context from a directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)
            content_type: Type of content (optional)

        Returns:
            ContextResult with the content context if successful.
        """
        try:
            ctx = self._resolver._detect_content_context(start_dir, content_type)
            return ContextResult(success=True, context=ctx)
        except Exception as e:
            self.logger.error(f"Failed to detect content context: {e}")
            return ContextResult(success=False, error=str(e))

    def get_known_directory(
        self, name: str, start_dir: str | None = None
    ) -> PathResult:
        """
        Get a known directory by name.

        Args:
            name: Name of the directory (e.g., "src", "output", "data").
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            PathResult with the directory path if successful.
        """
        try:
            context_result = self.detect_project_context(start_dir)
            if not context_result.success or not context_result.context:
                return PathResult(success=False, error=context_result.error)

            context = context_result.context
            dir_path = context._get_directory(name)
            if not dir_path:
                return PathResult(
                    success=False, error=f"Directory '{name}' not found in project"
                )
            return PathResult(success=True, path=dir_path)
        except Exception as e:
            self.logger.error(f"Failed to get known directory '{name}': {e}")
            return PathResult(success=False, error=str(e))

    def get_module_path(
        self, module: str, start_dir: str | None = None
    ) -> PathResult:
        """
        Get the file path for a Python module.

        Args:
            module: Python module path (e.g., "myproject.utils.helper")
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            PathResult with the file path if successful.
        """
        try:
            # Get project context to find the source directory
            context_result = self.detect_project_context(start_dir)
            if not context_result.success or not context_result.context:
                return PathResult(success=False, error=context_result.error)

            context = context_result.context
            src_dir = context._get_source_dir()
            if not src_dir:
                return PathResult(
                    success=False, error="Source directory not found in project"
                )

            # Convert module path to file path
            module_parts = module.split(".")
            file_path = os.path.join(src_dir, *module_parts)

            # Check if it's a package or a module
            if os.path.isdir(file_path):
                # It's a package, look for __init__.py
                init_path = os.path.join(file_path, "__init__.py")
                if os.path.exists(init_path):
                    return PathResult(success=True, path=init_path)
                return PathResult(
                    success=False,
                    error=f"Package '{module}' exists but has no __init__.py",
                )
            else:
                # It's a module, append .py extension
                file_path += ".py"
                if os.path.exists(file_path):
                    return PathResult(success=True, path=file_path)
                return PathResult(
                    success=False, error=f"Module '{module}' not found at {file_path}"
                )
        except Exception as e:
            self.logger.error(f"Failed to get module path for '{module}': {e}")
            return PathResult(success=False, error=str(e))

    def get_relative_path(
        self, abs_path: str, start_dir: str | None = None
    ) -> PathResult:
        """
        Get the path relative to the project root.

        Args:
            abs_path: Absolute path to convert.
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            PathResult with the relative path if successful.
        """
        try:
            # Ensure the path is absolute
            norm_path = os.path.abspath(abs_path)

            # Get project root
            root_result = self.get_project_root(start_dir)
            if not root_result.success or not root_result.path:
                return PathResult(success=False, error=root_result.error)

            root_dir = root_result.path

            # Check if path is inside the project
            if not norm_path.startswith(root_dir):
                return PathResult(
                    success=False,
                    error=f"Path '{abs_path}' is not inside project root '{root_dir}'",
                )

            # Compute relative path
            rel_path = os.path.relpath(norm_path, root_dir)
            return PathResult(success=True, path=rel_path)
        except Exception as e:
            self.logger.error(f"Failed to get relative path for '{abs_path}': {e}")
            return PathResult(success=False, error=str(e))

    def get_content_dir(
        self,
        content_type: str,
        content_name: str,
        start_dir: str | None = None,
    ) -> PathResult:
        """
        Get the directory for specific content.

        Args:
            content_type: Type of content (e.g., "tutorials", "videos")
            content_name: Name of the content
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            PathResult with the content directory path if successful.
        """
        try:
            # Get project context to find the source directory
            context_result = self.detect_project_context(start_dir)
            if not context_result.success or not context_result.context:
                return PathResult(success=False, error=context_result.error)

            context = context_result.context
            src_dir = context._get_source_dir()
            if not src_dir:
                return PathResult(
                    success=False, error="Source directory not found in project"
                )

            # Construct the content directory path
            content_dir = os.path.join(src_dir, content_type, content_name)

            # Check if the directory exists
            if not os.path.isdir(content_dir):
                return PathResult(
                    success=False,
                    error=f"Content directory for '{content_type}/{content_name}' not found",
                )

            return PathResult(success=True, path=content_dir)
        except Exception as e:
            self.logger.error(
                f"Failed to get content directory for '{content_type}/{content_name}': {e}"
            )
            return PathResult(success=False, error=str(e))

    def list_known_directories(self, start_dir: str | None = None) -> list[str]:
        """
        List all known directories in the project.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            List of known directory names.
        """
        try:
            context_result = self.detect_project_context(start_dir)
            if not context_result.success or not context_result.context:
                return []

            context = context_result.context
            return list(context.directories.keys())
        except Exception as e:
            self.logger.error(f"Failed to list known directories: {e}")
            return []

    def is_inside_project(self, path: str, start_dir: str | None = None) -> bool:
        """
        Check if a path is inside the project root.

        Args:
            path: Path to check
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            True if the path is inside the project root, False otherwise.
        """
        try:
            # Ensure the path is absolute
            norm_path = os.path.abspath(path)

            # Get project root
            root_result = self.get_project_root(start_dir)
            if not root_result.success or not root_result.path:
                return False

            root_dir = root_result.path

            # Check if path is inside the project
            return norm_path.startswith(root_dir)
        except Exception as e:
            self.logger.error(
                f"Failed to check if path '{path}' is inside project: {e}"
            )
            return False

    def resolve_content_module(
        self, path: str, start_dir: str | None = None
    ) -> PathResult:
        """
        Get the module name for a content file path.

        Args:
            path: Path to the content file
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            PathResult with the module name if successful.
        """
        try:
            # Ensure the path is absolute
            norm_path = os.path.abspath(path)

            # Get project context
            context_result = self.detect_content_context(start_dir)
            if not context_result.success or not context_result.context:
                return PathResult(success=False, error=context_result.error)

            context = context_result.context
            src_dir = context._get_source_dir()
            if not src_dir:
                return PathResult(
                    success=False, error="Source directory not found in project"
                )

            # Check if path is inside the source directory
            if not norm_path.startswith(src_dir):
                return PathResult(
                    success=False,
                    error=f"Path '{path}' is not inside source directory '{src_dir}'",
                )

            # Infer module name
            module_name = _infer_module_from_path(norm_path, context.root_dir)
            return PathResult(success=True, path=module_name)
        except Exception as e:
            self.logger.error(f"Failed to resolve content module for '{path}': {e}")
            return PathResult(success=False, error=str(e))

    def path_exists_in_known_dir(
        self, dir_name: str, rel_path: str, start_dir: str | None = None
    ) -> bool:
        """
        Check if a relative path exists in a known directory.

        Args:
            dir_name: Name of the known directory (e.g., "assets")
            rel_path: Relative path within the directory
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            True if the path exists, False otherwise.
        """
        try:
            # Get the known directory
            dir_result = self.get_known_directory(dir_name, start_dir)
            if not dir_result.success or not dir_result.path:
                return False

            # Construct the full path
            full_path = os.path.join(dir_result.path, rel_path)

            # Check if the path exists
            return os.path.exists(full_path)
        except Exception as e:
            self.logger.error(
                f"Failed to check if path '{rel_path}' exists in '{dir_name}': {e}"
            )
            return False

    def find_source_directory(self, start_dir: str | None = None) -> PathResult:
        """
        Find the source directory of the project.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            PathResult with the source directory path if successful.
        """
        try:
            src_dir = self._resolver._find_source_directory(start_dir)
            return PathResult(success=True, path=src_dir)
        except Exception as e:
            self.logger.error(f"Failed to find source directory: {e}")
            return PathResult(success=False, error=str(e))

    def find_output_directory(
        self, start_dir: str | None = None, create: bool = False
    ) -> PathResult:
        """
        Find or create the output directory of the project.

        Args:
            start_dir: Directory to start searching from (default: current directory)
            create: Whether to create the directory if it doesn't exist

        Returns:
            PathResult with the output directory path if successful.
        """
        try:
            output_dir = self._resolver._find_output_directory(start_dir, create)
            return PathResult(success=True, path=output_dir)
        except Exception as e:
            self.logger.error(f"Failed to find output directory: {e}")
            return PathResult(success=False, error=str(e))

    def infer_current_content(self, start_dir: str | None = None) -> dict[str, str]:
        """
        Infer current content type and name from the current directory.

        Args:
            start_dir: Directory to start from (default: current working directory)

        Returns:
            Dictionary with 'type' and 'name' keys if found.
        """
        try:
            return self._resolver._infer_current_content(start_dir)
        except Exception as e:
            self.logger.error(f"Failed to infer current content: {e}")
            return {}
