# quackcore/tests/test_workflow/mixins/test_output_writer.py
from pathlib import Path
from types import SimpleNamespace

import pytest

import quackcore.fs.service as fs_service
from quackcore.workflow.mixins.output_writer import DefaultOutputWriter
from quackcore.workflow.results import FinalResult, OutputResult
from quackcore.workflow.runners.file_runner import WorkflowError


class StubFS:
    def __init__(self):
        self.created = []
        self.json_calls = []
        self.txt_calls = []

    def create_directory(self, path, exist_ok: bool = False):
        self.created.append((path, exist_ok))

    def write_json(self, path, data, indent=None):
        self.json_calls.append((path, data, indent))
        return SimpleNamespace(success=True, error=None)

    def write_text(self, path, data):
        self.txt_calls.append((path, data))
        return SimpleNamespace(success=True, error=None)


@pytest.fixture(autouse=True)
def patch_get_service(monkeypatch):
    stub = StubFS()
    monkeypatch.setattr(fs_service, "get_service", lambda: stub)
    return stub


def test_write_dict_json(tmp_path: Path, patch_get_service):
    writer = DefaultOutputWriter()
    res = OutputResult(success=True, content={"a": 1})
    out = writer.write(res, tmp_path / "inp.txt", {"output_dir": str(tmp_path)})
    assert isinstance(out, FinalResult)
    assert out.success
    assert out.result_path == tmp_path / "inp.json"
    md = out.metadata
    assert "input_file" in md and md["input_file"].endswith("inp.txt")
    assert "output_file" in md and md["output_file"].endswith("inp.json")
    assert md["output_format"] == "json"
    assert md["output_size"] == len(str({"a": 1}))
    assert patch_get_service.json_calls


def test_write_plain_text(tmp_path: Path, patch_get_service):
    writer = DefaultOutputWriter()
    res = OutputResult(success=True, content="hello")
    out = writer.write(res, tmp_path / "foo.txt", {"output_dir": str(tmp_path)})
    assert out.success
    assert out.result_path == tmp_path / "foo.txt"
    assert out.metadata["output_format"] == "text"
    assert patch_get_service.txt_calls


def test_write_failure_raises(monkeypatch, tmp_path: Path, patch_get_service):
    stub = patch_get_service
    # make write_json fail
    stub.write_json = lambda *args, **kwargs: SimpleNamespace(success=False, error="fail")
    writer = DefaultOutputWriter()
    with pytest.raises(WorkflowError) as ei:
        writer.write(OutputResult(success=True, content={"x": 2}), tmp_path / "a.txt", {"output_dir": str(tmp_path)})
    assert "fail" in str(ei.value)
