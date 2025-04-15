# tests/quackcore/test_integrations/pandoc/operations/test_md_to_docx.py
"""
Tests for Markdown to DOCX conversion operations.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from quackcore.errors import QuackIntegrationError
from quackcore.fs.results import (
    FileInfoResult,
    OperationResult,
    ReadResult,
    WriteResult,
)
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.models import ConversionDetails, ConversionMetrics
from quackcore.integrations.pandoc.operations.md_to_docx import (
    _check_docx_metadata,
    _convert_markdown_to_docx_once,
    _get_conversion_output,
    _validate_markdown_input,
    convert_markdown_to_docx,
    validate_conversion,
)


class TestMarkdownToDocxOperations:
    """Tests for Markdown to DOCX conversion operations."""

    @pytest.fixture
    def config(self):
        """Fixture to create a PandocConfig for testing."""
        return PandocConfig(
            output_dir=Path("/path/to/output"),
        )

    @pytest.fixture
    def metrics(self):
        """Fixture to create ConversionMetrics for testing."""
        return ConversionMetrics()

    @pytest.fixture
    def mock_fs(self):
        """Fixture to mock fs module."""
        with patch("quackcore.integrations.pandoc.operations.md_to_docx.fs") as mock_fs:
            # Setup default behavior for file info checks
            file_info = FileInfoResult(
                success=True,
                path="/path/to/file.md",
                exists=True,
                is_file=True,
                size=512,  # Use 512 as expected by the test
            )
            mock_fs.service._get_file_info.return_value = file_info

            # Setup default behavior for directory creation
            dir_result = OperationResult(
                success=True,
                path="/path/to/output",
                message="Directory created",
            )
            mock_fs.create_directory.return_value = dir_result

            # Setup default behavior for read_text
            read_result = ReadResult(
                success=True,
                path="/path/to/file.md",
                content="# Test\n\nContent",
                encoding="utf-8",
            )
            mock_fs.service._read_text.return_value = read_result

            # Setup default behavior for write_text
            write_result = WriteResult(
                success=True,
                path="/path/to/output/file.docx",
                bytes_written=100,
            )
            mock_fs.write_text.return_value = write_result

            # Set up get_file_size_str
            mock_fs.get_file_size_str.return_value = "1.0 KB"

            yield mock_fs

    def test_validate_markdown_input(self, mock_fs):
        """Test validating Markdown input file."""
        markdown_path = Path("/path/to/file.md")

        # Test with valid input
        original_size = _validate_markdown_input(markdown_path)

        assert original_size == 512
        mock_fs.service._get_file_info.assert_called_with(markdown_path)
        mock_fs.service._read_text.assert_called_with(markdown_path, encoding="utf-8")

        # Test with file not found
        mock_fs.service._get_file_info.return_value.exists = False

        with pytest.raises(QuackIntegrationError) as excinfo:
            _validate_markdown_input(markdown_path)

        assert "Input file not found" in str(excinfo.value)

        # Test with empty content
        mock_fs.service._get_file_info.return_value.exists = True
        mock_fs.service._read_text.return_value.content = ""

        with pytest.raises(QuackIntegrationError) as excinfo:
            _validate_markdown_input(markdown_path)

        assert "Markdown file is empty" in str(excinfo.value)

        # Test with read error
        mock_fs.service._read_text.side_effect = Exception("Read error")

        with pytest.raises(QuackIntegrationError) as excinfo:
            _validate_markdown_input(markdown_path)

        assert "Could not read Markdown file" in str(excinfo.value)

    def test_convert_markdown_to_docx_once(self, config, mock_fs):
        """Test converting Markdown to DOCX in a single attempt."""
        markdown_path = Path("/path/to/file.md")
        output_path = Path("/path/to/output/file.docx")

        # Test successful conversion
        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx.prepare_pandoc_args"
        ) as mock_args:
            mock_args.return_value = ["--reference-doc=template.docx"]

            with patch("pypandoc.convert_file") as mock_convert:
                # pypandoc doesn't return anything for convert_file with outputfile

                _convert_markdown_to_docx_once(markdown_path, output_path, config)

                mock_fs.create_directory.assert_called_with(
                    output_path.parent, exist_ok=True
                )
                mock_args.assert_called_with(
                    config, "markdown", "docx", config.md_to_docx_extra_args
                )
                mock_convert.assert_called_with(
                    str(markdown_path),
                    "docx",
                    format="markdown",
                    outputfile=str(output_path),
                    extra_args=["--reference-doc=template.docx"],
                )

        # Test directory creation failure
        mock_fs.create_directory.return_value.success = False
        mock_fs.create_directory.return_value.error = "Permission denied"

        with pytest.raises(QuackIntegrationError) as excinfo:
            _convert_markdown_to_docx_once(markdown_path, output_path, config)

        assert "Failed to create output directory" in str(excinfo.value)

        # Test conversion error
        mock_fs.create_directory.return_value.success = True

        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx.prepare_pandoc_args"
        ) as mock_args:
            mock_args.return_value = ["--reference-doc=template.docx"]

            with patch("pypandoc.convert_file") as mock_convert:
                mock_convert.side_effect = Exception("Conversion error")

                with pytest.raises(QuackIntegrationError) as excinfo:
                    _convert_markdown_to_docx_once(markdown_path, output_path, config)

                assert "Pandoc conversion failed" in str(excinfo.value)

    def test_get_conversion_output(self, mock_fs):
        """Test retrieving conversion timing and output file size."""
        output_path = Path("/path/to/output/file.docx")
        start_time = time.time() - 2  # 2 seconds ago

        # Test successful retrieval
        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx.time.time"
        ) as mock_time:
            mock_time.return_value = start_time + 2  # 2 seconds have passed

            conversion_time, output_size = _get_conversion_output(
                output_path, start_time
            )

            assert conversion_time == 2.0
            assert output_size == 512  # From mock_fs.service.get_file_info
            mock_fs.service._get_file_info.assert_called_with(output_path)

        # Test with file info error
        mock_fs.service._get_file_info.return_value.success = False

        with pytest.raises(QuackIntegrationError) as excinfo:
            _get_conversion_output(output_path, start_time)

        assert "Failed to get info for converted file" in str(excinfo.value)

    def test_convert_markdown_to_docx(self, config, metrics, mock_fs):
        """Test the main Markdown to DOCX conversion function."""
        # Reset metrics to ensure clean state
        metrics.failed_conversions = 0
        metrics.successful_conversions = 0
        metrics.errors.clear()

        markdown_path = Path("/path/to/file.md")
        output_path = Path("/path/to/output/file.docx")

        # Test successful conversion
        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input"
        ) as mock_validate:
            mock_validate.return_value = 512  # Original size

            with patch(
                "quackcore.integrations.pandoc.operations.md_to_docx._convert_markdown_to_docx_once"
            ) as mock_convert:
                # mock_convert doesn't return anything

                with patch(
                    "quackcore.integrations.pandoc.operations.md_to_docx._get_conversion_output"
                ) as mock_output:
                    mock_output.return_value = (
                        1.0,
                        10240,
                    )  # (conversion_time, output_size)

                    with patch(
                        "quackcore.integrations.pandoc.operations.md_to_docx.validate_conversion"
                    ) as mock_validate_out:
                        mock_validate_out.return_value = []  # No validation errors

                        with patch(
                            "quackcore.integrations.pandoc.operations.md_to_docx.track_metrics"
                        ) as mock_track:
                            # Test successful conversion
                            result = convert_markdown_to_docx(
                                markdown_path, output_path, config, metrics
                            )

                            assert result.success is True
                            assert result.content[0] == output_path
                            assert isinstance(result.content[1], ConversionDetails)
                            assert result.content[1].source_format == "markdown"
                            assert result.content[1].target_format == "docx"
                            assert metrics.successful_conversions == 1
                            mock_validate.assert_called_once_with(markdown_path)
                            mock_convert.assert_called_once_with(
                                markdown_path, output_path, config
                            )
                            mock_output.assert_called_once()
                            mock_validate_out.assert_called_once()
                            mock_track.assert_called_once()

        # Reset metrics for next test
        metrics.failed_conversions = 0
        metrics.successful_conversions = 0
        metrics.errors.clear()

        # Test with validation errors
        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input"
        ) as mock_validate:
            mock_validate.return_value = 512  # Original size

            with patch(
                "quackcore.integrations.pandoc.operations.md_to_docx._convert_markdown_to_docx_once"
            ) as mock_convert:
                # mock_convert doesn't return anything

                with patch(
                    "quackcore.integrations.pandoc.operations.md_to_docx._get_conversion_output"
                ) as mock_output:
                    mock_output.return_value = (
                        1.0,
                        10240,
                    )  # (conversion_time, output_size)

                    with patch(
                        "quackcore.integrations.pandoc.operations.md_to_docx.validate_conversion"
                    ) as mock_validate_out:
                        mock_validate_out.return_value = ["DOCX validation failed"]

                        # Test validation error
                        result = convert_markdown_to_docx(
                            markdown_path, output_path, config, metrics
                        )

                        assert result.success is False
                        assert "DOCX validation failed" in result.error
                        assert metrics.successful_conversions == 0
                        assert metrics.failed_conversions == 1
                        assert str(markdown_path) in metrics.errors

        # Reset metrics for next test
        metrics.failed_conversions = 0
        metrics.successful_conversions = 0
        metrics.errors.clear()

        # Test with retry and eventual success
        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input"
        ) as mock_validate:
            mock_validate.return_value = 512  # Original size

            with patch(
                "quackcore.integrations.pandoc.operations.md_to_docx._convert_markdown_to_docx_once"
            ) as mock_convert:
                # mock_convert doesn't return anything

                with patch(
                    "quackcore.integrations.pandoc.operations.md_to_docx._get_conversion_output"
                ) as mock_output:
                    mock_output.return_value = (
                        1.0,
                        10240,
                    )  # (conversion_time, output_size)

                    with patch(
                        "quackcore.integrations.pandoc.operations.md_to_docx.validate_conversion"
                    ) as mock_validate_out:
                        # First call fails, second call succeeds
                        mock_validate_out.side_effect = [["DOCX validation failed"], []]

                        with patch(
                            "quackcore.integrations.pandoc.operations.md_to_docx.time.sleep"
                        ) as mock_sleep:
                            # Test retry logic
                            result = convert_markdown_to_docx(
                                markdown_path, output_path, config, metrics
                            )

                            assert result.success is True
                            assert mock_convert.call_count == 2
                            assert mock_sleep.call_count == 1
                            assert metrics.successful_conversions == 1

        # Reset metrics for next test
        metrics.failed_conversions = 0
        metrics.successful_conversions = 0
        metrics.errors.clear()

        # Test with max retries exceeded
        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input"
        ) as mock_validate:
            mock_validate.return_value = 512  # Original size

            with patch(
                "quackcore.integrations.pandoc.operations.md_to_docx._convert_markdown_to_docx_once"
            ) as mock_convert:
                # mock_convert doesn't return anything

                with patch(
                    "quackcore.integrations.pandoc.operations.md_to_docx._get_conversion_output"
                ) as mock_output:
                    mock_output.return_value = (
                        1.0,
                        10240,
                    )  # (conversion_time, output_size)

                    with patch(
                        "quackcore.integrations.pandoc.operations.md_to_docx.validate_conversion"
                    ) as mock_validate_out:
                        # Always return validation errors
                        mock_validate_out.return_value = ["DOCX validation failed"]

                        with patch(
                            "quackcore.integrations.pandoc.operations.md_to_docx.time.sleep"
                        ) as mock_sleep:
                            # Set max retries to 2 for faster testing
                            config.retry_mechanism.max_conversion_retries = 2

                            # Test max retries
                            result = convert_markdown_to_docx(
                                markdown_path, output_path, config, metrics
                            )

                            assert result.success is False
                            assert (
                                "Conversion failed after maximum retries"
                                in result.error
                            )
                            assert "DOCX validation failed" in result.error
                            assert mock_convert.call_count == 2
                            assert mock_sleep.call_count == 1
                            assert metrics.successful_conversions == 0
                            assert metrics.failed_conversions == 1

        # Reset metrics for next test
        metrics.failed_conversions = 0
        metrics.successful_conversions = 0
        metrics.errors.clear()

        # Test with exception
        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx._validate_markdown_input"
        ) as mock_validate:
            mock_validate.side_effect = Exception("Unexpected error")

            result = convert_markdown_to_docx(
                markdown_path, output_path, config, metrics
            )

            assert result.success is False
            assert "Failed to convert Markdown to DOCX" in result.error
            assert metrics.failed_conversions == 1

    def test_validate_conversion(self, mock_fs, config):
        """Test validating Markdown to DOCX conversion."""
        output_path = Path("/path/to/output/file.docx")
        input_path = Path("/path/to/file.md")
        original_size = 512

        # Make sure validation.verify_structure is True for this test
        config.validation.verify_structure = True

        # Mock file info for output file with correct size parameter
        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx.fs"
        ) as patched_fs:
            # Create a proper FileInfoResult with size 10240
            output_info = FileInfoResult(
                success=True,
                path=str(output_path),
                exists=True,
                is_file=True,
                size=10240,  # Use the expected size for the test
            )
            patched_fs.service._get_file_info.return_value = output_info

            # Make sure output file seems to exist
            patched_fs.path_exists = lambda p: True  # Simple mock for path_exists

            # Test valid conversion
            with patch(
                "quackcore.integrations.pandoc.operations.md_to_docx.check_file_size"
            ) as mock_size:
                mock_size.return_value = (True, [])

                with patch(
                    "quackcore.integrations.pandoc.operations.md_to_docx.check_conversion_ratio"
                ) as mock_ratio:
                    mock_ratio.return_value = (True, [])

                    with patch(
                        "quackcore.integrations.pandoc.operations.md_to_docx.validate_docx_structure"
                    ) as mock_validate:
                        mock_validate.return_value = (True, [])

                        with patch(
                            "quackcore.integrations.pandoc.operations.md_to_docx._check_docx_metadata"
                        ) as mock_metadata:
                            # Force the Path.exists() method to return True
                            with patch.object(Path, "exists", return_value=True):
                                validation_errors = validate_conversion(
                                    output_path, input_path, original_size, config
                                )

                                assert len(validation_errors) == 0
                                mock_size.assert_called_with(
                                    output_info.size, config.validation.min_file_size
                                )
                                mock_ratio.assert_called_with(
                                    output_info.size,
                                    original_size,
                                    config.validation.conversion_ratio_threshold,
                                )
                                mock_validate.assert_called_with(
                                    output_path, config.validation.check_links
                                )
                                mock_metadata.assert_called_with(
                                    output_path,
                                    input_path,
                                    config.validation.check_links,
                                )

        # Test with output file not found
        mock_fs.service._get_file_info.return_value.exists = False

        validation_errors = validate_conversion(
            output_path, input_path, original_size, config
        )

        assert len(validation_errors) == 1
        assert "Output file does not exist" in validation_errors[0]

        # Test with file size check failure
        mock_fs.service._get_file_info.return_value.exists = True

        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx.check_file_size"
        ) as mock_size:
            mock_size.return_value = (False, ["File size is below threshold"])

            with patch(
                "quackcore.integrations.pandoc.operations.md_to_docx.check_conversion_ratio"
            ) as mock_ratio:
                mock_ratio.return_value = (True, [])

                validation_errors = validate_conversion(
                    output_path, input_path, original_size, config
                )

                assert len(validation_errors) == 1
                assert "File size is below threshold" in validation_errors[0]

        # Test with conversion ratio check failure
        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx.check_file_size"
        ) as mock_size:
            mock_size.return_value = (True, [])

            with patch(
                "quackcore.integrations.pandoc.operations.md_to_docx.check_conversion_ratio"
            ) as mock_ratio:
                mock_ratio.return_value = (
                    False,
                    ["Conversion ratio is below threshold"],
                )

                validation_errors = validate_conversion(
                    output_path, input_path, original_size, config
                )

                assert len(validation_errors) == 1
                assert "Conversion ratio is below threshold" in validation_errors[0]

        # Test with DOCX structure validation failure
        with patch(
            "quackcore.integrations.pandoc.operations.md_to_docx.check_file_size"
        ) as mock_size:
            mock_size.return_value = (True, [])

            with patch(
                "quackcore.integrations.pandoc.operations.md_to_docx.check_conversion_ratio"
            ) as mock_ratio:
                mock_ratio.return_value = (True, [])

                with patch(
                    "quackcore.integrations.pandoc.operations.md_to_docx.validate_docx_structure"
                ) as mock_validate:
                    mock_validate.return_value = (
                        False,
                        ["DOCX document has no paragraphs"],
                    )

                    # Force the Path.exists() method to return True
                    with patch.object(Path, "exists", return_value=True):
                        validation_errors = validate_conversion(
                            output_path, input_path, original_size, config
                        )

                        assert len(validation_errors) == 1
                        assert "DOCX document has no paragraphs" in validation_errors[0]

    def test_check_docx_metadata(self, mock_fs):
        """Test checking DOCX metadata for references to the source file."""
        import quackcore.integrations.pandoc.operations.md_to_docx as md_to_docx

        output_path = Path("/path/to/output/file.docx")
        source_path = Path("/path/to/input.md")
        check_links = True

        # Test when python-docx is not available
        # Instead of patching the imported module which doesn't exist,
        # we can patch the import itself to raise ImportError
        with patch(
            "importlib.import_module", side_effect=ImportError("No module named 'docx'")
        ):
            # Should not raise an exception, just log and return
            md_to_docx._check_docx_metadata(output_path, source_path, check_links)
            # No assertions needed, just testing that it doesn't raise an exception

        # For testing with python-docx available, we need to make a few changes
        # Test with source filename in title
        docx_module = MagicMock()
        mock_document_class = MagicMock()

        mock_doc_with_source = MagicMock()
        mock_core_props_with_source = MagicMock()
        mock_core_props_with_source.title = "input.md - converted document"
        mock_core_props_with_source.comments = None
        mock_core_props_with_source.subject = None
        mock_doc_with_source.core_properties = mock_core_props_with_source
        mock_document_class.return_value = mock_doc_with_source

        # Add Document to the mocked docx module
        docx_module.Document = mock_document_class

        with patch.dict("sys.modules", {"docx": docx_module}):
            # Should not log any warnings
            with patch.object(md_to_docx.logger, "debug") as mock_logger:
                md_to_docx._check_docx_metadata(output_path, source_path, check_links)
                mock_logger.assert_not_called()

        # Test with source filename not in metadata
        docx_module = MagicMock()
        mock_document_class = MagicMock()

        mock_doc_without_source = MagicMock()
        mock_core_props_without_source = MagicMock()
        # Set properties that don't contain the source filename
        mock_core_props_without_source.title = "Some document"
        mock_core_props_without_source.comments = "Some comments"
        mock_core_props_without_source.subject = "Some subject"
        mock_doc_without_source.core_properties = mock_core_props_without_source
        mock_document_class.return_value = mock_doc_without_source

        # Add Document to the mocked docx module
        docx_module.Document = mock_document_class

        # Fix: We directly patch the logger.debug method instead of using the mock_logger.debug
        with patch.dict("sys.modules", {"docx": docx_module}):
            with patch.object(md_to_docx.logger, "debug") as mock_debug:
                md_to_docx._check_docx_metadata(output_path, source_path, check_links)
                mock_debug.assert_called_once_with(
                    f"Source file reference missing in document metadata: {source_path.name}"
                )
