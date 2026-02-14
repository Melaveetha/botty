"""
Dependency injection internals.
"""

from .container import DependencyContainer
from .markers import Dependency, Depends
from .resolver import DependencyResolver
from .scope import RequestScope
from .types import Handler, HandlerProtocol, HandlerResponse

__all__ = [
    "DependencyContainer",
    "DependencyResolver",
    "RequestScope",
    "Depends",
    "Handler",
    "HandlerProtocol",
    "HandlerResponse",
    "Dependency",
]
