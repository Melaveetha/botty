from typing import Protocol

from ..domain import Message
from ..responses import BaseAnswer


class TelegramBotClient(Protocol):
    """Port for sending and editing messages."""

    async def send(self, chat_id: int, answer: BaseAnswer) -> Message | None:
        """Send a message, return message_id."""
        ...

    async def edit(
        self, chat_id: int, message_id: int | None, answer: BaseAnswer
    ) -> Message | None:
        """Edit a message or send it, return message_id."""
        ...
