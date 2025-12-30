"""Tests for teaching services."""

import pytest

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.modules.teaching.services import (
    TeachingService,
    create_deep_link,
    generate_invite_code,
)
from src.modules.users.dto import UserReadDTO

INVITE_CODE_LENGTH = 12
UNIQUENESS_TEST_COUNT = 100


class TestGenerateInviteCode:
    """Tests for generate_invite_code function."""

    def test_returns_12_characters(self) -> None:
        """Invite code is exactly 12 characters."""
        code = generate_invite_code()
        assert len(code) == INVITE_CODE_LENGTH

    def test_returns_uppercase_alphanumeric(self) -> None:
        """Invite code contains only uppercase alphanumeric characters."""
        code = generate_invite_code()
        assert code.isalnum()
        assert code.isupper()

    def test_generates_unique_codes(self) -> None:
        """Each generated code should be unique."""
        codes = {generate_invite_code() for _ in range(UNIQUENESS_TEST_COUNT)}
        assert len(codes) == UNIQUENESS_TEST_COUNT


class TestCreateDeepLink:
    """Tests for create_deep_link function."""

    def test_creates_correct_format(self) -> None:
        """Deep link has correct format."""
        link = create_deep_link("ABC123DEF456")
        assert "?start=join_ABC123DEF456" in link
        assert link.startswith("https://t.me/")


