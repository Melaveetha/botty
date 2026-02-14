# tests/unit/responses/test_response_types.py
from telegram.constants import ParseMode

from botty.responses import (
    Answer,
    AudioAnswer,
    ContactAnswer,
    DiceAnswer,
    DocumentAnswer,
    EditAnswer,
    EmptyAnswer,
    LocationAnswer,
    PhotoAnswer,
    PollAnswer,
    VenueAnswer,
    VideoAnswer,
    VoiceAnswer,
)


class TestBaseAnswer:
    """Tests for base Answer functionality."""

    def test_answer_creation(self):
        answer = Answer(text="Hello")
        assert answer.text == "Hello"
        assert answer.parse_mode == ParseMode.HTML
        assert answer.reply_markup is None
        assert answer.disable_notification is False
        assert answer.protect_content is False
        assert answer.message_key is None
        assert answer.metadata is None
        assert answer.handler_name is None

    def test_to_dict_basic(self):
        answer = Answer(text="Hi", parse_mode="Markdown")
        d = answer.to_dict()
        assert d == {
            "text": "Hi",
            "disable_notification": False,
            "protect_content": False,
            "parse_mode": "Markdown",
        }

    def test_to_dict_with_reply_markup(self):
        from telegram import ReplyKeyboardMarkup

        markup = ReplyKeyboardMarkup([["Yes", "No"]])
        answer = Answer(text="Choose", reply_markup=markup)
        d = answer.to_dict()
        assert d["reply_markup"] is markup
        assert d["text"] == "Choose"

    def test_type_property(self):
        assert Answer(text="").type == "answer"
        assert EditAnswer(text="").type == "editanswer"
        assert EmptyAnswer().type == "emptyanswer"
        assert PhotoAnswer(photo=b"data", text="").type == "photoanswer"


class TestEditAnswer:
    """Tests for EditAnswer."""

    def test_edit_answer_creation(self):
        answer = EditAnswer(
            text="Edited", message_id=42, message_key="key", handler_name="handler"
        )
        assert answer.message_id == 42
        assert answer.message_key == "key"
        assert answer.handler_name == "handler"

    def test_edit_answer_to_dict(self):
        answer = EditAnswer(text="New text")
        d = answer.to_dict()
        assert d["text"] == "New text"
        assert "message_id" not in d  # message_id is not part of PTB send params


class TestEmptyAnswer:
    """Tests for EmptyAnswer."""

    def test_empty_answer_creation(self):
        answer = EmptyAnswer()
        assert answer.text is None  # EmptyAnswer allows None text
        assert answer.parse_mode is None


class TestPhotoAnswer:
    """Tests for PhotoAnswer."""

    def test_photo_answer_creation(self):
        answer = PhotoAnswer(photo=b"fake_image_data", text="Caption")
        assert answer.photo == b"fake_image_data"
        assert answer.caption is None  # defaults to None

    def test_to_dict_uses_caption_from_text(self):
        answer = PhotoAnswer(photo="file_id", text="My caption")
        d = answer.to_dict()
        assert d["photo"] == "file_id"
        assert d["caption"] == "My caption"

    def test_to_dict_with_explicit_caption(self):
        answer = PhotoAnswer(photo="file_id", text="fallback", caption="explicit")
        d = answer.to_dict()
        assert d["caption"] == "explicit"

    def test_to_dict_omits_none_fields(self):
        answer = PhotoAnswer(photo="file_id", text="")
        d = answer.to_dict()
        assert "caption" in d  # caption is set to text, which is empty string


class TestDocumentAnswer:
    """Tests for DocumentAnswer."""

    def test_document_answer_creation(self):
        answer = DocumentAnswer(document=b"pdf data", text="Doc", filename="doc.pdf")
        assert answer.document == b"pdf data"
        assert answer.filename == "doc.pdf"
        assert answer.caption is None

    def test_to_dict(self):
        answer = DocumentAnswer(document="file_id", text="Here's a file")
        d = answer.to_dict()
        assert d["document"] == "file_id"
        assert d["caption"] == "Here's a file"
        assert "filename" not in d

    def test_to_dict_with_filename(self):
        answer = DocumentAnswer(document="file_id", text="", filename="doc.pdf")
        d = answer.to_dict()
        assert d["filename"] == "doc.pdf"


