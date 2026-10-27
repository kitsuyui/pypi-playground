"""POSIX advisory locking for explicitly chosen lock files."""

from __future__ import annotations

import contextlib
import errno
import math
import os
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

_Flock = Callable[[int, int], None]
_flock: _Flock | None

try:
    from fcntl import LOCK_EX as _LOCK_EX
    from fcntl import LOCK_NB as _LOCK_NB
    from fcntl import LOCK_SH as _LOCK_SH
    from fcntl import LOCK_UN as _LOCK_UN
    from fcntl import flock as _native_flock
except ImportError:
    _flock = None
else:
    _flock = _native_flock

LockMode = Literal["exclusive", "shared"]
_DEFAULT_POLL_INTERVAL = 0.05
_BUSY_ERRNOS = {errno.EACCES, errno.EAGAIN}


class AdvisoryLockError(Exception):
    """Base class for errors raised by :func:`advisory_lock`."""


class AdvisoryLockUnsupportedError(AdvisoryLockError, RuntimeError):
    """Raised when this platform has no supported advisory lock primitive."""


class AdvisoryLockTimeoutError(AdvisoryLockError, TimeoutError):
    """Raised when a lock remains held until its acquisition deadline."""

    def __init__(self, path: Path, timeout: float) -> None:
        self.path = path
        self.timeout = timeout
        super().__init__(f"timed out acquiring advisory lock: {path}")


@dataclass
class _ThreadGate:
    condition: threading.Condition = field(default_factory=threading.Condition)
    readers: int = 0
    writer: bool = False
    waiting_writers: int = 0
    users: int = 0


class _ThreadGates:
    """Make POSIX lock modes consistent between threads in one process."""

    def __init__(self) -> None:
        self._gates: dict[Path, _ThreadGate] = {}
        self._registry_lock = threading.Lock()

    def acquire(
        self,
        path: Path,
        mode: LockMode,
        deadline: float | None,
        timeout: float | None,
    ) -> _ThreadGate:
        gate = self._claim(path)
        if self._acquire_gate(gate, mode, deadline):
            return gate
        self._release_claim(path, gate)
        raise AdvisoryLockTimeoutError(path, timeout or 0)

    def release(self, path: Path, mode: LockMode, gate: _ThreadGate) -> None:
        try:
            with gate.condition:
                if mode == "shared":
                    gate.readers -= 1
                else:
                    gate.writer = False
                gate.condition.notify_all()
        finally:
            self._release_claim(path, gate)

    def _claim(self, path: Path) -> _ThreadGate:
        with self._registry_lock:
            gate = self._gates.setdefault(path, _ThreadGate())
            gate.users += 1
            return gate

    def _release_claim(self, path: Path, gate: _ThreadGate) -> None:
        with self._registry_lock:
            gate.users -= 1
            if gate.users == 0:
                del self._gates[path]

    @staticmethod
    def _acquire_gate(
        gate: _ThreadGate, mode: LockMode, deadline: float | None
    ) -> bool:
        if mode == "exclusive":
            return _acquire_exclusive_gate(gate, deadline)
        return _acquire_shared_gate(gate, deadline)


_thread_gates = _ThreadGates()


def _wait_for_gate(
    condition: threading.Condition, deadline: float | None
) -> bool:
    if deadline is None:
        condition.wait()
        return True
    remaining = _remaining_timeout(deadline)
    if remaining == 0:
        return False
    condition.wait(timeout=remaining)
    return _remaining_timeout(deadline) != 0


def _acquire_exclusive_gate(gate: _ThreadGate, deadline: float | None) -> bool:
    with gate.condition:
        gate.waiting_writers += 1
        try:
            while gate.writer or gate.readers:
                if not _wait_for_gate(gate.condition, deadline):
                    return False
            gate.writer = True
            return True
        finally:
            gate.waiting_writers -= 1
            gate.condition.notify_all()


def _acquire_shared_gate(gate: _ThreadGate, deadline: float | None) -> bool:
    with gate.condition:
        while gate.writer or gate.waiting_writers:
            if not _wait_for_gate(gate.condition, deadline):
                return False
        gate.readers += 1
        return True


def _validate_options(
    mode: LockMode,
    timeout: float | None,
    poll_interval: float,
    permissions: int,
) -> None:
    _validate_mode(mode)
    _validate_timeout(timeout)
    _validate_poll_interval(poll_interval)
    _validate_permissions(permissions)


def _validate_mode(mode: LockMode) -> None:
    if mode not in ("exclusive", "shared"):
        raise ValueError(f"invalid lock mode: {mode!r}")


def _validate_timeout(timeout: float | None) -> None:
    if timeout is not None and (not math.isfinite(timeout) or timeout < 0):
        raise ValueError(
            "timeout must be a finite non-negative number or None"
        )


