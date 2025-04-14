# tests/quackcore/test_fs/test_service.py
"""
Tests for the FileSystemService class.
"""

import json
import os
import platform
import tempfile
from pathlib import Path

import yaml
from hypothesis import given
from hypothesis import strategies as st

from quackcore.fs.service import FileSystemService


class TestFileSystemService:
    """Tests for FileSystemService."""

    def test_initialize(self, temp_dir: Path) -> None:
        """Test initializing the service with and without base_dir."""
        # Default initialization
        service = FileSystemService()
        assert service.base_dir == Path.cwd()

        # Initialize with custom base_dir (using the temp_dir fixture)
        service = FileSystemService(base_dir=temp_dir)
        assert service.base_dir == temp_dir

    def test_read_text(self, test_file: Path) -> None:
        """Test reading text from a file."""
        service = FileSystemService()

        # Test successful read
        result = service.read_text(test_file)
        assert result.success is True
        assert result.content == "test content"
        assert result.encoding == "utf-8"

        # Test reading non-existent file
        result = service.read_text(test_file.parent / "nonexistent.txt")
        assert result.success is False
        assert "File not found" in result.error

    def test_read_binary(self, test_binary_file: Path) -> None:
        """Test reading binary data from a file."""
        service = FileSystemService()

        # Test successful read
        result = service.read_binary(test_binary_file)
        assert result.success is True
        assert result.content == b"\x00\x01\x02\x03"

        # Test reading non-existent file
        result = service.read_binary(test_binary_file.parent / "nonexistent.bin")
        assert result.success is False
        assert "File not found" in result.error

    def test_read_lines(self, temp_dir: Path) -> None:
        """Test reading lines from a file."""
        service = FileSystemService()

        # Create a multi-line file
        lines_file = temp_dir / "lines.txt"
        lines_file.write_text("line 1\nline 2\nline 3")

        # Test successful read
        result = service.read_lines(lines_file)
        assert result.success is True
        assert result.content == ["line 1", "line 2", "line 3"]

        # Test reading non-existent file
        result = service.read_lines(temp_dir / "nonexistent.txt")
        assert result.success is False
        assert "File not found" in result.error

    def test_write_text(self, temp_dir: Path) -> None:
        """Test writing text to a file."""
        service = FileSystemService()
        file_path = temp_dir / "write_test.txt"

        # Test writing to a new file
        result = service.write_text(file_path, "test content")
        assert result.success is True
        assert result.bytes_written > 0
        assert file_path.read_text() == "test content"

        # Test overwriting an existing file
        result = service.write_text(file_path, "new content")
        assert result.success is True
        assert file_path.read_text() == "new content"

        # Test writing with different encoding
        result = service.write_text(file_path, "тест", encoding="utf-8")
        assert result.success is True
        assert file_path.read_text(encoding="utf-8") == "тест"

    def test_write_binary(self, temp_dir: Path) -> None:
        """Test writing binary data to a file."""
        service = FileSystemService()
        file_path = temp_dir / "binary_test.bin"

        # Test writing to a new file
        result = service.write_binary(file_path, b"\x00\x01\x02\x03")
        assert result.success is True
        assert result.bytes_written == 4
        assert file_path.read_bytes() == b"\x00\x01\x02\x03"

        # Test overwriting an existing file
        result = service.write_binary(file_path, b"\x04\x05\x06\x07")
        assert result.success is True
        assert file_path.read_bytes() == b"\x04\x05\x06\x07"

    def test_write_lines(self, temp_dir: Path) -> None:
        """Test writing lines to a file."""
        service = FileSystemService()
        file_path = temp_dir / "lines_test.txt"

        # Test writing to a new file
        lines = ["line 1", "line 2", "line 3"]
        result = service.write_lines(file_path, lines)
        assert result.success is True
        assert file_path.read_text() == "line 1\nline 2\nline 3"

        # Test writing with different line ending
        result = service.write_lines(file_path, lines, line_ending="\r\n")
        assert result.success is True
        # Read the file with newline="" to preserve the written line endings.
        with open(file_path, encoding="utf-8", newline="") as f:
            content = f.read()
        assert content == "line 1\r\nline 2\r\nline 3"

    def test_copy(self, test_file: Path, temp_dir: Path) -> None:
        """Test copying a file."""
        service = FileSystemService()
        dest_path = temp_dir / "copy_dest.txt"

        # Test successful copy
        result = service.copy(test_file, dest_path)
        assert result.success is True
        assert dest_path.exists()
        assert dest_path.read_text() == "test content"

        # Test copying to existing file (should fail without overwrite)
        result = service.copy(test_file, dest_path)
        assert result.success is False
        assert "already exists" in result.error

        # Test copying with overwrite
        modified_file = temp_dir / "modified.txt"
        modified_file.write_text("modified content")
        result = service.copy(modified_file, dest_path, overwrite=True)
        assert result.success is True
        assert dest_path.read_text() == "modified content"

        # Test copying non-existent file
        result = service.copy(temp_dir / "nonexistent.txt", dest_path)
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_delete(self, temp_dir: Path) -> None:
        """Test deleting a file."""
        service = FileSystemService()
        file_path = temp_dir / "to_delete.txt"
        file_path.write_text("delete me")

        # Test successful delete
        result = service.delete(file_path)
        assert result.success is True
        assert not file_path.exists()

        # Test deleting non-existent file (should succeed with missing_ok=True)
        result = service.delete(file_path)
        assert result.success is True

        # Test deleting non-existent file with missing_ok=False
        result = service.delete(file_path, missing_ok=False)
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_create_directory(self, temp_dir: Path) -> None:
        """Test creating a directory."""
        service = FileSystemService()
        dir_path = temp_dir / "new_dir"

        # Test successful directory creation
        result = service.create_directory(dir_path)
        assert result.success is True
        assert dir_path.is_dir()

        # Test creating an existing directory (should succeed with exist_ok=True)
        result = service.create_directory(dir_path)
        assert result.success is True

        # Test creating nested directories
        nested_path = dir_path / "sub1" / "sub2"
        result = service.create_directory(nested_path)
        assert result.success is True
        assert nested_path.is_dir()

    def test_get_file_info(self, test_file: Path, temp_dir: Path) -> None:
        """Test getting file information."""
        service = FileSystemService()

        # Test getting info for a file
        result = service.get_file_info(test_file)
        assert result.success is True
        assert result.exists is True
        assert result.is_file is True
        assert result.is_dir is False
        assert result.size > 0
        assert result.modified is not None

        # Test getting info for a directory
        result = service.get_file_info(temp_dir)
        assert result.success is True
        assert result.exists is True
        assert result.is_file is False
        assert result.is_dir is True

        # Test getting info for a non-existent file
        result = service.get_file_info(temp_dir / "nonexistent.txt")
        assert (
            result.success is True
        )  # Note: This is true because the operation succeeded
        assert result.exists is False

    def test_list_directory(self, temp_dir: Path) -> None:
        """Test listing directory contents."""
        service = FileSystemService()

        # Create some files and directories for testing
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.txt").write_text("content2")
        (temp_dir / ".hidden_file").write_text("hidden")
        subdir = temp_dir / "subdir"
        subdir.mkdir()

        # Test listing with default parameters
        result = service.list_directory(temp_dir)
        assert result.success is True
        assert result.exists is True
        assert result.is_empty is False
        assert len(result.files) == 2  # Hidden files not included by default
        assert len(result.directories) == 1
        assert temp_dir / "file1.txt" in result.files
        assert temp_dir / "file2.txt" in result.files
        assert temp_dir / "subdir" in result.directories

        # Test listing with include_hidden=True
        result = service.list_directory(temp_dir, include_hidden=True)
        assert result.success is True
        assert len(result.files) == 3  # Now includes hidden file
        assert temp_dir / ".hidden_file" in result.files

        # Test listing with pattern
        result = service.list_directory(temp_dir, pattern="*.txt")
        assert result.success is True
        assert len(result.files) == 2

        # Test listing non-existent directory
        result = service.list_directory(temp_dir / "nonexistent")
        assert result.success is False
        assert result.exists is False

    def test_find_files(self, temp_dir: Path) -> None:
        """Test finding files matching a pattern."""
        service = FileSystemService()

        # Create some files and directories for testing
        (temp_dir / "file1.txt").write_text("content1")
        (temp_dir / "file2.txt").write_text("content2")
        (temp_dir / "doc1.pdf").write_text("pdf content")
        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "subfile.txt").write_text("sub content")

        # Test finding with pattern
        result = service.find_files(temp_dir, "*.txt")
        assert result.success is True
        assert (
            len(result.files) == 3
        )  # Includes subdir/subfile.txt due to recursive=True
        assert temp_dir / "file1.txt" in result.files
        assert temp_dir / "file2.txt" in result.files
        assert subdir / "subfile.txt" in result.files

        # Test finding without recursion
        result = service.find_files(temp_dir, "*.txt", recursive=False)
        assert result.success is True
        assert len(result.files) == 2  # Excludes subdir/subfile.txt
        assert subdir / "subfile.txt" not in result.files

        # Test finding directories
        result = service.find_files(temp_dir, "*subdir*")
        assert result.success is True
        assert len(result.directories) == 1
        assert subdir in result.directories

    def test_read_yaml(self, temp_dir: Path) -> None:
        """Test reading YAML files."""
        service = FileSystemService()
        yaml_file = temp_dir / "test.yaml"

        # Create a YAML file
        data = {"name": "Test", "values": [1, 2, 3], "nested": {"key": "value"}}
        yaml_content = yaml.dump(data)
        yaml_file.write_text(yaml_content)

        # Test successful read
        result = service.read_yaml(yaml_file)
        assert result.success is True
        assert result.data == data
        assert result.format == "yaml"

        # Test reading invalid YAML
        invalid_yaml = temp_dir / "invalid.yaml"
        invalid_yaml.write_text("name: Test\ninvalid: : value")
        result = service.read_yaml(invalid_yaml)
        assert result.success is False
        assert "format" in result.error.lower()

        # Test reading non-existent file
        result = service.read_yaml(temp_dir / "nonexistent.yaml")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_write_yaml(self, temp_dir: Path) -> None:
        """Test writing YAML files."""
        service = FileSystemService()
        yaml_file = temp_dir / "write.yaml"

        # Test writing data
        data = {"name": "Test", "values": [1, 2, 3], "nested": {"key": "value"}}
        result = service.write_yaml(yaml_file, data)
        assert result.success is True

        # Verify the written data
        read_result = service.read_yaml(yaml_file)
        assert read_result.success is True
        assert read_result.data == data

    def test_read_json(self, temp_dir: Path) -> None:
        """Test reading JSON files."""
        service = FileSystemService()
        json_file = temp_dir / "test.json"

        # Create a JSON file
        data = {"name": "Test", "values": [1, 2, 3], "nested": {"key": "value"}}
        json_content = json.dumps(data)
        json_file.write_text(json_content)

        # Test successful read
        result = service.read_json(json_file)
        assert result.success is True
        assert result.data == data
        assert result.format == "json"

        # Test reading invalid JSON
        invalid_json = temp_dir / "invalid.json"
        invalid_json.write_text('{"name": "Test", "invalid": }')
        result = service.read_json(invalid_json)
        assert result.success is False
        assert "format" in result.error.lower()

        # Test reading non-existent file
        result = service.read_json(temp_dir / "nonexistent.json")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_write_json(self, temp_dir: Path) -> None:
        """Test writing JSON files."""
        service = FileSystemService()
        json_file = temp_dir / "write.json"

        # Test writing data
        data = {"name": "Test", "values": [1, 2, 3], "nested": {"key": "value"}}
        result = service.write_json(json_file, data)
        assert result.success is True

        # Verify the written data
        read_result = service.read_json(json_file)
        assert read_result.success is True
        assert read_result.data == data

    def test_ensure_directory(self, temp_dir: Path) -> None:
        """Test ensuring a directory exists."""
        service = FileSystemService()
        dir_path = temp_dir / "ensure_dir"

        # Test creating a non-existent directory
        result = service.ensure_directory(dir_path)
        assert result.exists()
        assert result.is_dir()

        # Test with existing directory
        result = service.ensure_directory(dir_path)
        assert result.exists()
        assert result.is_dir()

        # Test with nested path
        nested_path = dir_path / "sub1" / "sub2"
        result = service.ensure_directory(nested_path)
        assert result.exists()
        assert result.is_dir()

    def test_get_unique_filename(self, temp_dir: Path) -> None:
        """Test getting a unique filename."""
        service = FileSystemService()

        # Test with a non-existent filename
        unique_name = service.get_unique_filename(temp_dir, "unique.txt")
        assert unique_name == temp_dir / "unique.txt"
        assert not unique_name.exists()

        # Test with an existing filename
        existing_file = temp_dir / "existing.txt"
        existing_file.touch()
        unique_name = service.get_unique_filename(temp_dir, "existing.txt")
        assert unique_name != existing_file
        assert str(unique_name).startswith(str(temp_dir / "existing"))
        assert "_1" in str(unique_name)
        assert not unique_name.exists()

    def test_path_utilities(self, temp_dir: Path) -> None:
        """Test path manipulation utilities."""
        service = FileSystemService()

        # Test join_path
        joined_path = service.join_path(temp_dir, "subdir", "file.txt")
        assert joined_path == temp_dir / "subdir" / "file.txt"

        # Test split_path
        split = service.split_path(temp_dir / "subdir" / "file.txt")
        assert len(split) >= 3
        assert split[-1] == "file.txt"
        assert split[-2] == "subdir"

        # Test normalize_path
        normalized = service.normalize_path("./test/../test")
        assert normalized.name == "test"

        # Test get_extension
        assert service.get_extension("file.txt") == "txt"
        assert service.get_extension("file") == ""
        assert service.get_extension("file.tar.gz") == "gz"

        # Test is_same_file
        file1 = temp_dir / "same1.txt"
        file1.touch()
        file2 = temp_dir / "same2.txt"
        file2.touch()
        file1_link = temp_dir / "same1_link.txt"
        os.symlink(
            file1, file1_link
        ) if platform.system() != "Windows" else file1_link.touch()

        assert service.is_same_file(file1, file1)
        assert not service.is_same_file(file1, file2)
        if platform.system() != "Windows":
            assert service.is_same_file(file1, file1_link)

    @given(st.text(min_size=1, max_size=100))
    def test_hypothetical_file_operations(self, content: str) -> None:
        """Test file operations with hypothesis-generated content."""
        # Skip problematic input like lone carriage returns
        if content in ("\r", "\r\n", "\n\r"):
            return

        service = FileSystemService()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            file_path = tmp_path / "hypo_test.txt"

            # Write content
            result = service.write_text(file_path, content)
            assert result.success is True

            # Read content
            read_result = service.read_text(file_path)
            assert read_result.success is True
            # Use normalized comparison for line endings
            assert read_result.content.replace("\r\n", "\n").replace(
                "\r", "\n"
            ) == content.replace("\r\n", "\n").replace("\r", "\n")

            # Copy content
            copy_path = tmp_path / "hypo_copy.txt"
            copy_result = service.copy(file_path, copy_path)
            assert copy_result.success is True

            # Verify copied content
            copy_read_result = service.read_text(copy_path)
            assert copy_read_result.success is True
            # Compare after normalizing line endings
            normalized_read = copy_read_result.content.replace("\r\n", "\n").replace(
                "\r", "\n"
            )
            normalized_original = content.replace("\r\n", "\n").replace("\r", "\n")
            assert normalized_read == normalized_original

    def test_move(self, temp_dir: Path) -> None:
        """Test moving a file."""
        service = FileSystemService()
        source_path = temp_dir / "source.txt"
        source_path.write_text("source content")
        dest_path = temp_dir / "move_dest.txt"

        # Test successful move
        result = service.move(source_path, dest_path)
        assert result.success is True
        assert dest_path.exists()
        assert not source_path.exists()
        assert dest_path.read_text() == "source content"

        # Test moving to existing file (should fail without overwrite)
        source_path.write_text("new source content")
        result = service.move(source_path, dest_path)
        assert result.success is False
        assert "already exists" in result.error

        # Test moving with overwrite
        result = service.move(source_path, dest_path, overwrite=True)
        assert result.success is True
        assert dest_path.exists()
        assert not source_path.exists()
        assert dest_path.read_text() == "new source content"

        # Test moving non-existent file
        result = service.move(temp_dir / "nonexistent.txt", dest_path)
        assert result.success is False
        assert "not found" in result.error.lower()
