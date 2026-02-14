from typing import Annotated, TypeAlias

from .context import ContextProtocol
from .di import Depends
from .domain import (
    CallbackQuery,
    EditedMessage,
    EffectiveChat,
    EffectiveMessage,
    EffectiveUser,
    Poll,
    PollAnswer,
    Update,
)
from .exceptions import (
    CallbackQueryNotFound,
    EditedMessageNotFound,
    EffectiveChatNotFound,
    EffectiveUserNotFound,
    PollAnswerNotFound,
    PollNotFound,
    EffectiveMessageNotFound,
)


def _get_effective_user(update: Update, context: ContextProtocol) -> EffectiveUser:
    if update.user is None:
        raise EffectiveUserNotFound()
    return update.user


InjectableUser: TypeAlias = Annotated[EffectiveUser, Depends(_get_effective_user)]
"""Type hint for injecting the effective user.

Use this annotation in handler parameters to get the user object.
Raises EffectiveUserNotFound if the update lacks a user.

Example:
    ```python
    async def handler(..., user: InjectableUser):
        print(user.id)
    ```
"""


def _get_effective_chat(update: Update, context: ContextProtocol) -> EffectiveChat:
    if update.chat is None:
        raise EffectiveChatNotFound()
    return update.chat


InjectableChat: TypeAlias = Annotated[EffectiveChat, Depends(_get_effective_chat)]
"""Type hint for injecting the effective chat.

Use this annotation in handler parameters to get the chat object.
Raises EffectiveChatNotFound if the update lacks a chat.

Example:
    ```python
    async def handler(..., chat: InjectableChat):
        print(chat.id)
    ```
"""


def _get_effective_message(
    update: Update, context: ContextProtocol
) -> EffectiveMessage:
    if update.message is None:
        raise EffectiveMessageNotFound()
    return update.message


InjectableMessage: TypeAlias = Annotated[
    EffectiveMessage, Depends(_get_effective_message)
]
"""Type hint for injecting the effective message.

Use this annotation in handler parameters to get the message object.
Raises EffectiveMessageNotFound if the update lacks a message.

Example:
    ```python
    async def handler(..., message: InjectableMessage):
        print(message.id)
    ```
"""


def _get_callback_query(update: Update, context: ContextProtocol) -> CallbackQuery:
    if update.callback_query is None:
        raise CallbackQueryNotFound()
    return update.callback_query


InjectableCallbackQuery: TypeAlias = Annotated[
    CallbackQuery, Depends(_get_callback_query)
]
"""Type hint for injecting the callback query.

Use this annotation in handler parameters to get the callback query object.
Raises CallbackQueryNotFound if the update lacks a callback query.

Example:
    ```python
    async def handler(..., callback_query: InjectableCallbackQuery):
        print(callback_query.name)
    ```
"""


def _get_edited_message(update: Update, context: ContextProtocol) -> EditedMessage:
    if update.edited_message is None:
        raise EditedMessageNotFound()
    return update.edited_message


InjectableEditedMessage: TypeAlias = Annotated[
    EditedMessage, Depends(_get_edited_message)
]
"""Type hint for injecting the edited message.

Use this annotation in handler parameters to get the edited message object.
Raises EditedMessageNotFound if the update lacks a edited message.

Example:
    ```python
    async def handler(..., message: InjectableEditedMessage):
        print(message.id)
    ```
"""


def _get_poll(update: Update, context: ContextProtocol) -> Poll:
    if update.poll is None:
        raise PollNotFound()
    return update.poll


InjectablePoll: TypeAlias = Annotated[Poll, Depends(_get_poll)]
"""Type hint for injecting the poll.

Use this annotation in handler parameters to get the pool object.
Raises PollNotFound if the update lacks a pool.

Example:
    ```python
    async def handler(..., poll: InjectablePoll):
        print(poll.id)
    ```
"""


def _get_poll_answer(update: Update, context: ContextProtocol) -> PollAnswer:
    if update.poll_answer is None:
        raise PollAnswerNotFound()
    return update.poll_answer


InjectablePollAnswer: TypeAlias = Annotated[PollAnswer, Depends(_get_poll_answer)]
"""Type hint for injecting the poll answer.

Use this annotation in handler parameters to get the pool answer object.
Raises PollAnswerNotFound if the update lacks a pool answer.

Example:
    ```python
    async def handler(..., poll_answer: InjectablePollAnswer):
        print(poll_answer.id)
    ```
"""

# TODO: support for inline queries

__all__ = [
    InjectableUser,
    InjectableChat,
    InjectableMessage,
    InjectableCallbackQuery,
    InjectableEditedMessage,
    InjectablePoll,
    InjectablePollAnswer,
]
