# tests/quackster/test_npc/test_tools/test_certificate_tools.py
"""
Tests for the certificate tools in quackster.npc.tools.certificate_tools.

This module tests the functions for retrieving certificate information
and checking certificate eligibility.
"""

from unittest.mock import MagicMock

import pytest

from quackster.npc.schema import UserMemory
from quackster.npc.tools import CertificateListOutput, certificate_tools


class TestCertificateTools:
    """Tests for certificate tools functionality."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock user object for testing."""
        user = MagicMock()
        return user

    @pytest.fixture
    def user_memory_basics_incomplete(self):
        """Create a UserMemory object with incomplete quackverse-basics certificate."""
        return UserMemory(
            github_username="testuser",
            xp=50,  # Not enough XP for basics certificate
            level=1,
            completed_quests=["star-quackcore", "run-ducktyper"],  # Missing one quest
            badges=[],
            custom_data={"learning_style": "step by step"},
        )

    @pytest.fixture
    def user_memory_basics_complete(self):
        """Create a UserMemory object with complete quackverse-basics certificate."""
        return UserMemory(
            github_username="testuser",
            xp=150,  # Enough XP for basics certificate
            level=2,
            completed_quests=["star-quackcore", "run-ducktyper", "complete-tutorial"],
            badges=[],
            custom_data={"learning_style": "challenge"},
        )

    @pytest.fixture
    def user_memory_github_complete(self):
        """Create a UserMemory object with complete github-contributor certificate."""
        return UserMemory(
            github_username="testuser",
            xp=350,  # Enough XP for github certificate
            level=4,
            completed_quests=[
                "star-quackcore",
                "run-ducktyper",
                "complete-tutorial",
                "open-pr",
                "merged-pr",
            ],
            badges=["duck-team-player"],
            custom_data={"learning_style": "visual"},
        )

    def test_get_certificate_info_no_certificates(
        self, mocker, mock_user, user_memory_basics_incomplete
    ):
        """Test get_certificate_info with no earned certificates."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.certificate_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_certificates = mocker.patch(
            "quackster.npc.tools.certificate_tools.certificates"
        )
        # No certificates earned
        mock_certificates.has_earned_certificate.return_value = False

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.certificate_tools.standardize_tool_output"
        )
        mock_standardize.return_value = CertificateListOutput(
            name="get_certificate_info",
            result=MagicMock(),
            formatted_text="Certificate list output",
        )

        # Call the function
        result = certificate_tools.get_certificate_info(user_memory_basics_incomplete)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_certificates.has_earned_certificate.assert_any_call(
            mock_user, "quackverse-basics"
        )
        mock_certificates.has_earned_certificate.assert_any_call(
            mock_user, "github-contributor"
        )
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, CertificateListOutput)

        # Check that the standardized output contains correct data
        args = mock_standardize.call_args[0]
        assert args[0] == "get_certificate_info"
        assert args[1]["earned_any"] is False
        assert args[1]["certificate_count"] == 2
        assert args[1]["earned_count"] == 0
        assert "certificates" in args[1]
        assert "formatted_text" in args[1]
        assert (
            "Certificate Path" in args[1]["formatted_text"]
        )  # Step by step learning style

    def test_get_certificate_info_with_earned_certificate(
        self, mocker, mock_user, user_memory_basics_complete
    ):
        """Test get_certificate_info with earned certificates."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.certificate_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_certificates = mocker.patch(
            "quackster.npc.tools.certificate_tools.certificates"
        )
        # First certificate earned, second not earned
        mock_certificates.has_earned_certificate.side_effect = (
            lambda u, cert_id: cert_id == "quackverse-basics"
        )

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.certificate_tools.standardize_tool_output"
        )
        mock_standardize.return_value = CertificateListOutput(
            name="get_certificate_info",
            result=MagicMock(),
            formatted_text="Certificate list output with earned cert",
        )

        # Call the function
        result = certificate_tools.get_certificate_info(user_memory_basics_complete)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_certificates.has_earned_certificate.assert_any_call(
            mock_user, "quackverse-basics"
        )
        mock_certificates.has_earned_certificate.assert_any_call(
            mock_user, "github-contributor"
        )
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, CertificateListOutput)

        # Check that the standardized output contains correct data
        args = mock_standardize.call_args[0]
        assert args[0] == "get_certificate_info"
        assert args[1]["earned_any"] is True
        assert args[1]["certificate_count"] == 2
        assert args[1]["earned_count"] == 1
        assert "certificates" in args[1]
        assert "formatted_text" in args[1]
        assert (
            "Certificate Challenges" in args[1]["formatted_text"]
        )  # Challenge learning style
        assert "To generate your certificate" in args[1]["formatted_text"]

    def test_get_certificate_info_all_certificates_earned(
        self, mocker, mock_user, user_memory_github_complete
    ):
        """Test get_certificate_info with all certificates earned."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.certificate_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_certificates = mocker.patch(
            "quackster.npc.tools.certificate_tools.certificates"
        )
        # All certificates earned
        mock_certificates.has_earned_certificate.return_value = True

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.certificate_tools.standardize_tool_output"
        )
        mock_standardize.return_value = CertificateListOutput(
            name="get_certificate_info",
            result=MagicMock(),
            formatted_text="All certificates earned output",
        )

        # Call the function
        result = certificate_tools.get_certificate_info(user_memory_github_complete)

        # Verify dependencies were called correctly
        mock_utils.load_progress.assert_called_once()
        mock_certificates.has_earned_certificate.assert_any_call(
            mock_user, "quackverse-basics"
        )
        mock_certificates.has_earned_certificate.assert_any_call(
            mock_user, "github-contributor"
        )
        mock_standardize.assert_called_once()

        # Verify result
        assert isinstance(result, CertificateListOutput)

        # Check that the standardized output contains correct data
        args = mock_standardize.call_args[0]
        assert args[0] == "get_certificate_info"
        assert args[1]["earned_any"] is True
        assert args[1]["certificate_count"] == 2
        assert args[1]["earned_count"] == 2
        assert "certificates" in args[1]
        assert "formatted_text" in args[1]
        assert "To generate your certificate" in args[1]["formatted_text"]

    def test_certificate_progress_calculation(
        self, mocker, mock_user, user_memory_basics_incomplete
    ):
        """Test that certificate progress is calculated correctly."""
        # Mock dependencies
        mock_utils = mocker.patch("quackster.npc.tools.certificate_tools.utils")
        mock_utils.load_progress.return_value = mock_user

        mock_certificates = mocker.patch(
            "quackster.npc.tools.certificate_tools.certificates"
        )
        mock_certificates.has_earned_certificate.return_value = False

        # Mock standardize_tool_output
        mock_standardize = mocker.patch(
            "quackster.npc.tools.certificate_tools.standardize_tool_output"
        )
        mock_standardize.return_value = CertificateListOutput(
            name="get_certificate_info",
            result=MagicMock(),
            formatted_text="Certificate progress output",
        )

        # Call the function
        certificate_tools.get_certificate_info(user_memory_basics_incomplete)

        # Check progress calculation
        args = mock_standardize.call_args[0]
        certificates = args[1]["certificates"]

        # Find the quackverse-basics certificate
        basics_cert = next(
            cert for cert in certificates if cert.id == "quackverse-basics"
        )

        # User has 2 out of 3 quests and 50/100 XP, so progress should be 50%
        assert basics_cert.progress == 50.0

        # Find the github-contributor certificate
        github_cert = next(
            cert for cert in certificates if cert.id == "github-contributor"
        )

        # User has 0 out of 4 requirements, so progress should be 0%
        assert github_cert.progress == 0.0
