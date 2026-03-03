"""
Testing utilities – test doubles and helpers.
"""

from .bot_client import TestBotClient
from .container import TestDependencyContainer
from .context import TestContext
from .database import TestDatabaseProvider
from .registry import TestMessageRegistry
from .scope import TestRequestScope
from .conversation import ConversationTester

__all__ = [
    "TestBotClient",
    "TestDependencyContainer",
    "TestContext",
    "TestDatabaseProvider",
    "TestMessageRegistry",
    "TestRequestScope",
    "ConversationTester",
]
