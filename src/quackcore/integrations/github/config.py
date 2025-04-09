# src/quackcore/integrations/github/config.py
"""Configuration provider for GitHub integration."""

import os
from typing import Any

from quackcore.integrations.core import BaseConfigProvider, ConfigResult
from quackcore.logging import get_logger

logger = get_logger(__name__)


class GitHubConfigProvider(BaseConfigProvider):
    """Configuration provider for GitHub integration."""

    @property
    def name(self) -> str:
        """Name of the configuration provider."""
        return "GitHub"

    def get_default_config(self) -> dict[str, Any]:
        """Get default GitHub configuration."""
        return {
            "token": "",  # Default to empty, should be set in env or config
            "api_url": "https://api.github.com",
            "timeout_seconds": 30,
            "max_retries": 3,
            "retry_delay": 1.0,
            "teaching": {
                "assignment_branch_prefix": "assignment-",
                "default_base_branch": "main",
                "pr_title_template": "[SUBMISSION] {title}",
                "pr_body_template": "This is a submission for the assignment: {assignment}\n\nSubmitted by: {student}",
            },
        }

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate GitHub configuration."""
        # Check if token is available in config or environment variable
        has_token = False

        if "token" in config and config["token"]:
            has_token = True
        elif os.environ.get("GITHUB_TOKEN"):
            has_token = True

        if not has_token:
            logger.error(
                "GitHub token not found in config or GITHUB_TOKEN environment variable."
            )
            return False

        # Validate API URL format
        if "api_url" in config:
            api_url = config["api_url"]
            if not api_url.startswith(("http://", "https://")):
                logger.error(f"Invalid GitHub API URL format: {api_url}")
                return False

        return True

    def _extract_config(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """Extract GitHub-specific configuration from the full config."""
        # Look for GitHub configuration in various possible locations
        for key in ["github", "GitHub", "integrations.github", "integrations.GitHub"]:
            # Handle the case of dotted path
            if "." in key:
                parts = key.split(".")
                current = config_data
                for part in parts:
                    if part in current:
                        current = current[part]
                    else:
                        current = None
                        break
                if current is not None:
                    return current
            # Handle direct key
            elif key in config_data:
                return config_data[key]

        # If no GitHub-specific section is found, try the "integrations" section
        if "integrations" in config_data and isinstance(
            config_data["integrations"], dict
        ):
            for key in ["github", "GitHub"]:
                if key in config_data["integrations"]:
                    return config_data["integrations"][key]

        # If we still haven't found GitHub config, check for token in environment
        if os.environ.get("GITHUB_TOKEN"):
            # Create a minimal config with just the token from environment
            default_config = self.get_default_config()
            default_config["token"] = os.environ.get("GITHUB_TOKEN", "")
            return default_config

        # Fall back to default implementation
        return super()._extract_config(config_data)

    def load_config(self, config_path: str | None = None) -> ConfigResult:
        """Load configuration from a file."""
        # First try loading from the QuackCore configuration system
        result = super().load_config(config_path)

        # If successful but token is missing, try to get it from environment
        if result.success and result.content and "token" in result.content:
            # If token is empty, try to get from environment
            if not result.content["token"]:
                env_token = os.environ.get("GITHUB_TOKEN")
                if env_token:
                    result.content["token"] = env_token
                    logger.debug("Using GitHub token from environment variable")

        return result
