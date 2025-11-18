from .base_store import BaseStoreProtocol
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
