from typing import TYPE_CHECKING, Protocol
from telegram.ext import CallbackContext, ExtBot, Application as TgApplication


if TYPE_CHECKING:
    from .database import DatabaseProvider
    from .routing import MessageRegistry
    from .di import DependencyContainer
    from .ports import TelegramBotClient


class BotData:
    """Bot-wide data stored in PTB's bot_data.

    Attributes:
        message_registry: Registry for tracking sent messages.
        dependency_container: Container for dependency injection.
        database_provider: Optional database provider instance.
        bot_client: Client for sending/editing messages (adapter).
    """

    message_registry: "MessageRegistry"
    dependency_container: "DependencyContainer"
    database_provider: "DatabaseProvider | None"
    bot_client: "TelegramBotClient"

    def __init__(self):
        # TODO: add error when not properly initialized
        self.message_registry = None  # type: ignore [invalid-assignment]
        self.dependency_container = None  # type: ignore [invalid-assignment]
        self.database_provider = None
        self.bot_client = None  # type: ignore [invalid-assignment]


class UserData:
    def __init__(self):
        pass


class ChatData:
    def __init__(self):
        pass


class ContextProtocol(Protocol):
    """Minimal protocol defining the context interface required by botty.

    Used for type hints to avoid tight coupling with the concrete Context
    class.
    """

    @property
    def bot_data(self) -> BotData: ...
    @property
    def user_data(self) -> UserData: ...
    @property
    def chat_data(self) -> ChatData: ...
    @property
    def args(self) -> list[str]: ...


class Context(CallbackContext[ExtBot, UserData, ChatData, BotData]):
    """Custom context class for botty handlers.

    Inherits from PTB's CallbackContext and provides access to bot_data,
    user_data, chat_data, and command arguments.
    """

    def __init__(
        self,
        application: TgApplication,
        chat_id: int | None = None,
        user_id: int | None = None,
    ):
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)
