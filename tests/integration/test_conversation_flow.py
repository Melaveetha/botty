import pytest
from sqlmodel import SQLModel, Field, select

from botty import (
    Router,
    Update,
    Context,
    BaseRepository,
    Answer,
    HandlerResponse,
    Conversation,
    entry,
    step,
    cancel,
    error,
    ConversationState,
    InjectableUser,
)
from botty.testing import (
    TestBotClient,
    TestContext,
    TestDatabaseProvider,
    TestMessageRegistry,
    TestDependencyContainer,
    ConversationTester,
)


# -------------------------------------------------------------------
# Models
# -------------------------------------------------------------------
class ConversationUser(SQLModel, table=True):
    __test__ = False
    id: int | None = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True)
    name: str
    age: int | None = None


# -------------------------------------------------------------------
# Repository
# -------------------------------------------------------------------
class UserRepository(BaseRepository[ConversationUser]):
    model = ConversationUser

    def get_by_telegram_id(self, telegram_id: int) -> ConversationUser | None:
        statement = select(ConversationUser).where(
            ConversationUser.telegram_id == telegram_id
        )
        return self.session.exec(statement).first()

    def create(self, telegram_id: int, name: str) -> ConversationUser:  # ty: ignore
        user = ConversationUser(telegram_id=telegram_id, name=name)
        result = super().create(user)
        self.commit()
        return result

    def update_age(self, user: ConversationUser, age: int) -> ConversationUser:
        user.age = age
        result = self.update(user)
        self.commit()
        return result


# -------------------------------------------------------------------
# Conversation
# -------------------------------------------------------------------
router = Router("TestConversations")


@router.conversation("register", cancel_command="stop")
class RegisterConversation(Conversation):
    @entry
    async def start(
        self, update: Update, context: Context, state: ConversationState
    ) -> HandlerResponse:
        yield Answer("Welcome! What's your name?")
        self.step("ask_age")

    @step
    async def ask_age(
        self,
        update: Update,
        context: Context,
        state: ConversationState,
        user_repo: UserRepository,
        user: InjectableUser,
    ) -> HandlerResponse:
        name = update.message.text if update.message else "Unknown"
        state["name"] = name

        # Store user in DB (will be rolled back if something fails later)
        user = user_repo.create(user.id, name)  # ty: ignore
        state["user_id"] = user.id

        yield Answer(f"Nice to meet you, {name}! How old are you?")
        self.step("farewell")

    @step
    async def farewell(
        self,
        update: Update,
        context: Context,
        state: ConversationState,
        user_repo: UserRepository,
    ) -> HandlerResponse:
        age_text = update.message.text if update.message else "0"
        try:
            age = int(age_text)  # ty: ignore
        except ValueError:
            yield Answer("That doesn't look like a number. Please try again.")
            self.step("farewell")  # repeat the age step
            return

        state["age"] = age

        # Update user age in DB
        user = user_repo.get(state["user_id"])
        if user:
            user_repo.update_age(user, age)

        yield Answer(f"Thank you! You are {age} years old. Goodbye!")
        self.end()

    @cancel
    async def on_cancel(self, update: Update, context: Context) -> HandlerResponse:
        yield Answer("Registration cancelled.")
        # Ensure conversation state cleared
        self.end()

    @error
    async def on_error(
        self, update: Update, context: Context, exception: Exception
    ) -> HandlerResponse:
        yield Answer("Sorry, something went wrong. Please try again later.")
        self.end()


