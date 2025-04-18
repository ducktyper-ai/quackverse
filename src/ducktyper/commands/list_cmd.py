# src/ducktyper/commands/list_cmd.py
"""
Implementation of the 'list' command.

The list command displays all available QuackTools.
"""

import json
import sys
from typing import Optional

import typer
from quackcore.cli import CliContext
from quackcore.plugins.registry import list_plugins

from ducktyper.ui.branding import print_banner, print_error, print_info, retro_table
from ducktyper.ui.mode import is_playful_mode

# Create Typer app for the list command
app = typer.Typer(
    name="list",
    help="List all available QuackTools.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def list_tools(
        ctx: typer.Context,
        type_filter: Optional[str] = typer.Option(
            None, "--type", "-t", help="Filter by tool type"
        ),
        output_json: bool = typer.Option(
            False, "--json", "-j", help="Output as JSON"
        ),
) -> None:
    """
    List all available QuackTools.

    By default, displays a table with tool name, type, and description.
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    try:
        # Get all plugins from registry
        plugins = list_plugins()

        # Filter by type if requested
        if type_filter:
            plugins = [p for p in plugins if getattr(p, "type", None) == type_filter]

        if not plugins:
            if type_filter:
                print_info(f"No QuackTools of type '{type_filter}' found.")
            else:
                print_info("No QuackTools found.")
            return

        # Format as JSON if requested
        if output_json:
            plugin_data = []
            for plugin in plugins:
                plugin_info = {
                    "name": plugin.name,
                    "type": getattr(plugin, "type", "unknown"),
                    "description": getattr(plugin, "description",
                                           "No description available."),
                    "version": getattr(plugin, "version", "unknown"),
                }
                plugin_data.append(plugin_info)

            print(json.dumps(plugin_data, indent=2))
            return

        # Display as table
        if is_playful_mode():
            print_banner("Available QuackTools", "Your magical spell collection")
        else:
            print_info("Available QuackTools:")

        # Prepare table data
        headers = ["Name", "Type", "Description", "Version"]
        rows = []

        for plugin in plugins:
            name = plugin.name
            plugin_type = getattr(plugin, "type", "unknown")
            description = getattr(plugin, "description", "No description available.")
            version = getattr(plugin, "version", "unknown")

            rows.append([name, plugin_type, description, version])

        # Display the table
        retro_table(headers, rows, title="QuackTools")

    except Exception as e:
        print_error(f"Error listing QuackTools: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception("Error in list command")
        sys.exit(1)