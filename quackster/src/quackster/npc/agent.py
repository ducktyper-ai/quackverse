# quackster/src/quackster/npc/agent.py
"""
Main agent orchestration for the Quackster quackster NPC.

This module provides the core agent functionality for the Quackster
quackster NPC, including LLM integration and tool execution.
"""

import random
import re
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from quackcore.integrations.core import registry
from quackcore.logging import get_logger
from quackster.npc import config, memory, persona, rag, tools
from quackster.npc.dialogue.registry import DialogueRegistry
from quackster.npc.schema import (
    QuacksterProfile,
    TeachingNPCInput,
    TeachingNPCResponse,
    UserMemory,
)

logger = get_logger(__name__)

# Define the available tools for the NPC (for reference).
NPC_TOOLS = {
    "list_xp_and_level": tools.list_xp_and_level,
    "list_badges": tools.list_badges,
    "list_quests": tools.list_quests,
    "get_quest_details": tools.get_quest_details,
    "suggest_next_quest": tools.suggest_next_quest,
    "get_badge_details": tools.get_badge_details,
    "verify_quest_completion": tools.verify_quest_completion,
    "get_tutorial": tools.get_tutorial,
    "get_certificate_info": tools.get_certificate_info,
}


def trim_conversation_context(
    context: Sequence[dict[str, str]], max_messages: int = 10
) -> list[dict[str, str]]:
    """
    Trim the conversation context to the most recent messages to avoid token bloating.

    Each message is ensured to contain a timestamp. If a message is missing a timestamp,
    the current UTC time in ISO format is inserted.

    Args:
        context: The full conversation history.
        max_messages: Maximum number of recent messages to include.

    Returns:
        A list of the most recent conversation messages, each with a timestamp.
    """
    trimmed = list(context)[-max_messages:] if context else []
    for msg in trimmed:
        if "timestamp" not in msg:
            msg["timestamp"] = datetime.now().isoformat()
    return trimmed


