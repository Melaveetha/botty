from collections.abc import Callable
from typing import Type, TypeAlias

Dependency: TypeAlias = Callable | Type


class Depends:
    """Marks a parameter as a dependency to be injected."""

    def __init__(self, dependency: Dependency, *, use_cache: bool = True):
        self.dependency = dependency
        self.use_cache = use_cache
