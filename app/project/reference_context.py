"""Complete, bounded project notes captured in workers without silent omission."""

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass
import json
import os
from pathlib import Path
import stat

from app.document.encoding import has_binary_controls
from .model import ProjectError
from .paths import validate_project_path
from .service import Project

MAX_PROJECT_REFERENCE_BYTES = 64 * 1024


def check_reference_size(text: str) -> None:
    if len(text.encode("utf-8")) > MAX_PROJECT_REFERENCE_BYTES:
        raise ProjectError(
            "Complete project reference context exceeds the 64 KiB limit; "
            "reduce the reference material before retrying. No context was truncated."
        )


def _read_note(project: Project, note_id: str) -> str:
    path = validate_project_path(project.root, project.get_note(note_id).path)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
    with os.fdopen(descriptor, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise ProjectError("A reference note is not a regular file.")
        raw = stream.read(MAX_PROJECT_REFERENCE_BYTES + 1)
    if len(raw) > MAX_PROJECT_REFERENCE_BYTES:
        raise ProjectError("A complete reference note exceeds the 64 KiB context limit; no context was truncated.")
    text = raw.decode("utf-8")
    if has_binary_controls(text):
        raise ProjectError("A reference note contains binary data.")
    return text


@dataclass(frozen=True)
class CapturedNote:
    id: str
    title: str
    type: str
    text: str
    disk_text: str


@dataclass(frozen=True)
class ProjectNotes:
    root: Path
    manifest: dict
    notes: tuple[CapturedNote, ...]
    text: str

    def verify_current(self) -> None:
        """Run in a worker, including again after author review."""
        fresh = Project.open(self.root)
        if fresh.manifest.to_mapping() != self.manifest:
            raise ProjectError("Project reference context changed; discard the generated result and retry.")
        for note in self.notes:
            if _read_note(fresh, note.id) != note.disk_text:
                raise ProjectError("A reference note changed; discard the generated result and retry.")


def capture_project_notes(project: Project, open_text: Mapping[str, str | None]) -> ProjectNotes:
    """Capture all notes; None marks a too-large open buffer, never a disk fallback."""
    manifest = deepcopy(project.manifest.to_mapping())
    fresh = Project.open(project.root)
    if fresh.manifest.to_mapping() != manifest:
        raise ProjectError("Project reference context changed before the request; reload and retry.")
    notes = []
    serialized = []
    used_bytes = 2
    for note in fresh.manifest.notes:
        if note.id in open_text and open_text[note.id] is None:
            raise ProjectError("An open reference note exceeds the complete context limit; no context was truncated.")
        disk_text = _read_note(fresh, note.id)
        text = open_text.get(note.id, disk_text)
        check_reference_size(text)
        record = json.dumps({"id": note.id, "type": note.type, "title": note.title, "text": text},
                            ensure_ascii=False)
        used_bytes += len(record.encode("utf-8")) + (1 if serialized else 0)
        if used_bytes > MAX_PROJECT_REFERENCE_BYTES:
            raise ProjectError("Complete project notes exceed the 64 KiB context limit; no context was truncated.")
        serialized.append(record)
        notes.append(CapturedNote(note.id, note.title, note.type, text, disk_text))
    context = ProjectNotes(fresh.root, manifest, tuple(notes), "[" + ",".join(serialized) + "]")
    context.verify_current()
    return context
