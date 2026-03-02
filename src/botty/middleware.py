from typing import TypeAlias
from .context import ContextProtocol
from .domain import Update
from .responses import BaseAnswer
from collections.abc import Callable, AsyncGenerator

Middleware: TypeAlias = Callable[
    [Update, ContextProtocol, AsyncGenerator[BaseAnswer, None]],
    AsyncGenerator[BaseAnswer, None],
]
