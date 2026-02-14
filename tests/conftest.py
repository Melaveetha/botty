# tests/conftest.py
from botty import Router
from datetime import UTC, datetime

import pytest

from telegram import Update as PTBUpdate

from botty.domain import EffectiveChat, EffectiveMessage, EffectiveUser, Update, Message
from botty.di import DependencyContainer, DependencyResolver, RequestScope
from botty.testing import (
    TestContext,
    TestDatabaseProvider,
    TestRequestScope,
    TestBotClient,
    TestMessageRegistry,
    TestDependencyContainer,
)


@pytest.fixture
def container():
    """Fresh DependencyContainer per test (singleton cache is empty)."""
    return DependencyContainer()


@pytest.fixture
def db_provider():
    """In-memory SQLite provider with clean tables."""
    return TestDatabaseProvider()


@pytest.fixture
def session(db_provider):
    """Request-scoped session from the test provider."""
    return db_provider.get_session()


@pytest.fixture
def test_context(db_provider):
    """Context with bot_data containing the database provider."""
    ctx = TestContext()
    ctx.bot_data.database_provider = db_provider
    return ctx


@pytest.fixture
def sample_update():
    """Minimal Update object for injection tests."""
    return Update(
        update_id=1,
        user=EffectiveUser(id=123, first_name="Test", username="tester"),
        chat=EffectiveChat(id=456, type="private"),
        message=EffectiveMessage(
            message_id=789, chat_id=456, date=datetime.now(UTC), text="/start"
        ),
    )


@pytest.fixture
def request_scope(sample_update, test_context):
    """Real RequestScope (uses provider from context)."""
    return RequestScope(sample_update, test_context)


@pytest.fixture
def test_request_scope(sample_update, test_context, session):
    """TestRequestScope with explicit session override."""
    return TestRequestScope(update=sample_update, context=test_context, session=session)


@pytest.fixture
def resolver(container):
    return DependencyResolver(container)


@pytest.fixture
def test_bot_client() -> TestBotClient:
    """A TestBotClient instance."""
    return TestBotClient()


@pytest.fixture
def test_message_registry() -> TestMessageRegistry:
    """A TestMessageRegistry instance."""
    return TestMessageRegistry()


@pytest.fixture
def test_dependency_container() -> TestDependencyContainer:
    """A TestDependencyContainer instance."""
    return TestDependencyContainer()


@pytest.fixture
def test_db_provider() -> TestDatabaseProvider:
    """An in‑memory database provider."""
    return TestDatabaseProvider()


@pytest.fixture
def router() -> Router:
    """A fresh Router instance."""
    return Router(name="test_router")


@pytest.fixture
def test_context_with_doubles(
    test_bot_client,
    test_message_registry,
    test_dependency_container,
    test_db_provider,
) -> TestContext:
    """A TestContext with bot_data fully configured with test doubles."""
    ctx = TestContext()
    ctx.bot_data.bot_client = test_bot_client
    ctx.bot_data.message_registry = test_message_registry
    ctx.bot_data.dependency_container = test_dependency_container
    ctx.bot_data.database_provider = test_db_provider
    return ctx


@pytest.fixture
def ptb_update() -> PTBUpdate:
    """A minimal PTB Update object (with a message)."""
    from datetime import datetime
    from telegram import Chat, Message, User

    user = User(id=123, first_name="Test", is_bot=False)
    chat = Chat(id=456, type="private")
    message = Message(
        message_id=789,
        date=datetime.now(),
        chat=chat,
        text="/start",
        from_user=user,
    )
    return PTBUpdate(update_id=1, message=message)


@pytest.fixture
def message_registry() -> TestMessageRegistry:
    """A TestMessageRegistry instance with default settings."""
    return TestMessageRegistry(max_messages_per_chat=3)


@pytest.fixture
def sample_message() -> Message:
    """Create a sample domain Message."""
    return Message(message_id=100, chat_id=123, date=datetime.now())
