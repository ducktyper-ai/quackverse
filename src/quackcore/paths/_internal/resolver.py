# src/quackcore/paths/resolver.py
"""
Path resolver service for QuackCore.

This module provides a high-level service for resolving paths
in a QuackCore project, detecting project structure, and inferring context from file locations.
"""

from os import getcwd
from os import path as ospath

from quackcore.errors import QuackFileNotFoundError, wrap_io_errors
from quackcore.fs import service as fs
from quackcore.logging import LOG_LEVELS, LogLevel, get_logger
from quackcore.paths._internal.context import ContentContext, ProjectContext
from quackcore.paths._internal.utils import _find_nearest_directory, _find_project_root


# Helper function to determine if one path is relative to another.
def _is_relative_to(child: str, parent: str) -> bool:
    try:
        return ospath.commonpath(
            [ospath.abspath(child), ospath.abspath(parent)]
        ) == ospath.abspath(parent)
    except Exception:
        return False


# Helper function to get parent directory from a string path.
def _get_parent_dir(p: str) -> str:
    comps = fs.split_path(p)
    if len(comps) <= 1:
        return p
    return fs.join_path(*comps[:-1])


# Helper function to compute relative path.
def _compute_relative_path(full_path: str, base_path: str) -> str | None:
    try:
        abs_full = ospath.abspath(full_path)
        abs_base = ospath.abspath(base_path)
        if abs_full.startswith(abs_base):
            rel = abs_full[len(abs_base) :]
            return rel.lstrip("/\\")
    except Exception:
        pass
    return None


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
            log_level: Logging level for the service.
        """
        self.logger = get_logger(__name__)
        self.logger.setLevel(log_level)
        self._cache: dict[str, ProjectContext] = {}

    def _get_project_root(
        self,
        start_dir: str | None = None,
        marker_files: list[str] | None = None,
        marker_dirs: list[str] | None = None,
    ) -> str:
        """
        Find the project root directory.

        Args:
            start_dir: Directory to start searching from (default: current directory)
            marker_files: List of filenames that indicate a project root
            marker_dirs: List of directory names that indicate a project root

        Returns:
            Absolute path (as a string) to the project root directory.

        Raises:
            QuackFileNotFoundError: If project root cannot be found.
        """
        start = start_dir if start_dir is not None else getcwd()
        # Assume find_project_root accepts a string and returns a path-like object.
        root = _find_project_root(start, marker_files, marker_dirs)
        return str(root)

    def _detect_standard_directories(self, context: ProjectContext) -> None:
        """
        Detect standard directories in a project and add them to the context.

        Args:
            context: ProjectContext to update.
        """
        root_dir = context.root_dir  # root_dir is a string

        # Look for source directory
        try:
            src_dir = self._find_source_directory(root_dir)
            context._add_directory("src", src_dir, is_source=True)
        except QuackFileNotFoundError:
            try:
                src_dir = _find_nearest_directory("src", root_dir)
                context._add_directory("src", src_dir, is_source=True)
            except QuackFileNotFoundError:
                pass

        # Look for output directory
        try:
            output_dir = self._find_output_directory(root_dir)
            context._add_directory("output", output_dir, is_output=True)
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
            dir_path = fs.join_path(root_dir, name)
            info = fs.get_file_info(dir_path)
            if info.success and info.exists and info.is_dir:
                context._add_directory(name, dir_path, **attrs)

    def _find_source_directory(
        self,
        start_dir: str | None = None,
    ) -> str:
        """
        Find the source directory of a project.

        Args:
            start_dir: Directory to start searching from (default: current directory)

        Returns:
            Absolute path (as a string) to the source directory.

        Raises:
            QuackFileNotFoundError: If a source directory cannot be found.
        """
        current_dir = start_dir if start_dir is not None else getcwd()

        init_path = fs.join_path(current_dir, "__init__.py")
        info = fs.get_file_info(init_path)
        if info.success and info.exists:
            return current_dir

        try:
            return str(_find_nearest_directory("src", current_dir))
        except QuackFileNotFoundError as e:
            for _ in range(5):  # Check up to 5 levels upward.
                init_path = fs.join_path(current_dir, "__init__.py")
                info = fs.get_file_info(init_path)
                if info.success and info.exists:
                    return current_dir
                parent_dir = _get_parent_dir(current_dir)
                if parent_dir == current_dir:
                    break
                current_dir = parent_dir
            raise QuackFileNotFoundError(
                "src",
                f"Could not find source directory in or near {start_dir or getcwd()}",
            ) from e

    def _find_output_directory(
        self,
        start_dir: str | None = None,
        create: bool = False,
    ) -> str:
        """
        Find or create an output directory for a project.

        Args:
            start_dir: Directory to start searching from (default: current directory)
            create: Whether to create the directory if it doesn't exist

        Returns:
            Absolute path (as a string) to the output directory.

        Raises:
            QuackFileNotFoundError: If output directory cannot be found and create is False.
        """
        if start_dir and create:
            start_path = start_dir
            output_dir = fs.join_path(start_path, "output")
            fs.create_directory(output_dir, exist_ok=True)
            return output_dir

        try:
            root_dir = self._get_project_root(start_dir)
            for candidate in ["output", "out", "build"]:
                output_dir = fs.join_path(root_dir, candidate)
                info = fs.get_file_info(output_dir)
                if info.success and info.exists:
                    return output_dir

            if create:
                output_dir = fs.join_path(root_dir, "output")
                fs.create_directory(output_dir, exist_ok=True)
                return output_dir

            raise QuackFileNotFoundError(
                "output", f"Could not find output directory in project root {root_dir}"
            )
        except QuackFileNotFoundError as e:
            current_dir = start_dir if start_dir is not None else getcwd()
            if create:
                output_dir = fs.join_path(current_dir, "output")
                fs.create_directory(output_dir, exist_ok=True)
                return output_dir
            raise QuackFileNotFoundError(
                "output", f"Could not find output directory in or near {current_dir}"
            ) from e

    def _resolve_project_path(
        self,
        path_value: str | None,
        project_root: str | None = None,
    ) -> str:
        """
        Resolve a path relative to the project root.

        Args:
            path_value: Path to resolve as a string.
            project_root: Project root directory (default: auto-detected)

        Returns:
            Resolved absolute path as a string.
        """
        if path_value is None:
            return ""
        # If already absolute, return as is
        if ospath.isabs(path_value):
            return path_value

        if project_root is None:
            project_root = self._get_project_root()
        return fs.join_path(project_root, path_value)

    def _infer_content_structure(
        self,
        context: ContentContext,
        current_dir: str | None = None,
    ) -> None:
        """
        Infer content structure from directory structure and update context.

        Args:
            context: ContentContext to update.
            current_dir: Current directory (default: current working directory).
        """
        current = current_dir if current_dir is not None else getcwd()
        src_dir = context._get_source_dir()
        if not src_dir:
            return

        if not _is_relative_to(current, src_dir):
            return

        try:
            rel_path = ospath.relpath(current, start=src_dir)
            parts = rel_path.split(ospath.sep)
            if not parts:
                return

            content_types = ["tutorials", "videos", "images", "distro"]
            if parts[0] in content_types:
                context.content_type = parts[0]

            if len(parts) >= 2:
                context.content_name = parts[1]
                context.content_dir = fs.join_path(src_dir, parts[0], parts[1])
        except Exception:
            pass

    @wrap_io_errors
    def _detect_project_context(
        self,
        start_dir: str | None = None,
    ) -> ProjectContext:
        """
        Detect project context from a directory.

        Args:
            start_dir: Directory to start searching from (default: current directory).

        Returns:
            ProjectContext object.

        Raises:
            QuackFileNotFoundError: If the start directory does not exist.
        """
        start = start_dir if start_dir is not None else getcwd()
        info = fs.get_file_info(start)
        if not (info.success and info.exists):
            raise QuackFileNotFoundError(start)

        try:
            root_dir = str(_find_project_root(start))
        except QuackFileNotFoundError:
            root_dir = start

        cache_key = ospath.abspath(root_dir)
        if cache_key in self._cache:
            return self._cache[cache_key]

        context = ProjectContext(root_dir=root_dir)
        context.name = ospath.basename(ospath.abspath(root_dir))
        self._detect_standard_directories(context)
        self._detect_config_file(context)
        self._cache[cache_key] = context
        return context

    def _detect_config_file(self, context: ProjectContext) -> None:
        """
        Detect configuration file in a project.

        Args:
            context: ProjectContext to update.
        """
        root_dir = context.root_dir
        config_files = [
            "config/default.yaml",
            "config/default.yml",
            "quack_config.yaml",
            "quack_config.yml",
            ".quack",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
        ]
        for filename in config_files:
            file_path = fs.join_path(root_dir, filename)
            info = fs.get_file_info(file_path)
            if info.success and info.exists and info.is_file:
                context.config_file = file_path
                break

    def _detect_content_context(
        self,
        start_dir: str | None = None,
        content_type: str | None = None,
    ) -> ContentContext:
        """
        Detect content context from a directory.

        Args:
            start_dir: Directory to start searching from (default: current directory).
            content_type: Type of content (optional).

        Returns:
            ContentContext object.
        """
        project_context = self._detect_project_context(start_dir)
        context = ContentContext(
            root_dir=project_context.root_dir,
            directories=project_context.directories,
            config_file=project_context.config_file,
            name=project_context.name,
            content_type=content_type,
        )

        if content_type is None:
            self._infer_content_structure(context, start_dir)
        return context

    def _infer_current_content(
        self,
        start_dir: str | None = None,
    ) -> dict[str, str]:
        """
        Infer current content type and name from the current directory.

        Args:
            start_dir: Directory to start from (default: current working directory).

        Returns:
            Dictionary with 'type' and 'name' keys if found.
        """
        context = self._detect_content_context(start_dir)
        result: dict[str, str] = {}
        if context.content_type:
            result["type"] = context.content_type
        if context.content_name:
            result["name"] = context.content_name
        return result


# Module-level function for convenience.
def _get_project_root(
    start_dir: str | None = None,
    marker_files: list[str] | None = None,
    marker_dirs: list[str] | None = None,
) -> str:
    """
    Module-level function to find the project root directory.

    Instantiates a PathResolver and delegates to its get_project_root method.

    Args:
        start_dir: Directory to start searching from (default: current directory).
        marker_files: List of filenames that indicate a project root.
        marker_dirs: List of directory names that indicate a project root.

    Returns:
        Absolute path (as a string) to the project root directory.
    """
    return PathResolver()._get_project_root(start_dir, marker_files, marker_dirs)


# Module-level function for convenience.
def _resolve_project_path(
    path_value: str,
    project_root: str | None = None,
) -> str:
    """
    Module-level function to resolve a path relative to the project root.

    Instantiates a PathResolver and delegates to its resolve_project_path method.

    Args:
        path_value: Path to resolve as a string.
        project_root: Project root directory (default: auto-detected).

    Returns:
        Resolved absolute path as a string.
    """
    return PathResolver()._resolve_project_path(path_value, project_root)
