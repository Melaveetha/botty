from typing import Any

from sqlmodel import Session

from ..domain import Update
from ..context import ContextProtocol
from ..di import Dependency, Depends, RequestScope
from ..ports import TelegramBotClient
from ..routing import MessageRegistry
from .bot_client import TestBotClient
from .registry import TestMessageRegistry


class TestRequestScope(RequestScope):
    """Request scope with all dependencies replaceable."""

    __test__ = False

    def __init__(
        self,
        update: Update,
        context: ContextProtocol,
        session: Session | None = None,
        bot_client: TelegramBotClient | None = None,
        message_registry: MessageRegistry | None = None,
        overrides: dict[Dependency, Any] | None = None,
    ):
        super().__init__(update, context)
        self._session = session
        self._provider = None
        self.bot_client = bot_client or TestBotClient()
        self.message_registry = message_registry or TestMessageRegistry()
        self.overrides: dict[Dependency, Any] = overrides or {}

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("No session provided to TestRequestScope")
        return self._session

    def get_dependency(self, dep: Depends) -> Any:
        if dep.use_cache and dep.dependency in self.cache:
            return self.cache[dep.dependency]
        # Check overrides first
        if dep.dependency in self.overrides:
            return self.overrides[dep.dependency]
        return None
