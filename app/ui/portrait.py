"""Load bounded portrait images in a background worker."""

import base64
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice
from PySide6.QtGui import QImageReader

from app.project.portrait import MAX_PORTRAIT_BYTES, decode_portrait

MAX_DIMENSION = 2048


def load_portrait(*, path: str | None = None, encoded: str | None = None):
    if path is not None:
        with Path(path).open("rb") as stream:
            raw = stream.read(MAX_PORTRAIT_BYTES + 1)
        encoded = base64.b64encode(raw).decode("ascii")
    if not encoded:
        raise ValueError("Choose a PNG or JPEG portrait.")
    raw = decode_portrait(encoded)
    buffer = QBuffer()
    buffer.setData(QByteArray(raw))
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    reader = QImageReader(buffer)
    reader.setAutoTransform(True)
    size = reader.size()
    if not size.isValid() or size.width() > MAX_DIMENSION or size.height() > MAX_DIMENSION:
        raise ValueError("Portrait dimensions must be at most 2048 by 2048 pixels.")
    if bytes(reader.format()).lower() not in (b"png", b"jpeg", b"jpg"):
        raise ValueError("Portrait must be a PNG or JPEG image.")
    image = reader.read()
    if image.isNull():
        raise ValueError("The portrait image could not be decoded.")
    return encoded, image
