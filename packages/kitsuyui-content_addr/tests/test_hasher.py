import pytest

from kitsuyui.content_addr.hasher import SHA256Hasher, generate_hasher
from kitsuyui.content_addr.types import RawItem


def test_sha256_hasher() -> None:
    hasher = SHA256Hasher()
    item = RawItem(b"Hello, World!")
    expected_hash_hex = (
        "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    )
    computed_hash = hasher.compute_hash(item)
    assert computed_hash.hex() == expected_hash_hex


def test_generate_hasher_rejects_md5() -> None:
    with pytest.raises(ValueError, match="Unsafe hash algorithm"):
        generate_hasher("md5")
