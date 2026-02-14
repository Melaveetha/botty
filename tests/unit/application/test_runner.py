# tests/unit/application/test_runner.py
from unittest.mock import MagicMock, patch

from botty.adapters import PTBBotAdapter
from botty.application import Application
from botty.database import DatabaseProvider
from botty.di import DependencyContainer
from botty.routing import MessageRegistry, Router


class TestApplication:
    """Tests for the Application runner."""

    @patch("botty.application.runner.PTBApplicationBuilder")
    def test_init_sets_up_ptb_app(self, mock_ptb_builder_cls):
        # Mock the PTB builder chain
        mock_ptb_builder = MagicMock()
        mock_ptb_builder_cls.return_value = mock_ptb_builder
        mock_ptb_builder.token.return_value = mock_ptb_builder
        mock_ptb_builder.context_types.return_value = mock_ptb_builder
        mock_ptb_app = MagicMock()
        mock_ptb_builder.build.return_value = mock_ptb_app
        # Set up bot_data to receive attributes
        mock_ptb_app.bot_data = MagicMock()

        routers = [Router(name="r1"), Router(name="r2")]
        provider = MagicMock(spec=DatabaseProvider)

        app = Application("token", provider, routers)

        # Verify the app stores the PTB application
        assert app.application is mock_ptb_app

        # Verify builder chain
        mock_ptb_builder_cls.assert_called_once()
        mock_ptb_builder.token.assert_called_once_with("token")
        mock_ptb_builder.context_types.assert_called_once()
        mock_ptb_builder.build.assert_called_once()

        # Verify bot_data is populated
        bot_data = mock_ptb_app.bot_data
        assert isinstance(bot_data.message_registry, MessageRegistry)
        assert isinstance(bot_data.dependency_container, DependencyContainer)
        assert bot_data.database_provider is provider
        assert isinstance(bot_data.bot_client, PTBBotAdapter)

        # Verify handlers are added for each router
        assert mock_ptb_app.add_handlers.call_count == len(routers)
        for i, router in enumerate(routers):
            args, _ = mock_ptb_app.add_handlers.call_args_list[i]
            assert args[0] == router.get_handlers()

    @patch("botty.application.runner.PTBApplicationBuilder")
    def test_launch_calls_run_polling(self, mock_ptb_builder_cls):
        mock_ptb_app = MagicMock()
        mock_ptb_builder_cls.return_value.token.return_value.context_types.return_value.build.return_value = mock_ptb_app

        provider = MagicMock(spec=DatabaseProvider)
        app = Application("token", provider, [])
        app.launch()

        provider.create_engine.assert_called_once()
        mock_ptb_app.run_polling.assert_called_once()

    @patch("botty.application.runner.PTBApplicationBuilder")
    def test_launch_without_db_skips_create_engine(self, mock_ptb_builder_cls):
        mock_ptb_app = MagicMock()
        mock_ptb_builder_cls.return_value.token.return_value.context_types.return_value.build.return_value = mock_ptb_app

        app = Application("token", None, [])
        app.launch()

        mock_ptb_app.run_polling.assert_called_once()
