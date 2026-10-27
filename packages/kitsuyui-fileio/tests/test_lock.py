from __future__ import annotations

import errno
import multiprocessing
import multiprocessing.synchronize
import os
import threading
import time
from collections.abc import Callable
from contextlib import AbstractContextManager
from pathlib import Path
from typing import Any, cast

import pytest

from kitsuyui.fileio import (
    AdvisoryLockTimeoutError,
    AdvisoryLockUnsupportedError,
    LockMode,
    _lock,
    advisory_lock,
)

requires_posix = pytest.mark.skipif(
    os.name != "posix", reason="fcntl.flock is POSIX-only"
)


@requires_posix
def test_lock_file_remains_after_release_and_can_be_reused(
    tmp_path: Path,
) -> None:
    path = tmp_path / "writer.lock"
    with advisory_lock(path):
        assert path.exists()
    assert path.exists()
    with advisory_lock(path, timeout=0):
        pass


@requires_posix
def test_timeout_zero_is_nonblocking_between_threads(tmp_path: Path) -> None:
    path = tmp_path / "writer.lock"
    acquired = threading.Event()
    release = threading.Event()

    def hold_lock() -> None:
        with advisory_lock(path):
            acquired.set()
            release.wait()

    holder = threading.Thread(target=hold_lock)
    holder.start()
    assert acquired.wait(timeout=2)
    try:
        with (
            pytest.raises(AdvisoryLockTimeoutError) as error,
            advisory_lock(path, timeout=0),
        ):
            pass
        assert error.value.path == path.resolve()
        assert error.value.timeout == 0
    finally:
        release.set()
        holder.join(timeout=2)
    assert not holder.is_alive()


@requires_posix
def test_timeout_starts_when_context_enters(tmp_path: Path) -> None:
    lock = advisory_lock(tmp_path / "writer.lock", timeout=0.01)
    time.sleep(0.02)
    with lock:
        pass


def _hold_lock(
    path: str,
    mode: LockMode,
    acquired: multiprocessing.synchronize.Event,
    release: multiprocessing.synchronize.Event,
) -> None:
    with advisory_lock(path, mode=mode):
        acquired.set()
        release.wait(timeout=5)


def _start_holder(
    path: Path, mode: LockMode
) -> tuple[Any, multiprocessing.synchronize.Event]:
    context = multiprocessing.get_context("spawn")
    acquired = context.Event()
    release = context.Event()
    process = context.Process(
        target=_hold_lock, args=(os.fspath(path), mode, acquired, release)
    )
    process.start()
    assert acquired.wait(timeout=5)
    return process, release


def _stop_holder(
    process: Any,
    release: multiprocessing.synchronize.Event,
) -> None:
    release.set()
    process.join(timeout=5)
    assert process.exitcode == 0


@pytest.mark.skipif(os.name != "posix", reason="fcntl.flock is POSIX-only")
@pytest.mark.parametrize(
    ("held_mode", "requested_mode", "times_out"),
    [
        ("exclusive", "exclusive", True),
        ("exclusive", "shared", True),
        ("shared", "exclusive", True),
        ("shared", "shared", False),
    ],
)
def test_lock_modes_coordinate_between_processes(
    tmp_path: Path,
    held_mode: LockMode,
    requested_mode: LockMode,
    times_out: bool,
) -> None:
    path = tmp_path / "writer.lock"
    process, release = _start_holder(path, held_mode)
    try:
        if times_out:
            with (
                pytest.raises(AdvisoryLockTimeoutError),
                advisory_lock(path, mode=requested_mode, timeout=0),
            ):
                pass
        else:
            with advisory_lock(path, mode=requested_mode, timeout=0):
                pass
    finally:
        _stop_holder(process, release)


