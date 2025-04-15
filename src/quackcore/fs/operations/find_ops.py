# src/quackcore/fs/operations/find_ops.py
"""
File finding operations.
"""

from pathlib import Path

from quackcore.errors import (
    QuackFileNotFoundError,
    QuackIOError,
    QuackPermissionError,
)
from quackcore.fs.results import FindResult
from quackcore.logging import get_logger

# Set up logger
logger = get_logger(__name__)


class FindOperationsMixin:
    """File finding operations mixin class."""

    def _resolve_path(self, path: str | Path) -> Path:
        """Resolve a path relative to the base directory."""
        # This method is implemented in the main class
        # It's defined here for type checking
        raise NotImplementedError("This method should be overridden")

    def _find_files(
        self,
        path: str | Path,
        pattern: str,
        recursive: bool = True,
        include_hidden: bool = False,
    ) -> FindResult:
        """
        Find files matching a pattern.

        Args:
            path: Directory to search
            pattern: Pattern to match files against
            recursive: Whether to search recursively
            include_hidden: Whether to include hidden files

        Returns:
            FindResult with matching files
        """
        resolved_path = self._resolve_path(path)
        logger.debug(
            f"Finding files in {resolved_path} with pattern '{pattern}', "
            f"recursive={recursive}, include_hidden={include_hidden}"
        )

        try:
            # Early validation of the path
            if not self._validate_search_path(resolved_path):
                logger.error(
                    f"Directory does not exist or is not a directory: {resolved_path}"
                )
                return FindResult(
                    success=False,
                    path=resolved_path,
                    pattern=pattern,
                    recursive=recursive,
                    error=f"Directory does not exist or "
                    f"is not a directory: {resolved_path}",
                )

            # Perform the search
            files, directories = self._perform_pattern_search(
                resolved_path, pattern, recursive, include_hidden
            )

            # Create the result
            total_matches = len(files) + len(directories)
            logger.info(
                f"Found {len(files)} files and {len(directories)} directories "
                f"matching '{pattern}' in {resolved_path}"
            )

            return FindResult(
                success=True,
                path=resolved_path,
                pattern=pattern,
                recursive=recursive,
                files=files,
                directories=directories,
                total_matches=total_matches,
                message=f"Found {len(files)} files and {len(directories)} "
                f"directories matching '{pattern}'",
            )
        except (QuackFileNotFoundError, QuackPermissionError, QuackIOError) as e:
            logger.error(f"Error finding files in {resolved_path}: {str(e)}")
            return FindResult(
                success=False,
                path=resolved_path,
                pattern=pattern,
                recursive=recursive,
                error=str(e),
            )
        except Exception as e:
            logger.error(f"Unexpected error finding files in {resolved_path}: {str(e)}")
            return FindResult(
                success=False,
                path=resolved_path,
                pattern=pattern,
                recursive=recursive,
                error=str(e),
            )

    def _validate_search_path(self, path: Path) -> bool:
        """
        Validate that a path exists and is a directory.

        Args:
            path: Path to validate

        Returns:
            True if the path exists and is a directory, False otherwise
        """
        valid = path.exists() and path.is_dir()
        if not valid:
            logger.debug(
                f"Path validation failed: exists={path.exists()}, is_dir={path.is_dir() if path.exists() else False}"
            )
        return valid

    def _perform_pattern_search(
        self, directory: Path, pattern: str, recursive: bool, include_hidden: bool
    ) -> tuple[list[Path], list[Path]]:
        """
        Perform the actual search for files and directories matching a pattern.

        Args:
            directory: Directory to search in.
            pattern: Pattern to match against.
            recursive: Whether to search recursively.
            include_hidden: Whether to include hidden files.

        Returns:
            Tuple of (matching files, matching directories)
        """
        files: list[Path] = []
        directories: list[Path] = []

        # Choose the appropriate search method explicitly
        if recursive:
            logger.debug(f"Performing recursive glob with pattern '{pattern}'")
            items = list(directory.rglob(pattern))
        else:
            logger.debug(f"Performing non-recursive glob with pattern '{pattern}'")
            items = list(directory.glob(pattern))

        logger.debug(f"Found {len(items)} total items matching pattern")

        for item in items:
            # Skip hidden items if not requested
            if not include_hidden and item.name.startswith("."):
                logger.debug(f"Skipping hidden item: {item}")
                continue

            if item.is_file():
                files.append(item)
                logger.debug(f"Found matching file: {item}")
            elif item.is_dir():
                directories.append(item)
                logger.debug(f"Found matching directory: {item}")

        return files, directories
