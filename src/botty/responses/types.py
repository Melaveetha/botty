from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias

from telegram.constants import ParseMode

from .base import BaseAnswer


def _clean_dict(d: dict) -> dict:
    """Remove keys with None values."""
    return {k: v for k, v in d.items() if v is not None}


@dataclass
class Answer(BaseAnswer):
    """Send new message to current user"""


# TODO: add editing of other types of messages: photo, video and so on.
@dataclass
class EditAnswer(BaseAnswer):
    """Edit previous message send to current user. Keep in mind that this class can only edit text messages"""

    message_id: int | None = field(
        default=None, kw_only=True
    )  # Edit specific message by id
    message_key: str | None = field(default=None, kw_only=True)  # Reference by key


@dataclass
class EmptyAnswer(BaseAnswer):
    text: str | None = field(default=None, kw_only=True)
    parse_mode: ParseMode | None = field(default=None, kw_only=True)


@dataclass
class PhotoAnswer(BaseAnswer):
    """Send a photo."""

    photo: str | bytes
    caption: str | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        return _clean_dict(
            {
                "photo": self.photo,
                "caption": self.caption or self.text,
                "parse_mode": self.parse_mode,
                "reply_markup": self.reply_markup,
                "disable_notification": self.disable_notification,
                "protect_content": self.protect_content,
            }
        )


@dataclass
class DocumentAnswer(BaseAnswer):
    """Send a document."""

    document: str | bytes
    filename: str | None = field(default=None, kw_only=True)
    caption: str | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        return _clean_dict(
            {
                "document": self.document,
                "filename": self.filename,
                "caption": self.caption or self.text,
                "parse_mode": self.parse_mode,
                "reply_markup": self.reply_markup,
                "disable_notification": self.disable_notification,
                "protect_content": self.protect_content,
            }
        )


@dataclass
class AudioAnswer(BaseAnswer):
    """Send an audio file."""

    audio: str | bytes
    title: str | None = field(default=None, kw_only=True)
    caption: str | None = field(default=None, kw_only=True)
    duration: int | None = field(default=None, kw_only=True)
    performer: str | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        return _clean_dict(
            {
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
        )


@dataclass
class VideoAnswer(BaseAnswer):
    """Send a video."""

    video: str | bytes
    caption: str | None = field(default=None, kw_only=True)
    duration: int | None = field(default=None, kw_only=True)
    width: int | None = field(default=None, kw_only=True)
    height: int | None = field(default=None, kw_only=True)
    supports_streaming: bool = False

    def to_dict(self) -> dict[str, Any]:
        return _clean_dict(
            {
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
        )


@dataclass
class VoiceAnswer(BaseAnswer):
    """Send a voice note."""

    voice: str | bytes
    caption: str | None = field(default=None, kw_only=True)
    duration: int | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        return _clean_dict(
            {
                "voice": self.voice,
                "caption": self.caption or self.text,
                "parse_mode": self.parse_mode,
                "duration": self.duration,
                "reply_markup": self.reply_markup,
                "disable_notification": self.disable_notification,
                "protect_content": self.protect_content,
            }
        )


@dataclass
class LocationAnswer(BaseAnswer):
    """Send a location."""

    latitude: float
    longitude: float
    horizontal_accuracy: float | None = field(default=None, kw_only=True)
    live_period: int | None = field(default=None, kw_only=True)
    heading: int | None = field(default=None, kw_only=True)
    proximity_alert_radius: int | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        return _clean_dict(
            {
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
        )


@dataclass
class VenueAnswer(BaseAnswer):
    """Send a venue."""

    latitude: float
    longitude: float
    title: str
    address: str
    foursquare_id: str | None = field(default=None, kw_only=True)
    foursquare_type: str | None = field(default=None, kw_only=True)
    google_place_id: str | None = field(default=None, kw_only=True)
    google_place_type: str | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        return _clean_dict(
            {
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
        )


@dataclass
class ContactAnswer(BaseAnswer):
    """Send a phone contact."""

    phone_number: str
    first_name: str
    last_name: str | None = field(default=None, kw_only=True)
    vcard: str | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        return _clean_dict(
            {
                "phone_number": self.phone_number,
                "first_name": self.first_name,
                "last_name": self.last_name,
                "vcard": self.vcard,
                "reply_markup": self.reply_markup,
                "disable_notification": self.disable_notification,
                "protect_content": self.protect_content,
            }
        )


PollTypes: TypeAlias = Literal["regular"] | Literal["quiz"]


@dataclass
class PollAnswer(BaseAnswer):
    """Send a poll."""

    question: str
    options: list[str]
    is_anonymous: bool = field(default=True, kw_only=True)
    type: PollTypes = "regular"
    allows_multiple_answers: bool = field(default=False, kw_only=True)
    correct_option_id: int | None = field(default=None, kw_only=True)
    explanation: str | None = field(default=None, kw_only=True)
    explanation_parse_mode: str | None = field(default=ParseMode.HTML, kw_only=True)
    open_period: int | None = field(default=None, kw_only=True)
    close_date: int | None = field(default=None, kw_only=True)
    is_closed: bool = field(default=False, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        return _clean_dict(
            {
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
        )


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
        return _clean_dict(
            {
                "emoji": self.emoji,
                "reply_markup": self.reply_markup,
                "disable_notification": self.disable_notification,
                "protect_content": self.protect_content,
            }
        )
