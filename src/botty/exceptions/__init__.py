"""
Custom exceptions used throughout the framework.
"""

from .base import BottyError
from .config import ConfigurationError
from .database import (
    DatabaseNotConfiguredError,
    DatabaseNotInitializedError,
)
from .dependencies import DependencyResolutionError
from .handlers import (
    CallbackQueryNotFound,
    EditedMessageNotFound,
    EffectiveChatNotFound,
    EffectiveMessageNotFound,
    EffectiveUserNotFound,
    HandlerDiscoveryError,
    InvalidHandlerError,
    PollAnswerNotFound,
    PollNotFound,
)
from .registry import ChatIdNotFoundError
from .repository import RepositoryOperationError
from .responses import ResponseProcessingError

__all__ = [
    "BottyError",
    "ConfigurationError",
    "DatabaseNotConfiguredError",
    "DatabaseNotInitializedError",
    "DependencyResolutionError",
    "HandlerDiscoveryError",
    "InvalidHandlerError",
    "RepositoryOperationError",
    "ResponseProcessingError",
    "ChatIdNotFoundError",
    "EffectiveUserNotFound",
    "EffectiveChatNotFound",
    "EffectiveMessageNotFound",
    "CallbackQueryNotFound",
    "EditedMessageNotFound",
    "PollNotFound",
    "PollAnswerNotFound",
]
