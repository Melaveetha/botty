from botty import Answer, Context, HandlerResponse, Router, Update
from src.dependencies import CurrentUser

router = Router(name="profile")


@router.command("profile")
async def profile_command(
    update: Update,
    context: Context,
    current_user: CurrentUser,  # <-- injected via Depends
) -> HandlerResponse:
    if current_user is None:
        yield Answer("❌ You are not registered. Use /start to begin.")
        return

    yield Answer(
        f"👤 <b>Your Profile</b>\n\n"
        f"ID: {current_user.id}\n"
        f"Telegram ID: {current_user.telegram_id}\n"
        f"Name: {current_user.full_name}\n"
        f"Username: @{current_user.username}\n"
        f"Joined: {current_user.created_at.strftime('%Y-%m-%d')}",
        parse_mode="HTML",
    )
