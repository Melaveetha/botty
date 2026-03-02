from dataclasses import dataclass, field
from typing import Any, Literal, TypeAlias

from telegram.constants import ParseMode

from .base import BaseAnswer, _clean_dict


@dataclass
class Answer(BaseAnswer):
    """Send a simple text message.

    Maps to `bot.send_message` in python-telegram-bot.

    Inherits all fields from BaseAnswer (text, parse_mode, reply_markup, etc.).

    Example:
        ```python
        @router.command("hello")
        async def hello_handler(...) -> HandlerResponse:
            yield Answer(text="Hello, world!")
        ```
    """

    text: str

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["text"] = self.text
        return _clean_dict(d)


# TODO: add editing of other types of messages: photo, video and so on.
@dataclass
class EditAnswer(BaseAnswer):
    """Edit a previously sent message.

    Currently only supports editing text messages. If `message_id` or `message_key`
    are provided, that specific message is edited. Otherwise, the processor
    attempts to find the most recent message from the same handler or chat.

    Maps to `bot.edit_message_text` in python-telegram-bot.

    Attributes:
        message_id: Direct ID of the message to edit (if known).
        message_key: Key used when the message was registered (alternative to ID).

    Example:
        ```python
        @router.command("countdown")
        async def countdown(...) -> HandlerResponse:
            yield Answer("3", message_key="cd")
            await asyncio.sleep(1)
            yield EditAnswer("2", message_key="cd")
        ```
    """

    text: str
    message_id: int | None = field(
        default=None, kw_only=True
    )  # Edit specific message by id
    message_key: str | None = field(default=None, kw_only=True)  # Reference by key

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["text"] = self.text
        return _clean_dict(d)


@dataclass
class EmptyAnswer(BaseAnswer):
    """A response that does nothing (no message is sent).

    Useful when you want to conditionally skip sending a message while still
    maintaining a uniform handler interface (e.g., in a branch where no
    reply is needed).

    Example:
        ```python
        if not user:
            yield EmptyAnswer()   # nothing sent
            return
        ```
    """

    parse_mode: ParseMode | None = field(default=None, kw_only=True)


@dataclass
class PhotoAnswer(BaseAnswer):
    """Send a photo.

    Maps to `bot.send_photo` in python-telegram-bot.

    Attributes:
        photo: File ID, URL, or file-like object (bytes).
        caption: Optional caption; if omitted, falls back to `text`.

    Example:
        ```python
        @router.command("cat")
        async def cat_handler(...) -> HandlerResponse:
            yield PhotoAnswer(
                photo="https://cataas.com/cat",
                caption="Here's a random cat!"
            )
        ```
    """

    photo: str | bytes
    text: str | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["photo"] = self.photo
        d["caption"] = self.text
        return _clean_dict(d)


@dataclass
class DocumentAnswer(BaseAnswer):
    """Send a document (file).

    Maps to `bot.send_document` in python-telegram-bot.

    Attributes:
        document: File ID, URL, or file-like object.
        filename: Optional filename to display.
        caption: Optional caption; falls back to `text`.

    Example:
        ```python
        @router.command("file")
        async def file_handler(...) -> HandlerResponse:
            with open("report.pdf", "rb") as f:
                yield DocumentAnswer(
                    document=f,
                    filename="report.pdf",
                    caption="Your report is ready."
                )
        ```
    """

    document: str | bytes
    text: str | None = field(default=None, kw_only=True)
    filename: str | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["document"] = self.document
        d["filename"] = self.filename
        d["caption"] = self.text
        return _clean_dict(d)


@dataclass
class AudioAnswer(BaseAnswer):
    """Send an audio file (typically music).

    Maps to `bot.send_audio` in python-telegram-bot.

    Attributes:
        audio: File ID, URL, or file-like object.
        title: Optional title.
        caption: Optional caption; falls back to `text`.
        duration: Duration in seconds.
        performer: Performer name.

    Example:
        ```python
        @router.command("song")
        async def song_handler(...) -> HandlerResponse:
            yield AudioAnswer(
                audio="CQACAgIAAxkB...",  # file_id
                title="My Song",
                performer="My Band"
            )
        ```
    """

    audio: str | bytes
    title: str | None = field(default=None, kw_only=True)
    text: str | None = field(default=None, kw_only=True)
    duration: int | None = field(default=None, kw_only=True)
    performer: str | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["audio"] = self.audio
        d["title"] = self.title
        d["duration"] = self.duration
        d["performer"] = self.performer
        d["caption"] = self.text
        return _clean_dict(d)


