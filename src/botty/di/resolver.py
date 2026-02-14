import inspect
from typing import Any

from ..exceptions import DatabaseNotConfiguredError, DependencyResolutionError
from .container import DependencyContainer
from .scope import RequestScope
from .types import Handler
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
                        raise DependencyResolutionError(
                            message=f"{e.message} (handler '{handler_name}', parameter '{param_name}')",
                            dependency_chain=[handler_name, param_name],
                            parameter_name=param_name,
                            handler_name=handler_name,
                        ) from e

                raise DependencyResolutionError(
                    message=(
                        "Annotation does not contain Depends\n"
                        f"Parameter '{param_name}' of handler '{handler_name}' has no dependency information.\n"
                        "Either:\n"
                        "  - Use Annotated[T, Depends(...)] for injectable parameters, or\n"
                        "  - Remove the parameter if it is not needed."
                    ),
                    dependency_chain=[handler_name, param_name],
                    handler_name=handler_name,
                    parameter_name=param_name,
                    suggestion=(
                        "Example: async def handler(..., repo: Annotated[UserRepo, Depends(get_repo)]):"
                    ),
                )

            dependency_chain = [handler_name, param_name]
            try:
                kwargs[param_name] = await self.container.resolve_dependency(
                    dep, scope, dependency_chain
                )
            except DependencyResolutionError:
                raise
            except Exception as e:
                raise DependencyResolutionError(
                    message=f"Failed to resolve dependency: {e}",
                    dependency_chain=dependency_chain,
                    parameter_name=param_name,
                    handler_name=handler_name,
                    suggestion="Check that all required dependencies are registered.",
                ) from e

        return kwargs
