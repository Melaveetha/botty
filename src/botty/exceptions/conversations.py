from .base import BottyError


class InvalidConversationError(BottyError):
    """Raised when a conversation class definition is invalid."""

    def __init__(
        self,
        message: str,
        class_name: str | None = None,
        method_name: str | None = None,
        suggestion: str | None = None,
    ):
        details = []
        if class_name:
            details.append(f"Conversation class: {class_name}")
        if method_name:
            details.append(f"Method: {method_name}")

        super().__init__(
            message=message,
            details="\n".join(details) if details else None,
            suggestion=suggestion,
        )
