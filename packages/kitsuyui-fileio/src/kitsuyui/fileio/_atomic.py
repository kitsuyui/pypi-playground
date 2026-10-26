"""Atomically replace a single file with staged bytes."""

from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Literal

Durability = Literal["none", "file", "file_and_directory"]


class DurabilityError(OSError):
    """The replacement happened, but the directory could not be synced."""


def _validate_options(durability: Durability) -> None:
    if durability not in ("none", "file", "file_and_directory"):
        raise ValueError(f"invalid durability: {durability!r}")
    if durability == "file_and_directory" and os.name != "posix":
        raise NotImplementedError("directory sync is only supported on POSIX")


def _validate_permissions(permissions: int | None) -> None:
    if permissions is not None and not 0 <= permissions <= 0o777:
        raise ValueError("permissions must be between 0 and 0o777")


def _destination(path: str | os.PathLike[str]) -> Path:
    given_path = Path(path)
    if given_path.name in ("", ".", ".."):
        raise ValueError("path must name a file")
    # Resolve the parent only: the destination symlink must be replaced.
    return given_path.parent.resolve() / given_path.name


@contextlib.contextmanager
def _directory_handle(
    destination: Path, durability: Durability
) -> Generator[int | None, None, None]:
    fd = None
    try:
        if durability == "file_and_directory":
            fd = os.open(
                destination.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
        yield fd
    finally:
        if fd is not None:
            with contextlib.suppress(OSError):
                os.close(fd)


@dataclass
class _StagedPath:
    path: Path
    owned: bool = True

    def replace(self, destination: Path) -> None:
        self.path.replace(destination)
        self.owned = False

    def cleanup(self) -> None:
        if self.owned:
            with contextlib.suppress(OSError):
                self.path.unlink()


@contextlib.contextmanager
def _staged_file(
    destination: Path,
) -> Generator[tuple[_StagedPath, BinaryIO], None, None]:
    fd, name = tempfile.mkstemp(
        prefix=".fileio-", suffix=".tmp", dir=destination.parent
    )
    temporary = _StagedPath(Path(name))
    try:
        with _owned_stream(fd) as stream:
            yield temporary, stream
    finally:
        temporary.cleanup()


@contextlib.contextmanager
def _owned_stream(fd: int) -> Generator[BinaryIO, None, None]:
    stream = _open_stream(fd)
    try:
        yield stream
    except BaseException:
        with contextlib.suppress(BaseException):
            stream.close()
        raise
    else:
        _close_stream(stream)


def _close_stream(stream: BinaryIO) -> None:
    if not stream.closed:
        stream.close()


def _open_stream(fd: int) -> BinaryIO:
    try:
        return os.fdopen(fd, "wb")
    except BaseException:
        with contextlib.suppress(OSError):
            os.close(fd)
        raise


def _prepare_stream(
    stream: BinaryIO,
    temporary: Path,
    durability: Durability,
    permissions: int | None,
) -> None:
    _flush_stream(stream)
    if permissions is not None:
        _set_permissions(stream, temporary, permissions)
    if durability != "none":
        os.fsync(stream.fileno())


def _flush_stream(stream: BinaryIO) -> None:
    if stream.closed:
        raise ValueError("the atomic_write stream was closed by the caller")
    stream.flush()


def _set_permissions(
    stream: BinaryIO, temporary: Path, permissions: int
) -> None:
    if hasattr(os, "fchmod"):
        os.fchmod(stream.fileno(), permissions)
    else:
        temporary.chmod(permissions)


def _commit(
    temporary: _StagedPath, destination: Path, directory_fd: int | None
) -> None:
    temporary.replace(destination)
    if directory_fd is not None:
        try:
            os.fsync(directory_fd)
        except OSError as exc:
            raise DurabilityError(
                f"file was replaced, but directory sync failed: {destination}"
            ) from exc


@contextlib.contextmanager
def atomic_write(
    path: str | os.PathLike[str],
    *,
    durability: Durability = "file",
    permissions: int | None = None,
) -> Generator[BinaryIO, None, None]:
    """Yield a binary stream and replace the destination on successful exit.

    The destination directory must exist. Temporary files are private (0600 on
    POSIX); replacement does not preserve the original file's metadata.
    """
    _validate_options(durability)
    _validate_permissions(permissions)
    destination = _destination(path)
    with (
        _directory_handle(destination, durability) as directory_fd,
        _staged_file(destination) as (temporary, stream),
    ):
        yield stream
        _prepare_stream(stream, temporary.path, durability, permissions)
        stream.close()
        _commit(temporary, destination, directory_fd)


def atomic_write_bytes(
    path: str | os.PathLike[str],
    data: bytes,
    *,
    durability: Durability = "file",
    permissions: int | None = None,
) -> None:
    """Replace a file with bytes after the entire write succeeds."""
    with atomic_write(
        path, durability=durability, permissions=permissions
    ) as stream:
        stream.write(data)


def atomic_write_text(
    path: str | os.PathLike[str],
    text: str,
    *,
    encoding: str = "utf-8",
    errors: str = "strict",
    durability: Durability = "file",
    permissions: int | None = None,
) -> None:
    """Encode text and replace a file after the entire write succeeds."""
    atomic_write_bytes(
        path,
        text.encode(encoding, errors),
        durability=durability,
        permissions=permissions,
    )
