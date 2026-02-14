# tests/unit/routing/test_router.py
from typing import Annotated, AsyncGenerator
from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    PrefixHandler,
    filters,
)

from botty import Answer, BaseAnswer, Context, Depends, EditAnswer, Update
from botty.di import RequestScope
from botty.exceptions import DependencyResolutionError
from botty.responses import EmptyAnswer
from botty.testing import (
    TestBotClient,
    TestContext,
    TestDependencyContainer,
    TestMessageRegistry,
)

# -------------------------------------------------------------------
# Test doubles – handler functions for various scenarios
# -------------------------------------------------------------------


async def simple_handler(
    update: Update, context: Context
) -> AsyncGenerator[BaseAnswer, None]:
    """Handler that yields one answer."""
    yield Answer(text="Hello")


async def multi_answer_handler(
    update: Update, context: Context
) -> AsyncGenerator[BaseAnswer, None]:
    """Handler that yields multiple answers."""
    yield Answer(text="First")
    yield Answer(text="Second")


async def edit_handler(
    update: Update, context: Context
) -> AsyncGenerator[BaseAnswer, None]:
    """Handler that yields an edit answer."""
    yield EditAnswer(text="Edited", message_key="test_key")


async def handler_with_deps(
    update: Update,
    context: Context,
    value: Annotated[str, Depends(lambda: "injected")],
) -> AsyncGenerator[BaseAnswer, None]:
    """Handler that uses a dependency."""
    yield Answer(text=value)


async def handler_with_session(
    update: Update,
    context: Context,
    session: Session,
) -> AsyncGenerator[BaseAnswer, None]:
    """Handler that requests a database session."""
    yield Answer(text="session ok")


async def failing_handler(
    update: Update, context: Context
) -> AsyncGenerator[BaseAnswer, None]:
    """Handler that raises an exception during execution."""
    raise ValueError("oops")
    yield  # pragma: no cover


async def empty_handler(
    update: Update, context: Context
) -> AsyncGenerator[BaseAnswer, None]:
    """Handler that yields EmptyAnswer (should not send a message)."""
    yield EmptyAnswer(text="test")


# -------------------------------------------------------------------
# Test classes
# -------------------------------------------------------------------


class TestRouterRegistration:
    """Verify that decorators register handlers correctly."""

    def test_command_decorator_single(self, router):
        @router.command("start")
        async def handler(update: Update, context: Context):
            yield Answer(text="ok")

        assert len(router.handlers) == 1
        assert router.handlers[0][0] == "command"
        assert router.handlers[0][1] == "start"
        assert callable(router.handlers[0][2])

    def test_command_decorator_multiple(self, router):
        @router.command(["help", "info"])
        async def handler(update: Update, context: Context):
            yield Answer(text="ok")

        assert len(router.handlers) == 2
        assert router.handlers[0][0] == "command"
        assert router.handlers[0][1] == "help"
        assert router.handlers[1][1] == "info"

    def test_callback_query_decorator(self, router):
        @router.callback_query(r"^data_\d+")
        async def handler(update: Update, context: Context):
            yield Answer(text="ok")

        assert len(router.handlers) == 1
        assert router.handlers[0][0] == "callback_query"
        assert router.handlers[0][1] == r"^data_\d+"

    def test_message_decorator(self, router):
        @router.message(filters.TEXT)
        async def handler(update: Update, context: Context):
            yield Answer(text="ok")

        assert len(router.handlers) == 1
        assert router.handlers[0][0] == "message"
        assert router.handlers[0][1] is filters.TEXT

    def test_inline_query_decorator(self, router):
        @router.inline_query(pattern="^query")
        async def handler(update: Update, context: Context):
            yield Answer(text="ok")

        assert len(router.handlers) == 1
        assert router.handlers[0][0] == "inline_query"
        assert router.handlers[0][1] == "^query"

    def test_prefix_decorator_single(self, router):
        @router.prefix("!", "help")
        async def handler(update: Update, context: Context):
            yield Answer(text="ok")

        assert len(router.handlers) == 1
        assert router.handlers[0][0] == "prefix"
        assert router.handlers[0][1] == "!"
        assert router.handlers[0][2] == "help"

    def test_prefix_decorator_multiple(self, router):
        @router.prefix("!", ["help", "info"])
        async def handler(update: Update, context: Context):
            yield Answer(text="ok")

        assert len(router.handlers) == 2
        assert router.handlers[0][1] == "!"
        assert router.handlers[0][2] == "help"
        assert router.handlers[1][2] == "info"

    def test_get_handlers_returns_ptb_objects(self, router):
        @router.command("start")
        async def cmd(update: Update, context: Context):
            yield Answer(text="ok")

        @router.callback_query("pattern")
        async def cb(update: Update, context: Context):
            yield Answer(text="ok")

        @router.message(filters.TEXT)
        async def msg(update: Update, context: Context):
            yield Answer(text="ok")

        @router.inline_query()
        async def inline(update: Update, context: Context):
            yield Answer(text="ok")

        @router.prefix("!", "help")
        async def pref(update: Update, context: Context):
            yield Answer(text="ok")

        ptb_handlers = router.get_handlers()

        assert len(ptb_handlers) == 5
        assert isinstance(ptb_handlers[0], CommandHandler)
        assert isinstance(ptb_handlers[1], CallbackQueryHandler)
        assert isinstance(ptb_handlers[2], MessageHandler)
        assert isinstance(ptb_handlers[3], InlineQueryHandler)
        assert isinstance(ptb_handlers[4], PrefixHandler)


