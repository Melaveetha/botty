import importlib
import sys
from abc import ABC, abstractmethod
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType

from loguru import logger

from ..exceptions import HandlerDiscoveryError
from .router import Router


class ModuleSystem(ABC):
    @abstractmethod
    def add_to_sys_path(self, path: Path) -> None: ...

    @abstractmethod
    def import_module(self, module_name: str) -> ModuleType: ...

    @abstractmethod
    def path_exists(self, path: Path) -> bool: ...

    @abstractmethod
    def is_dir(self, path: Path) -> bool: ...

    @abstractmethod
    def glob(self, path: Path, pattern: str) -> Iterable[Path]: ...


class RealModuleSystem(ModuleSystem):
    def add_to_sys_path(self, path: Path) -> None:
        if str(path) not in sys.path:
            sys.path.insert(0, str(path))
            logger.debug(f"Added project root to sys.path: {path}")

    def import_module(self, module_name: str):
        return importlib.import_module(module_name)

    def path_exists(self, path: Path) -> bool:
        return path.exists()

    def is_dir(self, path: Path) -> bool:
        return path.is_dir()

    def glob(self, path: Path, pattern: str):
        return path.glob(pattern)


def discover_routers(
    path: Path | None = None,
    project_root: Path | None = None,
    module_system: ModuleSystem | None = None,
) -> list[Router]:

    module_system = module_system or RealModuleSystem()

    project_root = project_root or _find_project_root()
    module_system.add_to_sys_path(project_root)

    handlers_path = _resolve_handlers_path(path, project_root)

    _validate_handlers_package(handlers_path, module_system)

    try:
        routers = _discover_modules(
            handlers_path,
            project_root,
            module_system,
        )
    except Exception as e:
        raise HandlerDiscoveryError(
            f"Failed to discover routers: {e}",
            details=f"Handlers path: {handlers_path}",
        ) from e

    _log_discovered(routers)

    return [router for _, router in routers]


def _resolve_handlers_path(
    path: Path | None,
    project_root: Path,
) -> Path:
    return path or project_root / "src" / "handlers"


def _validate_handlers_package(
    path: Path,
    module_system: ModuleSystem,
) -> None:

    if not module_system.path_exists(path):
        raise HandlerDiscoveryError(f"{path} does not exist")

    if not module_system.is_dir(path):
        raise HandlerDiscoveryError(f"{path} isn't a directory")

    if not module_system.path_exists(path / "__init__.py"):
        raise HandlerDiscoveryError(
            f"{path} is not a python package",
            suggestion="Consider adding __init__.py to make it importable",
        )


def _discover_modules(
    path: Path,
    project_root: Path,
    module_system: ModuleSystem,
) -> list[tuple[str, Router]]:

    base_package = ".".join(path.relative_to(project_root).parts)

    routers: list[tuple[str, Router]] = []

    for py_file in module_system.glob(path, "*.py"):
        if py_file.name == "__init__.py":
            continue

        module_name = f"{base_package}.{py_file.stem}"

        module = _safe_import(module_name, module_system)
        if module is None:
            continue

        routers.extend(_extract_routers_from_module(py_file.stem, module))

    return routers


def _find_project_root() -> Path:
    """
    Find project root by looking for pyproject.toml, setup.py, .git
    """
    start = Path.cwd().absolute()

    for current in [start] + list(start.parents):
        if any(
            (current / file).exists() for file in ["pyproject.toml", "setup.py", ".git"]
        ):
            return current

    logger.debug("No project root was found. Falling back to current directory (cwd)")
    return start  # Fallback to start path


def _safe_import(
    module_name: str,
    module_system: ModuleSystem,
):
    try:
        return module_system.import_module(module_name)
    except ImportError as e:
        logger.warning(f"Couldn't import module {module_name}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during import of {module_name}: {e}")
    return None


def _extract_routers_from_module(
    module_name: str,
    module,
) -> list[tuple[str, Router]]:

    routers = []

    try:
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, Router):
                routers.append((module_name, attr))
    except Exception as e:
        logger.exception("Unexpected error during router resolution:", e)

    return routers


def _log_discovered(routers: list[tuple[str, Router]]) -> None:

    if not routers:
        return

    message = "📦 Discovered routers:"
    for name, _ in routers:
        message += f"\n - {name}"

    logger.info(message)
