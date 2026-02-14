from .base import BottyError


class DatabaseNotInitializedError(BottyError):
    """Raised when database engine is accessed before initialization."""

    def __init__(self, message: str | None = None):
        super().__init__(
            message or "Database engine is not initialized",
            suggestion=(
                "Ensure the database provider's create_engine() method has been called. "
            ),
        )


class DatabaseNotConfiguredError(BottyError):
    """Raised when a database dependency is requested but no database provider is set."""

    def __init__(self, dependency_name: str):
        super().__init__(
            message=f"Cannot inject '{dependency_name}': no database provider configured.",
            suggestion=(
                "Add `.database(...)` to your AppBuilder, or remove the database "
                "dependency from your handler if the bot does not need persistence."
            ),
        )