@dataclass
class VideoAnswer(BaseAnswer):
    """Send a video.

    Maps to `bot.send_video` in python-telegram-bot.

    Attributes:
        video: File ID, URL, or file-like object.
        caption: Optional caption; falls back to `text`.
        duration: Duration in seconds.
        width, height: Video dimensions.
        supports_streaming: Whether the video can be streamed.

    Example:
        ```python
        @router.command("video")
        async def video_handler(...) -> HandlerResponse:
            yield VideoAnswer(
                video="BAACAgIAAxkB...",  # file_id
                caption="Check out this video!",
                supports_streaming=True
            )
        ```
    """

    video: str | bytes
    text: str | None = field(default=None, kw_only=True)
    duration: int | None = field(default=None, kw_only=True)
    width: int | None = field(default=None, kw_only=True)
    height: int | None = field(default=None, kw_only=True)
    supports_streaming: bool = False

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["video"] = self.video
        d["duration"] = self.duration
        d["width"] = self.width
        d["height"] = self.height
        d["supports_streaming"] = self.supports_streaming
        d["caption"] = self.text
        return _clean_dict(d)


@dataclass
class VoiceAnswer(BaseAnswer):
    """Send a voice note (audio in OGG format).

    Maps to `bot.send_voice` in python-telegram-bot.

    Attributes:
        voice: File ID, URL, or file-like object.
        caption: Optional caption; falls back to `text`.
        duration: Duration in seconds.

    Example:
        ```python
        @router.command("voice")
        async def voice_handler(...) -> HandlerResponse:
            yield VoiceAnswer(
                voice="AwACAgIAAxkB...",  # file_id
                caption="Listen to this!"
            )
        ```
    """

    voice: str | bytes
    text: str | None = field(default=None, kw_only=True)
    duration: int | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["voice"] = self.voice
        d["duration"] = self.duration
        d["caption"] = self.text
        return _clean_dict(d)


@dataclass
class LocationAnswer(BaseAnswer):
    """Send a geographic location.

    Maps to `bot.send_location` in python-telegram-bot.

    Attributes:
        latitude: Latitude in degrees.
        longitude: Longitude in degrees.
        horizontal_accuracy: Accuracy radius in meters.
        live_period: For live locations, update period in seconds.
        heading: Direction in degrees.
        proximity_alert_radius: Radius for proximity alerts.

    Example:
        ```python
        @router.command("loc")
        async def location_handler(...) -> HandlerResponse:
            yield LocationAnswer(
                latitude=40.7128,
                longitude=-74.0060,
                live_period=60
            )
        ```
    """

    latitude: float
    longitude: float
    horizontal_accuracy: float | None = field(default=None, kw_only=True)
    live_period: int | None = field(default=None, kw_only=True)
    heading: int | None = field(default=None, kw_only=True)
    proximity_alert_radius: int | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["parse_mode"] = None
        d["latitude"] = self.latitude
        d["longitude"] = self.longitude
        d["horizontal_accuracy"] = self.horizontal_accuracy
        d["live_period"] = self.live_period
        d["heading"] = self.heading
        d["proximity_alert_radius"] = self.proximity_alert_radius
        return _clean_dict(d)


