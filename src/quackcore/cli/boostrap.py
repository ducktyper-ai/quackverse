"""
CLI bootstrapper for QuackCore.

This module provides utilities for initializing CLI applications with consistent
configuration, logging, and environment setup. It serves as the foundation for
all QuackVerse CLI tools, ensuring a unified developer experience.
"""

import logging
import os
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal, Protocol, TypeVar, cast

from pydantic import BaseModel, Field

from quackcore.config import QuackConfig
from quackcore.config import load_config as quack_load_config
from quackcore.config.utils import get_env, load_env_config, normalize_paths
from quackcore.errors import QuackConfigurationError, QuackError
from quackcore.fs import service as fs
from quackcore.paths import resolver as path_resolver

T = TypeVar("T")

# Define LogLevel type for better type checking
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@dataclass(frozen=True)
class QuackContext:
    """
    Runtime context for QuackCore CLI applications.

    This class encapsulates all the runtime information needed by CLI commands,
    including configuration, logging, paths, and environment metadata.
    """

    config: QuackConfig
    """Loaded and normalized configuration."""

    logger: logging.Logger
    """Configured logger for the CLI application."""

    base_dir: Path
    """Base directory for the application."""

    environment: str
    """Current environment (development, test, production)."""

    debug: bool = False
    """Whether debug mode is enabled."""

    verbose: bool = False
    """Whether verbose output is enabled."""

    working_dir: Path = field(default_factory=Path.cwd)
    """Current working directory."""

    extra: dict[str, Any] = field(default_factory=dict)
    """Additional context data that might be needed by specific commands."""

    def with_extra(self, **kwargs: object) -> "QuackContext":
        """
        Create a new context with additional extra data.

        This method allows for immutable updates to the context's extra data,
        returning a new context instance with the updated values.

        Args:
            **kwargs: Key-value pairs to add to the extra dictionary

        Returns:
            A new QuackContext with the updated extra dictionary
        """
        new_extra = self.extra.copy()
        new_extra.update(kwargs)
        return QuackContext(
            config=self.config,
            logger=self.logger,
            base_dir=self.base_dir,
            environment=self.environment,
            debug=self.debug,
            verbose=self.verbose,
            working_dir=self.working_dir,
            extra=new_extra,
        )


class CliOptions(BaseModel):
    """
    CLI options that can affect bootstrapping behavior.

    This model represents command-line options that can override configuration
    and control runtime behavior like logging and debugging.
    """

    config_path: Path | None = Field(
        default=None, description="Path to configuration file"
    )
    log_level: LogLevel | None = Field(default=None, description="Logging level")
    debug: bool = Field(default=False, description="Enable debug mode")
    verbose: bool = Field(default=False, description="Enable verbose output")
    quiet: bool = Field(default=False, description="Suppress non-error output")
    environment: str | None = Field(
        default=None, description="Override the environment"
    )
    base_dir: Path | None = Field(
        default=None, description="Override the base directory"
    )
    no_color: bool = Field(default=False, description="Disable colored output")

    model_config = {
        "frozen": True,
        "extra": "ignore",
    }


class LoggerFactory(Protocol):
    """Protocol for logger factory functions."""

    def __call__(self, name: str) -> logging.Logger:
        """
        Create or get a logger with the given name.

        Args:
            name: The name of the logger

        Returns:
            A configured logger instance
        """
        ...


def _determine_effective_level(
    cli_log_level: LogLevel | None,
    cli_debug: bool,
    cli_quiet: bool,
    cfg: QuackConfig | None,
) -> LogLevel:
    """
    Determine the effective logging level.

    Args:
        cli_log_level: Optional logging level override from CLI.
        cli_debug: True if debug flag is set.
        cli_quiet: True if quiet flag is set.
        cfg: Optional configuration with logging settings.

    Returns:
        The effective log level as a string.
    """
    if cli_debug:
        return "DEBUG"
    if cli_quiet:
        return "ERROR"
    if cli_log_level is not None:
        return cli_log_level
    if cfg and cfg.logging.level:
        config_level = cfg.logging.level.upper()
        if config_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            return cast(LogLevel, config_level)
    return "INFO"


