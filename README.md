# Botty

**A FastAPI-inspired modern framework for building Telegram bots with Python**

Botty is the elegance of FastAPI's dependency injection and type hints to Telegram bot development (based on `python-telegram-bot`).
Write clean, code with automatic dependency resolution and a developer-friendly API.


```python
from botty import Router, HandlerResponse, Context, Answer, Update, InjectableUser

router = Router()

@router.command("start")
async def start_handler(
    update: Update,
    context: Context,
    user_repo: UserRepository,  # Auto-injected!
    effective_user: InjectableUser # Auto-injected!
) -> HandlerResponse:
    user = user_repo.get_or_create(effective_user.id)
    yield Answer(text=f"Welcome back, {user.name}! 👋")
```

## 🎯 Main Idea

Traditional Telegram bot frameworks require a lot of boilerplate and make it hard to:
- Share code between handlers (no clean dependency injection)
- Track and edit messages you've sent
- Write testable code (everything is tightly coupled)
- Get type hints and IDE support

**Botty uses** FastAPI's best ideas to Telegram bots:
- **Dependency Injection** - Repositories and services are automatically injected
- **Type Hints** - Full type safety with IDE autocomplete
- **Async Generators** - Handlers yield responses, making sending and editing messages trivial


## Installation

```bash
pip install botty-framework
```
or
```bash
uv add botty-framework
```


## 🌟 Features

### FastAPI-Style Dependency Injection

Botty automatically injects *repositories* and *services* just by type‑hinting them – no decorators, no `Depends()` boilerplate.

1. **Automatic injection** – Any parameter whose type inherits from `BaseRepository` or `BaseService` is automatically provided.
   - Repositories are **request‑scoped**: a new instance is created for each update, with an open database session.
   - Services are **singletons**: the same instance is shared across all requests.

```python
@router.command("profile")
async def show_profile(
    update: Update,
    context: Context,
    user_repo: UserRepository,      # Injected automatically
    settings_svc: SettingsService,   # Services too!
    effective_user: InjectableUser
) -> HandlerResponse:
    user = user_repo.get(effective_user.id)
    settings = settings_svc.get_user_settings(user.id)

    yield Answer(f"👤 {user.name}\n⚙️ Theme: {settings.theme}")
```
2. Explicit injection with `Depends` – For everything else, use `Annotated[T, Depends(...)]`. This gives you full control over caching, nested dependencies, and computed values.
```python
async def get_current_user(
    update: Update, context: Context   # Nested works!
) -> User:
    ...

CurrentUser: TypeAlias = Annotated[User, Depends(get_current_user)]

@router.command("profile")
async def profile_handler(
    update: Update,
    context: Context,
    user: CurrentUser
) -> HandlerResponse:
    ...
```

Dependencies are cached per request by default; set use_cache=False to disable caching.

What dependencies are generated?
1. Any class that inherits from BaseRepository gets a request‑scoped instance with an open database session.
2. Any class that inherits from BaseService is a singleton – shared across requests.
3. Common objects like `Update`, `Context`, `Session`, `InjectableUser`, `InjectableChat`, `InjectableMessage`, and `InjectableCallbackQuery` are also injected automatically.

### Custom dependencies with `Depends`

For cases where automatic injection isn't enough (e.g., you need to compute a value or fetch something conditionally), Botty provides FastAPI‑style Depends.

```python
from botty import Depends, Annotated

async def get_current_user(
    update: Update,
    user_repo: UserRepository   # ← Nested dependencies work too!
) -> User:
    return user_repo.get(update.effective_user.id)

CurrentUser = Annotated[User, Depends(get_current_user)]

@router.command("profile")
async def profile_handler(
    update: Update,
    context: Context,
    current_user: CurrentUser   # ← Injected via Depends
) -> HandlerResponse:
    yield Answer(f"Your profile: {current_user.name}")
```
Dependencies can be cached within the same request (default) or recomputed each time. They can also depend on other dependencies – the resolver handles the graph automatically.

### Conversations
Botty supports class‑based conversations for multi‑step interactions. Decorate methods with `@entry`, `@step`, `@cancel`, and `@error`.

