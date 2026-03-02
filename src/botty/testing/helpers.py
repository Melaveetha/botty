from telegram import Chat, Message, User, Update, CallbackQuery
from datetime import datetime


def make_command_update(
    command: str,
    args: list[str] | None = None,
    user_id: int = 123,
    chat_id: int = 456,
) -> Update:
    """Create a PTB Update representing a command message."""
    text = f"/{command}"
    if args:
        text += " " + " ".join(args)
    return make_message_update(text, user_id, chat_id)


def make_message_update(
    text: str,
    user_id: int = 123,
    chat_id: int = 456,
) -> Update:
    """Create a PTB Update with a text message."""
    user = User(id=user_id, first_name="Test", is_bot=False)
    chat = Chat(id=chat_id, type="private")
    message = Message(
        message_id=1,
        date=datetime.now(),
        chat=chat,
        from_user=user,
        text=text,
    )
    return Update(update_id=1, message=message)


def make_callback_update(
    data: str,
    user_id: int = 123,
    chat_id: int = 456,
    message_id: int = 100,
) -> Update:
    """Create a PTB Update with a callback query."""
    user = User(id=user_id, first_name="Test", is_bot=False)
    chat = Chat(id=chat_id, type="private")
    message = Message(
        message_id=message_id,
        date=datetime.now(),
        chat=chat,
        text="dummy",
    )
    callback = CallbackQuery(
        id="1",
        from_user=user,
        data=data,
        chat_instance="...",
        message=message,
    )
    return Update(update_id=2, callback_query=callback)
