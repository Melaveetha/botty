from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncIterator

from telegram import Update as PTBUpdate
from telegram.ext import (
    ApplicationHandlerStop,
    CallbackQueryHandler,
    CommandHandler,
    InlineQueryHandler,
    MessageHandler,
    PrefixHandler,
    filters,
)

from ..adapters import PTBIncomingAdapter
from ..context import ContextProtocol, ConversationData
from ..di import Handler, HandlerResponse, RequestScope
from ..domain import Update
from ..exceptions import InvalidConversationError, InvalidHandlerError
from .conversation import Conversation, iterate_steps
from .dispatcher import _run_conversation_step
from .executor import execute_callable
from .validation import validate_at_most_one, validate_exactly_one, validate_handler


class Router:
    """Router that collects handlers and converts them to PTB handlers.

    Provides decorators for common update types (command, callback_query,
    message, inline_query, prefix) with automatic dependency injection
    and response processing.

    Example:
        ```python
        router = Router()

        @router.command("start")
        async def start(update: Update, context: Context) -> HandlerResponse:
            yield Answer("Hello!")

        @router.callback_query("^data")
        async def handle_callback(update: Update, context: Context,
                                   callback_query: CallbackQuery) -> HandlerResponse:
            await callback_query.answer()
            yield Answer("Callback handled")
        ```
    """

    def __init__(self, name: str | None = None):
        """Create a new router.

        Args:
            name: Optional name for the router (used in logs).
        """
        self.name = name or "router"
        # Add group
        self.handlers = []
        self.conversations = []
        self.incoming_adapter = PTBIncomingAdapter()

    @asynccontextmanager
    async def request_scope(
        self, update: Update, context: ContextProtocol
    ) -> AsyncIterator[RequestScope]:
        """Create a request scope for the duration of handler execution.

        Yields a scope that manages the database session and dependency cache.
        The session is automatically committed on success and closed afterwards.
        """
        scope = RequestScope(update, context)
        try:
            yield scope
            scope.commit()
        finally:
            scope.close()

    async def _wrap_function(
        self, func: Handler, tg_update: PTBUpdate, context: ContextProtocol
    ):
        """Internal wrapper that resolves dependencies, executes the handler,
        and processes its responses.
        """
        handler_name: str = func.__name__
        update = self.incoming_adapter.from_ptb(tg_update)
        async with self.request_scope(update, context) as scope:
            await execute_callable(func, scope, handler_name)

    def command(self, commands: str | list[str]):
        """
        Decorator for command handlers.

        Args:
            commands: Command name(s) without leading slash (e.g., "start" or ["help", "info"])

        Raises:
            InvalidHandlerError: If the decorated function does not match the required handler signature (async generator with at least `update` and `context` parameters).

        Example:
            ```python
            @router.command("start")
            async def start_handler(
                update: Update,
                context: ContextProtocol
            ) -> HandlerResponse:
                yield Answer("Welcome! Use /help for assistance")
            ```
        """

        def decorator(
            func: Handler,
        ):
            validate_handler(func, handler_type="command")

            @wraps(func)
            async def wrapper(update: PTBUpdate, context: ContextProtocol):
                return await self._wrap_function(func, update, context)

            if isinstance(commands, str):
                self.handlers.append(("command", commands, wrapper))
            else:
                self.handlers.extend(
                    ("command", command, wrapper) for command in commands
                )
            return wrapper

        return decorator

    def callback_query(self, pattern: str):
        """
        Decorator for callback_query handlers.

        Args:
            pattern: Regex pattern to match callback data


        Raises:
            InvalidHandlerError: If the decorated function does not match the required handler signature (async generator with at least `update` and `context` parameters).

        Example:
            ```python
            @router.callback_query(r"^button_")
            async def button_handler(
                update: Update,
                context: ContextProtocol,
                query: CallbackQuery
            ) -> HandlerResponse:
                await query.answer()  # Acknowledge the callback

                yield Answer(f"You clicked: {query.data}")
            ```
        """

        def decorator(func: Handler):
            validate_handler(func, handler_type="callback_query")

            @wraps(func)
            async def wrapper(update: PTBUpdate, context: ContextProtocol):
                return await self._wrap_function(func, update, context)

            self.handlers.append(("callback_query", pattern, wrapper))
            return wrapper

        return decorator

    def message(self, filters_obj: filters.BaseFilter | None = None):
        """
        Decorator for message handlers.

        Args:
            filters_obj: Filter to determine which messages to handle
                        (e.g., filters.TEXT, filters.PHOTO, filters.VIDEO)

        Raises:
            InvalidHandlerError: If the decorated function does not match the required handler signature (async generator with at least `update` and `context` parameters).

        Example:
            ```python
            @router.message(filters.TEXT)
            async def text_handler(
                update: Update,
                context: ContextProtocol
            ) -> HandlerResponse:
                yield Answer(f"You said: {update.message.text}")
            ```
        """

        def decorator(func: Handler):
            validate_handler(func, handler_type="message")

            @wraps(func)
            async def wrapper(update: PTBUpdate, context: ContextProtocol):
                return await self._wrap_function(func, update, context)

            self.handlers.append(("message", filters_obj, wrapper))
            return wrapper

        return decorator

    def inline_query(self, pattern: str | None = None):
        """
        Decorator for inline query handlers.

        Args:
            pattern: Regex pattern to match inline query (optional, handles all if None)

        Raises:
            InvalidHandlerError: If the decorated function does not match the required handler signature (async generator with at least `update` and `context` parameters).

        Example:
            ```python
            @router.inline_query()
            async def inline_handler(
                update: Update,
                context: ContextProtocol,
                inline_query: InlineQuery
            ) -> HandlerResponse:
                # Build inline query results
                results = [...]
                await inline_query.answer(results)
            ```
        """

        def decorator(func: Handler):
            validate_handler(func, handler_type="inline_query")

            @wraps(func)
            async def wrapper(update: PTBUpdate, context: ContextProtocol):
                return await self._wrap_function(func, update, context)

            self.handlers.append(("inline_query", pattern, wrapper))
            return wrapper

        return decorator

    def prefix(self, prefix: str, commands: str | list[str]):
        """
        Decorator for prefix-based command handlers.

        Args:
            prefix: The prefix to use (e.g., "!", "#", "@")
            commands: Command name(s) without the prefix (e.g., "help" or ["help", "info"])

        Raises:
            InvalidHandlerError: If the decorated function does not match the required handler signature (async generator with at least `update` and `context` parameters).

        Example:
            ```python
            @router.prefix("!", "help")
            async def help_handler(
                update: Update,
                context: ContextProtocol
            ) -> HandlerResponse:
                yield Answer("This is help for prefix commands!")
            ```
        """

        def decorator(func: Handler):
            validate_handler(func, handler_type="prefix")

            @wraps(func)
            async def wrapper(update: PTBUpdate, context: ContextProtocol):
                return await self._wrap_function(func, update, context)

            if isinstance(commands, str):
                self.handlers.append(("prefix", prefix, commands, wrapper))
            else:
                self.handlers.extend(
                    ("prefix", prefix, command, wrapper) for command in commands
                )
            return wrapper

        return decorator

    def conversation(self, command: str | list[str], cancel_command: str = "cancel"):
        """
        Decorator that registers a conversation class and creates a command handler
        to start the conversation.

        When the command is issued, any currently active conversation for that user
        is overwritten and a new conversation begins. There is no automatic
        resumption of a previous conversation.

        Args:
            command: The command name (without slash) that triggers the conversation.
            cancel_command: The command name (without slash) that triggers the cancellation of this conversation (Default is `cancel`).

        Raises:
            InvalidConversationError: If the class does not meet the conversation requirements (exactly one `@entry`, at most one `@cancel` and one `@error`).

        The decorated class must:
            - Inherit from Conversation (optional but recommended).
            - Have exactly one method marked with @entry.
            - Have at most one method marked with @cancel.
            - Have at most one method marked with @error.

        Example:
            @router.conversation("register")
            class RegisterConversation(Conversation):
                @entry
                async def start(self, update: Update, context: Context) -> HandlerResponse:
                    yield Answer("Welcome! What's your name?")
                    self.step("ask_age")
                    return
        """

        def decorator(cls: type[Conversation]) -> type[Conversation]:
            entry_step = validate_exactly_one(cls, "_is_entry", "entry")
            validate_at_most_one(cls, "_is_cancel", "cancel")
            validate_at_most_one(cls, "_is_error", "error")

            # Validate step methods
            for name, method in iterate_steps(cls):
                if getattr(method, "_is_step", False):
                    try:
                        validate_handler(
                            method, handler_type="conversation_step", skip_params=1
                        )
                    except InvalidHandlerError as e:
                        raise InvalidConversationError(
                            message=f"Invalid step method '{name}' in conversation '{cls.__name__}': {e.message}",
                            class_name=cls.__name__,
                            method_name=name,
                            suggestion=e.suggestion,
                        ) from e

            cls._cancel_command = cancel_command
            self.conversations.append(cls)

            async def command_callback(
                update: PTBUpdate, context: ContextProtocol
            ) -> HandlerResponse:
                context.user_data.conversation_data = ConversationData(
                    cls.__name__, entry_step, dict()
                )
                await _run_conversation_step(cls, entry_step, update, context)
                raise ApplicationHandlerStop()

            if isinstance(command, list):
                self.handlers.extend(
                    ("command", cmd, command_callback) for cmd in command
                )
            else:
                self.handlers.append(("command", command, command_callback))

            return cls

        return decorator

    def get_handlers(self):
        """Convert to telegram handlers."""
        handlers = []
        for handler_info in self.handlers:
            if handler_info[0] == "command":
                handlers.append(CommandHandler(handler_info[1], handler_info[2]))
            elif handler_info[0] == "callback_query":
                handlers.append(
                    CallbackQueryHandler(handler_info[2], pattern=handler_info[1])
                )
            elif handler_info[0] == "message":
                handlers.append(
                    MessageHandler(handler_info[1] or filters.ALL, handler_info[2])
                )
            elif handler_info[0] == "inline_query":
                handlers.append(
                    InlineQueryHandler(handler_info[2], pattern=handler_info[1])
                )
            elif handler_info[0] == "prefix":
                # Custom handler needed – suggest creating a PrefixCommandHandler
                handlers.append(
                    PrefixHandler(handler_info[1], handler_info[2], handler_info[3])
                )
        return handlers
