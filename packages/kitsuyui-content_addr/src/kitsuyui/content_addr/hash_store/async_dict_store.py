import asyncio

from .base_store import AsyncBaseStoreProtocol
from .dict_store import DictStore
from ..types import HashValue, RawItem


class AsyncDictStore(AsyncBaseStoreProtocol):
    """This is an example implementation of an asynchronous Store."""

    def __init__(self) -> None:
        self.actual_store = DictStore()

    async def wait_for_io(self) -> None:
        await asyncio.sleep(0)  # Simulate an async I/O operation

    async def store_item(self, hash_value: HashValue, item: RawItem) -> None:
        await self.wait_for_io()
        self.actual_store.store_item(hash_value, item)

    async def stores(self, hash_value: HashValue) -> bool:
        await self.wait_for_io()
        return self.actual_store.stores(hash_value)

    async def retrieve(self, hash_value: HashValue) -> RawItem:
        await self.wait_for_io()
        return self.actual_store.retrieve(hash_value)

    async def delete(self, hash_value: HashValue) -> None:
        await self.wait_for_io()
        self.actual_store.delete(hash_value)

    async def clear(self) -> None:
        await self.wait_for_io()
        self.actual_store.clear()

    async def destroy(self) -> None:
        await self.clear()
