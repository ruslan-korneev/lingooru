"""Voice module database models - PronunciationLog."""

import uuid
from datetime import datetime

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import SAModel


class PronunciationLog(SAModel):
    """Log of pronunciation practice attempts."""

    __tablename__ = "pronunciation_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    word_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("words.id", ondelete="CASCADE"),
        index=True,
    )

    transcribed_text: Mapped[str] = mapped_column(String(500))
    expected_text: Mapped[str] = mapped_column(String(255))
    rating: Mapped[int] = mapped_column(Integer)  # 1-5
    feedback: Mapped[str] = mapped_column(Text)
    audio_duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
