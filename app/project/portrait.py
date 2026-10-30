"""Portable, size-limited embedded character portrait data."""

import base64
import binascii

MAX_PORTRAIT_BYTES = 256_000


def decode_portrait(value: str) -> bytes:
    if not isinstance(value, str) or len(value) > ((MAX_PORTRAIT_BYTES + 2) // 3) * 4:
        raise ValueError("Portrait data is invalid or exceeds 256 KB.")
    if not value:
        return b""
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("Portrait data is not valid base64.") from exc
    if len(raw) > MAX_PORTRAIT_BYTES or not (raw.startswith(b"\x89PNG\r\n\x1a\n") or raw.startswith(b"\xff\xd8\xff")):
        raise ValueError("Portrait must be a PNG or JPEG of at most 256 KB.")
    return raw