@requires_posix
def test_positive_timeout_retries_until_another_process_releases(
    tmp_path: Path,
) -> None:
    path = tmp_path / "writer.lock"
    process, release = _start_holder(path, "exclusive")
    timer = threading.Timer(0.05, release.set)
    timer.start()
    try:
        started = time.monotonic()
        with advisory_lock(path, timeout=1, poll_interval=0.01):
            pass
        assert time.monotonic() - started >= 0.04
    finally:
        timer.cancel()
        _stop_holder(process, release)


@pytest.mark.skipif(os.name != "posix", reason="fcntl.flock is POSIX-only")
def test_body_exception_releases_lock_for_another_process(
    tmp_path: Path,
) -> None:
    path = tmp_path / "writer.lock"
    with pytest.raises(RuntimeError, match="body"), advisory_lock(path):
        raise RuntimeError("body")
    process, release = _start_holder(path, "exclusive")
    _stop_holder(process, release)


@requires_posix
def test_body_exception_survives_cleanup_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "writer.lock"
    real_release = _lock._release_file_lock

    def close_then_fail(fd: int) -> None:
        real_release(fd)
        raise OSError("cleanup failed")

    monkeypatch.setattr(_lock, "_release_file_lock", close_then_fail)
    with pytest.raises(RuntimeError, match="body"), advisory_lock(path):
        raise RuntimeError("body")
    monkeypatch.setattr(_lock, "_release_file_lock", real_release)
    with advisory_lock(path, timeout=0):
        pass


@requires_posix
def test_cleanup_error_is_reported_without_body_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "writer.lock"
    real_release = _lock._release_file_lock

    def close_then_fail(fd: int) -> None:
        real_release(fd)
        raise OSError("cleanup failed")

    monkeypatch.setattr(_lock, "_release_file_lock", close_then_fail)
    with pytest.raises(OSError, match="cleanup failed"), advisory_lock(path):
        pass


def test_unsupported_platform_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(_lock, "_flock", None)
    with (
        pytest.raises(AdvisoryLockUnsupportedError),
        advisory_lock(tmp_path / "writer.lock"),
    ):
        pass


@pytest.mark.parametrize("busy_errno", [errno.EACCES, errno.EAGAIN])
@requires_posix
def test_busy_os_errors_become_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, busy_errno: int
) -> None:
    def busy(_fd: int, _operation: int) -> None:
        raise OSError(busy_errno, "busy")

    monkeypatch.setattr(_lock, "_flock", busy)
    with (
        pytest.raises(AdvisoryLockTimeoutError),
        advisory_lock(tmp_path / "writer.lock", timeout=0),
    ):
        pass


@requires_posix
def test_non_contention_os_error_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_with_permission_error(_fd: int, _operation: int) -> None:
        raise OSError(errno.EPERM, "not permitted")

    monkeypatch.setattr(_lock, "_flock", fail_with_permission_error)
    with (
        pytest.raises(PermissionError, match="not permitted"),
        advisory_lock(tmp_path / "writer.lock"),
    ):
        pass


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda path: advisory_lock(path, mode=cast(LockMode, "other")),
            "lock mode",
        ),
        (lambda path: advisory_lock(path, timeout=-1), "timeout"),
        (lambda path: advisory_lock(path, timeout=float("inf")), "timeout"),
        (lambda path: advisory_lock(path, poll_interval=0), "poll_interval"),
        (lambda path: advisory_lock(path, permissions=0o1000), "permissions"),
    ],
)
def test_invalid_options_do_not_create_lock_file(
    tmp_path: Path,
    factory: Callable[[Path], AbstractContextManager[None]],
    message: str,
) -> None:
    path = tmp_path / "writer.lock"
    with pytest.raises(ValueError, match=message), factory(path):
        pass
    assert not path.exists()


@requires_posix
def test_invalid_lock_path_does_not_create_file(tmp_path: Path) -> None:
    with pytest.raises(IsADirectoryError), advisory_lock(tmp_path):
        pass
    assert list(tmp_path.iterdir()) == []
