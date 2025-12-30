import uuid
from datetime import datetime

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import SAModel
from src.modules.teaching.enums import TeacherStudentStatus


class TeacherStudent(SAModel):
    """Teacher-student relationship with invite code."""

    __tablename__ = "teacher_students"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    student_id: Mapped[uuid.UUID | None] = mapped_column(
        SA_UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    invite_code: Mapped[str] = mapped_column(
        String(12),
        unique=True,
        index=True,
    )
    status: Mapped[TeacherStudentStatus] = mapped_column(
        default=TeacherStudentStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    accepted_at: Mapped[datetime | None] = mapped_column(nullable=True)

    __table_args__ = (
        UniqueConstraint(
            "teacher_id",
            "student_id",
            name="teacher_students_teacher_student_key",
        ),
    )
