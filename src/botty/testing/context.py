from dataclasses import dataclass, field

from ..context import BotData, ChatData, UserData
from ..routing import ConversationRegistry
from .bot_client import TestBotClient
from .container import TestDependencyContainer
from .database import TestDatabaseProvider
from .registry import TestMessageRegistry


def init_bot_data() -> BotData:
    data = BotData()
    data.bot_client = TestBotClient()
    data.conversation_registry = ConversationRegistry()
    data.database_provider = TestDatabaseProvider()
    data.dependency_container = TestDependencyContainer()
    data.message_registry = TestMessageRegistry()
    return data


@dataclass
class TestContext:
    """Mutable test context – modify attributes directly."""

    __test__ = False
    bot_data: BotData = field(default_factory=init_bot_data)
    user_data: UserData = field(default_factory=UserData)
    chat_data: ChatData = field(default_factory=ChatData)
    args: list[str] = field(default_factory=list)

    # Additional control for tests
    called_commands: list[str] = field(default_factory=list)

    def record_command(self, command: str) -> None:
        self.called_commands.append(command)
