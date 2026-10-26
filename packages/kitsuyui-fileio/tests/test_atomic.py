from __future__ import annotations

import os
import threading
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import pytest

from kitsuyui.fileio import (
    DurabilityError,
    atomic_write,
    atomic_write_bytes,
    atomic_write_text,
)


def test_text_and_bytes_replace_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "data"
    path.write_bytes(b"old")
    atomic_write_text(path, "caf\u00e9", encoding="utf-8")
    assert path.read_bytes() == "caf\u00e9".encode()
    atomic_write_bytes(path, b"new")
    assert path.read_bytes() == b"new"
    assert list(tmp_path.iterdir()) == [path]


def test_context_error_preserves_original_and_removes_temporary(
    tmp_path: Path,
) -> None:
    path = tmp_path / "data"
    path.write_bytes(b"old")
    with pytest.raises(ValueError, match="stop"), atomic_write(path) as stream:
        stream.write(b"partial")
        raise ValueError("stop")
    assert path.read_bytes() == b"old"
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.parametrize("operation", ["replace", "fsync"])
def test_precommit_failure_keeps_original(
    tmp_path: Path, operation: str
) -> None:
    path = tmp_path / "data"
    path.write_bytes(b"old")
    with (
        patch.object(os, operation, side_effect=OSError("injected")),
        pytest.raises(OSError, match="injected"),
    ):
        atomic_write_bytes(path, b"new")
    assert path.read_bytes() == b"old"
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.skipif(os.name != "posix", reason="directory fsync is POSIX-only")
def test_directory_sync_failure_reports_visible_replacement(
    tmp_path: Path,
) -> None:
    path = tmp_path / "data"
    path.write_bytes(b"old")
    original_fsync = os.fsync
    calls = 0

    def fail_second(fd: int) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("directory sync failed")
        original_fsync(fd)

    with (
        patch.object(os, "fsync", side_effect=fail_second),
        pytest.raises(DurabilityError),
    ):
        atomic_write_bytes(path, b"new", durability="file_and_directory")
    assert path.read_bytes() == b"new"
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.skipif(
    os.name == "nt", reason="Windows may deny replacement of an open file"
)
def test_reader_sees_only_complete_versions(tmp_path: Path) -> None:  # noqa: C901
    path = tmp_path / "data"
    versions = (b"a" * 32768, b"b" * 32768)
    path.write_bytes(versions[0])
    observed: list[bytes] = []
    done = threading.Event()

    def reader() -> None:
        while not done.is_set():
            observed.append(path.read_bytes())

    thread = threading.Thread(target=reader)
    thread.start()
    try:
        for index in range(30):
            atomic_write_bytes(path, versions[index % 2], durability="none")
    finally:
        done.set()
        thread.join()
    assert observed
    assert all(value in versions for value in observed)


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission semantics")
def test_permissions_and_symlink_replacement(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.write_bytes(b"unchanged")
    path = tmp_path / "link"
    path.symlink_to(target)
    atomic_write_bytes(path, b"new")
    assert not path.is_symlink()
    assert target.read_bytes() == b"unchanged"
    assert path.stat().st_mode & 0o777 == 0o600


def test_invalid_durability_does_not_create_files(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        atomic_write_bytes(
            tmp_path / "data", b"new", durability=cast(Any, "unknown")
        )
    assert list(tmp_path.iterdir()) == []


def test_body_exception_survives_close_failure(tmp_path: Path) -> None:
    path = tmp_path / "data"
    path.write_bytes(b"old")
    with (
        pytest.raises(RuntimeError, match="body"),
        atomic_write(path) as stream,
    ):
        real_close = stream.close

        def fail_close() -> None:
            real_close()
            raise OSError("close")

        setattr(stream, "close", fail_close)  # noqa: B010
        raise RuntimeError("body")
    assert path.read_bytes() == b"old"


def test_caller_close_has_clear_error_and_preserves_old(
    tmp_path: Path,
) -> None:
    path = tmp_path / "data"
    path.write_bytes(b"old")
    with (
        pytest.raises(ValueError, match="closed by the caller"),
        atomic_write(path) as stream,
    ):
        stream.write(b"new")
        stream.close()
    assert path.read_bytes() == b"old"
    assert list(tmp_path.iterdir()) == [path]


@pytest.mark.skipif(os.name != "posix", reason="POSIX permission semantics")
def test_explicit_permissions(tmp_path: Path) -> None:
    path = tmp_path / "data"
    atomic_write_text(path, "hi", permissions=0o640)
    assert path.stat().st_mode & 0o777 == 0o640


@pytest.mark.skipif(os.name != "posix", reason="symlink availability")
def test_parent_symlink_dotdot_resolves_like_os(tmp_path: Path) -> None:
    nested = tmp_path / "other" / "nested"
    nested.mkdir(parents=True)
    (tmp_path / "link").symlink_to(nested, target_is_directory=True)
    atomic_write_bytes(tmp_path / "link" / ".." / "data", b"yes")
    assert (tmp_path / "other" / "data").read_bytes() == b"yes"
    assert not (tmp_path / "data").exists()


def test_long_destination_and_encoding_errors(tmp_path: Path) -> None:
    path = tmp_path / ("x" * 240)
    atomic_write_text(path, "caf\u00e9", encoding="ascii", errors="replace")
    assert path.read_bytes() == b"caf?"


def test_invalid_permissions_does_not_create_file(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="permissions"):
        atomic_write_bytes(tmp_path / "data", b"new", permissions=0o1000)
    assert list(tmp_path.iterdir()) == []
