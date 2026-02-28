from botty.exceptions import DatabaseNotConfiguredError
from collections.abc import AsyncGenerator
from types import MethodType

from loguru import logger

from ..di import DependencyResolver, HandlerProtocol, RequestScope
from ..responses import BaseAnswer
from .conversation import Conversation
from .response_processor import ResponseProcessor


async def execute_callable(
    func: MethodType | HandlerProtocol,
    scope: RequestScope,
    handle_name: str,
    instance: Conversation | None = None,
):
    """
    Resolve dependencies for a callable, execute it (must be an async generator),
    and process all yielded responses.

    Args:
        func: The async generator function or method to execute.
        scope: Current request scope (provides session, cache, etc.).
        handler_name: Name of the handler (for logging and registry).
        instance: If the callable is a bound method, pass the instance here.
                 For free functions, leave as None.
    """

    resolver = DependencyResolver(container=scope.context.bot_data.dependency_container)
    try:
        if instance is None:
            kwargs = await resolver.resolve_handler(func, scope)
        else:
            kwargs = await resolver.resolve_bound_method(func, instance, scope)  # ty: ignore [invalid-argument-type]

        generator = func(**kwargs)

        middlewares = scope.context.bot_data.middlewares

        wrapped_generator: AsyncGenerator[BaseAnswer, None] = generator
        for middleware in reversed(middlewares):
            wrapped_generator = middleware(
                scope.update, scope.context, wrapped_generator
            )

        processor = ResponseProcessor(
            scope.context.bot_data.message_registry, scope.context.bot_data.bot_client
        )

        await processor.process_async_generator(
            wrapped_generator, scope.update.get_chat_id(), handle_name
        )
    except Exception as e:
        await _handle_error(e, scope, handle_name)


async def _handle_error(e: Exception, old_scope: RequestScope, handle_name: str):
    try:
        if old_scope.session is not None:
            old_scope.session.rollback()
            old_scope.close()
    except DatabaseNotConfiguredError:
        pass

    handlers = old_scope.context.bot_data.exception_handlers

    error_handler = _find_exception_handler(e, handlers)
    if error_handler is None:
        raise e

    new_scope = RequestScope(
        update=old_scope.update, context=old_scope.context, exception=e
    )

    try:
        resolver = DependencyResolver(
            container=new_scope.context.bot_data.dependency_container
        )

        error_kwargs = await resolver.resolve_handler(error_handler, new_scope)

        error_gen = error_handler(**error_kwargs)

        # Skip middleware to avoid infinite loops

        processor = ResponseProcessor(
            new_scope.context.bot_data.message_registry,
            new_scope.context.bot_data.bot_client,
        )
        await processor.process_async_generator(
            error_gen, new_scope.update.get_chat_id(), error_handler.__name__
        )

        new_scope.commit()
    except Exception as inner_exc:
        logger.exception(
            f"Error handler '{error_handler.__name__}' raised an exception"
        )
        raise inner_exc
    finally:
        new_scope.close()


def _find_exception_handler(
    e: Exception, handlers: list[tuple[type[Exception], HandlerProtocol]]
) -> HandlerProtocol | None:
    for exc_class, handler in handlers:
        if isinstance(e, exc_class):
            return handler
    return None
