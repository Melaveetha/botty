from botty.routing.registry import MessageRecord, MessageRegistry


class TestMessageRegistry(MessageRegistry):
    """Adds methods to inspect and clear registry state."""

    __test__ = False

    def __init__(self, max_messages_per_chat: int = 100):
        super().__init__(max_messages_per_chat)

    def get_all_records(self) -> list[MessageRecord]:
        """Return all stored records (flattened)."""
        all_records = []
        for deque in self._registry.values():
            all_records.extend(deque)
        return all_records

    def clear(self):
        self._registry.clear()
        self._key_registry.clear()
        self._handler_registry.clear()
