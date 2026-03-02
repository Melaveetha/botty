from telegram.ext import filters
from botty import Router, Context, Answer, HandlerResponse, Update, InjectableMessage
from src.repositories.media_repository import MediaRepository
from src.services.file_service import FileService

router = Router(name="receive_media")


@router.message(filters.PHOTO)
async def handle_photo(
    update: Update,
    context: Context,
    message: InjectableMessage,
    media_repo: MediaRepository,
    file_svc: FileService,
) -> HandlerResponse:
    photo = message.photo[-1]
    caption = message.text or "No caption"
    media_repo.add_file(update.effective_user_id, photo.file_id, "photo", caption)
    file_svc.store_file_info(photo.file_id, "photo", caption)
    yield Answer(f"✅ Photo saved! File ID: `{photo.file_id}`", parse_mode="Markdown")


@router.message(filters.Document.ALL)
async def handle_document(
    update: Update,
    context: Context,
    message: InjectableMessage,
    media_repo: MediaRepository,
    file_svc: FileService,
) -> HandlerResponse:
    doc = message.document
    media_repo.add_file(
        update.effective_user_id, doc.file_id, "document", doc.file_name
    )
    file_svc.store_file_info(doc.file_id, "document", doc.file_name)
    yield Answer(
        f"✅ Document saved: `{doc.file_name}`. File ID: `{doc.file_id}`",
        parse_mode="Markdown",
    )
