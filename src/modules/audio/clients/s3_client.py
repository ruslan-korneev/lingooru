"""S3/MinIO client for audio file storage."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

import aioboto3
from botocore.exceptions import BotoCoreError, ClientError
from loguru import logger

from src.config import settings

if TYPE_CHECKING:
    from types_aiobotocore_s3 import S3Client as S3ClientType


class S3Client:
    """Async S3 client for audio file storage."""

    def __init__(self) -> None:
        self._session = aioboto3.Session()

    @asynccontextmanager
    async def _get_client(self) -> AsyncIterator["S3ClientType"]:
        """Get an S3 client context manager."""
        async with self._session.client(
            "s3",
            endpoint_url=settings.s3.endpoint_url,
            aws_access_key_id=settings.s3.access_key.get_secret_value(),
            aws_secret_access_key=settings.s3.secret_key.get_secret_value(),
            region_name=settings.s3.region,
        ) as client:
            yield client

    async def upload_audio(
        self,
        audio_bytes: bytes,
        key: str,
        content_type: str = "audio/mpeg",
    ) -> str:
        """Upload audio and return public URL.

        Args:
            audio_bytes: Audio data to upload
            key: S3 object key (e.g., "words/{word_id}.mp3")
            content_type: MIME type of the audio

        Returns:
            Public URL for the uploaded file
        """
        try:
            async with self._get_client() as client:
                await client.put_object(
                    Bucket=settings.s3.bucket_name,
                    Key=key,
                    Body=audio_bytes,
                    ContentType=content_type,
                )
            return self._get_public_url(key)
        except (ClientError, BotoCoreError) as e:
            logger.error(f"S3 upload failed for key '{key}': {e}")
            raise

    async def file_exists(self, key: str) -> bool:
        """Check if file exists in bucket."""
        try:
            async with self._get_client() as client:
                await client.head_object(
                    Bucket=settings.s3.bucket_name,
                    Key=key,
                )
        except (ClientError, BotoCoreError):
            return False
        else:
            return True

    async def get_file(self, key: str) -> bytes | None:
        """Download file from S3."""
        try:
            async with self._get_client() as client:
                response = await client.get_object(
                    Bucket=settings.s3.bucket_name,
                    Key=key,
                )
                async with response["Body"] as stream:
                    return await stream.read()
        except (ClientError, BotoCoreError) as e:
            logger.error(f"S3 download failed for key '{key}': {e}")
            return None

    async def delete(self, key: str) -> None:
        """Delete file from bucket."""
        try:
            async with self._get_client() as client:
                await client.delete_object(
                    Bucket=settings.s3.bucket_name,
                    Key=key,
                )
        except (ClientError, BotoCoreError) as e:
            logger.error(f"S3 delete failed for key '{key}': {e}")
            raise

    def _get_public_url(self, key: str) -> str:
        """Get public URL for file."""
        if settings.s3.public_url_base:
            return f"{settings.s3.public_url_base.rstrip('/')}/{key}"
        return f"{settings.s3.endpoint_url}/{settings.s3.bucket_name}/{key}"


class _S3ClientHolder:
    """Holder for singleton S3 client instance."""

    _instance: S3Client | None = None

    @classmethod
    def get(cls) -> S3Client:
        if cls._instance is None:
            cls._instance = S3Client()
        return cls._instance


def get_s3_client() -> S3Client:
    """Get the singleton S3 client instance."""
    return _S3ClientHolder.get()
