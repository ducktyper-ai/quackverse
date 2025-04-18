# quackcore/tests/test_integrations/google/mail/test_mail.py
"""
Main entry point for Google Mail integration tests.

This file imports all the specific test modules to ensure they are discovered
by pytest when running the test suite.
"""

# Import test modules to ensure they are discovered by pytest
from tests.quackcore.test_integrations.google.mail.operations.test_attachments import (
    TestGmailAttachmentOperations,
)
from tests.quackcore.test_integrations.google.mail.operations.test_auth import (
    TestGmailAuthOperations,
)
from tests.quackcore.test_integrations.google.mail.operations.test_email import (
    TestGmailEmailOperations,
)
from tests.quackcore.test_integrations.google.mail.test_mail_service import (
    TestGoogleMailService,
)
from tests.quackcore.test_integrations.google.mail.utils.test_api import (
    TestGmailApiUtils,
)

# Export the test classes for direct import
__all__ = [
    "TestGoogleMailService",
    "TestGmailEmailOperations",
    "TestGmailAttachmentOperations",
    "TestGmailAuthOperations",
    "TestGmailApiUtils",
]
