# src/ducktyper/commands/explain.py
"""
Implementation of the 'explain' command.

The explain command shows documentation and help for a specified QuackTool.
"""

import sys

import typer
from quackcore.cli import CliContext
from quackcore.plugins.registry import get_plugin

from ducktyper.ui.branding import (
    print_banner,
    print_error,
    print_info,
    quack_say,
    retro_box,
    retro_table,
)
from ducktyper.ui.mode import is_playful_mode
from ducktyper.ui.styling import format_dict_for_display

# Create Typer app for the explain command
app = typer.Typer(
    name="explain",
    help="Show documentation for a QuackTool.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def explain_tool(
        ctx: typer.Context,
        tool_name: str = typer.Argument(..., help="Name of the tool to explain"),
        show_examples: bool = typer.Option(
            False, "--examples", "-e", help="Show usage examples"
        ),
        show_config: bool = typer.Option(
            False, "--config", "-c", help="Show configuration options"
        ),
) -> None:
    """
    Show documentation and help for a QuackTool.

    Displays name, type, description, commands, and usage information.
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    try:
        # Get the plugin from registry
        plugin = get_plugin(tool_name)

        if plugin is None:
            print_error(
                f"Tool '{tool_name}' not found. Run 'ducktyper list' to see available tools.")
            sys.exit(1)

        # Get tool metadata
        tool_type = getattr(plugin, "type", "unknown")
        tool_description = getattr(plugin, "description", "No description available.")
        tool_version = getattr(plugin, "version", "unknown")

        # Display tool info
        if is_playful_mode():
            print_banner(f"QuackTool: {tool_name}",
                         f"Type: {tool_type} | Version: {tool_version}", mood="wizard")
            quack_say(f"Let me explain the {tool_name} spell for you!")

            # Main description
            retro_box("📖 Description", tool_description, icon="✨")
        else:
            print_info(f"QuackTool: {tool_name}")
            print_info(f"Type: {tool_type}")
            print_info(f"Version: {tool_version}")
            print_info(f"Description: {tool_description}")

        # List commands if available
        if hasattr(plugin, "list_commands") and callable(plugin.list_commands):
            commands = plugin.list_commands()

            if commands:
                command_info = []

                for cmd_name in commands:
                    cmd_description = "No description available."

                    # Try to get command function and extract its docstring
                    if hasattr(plugin, "get_command") and callable(plugin.get_command):
                        cmd_func = plugin.get_command(cmd_name)

                        if cmd_func and cmd_func.__doc__:
                            cmd_description = cmd_func.__doc__.strip().split("\n")[0]

                    command_info.append([cmd_name, cmd_description])

                # Display commands
                if is_playful_mode():
                    retro_box("🔧 Available Commands",
                              "These are the magical incantations this tool provides:")
                    retro_table(["Command", "Description"], command_info)
                else:
                    print_info("\nAvailable Commands:")
                    retro_table(["Command", "Description"], command_info)

        # Show configuration if available and requested
        if show_config and hasattr(plugin, "get_config_schema") and callable(
                plugin.get_config_schema):
            config_schema = plugin.get_config_schema()

            if config_schema:
                if is_playful_mode():
                    retro_box("⚙️ Configuration Options",
                              "Customize your spell with these settings:")
                else:
                    print_info("\nConfiguration Options:")

                # Display configuration schema in a readable format
                if isinstance(config_schema, dict):
                    if is_playful_mode():
                        config_text = format_dict_for_display(config_schema)
                        retro_box("Configuration Schema", config_text)
                    else:
                        print(format_dict_for_display(config_schema))

        # Show examples if available and requested
        if show_examples and hasattr(plugin, "get_examples") and callable(
                plugin.get_examples):
            examples = plugin.get_examples()

            if examples:
                if is_playful_mode():
                    retro_box("📋 Usage Examples",
                              "Here's how to use this magical tool:")
                else:
                    print_info("\nUsage Examples:")

                for i, example in enumerate(examples, 1):
                    title = example.get("title", f"Example {i}")
                    code = example.get("code", "")
                    description = example.get("description", "")

                    if is_playful_mode():
                        retro_box(f"Example {i}: {title}",
                                  f"{description}\n\n```\n{code}\n```")
                    else:
                        print_info(f"\nExample {i}: {title}")
                        if description:
                            print_info(description)
                        print(f"\n```\n{code}\n```\n")

        # If no examples were shown but requested
        elif show_examples:
            if is_playful_mode():
                quack_say("This tool doesn't provide any usage examples yet.")
            else:
                print_info("No examples available for this tool.")

    except Exception as e:
        print_error(f"Error explaining tool '{tool_name}': {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception(f"Error in explain command for tool '{tool_name}'")
        sys.exit(1)