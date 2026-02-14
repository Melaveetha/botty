from collections.abc import AsyncGenerator
from typing import Any, Protocol, TypeAlias, runtime_checkable

from ..context import ContextProtocol
from ..domain import Update
from ..responses import BaseAnswer

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
            context: ContextProtocol,
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

    __name__: str

    def __call__(
        self,
        update: Update,
        context: ContextProtocol,
        **kwargs: Any,
    ) -> HandlerResponse:
        """
        Handler function signature.

        Args:
            update: Telegram Update object
            context: Botty ContextProtocol object with bot_data, user_data, etc.
            **kwargs: Injected dependencies (repositories, services, etc.)

        Yields:
            Answer, EditAnswer, or EmptyAnswer objects
        """
        ...


# Type alias for convenience
Handler: TypeAlias = HandlerProtocol