def _validate_poll_interval(poll_interval: float) -> None:
    if not math.isfinite(poll_interval) or poll_interval <= 0:
        raise ValueError("poll_interval must be a finite positive number")


def _validate_permissions(permissions: int) -> None:
    if not 0 <= permissions <= 0o777:
        raise ValueError("permissions must be between 0 and 0o777")


def _lock_path(path: str | os.PathLike[str]) -> Path:
    given_path = Path(path)
    if given_path.name in ("", ".", ".."):
        raise ValueError("path must name a lock file")
    return given_path.parent.resolve() / given_path.name


def _deadline(timeout: float | None) -> float | None:
    if timeout is None:
        return None
    return time.monotonic() + timeout


def _remaining_timeout(deadline: float | None) -> float:
    if deadline is None:
        return 0
    return max(0.0, deadline - time.monotonic())


def _require_flock() -> _Flock:
    if _flock is None:
        raise AdvisoryLockUnsupportedError(
            "advisory_lock requires POSIX fcntl.flock support"
        )
    return _flock


def _open_lock_file(path: Path, permissions: int) -> int:
    return os.open(path, os.O_RDWR | os.O_CREAT, permissions)


def _operation_for(mode: LockMode) -> int:
    return _LOCK_EX if mode == "exclusive" else _LOCK_SH


def _acquire_file_lock(
    fd: int,
    path: Path,
    mode: LockMode,
    timeout: float | None,
    poll_interval: float,
    deadline: float | None,
) -> None:
    operation = _operation_for(mode) | _LOCK_NB
    while not _try_file_lock(fd, operation):
        _wait_for_file_lock(path, timeout, poll_interval, deadline)


def _try_file_lock(fd: int, operation: int) -> bool:
    try:
        _require_flock()(fd, operation)
    except OSError as exc:
        if exc.errno not in _BUSY_ERRNOS:
            raise
        return False
    return True


def _wait_for_file_lock(
    path: Path,
    timeout: float | None,
    poll_interval: float,
    deadline: float | None,
) -> None:
    remaining = _remaining_timeout(deadline)
    if timeout == 0 or remaining == 0:
        raise AdvisoryLockTimeoutError(path, timeout or 0)
    time.sleep(min(poll_interval, remaining))


def _release_file_lock(fd: int) -> None:
    flock = _require_flock()
    try:
        flock(fd, _LOCK_UN)
    finally:
        os.close(fd)


def advisory_lock(
    path: str | os.PathLike[str],
    *,
    mode: LockMode = "exclusive",
    timeout: float | None = None,
    poll_interval: float = _DEFAULT_POLL_INTERVAL,
    permissions: int = 0o600,
) -> _AdvisoryLock:
    """Hold a POSIX advisory lock on the explicit lock-file ``path``.

    The parent directory must already exist. The lock file is retained after
    release so that later acquisitions continue to lock the same inode.
    """
    _validate_options(mode, timeout, poll_interval, permissions)
    return _AdvisoryLock(
        _lock_path(path), mode, timeout, poll_interval, permissions
    )


class _AdvisoryLock:
    def __init__(
        self,
        path: Path,
        mode: LockMode,
        timeout: float | None,
        poll_interval: float,
        permissions: int,
    ) -> None:
        self._path = path
        self._mode = mode
        self._timeout = timeout
        self._poll_interval = poll_interval
        self._permissions = permissions
        self._deadline: float | None = None
        self._gate: _ThreadGate | None = None
        self._fd: int | None = None

    def __enter__(self) -> None:
        _require_flock()
        self._deadline = _deadline(self._timeout)
        self._gate = _thread_gates.acquire(
            self._path, self._mode, self._deadline, self._timeout
        )
        try:
            self._fd = _open_lock_file(self._path, self._permissions)
            _acquire_file_lock(
                self._fd,
                self._path,
                self._mode,
                self._timeout,
                self._poll_interval,
                self._deadline,
            )
        except BaseException:
            self._release_after_failed_enter()
            raise

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: object,
    ) -> Literal[False]:
        try:
            if exception is None:
                self._release()
            else:
                self._release_suppressing_errors()
        finally:
            self._release_gate()
        return False

    def _release_after_failed_enter(self) -> None:
        self._release_suppressing_errors()
        self._release_gate()

    def _release_suppressing_errors(self) -> None:
        with contextlib.suppress(BaseException):
            self._release()

    def _release(self) -> None:
        if self._fd is not None:
            _release_file_lock(self._fd)
            self._fd = None

    def _release_gate(self) -> None:
        if self._gate is not None:
            _thread_gates.release(self._path, self._mode, self._gate)
            self._gate = None
