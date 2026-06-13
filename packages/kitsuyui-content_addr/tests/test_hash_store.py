import tempfile

import pytest

from kitsuyui.content_addr.exceptions import (
    CorruptedItemError,
    ItemAlreadyExists,
    ItemNotFound,
)
from kitsuyui.content_addr.hash_store import HashStore, factory
from kitsuyui.content_addr.hash_store.dict_store import DictStore
from kitsuyui.content_addr.hasher import SHA256Hasher
from kitsuyui.content_addr.types import HashValue, RawItem


def test_example_usage() -> None:
    store = HashStore.create(hasher_name="sha256", store_name="dict_store")
    item = RawItem(b"example item")
    hash_value = store.store(item)
    assert store.stores(hash_value)
    retrieved_item = store.retrieve(hash_value)
    assert retrieved_item == item


def test_hash_store() -> None:
    store = HashStore(hasher=SHA256Hasher(), base_store=DictStore())
    item = RawItem(b"test item")
    hash_value = store.store(item)
    assert store.stores(hash_value)
    retrieved_item = store.retrieve(hash_value)
    assert retrieved_item == item

    # Storing the same item again should be fine.
    store.store(item)

    # Conflict action "error" should raise ItemAlreadyExists.
    with pytest.raises(ItemAlreadyExists):
        store.store(item, conflicts="error")

    with pytest.raises(ValueError):
        store.store(item, conflicts="unexpected")  # type: ignore[arg-type]

    # validate stored item should return True
    assert store.verify(hash_value, action="ignore")

    # break the item in the store to test validation failure
    store._store_raw(hash_value, RawItem(b"corrupted item"))
    assert not store.verify(hash_value, action="ignore")
    with pytest.raises(CorruptedItemError):
        store.verify(hash_value, action="error")
    with pytest.raises(ValueError):
        store.verify(hash_value, action="unexpected")  # type: ignore[arg-type]

    # Overwrite the corrupted item with the correct one.
    store.store(item, conflicts="overwrite")
    assert store.verify(hash_value, action="ignore")

    # break the item again and test delete action
    store._store_raw(hash_value, RawItem(b"corrupted item"))
    store.verify(hash_value, action="delete")
    assert not store.stores(hash_value)


def test_store_if_not_exists() -> None:
    """store_if_not_exists is equivalent to store(conflicts="ignore")."""
    store = HashStore(hasher=SHA256Hasher(), base_store=DictStore())
    item = RawItem(b"alias ignore item")
    hash_value = store.store_if_not_exists(item)
    assert store.stores(hash_value)
    # Second call must not raise and must return the same hash.
    hash_value2 = store.store_if_not_exists(item)
    assert hash_value == hash_value2


def test_store_or_raise() -> None:
    """store_or_raise is equivalent to store(conflicts="error")."""
    store = HashStore(hasher=SHA256Hasher(), base_store=DictStore())
    item = RawItem(b"alias error item")
    hash_value = store.store_or_raise(item)
    assert store.stores(hash_value)
    # Second call must raise ItemAlreadyExists.
    with pytest.raises(ItemAlreadyExists):
        store.store_or_raise(item)


def test_hash_store_is_valid_missing_item_raises_item_not_found() -> None:
    store = HashStore(hasher=SHA256Hasher(), base_store=DictStore())
    missing_hash = HashValue(b"\x00" * 32)
    with pytest.raises(ItemNotFound):
        store.is_valid_stored_item(missing_hash)
    with pytest.raises(ItemNotFound):
        store.verify(missing_hash)


def test_hash_store_factory() -> None:
    store = factory(
        hasher_name="sha256",
        store_name="dict_store",
    )
    assert isinstance(store.base_store, DictStore)
    assert isinstance(store.hasher, SHA256Hasher)

    item = RawItem(b"another test item")
    hash_value = store.store(item)
    assert store.stores(hash_value)

    with tempfile.TemporaryDirectory() as temp_dir:
        store2 = factory(
            hasher_name="sha256",
            store_name="filesystem_store",
            store_config={"repo_dir": temp_dir},
        )
        assert not store2.stores(hash_value)
        hash_value2 = store2.store(item)
        assert store2.stores(hash_value2)


def test_hash_store_factory_rejects_md5() -> None:
    with pytest.raises(ValueError, match="Hasher 'md5' is not registered"):
        factory(
            hasher_name="md5",
            store_name="dict_store",
        )
