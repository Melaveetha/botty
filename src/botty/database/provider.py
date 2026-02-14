from abc import ABC, abstractmethod

from sqlalchemy import Engine
from sqlmodel import Session


class DatabaseProvider(ABC):
    """Abstract base class for database providers."""

    @abstractmethod
    def create_engine(self) -> Engine:
        """Create and return a SQLAlchemy engine."""
        pass

    @abstractmethod
    def close(self) -> None:
        """Destructor for database"""
        pass

    @abstractmethod
    def get_session(self) -> Session:
        """Create and return session. Never call this function in code: this might lead to connection leaks. Leave session handling to Botty!"""
        pass

    def __del__(self):
        self.close()
