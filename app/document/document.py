"""Provider-neutral document state."""

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Document:
    """The persistent state associated with one editor tab."""

    text: str = ""
    path: Path | None = None
    encoding: str = "utf-8"
    line_ending: str = "LF"
    revision: int = 0
    dirty: bool = False
    _saved_revision: int = field(default=0, repr=False)

    @property
    def display_name(self) -> str:
        return self.path.name if self.path else "Untitled"

    def update_text(self, text: str) -> None:
        if text != self.text:
            self.text = text
            self.revision += 1
            self.dirty = self.revision != self._saved_revision

    def mark_saved(self) -> None:
        self._saved_revision = self.revision
        self.dirty = False

    @classmethod
    def from_text(cls, text: str, path: Path | None = None) -> "Document":
        document = cls(text=text, path=path)
        document.mark_saved()
        return document
