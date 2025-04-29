# quackcore/tests/test_workflow/mixins/test_save_output_mixin.py
from pathlib import Path
from types import SimpleNamespace

import pytest

import quackcore.fs.service as fs_service
from quackcore.workflow.mixins.save_output_mixin import SaveOutputMixin


class StubFS:
    def __init__(self):
        self.storage = {}

    def write_json(self, path, data, indent=None):
        self.storage[path] = data
        return SimpleNamespace(success=True, path=path)

    def write_text(self, path, data):
        self.storage[path] = data
        return SimpleNamespace(success=True, path=path)

    def create_directory(self, path, exist_ok=False):
        pass


@pytest.fixture(autouse=True)
def patch_fs(monkeypatch):
    stub = StubFS()
    monkeypatch.setattr(fs_service, "get_service", lambda: stub)
    return stub


class Dummy(SaveOutputMixin):
    pass


def test_supported_formats(dummy=Dummy()):
    fmts = dummy.supported_formats
    assert set(fmts) >= {"json", "yaml", "csv", "txt"}


def test_save_json_infer(tmp_path: Path, patch_fs):
    dummy = Dummy()
    data = {"z": 9}
    out = dummy.save_output(data, tmp_path / "out")
    assert out == (tmp_path / "out.json")
    # storage recorded
    assert patch_fs.storage[out] == data


def test_save_yaml_explicit(tmp_path: Path, patch_fs):
    dummy = Dummy()
    data = {"y": 7}
    out = dummy.save_output(data, tmp_path / "o.yaml", format="yaml")
    assert out == (tmp_path / "o.yaml")
    assert patch_fs.storage[out] == data


def test_save_csv_and_errors(tmp_path: Path, patch_fs):
    dummy = Dummy()
    good = [{"a": 1}, {"a": 2}]
    path = tmp_path / "t.csv"
    out = dummy.save_output(good, path)
    txt = patch_fs.storage[out]
    assert "a" in txt and "1" in txt
    with pytest.raises(ValueError):
        dummy.save_output("notalist", tmp_path / "bad.csv")


def test_save_txt(tmp_path: Path, patch_fs):
    dummy = Dummy()
    out = dummy.save_output("hello", tmp_path / "f.txt")
    assert out == tmp_path / "f.txt"
    assert patch_fs.storage[out] == "hello"


def test_with_timestamp(monkeypatch):
    dummy = Dummy()
    # freeze datetime.now
    fake = "20220101123000"
    class FakeDT:
        @classmethod
        def now(cls, tz):
            class D:
                def strftime(self, fmt): return fake
            return D()
    monkeypatch.setattr("quackcore.workflow.mixins.save_output_mixin.datetime", FakeDT)
    ts = dummy.with_timestamp("f.txt")
    assert ts.name == f"f_{fake}.txt"


def test_register_custom_writer(tmp_path: Path, patch_fs):
    dummy = Dummy()
    class MDWriter:
        def write_output(self, data, path):
            return str(path) + ".md"
    dummy.register_output_writer("md", MDWriter())
    assert "md" in dummy.supported_formats
    got = dummy.save_output({"m": 1}, tmp_path / "D.md", format="md")
    assert got.name.endswith(".md.md")
