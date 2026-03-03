import inspect
from collections.abc import Callable, Awaitable
from types import MethodType
from typing import Any

from ..exceptions import (
    DependencyResolutionError,
    InvalidHandlerError,
)
from .types import HandlerProtocol
from ..domain import BaseRepository, BaseService
from .container import DependencyContainer
from .scope import RequestScope
from .types import Handler, ResolutionPlan
from .utils import _extract_depends


class DependencyResolver:
    """Resolves dependencies for a handler function.

    Given a handler and a request scope, this class extracts the function
    signature, identifies parameters that need injection (via Depends or
    basic types), and builds a dictionary of keyword arguments to call the
    handler with.
    """

    def __init__(self, container: DependencyContainer):
        """Initialize the resolver with a dependency container.

        Args:
            container: The container that holds singletons and resolves
                       nested dependencies.
        """
        self.container: DependencyContainer = container

    async def resolve_handler(
        self, handler: Handler, scope: RequestScope
    ) -> dict[str, Any]:
        """Resolve all dependencies for a handler.

        Args:
            handler: The handler function (async generator) to resolve.
            scope: The current request scope.

        Returns:
            A dictionary mapping parameter names to resolved values, ready
            to be passed to the handler.

        Raises:
            DependencyResolutionError: If any parameter cannot be resolved,
                                       or if a required database dependency
                                       is requested but no provider is set.
        """
        return await self._resolve_callable(handler, scope, skip_params=0)

    async def resolve_bound_method(
        self,
        method: MethodType,
        instance: Any,
        scope: RequestScope,
    ) -> dict[str, Any]:
        """Resolve all dependencies for a bound method.

        Args:
            method: The handler function (async generator) to resolve.
            instance: Conversation instance owning the method
            scope: The current request scope.

        Returns:
            A dictionary mapping parameter names to resolved values, ready
            to be passed to the handler.

        Raises:
            DependencyResolutionError: If any parameter cannot be resolved,
                                       or if a required database dependency
                                       is requested but no provider is set.
        """
        unbound = method.__func__
        handler_name = f"{instance.__class__.__name__}.{method.__name__}"
        return await self._resolve_callable(
            unbound,  # ty: ignore [invalid-argument-type]
            scope,
            skip_params=1,
            handler_name=handler_name,
        )

    async def _resolve_callable(
        self,
        func: HandlerProtocol,
        scope: RequestScope,
        skip_params: int = 0,
        handler_name: str | None = None,
    ) -> dict[str, Any]:
        if handler_name is None:
            handler_name = getattr(func, "__name__") or "unknown"

        plan: ResolutionPlan | None = getattr(func, "__botty_resolve_plan__", None)
        if plan is None:
            plan = await self.build_resolve_plan(func, handler_name, skip_params)
            setattr(func, "__botty_resolve_plan__", plan)
        kwargs = {}

        for param_name, resolver in plan:
            kwargs[param_name] = await resolver(scope)

        return kwargs

    async def build_resolve_plan(
        self, handler: Handler, handler_name: str, skip_params: int = 0
    ) -> ResolutionPlan:
        """
        Pre‑compute resolvers for all injectable parameters of a handler.

        Args:
            handler: The handler function (unbound).
            handler_name: Name of the handler (for error messages).
            skip_params: Number of initial parameters to ignore
                         (0 for free functions, 1 for bound methods).

        Returns:
            ResolutionPlan (list of (param_name, async_resolver) pairs).
        """
        sig = inspect.signature(handler)
        type_hints = inspect.get_annotations(handler)

        if handler_name is None:
            handler_name = getattr(handler, "__name__") or "unknown"

        params = list(sig.parameters.items())

        if len(params) < skip_params + 2:
            raise InvalidHandlerError(
                handler_name=handler_name,
                reason="Handler must accept at least 'update' and 'context' parameters",
            )

        plan: ResolutionPlan = []

        for param_name, param in params[skip_params:]:
            annotation = type_hints.get(param_name)
            resolver = self._build_param_resolver(param_name, annotation, handler_name)
            plan.append((param_name, resolver))

        return plan

    def _build_param_resolver(
        self,
        param_name: str,
        annotation: Any,
        handler_name: str,
    ) -> Callable[[RequestScope], Awaitable[Any]]:
        dep = _extract_depends(annotation)
        if dep is not None:

            async def depends_resolve(scope: RequestScope):
                container = scope.context.bot_data.dependency_container
                try:
                    return await container.resolve_dependency(
                        dep, scope, [handler_name, param_name]
                    )
                except Exception as e:
                    raise DependencyResolutionError(
                        message=f"Failed to resolve dependency `{annotation}`. Got following error: {e}",
                        dependency_chain=[handler_name, param_name],
                        handler_name=handler_name,
                        parameter_name=param_name,
                        suggestion=f"Verify you using correct syntax: async def {handler_name}(update: Update, context: Context, data: Annotated[Data, Depends(get_data)])",
                    )

            return depends_resolve

        basic_resolve = self.container._BASIC_DEPENDENCIES.get(annotation, None)
        if basic_resolve is not None:

            async def basic_resolver(scope: RequestScope):
                try:
                    return basic_resolve(scope)
                except Exception as e:
                    raise DependencyResolutionError(
                        message=f"Failed to resolve dependency `{annotation}`. Got following error: {e}",
                        dependency_chain=[handler_name, param_name],
                        handler_name=handler_name,
                        parameter_name=param_name,
                    )

            return basic_resolver

        if hasattr(annotation, "__mro__") and BaseService in annotation.__mro__:

            async def service_resolver(scope: RequestScope):
                container = scope.context.bot_data.dependency_container
                try:
                    return container.singleton(annotation)
                except Exception as e:
                    raise DependencyResolutionError(
                        message=f"Failed to resolve service `{annotation}`. Got following error: {e}",
                        dependency_chain=[handler_name, param_name],
                        handler_name=handler_name,
                        parameter_name=param_name,
                        suggestion=(
                            "Example: async def handler(..., repo: MapService):"
                        ),
                    )

            return service_resolver

        if hasattr(annotation, "__mro__") and BaseRepository in annotation.__mro__:

            async def repository_resolver(scope: RequestScope):
                try:
                    return annotation(session=scope.session)
                except Exception as e:
                    raise DependencyResolutionError(
                        message=f"Failed to resolve repository `{annotation}`. Got following error: {e}",
                        dependency_chain=[handler_name, param_name],
                        handler_name=handler_name,
                        parameter_name=param_name,
                        suggestion=("Example: async def handler(..., repo: UserRepo):"),
                    )

            return repository_resolver

        raise InvalidHandlerError(
            handler_name=handler_name,
            reason=f"Parameter '{param_name}' has no dependency information",
            suggestion="Use Annotated[T, Depends(...)] for injectable parameters, or ensure it's a repository/service class.",
        )
