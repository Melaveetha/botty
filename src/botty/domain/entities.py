from dataclasses import dataclass
from datetime import datetime

from telegram import Message as TGMessage
from telegram import PollOption

from ..exceptions import ChatIdNotFoundError


class Message:
    message_id: int
    chat_id: int
    date: datetime

    def __init__(self, message_id: int, chat_id: int, date: datetime):
        self.message_id = message_id
        self.chat_id = chat_id
        self.date = date

    @staticmethod
    def from_telegram(message: TGMessage) -> "Message":
        return Message(message.id, chat_id=message.chat_id, date=message.date)


@dataclass
class EffectiveUser:
    id: int
    first_name: str
    username: str | None = None


@dataclass
class EffectiveChat:
    id: int
    type: str


@dataclass
class EffectiveMessage:
    message_id: int
    chat_id: int
    date: datetime
    text: str | None


@dataclass
class CallbackQuery:
    id: str
    data: str | None
    user_id: int
    message_id: int | None
    chat_id: int | None


@dataclass
class EditedMessage:
    """Represents an edited message."""

    message_id: int
    chat_id: int
    date: datetime
    edit_date: datetime | None
    text: str | None = None


@dataclass
class Poll:
    id: str
    question: str
    options: list[PollOption]
    total_voter_count: int
    is_closed: bool
    is_anonymous: bool
    type: str
    allows_multiple_answers: bool


@dataclass
class PollAnswer:
    poll_id: str
    user: EffectiveUser | None
    option_ids: list[int]


@dataclass
class Update:
    update_id: int
    user: EffectiveUser | None = None
    chat: EffectiveChat | None = None
    message: EffectiveMessage | None = None
    callback_query: CallbackQuery | None = None

    edited_message: EditedMessage | None = None
    poll: Poll | None = None
    poll_answer: PollAnswer | None = None

    @property
    def effective_user_id(self) -> int | None:
        return self.user.id if self.user else None

    @property
    def effective_chat_id(self) -> int | None:
        return self.chat.id if self.chat else None

    def get_chat_id(self) -> int:
        """Extract chat ID from update with comprehensive fallback logic."""
        if self.message:
            return self.message.chat_id
        elif self.callback_query and self.callback_query.chat_id:
            return self.callback_query.chat_id
        elif self.chat:
            return self.chat.id
        else:
            raise ChatIdNotFoundError()
