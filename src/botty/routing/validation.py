"""
Handler validation utilities.

Validates handler functions to ensure they match the expected signature
and provides helpful error messages for common mistakes.
"""

import inspect
from collections.abc import AsyncGenerator
from typing import get_type_hints

from loguru import logger

from ..di import Handler
from ..exceptions import InvalidConversationError, InvalidHandlerError
from .conversation import Conversation, iterate_steps


def validate_handler(
    func: Handler, handler_type: str = "command", skip_params: int = 0
) -> None:
    """
    Validate that a function matches the handler protocol.

    Checks:
    - Function is async
    - Function is a generator (uses yield)
    - Has update and context parameters
    - Type hints are correct (if present)

    Args:
        func: Function to validate
        handler_type: Type of handler (for error messages)

    Raises:
        InvalidHandlerError: If validation fails
    """
    func_name = func.__name__

    # Check if it's async
    if not inspect.isasyncgenfunction(func):
        raise InvalidHandlerError(
            handler_name=func_name,
            reason="Handler must be an async function (use 'async def')",
            suggestion=f"Change 'def {func_name}(...)' to 'async def {func_name}(...)'",
        )

    # Check signature
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())

    # Must have at least update and context
    if len(params) < skip_params + 2:
        raise InvalidHandlerError(
            handler_name=func_name,
            reason="Handler must accept at least 'update' and 'context' parameters",
            suggestion=f"Add parameters: async def {func_name}(update: Update, context: Context, ...):",
        )

    # First two params should be update and context
    if params[skip_params] not in ("update", "_update"):
        logger.warning(
            f"Handler '{func_name}': First parameter '{params[0]}' should be named 'update'"
        )

    if params[skip_params + 1] not in ("context", "ctx", "_context"):
        logger.warning(
            f"Handler '{func_name}': Second parameter '{params[1]}' should be named 'context'"
        )

    # Validate type hints if present
    try:
        type_hints = get_type_hints(func)

        # Check return type if specified
        if "return" in type_hints:
            return_type = type_hints["return"]

            # Check if it's AsyncGenerator[BaseAnswer, None] or similar
            origin = getattr(return_type, "__origin__", None)
            if origin is not None and origin is not AsyncGenerator:
                logger.warning(
                    f"Handler '{func_name}': Return type should be "
                    f"'AsyncGenerator[BaseAnswer, None]' or 'HandlerResponse', "
                    f"got '{return_type}'"
                )

    except Exception as e:
        # Type hint validation is best-effort
        logger.error(f"Could not validate type hints for '{func_name}': {e}")


def is_valid_handler(func: Handler, silent: bool = True) -> bool:
    """Check if a function is a valid handler without raising exceptions.

    Args:
        func: Function to check.
        silent: If False, log validation errors.

    Returns:
        True if the function passes validation, else False.
    """
    try:
        validate_handler(func)
        return True
    except InvalidHandlerError as e:
        if not silent:
            logger.error(str(e))
        return False


def validate_exactly_one(
    cls: type[Conversation], attr_name: str, decorator_name: str
) -> str:
    """
    Validate that a class has exactly one method with attribute `attr_name`.

    This is called during handler execution to catch cases where
    a handler returns something unexpected.

    Args:
        cls: Class that would be checked
        attr_name: Attribute name
        decorator_name: Name of decorator, that sets this attribute (for error message)

    Returns:
        Name of the matched method

    Raises:
        InvalidConversationError: If cls has zero or more than one method with `attr_name`
    """
    matched_methods = []
    for name, method in iterate_steps(cls):
        if getattr(method, attr_name, False):
            matched_methods.append(name)
    if len(matched_methods) != 1:
        raise InvalidConversationError(
            message=f"Conversation class '{cls.__name__}' must have exactly one method decorated with @{decorator_name}",
            class_name=cls.__name__,
            suggestion=(
                f"Add exactly one @{decorator_name} decorator to a method in {cls.__name__}. "
                f"Found {len(matched_methods)} methods: {', '.join(matched_methods)}"
            ),
        )
    return matched_methods[0]


def validate_at_most_one(
    cls: type[Conversation], attr_name: str, decorator_name: str
) -> None:
    """
    Validate that a class has exactly one method with attribute `attr_name`.

    This is called during handler execution to catch cases where
    a handler returns something unexpected.

    Args:
        cls: Class that would be checked
        attr_name: Attribute name
        decorator_name: Name of decorator, that sets this attribute (for error message)

    Raises:
        InvalidConversationError: If cls has more than one method with `attr_name`
    """
    matched_methods = []
    for name, method in iterate_steps(cls):
        if getattr(method, attr_name, False):
            matched_methods.append(name)
    if len(matched_methods) > 1:
        raise InvalidConversationError(
            message=f"Conversation class '{cls.__name__}' must have at most one method decorated with @{decorator_name}",
            class_name=cls.__name__,
            suggestion=(
                f"Remove extra @{decorator_name} decorators. Found {len(matched_methods)} methods: {', '.join(matched_methods)}"
            ),
        )
