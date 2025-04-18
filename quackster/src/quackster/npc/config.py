# quackster/src/quackster/npc/config.py
"""
Configuration settings for the Quackster quackster NPC.

This module provides configuration settings and defaults for the
Quackster quackster NPC.
"""

import os
from typing import Any

from quackcore.config import (  # Global config instance that merges env vars and file-based defaults
    config,
)
from quackcore.config.utils import get_config_value

# Import QuackCore FS and Config utilities
from quackcore.fs import service as fs
from quackcore.fs.results import DataResult, OperationResult
from quackster.npc.schema import QuacksterProfile

# =============================================================================
# Default NPC Profile and Tutorial Paths
# =============================================================================

DEFAULT_PROFILE = QuacksterProfile(
    name="Quackster",
    tone="friendly",
    backstory="A magical duck who guides developers through quests",
    expertise=["Python", "CLI tools", "GitHub", "QuackVerse"],
    teaching_style="Socratic method with playful quips",
    emoji_style="moderate",
    catchphrases=[
        "Quacktastic!",
        "Let's code some magic!",
        "Time to spread your wings!",
        "Duck, duck, code!",
    ],
)

DEFAULT_TUTORIAL_PATHS = [
    "~/quackverse/tutorials",
    "./tutorials",
    "./docs/tutorials",
]

# Environment variable names used for overrides
ENV_TUTORIAL_PATH = "QUACK_TUTORIAL_PATH"
ENV_QUACKSTER_PROFILE = "QUACK_NPC_PROFILE"
ENV_QUACKSTER_TONE = "QUACK_NPC_TONE"

# Default model settings for the NPC
DEFAULT_MODEL = "claude-3-opus-20240229"  # Default model name
MODEL_TEMPERATURE = 0.7  # Default model temperature
MODEL_MAX_TOKENS = 2000  # Default max tokens for response

# =============================================================================
# Public API
# =============================================================================


def get_tutorial_path() -> str:
    """
    Get the path to tutorial documents.

    This function first checks for an environment variable override,
    then iterates through a list of default paths. File existence and
    directory status are checked using QuackCore FS.

    Returns:
        A string representing the absolute path to the tutorial documents directory.
    """
    # Check for an override via the environment variable.
    custom_path = os.environ.get(ENV_TUTORIAL_PATH)
    if custom_path:
        expanded = fs.expand_user_vars(custom_path)
        # Extract the string path from the result
        if isinstance(expanded, (DataResult, OperationResult)) and hasattr(
            expanded, "data"
        ):
            return str(expanded.data)
        return str(expanded)

    # Try each of the default paths.
    for path_str in DEFAULT_TUTORIAL_PATHS:
        expanded_result = fs.expand_user_vars(path_str)
        # Extract the string path from the result
        if isinstance(expanded_result, (DataResult, OperationResult)) and hasattr(
            expanded_result, "data"
        ):
            expanded_path = str(expanded_result.data)
        else:
            expanded_path = str(expanded_result)

        info_result = fs.get_file_info(expanded_path)
        if info_result.success and info_result.exists and info_result.is_dir:
            return expanded_path

    # Fallback to the first default path (expanded).
    fallback_result = fs.expand_user_vars(DEFAULT_TUTORIAL_PATHS[0])
    # Extract the string path from the result
    if isinstance(fallback_result, (DataResult, OperationResult)) and hasattr(
        fallback_result, "data"
    ):
        return str(fallback_result.data)
    return str(fallback_result)


def get_npc_profile() -> QuacksterProfile:
    """
    Get the NPC profile configuration.

    This function begins with a default profile, then checks for a user‑provided
    YAML file (via an environment variable). If found, that file is read using
    QuackCore FS and merged (via pydantic’s copy/update) into the default profile.
    Finally, a tone override is applied if specified via the environment.

    Returns:
        A QuacksterProfile object for the NPC.
    """
    # Start with a deep copy of the default profile.
    profile: QuacksterProfile = DEFAULT_PROFILE.model_copy(deep=True)

    # Check if a custom profile YAML is specified.
    custom_profile_path = os.environ.get(ENV_QUACKSTER_PROFILE)
    if custom_profile_path:
        try:
            expanded_path = fs.expand_user_vars(custom_profile_path)
            result = fs.read_yaml(expanded_path)
            if result.success:
                # Merge custom profile data into the default profile.
                profile = profile.model_copy(update=result.data)
        except Exception as e:
            print(f"Error loading custom NPC profile: {str(e)}")

    # Override tone if specified.
    custom_tone = os.environ.get(ENV_QUACKSTER_TONE)
    if custom_tone:
        profile.tone = custom_tone

    return profile


def get_model_settings() -> dict[str, Any]:
    """
    Get model settings for the NPC.

    This function prioritizes configuration values obtained through the
    QuackCore Config system (which merges environment variables and config files)
    and falls back on default values if not set.

    Returns:
        A dictionary containing the model name, temperature, and maximum tokens.
    """
    model = get_config_value(config, "npc.model", DEFAULT_MODEL)
    temperature = get_config_value(config, "npc.temperature", MODEL_TEMPERATURE)
    max_tokens = get_config_value(config, "npc.max_tokens", MODEL_MAX_TOKENS)

    return {
        "model": model,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
    }
