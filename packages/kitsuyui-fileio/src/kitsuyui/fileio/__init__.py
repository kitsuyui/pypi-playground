"""File I/O primitives with explicit replacement and durability semantics."""

from ._atomic import (
    Durability,
    DurabilityError,
    atomic_write,
    atomic_write_bytes,
    atomic_write_text,
)
from ._lock import (
    AdvisoryLockError,
    AdvisoryLockTimeoutError,
    AdvisoryLockUnsupportedError,
    LockMode,
    advisory_lock,
)

__all__ = [
    "AdvisoryLockError",
    "AdvisoryLockTimeoutError",
    "AdvisoryLockUnsupportedError",
    "Durability",
    "DurabilityError",
    "LockMode",
    "advisory_lock",
    "atomic_write",
    "atomic_write_bytes",
    "atomic_write_text",
]
