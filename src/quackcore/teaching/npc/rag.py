# src/quackcore/teaching/npc/rag.py
"""
RAG (Retrieval-Augmented Generation) module for the Quackster teaching NPC.

This module provides functions for loading and retrieving content from
Markdown documents to ground the NPC's knowledge in factual information.
"""

import os
import re
from pathlib import Path
from typing import Any

# Dogfood QuackCore FS for file operations and logging.
from quackcore.fs import service as fs
from quackcore.logging import get_logger

# Dogfood QuackCore Paths for content context detection.
from quackcore.paths import resolver

logger = get_logger(__name__)

# Default locations for tutorial content.
DEFAULT_DOC_PATHS = [
    "~/quackverse/tutorials",
    "./tutorials",
    "./docs/tutorials",
]


def get_doc_directories() -> list[Path]:
    """
    Get the directories containing tutorial documents.

    This function first checks for a custom override via the
    QUACK_TUTORIAL_PATH environment variable. If not found, it attempts to
    detect a content context (with content_type "tutorial") using the
    QuackCore Paths resolver. Finally, it falls back to the default paths,
    expanding user variables via fs.expand_user_vars and verifying existence
    with fs.get_file_info.

    Returns:
        A list of directory paths (as Path objects) containing tutorial documents.
    """
    # Check for a custom override.
    custom_path = os.environ.get("QUACK_TUTORIAL_PATH")
    if custom_path:
        custom_expanded = Path(fs.expand_user_vars(custom_path))
        return [custom_expanded]

    # Attempt to detect a content context for tutorials.
    content_context = resolver.detect_content_context(content_type="tutorial")
    if (
        content_context
        and content_context.content_dir
        and content_context.content_dir.exists()
    ):
        return [content_context.content_dir]

    # Fall back to the default paths.
    paths: list[Path] = []
    for path_str in DEFAULT_DOC_PATHS:
        expanded = Path(fs.expand_user_vars(path_str))
        info = fs.get_file_info(str(expanded))
        if info.success and info.exists and info.is_dir:
            paths.append(expanded)
    return paths


def load_docs_for_rag() -> str:
    """
    Load all tutorial documents for Retrieval-Augmented Generation (RAG).

    This function gathers all Markdown (.md) files found in the tutorial
    directories, reads their contents using the FS service, and then concatenates
    them into one string. Each file’s content is preceded by a header bearing
    the file name.

    Returns:
        A concatenated string of all document contents, or an empty string if none are found.
    """
    docs: list[str] = []
    doc_dirs = get_doc_directories()

    if not doc_dirs:
        logger.warning("No tutorial directories found. RAG will be limited.")
        return ""

    for doc_dir in doc_dirs:
        # Search for Markdown files recursively.
        result = fs.find_files(str(doc_dir), "*.md", recursive=True)
        if not result.success:
            logger.warning(f"Failed to search directory {doc_dir}: {result.error}")
            continue

        for file_path in result.files:
            try:
                read_result = fs.read_text(str(file_path))
                if read_result.success:
                    filename = Path(file_path).name
                    content = f"# {filename}\n\n{read_result.content}\n\n"
                    docs.append(content)
                else:
                    logger.warning(f"Failed to read {file_path}: {read_result.error}")
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")

    if not docs:
        logger.warning("No tutorial documents found.")
        return ""

    return "\n\n".join(docs)


def retrieve_relevant_content(query: str, all_content: str, max_chunks: int = 3) -> str:
    """
    Retrieve content relevant to a query from the full document content.

    The function splits the complete document content into chunks based on
    Markdown headings, scores each chunk by counting the occurrences of keywords
    (extracted from the query), and returns the top-scoring chunks (up to max_chunks).

    Args:
        query: The query string to search for.
        all_content: The full content (as a string) from which to retrieve relevant parts.
        max_chunks: The maximum number of chunks to return (default is 3).

    Returns:
        A concatenated string of the selected relevant content chunks.
    """
    chunks = _split_by_headings(all_content)
    scored_chunks: list[tuple[str, int]] = []
    keywords = _extract_keywords(query)

    for chunk in chunks:
        score = sum(chunk.lower().count(keyword.lower()) for keyword in keywords)
        if score > 0:
            scored_chunks.append((chunk, score))

    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    top_chunks = [chunk for chunk, _ in scored_chunks[:max_chunks]]
    return "\n\n".join(top_chunks)


