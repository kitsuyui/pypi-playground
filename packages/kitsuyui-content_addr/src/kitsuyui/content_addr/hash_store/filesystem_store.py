from __future__ import annotations

import pathlib

from typing import Any
from .base_store import BaseStoreProtocol, register_store_factory
from ..types import HashValue, RawItem


class FileSystemStore(BaseStoreProtocol):
    """File-based hash store implementation."""

    def __init__(self, parent_dir: pathlib.Path) -> None:
        self.parent_dir = pathlib.Path(parent_dir)
        self.parent_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def create(cls, parent_dir: pathlib.Path | str) -> FileSystemStore:
        return cls(pathlib.Path(parent_dir))

    def store_item(self, hash_value: HashValue, item: RawItem) -> None:
        file_path = self.parent_dir / hash_value.hex()
        with open(file_path, "wb") as f:
            f.write(item)

    def stores(self, hash_value: HashValue) -> bool:
        file_path = self.parent_dir / hash_value.hex()
        return file_path.exists()

    def retrieve(self, hash_value: HashValue) -> RawItem:
        file_path = self.parent_dir / hash_value.hex()
        with open(file_path, "rb") as f:
            return f.read()

    def delete(self, hash_value: HashValue) -> None:
        file_path = self.parent_dir / hash_value.hex()
        file_path.unlink()

    def clear(self) -> None:
        for file_path in self.parent_dir.iterdir():
            if file_path.is_file():
                file_path.unlink()

    def destroy(self) -> None:
        self.clear()
        self.parent_dir.rmdir()


@register_store_factory("filesystem_store")
def factory(config: Any) -> BaseStoreProtocol:
    """Factory function for creating a FileSystemStore class."""

    repo_key = "repo_dir"

    if not isinstance(config, dict) or repo_key not in config:
        raise ValueError("Invalid config for FileSystemStore")

    repo_dir = config[repo_key]
    if not isinstance(repo_dir, (str, pathlib.Path)):
        raise ValueError(f"{repo_key} must be a string or pathlib.Path")

    return FileSystemStore.create(repo_dir)
