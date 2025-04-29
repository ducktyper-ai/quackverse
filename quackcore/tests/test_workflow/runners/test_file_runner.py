# quackcore/tests/test_workflow/runners/test_file_runner.py
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from quackcore.workflow.results import FinalResult, InputResult
from quackcore.workflow.runners.file_runner import FileWorkflowRunner, WorkflowError


class StubFS:
    def __init__(self):
        self.reads = []
        self.should_fail = False  # Flag to control write failure behavior

    def read_text(self, path):
        if "missing" in path:
            return SimpleNamespace(success=False,
                                   error="[Errno 2] No such file or directory",
                                   content=None)
        self.reads.append(path)
        return SimpleNamespace(success=True, content="ok")

    def write_json(self, path, data, indent=None):
        if self.should_fail:
            return SimpleNamespace(success=False, error="boom")
        return SimpleNamespace(success=True, path=path)

    def create_directory(self, path, exist_ok=False):
        return SimpleNamespace(success=True, path=path)


# Create a global instance for use in patching
stub_fs = StubFS()


@pytest.fixture
def patch_fs_service():
    """
    Returns the StubFS instance used for patching.
    """
    return stub_fs


# Apply patching to all functions at the module level
@pytest.fixture(autouse=True)
def apply_patching():
    """
    Patch all filesystem functions at the module level before any tests run.
    """
    # The key is to patch both the standalone functions AND get_service
    with patch('quackcore.fs.service.get_service', return_value=stub_fs), \
            patch('quackcore.fs.service.standalone.read_text', stub_fs.read_text), \
            patch('quackcore.fs.service.standalone.write_json', stub_fs.write_json), \
            patch('quackcore.fs.service.standalone.create_directory',
                  stub_fs.create_directory):
        # Reset the stub state before each test
        stub_fs.reads = []
        stub_fs.should_fail = False

        yield


def dummy_processor(content, options):
    if options.get("fail_proc"):
        raise RuntimeError("bad proc")
    return True, {"got": content}, None


def test_remote_download(monkeypatch, tmp_path: Path, patch_fs_service):
    # write a dummy file
    f = tmp_path / "r.txt"
    f.write_text("x")

    class Remote:
        def __init__(self): self.dl = False

        def is_remote(self, s): return True

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
    runner = FileWorkflowRunner(processor=dummy_processor)
    bad = tmp_path / "missing.txt"
    res = runner.run(str(bad))
    assert not res.success
    assert res.metadata["error_type"] == "WorkflowError"
    # Check for 'No such file or directory' instead of 'not found'
    assert "No such file or directory" in res.metadata["error_message"]


def test_processor_exception_captured(tmp_path: Path, patch_fs_service):
    def p(content, opts): raise ValueError("fail!")

    f = tmp_path / "f.txt";
    f.write_text("x")
    runner = FileWorkflowRunner(processor=p)
    res = runner.run(str(f), options={"output_dir": str(tmp_path)})
    assert not res.success
    assert "fail!" in res.metadata["processor_error"]


def test_use_temp_dir(tmp_path: Path, patch_fs_service):
    f = tmp_path / "u.txt";
    f.write_text("hi")
    runner = FileWorkflowRunner(processor=dummy_processor)
    res = runner.run(str(f), options={"use_temp_dir": True})
    assert res.success
    assert res.metadata["output_format"] == "json"
    assert res.metadata["output_file"].endswith("u.json")


def test_custom_writer(monkeypatch, tmp_path: Path, patch_fs_service):
    class W:
        def write(self, res, inp, opts):
            return FinalResult(success=True, result_path=inp.with_suffix(".X"),
                               metadata={"ok": True})

    f = tmp_path / "c.txt";
    f.write_text("x")
    runner = FileWorkflowRunner(processor=dummy_processor, output_writer=W())
    res = runner.run(str(f), options={})
    assert res.success
    assert res.result_path == f.with_suffix(".X")
    assert res.metadata["ok"] is True


def test_write_error_propagates(tmp_path: Path, patch_fs_service):
    # make write_json fail inside default branch
    stub = patch_fs_service
    # Set the flag to make writes fail
    stub.should_fail = True

    f = tmp_path / "e.txt";
    f.write_text("x")
    runner = FileWorkflowRunner(processor=dummy_processor)
    res = runner.run(str(f), options={})

    # Check for the error message instead of success flag
    assert not res.success
    assert "error_type" in res.metadata
    assert "boom" in res.metadata.get("error_message", "")