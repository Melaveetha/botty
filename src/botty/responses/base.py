from dataclasses import dataclass, field

from telegram import ReplyKeyboardMarkup
from telegram.constants import ParseMode


@dataclass
class BaseAnswer:
    text: str
    parse_mode: str | None = field(default=ParseMode.HTML, kw_only=True)
    reply_markup: ReplyKeyboardMarkup | None = field(default=None, kw_only=True)
    disable_notification: bool = field(default=False, kw_only=True)
    protect_content: bool = field(default=False, kw_only=True)

    # For message registry
    message_key: str | None = field(default=None, kw_only=True)
    metadata: dict | None = field(default=None, kw_only=True)
    handler_name: str | None = field(default=None, kw_only=True)

    @property
    def type(self) -> str:
        """Return the type of answer for routing."""
        return self.__class__.__name__.lower()

    def to_dict(self) -> dict:
        """Convert to dictionary for telegram."""
        result = {
            "text": self.text,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }
        if self.parse_mode:
            result["parse_mode"] = self.parse_mode
        if self.reply_markup:
            result["reply_markup"] = self.reply_markup
        return result
