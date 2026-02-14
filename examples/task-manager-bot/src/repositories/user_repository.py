from botty import BaseRepository

from datetime import datetime, timedelta

from sqlmodel import Session, select

from src.models.user import User


class UserRepository(BaseRepository):
    """Repository for User model operations."""

    model = User

    def __init__(self, session: Session):
        super().__init__(session)

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """
        Get user by Telegram ID.

        Args:
            telegram_id: Telegram user ID

        Returns:
            User if found, None otherwise
        """
        statement = select(User).where(User.telegram_id == telegram_id)
        return self.session.exec(statement).first()

    def create_or_update(
        self, telegram_id: int, full_name: str, username: str | None = None
    ) -> User:
        """
        Create a new user or update existing user.

        Args:
            telegram_id: Telegram user ID
            full_name: User's full name
            username: User's Telegram username (optional)

        Returns:
            Created or updated User
        """
        user = self.get_by_telegram_id(telegram_id)

        if user:
            # Update existing user
            user.full_name = full_name
            user.username = username
            user.last_active = datetime.utcnow()
            self.update(user)
        else:
            # Create new user
            user = User(telegram_id=telegram_id, full_name=full_name, username=username)
            self.create(user)
        return user

    def update_last_active(self, user_id: int) -> None:
        """
        Update user's last active timestamp.

        Args:
            user_id: User ID
        """
        user = self.get(user_id)
        if user:
            user.last_active = datetime.utcnow()
            self.update(user)

    def get_all_active_users(self, days: int = 7) -> list[User]:
        """
        Get all users active within specified days.

        Args:
            days: Number of days to look back

        Returns:
            List of active users
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        statement = select(User).where(User.last_active >= cutoff)
        return list(self.session.exec(statement).all())
