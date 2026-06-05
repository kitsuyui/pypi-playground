import json
import pathlib
import tempfile

import pytest

from kitsuyui.content_addr.exceptions import ItemNotFound
from kitsuyui.content_addr.hash_store.filesystem_store import (
    _METADATA_FILENAME,
    FORMAT_VERSION,
    FileSystemStore,
    factory,
)
from kitsuyui.content_addr.types import HashValue, RawItem


@pytest.fixture(scope="function", autouse=True)
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_filesystem_store_store_and_retrieve(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    hash_value = HashValue(b"hash1")
    item = RawItem(b"item1")

    store.store_item(hash_value, item)
    assert store.stores(hash_value)
    retrieved_item = store.retrieve(hash_value)
    assert retrieved_item == item

    # second item
    hash_value2 = HashValue(b"hash2")
    item2 = RawItem(b"item2")
    store.store_item(hash_value2, item2)
    assert store.stores(hash_value2)
    retrieved_item2 = store.retrieve(hash_value2)
    assert retrieved_item2 == item2

    # delete first item
    store.delete(hash_value)
    assert not store.stores(hash_value)
    assert store.stores(hash_value2)

    # clear store
    store.clear()
    assert not store.stores(hash_value)
    assert not store.stores(hash_value2)

    # destroy store (should be no-op for DictStore)
    store.destroy()
    assert not store.stores(hash_value)


def test_filesystem_store_factory(temp_dir) -> None:
    store = factory({"repo_dir": temp_dir})
    assert isinstance(store, FileSystemStore)


def test_filesystem_store_creates_metadata(temp_dir) -> None:
    FileSystemStore(pathlib.Path(temp_dir))
    metadata_path = pathlib.Path(temp_dir) / _METADATA_FILENAME
    assert metadata_path.exists()
    with metadata_path.open() as f:
        metadata = json.load(f)
    assert metadata["format_version"] == FORMAT_VERSION


def test_filesystem_store_records_hasher_algorithm(temp_dir) -> None:
    FileSystemStore(pathlib.Path(temp_dir), hasher_algorithm="sha256")
    metadata_path = pathlib.Path(temp_dir) / _METADATA_FILENAME
    with metadata_path.open() as f:
        metadata = json.load(f)
    assert metadata["hasher_algorithm"] == "sha256"


def test_filesystem_store_algorithm_mismatch_raises(temp_dir) -> None:
    FileSystemStore(pathlib.Path(temp_dir), hasher_algorithm="sha256")
    with pytest.raises(ValueError, match="algorithm mismatch"):
        FileSystemStore(pathlib.Path(temp_dir), hasher_algorithm="sha3_256")


def test_filesystem_store_no_algorithm_on_reopen_ok(temp_dir) -> None:
    FileSystemStore(pathlib.Path(temp_dir), hasher_algorithm="sha256")
    # reopening without specifying algorithm is allowed
    store = FileSystemStore(pathlib.Path(temp_dir))
    assert isinstance(store, FileSystemStore)


def test_filesystem_store_format_version_mismatch_raises(temp_dir) -> None:
    metadata_path = pathlib.Path(temp_dir) / _METADATA_FILENAME
    with metadata_path.open("w") as f:
        json.dump({"format_version": 999}, f)
    with pytest.raises(ValueError, match="Incompatible format version"):
        FileSystemStore(pathlib.Path(temp_dir))


def test_filesystem_store_clear_preserves_metadata(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    store.store_item(HashValue(b"hash1"), RawItem(b"item1"))
    store.clear()
    metadata_path = pathlib.Path(temp_dir) / _METADATA_FILENAME
    assert metadata_path.exists()


def test_filesystem_store_destroy_removes_metadata(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    store.destroy()
    assert not pathlib.Path(temp_dir).exists()


def test_filesystem_store_factory_with_hasher_algorithm(temp_dir) -> None:
    store = factory({"repo_dir": temp_dir, "hasher_algorithm": "sha256"})
    assert isinstance(store, FileSystemStore)
    metadata_path = pathlib.Path(temp_dir) / _METADATA_FILENAME
    with metadata_path.open() as f:
        metadata = json.load(f)
    assert metadata["hasher_algorithm"] == "sha256"


def test_filesystem_store_clear_with_subdirectory(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    # Create a regular file and a subdirectory inside the store dir.
    (pathlib.Path(temp_dir) / "somefile").write_bytes(b"data")
    subdir = pathlib.Path(temp_dir) / "subdir"
    subdir.mkdir()
    (subdir / "nested").write_bytes(b"nested")

    # clear() must remove both the file and the subdirectory, while
    # preserving the store metadata file.
    store.clear()
    remaining = sorted(p.name for p in pathlib.Path(temp_dir).iterdir())
    assert remaining == [_METADATA_FILENAME]


def test_filesystem_store_destroy_with_subdirectory(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    subdir = pathlib.Path(temp_dir) / "subdir"
    subdir.mkdir()
    (subdir / "nested").write_bytes(b"nested")

    # destroy() must succeed even when subdirectories exist.
    store.destroy()
    assert not pathlib.Path(temp_dir).exists()


def test_filesystem_store_retrieve_missing_raises_item_not_found(
    temp_dir,
) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    missing_hash = HashValue(b"does_not_exist")
    with pytest.raises(ItemNotFound):
        store.retrieve(missing_hash)
