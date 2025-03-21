# src/quackcore/plugins/pandoc/config.py
"""
Configuration models for Pandoc plugin.

This module provides Pydantic models for the pandoc plugin configuration.
"""

import logging
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, Field, field_validator

from quackcore.config.models import LoggingConfig


class PandocOptions(BaseModel):
    """Configuration for pandoc conversion options."""

    wrap: str = Field(
        default="none",
        description="Text wrapping mode (none, auto, preserve)"
    )
    standalone: bool = Field(
        default=True,
        description="Whether to produce a standalone document"
    )
    markdown_headings: str = Field(
        default="atx",
        description="Markdown heading style (atx, setext)"
    )
    reference_links: bool = Field(
        default=False,
        description="Whether to use reference-style links"
    )
    resource_path: list[Path] = Field(
        default_factory=list,
        description="Additional resource paths for pandoc"
    )


class ValidationConfig(BaseModel):
    """Configuration for document validation."""

    verify_structure: bool = Field(
        default=True,
        description="Whether to verify document structure"
    )
    min_file_size: int = Field(
        default=50,
        description="Minimum file size in bytes"
    )
    conversion_ratio_threshold: float = Field(
        default=0.1,
        description="Minimum ratio of converted to original file size"
    )
    check_links: bool = Field(
        default=False,
        description="Whether to check links in the document"
    )


class RetryConfig(BaseModel):
    """Configuration for retry mechanism."""

    max_conversion_retries: int = Field(
        default=3,
        description="Maximum number of conversion retries"
    )
    conversion_retry_delay: float = Field(
        default=1.0,
        description="Delay between conversion retries in seconds"
    )


class MetricsConfig(BaseModel):
    """Configuration for metrics tracking."""

    track_conversion_time: bool = Field(
        default=True,
        description="Whether to track conversion time"
    )
    track_file_sizes: bool = Field(
        default=True,
        description="Whether to track file sizes"
    )


class ConversionConfig(BaseModel):
    """Main configuration for document conversion."""

    pandoc_options: PandocOptions = Field(
        default_factory=PandocOptions,
        description="Pandoc conversion options"
    )
    validation: ValidationConfig = Field(
        default_factory=ValidationConfig,
        description="Document validation settings"
    )
    retry_mechanism: RetryConfig = Field(
        default_factory=RetryConfig,
        description="Retry mechanism settings"
    )
    metrics: MetricsConfig = Field(
        default_factory=MetricsConfig,
        description="Metrics tracking settings"
    )
    html_to_md_extra_args: list[str] = Field(
        default_factory=lambda: ["--strip-comments", "--no-highlight"],
        description="Extra arguments for HTML to Markdown conversion"
    )
    md_to_docx_extra_args: list[str] = Field(
        default_factory=list,
        description="Extra arguments for Markdown to DOCX conversion"
    )
    output_dir: Path = Field(
        default=Path("./output"),
        description="Output directory for converted files"
    )
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig,
        description="Logging configuration"
    )

    @field_validator("output_dir")
    @classmethod
    def validate_output_dir(cls, v: Path) -> Path:
        """Validate that the output directory exists or can be created."""
        if not v.exists():
            # We validate but don't create - creation happens at runtime
            pass
        return v


class PandocConfigProvider:
    """Configuration provider for Pandoc plugin."""

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
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)

    @property
    def name(self) -> str:
        """Get the name of the configuration provider."""
        return "PandocConfig"

    def load_config(self, config_path: str | Path | None = None) -> Any:
        """
        Load configuration from a file.

        Args:
            config_path: Path to the configuration file

        Returns:
            ConfigResult: Result containing configuration data
        """
        from quackcore.config.loader import load_config
        from quackcore.fs.results import DataResult

        try:
            # Try to load from the specified path
            if config_path:
                from quackcore.fs import service as fs
                yaml_result = fs.read_yaml(config_path)
                if not yaml_result.success:
                    self.logger.error(
                        f"Failed to load config from {config_path}: {yaml_result.error}")
                    return DataResult(
                        success=False,
                        path=str(config_path),
                        data={},
                        format="yaml",
                        error=yaml_result.error
                    )
                config_data = yaml_result.data
            else:
                # Try to load from the QuackCore configuration system
                config = load_config()
                config_data = config.custom.get("pandoc", {})
                if not config_data:
                    # Use default configuration as fallback
                    config_data = self.get_default_config()

            # Extract pandoc-specific configuration
            pandoc_config = self._extract_config(config_data)

            # Validate the configuration
            if not self.validate_config(pandoc_config):
                return DataResult(
                    success=False,
                    path=str(config_path) if config_path else "default_config",
                    data={},
                    format="yaml",
                    error="Invalid configuration"
                )

            return DataResult(
                success=True,
                path=str(config_path) if config_path else "default_config",
                data=pandoc_config,
                format="yaml",
                message="Successfully loaded configuration"
            )

        except Exception as e:
            self.logger.error(f"Error loading configuration: {str(e)}")
            return DataResult(
                success=False,
                path=str(config_path) if config_path else "default_config",
                data={},
                format="yaml",
                error=f"Error loading configuration: {str(e)}"
            )

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
        Validate configuration data.

        Args:
            config: Configuration data to validate

        Returns:
            bool: True if configuration is valid
        """
        try:
            ConversionConfig(**config)
            return True
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False

    def get_default_config(self) -> dict[str, Any]:
        """
        Get default configuration values.

        Returns:
            dict[str, Any]: Default configuration values
        """
        default_config = ConversionConfig().model_dump()
        return default_config