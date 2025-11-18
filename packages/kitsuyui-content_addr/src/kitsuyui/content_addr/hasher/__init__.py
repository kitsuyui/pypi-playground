import hashlib

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


SHA256Hasher = generate_hasher("sha256")
MD5Hasher = generate_hasher("md5")


__all__ = [
    "HasherProtocol",
    "SHA256Hasher",
    "MD5Hasher",
    "generate_hasher",
]
