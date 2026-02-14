from telegram.ext import Application as PTBApplication
from telegram.ext import ApplicationBuilder as PTBApplicationBuilder
from telegram.ext import ContextTypes, ExtBot

from ..adapters import PTBBotAdapter
from ..context import BotData, ChatData, Context, UserData
from ..database import DatabaseProvider
from ..di import DependencyContainer
from ..routing import MessageRegistry, Router


class Application:
    def __init__(
        self,
        token: str,
        database_provider: DatabaseProvider | None,
        routers: list[Router],
    ):
        context_types = ContextTypes(
            context=Context, bot_data=BotData, chat_data=ChatData, user_data=UserData
        )
        self.application: PTBApplication[
            ExtBot, Context, UserData, ChatData, BotData, None
        ] = PTBApplicationBuilder().token(token).context_types(context_types).build()
        self.application.bot_data.message_registry = MessageRegistry()
        self.application.bot_data.database_provider = database_provider
        self.application.bot_data.dependency_container = DependencyContainer()
        self.application.bot_data.bot_client = PTBBotAdapter(self.application.bot)

        for router in routers:
            self.application.add_handlers(router.get_handlers())

    def launch(self):
        if self.application.bot_data.database_provider:
            self.application.bot_data.database_provider.create_engine()
        self.application.run_polling()
