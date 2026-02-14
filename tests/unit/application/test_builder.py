# tests/unit/application/test_builder.py
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from botty.application import AppBuilder, Application
from botty.database import DatabaseProvider
from botty.exceptions import ConfigurationError
from botty.routing import Router


class TestAppBuilder:
    """Tests for the AppBuilder configuration."""

    def test_token_setter(self):
        builder = AppBuilder().token("test-token")
        assert builder._token == "test-token"

    def test_database_setter(self):
        provider = MagicMock(spec=DatabaseProvider)
        builder = AppBuilder().database(provider)
        assert builder._database_provider is provider

    def test_handlers_directory_setter(self):
        path = "/custom/handlers"
        builder = AppBuilder().handlers_directory(path)
        assert builder._handlers_dir == Path(path)

    def test_add_router(self):
        router = Router(name="test")
        builder = AppBuilder().add_router(router)
        assert router in builder._routers

    def test_add_routers(self):
        r1 = Router(name="r1")
        r2 = Router(name="r2")
        builder = AppBuilder().add_routers(r1, r2)
        assert r1 in builder._routers
        assert r2 in builder._routers

    def test_manual_routes_disables_discovery(self):
        builder = AppBuilder().manual_routes()
        assert builder._discovery is False

    @patch("botty.application.builder.discover_routers")
    def test_build_with_discovery(self, mock_discover):
        mock_discover.return_value = [Router(name="discovered")]
        builder = AppBuilder().token("token").database(MagicMock(spec=DatabaseProvider))
        app = builder.build()
        assert isinstance(app, Application)
        mock_discover.assert_called_once_with(None)

    @patch("botty.application.builder.discover_routers")
    def test_build_manual_routers_only(self, mock_discover):
        r1 = Router(name="r1")
        builder = (
            AppBuilder()
            .token("token")
            .database(MagicMock(spec=DatabaseProvider))
            .manual_routes()
            .add_router(r1)
        )
        builder.build()
        mock_discover.assert_not_called()

    def test_build_missing_token_raises_error(self):
        builder = AppBuilder().database(MagicMock(spec=DatabaseProvider))
        with pytest.raises(ConfigurationError) as exc:
            builder.build()
        assert "Token was not specified" in str(exc.value)

    def test_build_missing_database_warns(self, caplog):
        builder = AppBuilder().manual_routes().token("token")
        with caplog.at_level("WARNING"):
            app = builder.build()
        assert "No database provider specified" in caplog.text
        assert isinstance(app, Application)
