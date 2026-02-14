from typing import Any

from botty.di import Dependency, DependencyContainer, Depends, RequestScope


class TestDependencyContainer(DependencyContainer):
    """Allows registration of test doubles for any type."""

    __test__ = False

    def __init__(self):
        super().__init__()
        self._overrides: dict[Dependency, Any] = {}

    def override(self, cls: Dependency, instance: Any):
        self._overrides[cls] = instance

    async def resolve_dependency(
        self, dep: Depends, scope: RequestScope, dependency_chain: list[str]
    ) -> Any:
        # Give precedence to overrides
        if dep.dependency in self._overrides:
            return self._overrides[dep.dependency]
        return await super().resolve_dependency(dep, scope, dependency_chain)
