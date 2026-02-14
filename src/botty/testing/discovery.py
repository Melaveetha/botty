from botty.routing.discovery import ModuleSystem
from pathlib import Path


class FakeModuleSystem(ModuleSystem):
    def __init__(
        self,
        *,
        existing_paths=None,
        directories=None,
        files=None,
        modules=None,
        import_side_effect=None,
    ):
        self.existing_paths = set(existing_paths or [])
        self.directories = set(directories or [])
        self.files = files or []
        self.modules = modules or {}
        self.import_side_effect = import_side_effect
        self.added_sys_paths = []

    def add_to_sys_path(self, path: Path):
        self.added_sys_paths.append(path)

    def import_module(self, module_name: str):
        if self.import_side_effect:
            raise self.import_side_effect
        return self.modules[module_name]

    def path_exists(self, path: Path) -> bool:
        return path in self.existing_paths

    def is_dir(self, path: Path) -> bool:
        return path in self.directories

    def glob(self, path: Path, pattern: str):
        return self.files
