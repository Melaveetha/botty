from collections.abc import AsyncGenerator
from unittest.mock import Mock, call

import pytest

from botty import Answer, BaseAnswer, Context, Update
from botty.routing import Conversation, Router, entry, step
from botty.testing import TestBotClient, TestContext
from botty.testing.helpers import make_message_update


async def logging_middleware(
    update: Update,
    context: Context,
    inner: AsyncGenerator[BaseAnswer, None],
) -> AsyncGenerator[BaseAnswer, None]:
    """Logs entry and exit, passes responses through."""
    context.mock_calls.logging_before()  # ty: ignore [unresolved-attribute]
    async for response in inner:
        context.mock_calls.logging_after(response.text)  # ty: ignore [unresolved-attribute]
        yield response


async def modify_middleware(
    update: Update,
    context: Context,
    inner: AsyncGenerator[BaseAnswer, None],
) -> AsyncGenerator[BaseAnswer, None]:
    """Adds a suffix to every text response."""
    async for response in inner:
        if hasattr(response, "text") and response.text:
            response.text += " (modified)"  # ty: ignore
        yield response


async def short_circuit_middleware(
    update: Update,
    context: Context,
    inner: AsyncGenerator[BaseAnswer, None],
) -> AsyncGenerator[BaseAnswer, None]:
    """Ignores the inner handler and yields its own answer."""
    context.mock_calls.short_circuit()  # ty: ignore [unresolved-attribute]
    yield Answer(text="Short-circuited")


async def exception_middleware(
    update: Update,
    context: Context,
    inner: AsyncGenerator[BaseAnswer, None],
) -> AsyncGenerator[BaseAnswer, None]:
    """Catches exception from inner and yields a fallback."""
    try:
        async for response in inner:
            yield response
    except Exception as e:
        context.mock_calls.exception_caught(str(e))  # ty: ignore [unresolved-attribute]
        yield Answer(text="Error recovered")


@pytest.fixture
def mock_calls() -> Mock:
    """A fresh Mock to record call events."""
    return Mock()


@pytest.fixture
def test_context_with_mock(test_context: TestContext, mock_calls: Mock) -> TestContext:
    """Inject the mock into the test context for middlewares to use."""
    test_context.mock_calls = mock_calls  # ty: ignore [unresolved-attribute]
    return test_context


class TestMiddlewareExecution:
    """Test that middlewares are applied in the correct order and can modify behavior."""

    @pytest.mark.asyncio
    async def test_middleware_order(
        self,
        router: Router,
        test_context_with_mock: TestContext,
        ptb_update,
        mock_calls: Mock,
    ):
        """First added = outermost, last added = innermost."""
        test_context_with_mock.bot_data.middlewares = [  # ty: ignore [invalid-assignment]
            logging_middleware,
            modify_middleware,
        ]

        @router.command("test")
        async def handler(update: Update, context: Context):
            context.mock_calls.handler_executed()  # ty: ignore [unresolved-attribute]
            yield Answer(text="Hello")

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_mock)

        expected_calls = [
            call.logging_before(),
            call.handler_executed(),
            call.logging_after("Hello (modified)"),
        ]
        assert mock_calls.mock_calls == expected_calls

        client: TestBotClient = test_context_with_mock.bot_data.bot_client  # ty: ignore [invalid-assignment]
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "Hello (modified)"  # ty: ignore

    @pytest.mark.asyncio
    async def test_middleware_short_circuit(
        self,
        router: Router,
        test_context_with_mock: TestContext,
        ptb_update,
        mock_calls: Mock,
    ):
        """Middleware can short-circuit and prevent handler from running."""
        test_context_with_mock.bot_data.middlewares = [  # ty: ignore [invalid-assignment]
            short_circuit_middleware,
            logging_middleware,
        ]

        @router.command("test")
        async def handler(update: Update, context: Context):
            context.mock_calls.handler_executed()  # ty: ignore [unresolved-attribute]
            yield Answer(text="Hello")

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_mock)

        assert mock_calls.mock_calls == [call.short_circuit()]

        client: TestBotClient = test_context_with_mock.bot_data.bot_client  # ty: ignore [invalid-assignment]
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "Short-circuited"  # ty: ignore

    @pytest.mark.asyncio
    async def test_middleware_can_modify_response_stream(
        self,
        router: Router,
        test_context_with_mock: TestContext,
        ptb_update,
        mock_calls: Mock,
    ):
        """Middleware can intercept and modify each yielded response."""
        test_context_with_mock.bot_data.middlewares = [modify_middleware]  # ty: ignore [invalid-assignment]

        @router.command("test")
        async def handler(update: Update, context: Context):
            yield Answer(text="First")
            yield Answer(text="Second")

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_mock)

        client: TestBotClient = test_context_with_mock.bot_data.bot_client  # ty: ignore [invalid-assignment]
        assert len(client.sent) == 2
        assert client.sent[0].answer.text == "First (modified)"  # ty: ignore
        assert client.sent[1].answer.text == "Second (modified)"  # ty: ignore

    @pytest.mark.asyncio
    async def test_middleware_can_handle_exceptions(
        self,
        router: Router,
        test_context_with_mock: TestContext,
        ptb_update,
        mock_calls: Mock,
    ):
        """Middleware can catch exceptions from the handler and recover."""
        test_context_with_mock.bot_data.middlewares = [exception_middleware]  # ty: ignore [invalid-assignment]

        @router.command("fail")
        async def handler(update: Update, context: Context):
            context.mock_calls.handler_executed()  # ty: ignore [unresolved-attribute]
            raise ValueError("boom")
            yield  # pragma: no cover

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_mock)

        assert mock_calls.mock_calls == [
            call.handler_executed(),
            call.exception_caught("boom"),
        ]
        client: TestBotClient = test_context_with_mock.bot_data.bot_client  # ty: ignore [invalid-assignment]
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "Error recovered"  # ty: ignore

    @pytest.mark.asyncio
    async def test_middleware_can_use_update_and_context(
        self,
        router: Router,
        test_context_with_mock: TestContext,
        ptb_update,
        mock_calls: Mock,
    ):
        """Middleware has access to the original update and context."""

        async def auth_middleware(
            update: Update,
            context: Context,
            inner: AsyncGenerator[BaseAnswer, None],
        ) -> AsyncGenerator[BaseAnswer, None]:
            if update.effective_user_id != 123:
                yield Answer("Unauthorized")
                return
            async for response in inner:
                yield response

        test_context_with_mock.bot_data.middlewares = [auth_middleware]  # ty: ignore [invalid-assignment]

        @router.command("secure")
        async def handler(update: Update, context: Context):
            context.mock_calls.handler_executed()  # ty: ignore [unresolved-attribute]
            yield Answer("Secret data")

        wrapper = router.handlers[0][2]

        await wrapper(ptb_update, test_context_with_mock)
        assert mock_calls.mock_calls == [call.handler_executed()]
        client: TestBotClient = test_context_with_mock.bot_data.bot_client  # ty: ignore [invalid-assignment]
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "Secret data"  # ty: ignore

        unauth_update = make_message_update(text="/secure", user_id=999, chat_id=456)
        mock_calls.reset_mock()
        client.clear()
        await wrapper(unauth_update, test_context_with_mock)
        assert mock_calls.mock_calls == []  # handler not called
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "Unauthorized"  # ty: ignore


