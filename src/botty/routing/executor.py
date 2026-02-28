from collections.abc import AsyncGenerator
from types import MethodType

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

    if instance is None:
        kwargs = await resolver.resolve_handler(func, scope)
    else:
        kwargs = await resolver.resolve_bound_method(func, instance, scope)  # ty: ignore [invalid-argument-type]

    generator = func(**kwargs)

    middlewares = scope.context.bot_data.middlewares

    wrapped_generator: AsyncGenerator[BaseAnswer, None] = generator
    for middleware in reversed(middlewares):
        wrapped_generator = middleware(scope.update, scope.context, wrapped_generator)

    processor = ResponseProcessor(
        scope.context.bot_data.message_registry, scope.context.bot_data.bot_client
    )

    await processor.process_async_generator(
        wrapped_generator, scope.update.get_chat_id(), handle_name
    )
