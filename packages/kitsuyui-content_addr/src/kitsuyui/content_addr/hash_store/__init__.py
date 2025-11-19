from __future__ import annotations

from typing import Literal, Any

from dataclasses import dataclass

from .base_store import BaseStoreProtocol
from ..types import RawItem, HashValue
from ..exceptions import ItemAlreadyExists
from ..hasher.types import HasherProtocol
from ..hasher import factory as hasher_factory
from .base_store import factory as store_factory


ConflictAction = Literal["overwrite", "error", "ignore"]
VerifyAction = Literal["delete", "error", "ignore"]


@dataclass
class HashStore:
    hasher: HasherProtocol
    base_store: BaseStoreProtocol

    @classmethod
    def create(
        cls,
        hasher_name: str,
        store_name: str,
        hasher_config: Any = None,
        store_config: Any = None,
    ) -> HashStore:
        return factory(
            hasher_name=hasher_name,
            store_name=store_name,
            hasher_config=hasher_config,
            store_config=store_config,
        )

    def compute_hash(self, item: RawItem) -> HashValue:
        """Compute and return the hash value of the given item."""
        return self.hasher.compute_hash(item)

    def stores(self, hash_value: HashValue) -> bool:
        """Return whether the item with the given hash value is stored."""
        return self.base_store.stores(hash_value)

    def retrieve(self, hash_value: HashValue) -> RawItem:
        """Retrieve and return the item with the given hash value."""
        return self.base_store.retrieve(hash_value)

    def delete(self, hash_value: HashValue) -> None:
        """Delete the item with the given hash value from the store."""
        self.base_store.delete(hash_value)

    def is_valid_stored_item(self, hash_value: HashValue) -> bool:
        """Validate the already stored item by recomputing its hash and comparing it to the given hash value."""
        item = self.retrieve(hash_value)
        computed_hash = self.compute_hash(item)
        return computed_hash == hash_value

    def verify(self, hash_value: HashValue, *, action: VerifyAction = "error") -> bool:
        """Verify the stored item with the given hash value.
        action:
            - 'delete': delete the item if invalid
            - 'error': raise ValueError if invalid
            - 'ignore': do nothing if invalid (default)
        Returns True if the item is valid, False otherwise.
        """
        is_valid = self.is_valid_stored_item(hash_value)
        if not is_valid:
            if action == "delete":
                self.delete(hash_value)
            elif action == "error":
                raise ValueError(
                    f"Stored item with hash {hash_value.hex()} is invalid."
                )
            elif action == "ignore":
                pass
            else:
                raise ValueError(f"Invalid verify action: {action}")
        return is_valid

    def _store_raw(self, hash_value: HashValue, item: RawItem) -> None:
        self.base_store.store_item(hash_value, item)

    def store(
        self, item: RawItem, *, conflicts: ConflictAction = "ignore"
    ) -> HashValue:
        """Store the given item and return its hash value.
        conflicts:
            - 'overwrite': overwrite existing item if exists
            - 'error': raise ItemAlreadyExists if item already exists
            - 'ignore': do nothing if item already exists (default)
        """
        hash_value = self.compute_hash(item)
        if conflicts == "overwrite":
            self._store_raw(hash_value, item)
        elif conflicts == "error":
            if self.stores(hash_value):
                raise ItemAlreadyExists(
                    f"Item with hash {hash_value.hex()} already exists."
                )
            self._store_raw(hash_value, item)
        elif conflicts == "ignore":
            if not self.stores(hash_value):
                self.base_store.store_item(hash_value, item)
        else:
            raise ValueError(f"Invalid conflict action: {conflicts}")
        return hash_value

    def store_if_not_exists(self, item: RawItem) -> HashValue:
        """Store the item only if it does not already exist."""
        hash_value = self.compute_hash(item)
        if not self.stores(hash_value):
            self._store_raw(hash_value, item)
        return hash_value

    def store_or_raise(self, item: RawItem) -> HashValue:
        """Store the item, raising ItemAlreadyExists if it already exists."""
        hash_value = self.compute_hash(item)
        if self.stores(hash_value):
            raise ItemAlreadyExists(
                f"Item with hash {hash_value.hex()} already exists."
            )
        self._store_raw(hash_value, item)
        return hash_value


def factory(
    hasher_name: str,
    store_name: str,
    hasher_config: Any = None,
    store_config: Any = None,
) -> HashStore:
    """Factory function for creating a HashStore instance."""
    hasher = hasher_factory(hasher_name, hasher_config)
    base_store = store_factory(store_name, store_config)
    return HashStore(hasher=hasher, base_store=base_store)


__all__ = [
    "HashStore",
    "BaseStoreProtocol",
    "ConflictAction",
]
