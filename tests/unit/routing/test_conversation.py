from typing import Annotated

import pytest

from botty import (
    Answer,
    BaseRepository,
    Context,
    ConversationState,
    Depends,
    HandlerResponse,
    Router,
    Update,
)
from botty.context import ConversationData
from botty.exceptions import InvalidConversationError
from botty.routing import (
    Conversation,
    ConversationDispatcher,
    ConversationRegistry,
    cancel,
    entry,
    error,
    step,
)
from botty.testing import (
    TestBotClient,
    TestContext,
    TestDependencyContainer,
    TestMessageRegistry,
)
from botty.testing.conversation import ConversationTester
from botty.testing.helpers import make_message_update


class GreetConversation(Conversation):
    @entry
    async def start(self, update: Update, context: Context) -> HandlerResponse:
        yield Answer("What's your name?")
        self.step("ask_age")

    @step
    async def ask_age(
        self, update: Update, context: Context, state: ConversationState
    ) -> HandlerResponse:
        name = update.message.text if update.message else "Unknown"
        state["name"] = name
        yield Answer(f"Hello {name}, how old are you?")
        self.step("farewell")

    @step
    async def farewell(
        self, update: Update, context: Context, state: ConversationState
    ) -> HandlerResponse:
        age = update.message.text if update.message else "?"
        state["age"] = age
        yield Answer(f"Thanks! You are {age} years old. Goodbye!")
        self.end()


class CancelableConversation(Conversation):
    @entry
    async def start(self, update: Update, context: Context) -> HandlerResponse:
        yield Answer("Start")
        self.step("step1")

    @step
    async def step1(self, update: Update, context: Context) -> HandlerResponse:
        yield Answer("Step1")
        self.step("step2")

    @cancel
    async def on_cancel(self, update: Update, context: Context) -> HandlerResponse:
        yield Answer("Canceled!")
        self.end()


class ErrorConversation(Conversation):
    @entry
    async def start(self, update: Update, context: Context) -> HandlerResponse:
        raise ValueError("Boom!")

    @error
    async def handle_error(
        self, update: Update, context: Context, exception: Exception
    ) -> HandlerResponse:
        yield Answer(f"Error caught: {exception}")
        self.end()


class DepsConversation(Conversation):
    @entry
    async def start(
        self,
        update: Update,
        context: Context,
        repo: Annotated[BaseRepository, Depends(lambda: "fake_repo")],
    ) -> HandlerResponse:
        yield Answer(f"Repo: {repo}")


@pytest.fixture
def router():
    return Router(name="test")


@pytest.fixture
def test_context():
    ctx = TestContext()
    ctx.bot_data.dependency_container = TestDependencyContainer()
    ctx.bot_data.message_registry = TestMessageRegistry()
    ctx.bot_data.bot_client = TestBotClient()
    ctx.bot_data.conversation_registry = ConversationRegistry()
    return ctx


def test_conversation_decorator_registers_class(router):
    @router.conversation("test")
    class TestConv(Conversation):
        @entry
        async def start(self, update: Update, context: Context) -> HandlerResponse:
            yield Answer("ok")

    assert len(router.conversations) == 1
    assert router.conversations[0] is TestConv

    assert any(h[0] == "command" and h[1] == "test" for h in router.handlers)


def test_conversation_missing_entry_raises(router):
    with pytest.raises(InvalidConversationError) as exc:

        @router.conversation("test")
        class MissingEntry(Conversation):
            @step
            async def test_step(self):
                pass

    assert "exactly one method decorated with @entry" in str(exc.value)


def test_conversation_multiple_entry_raises(router):
    with pytest.raises(InvalidConversationError) as exc:

        @router.conversation("test")
        class MultiEntry(Conversation):
            @entry
            async def entry1(self):
                pass

            @entry
            async def entry2(self):
                pass

    assert "exactly one method decorated with @entry" in str(exc.value)


def test_conversation_multiple_cancel_raises(router):
    with pytest.raises(InvalidConversationError) as exc:

        @router.conversation("test")
        class MultiCancel(Conversation):
            @entry
            async def start(self):
                pass

            @cancel
            async def cancel1(self):
                pass

            @cancel
            async def cancel2(self):
                pass

    assert "at most one method decorated with @cancel" in str(exc.value)


def test_conversation_multiple_error_raises(router):
    with pytest.raises(InvalidConversationError) as exc:

        @router.conversation("test")
        class MultiError(Conversation):
            @entry
            async def start(self):
                pass

            @error
            async def error1(self):
                pass

            @error
            async def error2(self):
                pass

    assert "at most one method decorated with @error" in str(exc.value)


def test_conversation_invalid_step_signature_raises(router):
    with pytest.raises(InvalidConversationError) as exc:

        @router.conversation("test")
        class BadStep(Conversation):
            @entry
            async def start(self, update: Update, context: Context) -> HandlerResponse:
                yield Answer("test")

            @step
            async def test_step(self, wrong_param):  # missing update, context
                pass

    assert "Invalid step method 'test_step'" in str(exc.value)


