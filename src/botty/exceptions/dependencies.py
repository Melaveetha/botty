from .base import BottyError


class DependencyResolutionError(BottyError):
    """Raise when dependency resolution fails"""

    def __init__(
        self,
        message: str,
        dependency_chain: list[str] | None = None,
        parameter_name: str | None = None,
        handler_name: str | None = None,
        suggestion: str | None = None,
    ):
        self.dependency_chain: list[str] = dependency_chain or list()

        details = []
        if handler_name is not None:
            details.append(f"Handler: {handler_name}")
        if parameter_name is not None:
            details.append(f"Parameter: {parameter_name}")
        if len(self.dependency_chain) > 0:
            details.append(f"Dependency chain: {' -> '.join(self.dependency_chain)}")

        super().__init__(message, "\n".join(details), suggestion)
