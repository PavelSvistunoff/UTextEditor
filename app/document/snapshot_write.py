"""Shared durable staging for JSON recovery and revision snapshots.

Callers own serialization, destination validation and retention. This does not
coordinate concurrent writers or provide the manuscript conflict protocol.
"""

import os
from pathlib import Path
import tempfile


def write_snapshot_bytes(target: Path, payload: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except BaseException:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            # Preserve the write failure if best-effort staging cleanup also fails.
            pass
        raise
