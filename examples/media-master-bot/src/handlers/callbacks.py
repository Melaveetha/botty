# src/handlers/receive_media.py
from telegram.ext import filters
from botty import (
    Router,
    Context,
    HandlerResponse,
    Update,
    InjectableMessage,
    DocumentAnswer,
    PhotoAnswer,
    AudioAnswer,
    VideoAnswer,
    VoiceAnswer,
)
from src.repositories.media_repository import MediaRepository

router = Router(name="receive_media")


@router.message(filters.PHOTO)
async def handle_photo(
    update: Update,
    context: Context,
    message: InjectableMessage,
    media_repo: MediaRepository,
) -> HandlerResponse:
    photo = message.photo[-1]  # largest size
    media_repo.add_file(
        user_id=update.effective_user_id,
        file_id=photo.file_id,
        file_type="photo",
        caption=message.text,
    )
    # Echo the photo back with confirmation
    yield PhotoAnswer(
        photo=photo.file_id,
        caption=f"✅ Photo saved! File ID: `{photo.file_id}`\nUse /get {photo.file_id} to retrieve it.",
    )


@router.message(filters.Document.ALL)
async def handle_document(
    update: Update,
    context: Context,
    message: InjectableMessage,
    media_repo: MediaRepository,
) -> HandlerResponse:
    doc = message.document
    media_repo.add_file(
        user_id=update.effective_user_id,
        file_id=doc.file_id,
        file_type="document",
        caption=doc.file_name,
    )
    yield DocumentAnswer(
        document=doc.file_id, caption=f"✅ Document saved! File ID: `{doc.file_id}`"
    )


@router.message(filters.AUDIO)
async def handle_audio(
    update: Update,
    context: Context,
    message: InjectableMessage,
    media_repo: MediaRepository,
) -> HandlerResponse:
    audio = message.audio
    media_repo.add_file(
        user_id=update.effective_user_id,
        file_id=audio.file_id,
        file_type="audio",
        caption=audio.file_name,
    )
    yield AudioAnswer(
        audio=audio.file_id, caption=f"✅ Document saved! File ID: `{audio.file_id}`"
    )


@router.message(filters.VIDEO)
async def handle_video(
    update: Update,
    context: Context,
    message: InjectableMessage,
    media_repo: MediaRepository,
) -> HandlerResponse:
    video = message.video
    media_repo.add_file(
        user_id=update.effective_user_id,
        file_id=video.file_id,
        file_type="video",
        caption=video.file_name,
    )
    yield VideoAnswer(
        video=video.file_id, caption=f"✅ Document saved! File ID: `{video.file_id}`"
    )


@router.message(filters.VOICE)
async def handle_voice(
    update: Update,
    context: Context,
    message: InjectableMessage,
    media_repo: MediaRepository,
) -> HandlerResponse:
    voice = message.voice
    media_repo.add_file(
        user_id=update.effective_user_id,
        file_id=voice.file_id,
        file_type="voice",
        caption=voice.file_name,
    )
    yield VoiceAnswer(
        voice=voice.file_id, caption=f"✅ Document saved! File ID: `{voice.file_id}`"
    )