def run_npc_session(input: TeachingNPCInput) -> TeachingNPCResponse:
    """
    Run a session with the Quackster quackster NPC.

    Args:
        input: Input data for the NPC session

    Returns:
        NPC response
    """
    # Load user memory.
    user_memory: UserMemory = memory.get_user_memory(input.github_username)
    user_memory = memory.update_user_memory(user_memory, input.user_input)

    # Add conversation history record with a timestamp.
    if "conversation_history" not in user_memory.custom_data:
        user_memory.custom_data["conversation_history"] = []
    user_memory.custom_data["conversation_history"].append(
        {
            "role": "user",
            "message": input.user_input,
            "timestamp": datetime.now().isoformat(),
        }
    )

    actions_taken: list[str] = []
    tool_outputs: list[Any] = []
    should_verify_quests = False

    # Detect explicit matches for quest, badge, and tutorial queries.
    quest_match = re.search(
        r'quest[s\s]*[\'"]?([\w-]+)[\'"]?', input.user_input, re.IGNORECASE
    )
    badge_match = re.search(
        r'badge[s\s]*[\'"]?([\w-]+)[\'"]?', input.user_input, re.IGNORECASE
    )
    tutorial_match = re.search(
        r'tutorial[s\s]*(?:on|about)?\s*[\'"]?([\w-]+)[\'"]?',
        input.user_input,
        re.IGNORECASE,
    )

    # Dispatch common tool triggers via a mapping.
    dispatch_map = [
        {
            "pattern": r"\b(xp|level|progress)\b",
            "desc": "Checking XP and level",
            "func": tools.list_xp_and_level,
        },
        {
            "pattern": r"\bbadges?\b",
            "desc": "Listing badges",
            "func": tools.list_badges,
            "exclude": badge_match is not None,  # Skip if explicit badge query exists.
        },
        {
            "pattern": r"\bquests?\b",
            "desc": "Listing quests",
            "func": tools.list_quests,
            "exclude": quest_match is not None,  # Skip if explicit quest query exists.
        },
        {
            "pattern": r"\b(what next|next quest|suggest|do next)\b",
            "desc": "Suggesting next quest",
            "func": tools.suggest_next_quest,
        },
        {
            "pattern": r"\bcertificates?\b",
            "desc": "Getting certificate information",
            "func": tools.get_certificate_info,
        },
    ]

    for entry in dispatch_map:
        if entry.get("exclude", False):
            continue
        if re.search(entry["pattern"], input.user_input, re.IGNORECASE):
            actions_taken.append(entry["desc"])
            tool_outputs.append(entry["func"](user_memory))

    # Process explicit quest queries.
    if quest_match:
        quest_id = quest_match.group(1).lower().strip()
        actions_taken.append(f"Getting details for quest: {quest_id}")
        tool_outputs.append(tools.get_quest_details(quest_id))
        # Track this as a recently discussed quest.
        if "recent_quests_discussed" not in user_memory.custom_data:
            user_memory.custom_data["recent_quests_discussed"] = []
        if quest_id not in user_memory.custom_data["recent_quests_discussed"]:
            user_memory.custom_data["recent_quests_discussed"].append(quest_id)
            # Keep only the 5 most recent.
            if len(user_memory.custom_data["recent_quests_discussed"]) > 5:
                user_memory.custom_data["recent_quests_discussed"] = (
                    user_memory.custom_data["recent_quests_discussed"][-5:]
                )

    # Process explicit badge queries.
    if badge_match:
        badge_id = badge_match.group(1).lower().strip()
        actions_taken.append(f"Getting details for badge: {badge_id}")
        tool_outputs.append(tools.get_badge_details(badge_id))

    # Process explicit tutorial queries.
    if tutorial_match:
        topic = tutorial_match.group(1).lower().strip()
        actions_taken.append(f"Getting tutorial for: {topic}")
        tool_outputs.append(tools.get_tutorial(topic))

    # Check if the user indicates completion of a quest.
    if re.search(r"\b(completed|finished|done|did)\b", input.user_input, re.IGNORECASE):
        actions_taken.append("Checking for quest completion")
        completion_result = tools.verify_quest_completion(user_memory)
        tool_outputs.append(completion_result)
        should_verify_quests = True

    # Prepare relevant RAG content.
    docs = rag.load_docs_for_rag()
    relevant_content = rag.retrieve_relevant_content(input.user_input, docs)

    # Create NPC profile.
    npc_profile: QuacksterProfile = config.get_npc_profile()

    # Generate response using LLM.
    llm_response = call_llm(
        npc_profile=npc_profile,
        user_memory=user_memory,
        user_input=input.user_input,
        conversation_context=input.conversation_context,
        tool_outputs=tool_outputs,
        relevant_content=relevant_content,
    )

    # Prepare suggested quests based on tool outputs.
    suggested_quests = None
    for output in tool_outputs:
        if isinstance(output, dict) and "suggested" in output:
            suggested_quests = output.get("suggested", None)
            break

    # Create and return the response.
    response = TeachingNPCResponse(
        response_text=llm_response,
        actions_taken=actions_taken,
        suggested_quests=suggested_quests,
        used_tools=[
            {
                "name": output.get("name", f"Tool {i + 1}"),
                "result": output.get("result", output),
            }
            for i, output in enumerate(tool_outputs)
        ],
        should_verify_quests=should_verify_quests,
    )

    return response


def call_llm(
    npc_profile: QuacksterProfile,
    user_memory: UserMemory,
    user_input: str,
    conversation_context: Sequence[dict[str, str]] = None,
    tool_outputs: Sequence[dict[str, Any]] = None,
    relevant_content: str = "",
) -> str:
    """
    Call the LLM to generate a response.

    Args:
        npc_profile: NPC personality profile
        user_memory: User memory data
        user_input: The user's message
        conversation_context: Previous conversation messages
        tool_outputs: Outputs from tools that were run
        relevant_content: Relevant content from RAG

    Returns:
        Generated response from the LLM
    """
    # Get LLM integration.
    llm = get_llm_client()
    if llm is None:
        return mock_llm_response(user_input, tool_outputs)

    # Generate the system prompt.
    system_prompt = persona.get_system_prompt(npc_profile, user_memory)

    # Format the relevant content.
    if relevant_content:
        system_prompt += "\n\nRELEVANT DOCUMENTATION:\n" + relevant_content

    # Format the tool outputs.
    tool_output_text = ""
    if tool_outputs:
        tool_output_text = "TOOL OUTPUTS:\n"
        for i, output in enumerate(tool_outputs):
            tool_name = output.get("name", f"Tool {i + 1}")
            formatted_text = output.get("formatted_text", str(output))
            tool_output_text += f"\n--- {tool_name} ---\n{formatted_text}\n"

    # Create the messages list.
    messages = []

    # Add the system message.
    messages.append({"role": "system", "content": system_prompt})

    # Add a random few-shot example conversation, if available.
    example_conversations = persona.get_example_conversations()
    if example_conversations:
        example = random.choice(example_conversations)
        for msg in example.get("conversation", []):
            messages.append(msg)

    # Trim and add the conversation context to limit tokens.
    if conversation_context:
        trimmed_context = trim_conversation_context(conversation_context)
        for msg in trimmed_context:
            messages.append(msg)

    # Add the tool outputs, if any.
    if tool_output_text:
        messages.append({"role": "system", "content": tool_output_text})

    # Add the user's message.
    messages.append({"role": "user", "content": user_input})

    try:
        # Get model settings.
        model_settings = config.get_model_settings()

        # Call the LLM.
        response = llm.generate(
            messages=messages,
            model=model_settings.get("model"),
            temperature=model_settings.get("temperature"),
            max_tokens=model_settings.get("max_tokens"),
        )

        return response.content
    except Exception as e:
        logger.error(f"Error calling LLM: {str(e)}")
        return mock_llm_response(user_input, tool_outputs)