```python
from botty import Conversation, entry, step, cancel, error, ConversationState

@router.conversation("register")
class RegistrationConversation(Conversation):
    @entry
    async def start(self, update: Update, context: Context) -> HandlerResponse:
        yield Answer("Welcome! What's your name?")
        self.step("ask_age")          # go to next step

    @step
    async def ask_age(
        self,
        update: Update,
        context: Context,
        state: ConversationState       # injected state
    ) -> HandlerResponse:
        name = update.message.text
        state["name"] = name
        yield Answer(f"Nice to meet you, {name}! How old are you?")
        self.step("farewell")

    @step
    async def farewell(
        self,
        update: Update,
        context: Context,
        state: ConversationState
    ) -> HandlerResponse:
        state["age"] = update.message.text
        yield Answer(f"Thank you! You are {state['age']} years old. Goodbye!")
        self.end()                      # ends conversation

    @cancel
    async def on_cancel(self, update: Update, context: Context) -> HandlerResponse:
        yield Answer("Registration cancelled.")
        self.end()

    @error
    async def handle_error(
        self,
        update: Update,
        context: Context,
        exception: Exception
    ) -> HandlerResponse:
        yield Answer("Something went wrong. Please try again later.")
        self.end()
```

- The cancel command defaults to `/cancel`. Override it in the decorator: `@router.conversation("register", cancel_command="stop")` (Note: no leading '/' for commands)
- State is automatically saved in `context.user_data` and cleared when the conversation ends.
- If you don’t define `@cancel` or `@error`, sensible defaults are used (they log and end the conversation).


### Message Registry & Smart Editing

Botty tracks every message you send in a registry (per chat, with a configurable limit). When you yield an `EditAnswer`, the framework decides which message to edit using this **priority order**:

1. **Direct message ID** – if you set `EditAnswer(message_id=123)`.
2. **Message key** – if you set `EditAnswer(message_key="my_key")`.
3. **Handler name (explicit)** – if you set `EditAnswer(handler_name="other_handler")`, the most recent message from that handler is used.
4. **Current handler** – the most recent message sent by the same handler.
5. **Last message in chat** – fallback to the very last message sent in this chat.

```python
@router.command("countdown")
async def countdown_handler(
    update: Update,
    context: Context
) -> HandlerResponse:
    # Send message with a key
    yield Answer("Starting in 3...", message_key="countdown")

    await asyncio.sleep(1)

    # Edit by key
    yield EditAnswer("2...", message_key="countdown")

    await asyncio.sleep(1)
    yield EditAnswer("1...", message_key="countdown")

    await asyncio.sleep(1)
    yield EditAnswer("GO! 🚀", message_key="countdown")
```

You can also interact with the registry manually if needed:

```python
# Get a message by its key
record = context.bot_data.message_registry.get_by_key("my_key")
if record:
    message_id = record.message_id

# Get all messages from a handler
records = context.bot_data.message_registry.get_by_handler("my_handler")
```

The registry is stored in `bot_data` and shared across all handlers. It automatically discards old messages when the per‑chat limit is reached (default 100).


### Middleware

Middleware lets you intercept and modify the response stream of every handler. A middleware is an async function that receives the `update`, `context`, and the inner generator, and returns an async generator that may yield its own responses.

**Example – logging middleware:**

```python
from botty import Middleware

async def logging_middleware(
    update: Update,
    context: Context,
    inner: AsyncGenerator[BaseAnswer, None]
) -> AsyncGenerator[BaseAnswer, None]:
    print(f"Handler called for update {update.update_id}")
    async for response in inner:
        print(f"Yielding response: {response}")
        yield response
```

**Registering middleware:**

Use the builder to add one or more middlewares:
```python
app = (
    AppBuilder()
    .token("TOKEN")
    .add_middleware(logging_middleware)
    .add_middleware(auth_middleware)
    .build()
)
```

**Execution order**: Middlewares are applied in the order they are added, forming a stack. The first added becomes the outermost, so it runs first before the handler and last after the handler.

