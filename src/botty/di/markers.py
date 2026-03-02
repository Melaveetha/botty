from collections.abc import Callable
from typing import Type, TypeAlias

Dependency: TypeAlias = Callable | Type


class Depends:
    """Marker for dependency injection.

    Used in Annotated type hints to indicate that a parameter should be
    injected by calling the provided dependency callable.

    Args:
        dependency: A callable (function or class) that returns the value
                    to be injected.
        use_cache: If True (default), the result is cached within the same
                   request scope. If False, the dependency is recomputed
                   every time it is requested.

    Example:
        ```python
        # Simple dependency
        async def get_db_session(update: Update, context: Context) -> Session:
            ...

        # Nested dependency: get_current_user depends on get_db_session
        async def get_current_user(..., session: Annotated[Session, Depends(get_db_session)]) -> User:
            ...

        # Use in handler
        @router.command("profile")
        async def profile_handler(
            update: Update,
            context: Context,
            user: Annotated[User, Depends(get_current_user)]
        ) -> HandlerResponse:
            yield Answer(f"Hello {user.name}!")
        ```

    When `use_cache=True` (default), the same User instance will be injected
    everywhere `get_current_user` is requested within the same request scope.
    Set `use_cache=False` if you need a fresh value each time (e.g., a random
    number or timestamp).
    """

    def __init__(self, dependency: Dependency, *, use_cache: bool = True):
        self.dependency = dependency
        self.use_cache = use_cache
