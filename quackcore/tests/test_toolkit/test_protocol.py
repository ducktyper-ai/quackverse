# quackcore/tests/test_toolkit/test_protocol.py
"""
Tests for the QuackToolPluginProtocol.
"""

import unittest
from typing import Any
from unittest.mock import MagicMock

from quackcore.integrations.core import IntegrationResult
from quackcore.plugins.protocols import QuackPluginMetadata
from quackcore.toolkit.protocol import QuackToolPluginProtocol


class TestQuackToolPluginProtocol(unittest.TestCase):
    """
    Test cases for QuackToolPluginProtocol.
    """

    def test_protocol_implementation(self) -> None:
        """
        Test that a class implementing all required methods passes protocol check.
        """
        # Create a mock class that implements all protocol methods
        class MockToolImplementation:
            @property
            def name(self) -> str:
                return "mock_tool"

            @property
            def version(self) -> str:
                return "1.0.0"

            @property
            def logger(self) -> MagicMock:
                return MagicMock()

            def get_metadata(self) -> QuackPluginMetadata:
                return QuackPluginMetadata(
                    name="mock_tool",
                    version="1.0.0",
                    description="Mock tool for testing"
                )

            def initialize(self) -> IntegrationResult:
                return IntegrationResult.success_result(
                    message="Initialized successfully"
                )

            def is_available(self) -> bool:
                return True

            def process_file(
                    self,
                    file_path: str,
                    output_path: str | None = None,
                    options: dict[str, Any] | None = None
            ) -> IntegrationResult:
                return IntegrationResult.success_result(
                    message="File processed successfully"
                )

        # Create an instance of the mock implementation
        mock_tool = MockToolImplementation()

        # Verify it can be used as a QuackToolPluginProtocol
        # This will raise a TypeError if the protocol is not properly implemented
        tool: QuackToolPluginProtocol = mock_tool  # type: ignore

        # Test basic properties to ensure they work as expected
        self.assertEqual(tool.name, "mock_tool")
        self.assertEqual(tool.version, "1.0.0")
        self.assertIsNotNone(tool.logger)


if __name__ == "__main__":
    unittest.main()