**Short‑circuiting**: If a middleware yields a response without calling the inner generator, the handler is never executed.

### Clean Handler Syntax

Handlers are async generators that yield responses:

```python
@router.command("weather")
async def weather_handler(
    update: Update,
    context: Context,
    weather_api: WeatherService
) -> HandlerResponse:
    city = " ".join(context.args)

    # Show loading state
    yield Answer("🔍 Fetching weather...", message_key="weather")

    # Get data
    data = await weather_api.get_current(city)

    # Update message
    yield EditAnswer(
        f"🌤️ {city}: {data.temp}°C, {data.condition}",
        message_key="weather"
    )
```

### Repository Pattern

Built-in support for the repository pattern with SQLModel:

```python
from botty import BaseRepository
from sqlmodel import Session, select

class UserRepository(BaseRepository[User]): # Inheritance from BaseRepository allows to be injected
    model = User

    def get_by_telegram_id(self, telegram_id: int) -> User | None:
        statement = select(User).where(User.telegram_id == telegram_id)
        return self.session.exec(statement).first()

    def get_active_users(self) -> list[User]:
        statement = select(User).where(User.is_active == True)
        return list(self.session.exec(statement).all())

# Automatically injected with proper session management!
@router.command("stats")
async def stats_handler(
    update: Update,
    context: Context,
    user_repo: UserRepository
) -> HandlerResponse:
    active = user_repo.get_active_users()
    yield Answer(f"📊 Active users: {len(active)}")
```

### Type Safety & Validation

Handlers are validated at registration time with helpful error messages:

```python
@router.command("test")
def wrong_handler(update: Update, context: Context):  # ❌ Forgot 'async'
    yield Answer("Hi")

# Error: Handler must be an async function (use 'async def')
# 💡 Suggestion: Change 'def wrong_handler(...)' to 'async def wrong_handler(...)'
```

### Built-in Database Support (optional)

SQLModel integration with automatic session management:

```python
from botty import AppBuilder, SQLiteProvider
from sqlmodel import SQLModel, Field

# Define your models
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.UTC))

# Build app with database
app = (
    AppBuilder(token="YOUR_TOKEN")
    .database(SQLiteProvider("bot.db"))
    .build()
)
```

### Global Exception Handlers

You can register handlers that are called when specific exceptions occur during request processing. This is useful for custom error messages or logging.

```python
from botty import Answer

async def on_telegram_error(update, context, exc: TelegramError):
    yield Answer("A Telegram API error occurred. Please try again later.")

builder.add_exception_handler(TelegramError, on_telegram_error)
```

The exception is injected automatically if your handler declares a parameter with that type. Handlers are tried in registration order.

### Testing

Botty provides a comprehensive testing toolkit in `botty.testing` to unit‑test handlers and conversations without a real Telegram bot.

**Key test doubles:**

- `TestBotClient` – records sent messages instead of actually sending them.
- `TestContext` – a mutable context you can pre‑configure.
- `TestDatabaseProvider` – in‑memory SQLite database, isolated per test.
- `TestDependencyContainer` – allows overriding dependencies with mocks.
- `ConversationTester` – a helper to drive conversations step by step.

**Example – testing a simple handler:**

```python
from botty.testing import TestContext, TestBotClient

async def test_hello_handler(router):
    ctx = TestContext()
    ctx.bot_data.bot_client = TestBotClient()

    # Simulate a /hello command
    update = make_command_update("hello")
    wrapper = router.handlers[0][2]   # get the wrapped handler
    await wrapper(update, ctx)

    assert len(ctx.bot_data.bot_client.sent) == 1
    assert ctx.bot_data.bot_client.sent[0].answer.text == "Hello!"
```

**Testing conversations with** `ConversationTester`:

```python
from botty.testing import ConversationTester

async def test_registration_flow(router):
    tester = ConversationTester(router, RegistrationConversation, "register")
    await tester.start()
    assert tester.current_step == "ask_age"
    assert tester.last_responses[0].answer.text == "Welcome! What's your name?"

    await tester.send_message("Alice")
    assert tester.current_step == "farewell"
    assert tester.conversation_data["name"] == "Alice"
    assert tester.last_responses[0].answer.text == "Nice to meet you, Alice! How old are you?"

    await tester.send_message("30")
    assert tester.current_step is None  # conversation ended
    assert "30" in tester.last_responses[0].answer.text
```

