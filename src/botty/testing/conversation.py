from botty.adapters import PTBIncomingAdapter
from botty.context import ConversationData
from collections.abc import Callable
from typing import Any, Type

from telegram import Update as PTBUpdate
from telegram.ext import ApplicationHandlerStop

from ..di import Dependency
from ..routing import Conversation, ConversationDispatcher, ConversationRegistry, Router
from ..routing.executor import execute_callable
from .bot_client import SentMessage, TestBotClient
from .context import TestContext
from .helpers import make_callback_update, make_command_update, make_message_update
from .registry import TestMessageRegistry
from .scope import TestRequestScope


class ConversationTester:
    """
    Test harness for Botty conversations.

    Example:
        ```python
        tester = ConversationTester(router, MyConversation, command="start")
        await tester.start("/start")

        await tester.send_message("Hello")
        assert tester.current_step == "ask_age"
        assert tester.last_response.text == "How old are you?"

        await tester.send_message("30")
        assert tester.conversation_data["age"] == 30
        assert tester.current_step is None  # conversation ended
        ```
    """

    def __init__(
        self,
        router: Router,
        conversation_class: Type[Conversation],
        command: str,
        context: TestContext | None = None,
        user_id: int = 123,
        chat_id: int = 456,
    ):
        """
        Args:
            router: The router that registered the conversation.
            conversation_class: The conversation class to test.
            command: The command that starts the conversation (without slash).
            context: Optional pre‑configured TestContext. If not given, a fresh one is created.
            user_id: Default user ID to use for updates.
            chat_id: Default chat ID to use for updates.
        """
        self.conversation_class = conversation_class
        self.command = command
        self.user_id = user_id
        self.chat_id = chat_id

        # Set up test context with all necessary doubles
        self.context = context or TestContext()
        self.context.bot_data.bot_client = TestBotClient()
        self.context.bot_data.message_registry = TestMessageRegistry()
        self.context.bot_data.conversation_registry = (
            self.context.bot_data.conversation_registry or ConversationRegistry()
        )
        self.context.bot_data.conversation_registry.register(conversation_class)

        self.dispatcher = ConversationDispatcher()
        self._last_responses: list[SentMessage] = []

        # Locate the command handler from the router
        self._command_handler = self._find_command_handler(router, command)

    async def start(self, args: list[str] | None = None) -> "ConversationTester":
        """
        Simulate the user typing the start command.

        Args:
            args: Optional command arguments (e.g., ["arg1", "arg2"]).
        """
        update = make_command_update(self.command, args, self.user_id, self.chat_id)
        await self._run_command_handler(update)
        return self

    async def send_message(self, text: str) -> "ConversationTester":
        """Simulate a user text message."""
        update = make_message_update(text, self.user_id, self.chat_id)
        await self._run_dispatcher(update)
        return self

    async def send_callback_query(self, data: str) -> "ConversationTester":
        """Simulate a callback query (inline button press)."""
        update = make_callback_update(data, self.user_id, self.chat_id)
        await self._run_dispatcher(update)
        return self

    async def send_any(self, update: PTBUpdate) -> "ConversationTester":
        """Directly pass a custom PTB update for advanced scenarios."""
        await self._run_dispatcher(update)
        return self

    async def cancel(self) -> "ConversationTester":
        """Simulate the user sending the cancel command."""
        update = make_command_update(
            self.conversation_class._cancel_command,
            user_id=self.user_id,
            chat_id=self.chat_id,
        )
        await self._run_dispatcher(update)
        return self

    async def run_step(
        self,
        step_name: str,
        data: dict[str, Any] | None = None,
        deps: dict[Dependency, Any] | None = None,
    ) -> "ConversationTester":
        """
        Directly execute a single step method, bypassing the dispatcher.

        Useful for unit‑testing a step in isolation. The conversation data
        will be temporarily set to `data` (or an empty dict) during the call.

        Args:
            step_name: Name of the step method (e.g., "ask_age").
            data: Optional conversation data to inject.
            deps: Additional dependencies to override (e.g., {"repo": Mock()}).
        """
        if data is not None:
            self._set_conversation_data(step_name, data)

        scope = self._build_scope(update=None, deps=deps)

        instance = self.conversation_class()
        method = getattr(instance, step_name)

        await execute_callable(method, scope, step_name, instance)

        self._update_state_from_instance(instance)

        self._capture_responses()
        return self

    @property
    def current_step(self) -> str | None:
        """Name of the current step, or None if conversation is not active."""
        if self.context.user_data.conversation_data is None:
            return None
        return self.context.user_data.conversation_data.step

    @property
    def conversation_data(self) -> dict[str, Any]:
        """The data dict stored in user_data for the active conversation."""
        if self.context.user_data.conversation_data is None:
            return {}
        return self.context.user_data.conversation_data.state

    @property
    def last_responses(self) -> list[SentMessage]:
        """Responses sent during the most recent step execution."""
        return self._last_responses

    @property
    def all_responses(self) -> list[SentMessage]:
        """All responses sent so far (cumulative)."""
        return self.context.bot_data.bot_client.sent  # ty: ignore [possibly-missing-attribute]

    def _find_command_handler(self, router: Router, command: str) -> Callable:
        """Extract the command callback from router.handlers."""
        for handler_info in router.handlers:
            if handler_info[0] == "command" and handler_info[1] == command:
                return handler_info[2]
        raise ValueError(f"Command '/{command}' not found in router")

    async def _run_command_handler(self, update: PTBUpdate) -> None:
        """Invoke the command handler that starts the conversation."""
        try:
            await self._command_handler(update, self.context)
        except ApplicationHandlerStop:
            pass
        self._capture_responses()

    async def _run_dispatcher(self, update: PTBUpdate) -> None:
        """Let the ConversationDispatcher process an update."""
        self._last_responses = []
        self.context.bot_data.bot_client.clear()  # ty: ignore [possibly-missing-attribute]

        try:
            await self.dispatcher.handle_update(
                update=update,
                application=None,  # ty: ignore [invalid-argument-type]
                check_result=None,
                context=self.context,
            )
        except ApplicationHandlerStop:
            pass
        self._capture_responses()

    def _capture_responses(self) -> None:
        """Copy the bot client's sent messages into _last_responses."""
        self._last_responses = list(self.context.bot_data.bot_client.sent)  # ty: ignore [possibly-missing-attribute]

    def _set_conversation_data(self, step: str, data: dict[str, Any]) -> None:
        """Manually set user_data.conversation_data."""
        self.context.user_data.conversation_data = ConversationData(
            class_name=self.conversation_class.__name__,
            step=step,
            state=data.copy(),
        )

    def _update_state_from_instance(self, instance: Conversation) -> None:
        """After a step runs, update user_data based on instance._next_step."""
        if instance._next_step is None:
            self.context.user_data.conversation_data = None
        else:
            if self.context.user_data.conversation_data is None:
                self._set_conversation_data(instance._next_step, {})
            else:
                self.context.user_data.conversation_data.step = instance._next_step

    def _build_scope(
        self,
        update: PTBUpdate | None,
        deps: dict[Dependency, Any] | None,
    ) -> TestRequestScope:
        """Build a TestRequestScope with optional dependency overrides."""
        domain_update = PTBIncomingAdapter.from_ptb(update or make_message_update(""))

        scope = TestRequestScope(
            update=domain_update,
            context=self.context,
            session=None,
            bot_client=self.context.bot_data.bot_client,
            message_registry=self.context.bot_data.message_registry,
            overrides=deps,
        )
        return scope
