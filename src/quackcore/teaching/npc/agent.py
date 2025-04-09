# src/quackcore/teaching/npc/agent.py
"""
Main agent orchestration for the Quackster teaching NPC.

This module provides the core agent functionality for the Quackster
teaching NPC, including LLM integration and tool execution.
"""

import random
import re
from typing import Any

from quackcore.integrations.core import registry
from quackcore.logging import get_logger
from quackcore.teaching.npc import config, memory, persona, rag, tools
from quackcore.teaching.npc.schema import (
    QuacksterProfile,
    TeachingNPCInput,
    TeachingNPCResponse,
    UserMemory,
)

logger = get_logger(__name__)

# Define the available tools for the NPC
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


def run_npc_session(input: TeachingNPCInput) -> TeachingNPCResponse:
    """
    Run a session with the Quackster teaching NPC.

    Args:
        input: Input data for the NPC session

    Returns:
        NPC response
    """
    # Load user memory
    user_memory = memory.get_user_memory(input.github_username)
    user_memory = memory.update_user_memory(user_memory, input.user_input)

    # Process the input
    actions_taken = []
    tool_outputs = []
    should_verify_quests = False

    # Detect if user is asking about a specific quest or badge
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

    # Check for specific tool triggers
    if re.search(r"\b(xp|level|progress)\b", input.user_input, re.IGNORECASE):
        actions_taken.append("Checking XP and level")
        tool_outputs.append(tools.list_xp_and_level(user_memory))

    if re.search(r"\bbadges?\b", input.user_input, re.IGNORECASE) and not badge_match:
        actions_taken.append("Listing badges")
        tool_outputs.append(tools.list_badges(user_memory))

    if re.search(r"\bquests?\b", input.user_input, re.IGNORECASE) and not quest_match:
        actions_taken.append("Listing quests")
        tool_outputs.append(tools.list_quests(user_memory))

    if quest_match:
        quest_id = quest_match.group(1).lower().strip()
        actions_taken.append(f"Getting details for quest: {quest_id}")
        tool_outputs.append(tools.get_quest_details(quest_id))

    if badge_match:
        badge_id = badge_match.group(1).lower().strip()
        actions_taken.append(f"Getting details for badge: {badge_id}")
        tool_outputs.append(tools.get_badge_details(badge_id))

    if tutorial_match:
        topic = tutorial_match.group(1).lower().strip()
        actions_taken.append(f"Getting tutorial for: {topic}")
        tool_outputs.append(tools.get_tutorial(topic))

    if re.search(
        r"\b(what next|next quest|suggest|do next)\b", input.user_input, re.IGNORECASE
    ):
        actions_taken.append("Suggesting next quest")
        tool_outputs.append(tools.suggest_next_quest(user_memory))

    if re.search(r"\bcertificates?\b", input.user_input, re.IGNORECASE):
        actions_taken.append("Getting certificate information")
        tool_outputs.append(tools.get_certificate_info(user_memory))

    # Check if user is mentioning they completed something
    if re.search(r"\b(completed|finished|done|did)\b", input.user_input, re.IGNORECASE):
        actions_taken.append("Checking for quest completion")
        completion_result = tools.verify_quest_completion(user_memory)
        tool_outputs.append(completion_result)
        should_verify_quests = True

    # Prepare relevant RAG content
    docs = rag.load_docs_for_rag()
    relevant_content = rag.retrieve_relevant_content(input.user_input, docs)

    # Create NPC profile
    npc_profile = config.get_npc_profile()

    # Generate response using LLM
    llm_response = call_llm(
        npc_profile=npc_profile,
        user_memory=user_memory,
        user_input=input.user_input,
        conversation_context=input.conversation_context,
        tool_outputs=tool_outputs,
        relevant_content=relevant_content,
    )

    # Prepare suggested quests based on tool outputs
    suggested_quests = None
    for output in tool_outputs:
        if isinstance(output, dict) and "suggested" in output:
            suggested_quests = output.get("suggested", None)
            break

    # Create response
    response = TeachingNPCResponse(
        response_text=llm_response,
        actions_taken=actions_taken,
        suggested_quests=suggested_quests,
        used_tools=[
            {"name": tool["name"], "result": tool["result"]}
            for tool in tool_outputs
            if "name" in tool
        ],
        should_verify_quests=should_verify_quests,
    )

    return response


