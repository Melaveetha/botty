from loguru import logger
from telegram import Bot, Message as TGMessage

from ..classes import Message
from ..exceptions import BottyError
from ..handlers import (
    Answer,
    EditAnswer,
    AudioAnswer,
    BaseAnswer,
    ContactAnswer,
    DiceAnswer,
    DocumentAnswer,
    EmptyAnswer,
    LocationAnswer,
    PhotoAnswer,
    PollAnswer,
    VenueAnswer,
    VoiceAnswer,
    VideoAnswer,
)
from ..ports import TelegramBotClient


class PTBBotAdapter(TelegramBotClient):
    def __init__(self, bot: Bot):
        self._bot = bot

    async def send(self, chat_id: int, answer: BaseAnswer) -> Message | None:
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
