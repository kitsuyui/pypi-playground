import pytest

from kitsuyui.content_addr.hash_store import HashStore
from kitsuyui.content_addr.hasher import SHA256Hasher
from kitsuyui.content_addr.hash_store.dict_store import DictStore
from kitsuyui.content_addr.exceptions import ItemAlreadyExists


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
