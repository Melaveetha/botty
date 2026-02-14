import time
from collections import deque
from dataclasses import dataclass, field

from loguru import logger

from ..domain import Message
from ..responses import EditAnswer


@dataclass
class MessageRecord:
    """Record about a sent message stored in the MessageRegistry.

    Attributes:
        message_id: Telegram message ID.
        chat_id: Telegram chat ID.
        handler_name: Name of the handler that sent this message.
        timestamp: Unix timestamp when the message was sent.
        metadata: Optional custom metadata provided at registration.
    """

    message_id: int
    chat_id: int
    handler_name: str
    timestamp: float
    metadata: dict = field(default_factory=dict)

    @property
    def age(self) -> float:
        """Get age of message in seconds."""
        return time.time() - self.timestamp

    def is_older_than(self, seconds: float) -> bool:
        """Check if message is older than given seconds."""
        return self.age > seconds


class MessageRegistry:
    """Registry for tracking bot-sent messages with automatic cleanup.

    Features:
    - Track messages by chat, handler, and custom keys.
    - Automatic cleanup of old messages (FIFO per chat).
    - Configurable limits per chat.
    - Memory-efficient using deques.

    The registry is stored in `bot_data` and shared across all handlers.
    It is used primarily by ResponseProcessor to find messages for editing.

    Example:
        registry = MessageRegistry(max_messages_per_chat=50)
        registry.register_message(message, handler_name="start")
        record = registry.get_last_message(chat_id)
    """

    def __init__(
        self,
        max_messages_per_chat: int = 100,
    ):
        """Initialize the registry.

        Args:
            max_messages_per_chat: Maximum number of messages to keep per chat.
                                   Older messages are automatically discarded.
        """
        self.max_messages_per_chat = max_messages_per_chat

        self._registry: dict[int, deque[MessageRecord]] = dict()
        self._key_registry: dict[str, MessageRecord] = (
            dict()
        )  # mapping of keys to chat_id
        self._handler_registry: dict[str, list[MessageRecord]] = (
            dict()
        )  # mapping of handlers to chat_id list

        logger.debug(
            f"Initialized MessageRegistry: max_per_chat={max_messages_per_chat}, "
        )

    def register_message(
        self,
        message: Message,
        handler_name: str | None = None,
        key: str | None = None,
        metadata: dict | None = None,
    ) -> MessageRecord:
        """Store a sent message in the registry.

        Args:
            message: The Message object returned by the bot client.
            handler_name: Name of the handler that produced this message.
            key: Optional unique key for later retrieval.
            metadata: Optional extra data to store.

        Returns:
            The created MessageRecord.

        Example:
            ```python
            record = registry.register_message(
                message,
                handler_name="profile_command",
                key="user_profile_123",
                metadata={"user_id": 123}
            )
            ```
        """

        record = MessageRecord(
            message_id=message.message_id,
            chat_id=message.chat_id,
            handler_name=handler_name or "unknown",
            timestamp=message.date.timestamp() if message.date else time.time(),
            metadata=metadata or {},
        )

        if message.chat_id not in self._registry:
            self._registry[message.chat_id] = deque(maxlen=self.max_messages_per_chat)

        # Add to chat's message deque (automatically removes oldest if full)
        old_record = None
        if len(self._registry[message.chat_id]) >= self.max_messages_per_chat:
            old_record = self._registry[message.chat_id][0]

        self._registry[message.chat_id].append(record)

        if old_record:
            self._cleanup_record_references(old_record)

        if key:
            if key in self._key_registry:
                logger.debug(f"Replacing existing key mapping: {key}")
            self._key_registry[key] = record

        if handler_name:
            if handler_name not in self._handler_registry:
                self._handler_registry[handler_name] = []
            self._handler_registry[handler_name].append(record)

        return record

    def get_last_message(self, chat_id: int) -> MessageRecord | None:
        """Retrieve the most recent message sent in a chat.

        Args:
            chat_id: Telegram chat ID.

        Returns:
            The latest MessageRecord, or None if none exist.
        """
        if chat_id in self._registry and self._registry[chat_id]:
            return self._registry[chat_id][-1]
        return None

    def get_by_key(self, key: str) -> MessageRecord | None:
        """Retrieve a message by its unique key.

        Args:
            key: The key provided during registration.

        Returns:
            The associated MessageRecord, or None if not found.
        """
        return self._key_registry.get(key)

    def get_by_handler(
        self,
        handler_name: str,
        chat_id: int | None = None,
        limit: int | None = None,
    ) -> list[MessageRecord]:
        """Retrieve messages sent by a specific handler.

        Args:
            handler_name: Name of the handler.
            chat_id: If provided, only messages from this chat are returned.
            limit: Maximum number of messages (most recent first).

        Returns:
            List of matching MessageRecords.
        """
        records = self._handler_registry.get(handler_name, []).copy()

        if chat_id:
            records = [r for r in records if r.chat_id == chat_id]

        records = sorted(records, key=lambda r: r.timestamp, reverse=True)

        # Apply limit
        if limit:
            records = records[:limit]

        return records

    def get_all_for_chat(
        self, chat_id: int, limit: int | None = None
    ) -> list[MessageRecord]:
        """Retrieve all messages for a chat, most recent first.

        Args:
            chat_id: Telegram chat ID.
            limit: Maximum number of messages to return.

        Returns:
            List of MessageRecords.
        """
        if chat_id not in self._registry:
            return []

        messages = list(self._registry[chat_id])
        messages.reverse()  # Most recent first

        if limit:
            messages = messages[:limit]

        return messages

    def _cleanup_record_references(self, record: MessageRecord) -> None:
        """Remove all references to a record from secondary indexes."""
        # Remove from key registry
        keys_to_remove = [
            k
            for k, v in self._key_registry.items()
            if v.message_id == record.message_id
        ]
        for key in keys_to_remove:
            del self._key_registry[key]

        # Remove from handler registry
        if record.handler_name in self._handler_registry:
            try:
                self._handler_registry[record.handler_name].remove(record)
                if not self._handler_registry[record.handler_name]:
                    del self._handler_registry[record.handler_name]
            except ValueError:
                pass

    def find_message_to_edit(
        self, answer: EditAnswer, chat_id: int, handler_name: str
    ) -> int | None:
        """Determine which message ID to edit based on the EditAnswer criteria.

        Priority order:
        1. Direct message_id from answer.
        2. Lookup by message_key.
        3. Handler name specified in answer.
        4. Last message from current handler.
        5. Last message in chat (fallback).

        Args:
            answer: The EditAnswer containing editing hints.
            chat_id: The chat where editing should occur.
            handler_name: Name of the handler currently executing.

        Returns:
            The message ID to edit, or None if no suitable message found.
        """
        # 1. Direct message ID
        if answer.message_id is not None:
            return answer.message_id

        # 2. Message key lookup
        if answer.message_key is not None:
            record = self.get_by_key(answer.message_key)
            if record is not None and record.chat_id == chat_id:
                return record.message_id

        # 3. Handler name was specified by user
        if answer.handler_name is not None:
            records = self.get_by_handler(answer.handler_name, chat_id)
            if len(records) > 0:
                return records[0].message_id

        # 4. Last message from current handler
        records = self.get_by_handler(handler_name, chat_id)
        if len(records) > 0:
            return records[0].message_id

        # 5. Last message in chat (fallback)
        last_message = self.get_last_message(chat_id)
        if last_message is not None:
            return last_message.message_id

        return None
