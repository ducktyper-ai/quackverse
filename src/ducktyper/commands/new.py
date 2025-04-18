# src/ducktyper/commands/new.py
"""
Implementation of the 'new' command.

The new command scaffolds a new QuackTool from a template.
"""

import os
import re
import sys
from pathlib import Path
from typing import Optional

import jinja2
import typer
from quackcore.cli import CliContext
from rich.prompt import Confirm, Prompt

from ducktyper.ui.branding import (
    get_retro_progress,
    print_banner,
    print_error,
    print_info,
    print_success,
    quack_say,
    retro_box,
)
from ducktyper.ui.mode import is_playful_mode

# Create Typer app for the new command
app = typer.Typer(
    name="new",
    help="Scaffold a new QuackTool.",
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def create_new_tool(
        ctx: typer.Context,
        tool_name: str = typer.Argument(..., help="Name of the new tool to create"),
        output_dir: Optional[str] = typer.Option(
            None, "--output", "-o", help="Output directory for the new tool"
        ),
        template: str = typer.Option(
            "default", "--template", "-t", help="Template to use for scaffolding"
        ),
        description: Optional[str] = typer.Option(
            None, "--description", "-d", help="Short description of the tool"
        ),
) -> None:
    """
    Scaffold a new QuackTool from a template.

    Creates a new QuackTool project with the basic structure and files needed.
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    try:
        # Validate tool name
        if not re.match(r"^[a-z][a-z0-9_-]*$", tool_name):
            print_error(
                f"Invalid tool name: '{tool_name}'. Use lowercase letters, numbers, underscores, or hyphens.")
            sys.exit(1)

        # Normalize tool name
        normalized_name = tool_name.replace("-", "_")
        package_name = f"quack_{normalized_name}"
        class_name = "".join(word.capitalize() for word in normalized_name.split("_"))

        # Get template dir
        template_dir = Path(__file__).parent.parent / "templates" / template

        if not template_dir.exists():
            print_error(f"Template '{template}' not found.")
            sys.exit(1)

        # Determine output directory
        if output_dir is None:
            output_dir = os.getcwd()

        output_path = Path(output_dir) / package_name

        # Check if output directory already exists
        if output_path.exists():
            if not Confirm.ask(f"Directory '{output_path}' already exists. Overwrite?"):
                print_info("Operation cancelled.")
                return

        # Get description if not provided
        if description is None:
            description = Prompt.ask("Enter a short description of your tool",
                                     default=f"A QuackTool for {tool_name}")

        # Prepare context for templates
        template_context = {
            "tool_name": tool_name,
            "normalized_name": normalized_name,
            "package_name": package_name,
            "class_name": class_name,
            "description": description,
            "author": os.environ.get("USER", "QuackTool Developer"),
        }

        # Create template environment
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            keep_trailing_newline=True,
        )

        # Show banner
        if is_playful_mode():
            print_banner(f"Creating New QuackTool: {tool_name}", description,
                         mood="wizard")
            quack_say("Let's craft a new magical tool for the QuackVerse!")
        else:
            print_info(f"Creating new QuackTool: {tool_name}")
            print_info(f"Description: {description}")

        # Create output directory
        output_path.mkdir(parents=True, exist_ok=True)

        # Find template files
        template_files = []
        for root, _, files in os.walk(template_dir):
            rel_dir = os.path.relpath(root, template_dir)
            for file in files:
                if file.endswith(".template"):
                    rel_path = os.path.join(rel_dir, file)
                    template_files.append(rel_path)

        # Process templates with progress bar
        with get_retro_progress(total=len(template_files), description="Creating files",
                                unit="files") as progress:
            task = progress.add_task("Creating files", total=len(template_files))

            for template_file in template_files:
                # Replace template variables in path
                relative_path = template_file
                for var_name, var_value in template_context.items():
                    if isinstance(var_value, str):
                        relative_path = relative_path.replace(f"{{{var_name}}}",
                                                              var_value)

                # Remove .template suffix
                output_file = relative_path.replace(".template", "")

                # Create directory if needed
                os.makedirs(os.path.dirname(output_path / output_file), exist_ok=True)

                # Render template
                template = env.get_template(template_file)
                rendered = template.render(**template_context)

                # Write output file
                with open(output_path / output_file, "w") as f:
                    f.write(rendered)

                # Update progress
                progress.update(task, advance=1, description=f"Created {output_file}")

        # Success message
        if is_playful_mode():
            print_success(f"✨ Your new QuackTool '{tool_name}' is ready!")
            retro_box("Next Steps", f"""
1. Navigate to your new tool:
   cd {output_path}

2. Install it in development mode:
   pip install -e .

3. Try it out:
   ducktyper run {tool_name}
""")
        else:
            print_success(f"QuackTool '{tool_name}' created in {output_path}")
            print_info("\nNext steps:")
            print_info(f"1. cd {output_path}")
            print_info("2. pip install -e .")
            print_info(f"3. ducktyper run {tool_name}")

    except Exception as e:
        print_error(f"Error creating new tool: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception("Error in new command")
        sys.exit(1)