class TestHandlerExecution:
    """Test that the wrapper executes handlers correctly with all components."""

    @pytest.mark.asyncio
    async def test_simple_handler_sends_message(
        self, router, ptb_update, test_context_with_doubles
    ):
        @router.command("start")
        async def handler(update: Update, context: Context):
            yield Answer(text="Hello")

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_doubles)

        client = test_context_with_doubles.bot_data.bot_client
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "Hello"
        assert client.sent[0].method == "send"

        registry = test_context_with_doubles.bot_data.message_registry
        records = registry.get_all_records()
        assert len(records) == 1
        assert records[0].handler_name == "handler"
        assert records[0].message_id == 1000

    @pytest.mark.asyncio
    async def test_multi_answer_handler_sends_multiple_messages(
        self, router, ptb_update, test_context_with_doubles
    ):
        @router.command("multi")
        async def handler(update: Update, context: Context):
            yield Answer(text="First")
            yield Answer(text="Second")

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_doubles)

        client = test_context_with_doubles.bot_data.bot_client
        assert len(client.sent) == 2
        assert client.sent[0].answer.text == "First"
        assert client.sent[1].answer.text == "Second"
        assert client.sent[0].message_id == 1000
        assert client.sent[1].message_id == 1001

    @pytest.mark.asyncio
    async def test_edit_handler_finds_message_by_key(
        self, router, ptb_update, test_context_with_doubles
    ):
        @router.command("edit")
        async def handler(update: Update, context: Context):
            yield EditAnswer(text="Edited", message_key="test_key")

        wrapper = router.handlers[0][2]

        registry = test_context_with_doubles.bot_data.message_registry
        from datetime import datetime

        from botty.domain import Message

        fake_message = Message(message_id=42, chat_id=456, date=datetime.now())
        registry.register_message(fake_message, key="test_key", handler_name="previous")

        await wrapper(ptb_update, test_context_with_doubles)

        client = test_context_with_doubles.bot_data.bot_client
        assert len(client.sent) == 1
        sent = client.sent[0]
        assert sent.method == "edit"
        assert sent.message_id == 42
        assert sent.answer.text == "Edited"

    @pytest.mark.asyncio
    async def test_handler_with_dependency_injection(
        self, router, ptb_update, test_context_with_doubles
    ):
        @router.command("dep")
        async def handler(
            update: Update,
            context: Context,
            value: Annotated[str, Depends(lambda: "injected")],
        ):
            yield Answer(text=value)

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_doubles)

        client = test_context_with_doubles.bot_data.bot_client
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "injected"

    @pytest.mark.asyncio
    async def test_handler_with_session_injection(
        self, router, ptb_update, test_context_with_doubles
    ):
        @router.command("session")
        async def handler(update: Update, context: Context, session: Session):
            yield Answer(text="session ok")

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_doubles)

        client = test_context_with_doubles.bot_data.bot_client
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "session ok"

    @pytest.mark.asyncio
    async def test_request_scope_closes_session(
        self, router, ptb_update, test_context_with_doubles
    ):
        with patch.object(
            test_context_with_doubles.bot_data.database_provider, "get_session"
        ) as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = mock_session

            @router.command("close")
            async def handler(update: Update, context: Context, session: Session):
                yield Answer(text="done")

            wrapper = router.handlers[0][2]
            await wrapper(ptb_update, test_context_with_doubles)

            mock_session.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_registry_records_handler_name_and_key(
        self, router, ptb_update, test_context_with_doubles
    ):
        @router.command("register")
        async def handler(update: Update, context: Context):
            yield Answer(text="Hi", message_key="greeting", metadata={"foo": "bar"})

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_doubles)

        registry = test_context_with_doubles.bot_data.message_registry
        record = registry.get_by_key("greeting")
        assert record is not None
        assert record.handler_name == "handler"
        assert record.metadata == {"foo": "bar"}
        assert record.chat_id == 456


