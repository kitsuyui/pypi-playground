from __future__ import annotations

import asyncio

from typing import Protocol, Callable
import functools

from ..types import RawItem, HashValue


class BaseStoreProtocol(Protocol):
    """Protocol for a basic hash store.

    This defines the essential methods that any hash store implementation must provide.
    More specific methods are defined in HashStore
    """

    def store_item(self, hash_value: HashValue, item: RawItem) -> None:
        """Store the given item and return its hash value."""

    def stores(self, hash_value: HashValue) -> bool:
        """Return whether the item with the given hash value is stored."""

    def retrieve(self, hash_value: HashValue) -> RawItem:
        """Retrieve and return the item with the given hash value."""

    def delete(self, hash_value: HashValue) -> None:
        """Delete the item with the given hash value from the store."""

    def clear(self) -> None:
        """Clear all items from the store."""

    def destroy(self) -> None:
        """Destroy the store and clean up any resources."""


class AsyncBaseStoreProtocol(Protocol):
    """Protocol for an asynchronous basic hash store.

    This defines the essential methods that any async hash store implementation must provide.
    More specific methods are defined in HashStore
    """

    async def store_item(self, hash_value: HashValue, item: RawItem) -> None:
        """Store the given item and return its hash value."""

    async def stores(self, hash_value: HashValue) -> bool:
        """Return whether the item with the given hash value is stored."""

    async def retrieve(self, hash_value: HashValue) -> RawItem:
        """Retrieve and return the item with the given hash value."""

    async def delete(self, hash_value: HashValue) -> None:
        """Delete the item with the given hash value from the store."""

    async def clear(self) -> None:
        """Clear all items from the store."""

    async def destroy(self) -> None:
        """Destroy the store and clean up any resources."""


def wrap_async_store_as_sync(
    name: str, async_store_class: type[AsyncBaseStoreProtocol]
) -> type[BaseStoreProtocol]:
    """Convert an asynchronous store to a synchronous store."""

    class Wrapped(BaseStoreProtocol):
        def __init__(self, *args, **kwargs) -> None:
            self.async_store = async_store_class(*args, **kwargs)

        def store_item(self, hash_value: HashValue, item: RawItem) -> None:
            return asyncio.run(self.async_store.store_item(hash_value, item))

        def stores(self, hash_value: HashValue) -> bool:
            return asyncio.run(self.async_store.stores(hash_value))

        def retrieve(self, hash_value: HashValue) -> RawItem:
            return asyncio.run(self.async_store.retrieve(hash_value))

        def delete(self, hash_value: HashValue) -> None:
            return asyncio.run(self.async_store.delete(hash_value))

        def clear(self) -> None:
            return asyncio.run(self.async_store.clear())

        def destroy(self) -> None:
            return asyncio.run(self.async_store.destroy())

    Wrapped.__name__ = name
    return Wrapped


STORE_FACTORIES: dict[str, Callable[..., BaseStoreProtocol]] = {}


def __register_store(name: str, factory: Callable[..., BaseStoreProtocol]) -> None:
    """Register a store class with the given name."""
    STORE_FACTORIES[name] = factory


def register_store_factory(name: str):
    """Decorator for registering a store factory function.

    Usage:

    @register_store_factory("my_store")
    def factory(...) -> BaseStoreProtocol:
        ...
    """

    def decorator(
        factory: Callable[..., BaseStoreProtocol],
    ) -> Callable[..., BaseStoreProtocol]:
        __register_store(name, factory)

        @functools.wraps(factory)
        def wrapper(*args, **kwargs) -> BaseStoreProtocol:
            store_class = factory(*args, **kwargs)
            return store_class

        return wrapper

    return decorator


def factory(name: str, *args, **kwargs) -> BaseStoreProtocol:
    """Factory function for creating a store instance by name."""
    if name not in STORE_FACTORIES:
        raise ValueError(f"Store '{name}' is not registered.")
    store_factory = STORE_FACTORIES[name]
    return store_factory(*args, **kwargs)
