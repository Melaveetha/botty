from typing import Annotated

from botty import Depends, InjectableUser, Update
from src.models.user import User
from src.repositories.user_repository import UserRepository


async def get_current_user(
    update: Update,
    user_repo: UserRepository,  # automatically injected
    user: InjectableUser,  # automatically injected
) -> User | None:
    """Return the User object for the effective user, or None if not found."""
    return user_repo.get_by_telegram_id(user.id)


# Type alias for easy reuse
CurrentUser = Annotated[User | None, Depends(get_current_user)]
