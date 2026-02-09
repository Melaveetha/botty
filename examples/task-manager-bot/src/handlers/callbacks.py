from botty import (
    Router,
    Context,
    Answer,
    EditAnswer,
    HandlerResponse,
    Update,
    CallbackQuery,
    EffectiveUser,
)

from src.repositories.task_repository import TaskRepositoryDependency
from src.repositories.user_repository import UserRepositoryDependency

router = Router(name="callbacks")


@router.callback_query(pattern=r"^task_done_(\d+)$")
async def task_done_callback(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
    query: CallbackQuery,
    effective_user: EffectiveUser,
) -> HandlerResponse:
    """
    Handle callback when user clicks 'Mark Done' button.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
    """
    await query.answer()

    # Get user
    user = user_repo.get_by_telegram_id(effective_user.id)
    if not user:
        yield Answer(text="❌ User not found.")
        return

    # Extract task ID from callback data
    task_id = int(query.data.split("_")[2])

    # Get and verify task
    task = task_repo.get(task_id)
    if not task or task.user_id != user.id:
        yield Answer(text="❌ Task not found.")
        return

    # Mark as complete
    task = task_repo.mark_complete(task_id, completed=True)

    if task is None:
        yield EditAnswer(text="Couldn't find task")
        return

    # Update message
    yield EditAnswer(
        text=f"✅ <b>Task Completed!</b>\n\n<s>{task.title}</s>", parse_mode="HTML"
    )


@router.callback_query(pattern=r"^task_delete_(\d+)$")
async def task_delete_callback(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
    query: CallbackQuery,
    effective_user: EffectiveUser,
) -> HandlerResponse:
    """
    Handle callback when user clicks 'Delete' button.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
    """
    await query.answer()

    # Get user
    user = user_repo.get_by_telegram_id(effective_user.id)
    if not user:
        yield Answer(text="❌ User not found.")
        return

    # Extract task ID from callback data
    task_id = int(query.data.split("_")[2])

    # Get and verify task
    task = task_repo.get(task_id)
    if not task or task.user_id != user.id:
        yield Answer(text="❌ Task not found.")
        return

    # Delete task
    task_repo.delete(task_id)

    # Update message
    yield EditAnswer(
        text=f"🗑️ <b>Task Deleted</b>\n\n<s>{task.title}</s>", parse_mode="HTML"
    )


@router.callback_query(pattern=r"^refresh_list$")
async def refresh_list_callback(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
    query: CallbackQuery,
    effective_user: EffectiveUser,
) -> HandlerResponse:
    """
    Handle callback to refresh task list.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
    """
    yield Answer("Refreshing...")

    # Get user
    user = user_repo.get_by_telegram_id(effective_user.id)
    if user is None:
        yield Answer(text="❌ User not found.")
        return

    # Get tasks
    tasks = task_repo.get_pending_tasks(user.id)

    if not tasks:
        yield EditAnswer(text="✅ <b>All tasks completed!</b>", parse_mode="HTML")
        return

    # Format task list
    lines = ["📋 <b>Your Tasks:</b>\n"]
    for task in tasks:
        lines.append(f"  {task.format_for_display()}")

    yield EditAnswer(text="\n".join(lines), parse_mode="HTML")
