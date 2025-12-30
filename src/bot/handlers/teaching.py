from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from loguru import logger

from src.bot.keyboards.teaching import (
    get_confirm_leave_keyboard,
    get_confirm_remove_keyboard,
    get_invite_keyboard,
    get_join_cancel_keyboard,
    get_role_selection_keyboard,
    get_student_detail_keyboard,
    get_student_list_keyboard,
    get_student_panel_keyboard,
    get_teacher_dashboard_keyboard,
)
from src.bot.utils import parse_callback_int, parse_callback_uuid, safe_edit_or_send
from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.db.session import AsyncSessionMaker
from src.modules.teaching.services import TeachingService
from src.modules.users.dto import UserReadDTO

router = Router(name="teaching")


class TeachingStates(StatesGroup):
    entering_invite_code = State()


@router.callback_query(F.data == "teaching:role")
async def on_role_selection(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Show role selection screen."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    await state.clear()

    async with AsyncSessionMaker() as session:
        service = TeachingService(session)
        is_teacher = await service.is_teacher(db_user.id)
        has_teacher = await service.is_student(db_user.id)

    text = f"{i18n.get('teaching-role-title')}\n\n" f"{i18n.get('teaching-role-desc')}"

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_role_selection_keyboard(i18n, is_teacher=is_teacher, has_teacher=has_teacher),
    )
    await callback.answer()


