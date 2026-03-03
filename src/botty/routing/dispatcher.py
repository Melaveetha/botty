from types import MethodType
from loguru import logger
from telegram import Update as PTBUpdate
from telegram.ext import (
    Application,
    ApplicationHandlerStop,
    BaseHandler,
    CallbackContext,
    ExtBot,
)

from ..adapters import PTBIncomingAdapter
from ..context import BotData, ChatData, Context, ContextProtocol, UserData
from ..di import RequestScope
from .conversation import Conversation, iterate_steps
from .executor import execute_callable


class ConversationDispatcher(BaseHandler[PTBUpdate, Context, None]):
    """
    Dispatcher that manages active conversations.

    This handler runs with the highest priority (group 0) and checks for an
    ongoing conversation in `user_data`. If a conversation exists, it executes
    the current step, updates the conversation state, and stops propagation
    so that no other handlers process the update.
    """

    def __init__(self):
        """
        Initialize the dispatcher with a conversation registry.

        Args:
            registry: Registry that maps conversation class names to their
                      definitions. This is typically stored in `bot_data`.
        """

        # Provide a dummy callback (required by BaseHandler). The real work
        # happens in `handle_update`.
        async def _dummy_callback(update: PTBUpdate, context: CallbackContext) -> None:
            pass

        super().__init__(_dummy_callback, block=True)

    def check_update(self, update: object) -> bool:
        """
        Accept all updates; the actual filtering is done by inspecting
        `user_data` inside `handle_update`.
        """
        return True

    async def handle_update(
        self,
        update: PTBUpdate,
        application: Application[ExtBot, Context, BotData, UserData, ChatData, None],
        check_result: object,
        context: ContextProtocol,
    ) -> None:
        """
        Process an update: if a conversation is active, run its current step
        and stop propagation. Otherwise, do nothing.
        """
        logger.trace(f"Processing update {update.update_id}")
        if context.user_data is None:
            logger.debug("No user data – passing through")
            return
        conversation_data = context.user_data.conversation_data
        if not conversation_data:
            logger.debug("No active conversation – passing through")
            return

        class_name: str = conversation_data.class_name
        conversation_class = context.bot_data.conversation_registry.get(class_name)

        if conversation_class is None:
            logger.warning(
                f"Conversation class '{class_name}' not found in registry. "
                "Clearing invalid state."
            )
            context.user_data.conversation_data = None
            return

        # Check if cancel command was called
        cancel_step: str | None = None
        if (
            update.effective_message
            and update.effective_message.text
            and update.effective_message.text.startswith("/")
        ):
            command = update.effective_message.text[1:].split()[0]
            if command == conversation_class._cancel_command:
                cancel_step = "_default_cancel_step"
                for name, method in iterate_steps(conversation_class):
                    if getattr(method, "_is_cancel", False):
                        cancel_step = name

        current_step = conversation_data.step
        try:
            await _run_conversation_step(
                conversation_class,
                cancel_step or current_step,
                update,
                context,
            )
        except Exception as exception:
            error_step = "_default_error_step"
            for name, method in iterate_steps(conversation_class):
                if getattr(method, "_is_error", False):
                    error_step = name
            try:
                await _run_conversation_step(
                    conversation_class, error_step, update, context, exception
                )
            except Exception as e:
                logger.error(
                    f"Error during error_step processing for conversation `{conversation_class.__name__}`."
                    f"Error method is `{error_step}`."
                    f"\n\nThis error occurred during handling following error: {e}"
                )
                context.user_data.conversation_data = None
        raise ApplicationHandlerStop()


async def _run_conversation_step(
    conv_class: type[Conversation],
    step_name: str,
    ptb_update: PTBUpdate,
    context: ContextProtocol,
    exception: Exception | None = None,
) -> None:
    """
    Execute a single step of a conversation.

    This function is responsible for:
      - Instantiating the conversation class (no arguments).
      - Building a RequestScope.
      - Calling the step method (async generator) and processing responses.

    It is shared between ConversationDispatcher and the command handler
    that starts a conversation.
    """
    if context.user_data.conversation_data is None:
        return

    adapter = PTBIncomingAdapter()
    update = adapter.from_ptb(ptb_update)

    scope = RequestScope(update, context, exception)

    conversation = conv_class()

    method: MethodType | None = getattr(conversation, step_name)

    await execute_callable(method, scope, step_name, conversation)

    next_step = conversation._next_step

    if next_step is None:
        context.user_data.conversation_data = None
        return

    context.user_data.conversation_data.step = next_step
