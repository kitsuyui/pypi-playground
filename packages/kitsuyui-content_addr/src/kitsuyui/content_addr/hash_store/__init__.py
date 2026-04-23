from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ..exceptions import ItemAlreadyExists
from ..hasher import factory as hasher_factory
from ..hasher.types import HasherProtocol
from ..types import HashValue, RawItem
from .base_store import BaseStoreProtocol
from .base_store import factory as store_factory

ConflictAction = Literal["overwrite", "error", "ignore"]
VerifyAction = Literal["delete", "error", "ignore"]
StoreConfig = dict[str, str | None]


@dataclass
class HashStore:
    hasher: HasherProtocol
    base_store: BaseStoreProtocol

    @classmethod
    def create(
        cls,
        hasher_name: str,
        store_name: str,
        hasher_config: object | None = None,
        store_config: StoreConfig | None = None,
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
        """Validate a stored item by recomputing its hash."""
        item = self.retrieve(hash_value)
        computed_hash = self.compute_hash(item)
        return computed_hash == hash_value

    def _delete_invalid_stored_item(self, hash_value: HashValue) -> None:
        self.delete(hash_value)

    def _raise_invalid_stored_item(self, hash_value: HashValue) -> None:
        raise ValueError(
            f"Stored item with hash {hash_value.hex()} is invalid."
        )

    def _ignore_invalid_stored_item(self, _hash_value: HashValue) -> None:
        return None

    def _handle_invalid_stored_item(
        self, hash_value: HashValue, action: VerifyAction
    ) -> None:
        handlers = {
            "delete": self._delete_invalid_stored_item,
            "error": self._raise_invalid_stored_item,
            "ignore": self._ignore_invalid_stored_item,
        }
        handler = handlers.get(action)
        if handler is None:
            raise ValueError(f"Invalid verify action: {action}")
        handler(hash_value)

    def verify(
        self, hash_value: HashValue, *, action: VerifyAction = "error"
    ) -> bool:
        """Verify the stored item with the given hash value.
        action:
            - 'delete': delete the item if invalid
            - 'error': raise ValueError if invalid
            - 'ignore': do nothing if invalid (default)
        Returns True if the item is valid, False otherwise.
        """
        is_valid = self.is_valid_stored_item(hash_value)
        if is_valid:
            return True
        self._handle_invalid_stored_item(hash_value, action)
        return False

    def _store_raw(self, hash_value: HashValue, item: RawItem) -> None:
        self.base_store.store_item(hash_value, item)

    def _store_overwriting(
        self, hash_value: HashValue, item: RawItem
    ) -> None:
        self._store_raw(hash_value, item)

    def _store_with_error_on_conflict(
        self, hash_value: HashValue, item: RawItem
    ) -> None:
        if self.stores(hash_value):
            raise ItemAlreadyExists(
                f"Item with hash {hash_value.hex()} already exists."
            )
        self._store_raw(hash_value, item)

    def _store_ignoring_conflicts(
        self, hash_value: HashValue, item: RawItem
    ) -> None:
        if not self.stores(hash_value):
            self._store_raw(hash_value, item)

    def _store_with_conflict_policy(
        self,
        hash_value: HashValue,
        item: RawItem,
        conflicts: ConflictAction,
    ) -> None:
        handlers = {
            "overwrite": self._store_overwriting,
            "error": self._store_with_error_on_conflict,
            "ignore": self._store_ignoring_conflicts,
        }
        handler = handlers.get(conflicts)
        if handler is None:
            raise ValueError(f"Invalid conflict action: {conflicts}")
        handler(hash_value, item)

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
        self._store_with_conflict_policy(hash_value, item, conflicts)
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
    hasher_config: object | None = None,
    store_config: StoreConfig | None = None,
) -> HashStore:
    """Factory function for creating a HashStore instance."""
    hasher = hasher_factory(hasher_name, hasher_config)
    base_store = store_factory(store_name, store_config)
    return HashStore(hasher=hasher, base_store=base_store)


__all__ = [
    "BaseStoreProtocol",
    "ConflictAction",
    "HashStore",
]
