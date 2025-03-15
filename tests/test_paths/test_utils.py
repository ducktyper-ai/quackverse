# tests/test_paths/test_utils.py
"""
Tests for path utility functions.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from quackcore.errors import QuackFileNotFoundError
from quackcore.paths.utils import (
    find_nearest_directory,
    find_project_root,
    get_extension,
    infer_module_from_path,
    join_path,
    normalize_path,
    resolve_relative_to_project,
    split_path,
)


class TestPathUtils:
    """Tests for path utility functions."""

    def test_find_project_root(self, mock_project_structure: Path) -> None:
        """Test finding a project root directory."""
        # Test finding from project root
        root = find_project_root(mock_project_structure)
        assert root == mock_project_structure

        # Test finding from subdirectory
        subdir = mock_project_structure / "src"
        root = find_project_root(subdir)
        assert root == mock_project_structure

        # Test with custom marker files
        root = find_project_root(
            mock_project_structure, marker_files=["pyproject.toml"]
        )
        assert root == mock_project_structure

        # Test with custom marker directories
        root = find_project_root(mock_project_structure, marker_dirs=["src", "tests"])
        assert root == mock_project_structure

        # Test with non-existent path
        with pytest.raises(QuackFileNotFoundError):
            find_project_root("/nonexistent/path")

        # Test where no project root can be found
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with pytest.raises(QuackFileNotFoundError):
                find_project_root(tmp_path)

    def test_find_nearest_directory(self, mock_project_structure: Path) -> None:
        """Test finding the nearest directory with a given name."""
        # Create a nested directory structure
        nested = mock_project_structure / "src" / "nested" / "deeply" / "structure"
        nested.mkdir(parents=True)

        # Test finding from inside nested structure
        found = find_nearest_directory("src", nested)
        assert found == mock_project_structure / "src"

        # Test finding non-existent directory
        with pytest.raises(QuackFileNotFoundError):
            find_nearest_directory("nonexistent", mock_project_structure)

        # Test with max_levels
        with pytest.raises(QuackFileNotFoundError):
            find_nearest_directory("src", nested, max_levels=2)

    def test_resolve_relative_to_project(self, mock_project_structure: Path) -> None:
        """Test resolving a path relative to the project root."""
        # Test resolving a relative path
        resolved = resolve_relative_to_project("src/file.txt", mock_project_structure)
        assert resolved == mock_project_structure / "src" / "file.txt"

        # Test resolving an absolute path (should remain unchanged)
        abs_path = Path("/absolute/path/file.txt")
        resolved = resolve_relative_to_project(abs_path, mock_project_structure)
        assert resolved == abs_path

        # Test resolving without explicit project root
        with patch(
            "quackcore.paths.utils.find_project_root",
            return_value=mock_project_structure,
        ):
            resolved = resolve_relative_to_project("src/file.txt")
            assert resolved == mock_project_structure / "src" / "file.txt"

        # Test when project root cannot be found
        with patch(
            "quackcore.paths.utils.find_project_root",
            side_effect=QuackFileNotFoundError(""),
        ):
            # Should default to current directory
            with patch("pathlib.Path.cwd", return_value=Path("/current/dir")):
                resolved = resolve_relative_to_project("file.txt")
                assert resolved == Path("/current/dir") / "file.txt"

    def test_normalize_path(self) -> None:
        """Test normalizing paths."""
        # Test relative path
        normalized = normalize_path("./test/../file.txt")
        assert normalized.name == "file.txt"
        assert normalized.is_absolute()

        # Test absolute path
        abs_path = Path("/absolute/path/file.txt")
        normalized = normalize_path(abs_path)
        assert normalized == abs_path

        # Test user home
        home_path = "~/Documents/file.txt"
        normalized = normalize_path(home_path)
        assert normalized.is_absolute()
        assert str(normalized).startswith(str(Path.home()))

    def test_join_path(self) -> None:
        """Test joining path components."""
        # Test with string paths
        joined = join_path("dir1", "dir2", "file.txt")
        assert joined == Path("dir1") / "dir2" / "file.txt"

        # Test with Path objects
        joined = join_path(Path("/dir1"), Path("dir2"), "file.txt")
        assert joined == Path("/dir1") / "dir2" / "file.txt"

        # Test with mixed types
        joined = join_path("/dir1", Path("dir2/dir3"), "file.txt")
        assert joined == Path("/dir1") / "dir2/dir3" / "file.txt"

    def test_split_path(self) -> None:
        """Test splitting a path into components."""
        # Test absolute path
        parts = split_path("/dir1/dir2/file.txt")
        assert parts[0] == "/"
        assert "dir1" in parts
        assert "dir2" in parts
        assert parts[-1] == "file.txt"

        # Test relative path
        parts = split_path("dir1/dir2/file.txt")
        assert parts[0] == "dir1"
        assert parts[1] == "dir2"
        assert parts[2] == "file.txt"

        # Test dot path
        parts = split_path("./dir/file.txt")
        assert parts[0] == "."
        assert "dir" in parts
        assert parts[-1] == "file.txt"

    def test_get_extension(self) -> None:
        """Test getting file extensions."""
        assert get_extension("file.txt") == "txt"
        assert get_extension("file.tar.gz") == "gz"
        assert get_extension("file") == ""
        assert get_extension(Path("/path/to/file.png")) == "png"
        assert get_extension(".hidden") == "hidden"  # Special case for dot files

    def test_infer_module_from_path(self, mock_project_structure: Path) -> None:
        """Test inferring a Python module name from a file path."""
        # Create a module structure
        module_dir = mock_project_structure / "src" / "test_module"
        sub_module = module_dir / "submodule"
        sub_module.mkdir(parents=True, exist_ok=True)
        module_file = sub_module / "test_file.py"
        module_file.touch()

        # Test inferring from a file within src directory
        module_name = infer_module_from_path(module_file, mock_project_structure)
        assert module_name == "test_module.submodule.test_file"

        # Test inferring from a file with a relative path
        with patch(
            "quackcore.paths.utils.find_project_root",
            return_value=mock_project_structure,
        ):
            module_name = infer_module_from_path(
                "src/test_module/submodule/test_file.py"
            )
            assert module_name == "test_module.submodule.test_file"

        # Test inferring when src directory cannot be found
        with patch(
            "quackcore.paths.utils.find_nearest_directory",
            side_effect=QuackFileNotFoundError(""),
        ):
            # Should use file's directory as fallback
            module_name = infer_module_from_path(module_file, mock_project_structure)
            assert "test_file" in module_name

        # Test inferring when file is not in project
        with patch(
            "quackcore.paths.utils.find_project_root",
            side_effect=QuackFileNotFoundError(""),
        ):
            module_name = infer_module_from_path("/outside/project/file.py")
            assert module_name == "file"
