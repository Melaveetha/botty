from collections.abc import AsyncGenerator, Callable
from typing import Any, Protocol, Type, TypeAlias, runtime_checkable

from ..context import Context
from ..classes import Update
from ..handlers import BaseAnswer


class Depends:
    """Marks a parameter as a dependency to be injected."""

    def __init__(self, dependency: Callable | Type, *, use_cache: bool = True):
        self.dependency = dependency
        self.use_cache = use_cache


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
            user_repo: UserRepository,
            effective_user: EffectiveUser
        ) -> HandlerResponse:
            # Do some work
            user = user_repo.get(effective_user.id)

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
