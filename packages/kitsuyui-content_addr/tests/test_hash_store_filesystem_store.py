import pathlib
import tempfile

import pytest

from kitsuyui.content_addr.hash_store.filesystem_store import (
    FileSystemStore,
    factory,
)


@pytest.fixture(scope="function", autouse=True)
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_filesystem_store_store_and_retrieve(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    hash_value = b"hash1"
    item = b"item1"

    store.store_item(hash_value, item)
    assert store.stores(hash_value)
    retrieved_item = store.retrieve(hash_value)
    assert retrieved_item == item

    # second item
    hash_value2 = b"hash2"
    item2 = b"item2"
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


def test_filesystem_store_clear_with_subdirectory(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    # Create a regular file and a subdirectory inside the store dir.
    (pathlib.Path(temp_dir) / "somefile").write_bytes(b"data")
    subdir = pathlib.Path(temp_dir) / "subdir"
    subdir.mkdir()
    (subdir / "nested").write_bytes(b"nested")

    # clear() must remove both the file and the subdirectory.
    store.clear()
    assert list(pathlib.Path(temp_dir).iterdir()) == []


def test_filesystem_store_destroy_with_subdirectory(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    subdir = pathlib.Path(temp_dir) / "subdir"
    subdir.mkdir()
    (subdir / "nested").write_bytes(b"nested")

    # destroy() must succeed even when subdirectories exist.
    store.destroy()
    assert not pathlib.Path(temp_dir).exists()
