from typing import Any
from .base_store import BaseStoreProtocol, register_store_factory
from ..types import HashValue, RawItem


class DictStore(BaseStoreProtocol):
    """In-memory dictionary-based hash store implementation.
    This is mainly for testing and demonstration purposes.
    """

    def __init__(self) -> None:
        self._store: dict[bytes, bytes] = {}

    def store_item(self, hash_value: HashValue, item: RawItem) -> None:
        self._store[hash_value] = item

    def stores(self, hash_value: HashValue) -> bool:
        return hash_value in self._store

    def retrieve(self, hash_value: HashValue) -> RawItem:
        return self._store[hash_value]

    def delete(self, hash_value: HashValue) -> None:
        del self._store[hash_value]

    def clear(self) -> None:
        self._store.clear()

    def destroy(self) -> None:
        self.clear()


@register_store_factory("dict_store")
def factory(config: Any) -> BaseStoreProtocol:
    """Factory function for creating a DictStore class."""
    return DictStore()
