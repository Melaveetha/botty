from dataclasses import dataclass, field

from botty.context import BotData, ChatData, UserData


@dataclass
class TestContext:
    """Mutable test context – modify attributes directly."""

    __test__ = False
    bot_data: BotData = field(default_factory=BotData)
    user_data: UserData = field(default_factory=UserData)
    chat_data: ChatData = field(default_factory=ChatData)
    args: list[str] = field(default_factory=list)

    # Additional control for tests
    called_commands: list[str] = field(default_factory=list)

    def record_command(self, command: str) -> None:
        self.called_commands.append(command)
