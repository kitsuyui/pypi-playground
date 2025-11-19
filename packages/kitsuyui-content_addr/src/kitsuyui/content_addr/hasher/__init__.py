import hashlib
from typing import Any, Callable
import functools

from .types import HasherProtocol
from ..types import RawItem, HashValue


"""
Example implementation of a HasherProtocol using SHA-256:

class SHA256Hasher(HasherProtocol):
    def compute_hash(self, item: RawItem) -> HashValue:
        sha256 = hashlib.sha256()
        sha256.update(item)
        return sha256.digest()
"""


def generate_hasher(name: str) -> type[HasherProtocol]:
    class CustomHasher(HasherProtocol):
        def compute_hash(self, item: RawItem) -> HashValue:
            raw_hasher = hashlib.new(name)
            raw_hasher.update(item)
            return raw_hasher.digest()

    return CustomHasher


HASHER_REGISTRY: dict[str, Callable[..., HasherProtocol]] = {}


def __register_hasher(name: str, hasher_factory: Callable[..., HasherProtocol]) -> None:
    """Register a hasher class with the given name."""
    HASHER_REGISTRY[name] = hasher_factory


def register_hasher_factory(name: str):
    """Decorator for registering a hasher factory function.

    Usage:

    @register_hasher_factory("my_hasher")
    def factory(...) -> HasherProtocol:
        ...
    """

    def decorator(
        factory: Callable[..., HasherProtocol],
    ) -> Callable[..., HasherProtocol]:
        __register_hasher(name, factory)

        @functools.wraps(factory)
        def wrapper(*args, **kwargs) -> HasherProtocol:
            hasher = factory(*args, **kwargs)
            return hasher

        return wrapper

    return decorator


def factory(name: str, *args, **kwargs) -> HasherProtocol:
    """Factory function for creating a hasher instance by name."""
    if name not in HASHER_REGISTRY:
        raise ValueError(f"Hasher '{name}' is not registered.")
    hasher_factory = HASHER_REGISTRY[name]
    return hasher_factory(*args, **kwargs)


SHA256Hasher = generate_hasher("sha256")
MD5Hasher = generate_hasher("md5")


@register_hasher_factory("sha256")
def sha256_factory(config: Any) -> HasherProtocol:
    """Factory function for creating a SHA256Hasher class."""
    return SHA256Hasher()


@register_hasher_factory("md5")
def md5_factory(config: Any) -> HasherProtocol:
    """Factory function for creating a MD5Hasher class."""
    return MD5Hasher()


__all__ = [
    "HasherProtocol",
    "SHA256Hasher",
    "MD5Hasher",
    "generate_hasher",
    "register_hasher_factory",
]
