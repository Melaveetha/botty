from botty import Router, Context, Answer, HandlerResponse, Update
from src.repositories.media_repository import MediaRepository

router = Router(name="start")


@router.command("start")
async def start_handler(update: Update, context: Context) -> HandlerResponse:
    text = (
        "🎛️ **Media Master Bot**\n\n"
        "I can send and receive all kinds of media. Try these commands:\n\n"
        "/photo – send a sample photo\n"
        "/doc – send a sample document\n"
        "/audio – send a sample audio file\n"
        "/video – send a sample video\n"
        "/voice – send a voice note\n"
        "/location – share a location\n"
        "/venue – share a venue\n"
        "/contact – share a contact\n"
        "/dice – roll a dice\n"
        "/stats – show your media stats\n\n"
        "You can also send me any photo, document, audio, video, or voice message, and I'll save it!"
    )
    yield Answer(text, parse_mode="Markdown")


@router.command("help")
async def help_handler(update: Update, context: Context) -> HandlerResponse:
    text = (
        "🎛️ **Media Master Bot – Help**\n\n"
        "**Commands to send sample media:**\n"
        "/photo – Send a sample photo\n"
        "/document – Send a sample document (PDF)\n"
        "/audio – Send a sample audio file\n"
        "/video – Send a sample video\n"
        "/voice – Send a voice note\n"
        "/location – Share a test location\n"
        "/venue – Share a test venue\n"
        "/contact – Share a test contact\n"
        "/dice – Roll a dice\n\n"
        "**Working with your own files:**\n"
        "Just send me any photo, document, audio, video, or voice message. "
        "I'll save its file ID and you can retrieve it later.\n"
        "/get 123 – Resend a file you previously uploaded\n"
        "/stats – Show how many files you've sent\n\n"
        "Use /help to see this message again."
    )
    yield Answer(text, parse_mode="Markdown")


@router.command("stats")
async def stats_handler(
    update: Update, context: Context, media_repo: MediaRepository
) -> HandlerResponse:
    files = media_repo.get_user_files(update.effective_user_id)
    if not files:
        yield Answer("You haven't sent any media yet.")
        return
    counts = {}
    for f in files:
        counts[f.file_type] = counts.get(f.file_type, 0) + 1
    lines = ["📊 Your media stats:"]
    for ftype, count in counts.items():
        lines.append(f"  • {ftype}: {count}")
    yield Answer("\n".join(lines))
