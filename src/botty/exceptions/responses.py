from .base import BottyError


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
