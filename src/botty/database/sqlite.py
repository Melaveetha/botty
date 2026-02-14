from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from ..exceptions import DatabaseNotInitializedError
from .provider import DatabaseProvider


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

    def close(self):
        if self.engine:
            self.engine.dispose()
