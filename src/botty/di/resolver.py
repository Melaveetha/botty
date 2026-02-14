import inspect
from typing import Any

from ..exceptions import DatabaseNotConfiguredError, DependencyResolutionError
from .container import DependencyContainer
from .scope import RequestScope
from .types import Handler
from .utils import _extract_depends


class DependencyResolver:
    """Resolver for FastAPI-like dependencies."""

    def __init__(self, container: DependencyContainer):
        self.container: DependencyContainer = container

    async def resolve_handler(
        self, handler: Handler, scope: RequestScope
    ) -> dict[str, Any]:
        """Resolve all dependencies for a handler."""
        sig = inspect.signature(handler)
        type_hints = inspect.get_annotations(handler)

        kwargs = {}
        handler_name = handler.__name__

        for param_name, param in sig.parameters.items():
            annotation = type_hints.get(param_name)

            dep = _extract_depends(annotation)
            if dep is None:
                if annotation is not None:
                    try:
                        injected = self.container._inject_basic_dependencies(
                            annotation, scope
                        )
                        if injected is not None:
                            kwargs[param_name] = injected
                            continue
                    except DatabaseNotConfiguredError as e:
                        raise DatabaseNotConfiguredError(
                            f"{e.message} (handler '{handler_name}', parameter '{param_name}')"
                        ) from e

                raise DependencyResolutionError(
                    message=(
                        "Annotation does not contain Depends\n"
                        f"Parameter '{param_name}' of handler '{handler_name}' has no dependency information.\n"
                        "Either:\n"
                        "  - Use Annotated[T, Depends(...)] for injectable parameters, or\n"
                        "  - Remove the parameter if it is not needed."
                    ),
                    suggestion=(
                        "Example: async def handler(..., repo: Annotated[UserRepo, Depends(get_repo)]):"
                    ),
                )

            kwargs[param_name] = await self.container.resolve_dependency(
                dep,
                scope,
            )

        return kwargs
