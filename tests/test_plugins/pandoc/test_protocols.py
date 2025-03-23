# tests/test_plugins/pandoc/test_protocols.py
"""
Tests for pandoc protocol implementations.

This module tests the protocols defined for the pandoc plugin,
ensuring proper adherence to the defined interfaces.
"""

from pathlib import Path
from unittest.mock import MagicMock

from quackcore.plugins.pandoc.models import (
    BatchConversionResult,
    ConversionResult,
    ConversionTask,
    FileInfo,
)
from quackcore.plugins.pandoc.protocols import (
    BatchConverterProtocol,
    DocumentConverterProtocol,
    PandocServiceProtocol,
)


class TestDocumentConverterProtocol:
    """Tests for the DocumentConverterProtocol."""

    def test_protocol_conformance(self) -> None:
        """Test if a mock object conforms to the DocumentConverterProtocol."""
        # Create a mock object implementing the protocol methods
        mock_converter = MagicMock()
        mock_converter.convert_file.return_value = ConversionResult()
        mock_converter.validate_conversion.return_value = True

        # Verify it's recognized as implementing the protocol
        assert isinstance(mock_converter, DocumentConverterProtocol)

        # Test the methods
        result = mock_converter.convert_file(
            Path("/path/to/input.html"), Path("/path/to/output.md"), "markdown"
        )
        assert isinstance(result, ConversionResult)

        is_valid = mock_converter.validate_conversion(
            Path("/path/to/output.md"), Path("/path/to/input.html")
        )
        assert is_valid is True

    def test_missing_method_fails_protocol(self) -> None:
        """Test that objects missing protocol methods fail the isinstance check."""
        # Create an incomplete mock
        incomplete_converter = MagicMock()
        incomplete_converter.convert_file.return_value = ConversionResult()
        # Missing validate_conversion method

        # Should not be recognized as implementing the protocol
        assert not isinstance(incomplete_converter, DocumentConverterProtocol)


class TestBatchConverterProtocol:
    """Tests for the BatchConverterProtocol."""

    def test_protocol_conformance(self) -> None:
        """Test if a mock object conforms to the BatchConverterProtocol."""
        # Create a mock object implementing the protocol methods
        mock_batch_converter = MagicMock()
        mock_batch_converter.convert_batch.return_value = BatchConversionResult()

        # Verify it's recognized as implementing the protocol
        assert isinstance(mock_batch_converter, BatchConverterProtocol)

        # Test the method
        tasks = [
            ConversionTask(
                source=FileInfo(path=Path("/path/to/file.html"), format="html"),
                target_format="markdown",
            )
        ]
        result = mock_batch_converter.convert_batch(tasks, Path("/output/dir"))
        assert isinstance(result, BatchConversionResult)

    def test_missing_method_fails_protocol(self) -> None:
        """Test that objects missing protocol methods fail the isinstance check."""
        # Create an incomplete mock (with no methods at all)
        incomplete_batch_converter = MagicMock(spec=[])

        # Should not be recognized as implementing the protocol
        assert not isinstance(incomplete_batch_converter, BatchConverterProtocol)


class TestPandocServiceProtocol:
    """Tests for the PandocServiceProtocol."""

    def test_protocol_conformance(self) -> None:
        """Test if a mock object conforms to the PandocServiceProtocol."""
        # Create a mock object implementing all protocol methods
        mock_service = MagicMock()
        mock_service.html_to_markdown.return_value = ConversionResult()
        mock_service.markdown_to_docx.return_value = ConversionResult()
        mock_service.convert_directory.return_value = BatchConversionResult()
        mock_service.is_pandoc_available.return_value = True
        mock_service.get_pandoc_version.return_value = "2.18"

        # Verify it's recognized as implementing the protocol
        assert isinstance(mock_service, PandocServiceProtocol)

        # Test each method
        result1 = mock_service.html_to_markdown(Path("/path/to/file.html"))
        assert isinstance(result1, ConversionResult)

        result2 = mock_service.markdown_to_docx(Path("/path/to/file.md"))
        assert isinstance(result2, ConversionResult)

        result3 = mock_service.convert_directory(
            Path("/input/dir"), "markdown", Path("/output/dir")
        )
        assert isinstance(result3, BatchConversionResult)

        available = mock_service.is_pandoc_available()
        assert available is True

        version = mock_service.get_pandoc_version()
        assert version == "2.18"

    def test_incomplete_implementation_fails_protocol(self) -> None:
        """Test that incomplete implementations fail the isinstance check."""
        # Create an incomplete mock
        incomplete_service = MagicMock()
        incomplete_service.html_to_markdown.return_value = ConversionResult()
        # Missing other required methods

        # Should not be recognized as implementing the protocol
        assert not isinstance(incomplete_service, PandocServiceProtocol)


class TestProtocolComposition:
    """Tests for protocol composition and interactions."""

    def test_combined_protocols(self) -> None:
        """Test that an object can implement multiple protocols."""
        # Create a mock implementing both DocumentConverterProtocol and BatchConverterProtocol
        combined_mock = MagicMock()
        combined_mock.convert_file.return_value = ConversionResult()
        combined_mock.validate_conversion.return_value = True
        combined_mock.convert_batch.return_value = BatchConversionResult()

        # Should be recognized as implementing both protocols
        assert isinstance(combined_mock, DocumentConverterProtocol)
        assert isinstance(combined_mock, BatchConverterProtocol)
