from pathlib import Path
from types import SimpleNamespace

import pytest

from botty import Router
from botty.exceptions import HandlerDiscoveryError
from botty.routing import discover_routers
from botty.testing.discovery import FakeModuleSystem


def test_raises_if_path_does_not_exist():
    project_root = Path("/project")
    handlers = project_root / "src" / "handlers"

    fake = FakeModuleSystem(
        existing_paths={project_root},
        directories={project_root},
    )

    with pytest.raises(HandlerDiscoveryError) as exc:
        discover_routers(
            path=handlers,
            project_root=project_root,
            module_system=fake,
        )

    assert "does not exist" in str(exc.value)


def test_raises_if_not_directory():
    project_root = Path("/project")
    handlers = project_root / "src" / "handlers"

    fake = FakeModuleSystem(
        existing_paths={handlers, project_root},
        directories={project_root},  # handlers NOT directory
    )

    with pytest.raises(HandlerDiscoveryError) as exc:
        discover_routers(
            path=handlers,
            project_root=project_root,
            module_system=fake,
        )

    assert "isn't a directory" in str(exc.value)


def test_raises_if_not_package():
    project_root = Path("/project")
    handlers = project_root / "src" / "handlers"

    fake = FakeModuleSystem(
        existing_paths={handlers, project_root},
        directories={handlers, project_root},
    )

    with pytest.raises(HandlerDiscoveryError) as exc:
        discover_routers(
            path=handlers,
            project_root=project_root,
            module_system=fake,
        )

    assert "not a python package" in str(exc.value)


def test_discovers_router_instances(caplog):
    project_root = Path("/project")
    handlers = project_root / "src" / "handlers"
    init_file = handlers / "__init__.py"

    router = Router("users")

    fake_module = SimpleNamespace(router=router)

    fake = FakeModuleSystem(
        existing_paths={handlers, project_root, init_file},
        directories={handlers, project_root},
        files=[handlers / "users.py"],
        modules={"src.handlers.users": fake_module},
    )

    routers = discover_routers(
        path=handlers,
        project_root=project_root,
        module_system=fake,
    )

    assert len(routers) == 1
    assert routers[0] is router

    # Verify logging
    assert "Discovered routers" in caplog.text


def test_ignores_modules_without_router():
    project_root = Path("/project")
    handlers = project_root / "src" / "handlers"
    init_file = handlers / "__init__.py"

    fake_module = SimpleNamespace()

    fake = FakeModuleSystem(
        existing_paths={handlers, project_root, init_file},
        directories={handlers, project_root},
        files=[handlers / "empty.py"],
        modules={"src.handlers.empty": fake_module},
    )

    routers = discover_routers(
        path=handlers,
        project_root=project_root,
        module_system=fake,
    )

    assert routers == []


def test_import_error_is_logged_and_skipped(caplog):
    project_root = Path("/project")
    handlers = project_root / "src" / "handlers"
    init_file = handlers / "__init__.py"

    fake = FakeModuleSystem(
        existing_paths={handlers, project_root, init_file},
        directories={handlers, project_root},
        files=[handlers / "broken.py"],
        import_side_effect=ImportError("boom"),
    )

    routers = discover_routers(
        path=handlers,
        project_root=project_root,
        module_system=fake,
    )

    assert routers == []
    assert "Couldn't import module" in caplog.text


def test_unexpected_exception_is_logged(caplog):
    project_root = Path("/project")
    handlers = project_root / "src" / "handlers"
    init_file = handlers / "__init__.py"

    class ExplodingModule:
        def __dir__(self):
            raise RuntimeError("unexpected")

    fake = FakeModuleSystem(
        existing_paths={handlers, project_root, init_file},
        directories={handlers, project_root},
        files=[handlers / "weird.py"],
        modules={"src.handlers.weird": ExplodingModule()},
    )

    routers = discover_routers(
        path=handlers,
        project_root=project_root,
        module_system=fake,
    )

    assert routers == []
    assert "Unexpected error during router resolution" in caplog.text


def test_wrapped_exception_from_discovery():
    project_root = Path("/project")
    handlers = project_root / "src" / "handlers"
    init_file = handlers / "__init__.py"

    fake = FakeModuleSystem(
        existing_paths={handlers, project_root, init_file},
        directories={handlers, project_root},
    )

    # Patch glob to raise
    def exploding_glob(*args, **kwargs):
        raise RuntimeError("catastrophic")

    fake.glob = exploding_glob  # ty: ignore [invalid-assignment]

    with pytest.raises(HandlerDiscoveryError) as exc:
        discover_routers(
            path=handlers,
            project_root=project_root,
            module_system=fake,
        )

    assert "Failed to discover routers" in str(exc.value)


def test_project_root_added_to_sys_path():
    project_root = Path("/project")
    handlers = project_root / "src" / "handlers"
    init_file = handlers / "__init__.py"

    fake = FakeModuleSystem(
        existing_paths={handlers, project_root, init_file},
        directories={handlers, project_root},
    )

    discover_routers(
        path=handlers,
        project_root=project_root,
        module_system=fake,
    )

    assert project_root in fake.added_sys_paths
