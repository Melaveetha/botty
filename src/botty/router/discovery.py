import importlib
import sys
from loguru import logger
from .router import Router
from pathlib import Path
from ..exceptions import HandlerDiscoveryError


def discover_routers(
    path: Path | None = None, project_root: Path | None = None
) -> list[Router]:
    """
    Automatically discover Router instances from Python files in a directory.

    Args:
        path: Directory to scan. Defaults to <project_root>/src/handlers.

    Returns:
        List of discovered Router instances.

    Raises:
        HandlerDiscoveryError: If the directory is not a package or imports fail.
    """
    if project_root is None:
        project_root = _find_project_root()

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        logger.debug(f"Added project root to sys.path: {project_root}")

    if path is None:
        path = project_root / "src" / "handlers"

    if not path.exists():
        raise HandlerDiscoveryError(f"{path} does not exist")

    if not path.is_dir():
        raise HandlerDiscoveryError(f"{path} isn't a directory")

    if not (path / "__init__.py").exists():
        raise HandlerDiscoveryError(
            f"{path} is not a python package",
            suggestion="Consider adding __init__.py to make it importable",
        )

    routers = []

    try:
        routers = _discover_handlers(path, project_root)
    except Exception as e:
        raise HandlerDiscoveryError(
            f"Failed to discover routers: {e}",
            details=f"Handlers path: {path}",
        ) from e

    if len(routers) > 0:
        discovered_routes = "📦 Discovered routers:"
        for name, router in routers:
            discovered_routes += f"\n - {name}"
        logger.info(discovered_routes)

    return [router for _, router in routers]


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


def _discover_handlers(path: Path, project_root: Path) -> list[tuple[str, Router]]:
    base_package = ".".join(path.relative_to(project_root).parts)

    routers = []

    for py_file in path.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
        module_name = f"{base_package}.{py_file.stem}"

        try:
            module = importlib.import_module(module_name)

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, Router):
                    routers.append((py_file.stem, attr))
        except ImportError as e:
            logger.warning(f"Couldn't import module {module_name}: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error during import of {module_name}: {e}")

    return routers
