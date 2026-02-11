from typing import Any, Literal, TypeAlias
from telegram.constants import ParseMode
from telegram import InlineKeyboardMarkup
from dataclasses import dataclass


@dataclass
class BaseAnswer:
    text: str
    parse_mode: str | None = ParseMode.HTML
    reply_markup: InlineKeyboardMarkup | None = None
    disable_notification: bool = False
    protect_content: bool = False

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


@dataclass
class Answer(BaseAnswer):
    """Send new message to current user"""


# TODO: add editing of other types of messages: photo, video and so on.
@dataclass
class EditAnswer(BaseAnswer):
    """Edit previous message send to current user. Keep in mind that this class can only edit text messages"""

    message_id: int | None = None  # Edit specific message by id
    message_key: str | None = None  # Reference by key


@dataclass
class EmptyAnswer(BaseAnswer):
    text: str | None = None


@dataclass
class PhotoAnswer(BaseAnswer):
    """Send a photo."""

    photo: str | bytes
    caption: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "photo": self.photo,
            "caption": self.caption or self.text,
            "parse_mode": self.parse_mode,
            "reply_markup": self.reply_markup,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }


@dataclass
class DocumentAnswer(BaseAnswer):
    """Send a document."""

    document: str | bytes
    filename: str | None = None
    caption: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "document": self.document,
            "filename": self.filename,
            "caption": self.caption or self.text,
            "parse_mode": self.parse_mode,
            "reply_markup": self.reply_markup,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }


@dataclass
class AudioAnswer(BaseAnswer):
    """Send an audio file."""

    audio: str | bytes
    title: str | None = None
    caption: str | None = None
    duration: int | None = None
    performer: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "audio": self.audio,
            "caption": self.caption or self.text,
            "parse_mode": self.parse_mode,
            "duration": self.duration,
            "performer": self.performer,
            "title": self.title,
            "reply_markup": self.reply_markup,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }


@dataclass
class VideoAnswer(BaseAnswer):
    """Send a video."""

    video: str | bytes
    caption: str | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None
    supports_streaming: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "video": self.video,
            "caption": self.caption or self.text,
            "parse_mode": self.parse_mode,
            "duration": self.duration,
            "width": self.width,
            "height": self.height,
            "supports_streaming": self.supports_streaming,
            "reply_markup": self.reply_markup,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }


@dataclass
class VoiceAnswer(BaseAnswer):
    """Send a voice note."""

    voice: str | bytes
    caption: str | None = None
    duration: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "voice": self.voice,
            "caption": self.caption or self.text,
            "parse_mode": self.parse_mode,
            "duration": self.duration,
            "reply_markup": self.reply_markup,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }


@dataclass
class LocationAnswer(BaseAnswer):
    """Send a location."""

    latitude: float
    longitude: float
    horizontal_accuracy: float | None = None
    live_period: int | None = None
    heading: int | None = None
    proximity_alert_radius: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "horizontal_accuracy": self.horizontal_accuracy,
            "live_period": self.live_period,
            "heading": self.heading,
            "proximity_alert_radius": self.proximity_alert_radius,
            "reply_markup": self.reply_markup,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }


@dataclass
class VenueAnswer(BaseAnswer):
    """Send a venue."""

    latitude: float
    longitude: float
    title: str
    address: str
    foursquare_id: str | None = None
    foursquare_type: str | None = None
    google_place_id: str | None = None
    google_place_type: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "title": self.title,
            "address": self.address,
            "foursquare_id": self.foursquare_id,
            "foursquare_type": self.foursquare_type,
            "google_place_id": self.google_place_id,
            "google_place_type": self.google_place_type,
            "reply_markup": self.reply_markup,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }


@dataclass
class ContactAnswer(BaseAnswer):
    """Send a phone contact."""

    phone_number: str
    first_name: str
    last_name: str | None = None
    vcard: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "phone_number": self.phone_number,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "vcard": self.vcard,
            "reply_markup": self.reply_markup,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }


PollTypes: TypeAlias = Literal["regular"] | Literal["quiz"]


@dataclass
class PollAnswer(BaseAnswer):
    """Send a poll."""

    question: str
    options: list[str]
    is_anonymous: bool = True
    type: PollTypes = "regular"
    allows_multiple_answers: bool = False
    correct_option_id: int | None = None
    explanation: str | None = None
    explanation_parse_mode: str | None = ParseMode.HTML
    open_period: int | None = None
    close_date: int | None = None
    is_closed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "question": self.question or self.text,
            "options": self.options,
            "is_anonymous": self.is_anonymous,
            "type": self.type,
            "allows_multiple_answers": self.allows_multiple_answers,
            "correct_option_id": self.correct_option_id,
            "explanation": self.explanation,
            "explanation_parse_mode": self.explanation_parse_mode,
            "open_period": self.open_period,
            "close_date": self.close_date,
            "is_closed": self.is_closed,
            "reply_markup": self.reply_markup,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }


DiceEmojis: TypeAlias = (
    Literal["🎲"]
    | Literal["🎯"]
    | Literal["🏀"]
    | Literal["⚽"]
    | Literal["🎰"]
    | Literal["🎳"]
)


@dataclass
class DiceAnswer(BaseAnswer):
    """Send a dice with animated emoji."""

    emoji: DiceEmojis = "🎲"  # 🎲, 🎯, 🏀, ⚽, 🎰, 🎳

    def to_dict(self) -> dict[str, Any]:
        return {
            "emoji": self.emoji,
            "reply_markup": self.reply_markup,
            "disable_notification": self.disable_notification,
            "protect_content": self.protect_content,
        }
