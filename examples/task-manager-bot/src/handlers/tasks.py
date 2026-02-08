from botty import Router, Context, Answer, EditAnswer, HandlerResponse, Update

from src.repositories.task_repository import TaskRepositoryDependency
from src.repositories.user_repository import UserRepositoryDependency
from src.services.task_service import TaskServiceDependency

router = Router(name="tasks")


@router.command(["add", "new"])
async def new_task_command(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
    task_service: TaskServiceDependency,
) -> HandlerResponse:
    """
    Handle /new and /add commands - create a new task.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
        task_service: Injected task service
    """
    # Get user
    user = user_repo.get_by_telegram_id(update.effective_user.id)
    if not user:
        yield Answer(text="❌ User not found. Please /start first.")
        return

    # Get task text from command arguments
    if not context.args:
        help_text = """
📝 <b>Create a New Task</b>

<b>Usage:</b>
<code>/new &lt;task description&gt;</code>

<b>Examples:</b>
• <code>/new Buy groceries</code>
• <code>/new Fix bug #work</code>
• <code>/new Meeting !!! #important</code>

<b>💡 Tips:</b>
• Add #tags to organize tasks
• Use !!! for high priority
• Use !! for medium priority
        """
        yield Answer(text=help_text.strip(), parse_mode="HTML")
        return

    # Join all arguments as task text
    task_text = " ".join(context.args)

    # Parse task input
    parsed = task_service.parse_task_input(task_text)

    # Create task
    task = task_repo.create_task(
        user_id=user.id,
        title=parsed["title"],
        priority=parsed["priority"],
        tags=parsed["tags"],
    )

    # Format response
    response_text = f"""
✅ <b>Task Created!</b>

{task.format_for_display()}

<i>Use /list to view all tasks</i>
    """

    yield Answer(text=response_text.strip(), parse_mode="HTML")


@router.command(["tasks", "list"])
async def list_tasks_command(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
    task_service: TaskServiceDependency,
) -> HandlerResponse:
    """
    Handle /list and /tasks commands - view all tasks.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
        task_service: Injected task service
    """
    # Get user
    user = user_repo.get_by_telegram_id(update.effective_user.id)
    if not user:
        yield Answer(text="❌ User not found. Please /start first.")
        return

    # Get all tasks
    tasks = task_repo.get_user_tasks(user.id)

    if not tasks:
        yield Answer(
            text="📭 <b>No tasks yet!</b>\n\nCreate your first task with /new",
            parse_mode="HTML",
        )
        return

    # Format task list
    task_list = task_service.format_task_list(tasks, show_completed=True)

    yield Answer(text=task_list, parse_mode="HTML")


@router.command("pending")
async def pending_tasks_command(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
    task_service: TaskServiceDependency,
) -> HandlerResponse:
    """
    Handle /pending command - view incomplete tasks only.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
        task_service: Injected task service
    """
    # Get user
    user = user_repo.get_by_telegram_id(update.effective_user.id)
    if not user:
        yield Answer(text="❌ User not found. Please /start first.")
        return

    # Get pending tasks
    tasks = task_repo.get_pending_tasks(user.id)

    if not tasks:
        yield Answer(
            text="✅ <b>No pending tasks!</b>\n\nAll done! 🎉", parse_mode="HTML"
        )
        return

    # Format task list
    task_list = task_service.format_task_list(tasks, show_completed=False)

    yield Answer(text=task_list, parse_mode="HTML")


@router.command("completed")
async def completed_tasks_command(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
) -> HandlerResponse:
    """
    Handle /completed command - view completed tasks.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
    """
    # Get user
    user = user_repo.get_by_telegram_id(update.effective_user.id)
    if not user:
        yield Answer(text="❌ User not found. Please /start first.")
        return

    # Get completed tasks
    tasks = task_repo.get_completed_tasks(user.id, limit=20)

    if not tasks:
        yield Answer(
            text="📭 <b>No completed tasks yet</b>\n\nKeep working! 💪",
            parse_mode="HTML",
        )
        return

    # Format tasks
    lines = ["✅ <b>Completed Tasks:</b>\n"]
    for task in tasks:
        lines.append(f"  {task.format_for_display()}")

    yield Answer(text="\n".join(lines), parse_mode="HTML")


@router.command("done")
async def mark_done_command(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
    task_service: TaskServiceDependency,
) -> HandlerResponse:
    """
    Handle /done command - mark task as complete.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
        task_service: Injected task service
    """
    # Get user
    user = user_repo.get_by_telegram_id(update.effective_user.id)
    if not user:
        yield Answer(text="❌ User not found. Please /start first.")
        return

    # Get task ID
    if not context.args:
        yield Answer(
            text="❌ <b>Missing task ID</b>\n\n<b>Usage:</b> <code>/done &lt;task_id&gt;</code>",
            parse_mode="HTML",
        )
        return

    task_id = task_service.validate_task_id(context.args[0])
    if not task_id:
        yield Answer(text="❌ Invalid task ID. Please provide a valid number.")
        return

    # Get and verify task
    task = task_repo.get(task_id)
    if not task or task.user_id != user.id:
        yield Answer(text="❌ Task not found or doesn't belong to you.")
        return

    if task.completed:
        yield Answer(text="ℹ️ Task is already marked as complete.")
        return

    # Mark as complete
    task = task_repo.mark_complete(task_id, completed=True)

    if task is None:
        yield EditAnswer(text="Couldn't find task")
        return

    yield Answer(
        text=f"✅ <b>Task Completed!</b>\n\n{task.format_for_display()}",
        parse_mode="HTML",
    )