class TestTeachingService:
    """Tests for TeachingService."""

    async def test_become_teacher_creates_invite(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """become_teacher creates a new invite code."""
        result = await teaching_service.become_teacher(sample_user.id)

        assert result.code is not None
        assert len(result.code) == INVITE_CODE_LENGTH
        assert result.deep_link is not None
        assert result.code in result.deep_link

    async def test_become_teacher_returns_existing_invite(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """become_teacher returns existing pending invite if exists."""
        first_result = await teaching_service.become_teacher(sample_user.id)
        second_result = await teaching_service.become_teacher(sample_user.id)

        assert first_result.code == second_result.code

    async def test_regenerate_invite_code_creates_new(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """regenerate_invite_code creates a new invite code."""
        first_result = await teaching_service.become_teacher(sample_user.id)
        regenerated = await teaching_service.regenerate_invite_code(sample_user.id)

        assert regenerated.code != first_result.code
        assert len(regenerated.code) == INVITE_CODE_LENGTH

    async def test_validate_invite_code_returns_dto(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """validate_invite_code returns DTO for valid code."""
        invite = await teaching_service.become_teacher(sample_user.id)

        result = await teaching_service.validate_invite_code(invite.code)

        assert result is not None
        assert result.invite_code == invite.code

    async def test_validate_invite_code_returns_none_for_invalid(
        self,
        teaching_service: TeachingService,
    ) -> None:
        """validate_invite_code returns None for invalid code."""
        result = await teaching_service.validate_invite_code("INVALIDCODE1")

        assert result is None

    async def test_join_teacher_success(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """join_teacher links student to teacher."""
        invite = await teaching_service.become_teacher(sample_user.id)

        result = await teaching_service.join_teacher(
            second_sample_user.id,
            invite.code,
        )

        assert result.teacher_id == sample_user.id
        assert result.student_id == second_sample_user.id

    async def test_join_teacher_invalid_code_raises(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """join_teacher raises NotFoundError for invalid code."""
        with pytest.raises(NotFoundError):
            await teaching_service.join_teacher(sample_user.id, "INVALIDCODE1")

    async def test_join_teacher_self_raises_validation_error(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """join_teacher raises ValidationError when joining self."""
        invite = await teaching_service.become_teacher(sample_user.id)

        with pytest.raises(ValidationError):
            await teaching_service.join_teacher(sample_user.id, invite.code)

    async def test_join_teacher_duplicate_raises_conflict(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """join_teacher raises ConflictError for duplicate relationship."""
        invite = await teaching_service.become_teacher(sample_user.id)
        await teaching_service.join_teacher(second_sample_user.id, invite.code)

        # Create a new invite and try to join again
        new_invite = await teaching_service.regenerate_invite_code(sample_user.id)

        with pytest.raises(ConflictError):
            await teaching_service.join_teacher(second_sample_user.id, new_invite.code)

    async def test_get_students_returns_list(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """get_students returns list of students."""
        invite = await teaching_service.become_teacher(sample_user.id)
        await teaching_service.join_teacher(second_sample_user.id, invite.code)

        students = await teaching_service.get_students(sample_user.id)

        assert len(students) == 1
        assert students[0].user_id == second_sample_user.id

    async def test_get_students_empty_when_no_students(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """get_students returns empty list when no students."""
        await teaching_service.become_teacher(sample_user.id)

        students = await teaching_service.get_students(sample_user.id)

        assert len(students) == 0

    async def test_get_teacher_returns_teacher(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """get_teacher returns teacher for student."""
        invite = await teaching_service.become_teacher(sample_user.id)
        await teaching_service.join_teacher(second_sample_user.id, invite.code)

        teacher = await teaching_service.get_teacher(second_sample_user.id)

        assert teacher is not None
        assert teacher.user_id == sample_user.id

    async def test_get_teacher_returns_none_when_no_teacher(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """get_teacher returns None when student has no teacher."""
        teacher = await teaching_service.get_teacher(sample_user.id)

        assert teacher is None

    async def test_is_teacher_true(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """is_teacher returns True when user is a teacher."""
        await teaching_service.become_teacher(sample_user.id)

        result = await teaching_service.is_teacher(sample_user.id)

        assert result is True

    async def test_is_teacher_false(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """is_teacher returns False when user is not a teacher."""
        result = await teaching_service.is_teacher(sample_user.id)

        assert result is False

    async def test_is_student_true(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """is_student returns True when user has a teacher."""
        invite = await teaching_service.become_teacher(sample_user.id)
        await teaching_service.join_teacher(second_sample_user.id, invite.code)

        result = await teaching_service.is_student(second_sample_user.id)

        assert result is True

    async def test_is_student_false(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
    ) -> None:
        """is_student returns False when user has no teacher."""
        result = await teaching_service.is_student(sample_user.id)

        assert result is False

    async def test_remove_student_success(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """remove_student archives the relationship."""
        invite = await teaching_service.become_teacher(sample_user.id)
        await teaching_service.join_teacher(second_sample_user.id, invite.code)

        await teaching_service.remove_student(sample_user.id, second_sample_user.id)

        students = await teaching_service.get_students(sample_user.id)
        assert len(students) == 0

    async def test_remove_student_not_found_raises(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """remove_student raises NotFoundError for non-existent relationship."""
        with pytest.raises(NotFoundError):
            await teaching_service.remove_student(sample_user.id, second_sample_user.id)

    async def test_leave_teacher_success(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """leave_teacher archives the relationship."""
        invite = await teaching_service.become_teacher(sample_user.id)
        await teaching_service.join_teacher(second_sample_user.id, invite.code)

        await teaching_service.leave_teacher(second_sample_user.id, sample_user.id)

        teacher = await teaching_service.get_teacher(second_sample_user.id)
        assert teacher is None

    async def test_leave_teacher_not_found_raises(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """leave_teacher raises NotFoundError for non-existent relationship."""
        with pytest.raises(NotFoundError):
            await teaching_service.leave_teacher(second_sample_user.id, sample_user.id)

    async def test_get_teacher_dashboard_stats(
        self,
        teaching_service: TeachingService,
        sample_user: UserReadDTO,
        second_sample_user: UserReadDTO,
    ) -> None:
        """get_teacher_dashboard_stats returns correct stats."""
        invite = await teaching_service.become_teacher(sample_user.id)
        await teaching_service.join_teacher(second_sample_user.id, invite.code)

        stats = await teaching_service.get_teacher_dashboard_stats(sample_user.id)

        assert stats.students_count == 1
        assert stats.active_assignments_count == 0
