from botty import BaseService


class FileService(BaseService):
    def __init__(self):
        self._file_store = {}  # mapping: file_id -> metadata (in production, use DB)

    def store_file_info(self, file_id: str, file_type: str, caption: str | None = None):
        self._file_store[file_id] = {"type": file_type, "caption": caption}

    def get_file_info(self, file_id: str) -> dict | None:
        return self._file_store.get(file_id)
