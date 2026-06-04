import json
import pathlib
import tempfile

import pytest

from kitsuyui.content_addr.hash_store.filesystem_store import (
    FileSystemStore,
    factory,
)


@pytest.fixture(scope="function", autouse=True)
def temp_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


def test_filesystem_store_store_and_retrieve(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir))
    hash_value = b"hash1"
    item = b"item1"

    store.store_item(hash_value, item)
    assert store.stores(hash_value)
    retrieved_item = store.retrieve(hash_value)
    assert retrieved_item == item

    # second item
    hash_value2 = b"hash2"
    item2 = b"item2"
    store.store_item(hash_value2, item2)
    assert store.stores(hash_value2)
    retrieved_item2 = store.retrieve(hash_value2)
    assert retrieved_item2 == item2

    # delete first item
    store.delete(hash_value)
    assert not store.stores(hash_value)
    assert store.stores(hash_value2)

    # clear store
    store.clear()
    assert not store.stores(hash_value)
    assert not store.stores(hash_value2)

    # destroy store (should be no-op for DictStore)
    store.destroy()
    assert not store.stores(hash_value)


def test_filesystem_store_factory(temp_dir) -> None:
    store = factory({"repo_dir": temp_dir})
    assert isinstance(store, FileSystemStore)


def test_filesystem_store_no_metadata_without_hasher_name(temp_dir) -> None:
    FileSystemStore(pathlib.Path(temp_dir))
    metadata_path = pathlib.Path(temp_dir) / FileSystemStore.METADATA_FILENAME
    assert not metadata_path.exists()


def test_filesystem_store_writes_metadata_with_hasher_name(temp_dir) -> None:
    FileSystemStore(pathlib.Path(temp_dir), hasher_name="sha256")
    metadata_path = pathlib.Path(temp_dir) / FileSystemStore.METADATA_FILENAME
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text())
    assert metadata["hasher"] == "sha256"
    assert metadata["schema_version"] == 1


def test_filesystem_store_clear_preserves_metadata(temp_dir) -> None:
    store = FileSystemStore(pathlib.Path(temp_dir), hasher_name="sha256")
    store.store_item(b"hash1", b"item1")
    store.clear()
    metadata_path = pathlib.Path(temp_dir) / FileSystemStore.METADATA_FILENAME
    assert metadata_path.exists()
    assert not store.stores(b"hash1")


def test_filesystem_store_factory_writes_metadata(temp_dir) -> None:
    store = factory({"repo_dir": temp_dir, "hasher_name": "md5"})
    assert isinstance(store, FileSystemStore)
    metadata_path = pathlib.Path(temp_dir) / FileSystemStore.METADATA_FILENAME
    assert metadata_path.exists()
    metadata = json.loads(metadata_path.read_text())
    assert metadata["hasher"] == "md5"


def test_filesystem_store_metadata_cleanup_on_write_failure(
    temp_dir, monkeypatch
) -> None:
    import json as json_module

    original_dump = json_module.dump

    def failing_dump(*_args, **_kwargs):
        raise OSError("simulated disk full")

    monkeypatch.setattr(json_module, "dump", failing_dump)

    with pytest.raises(OSError, match="simulated disk full"):
        FileSystemStore(pathlib.Path(temp_dir), hasher_name="sha256")

    metadata_path = pathlib.Path(temp_dir) / FileSystemStore.METADATA_FILENAME
    tmp_path = metadata_path.with_name(metadata_path.name + ".tmp")
    assert not metadata_path.exists()
    assert not tmp_path.exists()

    monkeypatch.setattr(json_module, "dump", original_dump)
    FileSystemStore(pathlib.Path(temp_dir), hasher_name="sha256")
    assert metadata_path.exists()
    assert json.loads(metadata_path.read_text())["hasher"] == "sha256"