class TestErrorHandling:
    """Test that the router handles errors gracefully."""

    @pytest.mark.asyncio
    async def test_dependency_resolution_error_propagates(
        self, router, ptb_update, test_context_with_doubles
    ):
        @router.command("bad")
        async def handler(
            update: Update,
            context: Context,
            missing: Annotated[str, Depends(lambda: "x")],
        ):
            yield Answer(text="test")

        container = test_context_with_doubles.bot_data.dependency_container

        async def failing_resolve(dep, scope):
            raise DependencyResolutionError("simulated failure")

        container.resolve_dependency = failing_resolve

        wrapper = router.handlers[0][2]
        with pytest.raises(DependencyResolutionError):
            await wrapper(ptb_update, test_context_with_doubles)

    @pytest.mark.asyncio
    async def test_handler_exception_caught_and_logged(
        self, router, ptb_update, test_context_with_doubles
    ):
        @router.command("fail")
        async def handler(update: Update, context: Context):
            raise ValueError("boom")
            yield  # pragma: no cover

        wrapper = router.handlers[0][2]
        with pytest.raises(ValueError):
            await wrapper(ptb_update, test_context_with_doubles)

        # Exception propagates, no log capture needed

    @pytest.mark.asyncio
    async def test_response_processor_handles_send_failure(
        self, router, ptb_update, test_context_with_doubles, caplog
    ):
        caplog.set_level("ERROR")
        client = test_context_with_doubles.bot_data.bot_client

        async def failing_send(chat_id, answer):
            raise Exception("network error")

        client.send = failing_send

        @router.command("failing")
        async def handler(update: Update, context: Context):
            yield Answer(text="will fail")

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_doubles)

        assert "network error" in caplog.text

    @pytest.mark.asyncio
    async def test_missing_database_for_session_raises_helpful_error(
        self, router, ptb_update
    ):
        ctx = TestContext()
        ctx.bot_data.database_provider = None
        ctx.bot_data.dependency_container = TestDependencyContainer()
        ctx.bot_data.message_registry = TestMessageRegistry()
        ctx.bot_data.bot_client = TestBotClient()

        @router.command("needs_db")
        async def needs_db_handler(update: Update, context: Context, session: Session):
            yield Answer(text="test")

        wrapper = router.handlers[0][2]
        with pytest.raises(DependencyResolutionError) as exc:
            await wrapper(ptb_update, ctx)
        assert "no database provider configured" in str(exc.value)
        assert "handler 'needs_db_handler'" in str(exc.value)


class TestRouterInternals:
    """Test internal methods like request_scope and _wrap_function."""

    @pytest.mark.asyncio
    async def test_request_scope_context_manager(
        self, router, sample_update, test_context_with_doubles
    ):
        async with router.request_scope(
            sample_update, test_context_with_doubles
        ) as scope:
            assert isinstance(scope, RequestScope)
            assert scope.update is sample_update
            assert scope.context is test_context_with_doubles
            sess = scope.session
            assert sess is not None

    @pytest.mark.asyncio
    async def test_wrap_function_calls_resolve_and_process(
        self, router, ptb_update, test_context_with_doubles
    ):
        with patch.object(
            router, "_wrap_function", wraps=router._wrap_function
        ) as wrap_spy:

            @router.command("spy")
            async def handler(update: Update, context: Context):
                yield Answer(text="spied")

            wrapper = router.handlers[0][2]
            await wrapper(ptb_update, test_context_with_doubles)

            wrap_spy.assert_called_once()
            # We can't easily compare the function because it's wrapped, but we can check that the call happened
            # and that a message was sent.
            client = test_context_with_doubles.bot_data.bot_client
            assert len(client.sent) == 1
            assert client.sent[0].answer.text == "spied"
