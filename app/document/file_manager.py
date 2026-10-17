"""Text-file persistence for the MVP."""

from pathlib import Path
import os
import tempfile

from .document import Document
from .encoding import detect_line_ending, normalize_line_endings


class FileManager:
    def open(self, path: str | Path) -> Document:
        file_path = Path(path)
        raw = file_path.read_bytes()
        text = raw.decode("utf-8-sig")
        if "\x00" in text:
            raise ValueError("This file contains binary data and cannot be opened as UTF-8 text.")
        document = Document.from_text(text.replace("\r\n", "\n").replace("\r", "\n"), file_path)
        document.line_ending = detect_line_ending(text)
        return document

    def save(self, document: Document, path: str | Path | None = None) -> Path:
        target = Path(path) if path is not None else document.path
        if target is None:
            raise ValueError("A path is required to save an untitled document")
        write_target = target.resolve() if target.is_symlink() else target
        write_target.parent.mkdir(parents=True, exist_ok=True)
        payload = normalize_line_endings(document.text, document.line_ending).encode(document.encoding)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{write_target.name}.", suffix=".tmp", dir=write_target.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            if write_target.exists():
                os.chmod(temporary, write_target.stat().st_mode)
            os.replace(temporary, write_target)
        except BaseException:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        document.path = target
        document.mark_saved()
        return target
