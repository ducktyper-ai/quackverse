# quackcore/tests/test_paths/test_resolvers.py
"""
Tests for the PathResolver class.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from quackcore.errors import QuackFileNotFoundError
from quackcore.paths import PathResolver


class TestPathResolver:
    """Tests for the PathResolver class."""

    def test_init(self) -> None:
        """Test initializing a PathResolver."""
        resolver = PathResolver()
        assert resolver is not None
        assert resolver._cache == {}

    def test_get_project_root(self, mock_project_structure: Path) -> None:
        """Test finding a project root based on marker files."""
        from quackcore.paths import service as paths

        # Test finding from project root
        root_result = paths.get_project_root(str(mock_project_structure))
        assert root_result.success
        assert root_result.path == str(mock_project_structure)

        # Test finding from subdirectory
        subdir = f"{mock_project_structure}/src"
        root = paths.resolver._get_project_root(subdir)
        assert root == str(mock_project_structure)

        # Test with custom marker files
        root_result = paths.get_project_root(
            str(mock_project_structure), marker_files=["pyproject.toml"]
        )
        assert root_result.success
        assert root_result.path == str(mock_project_structure)

        # Test with custom marker directories
        root_result = paths.get_project_root(
            mock_project_structure, marker_dirs=["src", "tests"]
        )
        assert root_result.success
        assert root_result.path == str(mock_project_structure)

        # Test with non-existent path (should raise)
        with pytest.raises(QuackFileNotFoundError):
            paths.get_project_root("/nonexistent/path")

        # Test where no project root can be found
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with pytest.raises(QuackFileNotFoundError):
                paths.get_project_root(tmp_path)

    def test_find_source_directory(self, mock_project_structure: Path) -> None:
        """Test finding a source directory."""
        resolver = PathResolver()

        # Test finding src from project root
        src_dir = resolver._find_source_directory(str(mock_project_structure))
        assert src_dir == str(mock_project_structure / "src")

        # Test finding src from subdirectory
        src_dir = resolver._find_source_directory(str(mock_project_structure / "tests"))
        assert src_dir == str(mock_project_structure / "src")

        # Test finding a Python package (folder with __init__.py)
        package_dir = mock_project_structure / "src" / "test_module"
        src_dir = resolver._find_source_directory(str(package_dir))
        assert src_dir == str(package_dir)

    def test_find_output_directory(self, mock_project_structure: Path) -> None:
        resolver = PathResolver()

        # Test finding existing output directory
        output_dir = resolver._find_output_directory(str(mock_project_structure))
        assert output_dir == str(mock_project_structure / "output")

        # Test creating output directory
        no_output_dir = mock_project_structure / "no_output"
        no_output_dir.mkdir()
        created_output = resolver._find_output_directory(str(no_output_dir), create=True)
        assert created_output == str(no_output_dir / "output")
        assert Path(created_output).exists()

        # Now, simulate a scenario where no output directory exists by patching
        # get_project_root to return a fresh directory
        # that does not contain an output folder.
        non_existent_dir = mock_project_structure / "non_existent_dir"
        non_existent_dir.mkdir()
        with patch.object(resolver, "_get_project_root", return_value=str(non_existent_dir)):
            with pytest.raises(QuackFileNotFoundError):
                resolver._find_output_directory(str(non_existent_dir), create=False)

    def test_resolve_project_path(self, mock_project_structure: Path) -> None:
        """Test resolving a path relative to the project root."""
        resolver = PathResolver()

        # Test resolving a relative path
        resolved = resolver._resolve_project_path(
            "src/file.txt", str(mock_project_structure)
        )
        assert resolved == str(mock_project_structure / "src" / "file.txt")

        # Test resolving an absolute path (should remain unchanged)
        abs_path = Path("/absolute/path/file.txt")
        resolved = resolver._resolve_project_path(str(abs_path), str(mock_project_structure))
        assert resolved == str(abs_path)

        # Test resolving without explicit project root (should find it)
        with patch.object(
            resolver, "_get_project_root", return_value=str(mock_project_structure)
        ):
            resolved = resolver._resolve_project_path("src/file.txt")
            assert resolved == str(mock_project_structure / "src" / "file.txt")

        # Test resolving when project root cannot be found
        with patch.object(
            resolver, "_get_project_root", side_effect=QuackFileNotFoundError("")
        ):
            # Should use current directory as fallback
            with patch("os.getcwd", return_value="/current/dir"):
                resolved = resolver._resolve_project_path("file.txt")
                assert resolved == "/current/dir/file.txt"

    def test_detect_project_context(self, mock_project_structure: Path) -> None:
        """Test detecting project context from a directory."""
        resolver = PathResolver()

        # Test from project root
        context = resolver._detect_project_context(str(mock_project_structure))
        assert context.root_dir == str(mock_project_structure)
        assert context.name == mock_project_structure.name
        assert len(context.directories) > 0
        assert "src" in context.directories
        assert context.directories["src"].is_source is True
        assert "output" in context.directories
        assert context.directories["output"].is_output is True
        assert context.config_file is not None

        # Test from subdirectory (should cache result)
        subdir = mock_project_structure / "src"
        assert subdir.is_dir()
        context2 = resolver._detect_project_context(str(subdir))
        assert context2.root_dir == str(mock_project_structure)
        assert id(context) == id(context2)  # Should be the same cached object

        # Test with non-existent path
        with pytest.raises(QuackFileNotFoundError):
            resolver._detect_project_context("/nonexistent/path")

        # Test where no project root can be found
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Should return a context with the path as root
            context = resolver._detect_project_context(str(tmp_path))
            assert context.root_dir == str(tmp_path)
            assert len(context.directories) == 0

    def test_detect_content_context(self, mock_project_structure: Path) -> None:
        """Test detecting content context from a directory."""
        resolver = PathResolver()

        # Create some content structure
        content_dir = mock_project_structure / "src" / "tutorials"
        content_dir.mkdir()
        example_dir = content_dir / "example"
        example_dir.mkdir()
        (example_dir / "content.md").write_text("# Example Content")

        # Test from content root
        context = resolver._detect_content_context(str(content_dir))
        assert context.root_dir == str(mock_project_structure)
        assert context.content_type == "tutorials"
        assert context.content_name is None

        # Test from content example
        context = resolver._detect_content_context(str(example_dir))
        assert context.root_dir == str(mock_project_structure)
        assert context.content_type == "tutorials"
        assert context.content_name == "example"
        assert context.content_dir == str(content_dir / "example")

        # Test with explicit content type
        context = resolver._detect_content_context(str(example_dir), content_type="manual")
        assert context.content_type == "manual"

        # Test with non-content directory
        context = resolver._detect_content_context(str(mock_project_structure / "tests"))
        assert context.content_type is None
        assert context.content_name is None

    def test_infer_current_content(self, mock_project_structure: Path) -> None:
        """Test inferring content type and name from current directory."""
        resolver = PathResolver()

        # Create some content structure
        content_dir = mock_project_structure / "src" / "tutorials"
        content_dir.mkdir()
        example_dir = content_dir / "example"
        example_dir.mkdir()

        # Test from content example
        with patch("os.getcwd", return_value=str(example_dir)):
            with patch.object(resolver, "_detect_content_context") as mock_detect:
                mock_detect.return_value.content_type = "tutorials"
                mock_detect.return_value.content_name = "example"

                result = resolver._infer_current_content()
                assert result == {"type": "tutorials", "name": "example"}

        # Test with only content type
        with patch("os.getcwd", return_value=str(content_dir)):
            with patch.object(resolver, "_detect_content_context") as mock_detect:
                mock_detect.return_value.content_type = "tutorials"
                mock_detect.return_value.content_name = None

                result = resolver._infer_current_content()
                assert result == {"type": "tutorials"}

        # Test with no content info
        with patch("os.getcwd", return_value=str(mock_project_structure)):
            with patch.object(resolver, "_detect_content_context") as mock_detect:
                mock_detect.return_value.content_type = None
                mock_detect.return_value.content_name = None

                result = resolver._infer_current_content()
                assert result == {}

    def test_helper_methods(self, mock_project_structure: Path) -> None:
        """Test helper methods of the PathResolver."""
        resolver = PathResolver()

        # Create a context for testing
        context = resolver._detect_project_context(str(mock_project_structure))

        # Test _detect_standard_directories
        resolver._detect_standard_directories(context)
        assert "src" in context.directories
        assert context.directories["src"].is_source is True

        # Test _detect_config_file
        resolver._detect_config_file(context)
        assert context.config_file is not None
        assert "pyproject.toml" in str(context.config_file)

        # Test _infer_content_structure with tutorials
        content_context = resolver._detect_content_context(str(mock_project_structure))

        # Create tutorials directory for testing
        (mock_project_structure / "src" / "tutorials").mkdir()
        (mock_project_structure / "src" / "tutorials" / "example").mkdir()

        # Test with path in tutorials directory
        tutorial_path = mock_project_structure / "src" / "tutorials" / "example"
        resolver._infer_content_structure(content_context, str(tutorial_path))
        assert content_context.content_type == "tutorials"
        assert content_context.content_name == "example"
        assert content_context.content_dir == str(tutorial_path)