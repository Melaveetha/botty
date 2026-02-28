from botty.middleware import Middleware
from pathlib import Path
from typing import Self

from loguru import logger

from ..database import DatabaseProvider
from ..exceptions import ConfigurationError
from ..routing import Router, discover_routers
from .runner import Application
from .webhook import WebhookConfig


class AppBuilder:
    """Builder class for botty Application.

    Provides a interface to configure the bot token, database,
    routers, and discovery options before building the final Application.

    Example:
        ```python
        app = (AppBuilder()
                .token("YOUR_TOKEN")
                .database(SQLiteProvider("bot.db"))
                .add_router(my_router)
                .build())
        app.launch()
        ```
    """

    def __init__(self):
        self._token: str | None = None
        self._handlers_dir: Path | None = None
        self._routers: list[Router] = []
        self._database_provider: DatabaseProvider | None = None
        self._discovery: bool = True
        self._webhook: WebhookConfig | None = None
        self._middlewares: list[Middleware] = []

    def token(self, token: str) -> Self:
        """Set the bot token obtained from @BotFather.

        Args:
            token: The Telegram bot token.

        Returns:
            The builder instance for chaining.
        """
        self._token = token
        return self

    def database(self, provider: DatabaseProvider) -> Self:
        """Set the database provider for the application.

        Args:
            provider: A concrete DatabaseProvider (e.g., SQLiteProvider).

        Returns:
            The builder instance for chaining.
        """
        self._database_provider = provider
        return self

    def webhook(self, webhook: WebhookConfig) -> Self:
        """Configure the bot to run in webhook mode.

        Args:
            url: Public HTTPS URL where Telegram will send updates (e.g., "https://example.com/webhook").
            port: Local port to listen on (default 8443).
            listen: IP address to bind (default "0.0.0.0").
            path: URL path that will receive updates (default "/").
            secret_token: Optional secret to verify incoming requests (recommended).
            cert: Path to SSL certificate file if using a self‑signed certificate.
            key: Path to private key file (required if cert is provided).

        Returns:
            The builder instance for chaining.
        """
        self._webhook = webhook
        return self

    def handlers_directory(self, path: str | Path) -> Self:
        """Set a custom directory for automatic router discovery.

        By default, botty looks for handlers in `src/handlers/` relative to
        the project root. Use this method to specify a different path.

        Args:
            path: Path to the directory containing handler modules.

        Returns:
            The builder instance for chaining.
        """
        self._handlers_dir = Path(path)
        return self

    def add_middleware(self, middleware: Middleware) -> Self:
        """Add a single middleware.

        Args:
            middleware: A functions that receives update: Update, context: Context and generator: AsyncGenerator[BaseAnswer, None] and returns AsyncGenerator[BaseAnswer, None].

        Returns:
            The builder instance for chaining.
        """
        self._middlewares.append(middleware)
        return self

    def add_middlewares(self, middlewares: list[Middleware]) -> Self:
        self._middlewares.extend(middlewares)
        return self

    def add_router(self, router: Router) -> Self:
        """Add a single router manually (instead of auto-discovery).

        Args:
            router: A Router instance.

        Returns:
            The builder instance for chaining.
        """
        self._routers.append(router)
        return self

    def add_routers(self, *routers: Router) -> Self:
        """Add multiple routers at once.

        Args:
            *routers: One or more Router instances.

        Returns:
            The builder instance for chaining.
        """
        self._routers.extend(routers)
        return self

    def manual_routes(self) -> Self:
        """Disable automatic router discovery.

        Use this if you want to register all routers explicitly via
        `add_router` or `add_routers`. Auto-discovery is enabled by default.

        Returns:
            The builder instance for chaining.
        """
        self._discovery = False
        return self

    def build(self) -> Application:
        """Construct the Application instance with the configured settings.

        Returns:
            A fully initialized Application ready to be launched.

        Raises:
            ConfigurationError: If required settings (like token) are missing.
        """
        if self._database_provider is None:
            logger.warning(
                "No database provider specified. Could lead to some features not working properly."
                "If you don't need a database, ignore this warning."
            )
        if self._token is None:
            raise ConfigurationError(
                "Token was not specified.",
                suggestion='add `.token("Your token from @BotFather").build()` in your bot.py file',
            )
        if self._discovery:
            self._routers.extend(discover_routers(self._handlers_dir))
        return Application(
            self._token,
            self._database_provider,
            self._routers,
            self._middlewares,
            self._webhook,
        )
