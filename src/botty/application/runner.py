from loguru import logger
from telegram.ext import (
    Application as PTBApplication,
    CallbackQueryHandler,
)
from telegram.ext import ApplicationBuilder as PTBApplicationBuilder
from telegram.ext import ContextTypes, ExtBot

from ..adapters import PTBBotAdapter
from ..context import BotData, ChatData, Context, UserData
from ..database import DatabaseProvider
from ..di import DependencyContainer, HandlerProtocol
from ..exceptions import BottyError
from ..middleware import Middleware
from ..routing import (
    ConversationDispatcher,
    ConversationRegistry,
    MessageRegistry,
    Router,
)
from .webhook import WebhookConfig


import logging

logging.getLogger("httpx").setLevel(level=logging.DEBUG)


class Application:
    """The main application wrapper around python-telegram-bot's Application.

    This class sets up the PTB application, registers handlers from all
    routers, initializes shared components (message registry, dependency
    container, database), and provides a `launch` method to start polling.

    Attributes:
        application: The underlying PTB Application instance.
    """

    def __init__(
        self,
        token: str,
        database_provider: DatabaseProvider | None,
        routers: list[Router],
        middlewares: list[Middleware] = [],
        exception_handlers: list[tuple[type[Exception], HandlerProtocol]] = [],
        webhook: WebhookConfig | None = None,
    ):
        """Initialize the application and register all handlers.

        Args:
            token: The Telegram bot token from @BotFather.
            database_provider: Optional database provider.
            routers: List of Router instances.
        """
        context_types = ContextTypes(
            context=Context, bot_data=BotData, chat_data=ChatData, user_data=UserData
        )
        self._webhook = webhook
        self.application: PTBApplication[
            ExtBot, Context, UserData, ChatData, BotData, None
        ] = PTBApplicationBuilder().token(token).context_types(context_types).build()

        self.application.bot_data.message_registry = MessageRegistry()
        self.application.bot_data.database_provider = database_provider
        self.application.bot_data.dependency_container = DependencyContainer()
        self.application.bot_data.bot_client = PTBBotAdapter(self.application.bot)
        self.application.bot_data.conversation_registry = ConversationRegistry()
        self.application.bot_data.middlewares = middlewares
        self.application.bot_data.exception_handlers = exception_handlers

        async def log_all(update, context):
            logger.debug(f"Update {update.update_id} arrived")

        self.application.add_handler(
            CallbackQueryHandler(log_all, pattern=".*"),
            group=-2,
        )
        self.application.add_handler(ConversationDispatcher(), group=-1)
        for router in routers:
            self.application.add_handlers(router.get_handlers())
            for conversation in router.conversations:
                self.application.bot_data.conversation_registry.register(conversation)

    def launch(self):
        """Start the bot in polling mode.

        If a database provider was configured, its engine is created before
        starting. This method blocks until the bot is stopped.
        """
        if self.application.bot_data.database_provider:
            self.application.bot_data.database_provider.create_engine()
        if self._webhook is None:
            self.application.run_polling()
        else:
            self._launch_webhook()

    def _launch_webhook(self):
        config = self._webhook
        if config is None:
            raise BottyError(
                "Unexpected call of `_launch_webhook` while webhook config is not specified"
            )
        self.application.run_webhook(
            listen=config.listen,
            port=config.port,
            url_path=config.path.lstrip("/"),
            webhook_url=config.url,
            secret_token=config.secret_token,
            cert=str(config.cert) if config.cert else None,
            key=str(config.key) if config.key else None,
        )
