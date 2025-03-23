# src/quackcore/cli/bootstrap.py
"""
CLI bootstrapper for QuackCore.

This module provides utilities for initializing CLI applications with consistent
configuration, logging, and environment setup. It serves as the foundation for
all QuackVerse CLI tools, ensuring a unified developer experience.
"""

import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from quackcore.cli.config import find_project_root, load_config
from quackcore.cli.context import QuackContext
from quackcore.cli.logging import setup_logging
from quackcore.cli.options import CliOptions
from quackcore.errors import QuackError


def init_cli_env(
    *,
    config_path: str | Path | None = None,
    log_level: str | None = None,
    debug: bool = False,
    verbose: bool = False,
    quiet: bool = False,
    environment: str | None = None,
    base_dir: str | Path | None = None,
    cli_args: Mapping[str, Any] | None = None,
    app_name: str = "quack",
) -> QuackContext:
    """
    Initialize a CLI environment and return a context object.

    This function is the main entry point for CLI bootstrapping, handling
    configuration loading, logging setup, and context creation with the
    appropriate precedence of settings.

    Args:
        config_path: Path to configuration file
        log_level: Logging level
        debug: Enable debug mode
        verbose: Enable verbose output
        quiet: Suppress non-error output
        environment: Override environment
        base_dir: Override base directory
        cli_args: Additional CLI arguments to apply as config overrides
        app_name: Application name (used for the logger namespace)

    Returns:
        QuackContext containing all initialized components

    Raises:
        QuackError: If initialization fails
    """
    try:
        base_directory = Path(base_dir) if base_dir else find_project_root()
        effective_config_path = config_path
        cfg = load_config(effective_config_path, cli_args, environment)

        if debug:
            cfg.general.debug = True
        if verbose:
            cfg.general.verbose = True

        logger, get_logger = setup_logging(log_level, debug, quiet, cfg, app_name)
        env = os.environ.get("QUACK_ENV", "development").lower()

        logger.debug(f"QuackCore CLI initialized in {env} environment")
        logger.debug(f"Base directory: {base_directory}")
        if effective_config_path:
            logger.debug(f"Config loaded from: {effective_config_path}")

        return QuackContext(
            config=cfg,
            logger=logger,
            base_dir=base_directory,
            environment=env,
            debug=debug,
            verbose=verbose,
            working_dir=Path.cwd(),
        )

    except QuackError as e:
        logging.error(f"Failed to initialize CLI environment: {e}")
        raise
    except Exception as e:
        error = QuackError(f"Unexpected error initializing CLI environment: {e}")
        logging.error(str(error))
        raise error from e


def from_cli_options(
    options: CliOptions,
    cli_args: Mapping[str, Any] | None = None,
    app_name: str = "quack",
) -> QuackContext:
    """
    Initialize CLI environment from a CliOptions object.

    This is a convenience function for frameworks that already parse options
    into a structured object.

    Args:
        options: Parsed CLI options
        cli_args: Additional CLI arguments to apply as config overrides
        app_name: Application name (used for the logger namespace)

    Returns:
        Initialized QuackContext
    """
    return init_cli_env(
        config_path=options.config_path,
        log_level=options.log_level,
        debug=options.debug,
        verbose=options.verbose,
        quiet=options.quiet,
        environment=options.environment,
        base_dir=options.base_dir,
        cli_args=cli_args,
        app_name=app_name,
    )
