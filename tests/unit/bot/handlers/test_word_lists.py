"""Tests for word_lists handler."""

from unittest.mock import AsyncMock, MagicMock, patch

from src.bot.handlers.word_lists import (
    on_list_add,
    on_list_preview,
    on_lists_show,
    on_noop,
)
from src.modules.users.dto import UserReadDTO


class TestOnListsShow:
    """Tests for on_lists_show handler."""

    async def test_returns_early_when_no_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no message."""
        mock_callback.message = None

        await on_lists_show(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_lists_show(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_empty_message_when_no_lists(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows empty message when no word lists available."""
        mock_callback.message = mock_message

        with patch("src.bot.handlers.word_lists.get_word_lists_by_language", return_value=[]):
            await on_lists_show(mock_callback, mock_i18n, db_user)

        mock_i18n.get.assert_any_call("lists-empty")
        mock_callback.answer.assert_called_once()

    async def test_shows_word_lists(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows word lists."""
        mock_callback.message = mock_message

        mock_word_list = MagicMock()
        mock_word_list.id = "test_list"
        mock_word_list.get_name = MagicMock(return_value="Test List")

        with (
            patch("src.bot.handlers.word_lists.get_word_lists_by_language", return_value=[mock_word_list]),
            patch("src.bot.handlers.word_lists.AsyncSessionMaker") as mock_session_maker,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.word_lists.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.get_user_added_word_lists = AsyncMock(return_value=set())

                await on_lists_show(mock_callback, mock_i18n, db_user)

        mock_message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnListPreview:
    """Tests for on_list_preview handler."""

    async def test_returns_early_when_no_data_or_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no data or message."""
        mock_callback.data = None
        mock_callback.message = MagicMock()

        await on_list_preview(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.data = "lists:preview:test"
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_list_preview(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_alert_when_list_not_found(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows alert when word list not found."""
        mock_callback.data = "lists:preview:nonexistent"
        mock_callback.message = mock_message

        with patch("src.bot.handlers.word_lists.get_word_list_by_id", return_value=None):
            await on_list_preview(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_called_once()
        mock_i18n.get.assert_any_call("list-not-found")

    async def test_shows_list_preview(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows word list preview."""
        mock_callback.data = "lists:preview:food"
        mock_callback.message = mock_message

        mock_word = MagicMock()
        mock_word.text = "apple"
        mock_word.translation = "яблоко"

        mock_word_list = MagicMock()
        mock_word_list.id = "food"
        mock_word_list.get_name = MagicMock(return_value="Food")
        mock_word_list.words = [mock_word]

        with (
            patch("src.bot.handlers.word_lists.get_word_list_by_id", return_value=mock_word_list),
            patch("src.bot.handlers.word_lists.AsyncSessionMaker") as mock_session_maker,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.word_lists.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.is_word_list_added = AsyncMock(return_value=False)

                await on_list_preview(mock_callback, mock_i18n, db_user)

        mock_message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnListAdd:
    """Tests for on_list_add handler."""

    async def test_returns_early_when_no_data_or_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when callback has no data or message."""
        mock_callback.data = None
        mock_callback.message = MagicMock()

        await on_list_add(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_returns_early_when_message_not_message_type(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
    ) -> None:
        """Handler returns early when message is not Message type."""
        mock_callback.data = "lists:add:test"
        mock_callback.message = MagicMock()  # Not a Message instance

        await on_list_add(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_not_called()

    async def test_shows_alert_when_list_not_found(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows alert when word list not found."""
        mock_callback.data = "lists:add:nonexistent"
        mock_callback.message = mock_message

        with patch("src.bot.handlers.word_lists.get_word_list_by_id", return_value=None):
            await on_list_add(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_called_once()
        mock_i18n.get.assert_any_call("list-not-found")

    async def test_shows_alert_when_list_already_added(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler shows alert when list is already added."""
        mock_callback.data = "lists:add:food"
        mock_callback.message = mock_message

        mock_word_list = MagicMock()
        mock_word_list.id = "food"
        mock_word_list.source_language = MagicMock()

        with (
            patch("src.bot.handlers.word_lists.get_word_list_by_id", return_value=mock_word_list),
            patch("src.bot.handlers.word_lists.AsyncSessionMaker") as mock_session_maker,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.word_lists.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.is_word_list_added = AsyncMock(return_value=True)

                await on_list_add(mock_callback, mock_i18n, db_user)

        mock_callback.answer.assert_called_once()
        mock_i18n.get.assert_any_call("list-already-added")

    async def test_adds_words_from_list(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
        db_user: UserReadDTO,
        mock_message: MagicMock,
    ) -> None:
        """Handler adds words from list to vocabulary."""
        mock_callback.data = "lists:add:food"
        mock_callback.message = mock_message

        mock_word = MagicMock()
        mock_word.text = "apple"
        mock_word.translation = "яблоко"
        mock_word.example = None

        mock_word_list = MagicMock()
        mock_word_list.id = "food"
        mock_word_list.source_language = MagicMock()
        mock_word_list.words = [mock_word]
        mock_word_list.get_name = MagicMock(return_value="Food")

        with (
            patch("src.bot.handlers.word_lists.get_word_list_by_id", return_value=mock_word_list),
            patch("src.bot.handlers.word_lists.AsyncSessionMaker") as mock_session_maker,
        ):
            mock_session = AsyncMock()
            mock_session_maker.return_value.__aenter__.return_value = mock_session

            with patch("src.bot.handlers.word_lists.VocabularyService") as mock_service_class:
                mock_service = mock_service_class.return_value
                mock_service.is_word_list_added = AsyncMock(return_value=False)
                mock_service.add_word_with_translation = AsyncMock()
                mock_service.mark_word_list_added = AsyncMock()

                await on_list_add(mock_callback, mock_i18n, db_user)

        mock_service.add_word_with_translation.assert_called_once()
        mock_service.mark_word_list_added.assert_called_once()
        mock_message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once()


class TestOnNoop:
    """Tests for on_noop handler."""

    async def test_answers_callback_with_message(
        self,
        mock_callback: MagicMock,
        mock_i18n: MagicMock,
    ) -> None:
        """Handler answers callback with list already added message."""
        await on_noop(mock_callback, mock_i18n)

        mock_callback.answer.assert_called_once()
        mock_i18n.get.assert_any_call("list-already-added")
