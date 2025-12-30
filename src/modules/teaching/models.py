import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import UUID as SA_UUID
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import SAModel
from src.modules.teaching.enums import (
    AssignmentStatus,
    AssignmentType,
    TeacherStudentStatus,
)


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


class Assignment(SAModel):
    """Assignment from teacher to student."""

    __tablename__ = "assignments"

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
    student_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assignment_type: Mapped[AssignmentType]
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    status: Mapped[AssignmentStatus] = mapped_column(
        default=AssignmentStatus.PUBLISHED,
    )
    ai_generated: Mapped[bool] = mapped_column(default=False)
    due_date: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)


class AssignmentSubmission(SAModel):
    """Student's submission for an assignment."""

    __tablename__ = "assignment_submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("assignments.id", ondelete="CASCADE"),
        index=True,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        SA_UUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    content: Mapped[dict[str, Any]] = mapped_column(JSON)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_score: Mapped[int | None] = mapped_column(nullable=True)
    teacher_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    grade: Mapped[int | None] = mapped_column(nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(default=datetime.now)
    graded_at: Mapped[datetime | None] = mapped_column(nullable=True)