def _add_file_handler(
    root_logger: logging.Logger, cfg: QuackConfig, level_value: int
) -> None:
    """
    Add a file handler to the root logger if a log file is specified in the config.

    Args:
        root_logger: The root logger to configure.
        cfg: The configuration containing logging settings.
        level_value: The numeric logging level.
    """
    try:
        log_file = cfg.logging.file
        log_dir = log_file.parent
        fs.create_directory(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(str(log_file))
        file_handler.setLevel(level_value)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)

        root_logger.debug(f"Log file configured: {log_file}")
    except Exception as e:
        root_logger.warning(f"Failed to set up log file: {e}")


def setup_logging(
    log_level: LogLevel | None = None,
    debug: bool = False,
    quiet: bool = False,
    config: QuackConfig | None = None,
    logger_name: str = "quack",
) -> tuple[logging.Logger, LoggerFactory]:
    """
    Set up logging for CLI applications.

    This function configures logging based on CLI flags and configuration settings,
    ensuring consistent logging behavior across all QuackVerse tools.

    Args:
        log_level: Optional logging level (overrides config and other flags)
        debug: Whether debug mode is enabled (sets log level to DEBUG)
        quiet: Whether to suppress non-error output (sets log level to ERROR)
        config: Optional configuration to use for logging setup
        logger_name: Base name for the logger

    Returns:
        A tuple containing:
        - The root logger instance
        - A logger factory function to create named loggers
    """
    effective_level: LogLevel = _determine_effective_level(
        log_level, debug, quiet, config
    )

    root_logger = logging.getLogger(logger_name)
    try:
        level_value = getattr(logging, effective_level)
    except (AttributeError, TypeError):
        level_value = logging.INFO

    root_logger.setLevel(level_value)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level_value)
    if effective_level == "DEBUG":
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
    else:
        formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    if config and config.logging.file:
        _add_file_handler(root_logger, config, level_value)

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(f"{logger_name}.{name}")

    return root_logger, get_logger


def _merge_cli_overrides(
    config: QuackConfig, cli_overrides: Mapping[str, Any]
) -> QuackConfig:
    """
    Merge CLI overrides into the configuration.

    Args:
        config: The base configuration.
        cli_overrides: A mapping of CLI arguments.

    Returns:
        The configuration with overrides merged in.
    """
    override_dict: dict[str, Any] = {}
    for key, value in cli_overrides.items():
        if value is None:
            continue
        if key in ("config", "help", "version"):
            continue
        parts = key.replace("-", "_").split(".")
        current = override_dict
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                current[part] = value
            else:
                current.setdefault(part, {})
                current = current[part]
    if override_dict:
        from quackcore.config.loader import merge_configs

        config = merge_configs(config, override_dict)
    return config


@lru_cache(maxsize=1)
def load_config(
    config_path: str | Path | None = None,
    cli_overrides: Mapping[str, Any] | None = None,
    environment: str | None = None,
) -> QuackConfig:
    """
    Load configuration with standard precedence:
    CLI overrides > environment variables > config file.

    This function is cached to avoid reloading the same configuration
    multiple times during a single run.

    Args:
        config_path: Optional path to config file
        cli_overrides: Optional dict of CLI argument overrides
        environment: Optional environment name to override QUACK_ENV

    Returns:
        Loaded and normalized QuackConfig

    Raises:
        QuackConfigurationError: If configuration loading fails
    """
    if environment:
        os.environ["QUACK_ENV"] = environment

    try:
        config = quack_load_config(config_path)
    except QuackConfigurationError:
        if config_path:
            raise
        config = QuackConfig()

    config = load_env_config(config)

    if cli_overrides:
        config = _merge_cli_overrides(config, cli_overrides)

    return normalize_paths(config)


def find_project_root() -> Path:
    """
    Find the project root directory.

    The project root is determined by checking common markers like
    a git repository, pyproject.toml, or setup.py file.

    Returns:
        Path to the project root
    """
    try:
        return path_resolver.get_project_root()
    except (FileNotFoundError, PermissionError, ValueError, NotImplementedError):
        return Path.cwd()


