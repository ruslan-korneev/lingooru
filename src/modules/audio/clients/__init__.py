"""Audio clients for TTS and storage."""

from src.modules.audio.clients.gtts_client import GTTSClient, get_gtts_client
from src.modules.audio.clients.s3_client import S3Client, get_s3_client

__all__ = ["GTTSClient", "S3Client", "get_gtts_client", "get_s3_client"]