# -------------------------------------------------------------------
# Fixture for fully configured test context
# -------------------------------------------------------------------
@pytest.fixture
def conversation_test_context():
    db_provider = TestDatabaseProvider()
    bot_client = TestBotClient()
    msg_registry = TestMessageRegistry()
    dep_container = TestDependencyContainer()

    # We'll override the dependency in the test if needed

    ctx = TestContext()
    ctx.bot_data.database_provider = db_provider
    ctx.bot_data.bot_client = bot_client
    ctx.bot_data.message_registry = msg_registry
    ctx.bot_data.dependency_container = dep_container

    # Create tables
    db_provider.create_engine()

    return ctx, db_provider, bot_client, msg_registry, dep_container


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------
@pytest.mark.asyncio
async def test_conversation_normal_flow(conversation_test_context):
    ctx, db_provider, bot_client, msg_registry, dep_container = (
        conversation_test_context
    )

    # Create tester
    tester = ConversationTester(
        router, RegisterConversation, "register", context=ctx, user_id=1, chat_id=456
    )

    # Start conversation
    await tester.start()
    assert tester.current_step == "ask_age"
    assert len(tester.last_responses) == 1
    assert tester.last_responses[0].answer.text == "Welcome! What's your name?"  # ty: ignore

    # Send name
    await tester.send_message("Alice")
    assert tester.current_step == "farewell"
    assert tester.conversation_data["name"] == "Alice"
    assert (
        tester.last_responses[0].answer.text  # ty: ignore
        == "Nice to meet you, Alice! How old are you?"
    )

    # Send age
    await tester.send_message("30")
    assert tester.current_step is None  # conversation ended
    assert (
        tester.last_responses[0].answer.text
        == "Thank you! You are 30 years old. Goodbye!"
    )

    # Verify database: user created with correct age
    with db_provider.get_session() as session:
        user = session.exec(
            select(ConversationUser).where(ConversationUser.telegram_id == 1)
        ).first()
        assert user is not None
        assert user.name == "Alice"
        assert user.age == 30


@pytest.mark.asyncio
async def test_conversation_cancel(conversation_test_context):
    ctx, db_provider, bot_client, msg_registry, dep_container = (
        conversation_test_context
    )

    tester = ConversationTester(
        router, RegisterConversation, "register", context=ctx, user_id=2, chat_id=456
    )

    # Start conversation
    await tester.start()
    assert tester.current_step == "ask_age"

    # Cancel using the custom cancel command ("stop")
    await tester.cancel()  # this uses the conversation's cancel_command
    assert tester.current_step is None
    assert tester.last_responses[0].answer.text == "Registration cancelled."

    # Verify no user was created (since we didn't complete)
    with db_provider.get_session() as session:
        users = session.exec(select(ConversationUser)).all()
        assert len(users) == 0


@pytest.mark.asyncio
async def test_conversation_invalid_age_retry(conversation_test_context):
    ctx, db_provider, bot_client, msg_registry, dep_container = (
        conversation_test_context
    )

    tester = ConversationTester(
        router, RegisterConversation, "register", context=ctx, user_id=3, chat_id=456
    )

    await tester.start()
    await tester.send_message("Alice")
    assert tester.current_step == "farewell"

    # Send invalid age
    await tester.send_message("thirty")
    assert tester.current_step == "farewell"  # should go back to farewell
    assert "doesn't look like a number" in tester.last_responses[0].answer.text  # ty: ignore

    # Now send valid age
    await tester.send_message("30")
    assert tester.current_step is None
    assert (
        tester.last_responses[0].answer.text
        == "Thank you! You are 30 years old. Goodbye!"
    )

    # Verify user created with age 30
    with db_provider.get_session() as session:
        user = session.exec(
            select(ConversationUser).where(ConversationUser.telegram_id == 3)
        ).first()
        assert user.age == 30


@pytest.mark.asyncio
async def test_conversation_dependency_injection(conversation_test_context):
    """Verify that dependencies (like UserRepository) are correctly injected into steps."""
    ctx, db_provider, bot_client, msg_registry, dep_container = (
        conversation_test_context
    )

    # We can't directly inspect the injected repo, but we can verify its effects
    tester = ConversationTester(
        router, RegisterConversation, "register", context=ctx, user_id=5, chat_id=456
    )

    await tester.start()
    await tester.send_message("Alice")  # creates user
    await tester.send_message("30")  # updates age

    # Verify user exists and age set
    with db_provider.get_session() as session:
        user = session.exec(
            select(ConversationUser).where(ConversationUser.telegram_id == 5)
        ).first()
        assert user is not None
        assert user.name == "Alice"
        assert user.age == 30


@pytest.mark.asyncio
async def test_conversation_state_persistence_across_steps(conversation_test_context):
    """State dictionary should persist data between steps."""
    ctx, db_provider, bot_client, msg_registry, dep_container = (
        conversation_test_context
    )

    tester = ConversationTester(
        router, RegisterConversation, "register", context=ctx, user_id=6, chat_id=456
    )

    await tester.start()
    # The state is empty initially
    assert tester.conversation_data == {}

    await tester.send_message("Alice")
    assert tester.conversation_data["name"] == "Alice"
    assert "user_id" in tester.conversation_data

    await tester.send_message("30")
    assert tester.conversation_data == {}
    assert tester.current_step is None
