from collections.abc import Callable
from .typing import Depends
from typing import Any, Type
from sqlmodel import Session
from ..context import Context
from ..database import DatabaseProvider
from telegram import Update


class RequestScope:
    def __init__(self, update: Update, context: Context):
        self.update = update
        self.context = context
        self.cache: dict = {}
        self._session: Session | None = None
        self._provider: DatabaseProvider = context.bot_data.database_provider

    @property
    def session(self) -> Session:
        """Lazy session creation."""
        if self._session is None:
            self._session = self._provider.get_session()
        return self._session

    def close(self):
        """Close session if created."""
        if self._session is not None:
            self._session.close()

    def to_dict(self) -> dict[str, Any]:
        return {"update": self.update, "context": self.context}

    def get_dependency(self, dep: Depends) -> Any:
        if dep.use_cache and dep.dependency in self.cache:
            return self.cache[dep.dependency]
        return None

    def cache_dependency(self, cls: Callable | Type, dependency: Any):
        self.cache[cls] = dependency
