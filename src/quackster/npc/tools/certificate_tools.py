# src/quackster/npc/tools/certificate_tools.py
"""
Tools for certificate-related information and management.

This module provides functions for retrieving certificate information
and checking certificate eligibility.
"""

from quackster import certificates, utils
from quackster.npc.schema import UserMemory
from quackster.npc.tools.common import standardize_tool_output
from quackster.npc.tools.schema import CertificateInfo, CertificateListOutput


def get_certificate_info(user_memory: UserMemory) -> CertificateListOutput:
    """
    Get information about certificates that the user can earn.

    Args:
        user_memory: User memory data with XP and completed quests

    Returns:
        CertificateListOutput with certificate information
    """
    # Load user progress
    user = utils.load_progress()  # Still needed for certificate validation

    # Check available certificates
    available_certificates = [
        {
            "id": "quackverse-basics",
            "name": "QuackVerse Basics",
            "description": "Completed the introductory QuackVerse curriculum",
            "earned": certificates.has_earned_certificate(user, "quackverse-basics"),
            "requirements": [
                "Complete the 'star-quackcore' quest",
                "Complete the 'run-ducktyper' quest",
                "Complete the 'complete-tutorial' quest",
                "Earn at least 100 XP",
            ],
            # Calculate progress based on user_memory
            "progress": sum(
                [
                    1 if "star-quackcore" in user_memory.completed_quests else 0,
                    1 if "run-ducktyper" in user_memory.completed_quests else 0,
                    1 if "complete-tutorial" in user_memory.completed_quests else 0,
                    1 if user_memory.xp >= 100 else 0,
                ]
            )
            / 4
            * 100,
        },
        {
            "id": "github-contributor",
            "name": "GitHub Contributor",
            "description": "Contributed to the QuackVerse ecosystem on GitHub",
            "earned": certificates.has_earned_certificate(user, "github-contributor"),
            "requirements": [
                "Complete the 'open-pr' quest",
                "Complete the 'merged-pr' quest",
                "Earn the 'duck-team-player' badge",
                "Earn at least 300 XP",
            ],
            # Calculate progress based on user_memory
            "progress": sum(
                [
                    1 if "open-pr" in user_memory.completed_quests else 0,
                    1 if "merged-pr" in user_memory.completed_quests else 0,
                    1 if "duck-team-player" in user_memory.badges else 0,
                    1 if user_memory.xp >= 300 else 0,
                ]
            )
            / 4
            * 100,
        },
    ]

    # Format certificate list with progress information
    cert_list = []
    for cert in available_certificates:
        progress = cert["progress"]
        progress_bar = "█" * (int(progress) // 10) + "░" * (10 - (int(progress) // 10))

        if cert["earned"]:
            status = "✅ Earned"
            progress_info = ""
        else:
            status = "⏳ Not yet earned"
            progress_info = f"\n  Progress: {progress:.0f}% {progress_bar}"

        cert_list.append(
            CertificateInfo(
                id=cert["id"],
                name=cert["name"],
                description=cert["description"],
                earned=cert["earned"],
                requirements=cert["requirements"],
                progress=progress,
                progress_bar=progress_bar,
                formatted=f"{cert['name']} - {cert['description']}\n  Status: {status}{progress_info}",
            )
        )

    # If any certificate is earned, mention how to generate it
    earned_any = any(cert.earned for cert in cert_list)

    # Use learning style from user_memory for personalization
    learning_style = user_memory.custom_data.get("learning_style", "")

    if earned_any:
        generation_info = """
To generate your certificate, use the following command:
```
ducktyper cert --course=certificate_id
```
Replace 'certificate_id' with the ID of the certificate you've earned.
"""
    else:
        generation_info = ""

    # Adapt the message to be more enthusiastic if certificates are earned
    if earned_any:
        header = "# Quack-tastic! You've Earned Certificates! 🎓"
        intro = f"You've successfully completed course requirements and earned certifications! These prove your mastery of the QuackVerse ecosystem at level {user_memory.level}!"
    else:
        if "step by step" in learning_style:
            header = "# Certificate Path"
            intro = "Follow these clear steps to earn official QuackVerse certificates:"
        elif "challenge" in learning_style:
            header = "# Certificate Challenges"
            intro = "Ready to prove your skills? Complete these requirements to earn official recognition:"
        else:
            header = "# Available Certificates"
            intro = "Complete these learning paths to earn official QuackVerse certificates:"

    formatted_text = (
        f"{header}\n\n"
        f"{intro}\n\n"
        + "\n\n".join([cert.formatted for cert in cert_list])
        + generation_info
    )

    return standardize_tool_output(
        "get_certificate_info",
        {
            "certificates": cert_list,
            "earned_any": earned_any,
            "certificate_count": len(cert_list),
            "earned_count": sum(1 for cert in cert_list if cert.earned),
            "formatted_text": formatted_text,
        },
        return_type=CertificateListOutput,
    )
