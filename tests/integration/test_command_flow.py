import pytest
from sqlmodel import SQLModel, Field, select

from botty import (
    Router,
    Update,
    Context,
    BaseRepository,
    BaseService,
    Answer,
    HandlerResponse,
    InjectableUser,
)
from botty.testing.helpers import make_command_update
from botty.testing import (
    TestBotClient,
    TestContext,
    TestDatabaseProvider,
    TestMessageRegistry,
    TestDependencyContainer,
)


# -------------------------------------------------------------------
# Models
# -------------------------------------------------------------------
class User(SQLModel, table=True):
    __test__ = False
    id: int | None = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True)
    name: str


# -------------------------------------------------------------------
# Repositories
# -------------------------------------------------------------------
class UserRepository(BaseRepository[User]):
    model = User

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        statement = select(User).where(User.telegram_id == telegram_id)
        return self.session.exec(statement).first()

    def create_from_telegram(self, telegram_id: int, name: str) -> User:
        user = User(telegram_id=telegram_id, name=name)
        return self.create(user)


# -------------------------------------------------------------------
# Services (singleton)
# -------------------------------------------------------------------
class GreetingService(BaseService):
    def __init__(self):
        self.greeting_count = 0

    def get_greeting(self, name: str) -> str:
        self.greeting_count += 1
        return f"Hello {name}! (greeting #{self.greeting_count})"


# -------------------------------------------------------------------
# Handlers
# -------------------------------------------------------------------
router = Router()


@router.command("start")
async def start_handler(
    update: Update,
    context: Context,
    user_repo: UserRepository,
    greeting_svc: GreetingService,
    effective_user: InjectableUser,
) -> HandlerResponse:
    # Get or create user
    user = user_repo.get_by_telegram_id(effective_user.id)
    if not user:
        user = user_repo.create_from_telegram(
            effective_user.id, effective_user.first_name
        )

    # Get personalized greeting from service
    greeting = greeting_svc.get_greeting(user.name)

    yield Answer(text=greeting, message_key="welcome")


# -------------------------------------------------------------------
# Integration Test
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_full_command_flow_with_db():
    # 1. Set up test doubles and context
    db_provider = TestDatabaseProvider()
    bot_client = TestBotClient()
    msg_registry = TestMessageRegistry()
    dep_container = TestDependencyContainer()

    ctx = TestContext()
    ctx.bot_data.database_provider = db_provider
    ctx.bot_data.bot_client = bot_client
    ctx.bot_data.message_registry = msg_registry
    ctx.bot_data.dependency_container = dep_container

    # 2. Create tables (TestDatabaseProvider already does this in __init__, but idempotent)
    db_provider.create_engine()

    # 3. Create a PTB update representing a /start command from user 123
    ptb_update = make_command_update("start", user_id=123, chat_id=456)

    # 4. Get the wrapped handler function from the router
    wrapper = router.handlers[0][2]  # assuming only one handler

    # 5. Execute the handler
    await wrapper(ptb_update, ctx)

    # 6. Assertions
    # a) One message should have been sent
    assert len(bot_client.sent) == 1
    sent = bot_client.sent[0]
    assert sent.method == "send"
    assert sent.chat_id == 456
    assert sent.answer.text == "Hello Test! (greeting #1)"  # ty: ignore

    # b) The message should be registered with the correct key
    record = msg_registry.get_by_key("welcome")
    assert record is not None
    assert record.handler_name == "start_handler"
    assert record.chat_id == 456
    assert record.message_id == sent.message_id

    # c) Database: user should have been created
    with db_provider.get_session() as session:
        user = session.exec(select(User).where(User.telegram_id == 123)).first()
        assert user is not None
        assert user.name == "Test"  # from make_command_update default first_name

    # d) Verify service is a singleton by calling again with another user
    ptb_update2 = make_command_update("start", user_id=124, chat_id=457)
    await wrapper(ptb_update2, ctx)

    assert len(bot_client.sent) == 2
    sent2 = bot_client.sent[1]
    # The greeting count should have increased to 2
    assert sent2.answer.text == "Hello Test! (greeting #2)"  # ty: ignore

    # e) Check that the second user was also created
    with db_provider.get_session() as session:
        user2 = session.exec(select(User).where(User.telegram_id == 124)).first()
        assert user2 is not None
