import uuid
from datetime import datetime

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import BigInteger, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import SAModel
from src.modules.users.enums import LanguagePair, UILanguage


class User(SAModel):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ui_language: Mapped[UILanguage] = mapped_column(default=UILanguage.RU)
    language_pair: Mapped[LanguagePair] = mapped_column(default=LanguagePair.EN_RU)

    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    notifications_enabled: Mapped[bool] = mapped_column(default=True)
    notification_times: Mapped[list[str]] = mapped_column(
        ARRAY(String),
        default=["09:00", "21:00"],
    )

    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.now,
        onupdate=datetime.now,
    )
