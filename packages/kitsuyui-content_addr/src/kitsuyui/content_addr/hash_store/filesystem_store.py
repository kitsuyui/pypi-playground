from __future__ import annotations

import json
import os
import pathlib
import tempfile
from typing import cast

from ..exceptions import ItemNotFound, RetrievalError, StoreDestroyedError
from ..types import HashValue, RawItem
from .base_store import BaseStoreProtocol, register_store_factory

FORMAT_VERSION = 1
_METADATA_FILENAME = "_metadata.json"


class FileSystemStore(BaseStoreProtocol):
    """File-based hash store implementation.

    Not thread-safe at the HashStore level: concurrent store/retrieve calls
    on the same hash key may interleave. store_item uses an atomic
    write-then-rename so partial writes do not corrupt stored content.
    """

    def __init__(
        self,
        parent_dir: pathlib.Path,
        hasher_algorithm: str | None = None,
    ) -> None:
        self.parent_dir = pathlib.Path(parent_dir).resolve()
        self.parent_dir.mkdir(parents=True, exist_ok=True)
        self._init_or_validate_metadata(hasher_algorithm)
        self._destroyed = False

    def _check_not_destroyed(self) -> None:
        if self._destroyed:
            raise StoreDestroyedError("store has been destroyed")

    def _metadata_path(self) -> pathlib.Path:
        return self.parent_dir / _METADATA_FILENAME

    def _load_metadata(self) -> dict[str, object]:
        try:
            with self._metadata_path().open("r") as f:
                return cast(dict[str, object], json.load(f))
        except (json.JSONDecodeError, OSError) as e:
            raise ValueError(f"Failed to read store metadata: {e}") from e

    def _check_algorithm_conflict(
        self, stored: object, hasher_algorithm: str | None
    ) -> None:
        if (
            not isinstance(stored, str)
            or hasher_algorithm is None
            or stored == hasher_algorithm
        ):
            return
        raise ValueError(
            f"Hasher algorithm mismatch: store was created with "
            f"'{stored}', but '{hasher_algorithm}' was requested."
        )

    def _validate_existing(
        self,
        metadata: dict[str, object],
        hasher_algorithm: str | None,
    ) -> None:
        if metadata.get("format_version") != FORMAT_VERSION:
            raise ValueError(
                f"Incompatible format version: "
                f"{metadata.get('format_version')!r}. "
                f"Expected {FORMAT_VERSION}."
            )
        self._check_algorithm_conflict(
            metadata.get("hasher_algorithm"), hasher_algorithm
        )

    def _write_metadata(self, hasher_algorithm: str | None) -> None:
        metadata_path = self._metadata_path()
        new_metadata: dict[str, object] = {"format_version": FORMAT_VERSION}
        if hasher_algorithm is not None:
            new_metadata["hasher_algorithm"] = hasher_algorithm
        try:
            with metadata_path.open("w") as f:
                json.dump(new_metadata, f)
        except OSError as e:
            metadata_path.unlink(missing_ok=True)
            raise ValueError(f"Failed to write store metadata: {e}") from e

    def _init_or_validate_metadata(self, hasher_algorithm: str | None) -> None:
        if self._metadata_path().exists():
            self._validate_existing(self._load_metadata(), hasher_algorithm)
        else:
            self._write_metadata(hasher_algorithm)

    @classmethod
    def create(
        cls,
        parent_dir: pathlib.Path | str,
        hasher_algorithm: str | None = None,
    ) -> FileSystemStore:
        return cls(pathlib.Path(parent_dir), hasher_algorithm=hasher_algorithm)

    def _file_path(self, hash_value: HashValue) -> pathlib.Path:
        if not hash_value:
            raise ValueError("hash_value must not be empty")
        return self.parent_dir / hash_value.hex()

    def store_item(self, hash_value: HashValue, item: RawItem) -> None:
        self._check_not_destroyed()
        file_path = self._file_path(hash_value)
        with tempfile.NamedTemporaryFile(
            dir=self.parent_dir, delete=False, suffix=".tmp"
        ) as tmp:
            tmp.write(item)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = pathlib.Path(tmp.name)
        tmp_path.replace(file_path)

    def stores(self, hash_value: HashValue) -> bool:
        self._check_not_destroyed()
        file_path = self._file_path(hash_value)
        return file_path.exists()

    def retrieve(self, hash_value: HashValue) -> RawItem:
        self._check_not_destroyed()
        file_path = self._file_path(hash_value)
        try:
            with file_path.open("rb") as f:
                return RawItem(f.read())
        except FileNotFoundError:
            raise ItemNotFound(
                f"Item with hash {hash_value.hex()} not found."
            ) from None
        except OSError as e:
            raise RetrievalError(
                f"IO error retrieving item with hash {hash_value.hex()}."
            ) from e

    def delete(self, hash_value: HashValue) -> None:
        self._check_not_destroyed()
        file_path = self._file_path(hash_value)
        file_path.unlink()

    def clear(self) -> None:
        self._check_not_destroyed()
        # Snapshot the listing before iterating so behaviour is deterministic:
        # files that exist at this point are deleted; files written after the
        # snapshot are not. Not safe for concurrent use without external
        # coordination.
        files = list(self.parent_dir.iterdir())
        for file_path in files:
            if file_path.is_file() and file_path.name != _METADATA_FILENAME:
                file_path.unlink(missing_ok=True)

    def destroy(self) -> None:
        self._check_not_destroyed()
        self.clear()
        self._metadata_path().unlink(missing_ok=True)
        self.parent_dir.rmdir()
        self._destroyed = True


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

    hasher_algorithm = cast(str | None, typed_config.get("hasher_algorithm"))
    return FileSystemStore.create(repo_dir, hasher_algorithm=hasher_algorithm)
