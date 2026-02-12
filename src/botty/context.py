from typing import TYPE_CHECKING
from telegram.ext import CallbackContext, ExtBot, Application as TgApplication


if TYPE_CHECKING:
    from .database import DatabaseProvider
    from .router import MessageRegistry, DependencyContainer
    from .ports import TelegramBotClient


class BotData:
    message_registry: "MessageRegistry"
    dependency_container: "DependencyContainer"
    database_provider: "DatabaseProvider | None"
    bot_client: "TelegramBotClient"

    def __init__(self):
        pass


class UserData:
    def __init__(self):
        pass


class ChatData:
    def __init__(self):
        pass


class Context(CallbackContext[ExtBot, UserData, ChatData, BotData]):
    def __init__(
        self,
        application: TgApplication,
        chat_id: int | None = None,
        user_id: int | None = None,
    ):
        super().__init__(application=application, chat_id=chat_id, user_id=user_id)
