from typing import Any

from sqlmodel import Session

from ..context import ContextProtocol
from ..database import DatabaseProvider
from ..domain import Update
from ..exceptions import DatabaseNotConfiguredError
from .markers import Dependency, Depends


class RequestScope:
    """Holds state for a single incoming update/request.

    The scope manages:
    - The current Update and Context objects.
    - A request-scoped cache for dependencies.
    - A lazy database session (created on first access).
    - Commit and cleanup of the session after handler execution.

    Attributes:
        update: The domain Update object.
        context: The botty context.
        cache: Dict storing cached dependency results.
    """

    def __init__(self, update: Update, context: ContextProtocol):
        """Initialize the scope with update and context.

        Args:
            update: The domain Update for this request.
            context: The botty context (contains bot_data, etc.).
        """
        self.update = update
        self.context = context
        self.cache: dict = {}
        self._session: Session | None = None
        self._session_closed = False
        self._provider: DatabaseProvider | None = context.bot_data.database_provider

    @property
    def session(self) -> Session:
        """Lazily create and return a database session.

        The session is created from the database provider stored in
        context.bot_data.database_provider. If no provider is configured,
        accessing this property raises DatabaseNotConfiguredError.

        Returns:
            A SQLModel Session.

        Raises:
            DatabaseNotConfiguredError: If no database provider was set.
        """
        if self._provider is None:
            raise DatabaseNotConfiguredError(dependency_name="Session")
        if self._session is None:
            self._session = self._provider.get_session()
        return self._session

    def close(self):
        """Close session if it was created."""
        if self._session is not None:
            self._session.close()
            self._session_closed = True

    def to_dict(self) -> dict[str, Any]:
        return {"update": self.update, "context": self.context}

    def get_dependency(self, dep: Depends) -> Any:
        """Retrieve a cached dependency if it exists and caching is enabled.

        Args:
            dep: The Depends marker.

        Returns:
            The cached value, or None if not cached or caching disabled.
        """
        if dep.use_cache and dep.dependency in self.cache:
            return self.cache[dep.dependency]
        return None

    def cache_dependency(self, cls: Dependency, dependency: Any):
        """Store a dependency result in the scope's cache.

        Args:
            cls: The dependency class/callable used as key.
            dependency: The value to cache.
        """
        self.cache[cls] = dependency

    def commit(self):
        """Commit the current transaction if a session exists."""
        if self._session:
            self._session.commit()

    def __del__(self):
        if self._session and not self._session_closed:
            self._session.close()
