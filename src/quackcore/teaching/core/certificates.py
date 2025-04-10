# src/quackcore/teaching/core/certificates.py
"""
Certificate generation and verification for completed courses.

This module provides functions for creating and verifying digital certificates
that recognize course completion.
"""

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime
from typing import Any

from quackcore.logging import get_logger
from quackcore.teaching.models import UserProgress

logger = get_logger(__name__)

# Certificate secret key
# In a real implementation, this would be stored securely
CERTIFICATE_SECRET = os.environ.get("QUACK_CERTIFICATE_SECRET", "quack-secret-key")


def create_certificate(
    user: UserProgress,
    course_id: str,
    issuer: str = "QuackVerse",
    additional_data: dict[str, Any] = None,
) -> dict[str, Any]:
    """
    Create a digital certificate for course completion.

    Args:
        user: User to create certificate for
        course_id: ID of the completed course
        issuer: Name of the certificate issuer
        additional_data: Additional data to include in the certificate

    Returns:
        Certificate data
    """
    if not user.github_username:
        raise ValueError("User must have a GitHub username to create a certificate")

    # Prepare certificate data
    now = datetime.now()
    timestamp = int(time.time())

    certificate = {
        "version": "1.0",
        "type": "course-completion",
        "course_id": course_id,
        "issuer": issuer,
        "recipient": user.github_username,
        "issued_at": timestamp,
        "issued_date": now.strftime("%Y-%m-%d"),
        "xp": user.xp,
        "level": user.get_level(),
    }

    # Add additional data if provided
    if additional_data:
        certificate.update(additional_data)

    # Generate certificate ID using user, course, and timestamp
    id_str = f"{user.github_username}:{course_id}:{timestamp}"
    cert_id = hashlib.sha256(id_str.encode()).hexdigest()
    certificate["id"] = cert_id

    # Generate signature
    signature = _sign_certificate(certificate)
    certificate["signature"] = signature

    logger.info(
        f"Created certificate for {user.github_username} - Course: {course_id}, ID: {cert_id[:8]}..."
    )
    return certificate


def verify_certificate(certificate: dict[str, Any]) -> bool:
    """
    Verify a certificate's authenticity.

    Args:
        certificate: Certificate data to verify

    Returns:
        True if the certificate is valid, False otherwise
    """
    # Check for required fields
    required_fields = [
        "id",
        "version",
        "type",
        "course_id",
        "issuer",
        "recipient",
        "issued_at",
        "signature",
    ]
    for field in required_fields:
        if field not in certificate:
            logger.warning(f"Certificate missing required field: {field}")
            return False

    # Extract the signature
    signature = certificate.get("signature")

    # Create a copy of the certificate without the signature
    cert_copy = certificate.copy()
    cert_copy.pop("signature", None)

    # Generate a new signature and compare
    expected_signature = _sign_certificate(cert_copy)

    # Verify the signature
    if signature != expected_signature:
        logger.warning("Certificate signature verification failed")
        return False

    logger.info(
        f"Certificate verified for {certificate['recipient']} - Course: {certificate['course_id']}"
    )
    return True


def certificate_to_string(certificate: dict[str, Any]) -> str:
    """
    Convert a certificate to a shareable string format.

    Args:
        certificate: Certificate data

    Returns:
        Certificate as a base64-encoded string
    """
    cert_json = json.dumps(certificate)
    cert_bytes = cert_json.encode("utf-8")
    cert_b64 = base64.b64encode(cert_bytes)
    return cert_b64.decode("utf-8")


def string_to_certificate(cert_string: str) -> dict[str, Any]:
    """
    Convert a certificate string back to dictionary format.

    Args:
        cert_string: Certificate as a base64-encoded string

    Returns:
        Certificate data
    """
    try:
        cert_bytes = base64.b64decode(cert_string)
        cert_json = cert_bytes.decode("utf-8")
        certificate = json.loads(cert_json)
        return certificate
    except Exception as e:
        logger.error(f"Error decoding certificate string: {str(e)}")
        raise ValueError("Invalid certificate string")


def format_certificate_markdown(certificate: dict[str, Any]) -> str:
    """
    Format a certificate as a markdown string for display or sharing.

    Args:
        certificate: Certificate data

    Returns:
        Certificate as a formatted markdown string
    """
    course_id = certificate.get("course_id", "Unknown Course")
    recipient = certificate.get("recipient", "Unknown")
    issued_date = certificate.get("issued_date", "Unknown Date")
    cert_id = certificate.get("id", "")[:8]

    return f"""# Certificate of Completion

**Course:** {course_id}
**Issued To:** {recipient}
**Date:** {issued_date}
**Verification ID:** {cert_id}...

This certificate verifies that **{recipient}** has successfully completed the **{course_id}** course on the QuackVerse platform.

Level achieved: {certificate.get("level", 1)}
XP earned: {certificate.get("xp", 0)}

---

Verify this certificate by uploading it to the DuckTyper certificate verification tool.
"""


def _sign_certificate(certificate: dict[str, Any]) -> str:
    """
    Create a signature for a certificate.

    Args:
        certificate: Certificate data to sign

    Returns:
        Signature string
    """
    # Sort keys for consistent ordering
    cert_json = json.dumps(certificate, sort_keys=True)

    # Create HMAC-SHA256 signature
    signature = hmac.new(
        CERTIFICATE_SECRET.encode(), cert_json.encode(), hashlib.sha256
    ).hexdigest()

    return signature


def has_earned_certificate(user: UserProgress, course_id: str) -> bool:
    """
    Check if a user has earned a certificate for a specific course.

    This is a placeholder implementation. In a real implementation,
    you would check if the user has completed all required quests
    for the course.

    Args:
        user: User to check
        course_id: ID of the course

    Returns:
        True if the user has earned a certificate, False otherwise
    """
    if course_id == "quackverse-basics":
        # Check if user has completed the required quests
        required_quests = ["star-quackcore", "run-ducktyper", "complete-tutorial"]
        for quest_id in required_quests:
            if not user.has_completed_quest(quest_id):
                return False

        # Check if the user has at least 100 XP
        if user.xp < 100:
            return False

        return True

    # For other courses, implement specific requirements
    return False
