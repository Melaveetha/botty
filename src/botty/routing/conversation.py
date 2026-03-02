import inspect
from types import MethodType
from typing import Any
from collections.abc import Callable, Generator
from loguru import logger

from ..responses import Answer
from ..di import HandlerResponse
from ..domain import Update
from ..context import ContextProtocol


class Conversation:
    """Base class for all conversations. Provides helper methods."""

    _cancel_command: str = "cancel"

    def __init__(self):
        self._next_step: str | None = None

    def step(self, next_step: str) -> None:
        """Return this to transition to the named step."""
        self._next_step = next_step

    def end(self) -> None:
        """Return this to end the conversation."""
        self._next_step = None

    async def _default_cancel_step(
        self, update: Update, context: ContextProtocol
    ) -> HandlerResponse:
        context.user_data.conversation_data = None
        yield Answer("Conversation canceled")

    async def _default_error_step(
        self, update: Update, context: ContextProtocol, exception: Exception
    ) -> HandlerResponse:
        conversation_data = context.user_data.conversation_data
        if conversation_data is None:
            logger.error(
                "Unexpected error during conversation processing."
                "Conversation data was not set, no way to determine where error occurred."
                f"\n{exception}"
            )
            yield Answer("Unexpected error occurred")
            return
        current_step = conversation_data.step
        class_name: str = conversation_data.class_name

        logger.error(
            f"Error in conversation step '{current_step}' of "
            f"class '{class_name}'"
            f"\nError: {exception}"
        )
        context.user_data.conversation_data = None
        yield Answer("Unexpected error occurred")


def step[F: Callable[..., Any]](method: F) -> F:
    """
    Decorator to mark a method as a regular conversation step.

    Steps are executed in sequence as defined by calls to `self.step(next_step)`
    inside the method. After a step finishes, the framework checks `self._next_step`
    to determine which step to run next.

    To persist data across steps, use the `ConversationState` injectable:

    Example:
        ```python
         @step
        async def ask_age(
            self,
            update: Update,
            context: Context,
            state: ConversationState   # ← automatically injected
        ) -> HandlerResponse:
            name = update.message.text
            state["name"] = name        # ← saved in user_data
            yield Answer(f"Hello {name}, how old are you?")
            self.step("farewell")
        ```

    The state is a plain dictionary that lives in `context.user_data.conversation_data`.
    Any changes made inside a step are automatically persisted.
    """
    method._is_step = True
    method._is_entry = False
    return method


def entry[F: Callable[..., Any]](method: F) -> F:
    """
    Decorator to mark the entry point of a conversation.

    A conversation class must have exactly one method decorated with `@entry`.
    This method is called when the conversation is first started (e.g., via the
    command that triggers it).

    Example:
        ```python
        @entry
        async def start(self, update: Update, context: Context) -> HandlerResponse:
            yield Answer("Welcome! What's your name?")
            self.step("ask_age")
        ```
    """
    method._is_step = True
    method._is_entry = True
    return method


def error[F: Callable[..., Any]](method: F) -> F:
    """
    Decorator to mark an error handler for the conversation.

    If an exception occurs during any step, and an `@error` method is defined,
    it will be called with the same update and context. The conversation then
    ends unless the error method itself calls `self.step(...)`.

    The exception object is injected automatically if the method has a parameter
    of type `Exception` or named `exception`.

    At most one method can be decorated with `@error`. If none is provided, a
    default error handler is used (it logs the error and sends a generic message).

    Example:
        ```python
        @error
        async def handle_error(self, update: Update, context: Context, exception: Exception) -> HandlerResponse:
            yield Answer("Sorry, something went wrong. Please try again.")
            logger.exception(exception)
            self.end()
        ```
    """
    method._is_step = True
    method._is_error = True
    return method


def cancel[F: Callable[..., Any]](method: F) -> F:
    """
    Decorator to mark a cancellation handler for the conversation.

    This method is called when the user sends the cancel command (by default,
    `/cancel`). At most one method can be decorated with `@cancel`. If none is
    provided, a default cancel handler is used (it ends the conversation and
    sends a confirmation message).

    The cancel handler should clean up any state and typically call `self.end()`
    to terminate the conversation. It may also send a goodbye message.

    Example:
        ```python
        @cancel
        async def on_cancel(self, update: Update, context: Context) -> HandlerResponse:
            yield Answer("Operation cancelled. Goodbye!")
            self.end()   # explicitly end the conversation
        ```
    """

    method._is_step = True
    method._is_cancel = True
    return method


def iterate_steps(
    cls: Conversation | type[Conversation],
) -> Generator[tuple[str, MethodType]]:
    for name, method in inspect.getmembers(
        cls,
        predicate=lambda item: getattr(item, "_is_step", False),
    ):
        yield name, method


class ConversationRegistry:
    """Stores mapping from conversation class names to their definitions."""

    def __init__(self):
        self._classes: dict[str, type[Conversation]] = {}

    def register(self, cls: type[Conversation]):
        name = cls.__name__
        if name in self._classes:
            raise ValueError(f"Conversation class '{name}' already registered")
        self._classes[name] = cls

    def get(self, name: str) -> type[Conversation] | None:
        return self._classes.get(name)
