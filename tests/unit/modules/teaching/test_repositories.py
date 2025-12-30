"""Tests for teaching repositories."""

from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.teaching.dto import TeacherStudentCreateDTO
from src.modules.teaching.enums import TeacherStudentStatus
from src.modules.teaching.repositories import TeacherStudentRepository
from src.modules.users.dto import UserReadDTO


class TestTeacherStudentRepository:
    """Tests for TeacherStudentRepository."""

    async def test_save_creates_record(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """save creates a new teacher-student record."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=None,
            invite_code="TEST12345678",
            status=TeacherStudentStatus.PENDING,
        )

        result = await teacher_student_repository.save(dto)
        await session.flush()

        assert result.id is not None
        assert result.teacher_id == sample_user.id
        assert result.invite_code == "TEST12345678"

    async def test_get_by_invite_code_returns_dto(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """get_by_invite_code returns DTO for valid code."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=None,
            invite_code="FINDME123456",
            status=TeacherStudentStatus.PENDING,
        )
        await teacher_student_repository.save(dto)
        await session.flush()

        result = await teacher_student_repository.get_by_invite_code("FINDME123456")

        assert result is not None
        assert result.invite_code == "FINDME123456"

    async def test_get_by_invite_code_returns_none_for_invalid(
        self,
        teacher_student_repository: TeacherStudentRepository,
    ) -> None:
        """get_by_invite_code returns None for invalid code."""
        result = await teacher_student_repository.get_by_invite_code("NOTEXIST1234")

        assert result is None

    async def test_get_model_by_invite_code_returns_model(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """get_model_by_invite_code returns SQLAlchemy model."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=None,
            invite_code="MODELTEST123",
            status=TeacherStudentStatus.PENDING,
        )
        await teacher_student_repository.save(dto)
        await session.flush()

        result = await teacher_student_repository.get_model_by_invite_code("MODELTEST123")

        assert result is not None
        assert result.invite_code == "MODELTEST123"

    async def test_get_by_teacher_and_student_returns_dto(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """get_by_teacher_and_student returns DTO when exists."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=second_sample_user.id,
            invite_code="PAIR12345678",
            status=TeacherStudentStatus.ACTIVE,
        )
        await teacher_student_repository.save(dto)
        await session.flush()

        result = await teacher_student_repository.get_by_teacher_and_student(
            sample_user.id,
            second_sample_user.id,
        )

        assert result is not None
        assert result.teacher_id == sample_user.id
        assert result.student_id == second_sample_user.id

    async def test_get_by_teacher_and_student_returns_none(
        self,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """get_by_teacher_and_student returns None when not exists."""
        result = await teacher_student_repository.get_by_teacher_and_student(
            sample_user.id,
            second_sample_user.id,
        )

        assert result is None

    async def test_get_students_for_teacher_returns_list(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """get_students_for_teacher returns list of students with user info."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=second_sample_user.id,
            invite_code="STUDENTS1234",
            status=TeacherStudentStatus.ACTIVE,
        )
        await teacher_student_repository.save(dto)
        await session.flush()

        result = await teacher_student_repository.get_students_for_teacher(
            sample_user.id,
            TeacherStudentStatus.ACTIVE,
        )

        assert len(result) == 1
        assert result[0].user_id == second_sample_user.id
        assert result[0].first_name == second_sample_user.first_name

    async def test_get_students_for_teacher_filters_by_status(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """get_students_for_teacher filters by status."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=second_sample_user.id,
            invite_code="ARCHIVED1234",
            status=TeacherStudentStatus.ARCHIVED,
        )
        await teacher_student_repository.save(dto)
        await session.flush()

        active_result = await teacher_student_repository.get_students_for_teacher(
            sample_user.id,
            TeacherStudentStatus.ACTIVE,
        )
        archived_result = await teacher_student_repository.get_students_for_teacher(
            sample_user.id,
            TeacherStudentStatus.ARCHIVED,
        )

        assert len(active_result) == 0
        assert len(archived_result) == 1

    async def test_get_teacher_for_student_returns_teacher(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """get_teacher_for_student returns teacher with user info."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=second_sample_user.id,
            invite_code="TEACHER12345",
            status=TeacherStudentStatus.ACTIVE,
        )
        await teacher_student_repository.save(dto)
        await session.flush()

        result = await teacher_student_repository.get_teacher_for_student(
            second_sample_user.id,
            TeacherStudentStatus.ACTIVE,
        )

        assert result is not None
        assert result.user_id == sample_user.id
        assert result.first_name == sample_user.first_name

    async def test_get_teacher_for_student_returns_none(
        self,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """get_teacher_for_student returns None when no teacher."""
        result = await teacher_student_repository.get_teacher_for_student(
            sample_user.id,
            TeacherStudentStatus.ACTIVE,
        )

        assert result is None

    async def test_count_students_returns_correct_count(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """count_students returns correct count."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=second_sample_user.id,
            invite_code="COUNT1234567",
            status=TeacherStudentStatus.ACTIVE,
        )
        await teacher_student_repository.save(dto)
        await session.flush()

        result = await teacher_student_repository.count_students(
            sample_user.id,
            TeacherStudentStatus.ACTIVE,
        )

        assert result == 1

    async def test_count_students_zero_when_empty(
        self,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """count_students returns zero when no students."""
        result = await teacher_student_repository.count_students(
            sample_user.id,
            TeacherStudentStatus.ACTIVE,
        )

        assert result == 0

    async def test_is_teacher_true(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """is_teacher returns True when user has teacher-student records."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=None,
            invite_code="ISTEACHER123",
            status=TeacherStudentStatus.PENDING,
        )
        await teacher_student_repository.save(dto)
        await session.flush()

        result = await teacher_student_repository.is_teacher(sample_user.id)

        assert result is True

    async def test_is_teacher_false(
        self,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """is_teacher returns False when user has no records."""
        result = await teacher_student_repository.is_teacher(sample_user.id)

        assert result is False

    async def test_is_student_true(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """is_student returns True when user has active teacher."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=second_sample_user.id,
            invite_code="ISSTUDENT123",
            status=TeacherStudentStatus.ACTIVE,
        )
        await teacher_student_repository.save(dto)
        await session.flush()

        result = await teacher_student_repository.is_student(second_sample_user.id)

        assert result is True

    async def test_is_student_false(
        self,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """is_student returns False when user has no active teacher."""
        result = await teacher_student_repository.is_student(sample_user.id)

        assert result is False

    async def test_get_pending_invite_for_teacher_returns_dto(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """get_pending_invite_for_teacher returns pending invite."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=None,
            invite_code="PENDING12345",
            status=TeacherStudentStatus.PENDING,
        )
        await teacher_student_repository.save(dto)
        await session.flush()

        result = await teacher_student_repository.get_pending_invite_for_teacher(sample_user.id)

        assert result is not None
        assert result.invite_code == "PENDING12345"

    async def test_get_pending_invite_for_teacher_returns_none(
        self,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """get_pending_invite_for_teacher returns None when no pending invite."""
        result = await teacher_student_repository.get_pending_invite_for_teacher(sample_user.id)

        assert result is None

    async def test_update_status_updates_record(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """update_status updates the status."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=None,
            invite_code="UPDATE123456",
            status=TeacherStudentStatus.PENDING,
        )
        saved = await teacher_student_repository.save(dto)
        await session.flush()

        await teacher_student_repository.update_status(
            saved.id,
            TeacherStudentStatus.ACTIVE,
            student_id=second_sample_user.id,
        )
        await session.flush()

        result = await teacher_student_repository.get_by_id(saved.id)

        assert result is not None
        assert result.status == TeacherStudentStatus.ACTIVE
        assert result.student_id == second_sample_user.id

    async def test_delete_removes_record(
        self,
        session: AsyncSession,
        teacher_student_repository: TeacherStudentRepository,
        sample_user: UserReadDTO,
    ) -> None:
        """delete removes the record."""
        dto = TeacherStudentCreateDTO(
            teacher_id=sample_user.id,
            student_id=None,
            invite_code="DELETE123456",
            status=TeacherStudentStatus.PENDING,
        )
        saved = await teacher_student_repository.save(dto)
        await session.flush()

        await teacher_student_repository.delete(saved.id)
        await session.flush()

        result = await teacher_student_repository.get_by_id(saved.id)

        assert result is None
