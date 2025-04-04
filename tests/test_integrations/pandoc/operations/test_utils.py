# src/quackcore/integrations/pandoc/operations/utils.py
import time
from pathlib import Path

# Use the global FS service instance
from quackcore.fs import service as fs

# Use a module-specific logger
from quackcore.logging import get_logger
logger = get_logger(__name__)

from quackcore.errors import QuackIntegrationError
from quackcore.integrations.pandoc.config import PandocConfig
from quackcore.integrations.pandoc.models import FileInfo, ConversionMetrics


def verify_pandoc() -> str:
    """
    Verify Pandoc availability.

    Returns:
        The Pandoc version.

    Raises:
        QuackIntegrationError: When pypandoc is not installed or pandoc is not found.
    """
    import pypandoc
    try:
        version = pypandoc.get_pandoc_version()
        return version
    except ImportError:
        raise QuackIntegrationError("pypandoc module is not installed")
    except OSError:
        raise QuackIntegrationError("Pandoc is not installed")


def prepare_pandoc_args(
    config: PandocConfig,
    input_format: str,
    output_format: str,
    extra_args: list[str] | None = None,
) -> list[str]:
    """
    Prepare pandoc arguments based on configuration.
    """
    args = []
    # Process configuration options
    for key, value in config.pandoc_options.items():
        if isinstance(value, bool):
            if value:
                args.append(f"--{key}")
        elif isinstance(value, list):
            args.extend([f"--{key}={str(item)}" for item in value])
        else:
            args.append(f"--{key}={value}")

    # Append conversion-specific extra arguments
    if input_format == "html" and output_format == "markdown":
        args.extend(config.html_to_md_extra_args)
    elif input_format == "markdown" and output_format == "docx":
        args.extend(config.md_to_docx_extra_args)

    # Append any additional arguments provided
    if extra_args:
        args.extend(extra_args)
    return args


def get_file_info(path: Path, format_hint: str | None = None) -> FileInfo:
    """
    Get file information for conversion.

    Args:
        path: Path to the file.
        format_hint: Optional hint about the file format.

    Returns:
        FileInfo: Object containing file details.

    Raises:
        QuackIntegrationError: If the file does not exist.
    """
    file_info = fs.get_file_info(path)
    if not file_info.success or not file_info.exists:
        raise QuackIntegrationError(f"File not found: {path}")

    # Determine file format either from provided hint or file extension
    if format_hint:
        format_name = format_hint
    else:
        extension = fs.get_extension(path)
        format_mapping = {
            "md": "markdown",
            "markdown": "markdown",
            "html": "html",
            "htm": "html",
            "docx": "docx",
            "doc": "docx",
            "pdf": "pdf",
            "txt": "plain",
        }
        format_name = format_mapping.get(extension, extension)

    return FileInfo(
        path=path,
        format=format_name,
        size=file_info.size or 0,
        modified=file_info.modified,
    )


def check_file_size(
    converted_size: int, validation_min_size: int
) -> tuple[bool, list[str]]:
    """
    Check if the converted file meets the minimum file size.

    Args:
        converted_size: Size of the converted file.
        validation_min_size: Minimum size threshold.

    Returns:
        A tuple of (is_valid, error messages list).
    """
    errors: list[str] = []

    if validation_min_size > 0 and converted_size < validation_min_size:
        converted_size_str = fs.get_file_size_str(converted_size)
        min_size_str = fs.get_file_size_str(validation_min_size)
        errors.append(
            f"Converted file size ({converted_size_str}) is below the minimum threshold ({min_size_str})"
        )
        return False, errors

    return True, errors


def check_conversion_ratio(
    converted_size: int, original_size: int, threshold: float
) -> tuple[bool, list[str]]:
    """
    Check that the converted file is not too small compared to the original.

    Args:
        converted_size: Size of the converted file.
        original_size: Size of the original file.
        threshold: Minimum ratio threshold.

    Returns:
        A tuple of (is_valid, error messages list).
    """
    errors: list[str] = []
    if original_size > 0:
        conversion_ratio = converted_size / original_size
        if conversion_ratio < threshold:
            converted_size_str = fs.get_file_size_str(converted_size)
            original_size_str = fs.get_file_size_str(original_size)
            errors.append(
                f"Conversion error: Converted file size ({converted_size_str}) is less than "
                f"{threshold * 100:.0f}% of the original file size ({original_size_str}) "
                f"(ratio: {conversion_ratio:.2f})."
            )
            return False, errors
    return True, errors


def track_metrics(
    filename: str,
    start_time: float,
    original_size: int,
    converted_size: int,
    metrics: ConversionMetrics,
    config: PandocConfig,
) -> None:
    """
    Track conversion metrics such as conversion time and file size changes.

    Args:
        filename: Name of the file.
        start_time: Timestamp at the start of conversion.
        original_size: Original file size.
        converted_size: Converted file size.
        metrics: Object tracking conversion metrics.
        config: Pandoc configuration.
    """
    # Track conversion time if enabled
    if config.metrics.track_conversion_time:
        end_time = time.time()
        duration = end_time - start_time
        metrics.conversion_times[filename] = {"start": start_time, "end": end_time}
        logger.info(f"Conversion time for {filename}: {duration:.2f} seconds")

    # Track file size changes if enabled
    if config.metrics.track_file_sizes:
        metrics.file_sizes[filename] = {
            "original": original_size,
            "converted": converted_size,
            "ratio": converted_size / original_size if original_size > 0 else 0,
        }
        original_size_str = fs.get_file_size_str(original_size)
        converted_size_str = fs.get_file_size_str(converted_size)
        logger.info(f"File size change for {filename}: {original_size_str} -> {converted_size_str}")


def validate_html_structure(html_content: str, check_links: bool = False) -> tuple[bool, list[str]]:
    """
    Validate the structure of an HTML document.

    Args:
        html_content: HTML content as a string.
        check_links: Whether to check for empty links.

    Returns:
        A tuple of (is_valid, error messages list).
    """
    errors: list[str] = []
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        if not soup.body:
            errors.append("HTML document missing body tag")
        if check_links:
            empty_links = sum(1 for link in soup.find_all("a") if not link.get("href"))
            if empty_links > 0:
                errors.append(f"Found {empty_links} empty links in document")
    except Exception as e:
        errors.append(f"HTML validation error: {str(e)}")
        return False, errors

    return len(errors) == 0, errors


def validate_docx_structure(docx_path: Path, check_links: bool = False) -> tuple[bool, list[str]]:
    """
    Validate the structure of a DOCX document.

    Args:
        docx_path: Path to the DOCX file.
        check_links: Whether to check for incomplete document parts.

    Returns:
        A tuple of (is_valid, error messages list).
    """
    errors: list[str] = []
    try:
        from docx import Document as DocxDocument
        # Convert the Path object to a string to match the expected input type
        doc = DocxDocument(str(docx_path))
        if not doc.paragraphs:
            errors.append("DOCX document has no paragraphs")
        if check_links:
            # Example check for document integrity
            if not hasattr(doc, "part"):
                errors.append("Document structure appears incomplete")
    except ImportError:
        # If python-docx is not installed, validation passes
        return True, errors
    except Exception as e:
        errors.append(f"DOCX validation error: {str(e)}")
        return False, errors

    return len(errors) == 0, errors

