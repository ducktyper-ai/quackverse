# quackcore/tests/test_workflow/runners/test_file_runner.py
from pathlib import Path
from types import SimpleNamespace

import pytest

import quackcore.fs.service as fs_service
from quackcore.workflow.results import FinalResult, InputResult
from quackcore.workflow.runners.file_runner import FileWorkflowRunner


class StubFS:
    def __init__(self):
        self.reads = []
    def read_text(self, path):
        if "missing" in path:
            return SimpleNamespace(success=False, error="not found", content=None)
        self.reads.append(path)
        return SimpleNamespace(success=True, content="ok")
    def write_json(self, path, data, indent=None):
        return SimpleNamespace(success=True, path=path)
    def create_directory(self, path, exist_ok=False):
        pass

@pytest.fixture(autouse=True)
def patch_fs(monkeypatch):
    stub = StubFS()
    monkeypatch.setattr(fs_service, "get_service", lambda: stub)
    return stub


def dummy_processor(content, options):
    if options.get("fail_proc"):
        raise RuntimeError("bad proc")
    return {"got": content}


def test_remote_download(monkeypatch, tmp_path: Path, patch_fs):
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


def test_read_failure_returns_error(tmp_path: Path, patch_fs):
    runner = FileWorkflowRunner(processor=dummy_processor)
    bad = tmp_path / "missing.txt"
    res = runner.run(str(bad))
    assert not res.success
    assert res.metadata["error_type"] == "WorkflowError"
    assert "not found" in res.metadata["error_message"]


def test_processor_exception_captured(tmp_path: Path, patch_fs):
    def p(content, opts): raise ValueError("fail!")
    f = tmp_path / "f.txt"; f.write_text("x")
    runner = FileWorkflowRunner(processor=p)
    res = runner.run(str(f), options={"output_dir": str(tmp_path)})
    assert not res.success
    assert "fail!" in res.metadata["processor_error"]


def test_use_temp_dir(tmp_path: Path, patch_fs):
    f = tmp_path / "u.txt"; f.write_text("hi")
    runner = FileWorkflowRunner(processor=dummy_processor)
    res = runner.run(str(f), options={"use_temp_dir": True})
    assert res.success
    assert res.metadata["output_format"] == "json"
    assert res.metadata["output_file"].endswith("u.json")


def test_custom_writer(monkeypatch, tmp_path: Path, patch_fs):
    class W:
        def write(self, res, inp, opts):
            return FinalResult(success=True, result_path=inp.with_suffix(".X"), metadata={"ok": True})
    f = tmp_path / "c.txt"; f.write_text("x")
    runner = FileWorkflowRunner(processor=dummy_processor, output_writer=W())
    res = runner.run(str(f), options={})
    assert res.success
    assert res.result_path == f.with_suffix(".X")
    assert res.metadata["ok"] is True


def test_write_error_propagates(tmp_path: Path, patch_fs):
    # make write_json fail inside default branch
    stub = patch_fs
    stub.write_json = lambda *a, **k: SimpleNamespace(success=False, error="boom")
    f = tmp_path / "e.txt"; f.write_text("x")
    runner = FileWorkflowRunner(processor=dummy_processor)
    res = runner.run(str(f), options={})
    assert not res.success
    assert res.metadata["error_type"] == "WorkflowError"
    assert "boom" in res.metadata["error_message"]
