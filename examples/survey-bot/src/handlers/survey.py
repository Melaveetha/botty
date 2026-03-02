from botty.routing import Conversation
from loguru import logger
from botty import (
    Router,
    entry,
    step,
    cancel,
    error,
    Update,
    Context,
    Answer,
    EditAnswer,
    HandlerResponse,
    InjectableMessage,
    ConversationState,
    InjectableCallbackQuery,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

router = Router(name="survey")


@router.conversation("survey")
class SurveyConversation(Conversation):
    """
    A simple survey that asks for name, age, favorite color, and a photo.
    """

    @entry
    async def start(self, update: Update, context: Context) -> HandlerResponse:
        yield Answer(
            "Welcome to the survey! I'll ask you a few questions.\n\nWhat is your name?"
        )
        self.step("ask_age")

    @step
    async def ask_age(
        self,
        update: Update,
        context: Context,
        message: InjectableMessage,
        state: ConversationState,
    ) -> HandlerResponse:
        # Save name
        if message.text is None:
            yield Answer("Please send your name as text.")
            self.step("ask_age")  # stay on same step
            return

        state["name"] = message.text
        yield Answer(f"Nice to meet you, {message.text}! How old are you?")
        self.step("ask_color")

    @step
    async def ask_color(
        self,
        update: Update,
        context: Context,
        message: InjectableMessage,
        state: ConversationState,
    ) -> HandlerResponse:
        # Validate age
        if message.text is None:
            yield Answer("Please send your age as a number.")
            self.step("ask_color")
            return

        try:
            age = int(message.text)
        except ValueError:
            yield Answer(
                "That doesn't look like a number. Please enter your age (e.g., 25)."
            )
            self.step("ask_color")
            return

        state["age"] = age

        # Present inline keyboard for favorite color
        keyboard = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("🔴 Red", callback_data="color_red")],
                [InlineKeyboardButton("🟢 Green", callback_data="color_green")],
                [InlineKeyboardButton("🔵 Blue", callback_data="color_blue")],
            ]
        )
        yield Answer("Choose your favorite color:", reply_markup=keyboard)
        self.step("handle_color_choice")

    @step
    async def handle_color_choice(
        self,
        update: Update,
        context: Context,
        query: InjectableCallbackQuery,
        state: ConversationState,
    ) -> HandlerResponse:
        await query.answer()
        color = query.data.split("_")[1]  # "red", "green", "blue"
        state["favorite_color"] = color

        # Edit the original message to confirm
        yield EditAnswer(f"You selected {color}. Great choice!")

        # Ask for a photo
        yield Answer("Now, please send me a photo of something you like.")
        self.step("ask_photo")

    @step
    async def ask_photo(
        self,
        update: Update,
        context: Context,
        message: InjectableMessage,
        state: ConversationState,
    ) -> HandlerResponse:
        # Check if the message contains a photo
        if not message.photo:
            yield Answer("Please send a photo (as a file or picture).")
            self.step("ask_photo")
            return

        # In a real bot you might want to store the file_id or download it.
        # Here we just keep the largest photo's file_id.
        photo = message.photo[-1]  # largest size
        state["photo_file_id"] = photo.file_id

        # Summarize and end
        summary = (
            f"📋 **Survey Complete**\n\n"
            f"**Name:** {state['name']}\n"
            f"**Age:** {state['age']}\n"
            f"**Favorite color:** {state['favorite_color']}\n"
            f"**Photo file ID:** `{state['photo_file_id']}`"
        )
        yield Answer(summary, parse_mode="Markdown")
        self.end()  # conversation ends

    @cancel
    async def on_cancel(self, update: Update, context: Context) -> HandlerResponse:
        yield Answer("Survey cancelled. You can start over with /survey.")
        self.end()

    @error
    async def on_error(
        self, update: Update, context: Context, exception: Exception
    ) -> HandlerResponse:
        logger.error(f"Survey error: {exception}")
        yield Answer("An error occurred. Please try again later.")
        self.end()
