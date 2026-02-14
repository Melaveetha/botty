"""
Handler validation utilities.

Validates handler functions to ensure they match the expected signature
and provides helpful error messages for common mistakes.
"""

from collections.abc import AsyncGenerator
from botty.di import Handler

import inspect
from typing import Any, get_type_hints

from loguru import logger

from ..exceptions import InvalidHandlerError


def validate_handler(func: Handler, handler_type: str = "command") -> None:
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
    if len(params) < 2:
        raise InvalidHandlerError(
            handler_name=func_name,
            reason="Handler must accept at least 'update' and 'context' parameters",
            suggestion=f"Add parameters: async def {func_name}(update: Update, context: Context, ...):",
        )

    # First two params should be update and context
    if params[0] not in ("update", "_update"):
        logger.warning(
            f"Handler '{func_name}': First parameter '{params[0]}' should be named 'update'"
        )

    if params[1] not in ("context", "ctx", "_context"):
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
        logger.debug(f"Could not validate type hints for '{func_name}': {e}")


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


def validate_handler_return_type(obj: Any, handler_name: str) -> None:
    """
    Validate that a handler returns the correct type at runtime.

    This is called during handler execution to catch cases where
    a handler returns something unexpected.

    Args:
        obj: Object returned by handler
        handler_name: Name of handler for error messages

    Raises:
        InvalidHandlerError: If return type is invalid
    """
    if not inspect.isasyncgen(obj):
        raise InvalidHandlerError(
            handler_name=handler_name,
            reason=(
                f"Handler returned {type(obj).__name__} instead of async generator. "
                f"Did you forget to use 'yield'?"
            ),
            suggestion=(
                f"Handler '{handler_name}' should yield Answer objects:\n"
                f"  async def {handler_name}(...):\n"
                f"      yield Answer(text='Hello!')  # ← Use yield, not return"
            ),
        )
