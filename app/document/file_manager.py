"""Text-file persistence for the MVP."""

from pathlib import Path
import hashlib
import os
import tempfile

from .document import Document
from .encoding import detect_line_ending, normalize_line_endings


class ExternalChangeError(ValueError):
    """The on-disk document changed since it was loaded or last saved."""


class FileManager:
    def open(self, path: str | Path) -> Document:
        file_path = Path(path)
        raw = file_path.read_bytes()
        text = raw.decode("utf-8-sig")
        if "\x00" in text:
            raise ValueError("This file contains binary data and cannot be opened as UTF-8 text.")
        document = Document.from_text(text.replace("\r\n", "\n").replace("\r", "\n"), file_path)
        document.line_ending = detect_line_ending(text)
        document.disk_digest = hashlib.sha256(raw).hexdigest()
        return document

    def save(self, document: Document, path: str | Path | None = None) -> Path:
        target = Path(path) if path is not None else document.path
        if target is None:
            raise ValueError("A path is required to save an untitled document")
        write_target = target.resolve() if target.is_symlink() else target
        same_document = document.path is not None and target.resolve(strict=False) == document.path.resolve(strict=False)
        if same_document and document.disk_digest is not None:
            try:
                current = write_target.read_bytes()
            except FileNotFoundError as exc:
                raise ExternalChangeError(
                    f"{target} was removed after it was opened; use Save As to create a new file."
                ) from exc
            if hashlib.sha256(current).hexdigest() != document.disk_digest:
                raise ExternalChangeError(
                    f"{target} changed on disk since it was opened; reload, compare, or use Save As."
                )
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
            if same_document and document.disk_digest is not None:
                try:
                    current = write_target.read_bytes()
                except FileNotFoundError as exc:
                    raise ExternalChangeError(
                        f"{target} was removed during saving; use Save As to create a new file."
                    ) from exc
                if hashlib.sha256(current).hexdigest() != document.disk_digest:
                    raise ExternalChangeError(
                        f"{target} changed on disk during saving; reload, compare, or use Save As."
                    )
            os.replace(temporary, write_target)
        except BaseException:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        document.path = target
        document.disk_digest = hashlib.sha256(payload).hexdigest()
        document.mark_saved()
        return target
