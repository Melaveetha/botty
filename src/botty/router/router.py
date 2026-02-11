from collections.abc import Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncIterator

from telegram import Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    filters,
    MessageHandler,
    MessageReactionHandler,
    InlineQueryHandler,
    PrefixHandler,
)

from ..context import Context
from .dependencies import DependencyResolver
from .response_processor import ResponseProcessor
from .scope import RequestScope
from .typing import Handler
from .validation import validate_handler


class Router:
    """Router with FastAPI-like dependency injection."""

    def __init__(self, name: str | None = None):
        self.name = name or "router"
        self.handlers = []

    @asynccontextmanager
    async def request_scope(
        self, update: Update, context: Context
    ) -> AsyncIterator[RequestScope]:
        """Create a request scope (for database sessions)."""
        scope = RequestScope(update, context)
        try:
            yield scope
        finally:
            scope.close()

    async def _wrap_function(self, func: Callable, update: Update, context: Context):
        resolver = DependencyResolver(context.bot_data.dependency_container)
        processor = ResponseProcessor(context.bot_data.message_registry)
        async with self.request_scope(update, context) as scope:
            kwargs = await resolver.resolve_handler(func, scope)

            generator = func(update, context, **kwargs)
            return await processor.process_async_generator(
                generator, update, context, "handler name"
            )

    def command(self, commands: str | list[str]):
        """
        Decorator for command handlers.

        Args:
            commands: Command name(s) without leading slash (e.g., "start" or ["help", "info"])

        Example:
            ```python
            @router.command("start")
            async def start_handler(
                update: Update,
                context: Context
            ) -> HandlerResponse:
                yield Answer("Welcome! Use /help for assistance")
            ```
        """

        def decorator(
            func: Handler,
        ):
            validate_handler(func, handler_type="command")

            @wraps(func)
            async def wrapper(update: Update, context: Context):
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

        Example:
            ```python
            @router.callback_query(r"^button_")
            async def button_handler(
                update: Update,
                context: Context,
                query: CallbackQuery
            ) -> HandlerResponse:
                await query.answer()  # Acknowledge the callback

                yield Answer(f"You clicked: {query.data}")
            ```
        """

        def decorator(func: Callable):
            validate_handler(func, handler_type="callback_query")

            @wraps(func)
            async def wrapper(update: Update, context: Context):
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

        Example:
            ```python
            @router.message(filters.TEXT)
            async def text_handler(
                update: Update,
                context: Context
            ) -> HandlerResponse:
                yield Answer(f"You said: {update.message.text}")
            ```
        """

        def decorator(func: Callable):
            validate_handler(func, handler_type="message")

            @wraps(func)
            async def wrapper(update: Update, context: Context):
                return await self._wrap_function(func, update, context)

            self.handlers.append(("message", filters_obj, wrapper))
            return wrapper

        return decorator

    def message_reaction(self, filters_obj: filters.BaseFilter | None = None):
        """
        Decorator for message reaction handlers.

        Args:
            filters_obj: Filter to determine which reactions to handle

        Example:
            ```python
            @router.message_reaction()
            async def reaction_handler(
                update: Update,
                context: Context,
                message_reaction: MessageReaction
            ) -> HandlerResponse:
                yield Answer(f"Reaction updated: {message_reaction.new_reaction}")
            ```
        """

        def decorator(func: Callable):
            validate_handler(func, handler_type="message_reaction")

            @wraps(func)
            async def wrapper(update: Update, context: Context):
                return await self._wrap_function(func, update, context)

            self.handlers.append(("message_reaction", filters_obj, wrapper))
            return wrapper

        return decorator

    def inline_query(self, pattern: str | None = None):
        """
        Decorator for inline query handlers.

        Args:
            pattern: Regex pattern to match inline query (optional, handles all if None)

        Example:
            ```python
            @router.inline_query()
            async def inline_handler(
                update: Update,
                context: Context,
                inline_query: InlineQuery
            ) -> HandlerResponse:
                # Build inline query results
                results = [...]
                await inline_query.answer(results)
            ```
        """

        def decorator(func: Callable):
            validate_handler(func, handler_type="inline_query")

            @wraps(func)
            async def wrapper(update: Update, context: Context):
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

        Example:
            ```python
            @router.prefix("!", "help")
            async def help_handler(
                update: Update,
                context: Context
            ) -> HandlerResponse:
                yield Answer("This is help for prefix commands!")
            ```
        """

        def decorator(func: Callable):
            validate_handler(func, handler_type="prefix")

            @wraps(func)
            async def wrapper(update: Update, context: Context):
                return await self._wrap_function(func, update, context)

            if isinstance(commands, str):
                self.handlers.append(("prefix", prefix, commands, wrapper))
            else:
                self.handlers.extend(
                    ("prefix", prefix, command, wrapper) for command in commands
                )
            return wrapper

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
            elif handler_info[0] == "message_reaction":
                handlers.append(
                    MessageReactionHandler(handler_info[1], handler_info[2])
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
