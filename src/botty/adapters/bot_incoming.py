from telegram import Update as PTBUpdate

from ..domain import (
    CallbackQuery,
    EditedMessage,
    EffectiveChat,
    EffectiveMessage,
    EffectiveUser,
    Poll,
    PollAnswer,
    Update,
)


class PTBIncomingAdapter:
    @staticmethod
    def from_ptb(update: PTBUpdate) -> Update:
        user = None
        if update.effective_user:
            user = EffectiveUser(
                id=update.effective_user.id,
                first_name=update.effective_user.first_name,
                username=update.effective_user.username,
            )
        chat = None
        if update.effective_chat:
            chat = EffectiveChat(
                id=update.effective_chat.id,
                type=update.effective_chat.type,
            )
        message = None
        if update.effective_message:
            message = EffectiveMessage(
                message_id=update.effective_message.message_id,
                chat_id=update.effective_message.chat_id,
                date=update.effective_message.date,
                text=update.effective_message.text,
            )
        callback_query = None
        if update.callback_query:
            message_id: int | None = None
            chat_id: int | None = None
            if update.callback_query.message:
                message_id = update.callback_query.message.message_id
                chat_id = update.callback_query.message.chat.id
            callback_query = CallbackQuery(
                id=update.callback_query.id,
                data=update.callback_query.data,
                user_id=update.callback_query.from_user.id,
                message_id=message_id,
                chat_id=chat_id,
            )

        edited_message = None
        if update.edited_message:
            edited_message = EditedMessage(
                message_id=update.edited_message.id,
                chat_id=update.edited_message.chat_id,
                date=update.edited_message.date,
                edit_date=update.edited_message.edit_date,
                text=update.edited_message.text,
            )

        poll = None
        if update.poll:
            poll = Poll(
                id=update.poll.id,
                question=update.poll.question,
                options=list(update.poll.options),
                total_voter_count=update.poll.total_voter_count,
                is_closed=update.poll.is_closed,
                is_anonymous=update.poll.is_anonymous,
                type=update.poll.type,
                allows_multiple_answers=update.poll.allows_multiple_answers,
            )

        poll_answer = None
        if update.poll_answer:
            poll_answer = PollAnswer(
                poll_id=update.poll_answer.poll_id,
                option_ids=list(update.poll_answer.option_ids),
                user=EffectiveUser(
                    id=update.poll_answer.user.id,
                    first_name=update.poll_answer.user.first_name,
                    username=update.poll_answer.user.username,
                )
                if update.poll_answer.user
                else None,
            )

        return Update(
            update_id=update.update_id,
            user=user,
            chat=chat,
            message=message,
            callback_query=callback_query,
            edited_message=edited_message,
            poll=poll,
            poll_answer=poll_answer,
        )
