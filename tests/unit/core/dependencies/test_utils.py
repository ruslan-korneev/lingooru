"""Tests for core dependency utilities."""

import pytest
from fastapi import HTTPException

from src.core.dependencies.utils import validated_email, validated_optional_email, validated_uuid

HTTP_BAD_REQUEST = 400


class TestValidatedUuid:
    """Tests for validated_uuid function."""

    def test_valid_uuid_lowercase(self) -> None:
        """Accepts valid lowercase UUID."""
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"

        result = validated_uuid(uuid_str)

        assert result == uuid_str

    def test_valid_uuid_uppercase(self) -> None:
        """Accepts valid uppercase UUID and returns lowercase."""
        uuid_str = "123E4567-E89B-12D3-A456-426614174000"

        result = validated_uuid(uuid_str)

        assert result == uuid_str.lower()

    def test_valid_uuid_mixed_case(self) -> None:
        """Accepts valid mixed-case UUID and returns lowercase."""
        uuid_str = "123e4567-E89B-12d3-A456-426614174000"

        result = validated_uuid(uuid_str)

        assert result == uuid_str.lower()

    def test_invalid_uuid_format(self) -> None:
        """Raises HTTPException for invalid UUID format."""
        with pytest.raises(HTTPException) as exc_info:
            validated_uuid("not-a-uuid")

        assert exc_info.value.status_code == HTTP_BAD_REQUEST
        assert "Invalid UUID format" in exc_info.value.detail

    def test_invalid_uuid_too_short(self) -> None:
        """Raises HTTPException for too short UUID."""
        with pytest.raises(HTTPException) as exc_info:
            validated_uuid("123e4567-e89b-12d3-a456")

        assert exc_info.value.status_code == HTTP_BAD_REQUEST

    def test_invalid_uuid_wrong_chars(self) -> None:
        """Raises HTTPException for UUID with invalid characters."""
        with pytest.raises(HTTPException) as exc_info:
            validated_uuid("123g4567-e89b-12d3-a456-426614174000")  # 'g' is invalid

        assert exc_info.value.status_code == HTTP_BAD_REQUEST

    def test_invalid_uuid_no_dashes(self) -> None:
        """Raises HTTPException for UUID without dashes."""
        with pytest.raises(HTTPException) as exc_info:
            validated_uuid("123e4567e89b12d3a456426614174000")

        assert exc_info.value.status_code == HTTP_BAD_REQUEST

    def test_empty_string(self) -> None:
        """Raises HTTPException for empty string."""
        with pytest.raises(HTTPException) as exc_info:
            validated_uuid("")

        assert exc_info.value.status_code == HTTP_BAD_REQUEST


class TestValidatedEmail:
    """Tests for validated_email function."""

    def test_valid_email_simple(self) -> None:
        """Accepts valid simple email."""
        email = "user@example.com"

        result = validated_email(email)

        assert result == email

    def test_valid_email_with_dots(self) -> None:
        """Accepts valid email with dots in local part."""
        email = "user.name@example.com"

        result = validated_email(email)

        assert result == email

    def test_valid_email_with_plus(self) -> None:
        """Accepts valid email with plus sign."""
        email = "user+tag@example.com"

        result = validated_email(email)

        assert result == email

    def test_valid_email_uppercase_returns_lowercase(self) -> None:
        """Accepts uppercase email and returns lowercase."""
        email = "USER@EXAMPLE.COM"

        result = validated_email(email)

        assert result == "user@example.com"

    def test_valid_email_subdomain(self) -> None:
        """Accepts valid email with subdomain."""
        email = "user@mail.example.com"

        result = validated_email(email)

        assert result == email

    def test_invalid_email_no_at(self) -> None:
        """Raises HTTPException for email without @ sign."""
        with pytest.raises(HTTPException) as exc_info:
            validated_email("userexample.com")

        assert exc_info.value.status_code == HTTP_BAD_REQUEST
        assert "Invalid email format" in exc_info.value.detail

    def test_invalid_email_no_domain(self) -> None:
        """Raises HTTPException for email without domain."""
        with pytest.raises(HTTPException) as exc_info:
            validated_email("user@")

        assert exc_info.value.status_code == HTTP_BAD_REQUEST

    def test_invalid_email_no_tld(self) -> None:
        """Raises HTTPException for email without TLD."""
        with pytest.raises(HTTPException) as exc_info:
            validated_email("user@example")

        assert exc_info.value.status_code == HTTP_BAD_REQUEST

    def test_invalid_email_short_tld(self) -> None:
        """Raises HTTPException for email with too short TLD."""
        with pytest.raises(HTTPException) as exc_info:
            validated_email("user@example.c")

        assert exc_info.value.status_code == HTTP_BAD_REQUEST

    def test_empty_string(self) -> None:
        """Raises HTTPException for empty string."""
        with pytest.raises(HTTPException) as exc_info:
            validated_email("")

        assert exc_info.value.status_code == HTTP_BAD_REQUEST


class TestValidatedOptionalEmail:
    """Tests for validated_optional_email function."""

    def test_none_returns_none(self) -> None:
        """Returns None when input is None."""
        result = validated_optional_email(None)

        assert result is None

    def test_valid_email_returns_lowercase(self) -> None:
        """Validates and returns lowercase email."""
        result = validated_optional_email("USER@EXAMPLE.COM")

        assert result == "user@example.com"

    def test_invalid_email_raises(self) -> None:
        """Raises HTTPException for invalid email."""
        with pytest.raises(HTTPException) as exc_info:
            validated_optional_email("not-an-email")

        assert exc_info.value.status_code == HTTP_BAD_REQUEST
        assert "Invalid email format" in exc_info.value.detail
