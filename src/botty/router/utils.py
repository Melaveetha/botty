import importlib
import sys
from loguru import logger
from .router import Router
from pathlib import Path
from ..exceptions import HandlerDiscoveryError


def discover_routers(path: Path | None = None) -> list[Router]:
    project_root = find_project_root()

    if path is None:
        path = project_root / "src" / "handlers"

    try:
        routers: list[tuple[str, Router]] = discover_routers_util(
            path, package_root=project_root
        )
    except Exception as e:
        raise HandlerDiscoveryError(
            f"Failed to discover routers: {e}",
            details=f"Handlers path: {path}",
        ) from e

    discovered_routes = "📦 Discovered routers:"
    for name, router in routers:
        discovered_routes += f"\n - {name}"
    logger.info(discovered_routes)
    return [router for _, router in routers]


def find_project_root(start_path: Path | None = None) -> Path:
    """
    Find project root by looking for pyproject.toml or setup.py
    """
    if start_path is None:
        start_path = Path.cwd()

    # Go up the directory tree
    current = start_path.absolute()

    while current != current.parent:  # Stop at root
        if (
            (current / "pyproject.toml").exists()
            or (current / "setup.py").exists()
            or (current / "setup.cfg").exists()
        ):
            return current
        current = current.parent

    return start_path  # Fallback to start path


def discover_routers_util(
    directory: Path, package_root: Path | None = None
) -> list[tuple[str, Router]]:
    if package_root is None:
        package_root = find_project_root()
    if not directory.exists():
        return []
    if not (directory / "__init__.py").exists():
        raise ImportError(
            f"Directory {directory} is not a Python package. "
            f"Add __init__.py to make it importable."
        )

    discovered: list[tuple[str, Router]] = []

    try:
        # Get relative module path from package_root
        rel_path = directory.relative_to(package_root)
        package_name = ".".join(rel_path.parts)
    except ValueError:
        # If directory is not under package_root, use its name
        package_name = directory.name

    # Add package_root to sys.path for imports
    original_sys_path = sys.path.copy()
    if str(package_root) not in sys.path:
        sys.path.insert(0, str(package_root))

    try:
        # Find Python files
        for py_file in directory.glob("*.py"):
            if py_file.name.startswith("__"):
                continue

            module_name = f"{package_name}.{py_file.stem}"
            try:
                module = importlib.import_module(module_name)

                # Find routers
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, Router):
                        discovered.append((py_file.stem, attr))

            except ImportError as e:
                print(f"Warning: Could not import {module_name}: {e}")
                continue

    finally:
        sys.path = original_sys_path

    return discovered
