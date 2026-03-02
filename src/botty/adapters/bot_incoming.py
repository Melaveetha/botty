from telegram import (
    Audio as PTBAudio,
)
from telegram import (
    Document as PTBDocument,
)
from telegram import (
    PhotoSize as PTBPhotoSize,
)
from telegram import (
    Update as PTBUpdate,
)
from telegram import (
    Video as PTBVideo,
)
from telegram import Voice as PTBVoice, Location as PTBLocation, Contact as PTBContact

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
from ..domain.entities import (
    Audio,
    Document,
    PhotoSize,
    Video,
    Voice,
    Location,
    Contact,
)


def _convert_photo_size(ps: PTBPhotoSize) -> PhotoSize:
    return PhotoSize(
        file_id=ps.file_id,
        file_unique_id=ps.file_unique_id,
        width=ps.width,
        height=ps.height,
        file_size=ps.file_size,
    )


def _convert_document(doc: PTBDocument | None) -> Document | None:
    if not doc:
        return None
    thumb = _convert_photo_size(doc.thumbnail) if doc.thumbnail else None
    return Document(
        file_id=doc.file_id,
        file_unique_id=doc.file_unique_id,
        file_name=doc.file_name,
        mime_type=doc.mime_type,
        file_size=doc.file_size,
        thumbnail=thumb,
    )


def _convert_video(video: PTBVideo | None) -> Video | None:
    if not video:
        return None
    thumb = _convert_photo_size(video.thumbnail) if video.thumbnail else None
    return Video(
        file_id=video.file_id,
        file_unique_id=video.file_unique_id,
        width=video.width,
        height=video.height,
        duration=video.duration,
        thumbnail=thumb,
        file_name=video.file_name,
        mime_type=video.mime_type,
        file_size=video.file_size,
    )


def _convert_audio(audio: PTBAudio | None) -> Audio | None:
    if not audio:
        return None
    thumb = _convert_photo_size(audio.thumbnail) if audio.thumbnail else None
    return Audio(
        file_id=audio.file_id,
        file_unique_id=audio.file_unique_id,
        duration=audio.duration,
        performer=audio.performer,
        title=audio.title,
        file_name=audio.file_name,
        mime_type=audio.mime_type,
        file_size=audio.file_size,
        thumbnail=thumb,
    )


def _convert_voice(voice: PTBVoice | None) -> Voice | None:
    if not voice:
        return None
    return Voice(
        file_id=voice.file_id,
        file_unique_id=voice.file_unique_id,
        duration=voice.duration,
        mime_type=voice.mime_type,
        file_size=voice.file_size,
    )


def _convert_location(location: PTBLocation | None) -> Location | None:
    if not location:
        return None
    return Location(
        longitude=location.longitude,
        latitude=location.latitude,
        horizontal_accuracy=location.horizontal_accuracy,
        live_period=location.live_period,
        heading=location.heading,
        proximity_alert_radius=location.proximity_alert_radius,
    )


def _convert_contact(contact: PTBContact | None) -> Contact | None:
    if not contact:
        return None
    return Contact(
        phone_number=contact.phone_number,
        first_name=contact.first_name,
        last_name=contact.last_name,
        user_id=contact.user_id,
        vcard=contact.vcard,
    )


class PTBIncomingAdapter:
    """Adapter to convert python-telegram-bot Update objects into botty domain Update objects.

    This adapter extracts information from a PTB Update and constructs
    a botty Update entity, which is then used throughout the
    application layer.
    """

    @staticmethod
    def from_ptb(update: PTBUpdate) -> Update:
        """Convert a PTB Update to a botty domain Update.

        Args:
            update: The incoming Update from python-telegram-bot.

        Returns:
            A domain Update object containing extracted user, chat, message,
            callback query, edited message, poll, and poll answer data.

        Note:
            If a particular field is not present in the PTB update, the
            corresponding domain field will be set to None.
        """
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
            photo = None
            if update.effective_message.photo:
                photo = [
                    _convert_photo_size(photo)
                    for photo in update.effective_message.photo
                ]

            message = EffectiveMessage(
                message_id=update.effective_message.message_id,
                chat_id=update.effective_message.chat_id,
                date=update.effective_message.date,
                text=update.effective_message.text or update.effective_message.caption,
                photo=photo,
                document=_convert_document(update.effective_message.document),
                video=_convert_video(update.effective_message.video),
                audio=_convert_audio(update.effective_message.audio),
                voice=_convert_voice(update.effective_message.voice),
                location=_convert_location(update.effective_message.location),
                contact=_convert_contact(update.effective_message.contact),
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
                _answer=update.callback_query.answer,
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
