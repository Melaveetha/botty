import inspect
from collections.abc import Callable
from typing import Annotated, Any, Type, get_args, get_origin, get_type_hints

from sqlmodel import Session
from telegram import Update

from ..classes import (
    BaseRepository,
    BaseService,
)
from ..exceptions import DependencyResolutionError
from ..context import Context
from .scope import RequestScope
from .typing import Depends


def _extract_depends(annotation):
    if get_origin(annotation) is Annotated:
        _, *metadata = get_args(annotation)
        for meta in metadata:
            if isinstance(meta, Depends):
                return meta
    return None


class DependencyContainer:
    def __init__(self):
        self._singletons: dict[Callable | Type, Any] = {}

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

    def singleton(self, cls: Callable | Type) -> Any:
        """Resolve a single dependency."""
        if cls not in self._singletons:
            self._singletons[cls] = cls()
        return self._singletons[cls]

    async def _call_dependency(self, dependency: Callable, scope: RequestScope) -> Any:
        """Call a dependency function, resolving its own dependencies."""
        sig = inspect.signature(dependency)
        type_hints = get_type_hints(dependency, include_extras=True)

        # Prepare arguments
        dep_args = {}
        for param_name, param in sig.parameters.items():
            annotation = type_hints.get(param_name, param.annotation)

            dep = _extract_depends(annotation)
            if dep is not None:
                dep_args[param_name] = await self.resolve_dependency(dep, scope)
                continue

            if annotation != inspect.Parameter.empty:
                injected = await self._inject(annotation, scope)
                if injected is not None:
                    dep_args[param_name] = injected
                    continue

            if param.default != inspect.Parameter.empty:
                dep_args[param_name] = param.default

        # Call the dependency
        if inspect.iscoroutinefunction(dependency):
            return await dependency(**dep_args)
        else:
            return dependency(**dep_args)

    async def _inject(self, type_hint: Type, scope: RequestScope) -> Any:
        """Inject based on type annotation."""
        if type_hint is Update:
            return scope.update
        if type_hint is Context:
            return scope.context
        if type_hint is Session:
            return scope.session

        # Singleton services
        if hasattr(type_hint, "__mro__") and BaseService in type_hint.__mro__:
            return self.singleton(type_hint)

        # Repository classes (need session)
        if hasattr(type_hint, "__mro__") and BaseRepository in type_hint.__mro__:
            return type_hint(session=scope.session)

        return None


class DependencyResolver:
    """Resolver for FastAPI-like dependencies."""

    def __init__(self, container: DependencyContainer):
        self.container: DependencyContainer = container

    async def resolve_handler(
        self, handler: Callable, scope: RequestScope
    ) -> dict[str, Any]:
        """Resolve all dependencies for a handler."""
        sig = inspect.signature(handler)
        type_hints = get_type_hints(handler, include_extras=True)
        kwargs = {}

        for param_name, param in sig.parameters.items():
            if param_name in ("update", "context"):
                continue

            annotation = type_hints.get(param_name)

            dep = _extract_depends(annotation)
            if dep is not None:
                kwargs[param_name] = await self.container.resolve_dependency(
                    dep,
                    scope,
                )
                continue

            if param.default is not inspect.Parameter.empty:
                kwargs[param_name] = param.default

        return kwargs
