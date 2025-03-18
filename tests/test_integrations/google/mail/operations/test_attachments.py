# tests/test_integrations/google/mail/operations/test_attachments.py
"""
Tests for Gmail attachment operations.

This module tests the attachment handling functionality for the Google Mail integration,
including processing message parts and handling attachments.
"""

import base64
import logging
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from quackcore.integrations.google.mail.operations import attachments
from quackcore.integrations.google.mail.protocols import (
    GmailAttachmentsResource,
    GmailMessagesResource,
    GmailRequest,
    GmailService,
    GmailUsersResource,
)


class TestGmailAttachmentOperations:
    """Tests for Gmail attachment operations."""

    @pytest.fixture
    def mock_gmail_service(self):
        """Create a protocol-compatible mock Gmail service."""

        # Create a proper mock hierarchy that matches the protocol structure
        class MockRequest(GmailRequest):
            def __init__(self, return_value: Any):
                self.return_value = return_value

            def execute(self) -> Any:
                return self.return_value

        class MockAttachmentsResource(GmailAttachmentsResource):
            def __init__(self):
                self.get_return: Optional[Dict[str, Any]] = None
                # Initialize the attributes that will be set later
                self.last_user_id: str = ""
                self.last_message_id: str = ""
                self.last_attachment_id: str = ""

            def get(
                self, user_id: str, message_id: str, attachment_id: str
            ) -> GmailRequest[Dict[str, Any]]:
                # Store the parameters for test assertions
                self.last_user_id = user_id
                self.last_message_id = message_id
                self.last_attachment_id = attachment_id
                return MockRequest(self.get_return)

        class MockMessagesResource(GmailMessagesResource):
            def __init__(self):
                self.attachments_resource = MockAttachmentsResource()

            def list(
                self, user_id: str, q: str, max_results: int
            ) -> GmailRequest[Dict[str, Any]]:
                return MockRequest({})

            def get(
                self, user_id: str, message_id: str, message_format: str
            ) -> GmailRequest[Dict[str, Any]]:
                return MockRequest({})

            def attachments(self) -> GmailAttachmentsResource:
                return self.attachments_resource

        class MockUsersResource(GmailUsersResource):
            def __init__(self):
                self.messages_resource = MockMessagesResource()

            def messages(self) -> GmailMessagesResource:
                return self.messages_resource

        class MockGmailService(GmailService):
            def __init__(self):
                self.users_resource = MockUsersResource()

            def users(self) -> GmailUsersResource:
                return self.users_resource

        # Create an instance of our protocol-compatible mock
        return MockGmailService()

    def test_handle_attachment(self, mock_gmail_service) -> None:
        """Test handling an attachment."""
        logger = logging.getLogger("test_gmail")
        msg_id = "msg1"
        storage_path = "/path/to/storage"

        # Set up attachment data
        attachment_data = base64.urlsafe_b64encode(b"PDF content").decode()

        # Test with inline data
        part = {
            "filename": "test.pdf",
            "mimeType": "application/pdf",
            "body": {"data": attachment_data, "size": 11},
        }

        # Use MagicMock for the file to properly handle method assertions
        mock_file = MagicMock()
        mock_open_func = MagicMock(return_value=mock_file)

        with patch("builtins.open", mock_open_func):
            with patch("os.path.exists", return_value=False):
                path = attachments.handle_attachment(
                    mock_gmail_service, "me", part, msg_id, storage_path, logger
                )

                assert path == "/path/to/storage/test.pdf"
                # Check if open was called with the right parameters
                mock_open_func.assert_called_with("/path/to/storage/test.pdf", "wb")
                # Check if write was called with the right content
                mock_file.write.assert_called_with(b"PDF content")

        # Test with attachment ID
        part = {
            "filename": "test.pdf",
            "mimeType": "application/pdf",
            "body": {"attachmentId": "attachment1", "size": 11},
        }

        # Set up the return value for attachments.get
        attachment_response = {"data": attachment_data, "size": 11}
        mock_gmail_service.users().messages().attachments().get_return = (
            attachment_response
        )

        # Use MagicMock for the file to properly handle method assertions
        mock_file = MagicMock()
        mock_open_func = MagicMock(return_value=mock_file)

        with patch("builtins.open", mock_open_func):
            with patch("os.path.exists", return_value=False):
                with patch(
                    "quackcore.integrations.google.mail.operations.attachments.execute_api_request",
                    return_value=attachment_response,
                ):
                    path = attachments.handle_attachment(
                        mock_gmail_service, "me", part, msg_id, storage_path, logger
                    )

                    assert path == "/path/to/storage/test.pdf"
                    # Check if open was called with the right parameters
                    mock_open_func.assert_called_with("/path/to/storage/test.pdf", "wb")
                    # Check if write was called with the right content
                    mock_file.write.assert_called_with(b"PDF content")

        # Test with filename collision
        mock_file = MagicMock()
        mock_open_func = MagicMock(return_value=mock_file)
        exists_calls = [True, False]  # For first and second calls to exists

        with patch("builtins.open", mock_open_func):
            with patch("os.path.exists", side_effect=exists_calls):
                path = attachments.handle_attachment(
                    mock_gmail_service, "me", part, msg_id, storage_path, logger
                )

                assert path == "/path/to/storage/test-1.pdf"
                # Check if open was called with the right parameters
                mock_open_func.assert_called_with("/path/to/storage/test-1.pdf", "wb")

        # Rest of the tests remain mostly the same
        # Test with missing filename
        part = {
            "mimeType": "application/pdf",
            "body": {"data": attachment_data, "size": 11},
        }

        path = attachments.handle_attachment(
            mock_gmail_service, "me", part, msg_id, storage_path, logger
        )

        assert path is None

        # Test with missing data
        part = {
            "filename": "test.pdf",
            "mimeType": "application/pdf",
            "body": {"size": 11},
        }

        path = attachments.handle_attachment(
            mock_gmail_service, "me", part, msg_id, storage_path, logger
        )

        assert path is None

        # Test with decode error
        part = {
            "filename": "test.pdf",
            "mimeType": "application/pdf",
            "body": {"data": "invalid base64", "size": 11},
        }

        path = attachments.handle_attachment(
            mock_gmail_service, "me", part, msg_id, storage_path, logger
        )

        assert path is None

        # Test with file write error
        part = {
            "filename": "test.pdf",
            "mimeType": "application/pdf",
            "body": {"data": attachment_data, "size": 11},
        }

        mock_open_func = MagicMock(side_effect=IOError("Permission denied"))

        with patch("builtins.open", mock_open_func):
            path = attachments.handle_attachment(
                mock_gmail_service, "me", part, msg_id, storage_path, logger
            )

            assert path is None

    def test_process_message_parts(self, mock_gmail_service) -> None:
        """Test processing message parts."""
        logger = logging.getLogger("test_gmail")
        msg_id = "msg1"
        storage_path = "/path/to/storage"

        # Test with HTML content and attachments
        parts = [
            {
                "mimeType": "text/html",
                "body": {
                    "data": base64.urlsafe_b64encode(
                        b"<html><body>Test</body></html>"
                    ).decode(),
                    "size": 30,
                },
            },
            {
                "filename": "attachment.pdf",
                "mimeType": "application/pdf",
                "body": {
                    "data": base64.urlsafe_b64encode(b"PDF content").decode(),
                    "size": 11,
                },
            },
        ]

        with patch(
            "quackcore.integrations.google.mail.operations.attachments.handle_attachment",
            return_value="/path/to/storage/attachment.pdf",
        ):
            html_content, attachments_list = attachments.process_message_parts(
                mock_gmail_service, "me", parts, msg_id, storage_path, logger
            )

            assert html_content == "<html><body>Test</body></html>"
            assert attachments_list == ["/path/to/storage/attachment.pdf"]

        # Test with nested parts
        parts = [
            {
                "mimeType": "multipart/mixed",
                "parts": [
                    {
                        "mimeType": "text/html",
                        "body": {
                            "data": base64.urlsafe_b64encode(
                                b"<html><body>Nested</body></html>"
                            ).decode(),
                            "size": 32,
                        },
                    }
                ],
            },
            {
                "filename": "attachment.pdf",
                "mimeType": "application/pdf",
                "body": {
                    "data": base64.urlsafe_b64encode(b"PDF content").decode(),
                    "size": 11,
                },
            },
        ]

        with patch(
            "quackcore.integrations.google.mail.operations.attachments.handle_attachment",
            return_value="/path/to/storage/attachment.pdf",
        ):
            html_content, attachments_list = attachments.process_message_parts(
                mock_gmail_service, "me", parts, msg_id, storage_path, logger
            )

            assert html_content == "<html><body>Nested</body></html>"
            assert attachments_list == ["/path/to/storage/attachment.pdf"]

        # Test with no HTML content
        parts = [
            {
                "mimeType": "text/plain",
                "body": {
                    "data": base64.urlsafe_b64encode(b"Plain text").decode(),
                    "size": 10,
                },
            }
        ]

        html_content, attachments_list = attachments.process_message_parts(
            mock_gmail_service, "me", parts, msg_id, storage_path, logger
        )

        assert html_content is None
        assert attachments_list == []

        # Test with multiple HTML parts (should use first found)
        parts = [
            {
                "mimeType": "text/html",
                "body": {
                    "data": base64.urlsafe_b64encode(
                        b"<html><body>First</body></html>"
                    ).decode(),
                    "size": 30,
                },
            },
            {
                "mimeType": "text/html",
                "body": {
                    "data": base64.urlsafe_b64encode(
                        b"<html><body>Second</body></html>"
                    ).decode(),
                    "size": 31,
                },
            },
        ]

        html_content, attachments_list = attachments.process_message_parts(
            mock_gmail_service, "me", parts, msg_id, storage_path, logger
        )

        assert html_content == "<html><body>First</body></html>"
        assert attachments_list == []

        # Test with failed attachment handling
        parts = [
            {
                "mimeType": "text/html",
                "body": {
                    "data": base64.urlsafe_b64encode(
                        b"<html><body>Test</body></html>"
                    ).decode(),
                    "size": 30,
                },
            },
            {
                "filename": "attachment.pdf",
                "mimeType": "application/pdf",
                "body": {
                    "data": base64.urlsafe_b64encode(b"PDF content").decode(),
                    "size": 11,
                },
            },
        ]

        with patch(
            "quackcore.integrations.google.mail.operations.attachments.handle_attachment",
            return_value=None,
        ):  # Attachment handling failed
            html_content, attachments_list = attachments.process_message_parts(
                mock_gmail_service, "me", parts, msg_id, storage_path, logger
            )

            assert html_content == "<html><body>Test</body></html>"
            assert attachments_list == []  # No attachments returned
