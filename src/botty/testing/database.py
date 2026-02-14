from sqlmodel import Session, SQLModel, create_engine

from botty.database import DatabaseProvider


class TestDatabaseProvider(DatabaseProvider):
    """In‑memory SQLite provider with per‑test isolation."""

    __test__ = False

    def __init__(self):
        self.engine = create_engine("sqlite:///:memory:?cache=shared:")
        SQLModel.metadata.create_all(self.engine)

    def create_engine(self):
        return self.engine  # already created

    def get_session(self) -> Session:
        return Session(self.engine)

    def close(self):
        self.engine.dispose()

    def reset(self):
        """Drop and recreate all tables."""
        SQLModel.metadata.drop_all(self.engine)
        SQLModel.metadata.create_all(self.engine)
