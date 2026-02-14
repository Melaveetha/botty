import inspect
from collections.abc import Callable
from typing import Any, Type

from sqlmodel import Session

from ..context import Context, ContextProtocol
from ..domain import BaseRepository, BaseService, Update
from ..exceptions import DependencyResolutionError
from .markers import Dependency, Depends
from .scope import RequestScope
from .utils import _extract_depends


class DependencyContainer:
    """Container for managing and resolving dependencies.

    Holds singleton instances and provides methods to resolve dependencies
    with support for caching and nested dependencies.

    The container works together with RequestScope to provide request-scoped
    caching and session injection.
    """

    _BASIC_DEPENDENCIES = {
        Update: lambda scope: scope.update,
        Context: lambda scope: scope.context,
        ContextProtocol: lambda scope: scope.context,
        Session: lambda scope: scope.session,
    }

    def __init__(self):
        self._singletons: dict[Dependency, Any] = {}

    def reset(self):
        """Clear all cached singleton instances.

        Useful for testing to ensure a clean state.
        """
        self._singletons = dict()

    async def resolve_dependency(
        self, dep: Depends, scope: RequestScope, dependency_chain: list[str]
    ) -> Any:
        """Resolve a single dependency marked with Depends.

        This method handles caching (if use_cache is True) and delegates
        to _call_dependency to invoke the dependency function.

        Args:
            dep: The Depends marker containing the dependency callable/class.
            scope: Current request scope (provides session, cache, etc.).
            dependency_chain: List of names for error tracing (mutable).

        Returns:
            The resolved dependency value.

        Raises:
            DependencyResolutionError: If the dependency cannot be resolved.
        """
        if dep.dependency is None:
            raise DependencyResolutionError(
                message="Dependency function not provided",
                suggestion="check that you use Annotated[YourRepository, Depends(get_your_repository)] annotation",
            )

        # Check cache if enabled
        scoped = scope.get_dependency(dep)
        if dep.use_cache and scoped is not None:
            return scoped

        # Resolve the dependency
        result = await self._call_dependency(dep.dependency, scope, dependency_chain)

        # Cache if enabled
        if dep.use_cache:
            scope.cache_dependency(dep.dependency, result)

        return result

    def singleton(self, cls: Dependency) -> Any:
        """Retrieve or create a singleton instance of a class.

        Args:
            cls: A class (typically a service) that should be instantiated once.

        Returns:
            The singleton instance.
        """
        if cls not in self._singletons:
            self._singletons[cls] = cls()
        return self._singletons[cls]

    async def _call_dependency(
        self, dependency: Callable, scope: RequestScope, dependency_chain: list[str]
    ) -> Any:
        """Call a dependency function, resolving its dependencies recursively."""
        sig = inspect.signature(dependency)
        type_hints = inspect.get_annotations(dependency)

        # Prepare arguments
        dep_args = {}
        for param_name, param in sig.parameters.items():
            annotation = type_hints.get(param_name, param.annotation)

            dep = _extract_depends(annotation)
            if dep is not None:
                dep_name = getattr(dep.dependency, "__name__", str(dep.dependency))
                dependency_chain.append(dep_name)
                dep_args[param_name] = await self.resolve_dependency(
                    dep, scope, dependency_chain
                )
                continue

            if annotation != inspect.Parameter.empty:
                injected = self._inject_basic_dependencies(annotation, scope)
                if injected is not None:
                    dep_args[param_name] = injected
                    continue

        # Call the dependency
        if inspect.iscoroutinefunction(dependency):
            return await dependency(**dep_args)
        else:
            return dependency(**dep_args)

    def _inject_basic_dependencies(self, type_hint: Type, scope: RequestScope) -> Any:
        """Inject basic dependencies based on type annotation."""
        if type_hint in self._BASIC_DEPENDENCIES:
            return self._BASIC_DEPENDENCIES[type_hint](scope)

        # Singleton services
        if hasattr(type_hint, "__mro__") and BaseService in type_hint.__mro__:
            return self.singleton(type_hint)

        # Repository classes (need session)
        if hasattr(type_hint, "__mro__") and BaseRepository in type_hint.__mro__:
            return type_hint(session=scope.session)

        return None
