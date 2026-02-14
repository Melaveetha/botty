from abc import ABC


class BaseService(ABC):
    """Base class for all services.

    Services are business logic classes that operate on repositories or
    external APIs. They are instantiated as **singletons** (shared across
    all requests) by the dependency injection system.

    Example:
        ```python
        class NotificationService(BaseService):
            def __init__(self):
                self._email_client = EmailClient()

            async def send_welcome_email(self, user_email: str):
                ...
        ```
    """

    __name__ = "base_service"

    def __init__(self):
        pass
