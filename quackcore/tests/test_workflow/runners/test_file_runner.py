# quackcore/tests/test_workflow/runners/test_file_runner.py
"""
Tests for FileWorkflowRunner.

This module ensures the file workflow runner correctly handles file processing.
"""

import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from quackcore.workflow.results import FinalResult, InputResult
from quackcore.workflow.runners.file_runner import FileWorkflowRunner


# Stub for file system service
class StubFS:
    def __init__(self):
        self.should_fail = False
        self.file_exists = True
        self.last_read_type = None

    def get_file_info(self, path):
        return SimpleNamespace(
            success=True,
            exists=self.file_exists,
            size=100,
            modified=123456789
        )

    def read_text(self, path, encoding=None):
        self.last_read_type = 'text'
        if self.should_fail:
            return SimpleNamespace(success=False, error="Simulated read error")
        return SimpleNamespace(success=True, content="test content")

    def read_binary(self, path):
        self.last_read_type = 'binary'
        if self.should_fail:
            return SimpleNamespace(success=False, error="Simulated read error")
        return SimpleNamespace(success=True, content=b"test content")

    def write_json(self, path, data, indent=None):
        if self.should_fail:
            return SimpleNamespace(success=False, error="Simulated write error")
        return SimpleNamespace(success=True, bytes_written=100, path=path)

    def create_directory(self, path, exist_ok=False):
        if self.should_fail:
            return SimpleNamespace(success=False,
                                   error="Simulated directory creation error")
        return SimpleNamespace(success=True, path=path)

    def join_path(self, *parts):
        return SimpleNamespace(success=True, data=os.path.join(*parts))

    def split_path(self, path):
        return SimpleNamespace(success=True, data=path.split(os.sep))

    def get_extension(self, path):
        if not isinstance(path, str):
            path = str(path)

        if '.' not in path:
            return SimpleNamespace(success=True, data="")

        return SimpleNamespace(success=True, data=path.split('.')[-1])


@pytest.fixture
def patch_fs_service(monkeypatch):
    """Patch the fs.service.standalone with our stub."""
    stub = StubFS()

    # Make sure the module exists
    if 'quackcore.fs.service' not in sys.modules:
        import types

        if 'quackcore' not in sys.modules:
            quackcore_mod = types.ModuleType('quackcore')
            sys.modules['quackcore'] = quackcore_mod

        if 'quackcore.fs' not in sys.modules:
            fs_mod = types.ModuleType('quackcore.fs')
            sys.modules['quackcore.fs'] = fs_mod

        service_mod = types.ModuleType('quackcore.fs.service')
        sys.modules['quackcore.fs.service'] = service_mod

    # Set our stub as the standalone service
    import quackcore.fs.service
    quackcore.fs.service.standalone = stub
    quackcore.fs.service.get_service = lambda: stub

    return stub


# Simple processor function for testing
def dummy_processor(content, options=None):
    """Dummy processor that simply returns the content."""
    if options and options.get("fail_proc"):
        raise ValueError("Simulated processor error")
    return True, {"processed": True, "content": content, "options": options}, None


def test_remote_download(monkeypatch, tmp_path: Path, patch_fs_service):
    """Test handling of remote files."""
    # Write a dummy file
    f = tmp_path / "r.txt"
    f.write_text("x")

    class Remote:
        def __init__(self):
            self.dl = False

        def is_remote(self, s):
            return True

        def download(self, s):
            self.dl = True
            return InputResult(path=f, metadata={"foo": "bar"})

    remote = Remote()
    runner = FileWorkflowRunner(processor=dummy_processor, remote_handler=remote)
    res = runner.run(str(f), options={"output_dir": str(tmp_path)})
    assert res.success
    assert remote.dl
    assert res.metadata["input_type"] == "remote"


def test_read_failure_returns_error(tmp_path: Path, patch_fs_service):
    """Test that a failure to read a file results in an error."""
    # Configure fs stub to fail reads
    patch_fs_service.should_fail = True
    patch_fs_service.file_exists = False

    runner = FileWorkflowRunner(processor=dummy_processor)
    bad = tmp_path / "missing.txt"
    res = runner.run(str(bad))

    assert not res.success
    assert "error_type" in res.metadata
    assert "failed to read" in res.metadata.get("error_message", "").lower()


