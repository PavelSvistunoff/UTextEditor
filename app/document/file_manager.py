"""Text-file persistence for the MVP."""

from pathlib import Path

from .document import Document
from .encoding import detect_line_ending, normalize_line_endings


class FileManager:
    def open(self, path: str | Path) -> Document:
        file_path = Path(path)
        raw = file_path.read_bytes()
        text = raw.decode("utf-8")
        document = Document.from_text(text.replace("\r\n", "\n").replace("\r", "\n"), file_path)
        document.line_ending = detect_line_ending(text)
        return document

    def save(self, document: Document, path: str | Path | None = None) -> Path:
        target = Path(path) if path is not None else document.path
        if target is None:
            raise ValueError("A path is required to save an untitled document")
        target.write_bytes(normalize_line_endings(document.text, document.line_ending).encode(document.encoding))
        document.path = target
        document.mark_saved()
        return target
