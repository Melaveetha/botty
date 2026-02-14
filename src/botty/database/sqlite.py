from sqlalchemy import Engine
from sqlmodel import Session, SQLModel, create_engine

from ..exceptions import DatabaseNotInitializedError
from .provider import DatabaseProvider


class SQLiteProvider(DatabaseProvider):
    """SQLite implementation of DatabaseProvider.

    Creates a SQLite engine with the specified database file and automatically
    creates tables for all SQLModel models.

    Example:
        ```python
        provider = SQLiteProvider("data/bot.db")
        app = AppBuilder().database(provider).build()
        ```
    """

    def __init__(self, path: str = "bot.db"):
        """Initialize the SQLite provider.

        Args:
            path: Filesystem path where the SQLite database file will be stored.
                  Defaults to "bot.db" in the current working directory.
        """
        self.path = path
        self.engine: Engine | None = None

    def create_engine(self) -> Engine:
        """Create the SQLite engine and create all tables.

        The engine is configured with `check_same_thread=False` to allow
        usage across threads (asyncio). Tables are created using
        SQLModel.metadata.create_all.

        Returns:
            The created SQLAlchemy Engine.
        """
        url = f"sqlite:///{self.path}"
        self.engine = create_engine(
            url, echo=False, connect_args={"check_same_thread": False}
        )
        SQLModel.metadata.create_all(self.engine)
        return self.engine

    def get_session(self) -> Session:
        """Return a new SQLModel Session bound to the engine.

        **Important:** Do not call this method directly.
        Botty manages session lifecycle automatically via RequestScope.
        Calling it manually may lead to connection leaks.

        Raises:
            DatabaseNotInitializedError: If create_engine() has not been called yet.
        """
        if not self.engine:
            raise DatabaseNotInitializedError()
        return Session(self.engine)

    def close(self):
        """Dispose of the engine, closing all connections."""
        if self.engine:
            self.engine.dispose()
