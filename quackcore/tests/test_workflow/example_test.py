# Example Test (for reference)
from pathlib import Path
from typing import Any

from quackcore.workflow.runners.file_runner import FileWorkflowRunner


def dummy_processor(content: str, options: dict[str, Any]) -> tuple[bool, dict[str, int], str]:
    if options.get("simulate_failure", False):
        return False, {}, "Simulated processor failure"
    return True, {"length": len(content)}, ""

def test_file_runner_with_local_file(tmp_path: Path) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    runner = FileWorkflowRunner(processor=dummy_processor)
    result = runner.run(str(test_file), options={"output_dir": str(tmp_path)})

    assert result.success is True
    assert result.result_path and result.result_path.exists()
    assert "input_file" in result.metadata
    assert "output_file" in result.metadata

def test_runner_returns_failure_on_missing_file(tmp_path: Path) -> None:
    runner = FileWorkflowRunner(processor=dummy_processor)
    bad_file = tmp_path / "missing.txt"
    result = runner.run(str(bad_file))

    assert result.success is False
    assert "error_type" in result.metadata
    assert "error_message" in result.metadata

def test_runner_with_dry_run_option(tmp_path: Path) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    runner = FileWorkflowRunner(processor=dummy_processor)
    result = runner.run(str(test_file), options={"dry_run": True})

    assert result.success is True
    assert result.result_path is None
    assert result.metadata.get("dry_run") is True

def test_runner_with_processor_failure(tmp_path: Path) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_text("hello world")

    runner = FileWorkflowRunner(processor=dummy_processor)
    result = runner.run(str(test_file), options={
        "output_dir": str(tmp_path),
        "simulate_failure": True
    })

    assert result.success is False
    assert "processor_error" in result.metadata
