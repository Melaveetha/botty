from loguru import logger
from telegram import Bot
from telegram import Message as TGMessage

from ..domain import Message
from ..exceptions import BottyError
from ..ports import TelegramBotClient
from ..responses import (
    Answer,
    AudioAnswer,
    BaseAnswer,
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


class PTBBotAdapter(TelegramBotClient):
    """Concrete implementation of TelegramBotClient using python-telegram-bot's Bot.

    This adapter sends and edits messages via the PTB Bot instance, mapping
    botty's response objects to the appropriate PTB send_* methods.
    """

    def __init__(self, bot: Bot):
        """Initialize the adapter with a PTB Bot instance.

        Args:
            bot: The PTB Bot instance used for sending and editing messages.
        """
        self._bot = bot

    async def send(self, chat_id: int, answer: BaseAnswer) -> Message | None:
        """Send a message to a chat using the appropriate PTB method based on answer type.

        Args:
            chat_id: The Telegram chat ID to send the message to.
            answer: The botty response object (e.g., Answer, PhotoAnswer, etc.).

        Returns:
            A domain Message object if a message was sent, or None if the
            answer was EmptyAnswer or EditAnswer (which is handled separately) or answer type not known.
        """

        message: TGMessage
        match answer:
            case Answer():
                message = await self._bot.send_message(
                    chat_id=chat_id, **answer.to_dict()
                )
            case PhotoAnswer():
                message = await self._bot.send_photo(
                    chat_id=chat_id, **answer.to_dict()
                )
            case DocumentAnswer():
                message = await self._bot.send_document(
                    chat_id=chat_id, **answer.to_dict()
                )
            case AudioAnswer():
                message = await self._bot.send_audio(
                    chat_id=chat_id, **answer.to_dict()
                )
            case VideoAnswer():
                message = await self._bot.send_video(
                    chat_id=chat_id, **answer.to_dict()
                )
            case VoiceAnswer():
                message = await self._bot.send_voice(
                    chat_id=chat_id, **answer.to_dict()
                )
            case LocationAnswer():
                message = await self._bot.send_location(
                    chat_id=chat_id, **answer.to_dict()
                )
            case VenueAnswer():
                message = await self._bot.send_venue(
                    chat_id=chat_id, **answer.to_dict()
                )
            case ContactAnswer():
                message = await self._bot.send_contact(
                    chat_id=chat_id, **answer.to_dict()
                )
            case PollAnswer():
                message = await self._bot.send_poll(chat_id=chat_id, **answer.to_dict())
            case DiceAnswer():
                message = await self._bot.send_dice(chat_id=chat_id, **answer.to_dict())
            case EmptyAnswer():
                return None
            case EditAnswer():
                return None
            case _:
                logger.warning(
                    f"Received unknown message type: {type(answer)} in message {answer.message_key}"
                )
                return None

        return Message.from_telegram(message)

    async def edit(
        self, chat_id: int, message_id: int | None, answer: BaseAnswer
    ) -> Message | None:
        """Edit an existing message or send a new one if editing fails.

        This method currently only supports text editing. If
        message_id is None or editing fails, it falls back to sending a new
        message.

        Args:
            chat_id: The Telegram chat ID.
            message_id: The ID of the message to edit, if known.
            answer: The EditAnswer containing new text and options.

        Returns:
            A botty Message object for the edited or newly sent message,
            or None if the operation failed and no fallback was possible.

        Raises:
            BottyError: If answer is not an EditAnswer.
        """
        if not isinstance(answer, EditAnswer):
            raise BottyError(
                f"Edit received answer of type: {type(answer)}"
            )  # TODO: make custom exception
        if message_id is None:
            message = await self._bot.send_message(chat_id=chat_id, **answer.to_dict())
            return Message.from_telegram(message)
        try:
            result = await self._bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, **answer.to_dict()
            )

            if not result:
                logger.warning(f"Got {result} when editing message {message_id}")
        except Exception as e:
            logger.exception(f"Failed to edit message {message_id}: {e}")
            # Fall back to sending new message
            message = await self._bot.send_message(chat_id=chat_id, **answer.to_dict())
            logger.debug(f"Sent new message {message.message_id} after edit failed")
            return Message.from_telegram(message)
