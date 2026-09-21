from pathlib import Path


class LocalStorage:
    """Файловое хранилище на диске. Под S3 меняется реализация, интерфейс тот же."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, relative_path: str, data: bytes) -> Path:
        target = self.root / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return target

    def path(self, relative_path: str) -> Path:
        return self.root / relative_path

    def exists(self, relative_path: str) -> bool:
        return (self.root / relative_path).exists()
