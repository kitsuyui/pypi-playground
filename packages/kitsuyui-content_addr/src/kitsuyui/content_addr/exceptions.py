class ContentHashBaseError(Exception):
    """Base class for content hashing errors."""


class HashStoreError(ContentHashBaseError):
    """Base class for hash store errors."""


class ItemAlreadyExists(HashStoreError, KeyError):
    """Raised when trying to store an item that already exists."""


class ItemNotFound(HashStoreError, KeyError):
    """Raised when trying to access an item that does not exist."""


class RetrievalError(HashStoreError, IOError):
    """Raised when there is an error retrieving an item. (IO error, etc.)"""


class CorruptedItemError(HashStoreError):
    """Raised when a stored item is found to be corrupted."""
