# quackcore/tests/test_integrations/pandoc/mocks.py
import os
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


# Fixtures for monkeypatching filesystem service
@pytest.fixture(autouse=True)
def fs_stub(monkeypatch):
    """
    Stub out the quackcore.fs.service.standalone methods for file operations.
    """
    import sys
    import types

    # Create a module structure if it doesn't exist
    if 'quackcore.fs.service' not in sys.modules:
        # Create the module hierarchy
        if 'quackcore' not in sys.modules:
            quackcore_mod = types.ModuleType('quackcore')
            sys.modules['quackcore'] = quackcore_mod

        if 'quackcore.fs' not in sys.modules:
            fs_mod = types.ModuleType('quackcore.fs')
            sys.modules['quackcore.fs'] = fs_mod

        service_mod = types.ModuleType('quackcore.fs.service')
        sys.modules['quackcore.fs.service'] = service_mod

    # Create the stub with all necessary methods
    stub = SimpleNamespace()
    # Default get_file_info returns success, exists, size, modified
    stub.get_file_info = lambda path: SimpleNamespace(
        success=True, exists=True, size=100, modified=time.time(), is_dir=False
    )
    stub.create_directory = lambda path, exist_ok: SimpleNamespace(success=True)
    # match os.path.join signature: first arg required, then *paths
    stub.join_path = lambda a, *parts: os.path.join(a, *parts)
    stub.split_path = lambda path: path.split(os.sep)
    stub.write_text = lambda path, content, encoding=None: SimpleNamespace(
        success=True, bytes_written=len(content)
    )
    stub.read_text = lambda path, encoding=None: SimpleNamespace(
        success=True, content="<html><body><h1>Title</h1><p>Content</p></body></html>"
        if path.endswith('.html') else "# Title\n\nContent"
    )
    stub.get_extension = lambda path: SimpleNamespace(data=path.split('.')[-1])
    stub.get_path_info = lambda path: SimpleNamespace(success=True)
    stub.is_valid_path = lambda path: True
    stub.normalize_path = lambda p: SimpleNamespace(success=True,
                                                    path=os.path.abspath(p))
    stub.normalize_path_with_info = stub.normalize_path
    stub.get_file_size_str = lambda size: f"{size}B"
    stub.find_files = lambda dir_path, pattern, recursive=False: SimpleNamespace(
        success=True, files=["file1.html", "file2.html"]
    )

    # Set the standalone attribute directly in the sys.modules
    sys.modules['quackcore.fs.service'].standalone = stub

    return stub


# Fixture for mocking pypandoc
@pytest.fixture
def mock_pypandoc(monkeypatch):
    """
    Create a mock pypandoc module for testing.
    """
    mock = MagicMock()
    mock.get_pandoc_version.return_value = "2.11.0"
    mock.convert_file.return_value = "# Converted Content\n\nThis is markdown."
    monkeypatch.setitem(pytest.importorskip("sys").modules, 'pypandoc', mock)
    return mock


# Fixture for path service
@pytest.fixture
def mock_paths_service(monkeypatch):
    """
    Mock the paths service for resolving project paths.
    """
    mock = MagicMock()
    mock.resolve_project_path = lambda path: path  # Just return the path unchanged

    # Create a temp module if it doesn't exist
    if 'quackcore.paths' not in pytest.importorskip("sys").modules:
        import types
        temp_module = types.ModuleType('quackcore.paths')
        pytest.importorskip("sys").modules['quackcore.paths'] = temp_module
        temp_module.service = mock
    else:
        monkeypatch.setattr('quackcore.paths.service', mock)

    return mock


# Fixture for bs4
@pytest.fixture
def mock_bs4(monkeypatch):
    """
    Mock BeautifulSoup for HTML validation.
    """
    mock_soup = MagicMock()
    mock_soup.find.return_value = True  # Default to finding body tag
    mock_soup.find_all.return_value = []  # No links by default

    mock_bs = MagicMock()
    mock_bs.BeautifulSoup.return_value = mock_soup

    monkeypatch.setitem(pytest.importorskip("sys").modules, 'bs4', mock_bs)
    return mock_bs


# Fixture for docx
@pytest.fixture
def mock_docx(monkeypatch):
    """
    Mock python-docx for DOCX validation.
    """
    mock_para = MagicMock()
    mock_para.style.name = "Heading 1"

    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_para]

    mock_docx_module = MagicMock()
    mock_docx_module.Document.return_value = mock_doc

    monkeypatch.setitem(pytest.importorskip("sys").modules, 'docx', mock_docx_module)
    return mock_docx_module
