# tests/conftest.py
"""
Shared fixtures for QuackCore tests.
"""

import shutil
import tempfile
from collections.abc import Generator  # Changed from typing to collections.abc
from pathlib import Path

import pytest
from _pytest.monkeypatch import MonkeyPatch

from quackcore.config.models import QuackConfig
from quackcore.plugins.protocols import QuackPluginProtocol


@pytest.fixture
def temp_dir() -> Generator[Path]:  # Removed unnecessary None, None
    """Create a temporary directory for tests."""
    tmp_dir = Path(tempfile.mkdtemp())
    try:
        yield tmp_dir
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


@pytest.fixture
def test_file(temp_dir: Path) -> Generator[Path]:  # Removed unnecessary None, None
    """Create a test file with content."""
    file_path = temp_dir / "test_file.txt"
    with open(file_path, "w") as f:
        f.write("test content")
    yield file_path


@pytest.fixture
def test_binary_file(
    temp_dir: Path,
) -> Generator[Path]:  # Removed unnecessary None, None
    """Create a binary test file."""
    file_path = temp_dir / "test_binary_file.bin"
    with open(file_path, "wb") as f:
        f.write(b"\x00\x01\x02\x03")
    yield file_path


@pytest.fixture
def sample_config(temp_dir: Path) -> QuackConfig:  # Using temp_dir fixture for security
    """Create a sample configuration."""
    return QuackConfig(
        general={
            "project_name": "TestProject",
            "environment": "test",
            "debug": True,
        },
        paths={
            "base_dir": str(temp_dir),  # Using temp_dir instead of hardcoded path
            "output_dir": str(
                temp_dir / "output"
            ),  # Using temp_dir instead of hardcoded path
        },
        logging={
            "level": "DEBUG",
            "console": True,
        },
    )


@pytest.fixture
def mock_env_vars(monkeypatch: MonkeyPatch) -> None:
    """Set up environment variables for testing."""
    monkeypatch.setenv("QUACK_ENV", "test")
    monkeypatch.setenv("QUACK_GENERAL__DEBUG", "true")
    monkeypatch.setenv("QUACK_LOGGING__LEVEL", "DEBUG")


@pytest.fixture
def mock_project_structure(temp_dir: Path) -> Path:
    """Create a mock project structure for testing."""
    # Create project root with marker files
    project_root = temp_dir / "test_project"
    project_root.mkdir()
    (project_root / "pyproject.toml").touch()

    # Create src directory with module structure
    src_dir = project_root / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").touch()

    # Create module directory
    module_dir = src_dir / "test_module"
    module_dir.mkdir()
    (module_dir / "__init__.py").touch()

    # Create test file with some content
    test_module_file = module_dir / "test_file.py"
    test_module_file.write_text("def test_function():\n    return True")

    # Create other standard directories
    (project_root / "tests").mkdir()
    (project_root / "docs").mkdir()
    (project_root / "output").mkdir()
    (project_root / "config").mkdir()

    # Create a config file
    config_file = project_root / "config" / "default.yaml"
    config_file.write_text("general:\n  project_name: TestProject\n")

    return project_root


class MockPlugin(QuackPluginProtocol):
    """Mock plugin for testing."""

    @property
    def name(self) -> str:
        return "mock_plugin"


@pytest.fixture
def mock_plugin() -> MockPlugin:
    """Create a mock plugin for testing."""
    return MockPlugin()
