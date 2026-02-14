from .base import BottyError


class HandlerDiscoveryError(BottyError):
    """Error during handler discovery"""


class InvalidHandlerError(BottyError):
    """Raised when a handler function doesn't match the expected signature."""

    def __init__(
        self,
        handler_name: str,
        reason: str,
        suggestion: str | None = None,
    ):
        super().__init__(
            message=f"Invalid handler '{handler_name}': {reason}",
            details=f"Handler name: {handler_name}, reason: reason",
            suggestion=suggestion
            or "Check the handler documentation for correct signature",
        )


class EffectiveUserNotFound(BottyError):
    """Raised when update.effective_user is None"""

    def __init__(self, message: str | None = None):
        super().__init__(message=message or "Effective user was not found")


class EffectiveChatNotFound(BottyError):
    """Raised when update.effective_chat is None"""

    def __init__(self, message: str | None = None):
        super().__init__(message=message or "Effective chat was not found")


class EffectiveMessageNotFound(BottyError):
    """Raised when update.effective_message is None"""

    def __init__(self, message: str | None = None):
        super().__init__(message=message or "Effective message was not found")


class CallbackQueryNotFound(BottyError):
    """Raised when update.callback_query is None"""

    def __init__(self, message: str | None = None):
        super().__init__(message=message or "Callback query was not found")


class EditedMessageNotFound(BottyError):
    """Raised when update.edited_message is None"""

    def __init__(self, message: str | None = None):
        super().__init__(message=message or "EditedMessage was not found")


class PollNotFound(BottyError):
    """Raised when update.poll is None"""

    def __init__(self, message: str | None = None):
        super().__init__(message=message or "Poll was not found")


class PollAnswerNotFound(BottyError):
    """Raised when update.poll_answer is None"""

    def __init__(self, message: str | None = None):
        super().__init__(message=message or "Poll answer was not found")
