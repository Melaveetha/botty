import pytest
from datetime import datetime, UTC

from botty import (
    Update,
    EffectiveUser,
    EffectiveChat,
    EffectiveMessage,
    CallbackQuery,
    EditedMessage,
    Poll,
    PollAnswer,
    Answer,
    HandlerResponse,
)
from botty.context import ContextProtocol, ConversationData
from botty.di import DependencyResolver, RequestScope
from botty.exceptions import (
    DependencyResolutionError,
)
from botty.helpers import (
    InjectableUser,
    InjectableChat,
    InjectableMessage,
    InjectableCallbackQuery,
    InjectableEditedMessage,
    InjectablePoll,
    InjectablePollAnswer,
    ConversationState,
)
from botty.testing import TestContext


def make_update_with_user(user_id: int = 123) -> Update:
    return Update(
        update_id=1,
        user=EffectiveUser(id=user_id, first_name="Test", username="tester"),
    )


def make_update_with_chat(chat_id: int = 456) -> Update:
    return Update(
        update_id=1,
        chat=EffectiveChat(id=chat_id, type="private"),
    )


def make_update_with_message(chat_id: int = 456, text: str = "Hello") -> Update:
    return Update(
        update_id=1,
        message=EffectiveMessage(
            message_id=789,
            chat_id=chat_id,
            date=datetime.now(UTC),
            text=text,
        ),
    )


async def fake_answer(
    text: str | None = None, show_alert: bool | None = None, url: str | None = None
):
    pass


def make_update_with_callback_query(
    data: str = "button_1", user_id: int = 123, chat_id: int = 456
) -> Update:
    return Update(
        update_id=1,
        callback_query=CallbackQuery(
            id="cb123",
            data=data,
            user_id=user_id,
            message_id=100,
            chat_id=chat_id,
            _answer=fake_answer,  # ty: ignore
        ),
    )


def make_update_with_edited_message(chat_id: int = 456, text: str = "Edited") -> Update:
    return Update(
        update_id=1,
        edited_message=EditedMessage(
            message_id=789,
            chat_id=chat_id,
            date=datetime.now(UTC),
            edit_date=datetime.now(UTC),
            text=text,
        ),
    )


def make_update_with_poll() -> Update:
    return Update(
        update_id=1,
        poll=Poll(
            id="poll123",
            question="Yes or no?",
            options=[],  # simplified
            total_voter_count=0,
            is_closed=False,
            is_anonymous=True,
            type="regular",
            allows_multiple_answers=False,
        ),
    )


def make_update_with_poll_answer(user_id: int = 123) -> Update:
    return Update(
        update_id=1,
        poll_answer=PollAnswer(
            poll_id="poll123",
            user=EffectiveUser(id=user_id, first_name="Test", username="tester"),
            option_ids=[0],
        ),
    )


def make_empty_update() -> Update:
    return Update(update_id=1)


# -------------------------------------------------------------------
# Tests for each helper
# -------------------------------------------------------------------


@pytest.mark.asyncio
class TestInjectableUser:
    async def test_success(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_update_with_user()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, user: InjectableUser
        ) -> HandlerResponse:
            yield Answer("test")

        kwargs = await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        user = kwargs["user"]
        assert isinstance(user, EffectiveUser)
        assert user.id == 123

    async def test_missing(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_empty_update()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, user: InjectableUser
        ):
            pass

        with pytest.raises(DependencyResolutionError) as exc:
            await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        assert "Effective user was not found" in str(exc.value)


@pytest.mark.asyncio
class TestInjectableChat:
    async def test_success(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_update_with_chat()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, chat: InjectableChat
        ):
            return chat

        kwargs = await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        chat = kwargs["chat"]
        assert isinstance(chat, EffectiveChat)
        assert chat.id == 456

    async def test_missing(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_empty_update()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, chat: InjectableChat
        ):
            pass

        with pytest.raises(DependencyResolutionError) as exc:
            await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        assert "Effective chat was not found" in str(exc.value)


