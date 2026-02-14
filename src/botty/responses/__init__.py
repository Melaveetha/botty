"""
Response types – objects that handlers yield.
"""

from botty.responses.base import BaseAnswer
from botty.responses.types import (
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

__all__ = [
    "BaseAnswer",
    "Answer",
    "EditAnswer",
    "EmptyAnswer",
    "PhotoAnswer",
    "DocumentAnswer",
    "AudioAnswer",
    "VideoAnswer",
    "VoiceAnswer",
    "LocationAnswer",
    "VenueAnswer",
    "ContactAnswer",
    "PollAnswer",
    "DiceAnswer",
]
