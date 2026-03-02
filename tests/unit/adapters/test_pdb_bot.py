from botty import BaseAnswer
from botty.exceptions import BottyError
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, UTC

from telegram import Bot, Message as TGMessage, User, Chat
from telegram.error import TelegramError

from botty.adapters.ptb_bot import PTBBotAdapter
from botty.domain import Message
from botty.responses import (
    Answer,
    AudioAnswer,
    ContactAnswer,
    DiceAnswer,
    DocumentAnswer,
    EditAnswer,
    EmptyAnswer,
    LocationAnswer,
    PhotoAnswer,
    PollAnswer,
    VenueAnswer,
    VideoAnswer,
    VoiceAnswer,
)


@pytest.fixture
def mock_ptb_bot():
    """Return a mocked PTB Bot with async methods."""
    bot = AsyncMock(spec=Bot)
    # Mock the send_* methods to return a fake TGMessage
    fake_message = TGMessage(
        message_id=42,
        date=datetime.now(UTC),
        chat=Chat(id=123, type="private"),
        from_user=User(id=1, first_name="Bot", is_bot=True),
    )
    for method in [
        "send_message",
        "send_photo",
        "send_document",
        "send_audio",
        "send_video",
        "send_voice",
        "send_location",
        "send_venue",
        "send_contact",
        "send_poll",
        "send_dice",
        "edit_message_text",
    ]:
        getattr(bot, method).return_value = fake_message
    return bot


@pytest.fixture
def adapter(mock_ptb_bot):
    """Return a PTBBotAdapter with the mocked bot."""
    return PTBBotAdapter(mock_ptb_bot)


@pytest.mark.asyncio
class TestSend:
    """Test PTBBotAdapter.send with various answer types."""

    @pytest.mark.parametrize(
        "answer_class,ptb_method,extra_kwargs",
        [
            (Answer, "send_message", {"text": "test"}),
            (PhotoAnswer, "send_photo", {"photo": b"fake"}),
            (DocumentAnswer, "send_document", {"document": b"fake"}),
            (AudioAnswer, "send_audio", {"audio": b"fake"}),
            (VideoAnswer, "send_video", {"video": b"fake"}),
            (VoiceAnswer, "send_voice", {"voice": b"fake"}),
            (LocationAnswer, "send_location", {"latitude": 1.0, "longitude": 2.0}),
            (
                VenueAnswer,
                "send_venue",
                {
                    "latitude": 1.0,
                    "longitude": 2.0,
                    "title": "Venue",
                    "address": "Addr",
                },
            ),
            (
                ContactAnswer,
                "send_contact",
                {"phone_number": "+123", "first_name": "John"},
            ),
            (PollAnswer, "send_poll", {"question": "Q", "options": ["A", "B"]}),
            (DiceAnswer, "send_dice", {"emoji": "🎲"}),
        ],
    )
    async def test_send_correct_method(
        self, adapter, mock_ptb_bot, answer_class, ptb_method, extra_kwargs
    ):
        """Verify the correct PTB send_* method is called with expected arguments."""
        kwargs = {}
        kwargs.update(extra_kwargs)
        answer = answer_class(**kwargs)

        chat_id = 123
        result = await adapter.send(chat_id, answer)

        ptb_call = getattr(mock_ptb_bot, ptb_method)
        ptb_call.assert_awaited_once_with(chat_id=chat_id, **answer.to_dict())

        assert isinstance(result, Message)
        assert result.message_id == 42
        assert result.chat_id == 123

    async def test_empty_answer_returns_none(self, adapter, mock_ptb_bot):
        """EmptyAnswer should not call any PTB method and return None."""
        answer = EmptyAnswer()
        result = await adapter.send(123, answer)
        assert result is None
        mock_ptb_bot.send_message.assert_not_awaited()

    async def test_edit_answer_in_send_returns_none(self, adapter, mock_ptb_bot):
        """EditAnswer passed to send() should be ignored (return None)."""
        answer = EditAnswer(text="edit")
        result = await adapter.send(123, answer)
        assert result is None
        mock_ptb_bot.send_message.assert_not_awaited()

    async def test_unknown_answer_type_logs_warning(
        self, adapter, mock_ptb_bot, caplog
    ):
        """An unknown answer type should log a warning and return None."""

        class UnknownAnswer(BaseAnswer):
            pass

        answer = UnknownAnswer()
        with caplog.at_level("WARNING"):
            result = await adapter.send(123, answer)

        assert result is None
        mock_ptb_bot.send_message.assert_not_awaited()
        assert "Received unknown message type" in caplog.text


@pytest.mark.asyncio
class TestEdit:
    """Test PTBBotAdapter.edit method."""

    async def test_edit_success_with_message_id(self, adapter, mock_ptb_bot):
        """Edit with a known message_id should call edit_message_text."""
        answer = EditAnswer(text="Updated")
        chat_id = 123
        message_id = 42

        result = await adapter.edit(chat_id, message_id, answer)

        mock_ptb_bot.edit_message_text.assert_awaited_once_with(
            chat_id=chat_id, message_id=message_id, **answer.to_dict()
        )
        assert isinstance(result, Message)
        assert result.message_id == 42

    async def test_edit_without_message_id_falls_back_to_send(
        self, adapter, mock_ptb_bot
    ):
        """When message_id is None, edit should send a new message."""
        answer = EditAnswer(text="Updated")
        chat_id = 123

        result = await adapter.edit(chat_id, None, answer)

        mock_ptb_bot.send_message.assert_awaited_once_with(
            chat_id=chat_id, **answer.to_dict()
        )
        mock_ptb_bot.edit_message_text.assert_not_awaited()
        assert isinstance(result, Message)

    async def test_edit_failure_falls_back_to_send(self, adapter, mock_ptb_bot):
        """If edit_message_text raises an exception, fall back to send_message."""
        answer = EditAnswer(text="Updated")
        chat_id = 123
        message_id = 42

        mock_ptb_bot.edit_message_text.side_effect = TelegramError("Edit failed")

        with patch("botty.adapters.ptb_bot.logger") as mock_logger:
            result = await adapter.edit(chat_id, message_id, answer)

        mock_ptb_bot.edit_message_text.assert_awaited_once()
        mock_ptb_bot.send_message.assert_awaited_once_with(
            chat_id=chat_id, **answer.to_dict()
        )
        mock_logger.exception.assert_called_once()
        assert isinstance(result, Message)

    async def test_edit_with_non_edit_answer_raises_error(self, adapter, mock_ptb_bot):
        """Passing a non-EditAnswer to edit() should raise BottyError."""
        answer = Answer(text="wrong")
        with pytest.raises(BottyError) as exc:
            await adapter.edit(123, 42, answer)
        assert "Edit received answer of type" in str(exc.value)


@pytest.mark.asyncio
async def test_message_from_telegram_called(adapter, mock_ptb_bot):
    """Verify that Message.from_telegram is used to create the result."""
    with patch("botty.adapters.ptb_bot.Message.from_telegram") as mock_from_telegram:
        fake_domain_message = MagicMock(spec=Message)
        mock_from_telegram.return_value = fake_domain_message

        answer = Answer(text="test")
        chat_id = 123
        result = await adapter.send(chat_id, answer)

        mock_from_telegram.assert_called_once_with(
            mock_ptb_bot.send_message.return_value
        )
        assert result is fake_domain_message
