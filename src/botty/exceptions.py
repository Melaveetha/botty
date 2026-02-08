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


class ConfigurationError(BottyError):
    """Error during app configuration"""


class HandlerDiscoveryError(BottyError):
    """Error during handler discovery"""


class RepositoryOperationError(BottyError):
    """Error during database operation in repository"""

    def __init__(
        self,
        operation: str,
        repository_name: str,
        original_error: Exception | None = None,
        message: str | None = None,
    ):
        details = f"operation: {operation} repository_name: {repository_name}"
        if original_error:
            details += f"\n\noriginal_error:\n{original_error}"

        super().__init__(
            message
            or f"Repository operation '{operation}' failed in {repository_name}",
            details=details,
        )


class ChatIdNotFoundError(BottyError):
    """Chat id couldn't be found"""

    def __init__(self):
        super().__init__("Couldn't find chat id in update data.")


class ResponseProcessingError(BottyError):
    """Raised when response processing fails."""

    def __init__(
        self,
        message: str,
        response_type: str | None = None,
        handler_name: str | None = None,
    ):
        super().__init__(
            message,
            details=f"Response type: {response_type}; Handler name: {handler_name}",
        )


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


class DependencyResolutionError(BottyError):
    """Raise when dependency resolution fails"""


class DatabaseNotInitializedError(BottyError):
    """Raised when database engine is accessed before initialization."""

    def __init__(self, message: str | None = None):
        super().__init__(
            message or "Database engine is not initialized",
            suggestion=(
                "Ensure the database provider's create_engine() method has been called. "
            ),
        )
