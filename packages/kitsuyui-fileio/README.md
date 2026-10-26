# kitsuyui.fileio

Small, explicit file I/O primitives. The first release provides atomic
replacement of a single file without runtime dependencies (Python 3.10+).

```python
from kitsuyui.fileio import atomic_write, atomic_write_bytes, atomic_write_text

atomic_write_text("settings.txt", "ready\n")
atomic_write_bytes("data.bin", b"\x00\x01")
with atomic_write("large.bin") as output:
    output.write(b"first chunk")
    output.write(b"second chunk")
```

`atomic_write` yields a binary stream. On normal exit it flushes and closes the
stream before replacing the destination. An exception inside the block leaves
the destination untouched and removes the temporary file when possible. Do not
close the yielded stream manually. The convenience functions accept paths and
bytes or text respectively; text is encoded as UTF-8 unless specified otherwise.
The parent directory must already exist. A caller that wraps the binary stream
in a `TextIOWrapper` must flush and detach the wrapper before leaving the block;
closing the supplied stream causes a `ValueError` and cancels replacement.
Text convenience writes use `str.encode` and do not translate newlines; callers
may choose the encoding and encoding error handler.

## Guarantees and boundaries

The temporary file is created in the destination directory and installed with
`os.replace`. On a filesystem supporting POSIX atomic rename, a reader opening
the destination sees either the previous file or the complete new file during
normal execution; an
already-open descriptor may continue to refer to the old file. On other systems
and filesystems, replacement guarantees depend on the platform. This does not
lock writers, prevent lost updates, make multiple replacements transactional, or
secure a directory controlled by an untrusted party. Concurrent successful
writers are last-replacement-wins. A destination symlink itself is replaced;
its target is not modified. The temporary file is created with restrictive
permissions (0600 on POSIX). Existing ownership, permissions, timestamps, ACLs,
extended attributes and hard links are not preserved. The restrictive default
avoids silently exposing content from a private file or temporary write. To
choose another POSIX permission mode, pass `permissions=0o644` (for example);
the specified bits are applied to the temporary file before replacement and
are not filtered by umask. Do not use permissive modes for sensitive data. On
Windows `os.chmod` has limited permission semantics. Copying existing permissions
is deliberately left to the caller because metadata and access policy are
platform-specific and can change concurrently.

The keyword `durability` distinguishes visibility from persistence:

* `"none"`: flush and close before replacement; no `fsync`.
* `"file"` (default): also `fsync` the staged file before replacement.
* `"file_and_directory"`: also `fsync` the parent directory after replacement.
  This option is available only on POSIX and can still fail on a filesystem
  that does not support directory sync.

Sync calls request persistence from the operating system; they cannot guarantee
the behavior of every filesystem, storage device, or hardware buffer. A failure
before `os.replace` leaves an existing destination unchanged. If directory
sync fails after replacement, `DurabilityError` is raised: the new destination
is already visible, but its persistence is uncertain. If replacement itself fails,
the operating system error is propagated. Abrupt process termination can leave a
temporary file behind; ordinary exception cleanup is best effort. A crash with
`"none"` can leave the new file empty or truncated even after the rename, so
the runtime visibility guarantee is not a crash-recovery guarantee. On macOS,
`os.fsync` does not request the stronger `F_FULLFSYNC` operation, so even a
successful sync does not guarantee that hardware buffers reached durable media.

## License

BSD 3-Clause License. See the repository's LICENSE.
