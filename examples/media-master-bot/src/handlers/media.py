# src/handlers/media_commands.py
from botty import (
    Router,
    Context,
    PhotoAnswer,
    DocumentAnswer,
    AudioAnswer,
    VideoAnswer,
    VoiceAnswer,
    LocationAnswer,
    VenueAnswer,
    ContactAnswer,
    DiceAnswer,
    HandlerResponse,
    Update,
    Answer,
)
from src.repositories.media_repository import MediaRepository

router = Router(name="media_commands")


@router.command("photo")
async def send_photo(
    update: Update, context: Context, media_repo: MediaRepository
) -> HandlerResponse:
    # Send a sample photo from a public API
    yield PhotoAnswer(
        photo="https://picsum.photos/400/300", text="📸 Sample photo (from Picsum)"
    )
    # Store a record (no file_id, just note it's a sample)
    media_repo.add_file(
        user_id=update.effective_user_id,
        file_id="sample_photo",
        file_type="photo",
        caption="Sample photo (Picsum)",
    )


@router.command("document")
async def send_document(
    update: Update, context: Context, media_repo: MediaRepository
) -> HandlerResponse:
    # Sample PDF (a small PDF from the web)
    yield DocumentAnswer(
        document="https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        text="📄 Sample PDF (dummy document)",
        filename="dummy.pdf",
    )
    media_repo.add_file(
        user_id=update.effective_user_id,
        file_id="sample_document",
        file_type="document",
        caption="Sample PDF",
    )


@router.command("audio")
async def send_audio(
    update: Update, context: Context, media_repo: MediaRepository
) -> HandlerResponse:
    # Sample audio (MP3 from the web)
    yield AudioAnswer(
        audio="https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        title="SoundHelix Song 1",
        performer="SoundHelix",
        text="🎵 Sample audio",
    )
    media_repo.add_file(
        user_id=update.effective_user_id,
        file_id="sample_audio",
        file_type="audio",
        caption="Sample audio",
    )


@router.command("video")
async def send_video(
    update: Update, context: Context, media_repo: MediaRepository
) -> HandlerResponse:
    # Sample video (small MP4)
    yield VideoAnswer(
        video="https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4",
        text="🎬 Sample video (flower)",
        supports_streaming=True,
    )
    media_repo.add_file(
        user_id=update.effective_user_id,
        file_id="sample_video",
        file_type="video",
        caption="Sample video",
    )


@router.command("voice")
async def send_voice(
    update: Update, context: Context, media_repo: MediaRepository
) -> HandlerResponse:
    # Sample voice note (OGG)
    yield VoiceAnswer(
        voice="https://www.learningcontainer.com/wp-content/uploads/2020/02/Kalimba.mp3",  # not a real voice note but OGG would be better; using MP3 as placeholder
        text="🗣️ Sample voice note",
    )
    media_repo.add_file(
        user_id=update.effective_user_id,
        file_id="sample_voice",
        file_type="voice",
        caption="Sample voice",
    )


@router.command("location")
async def send_location(update: Update, context: Context) -> HandlerResponse:
    yield LocationAnswer(
        latitude=40.7128, longitude=-74.0060, live_period=60, heading=0
    )
    # No database entry for location


@router.command("venue")
async def send_venue(update: Update, context: Context) -> HandlerResponse:
    yield VenueAnswer(
        latitude=40.7128,
        longitude=-74.0060,
        title="Central Park",
        address="New York, NY",
    )


@router.command("contact")
async def send_contact(update: Update, context: Context) -> HandlerResponse:
    yield ContactAnswer(phone_number="+1234567890", first_name="John", last_name="Doe")


@router.command("dice")
async def send_dice(update: Update, context: Context) -> HandlerResponse:
    yield DiceAnswer(emoji="🎲")


@router.command("get")
async def get_file_command(
    update: Update, context: Context, media_repo: MediaRepository
) -> HandlerResponse:
    if not context.args:
        yield Answer("❌ Usage: /get <file_id>")
        return

    file_id = context.args[0]
    # Look up the file in the database (for this user)
    # (We'll need a method to get a file by file_id and user)
    # For simplicity, we assume we can query by file_id (but file_id is unique anyway)
    media = media_repo.get_by_file_id(file_id)  # you'd need to implement this method
    if not media:
        yield Answer("❌ File not found or doesn't belong to you.")
        return

    # Resend the file based on its type
    match media.file_type:
        case "photo":
            yield PhotoAnswer(photo=media.file_id, text=media.caption)
        case "document":
            yield DocumentAnswer(document=media.file_id, text=media.caption)
        case "audio":
            yield AudioAnswer(audio=media.file_id, text=media.caption)
        case "video":
            yield VideoAnswer(video=media.file_id, text=media.caption)
        case "voice":
            yield VoiceAnswer(voice=media.file_id, text=media.caption)
        case _:
            yield Answer("❌ Unsupported file type.")
