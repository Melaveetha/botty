from typing import Annotated, TypeAlias

from .context import ContextProtocol
from .di import Depends
from .domain import CallbackQuery as BottyCallbackQuery
from .domain import EditedMessage as BottyEditedMessage
from .domain import EffectiveChat as Chat
from .domain import EffectiveMessage as Message
from .domain import EffectiveUser as User
from .domain import Poll as BottyPoll
from .domain import PollAnswer as BottyPollAnswer
from .domain import Update
from .exceptions import (
    CallbackQueryNotFound,
    EditedMessageNotFound,
    EffectiveChatNotFound,
    EffectiveUserNotFound,
    PollAnswerNotFound,
    PollNotFound,
)


def _get_effective_user(update: Update, context: ContextProtocol) -> User:
    if update.user is None:
        raise EffectiveUserNotFound()
    return update.user


EffectiveUser: TypeAlias = Annotated[User, Depends(_get_effective_user)]


def _get_effective_chat(update: Update, context: ContextProtocol) -> Chat:
    if update.chat is None:
        raise EffectiveChatNotFound()
    return update.chat


EffectiveChat: TypeAlias = Annotated[Chat, Depends(_get_effective_chat)]


def _get_effective_message(update: Update, context: ContextProtocol) -> Message:
    if update.message is None:
        raise EffectiveChatNotFound()
    return update.message


EffectiveMessage: TypeAlias = Annotated[Message, Depends(_get_effective_message)]


def _get_callback_query(update: Update, context: ContextProtocol) -> BottyCallbackQuery:
    if update.callback_query is None:
        raise CallbackQueryNotFound()
    return update.callback_query


CallbackQuery: TypeAlias = Annotated[BottyCallbackQuery, Depends(_get_callback_query)]


def _get_edited_message(update: Update, context: ContextProtocol) -> BottyEditedMessage:
    if update.edited_message is None:
        raise EditedMessageNotFound()
    return update.edited_message


EditedMessage: TypeAlias = Annotated[BottyEditedMessage, Depends(_get_edited_message)]


def _get_poll(update: Update, context: ContextProtocol) -> BottyPoll:
    if update.poll is None:
        raise PollNotFound()
    return update.poll


Poll: TypeAlias = Annotated[BottyPoll, Depends(_get_poll)]


def _get_poll_answer(update: Update, context: ContextProtocol) -> BottyPollAnswer:
    if update.poll_answer is None:
        raise PollAnswerNotFound()
    return update.poll_answer


PollAnswer: TypeAlias = Annotated[BottyPollAnswer, Depends(_get_poll_answer)]

# TODO: support for inline queries

__all__ = ["EffectiveUser", "EffectiveChat", "EffectiveMessage", "CallbackQuery"]
