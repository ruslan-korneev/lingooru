"""Tests for teaching handlers."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from src.bot.handlers.teaching import (
    handle_deep_link_join,
    on_become_teacher,
    on_invite_code_input,
    on_join_teacher_prompt,
    on_leave_teacher,
    on_leave_teacher_confirm,
    on_noop,
    on_regenerate_invite,
    on_remove_student,
    on_remove_student_confirm,
    on_role_selection,
    on_show_invite,
    on_student_detail,
    on_student_list,
    on_student_list_page,
    on_student_panel,
    on_teacher_dashboard,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.modules.teaching.dto import InviteCodeDTO, TeacherDashboardStatsDTO, TeacherStudentWithUserDTO
from src.modules.teaching.enums import TeacherStudentStatus
from src.modules.users.dto import UserReadDTO


class TestOnRoleSelection:
    """Tests for on_role_selection handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_role_selection(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()

        await on_role_selection(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_not_called()

    async def test_shows_role_selection(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows role selection screen."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.is_teacher = AsyncMock(return_value=False)
                mock_service.is_student = AsyncMock(return_value=False)

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_role_selection(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.clear.assert_called_once()
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnBecomeTeacher:
    """Tests for on_become_teacher handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_become_teacher(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()

        await on_become_teacher(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_becomes_teacher_and_shows_invite(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler creates invite and shows it."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.become_teacher = AsyncMock(
                    return_value=InviteCodeDTO(
                        code="ABC123DEF456", deep_link="https://t.me/bot?start=join_ABC123DEF456"
                    ),
                )

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_become_teacher(mock_callback, mock_i18n, db_user)

        mock_session.commit.assert_called_once()
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnTeacherDashboard:
    """Tests for on_teacher_dashboard handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_teacher_dashboard(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()

        await on_teacher_dashboard(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_dashboard_with_stats(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows dashboard with stats."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_teacher_dashboard_stats = AsyncMock(
                    return_value=TeacherDashboardStatsDTO(students_count=5, active_assignments_count=2),
                )

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_teacher_dashboard(mock_callback, mock_i18n, db_user)

        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnStudentList:
    """Tests for on_student_list handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_student_list(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_empty_student_list(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows empty message when no students."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_students = AsyncMock(return_value=[])

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_student_list(mock_callback, mock_i18n, db_user)

        mock_i18n.get.assert_any_call("teaching-no-students")
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_shows_student_list_with_students(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows student list when students exist."""
        mock_callback.message = mock_message

        mock_student = TeacherStudentWithUserDTO(
            id=uuid4(),
            user_id=uuid4(),
            username="student1",
            first_name="Student",
            status=TeacherStudentStatus.ACTIVE,
        )

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_students = AsyncMock(return_value=[mock_student])

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_student_list(mock_callback, mock_i18n, db_user)

        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnStudentDetail:
    """Tests for on_student_detail handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None
        mock_callback.data = "teaching:student:abc"

        await on_student_detail(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_no_data(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler returns early when callback has no data."""
        mock_callback.message = mock_message
        mock_callback.data = None

        await on_student_detail(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()  # Not a Message instance
        mock_callback.data = "teaching:student:123"

        await on_student_detail(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_error_on_invalid_uuid(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows error on invalid UUID."""
        mock_callback.message = mock_message
        mock_callback.data = "teaching:student:invalid-uuid"

        await on_student_detail(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_called_once()
        call_kwargs = mock_callback.answer.call_args.kwargs
        assert call_kwargs.get("show_alert") is True

    async def test_shows_error_when_student_not_found(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows error when student not found."""
        student_id = uuid4()
        mock_callback.message = mock_message
        mock_callback.data = f"teaching:student:{student_id}"

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_students = AsyncMock(return_value=[])

                await on_student_detail(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_called_once()
        call_kwargs = mock_callback.answer.call_args.kwargs
        assert call_kwargs.get("show_alert") is True

    async def test_shows_student_detail_when_found(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows student detail when student is found."""
        student_id = uuid4()
        mock_callback.message = mock_message
        mock_callback.data = f"teaching:student:{student_id}"

        mock_student = TeacherStudentWithUserDTO(
            id=uuid4(),
            user_id=student_id,
            username="student1",
            first_name="Student One",
            status=TeacherStudentStatus.ACTIVE,
        )

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_students = AsyncMock(return_value=[mock_student])

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_student_detail(mock_callback, mock_i18n, db_user)

        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnStudentListPage:
    """Tests for on_student_list_page handler."""

    async def test_parses_page_from_callback_data(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler parses page number from callback data."""
        mock_callback.message = mock_message
        mock_callback.data = "teaching:students:2"

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_students = AsyncMock(return_value=[])

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_student_list_page(mock_callback, mock_i18n, db_user)

        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_defaults_to_page_zero_when_no_data(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler defaults to page 0 when callback.data is None."""
        mock_callback.message = mock_message
        mock_callback.data = None

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_students = AsyncMock(return_value=[])

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_student_list_page(mock_callback, mock_i18n, db_user)

        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnRemoveStudent:
    """Tests for on_remove_student handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None
        mock_callback.data = "teaching:remove:abc"

        await on_remove_student(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()  # Not a Message instance
        mock_callback.data = "teaching:remove:123"

        await on_remove_student(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_error_on_invalid_uuid(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows error on invalid UUID."""
        mock_callback.message = mock_message
        mock_callback.data = "teaching:remove:invalid-uuid"

        await on_remove_student(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_called_once()
        call_kwargs = mock_callback.answer.call_args.kwargs
        assert call_kwargs.get("show_alert") is True

    async def test_shows_confirmation(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows removal confirmation."""
        student_id = uuid4()
        mock_callback.message = mock_message
        mock_callback.data = f"teaching:remove:{student_id}"

        with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
            await on_remove_student(mock_callback, mock_i18n, db_user)

        mock_i18n.get.assert_any_call("teaching-remove-confirm")
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnRemoveStudentConfirm:
    """Tests for on_remove_student_confirm handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None
        mock_callback.data = "teaching:remove:confirm:abc"

        await on_remove_student_confirm(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_error_on_invalid_uuid(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows error on invalid UUID."""
        mock_callback.message = mock_message
        mock_callback.data = "teaching:remove:confirm:invalid-uuid"

        await on_remove_student_confirm(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_called_once()
        call_kwargs = mock_callback.answer.call_args.kwargs
        assert call_kwargs.get("show_alert") is True

    async def test_removes_student_successfully(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler removes student and redirects."""
        student_id = uuid4()
        mock_callback.message = mock_message
        mock_callback.data = f"teaching:remove:confirm:{student_id}"

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.remove_student = AsyncMock()
                mock_service.get_students = AsyncMock(return_value=[])

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock):
                    await on_remove_student_confirm(mock_callback, mock_i18n, db_user)

        mock_service.remove_student.assert_called_once()
        mock_session.commit.assert_called_once()

    async def test_shows_error_when_not_found(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows error when student not found."""
        student_id = uuid4()
        mock_callback.message = mock_message
        mock_callback.data = f"teaching:remove:confirm:{student_id}"

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.remove_student = AsyncMock(side_effect=NotFoundError())

                await on_remove_student_confirm(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_called_once()
        call_kwargs = mock_callback.answer.call_args.kwargs
        assert call_kwargs.get("show_alert") is True


class TestOnShowInvite:
    """Tests for on_show_invite handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_show_invite(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_show_invite(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_invite_code(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows invite code."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.become_teacher = AsyncMock(
                    return_value=InviteCodeDTO(code="XYZ789", deep_link="https://t.me/bot"),
                )

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_show_invite(mock_callback, mock_i18n, db_user)

        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnRegenerateInvite:
    """Tests for on_regenerate_invite handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_regenerate_invite(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_regenerate_invite(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_regenerates_and_shows_new_code(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler regenerates code and shows it."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.regenerate_invite_code = AsyncMock(
                    return_value=InviteCodeDTO(code="NEW123", deep_link="https://t.me/bot"),
                )

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_regenerate_invite(mock_callback, mock_i18n, db_user)

        mock_service.regenerate_invite_code.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnJoinTeacherPrompt:
    """Tests for on_join_teacher_prompt handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_join_teacher_prompt(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_join_teacher_prompt(mock_callback, mock_i18n, db_user, mock_state)

        mock_callback.answer.assert_not_called()

    async def test_sets_state_and_shows_prompt(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
        mock_message: MagicMock,
    ) -> None:
        """Handler sets FSM state and shows prompt."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
            await on_join_teacher_prompt(mock_callback, mock_i18n, db_user, mock_state)

        mock_state.set_state.assert_called_once()
        mock_i18n.get.assert_any_call("teaching-join-prompt")
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnInviteCodeInput:
    """Tests for on_invite_code_input handler."""

    async def test_returns_early_when_no_text(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler returns early when message has no text."""
        mock_message.text = None

        await on_invite_code_input(mock_message, mock_i18n, db_user, mock_state)

        mock_state.clear.assert_not_called()

    async def test_joins_teacher_successfully(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler joins teacher on valid code."""
        mock_message.text = "ABC123DEF456"

        mock_teacher = TeacherStudentWithUserDTO(
            id=uuid4(),
            user_id=uuid4(),
            username="teacher1",
            first_name="Teacher",
            status=TeacherStudentStatus.ACTIVE,
        )

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.join_teacher = AsyncMock()
                mock_service.get_teacher = AsyncMock(return_value=mock_teacher)

                await on_invite_code_input(mock_message, mock_i18n, db_user, mock_state)

        mock_state.clear.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_message.answer.assert_called_once()

    async def test_shows_error_on_invalid_code(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler shows error on invalid code."""
        mock_message.text = "INVALID"

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.join_teacher = AsyncMock(side_effect=NotFoundError())

                await on_invite_code_input(mock_message, mock_i18n, db_user, mock_state)

        mock_i18n.get.assert_any_call("teaching-join-invalid")
        mock_message.answer.assert_called_once()
        mock_state.clear.assert_not_called()

    async def test_shows_error_on_self_join(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler shows error when trying to join self."""
        mock_message.text = "SELFCODE"

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.join_teacher = AsyncMock(side_effect=ValidationError())

                await on_invite_code_input(mock_message, mock_i18n, db_user, mock_state)

        mock_i18n.get.assert_any_call("teaching-join-self")
        mock_state.clear.assert_not_called()

    async def test_shows_error_on_already_joined(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_state: MagicMock,
    ) -> None:
        """Handler shows error when already joined."""
        mock_message.text = "DUPLICATE"

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.join_teacher = AsyncMock(side_effect=ConflictError())

                await on_invite_code_input(mock_message, mock_i18n, db_user, mock_state)

        mock_i18n.get.assert_any_call("teaching-join-already")
        mock_state.clear.assert_not_called()


class TestOnStudentPanel:
    """Tests for on_student_panel handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_student_panel(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_student_panel(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_no_teacher_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows message when no teacher."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_teacher = AsyncMock(return_value=None)

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_student_panel(mock_callback, mock_i18n, db_user)

        mock_i18n.get.assert_any_call("teaching-no-teacher")
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()

    async def test_shows_teacher_info(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows teacher info when exists."""
        mock_callback.message = mock_message

        mock_teacher = TeacherStudentWithUserDTO(
            id=uuid4(),
            user_id=uuid4(),
            username="teacher1",
            first_name="Teacher",
            status=TeacherStudentStatus.ACTIVE,
        )

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_teacher = AsyncMock(return_value=mock_teacher)

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_student_panel(mock_callback, mock_i18n, db_user)

        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnLeaveTeacher:
    """Tests for on_leave_teacher handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_leave_teacher(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_leave_teacher(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_confirmation(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows leave confirmation."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
            await on_leave_teacher(mock_callback, mock_i18n, db_user)

        mock_i18n.get.assert_any_call("teaching-leave-confirm")
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnLeaveTeacherConfirm:
    """Tests for on_leave_teacher_confirm handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_leave_teacher_confirm(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_leaves_teacher_and_redirects(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler leaves teacher and redirects to role selection."""
        mock_callback.message = mock_message

        mock_teacher = TeacherStudentWithUserDTO(
            id=uuid4(),
            user_id=uuid4(),
            username="teacher1",
            first_name="Teacher",
            status=TeacherStudentStatus.ACTIVE,
        )

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_teacher = AsyncMock(return_value=mock_teacher)
                mock_service.leave_teacher = AsyncMock()
                mock_service.is_teacher = AsyncMock(return_value=False)
                mock_service.is_student = AsyncMock(return_value=False)

                with patch("src.bot.handlers.teaching.safe_edit_or_send", new_callable=AsyncMock) as mock_safe_edit:
                    await on_leave_teacher_confirm(mock_callback, mock_i18n, db_user)

        mock_service.leave_teacher.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_safe_edit.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnNoop:
    """Tests for on_noop handler."""

    async def test_answers_callback(
        self,
        mock_callback: MagicMock,
    ) -> None:
        """Handler answers callback."""
        await on_noop(mock_callback)

        mock_callback.answer.assert_called_once()


class TestHandleDeepLinkJoin:
    """Tests for handle_deep_link_join helper."""

    async def test_joins_successfully(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Helper joins teacher successfully."""
        mock_teacher = TeacherStudentWithUserDTO(
            id=uuid4(),
            user_id=uuid4(),
            username="teacher1",
            first_name="Teacher",
            status=TeacherStudentStatus.ACTIVE,
        )

        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.join_teacher = AsyncMock()
                mock_service.get_teacher = AsyncMock(return_value=mock_teacher)

                result = await handle_deep_link_join(mock_message, mock_i18n, db_user, "ABC123")

        assert result is True
        mock_session.commit.assert_called_once()
        mock_message.answer.assert_called_once()

    async def test_returns_false_on_not_found(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Helper returns False on invalid code."""
        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.join_teacher = AsyncMock(side_effect=NotFoundError())

                result = await handle_deep_link_join(mock_message, mock_i18n, db_user, "INVALID")

        assert result is False
        mock_i18n.get.assert_any_call("teaching-join-invalid")

    async def test_returns_false_on_self_join(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Helper returns False when trying to join self."""
        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.join_teacher = AsyncMock(side_effect=ValidationError())

                result = await handle_deep_link_join(mock_message, mock_i18n, db_user, "SELFCODE")

        assert result is False
        mock_i18n.get.assert_any_call("teaching-join-self")

    async def test_returns_false_on_conflict(
        self,
        mock_message: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Helper returns False when already joined."""
        with patch("src.bot.handlers.teaching.AsyncSessionMaker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.teaching.TeachingService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.join_teacher = AsyncMock(side_effect=ConflictError())

                result = await handle_deep_link_join(mock_message, mock_i18n, db_user, "DUPLICATE")

        assert result is False
        mock_i18n.get.assert_any_call("teaching-join-already")
