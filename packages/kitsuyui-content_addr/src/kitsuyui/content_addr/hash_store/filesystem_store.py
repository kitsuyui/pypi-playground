from __future__ import annotations

import json
import pathlib
from typing import cast

from ..types import HashValue, RawItem
from .base_store import BaseStoreProtocol, register_store_factory


class FileSystemStore(BaseStoreProtocol):
    """File-based hash store implementation."""

    METADATA_FILENAME = "_metadata.json"

    def __init__(
        self, parent_dir: pathlib.Path, hasher_name: str | None = None
    ) -> None:
        self.parent_dir = pathlib.Path(parent_dir)
        self.parent_dir.mkdir(parents=True, exist_ok=True)
        if hasher_name is not None:
            metadata_path = self.parent_dir / self.METADATA_FILENAME
            tmp_path = metadata_path.with_name(metadata_path.name + ".tmp")
            try:
                with tmp_path.open("w") as f:
                    json.dump({"schema_version": 1, "hasher": hasher_name}, f)
                tmp_path.replace(metadata_path)
            except Exception:
                tmp_path.unlink(missing_ok=True)
                raise

    @classmethod
    def create(
        cls, parent_dir: pathlib.Path | str, hasher_name: str | None = None
    ) -> FileSystemStore:
        return cls(pathlib.Path(parent_dir), hasher_name=hasher_name)

    def store_item(self, hash_value: HashValue, item: RawItem) -> None:
        file_path = self.parent_dir / hash_value.hex()
        with file_path.open("wb") as f:
            f.write(item)

    def stores(self, hash_value: HashValue) -> bool:
        file_path = self.parent_dir / hash_value.hex()
        return file_path.exists()

    def retrieve(self, hash_value: HashValue) -> RawItem:
        file_path = self.parent_dir / hash_value.hex()
        with file_path.open("rb") as f:
            return f.read()

    def delete(self, hash_value: HashValue) -> None:
        file_path = self.parent_dir / hash_value.hex()
        file_path.unlink()

    def clear(self) -> None:
        for file_path in self.parent_dir.iterdir():
            if (
                file_path.is_file()
                and file_path.name != self.METADATA_FILENAME
            ):
                file_path.unlink()

    def destroy(self) -> None:
        self.clear()
        self.parent_dir.rmdir()


@register_store_factory("filesystem_store")
def factory(config: object | None = None) -> BaseStoreProtocol:
    """Factory function for creating a FileSystemStore class."""

    repo_key = "repo_dir"

    if not isinstance(config, dict) or repo_key not in config:
        raise ValueError("Invalid config for FileSystemStore")

    typed_config = cast(dict[str, object], config)
    repo_dir = typed_config[repo_key]
    if not isinstance(repo_dir, (str, pathlib.Path)):
        raise ValueError(f"{repo_key} must be a string or pathlib.Path")

    hasher_name = typed_config.get("hasher_name")
    hasher_name_str = str(hasher_name) if hasher_name is not None else None
    return FileSystemStore.create(repo_dir, hasher_name=hasher_name_str)
