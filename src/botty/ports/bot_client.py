from typing import Protocol

from ..domain import Message
from ..responses import BaseAnswer


class TelegramBotClient(Protocol):
    """Port (interface) for sending and editing messages.

    Concrete implementations (e.g., PTBBotAdapter) must provide these methods.
    This protocol allows the framework to remain decoupled from the actual
    Telegram library.
    """

    async def send(self, chat_id: int, answer: BaseAnswer) -> Message | None:
        """Send a message to a chat.

        Args:
            chat_id: Telegram chat ID.
            answer: The response object to send.

        Returns:
            A domain Message object with details of the sent message,
            or None if nothing was sent (e.g., EmptyAnswer).
        """
        ...

    async def edit(
        self, chat_id: int, message_id: int | None, answer: BaseAnswer
    ) -> Message | None:
        """Edit an existing message or send a new one as fallback.

        Args:
            chat_id: Telegram chat ID.
            message_id: ID of the message to edit, if known.
            answer: The response object to apply (typically EditAnswer).

        Returns:
            A domain Message object for the edited/fallback message,
            or None if no action taken.
        """
        ...
