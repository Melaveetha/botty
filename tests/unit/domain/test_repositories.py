# tests/unit/domain/test_repositories.py
from unittest.mock import patch

import pytest
from sqlmodel import Field, SQLModel

from botty.domain import BaseRepository
from botty.exceptions import RepositoryOperationError
from botty.testing import TestDatabaseProvider


# -------------------------------------------------------------------
# Test model and repository
# -------------------------------------------------------------------
class UserModel(SQLModel, table=True):
    __test__ = False  # prevent pytest from collecting this
    id: int | None = Field(default=None, primary_key=True)
    name: str
    telegram_id: int = Field(unique=True)


class UserRepository(BaseRepository[UserModel]):
    model = UserModel


# -------------------------------------------------------------------
# Fixtures
# -------------------------------------------------------------------


@pytest.fixture
def db_provider():
    """Fresh in‑memory database provider."""
    provider = TestDatabaseProvider()
    engine = provider.create_engine()
    SQLModel.metadata.create_all(engine)
    return provider


@pytest.fixture
def session(db_provider):
    """Get a session from the provider."""
    with db_provider.get_session() as session:
        yield session


@pytest.fixture
def repo(session):
    """UserRepository instance with an open session."""
    return UserRepository(session)


# -------------------------------------------------------------------
# Tests
# -------------------------------------------------------------------
class TestBaseRepository:
    """Test all methods of BaseRepository."""

    def test_create(self, repo, session):
        """Create a new entity and verify it's persisted."""
        user = UserModel(name="Alice", telegram_id=123)
        created = repo.create(user)

        assert created.id is not None
        assert created.name == "Alice"
        assert created.telegram_id == 123

        # Verify in DB
        fetched = session.get(UserModel, created.id)
        assert fetched is not None
        assert fetched.name == "Alice"

    def test_get_existing(self, repo, session):
        """Retrieve an existing entity by ID."""
        user = UserModel(name="Bob", telegram_id=456)
        session.add(user)
        session.commit()
        session.refresh(user)

        fetched = repo.get(user.id)
        assert fetched is not None
        assert fetched.id == user.id
        assert fetched.name == "Bob"

    def test_get_nonexistent(self, repo):
        """Retrieve a non‑existent ID returns None."""
        fetched = repo.get(99999)
        assert fetched is None

    def test_get_all(self, repo, session):
        """Retrieve all entities with pagination."""
        # Create three users
        for i, name in enumerate(["Alice", "Bob", "Charlie"]):
            session.add(UserModel(name=name, telegram_id=100 + i))
        session.commit()

        all_users = repo.get_all()
        assert len(all_users) == 3

        # Test limit
        limited = repo.get_all(limit=2)
        assert len(limited) == 2

        # Test offset
        offset = repo.get_all(limit=2, offset=1)
        assert len(offset) == 2
        # Order not guaranteed, so just check count

    def test_update(self, repo, session):
        """Update an existing entity."""
        user = UserModel(name="Dave", telegram_id=789)
        session.add(user)
        session.commit()
        session.refresh(user)

        user.name = "David"
        updated = repo.update(user)

        assert updated.name == "David"
        # Verify in DB
        fetched = session.get(UserModel, user.id)
        assert fetched.name == "David"

    def test_update_entity_not_in_session(self, repo, session, db_provider):
        """Update an entity that is not attached to the session (should still work)."""
        # Create and then detach by closing session
        user = UserModel(name="Eve", telegram_id=101)
        session.add(user)
        session.commit()
        user_id = user.id
        session.close()  # detach

        # Re‑attach via new session
        with db_provider.get_session() as new_session:
            repo2 = UserRepository(new_session)
            detached_user = UserModel(id=user_id, name="Eve Updated", telegram_id=101)
            updated = repo2.update(detached_user)
            repo2.commit()
            assert updated.name == "Eve Updated"

        # Verify with fresh session
        with db_provider.get_session() as verify_session:
            fetched = verify_session.get(UserModel, user_id)
            assert fetched.name == "Eve Updated"

    def test_delete_existing(self, repo, session):
        """Delete an existing entity, returns True."""
        user = UserModel(name="Frank", telegram_id=202)
        session.add(user)
        session.commit()
        user_id = user.id

        result = repo.delete(user_id)
        assert result is True

        # Verify deletion
        fetched = session.get(UserModel, user_id)
        assert fetched is None

    def test_delete_nonexistent(self, repo):
        """Delete a non‑existent ID returns False."""
        result = repo.delete(99999)
        assert result is False

    def test_get_raises_repository_operation_error(self, repo):
        """Simulate a database error during get()."""
        with patch.object(repo.session, "get", side_effect=Exception("DB error")):
            with pytest.raises(RepositoryOperationError) as exc:
                repo.get(1)
            assert "get" in str(exc.value)
            assert "UserRepository" in str(exc.value)

    def test_get_all_raises_repository_operation_error(self, repo):
        """Simulate a database error during get_all()."""
        with patch.object(repo.session, "exec", side_effect=Exception("DB error")):
            with pytest.raises(RepositoryOperationError) as exc:
                repo.get_all()
            assert "get_all" in str(exc.value)
            assert "UserRepository" in str(exc.value)

    def test_create_raises_repository_operation_error(self, repo):
        """Simulate a database error during create()."""
        user = UserModel(name="Test", telegram_id=999)
        with patch.object(repo.session, "flush", side_effect=Exception("DB error")):
            with pytest.raises(RepositoryOperationError) as exc:
                repo.create(user)
            assert "create" in str(exc.value)
            assert "UserRepository" in str(exc.value)

    def test_update_raises_repository_operation_error(self, repo, session):
        """Simulate a database error during update()."""
        user = UserModel(name="Grace", telegram_id=303)
        session.add(user)
        session.commit()
        session.refresh(user)

        with patch.object(repo.session, "flush", side_effect=Exception("DB error")):
            with pytest.raises(RepositoryOperationError) as exc:
                repo.update(user)
            assert "update" in str(exc.value)
            assert "UserRepository" in str(exc.value)

    def test_delete_raises_repository_operation_error(self, repo, session):
        """Simulate a database error during delete()."""
        user = UserModel(name="Heidi", telegram_id=404)
        session.add(user)
        session.commit()
        user_id = user.id

        with patch.object(repo.session, "delete", side_effect=Exception("DB error")):
            with pytest.raises(RepositoryOperationError) as exc:
                repo.delete(user_id)
            assert "delete" in str(exc.value)
            assert "UserRepository" in str(exc.value)
