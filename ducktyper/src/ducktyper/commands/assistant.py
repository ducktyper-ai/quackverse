# ducktyper/src/ducktyper/commands/assistant.py
"""
Implementation of the 'assistant' command.

The assistant command provides a chat-like interactive terminal assistant
powered by LLMs from the QuackCore integration.
"""

import os
import re
import shlex
import subprocess
import sys
import time
from typing import Any

import typer
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from ducktyper.src.ducktyper.ui.mode import is_playful_mode
from ducktyper.ui.branding import (
    COLOR_PALETTE,
    print_banner,
    print_error,
    print_info,
    print_warning,
    quack_say,
    retro_box,
)
from quackcore.cli import CliContext
from quackcore.integrations.llms import (
    ChatMessage,
    LLMIntegration,
    LLMOptions,
    RoleType,
)
from quackcore.plugins.registry import list_plugins

# Create Typer app for the assistant command
app = typer.Typer(
    name="assistant",
    help="Start an interactive AI assistant in the terminal.",
    add_completion=False,
)

# Create console for rich output
console = Console()


class Assistant:
    """DuckTyper AI assistant."""

    def __init__(self, cli_env: CliContext):
        """
        Initialize the assistant.

        Args:
            cli_env: The CLI environment context
        """
        self.cli_env = cli_env
        self.conversation: list[ChatMessage] = []
        self.llm: LLMIntegration | None = None
        self.history: list[
            tuple[str, str]] = []  # Store (user_input, assistant_response) pairs

        # Commands that can be executed directly from the assistant
        self.commands: dict[str, Any] = {
            "!help": self.cmd_help,
            "!exit": self.cmd_exit,
            "!quit": self.cmd_exit,
            "!history": self.cmd_history,
            "!clear": self.cmd_clear,
            "!run": self.cmd_run,
            "!list": self.cmd_list,
        }

    def initialize(self) -> bool:
        """
        Initialize the LLM integration.

        Returns:
            True if initialization was successful, False otherwise
        """
        try:
            # Initialize LLM integration
            self.llm = LLMIntegration()
            init_result = self.llm.initialize()

            if not init_result.success:
                print_error(f"Failed to initialize LLM: {init_result.error}")
                return False

            # Add system prompt
            system_prompt = self._get_system_prompt()
            self.conversation.append(
                ChatMessage(role=RoleType.SYSTEM, content=system_prompt)
            )

            return True

        except Exception as e:
            print_error(f"Error initializing assistant: {str(e)}")
            if self.cli_env.debug:
                self.cli_env.logger.exception("Error initializing assistant")
            return False

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the assistant.

        Returns:
            System prompt string
        """
        # Get list of available tools
        plugins = list_plugins()
        plugin_names = [p.name for p in plugins]
        plugin_info = []

        for plugin in plugins:
            description = getattr(plugin, "description", "No description available.")
            commands = []

            if hasattr(plugin, "list_commands") and callable(plugin.list_commands):
                commands = plugin.list_commands()

            plugin_info.append(
                f"- {plugin.name}: {description}" +
                (f" (Commands: {', '.join(commands)})" if commands else "")
            )

        # Build system prompt
        prompt = f"""You are DuckTyper's AI assistant, a helpful and friendly guide to the QuackVerse ecosystem.

Available QuackTools:
{chr(10).join(plugin_info)}

You can help users with:
- Explaining how to use QuackTools
- Suggesting tools for specific tasks
- Providing code examples
- Answering questions about the QuackVerse ecosystem

The user can run commands directly from this chat using special commands:
- !run <tool-name> [args...] - Run a QuackTool
- !list - List available QuackTools
- !help - Show help for the assistant
- !history - Show conversation history
- !clear - Clear the conversation history
- !exit or !quit - Exit the assistant

