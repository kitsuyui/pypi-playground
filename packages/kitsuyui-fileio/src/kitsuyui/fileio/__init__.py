"""File I/O primitives with explicit replacement and durability semantics."""

from ._atomic import (
    Durability,
    DurabilityError,
    atomic_write,
    atomic_write_bytes,
    atomic_write_text,
)

__all__ = [
    "Durability",
    "DurabilityError",
    "atomic_write",
    "atomic_write_bytes",
    "atomic_write_text",
]