@dataclass
class VenueAnswer(BaseAnswer):
    """Send information about a venue.

    Maps to `bot.send_venue` in python-telegram-bot.

    Attributes:
        latitude, longitude: Coordinates.
        title: Name of the venue.
        address: Street address.
        foursquare_id, foursquare_type: Foursquare identifiers.
        google_place_id, google_place_type: Google Places identifiers.

    Example:
        ```python
        @router.command("venue")
        async def venue_handler(...) -> HandlerResponse:
            yield VenueAnswer(
                latitude=40.7128,
                longitude=-74.0060,
                title="Central Park",
                address="New York, NY"
            )
        ```
    """

    latitude: float
    longitude: float
    title: str
    address: str
    foursquare_id: str | None = field(default=None, kw_only=True)
    foursquare_type: str | None = field(default=None, kw_only=True)
    google_place_id: str | None = field(default=None, kw_only=True)
    google_place_type: str | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["parse_mode"] = None
        d["latitude"] = self.latitude
        d["longitude"] = self.longitude
        d["title"] = self.title
        d["address"] = self.address
        d["foursquare_id"] = self.foursquare_id
        d["foursquare_type"] = self.foursquare_type
        d["google_place_id"] = self.google_place_id
        d["google_place_type"] = self.google_place_type
        return _clean_dict(d)


@dataclass
class ContactAnswer(BaseAnswer):
    """Send a phone contact.

    Maps to `bot.send_contact` in python-telegram-bot.

    Attributes:
        phone_number: Contact's phone number.
        first_name: Contact's first name.
        last_name: Optional last name.
        vcard: Optional vCard data.

    Example:
        ```python
        @router.command("contact")
        async def contact_handler(...) -> HandlerResponse:
            yield ContactAnswer(
                phone_number="+1234567890",
                first_name="John",
                last_name="Doe"
            )
        ```
    """

    phone_number: str
    first_name: str
    last_name: str | None = field(default=None, kw_only=True)
    vcard: str | None = field(default=None, kw_only=True)

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["parse_mode"] = None
        d["phone_number"] = self.phone_number
        d["first_name"] = self.first_name
        d["last_name"] = self.last_name
        d["vcard"] = self.vcard
        return _clean_dict(d)


PollTypes: TypeAlias = Literal["regular"] | Literal["quiz"]


@dataclass
class PollAnswer(BaseAnswer):
    """Send a poll.

    Maps to `bot.send_poll` in python-telegram-bot.

    Attributes:
        question: Poll question (overrides `text` if provided).
        options: List of answer strings.
        is_anonymous: Whether votes are anonymous (default True).
        type: "regular" or "quiz".
        allows_multiple_answers: For regular polls, allow multiple selections.
        correct_option_id: For quiz polls, index of correct option.
        explanation: For quiz polls, explanation shown after answer.
        explanation_parse_mode: Parse mode for explanation.
        open_period: Seconds the poll will be active.
        close_date: Unix timestamp when poll closes.
        is_closed: Pass True to close the poll immediately.

    Example:
        ```python
        @router.command("poll")
        async def poll_handler(...) -> HandlerResponse:
            yield PollAnswer(
                question="What's your favorite color?",
                options=["Red", "Green", "Blue"],
                type="quiz",
                correct_option_id=0
            )
        ```
    """

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
        d = super().to_dict()
        d["question"] = self.question
        d["options"] = self.options
        d["is_anonymous"] = self.is_anonymous
        d["type"] = self.type
        d["allows_multiple_answers"] = self.allows_multiple_answers
        d["correct_option_id"] = self.correct_option_id
        d["explanation"] = self.explanation
        d["explanation_parse_mode"] = self.explanation_parse_mode
        d["open_period"] = self.open_period
        d["close_date"] = self.close_date
        d["is_closed"] = self.is_closed
        return _clean_dict(d)


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
    """Send a dice with an animated emoji.

    Maps to `bot.send_dice` in python-telegram-bot.

    Attributes:
        emoji: Dice type. Allowed values: "🎲" (default), "🎯", "🏀", "⚽", "🎰", "🎳".

    Example:
        ```python
        @router.command("roll")
        async def roll_handler(...) -> HandlerResponse:
            yield DiceAnswer(emoji="🎲")
        ```
    """

    emoji: DiceEmojis = "🎲"  # 🎲, 🎯, 🏀, ⚽, 🎰, 🎳

    def to_dict(self) -> dict[str, Any]:
        d = super().to_dict()
        d["parse_mode"] = None
        d["emoji"] = self.emoji
        return _clean_dict(d)
