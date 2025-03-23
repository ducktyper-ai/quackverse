# tests/test_plugins/pandoc/test_plugin_init.py
"""
Tests for pandoc plugin initialization.

This module tests the plugin initialization and discovery mechanism
defined in the __init__.py file.
"""

from unittest.mock import patch

from quackcore.plugins.pandoc import create_plugin
from quackcore.plugins.pandoc.service import PandocService
from quackcore.plugins.protocols import QuackPluginProtocol


class TestPluginInit:
    """Tests for the plugin initialization functions."""

    def test_create_plugin(self) -> None:
        """Test the create_plugin factory function."""
        plugin = create_plugin()

        assert isinstance(plugin, PandocService)
        assert isinstance(plugin, QuackPluginProtocol)
        assert plugin.name == "Pandoc"

    def test_module_exports(self) -> None:
        """Test that all necessary components are exported."""
        import quackcore.plugins.pandoc as pandoc

        # Check that key classes are exported
        assert hasattr(pandoc, "PandocService")
        assert hasattr(pandoc, "ConversionConfig")
        assert hasattr(pandoc, "PandocConfigProvider")
        assert hasattr(pandoc, "DocumentConverter")
        assert hasattr(pandoc, "create_converter")

        # Check that models are exported
        assert hasattr(pandoc, "BatchConversionResult")
        assert hasattr(pandoc, "ConversionMetrics")
        assert hasattr(pandoc, "ConversionResult")
        assert hasattr(pandoc, "ConversionTask")
        assert hasattr(pandoc, "FileInfo")

        # Check factory function is exported
        assert hasattr(pandoc, "create_plugin")

        # Check __all__ is properly defined
        assert "PandocService" in pandoc.__all__
        assert "create_plugin" in pandoc.__all__
        assert "DocumentConverter" in pandoc.__all__
        assert "ConversionConfig" in pandoc.__all__
        assert "FileInfo" in pandoc.__all__

    @patch("quackcore.plugins.pandoc.PandocService")
    def test_plugin_discovery(self, mock_service: QuackPluginProtocol) -> None:
        """Test that plugin can be discovered properly."""
        mock_service.return_value = mock_service

        plugin = create_plugin()

        assert plugin == mock_service
        mock_service.assert_called_once()
