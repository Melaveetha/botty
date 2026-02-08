from botty import BaseRepository, Context, Depends

from datetime import datetime, timedelta
from typing import Annotated, Optional, TypeAlias

from sqlmodel import Session, select
from telegram import Update

from src.models.user import User


class UserRepository(BaseRepository):
    """Repository for User model operations."""

    model = User

    def __init__(self, session: Session):
        super().__init__(session)

    def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
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
        self, telegram_id: int, full_name: str, username: Optional[str] = None
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
        else:
            # Create new user
            user = User(telegram_id=telegram_id, full_name=full_name, username=username)
            self.session.add(user)

        self.session.commit()
        self.session.refresh(user)
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
            self.session.commit()

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


async def user_repo(update: Update, context: Context, session: Session):
    return UserRepository(session)


UserRepositoryDependency: TypeAlias = Annotated[UserRepository, Depends(user_repo)]
