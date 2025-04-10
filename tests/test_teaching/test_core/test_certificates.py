"""
Tests for the teaching certificates module.

This module tests the certificate functionality in quackcore.teaching.core.certificates.
"""
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from quackcore.teaching.core.models import UserProgress
from quackcore.teaching.core import certificates


class TestCertificates:
    """Tests for certificate functionality."""

    @patch("quackcore.teaching.core.certificates.time")
    @patch("quackcore.teaching.core.certificates.datetime")
    @patch("quackcore.teaching.core.certificates.logger")
    @patch("quackcore.teaching.core.certificates._sign_certificate")
    def test_create_certificate(self, mock_sign, mock_logger, mock_datetime, mock_time):
        """Test creating a certificate."""
        # Setup
        user = UserProgress(github_username="testuser", xp=300)
        course_id = "test-course"
        issuer = "Test Issuer"
        additional_data = {"course_name": "Test Course"}

        # Mock the timestamp and date
        timestamp = 1712751600  # April 10, 2025
        mock_time.time.return_value = timestamp
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2025-04-10"
        mock_datetime.now.return_value = mock_now

        # Mock the signature
        mock_sign.return_value = "test-signature"

        # Mock the GamificationService
        mock_gamification_service = MagicMock()
        mock_award_badge_result = MagicMock()
        mock_award_badge_result.message = "Badge awarded"
        mock_gamification_service.award_badge.return_value = mock_award_badge_result

        mock_course_completion_result = MagicMock()
        mock_course_completion_result.message = "Course completed"
        mock_gamification_service.handle_course_completion.return_value = mock_course_completion_result

        with patch("quackcore.teaching.core.certificates.GamificationService",
                   return_value=mock_gamification_service):
            # Act
            certificate = certificates.create_certificate(
                user, course_id, issuer, additional_data
            )

            # Assert
            assert certificate["version"] == "1.0"
            assert certificate["type"] == "course-completion"
            assert certificate["course_id"] == course_id
            assert certificate["issuer"] == issuer
            assert certificate["recipient"] == "testuser"
            assert certificate["issued_at"] == timestamp
            assert certificate["issued_date"] == "2025-04-10"
            assert certificate["xp"] == 300
            assert certificate["level"] == 4  # Level 4 at 300 XP
            assert certificate["course_name"] == "Test Course"
            assert "id" in certificate
            assert certificate["signature"] == "test-signature"

            # Verify gamification integration
            mock_gamification_service.award_badge.assert_called_with("duck-graduate")
            mock_gamification_service.handle_course_completion.assert_called_with(
                course_id, "Test Course"
            )
            mock_logger.info.assert_called()

    def test_create_certificate_no_github_username(self):
        """Test creating a certificate for a user without GitHub username."""
        # Setup
        user = UserProgress(github_username=None, xp=100)
        course_id = "test-course"

        # Act & Assert
        with pytest.raises(ValueError, match="User must have a GitHub username"):
            certificates.create_certificate(user, course_id)

    @patch("quackcore.teaching.core.certificates._sign_certificate")
    def test_verify_certificate_valid(self, mock_sign):
        """Test verifying a valid certificate."""
        # Setup
        certificate = {
            "id": "abc123",
            "version": "1.0",
            "type": "course-completion",
            "course_id": "test-course",
            "issuer": "Test Issuer",
            "recipient": "testuser",
            "issued_at": 1712751600,
            "signature": "valid-signature",
        }

        # Mock the signature verification
        mock_sign.return_value = "valid-signature"

        # Act
        result = certificates.verify_certificate(certificate)

        # Assert
        assert result is True
        # We should have created a copy of the certificate without the signature
        cert_copy = dict(certificate)
        cert_copy.pop("signature", None)
        mock_sign.assert_called_with(cert_copy)

    @patch("quackcore.teaching.core.certificates.logger")
    def test_verify_certificate_missing_fields(self, mock_logger):
        """Test verifying a certificate with missing required fields."""
        # Setup
        certificate = {
            "id": "abc123",
            "version": "1.0",
            # Missing type
            "course_id": "test-course",
            "issuer": "Test Issuer",
            "recipient": "testuser",
            "issued_at": 1712751600,
            "signature": "valid-signature",
        }

        # Act
        result = certificates.verify_certificate(certificate)

        # Assert
        assert result is False
        mock_logger.warning.assert_called()

    @patch("quackcore.teaching.core.certificates._sign_certificate")
    @patch("quackcore.teaching.core.certificates.logger")
    def test_verify_certificate_invalid_signature(self, mock_logger, mock_sign):
        """Test verifying a certificate with an invalid signature."""
        # Setup
        certificate = {
            "id": "abc123",
            "version": "1.0",
            "type": "course-completion",
            "course_id": "test-course",
            "issuer": "Test Issuer",
            "recipient": "testuser",
            "issued_at": 1712751600,
            "signature": "invalid-signature",
        }

        # Mock the signature verification
        mock_sign.return_value = "valid-signature"  # Different from the certificate

        # Act
        result = certificates.verify_certificate(certificate)

        # Assert
        assert result is False
        mock_logger.warning.assert_called_with(
            "Certificate signature verification failed")

    def test_certificate_to_string(self):
        """Test converting a certificate to a string format."""
        # Setup
        certificate = {
            "id": "abc123",
            "version": "1.0",
            "type": "course-completion",
            "course_id": "test-course",
            "issuer": "Test Issuer",
            "recipient": "testuser",
        }

        # Act
        cert_string = certificates.certificate_to_string(certificate)

        # Assert
        assert isinstance(cert_string, str)
        # Check that the string is valid base64
        decoded = base64.b64decode(cert_string).decode("utf-8")
        decoded_cert = json.loads(decoded)
        assert decoded_cert == certificate

    def test_string_to_certificate_valid(self):
        """Test converting a valid certificate string back to a dictionary."""
        # Setup
        certificate = {
            "id": "abc123",
            "version": "1.0",
            "type": "course-completion",
            "course_id": "test-course",
            "issuer": "Test Issuer",
            "recipient": "testuser",
        }
        cert_json = json.dumps(certificate)
        cert_bytes = cert_json.encode("utf-8")
        cert_b64 = base64.b64encode(cert_bytes).decode("utf-8")

        # Act
        result = certificates.string_to_certificate(cert_b64)

        # Assert
        assert result == certificate

    @patch("quackcore.teaching.core.certificates.logger")
    def test_string_to_certificate_invalid(self, mock_logger):
        """Test handling an invalid certificate string."""
        # Setup
        invalid_string = "not-valid-base64"

        # Act & Assert
        with pytest.raises(ValueError, match="Invalid certificate string"):
            certificates.string_to_certificate(invalid_string)
        mock_logger.error.assert_called()

    def test_format_certificate_markdown(self):
        """Test formatting a certificate as markdown."""
        # Setup
        certificate = {
            "id": "abc123def456",
            "version": "1.0",
            "type": "course-completion",
            "course_id": "test-course",
            "course_name": "Test Course",
            "issuer": "Test Issuer",
            "recipient": "testuser",
            "issued_date": "2025-04-10",
            "level": 3,
            "xp": 250,
        }

        # Act
        markdown = certificates.format_certificate_markdown(certificate)

        # Assert
        assert "# Certificate of Completion" in markdown
        assert "**Course:** test-course" in markdown
        assert "**Issued To:** testuser" in markdown
        assert "**Date:** 2025-04-10" in markdown
        assert "**Verification ID:** abc123de" in markdown
        assert "Level achieved: 3" in markdown
        assert "XP earned: 250" in markdown

    @patch("quackcore.teaching.core.certificates.hmac")
    def test_sign_certificate(self, mock_hmac):
        """Test signing a certificate."""
        # Setup
        certificate = {
            "id": "abc123",
            "version": "1.0",
            "type": "course-completion",
            "course_id": "test-course",
        }

        mock_hmac_instance = MagicMock()
        mock_hmac_instance.hexdigest.return_value = "fake-signature"
        mock_hmac.new.return_value = mock_hmac_instance

        # Act
        result = certificates._sign_certificate(certificate)

        # Assert
        assert result == "fake-signature"
        # Verify HMAC was created with sorted keys for consistency
        mock_hmac.new.assert_called_once()
        # The first arg should be the secret key
        assert mock_hmac.new.call_args[0][0] == certificates.CERTIFICATE_SECRET.encode()
        # The second arg should be the JSON string of the certificate with sorted keys
        cert_json = json.dumps(certificate, sort_keys=True)
        assert mock_hmac.new.call_args[0][1] == cert_json.encode()
        # The third arg should be the hashlib.sha256 algorithm
        assert mock_hmac.new.call_args[0][2] == hashlib.sha256

    def test_has_earned_certificate_basic_course(self):
        """Test checking if a user has earned a certificate for the basic course."""
        # Setup
        user = UserProgress(
            github_username="testuser",
            xp=150,
            completed_quest_ids=["star-quackcore", "run-ducktyper",
                                 "complete-tutorial"],
        )

        # Act
        result = certificates.has_earned_certificate(user, "quackverse-basics")

        # Assert
        assert result is True

    def test_has_earned_certificate_missing_xp(self):
        """Test certification check when user has completed quests but lacks XP."""
        # Setup
        user = UserProgress(
            github_username="testuser",
            xp=80,  # Not enough XP
            completed_quest_ids=["star-quackcore", "run-ducktyper",
                                 "complete-tutorial"],
        )

        # Act
        result = certificates.has_earned_certificate(user, "quackverse-basics")

        # Assert
        assert result is False

    def test_has_earned_certificate_missing_quests(self):
        """Test certification check when user has XP but hasn't completed required quests."""
        # Setup
        user = UserProgress(
            github_username="testuser",
            xp=150,
            completed_quest_ids=["star-quackcore", "run-ducktyper"],
            # Missing "complete-tutorial"
        )

        # Act
        result = certificates.has_earned_certificate(user, "quackverse-basics")

        # Assert
        assert result is False

    def test_has_earned_certificate_other_course(self):
        """Test checking certification for a course other than quackverse-basics."""
        # Setup
        user = UserProgress(
            github_username="testuser",
            xp=150,
            completed_quest_ids=["star-quackcore", "run-ducktyper",
                                 "complete-tutorial"],
        )

        # Act
        result = certificates.has_earned_certificate(user, "other-course")

        # Assert
        assert result is False  # No specific implementation for other courses