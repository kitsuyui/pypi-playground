from typing import Protocol

from ..types import HashValue, RawItem


class HasherProtocol(Protocol):
    """Protocol for hashing algorithms."""

    @property
    def output_size_bytes(self) -> int:
        """Return the number of bytes produced by this hasher."""
        ...

    def compute_hash(self, item: RawItem) -> HashValue:
        """Compute and return the hash value of the given item."""
        ...