The ConversationTester also supports dependency overrides, direct step execution, and callback queries.

## 🎨 Inspirations

### FastAPI
Botty is heavily inspired by FastAPI's elegant dependency injection system:
- Type hints for automatic injection
- Clean decorator-based routing
- Dependency resolution with `Depends()`

### Django
Repository pattern and clean architecture:
- Repository layer for data access
- Service layer for business logic


## 📚 Complete Example

### Project Structure

Botty auto-discovers handlers from project structure:

```
todo_bot/
├── src/
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py        # Start command handlers
│   │   ├── todos.py        # Todo-related handlers
│   │   └── settings.py     # Settings handlers
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   └── todo_repository.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── notification_service.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── todo.py
├── main.py                 # App entry point
└── pyproject.toml
```

- The directory must be a **Python package** (contain an `__init__.py` file).
- Each `.py` file inside (except `__init__.py`) may define a `Router` instance (usually named `router`).
- The router will be picked up and registered with the application.
- You can override the default path using `.handlers_directory("/custom/path")` on the builder.

If you prefer explicit registration, disable discovery with `.manual_routes()` and use `.add_router(...)`.

### Implementation

Here's a full todo bot showing all features:

```python
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from sqlmodel import SQLModel, Field, Session, select
from botty import (
    AppBuilder,
    Router,
    Context,
    HandlerResponse,
    BaseRepository,
    Answer,
    EditAnswer,
    SQLiteProvider,
    Update,
)

# ============================================================================
# Models
# ============================================================================

class Todo(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int
    task: str
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(datetime.UTC))


# ============================================================================
# Repositories
# ============================================================================

class TodoRepository(BaseRepository[Todo]):  # Inheritance from BaseRepository allows to be injected
    model = Todo

    def get_by_user(self, user_id: int) -> list[Todo]:
        """Get all todos for a user."""
        statement = select(Todo).where(Todo.user_id == user_id)
        return list(self.session.exec(statement).all())

    def get_pending(self, user_id: int) -> list[Todo]:
        """Get incomplete todos."""
        statement = (
            select(Todo)
            .where(Todo.user_id == user_id)
            .where(Todo.completed == False)
        )
        return list(self.session.exec(statement).all())

    def toggle_complete(self, todo_id: int) -> Todo | None:
        """Toggle completion status."""
        todo = self.get(todo_id)
        if todo:
            todo.completed = not todo.completed
            self.update(todo)
        return todo

# ============================================================================
# Handlers
# ============================================================================

router = Router()

@router.command("start")
async def start_handler(
    update: Update,
    context: Context
) -> HandlerResponse:
    """Welcome message."""
    yield Answer(
        "👋 Welcome to Todo Bot!\n\n"
        "Commands:\n"
        "/add <task> - Add a new todo\n"
        "/list - Show all todos\n"
        "/pending - Show incomplete todos"
    )


@router.command("add")
async def add_todo_handler(
    update: Update,
    context: Context,
    todo_repo: TodoRepository,  # Auto-injected!
    effective_user: InjectableUser
) -> HandlerResponse:
    """Add a new todo."""
    if not context.args:
        yield Answer("❌ Usage: /add <task description>")
        return

    task = " ".join(context.args)
    todo = Todo(
        user_id=effective_user.id,
        task=task
    )

    todo_repo.create(todo)
    yield Answer(f"✅ Added: {task}")


@router.command("list")
async def list_todos_handler(
    update: Update,
    context: Context,
    todo_repo: TodoRepository,  # Auto-injected!
    effective_user: InjectableUser
) -> HandlerResponse:
    """List all todos."""
    todos = todo_repo.get_by_user(effective_user.id)

    if not todos:
        yield Answer("📝 You have no todos!\nUse /add to create one.")
        return

    # Build message with buttons
    text = "📝 Your todos:\n\n"
    buttons = []

    for i, todo in enumerate(todos, 1):
        status = "✅" if todo.completed else "⏺️"
        text += f"{i}. {status} {todo.task}\n"

        button_text = "✅ Complete" if not todo.completed else "↩️ Undo"
        buttons.append([
            InlineKeyboardButton(
                f"{i}. {button_text}",
                callback_data=f"toggle_{todo.id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(buttons)

    yield Answer(
        text=text,
        reply_markup=keyboard,
        message_key="todo_list"
    )


@router.command("pending")
async def pending_todos_handler(
    update: Update,
    context: Context,
    todo_repo: TodoRepository,  # Auto-injected!
    effective_user: InjectableUser
) -> HandlerResponse:
    """List incomplete todos."""
    todos = todo_repo.get_pending(effective_user.id)

    if not todos:
        yield Answer("🎉 All done! No pending todos.")
        return

    text = "⏺️ Pending todos:\n\n"
    for i, todo in enumerate(todos, 1):
        text += f"{i}. {todo.task}\n"

    yield Answer(text)


@router.callback_query(r"^toggle_(\d+)")
async def toggle_todo_handler(
    update: Update,
    context: Context,
    todo_repo: TodoRepository,  # Auto-injected!
    callback_query: InjectableCallbackQuery,
    effective_user: InjectableUser
) -> HandlerResponse:
    """Toggle todo completion."""
    await callback_query.answer()

    # Extract todo ID from callback data
    todo_id = int(query.data.split("_")[1])

    # Toggle the todo
    todo = todo_repo.toggle_complete(todo_id)

    if not todo:
        yield EditAnswer("❌ Todo not found")
        return

    # Refresh the list
    todos = todo_repo.get_by_user(effective_user.id)

    text = "📝 Your todos:\n\n"
    buttons = []

    for i, t in enumerate(todos, 1):
        status = "✅" if t.completed else "⏺️"
        text += f"{i}. {status} {t.task}\n"

        button_text = "✅ Complete" if not t.completed else "↩️ Undo"
        buttons.append([
            InlineKeyboardButton(
                f"{i}. {button_text}",
                callback_data=f"toggle_{t.id}"
            )
        ])

    keyboard = InlineKeyboardMarkup(buttons)

    yield EditAnswer(
        text=text,
        reply_markup=keyboard,
        message_key="todo_list"
    )


# ============================================================================
# Application Setup
# ============================================================================

if __name__ == "__main__":
    app = (
        AppBuilder(token="YOUR_BOT_TOKEN_HERE")
        .database(SQLiteProvider("todos.db"))
        .build()
    )

    app.launch()
```

