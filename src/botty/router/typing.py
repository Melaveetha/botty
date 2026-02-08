from collections.abc import AsyncGenerator, Callable
from typing import Any, Protocol, Type, TypeAlias, runtime_checkable

from telegram import Update

from ..context import Context
from .handlers import BaseAnswer


class Depends:
    """Marks a parameter as a dependency to be injected."""

    def __init__(self, dependency: Callable | Type, *, use_cache: bool = True):
        self.dependency = dependency
        self.use_cache = use_cache
        self._cache = {}

    def __call__(self, dependency: Callable) -> "Depends":
        """Allow using @Depends() as decorator."""
        self.dependency = dependency
        return self


# Type alias for the handler return type
HandlerResponse: TypeAlias = AsyncGenerator[BaseAnswer, None]


@runtime_checkable
class HandlerProtocol(Protocol):
    """
    Protocol for handler functions.

    Handlers must be async generators that yield Answer objects.

    Example:
        ```python
        async def my_handler(
            update: Update,
            context: Context,
            user_repo: UserRepository
        ) -> HandlerResponse:
            # Do some work
            user = user_repo.get(update.effective_user.id)

            # Yield responses
            yield Answer(text=f"Hello {user.name}!")
            yield Answer(text="Here's more info...")
        ```
    """

    async def __call__(
        self,
        update: Update,
        context: Context,
        **kwargs: Any,
    ) -> HandlerResponse:
        """
        Handler function signature.

        Args:
            update: Telegram Update object
            context: Botty Context object with bot_data, user_data, etc.
            **kwargs: Injected dependencies (repositories, services, etc.)

        Yields:
            Answer, EditAnswer, or EmptyAnswer objects
        """
        ...


# Type alias for convenience
Handler: TypeAlias = HandlerProtocol
