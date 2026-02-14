from .base import BottyError


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
