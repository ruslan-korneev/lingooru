"""Unit tests for S3 client with mocks."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import BotoCoreError, ClientError

from src.modules.audio.clients.s3_client import S3Client, get_s3_client


class TestS3Client:
    """Tests for S3Client methods."""

    @pytest.fixture
    def s3_client(self) -> S3Client:
        """Create a fresh S3Client for each test."""
        return S3Client()

    @pytest.fixture
    def mock_s3_client_context(self) -> tuple[AsyncMock, AsyncMock]:
        """Create a mock for the S3 client context manager."""
        mock_client = AsyncMock()
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_client
        mock_context.__aexit__.return_value = None
        return mock_context, mock_client

    async def test_upload_audio_success(
        self,
        s3_client: S3Client,
        mock_s3_client_context: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test successful audio upload."""
        mock_context, mock_client = mock_s3_client_context
        mock_client.put_object = AsyncMock()

        with patch.object(s3_client, "_get_client", return_value=mock_context):
            result = await s3_client.upload_audio(
                audio_bytes=b"test audio data",
                key="words/test.mp3",
            )

        mock_client.put_object.assert_called_once()
        assert "words/test.mp3" in result

    async def test_upload_audio_client_error(
        self,
        s3_client: S3Client,
        mock_s3_client_context: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test upload raises on ClientError."""
        mock_context, mock_client = mock_s3_client_context
        mock_client.put_object = AsyncMock(
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Internal Error"}},
                "PutObject",
            )
        )

        with (
            patch.object(s3_client, "_get_client", return_value=mock_context),
            pytest.raises(ClientError),
        ):
            await s3_client.upload_audio(b"data", "key.mp3")

    async def test_upload_audio_botocore_error(
        self,
        s3_client: S3Client,
        mock_s3_client_context: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test upload raises on BotoCoreError."""
        mock_context, mock_client = mock_s3_client_context
        mock_client.put_object = AsyncMock(side_effect=BotoCoreError())

        with (
            patch.object(s3_client, "_get_client", return_value=mock_context),
            pytest.raises(BotoCoreError),
        ):
            await s3_client.upload_audio(b"data", "key.mp3")

    async def test_file_exists_true(
        self,
        s3_client: S3Client,
        mock_s3_client_context: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test file_exists returns True when file exists."""
        mock_context, mock_client = mock_s3_client_context
        mock_client.head_object = AsyncMock()

        with patch.object(s3_client, "_get_client", return_value=mock_context):
            result = await s3_client.file_exists("existing_key.mp3")

        assert result is True

    async def test_file_exists_false_client_error(
        self,
        s3_client: S3Client,
        mock_s3_client_context: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test file_exists returns False on ClientError (file not found)."""
        mock_context, mock_client = mock_s3_client_context
        mock_client.head_object = AsyncMock(
            side_effect=ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}},
                "HeadObject",
            )
        )

        with patch.object(s3_client, "_get_client", return_value=mock_context):
            result = await s3_client.file_exists("nonexistent.mp3")

        assert result is False

    async def test_file_exists_false_botocore_error(
        self,
        s3_client: S3Client,
        mock_s3_client_context: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test file_exists returns False on BotoCoreError."""
        mock_context, mock_client = mock_s3_client_context
        mock_client.head_object = AsyncMock(side_effect=BotoCoreError())

        with patch.object(s3_client, "_get_client", return_value=mock_context):
            result = await s3_client.file_exists("error.mp3")

        assert result is False

    async def test_get_file_success(
        self,
        s3_client: S3Client,
        mock_s3_client_context: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test successful file download."""
        mock_context, mock_client = mock_s3_client_context
        mock_stream = AsyncMock()
        mock_stream.read = AsyncMock(return_value=b"file content")
        mock_response = {"Body": MagicMock()}
        mock_response["Body"].__aenter__ = AsyncMock(return_value=mock_stream)
        mock_response["Body"].__aexit__ = AsyncMock()
        mock_client.get_object = AsyncMock(return_value=mock_response)

        with patch.object(s3_client, "_get_client", return_value=mock_context):
            result = await s3_client.get_file("test.mp3")

        assert result == b"file content"

    async def test_get_file_not_found(
        self,
        s3_client: S3Client,
        mock_s3_client_context: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test get_file returns None when file not found."""
        mock_context, mock_client = mock_s3_client_context
        mock_client.get_object = AsyncMock(
            side_effect=ClientError(
                {"Error": {"Code": "404", "Message": "Not Found"}},
                "GetObject",
            )
        )

        with patch.object(s3_client, "_get_client", return_value=mock_context):
            result = await s3_client.get_file("nonexistent.mp3")

        assert result is None

    async def test_delete_success(
        self,
        s3_client: S3Client,
        mock_s3_client_context: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test successful file deletion."""
        mock_context, mock_client = mock_s3_client_context
        mock_client.delete_object = AsyncMock()

        with patch.object(s3_client, "_get_client", return_value=mock_context):
            await s3_client.delete("test.mp3")

        mock_client.delete_object.assert_called_once()

    async def test_delete_error(
        self,
        s3_client: S3Client,
        mock_s3_client_context: tuple[MagicMock, AsyncMock],
    ) -> None:
        """Test delete raises on error."""
        mock_context, mock_client = mock_s3_client_context
        mock_client.delete_object = AsyncMock(
            side_effect=ClientError(
                {"Error": {"Code": "500", "Message": "Error"}},
                "DeleteObject",
            )
        )

        with (
            patch.object(s3_client, "_get_client", return_value=mock_context),
            pytest.raises(ClientError),
        ):
            await s3_client.delete("test.mp3")

    def test_get_public_url_with_base(self, s3_client: S3Client) -> None:
        """Test URL generation with public_url_base set."""
        with patch("src.modules.audio.clients.s3_client.settings") as mock_settings:
            mock_settings.s3.public_url_base = "https://cdn.example.com"
            mock_settings.s3.endpoint_url = "https://s3.example.com"
            mock_settings.s3.bucket_name = "test-bucket"

            result = s3_client._get_public_url("test/file.mp3")  # noqa: SLF001

        assert result == "https://cdn.example.com/test/file.mp3"

    def test_get_public_url_without_base(self, s3_client: S3Client) -> None:
        """Test URL generation without public_url_base (fallback)."""
        with patch("src.modules.audio.clients.s3_client.settings") as mock_settings:
            mock_settings.s3.public_url_base = None
            mock_settings.s3.endpoint_url = "https://s3.example.com"
            mock_settings.s3.bucket_name = "test-bucket"

            result = s3_client._get_public_url("test/file.mp3")  # noqa: SLF001

        assert result == "https://s3.example.com/test-bucket/test/file.mp3"


class TestS3ClientSingleton:
    """Tests for S3Client singleton pattern."""

    def test_get_s3_client_returns_instance(self) -> None:
        """Test that get_s3_client returns an S3Client instance."""
        client = get_s3_client()

        assert isinstance(client, S3Client)

    def test_get_s3_client_returns_same_instance(self) -> None:
        """Test that get_s3_client returns the same singleton."""
        client1 = get_s3_client()
        client2 = get_s3_client()

        assert client1 is client2
