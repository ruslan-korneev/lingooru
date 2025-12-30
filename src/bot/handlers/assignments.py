"""Handlers for assignment functionality."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from aiogram_i18n import I18nContext
from loguru import logger

from src.bot.keyboards.assignments import (
    get_answer_cancel_keyboard,
    get_assignment_detail_keyboard,
    get_assignment_list_keyboard,
    get_assignment_method_keyboard,
    get_assignment_type_keyboard,
    get_difficulty_keyboard,
    get_grade_keyboard,
    get_submission_review_keyboard,
    get_topic_cancel_keyboard,
)
from src.bot.utils import (
    parse_callback_int,
    parse_callback_param,
    parse_callback_uuid,
    safe_edit_or_send,
)
from src.core.exceptions import NotFoundError, ValidationError
from src.db.session import AsyncSessionMaker
from src.modules.teaching.enums import AssignmentType
from src.modules.teaching.services import AssignmentService
from src.modules.users.dto import UserReadDTO

router = Router(name="assignments")

# Grade range constants
MIN_GRADE = 1
MAX_GRADE = 5


class AssignmentStates(StatesGroup):
    entering_topic = State()
    entering_answer = State()


# ---- Teacher: Assignment List ----


@router.callback_query(F.data == "assign:list")
async def on_assignment_list(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show teacher's assignments."""
    logger.debug(f"assign:list:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    async with AsyncSessionMaker() as session:
        service = AssignmentService(session)
        assignments = await service.get_teacher_assignments(db_user.id)

    text = i18n.get("assign-no-assignments") if not assignments else i18n.get("assign-list-title")

    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_assignment_list_keyboard(i18n, assignments, page=0, is_teacher=True),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign:page:"))
async def on_assignment_page(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Handle assignment list pagination."""
    if not callback.message or not isinstance(callback.message, Message):
        return

    page = parse_callback_int(callback.data, 2)

    async with AsyncSessionMaker() as session:
        service = AssignmentService(session)
        # Determine if teacher or student based on context
        teacher_assignments = await service.get_teacher_assignments(db_user.id)
        if teacher_assignments:
            assignments = teacher_assignments
            is_teacher = True
        else:
            assignments = await service.get_student_assignments(db_user.id)
            is_teacher = False

    text = i18n.get("assign-list-title")
    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_assignment_list_keyboard(i18n, assignments, page=page, is_teacher=is_teacher),
    )
    await callback.answer()


# ---- Teacher: Create Assignment ----


@router.callback_query(F.data.startswith("assign:new:"))
async def on_new_assignment(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Start creating assignment for student."""
    logger.debug(f"assign:new:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    student_id = parse_callback_uuid(callback.data, 2)
    if student_id is None:
        await callback.answer(i18n.get("error-invalid-data"))
        return

    text = i18n.get("assign-select-type")
    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_assignment_type_keyboard(i18n, student_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign:type:"))
async def on_select_type(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Handle assignment type selection."""
    logger.debug(f"assign:type:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    assignment_type = parse_callback_param(callback.data, 2)
    student_id = parse_callback_uuid(callback.data, 3)

    if student_id is None:
        await callback.answer(i18n.get("error-invalid-data"))
        return

    text = i18n.get("assign-select-method")
    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_assignment_method_keyboard(i18n, student_id, assignment_type),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign:ai:"))
async def on_ai_method(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Select AI generation - show difficulty selection."""
    logger.debug(f"assign:ai:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    assignment_type = parse_callback_param(callback.data, 2)
    student_id = parse_callback_uuid(callback.data, 3)

    if student_id is None:
        await callback.answer(i18n.get("error-invalid-data"))
        return

    text = i18n.get("assign-select-difficulty")
    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_difficulty_keyboard(i18n, student_id, assignment_type),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign:diff:"))
async def on_select_difficulty(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Handle difficulty selection - ask for topic."""
    logger.debug(f"assign:diff:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    difficulty = parse_callback_param(callback.data, 2)
    assignment_type = parse_callback_param(callback.data, 3)
    student_id = parse_callback_uuid(callback.data, 4)

    if student_id is None:
        await callback.answer(i18n.get("error-invalid-data"))
        return

    # Save state for topic input
    await state.set_state(AssignmentStates.entering_topic)
    await state.update_data(
        student_id=str(student_id),
        assignment_type=assignment_type,
        difficulty=difficulty,
    )

    text = i18n.get("assign-enter-topic")
    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_topic_cancel_keyboard(i18n, student_id, assignment_type),
    )
    await callback.answer()


@router.message(AssignmentStates.entering_topic)
async def on_topic_input(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Handle topic input and generate AI assignment."""
    logger.debug(f"assign:topic:user:{db_user.username}")

    data = await state.get_data()
    await state.clear()

    topic = message.text or ""
    if not topic:
        await message.answer(i18n.get("error-empty-topic"))
        return

    student_id_str = data.get("student_id")
    assignment_type_str = data.get("assignment_type", "text")
    difficulty = data.get("difficulty", "medium")

    if not student_id_str:
        await message.answer(i18n.get("error-invalid-data"))
        return

    from uuid import UUID

    student_id = UUID(student_id_str)

    # Map type string to enum
    type_map = {
        "text": AssignmentType.TEXT,
        "mc": AssignmentType.MULTIPLE_CHOICE,
        "voice": AssignmentType.VOICE,
    }
    assignment_type = type_map.get(assignment_type_str, AssignmentType.TEXT)

    # Show generating message
    generating_msg = await message.answer(i18n.get("assign-generating"))

    try:
        async with AsyncSessionMaker() as session:
            service = AssignmentService(session)
            assignment = await service.generate_ai_assignment(
                teacher_id=db_user.id,
                student_id=student_id,
                topic=topic,
                assignment_type=assignment_type,
                difficulty=difficulty,
            )
            await session.commit()

        text = i18n.get("assign-created", title=assignment.title)
        await generating_msg.edit_text(text)

    except (NotFoundError, ValidationError) as e:
        logger.error(f"Failed to generate assignment: {e}")
        await generating_msg.edit_text(i18n.get("error-generation-failed"))


# ---- Teacher/Student: View Assignment ----


@router.callback_query(F.data.startswith("assign:view:"))
async def on_view_assignment(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """View assignment details."""
    logger.debug(f"assign:view:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    assignment_id = parse_callback_uuid(callback.data, 2)
    if assignment_id is None:
        await callback.answer(i18n.get("error-invalid-data"))
        return

    async with AsyncSessionMaker() as session:
        service = AssignmentService(session)
        assignment = await service.get_assignment(assignment_id)

        if assignment is None:
            await callback.answer(i18n.get("error-not-found"))
            return

        submission = await service.get_submission(assignment_id)
        has_submission = submission is not None
        is_teacher = assignment.teacher_id == db_user.id

    # Build detail text
    type_label = i18n.get(f"type-{assignment.assignment_type.value}")
    status_label = i18n.get(f"status-{assignment.status.value}")
    text = (
        f"{i18n.get('assign-view-title', title=assignment.title)}\n\n"
        f"{i18n.get('assign-type')}: {type_label}\n"
        f"{i18n.get('assign-status')}: {status_label}\n"
    )
    if assignment.description:
        text += f"\n{assignment.description}"

    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_assignment_detail_keyboard(
            i18n, assignment, is_teacher=is_teacher, has_submission=has_submission
        ),
    )
    await callback.answer()


# ---- Student: Pending Assignments ----


@router.callback_query(F.data == "assign:pending")
async def on_pending_assignments(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show student's pending assignments."""
    logger.debug(f"assign:pending:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    async with AsyncSessionMaker() as session:
        service = AssignmentService(session)
        assignments = await service.get_student_pending_assignments(db_user.id)

    text = i18n.get("assign-no-pending") if not assignments else i18n.get("assign-pending-title")

    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_assignment_list_keyboard(i18n, assignments, page=0, is_teacher=False),
    )
    await callback.answer()


# ---- Student: Start Assignment ----


@router.callback_query(F.data.startswith("assign:start:"))
async def on_start_assignment(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Start working on assignment."""
    logger.debug(f"assign:start:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    assignment_id = parse_callback_uuid(callback.data, 2)
    if assignment_id is None:
        await callback.answer(i18n.get("error-invalid-data"))
        return

    async with AsyncSessionMaker() as session:
        service = AssignmentService(session)
        assignment = await service.get_assignment(assignment_id)

    if assignment is None:
        await callback.answer(i18n.get("error-not-found"))
        return

    # Save state for answer input
    await state.set_state(AssignmentStates.entering_answer)
    await state.update_data(assignment_id=str(assignment_id))

    # Show questions
    questions = assignment.content.get("questions", [])
    words = assignment.content.get("words", [])

    if assignment.assignment_type == AssignmentType.VOICE:
        items = words
        prefix = i18n.get("assign-pronounce")
    else:
        items = questions
        prefix = i18n.get("assign-answer")

    if not items:
        text = i18n.get("error-no-questions")
    else:
        text = f"{prefix}\n\n"
        for idx, item in enumerate(items, 1):
            item_text = item.get("text", "")
            text += f"{idx}. {item_text}\n"

    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_answer_cancel_keyboard(i18n),
    )
    await callback.answer()


@router.message(AssignmentStates.entering_answer)
async def on_answer_input(
    message: Message,
    i18n: I18nContext,
    db_user: UserReadDTO,
    state: FSMContext,
) -> None:
    """Handle answer input and submit assignment."""
    logger.debug(f"assign:answer:user:{db_user.username}")

    data = await state.get_data()
    await state.clear()

    answer_text = message.text or ""
    if not answer_text:
        await message.answer(i18n.get("error-empty-answer"))
        return

    assignment_id_str = data.get("assignment_id")
    if not assignment_id_str:
        await message.answer(i18n.get("error-invalid-data"))
        return

    from uuid import UUID

    assignment_id = UUID(assignment_id_str)

    # Parse answers (one per line)
    lines = [line.strip() for line in answer_text.split("\n") if line.strip()]
    answers = [{"question_id": f"q{idx + 1}", "answer": line} for idx, line in enumerate(lines)]
    content = {"answers": answers}

    try:
        async with AsyncSessionMaker() as session:
            service = AssignmentService(session)
            submission = await service.submit_assignment(
                assignment_id=assignment_id,
                student_id=db_user.id,
                content=content,
            )
            await session.commit()

        # Show result
        feedback = submission.ai_feedback or i18n.get("assign-submitted")
        score = submission.ai_score
        text = f"{i18n.get('assign-score')}: {score}/100\n\n{feedback}" if score is not None else feedback

        await message.answer(text)

    except NotFoundError:
        await message.answer(i18n.get("error-not-found"))
    except ValidationError:
        await message.answer(i18n.get("error-not-your-assignment"))


# ---- Teacher: View Submission ----


@router.callback_query(F.data.startswith("assign:submission:"))
async def on_view_submission(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """View student submission."""
    logger.debug(f"assign:submission:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    assignment_id = parse_callback_uuid(callback.data, 2)
    if assignment_id is None:
        await callback.answer(i18n.get("error-invalid-data"))
        return

    async with AsyncSessionMaker() as session:
        service = AssignmentService(session)
        submission = await service.get_submission(assignment_id)

    if submission is None:
        await callback.answer(i18n.get("error-no-submission"))
        return

    # Build submission detail
    text = f"{i18n.get('assign-submission-title')}\n\n"
    answers = submission.content.get("answers", [])
    for answer in answers:
        text += f"- {answer.get('answer', '')}\n"

    if submission.ai_feedback:
        text += f"\n{i18n.get('assign-ai-feedback')}:\n{submission.ai_feedback}"
        if submission.ai_score is not None:
            text += f"\n{i18n.get('assign-ai-score')}: {submission.ai_score}/100"

    if submission.grade is not None:
        text += f"\n\n{i18n.get('assign-grade')}: {submission.grade}/5"
        if submission.teacher_feedback:
            text += f"\n{submission.teacher_feedback}"

    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_submission_review_keyboard(i18n, submission.id),
    )
    await callback.answer()


# ---- Teacher: Grade ----


@router.callback_query(F.data.startswith("assign:grade:"))
async def on_grade_assignment(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Show grading keyboard."""
    logger.debug(f"assign:grade:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    submission_id = parse_callback_uuid(callback.data, 2)
    if submission_id is None:
        await callback.answer(i18n.get("error-invalid-data"))
        return

    text = i18n.get("assign-select-grade")
    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_grade_keyboard(i18n, submission_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("assign:rate:"))
async def on_rate_assignment(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """Handle grade selection."""
    logger.debug(f"assign:rate:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    grade = parse_callback_int(callback.data, 2)
    submission_id = parse_callback_uuid(callback.data, 3)

    if submission_id is None or grade < MIN_GRADE or grade > MAX_GRADE:
        await callback.answer(i18n.get("error-invalid-data"))
        return

    try:
        async with AsyncSessionMaker() as session:
            service = AssignmentService(session)
            await service.grade_assignment(
                submission_id=submission_id,
                teacher_id=db_user.id,
                grade=grade,
            )
            await session.commit()

        text = i18n.get("assign-graded", grade=grade)
        await safe_edit_or_send(callback.message, text=text)
        await callback.answer(i18n.get("success"))

    except NotFoundError:
        await callback.answer(i18n.get("error-not-found"))
    except ValidationError:
        await callback.answer(i18n.get("error-not-your-assignment"))


# ---- Student: View Result ----


@router.callback_query(F.data.startswith("assign:result:"))
async def on_view_result(
    callback: CallbackQuery,
    i18n: I18nContext,
    db_user: UserReadDTO,
) -> None:
    """View assignment result."""
    logger.debug(f"assign:result:user:{db_user.username}")
    if not callback.message or not isinstance(callback.message, Message):
        return

    assignment_id = parse_callback_uuid(callback.data, 2)
    if assignment_id is None:
        await callback.answer(i18n.get("error-invalid-data"))
        return

    async with AsyncSessionMaker() as session:
        service = AssignmentService(session)
        submission = await service.get_submission(assignment_id)

    if submission is None:
        await callback.answer(i18n.get("error-no-submission"))
        return

    # Build result text
    text = f"{i18n.get('assign-result-title')}\n\n"

    if submission.ai_score is not None:
        text += f"{i18n.get('assign-ai-score')}: {submission.ai_score}/100\n"
    if submission.ai_feedback:
        text += f"{submission.ai_feedback}\n"

    if submission.grade is not None:
        text += f"\n{i18n.get('assign-grade')}: {submission.grade}/5"
        if submission.teacher_feedback:
            text += f"\n{submission.teacher_feedback}"

    from src.bot.keyboards.teaching import get_student_panel_keyboard

    await safe_edit_or_send(
        callback.message,
        text=text,
        reply_markup=get_student_panel_keyboard(i18n, has_teacher=True),
    )
    await callback.answer()
