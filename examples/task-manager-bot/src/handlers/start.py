from botty import (
    Router,
    Context,
    Answer,
    HandlerResponse,
    Update,
    EffectiveUser,
)

from src.repositories.user_repository import UserRepositoryDependency

router = Router(name="start")


@router.command("start")
async def start_command(
    update: Update,
    context: Context,
    user_repo: UserRepositoryDependency,
    effective_user: EffectiveUser,
) -> HandlerResponse:
    """
    Handle /start command - register user and show welcome message.

    Args:
        update: Telegram update
        context: Telegram context
        user_repo: Injected user repository
    """

    # Create or update user in database
    user = user_repo.create_or_update(
        telegram_id=effective_user.id,
        full_name=effective_user.full_name,
        username=effective_user.username,
    )

    # Send welcome message
    welcome_message = f"""
👋 <b>Welcome, {user.full_name}!</b>

I'm your personal task manager bot. I'll help you keep track of all your tasks and stay organized! 📝

<b>Quick Start:</b>
• /new - Create a new task
• /list - View your tasks
• /help - See all commands

Let's get started! Try creating your first task with /new
    """

    yield Answer(text=welcome_message.strip(), parse_mode="HTML")


@router.command("help")
async def help_command(update: Update, context: Context) -> HandlerResponse:
    """
    Handle /help command - show available commands.

    Args:
        update: Telegram update
        context: Telegram context
    """
    help_text = """
📚 <b>Available Commands:</b>

<b>Task Management:</b>
/new &lt;task&gt; - Create a new task
/add &lt;task&gt; - Same as /new
/list - View all your tasks
/tasks - Same as /list
/done &lt;id&gt; - Mark task as complete
/undone &lt;id&gt; - Mark task as incomplete
/delete &lt;id&gt; - Delete a task

<b>Organization:</b>
/search &lt;keyword&gt; - Search tasks
/tag &lt;tagname&gt; - View tasks by tag
/pending - View incomplete tasks only
/completed - View completed tasks

<b>Statistics:</b>
/stats - View your task statistics
/summary - Get daily summary

<b>Other:</b>
/help - Show this help message
/about - About this bot

<b>💡 Tips:</b>
• Add #tags to organize: <code>/new Buy milk #shopping</code>
• Use !!! for urgent: <code>/new Fix bug !!!</code>
• Combine both: <code>/new Meeting #work !!!</code>
    """

    yield Answer(text=help_text.strip(), parse_mode="HTML")


@router.command("about")
async def about_command(update: Update, context: Context) -> HandlerResponse:
    """
    Handle /about command - show bot information.

    Args:
        update: Telegram update
        context: Telegram context
    """
    about_text = """
🤖 <b>Task Manager Bot</b>

A personal task management assistant built with the Botty framework.

<b>Features:</b>
✅ Create and manage tasks
✅ Organize with tags and priorities
✅ Track completion statistics
✅ Search and filter tasks
✅ Get daily summaries

<b>Built with:</b>
• Botty Framework
• python-telegram-bot
• SQLModel

<b>Version:</b> 1.0.0

💬 Questions or feedback? Contact the developer!
    """

    yield Answer(text=about_text.strip(), parse_mode="HTML")
