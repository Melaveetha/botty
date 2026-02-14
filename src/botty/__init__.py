"""
Botty – A FastAPI-inspired framework for Telegram bots.

Exposes the main public API.
"""

from .application import AppBuilder, Application
from .context import Context, ContextProtocol
from .di import Depends, HandlerResponse
from .database import DatabaseProvider, SQLiteProvider
from .domain import (
    Update,
    Message,
    EffectiveUser,
    EffectiveChat,
    EffectiveMessage,
    CallbackQuery,
    EditedMessage,
    Poll,
    PollAnswer,
    BaseRepository,
    BaseService,
)
from .helpers import (
    InjectableCallbackQuery,
    InjectableEditedMessage,
    InjectableChat,
    InjectableMessage,
    InjectableUser,
    InjectablePoll,
    InjectablePollAnswer,
)
from .responses import (
    BaseAnswer,
    Answer,
    AudioAnswer,
    ContactAnswer,
    DiceAnswer,
    DocumentAnswer,
    EditAnswer,
    EmptyAnswer,
    LocationAnswer,
    PhotoAnswer,
    PollAnswer as ResponsePollAnswer,  # renamed to avoid clash with domain PollAnswer
    VenueAnswer,
    VideoAnswer,
    VoiceAnswer,
)
from .routing import Router

__all__ = [
    # Application
    "AppBuilder",
    "Application",
    # Context
    "Context",
    "ContextProtocol",
    # DI
    "Depends",
    "HandlerResponse",
    # Domain entities
    "Update",
    "Message",
    "EffectiveUser",
    "EffectiveChat",
    "EffectiveMessage",
    "CallbackQuery",
    "EditedMessage",
    "Poll",
    "PollAnswer",
    # Helpers
    "InjectableCallbackQuery",
    "InjectableEditedMessage",
    "InjectableChat",
    "InjectableMessage",
    "InjectableUser",
    "InjectablePoll",
    "InjectablePollAnswer",
    # Domain repositories
    "BaseRepository",
    # Domain services
    "BaseService",
    # Responses
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
    "ResponsePollAnswer",  # if needed
    "DiceAnswer",
    # Routing
    "Router",
    # Database
    "DatabaseProvider",
    "SQLiteProvider",
]
