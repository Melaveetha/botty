from dataclasses import dataclass
from abc import ABC
from datetime import datetime
from typing import Generic, Type, TypeVar

from sqlmodel import Session, SQLModel, select
from telegram import (
    Message as TGMessage,
    PollOption,
)

from .exceptions import RepositoryOperationError, ChatIdNotFoundError

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


class BaseService(ABC):
    __name__ = "base_service"

    def __init__(self):
        pass


class Message:
    message_id: int
    chat_id: int
    date: datetime

    def __init__(self, message_id: int, chat_id: int, date: datetime):
        self.message_id = message_id
        self.chat_id = chat_id
        self.date = date

    @staticmethod
    def from_telegram(message: TGMessage) -> "Message":
        return Message(message.id, chat_id=message.chat_id, date=message.date)


@dataclass
class EffectiveUser:
    id: int
    first_name: str
    username: str | None = None


@dataclass
class EffectiveChat:
    id: int
    type: str


@dataclass
class EffectiveMessage:
    message_id: int
    chat_id: int
    date: datetime
    text: str | None


@dataclass
class CallbackQuery:
    id: str
    data: str | None
    user_id: int
    message_id: int | None
    chat_id: int | None


@dataclass
class EditedMessage:
    """Represents an edited message."""

    message_id: int
    chat_id: int
    date: datetime
    edit_date: datetime | None
    text: str | None = None


@dataclass
class Poll:
    id: str
    question: str
    options: list[PollOption]
    total_voter_count: int
    is_closed: bool
    is_anonymous: bool
    type: str
    allows_multiple_answers: bool


@dataclass
class PollAnswer:
    poll_id: str
    user: EffectiveUser | None
    option_ids: list[int]


@dataclass
class Update:
    update_id: int
    user: EffectiveUser | None = None
    chat: EffectiveChat | None = None
    message: EffectiveMessage | None = None
    callback_query: CallbackQuery | None = None

    edited_message: EditedMessage | None = None
    poll: Poll | None = None
    poll_answer: PollAnswer | None = None

    @property
    def effective_user_id(self) -> int | None:
        return self.user.id if self.user else None

    @property
    def effective_chat_id(self) -> int | None:
        return self.chat.id if self.chat else None

    def get_chat_id(self) -> int:
        """Extract chat ID from update with comprehensive fallback logic."""
        if self.message:
            return self.message.chat_id
        elif self.callback_query and self.callback_query.chat_id:
            return self.callback_query.chat_id
        elif self.chat:
            return self.chat.id
        else:
            raise ChatIdNotFoundError()
