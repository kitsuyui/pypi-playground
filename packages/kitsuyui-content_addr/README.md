# kitsuyui.content_addr

## What is this?

`kitsuyui.content_addr` is a small content-addressable storage package.
It stores bytes by a hash of their content, then lets callers retrieve,
verify, and delete those bytes by hash value.

The package separates hashing from storage:

- hashers compute stable content identifiers, such as SHA-256 or MD5
- stores persist bytes behind those identifiers, such as in memory or on disk
- `HashStore` combines a hasher and a store into a simple API

## Install

```bash
pip install kitsuyui.content_addr
```

## Basic usage

```python
from kitsuyui.content_addr.hash_store import HashStore
from kitsuyui.content_addr.hash_store.dict_store import DictStore
from kitsuyui.content_addr.hasher import SHA256Hasher

store = HashStore(hasher=SHA256Hasher(), base_store=DictStore())

item = b"example item"
hash_value = store.store(item)

assert store.stores(hash_value)
assert store.retrieve(hash_value) == item
assert store.verify(hash_value)
```

Use `DictStore` for in-memory storage in tests or examples. Use
`FileSystemStore` when stored bytes should live in a directory on disk.

# LICENSE

BSD 3-Clause License
