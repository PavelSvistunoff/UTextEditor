"""Resolve recovered project identities without touching widgets or canonical text."""

from dataclasses import dataclass, replace
from pathlib import Path

from app.document.document import Document
from app.document.recovery import RecoveryStore, RecoveryEntry, RecoveryConflictError
from .service import Project
from .model import Note, ProjectError, Scene


@dataclass(frozen=True)
class RecoveryRestoreMessages:
    project_unavailable: str = "Original project is unavailable; recovered text was opened separately."
    wrong_project: str = "The selected directory is a different project."
    unidentified_item: str = "The original project item could not be identified."


def prepare_recovery_restore(
    store: RecoveryStore, entries: tuple[RecoveryEntry, ...], located_directory: str | Path | None,
    messages: RecoveryRestoreMessages | None = None,
) -> list[tuple[RecoveryEntry, Document, str | None]]:
    messages = messages or RecoveryRestoreMessages()
    restored = []
    for original in entries:
        entry = original
        if entry.project_id is not None:
            project_path = Path(entry.project_path) if entry.project_path else None
            if (project_path is None or not project_path.is_dir()) and located_directory:
                project_path = Path(located_directory)
            if project_path is None or not project_path.is_dir():
                restored.append((entry, Document(text=entry.text, dirty=True), messages.project_unavailable))
                continue
            try:
                project = Project.open(project_path)
                if project.manifest.project_id != entry.project_id:
                    raise ProjectError(messages.wrong_project)
                item = _recovery_project_item(project, entry, messages)
                entry = replace(
                    entry,
                    canonical_path=str(project.root / item.path),
                    project_path=str(project.root),
                )
            except (OSError, ProjectError) as exc:
                restored.append((entry, Document(text=entry.text, dirty=True), str(exc)))
                continue
        try:
            document = store.restore(entry)
            restored.append((entry, document, None))
        except (RecoveryConflictError, OSError, UnicodeError) as exc:
            restored.append(
                (entry, Document(text=entry.text, dirty=True), str(exc))
            )
    return restored


def _recovery_project_item(project: Project, entry: RecoveryEntry, messages: RecoveryRestoreMessages) -> Scene | Note:
    if entry.project_item_id is not None:
        return (project.get_scene(entry.project_item_id) if entry.project_item_kind == "scene"
                else project.get_note(entry.project_item_id))
    # Legacy snapshots identify a project-relative path instead of a stable item ID.
    relative_path = None
    if entry.canonical_path and entry.project_path:
        try:
            relative_path = Path(entry.canonical_path).resolve().relative_to(Path(entry.project_path).resolve())
        except ValueError:
            pass
    candidates = [*project.iter_scenes(), *project.manifest.notes]
    matches = [item for item in candidates if relative_path is not None and Path(item.path) == relative_path]
    if len(matches) != 1:
        raise ProjectError(messages.unidentified_item)
    return matches[0]
