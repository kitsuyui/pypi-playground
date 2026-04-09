"""kitsuyui.content_addr package

This package provides content-addressable storage functionality.
"""

# https://packaging-guide.openastronomy.org/en/latest/advanced/versioning.html
from ._version import __version__
from .hash_store import HashStore
from .hash_store.base_store import register_store_factory
from .hasher import register_hasher_factory

__all__ = [
    "HashStore",
    "__version__",
    "register_hasher_factory",
    "register_store_factory",
]