@router.callback_query(F.data == "teaching:become")
async def on_become_teacher(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Become a teacher and get invite code."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    async with AsyncSessionMaker() as session:
        service = TeachingService(session)
        invite = await service.become_teacher(db_user.id)
        await session.commit()

    text = (
        f"{i18n.get('teaching-invite-title')}\n\n"
        f"{i18n.get('teaching-invite-code', code=invite.code)}\n\n"
        f"{i18n.get('teaching-invite-link', link=invite.deep_link)}"
    )

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_invite_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "teaching:dashboard")
async def on_teacher_dashboard(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show teacher dashboard."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    async with AsyncSessionMaker() as session:
        service = TeachingService(session)
        stats = await service.get_teacher_dashboard_stats(db_user.id)

    stats_text = i18n.get(
        "teaching-dashboard-stats",
        students=stats.students_count,
        assignments=stats.active_assignments_count,
    )
    text = f"{i18n.get('teaching-dashboard-title')}\n\n{stats_text}"

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_teacher_dashboard_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "teaching:students")
async def on_student_list(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show student list."""
    await _show_student_list(callback, i18n, db_user, page=0)


@router.callback_query(F.data.startswith("teaching:students:"))
async def on_student_list_page(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show student list page."""
    page = parse_callback_int(callback.data, 2, 0) if callback.data else 0
    await _show_student_list(callback, i18n, db_user, page)


async def _show_student_list(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    page: int,
) -> None:
    """Show student list with pagination."""
    logger.debug(f"{__name__}:user:{db_user.username}:page:{page}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    async with AsyncSessionMaker() as session:
        service = TeachingService(session)
        students = await service.get_students(db_user.id)

    if not students:
        text = f"{i18n.get('teaching-students-title')}\n\n" f"{i18n.get('teaching-no-students')}"
    else:
        text = i18n.get("teaching-students-title")

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_student_list_keyboard(i18n, students, page),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("teaching:student:") & ~F.data.contains(":remove"))
async def on_student_detail(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show student detail."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message or not callback.data:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    student_id = parse_callback_uuid(callback.data, 2)
    if student_id is None:
        await callback.answer(text=i18n.get("error-invalid-data"), show_alert=True)
        return

    # For now, show simple student info
    # In Phase 6.2, we'll add assignment stats
    async with AsyncSessionMaker() as session:
        service = TeachingService(session)
        students = await service.get_students(db_user.id)

    student = next((s for s in students if s.user_id == student_id), None)
    if student is None:
        await callback.answer(text=i18n.get("error-not-found"), show_alert=True)
        return

    name = student.first_name or student.username or i18n.get("unknown-user")
    text = f"{i18n.get('teaching-student-item', name=name, words=student.words_learned, streak=student.current_streak)}"

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_student_detail_keyboard(i18n, student_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("teaching:remove:") & ~F.data.contains(":confirm"))
async def on_remove_student(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Confirm student removal."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message or not callback.data:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    student_id = parse_callback_uuid(callback.data, 2)
    if student_id is None:
        await callback.answer(text=i18n.get("error-invalid-data"), show_alert=True)
        return

    text = i18n.get("teaching-remove-confirm")
    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_confirm_remove_keyboard(i18n, student_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("teaching:remove:confirm:"))
async def on_remove_student_confirm(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Remove student from teacher's list."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message or not callback.data:
        return

    student_id = parse_callback_uuid(callback.data, 3)
    if student_id is None:
        await callback.answer(text=i18n.get("error-invalid-data"), show_alert=True)
        return

    try:
        async with AsyncSessionMaker() as session:
            service = TeachingService(session)
            await service.remove_student(db_user.id, student_id)
            await session.commit()
    except NotFoundError:
        await callback.answer(text=i18n.get("error-not-found"), show_alert=True)
        return

    await callback.answer(text=i18n.get("teaching-removed"), show_alert=True)
    await _show_student_list(callback, i18n, db_user, page=0)


@router.callback_query(F.data == "teaching:invite")
async def on_show_invite(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show invite code."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    async with AsyncSessionMaker() as session:
        service = TeachingService(session)
        invite = await service.become_teacher(db_user.id)
        await session.commit()

    text = (
        f"{i18n.get('teaching-invite-title')}\n\n"
        f"{i18n.get('teaching-invite-code', code=invite.code)}\n\n"
        f"{i18n.get('teaching-invite-link', link=invite.deep_link)}"
    )

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_invite_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "teaching:regenerate")
async def on_regenerate_invite(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Regenerate invite code."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    async with AsyncSessionMaker() as session:
        service = TeachingService(session)
        invite = await service.regenerate_invite_code(db_user.id)
        await session.commit()

    text = (
        f"{i18n.get('teaching-invite-title')}\n\n"
        f"{i18n.get('teaching-invite-code', code=invite.code)}\n\n"
        f"{i18n.get('teaching-invite-link', link=invite.deep_link)}"
    )

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_invite_keyboard(i18n),
    )
    await callback.answer(text=i18n.get("teaching-regenerated"), show_alert=True)


@router.callback_query(F.data == "teaching:join")
async def on_join_teacher_prompt(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Prompt to enter invite code."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    await state.set_state(TeachingStates.entering_invite_code)

    await safe_edit_or_send(
        message,
        text=i18n.get("teaching-join-prompt"),
        reply_markup=get_join_cancel_keyboard(i18n),
    )
    await callback.answer()


@router.message(TeachingStates.entering_invite_code)
async def on_invite_code_input(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Handle invite code input."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not message.text:
        return

    code = message.text.strip().upper().replace("-", "").replace(" ", "")

    try:
        async with AsyncSessionMaker() as session:
            service = TeachingService(session)
            await service.join_teacher(db_user.id, code)
            teacher = await service.get_teacher(db_user.id)
            await session.commit()
    except NotFoundError:
        await message.answer(text=i18n.get("teaching-join-invalid"))
        return
    except ValidationError:
        await message.answer(text=i18n.get("teaching-join-self"))
        return
    except ConflictError:
        await message.answer(text=i18n.get("teaching-join-already"))
        return

    await state.clear()

    teacher_name = (
        (teacher.first_name or teacher.username or i18n.get("unknown-user")) if teacher else i18n.get("unknown-user")
    )

    await message.answer(
        text=i18n.get("teaching-join-success", name=teacher_name),
        reply_markup=get_student_panel_keyboard(i18n, has_teacher=True),
    )


@router.callback_query(F.data == "teaching:panel")
async def on_student_panel(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show student panel (my teacher view)."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    async with AsyncSessionMaker() as session:
        service = TeachingService(session)
        teacher = await service.get_teacher(db_user.id)

    if teacher is None:
        text = f"{i18n.get('teaching-panel-title')}\n\n" f"{i18n.get('teaching-no-teacher')}"
        has_teacher = False
    else:
        teacher_name = teacher.first_name or teacher.username or i18n.get("unknown-user")
        text = f"{i18n.get('teaching-panel-title')}\n\n" f"{i18n.get('teaching-panel-teacher', name=teacher_name)}"
        has_teacher = True

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_student_panel_keyboard(i18n, has_teacher=has_teacher),
    )
    await callback.answer()


@router.callback_query(F.data == "teaching:leave")
async def on_leave_teacher(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Confirm leaving teacher."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    text = i18n.get("teaching-leave-confirm")
    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_confirm_leave_keyboard(i18n),
    )
    await callback.answer()


@router.callback_query(F.data == "teaching:leave:confirm")
async def on_leave_teacher_confirm(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Leave teacher."""
    logger.debug(f"{__name__}:user:{db_user.username}")
    if not callback.message:
        return

    message = callback.message
    if not isinstance(message, Message):
        return

    async with AsyncSessionMaker() as session:
        service = TeachingService(session)
        teacher = await service.get_teacher(db_user.id)
        if teacher:
            await service.leave_teacher(db_user.id, teacher.user_id)
            await session.commit()

    await callback.answer(text=i18n.get("teaching-left"), show_alert=True)

    # Redirect to role selection
    text = f"{i18n.get('teaching-role-title')}\n\n" f"{i18n.get('teaching-role-desc')}"

    async with AsyncSessionMaker() as session:
        service = TeachingService(session)
        is_teacher = await service.is_teacher(db_user.id)
        has_teacher = await service.is_student(db_user.id)

    await safe_edit_or_send(
        message,
        text=text,
        reply_markup=get_role_selection_keyboard(i18n, is_teacher=is_teacher, has_teacher=has_teacher),
    )


@router.callback_query(F.data == "noop")
async def on_noop(callback: CallbackQuery) -> None:
    """No-op callback for pagination indicators."""
    await callback.answer()


async def handle_deep_link_join(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,
    invite_code: str,
) -> bool:
    """Handle deep link join from /start command.

    Returns True if handled successfully, False otherwise.
    """
    try:
        async with AsyncSessionMaker() as session:
            service = TeachingService(session)
            await service.join_teacher(db_user.id, invite_code)
            teacher = await service.get_teacher(db_user.id)
            await session.commit()
    except NotFoundError:
        await message.answer(text=i18n.get("teaching-join-invalid"))
        return False
    except ValidationError:
        await message.answer(text=i18n.get("teaching-join-self"))
        return False
    except ConflictError:
        await message.answer(text=i18n.get("teaching-join-already"))
        return False

    teacher_name = (
        (teacher.first_name or teacher.username or i18n.get("unknown-user")) if teacher else i18n.get("unknown-user")
    )

    await message.answer(
        text=i18n.get("teaching-join-success", name=teacher_name),
        reply_markup=get_student_panel_keyboard(i18n, has_teacher=True),
    )
    return True