def init_cli_env(
    *,
    config_path: str | Path | None = None,
    log_level: LogLevel | None = None,
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
        env = get_env()

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


def format_cli_error(error: Exception) -> str:
    """
    Format an error for CLI display.

    Args:
        error: The exception to format

    Returns:
        Formatted error message suitable for CLI output
    """
    if isinstance(error, QuackError):
        message = str(error)
        parts = [message]
        if hasattr(error, "context") and error.context:
            context_lines = []
            for key, value in error.context.items():
                context_lines.append(f"  {key}: {value}")
            if context_lines:
                parts.append("\nContext:")
                parts.extend(context_lines)
        return "\n".join(parts)
    else:
        return str(error)


def resolve_cli_args(args: Sequence[str]) -> dict[str, Any]:
    """
    Parse common CLI arguments into a dictionary.

    This function is useful for libraries that want to handle standard
    QuackCore CLI arguments without using a full argument parser.

    Args:
        args: Sequence of command-line arguments

    Returns:
        Dictionary of parsed arguments
    """
    result: dict[str, Any] = {}
    i = 0
    while i < len(args):
        arg = args[i]
        if arg.startswith("--"):
            name = arg[2:]
            if "=" in name:
                name, value = name.split("=", 1)
                result[name] = value
                i += 1
                continue
            if name in ("debug", "verbose", "quiet", "no-color"):
                result[name] = True
                i += 1
                continue
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                result[name] = args[i + 1]
                i += 2
                continue
            result[name] = True
            i += 1
            continue
        elif arg.startswith("-") and len(arg) == 2:
            flag_map = {"d": "debug", "v": "verbose", "q": "quiet"}
            name = flag_map.get(arg[1], arg[1])
            result[name] = True
            i += 1
            continue
        i += 1
    return result


def ensure_single_instance(app_name: str) -> bool:
    """
    Ensure only one instance of a CLI application is running.

    This is useful for daemons or long-running services that should
    not have multiple instances running concurrently.

    Args:
        app_name: Name of the application

    Returns:
        True if this is the only instance, False otherwise
    """
    import atexit
    import socket
    from tempfile import gettempdir

    temp_dir = gettempdir()
    lock_path = Path(temp_dir) / f"{app_name}.lock"
    port = sum(ord(c) for c in app_name) % 10000 + 10000
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        sock.bind(("127.0.0.1", port))
        lock_path.write_text(str(os.getpid()))

        def cleanup() -> None:
            sock.close()
            try:
                lock_path.unlink()
            except (FileNotFoundError, PermissionError, OSError):
                pass

        atexit.register(cleanup)
        return True

    except OSError:
        return False


def get_terminal_size() -> tuple[int, int]:
    """
    Get the terminal size.

    Returns:
        Tuple of (columns, lines)
    """
    try:
        import shutil

        terminal_size = shutil.get_terminal_size((80, 24))
        return terminal_size.columns, terminal_size.lines
    except (ImportError, OSError):
        return 80, 24


def get_cli_info() -> dict[str, Any]:
    """
    Get information about the CLI environment.

    This function returns a dictionary with various pieces of information
    about the current CLI environment, useful for diagnostics and troubleshooting.

    Returns:
        Dictionary with CLI environment information
    """
    import platform
    from datetime import datetime

    info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "time": datetime.now().isoformat(),
        "pid": os.getpid(),
        "cwd": str(Path.cwd()),
        "environment": get_env(),
    }

    try:
        columns, lines = get_terminal_size()
        info["terminal_size"] = f"{columns}x{lines}"
    except (AttributeError, OSError):
        info["terminal_size"] = "unknown"

    info["username"] = os.environ.get("USER", os.environ.get("USERNAME", "unknown"))
    info["is_ci"] = bool(
        "CI" in os.environ
        or "GITHUB_ACTIONS" in os.environ
        or "GITLAB_CI" in os.environ
    )

    return info
