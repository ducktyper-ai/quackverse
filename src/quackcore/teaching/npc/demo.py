# src/quackcore/teaching/npc/demo.py
"""
Demo REPL for the Quackster teaching NPC.

This module provides a simple REPL for testing and demonstrating the
Quackster teaching NPC.
"""

import argparse

from quackcore.teaching import quests, utils, xp
from quackcore.teaching.models import XPEvent
from quackcore.teaching.npc import agent
from quackcore.teaching.npc.schema import TeachingNPCInput


def main():
    """Run the Quackster NPC demo."""
    parser = argparse.ArgumentParser(description="Quackster NPC Demo")
    parser.add_argument("--debug", action="store_true", help="Enable debug output")
    parser.add_argument("--username", type=str, help="GitHub username to use")
    parser.add_argument(
        "--reset", action="store_true", help="Reset user progress before starting"
    )
    args = parser.parse_args()

    # Initialize demo environment
    initialize_demo(args)

    # Store conversation history for context
    conversation_history = []

    print("\n" + "=" * 60)
    print("🦆 Welcome to the Quackster Teaching NPC Demo!")
    print("=" * 60)
    print("Type 'exit', 'quit', or 'bye' to end the demo")
    print("Type 'help' for a list of demo commands")
    print("Type 'reset' to reset your progress")
    print("=" * 60 + "\n")

    # Run the REPL
    while True:
        try:
            # Get user input
            user_input = input("\nYou: ")

            # Check for exit command
            if user_input.lower() in ("exit", "quit", "bye"):
                print("\n🦆 Quackster: Quack for now! Come back soon!")
                break

            # Check for special commands
            if user_input.lower() == "help":
                show_help()
                continue

            if user_input.lower() == "reset":
                utils.reset_progress()
                print("\n🦆 Quackster: Your progress has been reset!")
                conversation_history = []
                continue

            if user_input.lower() == "debug":
                args.debug = not args.debug
                print(
                    f"\n🦆 Quackster: Debug mode {'enabled' if args.debug else 'disabled'}!"
                )
                continue

            # Prepare input for the NPC
            npc_input = TeachingNPCInput(
                user_input=user_input,
                github_username=args.username,
                conversation_context=conversation_history,
            )

            # Run the NPC
            result = agent.run_npc_session(npc_input)

            # Display result
            print(f"\n🦆 Quackster: {result.response_text}")

            # Display debug info if enabled
            if args.debug:
                print("\n=== Debug Info ===")
                print(f"Actions taken: {', '.join(result.actions_taken)}")
                print(f"Should verify quests: {result.should_verify_quests}")
                if result.suggested_quests:
                    print(f"Suggested quests: {len(result.suggested_quests)}")
                print("=================")

            # Update conversation history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append(
                {"role": "assistant", "content": result.response_text}
            )

            # Keep conversation history limited to last 10 messages (5 exchanges)
            if len(conversation_history) > 10:
                conversation_history = conversation_history[-10:]

            # Award XP for using the NPC
            if len(conversation_history) % 2 == 0:  # Every exchange (2 messages)
                award_conversation_xp()

        except KeyboardInterrupt:
            print(
                "\n\n🦆 Quackster: Quack! Looks like you're leaving. See you next time!"
            )
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            if args.debug:
                import traceback

                traceback.print_exc()


def initialize_demo(args):
    """Initialize the demo environment."""
    # Create a user if none exists
    user = utils.load_progress()

    # Reset progress if requested
    if args.reset:
        utils.reset_progress()
        user = utils.load_progress()

    # Set GitHub username if provided
    if args.username:
        user.github_username = args.username
        utils.save_progress(user)

    # Add some initial XP if brand new user (for testing)
    if user.xp == 0:
        event = XPEvent(
            id="welcome-to-demo", label="Welcome to the Quackster Demo", points=5
        )
        xp.add_xp(user, event)
        utils.save_progress(user)


def award_conversation_xp():
    """Award XP for having a conversation with Quackster."""
    user = utils.load_progress()

    # Calculate conversation count
    conversation_count = len(
        [e for e in user.completed_event_ids if e.startswith("quackster-conversation-")]
    )

    # Create event ID based on conversation count
    event_id = f"quackster-conversation-{conversation_count + 1}"

    # Check if this specific conversation has already been counted
    if event_id in user.completed_event_ids:
        return

    # Award XP (diminishing returns)
    xp_amount = 5 if conversation_count < 5 else (3 if conversation_count < 10 else 1)

    # Create and apply XP event
    event = XPEvent(
        id=event_id,
        label=f"Conversation with Quackster #{conversation_count + 1}",
        points=xp_amount,
    )
    xp.add_xp(user, event)

    # Check for any completed quests
    quests.apply_completed_quests(user)

    # Save progress
    utils.save_progress(user)


def show_help():
    """Show help information for the demo."""
    help_text = """
DEMO COMMANDS:
  help    - Show this help message
  exit    - Exit the demo (also 'quit' or 'bye')
  reset   - Reset your progress
  debug   - Toggle debug output

EXAMPLE QUESTIONS:
  What's my level?
  How many badges do I have?
  What quests are available?
  How do I complete the star-quackcore quest?
  What should I do next?
  Tell me about certificates
  I just starred the repository!
    """
    print(help_text)


if __name__ == "__main__":
    main()