When a user asks how to perform a task, suggest relevant QuackTools and explain how to use them.
Be concise but helpful, and use markdown formatting for code examples and explanations.
"""
        return prompt

    def run(self) -> None:
        """Run the assistant in an interactive loop."""
        try:
            # Show welcome message
            if is_playful_mode():
                print_banner("DuckTyper AI Assistant", "Your friendly terminal buddy",
                             mood="wizard")
                quack_say(
                    "Hello! I'm your magical assistant. How can I help you today?")
                print_info("Type '!help' for available commands or '!exit' to quit.")
            else:
                print_info("DuckTyper AI Assistant")
                print_info("Type '!help' for available commands or '!exit' to quit.")

            # Main interaction loop
            while True:
                # Get user input
                user_input = Prompt.ask("\n[bold]You[/bold]")

                # Skip empty input
                if not user_input.strip():
                    continue

                # Check if it's a special command
                if user_input.startswith("!"):
                    command_parts = shlex.split(user_input)
                    command = command_parts[0]
                    args = command_parts[1:] if len(command_parts) > 1 else []

                    if command in self.commands:
                        # Execute command
                        if self.commands[command](args):
                            continue
                        else:
                            # Exit if command returns False
                            break
                    else:
                        print_warning(f"Unknown command: {command}")
                        continue

                # Regular chat interaction
                self._chat(user_input)

        except KeyboardInterrupt:
            print("\nAssistant closed.")
        except Exception as e:
            print_error(f"Error in assistant: {str(e)}")
            if self.cli_env.debug:
                self.cli_env.logger.exception("Error in assistant")

    def _chat(self, user_input: str) -> None:
        """
        Process a chat message from the user.

        Args:
            user_input: The user's input message
        """
        if not self.llm:
            print_error("LLM integration not initialized")
            return

        # Add user message to conversation
        self.conversation.append(
            ChatMessage(role=RoleType.USER, content=user_input)
        )

        # Show thinking indicator
        with console.status("[bold green]Thinking...") as status:
            # Stream the response if we're in teaching mode
            if is_playful_mode():
                # Configure streaming
                options = LLMOptions(stream=True)
                response_chunks = []

                # Start a Live display for streaming response
                with Live(Panel("", title="[bold]DuckTyper[/bold]",
                                border_style=COLOR_PALETTE["primary"]),
                          refresh_per_second=10) as live:
                    # Define callback for streaming
                    def stream_callback(chunk: str) -> None:
                        nonlocal response_chunks
                        response_chunks.append(chunk)
                        # Update the Live display with the accumulated response
                        text = "".join(response_chunks)
                        # Render markdown if content looks like markdown
                        try:
                            if re.search(r"```|##|\*\*|\*|\[|\]\(", text):
                                live.update(Panel(Markdown(text),
                                                  title="[bold]DuckTyper[/bold]",
                                                  border_style=COLOR_PALETTE[
                                                      "primary"]))
                            else:
                                live.update(Panel(text, title="[bold]DuckTyper[/bold]",
                                                  border_style=COLOR_PALETTE[
                                                      "primary"]))
                        except Exception:
                            # Fall back to plain text if markdown parsing fails
                            live.update(Panel(text, title="[bold]DuckTyper[/bold]",
                                              border_style=COLOR_PALETTE["primary"]))

                    # Get response (streaming)
                    result = self.llm.chat(self.conversation, options,
                                           callback=stream_callback)

                    # Sleep briefly to ensure final update is visible
                    time.sleep(0.1)
            else:
                # Non-streaming for production mode
                result = self.llm.chat(self.conversation)
                response_chunks = [result.content] if result.success else [
                    f"Error: {result.error}"]

        # Process the result
        if result.success:
            response_text = "".join(response_chunks)

            # Add assistant response to conversation
            self.conversation.append(
                ChatMessage(role=RoleType.ASSISTANT, content=response_text)
            )

            # Add to history
            self.history.append((user_input, response_text))

            # In production mode, print the response (it wasn't streamed)
            if not is_playful_mode():
                if re.search(r"```|##|\*\*|\*|\[|\]\(", response_text):
                    console.print(Markdown(response_text))
                else:
                    console.print(response_text)
        else:
            print_error(f"Error getting response: {result.error}")

    def cmd_help(self, args: list[str]) -> bool:
        """
        Show help information for assistant commands.

        Args:
            args: Command arguments (unused)

        Returns:
            True to continue the assistant loop
        """
        if is_playful_mode():
            retro_box("🔮 Assistant Commands", """
!help - Show this help message
!exit, !quit - Exit the assistant
!history - Show conversation history
!clear - Clear the conversation history
!run <tool-name> [args...] - Run a QuackTool directly
!list - List available QuackTools

