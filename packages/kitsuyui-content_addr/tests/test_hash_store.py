import tempfile
import pytest

from kitsuyui.content_addr.hash_store import HashStore, factory
from kitsuyui.content_addr.hasher import SHA256Hasher
from kitsuyui.content_addr.hash_store.dict_store import DictStore
from kitsuyui.content_addr.exceptions import ItemAlreadyExists


def test_example_usage() -> None:
    store = HashStore.create(hasher_name="sha256", store_name="dict_store")
    item = b"example item"
    hash_value = store.store(item)
    assert store.stores(hash_value)
    retrieved_item = store.retrieve(hash_value)
    assert retrieved_item == item


def test_hash_store() -> None:
    store = HashStore(hasher=SHA256Hasher(), base_store=DictStore())
    item = b"test item"
    hash_value = store.store(item)
    assert store.stores(hash_value)
    retrieved_item = store.retrieve(hash_value)
    assert retrieved_item == item

    # storing the same item again should be fine (default conflict action is 'ignore')
    store.store(item)

    # trying to store the same item with conflict action 'error' should raise ItemAlreadyExists
    with pytest.raises(ItemAlreadyExists):
        store.store(item, conflicts="error")

    # validate stored item should return True
    assert store.verify(hash_value, action="ignore")

    # break the item in the store to test validation failure
    store._store_raw(hash_value, b"corrupted item")
    assert not store.verify(hash_value, action="ignore")
    with pytest.raises(ValueError):
        store.verify(hash_value, action="error")

    # overwrite the corrupted item with the correct one and test overwrite action
    store.store(item, conflicts="overwrite")
    assert store.verify(hash_value, action="ignore")

    # break the item again and test delete action
    store._store_raw(hash_value, b"corrupted item")
    store.verify(hash_value, action="delete")
    assert not store.stores(hash_value)


def test_hash_store_factory() -> None:
    store = factory(
        hasher_name="sha256",
        store_name="dict_store",
    )
    assert isinstance(store.base_store, DictStore)
    assert isinstance(store.hasher, SHA256Hasher)

    item = b"another test item"
    hash_value = store.store(item)
    assert store.stores(hash_value)

    with tempfile.TemporaryDirectory() as temp_dir:
        store2 = factory(
            hasher_name="md5",
            store_name="filesystem_store",
            store_config={"repo_dir": temp_dir},
        )
        assert not store2.stores(hash_value)
        hash_value2 = store2.store(item)
        assert store2.stores(hash_value2)