@pytest.mark.asyncio
class TestInjectableMessage:
    async def test_success(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_update_with_message()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, msg: InjectableMessage
        ):
            return msg

        kwargs = await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        msg = kwargs["msg"]
        assert isinstance(msg, EffectiveMessage)
        assert msg.message_id == 789
        assert msg.text == "Hello"

    async def test_missing(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_empty_update()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, msg: InjectableMessage
        ):
            pass

        with pytest.raises(DependencyResolutionError) as exc:
            await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        assert "Effective message was not found" in str(exc.value)


@pytest.mark.asyncio
class TestInjectableCallbackQuery:
    async def test_success(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_update_with_callback_query()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, cb: InjectableCallbackQuery
        ):
            return cb

        kwargs = await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        cb = kwargs["cb"]
        assert isinstance(cb, CallbackQuery)
        assert cb.id == "cb123"
        assert cb.data == "button_1"

    async def test_missing(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_empty_update()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, cb: InjectableCallbackQuery
        ):
            pass

        with pytest.raises(DependencyResolutionError) as exc:
            await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        assert "Callback query was not found" in str(exc.value)


@pytest.mark.asyncio
class TestInjectableEditedMessage:
    async def test_success(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_update_with_edited_message()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, em: InjectableEditedMessage
        ):
            return em

        kwargs = await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        em = kwargs["em"]
        assert isinstance(em, EditedMessage)
        assert em.message_id == 789
        assert em.text == "Edited"

    async def test_missing(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_empty_update()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, em: InjectableEditedMessage
        ):
            pass

        with pytest.raises(DependencyResolutionError) as exc:
            await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        assert "EditedMessage was not found" in str(exc.value)


@pytest.mark.asyncio
class TestInjectablePoll:
    async def test_success(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_update_with_poll()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, poll: InjectablePoll
        ):
            return poll

        kwargs = await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        poll = kwargs["poll"]
        assert isinstance(poll, Poll)
        assert poll.id == "poll123"

    async def test_missing(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_empty_update()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, poll: InjectablePoll
        ):
            pass

        with pytest.raises(DependencyResolutionError) as exc:
            await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        assert "Poll was not found" in str(exc.value)


@pytest.mark.asyncio
class TestInjectablePollAnswer:
    async def test_success(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_update_with_poll_answer()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, pa: InjectablePollAnswer
        ):
            return pa

        kwargs = await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        pa = kwargs["pa"]
        assert isinstance(pa, PollAnswer)
        assert pa.poll_id == "poll123"
        assert pa.option_ids == [0]

    async def test_missing(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        update = make_empty_update()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, pa: InjectablePollAnswer
        ):
            pass

        with pytest.raises(DependencyResolutionError) as exc:
            await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        assert "Poll answer was not found" in str(exc.value)


@pytest.mark.asyncio
class TestConversationState:
    async def test_success(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        # Set up conversation data
        test_context.user_data.conversation_data = ConversationData(
            class_name="TestConv",
            step="step1",
            state={"foo": "bar", "counter": 1},
        )

        update = make_empty_update()  # state doesn't depend on update content
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, state: ConversationState
        ):
            return state

        kwargs = await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        state = kwargs["state"]
        assert isinstance(state, dict)
        assert state["foo"] == "bar"
        assert state["counter"] == 1

        # Test mutability – changes should reflect in original
        state["new"] = "value"
        assert test_context.user_data.conversation_data.state["new"] == "value"

    async def test_missing(
        self, resolver: DependencyResolver, test_context: TestContext
    ):
        # No conversation_data set
        test_context.user_data.conversation_data = None

        update = make_empty_update()
        scope = RequestScope(update, test_context)

        async def handler(
            update: Update, context: ContextProtocol, state: ConversationState
        ):
            pass

        with pytest.raises(DependencyResolutionError) as exc:
            await resolver.resolve_handler(handler, scope)  # ty: ignore [invalid-argument-type]
        assert "Conversation was not started" in str(exc.value)
