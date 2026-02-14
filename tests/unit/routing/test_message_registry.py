from botty.routing import MessageRegistry
import time
from botty.testing import TestMessageRegistry
from datetime import datetime

from botty.domain import Message
from botty.responses import EditAnswer


class TestMessageRegistryLocal:
    """Tests for the MessageRegistry class."""

    def test_register_message_without_key(self, message_registry, sample_message):
        """Register a message without a key."""
        record = message_registry.register_message(sample_message, handler_name="test")

        assert record.message_id == 100
        assert record.chat_id == 123
        assert record.handler_name == "test"
        assert record.metadata == {}

        # Check that it appears in per-chat deque
        assert len(message_registry._registry[123]) == 1
        assert message_registry._registry[123][0] is record

    def test_register_message_with_key(self, message_registry, sample_message):
        """Register a message with a key."""
        record = message_registry.register_message(
            sample_message, handler_name="test", key="mykey", metadata={"foo": "bar"}
        )

        assert record.message_id == 100
        assert record.metadata == {"foo": "bar"}

        # Check key registry
        assert message_registry.get_by_key("mykey") is record

        # Check handler registry
        records = message_registry.get_by_handler("test")
        assert len(records) == 1
        assert records[0] is record

    def test_register_multiple_messages_per_chat(
        self, message_registry, sample_message
    ):
        """Register multiple messages for same chat."""
        msg1 = Message(message_id=1, chat_id=123, date=datetime.now())
        msg2 = Message(message_id=2, chat_id=123, date=datetime.now())
        msg3 = Message(message_id=3, chat_id=123, date=datetime.now())

        message_registry.register_message(msg1, handler_name="h1")
        message_registry.register_message(msg2, handler_name="h2")
        message_registry.register_message(msg3, handler_name="h3")

        chat_messages = message_registry.get_all_for_chat(123)
        assert len(chat_messages) == 3
        # Most recent first
        assert chat_messages[0].message_id == 3
        assert chat_messages[1].message_id == 2
        assert chat_messages[2].message_id == 1

    def test_automatic_cleanup_when_limit_exceeded(
        self, message_registry, sample_message
    ):
        """When max per chat exceeded, oldest is removed from indexes."""
        # Send 4 messages to chat 123 (max=3)
        for i in range(4):
            msg = Message(message_id=i, chat_id=123, date=datetime.now())
            message_registry.register_message(msg, handler_name=f"h{i}", key=f"key{i}")

        # Only the last 3 should remain
        messages = message_registry.get_all_for_chat(123)
        assert len(messages) == 3
        assert [m.message_id for m in messages] == [3, 2, 1]

        # Oldest message (id=0) should be removed from key registry
        assert message_registry.get_by_key("key0") is None

        # Oldest message should be removed from handler registry
        assert len(message_registry.get_by_handler("h0")) == 0

        # Newer messages still have their keys
        assert message_registry.get_by_key("key3") is not None
        assert len(message_registry.get_by_handler("h3")) == 1

    def test_get_last_message(self, message_registry, sample_message):
        """get_last_message returns most recent message."""
        msg1 = Message(message_id=1, chat_id=123, date=datetime.now())
        msg2 = Message(message_id=2, chat_id=123, date=datetime.now())
        message_registry.register_message(msg1)
        message_registry.register_message(msg2)

        last = message_registry.get_last_message(123)
        assert last is not None
        assert last.message_id == 2

        # Non-existent chat returns None
        assert message_registry.get_last_message(999) is None

    def test_get_by_handler_with_filters(self):
        """get_by_handler respects chat_id and limit."""
        # Messages from different chats and handlers
        registry = TestMessageRegistry(max_messages_per_chat=100)
        for chat in [1, 2]:
            for handler in ["a", "b"]:
                for i in range(2):
                    msg = Message(message_id=i, chat_id=chat, date=datetime.now())
                    registry.register_message(msg, handler_name=handler)

        # All messages from handler 'a'
        all_a = registry.get_by_handler("a")
        assert len(all_a) == 4  # 2 chats * 2 messages

        # Only chat 1
        chat1_a = registry.get_by_handler("a", chat_id=1)
        assert len(chat1_a) == 2

        # Limit
        limited = registry.get_by_handler("a", limit=2)
        assert len(limited) == 2
        # Should be most recent first, but since we didn't vary dates, order not important

    def test_get_by_key_nonexistent(self, message_registry):
        """get_by_key returns None for unknown key."""
        assert message_registry.get_by_key("missing") is None

    def test_find_message_to_edit_priority(self, sample_message):
        """Test edit target selection follows priority order."""
        chat_id = 123
        handler_name = "current_handler"
        message_registry = MessageRegistry(5)

        # Setup: register some messages with different attributes
        # Message with direct ID
        msg_id = Message(message_id=50, chat_id=chat_id, date=datetime.now())
        message_registry.register_message(msg_id, handler_name="other")
        time.sleep(0.001)

        # Message with key
        msg_key = Message(message_id=51, chat_id=chat_id, date=datetime.now())
        message_registry.register_message(
            msg_key, handler_name="other", key="target_key"
        )
        time.sleep(0.001)

        # Message from same handler
        msg_handler = Message(message_id=52, chat_id=chat_id, date=datetime.now())
        message_registry.register_message(msg_handler, handler_name=handler_name)
        time.sleep(0.001)

        # Last message in chat
        msg_last = Message(message_id=53, chat_id=chat_id, date=datetime.now())
        message_registry.register_message(msg_last, handler_name="other")
        time.sleep(0.001)

        # 1. Direct message ID takes precedence
        answer = EditAnswer(text="edit", message_id=50)
        found = message_registry.find_message_to_edit(answer, chat_id, handler_name)
        assert found == 50

        # 2. Message key
        answer = EditAnswer(text="edit", message_key="target_key")
        found = message_registry.find_message_to_edit(answer, chat_id, handler_name)
        assert found == 51

        # 3. Handler name specified in answer
        answer = EditAnswer(text="edit", handler_name="other")
        found = message_registry.find_message_to_edit(answer, chat_id, handler_name)
        assert found == 53

        # Register: id 100 (key="key100", handler="h1"), id 101 (handler="h2"), id 102 (no special), id 103 (last in chat)
        m1 = Message(message_id=100, chat_id=chat_id, date=datetime.now())
        message_registry.register_message(m1, handler_name="h1", key="key100")
        m2 = Message(message_id=101, chat_id=chat_id, date=datetime.now())
        message_registry.register_message(m2, handler_name="h2")
        m3 = Message(message_id=102, chat_id=chat_id, date=datetime.now())
        message_registry.register_message(m3, handler_name="h1")
        m4 = Message(message_id=103, chat_id=chat_id, date=datetime.now())
        message_registry.register_message(m4, handler_name="h3")

        # Now test priorities with current_handler = "h2"
        # 1. Direct ID
        assert (
            message_registry.find_message_to_edit(
                EditAnswer(text="test", message_id=102), chat_id, "h2"
            )
            == 102
        )
        # 2. Key
        assert (
            message_registry.find_message_to_edit(
                EditAnswer(text="test", message_key="key100"), chat_id, "h2"
            )
            == 100
        )
        # 3. Handler name in answer (should pick last from that handler, here h1 last is 102)
        assert (
            message_registry.find_message_to_edit(
                EditAnswer(text="test", handler_name="h1"), chat_id, "h2"
            )
            == 102
        )
        # 4. Current handler's last (h2's last is 101)
        assert (
            message_registry.find_message_to_edit(
                EditAnswer(text="test"), chat_id, "h2"
            )
            == 101
        )
        # 5. Last message in chat (103)
        # But if current handler has no messages, fallback to last chat
        assert (
            message_registry.find_message_to_edit(
                EditAnswer(text="test"), chat_id, "nonexistent"
            )
            == 103
        )

    def test_cleanup_removes_all_references(self, message_registry):
        """When a message is evicted, it's removed from all indexes."""
        chat_id = 1
        # Fill up to max (3)
        msg1 = Message(message_id=1, chat_id=chat_id, date=datetime.now())
        msg2 = Message(message_id=2, chat_id=chat_id, date=datetime.now())
        msg3 = Message(message_id=3, chat_id=chat_id, date=datetime.now())
        r1 = message_registry.register_message(msg1, handler_name="h1", key="k1")
        r2 = message_registry.register_message(msg2, handler_name="h2", key="k2")
        r3 = message_registry.register_message(msg3, handler_name="h3", key="k3")

        # Add fourth, evicts first
        msg4 = Message(message_id=4, chat_id=chat_id, date=datetime.now())
        r4 = message_registry.register_message(msg4, handler_name="h4", key="k4")

        # Check r1 is gone
        assert message_registry.get_by_key("k1") is None
        assert r1 not in message_registry.get_by_handler("h1")
        # r2, r3, r4 remain
        assert message_registry.get_by_key("k2") is r2
        assert message_registry.get_by_key("k3") is r3
        assert message_registry.get_by_key("k4") is r4
        assert len(message_registry.get_by_handler("h2")) == 1
        assert len(message_registry.get_by_handler("h3")) == 1
        assert len(message_registry.get_by_handler("h4")) == 1

    def test_cleanup_removes_empty_handler_entry(self, message_registry):
        """When last message of a handler is removed, handler entry is deleted."""
        chat_id = 1
        msg = Message(message_id=1, chat_id=chat_id, date=datetime.now())
        message_registry.register_message(msg, handler_name="lonely", key="k1")

        # Add two more to evict the lonely one
        msg2 = Message(message_id=2, chat_id=chat_id, date=datetime.now())
        msg3 = Message(message_id=3, chat_id=chat_id, date=datetime.now())
        msg4 = Message(message_id=4, chat_id=chat_id, date=datetime.now())
        message_registry.register_message(msg2, handler_name="h2")
        message_registry.register_message(msg3, handler_name="h3")
        message_registry.register_message(msg4, handler_name="h4")

        # "lonely" handler should be gone
        assert "lonely" not in message_registry._handler_registry
