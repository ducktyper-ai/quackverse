# ducktyper/src/ducktyper/commands/config.py
"""
Implementation of the 'config' command.

The config command allows viewing and editing DuckTyper configuration.
"""

import os
import subprocess
import sys
from pathlib import Path

import typer
import yaml

from ducktyper.ui.branding import (
    print_banner,
    print_error,
    print_info,
    print_success,
    print_warning,
    quack_say,
    retro_box,
)
from ducktyper.ui.mode import is_playful_mode
from ducktyper.ui.styling import format_dict_for_display
from quackcore.cli import CliContext

# Create Typer app for the config command
app = typer.Typer(
    name="config",
    help="Manage DuckTyper configuration.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def config_callback(ctx: typer.Context) -> None:
    """
    Manage DuckTyper configuration.

    View, edit, or set configuration values.
    """
    # Only show help if no subcommand is invoked
    if ctx.invoked_subcommand is None:
        if is_playful_mode():
            print_banner("DuckTyper Configuration", "Manage your magical settings",
                         mood="wizard")
            quack_say(
                "Use a subcommand to view or edit configuration. Type 'tests config --help' for options.")
        else:
            print_info("DuckTyper Configuration")
            print_info("Use a subcommand to view or edit configuration.")


@app.command("show")
def show_config(
        ctx: typer.Context,
        section: str | None = typer.Option(
            None, "--section", "-s", help="Show only specified config section"
        ),
) -> None:
    """
    Display the current configuration.
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    try:
        # Get config as dictionary
        config_dict = cli_env.config.model_dump()

        # Get config file location
        config_source = getattr(cli_env.config, "source_path", "Default configuration")

        if is_playful_mode():
            print_banner("DuckTyper Configuration", f"Source: {config_source}",
                         mood="wizard")
        else:
            print_info(f"Configuration source: {config_source}")

        # Show only specific section if requested
        if section:
            if section in config_dict:
                section_data = config_dict[section]

                if is_playful_mode():
                    retro_box(f"Configuration Section: {section}",
                              format_dict_for_display(section_data))
                else:
                    print_info(f"\nConfiguration Section: {section}")
                    print(format_dict_for_display(section_data))
            else:
                available_sections = ", ".join(config_dict.keys())
                print_error(
                    f"Section '{section}' not found. Available sections: {available_sections}")
                sys.exit(1)
        else:
            # Show all sections
            if is_playful_mode():
                for section_name, section_data in config_dict.items():
                    if isinstance(section_data, dict) and section_data:
                        retro_box(f"Configuration Section: {section_name}",
                                  format_dict_for_display(section_data))
            else:
                # Simpler display for production mode
                print_info("\nConfiguration:")
                print(format_dict_for_display(config_dict))

    except Exception as e:
        print_error(f"Error displaying configuration: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception("Error in config show command")
        sys.exit(1)


@app.command("set")
def set_config(
        ctx: typer.Context,
        key_value: str = typer.Argument(...,
                                        help="Config key and value in format 'key=value'"),
) -> None:
    """
    Set a configuration value.

    Example: tests config set llm.provider=openai
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    try:
        # Parse key=value format
        if "=" not in key_value:
            print_error(
                "Invalid format. Use 'key=value' format (e.g., 'llm.provider=openai')")
            sys.exit(1)

        key, value = key_value.split("=", 1)

        # Convert nested keys (e.g., "llm.provider") to dictionary path
        key_parts = key.split(".")

        # Attempt to parse value (handle booleans, numbers, etc.)
        try:
            # Try to parse as YAML for type conversion
            parsed_value = yaml.safe_load(value)

            # Special case for empty string
            if value == "" and parsed_value is None:
                parsed_value = ""
        except Exception:
            # Fall back to string if parsing fails
            parsed_value = value

        # Reload config to make sure we have latest
        config_path = getattr(cli_env.config, "source_path", None)

        if not config_path:
            print_error("No configuration file found to modify.")
            sys.exit(1)

        config_dict = {}
        try:
            with open(config_path) as f:
                config_dict = yaml.safe_load(f) or {}
        except FileNotFoundError:
            # Create new config file if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

        # Navigate to the right part of the config
        current = config_dict
        for i, part in enumerate(key_parts[:-1]):
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                path_so_far = ".".join(key_parts[:i + 1])
                print_error(
                    f"Cannot set '{key}' because '{path_so_far}' is not a dictionary.")
                sys.exit(1)
            current = current[part]

        # Set the value
        current[key_parts[-1]] = parsed_value

        # Write updated config
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)

        if is_playful_mode():
            quack_say(f"Configuration updated! Set {key}={value}")
        else:
            print_success(f"Configuration updated: {key}={value}")

    except Exception as e:
        print_error(f"Error setting configuration: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception("Error in config set command")
        sys.exit(1)


@app.command("edit")
def edit_config(
        ctx: typer.Context,
) -> None:
    """
    Open the configuration file in your default editor.
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    try:
        # Get config file path
        config_path = getattr(cli_env.config, "source_path", None)

        if not config_path:
            # Try to create default config path
            default_config_dir = Path.home() / ".quack"
            default_config_dir.mkdir(exist_ok=True)
            config_path = default_config_dir / "config.yaml"

            # Create empty config file if it doesn't exist
            if not config_path.exists():
                with open(config_path, "w") as f:
                    yaml.dump({
                        "tests": {
                            "mode": "teaching",
                            "always_dance": False,
                        }
                    }, f, default_flow_style=False)

        # Check if file exists
        if not os.path.exists(config_path):
            print_warning(
                f"Configuration file '{config_path}' does not exist. Creating a new one.")

            # Create directory if needed
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            # Create empty file
            with open(config_path, "w") as f:
                yaml.dump({
                    "tests": {
                        "mode": "teaching",
                        "always_dance": False,
                    }
                }, f, default_flow_style=False)

        # Get editor command
        editor = os.environ.get("EDITOR", os.environ.get("VISUAL", "nano"))

        if is_playful_mode():
            quack_say(f"Opening configuration file with {editor}...")
        else:
            print_info(f"Opening configuration file: {config_path}")

        # Open editor
        try:
            subprocess.run([editor, str(config_path)], check=True)
            if is_playful_mode():
                print_success("Configuration file updated successfully!")
            else:
                print_info("Configuration file edited.")
        except subprocess.SubprocessError as e:
            print_error(f"Failed to open editor: {str(e)}")
            sys.exit(1)

    except Exception as e:
        print_error(f"Error editing configuration: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception("Error in config edit command")
        sys.exit(1)
