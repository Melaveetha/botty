from dataclasses import dataclass
from datetime import UTC, datetime

from botty.domain import Message
from botty.ports import TelegramBotClient
from botty.responses import BaseAnswer, EditAnswer


@dataclass
class SentMessage:
    __test__ = False
    chat_id: int
    answer: BaseAnswer
    method: str  # "send" or "edit"
    message_id: int | None = None


class TestBotClient(TelegramBotClient):
    __test__ = False

    def __init__(self):
        self.sent: list[SentMessage] = []
        self.next_id = 1000

    async def send(self, chat_id: int, answer: BaseAnswer) -> Message | None:
        msg = Message(message_id=self.next_id, chat_id=chat_id, date=datetime.now(UTC))
        self.sent.append(SentMessage(chat_id, answer, "send", self.next_id))
        self.next_id += 1
        return msg

    async def edit(
        self, chat_id: int, message_id: int | None, answer: BaseAnswer
    ) -> Message | None:
        if not isinstance(answer, EditAnswer):
            return None
        self.sent.append(SentMessage(chat_id, answer, "edit", message_id))
        return Message(
            message_id=message_id or 0, chat_id=chat_id, date=datetime.now(UTC)
        )

    def clear(self):
        self.sent.clear()
        self.next_id = 1000
