# tests/test_integrations/google/mail/mocks.py
"""
Mock objects for Gmail service testing.

This module provides mock implementations of Gmail service objects
that can be used across different test modules.
"""

import base64
from unittest.mock import MagicMock

from quackcore.integrations.google.mail.protocols import GmailService


class MockGmailAttachmentsResource:
    """Mock attachments resource."""

    def get(self, userId: str, messageId: str, id: str):
        """Mock get method."""

        class MockRequest:
            """Mock request object."""

            def execute(self):
                """Mock execute method."""
                return {
                    "data": base64.urlsafe_b64encode(
                        b"attachment content"
                    ).decode()
                }

        return MockRequest()


class MockGmailMessagesResource:
    """Mock messages resource."""

    def __init__(self):
        """Initialize mock messages resource."""
        self._attachments = MockGmailAttachmentsResource()

    def attachments(self):
        """Return mock attachments resource."""
        return self._attachments

    def get(self, userId: str, id: str):
        """Mock get method for message retrieval."""

        class MockRequest:
            """Mock request object."""

            def execute(self):
                """Mock execute method."""
                return {
                    "id": id,
                    "threadId": f"thread-{id}",
                    "labelIds": ["INBOX"],
                    "snippet": "Email snippet...",
                    "payload": {
                        "mimeType": "multipart/mixed",
                        "headers": [
                            {"name": "From", "value": "sender@example.com"},
                            {"name": "To", "value": "recipient@example.com"},
                            {"name": "Subject", "value": f"Test Email {id}"},
                            {"name": "Date", "value": "Mon, 1 Jan 2023 12:00:00 +0000"},
                        ],
                        "parts": [
                            {
                                "mimeType": "text/html",
                                "body": {
                                    "data": base64.urlsafe_b64encode(
                                        b"<html><body>Test Email Content</body></html>"
                                    ).decode()
                                },
                            }
                        ],
                    },
                }

        return MockRequest()

    def list(self, userId: str, q: str = None, maxResults: int = 100):
        """Mock list method for listing messages."""

        class MockRequest:
            """Mock request object."""

            def execute(self):
                """Mock execute method."""
                # Return different results based on the query
                if q and "subject:Error" in q:
                    return {"messages": []}

                return {
                    "messages": [
                        {"id": "msg1", "threadId": "thread1"},
                        {"id": "msg2", "threadId": "thread2"},
                    ],
                    "nextPageToken": None,
                }

        return MockRequest()


class MockGmailUsersResource:
    """Mock users resource."""

    def __init__(self):
        """Initialize mock users resource."""
        self._messages = MockGmailMessagesResource()

    def messages(self):
        """Return mock messages resource."""
        return self._messages


class MockGmailService:
    """Mock Gmail service for testing."""

    def __init__(self):
        """Initialize mock Gmail service."""
        self._users = MockGmailUsersResource()

    def users(self):
        """Return mock users resource."""
        return self._users


def create_mock_gmail_service() -> GmailService:
    """
    Create and return a mock Gmail service that conforms to the GmailService protocol.

    Returns:
        A mock Gmail service object cast to the GmailService type.
    """
    return MockGmailService()  # type: ignore


def create_error_gmail_service() -> GmailService:
    """
    Create a Gmail service mock that raises exceptions for testing error handling.

    Returns:
        A mock Gmail service object that will raise exceptions.
    """
    mock_service = MagicMock(spec=GmailService)
    users_mock = MagicMock()
    messages_mock = MagicMock()

    # Configure mocks to raise exceptions
    messages_mock.get.side_effect = Exception("API Error: Failed to get message")
    messages_mock.list.side_effect = Exception("API Error: Failed to list messages")

    # Set up the chain: service.users().messages()
    mock_service.users.return_value = users_mock
    users_mock.messages.return_value = messages_mock

    return mock_service