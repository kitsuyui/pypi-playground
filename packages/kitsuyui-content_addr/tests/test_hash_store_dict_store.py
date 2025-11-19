from kitsuyui.content_addr.hash_store.dict_store import DictStore, factory


def test_dict_store_store_and_retrieve() -> None:
    store = DictStore()
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


def test_dict_store_factory() -> None:
    store = factory(None)
    assert isinstance(store, DictStore)