class TestAudioAnswer:
    """Tests for AudioAnswer."""

    def test_audio_answer_creation(self):
        answer = AudioAnswer(
            audio="file_id", text="Song", title="My Song", duration=180
        )
        assert answer.audio == "file_id"
        assert answer.title == "My Song"
        assert answer.duration == 180

    def test_to_dict(self):
        answer = AudioAnswer(audio="file_id", text="Audio caption")
        d = answer.to_dict()
        assert d["audio"] == "file_id"
        assert d["caption"] == "Audio caption"
        assert "duration" not in d


class TestVideoAnswer:
    """Tests for VideoAnswer."""

    def test_video_answer_creation(self):
        answer = VideoAnswer(
            video="file_id",
            text="Video",
            width=1920,
            height=1080,
            supports_streaming=True,
        )
        assert answer.video == "file_id"
        assert answer.width == 1920
        assert answer.supports_streaming is True

    def test_to_dict(self):
        answer = VideoAnswer(video="file_id", text="Video caption")
        d = answer.to_dict()
        assert d["video"] == "file_id"
        assert d["caption"] == "Video caption"
        assert d["supports_streaming"] is False


class TestVoiceAnswer:
    """Tests for VoiceAnswer."""

    def test_voice_answer_creation(self):
        answer = VoiceAnswer(voice="file_id", text="Voice note", duration=45)
        assert answer.voice == "file_id"
        assert answer.duration == 45

    def test_to_dict(self):
        answer = VoiceAnswer(voice="file_id", text="Voice caption")
        d = answer.to_dict()
        assert d["voice"] == "file_id"
        assert d["caption"] == "Voice caption"
        assert "duration" not in d


class TestLocationAnswer:
    """Tests for LocationAnswer."""

    def test_location_answer_creation(self):
        answer = LocationAnswer(latitude=40.7128, longitude=-74.0060, text="Location")
        assert answer.latitude == 40.7128
        assert answer.longitude == -74.0060

    def test_to_dict(self):
        answer = LocationAnswer(latitude=1.0, longitude=2.0, text="")
        d = answer.to_dict()
        assert d["latitude"] == 1.0
        assert d["longitude"] == 2.0
        assert "horizontal_accuracy" not in d


class TestVenueAnswer:
    """Tests for VenueAnswer."""

    def test_venue_answer_creation(self):
        answer = VenueAnswer(
            latitude=40.7, longitude=-74.0, title="Central Park", address="NYC", text=""
        )
        assert answer.title == "Central Park"
        assert answer.address == "NYC"

    def test_to_dict(self):
        answer = VenueAnswer(
            latitude=40.7, longitude=-74.0, title="Park", address="NYC", text=""
        )
        d = answer.to_dict()
        assert d["title"] == "Park"
        assert d["address"] == "NYC"
        assert "foursquare_id" not in d


class TestContactAnswer:
    """Tests for ContactAnswer."""

    def test_contact_answer_creation(self):
        answer = ContactAnswer(phone_number="+123456789", first_name="John", text="")
        assert answer.phone_number == "+123456789"
        assert answer.first_name == "John"
        assert answer.last_name is None

    def test_to_dict(self):
        answer = ContactAnswer(phone_number="+123", first_name="Jane", text="")
        d = answer.to_dict()
        assert d["phone_number"] == "+123"
        assert d["first_name"] == "Jane"
        assert "last_name" not in d


class TestPollAnswer:
    """Tests for PollAnswer."""

    def test_poll_answer_creation(self):
        answer = PollAnswer(question="Q?", options=["A", "B"], text="")
        assert answer.question == "Q?"
        assert answer.options == ["A", "B"]
        assert answer.type == "regular"

    def test_to_dict(self):
        answer = PollAnswer(
            question="Q?", options=["A", "B"], text="", is_anonymous=False
        )
        d = answer.to_dict()
        assert d["question"] == "Q?"
        assert d["options"] == ["A", "B"]
        assert d["is_anonymous"] is False
        assert d["type"] == "regular"
        assert "explanation" not in d


class TestDiceAnswer:
    """Tests for DiceAnswer."""

    def test_dice_answer_default_emoji(self):
        answer = DiceAnswer(text="")
        assert answer.emoji == "🎲"

    def test_dice_answer_custom_emoji(self):
        answer = DiceAnswer(emoji="🎯", text="")
        assert answer.emoji == "🎯"

    def test_to_dict(self):
        answer = DiceAnswer(emoji="🎲", text="")
        d = answer.to_dict()
        assert d["emoji"] == "🎲"
        assert "text" not in d  # DiceAnswer does not include text
