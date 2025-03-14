# tests/test_fs/test_operations.py
"""
Tests for the FileSystemOperations class.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from quackcore.errors import QuackFileExistsError, QuackFileNotFoundError, QuackIOError
from quackcore.fs.operations import FileSystemOperations


class TestFileSystemOperations:
    """Tests for the FileSystemOperations class."""

    def test_initialize(self) -> None:
        """Test initializing operations with and without base_dir."""
        # Default initialization
        operations = FileSystemOperations()
        assert operations.base_dir == Path.cwd()

        # Initialize with custom base_dir
        custom_dir = Path("/tmp/custom")
        operations = FileSystemOperations(base_dir=custom_dir)
        assert operations.base_dir == custom_dir

    def test_resolve_path(self) -> None:
        """Test resolving paths relative to the base directory."""
        base_dir = Path("/base/dir")
        operations = FileSystemOperations(base_dir=base_dir)

        # Test with relative path
        rel_path = Path("subdir/file.txt")
        resolved = operations.resolve_path(rel_path)
        assert resolved == base_dir / rel_path

        # Test with absolute path
        abs_path = Path("/absolute/path/file.txt")
        resolved = operations.resolve_path(abs_path)
        assert resolved == abs_path  # Should remain unchanged

        # Test with string path
        str_path = "string/path/file.txt"
        resolved = operations.resolve_path(str_path)
        assert resolved == base_dir / str_path

    def test_read_text(self, temp_dir: Path) -> None:
        """Test reading text from a file."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Create a test file
        file_path = temp_dir / "text_test.txt"
        file_path.write_text("test content")

        # Test successful read
        result = operations.read_text("text_test.txt")
        assert result.success is True
        assert result.content == "test content"
        assert result.encoding == "utf-8"

        # Test custom encoding
        utf16_file = temp_dir / "utf16_test.txt"
        utf16_file.write_text("тест текст", encoding="utf-16")
        result = operations.read_text("utf16_test.txt", encoding="utf-16")
        assert result.success is True
        assert result.content == "тест текст"
        assert result.encoding == "utf-16"

        # Test reading non-existent file
        result = operations.read_text("nonexistent.txt")
        assert result.success is False
        assert "File not found" in result.error

    def test_read_binary(self, temp_dir: Path) -> None:
        """Test reading binary data from a file."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Create a test binary file
        file_path = temp_dir / "binary_test.bin"
        file_path.write_bytes(b"\x00\x01\x02\x03")

        # Test successful read
        result = operations.read_binary("binary_test.bin")
        assert result.success is True
        assert result.content == b"\x00\x01\x02\x03"

        # Test reading non-existent file
        result = operations.read_binary("nonexistent.bin")
        assert result.success is False
        assert "File not found" in result.error

    def test_write_text(self, temp_dir: Path) -> None:
        """Test writing text to a file."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Test writing to a new file
        result = operations.write_text("write_test.txt", "test content")
        assert result.success is True
        assert result.bytes_written > 0
        assert (temp_dir / "write_test.txt").read_text() == "test content"

        # Test writing with custom encoding
        result = operations.write_text("encoding_test.txt", "тест", encoding="utf-16")
        assert result.success is True
        assert (temp_dir / "encoding_test.txt").read_text(encoding="utf-16") == "тест"

        # Test with atomic=False
        result = operations.write_text("nonatomic.txt", "content", atomic=False)
        assert result.success is True
        assert (temp_dir / "nonatomic.txt").read_text() == "content"

        # Test with calculate_checksum=True
        result = operations.write_text(
            "checksum.txt", "content", calculate_checksum=True
        )
        assert result.success is True
        assert result.checksum is not None

    def test_write_binary(self, temp_dir: Path) -> None:
        """Test writing binary data to a file."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Test writing to a new file
        result = operations.write_binary("binary.bin", b"\x00\x01\x02\x03")
        assert result.success is True
        assert result.bytes_written == 4
        assert (temp_dir / "binary.bin").read_bytes() == b"\x00\x01\x02\x03"

        # Test with atomic=False
        result = operations.write_binary(
            "nonatomic.bin", b"\x04\x05\x06\x07", atomic=False
        )
        assert result.success is True
        assert (temp_dir / "nonatomic.bin").read_bytes() == b"\x04\x05\x06\x07"

        # Test with calculate_checksum=True
        result = operations.write_binary(
            "checksum.bin", b"\x08\x09\x0a\x0b", calculate_checksum=True
        )
        assert result.success is True
        assert result.checksum is not None

    def test_copy(self, temp_dir: Path) -> None:
        """Test copying a file."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Create a source file
        source_path = temp_dir / "source.txt"
        source_path.write_text("source content")

        # Test successful copy
        result = operations.copy("source.txt", "dest.txt")
        assert result.success is True
        assert (temp_dir / "dest.txt").exists()
        assert (temp_dir / "dest.txt").read_text() == "source content"

        # Test copy to existing file (should fail)
        result = operations.copy("source.txt", "dest.txt")
        assert result.success is False
        assert "already exists" in result.error

        # Test copy with overwrite
        result = operations.copy("source.txt", "dest.txt", overwrite=True)
        assert result.success is True

        # Test copy with non-existent source
        result = operations.copy("nonexistent.txt", "new_dest.txt")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_move(self, temp_dir: Path) -> None:
        """Test moving a file."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Create a source file
        source_path = temp_dir / "move_source.txt"
        source_path.write_text("move content")

        # Test successful move
        result = operations.move("move_source.txt", "move_dest.txt")
        assert result.success is True
        assert (temp_dir / "move_dest.txt").exists()
        assert not (temp_dir / "move_source.txt").exists()
        assert (temp_dir / "move_dest.txt").read_text() == "move content"

        # Create new source file
        source_path.write_text("new move content")

        # Test move to existing file (should fail)
        result = operations.move("move_source.txt", "move_dest.txt")
        assert result.success is False
        assert "already exists" in result.error

        # Test move with overwrite
        result = operations.move("move_source.txt", "move_dest.txt", overwrite=True)
        assert result.success is True
        assert (temp_dir / "move_dest.txt").read_text() == "new move content"

        # Test move with non-existent source
        result = operations.move("nonexistent.txt", "new_dest.txt")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_delete(self, temp_dir: Path) -> None:
        """Test deleting a file."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Create a file to delete
        file_path = temp_dir / "to_delete.txt"
        file_path.write_text("delete me")

        # Test successful delete
        result = operations.delete("to_delete.txt")
        assert result.success is True
        assert not file_path.exists()

        # Test deleting non-existent file (should succeed with missing_ok=True)
        result = operations.delete("to_delete.txt")
        assert result.success is True

        # Test deleting non-existent file with missing_ok=False
        result = operations.delete("to_delete.txt", missing_ok=False)
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_create_directory(self, temp_dir: Path) -> None:
        """Test creating a directory."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Test creating directory
        result = operations.create_directory("new_dir")
        assert result.success is True
        assert (temp_dir / "new_dir").is_dir()

        # Test creating existing directory (should succeed with exist_ok=True)
        result = operations.create_directory("new_dir")
        assert result.success is True

        # Test creating existing directory with exist_ok=False
        with patch("quackcore.fs.operations.ensure_directory") as mock_ensure_directory:
            mock_ensure_directory.side_effect = QuackFileExistsError(
                str(temp_dir / "new_dir")
            )
            result = operations.create_directory("new_dir", exist_ok=False)
            assert result.success is False
            assert "already exists" in result.error.lower()

    def test_get_file_info(self, temp_dir: Path) -> None:
        """Test getting file information."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Create a test file
        file_path = temp_dir / "info_test.txt"
        file_path.write_text("info content")

        # Create a test directory
        dir_path = temp_dir / "info_dir"
        dir_path.mkdir()

        # Test getting info for a file
        result = operations.get_file_info("info_test.txt")
        assert result.success is True
        assert result.exists is True
        assert result.is_file is True
        assert result.is_dir is False
        assert result.size > 0
        assert result.modified is not None

        # Test getting info for a directory
        result = operations.get_file_info("info_dir")
        assert result.success is True
        assert result.exists is True
        assert result.is_file is False
        assert result.is_dir is True

        # Test getting info for a non-existent file
        result = operations.get_file_info("nonexistent.txt")
        assert result.success is True  # Operation succeeded, but file doesn't exist
        assert result.exists is False

    def test_list_directory(self, temp_dir: Path) -> None:
        """Test listing directory contents."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Create some files and directories for testing
        (temp_dir / "list_file1.txt").write_text("content1")
        (temp_dir / "list_file2.txt").write_text("content2")
        (temp_dir / ".hidden_file").write_text("hidden")
        (temp_dir / "list_dir").mkdir()

        # Test listing with default parameters
        result = operations.list_directory(".")
        assert result.success is True
        assert result.exists is True
        assert result.is_empty is False
        assert len(result.files) >= 2  # At least our created files
        assert len(result.directories) >= 1  # At least our created directory
        assert any(f.name == "list_file1.txt" for f in result.files)
        assert any(f.name == "list_file2.txt" for f in result.files)
        assert any(d.name == "list_dir" for d in result.directories)

        # Test listing with include_hidden=True
        result = operations.list_directory(".", include_hidden=True)
        assert result.success is True
        assert any(f.name == ".hidden_file" for f in result.files)

        # Test listing with pattern
        result = operations.list_directory(".", pattern="list_*.txt")
        assert result.success is True
        assert len(result.files) == 2
        assert all(f.name.startswith("list_") for f in result.files)

        # Test listing non-existent directory
        result = operations.list_directory("nonexistent_dir")
        assert result.success is False
        assert result.exists is False

    def test_find_files(self, temp_dir: Path) -> None:
        """Test finding files matching a pattern."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Create some files and directories for testing
        (temp_dir / "find_file1.txt").write_text("content1")
        (temp_dir / "find_file2.txt").write_text("content2")
        (temp_dir / "find_doc.pdf").write_text("pdf content")
        (temp_dir / "find_dir").mkdir()
        (temp_dir / "find_dir" / "subfile.txt").write_text("sub content")

        # Test finding with pattern
        result = operations.find_files(".", "find_*.txt")
        assert result.success is True
        assert len(result.files) == 3  # Includes subfile.txt due to recursive=True
        assert any(f.name == "find_file1.txt" for f in result.files)
        assert any(f.name == "find_file2.txt" for f in result.files)
        assert any(f.name == "subfile.txt" for f in result.files)

        # Test finding without recursion
        result = operations.find_files(".", "find_*.txt", recursive=False)
        assert result.success is True
        assert len(result.files) == 2
        assert not any(f.name == "subfile.txt" for f in result.files)

        # Test finding directories
        result = operations.find_files(".", "*dir*")
        assert result.success is True
        assert len(result.directories) >= 1
        assert any(d.name == "find_dir" for d in result.directories)

        # Test finding with non-existent directory
        result = operations.find_files("nonexistent_dir", "*")
        assert result.success is False
        assert "directory does not exist" in result.error.lower()

    def test_read_yaml(self, temp_dir: Path) -> None:
        """Test reading YAML files."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Create a YAML file
        data = {"name": "Test", "values": [1, 2, 3], "nested": {"key": "value"}}
        yaml_file = temp_dir / "test.yaml"
        yaml_file.write_text(yaml.dump(data))

        # Test successful read
        result = operations.read_yaml("test.yaml")
        assert result.success is True
        assert result.data == data
        assert result.format == "yaml"

        # Test empty YAML file (should return empty dict)
        empty_yaml = temp_dir / "empty.yaml"
        empty_yaml.write_text("")
        result = operations.read_yaml("empty.yaml")
        assert result.success is True
        assert result.data == {}

        # Test reading invalid YAML
        invalid_yaml = temp_dir / "invalid.yaml"
        invalid_yaml.write_text("name: Test\ninvalid: : value")
        result = operations.read_yaml("invalid.yaml")
        assert result.success is False
        assert "yaml" in result.error.lower()

        # Test non-dictionary YAML
        list_yaml = temp_dir / "list.yaml"
        list_yaml.write_text("- item1\n- item2")
        result = operations.read_yaml("list.yaml")
        assert result.success is False
        assert "not a dictionary" in result.error.lower()

        # Test reading non-existent file
        result = operations.read_yaml("nonexistent.yaml")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_write_yaml(self, temp_dir: Path) -> None:
        """Test writing YAML files."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Test writing data
        data = {"name": "Test", "values": [1, 2, 3], "nested": {"key": "value"}}
        result = operations.write_yaml("write.yaml", data)
        assert result.success is True

        # Verify the written data
        result = operations.read_yaml("write.yaml")
        assert result.success is True
        assert result.data == data

        # Test writing with non-serializable data
        with patch("yaml.safe_dump") as mock_dump:
            mock_dump.side_effect = yaml.YAMLError("YAML error")
            result = operations.write_yaml("error.yaml", {"error": object()})
            assert result.success is False
            assert "yaml" in result.error.lower()

    def test_read_json(self, temp_dir: Path) -> None:
        """Test reading JSON files."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Create a JSON file
        data = {"name": "Test", "values": [1, 2, 3], "nested": {"key": "value"}}
        json_file = temp_dir / "test.json"
        json_file.write_text(json.dumps(data))

        # Test successful read
        result = operations.read_json("test.json")
        assert result.success is True
        assert result.data == data
        assert result.format == "json"

        # Test reading invalid JSON
        invalid_json = temp_dir / "invalid.json"
        invalid_json.write_text('{"name": "Test", "invalid": }')
        result = operations.read_json("invalid.json")
        assert result.success is False
        assert "json" in result.error.lower()

        # Test non-dictionary JSON
        list_json = temp_dir / "list.json"
        list_json.write_text("[1, 2, 3]")
        result = operations.read_json("list.json")
        assert result.success is False
        assert "not an object" in result.error.lower()

        # Test reading non-existent file
        result = operations.read_json("nonexistent.json")
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_write_json(self, temp_dir: Path) -> None:
        """Test writing JSON files."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Test writing data
        data = {"name": "Test", "values": [1, 2, 3], "nested": {"key": "value"}}
        result = operations.write_json("write.json", data)
        assert result.success is True

        # Verify the written data
        result = operations.read_json("write.json")
        assert result.success is True
        assert result.data == data

        # Test writing with indent
        result = operations.write_json("pretty.json", data, indent=4)
        assert result.success is True
        content = (temp_dir / "pretty.json").read_text()
        assert "    " in content  # Check for indentation

        # Test writing with non-serializable data
        with patch("json.dumps") as mock_dumps:
            mock_dumps.side_effect = TypeError("Type error")
            result = operations.write_json("error.json", {"error": object()})
            assert result.success is False
            assert "json" in result.error.lower()

    def test_error_handling(self, temp_dir: Path) -> None:
        """Test error handling in operations."""
        operations = FileSystemOperations(base_dir=temp_dir)

        # Test permission error
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = PermissionError("Permission denied")
            result = operations.read_text("permission.txt")
            assert result.success is False
            assert "permission denied" in result.error.lower()

        # Test IO error
        with patch("quackcore.fs.operations.atomic_write") as mock_atomic_write:
            mock_atomic_write.side_effect = QuackIOError("IO error")
            result = operations.write_text("io_error.txt", "content")
            assert result.success is False
            assert "io error" in result.error.lower()

        # Test unexpected error
        with patch("builtins.open") as mock_open:
            mock_open.side_effect = RuntimeError("Unexpected error")
            result = operations.read_text("unexpected.txt")
            assert result.success is False
            assert "unexpected error" in result.error.lower()
