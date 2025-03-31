# src/quackcore/paths/resolver.py
"""
Path resolver service for QuackCore.

This module provides a high-level service for resolving paths
in a QuackCore project, detecting project structure,
and inferring context from file locations.
"""

from pathlib import Path
from typing import TypeVar

from quackcore.errors import QuackFileNotFoundError, wrap_io_errors
from quackcore.logging import LOG_LEVELS, LogLevel, get_logger
from quackcore.paths.context import ContentContext, ProjectContext
from quackcore.paths.utils import (
    find_nearest_directory,
    find_project_root,
)

T = TypeVar("T")  # Generic type for flexible typing


class PathResolver:
    """
    High-level service for path resolution in QuackCore projects.

    This service provides methods for resolving paths, detecting project structure,
    and inferring context from file locations.
    """

    def __init__(self, log_level: int = LOG_LEVELS[LogLevel.INFO]) -> None:
        """
        Initialize the path resolver service.

        Args:
            log_level: Logging level for the service
        """
        self.logger = get_logger(__name__)
        self.logger.setLevel(log_level)
        self._cache: dict[str, ProjectContext] = {}

    def get_project_root(
        self,
        start_dir: str | Path | None = None,
        marker_files: list[str] | None = None,
        marker_dirs: list[str] | None = None,
    ) -> Path:
        """
        Find the project root directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)
            marker_files: List of filenames that indicate a project root
            marker_dirs: List of directory names that indicate a project root

        Returns:
            Path to the project root directory

        Raises:
            QuackFileNotFoundError: If project root cannot be found
        """
        return find_project_root(start_dir, marker_files, marker_dirs)

    # src/quackcore/paths/resolver.py fixes for PathResolver methods

    def _detect_standard_directories(self, context: ProjectContext) -> None:
        """
        Detect standard directories in a project and add them to the context.

        Args:
            context: ProjectContext to update
        """
        root_dir = context.root_dir

        # Look for source directory
        try:
            src_dir = self.find_source_directory(root_dir)
            # Mark it explicitly as a source directory when adding to context
            context.add_directory("src", src_dir, is_source=True)
        except QuackFileNotFoundError:
            try:
                src_dir = find_nearest_directory("src", str(root_dir))
                context.add_directory("src", src_dir, is_source=True)
            except QuackFileNotFoundError:
                pass

        # Look for output directory
        try:
            output_dir = self.find_output_directory(str(root_dir))
            context.add_directory("output", output_dir, is_output=True)
        except QuackFileNotFoundError:
            pass

        # Look for other standard directories
        standard_dirs = {
            "tests": {"is_test": True},
            "test": {"is_test": True},
            "data": {"is_data": True},
            "config": {"is_config": True},
            "configs": {"is_config": True},
            "docs": {},
            "assets": {"is_asset": True},
            "resources": {},
            "scripts": {},
            "examples": {},
            "temp": {"is_temp": True},
        }

        for name, attrs in standard_dirs.items():
            dir_path = root_dir / name
            if dir_path.is_dir():
                context.add_directory(name, dir_path, **attrs)

    def find_source_directory(
        self,
        start_dir: str | Path | None = None,
    ) -> Path:
        """
        Find the source directory of a project.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            Path to the source directory

        Raises:
            QuackFileNotFoundError: If a source directory cannot be found
        """
        current_dir = Path(start_dir) if start_dir else Path.cwd()

        # First, check if the current directory is a Python package.
        if (current_dir / "__init__.py").exists():
            return current_dir

        try:
            # Try to find a 'src' directory starting from the given directory.
            return find_nearest_directory("src", start_dir)
        except QuackFileNotFoundError as e:
            # If a 'src' directory is not found, search upward for a Python package.
            for _ in range(5):  # Check up to 5 levels upward.
                if (current_dir / "__init__.py").exists():
                    return current_dir
                parent_dir = current_dir.parent
                if parent_dir == current_dir:  # Reached the filesystem root.
                    break
                current_dir = parent_dir

            raise QuackFileNotFoundError(
                "src",
                f"Could not find source directory in or near {start_dir or Path.cwd()}",
            ) from e

    def find_output_directory(
        self,
        start_dir: str | Path | None = None,
        create: bool = False,
    ) -> Path:
        """
        Find or create an output directory for a project.

        Args:
            start_dir: Directory to start searching from (default: current directory)
            create: Whether to create the directory if it doesn't exist

        Returns:
            Path to the output directory

        Raises:
            QuackFileNotFoundError: If output directory
                                    cannot be found and create is False
        """
        # If start_dir is specified and create is True, prioritize creating there.
        if start_dir and create:
            start_path = Path(start_dir)
            output_dir = start_path / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir

        try:
            root_dir = self.get_project_root(start_dir)

            # Check common output directories
            output_dir = root_dir / "output"
            if output_dir.exists():
                return output_dir

            output_dir = root_dir / "out"
            if output_dir.exists():
                return output_dir

            output_dir = root_dir / "build"
            if output_dir.exists():
                return output_dir

            if create:
                output_dir = root_dir / "output"
                output_dir.mkdir(parents=True, exist_ok=True)
                return output_dir

            # This line should properly raise the exception
            raise QuackFileNotFoundError(
                "output", f"Could not find output directory in project root {root_dir}"
            )
        except QuackFileNotFoundError as e:
            current_dir = Path(start_dir) if start_dir else Path.cwd()
            if create:
                output_dir = current_dir / "output"
                output_dir.mkdir(parents=True, exist_ok=True)
                return output_dir
            raise QuackFileNotFoundError(
                "output", f"Could not find output directory in or near {current_dir}"
            ) from e

    # Add resolve_project_path method to the
    # PathResolver class in src/quackcore/paths/resolver.py

    def resolve_project_path(
        self,
        path: str | Path,
        project_root: str | Path | None = None,
    ) -> Path:
        """
        Resolve a path relative to the project root.

        Args:
            path: Path to resolve
            project_root: Project root directory (default: auto-detected)

        Returns:
            Path: Resolved absolute path
        """
        path_obj = Path(path)

        # If path is absolute, return it as is
        if path_obj.is_absolute():
            return path_obj

        # If project root is not specified, try to find it
        if project_root is None:
            try:
                project_root = self.get_project_root()
            except QuackFileNotFoundError:
                # If project root cannot be found, use current directory
                project_root = Path.cwd()
        else:
            project_root = Path(project_root)

        # Resolve path relative to project root
        return project_root / path_obj

    def _infer_content_structure(
        self,
        context: ContentContext,
        current_dir: str | Path | None = None,
    ) -> None:
        """
        Infer content structure from directory structure and update context.

        Args:
            context: ContentContext to update
            current_dir: Current directory (default: current working directory)
        """
        if current_dir is None:
            current_dir = Path.cwd()
        current_dir = Path(current_dir)
        src_dir = context.get_source_dir()
        if not src_dir:
            return

        try:
            # Check if current_dir is within the src directory
            if not current_dir.is_relative_to(src_dir):
                return

            rel_path = current_dir.relative_to(src_dir)
            parts = rel_path.parts

            # Only process if there are path components to analyze
            if not parts:
                return

            # The first level might be a content type directory
            content_types = ["tutorials", "videos", "images", "distro"]
            if len(parts) >= 1 and parts[0] in content_types:
                context.content_type = parts[0]

            # The second level might be a content name
            if len(parts) >= 2:
                context.content_name = parts[1]
                context.content_dir = src_dir / parts[0] / parts[1]
        except (ValueError, IndexError):
            # Handle any exceptions during path processing
            pass

    @wrap_io_errors
    def detect_project_context(
        self,
        start_dir: str | Path | None = None,
    ) -> ProjectContext:
        """
        Detect project context from a directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            ProjectContext object

        Raises:
            QuackFileNotFoundError: If the start directory does not exist.
        """
        if start_dir is None:
            start_dir = Path.cwd()
        start_dir = Path(start_dir)

        # If the start directory doesn't exist, raise an error.
        if not start_dir.exists():
            raise QuackFileNotFoundError(str(start_dir))

        try:
            root_dir = find_project_root(start_dir)
        except QuackFileNotFoundError:
            # Fallback: if no markers are found, use the provided directory as the root.
            root_dir = start_dir

        # Use the resolved root directory as the cache key.
        cache_key = str(root_dir.resolve())
        if cache_key in self._cache:
            return self._cache[cache_key]

        context = ProjectContext(root_dir=root_dir)
        context.name = root_dir.name
        self._detect_standard_directories(context)
        self._detect_config_file(context)
        self._cache[cache_key] = context
        return context

    def _detect_config_file(self, context: ProjectContext) -> None:
        """
        Detect configuration file in a project.

        Args:
            context: ProjectContext to update
        """
        root_dir = context.root_dir
        config_files = [
            "config/default.yaml",
            "config/default.yml",
            "quack_config.yaml",
            "quack_config.yml",
            ".quack",
            "pyproject.toml",  # Move this to the end
            "setup.py",
            "setup.cfg",
        ]
        for filename in config_files:
            file_path = root_dir / filename
            if file_path.is_file():
                context.config_file = file_path
                break

    def detect_content_context(
        self,
        start_dir: str | Path | None = None,
        content_type: str | None = None,
    ) -> ContentContext:
        """
        Detect content context from a directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)
            content_type: Type of content (optional)

        Returns:
            ContentContext object
        """
        project_context = self.detect_project_context(start_dir)
        context = ContentContext(
            root_dir=project_context.root_dir,
            directories=project_context.directories,
            config_file=project_context.config_file,
            name=project_context.name,
            content_type=content_type,  # Use the provided content_type
        )

        # Only infer content structure if content_type wasn't explicitly provided
        if content_type is None:
            self._infer_content_structure(context, start_dir)
        return context

    def infer_current_content(
        self,
        start_dir: str | Path | None = None,
    ) -> dict[str, str]:
        """
        Infer current content type and name from the current directory.

        Args:
            start_dir: Directory to start from (default: current working directory)

        Returns:
            Dictionary with 'type' and 'name' keys if found
        """
        context = self.detect_content_context(start_dir)
        result = {}
        if context.content_type:
            result["type"] = context.content_type
        if context.content_name:
            result["name"] = context.content_name
        return result


def get_project_root(
    start_dir: str | Path | None = None,
    marker_files: list[str] | None = None,
    marker_dirs: list[str] | None = None,
) -> Path:
    """
    Module-level function to get the project root directory.

    This function instantiates a PathResolver and returns the project root.
    """
    return PathResolver().get_project_root(start_dir, marker_files, marker_dirs)


# Add module-level resolve_project_path function to src/quackcore/paths/resolver.py


def resolve_project_path(
    path: str | Path,
    project_root: str | Path | None = None,
) -> Path:
    """
    Module-level function to resolve a path relative to the project root.

    This function instantiates a PathResolver and delegates
    to its resolve_project_path method.

    Args:
        path: Path to resolve
        project_root: Project root directory (default: auto-detected)

    Returns:
        Path: Resolved absolute path
    """
    return PathResolver().resolve_project_path(path, project_root)
