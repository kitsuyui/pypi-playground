"""Atomically replace a single file with staged bytes."""

from __future__ import annotations

import contextlib
import os
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import BinaryIO, Literal

Durability = Literal["none", "file", "file_and_directory"]


class DurabilityError(OSError):
    """The replacement happened, but the directory could not be synced."""


@contextlib.contextmanager
def atomic_write(  # noqa: C901
    path: str | os.PathLike[str],
    *,
    durability: Durability = "file",
    permissions: int | None = None,
) -> Generator[BinaryIO, None, None]:
    """Yield a binary stream and replace the destination on successful exit.

    The destination directory must exist. Temporary files are private (0600 on
    POSIX); replacement does not preserve the original file's metadata.
    """
    if durability not in ("none", "file", "file_and_directory"):
        raise ValueError(f"invalid durability: {durability!r}")
    if durability == "file_and_directory" and os.name != "posix":
        raise NotImplementedError("directory sync is only supported on POSIX")
    if permissions is not None and not 0 <= permissions <= 0o777:
        raise ValueError("permissions must be between 0 and 0o777")

    given_path = Path(path)
    if given_path.name in ("", ".", ".."):
        raise ValueError("path must name a file")
    # Resolve the parent only: the destination symlink must be replaced.
    destination = given_path.parent.resolve() / given_path.name
    directory_fd: int | None = None
    temp_path: Path | None = None
    fd: int | None = None
    replaced = False
    try:
        if durability == "file_and_directory":
            directory_fd = os.open(
                destination.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            )
        fd, temp_name = tempfile.mkstemp(
            prefix=".fileio-",
            suffix=".tmp",
            dir=destination.parent,
        )
        temp_path = Path(temp_name)
        stream = os.fdopen(fd, "wb")
        fd = None
        try:
            yield stream
            if stream.closed:
                raise ValueError(
                    "the atomic_write stream was closed by the caller"
                )
            stream.flush()
            if permissions is not None:
                if hasattr(os, "fchmod"):
                    os.fchmod(stream.fileno(), permissions)
                else:
                    temp_path.chmod(permissions)
            if durability != "none":
                os.fsync(stream.fileno())
        except BaseException:
            with contextlib.suppress(BaseException):
                stream.close()
            raise
        else:
            stream.close()
        os.replace(temp_path, destination)  # noqa: PTH105
        replaced = True
        if directory_fd is not None:
            try:
                os.fsync(directory_fd)
            except OSError as exc:
                raise DurabilityError(
                    "file was replaced, but directory sync failed: "
                    f"{destination}"
                ) from exc
    finally:
        if fd is not None:
            with contextlib.suppress(OSError):
                os.close(fd)
        if temp_path is not None and not replaced:
            with contextlib.suppress(OSError):
                temp_path.unlink()
        if directory_fd is not None:
            with contextlib.suppress(OSError):
                os.close(directory_fd)


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
