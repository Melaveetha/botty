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
        async def get_current_user(user_repo: UserRepository) -> User:
            ...

        CurrentUser = Annotated[User, Depends(get_current_user)]
        ```
    """

    def __init__(self, dependency: Dependency, *, use_cache: bool = True):
        self.dependency = dependency
        self.use_cache = use_cache
