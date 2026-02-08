from telegram import InlineKeyboardMarkup
from dataclasses import dataclass


@dataclass
class BaseAnswer:
    text: str
    parse_mode: str | None = "HTML"
    reply_markup: InlineKeyboardMarkup | None = None

    # For message registry
    message_key: str | None = None
    metadata: dict | None = None
    handler_name: str | None = None

    @property
    def type(self) -> str:
        """Return the type of answer for routing."""
        return self.__class__.__name__.lower()

    def to_dict(self) -> dict:
        """Convert to dictionary for telegram."""
        result = {"text": self.text}
        if self.parse_mode:
            result["parse_mode"] = self.parse_mode
        if self.reply_markup:
            result["reply_markup"] = self.reply_markup
        return result


@dataclass
class Answer(BaseAnswer):
    """Send new message to current user"""


@dataclass
class EditAnswer(BaseAnswer):
    """Edit previous message send to current user"""

    message_id: int | None = None  # Edit specific message by id
    message_key: str | None = None  # Reference by key


@dataclass
class EmptyAnswer(BaseAnswer):
    text: str | None = None
