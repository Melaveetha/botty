from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional


class User(SQLModel, table=True):
    """
    User model representing a Telegram user in the database.

    Attributes:
        id: Primary key
        telegram_id: Unique Telegram user ID
        username: Telegram username (optional)
        full_name: User's full name from Telegram
        created_at: When the user first started the bot
        last_active: Last time user interacted with bot
        timezone: User's timezone (optional, for future features)
    """

    id: int = Field(default=None, primary_key=True)
    telegram_id: int = Field(index=True, unique=True)
    username: Optional[str] = None
    full_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    timezone: Optional[str] = None

    def __repr__(self) -> str:
        return f"User(id={self.id}, telegram_id={self.telegram_id}, name='{self.full_name}')"
