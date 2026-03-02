from dataclasses import dataclass, field

from telegram import ReplyKeyboardMarkup
from telegram.constants import ParseMode


def _clean_dict(d: dict) -> dict:
    """Remove keys with None values."""
    return {k: v for k, v in d.items() if v is not None}


@dataclass
class BaseAnswer:
    """Base class for all bot responses.

    All concrete response types inherit from this class. It contains common
    fields like text, parse_mode, reply_markup, and metadata for message
    tracking.

    Attributes:
        parse_mode: HTML or Markdown formatting (default HTML).
        reply_markup: Inline keyboard or reply markup.
        disable_notification: If True, sends the message silently.
        protect_content: If True, prevents forwarding and saving.
        message_key: Optional key for later retrieval via MessageRegistry.
        metadata: Arbitrary additional data to store with the message.
        handler_name: Override the handler name used for registry tracking.
    """

    parse_mode: str | None = field(default=ParseMode.HTML, kw_only=True)
    reply_markup: ReplyKeyboardMarkup | None = field(default=None, kw_only=True)
    disable_notification: bool | None = field(default=None, kw_only=True)
    protect_content: bool | None = field(default=None, kw_only=True)

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
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }
        if self.parse_mode is not None:
            result["parse_mode"] = self.parse_mode
        if self.reply_markup is not None:
            result["reply_markup"] = self.reply_markup
        return _clean_dict(result)
