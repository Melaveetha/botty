from sqlmodel import Session
from typing import Annotated
import pytest
from unittest.mock import Mock

from botty import Answer, Update, Context, Depends
from botty.exceptions import BottyError
from botty.di import HandlerResponse


class ValueTooHighError(BottyError):
    pass


class ValueTooLowError(BottyError):
    pass


@pytest.fixture
def exception_handlers_context(test_context_with_doubles):
    """TestContext with an empty exception_handlers list."""
    ctx = test_context_with_doubles
    ctx.bot_data.exception_handlers = []
    return ctx


@pytest.mark.asyncio
class TestGlobalExceptionHandlers:
    """Test suite for global exception handlers."""

    async def test_exception_handler_called(
        self, router, ptb_update, exception_handlers_context
    ):
        """A registered exception handler should be invoked when its exception is raised."""

        # Arrange
        @router.command("raise")
        async def failing_handler(update: Update, context: Context) -> HandlerResponse:
            raise ValueError("boom")
            yield  # pragma: no cover

        async def value_error_handler(
            update: Update, context: Context, exc: Exception
        ) -> HandlerResponse:
            yield Answer(text="Caught ValueError")

        exception_handlers_context.bot_data.exception_handlers = [
            (ValueError, value_error_handler)
        ]

        wrapper = router.handlers[0][2]

        # Act
        await wrapper(ptb_update, exception_handlers_context)

        # Assert
        client = exception_handlers_context.bot_data.bot_client
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "Caught ValueError"

    async def test_exception_object_injected(
        self, router, ptb_update, exception_handlers_context
    ):
        """The exception should be injected into the handler if a parameter of that type exists."""

        # Arrange
        @router.command("raise")
        async def failing_handler(update: Update, context: Context) -> HandlerResponse:
            raise ValueError("specific message")
            yield

        async def value_error_handler(
            update: Update, context: Context, exc: Exception
        ) -> HandlerResponse:
            yield Answer(text=f"Got: {exc}")

        exception_handlers_context.bot_data.exception_handlers = [
            (ValueError, value_error_handler)
        ]

        wrapper = router.handlers[0][2]

        # Act
        await wrapper(ptb_update, exception_handlers_context)

        # Assert
        client = exception_handlers_context.bot_data.bot_client
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "Got: specific message"

    async def test_exception_handler_order(
        self, router, ptb_update, exception_handlers_context
    ):
        """Handlers are tried in registration order; the first matching one is used."""

        # Arrange
        @router.command("raise")
        async def failing_handler(update: Update, context: Context) -> HandlerResponse:
            raise ValueTooHighError("too high")
            yield

        async def high_handler(
            update: Update, context: Context, exc: Exception
        ) -> HandlerResponse:
            yield Answer(text="high handler")

        async def base_handler(
            update: Update, context: Context, exc: Exception
        ) -> HandlerResponse:
            yield Answer(text="base handler")

        # Register base first, then specific
        exception_handlers_context.bot_data.exception_handlers = [
            (Exception, base_handler),
            (ValueTooHighError, high_handler),
        ]

        wrapper = router.handlers[0][2]
        await wrapper(ptb_update, exception_handlers_context)

        client = exception_handlers_context.bot_data.bot_client
        assert len(client.sent) == 1
        # First match is Exception, so base handler should run
        assert client.sent[0].answer.text == "base handler"
        client.clear()

        # Now register specific first
        exception_handlers_context.bot_data.exception_handlers = [
            (ValueTooHighError, high_handler),
            (Exception, base_handler),
        ]
        await wrapper(ptb_update, exception_handlers_context)
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "high handler"

    async def test_no_matching_handler_propagates(
        self, router, ptb_update, exception_handlers_context
    ):
        """If no handler matches the exception, it propagates."""

        # Arrange
        @router.command("raise")
        async def failing_handler(update: Update, context: Context) -> HandlerResponse:
            raise ValueTooLowError("too low")
            yield

        async def high_handler(
            update: Update, context: Context, exc: Exception
        ) -> HandlerResponse:
            yield Answer(text="high handler")

        exception_handlers_context.bot_data.exception_handlers = [
            (ValueTooHighError, high_handler)
        ]

        wrapper = router.handlers[0][2]

        # Act & Assert
        with pytest.raises(ValueTooLowError):
            await wrapper(ptb_update, exception_handlers_context)

        # No message should be sent
        client = exception_handlers_context.bot_data.bot_client
        assert len(client.sent) == 0

    async def test_session_rolled_back_and_closed(
        self, router, ptb_update, exception_handlers_context
    ):
        """After exception handler runs, the session should be rolled back and closed."""

        # Arrange
        @router.command("raise")
        async def failing_handler(
            update: Update, context: Context, session: Session
        ) -> HandlerResponse:
            raise ValueError("boom")
            yield

        async def value_error_handler(
            update: Update, context: Context, exc: Exception
        ) -> HandlerResponse:
            yield Answer(text="handled")

        exception_handlers_context.bot_data.exception_handlers = [
            (ValueError, value_error_handler)
        ]

        # Mock the session
        mock_session = Mock()
        mock_session.rollback = Mock()
        mock_session.close = Mock()
        exception_handlers_context.bot_data.database_provider.get_session = Mock(
            return_value=mock_session
        )

        wrapper = router.handlers[0][2]

        # Act
        await wrapper(ptb_update, exception_handlers_context)

        # Assert
        mock_session.rollback.assert_called()
        mock_session.close.assert_called()

    async def test_exception_handler_can_use_dependencies(
        self, router, ptb_update, exception_handlers_context
    ):
        """Exception handlers should have access to dependency injection."""

        # Arrange
        @router.command("raise")
        async def failing_handler(update: Update, context: Context) -> HandlerResponse:
            raise ValueError("boom")
            yield

        # A simple dependency
        async def get_answer_text() -> str:
            return "from_dep"

        async def value_error_handler(
            update: Update,
            context: Context,
            exc: Exception,
            text: Annotated[str, Depends(get_answer_text)],
        ) -> HandlerResponse:
            yield Answer(text=text)

        exception_handlers_context.bot_data.exception_handlers = [
            (ValueError, value_error_handler)
        ]

        wrapper = router.handlers[0][2]

        # Act
        await wrapper(ptb_update, exception_handlers_context)

        # Assert
        client = exception_handlers_context.bot_data.bot_client
        assert len(client.sent) == 1
        assert client.sent[0].answer.text == "from_dep"

    async def test_exception_handler_itself_raises(
        self, router, ptb_update, exception_handlers_context, caplog
    ):
        """If the exception handler raises, the new exception should propagate (after logging)."""

        # Arrange
        @router.command("raise")
        async def failing_handler(update: Update, context: Context) -> HandlerResponse:
            raise ValueError("original")
            yield

        async def broken_handler(
            update: Update, context: Context, exc: Exception
        ) -> HandlerResponse:
            raise RuntimeError("handler broke")
            yield

        exception_handlers_context.bot_data.exception_handlers = [
            (ValueError, broken_handler)
        ]

        wrapper = router.handlers[0][2]

        # Act & Assert
        with pytest.raises(RuntimeError, match="handler broke"):
            await wrapper(ptb_update, exception_handlers_context)

        # Ensure the original exception is logged (the framework logs before raising)
        assert "Error handler 'broken_handler' raised an exception" in caplog.text

    async def test_multiple_answers_from_exception_handler(
        self, router, ptb_update, exception_handlers_context
    ):
        """Exception handlers can yield multiple answers, and they are all processed."""

        # Arrange
        @router.command("raise")
        async def failing_handler(update: Update, context: Context) -> HandlerResponse:
            raise ValueError("boom")
            yield

        async def multi_handler(
            update: Update, context: Context, exc: Exception
        ) -> HandlerResponse:
            yield Answer(text="First")
            yield Answer(text="Second")

        exception_handlers_context.bot_data.exception_handlers = [
            (ValueError, multi_handler)
        ]

        wrapper = router.handlers[0][2]

        # Act
        await wrapper(ptb_update, exception_handlers_context)

        # Assert
        client = exception_handlers_context.bot_data.bot_client
        assert len(client.sent) == 2
        assert client.sent[0].answer.text == "First"
        assert client.sent[1].answer.text == "Second"
