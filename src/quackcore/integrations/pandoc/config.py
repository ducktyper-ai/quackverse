# src/quackcore/integrations/pandoc/config.py
"""
Configuration models for Pandoc integration.

This module provides Pydantic models and configuration provider for the Pandoc
integration, handling settings for document conversion between various formats.
"""

import logging
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, Field, field_validator

from quackcore.config.models import LoggingConfig
from quackcore.integrations.core.base import BaseConfigProvider


class PandocOptions(BaseModel):
    """Configuration for pandoc conversion options."""

    wrap: str = Field(
        default="none", description="Text wrapping mode (none, auto, preserve)"
    )
    standalone: bool = Field(
        default=True, description="Whether to produce a standalone document"
    )
    markdown_headings: str = Field(
        default="atx", description="Markdown heading style (atx, setext)"
    )
    reference_links: bool = Field(
        default=False, description="Whether to use reference-style links"
    )
    resource_path: list[Path] = Field(
        default_factory=list, description="Additional resource paths for pandoc"
    )


class ValidationConfig(BaseModel):
    """Configuration for document validation."""

    verify_structure: bool = Field(
        default=True, description="Whether to verify document structure"
    )
    min_file_size: int = Field(default=50, description="Minimum file size in bytes")
    conversion_ratio_threshold: float = Field(
        default=0.1, description="Minimum ratio of converted to original file size"
    )
    check_links: bool = Field(
        default=False, description="Whether to check links in the document"
    )


class RetryConfig(BaseModel):
    """Configuration for retry mechanism."""

    max_conversion_retries: int = Field(
        default=3, description="Maximum number of conversion retries"
    )
    conversion_retry_delay: float = Field(
        default=1.0, description="Delay between conversion retries in seconds"
    )


class MetricsConfig(BaseModel):
    """Configuration for metrics tracking."""

    track_conversion_time: bool = Field(
        default=True, description="Whether to track conversion time"
    )
    track_file_sizes: bool = Field(
        default=True, description="Whether to track file sizes"
    )


class PandocConfig(BaseModel):
    """Main configuration for document conversion."""

    pandoc_options: PandocOptions = Field(
        default_factory=PandocOptions, description="Pandoc conversion options"
    )
    validation: ValidationConfig = Field(
        default_factory=ValidationConfig, description="Document validation settings"
    )
    retry_mechanism: RetryConfig = Field(
        default_factory=RetryConfig, description="Retry mechanism settings"
    )
    metrics: MetricsConfig = Field(
        default_factory=MetricsConfig, description="Metrics tracking settings"
    )
    html_to_md_extra_args: list[str] = Field(
        default_factory=lambda: ["--strip-comments", "--no-highlight"],
        description="Extra arguments for HTML to Markdown conversion",
    )
    md_to_docx_extra_args: list[str] = Field(
        default_factory=list,
        description="Extra arguments for Markdown to DOCX conversion",
    )
    output_dir: Path = Field(
        default=Path("./output"), description="Output directory for converted files"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging configuration"
    )

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Validate that the output directory exists or can be created."""
        # We only validate path format, creation happens at runtime
        return v


class PandocConfigProvider(BaseConfigProvider):
    """Configuration provider for Pandoc integration."""

    # Class variables with proper typing
    DEFAULT_CONFIG_LOCATIONS: ClassVar[list[str]] = [
        "./config/pandoc_config.yaml",
        "./config/quack_config.yaml",
        "./quack_config.yaml",
        "~/.quack/pandoc_config.yaml",
    ]
    ENV_PREFIX: ClassVar[str] = "QUACK_PANDOC_"

    def __init__(self, log_level: int = logging.INFO) -> None:
        """
        Initialize the Pandoc configuration provider.

        Args:
            log_level: Logging level
        """
        super().__init__(log_level)

    @property
    def name(self) -> str:
        """Get the name of the configuration provider."""
        return "PandocConfig"

    def _extract_config(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """
        Extract pandoc-specific configuration from the full config data.

        Args:
            config_data: Full configuration data

        Returns:
            dict[str, Any]: Pandoc-specific configuration
        """
        # Look for pandoc section first
        if "pandoc" in config_data:
            return config_data["pandoc"]

        # If not found, check for conversion section
        if "conversion" in config_data:
            return config_data["conversion"]

        # Otherwise, return the original data for further processing
        return config_data

    def validate_config(self, config: dict[str, Any]) -> bool:
        """
        Validate configuration data against the Pandoc configuration schema.

        Args:
            config: Configuration data to validate

        Returns:
            bool: True if configuration is valid
        """
        try:
            PandocConfig(**config)
            return True
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False

    def get_default_config(self) -> dict[str, Any]:
        """
        Get default configuration values for Pandoc.

        Returns:
            dict[str, Any]: Default configuration values
        """
        default_config = PandocConfig().model_dump()
        return default_config
