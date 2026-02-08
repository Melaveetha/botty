from abc import ABC, abstractmethod

from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from .exceptions import DatabaseNotInitializedError


class DatabaseProvider(ABC):
    """Abstract base class for database providers."""

    @abstractmethod
    def create_engine(self) -> Engine:
        """Create and return a SQLAlchemy engine."""
        pass

    @abstractmethod
    def get_session(self) -> Session:
        """Create and return session. Never call this function in code: this might lead to connection leaks. Leave session handling to Botty!"""
        pass


class SQLiteProvider(DatabaseProvider):
    """SQLite database provider."""

    def __init__(self, path: str = "bot.db"):
        self.path = path
        self.engine: Engine | None = None

    def create_engine(self) -> Engine:
        """Create SQLite engine."""
        url = f"sqlite:///{self.path}"
        self.engine = create_engine(
            url, echo=False, connect_args={"check_same_thread": False}
        )
        SQLModel.metadata.create_all(self.engine)
        return self.engine

    def get_session(self) -> Session:
        if not self.engine:
            raise DatabaseNotInitializedError()
        return Session(self.engine)
