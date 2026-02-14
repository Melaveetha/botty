from loguru import logger
from pathlib import Path
from typing import Self


from ..database import DatabaseProvider
from ..exceptions import ConfigurationError
from ..routing import Router, discover_routers
from .runner import Application


class AppBuilder:
    def __init__(self):
        self._token: str | None = None
        self._handlers_dir: Path | None = None
        self._routers: list[Router] = []
        self._database_provider: DatabaseProvider | None = None
        self._discovery: bool = True

    def token(self, token: str) -> Self:
        self._token = token
        return self

    def database(self, provider: DatabaseProvider) -> Self:
        """Set database provider"""
        self._database_provider = provider
        return self

    def handlers_directory(self, path: str | Path) -> Self:
        """Set custom handlers directory."""
        self._handlers_dir = Path(path)
        return self

    def add_router(self, router: Router) -> Self:
        """Add custom router"""
        self._routers.append(router)
        return self

    def add_routers(self, *routers: Router) -> Self:
        """Add custom routers"""
        self._routers.extend(routers)
        return self

    def manual_routes(self) -> Self:
        self._discovery = False
        return self

    def build(self) -> Application:
        if self._database_provider is None:
            logger.warning(
                "No database provider specified. Could lead to some features not working properly."
                "If you don't need a database, ignore this warning."
            )
            # raise ConfigurationError(
            #     "Database provider was not specified.",
            #     suggestion='add `.database(SqlProvider("data.db")).build()` in your bot.py file',
            # )
        if self._token is None:
            raise ConfigurationError(
                "Token was not specified.",
                suggestion='add `.token("Your token from @BotFather").build()` in your bot.py file',
            )
        if self._discovery:
            self._routers.extend(discover_routers(self._handlers_dir))
        return Application(self._token, self._database_provider, self._routers)
