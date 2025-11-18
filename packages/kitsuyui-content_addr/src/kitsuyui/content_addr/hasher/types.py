from typing import Protocol

from ..types import RawItem, HashValue


class HasherProtocol(Protocol):
    """Protocol for hashing algorithms."""

    def compute_hash(self, item: RawItem) -> HashValue:
        """Compute and return the hash value of the given item."""
        ...
