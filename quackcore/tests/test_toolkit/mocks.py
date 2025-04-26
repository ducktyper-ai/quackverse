# In test_toolkit/mocks.py
from unittest.mock import MagicMock, patch

from quackcore.toolkit import BaseQuackToolPlugin


def create_mock_fs():
    """Create a mock filesystem service for testing."""
    mock_fs = MagicMock()
    # Configure mock responses here
    return mock_fs


# In test_toolkit/test_base.py
from unittest.mock import patch

from .mocks import create_mock_fs


class DummyQuackTool(BaseQuackToolPlugin):
    """Test implementation of BaseQuackToolPlugin."""

    def __init__(self):
        # Patch filesystem service before initialization
        with patch('quackcore.fs.service.get_service', return_value=create_mock_fs()):
            super().__init__("dummy_tool", "1.0.0")

    # Rest of implementation