def test_file_exists_but_unreadable(tmp_path: Path, patch_fs_service):
    """Test behavior when a file exists but is unreadable."""
    # File exists but read fails
    patch_fs_service.file_exists = True
    patch_fs_service.should_fail = True

    runner = FileWorkflowRunner(processor=dummy_processor)
    bad = tmp_path / "unreadable.txt"
    res = runner.run(str(bad))

    assert not res.success
    assert "error_type" in res.metadata
    assert "failed to read" in res.metadata.get("error_message", "").lower()


def test_processor_error_handling(tmp_path: Path, patch_fs_service):
    """Test handling of errors from the processor function."""
    # Ensure the file exists and is readable
    patch_fs_service.file_exists = True
    patch_fs_service.should_fail = False

    # Create a file
    f = tmp_path / "test.txt"
    f.write_text("testing")

    # Run with options that trigger failure in the processor
    runner = FileWorkflowRunner(processor=dummy_processor)
    res = runner.run(str(f), options={"fail_proc": True})

    assert not res.success
    assert "processor_error" in res.metadata
    assert "simulated processor error" in res.metadata.get("processor_error",
                                                           "").lower()


def test_write_error_propagates(tmp_path: Path, patch_fs_service):
    """Test that errors during output writing are properly handled."""
    # Set up the file to exist and be readable
    patch_fs_service.file_exists = True
    patch_fs_service.should_fail = False

    # Create a file
    f = tmp_path / "e.txt"
    f.write_text("x")

    # Configure write to fail
    runner = FileWorkflowRunner(processor=dummy_processor)

    # Before running test, configure write to fail
    patch_fs_service.should_fail = True

    res = runner.run(str(f), options={})

    assert not res.success
    assert "error_type" in res.metadata
    assert "error_message" in res.metadata
    assert "simulated write error" in res.metadata.get("error_message", "").lower()


def test_directory_creation_failure(tmp_path: Path, patch_fs_service):
    """Test handling of directory creation failure."""
    # Ensure the file exists and is readable
    patch_fs_service.file_exists = True
    patch_fs_service.should_fail = False

    # Create a file
    f = tmp_path / "test.txt"
    f.write_text("testing")

    # Make directory creation fail only
    runner = FileWorkflowRunner(processor=dummy_processor)

    # Patch directory creation to fail
    with patch('quackcore.fs.service.standalone.create_directory',
               return_value=SimpleNamespace(success=False,
                                            error="Directory creation failed")):
        res = runner.run(str(f), options={"output_dir": "/nonexistent"})

    assert not res.success
    assert "error_type" in res.metadata
    assert "directory creation failed" in res.metadata.get("error_message", "").lower()


def test_use_temp_dir(tmp_path: Path, patch_fs_service):
    """Test using a temporary directory for output."""
    # Ensure the file exists and is readable
    patch_fs_service.file_exists = True
    patch_fs_service.should_fail = False

    # Create a file
    f = tmp_path / "u.txt"
    f.write_text("hi")

    runner = FileWorkflowRunner(processor=dummy_processor)
    res = runner.run(str(f), options={"use_temp_dir": True})

    assert res.success
    assert res.metadata["output_format"] == "json"
    assert res.metadata["output_file"].endswith("u.json")


def test_custom_writer(monkeypatch, tmp_path: Path, patch_fs_service):
    """Test using a custom output writer."""

    class CustomWriter:
        def write(self, result, input_path, options):
            return FinalResult(
                success=True,
                result_path=Path(input_path).with_suffix(".X"),
                metadata={"ok": True}
            )

    # Ensure the file exists and is readable
    patch_fs_service.file_exists = True
    patch_fs_service.should_fail = False

    # Create a file
    f = tmp_path / "c.txt"
    f.write_text("x")

    runner = FileWorkflowRunner(processor=dummy_processor, output_writer=CustomWriter())
    res = runner.run(str(f), options={})

    assert res.success
    assert res.result_path == f.with_suffix(".X")
    assert res.metadata["ok"] is True


def test_binary_file_handling(tmp_path: Path, patch_fs_service):
    """Test proper handling of binary files."""
    # Ensure the file exists and is readable
    patch_fs_service.file_exists = True
    patch_fs_service.should_fail = False

    # Create a file with binary extension
    f = tmp_path / "test.bin"
    f.write_bytes(b"\x00\x01\x02\x03")

    # Customize extension check to report binary
    patch_fs_service.get_extension = lambda path: SimpleNamespace(
        success=True, data="bin"
    )

    runner = FileWorkflowRunner(processor=dummy_processor)
    res = runner.run(str(f))

    # Runner should succeed with binary content
    assert res.success

    # Verify binary read was attempted by checking if the processor got binary data
    assert patch_fs_service.last_read_type == 'binary'
