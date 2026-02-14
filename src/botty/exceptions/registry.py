from .base import BottyError


class ChatIdNotFoundError(BottyError):
    """Chat id couldn't be found"""

    def __init__(self):
        super().__init__("Couldn't find chat id in update data.")
