# ducktyper/src/ducktyper/commands/new.py
"""
Implementation of the 'new' command.

The new command scaffolds a new QuackTool by cloning a template from GitHub.
"""

import os
import re
import sys
from pathlib import Path

import typer
from rich.prompt import Confirm, Prompt

from ducktyper.src.ducktyper.ui.mode import is_playful_mode
from ducktyper.ui.branding import (
    print_banner,
    print_error,
    print_info,
    print_loading,
    print_success,
    quack_say,
    retro_box,
)
from quackcore.cli import CliContext
from quackcore.integrations.core import registry

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
        output_dir: str | None = typer.Option(
            None, "--output", "-o", help="Output directory for the new tool"
        ),
        template_repo: str = typer.Option(
            "tests-ai/quacktool-template", "--template", "-t",
            help="GitHub repository to use as template"
        ),
        description: str | None = typer.Option(
            None, "--description", "-d", help="Short description of the tool"
        ),
) -> None:
    """
    Scaffold a new QuackTool by cloning a template from GitHub.

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
                f"Invalid tool name: '{tool_name}'. Use lowercase letters, numbers, underscores, or hyphens."
            )
            sys.exit(1)

        # Normalize tool name
        normalized_name = tool_name.replace("-", "_")
        package_name = f"quack_{normalized_name}"
        class_name = "".join(word.capitalize() for word in normalized_name.split("_"))

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
            description = Prompt.ask(
                "Enter a short description of your tool",
                default=f"A QuackTool for {tool_name}"
            )

        # Initialize GitHub integration
        github = registry.get_integration("GitHub")
        init_result = github.initialize()

        if not init_result.success:
            print_error(f"Failed to initialize GitHub integration: {init_result.error}")
            print_info(
                "Make sure GITHUB_TOKEN is set in your environment or configuration.")
            sys.exit(1)

        # Show banner
        if is_playful_mode():
            print_banner(f"Creating New QuackTool: {tool_name}", description,
                         mood="wizard")
            quack_say("Let's craft a new magical tool for the QuackVerse!")
        else:
            print_info(f"Creating new QuackTool: {tool_name}")
            print_info(f"Description: {description}")

        # Clone the template repository
        print_loading(f"Cloning template from GitHub: {template_repo}")

        # Get repository information
        repo_result = github.get_repo(template_repo)
        if not repo_result.success:
            print_error(f"Failed to fetch template repository: {repo_result.error}")
            sys.exit(1)

        # Clone repository locally
        # Note: For a full implementation, you would use git commands or PyGithub
        # This is a simplified version that would need to be expanded
        import subprocess

        try:
            # Create output directory
            output_path.mkdir(parents=True, exist_ok=True)

            # Clone the repository
            clone_url = repo_result.content.clone_url
            result = subprocess.run(
                ["git", "clone", clone_url, str(output_path)],
                check=True,
                capture_output=True,
                text=True,
            )

            # Remove .git directory to start fresh
            import shutil
            git_dir = output_path / ".git"
            if git_dir.exists():
                shutil.rmtree(git_dir)

            # Process template files (placeholder replacement)
            template_variables = {
                "{{tool_name}}": tool_name,
                "{{normalized_name}}": normalized_name,
                "{{package_name}}": package_name,
                "{{class_name}}": class_name,
                "{{description}}": description,
                "{{author}}": os.environ.get("USER", "QuackTool Developer"),
            }

            # Replace placeholders in all files
            for root, _, files in os.walk(output_path):
                for file in files:
                    file_path = Path(root) / file

                    # Skip binary files
                    if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.pdf', '.zip')):
                        continue

                    try:
                        with open(file_path, encoding='utf-8') as f:
                            content = f.read()

                        # Replace all placeholders
                        for placeholder, value in template_variables.items():
                            content = content.replace(placeholder, value)

                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                    except UnicodeDecodeError:
                        # Skip files that can't be decoded as text
                        continue

            # Initialize git repository
            subprocess.run(["git", "init"], cwd=output_path, check=True,
                           capture_output=True)

            # Success message
            if is_playful_mode():
                print_success(f"✨ Your new QuackTool '{tool_name}' is ready!")
                retro_box("Next Steps", f"""
1. Navigate to your new tool:
   cd {output_path}

2. Install it in development mode:
   pip install -e .

3. Try it out:
   tests run {tool_name}
""")
            else:
                print_success(f"QuackTool '{tool_name}' created in {output_path}")
                print_info("\nNext steps:")
                print_info(f"1. cd {output_path}")
                print_info("2. pip install -e .")
                print_info(f"3. tests run {tool_name}")

        except subprocess.CalledProcessError as e:
            print_error(f"Git command failed: {e.stderr}")
            sys.exit(1)

    except Exception as e:
        print_error(f"Error creating new tool: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception("Error in new command")
        sys.exit(1)
