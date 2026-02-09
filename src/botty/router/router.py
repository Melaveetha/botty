from collections.abc import Callable
from contextlib import asynccontextmanager
from functools import wraps
from typing import AsyncIterator

from telegram import Update
from telegram.ext import CallbackQueryHandler, CommandHandler

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
                yield answer("Welcome! Use /help for assistance")
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

                yield answer(f"You clicked: {query.data}")
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

    def get_handlers(self):
        """Convert to telegram handlers."""
        telegram_handlers = []
        for handler_type, *args in self.handlers:
            if handler_type == "command":
                telegram_handlers.append(CommandHandler(args[0], args[1]))
            elif handler_type == "callback_query":
                telegram_handlers.append(CallbackQueryHandler(args[1], args[0]))
        return telegram_handlers
