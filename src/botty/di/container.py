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
    _BASIC_DEPENDENCIES = {
        Update: lambda scope: scope.update,
        Context: lambda scope: scope.context,
        ContextProtocol: lambda scope: scope.context,
        Session: lambda scope: scope.session,
    }

    def __init__(self):
        self._singletons: dict[Dependency, Any] = {}

    def reset(self):
        self._singletons = dict()

    async def resolve_dependency(self, dep: Depends, scope: RequestScope) -> Any:
        """Resolve a single dependency."""
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
        result = await self._call_dependency(dep.dependency, scope)

        # Cache if enabled
        if dep.use_cache:
            scope.cache_dependency(dep.dependency, result)

        return result

    def singleton(self, cls: Dependency) -> Any:
        """Resolve a single dependency."""
        if cls not in self._singletons:
            self._singletons[cls] = cls()
        return self._singletons[cls]

    async def _call_dependency(self, dependency: Callable, scope: RequestScope) -> Any:
        """Call a dependency function, resolving its own dependencies."""
        sig = inspect.signature(dependency)
        type_hints = inspect.get_annotations(dependency)

        # Prepare arguments
        dep_args = {}
        for param_name, param in sig.parameters.items():
            annotation = type_hints.get(param_name, param.annotation)

            dep = _extract_depends(annotation)
            if dep is not None:
                dep_args[param_name] = await self.resolve_dependency(dep, scope)
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
        """Inject based on type annotation."""
        if type_hint in self._BASIC_DEPENDENCIES:
            return self._BASIC_DEPENDENCIES[type_hint](scope)

        # Singleton services
        if hasattr(type_hint, "__mro__") and BaseService in type_hint.__mro__:
            return self.singleton(type_hint)

        # Repository classes (need session)
        if hasattr(type_hint, "__mro__") and BaseRepository in type_hint.__mro__:
            return type_hint(session=scope.session)

        return None
