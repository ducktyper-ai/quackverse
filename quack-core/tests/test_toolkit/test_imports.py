# quack-core/tests/test_toolkit/test_imports.py
"""
Tests for toolkit imports.

This module tests that all expected imports from the toolkit
package are available and functioning correctly.
"""

import unittest
from types import ModuleType
from typing import Any
from unittest.mock import patch

# Import the main package
import quack_core.toolkit
from quack_core.toolkit.base import BaseQuackToolPlugin
from quack_core.toolkit.mixins.env_init import ToolEnvInitializerMixin
from quack_core.toolkit.mixins.integration_enabled import IntegrationEnabledMixin
from quack_core.toolkit.mixins.lifecycle import QuackToolLifecycleMixin
from quack_core.toolkit.mixins.output_handler import OutputFormatMixin

# Import components directly to avoid circular imports
from quack_core.toolkit.protocol import QuackToolPluginProtocol


class TestToolkitImports(unittest.TestCase):
    """
    Test cases for toolkit imports.
    """

    def test_base_imports(self) -> None:
        """
        Test that all expected classes and modules are imported.
        """
        # Check that the BaseQuackToolPlugin class is available
        self.assertTrue(hasattr(quack_core.toolkit, "BaseQuackToolPlugin"))
        self.assertTrue(callable(quack_core.toolkit.BaseQuackToolPlugin))

        # Check that the protocol is available
        self.assertTrue(hasattr(quack_core.toolkit, "QuackToolPluginProtocol"))

        # Check that all mixins are available
        self.assertTrue(hasattr(quack_core.toolkit, "IntegrationEnabledMixin"))
        self.assertTrue(hasattr(quack_core.toolkit, "OutputFormatMixin"))
        self.assertTrue(hasattr(quack_core.toolkit, "ToolEnvInitializerMixin"))
        self.assertTrue(hasattr(quack_core.toolkit, "QuackToolLifecycleMixin"))

    def test_mixin_compatibility(self) -> None:
        """
        Test that mixins can be combined with the base class.
        """
        # Create a patch for get_service to avoid filesystem issues
        with patch('quack-core.fs.service.get_service') as mock_get_service, \
             patch('os.getcwd') as mock_getcwd:

            # Configure the mock
            mock_fs = mock_get_service.return_value
            mock_fs.create_temp_directory.return_value.success = True
            mock_fs.create_temp_directory.return_value.data = "/tmp/test_dir"
            mock_fs.normalize_path.return_value.success = True
            mock_fs.normalize_path.return_value.data = "/tmp"
            mock_fs.join_path.return_value.success = True
            mock_fs.join_path.return_value.data = "/tmp/output"
            mock_fs.ensure_directory.return_value.success = True
            mock_getcwd.return_value = "/tmp"

            # Create a class that combines all mixins with the base class
            class TestTool(
                IntegrationEnabledMixin,
                OutputFormatMixin,
                ToolEnvInitializerMixin,
                QuackToolLifecycleMixin,
                BaseQuackToolPlugin
            ):
                def initialize_plugin(self) -> None:
                    pass

                def process_content(self, content: Any, options: dict[str, Any]) -> dict[str, Any]:
                    return {"content": content, "options": options}

            # Create an instance to verify it works
            test_tool = TestTool("test_tool", "1.0.0")

            # Verify it has expected methods from all mixins
            self.assertTrue(hasattr(test_tool, "resolve_integration"))
            self.assertTrue(hasattr(test_tool, "_get_output_extension"))
            self.assertTrue(hasattr(test_tool, "_initialize_environment"))
            self.assertTrue(hasattr(test_tool, "pre_run"))
            self.assertTrue(hasattr(test_tool, "post_run"))
            self.assertTrue(hasattr(test_tool, "run"))
            self.assertTrue(hasattr(test_tool, "validate"))
            self.assertTrue(hasattr(test_tool, "upload"))

            # Verify it has expected methods from base class
            self.assertTrue(hasattr(test_tool, "get_metadata"))
            self.assertTrue(hasattr(test_tool, "is_available"))
            self.assertTrue(hasattr(test_tool, "process_file"))
            self.assertTrue(hasattr(test_tool, "initialize"))


class TestToolkitImportsPytest:
    """
    Pytest-style tests for toolkit imports.
    """

    def test_module_attributes(self) -> None:
        """Test that the toolkit module has the expected attributes."""
        assert hasattr(quack_core.toolkit, "__all__")
        assert isinstance(quack_core.toolkit.__all__, list)

        # Check that all items in __all__ are actually in the module
        for item in quack_core.toolkit.__all__:
            assert hasattr(quack_core.toolkit, item)

    def test_importing_protocol(self) -> None:
        """Test importing the protocol directly."""
        # Protocol is already imported at the top
        assert callable(QuackToolPluginProtocol.__call__)

    def test_importing_base(self) -> None:
        """Test importing the base module directly."""
        import quack_core.toolkit.base as base

        assert isinstance(base, ModuleType)
        assert hasattr(base, "BaseQuackToolPlugin")

    def test_importing_mixins(self) -> None:
        """Test importing the mixins directly."""
        import quack_core.toolkit.mixins as mixins

        assert isinstance(mixins, ModuleType)

        # Import from individual modules
        from quack_core.toolkit.mixins import (
            IntegrationEnabledMixin,
            OutputFormatMixin,
            QuackToolLifecycleMixin,
            ToolEnvInitializerMixin,
        )

        # Test functionality of imported mixins
        assert callable(ToolEnvInitializerMixin._initialize_environment)
        assert callable(IntegrationEnabledMixin.resolve_integration)
        assert callable(QuackToolLifecycleMixin.pre_run)
        assert callable(OutputFormatMixin._get_output_extension)


if __name__ == "__main__":
    unittest.main()