## 🔍 Comparison

### vs. python-telegram-bot

**python-telegram-bot:**
```python
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Manual session management
    session = Session(engine)
    try:
        user_repo = UserRepository(session)
        user_name = "unknown"
        if update.effective_user is not None:
            user = user_repo.get(update.effective_user.id)
            user_name = user.name
        if update.message is not None:
            await update.message.reply_text(f"Hello {user_name}")
    finally:
        session.close()

application.add_handler(CommandHandler("start", start))
```

**Botty:**
```python
@router.command("start")
async def start_handler(
    update: Update,
    context: Context,
    user_repo: UserRepository,  # Auto-injected!
    effective_user: InjectableUser
) -> HandlerResponse:
    user = user_repo.get(effective_user.id)
    yield Answer(f"Hello {user.name}")
    # Session managed automatically
```

## 📄 License

MIT License - see LICENSE file for details

## Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - For the inspiration
- [python-telegram-bot](https://python-telegram-bot.org/) - For the excellent Telegram wrapper
- [SQLModel](https://sqlmodel.tiangolo.com/) - For the ORM integration

## 🗺️ Roadmap

- [ ] More database providers (PostgreSQL, MySQL, NoDatabase)
- [ ] Admin panel
- [ ] CLI for scaffolding projects
- [ ] Metrics and monitoring
- [ ] Plugin system

---

*Botty - Because building bots should be as elegant as using them*
