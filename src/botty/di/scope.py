from typing import Any

from sqlmodel import Session

from ..context import ContextProtocol
from ..database import DatabaseProvider
from ..domain import Update
from ..exceptions import DatabaseNotConfiguredError
from .markers import Dependency, Depends


class RequestScope:
    def __init__(self, update: Update, context: ContextProtocol):
        self.update = update
        self.context = context
        self.cache: dict = {}
        self._session: Session | None = None
        self._session_closed = False
        self._provider: DatabaseProvider | None = context.bot_data.database_provider

    @property
    def session(self) -> Session:
        """Lazy session creation."""
        if self._provider is None:
            raise DatabaseNotConfiguredError(dependency_name="Session")
        if self._session is None:
            self._session = self._provider.get_session()
        return self._session

    def close(self):
        """Close session if created."""
        if self._session is not None:
            self._session.close()
            self._session_closed = True

    def to_dict(self) -> dict[str, Any]:
        return {"update": self.update, "context": self.context}

    def get_dependency(self, dep: Depends) -> Any:
        if dep.use_cache and dep.dependency in self.cache:
            return self.cache[dep.dependency]
        return None

    def cache_dependency(self, cls: Dependency, dependency: Any):
        self.cache[cls] = dependency

    def __del__(self):
        if self._session and not self._session_closed:
            self._session.close()
