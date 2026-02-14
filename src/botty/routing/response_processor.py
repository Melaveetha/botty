from loguru import logger

from ..di import HandlerResponse
from ..domain import Message
from ..exceptions import ChatIdNotFoundError, ResponseProcessingError
from ..ports.bot_client import TelegramBotClient
from ..responses import (
    BaseAnswer,
    EditAnswer,
    EmptyAnswer,
)
from .registry import MessageRegistry


class ResponseProcessor:
    """
    Processes responses from handlers (Answer, EditPrevious, etc.).
    Handles message sending, editing, and registry updates.
    """

    def __init__(self, registry: MessageRegistry, client: TelegramBotClient):
        self.registry: MessageRegistry = registry
        self.client: TelegramBotClient = client

    async def process_async_generator(
        self,
        generator: HandlerResponse,
        chat_id: int,
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

        async for response in generator:
            try:
                await self._process_single_response(response, chat_id, handler_name)
            except ResponseProcessingError as e:
                logger.exception(
                    f"Error processing response in handler '{handler_name}': {e}"
                )
                # TODO: add retry logic
                continue
            except ChatIdNotFoundError as e:
                logger.exception(
                    f"Couldn't get chat id in handler '{handler_name}': {e}"
                )
                continue

    async def _process_single_response(
        self,
        answer: BaseAnswer,
        chat_id: int,
        handler_name: str,
    ) -> Message | None:
        try:
            if isinstance(answer, EditAnswer):
                message_id: int | None = self.registry.find_message_to_edit(
                    answer, chat_id, handler_name
                )
                message = await self.client.edit(chat_id, message_id, answer)
                if message is None:
                    return None
            else:
                message = await self.client.send(chat_id, answer)

            if message is None:
                if not isinstance(answer, EmptyAnswer):
                    logger.warning(
                        f"Message was not sent: {answer.handler_name or handler_name}"
                    )
                return None

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
            raise ResponseProcessingError(
                f"Failed to send message `{answer.message_key}`: {e}",
                response_type=type(answer).__name__,
                handler_name=handler_name,
            ) from e
