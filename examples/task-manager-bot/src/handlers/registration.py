from botty.routing import Conversation, step, entry
from botty import Router, Update, Context, Answer, InjectableMessage, ConversationState

router = Router(name="registration")


@router.conversation(["register", "reg", "auth"])
class RegistrationConversation(Conversation):
    def __init__(self):
        super().__init__()

    @entry
    async def ask_name(self, update: Update, context: Context):
        yield Answer("Write your name.")
        self.step("ask_age")
        return

    @step
    async def ask_age(
        self,
        update: Update,
        context: Context,
        message: InjectableMessage,
        state: ConversationState,
    ):
        if message.text is None:
            yield Answer("You should answer with text message. Try again")
            self.step("ask_age")
            return
        if context.user_data:
            state["name"] = message.text

        yield Answer("Write your age.")
        self.step("validate_age")

    @step
    async def validate_age(
        self,
        update: Update,
        context: Context,
        message: InjectableMessage,
        state: ConversationState,
    ):
        if message.text is None:
            yield Answer("You should send a text message")
        try:
            state["age"] = int(message.text)
        except ValueError:
            yield Answer("You should answer with a single integer number like `21`")
            self.step("validate_age")
            return

        yield Answer(
            f"Hello, {state['name']}! You are {state['age']} years old? Great!"
        )
        self.end()
