from abc import ABC, abstractmethod

from sqlalchemy import Engine
from sqlmodel import Session


class DatabaseProvider(ABC):
    """Abstract base class for database providers.

    Concrete implementations must provide methods to create an engine,
    obtain a session, and clean up resources. Botty uses this to manage
    database sessions automatically during request handling.
    """

    @abstractmethod
    def create_engine(self) -> Engine:
        """Create and return a SQLAlchemy engine.

        This method is called once during application startup. It should
        also create any necessary tables if they do not exist.

        Returns:
            A configured SQLAlchemy Engine instance.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """Dispose of the database engine and release resources.

        Called when the application shuts down. Implementations should
        call engine.dispose() or similar.
        """
        pass

    @abstractmethod
    def get_session(self) -> Session:
        """Create and return a new database session.

        **Important:** Do not call this method directly.
        Botty manages session lifecycle automatically via RequestScope.
        Calling it manually may lead to connection leaks.

        Returns:
            A SQLModel Session object.
        """
        pass

    def __del__(self):
        self.close()
