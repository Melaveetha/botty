from loguru import logger
from collections.abc import AsyncGenerator

from telegram import Update, Message

from .registry import MessageRegistry
from ..exceptions import ChatIdNotFoundError, ResponseProcessingError
from ..context import Context
from .handlers import (
    BaseAnswer,
    Answer,
    EditAnswer,
    PhotoAnswer,
    DocumentAnswer,
    AudioAnswer,
    VideoAnswer,
    VoiceAnswer,
    LocationAnswer,
    VenueAnswer,
    ContactAnswer,
    PollAnswer,
    DiceAnswer,
    EmptyAnswer,
)


class ResponseProcessor:
    """
    Processes responses from handlers (Answer, EditPrevious, etc.).
    Handles message sending, editing, and registry updates.
    """

    def __init__(self, registry: MessageRegistry):
        self.registry = registry

    async def process_async_generator(
        self,
        generator: AsyncGenerator[BaseAnswer, None],
        update: Update,
        context: Context,
        handler_name: str,
    ) -> None:
        """
        Process an async generator that yields Answer/EditPrevious objects.

        Args:
            generator: Async generator yielding response objects
            update: Telegram update object
            context: Telegram context object
            handler_name: Name of the handler function for registry tracking
        """
        chat_id = self._get_chat_id(update)

        async for response in generator:
            try:
                await self._process_single_response(
                    response, update, context, chat_id, handler_name
                )
            except Exception as e:
                logger.exception(
                    f"Error processing response in handler '{handler_name}': {e}"
                )
                # Continue processing other responses even if one fails
                continue

    @staticmethod
    def _get_chat_id(update: Update) -> int:
        """Extract chat ID from update with comprehensive fallback logic."""
        if update.message:
            return update.message.chat.id
        elif update.callback_query and update.callback_query.message:
            return update.callback_query.message.chat.id
        elif update.inline_query:
            return update.inline_query.from_user.id
        elif update.channel_post:
            return update.channel_post.chat.id
        elif update.edited_message:
            return update.edited_message.chat.id
        elif update.effective_chat:
            return update.effective_chat.id
        else:
            raise ChatIdNotFoundError()

    async def _process_single_response(
        self,
        answer: BaseAnswer,
        update: Update,
        context: Context,
        chat_id: int,
        handler_name: str,
    ) -> None:
        """Process a single response object."""
        try:
            if isinstance(answer, EditAnswer):
                await self._handle_edit_previous(
                    answer, update, context, chat_id, handler_name
                )

            else:
                await self._send_message(answer, update, handler_name)
        except Exception as e:
            raise ResponseProcessingError(
                f"Failed to process response in handler '{handler_name}': {e}",
                response_type=type(answer).__name__,
                handler_name=handler_name,
            ) from e

    async def _send_message(
        self,
        answer: BaseAnswer,
        update: Update,
        handler_name: str,
    ) -> Message | None:
        if update.effective_chat is None:
            logger.warning(
                f"Couldn't send message {answer.message_key}: effective_chat is None"
            )
            return

        try:
            match answer:
                case Answer():
                    message = await update.effective_chat.send_message(
                        **answer.to_dict()
                    )
                case PhotoAnswer():
                    message = await update.effective_chat.send_photo(**answer.to_dict())
                case DocumentAnswer():
                    message = await update.effective_chat.send_document(
                        **answer.to_dict()
                    )
                case AudioAnswer():
                    message = await update.effective_chat.send_audio(**answer.to_dict())
                case VideoAnswer():
                    message = await update.effective_chat.send_video(**answer.to_dict())
                case VoiceAnswer():
                    message = await update.effective_chat.send_voice(**answer.to_dict())
                case LocationAnswer():
                    message = await update.effective_chat.send_location(
                        **answer.to_dict()
                    )
                case VenueAnswer():
                    message = await update.effective_chat.send_venue(**answer.to_dict())
                case ContactAnswer():
                    message = await update.effective_chat.send_contact(
                        **answer.to_dict()
                    )
                case PollAnswer():
                    message = await update.effective_chat.send_poll(**answer.to_dict())
                case DiceAnswer():
                    message = await update.effective_chat.send_dice(**answer.to_dict())
                case EmptyAnswer():
                    logger.debug(f"Handler '{handler_name}' yielded EmptyAnswer")
                    return None
                case _:
                    logger.warning(
                        f"Received unknown message type: {type(answer)} in message {answer.message_key}"
                    )

            # Register the message for future reference
            self.registry.register_message(
                message=message,
                handler_name=answer.handler_name or handler_name,
                key=answer.message_key,
                metadata=answer.metadata,
            )

            logger.debug(
                f"Sent message {message.message_id} from handler '{handler_name}'"
            )

        except Exception as e:
            logger.exception(f"Failed to send message `{answer.message_key}`: {e}")
            raise

    async def _handle_edit_previous(
        self,
        response: EditAnswer,
        update: Update,
        context: Context,
        chat_id: int,
        handler_name: str,
    ) -> None:
        """Handle EditPrevious response - edit an existing message."""
        message_id = self._find_message_to_edit(response, chat_id, handler_name)

        if message_id is None:
            # No message found to edit, send new message
            if update.effective_chat is None:
                return
            message = await update.effective_chat.send_message(**response.to_dict())
            logger.debug(
                f"Sent new message {message.message_id} (no previous message to edit)"
            )
            return
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id, message_id=message_id, **response.to_dict()
            )
            logger.debug(f"Edited message {message_id} from handler '{handler_name}'")
        except Exception as e:
            logger.exception(f"Failed to edit message {message_id}: {e}")
            # Fall back to sending new message
            if update.effective_chat is None:
                return
            message = await update.effective_chat.send_message(**response.to_dict())
            logger.debug(f"Sent new message {message.message_id} after edit failed")

    def _find_message_to_edit(
        self, response: EditAnswer, chat_id: int, handler_name: str
    ) -> int | None:
        """
        Find the message ID to edit based on response criteria.

        Priority:
        1. Direct message ID
        2. Message key lookup
        3. Handler name lookup
        4. Last message in chat
        """
        # 1. Direct message ID
        if response.message_id is not None:
            return response.message_id

        # 2. Message key lookup
        if response.message_key is not None:
            record = self.registry.get_by_key(response.message_key)
            if record is not None and record.chat_id == chat_id:
                return record.message_id

        # 3. Handler name was specified by user
        if response.handler_name is not None:
            records = self.registry.get_by_handler(response.handler_name, chat_id)
            if len(records) > 0:
                return records[-1].message_id

        # 4. Last message from current handler
        records = self.registry.get_by_handler(handler_name, chat_id)
        if len(records) > 0:
            return records[-1].message_id

        # 5. Last message in chat (fallback)
        last_message = self.registry.get_last_message(chat_id)
        if last_message is not None:
            return last_message.message_id

        return None
