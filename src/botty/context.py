from typing import TYPE_CHECKING, Protocol
from telegram.ext import CallbackContext, ExtBot, Application as TgApplication


if TYPE_CHECKING:
    from .database import DatabaseProvider
    from .routing import MessageRegistry
    from .di import DependencyContainer
    from .ports import TelegramBotClient


class BotData:
    message_registry: "MessageRegistry"
    dependency_container: "DependencyContainer"
    database_provider: "DatabaseProvider | None"
    bot_client: "TelegramBotClient"

    def __init__(self):
        # TODO: add error when not properly initialized
        self.message_registry = None  # ty: ignore [invalid-assignment]
        self.dependency_container = None  # ty: ignore [invalid-assignment]
        self.database_provider = None
        self.bot_client = None  # ty: ignore [invalid-assignment]


class UserData:
    def __init__(self):
        pass


class ChatData:
    def __init__(self):
        pass


class ContextProtocol(Protocol):
    """The minimal context interface Botty requires."""

    @property
    def bot_data(self) -> BotData: ...
    @property
    def user_data(self) -> UserData: ...
    @property
    def chat_data(self) -> ChatData: ...
    @property
    def args(self) -> list[str]: ...


class Context(CallbackContext[ExtBot, UserData, ChatData, BotData]):
    def __init__(
        self,
        application: TgApplication,
        chat_id: int | None = None,
        user_id: int | None = None,
    ):
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)