def call_llm(
    npc_profile: QuacksterProfile,
    user_memory: UserMemory,
    user_input: str,
    conversation_context: list[dict[str, str]] = None,
    tool_outputs: list[dict[str, Any]] = None,
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
    # Get LLM integration
    llm = get_llm_client()
    if llm is None:
        return mock_llm_response(user_input, tool_outputs)

    # Generate the system prompt
    system_prompt = persona.get_system_prompt(npc_profile, user_memory)

    # Format the relevant content
    if relevant_content:
        system_prompt += "\n\nRELEVANT DOCUMENTATION:\n" + relevant_content

    # Format the tool outputs
    tool_output_text = ""
    if tool_outputs:
        tool_output_text = "TOOL OUTPUTS:\n"
        for i, output in enumerate(tool_outputs):
            tool_name = output.get("name", f"Tool {i + 1}")
            formatted_text = output.get("formatted_text", str(output))
            tool_output_text += f"\n--- {tool_name} ---\n{formatted_text}\n"

    # Create the messages
    messages = []

    # Add system message
    messages.append({"role": "system", "content": system_prompt})

    # Add few-shot examples if available
    example_conversations = persona.get_example_conversations()
    if example_conversations:
        # Add one random example conversation
        example = random.choice(example_conversations)
        for message in example.get("conversation", []):
            messages.append(message)

    # Add conversation context if available
    if conversation_context:
        for message in conversation_context:
            messages.append(message)

    # Add tool outputs if available
    if tool_output_text:
        messages.append({"role": "system", "content": tool_output_text})

    # Add the user's message
    messages.append({"role": "user", "content": user_input})

    try:
        # Get model settings
        model_settings = config.get_model_settings()

        # Call the LLM
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

    # Initialize if not already
    if not hasattr(llm_integration, "client") or llm_integration.client is None:
        result = llm_integration.initialize()
        if not result.success:
            logger.error(f"Failed to initialize LLM integration: {result.error}")
            return None

    return llm_integration


def mock_llm_response(
    user_input: str, tool_outputs: list[dict[str, Any]] = None
) -> str:
    """
    Generate a mock LLM response for testing.

    Args:
        user_input: The user's message
        tool_outputs: Outputs from tools that were run

    Returns:
        Mock response
    """
    # Get random greeting
    greetings = [
        "Quack! ",
        "Hello there! ",
        "Greetings, developer! ",
        "Well hello! ",
    ]
    greeting = random.choice(greetings)

    # For XP and level queries
    if re.search(r"\b(xp|level|progress)\b", user_input, re.IGNORECASE):
        if tool_outputs and tool_outputs[0].get("level"):
            data = tool_outputs[0]
            return f"{greeting}You're currently at Level {data['level']} with {data['xp']} XP! You need {data['xp_needed']} more XP to reach Level {data['next_level']}. Keep up the good work! 🦆"
        return f"{greeting}You're making great progress on your coding journey! Keep completing quests to earn more XP and level up! 🦆"

    # For badge queries
    if re.search(r"\bbadges?\b", user_input, re.IGNORECASE):
        if tool_outputs:
            data = tool_outputs[0]
            count = data.get("earned_count", 0)
            return f"{greeting}You've earned {count} badges so far! Each badge represents an achievement in your coding journey. Keep up the great work! 🦆"
        return f"{greeting}Badges are special achievements you can earn in the QuackVerse. Complete quests and earn XP to unlock more badges! 🦆"

    # For quest queries
    if re.search(r"\bquests?\b", user_input, re.IGNORECASE):
        return f"{greeting}Quests are challenges you can complete to earn XP and badges. Try starring the QuackCore repository on GitHub to complete your first quest! 🦆"

    # For "what's next" queries
    if re.search(
        r"\b(what next|next quest|suggest|do next)\b", user_input, re.IGNORECASE
    ):
        return f"{greeting}I suggest trying to complete the 'Star QuackCore' quest next! It's an easy way to earn 50 XP and get your first badge. 🦆"

    # For "completed" statements
    if re.search(r"\b(completed|finished|done|did)\b", user_input, re.IGNORECASE):
        return f"{greeting}That's fantastic! Let me check if you've completed any quests... Keep up the great work! 🦆"

    # Default response
    return f"{greeting}I'm Quackster, your friendly duck coding companion! I can help you track your progress, suggest quests, and guide you through the QuackVerse. What would you like to know? 🦆"


def demo_conversation():
    """
    Run a simple demo conversation with the Quackster NPC.

    This is useful for testing the NPC functionality directly.
    """
    print("🦆 Quackster NPC Demo")
    print("Type 'exit' to quit the demo")
    print("-" * 50)

    while True:
        user_message = input("You: ")
        if user_message.lower() in ("exit", "quit", "bye"):
            break

        result = run_npc_session(TeachingNPCInput(user_input=user_message))
        print(f"\n🦆 Quackster: {result.response_text}\n")


if __name__ == "__main__":
    # Run the demo if this file is executed directly
    demo_conversation()