@pytest.mark.asyncio
async def test_normal_conversation_flow(router, test_context):
    @router.conversation("greet")
    class TestGreet(GreetConversation):
        pass

    tester = ConversationTester(router, TestGreet, "greet", context=test_context)

    # Start
    await tester.start()
    assert tester.current_step == "ask_age"
    assert len(tester.last_responses) == 1
    assert tester.last_responses[0].answer.text == "What's your name?"

    # First reply
    await tester.send_message("Alice")
    assert tester.current_step == "farewell"
    assert tester.conversation_data["name"] == "Alice"
    assert tester.last_responses[0].answer.text == "Hello Alice, how old are you?"

    # Second reply
    await tester.send_message("30")
    assert tester.current_step is None  # conversation ended
    assert not tester.conversation_data
    assert (
        tester.last_responses[0].answer.text == "Thanks! You are 30 years old. Goodbye!"
    )


@pytest.mark.asyncio
async def test_conversation_data_persistence(router, test_context):
    @router.conversation("data")
    class DataConv(Conversation):
        @entry
        async def start(
            self, update: Update, context: Context, state: ConversationState
        ) -> HandlerResponse:
            state["foo"] = "bar"
            yield Answer("start")
            self.step("next")

        @step
        async def next(
            self, update: Update, context: Context, state: ConversationState
        ) -> HandlerResponse:
            assert state["foo"] == "bar"
            yield Answer("done")
            self.end()

    tester = ConversationTester(router, DataConv, "data", context=test_context)
    await tester.start()
    assert tester.conversation_data["foo"] == "bar"
    await tester.send_message("anything")
    assert tester.current_step is None


@pytest.mark.asyncio
async def test_cancel_command(router, test_context):
    @router.conversation("cancelable", cancel_command="stop")
    class TestCancel(CancelableConversation):
        pass

    tester = ConversationTester(router, TestCancel, "cancelable", context=test_context)
    await tester.start()
    assert tester.current_step == "step1"

    # Send cancel command
    await tester.cancel()  # uses "stop"
    assert tester.current_step is None
    assert len(tester.last_responses) == 1
    assert tester.last_responses[0].answer.text == "Conversation canceled"


@pytest.mark.asyncio
async def test_default_cancel_handler(router, test_context):
    @router.conversation("defaultcancel")
    class NoCancelConv(Conversation):
        @entry
        async def start(self, update: Update, context: Context):
            yield Answer("start")
            self.step("test_step")

        @step
        async def test_step(self, update: Update, context: Context):
            yield Answer("step")
            self.step("test_step")  # loop

    tester = ConversationTester(
        router, NoCancelConv, "defaultcancel", context=test_context
    )
    await tester.start()
    await tester.cancel()  # uses default "cancel"
    assert tester.current_step is None
    assert "Conversation canceled" in tester.last_responses[0].answer.text


@pytest.mark.asyncio
async def test_dependency_injection_in_step(router, test_context):
    def dependency():
        return "real_repo"

    test_context.bot_data.dependency_container.override(dependency, "fake_repo")

    @router.conversation("deps")
    class TestDeps(Conversation):
        @entry
        async def start(
            self,
            update: Update,
            context: Context,
            repo: Annotated[str, Depends(dependency)],
        ) -> HandlerResponse:
            yield Answer(f"repo={repo}")
            self.end()

    tester = ConversationTester(router, TestDeps, "deps", context=test_context)
    await tester.start()
    assert tester.last_responses[0].answer.text == "repo=fake_repo"


@pytest.mark.asyncio
async def test_message_registry_integration(router, test_context):
    @router.conversation("registry")
    class RegConv(Conversation):
        @entry
        async def start(self, update: Update, context: Context):
            yield Answer("first", message_key="key1")
            self.step("next")

        @step
        async def next(self, update: Update, context: Context):
            yield Answer("second", message_key="key2")
            self.end()

    tester = ConversationTester(router, RegConv, "registry", context=test_context)
    await tester.start()

    key1_record = test_context.bot_data.message_registry.get_by_key("key1")
    assert key1_record is not None
    assert key1_record.handler_name == "start"

    await tester.send_message("x")
    key2_record = test_context.bot_data.message_registry.get_by_key("key2")
    assert key2_record is not None
    assert key2_record.handler_name == "next"


@pytest.mark.asyncio
async def test_no_active_conversation_ignored(router, test_context):
    @router.conversation("ignored")
    class IgnoredConv(Conversation):
        @entry
        async def start(self, update: Update, context: Context):
            yield Answer("start")
            self.step("next")

        @step
        async def next(self, update: Update, context: Context):
            yield Answer("next")

    tester = ConversationTester(router, IgnoredConv, "ignored", context=test_context)

    update = make_message_update("hello")
    await tester.dispatcher.handle_update(update, None, None, test_context)  # ty: ignore [invalid-argument-type]
    assert len(test_context.bot_data.bot_client.sent) == 0
    assert test_context.user_data.conversation_data is None


@pytest.mark.asyncio
async def test_conversation_class_not_in_registry(router, test_context):
    test_context.user_data.conversation_data = ConversationData(
        class_name="NonExistent",
        step="start",
        state={},
    )

    update = make_message_update("hello")
    await ConversationDispatcher().handle_update(update, None, None, test_context)  # ty: ignore [invalid-argument-type]
    assert test_context.user_data.conversation_data is None
