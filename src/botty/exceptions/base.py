from typing import Any


class BottyError(Exception):
    """Base exception of all Botty exceptions.

    All custom Botty exceptions inherit from this base class.

    Attributes:
        message: The error message
        details: Optional additional details about the error
        suggestion: Optional suggestion for fixing the error
    """

    def __init__(
        self, message: str, details: str | None = None, suggestion: str | None = None
    ):
        self.message: str = message
        self.details: str | None = details
        self.suggestion: str | None = suggestion

        error = message
        if details:
            error += f"\n{details}"
        if suggestion:
            error += f"\n💡 Suggestion: {suggestion}"

        super().__init__(error)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging or serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "suggestion": self.suggestion,
        }