def get_llm_client():
    """
    Get the LLM client from the integration registry.

    Returns:
        LLM client or None if not available
    """
    llm_integration = registry.get_integration("LLM")
    if not llm_integration:
        logger.warning("LLM integration not found in registry")
        return None

    # Initialize if not already.
    if not hasattr(llm_integration, "client") or llm_integration.client is None:
        result = llm_integration.initialize()
        if not result.success:
            logger.error(f"Failed to initialize LLM integration: {result.error}")
            return None

    return llm_integration


def mock_llm_response(
    user_input: str, tool_outputs: Sequence[dict[str, Any]] = None
) -> str:
    """
    Generate a mock LLM response for testing.

    Args:
        user_input: The user's message
        tool_outputs: Outputs from tools that were run

    Returns:
        Mock response
    """
    greetings = [
        "Quack! ",
        "Hello there! ",
        "Greetings, developer! ",
        "Well hello! ",
        "Welcome back! ",
    ]
    greeting = random.choice(greetings)

    catchphrase = DialogueRegistry.get_catchphrase()

    if re.search(r"\b(xp|level|progress)\b", user_input, re.IGNORECASE):
        if tool_outputs and tool_outputs[0].get("level"):
            data = tool_outputs[0]
            return (
                f"{greeting}You're currently at Level {data['level']} with {data['xp']} XP! "
                f"You need {data['xp_needed']} more XP to reach Level {data['next_level']}. "
                f"{catchphrase} Keep up the good work! 🦆"
            )
        return (
            f"{greeting}You're making great progress on your coding journey! "
            f"Keep completing quests to earn more XP and level up! 🦆"
        )

    if re.search(r"\bbadges?\b", user_input, re.IGNORECASE):
        if tool_outputs:
            data = tool_outputs[0]
            count = data.get("earned_count", 0)
            return (
                f"{greeting}You've earned {count} badges so far! Each badge represents an achievement in your coding journey. "
                f"{catchphrase} Keep up the great work! 🦆"
            )
        return (
            f"{greeting}Badges are special achievements you can earn in the QuackVerse. "
            f"Complete quests and earn XP to unlock more badges! 🦆"
        )

    if re.search(r"\bquests?\b", user_input, re.IGNORECASE):
        return (
            f"{greeting}Quests are challenges you can complete to earn XP and badges. "
            f"Try starring the QuackCore repository on GitHub to complete your first quest! {catchphrase} 🦆"
        )

    if re.search(
        r"\b(what next|next quest|suggest|do next)\b", user_input, re.IGNORECASE
    ):
        return (
            f"{greeting}I suggest trying to complete the 'Star QuackCore' quest next! "
            f"It's an easy way to earn 50 XP and get your first badge. {catchphrase} 🦆"
        )

    if re.search(r"\b(completed|finished|done|did)\b", user_input, re.IGNORECASE):
        return (
            f"{greeting}That's fantastic! Let me check if you've completed any quests... "
            f"{catchphrase} Keep up the great work! 🦆"
        )

    return (
        f"{greeting}I'm Quackster, your friendly duck coding companion! "
        f"I can help you track your progress, suggest quests, and guide you through the QuackVerse. What would you like to know? 🦆"
    )
