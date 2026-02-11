from typing import Annotated, TypeAlias

from telegram import CallbackQuery as TelegramCallbackQuery
from telegram import Chat, Update, User
from telegram import Message as TelegramMessage
from telegram import InlineQuery as TelegramInlineQuery

from ..context import Context
from ..exceptions import (
    EffectiveChatNotFound,
    EffectiveUserNotFound,
    CallbackQueryNotFound,
    InlineQueryNotFound,
)
from ..router import Depends


def _get_effective_user(update: Update, context: Context) -> User:
    if update.effective_user is None:
        raise EffectiveUserNotFound()
    return update.effective_user


EffectiveUser: TypeAlias = Annotated[User, Depends(_get_effective_user)]


def _get_effective_chat(update: Update, context: Context) -> Chat:
    if update.effective_chat is None:
        raise EffectiveChatNotFound()
    return update.effective_chat


EffectiveChat: TypeAlias = Annotated[Chat, Depends(_get_effective_chat)]


def _get_effective_message(update: Update, context: Context) -> TelegramMessage:
    if update.effective_message is None:
        raise EffectiveChatNotFound()
    return update.effective_message


EffectiveMessage: TypeAlias = Annotated[
    TelegramMessage, Depends(_get_effective_message)
]


def _get_callback_quey(update: Update, context: Context) -> TelegramCallbackQuery:
    if update.callback_query is None:
        raise CallbackQueryNotFound()
    return update.callback_query


CallbackQuery: TypeAlias = Annotated[TelegramCallbackQuery, Depends(_get_callback_quey)]


def _get_inline_query(update: Update, context: Context) -> TelegramInlineQuery:
    if update.inline_query is None:
        raise InlineQueryNotFound()
    return update.inline_query


InlineQuery: TypeAlias = Annotated[TelegramInlineQuery, _get_inline_query]

__all__ = ["EffectiveUser", "EffectiveChat", "EffectiveMessage", "CallbackQuery"]
