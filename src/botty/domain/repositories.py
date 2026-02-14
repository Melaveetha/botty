from abc import ABC
from typing import Generic, Type, TypeVar

from sqlmodel import Session, SQLModel, select

from ..exceptions import RepositoryOperationError

T = TypeVar("T", bound=SQLModel)


class BaseRepository(ABC, Generic[T]):
    """Base class for all repositories following the repository pattern.

    Provides standard CRUD operations (get, get_all, create, update, delete)
    for SQLModel entities. Subclasses **must** set the `model` class attribute
    to the SQLModel class they manage.

    Repositories are request-scoped and receive a database session via the
    constructor. Botty injects them automatically when type-hinted in handlers.

    Example:
        ```python
        class UserRepository(BaseRepository[User]):
            model = User

            def find_by_email(self, email: str) -> User | None:
                return self.session.exec(
                    select(User).where(User.email == email)
                ).first()
        ```
    """

    model: Type[T]
    __name__: str

    def __init__(self, session: Session):
        """Initialize the repository with a database session.

        Args:
            session: SQLModel Session to use for all database operations.
        """
        self.session = session

    def get(self, id: int) -> T | None:
        """Retrieve an entity by its primary key.

        Args:
            id: Primary key value.

        Returns:
            The entity if found, else None.

        Raises:
            RepositoryOperationError: If the database operation fails.
        """
        try:
            return self.session.get(self.model, id)
        except Exception as e:
            raise RepositoryOperationError(
                operation="get",
                repository_name=self.__class__.__name__,
                original_error=e,
            ) from e

    def get_all(self, limit: int = 100, offset: int = 0) -> list[T]:
        """Retrieve all entities with pagination.

        Args:
            limit: Maximum number of records to return.
            offset: Number of records to skip.

        Returns:
            List of entities (may be empty).

        Raises:
            RepositoryOperationError: If the database operation fails.
        """
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
        """Insert a new entity into the database.

        The entity is added to the session and flushed, and then refreshed
        to obtain database-generated fields (e.g., auto-increment ID).

        Args:
            entity: The entity instance to create.

        Returns:
            The same entity with updated fields (e.g., ID populated).

        Raises:
            RepositoryOperationError: If the database operation fails.
        """
        try:
            self.session.add(entity)
            self.session.flush()
            self.session.refresh(entity)
            return entity
        except Exception as e:
            raise RepositoryOperationError(
                operation="create",
                repository_name=self.__class__.__name__,
                original_error=e,
            ) from e

    def update(self, entity: T) -> T:
        """Update an existing entity.

        Merges the entity into the session, flushes, and refreshes it.

        Args:
            entity: The entity with modified fields.

        Returns:
            The updated entity (same instance, but refreshed).

        Raises:
            RepositoryOperationError: If the database operation fails.
        """
        try:
            merged = self.session.merge(entity)
            self.session.flush()
            self.session.refresh(merged)
            return merged
        except Exception as e:
            raise RepositoryOperationError(
                operation="update",
                repository_name=self.__class__.__name__,
                original_error=e,
            ) from e

    def delete(self, id: int) -> bool:
        """Delete an entity by its primary key.

        Args:
            id: Primary key of the entity to delete.

        Returns:
            True if an entity was deleted, False if not found.

        Raises:
            RepositoryOperationError: If the database operation fails.
        """
        try:
            entity = self.get(id)
            if entity:
                self.session.delete(entity)
                self.session.flush()
                return True
            return False
        except Exception as e:
            raise RepositoryOperationError(
                operation="delete",
                repository_name=self.__class__.__name__,
                original_error=e,
            ) from e

    def commit(self):
        """Commit the current transaction.

        Note: In normal botty flow, commit is called automatically at the
        end of the request. This method is provided for manual control.
        """
        self.session.commit()
