# tests/unit/database/test_sqlite.py
import pytest
from sqlmodel import Field, Session, SQLModel, select

from botty.database import SQLiteProvider
from botty.exceptions import DatabaseNotInitializedError


# Define a test model
class TestUser(SQLModel, table=True):
    __test__ = False  # prevent pytest from collecting this as a test
    id: int | None = Field(default=None, primary_key=True)
    name: str
    telegram_id: int = Field(unique=True)


class TestSQLiteProvider:
    """Tests for the SQLite database provider."""

    def test_create_engine_creates_tables(self, tmp_path):
        db_path = tmp_path / "test.db"
        provider = SQLiteProvider(str(db_path))
        engine = provider.create_engine()

        # Verify engine is created and tables are present
        assert engine is not None
        # Use a session to check that the table exists
        with Session(engine) as session:
            # Should not raise
            session.exec(select(TestUser)).all()

    def test_get_session_returns_session(self, tmp_path):
        db_path = tmp_path / "test.db"
        provider = SQLiteProvider(str(db_path))
        provider.create_engine()

        session = provider.get_session()
        assert isinstance(session, Session)
        session.close()

    def test_get_session_before_create_engine_raises(self):
        provider = SQLiteProvider(":memory:")
        with pytest.raises(DatabaseNotInitializedError) as exc:
            provider.get_session()
        assert "Database engine is not initialized" in str(exc.value)

    def test_crud_operations(self, tmp_path):
        db_path = tmp_path / "test.db"
        provider = SQLiteProvider(str(db_path))
        provider.create_engine()

        # Create
        with provider.get_session() as session:
            user = TestUser(name="Alice", telegram_id=123)
            session.add(user)
            session.commit()
            session.refresh(user)
            user_id = user.id

        # Read
        with provider.get_session() as session:
            fetched = session.get(TestUser, user_id)
            assert fetched is not None
            assert fetched.name == "Alice"
            assert fetched.telegram_id == 123

        # Update
        with provider.get_session() as session:
            user = session.get(TestUser, user_id)
            user.name = "Alicia"  # ty: ignore [invalid-assignment]
            session.add(user)
            session.commit()

        with provider.get_session() as session:
            updated = session.get(TestUser, user_id)
            assert updated.name == "Alicia"  # ty: ignore [possibly-missing-attribute]

        # Delete
        with provider.get_session() as session:
            user = session.get(TestUser, user_id)
            session.delete(user)
            session.commit()

        with provider.get_session() as session:
            deleted = session.get(TestUser, user_id)
            assert deleted is None

    def test_multiple_sessions_are_different(self, tmp_path):
        db_path = tmp_path / "test.db"
        provider = SQLiteProvider(str(db_path))
        provider.create_engine()

        session1 = provider.get_session()
        session2 = provider.get_session()
        assert session1 is not session2
        session1.close()
        session2.close()