class TestMiddlewareWithConversations:
    """Verify that middlewares work with conversation steps as well."""

    @pytest.mark.asyncio
    async def test_middleware_applies_to_conversation_steps(
        self,
        router: Router,
        test_context_with_mock: TestContext,
        ptb_update,
        mock_calls: Mock,
    ):
        """Conversation steps should also pass through the middleware stack."""
        test_context_with_mock.bot_data.middlewares = [modify_middleware]  # ty: ignore [invalid-assignment]

        @router.conversation("testconv")
        class TestConv(Conversation):
            @entry
            async def start(self, update: Update, context: Context):
                context.mock_calls.start_executed()  # ty: ignore [unresolved-attribute]
                yield Answer(text="Start")
                self.step("next")

            @step
            async def next(self, update: Update, context: Context):
                context.mock_calls.next_executed()  # ty: ignore [unresolved-attribute]
                yield Answer(text="Next")
                self.end()

        from botty.testing.conversation import ConversationTester

        tester = ConversationTester(
            router, TestConv, "testconv", context=test_context_with_mock
        )
        await tester.start()

        assert tester.last_responses[0].answer.text == "Start (modified)"  # ty: ignore
        assert mock_calls.mock_calls == [call.start_executed()]

        mock_calls.reset_mock()
        await tester.send_message("anything")
        assert tester.last_responses[0].answer.text == "Next (modified)"  # ty: ignore
        assert mock_calls.mock_calls == [call.next_executed()]


class TestMiddlewareEdgeCases:
    """Test edge cases like empty middleware list or no responses."""

    @pytest.mark.asyncio
    async def test_no_middlewares(
        self,
        router: Router,
        test_context_with_mock: TestContext,
        ptb_update,
        mock_calls: Mock,
    ):
        """With no middlewares, handler should execute normally."""
        test_context_with_mock.bot_data.middlewares = []

        @router.command("test")
        async def handler(update: Update, context: Context):
            context.mock_calls.handler_executed()  # ty: ignore [unresolved-attribute]
            yield Answer(text="Hello")

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_mock)

        assert mock_calls.mock_calls == [call.handler_executed()]
        client: TestBotClient = test_context_with_mock.bot_data.bot_client  # ty: ignore [invalid-assignment]
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "Hello"  # ty: ignore

    @pytest.mark.asyncio
    async def test_handler_without_responses(
        self,
        router: Router,
        test_context_with_mock: TestContext,
        ptb_update,
        mock_calls: Mock,
    ):
        """Middleware that doesn't yield anything should be fine."""

        async def empty_middleware(update, context, inner):
            async for _ in inner:
                if False:
                    yield

        test_context_with_mock.bot_data.middlewares = [empty_middleware]

        @router.command("test")
        async def handler(update: Update, context: Context):
            context.mock_calls.handler_executed()  # ty: ignore [unresolved-attribute]
            yield Answer(text="Hello")

        print(router.handlers)
        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, test_context_with_mock)

        assert mock_calls.mock_calls == [call.handler_executed()]
        client: TestBotClient = test_context_with_mock.bot_data.bot_client  # ty: ignore [invalid-assignment]
        assert len(client.sent) == 0  # nothing yielded
