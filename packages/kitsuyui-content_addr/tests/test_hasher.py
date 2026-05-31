from kitsuyui.content_addr.hasher import MD5Hasher, SHA256Hasher
from kitsuyui.content_addr.types import RawItem


def test_sha256_hasher() -> None:
    hasher = SHA256Hasher()
    assert hasher.output_size_bytes == 32  # 256 bits
    item = RawItem(b"Hello, World!")
    expected_hash_hex = (
        "dffd6021bb2bd5b0af676290809ec3a53191dd81c7f70a4b28688a362182986f"
    )
    computed_hash = hasher.compute_hash(item)
    assert computed_hash.hex() == expected_hash_hex
    assert len(computed_hash) == hasher.output_size_bytes


def test_md5_hasher() -> None:
    hasher = MD5Hasher()
    assert hasher.output_size_bytes == 16  # 128 bits
    item = RawItem(b"Hello, World!")
    expected_hash_hex = "65a8e27d8879283831b664bd8b7f0ad4"
    computed_hash = hasher.compute_hash(item)
    assert computed_hash.hex() == expected_hash_hex
    assert len(computed_hash) == hasher.output_size_bytes
