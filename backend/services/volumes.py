"""Wraps Databricks Files API for Volume operations.

See ADR 0010 and design-specs/architecture/07-sequence-file-upload.md.

The streaming wrapper computes sha256 in flight so the digest is available
immediately after files.upload() returns.
"""

import asyncio
import hashlib
from dataclasses import dataclass
from typing import BinaryIO


@dataclass(frozen=True)
class UploadOutcome:
    sha256: str
    bytes_written: int


class Sha256StreamWrapper:
    """Read-through wrapper around a BinaryIO stream that updates a sha256 digest."""

    def __init__(self, inner: BinaryIO) -> None:
        self._inner = inner
        self._h = hashlib.sha256()
        self._n = 0

    def read(self, size: int = -1) -> bytes:
        chunk = self._inner.read(size)
        if chunk:
            self._h.update(chunk)
            self._n += len(chunk)
        return chunk

    @property
    def hexdigest(self) -> str:
        return self._h.hexdigest()

    @property
    def bytes_read(self) -> int:
        return self._n


async def upload_to_volume(
    *,
    volume_path: str,
    stream: BinaryIO,
    overwrite: bool = False,
    part_size: int = 8 * 1024 * 1024,
) -> UploadOutcome:
    """Stream `stream` into `volume_path` via Databricks Files API.

    The Databricks SDK is synchronous; we run it in a worker thread so we don't
    block the FastAPI event loop. See ADR 0010.
    """
    raise NotImplementedError(
        "TODO: instantiate WorkspaceClient and call ws.files.upload(volume_path, "
        "contents=Sha256StreamWrapper(stream), overwrite=overwrite, part_size=part_size, "
        "use_parallel=True) inside asyncio.to_thread()."
    )


async def get_metadata(volume_path: str) -> dict:
    raise NotImplementedError("TODO: ws.files.get_metadata(volume_path) inside asyncio.to_thread()")


async def delete(volume_path: str) -> None:
    raise NotImplementedError("TODO: ws.files.delete(volume_path) inside asyncio.to_thread()")


# Suppress unused-import warning until implemented.
_ = asyncio
