from .exceptions import RepositoryOperationError
from abc import ABC
from sqlmodel import SQLModel, Session, select
from typing import TypeVar, Generic, Type

T = TypeVar("T", bound=SQLModel)


class BaseRepository(ABC, Generic[T]):
    """Base repository for data access."""

    model: Type[T]
    __name__: str

    def __init__(self, session: Session):
        self.session = session

    def get(self, id: int) -> T | None:
        """Get entity by ID."""
        try:
            return self.session.get(self.model, id)
        except Exception as e:
            raise RepositoryOperationError(
                operation="get",
                repository_name=self.__class__.__name__,
                original_error=e,
            ) from e

    def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Get all entities with pagination."""
        try:
            statement = select(self.model).offset(offset).limit(limit)
            return list(self.session.exec(statement).all())
        except Exception as e:
            raise RepositoryOperationError(
                operation="get_all",
                repository_name=self.__class__.__name__,
                original_error=e,
            ) from e

    def create(self, entity: T) -> T:
        """Create new entity."""
        try:
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except Exception as e:
            raise RepositoryOperationError(
                operation="create",
                repository_name=self.__class__.__name__,
                original_error=e,
            ) from e

    def update(self, entity: T) -> T:
        """Update existing entity."""
        try:
            self.session.add(entity)
            self.session.commit()
            self.session.refresh(entity)
            return entity
        except Exception as e:
            raise RepositoryOperationError(
                operation="update",
                repository_name=self.__class__.__name__,
                original_error=e,
            ) from e

    def delete(self, id: int) -> bool:
        """Delete entity by ID."""
        try:
            entity = self.get(id)
            if entity:
                self.session.delete(entity)
                self.session.commit()
                return True
            return False
        except Exception as e:
            raise RepositoryOperationError(
                operation="delete",
                repository_name=self.__class__.__name__,
                original_error=e,
            ) from e


class BaseService:
    __name__ = "base_service"

    def __init__(self):
        pass