You can also just chat naturally with me about:
- How to use QuackTools
- Getting recommendations for specific tasks
- Learning about the QuackVerse ecosystem
- Code examples and explanations
""")
        else:
            print_info("\nAvailable Commands:")
            print_info("  !help - Show this help message")
            print_info("  !exit, !quit - Exit the assistant")
            print_info("  !history - Show conversation history")
            print_info("  !clear - Clear the conversation history")
            print_info("  !run <tool-name> [args...] - Run a QuackTool directly")
            print_info("  !list - List available QuackTools")

        return True

    def cmd_exit(self, args: list[str]) -> bool:
        """
        Exit the assistant.

        Args:
            args: Command arguments (unused)

        Returns:
            False to exit the assistant loop
        """
        if is_playful_mode():
            quack_say("Thanks for chatting! Quack you later! 🦆", mood="happy")
        else:
            print_info("Assistant closed.")

        return False

    def cmd_history(self, args: list[str]) -> bool:
        """
        Show conversation history.

        Args:
            args: Command arguments (unused)

        Returns:
            True to continue the assistant loop
        """
        if not self.history:
            print_info("No conversation history yet.")
            return True

        if is_playful_mode():
            print_banner("Conversation History", mood="wizard")

            for i, (user_msg, assistant_msg) in enumerate(self.history, 1):
                # Truncate long messages for display
                user_preview = (user_msg[:100] + "...") if len(
                    user_msg) > 100 else user_msg
                assistant_preview = (assistant_msg[:100] + "...") if len(
                    assistant_msg) > 100 else assistant_msg

                retro_box(
                    f"Exchange {i}",
                    f"[bold]You:[/bold] {user_preview}\n\n[bold]DuckTyper:[/bold] {assistant_preview}"
                )
        else:
            print_info("\nConversation History:")

            for i, (user_msg, assistant_msg) in enumerate(self.history, 1):
                print_info(f"\n--- Exchange {i} ---")
                print_info(f"You: {user_msg}")
                print_info(f"DuckTyper: {assistant_msg}")

        return True

    def cmd_clear(self, args: list[str]) -> bool:
        """
        Clear conversation history.

        Args:
            args: Command arguments (unused)

        Returns:
            True to continue the assistant loop
        """
        # Keep the system prompt but clear everything else
        system_prompt = self.conversation[0] if self.conversation else None
        self.conversation = [system_prompt] if system_prompt else []
        self.history = []

        if is_playful_mode():
            quack_say("✨ Conversation history cleared! Let's start fresh.",
                      mood="happy")
        else:
            print_info("Conversation history cleared.")

        return True

    def cmd_run(self, args: list[str]) -> bool:
        """
        Run a QuackTool directly from the assistant.

        Args:
            args: Command arguments (tool name and arguments)

        Returns:
            True to continue the assistant loop
        """
        if not args:
            print_warning(
                "Please specify a tool to run. Usage: !run <tool-name> [args...]")
            return True

        tool_name = args[0]
        tool_args = args[1:] if len(args) > 1 else []

        try:
            # Construct command
            cmd = ["tests", "run", tool_name] + tool_args

            if is_playful_mode():
                quack_say(f"Running: {' '.join(cmd)}", mood="wizard")
            else:
                print_info(f"Running: {' '.join(cmd)}")

            # Execute the command
            result = subprocess.run(cmd, capture_output=False)

            if result.returncode != 0:
                print_warning(f"Command exited with code {result.returncode}")

        except Exception as e:
            print_error(f"Error running tool: {str(e)}")

        return True

    def cmd_list(self, args: list[str]) -> bool:
        """
        List available QuackTools.

        Args:
            args: Command arguments (unused)

        Returns:
            True to continue the assistant loop
        """
        try:
            # Run the list command
            cmd = ["tests", "list"]

            if is_playful_mode():
                quack_say("Let me show you the available QuackTools:", mood="wizard")
            else:
                print_info("Available QuackTools:")

            # Execute the command
            subprocess.run(cmd, capture_output=False)

        except Exception as e:
            print_error(f"Error listing tools: {str(e)}")

        return True


@app.callback(invoke_without_command=True)
def start_assistant(
        ctx: typer.Context,
        model: str | None = typer.Option(
            None, "--model", "-m", help="LLM model to use"
        ),
        provider: str | None = typer.Option(
            None, "--provider", "-p", help="LLM provider to use"
        ),
) -> None:
    """
    Start an interactive AI assistant in the terminal.

    The assistant can help with QuackVerse tools, providing explanations,
    examples, and recommendations.
    """
    # Get CLI context from parent
    obj = ctx.obj or {}
    cli_env: CliContext = obj.get("cli_env")

    if cli_env is None:
        print_error("Failed to initialize CLI environment")
        sys.exit(1)

    # Set environment variables for LLM if provided
    if model:
        os.environ["QUACK_LLM_DEFAULT_MODEL"] = model

    if provider:
        os.environ["QUACK_LLM_DEFAULT_PROVIDER"] = provider

    try:
        # Initialize assistant
        assistant = Assistant(cli_env)

        if not assistant.initialize():
            print_error("Failed to initialize assistant. Check your LLM configuration.")
            sys.exit(1)

        # Run assistant loop
        assistant.run()

    except KeyboardInterrupt:
        print("\nAssistant closed.")
    except Exception as e:
        print_error(f"Error in assistant: {str(e)}")
        if cli_env.debug:
            cli_env.logger.exception("Error in assistant command")
        sys.exit(1)
