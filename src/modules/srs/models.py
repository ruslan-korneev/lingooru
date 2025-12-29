"""SRS database models - Review and ReviewLog."""

import uuid
from datetime import datetime

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import SAModel


class Review(SAModel):
    """Tracks SM-2 progress for each user word."""

    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_word_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("user_words.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )

    # SM-2 parameters
    easiness: Mapped[float] = mapped_column(Float, default=2.5)
    interval: Mapped[int] = mapped_column(Integer, default=0)  # days
    repetitions: Mapped[int] = mapped_column(Integer, default=0)

    next_review: Mapped[datetime] = mapped_column(default=datetime.now, index=True)
    last_review: Mapped[datetime | None] = mapped_column(nullable=True)

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class ReviewLog(SAModel):
    """History of review responses for analytics."""

    __tablename__ = "review_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    review_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("reviews.id", ondelete="CASCADE"),
        index=True,
    )
    quality: Mapped[int]  # 1-5 rating
    response_time_ms: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