def _split_by_headings(content: str) -> list[str]:
    """
    Split content into chunks by Markdown headings.

    Uses a regular expression to separate content at lines starting with 1-3 '#' characters.

    Args:
        content: The Markdown content to split.

    Returns:
        A list of content chunks, where each chunk starts with a Markdown heading.
    """
    heading_pattern = re.compile(r"^(#{1,3})\s+(.+)", re.MULTILINE)
    headings = [(m.start(), m.group(0)) for m in heading_pattern.finditer(content)]
    if not headings:
        return [content]

    chunks: list[str] = []
    for i, (pos, _) in enumerate(headings):
        end_pos = headings[i + 1][0] if i < len(headings) - 1 else len(content)
        chunk = content[pos:end_pos].strip()
        chunks.append(chunk)
    return chunks


def _extract_keywords(query: str) -> list[str]:
    """
    Extract keywords from the query to aid in content matching.

    This function tokenizes the query, removes common stop words, and filters out tokens shorter than three characters.

    Args:
        query: The query string.

    Returns:
        A list of keywords.
    """
    stop_words = {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "in",
        "on",
        "at",
        "to",
        "for",
        "with",
        "by",
        "about",
        "of",
        "that",
        "and",
        "or",
        "not",
        "but",
        "what",
        "which",
        "who",
        "whom",
        "whose",
        "when",
        "where",
        "why",
        "how",
        "this",
        "these",
        "those",
        "it",
        "they",
        "them",
        "their",
        "there",
        "here",
        "do",
        "does",
        "did",
        "can",
        "could",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "must",
        "i",
        "you",
        "he",
        "she",
        "we",
        "my",
        "your",
        "his",
        "her",
        "our",
    }
    tokens = re.findall(r"\b\w+\b", query.lower())
    keywords = [token for token in tokens if token not in stop_words and len(token) > 2]
    return keywords


def get_quest_info(quest_id: str) -> dict[str, Any]:
    """
    Get detailed information about a quest from documentation.

    Args:
        quest_id: The quest ID.

    Returns:
        A dictionary with quest details such as name, description, reward XP,
        badge information, and guidance.
    """
    from quackcore.teaching import quests

    quest = quests.get_quest(quest_id)
    if not quest:
        return {
            "id": quest_id,
            "name": f"Unknown Quest ({quest_id})",
            "description": "Quest information not found",
            "guidance": "Unable to provide guidance for this quest.",
        }

    guidance = {
        "star-quackcore": (
            "To complete this quest, you'll need to star the QuackCore repository on GitHub.\n\n"
            "1. Go to https://github.com/quackverse/quackcore\n"
            "2. Click the 'Star' button in the top-right corner\n"
            "3. That's it! Your quest progress will be automatically updated."
        ),
        "star-quackverse": (
            "To complete this quest, you'll need to star the QuackVerse organization on GitHub.\n\n"
            "1. Go to https://github.com/quackverse\n"
            "2. Click the 'Star' button in the top-right corner\n"
            "3. That's it! Your quest progress will be automatically updated."
        ),
        "run-ducktyper": (
            "To complete this quest, you'll need to run the DuckTyper CLI.\n\n"
            "1. Install DuckTyper if you haven't already:\n"
            "   pip install ducktyper\n"
            "2. Run a simple DuckTyper command:\n"
            "   ducktyper hello\n"
            "3. The quest will be marked as completed automatically."
        ),
    }

    return {
        "id": quest.id,
        "name": quest.name,
        "description": quest.description,
        "reward_xp": quest.reward_xp,
        "badge_id": quest.badge_id,
        "guidance": guidance.get(
            quest.id, "Complete this quest to earn XP and progress in your journey!"
        ),
    }