@router.command("undone")
async def mark_undone_command(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
    task_service: TaskServiceDependency,
) -> HandlerResponse:
    """
    Handle /undone command - mark task as incomplete.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
        task_service: Injected task service
    """
    # Get user
    user = user_repo.get_by_telegram_id(update.effective_user.id)
    if not user:
        yield Answer(text="❌ User not found. Please /start first.")
        return

    # Get task ID
    if not context.args:
        yield Answer(
            text="❌ <b>Missing task ID</b>\n\n<b>Usage:</b> <code>/undone &lt;task_id&gt;</code>",
            parse_mode="HTML",
        )
        return

    task_id = task_service.validate_task_id(context.args[0])
    if not task_id:
        yield Answer(text="❌ Invalid task ID.")
        return

    # Get and verify task
    task = task_repo.get(task_id)
    if not task or task.user_id != user.id:
        yield Answer(text="❌ Task not found.")
        return

    if not task.completed:
        yield Answer(text="ℹ️ Task is not marked as complete.")
        return

    # Mark as incomplete
    task = task_repo.mark_complete(task_id, completed=False)

    yield Answer(
        text=f"⭕ <b>Task Reopened</b>\n\n{task.format_for_display()}",
        parse_mode="HTML",
    )


@router.command(["delete", "remove"])
async def delete_task_command(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
    task_service: TaskServiceDependency,
) -> HandlerResponse:
    """
    Handle /delete command - delete a task.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
        task_service: Injected task service
    """
    # Get user
    user = user_repo.get_by_telegram_id(update.effective_user.id)
    if not user:
        yield Answer(text="❌ User not found. Please /start first.")
        return

    # Get task ID
    if not context.args:
        yield Answer(
            text="❌ <b>Missing task ID</b>\n\n<b>Usage:</b> <code>/delete &lt;task_id&gt;</code>",
            parse_mode="HTML",
        )
        return

    task_id = task_service.validate_task_id(context.args[0])
    if not task_id:
        yield Answer(text="❌ Invalid task ID.")
        return

    # Get and verify task
    task = task_repo.get(task_id)
    if not task or task.user_id != user.id:
        yield Answer(text="❌ Task not found.")
        return

    # Delete task
    task_repo.delete(task_id)

    yield Answer(
        text=f"🗑️ <b>Task Deleted</b>\n\n<s>{task.title}</s>", parse_mode="HTML"
    )


@router.command("search")
async def search_tasks_command(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
) -> HandlerResponse:
    """
    Handle /search command - search tasks by keyword.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
    """
    # Get user
    user = user_repo.get_by_telegram_id(update.effective_user.id)
    if not user:
        yield Answer(text="❌ User not found. Please /start first.")
        return

    # Get search keyword
    if not context.args:
        yield Answer(
            text="❌ <b>Missing keyword</b>\n\n<b>Usage:</b> <code>/search &lt;keyword&gt;</code>",
            parse_mode="HTML",
        )
        return

    keyword = " ".join(context.args)

    # Search tasks
    tasks = task_repo.search_tasks(user.id, keyword)

    if not tasks:
        yield Answer(
            text=f"🔍 <b>No tasks found</b> matching '<i>{keyword}</i>'",
            parse_mode="HTML",
        )
        return

    # Format results
    lines = [f"🔍 <b>Search Results for '{keyword}':</b>\n"]
    for task in tasks:
        lines.append(f"  {task.format_for_display()}")

    yield Answer(text="\n".join(lines), parse_mode="HTML")


@router.command("stats")
async def stats_command(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    task_repo: TaskRepositoryDependency,
    task_service: TaskServiceDependency,
) -> HandlerResponse:
    """
    Handle /stats command - show task statistics.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
        task_repo: Injected task repository
        task_service: Injected task service
    """
    # Get user
    user = user_repo.get_by_telegram_id(update.effective_user.id)
    if not user:
        yield Answer(text="❌ User not found. Please /start first.")
        return

    # Get statistics
    stats = task_repo.get_task_stats(user.id)

    if stats["total"] == 0:
        yield Answer(
            text="📊 <b>No statistics yet</b>\n\nCreate some tasks to see your stats!",
            parse_mode="HTML",
        )
        return

    # Format statistics
    stats_text = task_service.format_task_stats(stats)

    yield Answer(text=stats_text, parse_mode="HTML")
