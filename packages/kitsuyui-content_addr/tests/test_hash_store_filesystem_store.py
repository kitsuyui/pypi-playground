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


def test_filesystem_store_empty_hash_value_raises(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    empty_hash = b""
    with pytest.raises(ValueError, match="hash_value must not be empty"):
        store.store_item(empty_hash, b"data")
    with pytest.raises(ValueError, match="hash_value must not be empty"):
        store.stores(empty_hash)
    with pytest.raises(ValueError, match="hash_value must not be empty"):
        store.retrieve(empty_hash)
    with pytest.raises(ValueError, match="hash_value must not be empty"):
        store.delete(empty_hash)