def get_badge_info(badge_id: str) -> dict[str, Any]:
    """
    Get detailed information about a badge from documentation.

    Args:
        badge_id: The badge's ID.

    Returns:
        A dictionary containing badge details including name, description,
        required XP, emoji, and additional guidance.
    """
    from quackcore.teaching import badges

    badge = badges.get_badge(badge_id)
    if not badge:
        return {
            "id": badge_id,
            "name": f"Unknown Badge ({badge_id})",
            "description": "Badge information not found",
            "guidance": "Unable to provide information for this badge.",
        }

    info = {
        "github-collaborator": {
            "guidance": "This badge is earned by starring the QuackCore repository on GitHub.",
            "fun_fact": "GitHub's star feature was introduced in 2012 as a way to bookmark repositories.",
        },
        "duck-contributor": {
            "guidance": "This badge is earned by opening a Pull Request to a QuackVerse repository.",
            "fun_fact": "The concept of 'pull requests' was popularized by GitHub to make code collaboration easier.",
        },
        "duck-team-player": {
            "guidance": "This badge is earned by having a PR merged into a QuackVerse project.",
            "fun_fact": "The average time for PR review and merging in open source projects is about 4-5 days.",
        },
        "duck-initiate": {
            "guidance": "This badge is earned by gaining your first 10 XP in DuckTyper.",
            "fun_fact": "The concept of 'XP' was first popularized in role-playing games in the 1970s.",
        },
    }

    badge_info = info.get(
        badge_id,
        {
            "guidance": f"This badge is earned by reaching {badge.required_xp} XP.",
            "fun_fact": "Badges were originally physical emblems worn to show achievement or affiliation.",
        },
    )

    return {
        "id": badge.id,
        "name": badge.name,
        "description": badge.description,
        "required_xp": badge.required_xp,
        "emoji": badge.emoji,
        "guidance": badge_info.get("guidance", ""),
        "fun_fact": badge_info.get("fun_fact", ""),
    }


def get_tutorial_topic(topic: str) -> dict[str, Any]:
    """
    Get tutorial content for a specific topic.

    Args:
        topic: The topic to search for.

    Returns:
        A dictionary with tutorial information including title, description,
        and the main content.
    """
    topics = {
        "ducktyper": {
            "title": "Introduction to DuckTyper",
            "description": "DuckTyper is a CLI tool for the QuackVerse ecosystem.",
            "content": (
                "# DuckTyper Tutorial\n\n"
                "DuckTyper is a command-line interface (CLI) tool for the QuackVerse ecosystem. It provides a unified way to interact with QuackVerse components.\n\n"
                "## Installation\n\n"
                "You can install DuckTyper using pip:\n\n"
                "```bash\npip install ducktyper\n```\n\n"
                "## Basic Usage\n\n"
                "Once installed, you can run various commands:\n\n"
                "```bash\nducktyper --help\n```\n"
                "```bash\nducktyper xp\n```\n"
                "```bash\nducktyper quest list\n```\n"
                "```bash\nducktyper badge list\n```\n"
            ),
        },
        "quests": {
            "title": "Completing Quests with DuckTyper",
            "description": "Learn how to view and complete quests.",
            "content": (
                "# Quests in DuckTyper\n\n"
                "Quests are challenges that you can complete to earn XP and badges.\n\n"
                "## Viewing Quests\n\n"
                "To see available quests:\n\n"
                "```bash\nducktyper quest list\n```\n\n"
                "## Completing Quests\n\n"
                "Most quests involve GitHub actions or using DuckTyper features. For example:\n\n"
                "1. Star the QuackCore repository on GitHub\n"
                "2. Open a PR to a QuackVerse repository\n"
                "3. Run DuckTyper daily for a streak\n\n"
                "## Checking Progress\n\n"
                "Check your progress with:\n\n"
                "```bash\nducktyper progress\n```\n"
            ),
        },
    }

    lower_topic = topic.lower()
    for key, content in topics.items():
        if key.lower() in lower_topic or lower_topic in key.lower():
            return content

    return {
        "title": "Topic Not Found",
        "description": f"No tutorial found for '{topic}'",
        "content": (
            f"I don't have a specific tutorial on '{topic}' yet. Try asking about DuckTyper, quests, or badges."
        ),
    }
